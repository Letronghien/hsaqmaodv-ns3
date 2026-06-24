# H-SAQMAODV: Hybrid Self-Adaptive Q-learning Multipath AODV

**NS-3.40 implementation** | FANET routing protocol | Q3 journal submission

## Overview

H-SAQMAODV extends SA-QMAODV with:
1. **TVI mode switching** — 3-mode (BYPASS/EXPLORE/GREEDY) based on Topology Volatility Index
2. **Sigmoid transition smoothing** — prevents oscillatory mode toggling
3. **Congestion-aware reward** — penalizes queue-saturated forwarding paths
4. **AODV-assisted dual Q-update** — supporting mechanism for route recovery

**Recommended deployment:** N=15–30 nodes, V=20–100 m/s (high-mobility FANET)

## Repository Structure

```
paper/          ← Paper generator (gen-paper-hsaqmaodv.js) + final docx
scripts/
  run/          ← Simulation run scripts
  plot/         ← Figure generation (matplotlib)
  patch/        ← NS-3 source patch scripts
results/
  *.csv         ← Simulation data (EXP-5b, EXP-9)
  figures/      ← Generated figures
hsaqmaodv-src/  ← NS-3 module source + fanet-sim.cc
notes/          ← Project notes, session logs
```

## Quick Start

```bash
# 1. Build
cd ~/ns-allinone-3.40-hsaqmaodv/ns-3.40
./ns3 build scratch/fanet-sim

# 2. Run EXP-5b (high-speed ablation)
bash scripts/run/run_ablation_highspeed.sh test   # 4 jobs to verify
bash scripts/run/run_ablation_highspeed.sh full   # 240 jobs

# 3. Run EXP-9 (sparse FANET)
bash scripts/run/run_sparse_dualq.sh test
bash scripts/run/run_sparse_dualq.sh full

# 4. Plot
python3 scripts/plot/plot_exp5b.py
python3 scripts/plot/hsa_plot_exp9.py

# 5. Rebuild paper
cd paper && node gen-paper-hsaqmaodv.js
```

## Key Results

| Metric | H-SAQMAODV vs AODV |
|--------|-------------------|
| Delay at V=50 m/s | -12% |
| Routing overhead | Comparable |
| PDR at N=15-30 | Competitive |
| TVI threshold sensitivity | Robust (15 combos tested) |

## Operating Regime

| Condition | Recommendation |
|-----------|---------------|
| N≥15, V=20-100 m/s | H-SAQMAODV (primary range) |
| N=10-14 | H-SAQMAODV or SA-QMAODV |
| N<10 | AODV or P-MAODV |
| N≥40 | Protocol-agnostic (MAC saturation) |
