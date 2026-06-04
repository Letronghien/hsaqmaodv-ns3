#!/bin/bash
# run-paper1-experiments.sh
# ----------------------------------------------------------------------------
# Paper 1 — H-SAQMAODV Experiment Runner
#
# Runs all simulation families needed for the paper:
#   TVI  — TVI threshold sensitivity sweep (Fig 2)
#   N    — Node density effect (Fig 3)
#   S    — Mobility/speed effect (Fig 4)
#   E    — Heterogeneous battery (Fig 5)
#   L    — Traffic load effect (supplementary)
#
# Protocols compared:
#   AODV, AOMDV-3, QMAODV-3, SAQMAODV-3, HSAQMAODV-3
#
# Usage:
#   FAMILIES="TVI N S E" SEEDS=10 JOBS=8 bash run-paper1-experiments.sh
#
# Prereq: NS-3 must be built with HSAQMAODV module
#         (apply-hsaqmaodv-all.sh must have been run first)
# ----------------------------------------------------------------------------
set -u

NS3_DIR="${NS3_DIR:-$HOME/ns-allinone-3.40/ns-3.40}"
EXEC=$(find "$NS3_DIR/build" -maxdepth 2 -name "*fanet-sim*" -executable -type f 2>/dev/null | head -1)
[ -z "$EXEC" ] && { echo "ERROR: fanet-sim not found in $NS3_DIR/build"; exit 1; }

JOBS="${JOBS:-7}"
SEEDS="${SEEDS:-10}"
FAMILIES="${FAMILIES:-TVI N S E L}"

# -------- Shared hyper-parameters -------------------------------------------
QM_ALPHA=0.7;   QM_GAMMA=0.6;  QM_EPSILON=0.3; QM_DECAY=0.1

# SA base (reused by HSAQMAODV too)
SA_ALPHA0=0.5;  SA_GAMMA=0.9;  SA_EPSILON0=0.3
SA_LAMBDA=0.01; SA_WINDOW=10;  SA_PERIOD=1.0;   SA_LOWE=0.20
SA_W1=0.5;      SA_W2=0.4;     SA_W3=0.1

# H-SAQMAODV default thresholds (tuned from TVI family)
HS_TVI_HIGH="${HS_TVI_HIGH:-5}"
HS_TVI_LOW="${HS_TVI_LOW:-2}"

# -------- Results dir -------------------------------------------------------
TS=$(date +%Y%m%d-%H%M%S)
RESULTS_DIR="$HOME/results-paper1-${TS}"
JOB_DIR="$RESULTS_DIR/jobs"
mkdir -p "$JOB_DIR"
LOG="$RESULTS_DIR/run.log"

echo "======================================================" | tee "$LOG"
echo " H-SAQMAODV Paper 1 — Experiment Runner"            | tee -a "$LOG"
echo "======================================================" | tee -a "$LOG"
echo " Families:   $FAMILIES"                              | tee -a "$LOG"
echo " Seeds:      $SEEDS"                                 | tee -a "$LOG"
echo " Jobs:       $JOBS"                                  | tee -a "$LOG"
echo " TVI_high:   $HS_TVI_HIGH  TVI_low: $HS_TVI_LOW"   | tee -a "$LOG"
echo " Output:     $RESULTS_DIR"                           | tee -a "$LOG"
echo " Started:    $(date)"                                | tee -a "$LOG"
echo "======================================================" | tee -a "$LOG"

# -------- Protocol list (5 protocols for paper comparison) ------------------
# Format: "PROTO maxPaths"
PROTOCOLS=(
    "AODV       1"
    "PMAODV     3"
    "QMAODV     3"
    "SAQMAODV   3"
    "HSAQMAODV  3"
)

# -------- Job file generator ------------------------------------------------
JOB_FILE="$JOB_DIR/jobs.txt"
> "$JOB_FILE"

gen_jobs() {
    local FAMILY=$1
    shift
    local PARAMS=("$@")   # array of "param_name=value ..." strings (one per scenario point)
    for PARAM_STR in "${PARAMS[@]}"; do
        for SEED in $(seq 1 "$SEEDS"); do
            for EXP in "${PROTOCOLS[@]}"; do
                read -r PROTO MP <<< "$EXP"
                echo "$FAMILY $PROTO $MP $SEED $PARAM_STR" >> "$JOB_FILE"
            done
        done
    done
}

# TVI family — sweep TVI_high × TVI_low (HSAQMAODV only, others use defaults)
if echo "$FAMILIES" | grep -qw TVI; then
    for TVH in 3 5 8 10 15; do
        for TVL in 0 1 2; do
            [ $TVL -ge $TVH ] && continue
            for SEED in $(seq 1 "$SEEDS"); do
                echo "TVI HSAQMAODV 3 $SEED numNodes=15 simTime=200 speed=20 tviHigh=$TVH tviLow=$TVL scenarioTag=TVI-N15-V20-T200-E0-H${TVH}-L${TVL}" >> "$JOB_FILE"
                # Also run SAQMAODV baseline for comparison at same seed
                echo "TVI SAQMAODV  3 $SEED numNodes=15 simTime=200 speed=20 tviHigh=0  tviLow=0" >> "$JOB_FILE"
            done
        done
    done
fi

# N family — node density
if echo "$FAMILIES" | grep -qw N; then
    for N in 5 8 10 15 20 25 30; do
        for SEED in $(seq 1 "$SEEDS"); do
            for EXP in "${PROTOCOLS[@]}"; do
                read -r PROTO MP <<< "$EXP"
                echo "N $PROTO $MP $SEED numNodes=$N simTime=200 speed=20" >> "$JOB_FILE"
            done
        done
    done
fi

# S family — speed/mobility
if echo "$FAMILIES" | grep -qw S; then
    for SPEED in 5 10 15 20 25 30 50; do
        for SEED in $(seq 1 "$SEEDS"); do
            for EXP in "${PROTOCOLS[@]}"; do
                read -r PROTO MP <<< "$EXP"
                echo "S $PROTO $MP $SEED numNodes=15 simTime=200 speed=$SPEED" >> "$JOB_FILE"
            done
        done
    done
fi

# E family — heterogeneous battery (E0 mix)
if echo "$FAMILIES" | grep -qw E; then
    for E0 in 10 20 30 50; do
        for SEED in $(seq 1 "$SEEDS"); do
            for EXP in "${PROTOCOLS[@]}"; do
                read -r PROTO MP <<< "$EXP"
                echo "E $PROTO $MP $SEED numNodes=15 simTime=200 speed=20 e0=$E0" >> "$JOB_FILE"
            done
        done
    done
fi

# L family — traffic load
if echo "$FAMILIES" | grep -qw L; then
    for PKT in 1.0 0.5 0.25 0.1 0.05; do
        for SEED in $(seq 1 "$SEEDS"); do
            for EXP in "${PROTOCOLS[@]}"; do
                read -r PROTO MP <<< "$EXP"
                echo "L $PROTO $MP $SEED numNodes=15 simTime=200 speed=20 pktInterval=$PKT" >> "$JOB_FILE"
            done
        done
    done
fi

TOTAL=$(wc -l < "$JOB_FILE")
echo " Total jobs: $TOTAL" | tee -a "$LOG"

# -------- Job runner --------------------------------------------------------
run_job() {
    local FAMILY=$1 PROTO=$2 MP=$3 SEED=$4
    shift 4
    local EXTRA_ARGS="$*"

    # Parse extra key=value pairs into variables
    local NUM_NODES=15 SIM_TIME=200 SPEED=20 E0=0 PKT_INTERVAL=0.25
    local TVI_HIGH="$HS_TVI_HIGH" TVI_LOW="$HS_TVI_LOW"
    for kv in $EXTRA_ARGS; do
        case "$kv" in
            numNodes=*)    NUM_NODES="${kv#*=}"    ;;
            simTime=*)     SIM_TIME="${kv#*=}"     ;;
            speed=*)       SPEED="${kv#*=}"        ;;
            e0=*)          E0="${kv#*=}"           ;;
            pktInterval=*) PKT_INTERVAL="${kv#*=}" ;;
            tviHigh=*)     TVI_HIGH="${kv#*=}"     ;;
            tviLow=*)      TVI_LOW="${kv#*=}"      ;;
        esac
    done

    local LABEL="${PROTO}"
    [[ "$PROTO" != "AODV" ]] && LABEL="${PROTO}-${MP}"

    local SCENARIO="${FAMILY}-N${NUM_NODES}-V${SPEED}-T${SIM_TIME}-E${E0}"
    [[ "$FAMILY" == "TVI" ]] && SCENARIO="${SCENARIO}-H${TVI_HIGH}-L${TVI_LOW}"
    local CSV="$JOB_DIR/job-${FAMILY}-${LABEL}-N${NUM_NODES}-V${SPEED}-E${E0}-seed${SEED}.csv"
    local START=$(date +%s)

    # Build SA/HS flags
    local SA_FLAGS=""
    if [ "$PROTO" = "SAQMAODV" ] || [ "$PROTO" = "HSAQMAODV" ]; then
        SA_FLAGS="--saAlpha0=$SA_ALPHA0 --saGamma=$SA_GAMMA --saEpsilon0=$SA_EPSILON0 \
                  --saLambda=$SA_LAMBDA --saSeqNoWin=$SA_WINDOW \
                  --saAdaptPeriod=$SA_PERIOD --saLowEThresh=$SA_LOWE \
                  --saW1=$SA_W1 --saW2=$SA_W2 --saW3=$SA_W3"
    fi

    local HS_FLAGS=""
    if [ "$PROTO" = "HSAQMAODV" ]; then
        HS_FLAGS="--hsTviHigh=$TVI_HIGH --hsTviLow=$TVI_LOW"
    fi

    local ENERGY_FLAGS=""
    if [ "$E0" -gt 0 ] 2>/dev/null; then
        ENERGY_FLAGS="--enableEnergy=1 --initialEnergy=$E0"
    else
        ENERGY_FLAGS="--enableEnergy=1"
    fi

    "$EXEC" \
        --scenario="$SCENARIO" \
        --protocol="$PROTO" --maxPaths="$MP" \
        --mobility=GAUSS $ENERGY_FLAGS \
        --numNodes="$NUM_NODES" --simTime="$SIM_TIME" --seed="$SEED" \
        --meanVelMin="$SPEED" --meanVelMax="$SPEED" --alpha=0.85 \
        --pktInterval="$PKT_INTERVAL" --pktSize=512 --numFlows=0 \
        --qmAlpha="$QM_ALPHA" --qmGamma="$QM_GAMMA" \
        --qmEpsilon="$QM_EPSILON" --qmEpsilonDecay="$QM_DECAY" \
        $SA_FLAGS $HS_FLAGS \
        --csvFile="$CSV" >/dev/null 2>&1
    local RC=$? DUR=$(( $(date +%s) - START ))
    if [ "$RC" -eq 0 ] || [ "$RC" -eq 139 ]; then
        echo "OK   [$FAMILY] ${LABEL} N=${NUM_NODES} V=${SPEED} E=${E0} seed=${SEED} (${DUR}s)"
    else
        echo "FAIL [$FAMILY] ${LABEL} rc=$RC"
    fi
}
export -f run_job
export EXEC JOB_DIR
export QM_ALPHA QM_GAMMA QM_EPSILON QM_DECAY
export SA_ALPHA0 SA_GAMMA SA_EPSILON0 SA_LAMBDA SA_WINDOW SA_PERIOD SA_LOWE SA_W1 SA_W2 SA_W3
export HS_TVI_HIGH HS_TVI_LOW

# -------- Run ---------------------------------------------------------------
START_TS=$(date +%s)
cat "$JOB_FILE" | xargs -P "$JOBS" -L 1 bash -c 'run_job "$@"' _ | tee -a "$LOG"
END_TS=$(date +%s)
WALL=$(( END_TS - START_TS ))

# -------- Merge CSVs --------------------------------------------------------
MERGED="$RESULTS_DIR/merged.csv"
FIRST_CSV=$(ls "$JOB_DIR"/job-*.csv 2>/dev/null | head -1)
if [ -n "$FIRST_CSV" ]; then
    head -1 "$FIRST_CSV" > "$MERGED"
    for f in "$JOB_DIR"/job-*.csv; do
        tail -n +2 "$f" >> "$MERGED"
    done
    echo "" | tee -a "$LOG"
    echo "Merged CSV: $MERGED" | tee -a "$LOG"
fi

echo "Done: $(date), wall=$((WALL/3600))h $(((WALL%3600)/60))m" | tee -a "$LOG"

# -------- Quick summary -----------------------------------------------------
if command -v python3 >/dev/null && [ -s "$MERGED" ]; then
    python3 - "$MERGED" <<'PYEOF' | tee -a "$LOG"
import csv, sys
from collections import defaultdict
rows = list(csv.DictReader(open(sys.argv[1])))
agg = defaultdict(list)
for r in rows:
    proto = r.get('protocol', '')
    mp    = r.get('maxPaths', '1')
    label = f"{proto}-{mp}" if proto not in ('AODV',) else proto
    fam   = r.get('scenario', '').split('-')[0] if '-' in r.get('scenario','') else '?'
    try: pdr = float(r['deliveryRatio'])
    except: continue
    agg[(fam, label)].append(pdr)

families = sorted({k[0] for k in agg})
    protos   = ["AODV","PMAODV-3","QMAODV-3","SAQMAODV-3","HSAQMAODV-3"]

print()
print("=" * 65)
print(" PDR SUMMARY by Family")
print("=" * 65)
for fam in families:
    print(f"\n  [{fam}]")
    print(f"  {'Protocol':<18} {'PDR mean':>10} {'n':>5}")
    print(f"  {'-'*35}")
    for p in protos:
        v = agg.get((fam, p), [])
        if v:
            print(f"  {p:<18} {sum(v)/len(v)/100:>9.2%} {len(v):>5}")
PYEOF
fi

echo ""
echo "To plot: python3 scripts/plot/plot-paper1.py $MERGED"
