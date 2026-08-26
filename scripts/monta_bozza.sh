#!/usr/bin/env bash
# monta_bozza.sh — assembla le bozze del report in un PDF di lavoro.
# TEMPORANEO: i file restano separati, questo serve solo per la stampa.
#
#   bash scripts/monta_bozza.sh                # -> /tmp/animarium_report_bozza_<data>.pdf
#   bash scripts/monta_bozza.sh out/mio.pdf    # destinazione a scelta
#
# Richiede: pandoc, wkhtmltopdf (entrambi in Ubuntu). Non usa LaTeX.
set -eu
GSP="${GSP_ROOT:-$HOME/progetti/gsp}"
N="$GSP/note"
OUT="${1:-/tmp/animarium_report_bozza_$(date +%Y%m%d).pdf}"
ORD=(report_frontmatter_v1.md
     report_part1_v1.md
     report_part2_v1.md
     report_part3_v1.md
     report_part4_v1.md
     report_part5_v0.1.md)
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
i=1
for f in "${ORD[@]}"; do
  if [ ! -e "$N/$f" ]; then echo "[salto] $f non in note/"; continue; fi
  { echo; echo '<div style="page-break-before: always;"></div>'; echo
    echo "<!-- ===== $f ===== -->"; cat "$N/$f"; } > "$T/$(printf %02d $i).md"
  i=$((i+1))
done
HEAD=$(cd "$GSP" && git rev-parse --short HEAD)
if pandoc -f markdown-yaml_metadata_block "$T"/*.md -o "$OUT" --pdf-engine=xelatex \
     --metadata title="Animarium — technical report, working draft" \
     --metadata date="$(date +%F) · $HEAD" \
     -V geometry:margin=2.2cm -V fontsize=10pt -V colorlinks=true \
     --toc --toc-depth=2 2>/tmp/monta_bozza_tex.log; then
  echo "-> $OUT  (xelatex)"
else
  echo "[info] xelatex fallito (log in /tmp/monta_bozza_tex.log), ripiego su wkhtmltopdf"
  pandoc -f markdown-yaml_metadata_block "$T"/*.md --standalone --toc --toc-depth=2 \
    --metadata title="Animarium — technical report, working draft ($(date +%F), $HEAD)" \
    -o "$T/bozza.html"
  wkhtmltopdf --enable-local-file-access -q "$T/bozza.html" "$OUT"
  echo "-> $OUT  (wkhtmltopdf)"
fi
