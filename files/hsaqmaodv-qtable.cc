/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * \file hsaqmaodv-qtable.cc
 * \brief H-SAQMAODV Hybrid QTable — implementation.
 *
 * See hsaqmaodv-qtable.h for full design rationale and equations.
 *
 * Key changes vs. SAQMAODV base class:
 *   - SelectHybridRoute()            replaces SelectEpsilonGreedy()
 *   - RecomputeSmoothEnergyWeights() replaces RecomputeAdaptiveRewardWeights()
 *   - SigmoidActivation()            implements Eq. H.2
 */

#include "hsaqmaodv-qtable.h"

#include "ns3/log.h"
#include "ns3/simulator.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("HsaqmaodvQTable");

namespace hsaqmaodv {

// ============================================================================
// Constructor
// ============================================================================

QTable::QTable (uint32_t maxPaths, double tviHigh, double tviLow)
    : saqmaodv::QTable (maxPaths),
      m_tviHigh    (tviHigh),
      m_tviLow     (tviLow),
      m_sigmaTheta (0.30),
      m_sigmaSigma (0.08)
{
    NS_ASSERT_MSG (tviLow  > 0.0,      "tviLow must be > 0");
    NS_ASSERT_MSG (tviHigh > tviLow,   "tviHigh must be > tviLow");
    NS_ASSERT_MSG (m_sigmaSigma > 0.0, "sigma must be > 0");
}

// ============================================================================
// TVI threshold configuration
// ============================================================================

void
QTable::SetTVIThresholds (double tviHigh, double tviLow)
{
    NS_ASSERT_MSG (tviLow  > 0.0,    "tviLow must be > 0");
    NS_ASSERT_MSG (tviHigh > tviLow, "tviHigh must be > tviLow");
    m_tviHigh = tviHigh;
    m_tviLow  = tviLow;
}

// ============================================================================
// Sigmoid configuration (Contribution 2)
// ============================================================================

void
QTable::SetSigmoidParams (double theta, double sigma)
{
    NS_ASSERT_MSG (sigma > 0.0, "sigma must be > 0");
    m_sigmaTheta = theta;
    m_sigmaSigma = sigma;
}

// ============================================================================
// TVI / mode helpers (Contribution 1)
// ============================================================================

double
QTable::GetTVI () const
{
    double tvi = static_cast<double> (GetDeltaSeq ()) / kSeqNoWindowSec;
    NS_LOG_DEBUG ("HSAQMAODV TVI=" << tvi
                  << " (ΔSeq=" << GetDeltaSeq ()
                  << " / win=" << kSeqNoWindowSec << "s)");
    return tvi;
}

TopologyMode
QTable::GetCurrentMode () const
{
    double tvi = GetTVI ();
    if (tvi > m_tviHigh) return MODE_BYPASS;
    if (tvi < m_tviLow)  return MODE_GREEDY;
    return MODE_EXPLORE;
}

std::string
QTable::GetModeName () const
{
    switch (GetCurrentMode ())
    {
    case MODE_BYPASS:  return "BYPASS";
    case MODE_GREEDY:  return "GREEDY";
    case MODE_EXPLORE: return "EXPLORE";
    default:           return "UNKNOWN";
    }
}

// ============================================================================
// Sigmoid activation (Contribution 2, Eq. H.2)
// ============================================================================

double
QTable::SigmoidActivation (double energyFraction) const
{
    // s(E) = 1 / (1 + exp( (E − θ) / σ ))
    // As E drops below θ, s(E) → 1 (activates low-energy mode smoothly)
    double exponent = (energyFraction - m_sigmaTheta) / m_sigmaSigma;
    return 1.0 / (1.0 + std::exp (exponent));
}

// ============================================================================
// Smooth energy weighting (Contribution 2, Eq. H.3–H.5)
// ============================================================================

void
QTable::RecomputeSmoothEnergyWeights (double energyFraction)
{
    // Anchor weights from SA-QMAODV paper Table 1
    constexpr double w1Hi = 0.50, w2Hi = 0.40, w3Hi = 0.10;
    constexpr double                            w3Lo = 0.80;

    double s  = SigmoidActivation (energyFraction); // Eq. H.2

    double w3 = w3Hi + (w3Lo - w3Hi) * s;           // Eq. H.3
    double w2 = w2Hi * (1.0 - s);                   // Eq. H.4
    double w1 = 1.0 - w2 - w3;                      // Eq. H.5

    w1 = std::max (0.0, std::min (1.0, w1));
    w2 = std::max (0.0, std::min (1.0, w2));
    w3 = std::max (0.0, std::min (1.0, w3));

    SetRewardWeights (w1, w2, w3);

    NS_LOG_DEBUG ("HSAQMAODV smooth weights: E=" << energyFraction
                  << " s=" << s
                  << " w=(" << w1 << "," << w2 << "," << w3 << ")");
}

// ============================================================================
// Greedy selection — MODE_GREEDY (Contribution 1)
// ============================================================================

bool
QTable::SelectGreedy (const saqmaodv::RoutingTableEntry& primary,
                      saqmaodv::RoutingTableEntry&       out,
                      const saqmaodv::RoutingTable*      mainTable) const
{
    ns3::Ipv4Address dst = primary.GetDestination ();

    std::vector<saqmaodv::RoutingTableEntry> routes;
    uint32_t n = GetRoutes (dst, routes, mainTable);

    if (n == 0)
    {
        NS_LOG_DEBUG ("HSAQMAODV GREEDY: no Q-records for " << dst
                      << " — falling back to primary");
        out = primary;
        return true;
    }

    double bestQ   = std::numeric_limits<double>::lowest ();
    int    bestIdx = -1;
    for (uint32_t i = 0; i < routes.size (); ++i)
    {
        // Safety: skip entries with null Ptr<Ipv4Route> — can cause
        // AggregateObject(ptr, 0) crash when packet is forwarded.
        if (!routes[i].GetRoute ())
        {
            NS_LOG_DEBUG ("HSAQMAODV GREEDY: skip null-route entry nh="
                          << routes[i].GetNextHop ());
            continue;
        }
        double q = GetQValue (dst, routes[i].GetNextHop ());
        NS_LOG_DEBUG ("HSAQMAODV GREEDY candidate: nh=" << routes[i].GetNextHop ()
                      << " Q=" << q);
        if (q > bestQ) { bestQ = q; bestIdx = static_cast<int> (i); }
    }

    // Fall back to primary if no valid route found in Q-table
    out = (bestIdx >= 0) ? routes[static_cast<size_t> (bestIdx)] : primary;
    if (bestIdx >= 0 && !out.GetRoute ())
    {
        NS_LOG_DEBUG ("HSAQMAODV GREEDY: best route has null Ptr<Ipv4Route>, using primary");
        out = primary;
    }
    NS_LOG_DEBUG ("HSAQMAODV GREEDY selected: nh=" << out.GetNextHop ()
                  << " Q=" << bestQ);
    return true;
}

// ============================================================================
// 3-mode hybrid route selection (Contribution 1)
// ============================================================================

bool
QTable::SelectHybridRoute (const saqmaodv::RoutingTableEntry& primary,
                           saqmaodv::RoutingTableEntry&       out,
                           const saqmaodv::RoutingTable*      mainTable)
{
    TopologyMode mode = GetCurrentMode ();

    NS_LOG_DEBUG ("HSAQMAODV SelectHybridRoute:"
                  << " TVI="  << GetTVI ()
                  << " mode=" << GetModeName ()
                  << " dst="  << primary.GetDestination ());

    switch (mode)
    {
    case MODE_BYPASS:
        NS_LOG_DEBUG ("HSAQMAODV BYPASS → primary nh=" << primary.GetNextHop ());
        out = primary;
        return true;

    case MODE_GREEDY:
        return SelectGreedy (primary, out, mainTable);

    case MODE_EXPLORE:
    default:
        return SelectEpsilonGreedy (primary, out, mainTable);
    }
}

} // namespace hsaqmaodv
} // namespace ns3
