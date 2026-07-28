#!/usr/bin/env bash
# run_avq.sh — job anello-2 AVQ, a bassa priorita', convivente con fit_cs.
# uso: ./run_avq.sh [COMUNE] [ANNO] [POP_IN] [TAG]
set -euo pipefail

COMUNE="${1:-017029}"
ANNO="${2:-2024}"
POPIN="${3:-popolazione_K9C_naz.csv}"
TAG="${4:-v2}"
TARGETS="${5:-AMBIENTE,FIDUCIA,SALUTE,CRONI,FUMO,MH,BMI,BMIMIN,CPESO}"

GSP="$HOME/progetti/gsp"
CDIR="$GSP/data/comuni/$COMUNE/constraints_$ANNO"
SCRIPT="$GSP/scripts/assign_avq.py"
OUTNAME="popolazione_K9C_avq_${TAG}.csv"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOGDIR="$GSP/log"; mkdir -p "$LOGDIR"
LOG="$LOGDIR/avq_${COMUNE}_${ANNO}_${TAG}_${STAMP}.log"

# --- guardie ---------------------------------------------------------------
[[ "${CONDA_DEFAULT_ENV:-}" == "ml" ]] || {
  echo "!! env conda non e' 'ml' (e' '${CONDA_DEFAULT_ENV:-none}')"; exit 1; }
[[ -f "$SCRIPT" ]]          || { echo "!! manca $SCRIPT"; exit 1; }
[[ -d "$CDIR" ]]            || { echo "!! manca $CDIR"; exit 1; }
[[ -f "$CDIR/$POPIN" ]]     || { echo "!! manca $CDIR/$POPIN"; exit 1; }
[[ -e "$CDIR/$OUTNAME" ]]   && { echo "!! $OUTNAME esiste gia'"; exit 1; }

# --- backup dell'output corrente (se c'e') ---------------------------------
PREV="$CDIR/popolazione_K9C_avq.csv"
if [[ -f "$PREV" ]]; then
  BAK="$CDIR/backup"; mkdir -p "$BAK"
  cp -p "$PREV" "$BAK/popolazione_K9C_avq_${STAMP}.csv"
  echo "[bak] $BAK/popolazione_K9C_avq_${STAMP}.csv"
fi

# --- niente oversubscription: il fit ha la precedenza ----------------------
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1

echo "[run] $COMUNE $ANNO | in=$POPIN out=$OUTNAME"
echo "[run] log -> $LOG"
echo "[run] targets=$TARGETS"
free -g | head -2

nice -n 19 ionice -c3 \
  python -u "$SCRIPT" "$COMUNE" \
    --anno "$ANNO" \
    --pop-file "$POPIN" \
    --out "$OUTNAME" \
    --targets "$TARGETS" \
    --min-record 20 \
    --seed 42 \
  2>&1 | tee "$LOG"

echo "[done] $CDIR/$OUTNAME"
