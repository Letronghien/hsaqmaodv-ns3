#!/usr/bin/env python3
"""
fix2-sim-wiring.py — Fix remaining build errors:
  1. fanet-sim-hsa.cc:156  — 'hsVariant' not declared in scope
                             (VARIANT_BLOCK was inserted but std::string declaration missing)
  2. hsaqmaodv-routing-protocol.cc — ablation flags not wired to QTable (no wiring location found)

Usage: python3 ~/fix2-sim-wiring.py
"""
import os, re, shutil

NS3 = os.path.expanduser("~/ns-allinone-3.40/ns-3.40")

def bak(p):
    b = p + ".bak-fix2"
    if not os.path.exists(b): shutil.copy2(p, b)

def R(p):
    with open(p, encoding='utf-8') as f: return f.read()

def W(p, s):
    with open(p, 'w', encoding='utf-8') as f: f.write(s)

# ══════════════════════════════════════════════════════════════════════════════
# Fix 1 — fanet-sim-hsa.cc: ensure hsVariant variable is declared
# ══════════════════════════════════════════════════════════════════════════════
sim_path = f"{NS3}/scratch/fanet-sim-hsa.cc"
print(f"=== Fix 1: {os.path.basename(sim_path)} ===")

src = R(sim_path)
bak(sim_path)

# Show lines around where hsVariant appears
lines = src.split('\n')
for i, line in enumerate(lines):
    if 'hsVariant' in line:
        print(f"  Line {i+1}: {line[:100]}")

# Check: is the std::string hsVariant declaration present?
decl_present = bool(re.search(r'std\s*::\s*string\s+hsVariant', src))
addval_present = 'AddValue' in src and 'hsVariant' in src and \
                 bool(re.search(r'AddValue\s*\("hsVariant"', src))
print(f"  Declaration present: {decl_present}")
print(f"  AddValue present: {addval_present}")

if not decl_present:
    # Add declaration — find where other std::string or uint32_t variables are declared
    # Typical location: inside main() function, near hsTviHigh or numNodes
    # Try anchors in order
    inserted = False
    for anchor in [
        'uint32_t hsTviHigh',
        'uint32_t numNodes',
        'std::string protocol',
        'double simTime',
        'int seed',
        'uint32_t seed',
        'cmd.AddValue',
        'CommandLine cmd',
    ]:
        if anchor in src:
            idx = src.index(anchor)
            # Find start of line
            sol = src.rindex('\n', 0, idx) + 1
            indent = ' ' * (idx - sol)
            declaration = f'{indent}std::string hsVariant = "FULL"; // EXP5 ablation variant\n'
            src = src[:sol] + declaration + src[sol:]
            print(f"  Inserted 'std::string hsVariant' before '{anchor}'")
            inserted = True
            break
    if not inserted:
        print("  ERROR: could not find insertion point for hsVariant declaration")

if not addval_present:
    # Add cmd.AddValue for hsVariant
    for anchor in ['cmd.AddValue ("hsTviHigh"', 'cmd.AddValue("hsTviHigh"',
                   'cmd.AddValue ("hsTviLow"',  'cmd.Parse (argc']:
        if anchor in src:
            src = src.replace(anchor,
                'cmd.AddValue ("hsVariant", '
                '"Ablation variant: FULL/noTVI/noSigmoid/noCongestion/noDualQ", hsVariant);\n  '
                + anchor, 1)
            print(f"  Inserted cmd.AddValue(hsVariant) before '{anchor[:40]}'")
            break

W(sim_path, src)
print("  Written OK")

# ══════════════════════════════════════════════════════════════════════════════
# Fix 2 — hsaqmaodv-routing-protocol.cc: wire ablation flags to QTable
# ══════════════════════════════════════════════════════════════════════════════
rp_path = f"{NS3}/src/hsaqmaodv/model/hsaqmaodv-routing-protocol.cc"
print(f"\n=== Fix 2: {os.path.basename(rp_path)} ===")

src = R(rp_path)
bak(rp_path)

WIRING = """
  // Ablation flag wiring (fix2-sim-wiring.py)
  m_qtable.SetEnableTVI (!m_ablNoTVI);
  m_qtable.SetEnableDualQUpdate (!m_ablNoDualQ);
  m_qtable.SetSigmoidParams (m_ablSigTheta, m_ablSigSigma);"""

wiring_present = "SetEnableTVI" in src and "m_ablNoTVI" in src
print(f"  Wiring present: {wiring_present}")

if not wiring_present:
    # Look for SetTVIThresholds call to append after
    pat = re.compile(r'(m_qtable\.SetTVIThresholds\s*\([^)]+\)\s*;)')
    if pat.search(src):
        src = pat.sub(r'\1' + WIRING, src, count=1)
        print("  Wired after SetTVIThresholds call")
    else:
        # No SetTVIThresholds — find any m_qtable. call in DoInitialize / Start / NotifyInterfaceUp
        for hook in ["RoutingProtocol::DoInitialize",
                     "RoutingProtocol::Start",
                     "RoutingProtocol::NotifyInterfaceUp"]:
            if hook not in src:
                continue
            idx = src.index(hook)
            brace = src.index('{', idx)
            src = src[:brace+1] + "\n  m_qtable.SetTVIThresholds (m_tviHigh, m_tviLow);" + WIRING + src[brace+1:]
            print(f"  Wired in {hook}")
            break
        else:
            # Last resort: find first m_qtable. call
            m = re.search(r'm_qtable\.\w+\s*\(', src)
            if m:
                # find start of statement
                sol = src.rindex('\n', 0, m.start()) + 1
                src = src[:sol] + "  m_qtable.SetTVIThresholds (m_tviHigh, m_tviLow);" + WIRING + "\n" + src[sol:]
                print("  Wired before first m_qtable call (last resort)")
            else:
                print("  ERROR: no wiring location found at all")
else:
    print("  Wiring already present — no change")

W(rp_path, src)
print("  Written OK")

# ══════════════════════════════════════════════════════════════════════════════
print("""
=== Done ===
Build:
  cd ~/ns-allinone-3.40/ns-3.40
  ./ns3 build scratch/fanet-sim-hsa 2>&1 | grep 'error:' | head -30
""")
