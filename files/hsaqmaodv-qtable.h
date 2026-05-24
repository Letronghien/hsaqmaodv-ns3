/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * H-SAQMAODV: Topology-Aware Hybrid Self-Adaptive Q-Table.
 *
 * Extends SA-QMAODV QTable with THREE-MODE Q-SWITCHING based on
 * Topology Volatility Indicator (TVI = ΔSeq rate).
 *
 * New behaviour in SelectEpsilonGreedy():
 *
 *   TVI > m_tviHigh  → MODE_BYPASS:  return primary route directly
 *                       (network too chaotic, skip Q-learning)
 *   TVI < m_tviLow   → MODE_GREEDY:  select best Q-value (ε = 0)
 *                       (network stable, Q has converged)
 *   otherwise         → MODE_EXPLORE: standard ε-greedy (same as SAQMAODV)
 *
 * All SA adaptive mechanisms (ε decay, α recompute, reward weights) run
 * unchanged in the background — they help MODE_EXPLORE accuracy and smooth
 * mode transitions.
 *
 * Paper: "H-SAQMAODV: A Topology-Aware Hybrid Q-Learning Routing Protocol
 *         for Energy-Heterogeneous FANETs"
 * Inspired by: HQA (ScienceDirect 2025) — Bayesian stability evaluator
 */

#ifndef HSAQMAODV_QTABLE_H
#define HSAQMAODV_QTABLE_H

#include "saqmaodv-rtable.h"

#include "ns3/ipv4-address.h"
#include "ns3/nstime.h"
#include "ns3/random-variable-stream.h"

#include <map>
#include <vector>
#include <deque>

namespace ns3
{
namespace hsaqmaodv
{

/// Routing mode selected by Topology-Aware Q-Switching.
enum QSwitchMode
{
    MODE_BYPASS  = 0,   ///< TVI > tviHigh: skip Q, use primary route
    MODE_GREEDY  = 1,   ///< TVI < tviLow:  pure greedy (ε=0)
    MODE_EXPLORE = 2,   ///< normal ε-greedy (SA-QMAODV default)
};

/// One Q-learning record per (destination, next-hop) pair.
struct QRecord
{
    RoutingTableEntry rt;
    double            qValue;
    uint32_t          txCount;
    uint32_t          ackCount;
    Time              lastUpd;

    QRecord() : qValue(0.0), txCount(0), ackCount(0), lastUpd(Seconds(0)) {}
    QRecord(const RoutingTableEntry& e, double q)
        : rt(e), qValue(q), txCount(0), ackCount(0), lastUpd(Seconds(0)) {}
};

/**
 * \brief H-SAQMAODV Hybrid Self-Adaptive Q-Table.
 *
 * Drop-in replacement for saqmaodv::QTable with added topology-aware switching.
 */
class QTable
{
  public:
    QTable(uint32_t maxPaths = 3);

    void SetMaxPaths(uint32_t mp);
    uint32_t GetMaxPaths() const;

    // -------- Inherited SA hyper-parameter setters --------------------------
    void SetLearningParameters(double alpha0, double gamma, double epsilon0);
    void SetRewardWeights(double w1, double w2, double w3 = 0.0);
    void SetLowEnergyThreshold(double frac);
    void SetSensitivityLambda(double lambda);
    void SetSeqNoWindow(Time window);

    // -------- NEW: Topology-Aware Q-Switching thresholds -------------------
    /**
     * \brief Set TVI thresholds for mode switching.
     * \param tviHigh  ΔSeq count above which MODE_BYPASS activates (default 8).
     * \param tviLow   ΔSeq count below which MODE_GREEDY activates (default 1).
     */
    void SetTVIThresholds(uint32_t tviHigh, uint32_t tviLow);
    uint32_t GetTVIHigh() const { return m_tviHigh; }
    uint32_t GetTVILow()  const { return m_tviLow; }

    // -------- SA adaptive controller (unchanged from SAQMAODV) -------------
    void OnRouteError();
    void PeriodicEpsilonDecay();
    void RecordSeqNoUpdate();
    void RecomputeAdaptiveAlpha();
    void RecomputeAdaptiveRewardWeights(double energyFraction);

    // -------- Read accessors -----------------------------------------------
    double   GetAlpha()    const { return m_alpha; }
    double   GetGamma()    const { return m_gamma; }
    double   GetEpsilon()  const { return m_epsilon; }
    double   GetW1()       const { return m_w1; }
    double   GetW2()       const { return m_w2; }
    double   GetW3()       const { return m_w3; }
    uint32_t GetDeltaSeq() const;
    QSwitchMode GetCurrentMode() const { return m_lastMode; }
    /// Counters for paper Fig 6 (mode distribution)
    uint64_t GetBypassCount()  const { return m_bypassCount; }
    uint64_t GetGreedyCount()  const { return m_greedyCount; }
    uint64_t GetExploreCount() const { return m_exploreCount; }

    // -------- Standard Q-table operations (same as SAQMAODV) ---------------
    bool     AddRoute(const RoutingTableEntry& rt);
    void     ReinitQValues(Ipv4Address dst);
    uint32_t GetRoutes(Ipv4Address dst,
                       std::vector<RoutingTableEntry>& routes,
                       const RoutingTable* mainTable = nullptr) const;

    /**
     * \brief Route selection with THREE-MODE switching.
     *
     * Core contribution of H-SAQMAODV:
     *   - Evaluates TVI = GetDeltaSeq()
     *   - Selects MODE_BYPASS / MODE_GREEDY / MODE_EXPLORE accordingly
     */
    bool SelectEpsilonGreedy(const RoutingTableEntry& primary,
                             RoutingTableEntry& out,
                             const RoutingTable* mainTable = nullptr);

    void UpdateQValue(Ipv4Address dst, Ipv4Address nextHop,
                      double ackSuccess, double delaySec,
                      double energyFraction = 1.0);
    bool EnsureRecord(const RoutingTableEntry& rt);
    void UpdateQValueOrCreate(const RoutingTableEntry& rt,
                              double ackSuccess, double delaySec,
                              double energyFraction = 1.0);

    void     DeleteRoutes(Ipv4Address dst);
    void     DeleteRoute(Ipv4Address dst, Ipv4Address nextHop);
    void     RemoveNextHopGlobally(Ipv4Address nextHop);
    uint32_t Size() const;
    uint32_t CountFor(Ipv4Address dst) const;
    bool     IsFull(Ipv4Address dst) const;
    void     Clear();
    void     Print(std::ostream& os) const;
    double   GetQValue(Ipv4Address dst, Ipv4Address nextHop) const;

  private:
    std::vector<QRecord>::iterator FindWorst(std::vector<QRecord>& vec);
    std::vector<QRecord> BuildCandidates(const RoutingTableEntry& primary,
                                         const RoutingTable* mainTable) const;
    double ComputeReward(double ackSuccess, double delaySec, double energyFrac) const;
    void   PurgeSeqNoEvents();

    // Q-table storage
    std::map<Ipv4Address, std::vector<QRecord>> m_records;
    uint32_t m_maxPaths;

    // SA adaptive state (unchanged)
    double m_alpha, m_gamma, m_epsilon;
    double m_w1, m_w2, m_w3;
    bool   m_lowEnergyMode;
    double m_epsilonMin, m_epsilonMax, m_epsilonStep, m_epsilonBump;
    double m_lambda;
    Time   m_seqNoWindow;
    double m_lowEnergyThresh;
    double m_w1Normal, m_w2Normal, m_w3Normal;
    double m_w1Low, m_w2Low, m_w3Low;
    mutable std::deque<Time> m_seqEvents;

    // NEW: Topology-Aware Q-Switching state
    uint32_t    m_tviHigh;      ///< ΔSeq threshold → MODE_BYPASS  (default 8)
    uint32_t    m_tviLow;       ///< ΔSeq threshold → MODE_GREEDY  (default 1)
    QSwitchMode m_lastMode;     ///< Mode used in last SelectEpsilonGreedy call
    uint64_t    m_bypassCount;  ///< Total MODE_BYPASS selections
    uint64_t    m_greedyCount;  ///< Total MODE_GREEDY selections
    uint64_t    m_exploreCount; ///< Total MODE_EXPLORE selections

    Ptr<UniformRandomVariable> m_uniform;
};

} // namespace hsaqmaodv
} // namespace ns3

#endif /* HSAQMAODV_QTABLE_H */
