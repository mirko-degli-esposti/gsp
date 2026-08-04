#!/usr/bin/env python3
"""scarica_cognomi_wiki.py — repertori onomastici dalle categorie MediaWiki.

Usa l'API delle categorie, non lo scraping della pagina: restituisce JSON
pulito, e' paginata, ed e' fatta per essere usata. La provenienza risulta
riproducibile — l'URL e la data finiscono nel file — mentre un
copia-incolla dalla pagina darebbe «l'ho preso da un sito», che e'
precisamente cio' che il registro rifiuta.

    python scarica_cognomi_wiki.py --elenco
    python scarica_cognomi_wiki.py MA_ARAB NG_YORUBA
    python scarica_cognomi_wiki.py --tutti --out data/nomi/wiki

I titoli delle voci SONO i cognomi: `Category:Surnames_of_Moroccan_origin`
contiene pagine intitolate «Bennani», non pagine su persone di cognome
Bennani. `cmnamespace=0` esclude sottocategorie e pagine di servizio.
"""

import argparse
import csv
import json
import os
import re
import time
import unicodedata
import urllib.parse
import urllib.request

# I repertori disponibili. La chiave e' il codice usato in
# fonti/paesi_onomastici.yaml, non un codice ISO: sono estensioni per
# prossimita' linguistica, e un codice di paese suggerirebbe una
# corrispondenza che non c'e'.
REPERTORI = {
    "MA_ARAB": {
        "dominio": "en.wikipedia.org",
        "categoria": "Category:Surnames_of_Moroccan_origin",
        "nota": "cognomi di origine marocchina, arabi e berberi",
    },
    "NG_YORUBA": {
        "dominio": "en.wiktionary.org",
        "categoria": "Category:Yoruba surnames",
        "nota": "cognomi yoruba: UNO dei tre grandi repertori nigeriani, "
                "accanto a igbo e hausa",
    },
    "NG_IGBO": {
        "dominio": "en.wiktionary.org",
        "categoria": "Category:Igbo surnames",
        "nota": "cognomi igbo, Nigeria sud-orientale",
    },
    "NG_HAUSA": {
        "dominio": "en.wiktionary.org",
        "categoria": "Category:Hausa surnames",
        "nota": "cognomi hausa, Nigeria settentrionale; largamente "
                "sovrapposti al repertorio arabo-islamico",
    },
    "AK_AKAN": {
        "dominio": "en.wiktionary.org",
        "categoria": "Category:Akan surnames",
        "nota": "cognomi akan, Ghana e Costa d'Avorio",
    },
    "WOLOF": {
        "dominio": "en.wiktionary.org",
        "categoria": "Category:Wolof surnames",
        "nota": "cognomi wolof, Senegal e Gambia",
    },
}

# Suffissi che MediaWiki aggiunge per disambiguare: non fanno parte del
# cognome.
DISAMBIGUA = re.compile(
    r"\s*\((surname|name|disambiguation|given name|family name)\)\s*$", re.I)


def senza_diacritici(s):
    """«Adebayọ» -> «Adebayo».

    Un nigeriano residente in Italia scrive il cognome senza i segni
    tonali yoruba: i documenti italiani non li portano, e una popolazione
    sintetica italiana nemmeno. L'originale resta comunque nel file,
    perche' buttarlo sarebbe una perdita e perche' e' cio' che la fonte
    dice davvero.
    """
    n = unicodedata.normalize("NFKD", s)
    return "".join(c for c in n if not unicodedata.combining(c))


def scarica(dominio, categoria, pausa=0.5, limite_pagine=20):
    """Tutti i titoli della categoria, seguendo la paginazione."""
    fuori, cont, pagine = [], None, 0
    while pagine < limite_pagine:
        p = {"action": "query", "list": "categorymembers",
             "cmtitle": categoria, "cmlimit": "500", "cmnamespace": "0",
             "format": "json"}
        if cont:
            p["cmcontinue"] = cont
        url = f"https://{dominio}/w/api.php?{urllib.parse.urlencode(p)}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "gsp-registro-fonti/1.0 "
                                        "(ricerca accademica; unibo.it)"})
        with urllib.request.urlopen(req, timeout=30) as f:
            d = json.load(f)
        if "error" in d:
            raise SystemExit(f"API: {d['error'].get('info')}")
        fuori += [x["title"] for x in d["query"]["categorymembers"]]
        cont = d.get("continue", {}).get("cmcontinue")
        pagine += 1
        if not cont:
            break
        time.sleep(pausa)
    if cont:
        print(f"  [avviso] fermato a {limite_pagine} pagine: la categoria "
              f"e' piu' grande di {len(fuori)} voci")
    return fuori


def salva(codice, titoli, out):
    r = REPERTORI[codice]
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"cognomi_{codice}.csv")
    righe, scartati = [], []
    visti = set()
    for t in titoli:
        c = DISAMBIGUA.sub("", t).strip()
        if not c or len(c) < 2 or any(ch.isdigit() for ch in c):
            scartati.append(t)
            continue
        piano = senza_diacritici(c)
        if piano.lower() in visti:
            continue
        visti.add(piano.lower())
        righe.append({"cognome": piano, "originale": c,
                      "diacritici": int(piano != c)})
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["# fonte", f"https://{r['dominio']}", r["categoria"]])
        w.writerow(["# licenza", "CC-BY-SA-4.0", "en.wikipedia.org/wiki/"
                    "Wikipedia:Text_of_the_Creative_Commons_Attribution-"
                    "ShareAlike_4.0_International_License"])
        w.writerow(["# scaricato", time.strftime("%Y-%m-%d"), r["nota"]])
        w.writerow(["cognome", "originale", "diacritici"])
        for x in righe:
            w.writerow([x["cognome"], x["originale"], x["diacritici"]])
    dia = sum(x["diacritici"] for x in righe)
    print(f"  {codice:<11} {len(righe):>4} cognomi  "
          f"({dia} con diacritici, {len(titoli)-len(righe)} scartati o "
          f"doppi)  -> {path}")
    return righe


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codici", nargs="*", help="quali repertori scaricare")
    ap.add_argument("--tutti", action="store_true")
    ap.add_argument("--elenco", action="store_true")
    ap.add_argument("--out", default="data/nomi/wiki")
    a = ap.parse_args()

    if a.elenco or (not a.codici and not a.tutti):
        print("repertori disponibili:\n")
        for k, v in REPERTORI.items():
            print(f"  {k:<11} {v['dominio']:<20} {v['categoria']}")
            print(f"              {v['nota']}")
        return

    codici = list(REPERTORI) if a.tutti else a.codici
    for c in codici:
        if c not in REPERTORI:
            print(f"  {c}: sconosciuto, salto")
            continue
        r = REPERTORI[c]
        try:
            t = scarica(r["dominio"], r["categoria"])
        except Exception as e:                               # noqa: BLE001
            print(f"  {c:<11} ERRORE: {e}")
            continue
        if not t:
            print(f"  {c:<11} categoria vuota o inesistente: "
                  f"{r['categoria']}")
            continue
        salva(c, t, a.out)


if __name__ == "__main__":
    main()
