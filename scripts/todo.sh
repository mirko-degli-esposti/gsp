#!/usr/bin/env bash
# scripts/todo.sh — appende un item a note/TODO.md
# Uso:  ./scripts/todo.sh "testo dell'item"  [tag]
# Il tag (default: nessuno) identifica la sessione/chat di origine.
# La rimozione degli item è deliberatamente manuale.
set -eu
F="$(cd "$(dirname "$0")/.." && pwd)/note/TODO.md"
TESTO="$1"; TAG="${2:-}"
printf -- "- [ ] %s%s %s\n" "$(date +%F)" "${TAG:+ [$TAG]}" "$TESTO" >> "$F"
tail -3 "$F"    # stampa il risultato, non solo esegue
