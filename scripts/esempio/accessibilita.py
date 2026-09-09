#!/usr/bin/env python3
"""
accessibilita.py — l'esempio decisionale: la stessa domanda, due geografie.

    python scripts/esempio/accessibilita.py 037006
    python scripts/esempio/accessibilita.py --tutti --eta 75 --raggio 500

La domanda
----------
*Quanti residenti anziani vivono oltre una certa distanza dalla farmacia
piu' vicina?* E' la forma minima di una decisione di programmazione: dove
mettere un servizio, chi non e' coperto, quanto vale il divario.

Le due risposte
---------------
**A, comunale.** E' cio' che si puo' fare oggi con le sole statistiche
pubblicate: si sa quanti anziani ha il comune, e si sa quali sezioni sono
scoperte; non si sa dove stiano gli anziani. La risposta applica la quota
comunale di over-N alla popolazione delle sezioni scoperte --- cioe'
assume che gli anziani siano distribuiti come tutti gli altri.

**B, di sezione.** Conta gli over-N nelle sezioni scoperte, dove
effettivamente sono.

Che cosa misura
---------------
Lo scarto fra A e B, e **il suo segno**. Se gli anziani stanno nei centri
storici, dove i servizi abbondano, A sovrastima il problema; se stanno
nelle frazioni, lo sottostima. La tesi non e' che B sia la verita': e' che
A non descrive nessun luogo in particolare, e che la direzione dell'errore
dipende da come quella citta' e' fatta --- quindi non e' correggibile a
priori. Su piu' comuni, se il segno cambia, la dimostrazione e' completa.

Che cosa NON e'
---------------
Uno studio di accessibilita'. La distanza e' euclidea, non stradale; i
punti vengono da OpenStreetMap, la cui completezza non e' certificata
(`confronta_poi.py` la misura dove esiste un elenco comunale); la
copertura e' un cerchio, non un bacino d'utenza. Ognuna di queste e' una
semplificazione, e **nessuna tocca il confronto**: le due risposte usano
gli stessi punti, la stessa metrica e la stessa soglia. Cio' che cambia
fra A e B e' solo la geografia della popolazione.

Le coordinate del rilascio pubblico sono randomizzate dentro la sezione,
quindi la distanza e' calcolata dal **centroide della sezione**, che e'
l'unita' su cui il rilascio e' esatto per costruzione.

Dipendenze: pandas, pyarrow.
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
    "038008": "Ferrara",   "040012": "Forlì",      "040007": "Cesena",
    "033032": "Piacenza",   "017029": "Brescia",
}

# castenso fuori  "037021": "Castenaso",

FUORI_REGIONE = {"017029"}      # Brescia: in flotta per il tier 1, non per questo esempio

def analizza(codice: str, eta: int, raggio: float, quantile: float | None = None) -> dict | None:
    import numpy as np

    pq = ANIM / "bundle" / "comuni" / codice / "pop.parquet"
    poi = POI / f"{codice}_farmacia.csv"
    if not pq.exists():
        print(f"  [salto] manca {pq}")
        return None
    if not poi.exists():
        print(f"  [salto] manca {poi} — eseguire fetch_osm_poi.py")
        return None

    pop = pd.read_parquet(pq, columns=["sezione", "eta_anni", "lon", "lat"])
    servizi = pd.read_csv(poi)

    # --- centroidi di sezione, dalla popolazione stessa -------------------
    # Le coordinate individuali sono randomizzate dentro la sezione: la loro
    # media e' il centroide della nuvola, cioe' della sezione. E' l'unita'
    # su cui il rilascio e' esatto, ed e' la scala a cui la domanda ha senso.
    sez = pop.groupby("sezione").agg(
        n=("eta_anni", "size"),
        anziani=("eta_anni", lambda s: int((s >= eta).sum())),
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
        soglia = sez["dist"].quantile(1 - quantile)
        sez["scoperta"] = sez["dist"] >= soglia
    else:
        soglia = raggio
        sez["scoperta"] = sez["dist"] > raggio

    tot_pop = int(sez["n"].sum())
    tot_anz = int(sez["anziani"].sum())
    quota_com = tot_anz / tot_pop

    scop = sez[sez["scoperta"]]
    pop_scoperta = int(scop["n"].sum())

    # A: quota comunale applicata alla popolazione scoperta
    a = quota_com * pop_scoperta
    # B: gli anziani che stanno davvero nelle sezioni scoperte
    b = int(scop["anziani"].sum())

    r = {
        "comune": codice, "nome": COMUNI.get(codice, codice),
        "eta": eta, "raggio_m": raggio,
        "n_servizi": int(len(servizi)),
        "popolazione": tot_pop, "anziani": tot_anz,
        "quota_comunale": round(quota_com, 4),
        "sezioni": int(len(sez)), "sezioni_scoperte": int(len(scop)),
        "popolazione_scoperta": pop_scoperta,
        "A_stima_comunale": round(a, 1),
        "B_conteggio_sezioni": b,
        "scarto": round(b - a, 1),
        "scarto_relativo": round((b - a) / a, 4) if a else None,
        "quota_anziani_scoperta": round(b / pop_scoperta, 4) if pop_scoperta else None,
        "criterio": (f"quintile piu' lontano ({quantile:.0%})" if quantile
                     else f"oltre {raggio:.0f} m"),
        "soglia_effettiva_m": round(float(soglia), 1),
    }

    segno = "sottostima" if r["scarto"] > 0 else "sovrastima"
    print(f"  {r['nome']:<20} {r['sezioni_scoperte']:>4}/{r['sezioni']} sezioni "
          f"scoperte · A {a:>8.0f} · B {b:>6} · "
          f"{segno} del {abs(r['scarto_relativo'])*100:>4.1f}%")
    return r


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comune", nargs="?")
    ap.add_argument("--tutti", action="store_true")
    ap.add_argument("--eta", type=int, default=75,
                    help="soglia d'eta' (default 75)")
    ap.add_argument("--raggio", type=float, default=500.0,
                    help="metri oltre i quali una sezione e' scoperta")
    ap.add_argument("--quantile", type=float, default=None, help="frazione di sezioni piu' lontane, es. 0.20")
    ap.add_argument("--solo-er", action="store_true",
                    help="esclude i comuni fuori Emilia-Romagna (coerenza regionale)")
    args = ap.parse_args()

    bersagli = list(COMUNI) if args.tutti else ([args.comune] if args.comune
                                                else ap.error("comune o --tutti"))

    if args.solo_er:
        esclusi = [c for c in bersagli if c in FUORI_REGIONE]
        bersagli = [c for c in bersagli if c not in FUORI_REGIONE]
        if esclusi:
            print(f"  [escluso] {', '.join(COMUNI[c] for c in esclusi)}: "
                  f"fuori regione\n")

    #print(f"accessibilita': over-{args.eta}, farmacia oltre {args.raggio:.0f} m")
    crit = (f"il {args.quantile:.0%} di sezioni piu' lontane"
            if args.quantile else f"farmacia oltre {args.raggio:.0f} m")
    print(f"accessibilita': over-{args.eta}, {crit}")    
    print("  A = quota comunale applicata alla popolazione scoperta")
    print("  B = anziani contati nelle sezioni scoperte\n")

    ris = [r for c in bersagli if (r := analizza(c, args.eta, args.raggio, args.quantile))]
    if not ris:
        return

    segni = {("+" if r["scarto"] > 0 else "-") for r in ris}
    print()
    if len(segni) > 1:
        print("  Il segno dello scarto CAMBIA fra i comuni: non esiste una")
        print("  correzione da applicare alla media comunale, perche' la")
        print("  direzione dell'errore dipende da come la citta' e' fatta.")
    else:
        print("  Il segno dello scarto e' lo stesso in tutti i comuni esaminati.")

    out = OUT / f"accessibilita_over{args.eta}_{int(args.raggio)}m.json"
    json.dump({"parametri": {"eta": args.eta, "raggio_m": args.raggio,
                             "servizio": "farmacia", "fonte_poi": "OpenStreetMap",
                             "distanza": "euclidea da centroide di sezione"},
               "avvertenza": ("Esempio illustrativo, non uno studio di "
                              "accessibilita'. Le due risposte usano gli stessi "
                              "punti, la stessa metrica e la stessa soglia: cio' "
                              "che cambia e' solo la geografia della popolazione."),
               "comuni": ris}, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
