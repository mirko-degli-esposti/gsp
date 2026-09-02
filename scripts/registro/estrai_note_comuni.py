"""
scripts/registro/estrai_note_comuni.py — salva i commenti del dict COMUNI.

I commenti nel blocco COMUNI di common.py non sono decorazioni: sono
ragioni di disegno (perche' Bologna usa ASC2, il [v] sul confine 05/06
di Cesena, l'override di Brescia, i numeri del collaudo di Mantova).
Con la migrazione a flotta/comuni.yaml il dict sparisce e con lui i
commenti: questo script li estrae PRIMA, li attribuisce alla voce per
posizione, e li scrive nel yaml come campo `note` (testo a blocchi).

Regole di attribuzione (dalla forma reale del blocco):
- commento standalone con rientro > 4  -> voce corrente (e' dentro)
- commento standalone con rientro <= 4 -> voce SUCCESSIVA (e' un'intestazione
  di gruppo, come il blocco "PILOTA" prima dei tre comuni del pilota)
- commento inline su un campo (`"geo_liv": ..., # ...`) -> se il campo e'
  uno di quelli dello schema opendata_paese, va nelle NOTE DI SCHEMA in
  testa al file (e' documentazione del campo, ripetuta per ogni voce);
  altrimenti alla voce corrente, col nome del campo davanti.

Uso (PRIMA di sostituire il dict con il loader):
    python scripts/registro/estrai_note_comuni.py \
        --common src/gsp/common.py --yaml flotta/comuni.yaml
Con --dry-run stampa il report senza toccare il yaml.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

CAMPI_SCHEMA = {"geo_liv", "geo_col", "sesso", "dir", "override_nome", "loader"}


class _Dumper(yaml.SafeDumper):
    pass


def _rappresenta_str(dumper, s):
    if "\n" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
    style = "'" if s.isdigit() else None       # codici: mai ottali
    return dumper.represent_scalar("tag:yaml.org,2002:str", s, style=style)


_Dumper.add_representer(str, _rappresenta_str)


def estrai(righe_common):
    """Ritorna (note_per_comune: dict cod -> [righe], schema: [righe],
    orfani: [righe]) dal blocco COMUNI."""
    inizio = next(i for i, l in enumerate(righe_common) if l.startswith("COMUNI = {"))
    fine = next(i for i in range(inizio + 1, len(righe_common))
                if righe_common[i].startswith("}"))
    blocco = righe_common[inizio + 1:fine]

    note, schema, orfani = {}, [], []
    corrente, pendenti = None, []
    re_voce = re.compile(r'^\s+"(\d{6})":\s*\{')
    re_inline = re.compile(r'^\s*"(\w+)":.*?#\s*(.*)$')

    for l in blocco:
        m = re_voce.match(l)
        if m:
            corrente = m.group(1)
            note.setdefault(corrente, [])
            if pendenti:                         # intestazione di gruppo
                note[corrente].extend(pendenti)
                pendenti = []
            continue
        s = l.strip()
        if not s or "#" not in s:
            continue
        if s.startswith("#"):
            testo = s.lstrip("#").strip()
            rientro = len(l) - len(l.lstrip())
            # intestazione di gruppo: rientro basso, o una riga "--- ... ---"
            # (il blocco PILOTA aveva il titolo a rientro 8 e il testo a 4)
            if rientro <= 4 or testo.startswith("---"):
                pendenti.append(testo)
            elif corrente:
                note[corrente].append(testo)
            else:
                orfani.append(testo)
            continue
        mi = re_inline.match(l)
        if mi:
            campo, testo = mi.groups()
            if campo in CAMPI_SCHEMA:
                voce = f"{campo}: {testo}"
                if voce not in schema:
                    schema.append(voce)
            elif corrente:
                note[corrente].append(f"[{campo}] {testo}")
        else:
            orfani.append(s)
    if pendenti:
        orfani.extend(pendenti)
    return {k: v for k, v in note.items() if v}, schema, orfani


INTESTAZIONE = """\
# flotta/comuni.yaml — registro dei comuni: DATI, non codice.
# Caricato da gsp.common (COMUNI, info, livello_col, regione invariati per i
# consumatori); rigenera.sh deriva l'array da qui; l'emettitore scrive qui.
# Migrato dal dict di common.py il 2/9/2026 (scripts/registro/esporta_comuni.py,
# round-trip verificato; note estratte da estrai_note_comuni.py).
#
# CODICI SEMPRE QUOTATI: senza virgolette, un codice con sole cifre 0-7 e'
# letto da YAML 1.1 come OTTALE (015146 -> 6758). Il loader rifiuta le
# chiavi non-stringa con un errore che lo spiega.
#
# Voce minima (K6C): nome, slug, regione, pool, stato [, note]
#   il loader aggiunge livello: null, livelli: {}
# Voce articolata: + livello, livelli (mappe zone per esteso)
# Voce con fonte locale: + opendata_paese
# stato: flotta | collaudo | pilota | v2 | sotto_soglia
#
# Schema di opendata_paese (dai commenti inline del dict):
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--common", default="src/gsp/common.py")
    ap.add_argument("--yaml", default="flotta/comuni.yaml")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    righe = Path(a.common).read_text(encoding="utf-8").splitlines()
    note, schema, orfani = estrai(righe)

    print(f"note estratte per {len(note)} comuni:")
    for cod, ls in note.items():
        print(f"  {cod}: {len(ls)} righe — {ls[0][:60]}...")
    print(f"\nnote di schema (opendata_paese): {len(schema)}")
    for s in schema:
        print(f"  {s}")
    if orfani:
        print(f"\nORFANI (non attribuiti, da guardare): {len(orfani)}")
        for o in orfani:
            print(f"  {o}")
    if a.dry_run:
        return

    voci = yaml.safe_load(Path(a.yaml).read_text(encoding="utf-8"))
    for cod, ls in note.items():
        if cod not in voci:
            print(f"  !! {cod} ha note ma non e' nel yaml")
            continue
        voci[cod]["note"] = "\n".join(ls)
    testo = INTESTAZIONE + "".join(f"#   {s}\n" for s in schema) + "\n"
    testo += yaml.dump(voci, Dumper=_Dumper, allow_unicode=True, sort_keys=False)
    Path(a.yaml).write_text(testo, encoding="utf-8")
    print(f"\nscritto {a.yaml} con {len(note)} campi note + intestazione di schema")


if __name__ == "__main__":
    main()
