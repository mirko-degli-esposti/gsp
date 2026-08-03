#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# preflight.sh — verifica che il rollback sia pulito PRIMA di prendere il
# baseline. Non modifica niente: solo diagnosi.
#
#   ./preflight.sh
# ---------------------------------------------------------------------------
set -uo pipefail

GSP=~/progetti/gsp
REPO=~/progetti/maxent-popsynth-pcd
G="\033[32m"; R="\033[31m"; Y="\033[33m"; O="\033[0m"
fail=0
ok ()   { printf "  ${G}OK  ${O} %s\n" "$1"; }
bad ()  { printf "  ${R}NO  ${O} %s\n" "$1"; fail=$((fail+1)); }
warn () { printf "  ${Y}??  ${O} %s\n" "$1"; }

echo "=== 1. stato git del repo ==============================================="
if [ -d "$REPO/.git" ]; then
    cd "$REPO"
    dirty=$(git status --porcelain | grep -v '^??' || true)
    if [ -z "$dirty" ]; then ok "maxent-popsynth-pcd: working tree pulito"
    else bad "maxent-popsynth-pcd ha modifiche non committate:"; echo "$dirty" | sed 's/^/        /'; fi
    untracked=$(git status --porcelain | grep '^??' || true)
    [ -n "$untracked" ] && warn "file non tracciati (innocui se sono i nuovi):" \
        && echo "$untracked" | sed 's/^/        /'
    git stash list | sed 's/^/        stash: /'
else
    warn "$REPO non e' un repo git"
fi

echo
echo "=== 2. file .py modificati nelle ultime 6 ore ==========================="
found=$(find "$GSP/scripts" "$REPO/src" -type f -name '*.py' \
        -newermt '6 hours ago' -printf '%TY-%Tm-%Td %TH:%TM  %p\n' 2>/dev/null | sort)
if [ -z "$found" ]; then ok "nessuno"; else echo "$found" | sed 's/^/        /'
    warn "controlla che siano solo i file NUOVI (fast_F, test_F, regress_fit)"; fi

echo
echo "=== 3. le patch non ci sono piu' ========================================"
grep -q "cs_g, kept_sig_g = cs, kept_sig" "$GSP/scripts/fit_cs.py" \
    && bad "fit_cs.py contiene ancora la patch 1 (dedup cs_g)" \
    || ok "fit_cs.py: patch 1 assente"
grep -q "if cs_g is cs" "$GSP/scripts/fit_cs.py" \
    && bad "fit_cs.py contiene ancora la patch 3 (F_g = F)" \
    || ok "fit_cs.py: patch 3 assente"
grep -q "F=F_g" "$GSP/scripts/fit_cs.py" \
    && bad "fit_cs.py contiene ancora la patch 4 (F passata al solver)" \
    || ok "fit_cs.py: patch 4 assente"
SOLV=$(find "$REPO/src" -name solvers.py | head -1)
if [ -n "$SOLV" ]; then
    grep -qE "def __init__.*F=None|F=None, all_tuples" "$SOLV" \
        && bad "solvers.py contiene ancora la patch (F=None nella firma)" \
        || ok "solvers.py: patch assente"
    grep -q "cart_product" "$SOLV" && ok "solvers.py: cart_product presente (originale)" \
        || bad "solvers.py: cart_product mancante -> non e' l'originale"
else
    bad "solvers.py non trovato sotto $REPO/src"
fi
CSET=$(find "$REPO/src" -name constraint_set.py | head -1)
grep -q "fast_F\|build_F_fast" "$CSET" 2>/dev/null \
    && bad "constraint_set.py gia' collegato a fast_F" \
    || ok "constraint_set.py: builder originale"

echo
echo "=== 4. i file nuovi ci sono ============================================="
for f in fast_F.py test_F.py regress_fit.py run_regression.sh; do
    [ -f "$GSP/scripts/$f" ] && ok "$f" || bad "$f manca in $GSP/scripts/"
done

echo
echo "=== 5. il codice importa ================================================"
cd "$GSP/scripts"
python - << 'PY' && ok "import di ConstraintSet / ExactMaxEntSolver riuscito" \
                 || bad "import fallito (vedi traceback sopra)"
import sys, os, glob, importlib
for base in ["~/progetti/maxent-popsynth-pcd"]:
    hits = glob.glob(os.path.expanduser(base) + "/**/constraint_set.py", recursive=True)
    if hits:
        moddir = os.path.dirname(hits[0]); sys.path.insert(0, os.path.dirname(moddir))
        pkg = os.path.basename(moddir)
        importlib.import_module(f"{pkg}.constraint_set")
        importlib.import_module(f"{pkg}.solvers")
        importlib.import_module(f"{pkg}.gibbs_pcd_solver")
        break
else:
    raise SystemExit("repo non trovato")
PY

echo
echo "=== 6. test di equivalenza di F (K6C, veloce) ==========================="
CS6=$(ls "$GSP"/data/comuni/*/constraints_*/cs_K6C.json 2>/dev/null | head -1)
if [ -n "$CS6" ]; then
    python test_F.py "$CS6" > /tmp/testF.log 2>&1 \
        && ok "test_F.py su $(basename "$(dirname "$CS6")")/cs_K6C.json: tutti passati" \
        || { bad "test_F.py fallito"; tail -20 /tmp/testF.log | sed 's/^/        /'; }
else
    warn "cs_K6C.json non trovato: salto (non bloccante)"
fi

echo
echo "========================================================================"
if [ "$fail" -eq 0 ]; then
    printf "${G}PREFLIGHT PULITO — si puo' prendere il baseline${O}\n"
    echo "   ./run_regression.sh baseline"
else
    printf "${R}*** %d problemi: risolvi prima di procedere ***${O}\n" "$fail"
fi
exit "$fail"
