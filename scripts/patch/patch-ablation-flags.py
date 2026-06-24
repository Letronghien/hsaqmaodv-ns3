#!/usr/bin/env python3
"""
patch-ablation-flags.py — Add ablation variant support to H-SAQMAODV
Patches 5 files:
  1. src/hsaqmaodv/model/hsaqmaodv-qtable.h          — EnableTVI + EnableDualQ setters
  2. src/hsaqmaodv/model/hsaqmaodv-qtable.cc          — implement flag behaviour
  3. src/hsaqmaodv/model/hsaqmaodv-routing-protocol.h — new member vars
  4. src/hsaqmaodv/model/hsaqmaodv-routing-protocol.cc — TypeId attrs + wiring to QTable
  5. scratch/fanet-sim-hsa.cc                         — --hsVariant param + logic

Usage (on server):
    cd ~/ns-allinone-3.40/ns-3.40
    python3 ~/patch-ablation-flags.py
    ./ns3 build scratch/fanet-sim-hsa 2>&1 | grep 'error:' | head -30

    # dry-run (show what will change without writing):
    python3 ~/patch-ablation-flags.py --dry-run

EXP5 ablation variants:
  FULL          — default, TviHigh=5, TviLow=2
  noTVI         — EnableTVI=false  → always EXPLORE (epsilon-greedy only)
  noSigmoid     — SigmoidSigma=0.001 → hard threshold behaviour
  noCongestion  — RewardW3=0.0     (already a TypeId attr)
  noDualQ       — EnableDualQUpdate=false
"""

import os, sys, re, shutil, argparse


def backup(path):
    bak = path + ".bak-ablation"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        print(f"    Backup -> {bak}")


def read_file(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


# =============================================================================
# 1. hsaqmaodv-qtable.h
# =============================================================================
def patch_qtable_h(src):
    if "SetEnableTVI" in src:
        print("    SKIP: already patched")
        return src

    # Add setter declarations after SetTVIThresholds
    OLD = "void SetTVIThresholds(uint32_t tviHigh, uint32_t tviLow);"
    NEW = (OLD + "\n"
           "  void SetEnableTVI(bool enable);          ///< noTVI ablation\n"
           "  void SetEnableDualQUpdate(bool enable);  ///< noDualQ ablation\n"
           "  void SetSigmoidParams(double theta, double sigma); ///< noSigmoid ablation")
    if OLD in src:
        src = src.replace(OLD, NEW, 1)
        print("    Inserted setter declarations after SetTVIThresholds")
    else:
        # Fallback: insert before last "};" (class closing)
        last = src.rfind("};")
        if last == -1:
            print("    ERROR: cannot find class closing in qtable.h")
            return src
        DECLS = ("\n  // ablation setters\n"
                 "  void SetEnableTVI(bool enable);\n"
                 "  void SetEnableDualQUpdate(bool enable);\n"
                 "  void SetSigmoidParams(double theta, double sigma);\n")
        src = src[:last] + DECLS + src[last:]
        print("    Inserted setter declarations before class closing (fallback)")

    # Add member variables near m_tviHigh
    if "m_tviEnabled" not in src:
        for target in ("uint32_t m_tviHigh", "double m_tviHigh", "int m_tviHigh"):
            if target in src:
                src = src.replace(target,
                    "bool     m_tviEnabled {true};    ///< ablation: enable TVI switching\n"
                    "  bool     m_dualQEnabled {true};  ///< ablation: enable dual Q-update\n"
                    "  " + target, 1)
                print("    Inserted m_tviEnabled / m_dualQEnabled member vars")
                break
        else:
            print("    WARN: m_tviHigh not found — member vars not added")
    return src


# =============================================================================
# 2. hsaqmaodv-qtable.cc
# =============================================================================
def patch_qtable_cc(src):
    if "SetEnableTVI" in src:
        print("    SKIP: already patched")
        return src

    # Insert setter implementations after SetTVIThresholds body
    NEW_FUNCS = """
void QTable::SetEnableTVI(bool enable)
{
  m_tviEnabled = enable;
}

void QTable::SetEnableDualQUpdate(bool enable)
{
  m_dualQEnabled = enable;
}

void QTable::SetSigmoidParams(double theta, double sigma)
{
  m_sigTheta = theta;
  m_sigSigma = sigma;
}

"""
    ANCHOR = "void QTable::SetTVIThresholds"
    if ANCHOR in src:
        start = src.index(ANCHOR)
        brace_open = src.index('{', start)
        depth, pos = 0, brace_open
        while pos < len(src):
            if src[pos] == '{':
                depth += 1
            elif src[pos] == '}':
                depth -= 1
                if depth == 0:
                    break
            pos += 1
        src = src[:pos+1] + NEW_FUNCS + src[pos+1:]
        print("    Inserted setter implementations after SetTVIThresholds")
    else:
        src = src.rstrip() + "\n" + NEW_FUNCS
        print("    WARN: SetTVIThresholds not found — appended setter impls at EOF")

    # Guard TVI mode comparisons with m_tviEnabled
    c1 = re.compile(r'if\s*\(\s*tvi\s*>=\s*m_tviHigh\s*\)')
    c2 = re.compile(r'else\s+if\s*\(\s*tvi\s*<=\s*m_tviLow\s*\)')
    if c1.search(src):
        src = c1.sub('if (m_tviEnabled && tvi >= m_tviHigh)', src)
        src = c2.sub('else if (m_tviEnabled && tvi <= m_tviLow)', src)
        print("    Guarded TVI comparisons with m_tviEnabled")
    else:
        print("    WARN: TVI comparison pattern not found — noTVI variant won't disable mode switching at runtime")

    # Guard dual-Q block with m_dualQEnabled
    DQ_MARKERS = [
        "// AODV-assisted dual Q",
        "// Dual Q update",
        "// dual-Q",
        "dualQUpdate(",
    ]
    guarded = False
    for marker in DQ_MARKERS:
        if marker in src:
            idx = src.index(marker)
            sol = src.rindex('\n', 0, idx) + 1
            # Find the block that follows (opening brace within next 200 chars)
            snippet = src[idx:idx+300]
            brace_rel = snippet.find('{')
            if brace_rel != -1:
                brace_abs = idx + brace_rel
                depth, pos = 0, brace_abs
                while pos < len(src):
                    if src[pos] == '{':
                        depth += 1
                    elif src[pos] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    pos += 1
                old_block = src[sol:pos+1]
                new_block = "  if (m_dualQEnabled)\n  {\n" + old_block + "\n  }"
                src = src[:sol] + new_block + src[pos+1:]
                print(f"    Wrapped dual-Q block at: '{marker}'")
                guarded = True
            break
    if not guarded:
        print("    WARN: no dual-Q block found — noDualQ variant will have no runtime effect (verify manually)")

    return src


# =============================================================================
# 3. hsaqmaodv-routing-protocol.h
# =============================================================================
def patch_rp_h(src):
    if "m_ablNoTVI" in src:
        print("    SKIP: already patched")
        return src

    NEW_MEMBERS = (
        "  // ablation flags (EXP5)\n"
        "  bool     m_ablNoTVI     {false}; ///< true = disable TVI mode switching\n"
        "  bool     m_ablNoDualQ   {false}; ///< true = disable dual Q-update\n"
        "  double   m_ablSigTheta  {0.3};   ///< sigmoid centre (noSigmoid: unchanged)\n"
        "  double   m_ablSigSigma  {0.08};  ///< sigmoid width  (noSigmoid: set ~0)\n"
        "  "
    )
    for target in ("uint32_t m_tviHigh", "double m_tviHigh",
                   "uint32_t m_tviLow",  "double m_lowEnergyThreshold"):
        if target in src:
            src = src.replace(target, NEW_MEMBERS + target, 1)
            print(f"    Inserted ablation member vars before {target}")
            return src

    print("    WARN: no suitable insertion point found in routing-protocol.h")
    return src


# =============================================================================
# 4. hsaqmaodv-routing-protocol.cc — TypeId attrs
# =============================================================================
NEW_TYPEID_ATTRS = """\
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
                   "Enable TVI mode switching (false=always EXPLORE, noTVI ablation)",
                   BooleanValue (true),
                   MakeBooleanAccessor (&RoutingProtocol::m_ablNoTVI),
                   MakeBooleanChecker ())
    .AddAttribute ("EnableDualQUpdate",
                   "Enable AODV-assisted dual Q-update (false=noDualQ ablation)",
                   BooleanValue (true),
                   MakeBooleanAccessor (&RoutingProtocol::m_ablNoDualQ),
                   MakeBooleanChecker ())
    .AddAttribute ("SigmoidTheta",
                   "Sigmoid centre for mode hysteresis (default 0.3)",
                   DoubleValue (0.3),
                   MakeDoubleAccessor (&RoutingProtocol::m_ablSigTheta),
                   MakeDoubleChecker<double> ())
    .AddAttribute ("SigmoidSigma",
                   "Sigmoid width for mode hysteresis (noSigmoid: set ~0.001)",
                   DoubleValue (0.08),
                   MakeDoubleAccessor (&RoutingProtocol::m_ablSigSigma),
                   MakeDoubleChecker<double> ())
"""

def patch_rp_cc_typeid(src):
    if "EnableTVI" in src:
        print("    SKIP TypeId attrs: already patched")
        return src

    # Anchors: insert after the last known attribute
    for anchor in ['"PeriodicAdaptInterval"', '"LowEnergyThreshold"',
                   '"SeqNoWindow"', '"Lambda"', '"RewardW3"']:
        if anchor not in src:
            continue
        idx = src.index(anchor)
        # Find end of this .AddAttribute(...) — walk to matching paren
        # The call ends at the last ')' before the next '.Add' or ';'
        search_from = idx
        paren_depth = 0
        pos = search_from
        found_open = False
        while pos < len(src):
            ch = src[pos]
            if ch == '(':
                paren_depth += 1
                found_open = True
            elif ch == ')':
                paren_depth -= 1
                if found_open and paren_depth == 0:
                    break
            pos += 1
        src = src[:pos+1] + "\n" + NEW_TYPEID_ATTRS + src[pos+1:]
        print(f"    Inserted TypeId attrs after {anchor}")
        return src

    # Fallback: before .AddConstructor
    if ".AddConstructor" in src:
        idx = src.index(".AddConstructor")
        src = src[:idx] + NEW_TYPEID_ATTRS + "    " + src[idx:]
        print("    Inserted TypeId attrs before .AddConstructor (fallback)")
        return src

    print("    WARN: no TypeId insertion point found")
    return src


WIRING_CODE = """
  // Ablation flag wiring (added by patch-ablation-flags.py)
  m_qtable.SetEnableTVI (!m_ablNoTVI);
  m_qtable.SetEnableDualQUpdate (!m_ablNoDualQ);
  m_qtable.SetSigmoidParams (m_ablSigTheta, m_ablSigSigma);
  m_qtable.SetTVIThresholds (m_tviHigh, m_tviLow);
"""

def patch_rp_cc_wiring(src):
    if "SetEnableTVI" in src:
        print("    SKIP wiring: already patched")
        return src

    # Replace existing SetTVIThresholds call
    pat = re.compile(r'm_qtable\.SetTVIThresholds\s*\([^)]+\)\s*;')
    if pat.search(src):
        src = pat.sub(WIRING_CODE.strip(), src, count=1)
        print("    Wired ablation flags (replaced SetTVIThresholds call)")
        return src

    # No SetTVIThresholds call — insert at lifecycle hook
    for hook in ["void RoutingProtocol::DoInitialize",
                 "void RoutingProtocol::NotifyInterfaceUp",
                 "void RoutingProtocol::Start"]:
        if hook in src:
            idx = src.index(hook)
            brace = src.index('{', idx)
            src = src[:brace+1] + "\n" + WIRING_CODE + src[brace+1:]
            print(f"    Wired ablation flags in {hook}")
            return src

    print("    WARN: no wiring location found")
    return src


# =============================================================================
# 5. scratch/fanet-sim-hsa.cc
# =============================================================================
VARIANT_BLOCK = r"""
  // ── EXP5 Ablation variant configuration ─────────────────────────────────
  if (hsVariant == "FULL" || hsVariant.empty ())
    {
      hsaqmaodv.Set ("TviHigh", UintegerValue (hsTviHigh));
      hsaqmaodv.Set ("TviLow",  UintegerValue (hsTviLow));
    }
  else if (hsVariant == "noTVI")
    {
      // Disable TVI mode switching => always epsilon-greedy EXPLORE
      hsaqmaodv.Set ("EnableTVI", BooleanValue (false));
    }
  else if (hsVariant == "noSigmoid")
    {
      // Replace sigmoid hysteresis with hard threshold
      hsaqmaodv.Set ("TviHigh",      UintegerValue (hsTviHigh));
      hsaqmaodv.Set ("TviLow",       UintegerValue (hsTviLow));
      hsaqmaodv.Set ("SigmoidSigma", DoubleValue (0.001));
    }
  else if (hsVariant == "noCongestion")
    {
      // Remove congestion reward term
      hsaqmaodv.Set ("TviHigh",  UintegerValue (hsTviHigh));
      hsaqmaodv.Set ("TviLow",   UintegerValue (hsTviLow));
      hsaqmaodv.Set ("RewardW3", DoubleValue (0.0));
    }
  else if (hsVariant == "noDualQ")
    {
      // Disable AODV-assisted dual Q-update
      hsaqmaodv.Set ("TviHigh",           UintegerValue (hsTviHigh));
      hsaqmaodv.Set ("TviLow",            UintegerValue (hsTviLow));
      hsaqmaodv.Set ("EnableDualQUpdate", BooleanValue (false));
    }
  else
    {
      NS_FATAL_ERROR ("Unknown --hsVariant=" << hsVariant
                      << "  valid: FULL noTVI noSigmoid noCongestion noDualQ");
    }
"""

def patch_sim_cc(src):
    if "hsVariant" in src:
        print("    SKIP: already patched")
        return src

    # 1. Variable declaration — before hsTviHigh
    VAR_INSERT = 'std::string hsVariant = "FULL"; // EXP5 ablation variant\n  '
    for anchor in ("uint32_t hsTviHigh", "double hsTviHigh"):
        if anchor in src:
            src = src.replace(anchor, VAR_INSERT + anchor, 1)
            print("    Inserted hsVariant variable declaration")
            break
    else:
        print("    WARN: hsTviHigh not found — inserting hsVariant near cmd.Parse")
        if "cmd.Parse" in src:
            idx = src.index("cmd.Parse")
            sol = src.rindex('\n', 0, idx) + 1
            src = src[:sol] + '  std::string hsVariant = "FULL";\n' + src[sol:]

    # 2. cmd.AddValue
    AV_ANCHOR = None
    for a in ('cmd.AddValue ("hsTviHigh"', 'cmd.AddValue("hsTviHigh"',
              'cmd.AddValue ("hsTviLow"',  'cmd.Parse'):
        if a in src:
            AV_ANCHOR = a
            break
    if AV_ANCHOR:
        src = src.replace(AV_ANCHOR,
            'cmd.AddValue ("hsVariant", '
            '"Ablation variant: FULL/noTVI/noSigmoid/noCongestion/noDualQ", hsVariant);\n  '
            + AV_ANCHOR, 1)
        print(f"    Inserted cmd.AddValue(hsVariant) before {AV_ANCHOR[:35]}")

    # 3. Variant logic after HsaqmaodvHelper instantiation
    HELPER = "HsaqmaodvHelper hsaqmaodv;"
    if HELPER in src:
        idx = src.index(HELPER)
        eol = src.index('\n', idx)
        # Skip any existing hsaqmaodv.Set lines
        pos = eol + 1
        while pos < len(src):
            line_end = src.find('\n', pos)
            if line_end == -1:
                break
            line = src[pos:line_end].strip()
            if line.startswith("hsaqmaodv.Set") or line.startswith("// "):
                pos = line_end + 1
            else:
                break
        src = src[:pos] + VARIANT_BLOCK + src[pos:]
        print("    Inserted variant logic after HsaqmaodvHelper")
    else:
        print("    WARN: 'HsaqmaodvHelper hsaqmaodv;' not found")
        for fb in ("Ipv4ListRoutingHelper", "internet.Install", "NodeContainer"):
            if fb in src:
                idx = src.index(fb)
                sol = src.rindex('\n', 0, idx) + 1
                src = src[:sol] + VARIANT_BLOCK + src[sol:]
                print(f"    Inserted variant logic before {fb} (fallback)")
                break

    return src


# =============================================================================
# Main
# =============================================================================
def main():
    ap = argparse.ArgumentParser(description="Patch H-SAQMAODV for EXP5 ablation variants")
    ap.add_argument("--ns3dir", default=os.path.expanduser("~/ns-allinone-3.40/ns-3.40"),
                    help="Path to ns-3.40 directory (default: ~/ns-allinone-3.40/ns-3.40)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would be patched without modifying files")
    args = ap.parse_args()

    NS3 = args.ns3dir
    FILES = {
        "qtable_h":  os.path.join(NS3, "src/hsaqmaodv/model/hsaqmaodv-qtable.h"),
        "qtable_cc": os.path.join(NS3, "src/hsaqmaodv/model/hsaqmaodv-qtable.cc"),
        "rp_h":      os.path.join(NS3, "src/hsaqmaodv/model/hsaqmaodv-routing-protocol.h"),
        "rp_cc":     os.path.join(NS3, "src/hsaqmaodv/model/hsaqmaodv-routing-protocol.cc"),
        "sim_cc":    os.path.join(NS3, "scratch/fanet-sim-hsa.cc"),
    }

    print("=" * 62)
    print("  patch-ablation-flags.py — EXP5 ablation support for HSAQMAODV")
    print(f"  NS3 dir  : {NS3}")
    print(f"  Dry-run  : {args.dry_run}")
    print("=" * 62)

    missing = [p for p in FILES.values() if not os.path.exists(p)]
    if missing:
        for p in missing:
            print(f"ERROR: not found: {p}")
        print("Aborting — verify --ns3dir")
        sys.exit(1)

    PATCH_PLAN = [
        ("qtable_h",  [patch_qtable_h]),
        ("qtable_cc", [patch_qtable_cc]),
        ("rp_h",      [patch_rp_h]),
        ("rp_cc",     [patch_rp_cc_typeid, patch_rp_cc_wiring]),
        ("sim_cc",    [patch_sim_cc]),
    ]

    for key, fns in PATCH_PLAN:
        path = FILES[key]
        print(f"\n[{key}]  {os.path.basename(path)}")
        content = read_file(path)
        for fn in fns:
            content = fn(content)
        if args.dry_run:
            print("    (dry-run — not written)")
        else:
            backup(path)
            write_file(path, content)
            print("    Written OK")

    print()
    print("=" * 62)
    if args.dry_run:
        print("  DRY-RUN complete — no files modified")
    else:
        print("  Patch complete.")
        print()
        print("  Build:")
        print(f"    cd {NS3}")
        print("    ./ns3 build scratch/fanet-sim-hsa 2>&1 | grep 'error:' | head -30")
        print()
        print("  Quick smoke test (should run without NS_FATAL):")
        BIN = os.path.join(NS3, "build/scratch/ns3.40-fanet-sim-hsa-optimized")
        for v in ["FULL", "noTVI", "noSigmoid", "noCongestion", "noDualQ"]:
            print(f"    {BIN} --protocol=HSAQMAODV --maxPaths=3 --seed=1 --numNodes=10 \\")
            print(f"        --scenario=TEST-{v} --hsVariant={v} --simTime=10 --csvFile=/tmp/test-{v}.csv")
        print()
        print("  Run EXP5 ablation:")
        print("    SEEDS=30 JOBS=4 bash ~/run-exp5-ablation.sh")
    print("=" * 62)


if __name__ == "__main__":
    main()
