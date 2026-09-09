#!/usr/bin/env python3
"""
accessibilita.py — l'esempio decisionale: la stessa domanda, tre geografie.

    python scripts/esempio/accessibilita.py --tutti --quantile 0.20 --solo-er
    python scripts/esempio/accessibilita.py 037006 --eta 75 --istruzione basso

La domanda
----------
*Quanti residenti anziani con basso titolo di studio vivono nella parte
meno servita della citta'?* E' la forma minima di una decisione di
programmazione --- dove mettere un servizio, chi non e' raggiunto --- e il
bersaglio e' definito da DUE attributi insieme.

Perche' due e non uno (v2, dopo il referaggio interno)
------------------------------------------------------
La versione precedente contava gli over-75. Obiezione fatale: la
popolazione per eta' e sesso per sezione di censimento e' PUBBLICATA, ed
e' anzi la fonte da cui la pipeline costruisce il blocco Z1. Quel
conteggio si poteva fare senza alcuna popolazione sintetica, e l'esempio
dimostrava il valore della geografia ISTAT, non del rilascio.

L'incrocio eta' x istruzione per sezione, invece, non e' pubblicato. Il
censimento da', per sezione, la popolazione per eta' e sesso (Z1) e
l'istruzione per sesso (Z3), ma non la loro congiunta: quella la
fornisce il modello. Ed e' precisamente il tipo di quantita' per cui una
popolazione sintetica esiste.

Le tre risposte
---------------
**A, quota comunale.** Cio' che si ottiene senza geografia: la quota
comunale del bersaglio applicata alla popolazione delle sezioni
scoperte. Assume che il bersaglio sia distribuito come tutti.

**B, marginali di sezione.** Cio' che si ottiene con le tavole
territoriali pubblicate ma SENZA la congiunta: per ogni sezione si
moltiplica la sua quota di anziani per la sua quota di bassa istruzione,
come se i due attributi fossero indipendenti dentro la sezione. E' il
meglio che un analista puo' fare con le fonti pubblicate.

**C, congiunta sintetica.** Il conteggio nella popolazione rilasciata,
dove i due attributi stanno sullo stesso individuo.

A vs C misura quanto costa ignorare la geografia. **B vs C misura quanto
costa non avere la congiunta**, ed e' il confronto che riguarda il
rilascio: e' la differenza fra cio' che le tavole pubblicate permettono e
cio' che la popolazione sintetica aggiunge.

Onesta' sulla provenienza
-------------------------
Nell'incrocio, la geografia dell'eta' e quella dell'istruzione sono
entrambe vincolate dal censimento (Z1 e Z3); la loro CONGIUNTA dentro la
sezione e' massima entropia. Il paper misura altrove quanto quella parte
sia affidabile (hold-out dei blocchi territoriali), e va letta con quel
risultato in mano: qui si mostra che la congiunta cambia la risposta, non
che sia esatta.

Che cosa NON e'
---------------
Uno studio di accessibilita'. La distanza e' euclidea, dal centroide
della sezione --- la piu' fine unita' spaziale vincolata --- e i punti
vengono da OpenStreetMap, la cui completezza non e' certificata. Un punto
mancante puo' spostare quali sezioni entrano nel gruppo meno servito, non
solo i conteggi: e' un limite dichiarato, non aggirato.

Dipendenze: pandas, pyarrow, numpy.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("pip install pandas pyarrow")

GSP = Path(os.environ.get("GSP_ROOT", Path.home() / "progetti" / "gsp"))
ANIM = Path(os.environ.get("ANIMARIUM_ROOT", Path.home() / "progetti" / "animarium"))
POI = GSP / "data" / "esempio" / "poi"
OUT = GSP / "data" / "esempio"

COMUNI = {
    "037006": "Bologna",   "034027": "Parma",      "036023": "Modena",
    "035033": "Reggio nell'Emilia", "039014": "Ravenna", "099014": "Rimini",
    "038008": "Ferrara",   "040012": "Forli",      "040007": "Cesena",
    "033032": "Piacenza",  "017029": "Brescia",
}
FUORI_REGIONE = {"017029"}

# secondo attributo del bersaglio: quali modalita' contano
ISTRUZIONE = {
    "basso": {"nessun_titolo", "elementare", "media"},
    "alto":  {"laurea_o_its", "post_laurea"},
}


def analizza(codice: str, eta: int, istr: str, raggio: float,
             quantile: float | None = None) -> dict | None:
    import numpy as np

    pq = ANIM / "bundle" / "comuni" / codice / "pop.parquet"
    poi = POI / f"{codice}_farmacia.csv"
    for f in (pq, poi):
        if not f.exists():
            print(f"  [salto] {codice}: manca {f.name}")
            return None

    pop = pd.read_parquet(
        pq, columns=["sezione", "eta_anni", "istruzione", "lon", "lat"])
    servizi = pd.read_csv(poi)

    mod = ISTRUZIONE[istr]
    note = set().union(*ISTRUZIONE.values()) | {"diploma"}
    ignote = set(pop["istruzione"].dropna().unique()) - note
    if ignote:
        print(f"  [avviso] modalita' d'istruzione non classificate: {sorted(ignote)}")

    pop["is_anz"] = pop["eta_anni"] >= eta
    pop["is_istr"] = pop["istruzione"].isin(mod)
    pop["is_target"] = pop["is_anz"] & pop["is_istr"]

    sez = pop.groupby("sezione").agg(
        n=("is_anz", "size"),
        anz=("is_anz", "sum"),
        istr=("is_istr", "sum"),
        target=("is_target", "sum"),
        lat=("lat", "mean"),
        lon=("lon", "mean"),
    ).reset_index()

    # --- distanza dal servizio piu' vicino, per sezione -------------------
    R, p = 6371000.0, math.pi / 180.0
    slat = sez["lat"].to_numpy()[:, None] * p
    slon = sez["lon"].to_numpy()[:, None] * p
    plat = servizi["lat"].to_numpy()[None, :] * p
    plon = servizi["lon"].to_numpy()[None, :] * p
    latm = (slat + plat) / 2.0
    d = R * np.sqrt((plat - slat) ** 2 + ((plon - slon) * np.cos(latm)) ** 2)
    sez["dist"] = d.min(axis=1)

    if quantile:
        soglia = float(sez["dist"].quantile(1 - quantile))
        sez["scoperta"] = sez["dist"] >= soglia
    else:
        soglia = raggio
        sez["scoperta"] = sez["dist"] > raggio

    tot = int(sez["n"].sum())
    scop = sez[sez["scoperta"]].copy()
    n_scop = int(scop["n"].sum())
    if n_scop == 0:
        print(f"  [salto] {codice}: nessuna sezione scoperta")
        return None

    # A — quota comunale del bersaglio, applicata alla popolazione scoperta
    a = float(sez["target"].sum()) / tot * n_scop

    # B — marginali di sezione, indipendenza dentro la sezione:
    #     per ogni sezione  n * (anz/n) * (istr/n) = anz*istr/n
    denom = scop["n"].where(scop["n"] > 0, 1)
    b = float((scop["anz"] * scop["istr"] / denom).sum())

    # C — la congiunta, come sta nella popolazione rilasciata
    c = int(scop["target"].sum())

    # scarto: quanto A e B sbagliano RISPETTO A C (C al denominatore)
    da = (a - c) / c if c else None
    db = (b - c) / c if c else None

    r = {
        "comune": codice, "nome": COMUNI.get(codice, codice),
        "eta": eta, "istruzione": istr,
        "criterio": (f"quantile {quantile:.0%}" if quantile
                     else f"oltre {raggio:.0f} m"),
        "soglia_effettiva_m": round(soglia, 1),
        "sezioni": int(len(sez)), "sezioni_scoperte": int(len(scop)),
        "popolazione": tot, "popolazione_scoperta": n_scop,
        "A_quota_comunale": round(a, 1),
        "B_marginali_sezione": round(b, 1),
        "C_congiunta": c,
        "scarto_A_pct": round(100 * da, 1) if da is not None else None,
        "scarto_B_pct": round(100 * db, 1) if db is not None else None,
    }
    print(f"  {r['nome']:<20} A {a:>7.0f} · B {b:>7.0f} · C {c:>6}"
          f"   →  A {100*da:>+6.1f}%  ·  B {100*db:>+6.1f}%")
    return r


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comune", nargs="?")
    ap.add_argument("--tutti", action="store_true")
    ap.add_argument("--eta", type=int, default=75)
    ap.add_argument("--istruzione", default="basso", choices=sorted(ISTRUZIONE))
    ap.add_argument("--raggio", type=float, default=500.0)
    ap.add_argument("--quantile", type=float, default=None,
                    help="frazione di sezioni piu' lontane, es. 0.20")
    ap.add_argument("--solo-er", action="store_true")
    args = ap.parse_args()

    bersagli = list(COMUNI) if args.tutti else ([args.comune] if args.comune
                                                else ap.error("comune o --tutti"))
    if args.solo_er:
        fuori = [c for c in bersagli if c in FUORI_REGIONE]
        bersagli = [c for c in bersagli if c not in FUORI_REGIONE]
        if fuori:
            print(f"  [escluso] {', '.join(COMUNI[c] for c in fuori)}: fuori regione\n")

    crit = (f"il {args.quantile:.0%} di sezioni piu' lontane" if args.quantile
            else f"farmacia oltre {args.raggio:.0f} m")
    print(f"bersaglio: over-{args.eta} con istruzione '{args.istruzione}' · {crit}")
    print("  A = quota comunale del bersaglio        (nessuna geografia)")
    print("  B = marginali di sezione, indipendenti  (tavole pubblicate)")
    print("  C = congiunta della popolazione         (il rilascio)\n")

    ris = [r for c in bersagli
           if (r := analizza(c, args.eta, args.istruzione, args.raggio, args.quantile))]
    if not ris:
        return

    for k, et in (("scarto_A_pct", "A, quota comunale"),
                  ("scarto_B_pct", "B, marginali di sezione")):
        v = sorted(r[k] for r in ris if r[k] is not None)
        med = v[len(v)//2] if len(v) % 2 else (v[len(v)//2-1] + v[len(v)//2]) / 2
        print(f"\n  {et}: mediana {med:+.1f}%, intervallo {v[0]:+.1f}…{v[-1]:+.1f}%")
        if all(x > 0 for x in v):
            print("    sovrastima in tutti i comuni")
        elif all(x < 0 for x in v):
            print("    sottostima in tutti i comuni")
        else:
            print("    il segno cambia fra i comuni")

    tag = f"over{args.eta}_{args.istruzione}"
    tag += f"_q{int(args.quantile*100)}" if args.quantile else f"_{int(args.raggio)}m"
    out = OUT / f"accessibilita_{tag}.json"
    json.dump({
        "parametri": {"eta": args.eta, "istruzione": args.istruzione,
                      "modalita": sorted(ISTRUZIONE[args.istruzione]),
                      "criterio": crit, "servizio": "farmacia",
                      "fonte_poi": "OpenStreetMap",
                      "distanza": "euclidea da centroide di sezione"},
        "nota": ("A ignora la geografia; B usa le marginali di sezione "
                 "pubblicate assumendo indipendenza dentro la sezione; C usa "
                 "la congiunta della popolazione rilasciata. B vs C e' il "
                 "confronto che riguarda il rilascio. Gli scarti sono "
                 "riferiti a C. Esempio illustrativo, non uno studio di "
                 "accessibilita'."),
        "comuni": ris}, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
