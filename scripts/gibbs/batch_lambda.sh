#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# batch_lambda.sh — lambda converge a lambda*, e quando si ferma?
#
# Tutti i confronti fatti finora sono viziati dallo stesso difetto: run
# fermati a spostamenti cumulati di lambda diversi (sum lr = 8.0, 6.0, 6.4)
# e confrontati come se fossero asintoti. La MRE non se ne accorge perche'
# si appiattisce mentre ||lambda|| continua a crescere.
#
# Qui tutti i run vanno ben oltre sum_lr = 8, e si traccia ||lambda_t|| e
# ||lambda_t - lambda*|| a ogni iterazione.
#
#   J1  lr=0.01 costante      sum_lr = 25.0   riferimento: dove si ferma?
#   J2  lr=0.005 costante     sum_lr = 12.5   il plateau scala con lr?
#   J3  lr=0.01 tau=600       sum_lr =  9.8   il decadimento ci arriva?
#
# N=100k: KL e' risultata indipendente da N su un fattore 8 (0.1037-0.1059),
# quindi il banco piccolo e' valido e costa meta' tempo.
#
#   nohup ./batch_lambda.sh > /dev/null 2>&1 &
#   tail -f ~/progetti/gsp/regress/lab_*/progress.log
# ---------------------------------------------------------------------------
set -uo pipefail

COMUNE=017029
ANNO=2024
LIV=K10C
MIN_ALPHA=2e-4
N=100000
OUTER=2500
SWEEPS=5

SCRIPTS=~/progetti/gsp/scripts/gibbs
OUT=~/progetti/gsp/regress/lab_$(date +%Y%m%d_%H%M)
mkdir -p "$OUT"
LOG="$OUT/progress.log"
say () { echo "$(date +%H:%M:%S)  $*" | tee -a "$LOG"; }

say "=== traiettoria di lambda | N=$N outer=$OUTER sweeps=$SWEEPS ==="
say "output in $OUT"

run () {   # $1=tag  $2..=argomenti extra
    local tag=$1; shift
    say ">>> $tag  ($*)"
    python -u "$SCRIPTS/gibbs_lab.py" "$COMUNE" --anno "$ANNO" \
        --livello "$LIV" --min-alpha "$MIN_ALPHA" --pool "$N" \
        --outer "$OUTER" --sweeps "$SWEEPS" --tag "$tag" --out "$OUT" \
        "$@" > "$OUT/run_$tag.log" 2>&1
    if [ $? -ne 0 ]; then say "    FALLITO (vedi run_$tag.log)"; return; fi
    python - "$OUT/res_$tag.json" << 'PY' | tee -a "$LOG"
import json, sys
d = json.load(open(sys.argv[1]))
g = lambda k: d.get(k)
print(f"    sum_lr={g('sum_lr'):.1f}  MRE={g('mre_final'):.4f}  "
      f"MRE(an)={g('mre_analytic'):.4f}  |lam|={g('lam_norm'):.2f}  "
      f"|lam-lam*|={g('lam_dist'):.2f}  KL={g('kl_exact_gibbs'):.4f}  "
      f"H={g('H_gibbs'):.3f}")
PY
}

run "J1_const_lr010"  --lr 0.01
run "J2_const_lr005"  --lr 0.005
run "J3_decay_tau600" --lr 0.01 --lr-tau 600

# --- riepilogo ---
say ""
say "=== RIEPILOGO ==="
python - "$OUT" << 'PY' | tee -a "$LOG"
import json, glob, os, sys, csv
out = sys.argv[1]
print(f"{'tag':<18} {'sum_lr':>7} {'MRE':>7} {'MRE(an)':>8} {'|lam|':>7} "
      f"{'|lam-lam*|':>10} {'KL(e|g)':>8} {'H':>7} {'esclusa':>8}")
for f in sorted(glob.glob(os.path.join(out, "res_*.json"))):
    d = json.load(open(f))
    print(f"{d['tag']:<18} {d.get('sum_lr',0):7.1f} {d.get('mre_final',0):7.4f} "
          f"{d.get('mre_analytic',0):8.4f} {d.get('lam_norm',0):7.2f} "
          f"{d.get('lam_dist',0):10.2f} {d.get('kl_exact_gibbs',0):8.4f} "
          f"{d.get('H_gibbs',0):7.3f} {d.get('mass_excluded_gibbs',0)*100:7.2f}%")
d0 = json.load(open(sorted(glob.glob(os.path.join(out, "res_*.json")))[0]))
print(f"\n  riferimento esatto: |lambda*|={d0.get('lam_star_norm',0):.2f}  "
      f"H={d0.get('H_exact',0):.3f}  supporto={d0.get('support_exact',0):,}")
print()
# la traiettoria di |lam-lam*|: si e' fermata?
for f in sorted(glob.glob(os.path.join(out, "traj_*.csv"))):
    r = list(csv.DictReader(open(f)))
    if not r or r[-1].get("lam_dist") in (None, "", "nan"):
        continue
    d = [float(x["lam_dist"]) for x in r]
    n = len(d)
    print(f"  {os.path.basename(f)[5:-4]:<18} |lam-lam*| : "
          f"iniz={d[0]:6.2f}  meta={d[n//2]:6.2f}  fine={d[-1]:6.2f}  "
          f"min={min(d):6.2f} @ iter {r[d.index(min(d))]['iter']}")
print()
print("  Se |lam-lam*| si appiattisce ben prima della fine, i run precedenti")
print("  ERANO convergiuti e KL=0.104 e' il bias asintotico vero.")
print("  Se scende ancora a fine run, non lo erano e va esteso outer.")
print("  Se il plateau di |lam-lam*| scala con lr (J1 vs J2), e' jitter di Adam.")
PY
say "fatto."
