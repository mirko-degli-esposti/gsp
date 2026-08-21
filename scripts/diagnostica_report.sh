#!/usr/bin/env bash
# diagnostica_report.sh — misure per la Parte III.3 del report tecnico.
#
# Per ogni comune esegue le diagnostiche di qualita' e salva le uscite in
# note/misure/diagnostica_report_v1.0/ :
#
#   verifica_vincoli.py   MRE per blocco, pavimento, z-score   (anello 1)
#   verifica_donor.py     firme, n_eff per universo            (anello 2)
#
# poi raccoglie le diagnostiche dell'anello 4 gia' scritte da
# assign_nucleo.py (data/nuclei/nuclei_*_diagnostica.json) in una tabella
# unica. Non rigenera nulla: legge le popolazioni a terra.
#
# Uso:
#   bash scripts/diagnostica_report.sh                 # tutti
#   bash scripts/diagnostica_report.sh 034027 037006   # alcuni
#
set -uo pipefail
GSP="${GSP_ROOT:-$HOME/progetti/gsp}"
cd "$GSP" || exit 1
ANIM="${ANIMARIUM_ROOT:-$HOME/progetti/animarium}"
OUT="note/misure/diagnostica_report_v1.0"
mkdir -p "$OUT"

{ echo "HEAD=$(git rev-parse HEAD)"; echo "date=$(date -Iseconds)";
  echo "--- git status --short:"; git status --short; } > "$OUT/commit.txt"

declare -A LIV=( [037006]=K9C [017029]=K9C [034027]=K9C [036023]=K9C
                 [035033]=K9C [039014]=K9C [099014]=K9C [038008]=K6C
                 [040012]=K9C [033032]=K9C [037021]=K6C )
COMUNI=(037006 017029 034027 036023 035033 039014 099014 038008 040012 033032 037021)
[[ $# -gt 0 ]] && COMUNI=("$@")

printf '%-8s %-6s %-14s %-14s\n' COMUNE LIV vincoli donor
for C in "${COMUNI[@]}"; do
  L="${LIV[$C]:-K9C}"; V=ok; D=ok
  python scripts/diagnostica/verifica_vincoli.py "$C" \
      --cs "data/comuni/$C/constraints_2024/cs_${L}.json" \
      --parquet "$ANIM/bundle/comuni/$C/pop.parquet" \
      --out "$OUT/celle_$C.csv" > "$OUT/vincoli_$C.txt" 2>&1 || V=ERRORE
  python scripts/diagnostica/verifica_donor.py "$C" \
      --pop-file "data/comuni/$C/constraints_2024/popolazione_${L}_avq_full.csv" \
      > "$OUT/donor_$C.txt" 2>&1 || D=ERRORE
  printf '%-8s %-6s %-14s %-14s\n' "$C" "$L" "$V" "$D"
done

echo
echo "--- anello 4: raccolta diagnostiche nuclei ---"
python - "$OUT" <<'PYEOF'
import json, glob, sys, os
out = sys.argv[1]
righe = []
for f in sorted(glob.glob("data/nuclei/nuclei_*_diagnostica.json")):
    d = json.load(open(f))
    sc = d.get("stato_civile") or {}
    righe.append({
        "comune": d["comune"],
        "individui": d["individui"],
        "nuclei": d["nuclei"],
        "ampiezza_media": round(d["individui"] / max(d["nuclei"], 1), 2),
        "senza_ripiego": round(d["senza_ripiego"], 4),
        "non_collocati": round(d["quota_non_collocati"], 4),
        "coppie_omogenee": round(d["coppie_omogenee"], 4),
        "coniugati_incoerenti": (round(sc["incoerenti"], 4) if sc else None),
        "seme": d["seme"],
        "popolazione": d["popolazione"],
    })
with open(os.path.join(out, "nuclei_riepilogo.json"), "w") as fh:
    json.dump(righe, fh, indent=1, ensure_ascii=False)
# tabella Markdown pronta per il report
cols = ["comune","individui","nuclei","ampiezza_media","senza_ripiego",
        "non_collocati","coppie_omogenee","coniugati_incoerenti"]
with open(os.path.join(out, "nuclei_riepilogo.md"), "w") as fh:
    fh.write("| " + " | ".join(cols) + " |\n")
    fh.write("|" + "---|" * len(cols) + "\n")
    for r in righe:
        fh.write("| " + " | ".join(str(r[c]) for c in cols) + " |\n")
print(f"  {len(righe)} comuni -> {out}/nuclei_riepilogo.md")
PYEOF

echo
echo "uscite in $OUT/ — da committare con il resto delle misure"
