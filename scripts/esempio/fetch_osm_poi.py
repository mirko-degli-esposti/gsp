#!/usr/bin/env python3
"""
fetch_osm_poi.py — punti di interesse da OpenStreetMap, per l'esempio
decisionale del paper.

    python scripts/esempio/fetch_osm_poi.py 037006 --categoria farmacia
    python scripts/esempio/fetch_osm_poi.py --tutti --categoria farmacia

Che cosa fa
-----------
Interroga Overpass per una categoria di servizi dentro il confine
amministrativo di un comune, e scrive un CSV con una riga per punto:
`osm_id, categoria, nome, lon, lat`. Nient'altro: il nome serve solo a
rendere il file ispezionabile a occhio.

Che cosa NON e'
---------------
Questa fonte **non entra nel rilascio** e non e' registrata in
`fonti/registro.yaml` accanto alle fonti ISTAT. E' l'ingrediente di un
esempio illustrativo, e la differenza e' sostanziale: OpenStreetMap non
certifica la propria completezza, quindi il numero di farmacie che
questo script trova non e' il numero di farmacie che esistono.

L'esempio regge lo stesso, e vale la pena capire perche'. Cio' che
confronta sono due risposte alla stessa domanda --- una calcolata sulla
quota comunale, una sulle sezioni --- che usano **lo stesso identico
insieme di punti**. Se OSM ne omette alcuni, entrambe le risposte
cambiano insieme; lo scarto fra loro, che e' cio' che si misura, no.
Per la stessa ragione la distanza e' euclidea e non stradale: e' una
sottostima del percorso reale, ma identica per le due risposte.

Provenienza
-----------
Ogni CSV porta accanto un `.meta.json` con la query esatta, l'istante
dell'interrogazione, l'endpoint e il conteggio: senza quello il file e'
un elenco di coordinate senza universo, e la regola del progetto vale
anche per le fonti che non rilascia.

Dipendenze: requests. Nessuna chiave: Overpass e' pubblico, ma con una
politica d'uso equa --- lo script serializza le richieste e riprova con
attesa crescente sui 429/504.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

GSP = Path(os.environ.get("GSP_ROOT", Path.home() / "progetti" / "gsp"))
OUT = GSP / "data" / "esempio" / "poi"
ENDPOINT = os.environ.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")

# ---------------------------------------------------------------- categorie --
# Ogni categoria e' una lista di filtri OSM. Tenerle poche e mature: la
# copertura di OSM e' buona sui servizi che chiunque puo' verificare
# passando per strada, e cattiva su quelli che dipendono da una decisione
# amministrativa (centri diurni, servizi sociali), che spesso non ci sono.
CATEGORIE: dict[str, list[str]] = {
    "farmacia":   ['["amenity"="pharmacy"]'],
    "medico":     ['["amenity"="doctors"]', '["healthcare"="doctor"]'],
    "scuola":     ['["amenity"="school"]'],
    "infanzia":   ['["amenity"="kindergarten"]'],
    "alimentari": ['["shop"="supermarket"]', '["shop"="convenience"]'],
    "fermata":    ['["highway"="bus_stop"]', '["public_transport"="platform"]'],
}

# capoluoghi ER + Brescia: i comuni su cui l'esempio ha senso, perche' la
# copertura OSM e' buona e l'articolazione sub-comunale esiste.
COMUNI_ESEMPIO = {
    "037006": "Bologna",   "034027": "Parma",      "036023": "Modena",
    "035033": "Reggio nell'Emilia", "039014": "Ravenna", "099014": "Rimini",
    "038008": "Ferrara",   "040012": "Forlì",      "040007": "Cesena",
    "033032": "Piacenza",  "037021": "Castenaso",  "017029": "Brescia",
}


def query(codice: str, categoria: str) -> str:
    """Overpass QL: l'area amministrativa del comune per codice ISTAT.

    `ref:ISTAT` e' la chiave con cui i confini comunali italiani sono
    marcati in OSM; l'`admin_level=8` e' il comune. Cercare per nome
    sarebbe fragile (omonimie, accenti, forme ufficiali diverse).
    """
    filtri = CATEGORIE[categoria]
    corpo = "\n  ".join(
        f"node{f}(area.a);\n  way{f}(area.a);" for f in filtri
    )
    return f"""[out:json][timeout:180];
area["boundary"="administrative"]["admin_level"="8"]["ref:ISTAT"="{codice}"]->.a;
(
  {corpo}
);
out tags center;"""


def interroga(q: str, tentativi: int = 4) -> dict:
    testa = {"User-Agent": "animarium-esempio/1.0 (ricerca; mirko.degliesposti@unibo.it)"}
    attesa = 5
    for n in range(1, tentativi + 1):
        r = requests.post(ENDPOINT, data={"data": q}, headers=testa, timeout=300)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 502, 503, 504):
            print(f"    Overpass {r.status_code}, riprovo fra {attesa}s "
                  f"({n}/{tentativi})")
            time.sleep(attesa)
            attesa *= 2
            continue
        r.raise_for_status()
    sys.exit(f"Overpass non risponde dopo {tentativi} tentativi.")


def estrai(js: dict) -> list[dict]:
    """Un elemento OSM per riga. I `way` (edifici mappati come poligoni)
    danno la coordinata del centro, che Overpass calcola con `out center`."""
    righe = []
    for el in js.get("elements", []):
        if el["type"] == "node":
            lon, lat = el.get("lon"), el.get("lat")
        else:
            c = el.get("center") or {}
            lon, lat = c.get("lon"), c.get("lat")
        if lon is None or lat is None:
            continue
        righe.append({
            "osm_type": el["type"],
            "osm_id": el["id"],
            "nome": (el.get("tags") or {}).get("name", ""),
            "lon": round(lon, 6),
            "lat": round(lat, 6),
        })
    # dedup: uno stesso servizio puo' essere mappato come nodo dentro un way
    visti, out = set(), []
    for r in righe:
        k = (round(r["lon"], 5), round(r["lat"], 5), r["nome"])
        if k in visti:
            continue
        visti.add(k)
        out.append(r)
    return out


def scarica(codice: str, nome: str, categoria: str, forza: bool) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    csv = OUT / f"{codice}_{categoria}.csv"
    meta = OUT / f"{codice}_{categoria}.meta.json"
    if csv.exists() and not forza:
        n = sum(1 for _ in open(csv)) - 1
        print(f"  {nome:<20} {n:>5} punti  (gia' scaricato, --forza per rifare)")
        return n

    q = query(codice, categoria)
    t0 = time.time()
    js = interroga(q)
    righe = estrai(js)

    import csv as csvmod
    with open(csv, "w", newline="", encoding="utf-8") as f:
        w = csvmod.DictWriter(f, fieldnames=["osm_type", "osm_id", "nome", "lon", "lat"])
        w.writeheader()
        w.writerows(righe)

    json.dump({
        "comune": codice,
        "nome": nome,
        "categoria": categoria,
        "n_punti": len(righe),
        "endpoint": ENDPOINT,
        "interrogato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "secondi": round(time.time() - t0, 1),
        "query": q,
        "licenza": "ODbL 1.0",
        "attribuzione": "(c) OpenStreetMap contributors",
        "universo": (
            "Punti mappati in OpenStreetMap al momento dell'interrogazione, "
            "dentro il confine amministrativo del comune. La completezza NON "
            "e' certificata: il conteggio non e' il numero di servizi "
            "esistenti. Fonte esterna al rilascio, usata solo per l'esempio "
            "illustrativo."),
    }, open(meta, "w"), indent=2, ensure_ascii=False)

    print(f"  {nome:<20} {len(righe):>5} punti  -> {csv.name}")
    return len(righe)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comune", nargs="?", help="codice ISTAT")
    ap.add_argument("--tutti", action="store_true",
                    help=f"i {len(COMUNI_ESEMPIO)} comuni dell'esempio")
    ap.add_argument("--categoria", default="farmacia", choices=sorted(CATEGORIE))
    ap.add_argument("--forza", action="store_true", help="riscarica anche se esiste")
    ap.add_argument("--stampa-query", action="store_true",
                    help="stampa la query Overpass ed esce")
    args = ap.parse_args()

    if args.tutti:
        bersagli = list(COMUNI_ESEMPIO.items())
    elif args.comune:
        bersagli = [(args.comune, COMUNI_ESEMPIO.get(args.comune, args.comune))]
    else:
        ap.error("indicare un codice comune, oppure --tutti")

    if args.stampa_query:
        print(query(bersagli[0][0], args.categoria))
        return

    print(f"OpenStreetMap · {args.categoria} · {ENDPOINT}")
    tot = 0
    for i, (cod, nome) in enumerate(bersagli):
        tot += scarica(cod, nome, args.categoria, args.forza)
        if i < len(bersagli) - 1:
            time.sleep(3)          # politica d'uso equa di Overpass
    print(f"\n  totale {tot} punti in {len(bersagli)} comuni")
    print(f"  in {OUT}")
    print("\n  Fonte esterna al rilascio: completezza non certificata,")
    print("  usata solo per l'esempio illustrativo (vedi .meta.json).")


if __name__ == "__main__":
    main()
