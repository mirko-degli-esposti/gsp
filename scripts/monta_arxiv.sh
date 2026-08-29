#!/usr/bin/env bash
# monta_arxiv.sh — genera il pacchetto arXiv (main.tex + figure/ + zip)
# con lo stesso pandoc di monta_bozza.sh, ma emettendo il sorgente TeX.
#
#   bash scripts/monta_arxiv.sh            # -> ~/arxiv_submission/submission.zip
set -eu
GSP="${GSP_ROOT:-$HOME/progetti/gsp}"
N="$GSP/note"
DEST="${1:-$HOME/arxiv_submission}"
ORD=(report_frontmatter_v1.md
     report_part1_v1.md
     report_part2_v1.md
     report_part3_v1.md
     report_part4_v1.md
     report_part5_v0.1.md
     report_appendix_a_v1.md)
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
i=1
for f in "${ORD[@]}"; do
  [ -e "$N/$f" ] || { echo "[salto] $f"; continue; }
  { echo; echo '\newpage'; echo; cat "$N/$f"; } > "$T/$(printf %02d $i).md"
  i=$((i+1))
done
HEAD=$(cd "$GSP" && git rev-parse --short HEAD)
rm -rf "$DEST"; mkdir -p "$DEST/figure"
cp "$N"/figure/*.pdf "$DEST/figure/"
pandoc -f markdown-yaml_metadata_block --resource-path="$N" "$T"/*.md \
  -s -o "$DEST/main.tex" \
  --metadata title="Animarium — technical report, version 1" \
  --metadata date="$(date +%F) · $HEAD" \
  -V geometry:margin=2.2cm -V fontsize=10pt -V colorlinks=true \
  --toc --toc-depth=2
cd "$DEST"
grep -n includegraphics main.tex
xelatex -interaction=nonstopmode main.tex >/dev/null
xelatex -interaction=nonstopmode main.tex >/dev/null
zip -r submission.zip main.tex figure/ >/dev/null
unzip -l submission.zip
echo "-> $DEST/submission.zip   (PDF di controllo: $DEST/main.pdf)"