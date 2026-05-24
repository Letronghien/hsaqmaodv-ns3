#!/usr/bin/env python3
"""
apply-hsaqmaodv-fanet.py
─────────────────────────────────────────────────────────────────────────────
Step 2 of H-SAQMAODV NS-3 integration.

Patches fanet-sim.cc to add HSAQMAODV protocol support:
  - Adds #include "hsaqmaodv-helper.h"
  - Adds "HSAQMAODV" to protocol selection block
  - Wires SetTVIThresholds() from CLI args --hsTviHigh --hsTviLow
  - Adds modeBypass/modeGreedy/modeExplore columns to CSV output

Usage:
    NS3_DIR=/path/to/ns-3.40 python3 apply-hsaqmaodv-fanet.py
"""

import os, sys, re
from pathlib import Path

NS3_DIR  = Path(os.environ.get('NS3_DIR', Path.home() / 'ns-allinone-3.40/ns-3.40'))
FANET    = NS3_DIR / 'scratch' / 'fanet-sim.cc'

def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def info(msg):
    print(f"  [hsaqmaodv-fanet] {msg}")

if not FANET.exists():
    die(f"fanet-sim.cc not found at {FANET}")

text = FANET.read_text(encoding='utf-8')
original = text

# ─── 1. Add include if missing ───────────────────────────────────────────────
INCLUDE_SA = '#include "ns3/saqmaodv-helper.h"'
INCLUDE_HS = '#include "ns3/hsaqmaodv-helper.h"'
if INCLUDE_HS not in text:
    if INCLUDE_SA in text:
        text = text.replace(INCLUDE_SA, INCLUDE_SA + '\n' + INCLUDE_HS)
        info("Added hsaqmaodv-helper.h include")
    else:
        die(f"Cannot find anchor '{INCLUDE_SA}' in fanet-sim.cc")

# ─── 2. Add CLI arguments ────────────────────────────────────────────────────
HS_CLI = '''
  // H-SAQMAODV Topology-Aware Q-Switching thresholds
  uint32_t hsTviHigh = 8;
  uint32_t hsTviLow  = 1;
  cmd.AddValue ("hsTviHigh", "H-SAQMAODV TVI upper threshold (MODE_BYPASS)", hsTviHigh);
  cmd.AddValue ("hsTviLow",  "H-SAQMAODV TVI lower threshold (MODE_GREEDY)", hsTviLow);
'''
# Insert after SA CLI block
SA_CLI_ANCHOR = 'cmd.AddValue ("saW3"'
if HS_CLI.strip() not in text:
    if SA_CLI_ANCHOR in text:
        # Find end of that line
        idx = text.find(SA_CLI_ANCHOR)
        line_end = text.find('\n', idx) + 1
        text = text[:line_end] + HS_CLI + text[line_end:]
        info("Added --hsTviHigh / --hsTviLow CLI args")
    else:
        info(f"WARNING: Could not find '{SA_CLI_ANCHOR}' — skipping CLI args injection")

# ─── 3. Add HSAQMAODV to protocol selection block ────────────────────────────
# Pattern: find the SAQMAODV helper setup block and add HSAQMAODV after it
SA_PROTO_BLOCK = '''  if (protocol == "SAQMAODV") {
    SaqmaodvHelper saqHelper;'''

HS_PROTO_BLOCK = '''
  } else if (protocol == "HSAQMAODV") {
    ns3::hsaqmaodv::HsaqmaodvHelper hsHelper;
    hsHelper.SetTVIThresholds (hsTviHigh, hsTviLow);
    // Inherit all SA parameters
    hsHelper.Set ("Alpha0",         DoubleValue (saAlpha0));
    hsHelper.Set ("Gamma",          DoubleValue (saGamma));
    hsHelper.Set ("Epsilon0",       DoubleValue (saEpsilon0));
    hsHelper.Set ("Lambda",         DoubleValue (saLambda));
    hsHelper.Set ("SeqNoWindow",    TimeValue (Seconds (saSeqNoWin)));
    hsHelper.Set ("AdaptPeriod",    TimeValue (Seconds (saAdaptPeriod)));
    hsHelper.Set ("LowEThresh",     DoubleValue (saLowEThresh));
    hsHelper.Set ("W1",             DoubleValue (saW1));
    hsHelper.Set ("W2",             DoubleValue (saW2));
    hsHelper.Set ("W3",             DoubleValue (saW3));
    hsHelper.Set ("MaxPaths",       UintegerValue (maxPaths));
    internet.SetRoutingHelper (hsHelper);
'''

if 'protocol == "HSAQMAODV"' not in text:
    # Find the closing brace of SAQMAODV block
    # Strategy: insert HS block just before the final "} // end protocol" pattern
    # Look for the saqmaodv install end
    SA_CLOSE = 'internet.Install (nodes);'
    idx = text.rfind(SA_CLOSE)   # last occurrence — after all protocol blocks
    if idx == -1:
        info("WARNING: Could not find 'internet.Install (nodes)' anchor — skipping HSAQMAODV protocol block")
    else:
        # Walk back to find the protocol if-else chain closing brace
        # Simple approach: insert after last 'else if' block ending
        saqmaodv_if = text.find('protocol == "SAQMAODV"')
        if saqmaodv_if != -1:
            # Find next 'internet.SetRoutingHelper' after SAQMAODV block
            routing_set = text.find('internet.SetRoutingHelper', saqmaodv_if)
            if routing_set != -1:
                line_end = text.find('\n', routing_set) + 1
                # Find closing brace of that if block
                close_brace = text.find('\n  }', line_end)
                if close_brace != -1:
                    insert_at = close_brace + 4  # after "  }"
                    text = text[:insert_at] + ' else if (protocol == "HSAQMAODV") {\n' + \
                           '    ns3::hsaqmaodv::HsaqmaodvHelper hsHelper;\n' + \
                           '    hsHelper.SetTVIThresholds (hsTviHigh, hsTviLow);\n' + \
                           '    hsHelper.Set ("Alpha0",   DoubleValue (saAlpha0));\n' + \
                           '    hsHelper.Set ("Gamma",    DoubleValue (saGamma));\n' + \
                           '    hsHelper.Set ("Epsilon0", DoubleValue (saEpsilon0));\n' + \
                           '    hsHelper.Set ("Lambda",   DoubleValue (saLambda));\n' + \
                           '    hsHelper.Set ("W1", DoubleValue (saW1));\n' + \
                           '    hsHelper.Set ("W2", DoubleValue (saW2));\n' + \
                           '    hsHelper.Set ("W3", DoubleValue (saW3));\n' + \
                           '    hsHelper.Set ("MaxPaths", UintegerValue (maxPaths));\n' + \
                           '    internet.SetRoutingHelper (hsHelper);\n' + \
                           '  }' + text[insert_at:]
                    info("Injected HSAQMAODV protocol block")
                else:
                    info("WARNING: Could not find SAQMAODV block close — manual patch needed")
            else:
                info("WARNING: SetRoutingHelper not found after SAQMAODV")
        else:
            info("WARNING: SAQMAODV protocol block not found in fanet-sim.cc")

# ─── 4. Add CSV columns for mode stats ───────────────────────────────────────
# Find CSV header line and add modeBypass, modeGreedy, modeExplore columns
CSV_HEADER_ANCHOR = '"protocol,maxPaths,'
if 'modeBypass' not in text and CSV_HEADER_ANCHOR in text:
    idx = text.find(CSV_HEADER_ANCHOR)
    eol = text.find('"', idx + len(CSV_HEADER_ANCHOR))
    # Insert before closing quote of header string
    text = text[:eol] + ',modeBypass,modeGreedy,modeExplore' + text[eol:]
    info("Added modeBypass/modeGreedy/modeExplore to CSV header")

# ─── Write back ──────────────────────────────────────────────────────────────
if text != original:
    # Backup
    backup = FANET.with_suffix('.cc.bak.hsaqmaodv')
    backup.write_text(original, encoding='utf-8')
    FANET.write_text(text, encoding='utf-8')
    info(f"Patched fanet-sim.cc (backup: {backup.name})")
else:
    info("No changes needed (already patched?)")

print()
print("✓ fanet-sim.cc patched for HSAQMAODV")
print("  Next: cd $NS3_DIR && ./ns3 build")
