#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# batch_scaling.sh — scaling in N del GibbsPCD a K10C.
#
# Domanda: il residuo di MRE al plateau (0.046 a N=400k, contro 0.037 attesi
# se fosse solo rumore) e' rumore di campionamento o bias sistematico?
#
#   pavimento ~ 1/sqrt(N)   ->  se e' rumore, la MRE scende come 1/sqrt(N)
#   bias relativo costante  ->  se e' bias, la MRE si appiattisce su di esso
#
# Previsioni (pavimento a 400k = 0.0465, osservato 0.0462):
#            N        pavim.   se rumore   se bias 2.7%
#         200000      0.0658     0.053        0.059
#         400000      0.0465     0.037        0.046   <- osservato
#         800000      0.0329     0.026        0.038
#
# I run sono SEQUENZIALI: il kernel Numba usa gia' tutti i thread, e due job
# in parallelo si contenderebbero la banda di memoria senza guadagno.
#
#   nohup ./batch_scaling.sh > /dev/null 2>&1 &
#   tail -f ~/progetti/gsp/regress/scaling_*/progress.log
# ---------------------------------------------------------------------------
set -uo pipefail

COMUNE=017029
ANNO=2024
LIV=K10C
EPS=1e-8
MIN_ALPHA=2e-4
OUTER=800
SWEEPS=5                       # 5 e 10 danno lo stesso risultato; 3 destabilizza

GSP=~/progetti/gsp
CDIR=$GSP/data/comuni/$COMUNE/constraints_$ANNO
SCRIPTS=$GSP/scripts/gibbs
OUT=$GSP/regress/scaling_$(date +%Y%m%d_%H%M)
mkdir -p "$OUT"
LOG="$OUT/progress.log"

# N in ordine di valore diagnostico: 800k per primo, cosi' se il tempo finisce
# il run decisivo e' comunque completo.
POOLS=(800000 200000 100000)

say () { echo "$(date +%H:%M:%S)  $*" | tee -a "$LOG"; }

# --- il fit esatto va congelato: --no-exact rilegge lambdas_exact da
#     fit_<LIV>.json, che ogni run sovrascrive. Senza questo, il run 2
#     userebbe i lambda scritti dal run 1.
CANON="$OUT/fit_${LIV}_canonico.json"
if [ ! -f "$CDIR/fit_$LIV.json" ]; then
    say "ERRORE: manca $CDIR/fit_$LIV.json (serve per --no-exact)"; exit 1
fi
cp "$CDIR/fit_$LIV.json" "$CANON"
python - "$CANON" << 'PY' | tee -a "$LOG"
import json, sys
d = json.load(open(sys.argv[1]))
n = len(d.get("lambdas_exact") or [])
print(f"[canone] lambdas_exact: {n} valori | min_alpha={d.get('min_alpha')} "
      f"eps={d.get('eps')}")
if n == 0:
    sys.exit("ERRORE: fit_<LIV>.json non contiene lambdas_exact")
PY
[ ${PIPESTATUS[0]} -eq 0 ] || exit 1

say "=== scaling in N: ${POOLS[*]} | outer=$OUTER sweeps=$SWEEPS ==="
say "output in $OUT"

for N in "${POOLS[@]}"; do
    TAG="N${N}"
    say ">>> $TAG  (outer=$OUTER, sweeps=$SWEEPS)"
    cp "$CANON" "$CDIR/fit_$LIV.json"          # riparti sempre dagli stessi lambda

    /usr/bin/time -v python -u "$SCRIPTS/fit_cs.py" "$COMUNE" \
        --anno "$ANNO" --livello "$LIV" --eps "$EPS" --min-alpha "$MIN_ALPHA" \
        --pool "$N" --outer "$OUTER" --sweeps "$SWEEPS" \
        --numba --sparse --no-exact --tol 0 \
        > "$OUT/run_$TAG.log" 2>&1

    if [ $? -ne 0 ]; then
        say "    FALLITO (vedi run_$TAG.log)"; continue
    fi

    cp "$CDIR/fit_$LIV.json"  "$OUT/fit_$TAG.json"
    cp "$CDIR/pool_$LIV.csv"  "$OUT/pool_$TAG.csv" 2>/dev/null

    python "$SCRIPTS/check_marginals.py" "$COMUNE" --anno "$ANNO" \
        --livello "$LIV" --pops "$OUT/pool_$TAG.csv" --min-alpha "$MIN_ALPHA" \
        --csv "$OUT/marg_$TAG.csv" > "$OUT/marg_$TAG.log" 2>&1

    say "    $(grep -E '^\[gibbs\] fit in' "$OUT/run_$TAG.log" | tail -1)"
    say "    $(grep -E '^\[cmp\]' "$OUT/run_$TAG.log" | tail -1)"
    say "    $(grep 'rapporto MRE/pavimento' "$OUT/marg_$TAG.log" | head -1)"
done

# --- riepilogo ---
cp "$CANON" "$CDIR/fit_$LIV.json"
say ""
say "=== RIEPILOGO ==="
python - "$OUT" << 'PY' | tee -a "$LOG"
import sys, os, re, glob, json
out = sys.argv[1]
print(f"{'N':>9} {'MRE':>8} {'pavim.':>8} {'rapp.':>6} {'|z|med':>7} "
      f"{'KL(e|g)':>9} {'KL(g|e)':>9} {'H':>7} {'esclusa':>8} {'t':>7}")
rows = []
for f in sorted(glob.glob(os.path.join(out, "run_N*.log"))):
    N = int(re.search(r"run_N(\d+)\.log", f).group(1))
    t = open(f).read()
    g = lambda p: (re.search(p, t).group(1) if re.search(p, t) else "?")
    m = os.path.join(out, f"marg_N{N}.log")
    mt = open(m).read() if os.path.exists(m) else ""
    gm = lambda p: (re.search(p, mt).group(1) if re.search(p, mt) else "?")
    rows.append((N,
        g(r"final_mre\(repo\)=([\d.]+)"),
        gm(r"pavimento predetto\s+([\d.]+)"),
        gm(r"rapporto MRE/pavimento\s+([\d.]+)"),
        gm(r"\|z\| mediano\s+([\d.]+)"),
        g(r"KL\(exact\|\|gibbs\)=([\d.e+-]+)"),
        g(r"KL\(gibbs\|\|exact\)=([\d.e+-]+)"),
        g(r"H=([\d.]+) nat"),
        g(r"celle escluse \(pre-azzeramento\): ([\d.e+-]+)"),
        g(r"fit in ([\d.]+)s")))
for r in sorted(rows):
    print(f"{r[0]:>9,} {r[1]:>8} {r[2]:>8} {r[3]:>6} {r[4]:>7} "
          f"{r[5]:>9} {r[6]:>9} {r[7]:>7} {r[8]:>8} {r[9]:>7}")
print()
print("  Se il residuo e' RUMORE: 'rapp.' resta ~0.80 a ogni N, e la MRE")
print("  scende come 1/sqrt(N).")
print("  Se e' BIAS: 'rapp.' CRESCE al crescere di N (il pavimento scende,")
print("  il bias no), e la MRE si appiattisce.")
PY
say "fatto. dettaglio per vincolo in $OUT/marg_N*.csv"
