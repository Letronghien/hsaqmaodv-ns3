#!/bin/bash
NS3_DIR="${NS3_DIR:-$HOME/ns-allinone-3.40-hsaqmaodv/ns-3.40}"
EXEC=$(find "$NS3_DIR/build" -maxdepth 2 -name "*fanet-sim*" -executable -type f | head -1)
SEEDS="${SEEDS:-10}"
JOBS="${JOBS:-$(nproc)}"
TS=$(date +%Y%m%d-%H%M%S)
OUT="$HOME/results-hqa-params-${TS}"
mkdir -p "$OUT/jobs"

JOB="$OUT/jobs/jobs.txt"
> "$JOB"

PROTOCOLS=("AODV 1" "QMAODV 3" "SAQMAODV 3" "HSAQMAODV 3")

# N family: 10-70 nodes (like HQA)
for N in 10 20 30 40 50 70; do
  for SEED in $(seq 1 "$SEEDS"); do
    for EXP in "${PROTOCOLS[@]}"; do
      read -r PROTO MP <<< "$EXP"
      echo "$PROTO $MP $SEED $N" >> "$JOB"
    done
  done
done

run_job() {
  local PROTO=$1 MP=$2 SEED=$3 N=$4
  local CSV="$OUT/jobs/job-${PROTO}-N${N}-seed${SEED}.csv"
  "$EXEC" \
    --protocol="$PROTO" --maxPaths="$MP" \
    --mobility=RWP \
    --numNodes="$N" --simTime=300 --seed="$SEED" \
    --meanVelMin=10 --meanVelMax=100 \
    --pktInterval=0.25 --pktSize=127 \
    --initialEnergy=1000 --enableEnergy=1 \
    --areaX=500 --areaY=500 \
    --csvFile="$CSV" >/dev/null 2>&1
  echo "done $PROTO N=$N seed=$SEED"
}
export -f run_job
export EXEC OUT

cat "$JOB" | xargs -P "$JOBS" -L 1 bash -c 'run_job "$@"' _

# Merge
MERGED="$OUT/merged.csv"
FIRST=$(ls "$OUT/jobs"/*.csv 2>/dev/null | head -1)
[ -n "$FIRST" ] && head -1 "$FIRST" > "$MERGED"
for f in "$OUT/jobs"/*.csv; do tail -n +2 "$f" >> "$MERGED"; done

echo "Done: $MERGED"
