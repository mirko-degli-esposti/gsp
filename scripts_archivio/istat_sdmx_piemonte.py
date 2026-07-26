"""
Download ISTAT SDMX (esploradati) — Popolazione residente al 1° gennaio
per età, sesso e stato civile — Piemonte (ITC1), 2024.

Dataflow: IT1,22_289_DF_DCIS_POPRES1_26,1.0

Ambiente: WSL2 / conda env "ml" (Python 3.11).
Dipendenze: requests, pandas, lxml (tutte standard; se manca lxml:
    pip install lxml   — poi restart kernel se in notebook)

Uso:
    python istat_sdmx_piemonte.py
Output in OUT_DIR:
    popres_itc1_2024_raw.csv     (SDMX-CSV come arriva dal server)
    popres_itc1_2024_tidy.csv    (colonne decodificate, pronte per i marginali)
    structure_popres1_26.xml     (cache della struttura + codelist)
"""

import os
import time
import io
import requests
import pandas as pd
from lxml import etree

# ----------------------------------------------------------------------
# Config (pattern locale: expanduser, niente /content/drive)
# ----------------------------------------------------------------------
BASE = "https://esploradati.istat.it/SDMXWS/rest"
FLOW = "IT1,22_289_DF_DCIS_POPRES1_26,1.0"
FLOW_ID = "22_289_DF_DCIS_POPRES1_26"

# Età in wildcard (posizione vuota): il key esplicito supera il limite
# di 260 char/segmento del frontend http.sys di esploradati.
# I codici aggregati (TOTAL ecc.) vengono filtrati a valle in tidy().
KEY = "A.ITC1.JAN.1+2..1+2+3+4+15+16+17"

DATA_URL = (
    f"{BASE}/data/{FLOW}/{KEY}/ALL/"
    "?detail=full&startPeriod=2024-01-01&endPeriod=2024-12-31"
    "&dimensionAtObservation=TIME_PERIOD"
)
STRUCT_URL = (
    f"{BASE}/dataflow/IT1/{FLOW_ID}/1.0/?detail=Full&references=Descendants"
)

OUT_DIR = os.path.expanduser("~/progetti/gsp/data/istat_piemonte")
# in alternativa: os.path.expanduser("~/gdrive/GSP/data/istat_piemonte")
os.makedirs(OUT_DIR, exist_ok=True)

RATE_SLEEP = 13  # ~5 query/min: margine di sicurezza tra chiamate

# ----------------------------------------------------------------------
# 1) Dati in SDMX-CSV (niente parsing XML)
# ----------------------------------------------------------------------
def fetch_data() -> pd.DataFrame:
    headers = {"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"}
    r = requests.get(DATA_URL, headers=headers, timeout=120)
    r.raise_for_status()
    ctype = r.headers.get("Content-Type", "")
    if "csv" not in ctype and not r.text.lstrip().startswith(("DATAFLOW", "STRUCTURE")):
        raise RuntimeError(
            f"Risposta non CSV (Content-Type: {ctype}). "
            "Il server ha ignorato l'header Accept: ispezionare r.text[:500]."
        )
    raw_path = os.path.join(OUT_DIR, "popres_itc1_2024_raw.csv")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(r.text)
    print(f"[data] salvato {raw_path} ({len(r.text)/1024:.0f} KB)")
    return pd.read_csv(io.StringIO(r.text))

# ----------------------------------------------------------------------
# 2) Struttura (una volta, cacheata) -> codelist per decodifica
# ----------------------------------------------------------------------
def fetch_structure() -> str:
    path = os.path.join(OUT_DIR, "structure_popres1_26.xml")
    if os.path.exists(path):
        print(f"[struct] cache trovata: {path}")
        return path
    time.sleep(RATE_SLEEP)
    r = requests.get(STRUCT_URL, timeout=120)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"[struct] salvato {path} ({len(r.content)/1024:.0f} KB)")
    return path

def load_codelists(xml_path: str, lang: str = "it") -> dict:
    """Ritorna {dimension_id: {codice: etichetta}} usando il mapping
    dimensione->codelist dichiarato nel DSD (niente euristiche)."""
    ns = {
        "s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
        "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
    }
    XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
    tree = etree.parse(xml_path)
    # 1) tutte le codelist
    cls = {}
    for cl in tree.iterfind(".//s:Codelist", ns):
        codes = {}
        for code in cl.iterfind("s:Code", ns):
            names = code.findall("c:Name", ns)
            label = next((n.text for n in names if n.get(XML_LANG) == lang),
                         names[0].text if names else code.get("id"))
            codes[code.get("id")] = label
        cls[cl.get("id")] = codes
    # 2) mapping dimensione -> codelist dal DSD
    dim2cl = {}
    for el in tree.iter():
        if etree.QName(el).localname == "Dimension":
            dim_id = el.get("id")
            for ref in el.iter():
                if etree.QName(ref).localname == "Ref" and ref.get("class") == "Codelist":
                    dim2cl[dim_id] = ref.get("id")
    return {d: cls[c] for d, c in dim2cl.items() if c in cls}

# ----------------------------------------------------------------------
# 3) Tidy: decodifica + colonne utili per i marginali
# ----------------------------------------------------------------------
def tidy(df: pd.DataFrame, codelists: dict) -> pd.DataFrame:
    # nomi colonna SDMX-CSV: dimensioni in maiuscolo, valore in OBS_VALUE
    cols = {c.upper(): c for c in df.columns}
    sex_col = cols.get("SESSO") or cols.get("SEX")
    civ_col = cols.get("STATO_CIVILE") or cols.get("STATCIV2") or cols.get("MARITAL_STATUS")
    age_col = cols.get("ETA") or cols.get("ETA1") or cols.get("AGE")
    if not all([sex_col, civ_col, age_col]):
        raise RuntimeError(f"Colonne dimensione non riconosciute: {list(df.columns)}")
    # tieni solo età puntuali Y0..Y99 e Y_GE100; via TOTAL e altri aggregati
   # tieni solo età puntuali Y0..Y99 e Y_GE100; via TOTAL e altri aggregati
    n0 = len(df)
    df = df[df[age_col].astype(str).str.fullmatch(r"Y\d+|Y_GE100")].copy()
    print(f"[tidy] filtro età: {n0} -> {len(df)} righe")
    # il server ignora startPeriod/endPeriod: filtro client-side
    print("[tidy] somma per periodo:\n", df.groupby("TIME_PERIOD")["OBS_VALUE"].sum())
    df = df[df["TIME_PERIOD"] == 2024].copy()



    t = df.copy()
    for col in (sex_col, civ_col, age_col):
        mapping = codelists.get(col.upper())
        if mapping:
            t[col + "_label"] = t[col].astype(str).map(mapping)
            print(f"[tidy] {col} decodificata (codelist da DSD)")

            
    # età numerica per ordinamento/binning
    t["age_num"] = (
        t[age_col].astype(str).str.replace("Y_GE", "", regex=False)
        .str.replace("Y", "", regex=False).astype(int)
    )
    t = t.sort_values(["age_num", sex_col, civ_col]).reset_index(drop=True)
    out_path = os.path.join(OUT_DIR, "popres_itc1_2024_tidy.csv")
    t.to_csv(out_path, index=False)
    print(f"[tidy] salvato {out_path}  ({len(t)} righe)")
    return t

# ----------------------------------------------------------------------
if __name__ == "__main__":
    df = fetch_data()
    print(df.head())
    print(f"[check] righe: {len(df)}  (attese ~ 101 età × 2 sessi × 7 stati civili = 1414)")
    xml_path = fetch_structure()
    codelists = load_codelists(xml_path)
    t = tidy(df, codelists)
    # sanity check: somma = popolazione residente Piemonte all'1/1/2024 (~4.25M)
    print(f"[check] popolazione totale: {t['OBS_VALUE'].sum():,.0f}")
