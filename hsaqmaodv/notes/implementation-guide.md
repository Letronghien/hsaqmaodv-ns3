# H-SAQMAODV — Implementation Guide

## Overview

This guide walks through implementing H-SAQMAODV from scratch on top of the
existing SA-QMAODV NS-3 module. The key change is **one file**: `hsaqmaodv-qtable.cc`.
Everything else is wiring.

---

## Step 0: Prerequisites

- NS-3.40 installed and built
- SA-QMAODV running (`./ns3 run "fanet-sim --protocol=SAQMAODV"` works)
- Git repo synced (Windows → GitHub → Linux)

```bash
cd ~/saqmaodv-ns3
git pull
```

---

## Step 1: Run the Patch Scripts

```bash
cd paper1-hsaqmaodv
NS3_DIR=$HOME/ns-allinone-3.40/ns-3.40 bash scripts/patches/apply-hsaqmaodv-all.sh
```

This does:
1. Creates `$NS3_DIR/src/hsaqmaodv/` by copying SA-QMAODV source files
2. Replaces `hsaqmaodv-qtable.{h,cc}` with the new 3-mode implementation
3. Renames namespaces: `saqmaodv` → `hsaqmaodv` throughout
4. Patches `fanet-sim.cc` to add `HSAQMAODV` protocol option

---

## Step 2: Build

```bash
cd $NS3_DIR
./ns3 build 2>&1 | tail -20
```

Expected: no errors. Warnings about unused variables are OK.

### Common Build Errors

**`error: 'energy' is not a namespace`**
- Cause: ns-3.40 uses `ns3::` not `ns3::energy::`
- Fix: `sed -i 's/ns3::energy::/ns3::/g' src/hsaqmaodv/model/hsaqmaodv-routing-protocol.cc`

**`undefined reference to HsaqmaodvHelper`**
- Cause: helper file not copied or namespace not renamed
- Fix: Check `src/hsaqmaodv/helper/` — ensure `hsaqmaodv-helper.{h,cc}` exist
  and contain `namespace hsaqmaodv` not `namespace saqmaodv`

**`SetTVIThresholds` not found in helper**
- The routing-protocol must expose `SetTVIThresholds` as a method callable from helper.
- See §4 below for the wiring detail.

---

## Step 3: Smoke Test

```bash
# Quick single run — should complete without crash
$NS3_DIR/build/scratch/fanet-sim \
  --protocol=HSAQMAODV --maxPaths=3 \
  --numNodes=10 --simTime=60 --seed=1 \
  --hsTviHigh=8 --hsTviLow=1 \
  --mobility=GAUSS --enableEnergy=1 \
  --csvFile=/tmp/hs-smoke.csv

cat /tmp/hs-smoke.csv
```

Expected CSV row: `protocol=HSAQMAODV, deliveryRatio > 0`

---

## Step 4: The Core Logic (Code Walkthrough)

### 4.1 `hsaqmaodv-qtable.h` — What's New

Three new members vs. SA-QMAODV QTable:

```cpp
uint32_t    m_tviHigh;      // ΔSeq > this → MODE_BYPASS  (default: 8)
uint32_t    m_tviLow;       // ΔSeq < this → MODE_GREEDY  (default: 1)
QSwitchMode m_lastMode;     // Mode used in last selection
uint64_t    m_bypassCount, m_greedyCount, m_exploreCount;  // for Fig 6
```

And the new enum:
```cpp
enum QSwitchMode { MODE_BYPASS=0, MODE_GREEDY=1, MODE_EXPLORE=2 };
```

### 4.2 `SelectEpsilonGreedy()` — The Core

```cpp
bool QTable::SelectEpsilonGreedy(const RoutingTableEntry& primary,
                                 RoutingTableEntry& out,
                                 const RoutingTable* mainTable)
{
    uint32_t tvi = GetDeltaSeq();   // ΔSeq count in window

    // ── MODE_BYPASS ───────────────────────────────────────────────────────
    if (tvi > m_tviHigh) {
        m_lastMode = MODE_BYPASS;
        ++m_bypassCount;
        out = primary;
        return true;           // AODV-like: skip Q, use RREP-derived route
    }

    // Build Q-table candidate set
    auto cands = BuildCandidates(primary, mainTable);
    if (cands.empty()) { out = primary; return true; }

    // ── MODE_GREEDY ───────────────────────────────────────────────────────
    if (tvi < m_tviLow) {
        m_lastMode = MODE_GREEDY;
        ++m_greedyCount;
        auto best = std::max_element(cands.begin(), cands.end(),
            [](const QRecord& a, const QRecord& b){ return a.qValue < b.qValue; });
        out = best->rt;
        return true;           // Pure exploitation: ε = 0
    }

    // ── MODE_EXPLORE (ε-greedy, same as SA-QMAODV) ───────────────────────
    m_lastMode = MODE_EXPLORE;
    ++m_exploreCount;
    if (m_uniform->GetValue() < m_epsilon) {
        // Explore: random route
        uint32_t idx = m_uniform->GetInteger(0, cands.size()-1);
        out = cands[idx].rt;
    } else {
        // Exploit: best Q-value
        auto best = std::max_element(cands.begin(), cands.end(),
            [](const QRecord& a, const QRecord& b){ return a.qValue < b.qValue; });
        out = best->rt;
    }
    return true;
}
```

### 4.3 How TVI is Measured

Inherited from SA-QMAODV, unchanged:

```cpp
uint32_t QTable::GetDeltaSeq() const {
    PurgeSeqNoEvents();        // remove events older than m_seqNoWindow
    return m_seqEvents.size(); // count of SeqNo updates in window
}

void QTable::RecordSeqNoUpdate() {
    m_seqEvents.push_back(Simulator::Now());
}
```

`RecordSeqNoUpdate()` is called by the routing protocol each time it
processes a RREP with a fresher SeqNo for any destination.

### 4.4 Wiring TVI Thresholds from fanet-sim.cc

The helper must pass `hsTviHigh` and `hsTviLow` down to the QTable:

```cpp
// In HsaqmaodvHelper:
void HsaqmaodvHelper::SetTVIThresholds(uint32_t high, uint32_t low) {
    m_tviHigh = high;
    m_tviLow  = low;
}

// In HsaqmaodvHelper::Create():
Ptr<hsaqmaodv::RoutingProtocol> rp = ...;
rp->GetQTable()->SetTVIThresholds(m_tviHigh, m_tviLow);
```

---

## Step 5: Calibrating TVI Thresholds

Before running the full paper experiments, run the TVI sensitivity sweep:

```bash
FAMILIES="TVI" SEEDS=5 JOBS=8 bash scripts/run/run-paper1-experiments.sh
python3 scripts/plot/plot-paper1.py ~/results-paper1-*/merged.csv --outdir ./figures
```

Open `figures/fig2_tvi_heatmap.pdf`. The blue-bordered cell is the optimal
`(TVI_high, TVI_low)` pair. Update `HS_TVI_HIGH` and `HS_TVI_LOW` in the run
script, then re-run the full experiment suite.

**Expected optimal range** (from theory):
- `TVI_high` ∈ [5, 10] — moderate-to-high topology change rates
- `TVI_low`  = 1        — almost any SeqNo update disables pure greedy

---

## Step 6: Run All Experiments

```bash
# Full paper experiment suite (may take several hours)
FAMILIES="N S E L" SEEDS=10 JOBS=8 \
  HS_TVI_HIGH=8 HS_TVI_LOW=1 \
  bash scripts/run/run-paper1-experiments.sh

# Plot
python3 scripts/plot/plot-paper1.py ~/results-paper1-*/merged.csv --outdir ./figures
```

---

## Step 7: Expected Results

| Family | Expected finding |
|--------|-----------------|
| **TVI** | Heatmap shows clear optimal band; PDR ~2–5% above SA-QMAODV baseline at optimal thresholds |
| **N**   | H-SAQMAODV extends SA-QMAODV's lead to higher N (≥20 nodes), where SA degrades due to explore overhead |
| **S**   | H-SAQMAODV maintains PDR at higher speeds (≥25 m/s) where BYPASS mode activates |
| **E**   | H-SAQMAODV ≈ SA-QMAODV (energy mechanism unchanged; both beat AODV in hetero-battery) |
| **L**   | H-SAQMAODV marginally better under high load (EXPLORE → BYPASS reduces queue pressure) |

---

## Debugging Tips

**Q: MODE_BYPASS is 100% of the time**
→ TVI_high is too low for your scenario. Increase `--hsTviHigh` or lower UAV speed.

**Q: MODE_GREEDY is 100% of the time**
→ Network is very stable; either low speed or very few nodes. Normal at V=5 m/s.

**Q: H-SAQMAODV PDR ≈ AODV in all scenarios**
→ BYPASS mode is dominating. Check TVI distribution with `--verbose=1`.

**Q: H-SAQMAODV PDR ≈ SA-QMAODV everywhere**
→ TVI thresholds not effective — try narrower range (e.g., TVI_high=5, TVI_low=2).

---

## File Map

```
paper1-hsaqmaodv/
├── files/
│   ├── hsaqmaodv-qtable.h     ← THE core contribution (3-mode enum + counters)
│   └── hsaqmaodv-qtable.cc    ← SelectEpsilonGreedy() with TVI switching
├── scripts/
│   ├── patches/
│   │   ├── apply-hsaqmaodv-all.sh       ← Run this first
│   │   ├── apply-hsaqmaodv-module.py    ← Creates NS-3 module
│   │   └── apply-hsaqmaodv-fanet.py     ← Patches fanet-sim.cc
│   ├── run/
│   │   └── run-paper1-experiments.sh    ← All 5 experiment families
│   └── plot/
│       └── plot-paper1.py               ← All 6 paper figures
└── notes/
    └── implementation-guide.md          ← This file
```
