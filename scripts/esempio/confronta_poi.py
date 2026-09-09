#!/usr/bin/env python3
"""
confronta_poi.py — quanto e' completo OpenStreetMap, misurato contro una
fonte comunale.

    python scripts/esempio/confronta_poi.py 037006 --categoria farmacia \\
        --comunale ~/scarichi/farmacie.csv

Perche' serve
-------------
L'esempio decisionale usa OSM perche' e' una fonte sola per tutta Italia.
Il prezzo e' che la sua completezza non e' certificata. Dove esiste anche
un elenco comunale --- Bologna pubblica le sue farmacie --- si puo'
misurare quel prezzo invece di supporlo, e riportare il numero nel paper.

L'accoppiamento e' per distanza: due punti sono lo stesso servizio se
distano meno di una soglia. Non per nome, perche' i nomi divergono
sistematicamente ("COMUNALE BATTINDARNO" contro "Farmacia Comunale n. 12")
e un confronto testuale misurerebbe la nomenclatura, non la copertura.

Che cosa NON dimostra
---------------------
Che l'elenco comunale sia completo a sua volta. Un punto comunale senza
corrispondenza OSM e' un buco di OSM; un punto OSM senza corrispondenza
comunale puo' essere un errore di OSM oppure una farmacia che il comune
non elenca (parafarmacie, aperture recenti). Lo script riporta entrambe
le direzioni e non le interpreta.

Il file comunale e' atteso con separatore `;` e una colonna di coordinate
"lat, lon" (il formato di opendata Bologna). Con `--colonne` si adatta.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path

GSP = Path(os.environ.get("GSP_ROOT", Path.home() / "progetti" / "gsp"))
POI = GSP / "data" / "esempio" / "poi"


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Metri fra due (lat, lon). Equirettangolare: su scala urbana lo
    scarto dalla geodetica e' sotto il decimetro, e qui si confrontano
    soglie di decine di metri."""
    R = 6371000.0
    p = math.pi / 180.0
    dlat = (b[0] - a[0]) * p
    dlon = (b[1] - a[1]) * p
    latm = (a[0] + b[0]) / 2.0 * p
    return R * math.hypot(dlat, dlon * math.cos(latm))


def leggi_comunale(percorso: Path, col_geo: str, col_nome: str,
                   sep: str) -> list[dict]:
    fuori = []
    with open(percorso, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=sep):
            g = (r.get(col_geo) or "").strip()
            if not g:
                continue
            try:
                lat, lon = (float(x) for x in g.split(",")[:2])
            except ValueError:
                continue
            fuori.append({"nome": (r.get(col_nome) or "").strip(),
                          "lat": lat, "lon": lon,
                          "extra": {k: v for k, v in r.items()
                                    if k not in (col_geo,)}})
    return fuori


def leggi_osm(codice: str, categoria: str) -> list[dict]:
    p = POI / f"{codice}_{categoria}.csv"
    if not p.exists():
        sys.exit(f"manca {p}\nEseguire prima: fetch_osm_poi.py {codice} "
                 f"--categoria {categoria}")
    with open(p, encoding="utf-8") as f:
        return [{"nome": r["nome"], "lat": float(r["lat"]), "lon": float(r["lon"])}
                for r in csv.DictReader(f)]


def accoppia(a: list[dict], b: list[dict], soglia: float) -> tuple[list, list]:
    """Accoppiamento greedy per distanza crescente: ogni punto di `a` prende
    il piu' vicino ancora libero in `b`, se entro soglia. Greedy e non
    ottimale, ma con punti sparsi di decine di metri la differenza
    dall'assegnamento ottimo e' nulla, e il codice resta leggibile."""
    coppie = []
    liberi = list(range(len(b)))
    for i, x in enumerate(a):
        best, bd = None, soglia + 1
        for j in liberi:
            d = haversine((x["lat"], x["lon"]), (b[j]["lat"], b[j]["lon"]))
            if d < bd:
                best, bd = j, d
        if best is not None and bd <= soglia:
            coppie.append((i, best, bd))
            liberi.remove(best)
    accoppiati_a = {i for i, _, _ in coppie}
    orfani_a = [i for i in range(len(a)) if i not in accoppiati_a]
    return coppie, orfani_a


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comune")
    ap.add_argument("--categoria", default="farmacia")
    ap.add_argument("--comunale", required=True, type=Path,
                    help="CSV della fonte comunale")
    ap.add_argument("--col-geo", default="Geo Point",
                    help="colonna con 'lat, lon' (default: opendata Bologna)")
    ap.add_argument("--col-nome", default="FARMACIA")
    ap.add_argument("--sep", default=";")
    ap.add_argument("--soglia", type=float, default=150.0,
                    help="metri entro cui due punti sono lo stesso servizio")
    args = ap.parse_args()

    com = leggi_comunale(args.comunale, args.col_geo, args.col_nome, args.sep)
    osm = leggi_osm(args.comune, args.categoria)
    if not com:
        sys.exit(f"nessuna coordinata letta da {args.comunale}: "
                 f"controllare --col-geo e --sep")
    print(f"fonte comunale : {len(com):>4} punti  ({args.comunale.name})")
    print(f"OpenStreetMap  : {len(osm):>4} punti")

    print("\ncopertura di OSM sulla fonte comunale, per soglia")
    for s in (25, 50, 100, 150, 250, 500):
        c, _ = accoppia(com, osm, s)
        print(f"  entro {s:>3} m   {len(c):>4}/{len(com)}   "
              f"{100*len(c)/len(com):>5.1f}%")

    coppie, orfani_com = accoppia(com, osm, args.soglia)
    accoppiati_osm = {j for _, j, _ in coppie}
    orfani_osm = [j for j in range(len(osm)) if j not in accoppiati_osm]
    dist = sorted(d for _, _, d in coppie)

    print(f"\nalla soglia di {args.soglia:.0f} m")
    print(f"  accoppiati            {len(coppie)}")
    print(f"  comunali senza OSM    {len(orfani_com)}   <- buchi di OSM")
    print(f"  OSM senza comunale    {len(orfani_osm)}   <- da interpretare")
    if dist:
        print(f"  distanza mediana      {dist[len(dist)//2]:.0f} m"
              f"   (max {dist[-1]:.0f} m)")

    if orfani_com:
        print("\ncomunali senza corrispondenza (prime 15):")
        for i in orfani_com[:15]:
            c = com[i]
            vic = min(osm, key=lambda o: haversine((c["lat"], c["lon"]),
                                                   (o["lat"], o["lon"])))
            d = haversine((c["lat"], c["lon"]), (vic["lat"], vic["lon"]))
            print(f"  {c['nome'][:34]:<34} OSM piu' vicina a {d:>5.0f} m")

    if orfani_osm:
        print("\nOSM senza corrispondenza comunale (prime 15):")
        for j in orfani_osm[:15]:
            print(f"  {(osm[j]['nome'] or '(senza nome)')[:50]}")

    out = POI / f"{args.comune}_{args.categoria}_confronto.json"
    json.dump({
        "comune": args.comune, "categoria": args.categoria,
        "soglia_m": args.soglia,
        "n_comunale": len(com), "n_osm": len(osm),
        "accoppiati": len(coppie),
        "comunali_senza_osm": len(orfani_com),
        "osm_senza_comunale": len(orfani_osm),
        "copertura_osm": round(len(coppie) / len(com), 4),
        "distanza_mediana_m": round(dist[len(dist)//2], 1) if dist else None,
        "fonte_comunale": str(args.comunale),
        "nota": ("Accoppiamento per distanza, non per nome. Un punto comunale "
                 "senza corrispondenza e' un buco di OSM; un punto OSM senza "
                 "corrispondenza comunale puo' essere un errore di OSM o un "
                 "servizio che il comune non elenca. Lo script non interpreta."),
    }, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
