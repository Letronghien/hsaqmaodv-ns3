#!/bin/bash
# =============================================================
# EXP-9: Sparse FANET — N=5,8 — FULL vs SAQMAODV + AODV
# Mục tiêu: chứng minh DualQ + HS mechs giúp ở mạng thưa
# void region phổ biến hơn → DualQ seed Q-table quan trọng hơn
#
# Cách chạy:
#   chmod +x run_sparse_dualq.sh
#   ./run_sparse_dualq.sh test    # thử 2 seeds trước
#   ./run_sparse_dualq.sh full    # 5 protos × 2 N × 30 seeds = 300 jobs
# =============================================================
ulimit -c 0

BIN=~/ns-allinone-3.40-hsaqmaodv/ns-3.40/build/scratch/ns3.40-fanet-sim
TMPDIR=~/H-SA-full-results/exp9-sparse-tmp   # thư mục riêng
OUTCSV=~/H-SA-full-results/exp9-sparse.csv
mkdir -p "$TMPDIR"

MODE="${1:-test}"
PROTOS=("AODV" "PMAODV" "QMAODV" "SAQMAODV" "HSAQMAODV")
N_VALS=(5 8)
SEEDS=$(seq 1 30)

run_one() {
  local PROTO=$1
  local N=$2
  local SEED=$3
  local TMPFILE="$TMPDIR/${PROTO}_N${N}_S${SEED}.csv"

  [ -f "$TMPFILE" ] && { echo "  SKIP: ${PROTO}_N${N}_S${SEED}"; return 0; }

  RAW=$($BIN --protocol=$PROTO \
             --numNodes=$N \
             --meanVelMin=20 --meanVelMax=20 \
             --initialEnergy=30 \
             --seed=$SEED \
             --simTime=200 \
             --pktInterval=0.3 \
             --mobility=GAUSS \
             $EXTRA 2>&1)

  DELIVERY=$(echo "$RAW" | grep -oP '(?<=delivery=)[\d.]+')
  DELAY=$(echo "$RAW"    | grep -oP '(?<=delay=)[\d.]+')
  THR=$(echo "$RAW"      | grep -oP '(?<=thr=)[\d.]+')
  ROVER=$(echo "$RAW"    | grep -oP '(?<=rOver=)\d+')
  ENERGY=$(echo "$RAW"   | grep -oP '(?<= E=)[\d.]+' | head -1)

  if [ -n "$DELIVERY" ]; then
    local LINE="EXP9_N${N},$PROTO,GAUSS,1,$N,0,20,20,0.3,200,$SEED,$DELIVERY,$DELAY,$THR,$ROVER,$ENERGY,0"
    echo "$LINE" > "$TMPFILE"
    echo "  OK: $LINE"
  else
    echo "  WARN: No output — $PROTO N=$N seed=$SEED"
    echo "  RAW: $RAW" | head -3
  fi
}

# ─── TEST MODE ────────────────────────────────────────────────
if [ "$MODE" = "test" ]; then
  echo "============================================="
  echo "TEST MODE: HSAQMAODV vs SAQMAODV, N=5, seed=1,2"
  echo "============================================="
  for PROTO in "HSAQMAODV" "SAQMAODV"; do
    for SEED in 1 2; do
      echo "--- $PROTO N=5 seed=$SEED ---"
      run_one "$PROTO" 5 "$SEED"
    done
  done
  echo ""
  echo "Files: $(ls $TMPDIR 2>/dev/null | wc -l)"
  echo "Nếu OK → ./run_sparse_dualq.sh full"
  exit 0
fi

# ─── FULL MODE ────────────────────────────────────────────────
TOTAL=$(( ${#PROTOS[@]} * ${#N_VALS[@]} * 30 ))
echo "============================================="
echo "FULL MODE: $TOTAL jobs (5 protos × 2 N × 30 seeds)"
echo "Crash-safe: chạy lại sẽ skip jobs đã xong"
echo "============================================="

DONE=0
for N in "${N_VALS[@]}"; do
  for PROTO in "${PROTOS[@]}"; do
    echo ""
    echo "[$(date '+%H:%M:%S')] === $PROTO N=$N ==="
    for SEED in $SEEDS; do
      run_one "$PROTO" "$N" "$SEED"
      DONE=$((DONE+1))
    done
    COUNT=$(ls "$TMPDIR"/*.csv 2>/dev/null | wc -l)
    echo "[$(date '+%H:%M:%S')] Progress: $DONE/$TOTAL | Files: $COUNT"
  done
done

cat "$TMPDIR"/*.csv > "$OUTCSV"
echo ""
echo "DONE: $(wc -l < $OUTCSV) rows → $OUTCSV"
echo "Copy về: scp USER@SERVER:$OUTCSV ."
