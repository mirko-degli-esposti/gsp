#!/usr/bin/env bash
# code_anello3.sh — estrae i riepiloghi dei diagnostici dell'anello 3
# (seam quinquennale, coerenza eta'/istruzione) per tutti i comuni in un
# unico file da incollare: note/misure/diagnostica_report_v1.0/anello3_code.txt
#
#   bash scripts/code_anello3.sh
#
set -u
GSP="${GSP_ROOT:-$HOME/progetti/gsp}"
cd "$GSP" || exit 1
OUT="note/misure/diagnostica_report_v1.0"
F="$OUT/anello3_code.txt"
: > "$F"

for C in 037006 017029 034027 036023 035033 039014 099014 038008 040012 033032 037021; do
  for T in quinq istr_eta; do
    X="$OUT/${T}_$C.txt"
    [ -s "$X" ] || continue
    { echo "################ $T $C"
      # testa: righe [info] con dimensioni e file usati
      grep -m4 '^\[info\]' "$X"
      echo "..."
      # coda: il riepilogo finale (statistiche aggregate)
      tail -22 "$X"
      echo; } >> "$F"
  done
done

wc -l "$F"
echo "-> $F  (da incollare o caricare)"
