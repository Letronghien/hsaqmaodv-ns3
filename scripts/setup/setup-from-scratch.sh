#!/bin/bash
# =============================================================================
# setup-from-scratch.sh
#
# Cài đặt 5 giao thức base vào NS3_DIR (đã được set bởi standalone script):
#   AODV (stock), PMAODV, AOMDV, QMAODV, SAQMAODV
#
# Được gọi bởi setup-hsaqmaodv-standalone.sh — không chạy trực tiếp.
#
# Usage (standalone):
#   NS3_DIR=/path/to/ns-3.40 PROJECT_ROOT=/path/to/hsaqmaodv-ns3 \
#     bash scripts/setup/setup-from-scratch.sh
# =============================================================================

set -e

# ── Resolve paths ─────────────────────────────────────────────────────────────
if [ -z "${NS3_DIR:-}" ]; then
    for cand in \
        "$HOME/ns-allinone-3.40/ns-3.40" \
        "$HOME/ns-3-allinone/ns-3.40" \
        "$HOME/workspace/ns-allinone-3.40/ns-3.40" \
        "$HOME/ns-3.40"; do
        if [ -d "$cand" ] && [ -f "$cand/ns3" ] && [ -d "$cand/src/aodv" ]; then
            NS3_DIR="$cand"; break
        fi
    done
fi
if [ -z "${NS3_DIR:-}" ]; then
    echo "ERROR: NS3_DIR not set and ns-3.40 not found."
    echo "  NS3_DIR=/path/to/ns-3.40 bash $0"
    exit 1
fi
if [ ! -d "$NS3_DIR" ] || [ ! -f "$NS3_DIR/ns3" ] || [ ! -d "$NS3_DIR/src/aodv" ]; then
    echo "ERROR: NS3_DIR=$NS3_DIR invalid (needs ns3 binary + src/aodv/)."
    exit 1
fi

if [ -z "${PROJECT_ROOT:-}" ]; then
    PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
fi

export NS3_DIR PROJECT_ROOT

echo "========================================"
echo "  Setup base protocols (PMAODV/AOMDV/QMAODV/SAQMAODV)"
echo "========================================"
echo "NS3_DIR     : $NS3_DIR"
echo "PROJECT_ROOT: $PROJECT_ROOT"
echo ""

# ── Step 1: Backup existing custom modules ────────────────────────────────────
echo "[1/10] Backup existing custom modules (if any)..."
TS=$(date +%Y%m%d-%H%M%S)
BAK="$HOME/ns3-backup-${TS}"
mkdir -p "$BAK"
for m in pmaodv aomdv qmaodv saqmaodv; do
    if [ -d "$NS3_DIR/src/$m" ]; then
        mv "$NS3_DIR/src/$m" "$BAK/"
        echo "  Backed up src/$m"
    fi
done

# ── Step 2: PMAODV skeleton ───────────────────────────────────────────────────
echo "[2/10] Create PMAODV skeleton (clone src/aodv → src/pmaodv)..."
cd "$NS3_DIR"
cp -r src/aodv src/pmaodv
cd src/pmaodv
find . -depth -name "aodv*" | while read -r f; do
    new=$(echo "$f" | sed 's|/aodv|/pmaodv|; s|^aodv|pmaodv|')
    [ "$f" != "$new" ] && mv "$f" "$new"
done
find . -type f \( -name "*.h" -o -name "*.cc" -o -name "CMakeLists.txt" \) -print0 | \
    xargs -0 sed -i -e 's/aodv/pmaodv/g' -e 's/Aodv/Pmaodv/g' -e 's/AODV/PMAODV/g'
cd "$NS3_DIR"

# ── Step 3: AOMDV skeleton ────────────────────────────────────────────────────
echo "[3/10] Create AOMDV skeleton (clone src/aodv → src/aomdv)..."
cp -r src/aodv src/aomdv
cd src/aomdv
find . -depth -name "aodv*" | while read -r f; do
    new=$(echo "$f" | sed 's|/aodv|/aomdv|; s|^aodv|aomdv|')
    [ "$f" != "$new" ] && mv "$f" "$new"
done
find . -type f \( -name "*.h" -o -name "*.cc" -o -name "CMakeLists.txt" \) -print0 | \
    xargs -0 sed -i -e 's/aodv/aomdv/g' -e 's/Aodv/Aomdv/g' -e 's/AODV/AOMDV/g'
cd "$NS3_DIR"

# ── Step 3b: QMAODV skeleton ──────────────────────────────────────────────────
echo "[3b/10] Create QMAODV skeleton (clone src/aodv → src/qmaodv)..."
cp -r src/aodv src/qmaodv
cd src/qmaodv
find . -depth -name "aodv*" | while read -r f; do
    new=$(echo "$f" | sed 's|/aodv|/qmaodv|; s|^aodv|qmaodv|')
    [ "$f" != "$new" ] && mv "$f" "$new"
done
find . -type f \( -name "*.h" -o -name "*.cc" -o -name "CMakeLists.txt" \) -print0 | \
    xargs -0 sed -i -e 's/aodv/qmaodv/g' -e 's/Aodv/Qmaodv/g' -e 's/AODV/QMAODV/g'
cd "$NS3_DIR"

# ── Step 3c: SAQMAODV skeleton ────────────────────────────────────────────────
echo "[3c/10] Create SAQMAODV skeleton (clone src/aodv → src/saqmaodv)..."
cp -r src/aodv src/saqmaodv
cd src/saqmaodv
find . -depth -name "aodv*" | while read -r f; do
    new=$(echo "$f" | sed 's|/aodv|/saqmaodv|; s|^aodv|saqmaodv|')
    [ "$f" != "$new" ] && mv "$f" "$new"
done
find . -type f \( -name "*.h" -o -name "*.cc" -o -name "CMakeLists.txt" \) -print0 | \
    xargs -0 sed -i \
        -e 's/aodv/saqmaodv/g' -e 's/Aodv/Saqmaodv/g' -e 's/AODV/SAQMAODV/g'
cd "$NS3_DIR"

# ── Step 4: Copy custom files ─────────────────────────────────────────────────
echo "[4/10] Copy multipath/qtable files + update CMakeLists..."
cp "$PROJECT_ROOT/files/pmaodv-multipath-table.h"  src/pmaodv/model/
cp "$PROJECT_ROOT/files/pmaodv-multipath-table.cc" src/pmaodv/model/
cp "$PROJECT_ROOT/files/aomdv-multipath-table.h"   src/aomdv/model/
cp "$PROJECT_ROOT/files/aomdv-multipath-table.cc"  src/aomdv/model/
cp "$PROJECT_ROOT/files/qmaodv-qtable.h"           src/qmaodv/model/
cp "$PROJECT_ROOT/files/qmaodv-qtable.cc"          src/qmaodv/model/
cp "$PROJECT_ROOT/files/saqmaodv-qtable.h"         src/saqmaodv/model/
cp "$PROJECT_ROOT/files/saqmaodv-qtable.cc"        src/saqmaodv/model/

for m in pmaodv aomdv; do
    CM="src/$m/CMakeLists.txt"
    grep -q "${m}-multipath-table" "$CM" || \
        sed -i "s|model/${m}-rtable.cc|model/${m}-rtable.cc\n    model/${m}-multipath-table.cc|" "$CM"
    grep -q "${m}-multipath-table.h" "$CM" || \
        sed -i "s|model/${m}-rtable.h|model/${m}-rtable.h\n    model/${m}-multipath-table.h|" "$CM"
done
CM="src/qmaodv/CMakeLists.txt"
grep -q "qmaodv-qtable" "$CM" || {
    sed -i "s|model/qmaodv-rtable.cc|model/qmaodv-rtable.cc\n    model/qmaodv-qtable.cc|" "$CM"
    sed -i "s|model/qmaodv-rtable.h|model/qmaodv-rtable.h\n    model/qmaodv-qtable.h|" "$CM"
}
CM="src/saqmaodv/CMakeLists.txt"
grep -q "saqmaodv-qtable" "$CM" || {
    sed -i "s|model/saqmaodv-rtable.cc|model/saqmaodv-rtable.cc\n    model/saqmaodv-qtable.cc|" "$CM"
    sed -i "s|model/saqmaodv-rtable.h|model/saqmaodv-rtable.h\n    model/saqmaodv-qtable.h|" "$CM"
}
for m in qmaodv saqmaodv; do
    CM="src/$m/CMakeLists.txt"
    grep -q "energy" "$CM" || \
        sed -i 's|libcore|libcore\n  libenergy|' "$CM" 2>/dev/null || true
done

# ── Steps 5-7: Apply patches ──────────────────────────────────────────────────
echo "[5/10] Apply PMAODV patches..."
for p in apply-phase-2.3a.py apply-phase-2.3b.py apply-phase-2.3c.py apply-phase-2.3d.py; do
    [ -f "$PROJECT_ROOT/scripts/patches/$p" ] && python3 "$PROJECT_ROOT/scripts/patches/$p"
done
[ -f "$PROJECT_ROOT/scripts/patches/fix-2.3a.py" ] && \
    python3 "$PROJECT_ROOT/scripts/patches/fix-2.3a.py"

echo "[6/10] Apply AOMDV patches..."
python3 "$PROJECT_ROOT/scripts/patches/apply-aomdv-3.2-3.3.py"
python3 "$PROJECT_ROOT/scripts/patches/apply-aomdv-3.4-3.6.py"

echo "[6b/10] Apply QMAODV patches..."
for p in apply-qmaodv-2.3a.py apply-qmaodv-2.3b.py apply-qmaodv-2.3c.py \
          apply-qmaodv-2.3d.py apply-qmaodv-fix-v2.py; do
    [ -f "$PROJECT_ROOT/scripts/patches/$p" ] && python3 "$PROJECT_ROOT/scripts/patches/$p"
done

echo "[6c/10] Apply SAQMAODV patches..."
for p in apply-saqmaodv-2.3a.py apply-saqmaodv-2.3b.py apply-saqmaodv-2.3c.py \
          apply-saqmaodv-2.3d.py apply-saqmaodv-fix-v2.py; do
    [ -f "$PROJECT_ROOT/scripts/patches/$p" ] && python3 "$PROJECT_ROOT/scripts/patches/$p"
done

# Fix energy namespace for ns-3.40
if [ -d "src/energy" ] && \
   ! grep -q "namespace energy" "src/energy/model/basic-energy-source.h" 2>/dev/null; then
    echo "[6d/10] ns-3.40: fixing energy:: namespace in saqmaodv..."
    sed -i 's/ns3::energy::/ns3::/g' src/saqmaodv/model/saqmaodv-routing-protocol.cc
fi

echo "[7/10] Apply fix patches (level 1+2)..."
python3 "$PROJECT_ROOT/scripts/patches/apply-fix-level-1.py"
python3 "$PROJECT_ROOT/scripts/patches/apply-fix-level-2.py"

# ── Step 8: Copy fanet-sim.cc + Build ────────────────────────────────────────
echo "[8/10] Copy fanet-sim.cc + Configure + Build..."
cp "$PROJECT_ROOT/src/fanet-sim.cc" scratch/

if [ -d "src/energy" ] && \
   ! grep -q "namespace energy" "src/energy/model/basic-energy-source.h" 2>/dev/null; then
    echo "  Detected ns-3.40 — removing energy:: qualifiers from fanet-sim.cc"
    sed -i '/^namespace energy = ns3::energy;/d; s/energy:://g' scratch/fanet-sim.cc
fi

./ns3 configure --enable-examples --enable-tests --build-profile=optimized 2>&1 | tail -5
./ns3 build 2>&1 | tail -10

EXEC=$(find build -maxdepth 2 -name "*fanet-sim*" -executable -type f 2>/dev/null | head -1)
[ -z "$EXEC" ] && echo "ERROR: build failed" && exit 1

echo ""
echo "[9/10] Smoke test (AODV + SAQMAODV)..."
"$EXEC" --protocol=AODV    --numNodes=5 --simTime=10 --csvFile=/tmp/s.csv 2>&1 | tail -1
"$EXEC" --protocol=SAQMAODV --numNodes=5 --simTime=10 --maxPaths=3 --csvFile=/tmp/s.csv 2>&1 | tail -1

echo ""
echo "[10/10] Base protocols installed OK."
echo "  NS3_DIR: $NS3_DIR"
