#!/bin/bash
# apply-hsaqmaodv-all.sh
# Apply all H-SAQMAODV patches to NS-3 in order.
#
# Usage:
#   NS3_DIR=/path/to/ns-3.40 bash apply-hsaqmaodv-all.sh
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NS3_DIR="${NS3_DIR:-$HOME/ns-allinone-3.40/ns-3.40}"
export NS3_DIR

echo "=================================================="
echo " H-SAQMAODV — Applying NS-3 Patches"
echo "=================================================="
echo " NS3_DIR: $NS3_DIR"
echo " PATCHES: $SCRIPT_DIR"
echo ""

# Prereq: SA-QMAODV module must already be installed
if [ ! -d "$NS3_DIR/src/saqmaodv" ]; then
    echo "ERROR: saqmaodv module not found at $NS3_DIR/src/saqmaodv"
    echo "  → Run the base SA-QMAODV setup first (scripts/setup/setup-from-scratch.sh)"
    exit 1
fi

echo "[1/2] Creating hsaqmaodv NS-3 module..."
python3 "$SCRIPT_DIR/apply-hsaqmaodv-module.py"

echo ""
echo "[2/2] Patching fanet-sim.cc..."
python3 "$SCRIPT_DIR/apply-hsaqmaodv-fanet.py"

echo ""
echo "=================================================="
echo " All patches applied. Now build NS-3:"
echo "   cd \$NS3_DIR && ./ns3 build"
echo "=================================================="
