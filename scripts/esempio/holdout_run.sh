#!/usr/bin/env bash
# holdout_run.sh — la catena di hold-out su piu' comuni e piu' blocchi.
#
#   bash scripts/esempio/holdout_run.sh                    # Z3 sui 5 comuni
#   bash scripts/esempio/holdout_run.sh "Z2 Z3"            # due blocchi
#   bash scripts/esempio/holdout_run.sh Z3 "037006 034027" # comuni a scelta
#
# Per ogni (comune, blocco): costruisce il constraint set senza quel blocco,
# rifitta con LO STESSO pool della corsa di produzione --- e questo e' il
# punto: fra la corsa piena e quella di hold-out deve cambiare una cosa
# sola --- e lascia i file con il suffisso, senza toccare la produzione.
#
# Il pool si legge da fit_<livello>.json della corsa piena. Se manca, il
# comune viene saltato: meglio un buco dichiarato che un confronto fra due
# campioni di taglia diversa.
set -eu

GSP="${GSP_ROOT:-$HOME/progetti/gsp}"
ANNO="${ANNO:-2024}"
LIV="${LIV:-K9C}"
BLOCCHI="${1:-Z3}"
COMUNI="${2:-037006 034027 036023 035033 099014}"

cd "$GSP"
echo "hold-out · anno $ANNO · livello $LIV"
echo "  blocchi: $BLOCCHI"
echo "  comuni : $COMUNI"
echo

for c in $COMUNI; do
  D="data/comuni/$c/constraints_$ANNO"
  FIT="$D/fit_$LIV.json"
  if [ ! -e "$FIT" ]; then
    echo "[salto] $c: manca $FIT (corsa piena non fatta)"
    continue
  fi
  POOL=$(python3 -c "import json;print(json.load(open('$FIT'))['pool'])")
  echo "== $c  (pool $POOL)"

  for b in $BLOCCHI; do
    OUT="$D/popolazione_${LIV}_senza_${b}.csv"
    if [ -e "$OUT" ] && [ "${FORZA:-0}" != "1" ]; then
      echo "   $b: gia' fatto (FORZA=1 per rifare)"
      continue
    fi
    echo "   $b: constraint set ..."
    python scripts/vincoli/cs_build.py "$c" --anno "$ANNO" --livello "$LIV" \
        --esclusioni --senza "$b" > "/tmp/cs_${c}_${b}.log" 2>&1 || {
        echo "      FALLITO (log in /tmp/cs_${c}_${b}.log)"; continue; }
    m=$(grep -o 'm=[0-9]*' "/tmp/cs_${c}_${b}.log" | tail -1)
    echo "      $m vincoli"

    echo "   $b: fit ..."
    python scripts/fit/fit_cs.py "$c" --anno "$ANNO" \
        --livello "${LIV}_senza_${b}" --pool "$POOL" --no-gibbs \
        > "/tmp/fit_${c}_${b}.log" 2>&1 || {
        echo "      FALLITO (log in /tmp/fit_${c}_${b}.log)"; continue; }
    grep -o 'MRE(alpha>0)=[0-9.e-]*' "/tmp/fit_${c}_${b}.log" | tail -1 \
        | sed 's/^/      /'
  done
done

echo
for b in $BLOCCHI; do
  echo "== confronto, blocco $b"
  python scripts/esempio/holdout_z.py --tutti --blocco "$b" --anno "$ANNO" \
      --livello "$LIV"
  echo
done
