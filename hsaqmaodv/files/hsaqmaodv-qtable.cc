/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * H-SAQMAODV Hybrid Self-Adaptive Q-Table — implementation.
 * See hsaqmaodv-qtable.h for design discussion.
 */

#include "hsaqmaodv-qtable.h"

#include "ns3/log.h"
#include "ns3/simulator.h"

#include <algorithm>
#include <cmath>
#include <numeric>

namespace ns3
{

NS_LOG_COMPONENT_DEFINE("HsaqmaodvQTable");

namespace hsaqmaodv
{

QTable::QTable(uint32_t maxPaths)
    : m_maxPaths(maxPaths),
      // SA initial params (paper Table 1)
      m_alpha(0.5), m_gamma(0.9), m_epsilon(0.3),
      m_w1(0.5), m_w2(0.4), m_w3(0.1),
      m_lowEnergyMode(false),
      m_epsilonMin(0.10), m_epsilonMax(0.50),
      m_epsilonStep(0.02), m_epsilonBump(0.20),
      m_lambda(0.1),
      m_seqNoWindow(Seconds(5.0)),
      m_lowEnergyThresh(0.20),
      m_w1Normal(0.5), m_w2Normal(0.4), m_w3Normal(0.1),
      m_w1Low(0.1), m_w2Low(0.1), m_w3Low(0.8),
      // NEW: Topology-Aware Q-Switching defaults
      m_tviHigh(8),
      m_tviLow(1),
      m_lastMode(MODE_EXPLORE),
      m_bypassCount(0), m_greedyCount(0), m_exploreCount(0)
{
    m_uniform = CreateObject<UniformRandomVariable>();
}

// ============================================================================
// Configuration
// ============================================================================
void QTable::SetMaxPaths(uint32_t mp)       { m_maxPaths = mp; }
uint32_t QTable::GetMaxPaths() const        { return m_maxPaths; }

void QTable::SetLearningParameters(double a, double g, double e)
{
    m_alpha = a; m_gamma = g; m_epsilon = e;
}
void QTable::SetRewardWeights(double w1, double w2, double w3)
{
    m_w1 = w1; m_w2 = w2; m_w3 = w3;
    m_w1Normal = w1; m_w2Normal = w2; m_w3Normal = w3;
}
void QTable::SetLowEnergyThreshold(double f) { m_lowEnergyThresh = f; }
void QTable::SetSensitivityLambda(double l)  { m_lambda = l; }
void QTable::SetSeqNoWindow(Time w)          { m_seqNoWindow = w; }

void QTable::SetTVIThresholds(uint32_t tviHigh, uint32_t tviLow)
{
    NS_ASSERT_MSG(tviHigh > tviLow, "tviHigh must be > tviLow");
    m_tviHigh = tviHigh;
    m_tviLow  = tviLow;
    NS_LOG_INFO("H-SAQMAODV TVI thresholds: low=" << tviLow << " high=" << tviHigh);
}

// ============================================================================
// SA Adaptive Controller (identical to SAQMAODV)
// ============================================================================
void QTable::OnRouteError()
{
    m_epsilon = std::min(m_epsilonMax, m_epsilon + m_epsilonBump);
    NS_LOG_DEBUG("HSAQM ε bump on RERR → " << m_epsilon);
}

void QTable::PeriodicEpsilonDecay()
{
    m_epsilon = std::max(m_epsilonMin, m_epsilon - m_epsilonStep);
    NS_LOG_DEBUG("HSAQM ε decayed → " << m_epsilon);
}

void QTable::RecordSeqNoUpdate()
{
    m_seqEvents.push_back(Simulator::Now());
    PurgeSeqNoEvents();
}

void QTable::PurgeSeqNoEvents()
{
    const Time threshold = Simulator::Now() - m_seqNoWindow;
    while (!m_seqEvents.empty() && m_seqEvents.front() < threshold)
        m_seqEvents.pop_front();
}

uint32_t QTable::GetDeltaSeq() const
{
    const Time threshold = Simulator::Now() - m_seqNoWindow;
    while (!m_seqEvents.empty() && m_seqEvents.front() < threshold)
        m_seqEvents.pop_front();
    return static_cast<uint32_t>(m_seqEvents.size());
}

void QTable::RecomputeAdaptiveAlpha()
{
    uint32_t dSeq = GetDeltaSeq();
    m_alpha = 0.1 + 0.8 * (1.0 - std::exp(-m_lambda * static_cast<double>(dSeq)));
    NS_LOG_DEBUG("HSAQM α recomputed: ΔSeq=" << dSeq << " → α=" << m_alpha);
}

void QTable::RecomputeAdaptiveRewardWeights(double energyFraction)
{
    bool lowNow = (energyFraction < m_lowEnergyThresh);
    if (lowNow != m_lowEnergyMode)
    {
        m_lowEnergyMode = lowNow;
        if (lowNow)
            { m_w1 = m_w1Low; m_w2 = m_w2Low; m_w3 = m_w3Low; }
        else
            { m_w1 = m_w1Normal; m_w2 = m_w2Normal; m_w3 = m_w3Normal; }
        NS_LOG_DEBUG("HSAQM low-energy mode " << (lowNow ? "ON" : "OFF"));
    }
}

// ============================================================================
// Reward
// ============================================================================
double QTable::ComputeReward(double ack, double delaySec, double eFrac) const
{
    if (delaySec < 0.0) delaySec = 0.0;
    return m_w1 * ack + m_w2 * (1.0 / (delaySec + 1.0)) + m_w3 * eFrac;
}

// ============================================================================
// THREE-MODE TOPOLOGY-AWARE Q-SWITCHING  (core contribution)
// ============================================================================
bool QTable::SelectEpsilonGreedy(const RoutingTableEntry& primary,
                                  RoutingTableEntry& out,
                                  const RoutingTable* mainTable)
{
    auto cands = BuildCandidates(primary, mainTable);
    if (cands.empty()) { out = primary; return false; }
    if (cands.size() == 1) { out = cands[0].rt; return true; }

    // === Topology Volatility Indicator ===
    uint32_t tvi = GetDeltaSeq();

    if (tvi > m_tviHigh)
    {
        // MODE_BYPASS: network too chaotic, trust fresh AODV route
        m_lastMode = MODE_BYPASS;
        ++m_bypassCount;
        out = primary;
        NS_LOG_DEBUG("HSAQM MODE_BYPASS (TVI=" << tvi << " > " << m_tviHigh << ")");
        return true;
    }
    else if (tvi < m_tviLow)
    {
        // MODE_GREEDY: network stable, Q-values converged → exploit only
        m_lastMode = MODE_GREEDY;
        ++m_greedyCount;
        size_t bestIdx = 0;
        double bestQ   = -std::numeric_limits<double>::infinity();
        uint32_t bestHC = std::numeric_limits<uint32_t>::max();
        for (size_t i = 0; i < cands.size(); ++i)
        {
            double q  = cands[i].qValue;
            uint32_t hc = cands[i].rt.GetHop();
            if (q > bestQ || (std::fabs(q - bestQ) < 1e-9 && hc < bestHC))
                { bestQ = q; bestHC = hc; bestIdx = i; }
        }
        out = cands[bestIdx].rt;
        NS_LOG_DEBUG("HSAQM MODE_GREEDY (TVI=" << tvi << " < " << m_tviLow
                     << ") → Q=" << bestQ);
        return true;
    }
    else
    {
        // MODE_EXPLORE: standard ε-greedy (identical to SAQMAODV)
        m_lastMode = MODE_EXPLORE;
        ++m_exploreCount;
        double u = m_uniform->GetValue(0.0, 1.0);
        if (u < m_epsilon)
        {
            uint32_t idx = static_cast<uint32_t>(
                m_uniform->GetValue(0.0, static_cast<double>(cands.size())));
            if (idx >= cands.size()) idx = cands.size() - 1;
            out = cands[idx].rt;
        }
        else
        {
            size_t bestIdx = 0;
            double bestQ  = -std::numeric_limits<double>::infinity();
            uint32_t bestHC = std::numeric_limits<uint32_t>::max();
            for (size_t i = 0; i < cands.size(); ++i)
            {
                double q = cands[i].qValue; uint32_t hc = cands[i].rt.GetHop();
                if (q > bestQ || (std::fabs(q - bestQ) < 1e-9 && hc < bestHC))
                    { bestQ = q; bestHC = hc; bestIdx = i; }
            }
            out = cands[bestIdx].rt;
        }
        NS_LOG_DEBUG("HSAQM MODE_EXPLORE (TVI=" << tvi << ") ε=" << m_epsilon);
        return true;
    }
}

// ============================================================================
// Q-update (identical to SAQMAODV)
// ============================================================================
void QTable::UpdateQValue(Ipv4Address dst, Ipv4Address nextHop,
                           double ackSuccess, double delaySec, double energyFraction)
{
    double reward = ComputeReward(ackSuccess, delaySec, energyFraction);
    auto it = m_records.find(dst);
    if (it == m_records.end()) return;
    QRecord* target = nullptr;
    double maxFuture = 0.0;
    for (auto& r : it->second)
    {
        if (r.qValue > maxFuture) maxFuture = r.qValue;
        if (r.rt.GetNextHop() == nextHop) target = &r;
    }
    if (!target) return;
    double oldQ = target->qValue;
    target->qValue = (1.0 - m_alpha)*oldQ + m_alpha*(reward + m_gamma*maxFuture);
    ++target->txCount;
    if (ackSuccess > 0.5) ++target->ackCount;
    target->lastUpd = Simulator::Now();
}

void QTable::UpdateQValueOrCreate(const RoutingTableEntry& rt,
                                   double ack, double delay, double eFrac)
{
    EnsureRecord(rt);
    UpdateQValue(rt.GetDestination(), rt.GetNextHop(), ack, delay, eFrac);
}

// ============================================================================
// Standard route management (identical to SAQMAODV)
// ============================================================================
std::vector<QRecord>::iterator QTable::FindWorst(std::vector<QRecord>& vec)
{
    if (vec.empty()) return vec.end();
    auto worst = vec.begin();
    for (auto it = vec.begin()+1; it != vec.end(); ++it)
        if (it->rt.GetHop() > worst->rt.GetHop()) worst = it;
    return worst;
}

bool QTable::AddRoute(const RoutingTableEntry& rt)
{
    Ipv4Address dst = rt.GetDestination(), nh = rt.GetNextHop();
    auto& vec = m_records[dst];
    for (auto& e : vec) { if (e.rt.GetNextHop() == nh) { e.rt = rt; return false; } }
    if (vec.size() < m_maxPaths) { vec.push_back(QRecord(rt, 0.0)); ReinitQValues(dst); return true; }
    auto worst = FindWorst(vec);
    if (worst != vec.end() && rt.GetHop() < worst->rt.GetHop())
        { *worst = QRecord(rt, 0.0); ReinitQValues(dst); return true; }
    return false;
}

bool QTable::EnsureRecord(const RoutingTableEntry& rt)
{
    auto& vec = m_records[rt.GetDestination()];
    for (auto& e : vec) { if (e.rt.GetNextHop() == rt.GetNextHop()) { e.rt = rt; return false; } }
    vec.push_back(QRecord(rt, 0.0)); ReinitQValues(rt.GetDestination()); return true;
}

void QTable::ReinitQValues(Ipv4Address dst)
{
    auto it = m_records.find(dst);
    if (it == m_records.end()) return;
    double sumInv = 0.0;
    for (const auto& r : it->second) sumInv += 1.0/std::max<uint32_t>(1, r.rt.GetHop());
    if (sumInv <= 0.0) return;
    for (auto& r : it->second)
    {
        if (r.txCount > 0) continue;
        r.qValue = (1.0/std::max<uint32_t>(1, r.rt.GetHop())) / sumInv;
    }
}

uint32_t QTable::GetRoutes(Ipv4Address dst, std::vector<RoutingTableEntry>& routes,
                            const RoutingTable* mainTable) const
{
    auto it = m_records.find(dst);
    if (it == m_records.end()) return 0;
    uint32_t added = 0;
    for (const auto& r : it->second)
    {
        if (r.rt.GetFlag() != VALID || r.rt.GetLifeTime() <= Time(0)) continue;
        if (mainTable)
        {
            RoutingTableEntry nbr;
            if (!const_cast<RoutingTable*>(mainTable)->LookupRoute(r.rt.GetNextHop(), nbr) ||
                nbr.GetFlag() != VALID) continue;
        }
        routes.push_back(r.rt); ++added;
    }
    return added;
}

std::vector<QRecord> QTable::BuildCandidates(const RoutingTableEntry& primary,
                                               const RoutingTable* mainTable) const
{
    Ipv4Address dst = primary.GetDestination(), primNh = primary.GetNextHop();
    std::vector<QRecord> cands;
    auto it = m_records.find(dst);
    double primQ = 0.0; bool primFound = false;
    if (it != m_records.end())
        for (const auto& r : it->second)
            if (r.rt.GetNextHop() == primNh) { primQ = r.qValue; primFound = true; break; }
    if (it != m_records.end())
        for (const auto& r : it->second)
        {
            if (r.rt.GetNextHop() == primNh) continue;
            if (r.rt.GetFlag() != VALID || r.rt.GetLifeTime() <= Time(0)) continue;
            if (mainTable)
            {
                RoutingTableEntry nbr;
                if (!const_cast<RoutingTable*>(mainTable)->LookupRoute(r.rt.GetNextHop(), nbr) ||
                    nbr.GetFlag() != VALID) continue;
            }
            cands.push_back(r);
        }
    uint32_t hcP = std::max<uint32_t>(1, primary.GetHop());
    double primQVal = primFound ? primQ : (1.0/hcP);
    cands.insert(cands.begin(), QRecord(primary, primQVal));
    return cands;
}

void QTable::DeleteRoutes(Ipv4Address dst) { m_records.erase(dst); }

void QTable::DeleteRoute(Ipv4Address dst, Ipv4Address nh)
{
    auto it = m_records.find(dst);
    if (it == m_records.end()) return;
    auto& vec = it->second;
    vec.erase(std::remove_if(vec.begin(), vec.end(),
              [&](const QRecord& r){ return r.rt.GetNextHop() == nh; }), vec.end());
    if (vec.empty()) m_records.erase(it);
}

void QTable::RemoveNextHopGlobally(Ipv4Address nh)
{
    for (auto it = m_records.begin(); it != m_records.end(); )
    {
        auto& vec = it->second;
        vec.erase(std::remove_if(vec.begin(), vec.end(),
                  [&](const QRecord& r){ return r.rt.GetNextHop() == nh; }), vec.end());
        if (vec.empty()) it = m_records.erase(it); else ++it;
    }
}

uint32_t QTable::Size() const
{
    return std::accumulate(m_records.begin(), m_records.end(), uint32_t{0},
                           [](uint32_t a, const auto& kv){ return a + kv.second.size(); });
}
uint32_t QTable::CountFor(Ipv4Address dst) const
{
    auto it = m_records.find(dst);
    return it == m_records.end() ? 0 : static_cast<uint32_t>(it->second.size());
}
bool QTable::IsFull(Ipv4Address dst) const { return CountFor(dst) >= m_maxPaths; }
void QTable::Clear() { m_records.clear(); m_seqEvents.clear(); }
double QTable::GetQValue(Ipv4Address dst, Ipv4Address nh) const
{
    auto it = m_records.find(dst);
    if (it == m_records.end()) return 0.0;
    for (const auto& r : it->second) if (r.rt.GetNextHop() == nh) return r.qValue;
    return 0.0;
}

void QTable::Print(std::ostream& os) const
{
    os << "H-SA-Q-Table (" << Size() << " entries"
       << " α=" << m_alpha << " ε=" << m_epsilon
       << " TVI_low=" << m_tviLow << " TVI_high=" << m_tviHigh
       << " mode=" << (m_lastMode==MODE_BYPASS?"BYPASS":m_lastMode==MODE_GREEDY?"GREEDY":"EXPLORE")
       << " counts=[bypass=" << m_bypassCount
       << " greedy=" << m_greedyCount
       << " explore=" << m_exploreCount << "]):\n";
}

} // namespace hsaqmaodv
} // namespace ns3
