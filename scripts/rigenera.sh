#!/usr/bin/env bash
# rigenera.sh — rigenerazione completa della pipeline GSP.
#
# Esegue per ogni comune: cs_build -> fit_cs -> assign_avq -> enrich.
# Un log per comune in log/rigenera_<data>/<comune>.log, piu' un riepilogo
# a video. Non cancella nulla: i file vengono sovrascritti dagli script,
# quindi fare il backup PRIMA (vedi --help).
#
# I parametri per comune stanno nella tabella COMUNI qui sotto:
#   codice:livello:pool
# Il pool e' ~1,3x la popolazione residente, in linea con quanto usato
# per le generazioni singole.
#
# Uso:
#   ./rigenera.sh                  # tutti i comuni
#   ./rigenera.sh 039014 040012    # solo quelli indicati
#   ./rigenera.sh --dry-run        # stampa i comandi senza eseguirli
#   ./rigenera.sh --no-escl        # senza --esclusioni (comportamento v1)
#   ./rigenera.sh --from avq       # riparte da assign_avq (salta cs+fit)
#
set -uo pipefail

GSP="$HOME/progetti/gsp"
ANNO=2024

# codice : livello : pool
COMUNI=(
  "037006:K9C:500000"   # Bologna    390.098
  "017029:K9C:260000"   # Brescia    198.259
  "034027:K9C:260000"   # Parma      198.121
  "036023:K9C:240000"   # Modena     184.597
  "039014:K9C:200000"   # Ravenna    156.304
  "040012:K9C:150000"   # Forli'     117.050
  "037021:K6C:30000"    # Castenaso   16.357  (non articolato)
)

ESCL="--esclusioni"
DRY=0
FROM="cs"
SEL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=1; shift ;;
    --no-escl) ESCL=""; shift ;;
    --from)    FROM="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
      echo
      echo "Backup consigliato prima di eseguire:"
      echo "  cd $GSP/data && tar czf ~/gsp_backup_\$(date +%Y%m%d_%H%M).tar.gz comuni/"
      exit 0 ;;
    *) SEL+=("$1"); shift ;;
  esac
done

STAMP=$(date +%Y%m%d_%H%M)
LOGDIR="$GSP/log/rigenera_$STAMP"
mkdir -p "$LOGDIR"
cd "$GSP" || exit 1

esegui() {   # esegui <logfile> <comando...>
  local log="$1"; shift
  if [[ $DRY -eq 1 ]]; then
    echo "    [dry] $*"
    return 0
  fi
  echo "--- $* ---" >> "$log"
  "$@" >> "$log" 2>&1
}

printf '%-10s %-10s %-8s %-9s %s\n' COMUNE LIVELLO ESITO TEMPO NOTE
printf '%.0s-' {1..64}; echo

OK=0; KO=0
for riga in "${COMUNI[@]}"; do
  IFS=: read -r COD LIV POOL <<< "$riga"
  if [[ ${#SEL[@]} -gt 0 ]] && [[ ! " ${SEL[*]} " =~ " $COD " ]]; then
    continue
  fi

  LOG="$LOGDIR/$COD.log"
  : > "$LOG"
  T0=$SECONDS
  FASE=""

  if [[ "$FROM" == "cs" ]]; then
    FASE="cs_build"
    esegui "$LOG" python scripts/cs_build.py "$COD" --anno $ANNO \
           --livello "$LIV" $ESCL || { FASE="cs_build FALLITO"; }
  fi

  if [[ -z "${FASE##*cs_build}" || "$FROM" != "cs" ]] && \
     [[ "$FASE" != *FALLITO* ]] && [[ "$FROM" =~ ^(cs|fit)$ ]]; then
    FASE="fit_cs"
    esegui "$LOG" python scripts/fit_cs.py "$COD" --anno $ANNO \
           --livello "$LIV" --eps 1e-8 --min-alpha 2e-4 \
           --pool "$POOL" --outer 500 --numba --sparse \
           --tol 0 --sweeps 40 --no-gibbs || FASE="fit_cs FALLITO"
  fi

  if [[ "$FASE" != *FALLITO* ]]; then
    FASE="assign_avq"
    esegui "$LOG" python scripts/assign_avq.py "$COD" --anno $ANNO \
           --pop-file "popolazione_${LIV}.csv" \
      || FASE="assign_avq FALLITO"
  fi

  if [[ "$FASE" != *FALLITO* ]]; then
    FASE="enrich"
    esegui "$LOG" python scripts/enrich.py "$COD" --anno $ANNO \
           --pop-file "popolazione_${LIV}_avq.csv" \
      || FASE="enrich FALLITO"
  fi

  DT=$((SECONDS - T0))
  if [[ "$FASE" == *FALLITO* ]]; then
    KO=$((KO+1))
    printf '%-10s %-10s %-8s %-9s %s\n' "$COD" "$LIV" "KO" "${DT}s" "$FASE"
  else
    OK=$((OK+1))
    NOTA=""
    if [[ $DRY -eq 0 ]]; then
      NOTA=$(grep -m1 '^\[3c\] paese' "$LOG" | sed 's/.*tier /tier /;s/ |.*//')
    fi
    printf '%-10s %-10s %-8s %-9s %s\n' "$COD" "$LIV" "ok" "${DT}s" "$NOTA"
  fi
done

echo
echo "log in $LOGDIR"
echo "$OK completati, $KO falliti"

if [[ $DRY -eq 0 && $KO -eq 0 ]]; then
  echo
  echo "--- verifica combinazioni impossibili ---"
  python - <<'PYEOF'
import glob, sys, pandas as pd
sys.path.insert(0, "scripts")
import gsp_common as G
tot_i = tot_n = 0
for f in sorted(glob.glob("data/comuni/*/constraints_2024/popolazione_K*_avq_full.csv")):
    c = f.split("/")[2]
    d = pd.read_csv(f, low_memory=False)
    n = sum(int(d[d[va].isin(A) & d[vb].isin(B)].shape[0])
            for va, A, vb, B, _ in G.IMPOSSIBILI
            if va in d.columns and vb in d.columns)
    tot_i += n; tot_n += len(d)
    print(f"  {c}  {G.info(c)['nome']:<12} {n:>5} su {len(d):>9,}  "
          f"({d.shape[1]} colonne)")
print(f"  {'TOTALE':<26} {tot_i:>5} su {tot_n:>9,}")
PYEOF
fi
