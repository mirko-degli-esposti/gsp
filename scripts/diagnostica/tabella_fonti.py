#!/usr/bin/env python
"""Genera la tabella fonte -> anello per il report (Parte II, tab. II.2a).

Legge fonti/registro.yaml e fonti/anelli.yaml, scrive Markdown su stdout
(o CSV con --csv). Fallisce se un tag di `usabile_per` non ha una
destinazione in anelli.yaml.

    python scripts/diagnostica/tabella_fonti.py > note/misure/tabella_fonti.md
    python scripts/diagnostica/tabella_fonti.py --csv > tabella_fonti.csv
"""
import sys, os, yaml
from collections import Counter

GSP = os.path.expanduser(os.environ.get("GSP_ROOT", "~/progetti/gsp"))
reg = yaml.safe_load(open(os.path.join(GSP, "fonti", "registro.yaml")))
fonti = reg["fonti"] if isinstance(reg, dict) else reg
mappa = yaml.safe_load(open(os.path.join(GSP, "fonti", "anelli.yaml")))
dest = {t: k for k, v in mappa.items() for t in v}
SIGLA = {"anello1": "1", "anello2": "2", "anello3": "3", "anello4": "4",
         "derivati": "D", "validazione": "V", "viewer": "W", "infrastruttura": "I"}

def s(x, n=None):
    x = "" if x is None else str(x)
    x = x.replace("|", "/").replace("\n", " ")
    return x if n is None or len(x) <= n else x[:n - 1] + "…"

righe, ignoti = [], set()
for f in fonti:
    ks = set()
    for t in (f.get("usabile_per") or []):
        k = dest.get(t)
        if k is None: ignoti.add(t)
        elif k != "dimensione": ks.add(k)
    anelli = "".join(SIGLA[k] for k in SIGLA if k in ks) or "—"
    tempo = f.get("riferimento_temporale") or f.get("anno_usato") or ""
    if f.get("anno_usato") and f.get("riferimento_temporale"):
        tempo = f"{f['riferimento_temporale']} ({f['anno_usato']})"
    usato = f.get("usato_da") or []
    righe.append(dict(
        id=f["id"], ente=s(f.get("ente"), 30), universo=s(f.get("universo"), 60),
        tempo=s(tempo, 22), accesso=s(f.get("data_accesso"), 10),
        licenza=s(f.get("licenza"), 28), arch=s(f.get("archiviazione")),
        usato=s(", ".join(usato) if isinstance(usato, list) else usato, 40),
        anelli=anelli))
if ignoti:
    sys.exit(f"tag senza destinazione in anelli.yaml: {sorted(ignoti)}")

righe.sort(key=lambda r: (r["anelli"].replace("—", "Z"), r["id"]))
if "--csv" in sys.argv:
    import csv
    w = csv.DictWriter(sys.stdout, fieldnames=list(righe[0])); w.writeheader(); w.writerows(righe)
    sys.exit()

print("| id | ente | universe | temporal ref. | accessed | licence | stor. | used by | ring |")
print("|---|---|---|---|---|---|---|---|---|")
for r in righe:
    print("| `{id}` | {ente} | {universo} | {tempo} | {accesso} | {licenza} | {arch} | {usato} | **{anelli}** |".format(**r))
c = Counter(ch for r in righe for ch in r["anelli"] if ch != "—")
print("\nLegend: 1–4 rings; D derived layers; V validation/exploration; W viewer only; I infrastructure; — registered, not used.")
print("Sources per destination (a source may feed several): " + ", ".join(f"{k}: {c[k]}" for k in SIGLA.values() if c[k])
      + f"; total sources: {len(righe)}.")
