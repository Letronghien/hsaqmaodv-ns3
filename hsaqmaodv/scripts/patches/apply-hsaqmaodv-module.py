#!/usr/bin/env python3
"""
apply-hsaqmaodv-module.py
─────────────────────────────────────────────────────────────────────────────
Step 1 of H-SAQMAODV NS-3 integration.

Creates  $NS3_DIR/src/hsaqmaodv/  and wires it into the NS-3 build system.

What this script does (in order):
  1. Copy SA-QMAODV source files into src/hsaqmaodv/, renaming saqmaodv→hsaqmaodv
  2. Copy H-SAQMAODV Q-table (hsaqmaodv-qtable.{h,cc}) — the new contribution
  3. Patch namespace/includes in all copied files
  4. CRITICAL: Replace SelectEpsilonGreedy() → SelectHybridRoute() in the
     routing protocol, and RecomputeAdaptiveRewardWeights() →
     RecomputeSmoothEnergyWeights(), so the new logic is actually called.
  5. Write CMakeLists.txt (links libsaqmaodv as dependency)
  6. Register hsaqmaodv in top-level NS-3 CMakeLists.txt

Usage:
    NS3_DIR=/path/to/ns-3.40 python3 apply-hsaqmaodv-module.py

Prerequisites:
    - NS-3 3.40 installed at NS3_DIR
    - saqmaodv module already present (run setup-from-scratch.sh first)
    - hsaqmaodv-qtable.{h,cc} present in FILES_DIR (project files/)
"""

import os, sys, shutil, re
from pathlib import Path

NS3_DIR   = Path(os.environ.get('NS3_DIR', Path.home() / 'ns-allinone-3.40/ns-3.40'))
PROJ_DIR  = Path(__file__).resolve().parents[3]   # saqmaodv-ns3/ root

SRC_SA    = NS3_DIR  / 'src' / 'saqmaodv'
DST_HS    = NS3_DIR  / 'src' / 'hsaqmaodv'
FILES_DIR = PROJ_DIR / 'files'   # canonical location of hsaqmaodv-qtable.{h,cc}

def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def info(msg):
    print(f"  [hsaqmaodv-module] {msg}")

# ─── Sanity checks ────────────────────────────────────────────────────────────
if not NS3_DIR.exists():
    die(f"NS3_DIR not found: {NS3_DIR}")
if not SRC_SA.exists():
    die(f"saqmaodv module not found at {SRC_SA}\n"
        f"  → Run setup-from-scratch.sh first (installs AODV/PMAODV/QMAODV/SAQMAODV)")
if not (FILES_DIR / 'hsaqmaodv-qtable.h').exists():
    die(f"hsaqmaodv-qtable.h not found in {FILES_DIR}\n"
        f"  → Make sure project files/ directory is up to date (git pull)")

# ─── Step 1: Create module directory tree ────────────────────────────────────
info(f"Creating {DST_HS}")
for sub in ['model', 'helper', 'doc']:
    (DST_HS / sub).mkdir(parents=True, exist_ok=True)

# ─── Step 2: Copy shared SA-QMAODV files (all except q-table) ────────────────
# We reuse: rtable, rqueue, packet, routing-protocol, helper
# The routing-protocol is the one that calls SelectEpsilonGreedy() — we will
# patch that in Step 4 below.
SA_SHARED = [
    'model/saqmaodv-rtable.h',
    'model/saqmaodv-rtable.cc',
    'model/saqmaodv-rqueue.h',
    'model/saqmaodv-rqueue.cc',
    'model/saqmaodv-packet.h',
    'model/saqmaodv-packet.cc',
    'model/saqmaodv-routing-protocol.h',
    'model/saqmaodv-routing-protocol.cc',
    'helper/saqmaodv-helper.h',
    'helper/saqmaodv-helper.cc',
]

for rel in SA_SHARED:
    src = SRC_SA / rel
    if not src.exists():
        info(f"  WARNING: {rel} not found in saqmaodv — skipping")
        continue
    dst_name = Path(rel).name.replace('saqmaodv', 'hsaqmaodv')
    dst      = DST_HS / Path(rel).parent / dst_name
    shutil.copy2(src, dst)
    info(f"  copied  {rel} → {dst.name}")

# ─── Step 3: Copy H-SAQMAODV Q-table (the new contributions) ─────────────────
for fname in ['hsaqmaodv-qtable.h', 'hsaqmaodv-qtable.cc']:
    src = FILES_DIR / fname
    dst = DST_HS / 'model' / fname
    shutil.copy2(src, dst)
    info(f"  copied  {fname}  (H-SAQMAODV contribution)")

# ─── Step 4: Patch namespace / includes in all copied files ──────────────────
def patch_namespace(path: Path):
    """Rename saqmaodv→hsaqmaodv in namespace declarations and includes,
    but preserve the saqmaodv:: type references in hsaqmaodv-qtable.{h,cc}
    (those files deliberately reference saqmaodv:: base types)."""
    text = path.read_text(encoding='utf-8')

    # Skip the H-SAQMAODV qtable files: they manage their own namespaces
    if 'hsaqmaodv-qtable' in path.name:
        return

    # Rename namespace block declarations
    text = text.replace('namespace saqmaodv\n', 'namespace hsaqmaodv\n')
    text = text.replace('namespace saqmaodv {', 'namespace hsaqmaodv {')
    # Rename fully-qualified references (only those NOT in qtable include)
    text = re.sub(r'\bns3::saqmaodv::', 'ns3::hsaqmaodv::', text)
    # Rename include guards
    text = text.replace('SAQMAODV_', 'HSAQMAODV_')
    # Rename includes (except saqmaodv-qtable.h → that stays as hsaqmaodv-qtable.h)
    text = re.sub(r'#include "saqmaodv-qtable\.h"',
                  '#include "hsaqmaodv-qtable.h"', text)
    text = re.sub(r'#include "saqmaodv-', '#include "hsaqmaodv-', text)

    path.write_text(text, encoding='utf-8')

info("Patching namespace in copied files...")
for p in list(DST_HS.rglob('*.cc')) + list(DST_HS.rglob('*.h')):
    patch_namespace(p)
    info(f"  patched {p.name}")

# ─── Step 5 (CRITICAL): Wire SelectHybridRoute & RecomputeSmoothEnergyWeights ─
#
# After renaming, hsaqmaodv-routing-protocol.cc still calls:
#   m_qtable.SelectEpsilonGreedy()           ← SAQMAODV behaviour, not HSAQMAODV
#   m_qtable.RecomputeAdaptiveRewardWeights() ← hard-threshold, not smooth
#
# We must replace these to activate the H-SAQMAODV contributions.
# Without this step HSAQMAODV would run identically to SAQMAODV.

ROUTING_CC = DST_HS / 'model' / 'hsaqmaodv-routing-protocol.cc'

if ROUTING_CC.exists():
    text = ROUTING_CC.read_text(encoding='utf-8')
    original = text

    # 5a. Replace route-selection call
    n_sel = text.count('SelectEpsilonGreedy')
    text = text.replace('SelectEpsilonGreedy', 'SelectHybridRoute')
    info(f"  routing-protocol.cc: replaced SelectEpsilonGreedy "
         f"→ SelectHybridRoute  ({n_sel} occurrence(s))")

    # 5b. Replace energy-weight adaptation call
    n_rw = text.count('RecomputeAdaptiveRewardWeights')
    text = text.replace('RecomputeAdaptiveRewardWeights',
                        'RecomputeSmoothEnergyWeights')
    info(f"  routing-protocol.cc: replaced RecomputeAdaptiveRewardWeights "
         f"→ RecomputeSmoothEnergyWeights  ({n_rw} occurrence(s))")

    if text != original:
        ROUTING_CC.write_text(text, encoding='utf-8')
        info("  routing-protocol.cc written.")
    else:
        info("  routing-protocol.cc: no changes needed (already patched?)")
else:
    info("WARNING: hsaqmaodv-routing-protocol.cc not found — manual patch required")

# ─── Step 6: CMakeLists.txt for hsaqmaodv module ─────────────────────────────
cmake = """\
# CMakeLists.txt — hsaqmaodv NS-3 module
# Auto-generated by apply-hsaqmaodv-module.py
#
# hsaqmaodv depends on libsaqmaodv because hsaqmaodv::QTable extends
# saqmaodv::QTable.  Both modules share the same NS-3 installation.

build_lib(
  LIBNAME hsaqmaodv
  SOURCE_FILES
    model/hsaqmaodv-rtable.cc
    model/hsaqmaodv-rqueue.cc
    model/hsaqmaodv-packet.cc
    model/hsaqmaodv-qtable.cc
    model/hsaqmaodv-routing-protocol.cc
    helper/hsaqmaodv-helper.cc
  HEADER_FILES
    model/hsaqmaodv-rtable.h
    model/hsaqmaodv-rqueue.h
    model/hsaqmaodv-packet.h
    model/hsaqmaodv-qtable.h
    model/hsaqmaodv-routing-protocol.h
    helper/hsaqmaodv-helper.h
  LIBRARIES_TO_LINK
    ${libcore}
    ${libnetwork}
    ${libinternet}
    ${libwifi}
    ${libenergy}
    ${libmobility}
    ${libsaqmaodv}
)
"""
(DST_HS / 'CMakeLists.txt').write_text(cmake)
info("  wrote CMakeLists.txt (links libsaqmaodv)")

# ─── Step 7: Register in top-level CMakeLists.txt ────────────────────────────
top_cmake = NS3_DIR / 'CMakeLists.txt'
if top_cmake.exists():
    content = top_cmake.read_text()
    if 'src/hsaqmaodv' not in content:
        if 'src/saqmaodv' in content:
            content = content.replace(
                'add_subdirectory(src/saqmaodv)',
                'add_subdirectory(src/saqmaodv)\nadd_subdirectory(src/hsaqmaodv)'
            )
        else:
            content += '\nadd_subdirectory(src/hsaqmaodv)\n'
        top_cmake.write_text(content)
        info("  patched top-level CMakeLists.txt")
    else:
        info("  CMakeLists.txt already contains hsaqmaodv — skipped")

print()
print("✓  hsaqmaodv module created at:", DST_HS)
print("   SelectHybridRoute and RecomputeSmoothEnergyWeights are wired.")
print()
print("Next step: run apply-hsaqmaodv-fanet.py")
print("Then     : cd $NS3_DIR && ./ns3 build")
