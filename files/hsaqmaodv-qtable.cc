/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * \file hsaqmaodv-qtable.cc
 * \brief H-SAQMAODV Hybrid QTable — implementation.
 *
 * Key design decision: all extra parameters (TVI thresholds, sigmoid params)
 * are static constexpr in the header. This keeps sizeof(hsaqmaodv::QTable)
 * equal to sizeof(saqmaodv::QTable), preventing memory layout mismatch in
 * the routing protocol (which declares m_qtable as a VALUE member).
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
// Constructor — no extra member init needed (all params are static constexpr)
// ============================================================================

QTable::QTable (uint32_t maxPaths)
    : saqmaodv::QTable (maxPaths)
{
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
    double exponent = (energyFraction - m_sigmaTheta) / m_sigmaSigma;
    return 1.0 / (1.0 + std::exp (exponent));
}

// ============================================================================
// Smooth energy weighting (Contribution 2, Eq. H.3–H.5)
// ============================================================================

void
QTable::RecomputeSmoothEnergyWeights (double energyFraction)
{
    constexpr double w2Hi = 0.40, w3Hi = 0.10;
    constexpr double                w3Lo = 0.80;

    double s  = SigmoidActivation (energyFraction);
    double w3 = w3Hi + (w3Lo - w3Hi) * s;
    double w2 = w2Hi * (1.0 - s);
    double w1 = 1.0 - w2 - w3;

    w1 = std::max (0.0, std::min (1.0, w1));
    w2 = std::max (0.0, std::min (1.0, w2));
    w3 = std::max (0.0, std::min (1.0, w3));

    SetRewardWeights (w1, w2, w3);

    NS_LOG_DEBUG ("HSAQMAODV smooth weights: E=" << energyFraction
                  << " s=" << s
                  << " w=(" << w1 << "," << w2 << "," << w3 << ")");
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
        out = primary;
        return true;

    case MODE_GREEDY:
        {
            // Exploit best Q-value: epsilon=0 greedy via epsilon-greedy
            double saved = GetEpsilon ();
            SetLearningParameters (GetAlpha (), GetGamma (), 0.0);
            bool ok = SelectEpsilonGreedy (primary, out, mainTable);
            SetLearningParameters (GetAlpha (), GetGamma (), saved);
            return ok;
        }

    case MODE_EXPLORE:
    default:
        return SelectEpsilonGreedy (primary, out, mainTable);
    }
}

} // namespace hsaqmaodv
} // namespace ns3
