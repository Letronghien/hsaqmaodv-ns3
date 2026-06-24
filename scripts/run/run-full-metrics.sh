#!/bin/bash
# run-full-metrics.sh
# Chạy toàn bộ 5 families với đủ seeds + metrics đầy đủ
# Usage:
#   bash ~/run-full-metrics.sh          # tất cả families, SEEDS=30
#   bash ~/run-full-metrics.sh N        # chỉ Family N
#   SEEDS=10 bash ~/run-full-metrics.sh # chạy nhanh kiểm tra
#
# Tránh đơ VM: max 4 jobs song song, nice -n 10

set -euo pipefail

SEEDS=${SEEDS:-30}
SIMTIME=${SIMTIME:-200}
OUTDIR="$HOME/results-fullmetrics-$(date +%Y%m%d-%H%M%S)"
LOGDIR="$OUTDIR/logs"
NS3BIN="$HOME/hsaqmaodv-ns3/ns3"
SCRATCH="fanet-sim"
MAX_JOBS=4

mkdir -p "$OUTDIR" "$LOGDIR"
echo "[INFO] Output: $OUTDIR"
echo "[INFO] SEEDS=$SEEDS, SIMTIME=$SIMTIME, MAX_JOBS=$MAX_JOBS"

# Protocols
PROTOCOLS="AODV PMAODV-3 QMAODV-3 SA-QMAODV-3 H-SAQMAODV-3"

# ── Helper: chạy 1 scenario ───────────────────────────────────────────────────
run_one() {
    local family="$1" scenario_tag="$2" extra_args="$3" seed="$4"
    local outcsv="$OUTDIR/${family}-${scenario_tag}-s${seed}.csv"
    [[ -f "$outcsv" ]] && return 0   # resume

    nice -n 10 "$NS3BIN" run "$SCRATCH" -- \
        --seed=$seed \
        --simTime=$SIMTIME \
        $extra_args \
        --outFile="$outcsv" \
        > "$LOGDIR/${family}-${scenario_tag}-s${seed}.log" 2>&1 || \
        echo "[WARN] Failed: $outcsv"
}
export -f run_one
export OUTDIR LOGDIR SIMTIME NS3BIN SCRATCH

# ── Family TVI (sweep thresholds) ────────────────────────────────────────────
run_family_tvi() {
    echo "[START] Family TVI"
    local jobs=0
    for tviHigh in 3 5 8 10 15; do
        for tviLow in 0 1 2; do
            [[ $tviLow -ge $tviHigh ]] && continue
            for seed in $(seq 1 $SEEDS); do
                run_one "TVI" "h${tviHigh}_l${tviLow}" \
                    "--protocol=H-SAQMAODV-3 --tviHigh=$tviHigh --tviLow=$tviLow \
                     --numNodes=15 --speed=20 --energyJ=30" \
                    "$seed" &
                ((jobs++))
                [[ $jobs -ge $MAX_JOBS ]] && wait && jobs=0
            done
        done
    done
    wait
    echo "[DONE] Family TVI"
}

# ── Family N (node density sweep) ────────────────────────────────────────────
run_family_n() {
    echo "[START] Family N"
    local jobs=0
    for numNodes in 5 10 15 20 25 30; do
        for proto in $PROTOCOLS; do
            for seed in $(seq 1 $SEEDS); do
                run_one "N" "n${numNodes}_${proto}" \
                    "--protocol=$proto --numNodes=$numNodes \
                     --speed=20 --energyJ=30 --mobilityModel=GaussMarkov" \
                    "$seed" &
                ((jobs++))
                [[ $jobs -ge $MAX_JOBS ]] && wait && jobs=0
            done
        done
    done
    wait
    echo "[DONE] Family N"
}

# ── Family S (speed sweep) ────────────────────────────────────────────────────
run_family_s() {
    echo "[START] Family S"
    local jobs=0
    for speed in 5 10 20 30 50; do
        for proto in $PROTOCOLS; do
            for seed in $(seq 1 $SEEDS); do
                run_one "S" "v${speed}_${proto}" \
                    "--protocol=$proto --speed=$speed \
                     --numNodes=15 --energyJ=30 --mobilityModel=GaussMarkov" \
                    "$seed" &
                ((jobs++))
                [[ $jobs -ge $MAX_JOBS ]] && wait && jobs=0
            done
        done
    done
    wait
    echo "[DONE] Family S"
}

# ── Family E (energy sweep) ───────────────────────────────────────────────────
run_family_e() {
    echo "[START] Family E"
    local jobs=0
    for energyJ in 10 20 30 40 50; do
        for proto in $PROTOCOLS; do
            for seed in $(seq 1 $SEEDS); do
                run_one "E" "e${energyJ}_${proto}" \
                    "--protocol=$proto --energyJ=$energyJ \
                     --numNodes=15 --speed=20 --mobilityModel=GaussMarkov" \
                    "$seed" &
                ((jobs++))
                [[ $jobs -ge $MAX_JOBS ]] && wait && jobs=0
            done
        done
    done
    wait
    echo "[DONE] Family E"
}

# ── Family L (load sweep) ─────────────────────────────────────────────────────
run_family_l() {
    echo "[START] Family L"
    local jobs=0
    for interval in 0.05 0.1 0.3 0.5 1.0; do
        for proto in $PROTOCOLS; do
            for seed in $(seq 1 $SEEDS); do
                run_one "L" "i${interval}_${proto}" \
                    "--protocol=$proto --pktInterval=$interval \
                     --numNodes=15 --speed=20 --energyJ=30 --mobilityModel=GaussMarkov" \
                    "$seed" &
                ((jobs++))
                [[ $jobs -ge $MAX_JOBS ]] && wait && jobs=0
            done
        done
    done
    wait
    echo "[DONE] Family L"
}

# ── Family HQA (RWP params, N sweep) ─────────────────────────────────────────
run_family_hqa() {
    echo "[START] Family HQA"
    local jobs=0
    for numNodes in 10 20 30 40 50 60 70; do
        for proto in $PROTOCOLS; do
            for seed in $(seq 1 $SEEDS); do
                run_one "HQA" "n${numNodes}_${proto}" \
                    "--protocol=$proto --numNodes=$numNodes \
                     --mobilityModel=RWP --speed=55 --energyJ=1000 \
                     --simTime=300 --area=500 --pktSize=127" \
                    "$seed" &
                ((jobs++))
                [[ $jobs -ge $MAX_JOBS ]] && wait && jobs=0
            done
        done
    done
    wait
    echo "[DONE] Family HQA"
}

# ── Merge CSV per family ──────────────────────────────────────────────────────
merge_family() {
    local family="$1"
    local merged="$OUTDIR/merged-${family}.csv"
    local first=1
    for f in "$OUTDIR"/${family}-*.csv; do
        [[ -f "$f" ]] || continue
        if [[ $first -eq 1 ]]; then
            cat "$f" > "$merged"
            first=0
        else
            tail -n +2 "$f" >> "$merged"   # skip header
        fi
    done
    echo "[MERGE] $merged"
}

# ── Main ──────────────────────────────────────────────────────────────────────
TARGET="${1:-ALL}"

case "$TARGET" in
    TVI) run_family_tvi; merge_family TVI ;;
    N)   run_family_n;   merge_family N ;;
    S)   run_family_s;   merge_family S ;;
    E)   run_family_e;   merge_family E ;;
    L)   run_family_l;   merge_family L ;;
    HQA) run_family_hqa; merge_family HQA ;;
    ALL)
        echo "[INFO] Running ALL families sequentially (safe for VM)"
        run_family_tvi; merge_family TVI
        run_family_n;   merge_family N
        run_family_s;   merge_family S
        run_family_e;   merge_family E
        run_family_l;   merge_family L
        run_family_hqa; merge_family HQA
        ;;
    *)
        echo "Usage: bash $0 [TVI|N|S|E|L|HQA|ALL]"
        exit 1 ;;
esac

echo ""
echo "=== DONE ==="
echo "Results: $OUTDIR"
echo "Next: python3 ~/plot-full-metrics.py $OUTDIR/merged-*.csv --outdir ~/figures-fullmetrics"
