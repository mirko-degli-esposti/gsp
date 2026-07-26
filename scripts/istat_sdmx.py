"""
istat_sdmx.py — modulo generico per il web service SDMX di esploradati.istat.it

Fornisce:
    get_structure(flow_id)          scarica/cachea struttura + codelist di un dataflow
    dsd_dimensions(xml_path)        lista ordinata delle dimensioni (escluso TIME_PERIOD)
    load_codelists(xml_path)        {dimension_id: {codice: etichetta}} via DSD
    build_key(dims, spec)           KEY posizionale con wildcard per dimensioni non specificate
    fetch(flow_id, spec, ...)       dati in SDMX-CSV -> DataFrame

Note operative (lezioni apprese):
    - segmenti URL > ~260 char rifiutati dal frontend http.sys ("Bad Request - Invalid URL")
      -> preferire wildcard e filtrare a valle
    - startPeriod/endPeriod ignorati da alcune dataflow annuali -> filtrare TIME_PERIOD client-side
    - rate limit ~5 query/min -> intervallo minimo globale tra richieste
"""

import os
import time
import io
import requests
import pandas as pd
from lxml import etree

BASE = "https://esploradati.istat.it/SDMXWS/rest"
CACHE_DIR = os.path.expanduser("~/progetti/gsp/data/istat_structures")
CATALOG_CSV = os.path.expanduser("~/progetti/gsp/data/istat_catalog/catalog_dataflows.csv")
os.makedirs(CACHE_DIR, exist_ok=True)

MIN_INTERVAL = 13  # secondi tra richieste HTTP (rate limit ~5/min)
_last_request = [0.0]

NS = {
    "s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def _throttle():
    wait = MIN_INTERVAL - (time.time() - _last_request[0])
    if wait > 0:
        time.sleep(wait)
    _last_request[0] = time.time()


def flow_version(flow_id: str) -> str:
    """Versione del dataflow dal catalogo locale (default 1.0)."""
    if os.path.exists(CATALOG_CSV):
        cat = pd.read_csv(CATALOG_CSV)
        hit = cat[cat["dataflow_id"] == flow_id]
        if len(hit):
            return str(hit.iloc[0]["version"])
    return "1.f0"  # default per dataflow non in catalogo


def get_structure(flow_id: str, agency: str = "IT1") -> str:
    """Scarica (o riusa da cache) struttura + codelist del dataflow."""
    path = os.path.join(CACHE_DIR, f"{flow_id}.xml")
    if os.path.exists(path):
        return path
    ver = flow_version(flow_id)
    url = f"{BASE}/dataflow/{agency}/{flow_id}/{ver}/?detail=Full&references=Descendants"
    _throttle()
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"[struct] {flow_id}: salvato ({len(r.content)/1024:.0f} KB)")
    return path


def dsd_dimensions(xml_path: str) -> list[str]:
    """ID delle dimensioni nell'ordine del DSD (escluso TIME_PERIOD)."""
    tree = etree.parse(xml_path)
    dims = []
    for el in tree.iterfind(".//s:DimensionList/s:Dimension", NS):
        dims.append((int(el.get("position", len(dims) + 1)), el.get("id")))
    return [d for _, d in sorted(dims)]


def dim_codelist_map(xml_path: str) -> dict:
    """{dimension_id: codelist_id} dichiarato nel DSD."""
    tree = etree.parse(xml_path)
    out = {}
    for el in tree.iterfind(".//s:DimensionList/s:Dimension", NS):
        for ref in el.iter():
            if etree.QName(ref).localname == "Ref" and ref.get("class") == "Codelist":
                out[el.get("id")] = ref.get("id")
    return out


def load_codelists(xml_path: str, lang: str = "it") -> dict:
    """{dimension_id: {codice: etichetta}} usando il mapping del DSD."""
    tree = etree.parse(xml_path)
    cls = {}
    for cl in tree.iterfind(".//s:Codelist", NS):
        codes = {}
        for code in cl.iterfind("s:Code", NS):
            names = code.findall("c:Name", NS)
            label = next((n.text for n in names if n.get(XML_LANG) == lang),
                         names[0].text if names else code.get("id"))
            codes[code.get("id")] = label
        cls[cl.get("id")] = codes
    d2c = dim_codelist_map(xml_path)
    return {d: cls[c] for d, c in d2c.items() if c in cls}


def build_key(dims: list[str], spec: dict) -> str:
    """KEY posizionale: dimensioni non in spec -> wildcard (posizione vuota).
    spec: {dim_id: 'A'} o {dim_id: ['1','2']}."""
    parts = []
    for d in dims:
        v = spec.get(d, "")
        if isinstance(v, (list, tuple)):
            v = "+".join(str(x) for x in v)
        parts.append(str(v))
    key = ".".join(parts)
    for seg in key.split("/"):
        if len(seg) > 250:
            raise ValueError(f"Segmento KEY troppo lungo ({len(seg)} char): "
                             "usare wildcard e filtrare a valle.")
    return key


def fetch(flow_id: str, spec: dict, agency: str = "IT1",
          start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Scarica i dati in SDMX-CSV. spec mappa dimension_id -> valore/i."""
    xml_path = get_structure(flow_id, agency)
    dims = dsd_dimensions(xml_path)
    unknown = set(spec) - set(dims)
    if unknown:
        raise ValueError(f"{flow_id}: dimensioni sconosciute {unknown}; "
                         f"disponibili: {dims}")
    key = build_key(dims, spec)
    ver = flow_version(flow_id)
    url = f"{BASE}/data/{agency},{flow_id},{ver}/{key}/ALL/?detail=full" \
          "&dimensionAtObservation=TIME_PERIOD"
    if start:
        url += f"&startPeriod={start}"
    if end:
        url += f"&endPeriod={end}"
    _throttle()
    r = requests.get(url, headers={"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"},
                     timeout=300)
    if r.status_code == 404:
        print(f"[fetch] {flow_id}: nessun dato per key={key} (404)")
        return pd.DataFrame()
    r.raise_for_status()
    if "csv" not in r.headers.get("Content-Type", "") \
            and not r.text.lstrip().startswith(("DATAFLOW", "STRUCTURE")):
        raise RuntimeError(f"{flow_id}: risposta non CSV; inizio: {r.text[:300]!r}")
    df = pd.read_csv(io.StringIO(r.text))
    print(f"[fetch] {flow_id}: {len(df)} righe, key={key}")
    return df


def decode(df: pd.DataFrame, xml_path: str, lang: str = "it") -> pd.DataFrame:
    """Aggiunge colonne <DIM>_label per ogni dimensione decodificabile."""
    codelists = load_codelists(xml_path, lang)
    t = df.copy()
    for dim, mapping in codelists.items():
        if dim in t.columns:
            t[dim + "_label"] = t[dim].astype(str).map(mapping)
    return t
