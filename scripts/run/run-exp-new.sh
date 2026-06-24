#!/bin/bash
# run-exp-new.sh — H-SAQMAODV Full Experiment Runner (v3)
# Binary: fanet-sim-hsa (from ~/ns-allinone-3.40/ns-3.40/scratch/fanet-sim-hsa.cc)
# Output: ~/H-SA-results-YYYYMMDD-HHMMSS/
#
# Usage:
#   FAMILIES="EXP1 EXP2" SEEDS=30 JOBS=4 bash ~/run-exp-new.sh
#   FAMILIES="EXP1"       bash ~/run-exp-new.sh
#   FAMILIES="ALL"        bash ~/run-exp-new.sh   # không gồm EXP5

set -euo pipefail

NS3_DIR="${NS3_DIR:-$HOME/ns-allinone-3.40/ns-3.40}"
EXEC=$(find "$NS3_DIR/build" -maxdepth 3 -name "*fanet-sim-hsa*" -executable -type f 2>/dev/null | head -1)
[ -z "$EXEC" ] && { echo "ERROR: fanet-sim-hsa binary not found in $NS3_DIR/build"; exit 1; }

SEEDS="${SEEDS:-30}"
JOBS="${JOBS:-4}"
FAMILIES="${FAMILIES:-ALL}"
OUTDIR="${OUTDIR:-$HOME/H-SA-results-$(date +%Y%m%d-%H%M%S)}"
JOB_FILE="$OUTDIR/jobs.txt"

mkdir -p "$OUTDIR"
echo "[INFO] EXEC:    $EXEC"
echo "[INFO] SEEDS:   $SEEDS"
echo "[INFO] JOBS:    $JOBS"
echo "[INFO] OUTDIR:  $OUTDIR"
echo "[INFO] Started: $(date)"

# ── Protocols ─────────────────────────────────────────────────────────────────
PROTOCOLS=(
    "AODV      1"
    "PMAODV    3"
    "QMAODV    3"
    "SAQMAODV  3"
    "HSAQMAODV 3"
)

# H-SAQMAODV TVI optimal thresholds (EXP-6 sẽ sweep các giá trị khác)
HS_PARAMS="--hsTviHigh=5 --hsTviLow=2"

# Fixed environments
ENV_MAIN="--pktInterval=0.3 --mobility=GAUSS --enableEnergy=1"
ENV_HQA="--pktInterval=0.3 --mobility=RWP --simTime=300 --areaX=500 --areaY=500 --pktSize=127 --enableEnergy=1"

# ── Helpers ───────────────────────────────────────────────────────────────────
# gen_jobs: tất cả 5 protocols × SEEDS seeds
gen_jobs() {
    local CSV="$1"; shift
    local EXTRA="$*"
    for PROTO_LINE in "${PROTOCOLS[@]}"; do
        read -r PROTO NP <<< "$PROTO_LINE"
        for SEED in $(seq 1 "$SEEDS"); do
            echo "$EXEC --protocol=$PROTO --maxPaths=$NP --seed=$SEED $EXTRA --csvFile=$CSV" >> "$JOB_FILE"
        done
    done
}

# gen_jobs_proto: chỉ protocols trong PROTOS_STR
gen_jobs_proto() {
    local CSV="$1"; local PROTOS_STR="$2"; shift 2
    local EXTRA="$*"
    for PROTO_LINE in "${PROTOCOLS[@]}"; do
        read -r PROTO NP <<< "$PROTO_LINE"
        echo "$PROTOS_STR" | grep -qw "$PROTO" || continue
        for SEED in $(seq 1 "$SEEDS"); do
            echo "$EXEC --protocol=$PROTO --maxPaths=$NP --seed=$SEED $EXTRA --csvFile=$CSV" >> "$JOB_FILE"
        done
    done
}

# ── EXP-1: Node Density Sweep ─────────────────────────────────────────────────
run_exp1() {
    echo "[EXP-1] Node Density Sweep: N = 5 10 15 20 25 30"
    local CSV="$OUTDIR/exp1-node-density.csv"
    for N in 5 10 15 20 25 30; do
        gen_jobs "$CSV" \
            $ENV_MAIN $HS_PARAMS \
            --numNodes=$N --meanVelMin=20 --meanVelMax=20 --initialEnergy=30 \
            --scenario=EXP1-N${N}
    done
}

# ── EXP-2: Speed Sweep ────────────────────────────────────────────────────────
run_exp2() {
    echo "[EXP-2] Speed Sweep: v = 5 10 20 30 50 m/s"
    local CSV="$OUTDIR/exp2-speed.csv"
    for V in 5 10 20 30 50; do
        gen_jobs "$CSV" \
            $ENV_MAIN $HS_PARAMS \
            --numNodes=15 --meanVelMin=$V --meanVelMax=$V --initialEnergy=30 \
            --scenario=EXP2-V${V}
    done
}

# ── EXP-3: Traffic Load Sweep ─────────────────────────────────────────────────
run_exp3() {
    echo "[EXP-3] Traffic Load Sweep: interval = 0.05 0.1 0.3 0.5 1.0 s"
    local CSV="$OUTDIR/exp3-load.csv"
    for INTERVAL in 0.05 0.1 0.3 0.5 1.0; do
        local TAG="${INTERVAL//./_}"
        gen_jobs "$CSV" \
            --mobility=GAUSS --enableEnergy=1 $HS_PARAMS \
            --numNodes=15 --meanVelMin=20 --meanVelMax=20 --initialEnergy=30 \
            --pktInterval=$INTERVAL \
            --scenario=EXP3-I${TAG}
    done
}

# ── EXP-4: Battery Capacity Sweep ─────────────────────────────────────────────
run_exp4() {
    echo "[EXP-4] Energy Sweep: E0 = 5 10 20 30 50 J"
    local CSV="$OUTDIR/exp4-energy.csv"
    for E in 5 10 20 30 50; do
        gen_jobs "$CSV" \
            $ENV_MAIN $HS_PARAMS \
            --numNodes=15 --meanVelMin=20 --meanVelMax=20 --initialEnergy=$E \
            --scenario=EXP4-E${E}
    done
}

# ── EXP-6: TVI Sensitivity ────────────────────────────────────────────────────
run_exp6() {
    echo "[EXP-6] TVI Sensitivity: tviHigh ∈ {3,5,8,10,15} x tviLow ∈ {0,1,2}"
    local CSV="$OUTDIR/exp6-tvi-sensitivity.csv"
    for TVI_H in 3 5 8 10 15; do
        for TVI_L in 0 1 2; do
            [ "$TVI_L" -ge "$TVI_H" ] && continue
            # Chỉ 2 protocols, truyền TVI rõ ràng (không dùng HS_PARAMS mặc định)
            gen_jobs_proto "$CSV" "HSAQMAODV SAQMAODV" \
                $ENV_MAIN \
                --numNodes=15 --meanVelMin=20 --meanVelMax=20 --initialEnergy=30 \
                --hsTviHigh=$TVI_H --hsTviLow=$TVI_L \
                --scenario=EXP6-H${TVI_H}-L${TVI_L}
        done
    done
}

# ── EXP-7: HQA-Comparable Indirect Validation ─────────────────────────────────
run_exp7() {
    echo "[EXP-7] HQA-Comparable: RWP, N = 10 20 30 40 50 70"
    local CSV="$OUTDIR/exp7-hqa-comparable.csv"
    for N in 10 20 30 40 50 70; do
        gen_jobs "$CSV" \
            $ENV_HQA $HS_PARAMS \
            --numNodes=$N --meanVelMin=10 --meanVelMax=100 --initialEnergy=1000 \
            --scenario=EXP7-N${N}
    done
}

# ── EXP-8: Energy-Constrained HQA-Comparable ──────────────────────────────────
run_exp8() {
    echo "[EXP-8] HQA-Energy: RWP, E0 = 10 20 50 100 J, N=20"
    local CSV="$OUTDIR/exp8-hqa-energy.csv"
    for E in 10 20 50 100; do
        gen_jobs "$CSV" \
            $ENV_HQA $HS_PARAMS \
            --numNodes=20 --meanVelMin=10 --meanVelMax=100 --initialEnergy=$E \
            --scenario=EXP8-E${E}
    done
}

# ── Parallel runner ────────────────────────────────────────────────────────────
run_jobs() {
    local TOTAL
    TOTAL=$(wc -l < "$JOB_FILE")
    echo "[INFO] Total jobs: $TOTAL | Parallel: $JOBS"
    echo "[INFO] Running..."
    nice -n 10 xargs -P "$JOBS" -I{} bash -c '{}' < "$JOB_FILE"
    echo "[INFO] Done: $(date)"
}

# ── Main ──────────────────────────────────────────────────────────────────────
> "$JOB_FILE"

case "$FAMILIES" in
    ALL)
        run_exp1; run_exp2; run_exp3; run_exp4
        run_exp6; run_exp7; run_exp8
        ;;
    *)
        for FAM in $FAMILIES; do
            case "$FAM" in
                EXP1|exp1) run_exp1 ;;
                EXP2|exp2) run_exp2 ;;
                EXP3|exp3) run_exp3 ;;
                EXP4|exp4) run_exp4 ;;
                EXP6|exp6) run_exp6 ;;
                EXP7|exp7) run_exp7 ;;
                EXP8|exp8) run_exp8 ;;
                *) echo "[WARN] Unknown family: $FAM (bỏ qua)" ;;
            esac
        done
        ;;
esac

TOTAL=$(wc -l < "$JOB_FILE")
[ "$TOTAL" -eq 0 ] && { echo "[ERROR] No jobs — check FAMILIES"; exit 1; }

echo ""
echo "════════════════════════════════════════════"
echo "  Jobs ready: $TOTAL"
echo "  Preview (5 dòng đầu):"
head -5 "$JOB_FILE"
echo "  ..."
echo "════════════════════════════════════════════"

run_jobs

echo ""
echo "════════════════════════════════════════════"
echo "  DONE — Results: $OUTDIR"
echo "  Next: python3 ~/plot-results.py $OUTDIR/*.csv --outdir ~/H-SA-figures"
echo "════════════════════════════════════════════"
