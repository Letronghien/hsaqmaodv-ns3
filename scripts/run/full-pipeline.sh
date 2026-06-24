#!/bin/bash
# full-pipeline.sh
# Pipeline đầy đủ: patch NS-3 → build → run → plot → stats
# Usage: bash ~/full-pipeline.sh [FAMILY]
# Chạy từng bước, có thể resume nếu bị đứt

set -euo pipefail

NS3DIR="$HOME/hsaqmaodv-ns3"
SCRIPTS="$HOME"   # vị trí các scripts sau khi copy từ repo
TARGET="${1:-ALL}"

echo "════════════════════════════════════════════════════════════"
echo "  H-SAQMAODV Full Metrics Pipeline"
echo "  Target family: $TARGET | $(date)"
echo "════════════════════════════════════════════════════════════"

# ── Step 1: Kiểm tra NS-3 source có đủ metrics chưa ─────────────────────────
echo ""
echo "── Step 1: Check NS-3 source ───────────────────────────────"
python3 ~/check-ns3-source.sh 2>/dev/null || bash ~/check-ns3-source.sh

echo ""
echo "── Step 2: Patch NS-3 source để thêm metrics ───────────────"
# Chạy dry-run trước để xem thay đổi
python3 ~/patch-ns3-metrics.py --dry-run
echo ""
read -p "Apply patch? [y/N] " confirm
if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    python3 ~/patch-ns3-metrics.py
    echo ""
    echo "── Step 3: Rebuild NS-3 ─────────────────────────────────────"
    cd "$NS3DIR"
    ./ns3 build scratch/fanet-sim 2>&1 | tail -30
    echo "[OK] Build done"
else
    echo "[SKIP] Patch skipped — using existing binary"
fi

# ── Step 4: Run experiments ───────────────────────────────────────────────────
echo ""
echo "── Step 4: Run experiments ($TARGET) ───────────────────────"
echo "  Tip: chạy trong tmux để tránh mất kết nối"
echo "  tmux new -s fullrun && bash ~/full-pipeline.sh $TARGET"
echo ""

# Chạy trong background với tmux nếu có
if command -v tmux &>/dev/null && [[ -z "${TMUX:-}" ]]; then
    echo "[INFO] Không trong tmux — chạy trực tiếp"
fi

SEEDS=${SEEDS:-30} bash ~/run-full-metrics.sh "$TARGET"

# ── Step 5: Kiểm tra kết quả ─────────────────────────────────────────────────
echo ""
echo "── Step 5: Check output ─────────────────────────────────────"
RESULT_DIR=$(ls -dt ~/results-fullmetrics-* 2>/dev/null | head -1)
if [[ -z "$RESULT_DIR" ]]; then
    echo "[ERROR] Không tìm thấy results-fullmetrics-* directory"
    exit 1
fi
echo "Results dir: $RESULT_DIR"
for f in "$RESULT_DIR"/merged-*.csv; do
    rows=$(wc -l < "$f")
    cols=$(head -1 "$f" | tr ',' '\n' | wc -l)
    echo "  $(basename $f): ${rows} rows, ${cols} cols"
    head -1 "$f"
done

# ── Step 6: Plot all metrics ──────────────────────────────────────────────────
echo ""
echo "── Step 6: Plot ─────────────────────────────────────────────"
FIGDIR="$HOME/figures-fullmetrics-$(date +%Y%m%d)"
mkdir -p "$FIGDIR"
python3 ~/plot-full-metrics.py "$RESULT_DIR"/merged-*.csv --outdir "$FIGDIR"
echo "Figures: $FIGDIR"
ls "$FIGDIR"/*.pdf 2>/dev/null | wc -l | xargs -I{} echo "  {} PDF files generated"

# ── Step 7: Stats test ────────────────────────────────────────────────────────
echo ""
echo "── Step 7: Wilcoxon stats ───────────────────────────────────"
pip install scipy --break-system-packages -q 2>/dev/null || true
python3 ~/stats-test.py "$RESULT_DIR"/merged-*.csv 2>/dev/null || \
    echo "[WARN] stats-test.py failed — check scipy install"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Pipeline DONE"
echo "  Results:  $RESULT_DIR"
echo "  Figures:  $FIGDIR"
echo "  Zip:      zip -r figures-fullmetrics.zip $FIGDIR"
echo "════════════════════════════════════════════════════════════"
