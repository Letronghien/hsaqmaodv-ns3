#!/bin/bash
# =============================================================================
# setup-hsaqmaodv-standalone.sh
#
# Tạo môi trường NS-3 RIÊNG BIỆT cho dự án HSAQMAODV.
# KHÔNG đụng đến các NS-3 hiện có trên VM.
#
# Logic:
#   - Tìm NS-3 gốc (có saqmaodv) → rsync sang thư mục mới
#   - Nếu base modules (saqmaodv) đã có → CHỈ cài thêm hsaqmaodv
#   - Nếu chưa có → chạy setup-from-scratch.sh trước
#
# Usage:
#   cd ~/hsaqmaodv-ns3
#   bash scripts/setup/setup-hsaqmaodv-standalone.sh
#
#   # Custom NS-3 source:
#   NS3_SRC=/path/to/existing/ns-3.40 bash scripts/setup/setup-hsaqmaodv-standalone.sh
# =============================================================================

set -euo pipefail

# ── Paths (tất cả đều relative qua biến, không hardcode) ─────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJ_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

INSTALL_NAME="ns-allinone-3.40-hsaqmaodv"
NS3_DIR="$HOME/$INSTALL_NAME/ns-3.40"

export NS3_DIR
export PROJECT_ROOT="$PROJ_DIR"

echo "======================================================"
echo "  H-SAQMAODV — Standalone NS-3 Setup"
echo "======================================================"
echo "  PROJ_DIR  : $PROJ_DIR"
echo "  NS3_DIR   : $NS3_DIR"
echo ""

# ── Step 1: Tìm NS-3 source để copy từ đó ────────────────────────────────────
echo "[1/5] Locate NS-3 source..."

if [ -d "$NS3_DIR" ] && [ -f "$NS3_DIR/ns3" ]; then
    echo "  NS-3 already at $NS3_DIR — skipping copy"
else
    # Tìm NS-3 gốc có saqmaodv (ưu tiên version đã cài đủ modules)
    NS3_SRC="${NS3_SRC:-}"
    if [ -z "$NS3_SRC" ]; then
        for cand in \
            "$HOME/ns-allinone-3.40/ns-3.40" \
            "$HOME/ns-3-allinone/ns-3.40" \
            "$HOME/ns-3.40"; do
            if [ -d "$cand" ] && [ -f "$cand/ns3" ]; then
                NS3_SRC="$cand"
                break
            fi
        done
    fi

    if [ -z "$NS3_SRC" ] || [ ! -d "$NS3_SRC" ]; then
        echo "ERROR: Không tìm thấy NS-3 gốc."
        echo "  Chỉ định thủ công: NS3_SRC=/path/to/ns-3.40 bash $0"
        exit 1
    fi

    echo "  Source: $NS3_SRC"
    echo "  Copying to: $NS3_DIR (không copy build/ để tiết kiệm disk)..."
    mkdir -p "$(dirname "$NS3_DIR")"
    rsync -a --exclude='build/' --exclude='.git/' \
          "$NS3_SRC/" "$NS3_DIR/"
    echo "  Copy done."
fi

cd "$NS3_DIR"

# ── Step 2: Kiểm tra base modules đã tồn tại chưa ────────────────────────────
echo ""
echo "[2/5] Check base modules..."

NEED_BASE=false
for m in pmaodv qmaodv saqmaodv; do
    if [ ! -d "src/$m" ]; then
        echo "  src/$m : MISSING"
        NEED_BASE=true
    else
        echo "  src/$m : OK"
    fi
done

# ── Step 3: Cài base protocols nếu cần ───────────────────────────────────────
if [ "$NEED_BASE" = "true" ]; then
    echo ""
    echo "[3/5] Installing base protocols (PMAODV/QMAODV/SAQMAODV)..."
    bash "$PROJ_DIR/scripts/setup/setup-from-scratch.sh"
else
    echo ""
    echo "[3/5] Base protocols already present — skipping setup-from-scratch.sh"
fi

# ── Step 4: Cài HSAQMAODV module ─────────────────────────────────────────────
echo ""
echo "[4/5] Install H-SAQMAODV module..."

if [ -d "$NS3_DIR/src/hsaqmaodv" ]; then
    echo "  hsaqmaodv module already exists — re-applying patches (safe to re-run)"
fi

python3 "$PROJ_DIR/hsaqmaodv/scripts/patches/apply-hsaqmaodv-module.py"

# Copy fanet-sim.cc (luôn copy version mới nhất từ project)
echo "  Copying fanet-sim.cc..."
cp "$PROJ_DIR/src/fanet-sim.cc" "$NS3_DIR/scratch/"

# Fix energy:: namespace cho ns-3.40
if [ -d "$NS3_DIR/src/energy" ] && \
   ! grep -q "namespace energy" "$NS3_DIR/src/energy/model/basic-energy-source.h" 2>/dev/null; then
    echo "  Detected ns-3.40 — removing energy:: qualifiers..."
    sed -i '/^namespace energy = ns3::energy;/d; s/energy:://g' \
        "$NS3_DIR/scratch/fanet-sim.cc"
fi

# ── Step 5: Build + smoke test ────────────────────────────────────────────────
echo ""
echo "[5/5] Build NS-3..."
./ns3 configure --enable-examples --enable-tests --build-profile=optimized 2>&1 | tail -5
./ns3 build 2>&1 | tail -15

EXEC=$(find build -maxdepth 2 -name "*fanet-sim*" -executable -type f 2>/dev/null | head -1)
if [ -z "$EXEC" ]; then
    echo "ERROR: Build failed. Check output above."
    exit 1
fi

echo ""
echo "Smoke test (5 protocols, N=5, T=10s)..."
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
echo "  Binary  : $NS3_DIR/$EXEC"
echo ""
echo "  Daily workflow:"
echo "    cd ~/hsaqmaodv-ns3 && git pull"
echo "    cp files/hsaqmaodv-qtable.h  $NS3_DIR/src/hsaqmaodv/model/"
echo "    cp files/hsaqmaodv-qtable.cc $NS3_DIR/src/hsaqmaodv/model/"
echo "    cp src/fanet-sim.cc          $NS3_DIR/scratch/"
echo "    cd $NS3_DIR && ./ns3 build"
