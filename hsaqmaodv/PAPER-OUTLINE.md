# Paper 1 — H-SAQMAODV: Outline

**Tên đề xuất:**
> "H-SAQMAODV: A Topology-Aware Hybrid Q-Learning Routing Protocol for Energy-Heterogeneous FANETs"

**Target:** IEEE Access / Drones (MDPI) / Computer Networks

---

## Abstract (draft)

Q-learning-based routing protocols for Flying Ad-hoc Networks (FANETs) suffer from
a fundamental limitation: exploration overhead degrades packet delivery ratio when
network topology changes faster than the Q-table can converge. We propose H-SAQMAODV,
which extends SA-QMAODV with a topology-aware Q-switching mechanism that monitors
the rate of destination sequence number updates (ΔSeq) and dynamically selects one
of three routing modes: bypass (AODV-like), greedy exploitation, or ε-greedy
exploration. Simulation results in NS-3.40 show that H-SAQMAODV outperforms AODV
by X% in PDR across N=10–30 UAVs and speed 15–30 m/s, while maintaining SA-QMAODV's
energy-aware advantage in heterogeneous battery scenarios.

---

## 1. Introduction

- FANET routing challenges: high mobility, energy constraints
- Q-learning routing gap: convergence vs. topology change rate
- SA-QMAODV limitation: always explores, even when network is chaotic
- Contribution: 3-mode hybrid switching using ΔSeq signal already in SA framework
- Paper structure

## 2. Related Work

### 2.1 Multipath AODV variants
- AOMDV, PMAODV

### 2.2 Q-learning routing for FANET
- QMAODV, SA-QMAODV (prior work)
- QL-AODV (Future Internet 2025)
- HQA (ScienceDirect 2025) ← direct inspiration, cite

### 2.3 Hybrid routing approaches
- Protocols that switch between reactive and proactive

### 2.4 Gap
- HQA uses Bayesian evaluator (external component)
- H-SAQMAODV uses ΔSeq (internal SA signal) → simpler, more integrated

## 3. System Model

### 3.1 Network model
- 3D FANET, Gauss-Markov mobility
- IEEE 802.11, energy model

### 3.2 Problem formulation
- Maximize PDR subject to energy constraints
- Topology volatility metric: ΔSeq rate

## 4. H-SAQMAODV Protocol Design

### 4.1 SA-QMAODV background (brief recap)
- Adaptive ε, α, reward weights
- ΔSeq tracking (§4.3 of base paper)

### 4.2 Topology Volatility Indicator (TVI)
- TVI = ΔSeq / seqNoWindow   (normalized rate)
- Why ΔSeq is a good proxy for topology change rate
- Thresholds: TVI_high, TVI_low (tunable)

### 4.3 Three-Mode Q-Switching (core contribution)

**MODE_BYPASS** (TVI > TVI_high):
- Network too dynamic for Q-learning to be reliable
- Skip SelectEpsilonGreedy, return primary route directly
- Rationale: AODV's fresh route discovery beats stale Q-values

**MODE_GREEDY** (TVI < TVI_low):
- Network stable, Q-values have converged
- Select route with highest Q-value (ε = 0)
- Rationale: no need to explore when we know the best route

**MODE_EXPLORE** (TVI_low ≤ TVI ≤ TVI_high):
- Sweet spot: Q-learning can learn and improve
- Standard ε-greedy as in SA-QMAODV

### 4.4 Integration with SA adaptive mechanisms
- ε adaptation still runs in background (helps during mode transitions)
- α adaptation continues (important for MODE_EXPLORE accuracy)
- Reward weight adaptation unchanged

### 4.5 Complexity analysis
- O(1) overhead per packet (just compare ΔSeq count)
- Same memory as SA-QMAODV

## 5. Performance Evaluation

### 5.1 Simulation setup
- NS-3.40, Gauss-Markov 3D, IEEE 802.11
- Area: 1000×1000×300 m³
- Parameters: Table I

### 5.2 Protocols compared
| Protocol | Description |
|---|---|
| AODV | Baseline reactive |
| AOMDV-3 | Deterministic multipath |
| QMAODV-3 | Q-learning multipath |
| SAQMAODV-3 | Self-adaptive Q (prior work) |
| **H-SAQMAODV-3** | **Proposed** |

### 5.3 Threshold sensitivity (Family TVI)
- Sweep TVI_high ∈ {3,5,8,10,15}, TVI_low ∈ {0,1,2}
- Find optimal thresholds → use in all subsequent experiments

### 5.4 Effect of node density (Family N)
- N ∈ {5,8,10,15,20,25,30}
- Key result: H-SAQMAODV should win where SAQMAODV loses (N>20)

### 5.5 Effect of mobility (Family S)
- Speed ∈ {5,10,15,20,25,30,50} m/s
- Key result: H-SAQMAODV extends winning range to higher speeds

### 5.6 Effect of traffic load (Family L)
- pktInterval ∈ {1.0, 0.5, 0.25, 0.1, 0.05}

### 5.7 Heterogeneous battery scenario
- E0 ∈ {10,20,30,50} J
- H-SAQMAODV should match or exceed SAQMAODV (energy mechanism unchanged)

### 5.8 Discussion
- When does H-SAQMAODV win over SA-QMAODV?
- Trade-offs: MODE_BYPASS loses Q-learning benefit when topology stabilizes quickly

## 6. Conclusion

- H-SAQMAODV bridges the gap between Q-learning optimality and AODV robustness
- ΔSeq as topology volatility indicator: lightweight, no external component
- Future work: combine with queue-aware reward (Paper 2)

---

## Key Figures (planned)

1. Fig 1: System architecture / protocol state machine (3 modes)
2. Fig 2: TVI threshold sensitivity (heatmap PDR vs TVI_high × TVI_low)
3. Fig 3: PDR vs N — H-SAQMAODV vs SAQMAODV vs AODV
4. Fig 4: PDR vs Speed
5. Fig 5: PDR vs E0 (hetero-battery)
6. Fig 6: Mode distribution over time (pie/bar: % time in each mode)

---

## Key Tables

- Table I: Simulation parameters
- Table II: Protocol comparison summary
- Table III: Overhead comparison (control packets)
