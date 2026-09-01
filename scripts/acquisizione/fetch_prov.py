"""
fetch_prov.py — canale SPERIMENTALE: una query SDMX per molti comuni.

Perché: ~318 comuni ER mancanti x 10 tavole = ~3.200 query singole al
ritmo di 5/min; per provincia diventano ~90. Ma il canale va collaudato
PRIMA di promuoverlo: scrive in una SHADOW DIRECTORY, mai in
data/comuni/, e la promozione passa dal confronto semantico con i
known-good del canale singolo (confronta_prov.py).

Meccanica: sdmx.fetch accetta liste per dimensione (la spec anag usa
già SEX=[1,2] -> key "1+2"). La query multi-comune è la stessa cosa
sulla dimensione territorio: REF_AREA=033001+033002+...
La risposta si spacchetta per comune, producendo raw+decoded IDENTICI
per formato a quelli di fetch_one: a valle nessuno deve sapere da
quale canale arriva un file.

Trappola nota, gestita: i codici territorio possono perdere lo zero
iniziale (REF_AREA int nei decoded — già pagato in C3): lo split
confronta su int, mai su stringa.

Uso (pilota):
  python scripts/acquisizione/fetch_prov.py --tavola cens_istruzione_eta \
      --comuni 040007 040012
  python scripts/acquisizione/fetch_prov.py --tavola cens_istruzione_eta \
      --comuni-da-file /tmp/comuni_040.txt
"""
import argparse
import os
import sys

import pandas as pd

import gsp.istat.sdmx as sdmx
from fetch_comune import CORE, find_territory_dim   # stessi mattoni, mai copiati

SHADOW = os.path.expanduser("~/progetti/gsp/data/prov_shadow")


def fetch_molti(comuni: list[str], name: str):
    """Una query per la tavola su TUTTI i comuni della lista; ritorna
    (df_raw, xml_path, terr_dim). Le eccezioni salgono al chiamante,
    come in fetch_one."""
    cfg = CORE[name]
    xml_path = sdmx.get_structure(cfg["flow"])
    terr_dim, _ = find_territory_dim(xml_path, comuni[0])
    if terr_dim is None:
        raise ValueError(f"{comuni[0]} non in nessuna codelist territoriale")
    spec = dict(cfg["spec"])
    spec[terr_dim] = comuni                    # la lista -> key 033001+033002+...
    df = sdmx.fetch(cfg["flow"], spec)
    return df, xml_path, terr_dim


def spacchetta(df, xml_path, terr_dim, comuni, name):
    """Split per comune + salvataggio raw/decoded in SHADOW, formato
    fetch_one. Decodifica UNA volta sul frame intero, poi split sugli
    stessi indici (stesso risultato, un decimo del costo).
    Confronto codici su int: lo zero iniziale non è affidabile."""
    decoded = sdmx.decode(df, xml_path)
    terr_int = pd.to_numeric(df[terr_dim], errors="coerce").astype("Int64")

    esiti = []
    for cod in comuni:
        mask = terr_int == int(cod)
        n = int(mask.sum())
        if n == 0:
            esiti.append((cod, "ASSENTE", 0))
            continue
        out = os.path.join(SHADOW, cod)
        os.makedirs(out, exist_ok=True)
        df[mask].to_csv(os.path.join(out, f"{name}_raw.csv"), index=False)
        decoded[mask.values].to_csv(
            os.path.join(out, f"{name}_decoded.csv"), index=False)
        esiti.append((cod, "OK", n))
    return esiti

MAX_CODICI_KEY = 30   # il guard di sdmx.build_key (250 char) vale sull'INTERA
                      # key, non sul solo territorio: la key non contiene '/',
                      # quindi split('/') = un segmento unico. 30 codici =
                      # 209 char di territorio + ~28 di overhead dims (caso
                      # peggiore: anag, con MARITAL_STATUS esplicito) = ~237,
                      # sotto soglia con margine. Misurato: 35 codici -> 272.


def fetch_molti(comuni: list[str], name: str):
    """Una query logica per (lista comuni, tavola); se la lista supera
    MAX_CODICI_KEY viene spezzata in chunk e i frame concatenati —
    stessa risposta, piu' viaggi. Il chiamante non vede la differenza.
    Le eccezioni salgono: un chunk fallito fa fallire il gruppo intero,
    che resta 'mancante' e si ritenta (nessun gruppo mezzo-scaricato)."""
    cfg = CORE[name]
    xml_path = sdmx.get_structure(cfg["flow"])
    terr_dim, _ = find_territory_dim(xml_path, comuni[0])
    if terr_dim is None:
        raise ValueError(f"{comuni[0]} non in nessuna codelist territoriale")

    pezzi = []
    for i in range(0, len(comuni), MAX_CODICI_KEY):
        chunk = comuni[i:i + MAX_CODICI_KEY]
        spec = dict(cfg["spec"])
        spec[terr_dim] = chunk
        pezzi.append(sdmx.fetch(cfg["flow"], spec))
        if i + MAX_CODICI_KEY < len(comuni):
            import time; time.sleep(15)      # il ritmo vale anche fra chunk
    df = pd.concat(pezzi, ignore_index=True) if len(pezzi) > 1 else pezzi[0]
    return df, xml_path, terr_dim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tavola", required=True, choices=sorted(CORE))
    ap.add_argument("--comuni", nargs="*", default=[])
    ap.add_argument("--comuni-da-file", default=None,
                    help="un codice per riga")
    a = ap.parse_args()

    comuni = list(a.comuni)
    if a.comuni_da_file:
        comuni += [r.strip() for r in open(a.comuni_da_file) if r.strip()]
    if not comuni:
        sys.exit("nessun comune: --comuni o --comuni-da-file")

    df, xml, terr = fetch_molti(comuni, a.tavola)
    print(f"[prov] {a.tavola}: {len(df)} righe totali per {len(comuni)} comuni "
          f"richiesti (attese ~{len(comuni)} x invariante, se la tavola ne ha uno)")
    for cod, st, n in spacchetta(df, xml, terr, comuni, a.tavola):
        print(f"  {cod}  {st:<8} {n:>6} righe")
    print(f"[prov] shadow: {SHADOW}/<comune>/{a.tavola}_*.csv — "
          f"NON promosso: confrontare coi known-good prima")


if __name__ == "__main__":
    main()