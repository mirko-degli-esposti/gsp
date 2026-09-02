#!/usr/bin/env bash
# rigenera.sh — rigenerazione completa della pipeline GSP.
#
# Esegue per ogni comune: cs_build -> fit_cs -> assign_avq -> enrich -> nucleo.
# Un log per comune in log/rigenera_<data>/<comune>.log, piu' un riepilogo
# a video e commit.txt con HEAD e stato dell'albero. Non cancella nulla: i
# file vengono sovrascritti dagli script, quindi fare il backup PRIMA
# (vedi --help). Con --confronta <archivio> confronta a fine corsa i quattro
# prodotti di ogni comune (anelli 1-4) con quelli archiviati, byte a byte.
#
# I parametri per comune (codice:livello:pool) vengono dal registro
# flotta/comuni.yaml via `python -m gsp.common --righe-rigenera`; il pool
# e' ~1,3x la popolazione residente.
# Uso:
#   ./rigenera.sh                  # tutti i comuni
#   ./rigenera.sh 039014 040012    # solo quelli indicati
#   ./rigenera.sh --dry-run        # stampa i comandi senza eseguirli
#   ./rigenera.sh --no-escl        # senza --esclusioni (comportamento v1)
#   ./rigenera.sh --from avq       # riparte da assign_avq (salta cs+fit)
#   ./rigenera.sh --from nucleo    # solo l'anello 4
#   ./rigenera.sh --confronta ~/archivio_gsp/pre_rilancio_20260819
#                                  # cmp con l'archivio (test di determinismo)
#
set -uo pipefail

GSP="${GSP_ROOT:-$HOME/progetti/gsp}"
ANNO=2024

# codice : livello : pool — DERIVATI dal registro flotta/comuni.yaml.
# Qui non si scrive piu' nulla a mano: un comune entra in flotta con
# l'emettitore (python -m gsp.campagna --emetti / --promuovi-in-flotta),
# e questo array e' una vista del registro. Chi cerca la lista la trova
# in un posto solo.
mapfile -t COMUNI < <(python -m gsp.common --righe-rigenera)
[[ ${#COMUNI[@]} -gt 0 ]] || {
  echo "registro vuoto o illeggibile: 'python -m gsp.common --righe-rigenera' fallisce?" >&2
  exit 1
}
ESCL="--esclusioni"
DRY=0
FROM="cs"
CONFR=""
SEL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=1; shift ;;
    --no-escl) ESCL=""; shift ;;
    --from)    FROM="$2"; shift 2 ;;
        --confronta)
      CONFR="$2"; shift 2
      [[ -d "$CONFR" ]] || { echo "archivio inesistente: $CONFR" >&2; exit 1; }
      ;;
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
{ echo "GSP_ROOT=$GSP"; echo "HEAD=$(git rev-parse HEAD)"; echo "branch=$(git branch --show-current)";
  echo "date=$(date -Iseconds)"; echo "args=$*"; echo "--- git status --short (deve essere vuoto per un rilancio citabile):";
  git status --short; } > "$LOGDIR/commit.txt"
if [[ -n "$(git status --short)" ]]; then
  echo "[avviso] albero non pulito: vedi $LOGDIR/commit.txt (il rilancio non e' citabile per commit)"
fi

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
    esegui "$LOG" python scripts/vincoli/cs_build.py "$COD" --anno $ANNO \
           --livello "$LIV" $ESCL || { FASE="cs_build FALLITO"; }
  fi

  if [[ -z "${FASE##*cs_build}" || "$FROM" != "cs" ]] && \
     [[ "$FASE" != *FALLITO* ]] && [[ "$FROM" =~ ^(cs|fit)$ ]]; then
    FASE="fit_cs"
    esegui "$LOG" python scripts/fit/fit_cs.py "$COD" --anno $ANNO \
           --livello "$LIV" --eps 1e-8 --min-alpha 2e-4 \
           --pool "$POOL" --outer 500 --numba --sparse \
           --tol 0 --sweeps 40 --no-gibbs || FASE="fit_cs FALLITO"
  fi

  if [[ "$FASE" != *FALLITO* ]] && [[ "$FROM" =~ ^(cs|fit|avq)$ ]]; then
    FASE="assign_avq"
    esegui "$LOG" python scripts/attributi/assign_avq.py "$COD" --anno $ANNO \
           --pop-file "popolazione_${LIV}.csv" \
      || FASE="assign_avq FALLITO"
  fi

  if [[ "$FASE" != *FALLITO* ]] && [[ "$FROM" =~ ^(cs|fit|avq|enrich)$ ]]; then
    FASE="enrich"
    esegui "$LOG" python scripts/attributi/enrich.py "$COD" --anno $ANNO \
           --pop-file "popolazione_${LIV}_avq.csv" \
      || FASE="enrich FALLITO"
  fi

  if [[ "$FASE" != *FALLITO* ]]; then
    FASE="nucleo"
    esegui "$LOG" python scripts/attributi/assign_nucleo.py "$COD" --anno $ANNO \
      || FASE="nucleo FALLITO"
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
import gsp.common as G
tot_i = tot_n = 0
for f in sorted(glob.glob("data/comuni/*/constraints_2024/popolazione_K*_avq_full.csv")):
    if "K10C" in f:        # residuo sperimentale di Brescia, mai in produzione
        continue
    c = f.split("/")[2]
    d = pd.read_csv(f, low_memory=False)
    n = sum(int(d[d[va].isin(A) & d[vb].isin(B)].shape[0])
            for va, A, vb, B, _ in G.IMPOSSIBILI
            if va in d.columns and vb in d.columns)
    tot_i += n; tot_n += len(d)
    print(f"  {c}  {G.info(c)['nome'][:18]:<18} {n:>5} su {len(d):>9,}  "
          f"({d.shape[1]} colonne)")
print(f"  {'TOTALE':<26} {tot_i:>5} su {tot_n:>9,}")
PYEOF
fi

if [[ $DRY -eq 0 && -n "$CONFR" ]]; then
  echo
  echo "--- confronto con l'archivio: $CONFR ---"
  printf '%-10s %-8s %-8s %-8s %-8s\n' COMUNE anello1 anello2 anello3 anello4
  for riga in "${COMUNI[@]}"; do
    IFS=: read -r COD LIV POOL <<< "$riga"
    if [[ ${#SEL[@]} -gt 0 ]] && [[ ! " ${SEL[*]} " =~ " $COD " ]]; then continue; fi
    D="data/comuni/$COD/constraints_$ANNO"
    R=()
    for F in "$D/popolazione_${LIV}.csv" "$D/popolazione_${LIV}_avq.csv" \
             "$D/popolazione_${LIV}_avq_full.csv" "data/nuclei/nuclei_${COD}.csv"; do
      A="$CONFR/${F#data/}"            # archivio: <CONFR>/comuni/... e <CONFR>/nuclei/...
      if   [[ ! -e "$F" ]]; then R+=("manca")
      elif [[ ! -e "$A" ]]; then R+=("no-arch")
      elif cmp -s "$F" "$A";  then R+=("uguale")
      else R+=("DIVERSO"); fi
    done
    printf '%-10s %-8s %-8s %-8s %-8s\n' "$COD" "${R[@]}"
  done | tee "$LOGDIR/confronto.txt"
  echo "(salvato in $LOGDIR/confronto.txt)"
fi
