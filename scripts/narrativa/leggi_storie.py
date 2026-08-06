#!/usr/bin/env python3
"""leggi_storie.py — le storie in chiaro invece che in JSON.

    python scripts/narrativa/leggi_storie.py FILE
    python scripts/narrativa/leggi_storie.py FILE --latente 0
    python scripts/narrativa/leggi_storie.py FILE --gruppo HIGH -n 5
    python scripts/narrativa/leggi_storie.py FILE --problemi
"""
import argparse, json, textwrap

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--gruppo", default=None)
ap.add_argument("--latente", type=int, default=None)
ap.add_argument("-n", type=int, default=None)
ap.add_argument("--problemi", action="store_true",
                help="solo quelle segnalate dal controllo")
ap.add_argument("--nudo", action="store_true",
                help="senza profilo ne' latente: per leggerle alla cieca")
a = ap.parse_args()

d = json.load(open(a.file, encoding="utf-8"))
s = d["storie"]
if a.gruppo:  s = [x for x in s if x["gruppo"] == a.gruppo]
if a.latente is not None: s = [x for x in s if x["latente"] == a.latente]
if a.problemi: s = [x for x in s if x["problemi"]]
if a.n: s = s[:a.n]

print(f"{len(s)} storie · {d.get('modello')} · T {d.get('temperatura')}")
for x in s:
    print("\n" + "─" * 74)
    if not a.nudo:
        print(f"[{x['latente']:>2}] {x['profilo_testo']}")
        if x["problemi"]:
            print(f"     ! {x['problemi']}")
        print()
    for p in x["storia"].split("\n"):
        print(textwrap.fill(p, 74) if p.strip() else "")
