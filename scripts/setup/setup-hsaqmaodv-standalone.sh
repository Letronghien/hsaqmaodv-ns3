#!/bin/bash
# =============================================================================
# setup-hsaqmaodv-standalone.sh
#
# Tạo môi trường NS-3 RIÊNG BIỆT cho dự án HSAQMAODV.
# KHÔNG đụng đến các NS-3 hiện có trên VM.
#
# Pattern: ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/
# (giống cách dự án qsaqmaodv dùng ~/ns-allinone-3.40-qsaqmaodv/)
#
# Usage:
#   cd ~/hsaqmaodv-ns3
#   bash scripts/setup/setup-hsaqmaodv-standalone.sh
#
#   # Hoặc chỉ định NS3 tarball custom:
#   NS3_TARBALL=/path/to/ns-allinone-3.40.tar.bz2 \
#     bash scripts/setup/setup-hsaqmaodv-standalone.sh
#
# Kết quả: NS3_DIR=~/ns-allinone-3.40-hsaqmaodv/ns-3.40
#   cài đủ 5 giao thức: AODV, PMAODV, QMAODV, SAQMAODV, HSAQMAODV
# =============================================================================

set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────────────────
PROJ_DIR=$(cd "$(dirname "$0")/../.." && pwd)
INSTALL_NAME="ns-allinone-3.40-hsaqmaodv"
INSTALL_DIR="$HOME/$INSTALL_NAME"
NS3_DIR="$INSTALL_DIR/ns-3.40"

export NS3_DIR
export PROJECT_ROOT="$PROJ_DIR"

echo "======================================================"
echo "  H-SAQMAODV — Standalone NS-3 Setup"
echo "======================================================"
echo "  PROJ_DIR  : $PROJ_DIR"
echo "  INSTALL   : $INSTALL_DIR"
echo "  NS3_DIR   : $NS3_DIR"
echo ""

# ── Step 1: Check / Download NS-3.40 ─────────────────────────────────────────
echo "[1/7] Check NS-3.40 source..."
if [ -d "$NS3_DIR" ] && [ -f "$NS3_DIR/ns3" ]; then
    echo "  NS-3.40 already at $NS3_DIR — skipping download"
else
    mkdir -p "$INSTALL_DIR"

    # Use provided tarball or try to find/download
    if [ -n "${NS3_TARBALL:-}" ] && [ -f "$NS3_TARBALL" ]; then
        echo "  Extracting from $NS3_TARBALL ..."
        tar -xf "$NS3_TARBALL" -C "$HOME"
        # Rename extracted dir to our INSTALL_NAME
        extracted=$(ls -d "$HOME"/ns-allinone-3.40 2>/dev/null | head -1)
        [ -d "$extracted" ] && mv "$extracted" "$INSTALL_DIR"
    else
        # Try to copy from existing ns-allinone-3.40 if present (fastest)
        EXISTING="$HOME/ns-allinone-3.40"
        if [ -d "$EXISTING/ns-3.40" ] && [ -f "$EXISTING/ns-3.40/ns3" ]; then
            echo "  Copying from $EXISTING (faster than download)..."
            echo "  NOTE: only src/ and essential files are copied to save disk"
            rsync -a --exclude='build/' --exclude='.git/' \
                  "$EXISTING/ns-3.40/" "$NS3_DIR/"
        else
            echo "  Downloading ns-allinone-3.40.tar.bz2 from nsnam.org..."
            cd "$HOME"
            wget -q --show-progress \
                "https://www.nsnam.org/releases/ns-allinone-3.40.tar.bz2" \
                -O ns-allinone-3.40.tar.bz2
            tar -xjf ns-allinone-3.40.tar.bz2
            mv ns-allinone-3.40 "$INSTALL_NAME"
            rm ns-allinone-3.40.tar.bz2
        fi
    fi
fi

if [ ! -f "$NS3_DIR/ns3" ]; then
    echo "ERROR: $NS3_DIR/ns3 not found after setup. Aborting."
    exit 1
fi

# ── Step 2: Install base protocols (PMAODV, AOMDV, QMAODV, SAQMAODV) ─────────
echo ""
echo "[2/7] Install base protocols via setup-from-scratch.sh..."
bash "$PROJ_DIR/scripts/setup/setup-from-scratch.sh"

# setup-from-scratch.sh already builds fanet-sim and runs smoke tests.

# ── Step 3: Install H-SAQMAODV module ────────────────────────────────────────
echo ""
echo "[3/7] Install H-SAQMAODV module..."
python3 "$PROJ_DIR/hsaqmaodv/scripts/patches/apply-hsaqmaodv-module.py"

# ── Step 4: Patch fanet-sim.cc for HSAQMAODV ─────────────────────────────────
echo ""
echo "[4/7] Patch fanet-sim.cc for HSAQMAODV support..."
# fanet-sim.cc already includes HSAQMAODV in the project source.
# Just copy the updated version:
cp "$PROJ_DIR/src/fanet-sim.cc" "$NS3_DIR/scratch/fanet-sim.cc"

# ns-3.40 energy namespace fix (same as setup-from-scratch.sh)
if [ -d "$NS3_DIR/src/energy" ] && \
   ! grep -q "namespace energy" "$NS3_DIR/src/energy/model/basic-energy-source.h" 2>/dev/null; then
    echo "  Detected ns-3.40 layout — removing 'energy::' qualifiers from scratch/fanet-sim.cc"
    sed -i '/^namespace energy = ns3::energy;/d; s/energy:://g' \
        "$NS3_DIR/scratch/fanet-sim.cc"
fi

# ── Step 5: Build ─────────────────────────────────────────────────────────────
echo ""
echo "[5/7] Build NS-3 with all 5 protocols..."
cd "$NS3_DIR"
./ns3 configure --enable-examples --enable-tests --build-profile=optimized 2>&1 | tail -5
./ns3 build 2>&1 | tail -15

# ── Step 6: Verify build ──────────────────────────────────────────────────────
echo ""
echo "[6/7] Verify build..."
EXEC=$(find build -maxdepth 2 -name "*fanet-sim*" -executable -type f 2>/dev/null | head -1)
if [ -z "$EXEC" ]; then
    echo "ERROR: fanet-sim build failed. Check output above."
    exit 1
fi

echo "  Binary: $NS3_DIR/$EXEC"

# ── Step 7: Smoke test all 5 protocols ───────────────────────────────────────
echo ""
echo "[7/7] Smoke test (5 protocols, N=5, T=10s)..."
for proto in AODV PMAODV QMAODV SAQMAODV HSAQMAODV; do
    result=$("$EXEC" --protocol=$proto --numNodes=5 --simTime=10 \
                     --maxPaths=3 --csvFile=/tmp/hsaq-smoke.csv 2>&1 | tail -1)
    echo "  $proto : $result"
done

echo ""
echo "======================================================"
echo "  Setup complete!"
echo "======================================================"
echo ""
echo "  NS3_DIR : $NS3_DIR"
echo ""
echo "  Workflow:"
echo "    # Clone project (once):"
echo "    git clone https://github.com/Letronghien/hsaqmaodv-ns3.git ~/hsaqmaodv-ns3"
echo ""
echo "    # Daily: pull + copy + build:"
echo "    cd ~/hsaqmaodv-ns3 && git pull"
echo "    cp src/fanet-sim.cc $NS3_DIR/scratch/"
echo "    cp files/hsaqmaodv-qtable.h $NS3_DIR/src/hsaqmaodv/model/"
echo "    cp files/hsaqmaodv-qtable.cc $NS3_DIR/src/hsaqmaodv/model/"
echo "    cd $NS3_DIR && ./ns3 build"
echo ""
echo "    # Run experiments:"
echo "    bash ~/hsaqmaodv-ns3/scripts/run/run-paper-experiments.sh"
