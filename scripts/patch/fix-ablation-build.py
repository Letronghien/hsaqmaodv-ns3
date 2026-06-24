#!/usr/bin/env python3
"""
fix-ablation-build.py — Surgical fix for build errors after patch-ablation-flags.py
Fixes:
  1. hsaqmaodv-qtable.h      — ensure m_tviEnabled/m_dualQEnabled/m_sigTheta/m_sigSigma exist
  2. hsaqmaodv-routing-protocol.h — ensure m_tviHigh/m_tviLow/m_ablNoTVI/... exist as members
  3. hsaqmaodv-routing-protocol.cc — remove misplaced TypeId attrs, re-insert correctly

Usage: python3 ~/fix-ablation-build.py
"""

import os, sys, re, shutil

NS3 = os.path.expanduser("~/ns-allinone-3.40/ns-3.40")

FILES = {
    "qtable_h": f"{NS3}/src/hsaqmaodv/model/hsaqmaodv-qtable.h",
    "qtable_cc": f"{NS3}/src/hsaqmaodv/model/hsaqmaodv-qtable.cc",
    "rp_h":     f"{NS3}/src/hsaqmaodv/model/hsaqmaodv-routing-protocol.h",
    "rp_cc":    f"{NS3}/src/hsaqmaodv/model/hsaqmaodv-routing-protocol.cc",
}

def bak(path):
    b = path + ".bak-fix"
    if not os.path.exists(b):
        shutil.copy2(path, b)

def R(p): 
    with open(p, encoding='utf-8') as f: return f.read()

def W(p, s):
    with open(p, 'w', encoding='utf-8') as f: f.write(s)

# ── Show current state ────────────────────────────────────────────────────────
print("=== Diagnosing current state ===\n")

for k, p in FILES.items():
    if not os.path.exists(p):
        print(f"ERROR: {p} not found"); sys.exit(1)
    src = R(p)
    checks = {
        "qtable_h":  ["m_tviEnabled", "m_dualQEnabled", "m_sigTheta", "SetEnableTVI"],
        "qtable_cc": ["SetEnableTVI", "m_tviEnabled"],
        "rp_h":      ["m_tviHigh", "m_tviLow", "m_ablNoTVI", "m_ablNoDualQ"],
        "rp_cc":     ["EnableTVI", "EnableDualQUpdate", "m_tviHigh", "m_tviLow"],
    }
    for kw in checks[k]:
        status = "OK" if kw in src else "MISSING"
        print(f"  [{k}] {kw}: {status}")

print()

# ═══════════════════════════════════════════════════════════════════════════════
# FIX 1 — hsaqmaodv-qtable.h
# Add member vars at end of class (before final };)
# ═══════════════════════════════════════════════════════════════════════════════
print("=== Fix 1: hsaqmaodv-qtable.h ===")
src = R(FILES["qtable_h"])
bak(FILES["qtable_h"])

NEEDED_MEMBERS = {
    "m_tviEnabled":  "  bool     m_tviEnabled {true};    ///< ablation: enable TVI switching",
    "m_dualQEnabled":"  bool     m_dualQEnabled {true};  ///< ablation: enable dual Q-update",
    "m_sigTheta":    "  double   m_sigTheta {0.3};        ///< sigmoid centre",
    "m_sigSigma":    "  double   m_sigSigma {0.08};       ///< sigmoid width",
}
NEEDED_SETTERS = {
    "SetEnableTVI":       "  void SetEnableTVI(bool enable);",
    "SetEnableDualQUpdate":"  void SetEnableDualQUpdate(bool enable);",
    "SetSigmoidParams":   "  void SetSigmoidParams(double theta, double sigma);",
}

missing_members = {k: v for k, v in NEEDED_MEMBERS.items() if k not in src}
missing_setters = {k: v for k, v in NEEDED_SETTERS.items() if k not in src}

if missing_members or missing_setters:
    # Insert before last "};" in file
    insert_block = ""
    if missing_setters:
        insert_block += "\n  // ablation setters\n"
        insert_block += "\n".join(missing_setters.values()) + "\n"
    if missing_members:
        insert_block += "\n  // ablation member vars\n"
        insert_block += "\n".join(missing_members.values()) + "\n"

    last = src.rfind("};")
    if last == -1:
        print("  ERROR: cannot find class closing '};'")
    else:
        src = src[:last] + insert_block + src[last:]
        W(FILES["qtable_h"], src)
        print(f"  Added: {list(missing_members.keys()) + list(missing_setters.keys())}")
else:
    print("  All members/setters present — no change")

# ═══════════════════════════════════════════════════════════════════════════════
# FIX 2 — hsaqmaodv-routing-protocol.h
# Add m_tviHigh, m_tviLow, m_ablNoTVI, m_ablNoDualQ, m_ablSigTheta, m_ablSigSigma
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== Fix 2: hsaqmaodv-routing-protocol.h ===")
src = R(FILES["rp_h"])
bak(FILES["rp_h"])

NEEDED_RP_MEMBERS = {
    "m_tviHigh":    "  uint32_t m_tviHigh {5};          ///< TVI threshold BYPASS",
    "m_tviLow":     "  uint32_t m_tviLow {2};           ///< TVI threshold GREEDY",
    "m_ablNoTVI":   "  bool     m_ablNoTVI {false};     ///< ablation: disable TVI",
    "m_ablNoDualQ": "  bool     m_ablNoDualQ {false};   ///< ablation: disable dual Q",
    "m_ablSigTheta":"  double   m_ablSigTheta {0.3};    ///< ablation: sigmoid theta",
    "m_ablSigSigma":"  double   m_ablSigSigma {0.08};  ///< ablation: sigmoid sigma",
}

missing_rp = {k: v for k, v in NEEDED_RP_MEMBERS.items() if k not in src}
if missing_rp:
    insert_block = "\n  // TVI + ablation member vars\n" + "\n".join(missing_rp.values()) + "\n"
    last = src.rfind("};")
    if last == -1:
        print("  ERROR: cannot find class closing '};'")
    else:
        src = src[:last] + insert_block + src[last:]
        W(FILES["rp_h"], src)
        print(f"  Added: {list(missing_rp.keys())}")
else:
    print("  All members present — no change")

# ═══════════════════════════════════════════════════════════════════════════════
# FIX 3 — hsaqmaodv-routing-protocol.cc
# Clean up any misplaced TypeId attrs, then re-insert correctly
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== Fix 3: hsaqmaodv-routing-protocol.cc ===")
src = R(FILES["rp_cc"])
bak(FILES["rp_cc"])

NEW_TYPEID_ATTRS = """
    .AddAttribute ("TviHigh",
                   "TVI threshold for BYPASS mode (default 5)",
                   UintegerValue (5),
                   MakeUintegerAccessor (&RoutingProtocol::m_tviHigh),
                   MakeUintegerChecker<uint32_t> ())
    .AddAttribute ("TviLow",
                   "TVI threshold for GREEDY mode (default 2)",
                   UintegerValue (2),
                   MakeUintegerAccessor (&RoutingProtocol::m_tviLow),
                   MakeUintegerChecker<uint32_t> ())
    .AddAttribute ("EnableTVI",
                   "Enable TVI mode switching (false=noTVI ablation)",
                   BooleanValue (true),
                   MakeBooleanAccessor (&RoutingProtocol::m_ablNoTVI),
                   MakeBooleanChecker ())
    .AddAttribute ("EnableDualQUpdate",
                   "Enable AODV-assisted dual Q-update (false=noDualQ ablation)",
                   BooleanValue (true),
                   MakeBooleanAccessor (&RoutingProtocol::m_ablNoDualQ),
                   MakeBooleanChecker ())
    .AddAttribute ("SigmoidTheta",
                   "Sigmoid centre (default 0.3)",
                   DoubleValue (0.3),
                   MakeDoubleAccessor (&RoutingProtocol::m_ablSigTheta),
                   MakeDoubleChecker<double> ())
    .AddAttribute ("SigmoidSigma",
                   "Sigmoid width (noSigmoid: set ~0.001)",
                   DoubleValue (0.08),
                   MakeDoubleAccessor (&RoutingProtocol::m_ablSigSigma),
                   MakeDoubleChecker<double> ())"""

WIRING_CODE = """
  // Ablation flag wiring
  m_qtable.SetEnableTVI (!m_ablNoTVI);
  m_qtable.SetEnableDualQUpdate (!m_ablNoDualQ);
  m_qtable.SetSigmoidParams (m_ablSigTheta, m_ablSigSigma);
  m_qtable.SetTVIThresholds (m_tviHigh, m_tviLow);"""

# Step 3a: Remove any misplaced ablation attrs that got inserted wrong
# Look for the bad insertion at line 240 area — it's inside a TimeValue call
# Strategy: remove the entire NEW_TYPEID_ATTRS block if it appears, then re-insert correctly
ABLATION_MARKER_START = '.AddAttribute ("TviHigh"'
ABLATION_MARKER_END   = 'MakeDoubleChecker<double> ())'

if ABLATION_MARKER_START in src:
    # Find and remove the entire ablation attrs block
    start_idx = src.find(ABLATION_MARKER_START)
    # The block ends after the SigmoidSigma attribute closing paren
    # Find the last MakeDoubleChecker<double>()) after start_idx
    search = src[start_idx:]
    # Find end of SigmoidSigma block — look for the pattern ending the last attr
    # Each .AddAttribute ends with MakeXxxChecker<T>()) 
    # Find 2nd occurrence of MakeDoubleChecker (for SigmoidSigma)
    pos = 0
    count = 0
    while True:
        found = search.find('MakeDoubleChecker<double> ())', pos)
        if found == -1:
            break
        count += 1
        if count == 2:  # second one = end of SigmoidSigma
            end_idx = start_idx + found + len('MakeDoubleChecker<double> ())')
            # also eat the newline after
            if end_idx < len(src) and src[end_idx] == '\n':
                end_idx += 1
            break
        pos = found + 1
    else:
        # only one MakeDoubleChecker — fallback
        found = search.find('MakeDoubleChecker<double> ())')
        if found != -1:
            end_idx = start_idx + found + len('MakeDoubleChecker<double> ())')
        else:
            end_idx = start_idx  # can't find end, don't remove

    if end_idx > start_idx:
        removed = src[start_idx:end_idx]
        src = src[:start_idx] + src[end_idx:]
        print(f"  Removed misplaced ablation attrs block ({end_idx-start_idx} chars)")
    else:
        print("  Could not determine end of misplaced block — leaving as is")

# Step 3b: Insert attrs correctly — after last known TypeId attribute, before .AddConstructor
if ABLATION_MARKER_START not in src:
    # Find insertion point: after last .AddAttribute in TypeId chain
    # Look for PeriodicAdaptInterval or LowEnergyThreshold or SeqNoWindow
    inserted = False
    for anchor in ['"PeriodicAdaptInterval"', '"LowEnergyThreshold"', '"SeqNoWindow"', '"Lambda"', '"RewardW3"']:
        if anchor not in src:
            continue
        idx = src.index(anchor)
        # Walk forward to find the end of this .AddAttribute() call
        # It ends at the matching ) of MakeXxxChecker<T>())
        # Find MakeXxxChecker after anchor
        checker_pat = re.compile(r'Make\w+Checker[^)]*\(\)', re.DOTALL)
        m = checker_pat.search(src, idx)
        if not m:
            continue
        # Now find the closing ) of Make...() and then the outer )
        end_of_checker = m.end()
        # skip whitespace and find ) 
        pos = end_of_checker
        while pos < len(src) and src[pos] in ' \t\n':
            pos += 1
        if src[pos] == ')':
            pos += 1  # closing ) of .AddAttribute(...)
        src = src[:pos] + NEW_TYPEID_ATTRS + src[pos:]
        print(f"  Inserted TypeId attrs after {anchor}")
        inserted = True
        break

    if not inserted:
        # Last resort: before .AddConstructor
        if ".AddConstructor" in src:
            idx = src.index(".AddConstructor")
            src = src[:idx] + NEW_TYPEID_ATTRS + "\n    " + src[idx:]
            print("  Inserted TypeId attrs before .AddConstructor (last resort)")
        else:
            print("  ERROR: no TypeId insertion point found in routing-protocol.cc")
else:
    print("  TypeId attrs already present (after removal of bad ones)")

# Step 3c: Wire ablation flags to QTable
if "SetEnableTVI" not in src:
    # Insert wiring at DoInitialize or Start
    for hook in ["void RoutingProtocol::DoInitialize",
                 "void RoutingProtocol::NotifyInterfaceUp",
                 "void RoutingProtocol::Start"]:
        if hook in src:
            idx = src.index(hook)
            brace = src.index('{', idx)
            src = src[:brace+1] + WIRING_CODE + src[brace+1:]
            print(f"  Wired ablation flags in {hook}")
            break
    else:
        # Try after SetTVIThresholds call
        pat = re.compile(r'm_qtable\.SetTVIThresholds\s*\([^)]+\)\s*;')
        if pat.search(src):
            src = pat.sub(WIRING_CODE.strip(), src, count=1)
            print("  Wired ablation flags (replaced SetTVIThresholds call)")
        else:
            print("  WARN: no wiring location found")
else:
    print("  Wiring already present")

W(FILES["rp_cc"], src)
print("  Written OK")

# ═══════════════════════════════════════════════════════════════════════════════
# Done
# ═══════════════════════════════════════════════════════════════════════════════
print("""
=== Fix complete ===
Build:
  cd ~/ns-allinone-3.40/ns-3.40
  ./ns3 build scratch/fanet-sim-hsa 2>&1 | grep 'error:' | head -30
""")
