#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run_regression.sh — test di regressione a tre stadi per le patch su F.
#
#   stadio 0  baseline   codice NON patchato
#   stadio 1  patch 1-4  (F passata al solver; dedup di F_g se eps==0)
#   stadio 2  builder    build_indicator_matrix -> build_F_fast
#
# In tutti gli stadi lambdas_exact, diagnostiche e popolazione_*.csv devono
# uscire IDENTICI bit per bit. Cambiano solo tempo e memoria.
#
#   ./run_regression.sh baseline     # PRIMA di applicare qualsiasi patch
#   ./run_regression.sh check        # DOPO ogni stadio
#
# Variabili (default fra parentesi):
#   COMUNE (017029)  ANNO (2024)  LIV (K7C)  EPS (1e-8)  MIN_ALPHA (2e-4)
#   SPARSE (0 -> densa; 1 -> aggiunge --sparse)
# ---------------------------------------------------------------------------
set -uo pipefail

COMUNE=${COMUNE:-017029}
ANNO=${ANNO:-2024}
LIV=${LIV:-K7C}
EPS=${EPS:-1e-8}
MIN_ALPHA=${MIN_ALPHA:-2e-4}
SPARSE=${SPARSE:-0}

GSP=~/progetti/gsp
CDIR=$GSP/data/comuni/$COMUNE/constraints_$ANNO
BASE=$GSP/regress/baseline_${COMUNE}_${ANNO}_${LIV}_eps${EPS}_ma${MIN_ALPHA}
SCRIPTS=$GSP/scripts

# --no-gibbs obbligatorio: GibbsPCDSolver non e' seeded, non e' riproducibile
#   run-to-run e sporcherebbe il confronto.
# NIENTE --no-exact: riuserebbe i lambdas salvati e il test sarebbe vuoto.
CMD=(python -u "$SCRIPTS/fit_cs.py" "$COMUNE" --anno "$ANNO" --livello "$LIV"
     --eps "$EPS" --min-alpha "$MIN_ALPHA" --no-gibbs)
[ "$SPARSE" = "1" ] && CMD+=(--sparse)

if [ -x /usr/bin/time ]; then TIMER=(/usr/bin/time -v); else TIMER=(); fi

run_and_log () {
    echo "    ${CMD[*]}"
    "${TIMER[@]}" "${CMD[@]}" 2>&1 | tee "$1" \
        | grep -E "^\[(cs|mem|exact|pop|done)\]|Elapsed \(wall|Maximum resident"
    return 0
}

summarize () {
    echo ">>> tempo e memoria"
    for tag in "Elapsed (wall" "Maximum resident"; do
        printf "  %-20s baseline: %s\n" "$tag" \
            "$(grep -F "$tag" "$1" 2>/dev/null | tail -1 | sed 's/^ *//')"
        printf "  %-20s nuovo   : %s\n" "$tag" \
            "$(grep -F "$tag" "$2" 2>/dev/null | tail -1 | sed 's/^ *//')"
    done
}

case "${1:-}" in
  baseline)
    echo ">>> STADIO 0 — baseline col codice ATTUALE (deve essere non patchato)"
    mkdir -p "$BASE"
    run_and_log "$BASE/run.log"
    for f in "fit_$LIV.json" "popolazione_$LIV.csv"; do
        [ -f "$CDIR/$f" ] || { echo "manca $CDIR/$f: il run e' fallito?" >&2; exit 3; }
        cp "$CDIR/$f" "$BASE/"
    done
    echo
    echo "baseline in $BASE"
    ls -l "$BASE" | sed 's/^/    /'
    echo "ora applica le patch, poi:  ./run_regression.sh check"
    ;;

  check)
    [ -f "$BASE/fit_$LIV.json" ] || {
        echo "manca il baseline in $BASE" >&2
        echo "lancia prima:  ./run_regression.sh baseline" >&2; exit 2; }
    echo ">>> run col codice patchato (stessa riga di comando)"
    run_and_log /tmp/regress_run.log
    echo
    python "$SCRIPTS/regress_fit.py" \
        "$BASE/fit_$LIV.json" "$CDIR/fit_$LIV.json" \
        --csv "$BASE/popolazione_$LIV.csv" "$CDIR/popolazione_$LIV.csv"
    rc=$?
    echo
    summarize "$BASE/run.log" /tmp/regress_run.log
    exit $rc
    ;;

  *)
    sed -n '2,20p' "$0"
    exit 1
    ;;
esac
