#!/usr/bin/env python3
"""riempi_sha.py — sostituisce i `sha256: DA_CALCOLARE` nel registro.

Non prende gli hash da una lista: li CALCOLA dal file che ogni scheda
dichiara in `percorso`. Cosi' non c'e' modo di scambiarli fra loro, che e'
il rischio vero quando se ne inseriscono quattro a mano — `sha256sum` li
stampa nell'ordine degli argomenti, la scheda li vuole nell'ordine del
registro, e i due ordini non coincidono mai.

    python riempi_sha.py --prova     # mostra e basta
    python riempi_sha.py             # applica
"""

import hashlib
import os
import pathlib
import re
import sys

REGISTRO = pathlib.Path("fonti/registro.yaml")
prova = "--prova" in sys.argv


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blocco in iter(lambda: f.read(1 << 20), b""):
            h.update(blocco)
    return h.hexdigest()


if not REGISTRO.exists():
    sys.exit("eseguire dalla radice del repo (~/progetti/gsp)")

righe = REGISTRO.read_text(encoding="utf-8").splitlines(keepends=True)

# Si scorre il file tenendo l'ultimo `id` e l'ultimo `percorso` visti:
# quando si incontra un `sha256: DA_CALCOLARE`, il percorso giusto e'
# quello della scheda corrente. Il legame e' posizionale ma dentro la
# stessa scheda, quindi non puo' saltare a un'altra fonte.
id_cor = perc_cor = None
fatte, mancanti, gia = [], [], []

for i, r in enumerate(righe):
    m = re.match(r"^  - id:\s*(\S+)", r)
    if m:
        id_cor, perc_cor = m.group(1), None
        continue
    m = re.match(r"^    percorso:\s*(\S.*?)\s*$", r)
    if m:
        perc_cor = m.group(1).strip("'\"")
        continue
    m = re.match(r"^(\s*sha256:\s*)(\S+)\s*$", r)
    if not m:
        continue
    pre, val = m.group(1), m.group(2)
    if val != "DA_CALCOLARE":
        gia.append(id_cor)
        continue
    if not perc_cor:
        mancanti.append((id_cor, "nessun `percorso` nella scheda"))
        continue
    if "{istanza}" in perc_cor or "*" in perc_cor:
        mancanti.append((id_cor, "multi_istanza: l'hash sta nell'impronta, "
                                 "non nella scheda"))
        continue
    if not os.path.exists(perc_cor):
        mancanti.append((id_cor, f"file assente: {perc_cor}"))
        continue
    h = sha256(perc_cor)
    righe[i] = f"{pre}{h}\n"
    fatte.append((id_cor, perc_cor, h))

for idf, perc, h in fatte:
    print(f"  {idf:<28} {h[:16]}...  <- {perc}")
if mancanti:
    print("\nnon calcolati:")
    for idf, motivo in mancanti:
        print(f"  {idf:<28} {motivo}")
if gia:
    print(f"\n{len(gia)} schede avevano gia' l'hash")

if prova:
    print(f"\n{len(fatte)} da sostituire (prova, niente scritto)")
else:
    REGISTRO.write_text("".join(righe), encoding="utf-8")
    print(f"\n{len(fatte)} sostituiti in {REGISTRO}")
    print("   python -m gsp.fonti --verifica")
