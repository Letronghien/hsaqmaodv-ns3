#!/usr/bin/env python3
"""
apply-saqmaodv-hybrid.py
════════════════════════════════════════════════════════════════════════════
Patches the saqmaodv NS-3 module to add H-SAQMAODV hybrid extensions
DIRECTLY into saqmaodv::QTable and RoutingProtocol.

This avoids creating a separate hsaqmaodv NS-3 module (which causes
shared-library linkage conflicts). Instead, "HSAQMAODV" in fanet-sim.cc
is simply SaqmaodvHelper with UseHybrid=true.

What this script adds to saqmaodv::QTable (saqmaodv-qtable.{h,cc}):
  ── Contribution 1: TVI 3-mode switching ──────────────────────────────
  • GetTVI()             — Eq. H.1: TVI = ΔSeq / window_sec
  • GetCurrentHybridMode() — BYPASS / EXPLORE / GREEDY
  • SelectHybridRoute()  — 3-mode route selection
  ── Contribution 2: Sigmoid smooth energy weighting ───────────────────
  • SigmoidActivation()  — Eq. H.2: s(E) = 1/(1+exp((E-θ)/σ))
  • RecomputeSmoothEnergyWeights() — Eq. H.3-H.5

What this script adds to saqmaodv RoutingProtocol:
  • UseHybrid attribute (bool, default false)
  • TVIHigh / TVILow / SigmoidTheta / SigmoidSigma attributes
  • When UseHybrid=true: calls SelectHybridRoute + RecomputeSmoothEnergyWeights

Usage (on VM):
    NS3_DIR=~/ns-allinone-3.40-hsaqmaodv/ns-3.40 \\
        python3 scripts/patches/apply-saqmaodv-hybrid.py
"""

import os, re, sys, shutil
from pathlib import Path

NS3_DIR = Path(os.environ.get("NS3_DIR",
               Path.home() / "ns-allinone-3.40-hsaqmaodv/ns-3.40"))

SA_MODEL = NS3_DIR / "src" / "saqmaodv" / "model"
QTABLE_H  = SA_MODEL / "saqmaodv-qtable.h"
QTABLE_CC = SA_MODEL / "saqmaodv-qtable.cc"
PROTO_CC  = SA_MODEL / "saqmaodv-routing-protocol.cc"
PROTO_H   = SA_MODEL / "saqmaodv-routing-protocol.h"

def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr); sys.exit(1)

def info(msg):
    print(f"  [hybrid-patch] {msg}")

def backup(p: Path):
    bak = p.with_suffix(p.suffix + ".bak-hybrid")
    if not bak.exists():
        shutil.copy2(p, bak)
        info(f"backup → {bak.name}")

if not NS3_DIR.exists():
    die(f"NS3_DIR not found: {NS3_DIR}")
for f in [QTABLE_H, QTABLE_CC, PROTO_CC, PROTO_H]:
    if not f.exists():
        die(f"{f} not found — run setup-from-scratch.sh first")

# ═══════════════════════════════════════════════════════════════════════════
# Step 1: Patch saqmaodv-qtable.h — add hybrid method declarations + members
# ═══════════════════════════════════════════════════════════════════════════
info("Patching saqmaodv-qtable.h ...")
backup(QTABLE_H)
text = QTABLE_H.read_text(encoding="utf-8")

HYBRID_H_MARKER = "// -------- H-SAQMAODV Hybrid Extensions"
if HYBRID_H_MARKER in text:
    info("  qtable.h already patched — skipping")
else:
    # Insert before private section (or before closing brace of class)
    ANCHOR = "  private:"
    HYBRID_DECL = f"""
  // -------- H-SAQMAODV Hybrid Extensions (Contributions 1 & 2) --------
  //
  // Contribution 1: Topology Volatility Indicator (TVI) 3-mode switching
  //   TVI = ΔSeq_count / seqNoWindow_sec                     (Eq. H.1)
  //   TVI > tviHigh → BYPASS  : primary route (AODV-like, reduce overhead)
  //   TVI < tviLow  → GREEDY  : argmax-Q (exploit stable topology)
  //   else          → EXPLORE : epsilon-greedy (SA-QMAODV default)
  //
  // Contribution 2: Sigmoid smooth energy weighting
  //   s(E) = 1/(1+exp((E-θ)/σ))                              (Eq. H.2)
  //   w3(E) = w3_hi + (w3_lo - w3_hi)*s(E)                  (Eq. H.3)
  //   Replaces hard 20% threshold → continuous, no routing instability
  //
  void   SetUseHybrid   (bool   useHybrid);
  bool   GetUseHybrid   () const {{ return m_useHybrid; }}
  void   SetTVIThresholds(double tviHigh, double tviLow);
  void   SetSigmoidParams(double theta,   double sigma);

  double GetTVI              () const;   // Raw TVI value (Eq. H.1)
  int    GetCurrentHybridMode() const;   // 0=BYPASS 1=EXPLORE 2=GREEDY

  /**
   * Topology-aware 3-mode route selection (Contribution 1).
   * Called instead of SelectEpsilonGreedy() when UseHybrid=true.
   */
  bool SelectHybridRoute (const RoutingTableEntry& primary,
                          RoutingTableEntry&        out,
                          const RoutingTable*       mainTable = nullptr);

  /**
   * Sigmoid smooth energy weighting (Contribution 2).
   * Called instead of RecomputeAdaptiveRewardWeights() when UseHybrid=true.
   */
  void RecomputeSmoothEnergyWeights (double energyFraction);

  /// Sigmoid activation s(E) from Eq. H.2 — public for logging/tests.
  double SigmoidActivation (double energyFraction) const;

"""
    PRIVATE_MEMBERS = """
    // ---- H-SAQMAODV hybrid parameters (UseHybrid=false by default) ------
    bool   m_useHybrid;      // false = SAQMAODV, true = HSAQMAODV
    double m_tviHigh;        // TVI threshold for BYPASS  (default 3.0)
    double m_tviLow;         // TVI threshold for GREEDY  (default 1.0)
    double m_sigmoidTheta;   // sigmoid centre θ           (default 0.30)
    double m_sigmoidSigma;   // sigmoid steepness σ        (default 0.08)
"""
    if ANCHOR in text:
        text = text.replace(ANCHOR, HYBRID_DECL + ANCHOR + PRIVATE_MEMBERS, 1)
        QTABLE_H.write_text(text, encoding="utf-8")
        info("  qtable.h patched ✓")
    else:
        die("Cannot find 'private:' anchor in saqmaodv-qtable.h")

# ═══════════════════════════════════════════════════════════════════════════
# Step 2: Patch saqmaodv-qtable.cc — add hybrid implementations
# ═══════════════════════════════════════════════════════════════════════════
info("Patching saqmaodv-qtable.cc ...")
backup(QTABLE_CC)
text = QTABLE_CC.read_text(encoding="utf-8")

HYBRID_CC_MARKER = "// ── H-SAQMAODV Hybrid Implementations"
if HYBRID_CC_MARKER in text:
    info("  qtable.cc already patched — skipping")
else:
    # Add hybrid member init to constructor
    # Find the constructor initializer list and add new members
    CTOR_SEARCH = "m_seqNoWindow(Seconds(5.0)),"
    CTOR_REPLACE = "m_seqNoWindow(Seconds(5.0)),\n      m_useHybrid(false),\n      m_tviHigh(3.0), m_tviLow(1.0),\n      m_sigmoidTheta(0.30), m_sigmoidSigma(0.08),"
    if CTOR_SEARCH in text:
        text = text.replace(CTOR_SEARCH, CTOR_REPLACE, 1)
        info("  constructor init extended")
    else:
        info("  WARNING: constructor anchor not found — add init manually if needed")

    # Append hybrid implementations before final namespace closing braces
    HYBRID_IMPL = """
// ══════════════════════════════════════════════════════════════════════════
// H-SAQMAODV Hybrid Implementations (Contribution 1 + 2)
// Added by apply-saqmaodv-hybrid.py
// ══════════════════════════════════════════════════════════════════════════

// ── Hybrid control ────────────────────────────────────────────────────────
void QTable::SetUseHybrid(bool useHybrid) { m_useHybrid = useHybrid; }

void QTable::SetTVIThresholds(double tviHigh, double tviLow)
{
    NS_ASSERT_MSG(tviLow  > 0.0,    "tviLow must be > 0");
    NS_ASSERT_MSG(tviHigh > tviLow, "tviHigh must be > tviLow");
    m_tviHigh = tviHigh;
    m_tviLow  = tviLow;
}

void QTable::SetSigmoidParams(double theta, double sigma)
{
    NS_ASSERT_MSG(sigma > 0.0, "sigma must be > 0");
    m_sigmoidTheta = theta;
    m_sigmoidSigma = sigma;
}

// ── Contribution 1: TVI ───────────────────────────────────────────────────
double QTable::GetTVI() const
{
    // Eq. H.1: TVI = ΔSeq_count / seqNoWindow_sec
    double window_sec = m_seqNoWindow.GetSeconds();
    if (window_sec <= 0.0) return 0.0;
    return static_cast<double>(GetDeltaSeq()) / window_sec;
}

int QTable::GetCurrentHybridMode() const
{
    double tvi = GetTVI();
    if (tvi > m_tviHigh) return 0; // BYPASS
    if (tvi < m_tviLow)  return 2; // GREEDY
    return 1;                       // EXPLORE
}

bool QTable::SelectHybridRoute(const RoutingTableEntry& primary,
                               RoutingTableEntry&        out,
                               const RoutingTable*       mainTable)
{
    int mode = GetCurrentHybridMode();
    NS_LOG_DEBUG("HSAQ SelectHybridRoute: TVI=" << GetTVI()
                 << " mode=" << (mode==0?"BYPASS":mode==2?"GREEDY":"EXPLORE")
                 << " dst=" << primary.GetDestination());
    switch (mode)
    {
    case 0: // BYPASS — topology too dynamic, skip Q-table
        NS_LOG_DEBUG("HSAQ BYPASS → primary nh=" << primary.GetNextHop());
        out = primary;
        return true;

    case 2: // GREEDY — exploit best Q-value (epsilon=0)
        {
            double savedEps = m_epsilon;
            m_epsilon = 0.0;
            bool ok = SelectEpsilonGreedy(primary, out, mainTable);
            m_epsilon = savedEps;
            return ok;
        }

    default: // EXPLORE — standard SA-QMAODV epsilon-greedy
        return SelectEpsilonGreedy(primary, out, mainTable);
    }
}

// ── Contribution 2: Sigmoid smooth energy weighting ───────────────────────
double QTable::SigmoidActivation(double energyFraction) const
{
    // Eq. H.2: s(E) = 1 / (1 + exp((E - θ) / σ))
    // As E drops below θ, s(E) → 1 activating low-energy weighting smoothly
    double exponent = (energyFraction - m_sigmoidTheta) / m_sigmoidSigma;
    return 1.0 / (1.0 + std::exp(exponent));
}

void QTable::RecomputeSmoothEnergyWeights(double energyFraction)
{
    // Eq. H.3-H.5 (smooth, continuous — no hard flip at 20%)
    constexpr double w2Hi = 0.40, w3Hi = 0.10, w3Lo = 0.80;
    double s  = SigmoidActivation(energyFraction);
    double w3 = w3Hi + (w3Lo - w3Hi) * s;             // Eq. H.3
    double w2 = w2Hi * (1.0 - s);                      // Eq. H.4
    double w1 = 1.0 - w2 - w3;                         // Eq. H.5

    w1 = std::max(0.0, std::min(1.0, w1));
    w2 = std::max(0.0, std::min(1.0, w2));
    w3 = std::max(0.0, std::min(1.0, w3));

    // SetRewardWeights also updates m_w1Normal/w2Normal/w3Normal
    SetRewardWeights(w1, w2, w3);
    NS_LOG_DEBUG("HSAQ smooth weights: E=" << energyFraction
                 << " s=" << s << " w=(" << w1 << "," << w2 << "," << w3 << ")");
}

"""
    # Insert before last closing brace of namespace saqmaodv
    # Find "} // namespace saqmaodv" or similar
    ns_close = re.search(r'\n} // namespace saqmaodv\n} // namespace ns3', text)
    if ns_close:
        idx = ns_close.start()
        text = text[:idx] + "\n" + HYBRID_IMPL + text[idx:]
        QTABLE_CC.write_text(text, encoding="utf-8")
        info("  qtable.cc patched ✓")
    else:
        # Try appending before last two closing braces
        text = text.rstrip() + "\n" + HYBRID_IMPL + "\n} // namespace saqmaodv\n} // namespace ns3\n"
        QTABLE_CC.write_text(text, encoding="utf-8")
        info("  qtable.cc patched (appended) ✓")

# ═══════════════════════════════════════════════════════════════════════════
# Step 3: Patch saqmaodv-routing-protocol.cc — wire UseHybrid into routing
# ═══════════════════════════════════════════════════════════════════════════
info("Patching saqmaodv-routing-protocol.cc ...")
backup(PROTO_CC)
text = PROTO_CC.read_text(encoding="utf-8")

HYBRID_PROTO_MARKER = "// H-SAQMAODV: UseHybrid attribute"
if HYBRID_PROTO_MARKER in text:
    info("  routing-protocol.cc already patched — skipping")
else:
    # 3a. Add UseHybrid / TVI / sigmoid to GetTypeId() attribute list
    # Anchor: the last .AddAttribute before the closing of TypeId chain
    TYPEID_ANCHOR = '.AddAttribute ("PeriodicAdaptInterval"'
    TYPEID_EXTRA = '''
                  // ── H-SAQMAODV Hybrid Extensions ──────────────────────────
                  // H-SAQMAODV: UseHybrid attribute
                  .AddAttribute ("UseHybrid",
                                 "Enable H-SAQMAODV TVI 3-mode switching + sigmoid energy weights",
                                 BooleanValue (false),
                                 MakeBooleanAccessor (&RoutingProtocol::SetUseHybrid,
                                                      &RoutingProtocol::GetUseHybrid),
                                 MakeBooleanChecker ())
                  .AddAttribute ("TVIHigh",
                                 "TVI upper threshold for MODE_BYPASS (default 3.0)",
                                 DoubleValue (3.0),
                                 MakeDoubleAccessor (&RoutingProtocol::SetTVIHigh),
                                 MakeDoubleChecker<double> (0.0, 100.0))
                  .AddAttribute ("TVILow",
                                 "TVI lower threshold for MODE_GREEDY (default 1.0)",
                                 DoubleValue (1.0),
                                 MakeDoubleAccessor (&RoutingProtocol::SetTVILow),
                                 MakeDoubleChecker<double> (0.0, 100.0))
                  .AddAttribute ("SigmoidTheta",
                                 "Sigmoid centre θ for smooth energy weighting (default 0.30)",
                                 DoubleValue (0.30),
                                 MakeDoubleAccessor (&RoutingProtocol::SetSigmoidTheta),
                                 MakeDoubleChecker<double> (0.0, 1.0))
                  .AddAttribute ("SigmoidSigma",
                                 "Sigmoid steepness σ for smooth energy weighting (default 0.08)",
                                 DoubleValue (0.08),
                                 MakeDoubleAccessor (&RoutingProtocol::SetSigmoidSigma),
                                 MakeDoubleChecker<double> (0.001, 1.0))
'''
    if TYPEID_ANCHOR in text:
        idx = text.find(TYPEID_ANCHOR)
        # Insert BEFORE this anchor
        text = text[:idx] + TYPEID_EXTRA + text[idx:]
        info("  GetTypeId() attributes added")
    else:
        info("  WARNING: TypeId anchor not found — attributes NOT added")

    # 3b. Replace SelectEpsilonGreedy calls with hybrid wrapper
    # Pattern: m_qtable.SelectEpsilonGreedy(... → conditional call
    old_sel = "m_qtable.SelectEpsilonGreedy ("
    new_sel = ("(m_qtable.GetUseHybrid ()"
               " ? m_qtable.SelectHybridRoute ("
               " : m_qtable.SelectEpsilonGreedy (")
    if old_sel in text:
        n = text.count(old_sel)
        text = text.replace(old_sel, new_sel)
        info(f"  SelectEpsilonGreedy → hybrid wrapper ({n} occurrence(s))")
    else:
        info("  WARNING: SelectEpsilonGreedy call not found")

    # 3c. Replace RecomputeAdaptiveRewardWeights with hybrid wrapper
    old_rw = "m_qtable.RecomputeAdaptiveRewardWeights ("
    new_rw = ("(m_qtable.GetUseHybrid ()"
              " ? m_qtable.RecomputeSmoothEnergyWeights ("
              " : m_qtable.RecomputeAdaptiveRewardWeights (")
    if old_rw in text:
        n = text.count(old_rw)
        text = text.replace(old_rw, new_rw)
        info(f"  RecomputeAdaptiveRewardWeights → hybrid wrapper ({n} occurrence(s))")
    else:
        info("  WARNING: RecomputeAdaptiveRewardWeights call not found")

    PROTO_CC.write_text(text, encoding="utf-8")
    info("  routing-protocol.cc patched ✓")

# ═══════════════════════════════════════════════════════════════════════════
# Step 4: Patch saqmaodv-routing-protocol.h — add accessor declarations
# ═══════════════════════════════════════════════════════════════════════════
info("Patching saqmaodv-routing-protocol.h ...")
backup(PROTO_H)
text = PROTO_H.read_text(encoding="utf-8")

HYBRID_H_PROTO_MARKER = "void SetUseHybrid"
if HYBRID_H_PROTO_MARKER in text:
    info("  routing-protocol.h already patched — skipping")
else:
    PROTO_ANCHOR = "  void Start ();"
    PROTO_EXTRA = """
  // ── H-SAQMAODV hybrid attribute accessors ──────────────────────────────
  void SetUseHybrid   (bool v)   { m_qtable.SetUseHybrid(v); }
  bool GetUseHybrid   ()  const  { return m_qtable.GetUseHybrid(); }
  void SetTVIHigh     (double v) { m_qtable.SetTVIThresholds(v, m_qtable.GetTVILow()); }
  void SetTVILow      (double v) { m_qtable.SetTVIThresholds(m_qtable.GetTVIHigh(), v); }
  void SetSigmoidTheta(double v) { m_qtable.SetSigmoidParams(v, m_qtable.GetSigmoidSigma()); }
  void SetSigmoidSigma(double v) { m_qtable.SetSigmoidParams(m_qtable.GetSigmoidTheta(), v); }

"""
    if PROTO_ANCHOR in text:
        text = text.replace(PROTO_ANCHOR, PROTO_EXTRA + PROTO_ANCHOR, 1)
        PROTO_H.write_text(text, encoding="utf-8")
        info("  routing-protocol.h patched ✓")
    else:
        info("  WARNING: 'void Start()' anchor not found in routing-protocol.h")

# ═══════════════════════════════════════════════════════════════════════════
# We also need GetTVILow/GetTVIHigh/GetSigmoidTheta/GetSigmoidSigma in qtable.h
# Add them alongside SetTVIThresholds/SetSigmoidParams
# ═══════════════════════════════════════════════════════════════════════════
text_h = QTABLE_H.read_text(encoding="utf-8")
if "GetTVILow" not in text_h:
    text_h = text_h.replace(
        "void   SetTVIThresholds(double tviHigh, double tviLow);",
        "void   SetTVIThresholds(double tviHigh, double tviLow);\n"
        "  double GetTVIHigh()     const { return m_tviHigh; }\n"
        "  double GetTVILow()      const { return m_tviLow;  }\n"
        "  void   SetSigmoidParams(double theta,   double sigma);\n"
        "  double GetSigmoidTheta()const { return m_sigmoidTheta; }\n"
        "  double GetSigmoidSigma()const { return m_sigmoidSigma; }"
    )
    # Remove duplicate SetSigmoidParams
    text_h = text_h.replace(
        "  void   SetSigmoidParams(double theta,   double sigma);\n"
        "  double GetSigmoidTheta()const { return m_sigmoidTheta; }\n"
        "  double GetSigmoidSigma()const { return m_sigmoidSigma; }\n"
        "  double GetTVI              () const;",
        "  double GetTVI              () const;"
    )
    QTABLE_H.write_text(text_h, encoding="utf-8")
    info("  Added GetTVI*/GetSigmoid* accessors to qtable.h")

print()
print("✓  saqmaodv hybrid patch complete!")
print("   SAQMAODV module now supports UseHybrid=true for HSAQMAODV behaviour.")
print()
print("Next steps:")
print("  1. Update fanet-sim.cc (already done in project src/)")
print("  2. cd $NS3_DIR && ./ns3 build")
print("  3. Run smoke test with --protocol=HSAQMAODV")
