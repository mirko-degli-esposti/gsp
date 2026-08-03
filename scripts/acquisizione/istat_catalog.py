"""
Catalogo dataflow ISTAT SDMX (esploradati) — scarica una volta, greppa in locale.

Uso:
    python scripts/acquisizione/istat_catalog.py                # scarica/aggiorna il catalogo, stampa statistiche
    python scripts/acquisizione/istat_catalog.py istruzione     # grep case-insensitive su id + nomi
    python scripts/acquisizione/istat_catalog.py "condizione professionale"
    python scripts/acquisizione/istat_catalog.py --refresh      # forza ri-download del catalogo

Output in OUT_DIR:
    catalog_dataflows.xml   (risposta grezza, cache)
    catalog_dataflows.csv   (dataflow_id, version, name_it, name_en)

Ambiente: WSL2 / conda env "ml". Dipendenze: requests, pandas, lxml.
"""

import os
import sys
import requests
import pandas as pd
from lxml import etree

BASE = "https://esploradati.istat.it/SDMXWS/rest"
CATALOG_URL = f"{BASE}/dataflow/IT1"   # tutti i dataflow dell'agenzia IT1

OUT_DIR = os.path.expanduser("~/progetti/gsp/data/istat_catalog")
os.makedirs(OUT_DIR, exist_ok=True)
XML_PATH = os.path.join(OUT_DIR, "catalog_dataflows.xml")
CSV_PATH = os.path.join(OUT_DIR, "catalog_dataflows.csv")

NS = {
    "s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def fetch_catalog(refresh: bool = False) -> str:
    if os.path.exists(XML_PATH) and not refresh:
        print(f"[catalog] cache trovata: {XML_PATH}")
        return XML_PATH
    r = requests.get(CATALOG_URL, timeout=180)
    r.raise_for_status()
    with open(XML_PATH, "wb") as f:
        f.write(r.content)
    print(f"[catalog] salvato {XML_PATH} ({len(r.content)/1024:.0f} KB)")
    return XML_PATH


def parse_catalog(xml_path: str) -> pd.DataFrame:
    tree = etree.parse(xml_path)
    rows = []
    for df_el in tree.iterfind(".//s:Dataflow", NS):
        names = {n.get(XML_LANG): n.text for n in df_el.findall("c:Name", NS)}
        rows.append({
            "dataflow_id": df_el.get("id"),
            "version": df_el.get("version"),
            "name_it": names.get("it") or "",
            "name_en": names.get("en") or "",
        })
    df = pd.DataFrame(rows).sort_values("dataflow_id").reset_index(drop=True)
    df.to_csv(CSV_PATH, index=False)
    print(f"[catalog] {len(df)} dataflow -> {CSV_PATH}")
    return df


def load_catalog() -> pd.DataFrame:
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH).fillna("")
    return parse_catalog(fetch_catalog())


def grep_catalog(pattern: str, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Cerca (case-insensitive, regex ok) in id e nomi it/en."""
    if df is None:
        df = load_catalog()
    mask = (
        df["dataflow_id"].str.contains(pattern, case=False, regex=True)
        | df["name_it"].str.contains(pattern, case=False, regex=True)
        | df["name_en"].str.contains(pattern, case=False, regex=True)
    )
    hits = df[mask].reset_index(drop=True)
    with pd.option_context("display.max_rows", None, "display.max_colwidth", 100):
        print(hits[["dataflow_id", "name_it"]].to_string())
    print(f"\n[grep] '{pattern}': {len(hits)} risultati")
    return hits


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--refresh"]
    refresh = "--refresh" in sys.argv
    cat = parse_catalog(fetch_catalog(refresh)) if (refresh or not os.path.exists(CSV_PATH)) \
        else load_catalog()
    if args:
        grep_catalog(" ".join(args), cat)
    else:
        print(f"[catalog] {len(cat)} dataflow disponibili. Esempio: "
              f"python scripts/acquisizione/istat_catalog.py istruzione")
