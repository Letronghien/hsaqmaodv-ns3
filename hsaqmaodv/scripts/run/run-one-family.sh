#!/bin/bash
# Usage: bash run-one-family.sh <FAMILY> <SEEDS>
# Example: bash run-one-family.sh N 30

FAMILY=$1
SEEDS=${2:-10}
NS3_DIR=~/ns-allinone-3.40-hsaqmaodv/ns-3.40

echo "=== Chạy family: $FAMILY, seeds: $SEEDS ==="

NS3_DIR=$NS3_DIR FAMILIES="$FAMILY" SEEDS=$SEEDS \
  bash ~/run-paper1-experiments.sh

# Tìm kết quả mới nhất
MERGED=$(ls -t ~/results-paper1-*/merged.csv 2>/dev/null | head -1)
if [ -z "$MERGED" ]; then echo "Không có merged.csv"; exit 1; fi

echo "=== Vẽ biểu đồ từ: $MERGED ==="
OUTDIR=~/figures-${FAMILY}-$(date +%H%M%S)
python3 ~/plot-paper1.py "$MERGED" --outdir "$OUTDIR"

echo "=== Nén ==="
zip ~/figures-${FAMILY}.zip "$OUTDIR"/*.pdf 2>/dev/null && \
  echo "Done: ~/figures-${FAMILY}.zip" || echo "Không có PDF nào"
