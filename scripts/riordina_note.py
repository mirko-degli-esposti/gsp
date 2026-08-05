#!/usr/bin/env python3
"""riordina_note.py — tiene l'ultima versione, archivia le altre.

    python riordina_note.py              # mostra e basta
    python riordina_note.py --applica

TRE REGOLE.

1. Gli ausiliari LaTeX (.aux .log .out .toc .fls .fdb_latexmk
   .synctex.gz) si CANCELLANO: sono rigenerati da ogni compilazione e
   non contengono nulla che non stia nel .tex.

2. Dei sorgenti LaTeX si tiene il .tex e si cancella il .pdf: il PDF si
   ricompila, e tenerlo raddoppia lo spazio per un file che diverge dal
   sorgente appena lo si tocca.

3. Per ogni FAMIGLIA — stesso nome a meno del suffisso `_vNN` — si tiene
   la versione piu' alta e le altre vanno in `storico/`. Il file SENZA
   numero di versione, se la famiglia ne ha di numerate, e' il piu'
   vecchio e va in storico anche lui.

I file che non appartengono a nessuna famiglia versionata restano dove
sono: non c'e' modo di sapere se siano correnti o dimenticati, e
spostarli sarebbe una decisione presa dallo script invece che da chi
scrive.
"""

import argparse
import os
import re
import shutil
import sys
from collections import defaultdict

AUSILIARI = {".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk",
             ".blg", ".bbl", ".nav", ".snm", ".vrb", ".lof", ".lot"}
AUSILIARI_COMPOSTI = {".synctex.gz"}

VERSIONE = re.compile(r"^(?P<base>.+?)_v(?P<n>\d+)(?P<coda>\..+)$")


def famiglia(nome):
    """(base, versione, estensione) oppure (base, None, estensione)."""
    m = VERSIONE.match(nome)
    if m:
        coda = m.group("coda")
        # `.md.pdf` appartiene alla stessa famiglia del `.md`: e' il suo
        # compilato, quindi una versione piu' recente del markdown lo
        # supera anche se il PDF di quella versione non esiste. Senza
        # questa regola resterebbero in giro i PDF di versioni vecchie
        # accanto al sorgente nuovo.
        if coda == ".md.pdf":
            coda = ".md"
        return m.group("base"), int(m.group("n")), coda
    base, ext = os.path.splitext(nome)
    if ext == ".pdf" and base.endswith(".md"):
        return base[:-3], None, ".md"
    return base, None, ext


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default="note")
    ap.add_argument("--storico", default=None,
                    help="default: <dir>/storico")
    ap.add_argument("--applica", action="store_true")
    ap.add_argument("--tieni-pdf", action="store_true",
                    help="non cancellare i PDF dei sorgenti LaTeX")
    a = ap.parse_args()

    d = a.dir
    if not os.path.isdir(d):
        sys.exit(f"{d} non esiste: eseguire dalla radice del repo")
    stor = a.storico or os.path.join(d, "storico")

    file = [x for x in sorted(os.listdir(d))
            if os.path.isfile(os.path.join(d, x))]

    # --- 1. ausiliari LaTeX
    ausiliari = [x for x in file
                 if os.path.splitext(x)[1] in AUSILIARI
                 or any(x.endswith(s) for s in AUSILIARI_COMPOSTI)]
    resto = [x for x in file if x not in set(ausiliari)]

    # --- 2. PDF di sorgenti LaTeX presenti
    tex = {os.path.splitext(x)[0] for x in resto if x.endswith(".tex")}
    pdf_tex = [] if a.tieni_pdf else [
        x for x in resto
        if x.endswith(".pdf") and os.path.splitext(x)[0] in tex]
    resto = [x for x in resto if x not in set(pdf_tex)]

    # --- 3. famiglie versionate
    fam = defaultdict(list)
    for x in resto:
        base, n, ext = famiglia(x)
        fam[(base, ext)].append((n, x))

    tieni, archivia = [], []
    for (base, ext), membri in sorted(fam.items()):
        numerati = [(n, x) for n, x in membri if n is not None]
        if not numerati:
            tieni += [x for _, x in membri]      # famiglia senza versioni
            continue
        ultima = max(n for n, _ in numerati)
        for n, x in membri:
            (tieni if n == ultima else archivia).append(x)

    peso = lambda xs: sum(os.path.getsize(os.path.join(d, x))    # noqa: E731
                          for x in xs) / 1e6

    print(f"{d}/ — {len(file)} file\n")
    print(f"CANCELLARE · ausiliari LaTeX      {len(ausiliari):>3} file  "
          f"{peso(ausiliari):6.1f} MB")
    if pdf_tex:
        print(f"CANCELLARE · pdf ricompilabili    {len(pdf_tex):>3} file  "
              f"{peso(pdf_tex):6.1f} MB")
    print(f"ARCHIVIARE · versioni superate    {len(archivia):>3} file  "
          f"{peso(archivia):6.1f} MB")
    print(f"TENERE                            {len(tieni):>3} file  "
          f"{peso(tieni):6.1f} MB")

    if archivia:
        print("\nin storico/:")
        for x in archivia:
            print(f"   {x}")
    print("\nrestano in note/:")
    for x in sorted(tieni):
        print(f"   {x}")

    if not a.applica:
        print(f"\n(prova: niente toccato. Con --applica si cancellano "
              f"{len(ausiliari) + len(pdf_tex)} file e se ne spostano "
              f"{len(archivia)}.)")
        return

    os.makedirs(stor, exist_ok=True)
    for x in ausiliari + pdf_tex:
        os.remove(os.path.join(d, x))
    for x in archivia:
        dst = os.path.join(stor, x)
        if os.path.exists(dst):
            print(f"   {x}: gia' in storico, non sovrascrivo")
            continue
        shutil.move(os.path.join(d, x), dst)
    print(f"\ncancellati {len(ausiliari) + len(pdf_tex)}, "
          f"spostati {len(archivia)} in {stor}/")
    print("   git status --short  per vedere cosa e' cambiato")


if __name__ == "__main__":
    main()
