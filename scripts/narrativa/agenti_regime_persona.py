#!/usr/bin/env python
"""Porta i file dati/agenti/agenti_*.json al regime «persona».

Toglie da ogni agente i campi del regime narrativo che non compaiono nel
bundle pubblico: `nome`, `via`, `donor_id`. Tutto il resto (uid, gruppo,
attributi, vettore AVQ, metadati di testa) resta identico, così le campagne
in dati/campagne/ restano allineate per uid.

Aggiunge in testa `regime: "persona"` e `campi_rimossi: [...]`, con la data
dell'operazione, perché il file dichiari da solo cosa non contiene più.

Uso:
    python scripts/narrativa/agenti_regime_persona.py            # dry-run
    python scripts/narrativa/agenti_regime_persona.py --applica  # riscrive
"""
import json, sys, glob
from datetime import date

CAMPI = ["nome", "via", "donor_id"]
FILES = sorted(glob.glob("dati/agenti/agenti_*.json"))
applica = "--applica" in sys.argv

for f in FILES:
    d = json.load(open(f, encoding="utf-8"))
    ag = d.get("agenti")
    if not isinstance(ag, list):
        print(f"  ?  {f}: nessuna lista 'agenti', salto"); continue
    presenti = {c for a in ag for c in CAMPI if c in a}
    if not presenti:
        print(f"  ok {f}: già in regime persona"); continue
    for a in ag:
        for c in CAMPI: a.pop(c, None)
    # metadati in testa, prima di 'agenti'
    nuovo = {}
    for k, v in d.items():
        if k == "agenti":
            nuovo["regime"] = "persona"
            nuovo["campi_rimossi"] = sorted(presenti)
            nuovo["regime_applicato"] = date.today().isoformat()
        nuovo[k] = v
    print(f"  {'->' if applica else '..'} {f}: tolgo {sorted(presenti)} da {len(ag)} agenti")
    if applica:
        with open(f, "w", encoding="utf-8") as out:
            json.dump(nuovo, out, ensure_ascii=False, indent=1)
            out.write("\n")
if not applica:
    print("\n(dry-run: aggiungi --applica per riscrivere)")
