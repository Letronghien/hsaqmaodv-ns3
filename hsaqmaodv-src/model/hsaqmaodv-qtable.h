/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * \file hsaqmaodv-qtable.h
 * \brief H-SAQMAODV Hybrid Q-Table: Topology-Aware 3-Mode Switching
 *        with Smooth Energy-Aware Reward Weighting.
 *
 * ══════════════════════════════════════════════════════════════════════════
 * DESIGN OVERVIEW  (for paper / report reference)
 * ══════════════════════════════════════════════════════════════════════════
 *
 * SAQMAODV (base) provides three adaptive mechanisms (§4.2–§4.4):
 *   (1) Adaptive ε : bump on RERR (+0.20), periodic decay (−0.02)
 *   (2) Adaptive α : α_t = 0.1 + 0.8·(1 − exp(−λ·ΔSeq))
 *   (3) Adaptive reward weights: hard-threshold flip at E_res < 20%
 *
 * H-SAQMAODV (this class) extends SAQMAODV with TWO new contributions:
 *
 * ── Contribution 1: Topology Volatility Indicator (TVI) ─────────────────
 *
 *   TVI = ΔSeq_count / seqNoWindow_seconds                    (Eq. H.1)
 *
 *   where ΔSeq_count = number of destination sequence-number updates
 *   observed within the last seqNoWindow seconds (reuses SA base class).
 *   TVI measures how rapidly the topology is changing at the local node.
 *
 *   Three routing modes selected by TVI:
 *
 *     TVI > tviHigh  →  MODE_BYPASS :
 *         Topology too dynamic for Q-learning to be reliable.
 *         Return primary route directly (AODV-like reactive behaviour).
 *         Effect: suppresses exploration overhead in volatile conditions,
 *         directly addressing the high-variance / low-density phenomenon
 *         observed in SA-QMAODV (reviewer comment §3.1).
 *
 *     TVI < tviLow   →  MODE_GREEDY :
 *         Topology stable; Q-values have converged.
 *         Return the route with the highest Q-value (ε forced to 0).
 *         Effect: maximises exploitation when learning is reliable.
 *
 *     tviLow ≤ TVI ≤ tviHigh  →  MODE_EXPLORE :
 *         Standard ε-greedy from SA-QMAODV (default behaviour).
 *
 *   Default thresholds:  tviHigh = 3.0,  tviLow = 1.0
 *   (sensitivity analysis: see PAPER-NOTES.md §5)
 *
 * ── Contribution 2: Smooth Energy-Aware Reward Weighting ────────────────
 *
 *   SAQMAODV uses a HARD threshold: if E_res < 20% flip weights instantly.
 *   This causes abrupt routing instability when energy oscillates near 20%
 *   (reviewer comment §3.4 — "prevent abrupt routing instability").
 *
 *   H-SAQMAODV replaces the hard flip with a SIGMOID-SMOOTH transition:
 *
 *     s(E) = 1 / (1 + exp( (E − θ) / σ ))                   (Eq. H.2)
 *
 *     w3(E) = w3_lo + (w3_hi − w3_lo) · s(E)               (Eq. H.3)
 *     w2(E) = w2_hi · (1 − s(E))                            (Eq. H.4)
 *     w1(E) = 1 − w2(E) − w3(E)          [normalised]       (Eq. H.5)
 *
 *   where:
 *     θ = 0.30  (sigmoid centre — soft energy threshold)
 *     σ = 0.08  (sigmoid steepness — controls transition width)
 *     hi = high-energy (normal) mode target weights: w1=0.50, w2=0.40, w3=0.10
 *     lo = low-energy mode target weights          : w1=0.10, w2=0.10, w3=0.80
 *
 *   Properties:
 *     E = 1.0 (full)  : s ≈ 0  → weights ≈ (0.50, 0.40, 0.10)  [normal]
 *     E = θ  = 0.30   : s = 0.5 → weights smoothly interpolated
 *     E = 0.0 (dead)  : s ≈ 1  → weights ≈ (0.10, 0.10, 0.80)  [low-E]
 *     Monotone, C∞ continuous — no flip, no hysteresis instability.
 *
 * ══════════════════════════════════════════════════════════════════════════
 * NS-3 Integration steps:
 *   1. Copy hsaqmaodv-qtable.{h,cc} beside saqmaodv-qtable.{h,cc}
 *   2. In routing protocol .h : add  hsaqmaodv::QTable  m_hqtable
 *   3. In routing protocol .cc Start():
 *        m_hqtable.SetTVIThresholds(tviHigh, tviLow);
 *        m_hqtable.SetSigmoidParams(theta, sigma);
 *   4. Replace SelectEpsilonGreedy()          → SelectHybridRoute()
 *   5. Replace RecomputeAdaptiveRewardWeights → RecomputeSmoothEnergyWeights
 * ══════════════════════════════════════════════════════════════════════════
 */

#ifndef HSAQMAODV_QTABLE_H
#define HSAQMAODV_QTABLE_H

#include "saqmaodv-qtable.h"
#include "ns3/nstime.h"
#include <string>

namespace ns3 {
namespace hsaqmaodv {

// ── Topology mode ─────────────────────────────────────────────────────────────
/** Routing mode chosen by TVI. */
enum TopologyMode
{
    MODE_BYPASS  = 0, ///< TVI > tviHigh : skip Q-table, AODV-like
    MODE_EXPLORE = 1, ///< tviLow ≤ TVI ≤ tviHigh : epsilon-greedy (SA default)
    MODE_GREEDY  = 2, ///< TVI < tviLow  : exploit best Q-value (ε = 0)
};

// ─────────────────────────────────────────────────────────────────────────────
/**
 * \brief H-SAQMAODV Hybrid QTable.
 *
 * Inherits all of saqmaodv::QTable and adds:
 *   - TVI-based 3-mode hybrid route selection   (Contribution 1)
 *   - Sigmoid smooth energy-aware weighting     (Contribution 2)
 */
class QTable : public saqmaodv::QTable
{
  public:
    /**
     * \param maxPaths  Max alternate routes per destination (default 3).
     * TVI thresholds and sigmoid params are static constexpr (see below).
     */
    explicit QTable (uint32_t maxPaths = 3);

    // ── TVI configuration (Contribution 1) ───────────────────────────────────
    static double GetTVIHigh () { return m_tviHigh; }
    static double GetTVILow  () { return m_tviLow;  }

    // ── Runtime mode / TVI queries ────────────────────────────────────────────
    TopologyMode GetCurrentMode () const; ///< O(1) mode decision
    std::string  GetModeName    () const; ///< "BYPASS"|"EXPLORE"|"GREEDY"
    double       GetTVI         () const; ///< Raw TVI value (Eq. H.1)

    // ── 3-mode route selection — replaces SelectEpsilonGreedy ────────────────
    /**
     * \brief Topology-aware hybrid route selection.
     *
     *   MODE_BYPASS  → out = primary  (no Q-table access)
     *   MODE_GREEDY  → out = argmax_Q for primary's destination
     *   MODE_EXPLORE → saqmaodv::QTable::SelectEpsilonGreedy()
     *
     * \return true if out was set; false only if Q-table is empty and
     *         mode is GREEDY (falls back to primary in that case).
     */
    bool SelectHybridRoute (const saqmaodv::RoutingTableEntry& primary,
                            saqmaodv::RoutingTableEntry&       out,
                            const saqmaodv::RoutingTable*      mainTable = nullptr);

    // ── Smooth energy weighting — replaces RecomputeAdaptiveRewardWeights ────
    /**
     * \brief Recompute reward weights using sigmoid function (Eq. H.2–H.5).
     *
     * Replaces saqmaodv::QTable::RecomputeAdaptiveRewardWeights().
     *
     * \param energyFraction  Node residual energy in [0, 1].
     */
    void RecomputeSmoothEnergyWeights (double energyFraction);

    static double GetSigmoidTheta () { return m_sigmaTheta; }
    static double GetSigmoidSigma () { return m_sigmaSigma; }

    /**
     * \brief Public sigmoid evaluation — useful for unit tests and logging.
     * \return s(E) ∈ (0,1)  from Eq. H.2.
     */
    double SigmoidActivation (double energyFraction) const;

  private:
    // ── TVI thresholds (static — no extra per-instance memory) ───────────────
    // Using static constexpr avoids sizeof(hsaqmaodv::QTable) > sizeof(saqmaodv::QTable)
    // which would corrupt routing protocol member layout (memory offset mismatch).
    static constexpr double m_tviHigh   = 3.0;  ///< TVI → MODE_BYPASS
    static constexpr double m_tviLow    = 1.0;  ///< TVI → MODE_GREEDY
    static constexpr double m_sigmaTheta = 0.30; ///< θ sigmoid centre
    static constexpr double m_sigmaSigma = 0.08; ///< σ sigmoid width

    // ── Private helpers ───────────────────────────────────────────────────────
    bool SelectGreedy (const saqmaodv::RoutingTableEntry& primary,
                       saqmaodv::RoutingTableEntry&       out,
                       const saqmaodv::RoutingTable*      mainTable) const;

    /// seqNoWindow length in seconds (fixed at 5.0 per paper §4.3).
    static constexpr double kSeqNoWindowSec = 5.0;
};

} // namespace hsaqmaodv
} // namespace ns3

#endif /* HSAQMAODV_QTABLE_H */
