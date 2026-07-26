"""
fetch_comune.py — scarica la rosa dei fondamentali ISTAT per un comune.

Uso (staged, come da prassi):
    python fetch_comune.py 017029 --explore    # solo strutture: dimensioni e codelist per tavola
    python fetch_comune.py 017029              # fetch dei dati (dopo aver validato l'explore)
    python fetch_comune.py 017029 --only cens_istruzione_eta

Codici comune = ITTER107 (Brescia 017029, Torino 001272).
Output in ~/progetti/gsp/data/comuni/<codice>/ : un CSV raw + uno decodificato per tavola.
"""

import os
import sys
import pandas as pd
import istat_sdmx as sdmx

# ----------------------------------------------------------------------
# Rosa dei fondamentali.
# spec: vincoli espliciti per dimensione; tutto il resto in wildcard
# (i totali/aggregati si filtrano a valle, nel constraint builder).
# La dimensione territorio NON va in spec: viene individuata e riempita
# automaticamente (è quella la cui codelist contiene il codice comune).
# ----------------------------------------------------------------------
CORE = {
    # spine anagrafica (singolo anno d'età, conteggi esatti)
    "anag_sesso_eta_statociv": {
        "flow": "22_289_DF_DCIS_POPRES1_26",
        "spec": {"FREQ": "A", "DATA_TYPE": "JAN",
                 "SEX": ["1", "2"],
                 "MARITAL_STATUS": ["1", "2", "3", "4", "15", "16", "17"]},
    },
    # strato censuario DCSS (comuni)
    "cens_sesso_eta_cittadinanza": {"flow": "DF_DCSS_POP_DEMCITMIG_SETA_1", "spec": {}},
    "cens_istruzione_eta":         {"flow": "DF_DCSS_ISTR_LAV_PEN_2_TV_1", "spec": {}},
    "cens_istruzione_cittadinanza": {"flow": "DF_DCSS_ISTR_LAV_PEN_2_TV_2", "spec": {}},
    "cens_condprof_eta":           {"flow": "DF_DCSS_ISTR_LAV_PEN_2_TV_3", "spec": {}},
    "cens_condprof_cittadinanza":  {"flow": "DF_DCSS_ISTR_LAV_PEN_2_TV_4", "spec": {}},
    "cens_stranieri_paesi":        {"flow": "DF_DCSS_POP_DEMCITMIG_TV_3", "spec": {}},
}


def find_territory_dim(xml_path: str, comune: str):
    """Trova la dimensione la cui codelist contiene il codice comune."""
    codelists = sdmx.load_codelists(xml_path)
    for dim, codes in codelists.items():
        if comune in codes:
            return dim, codes[comune]
    return None, None


def explore(comune: str, tables: dict):
    for name, cfg in tables.items():
        flow = cfg["flow"]
        try:
            xml_path = sdmx.get_structure(flow)
        except Exception as e:
            print(f"\n=== {name} [{flow}] ===\n  ERRORE struttura: {e}")
            continue
        dims = sdmx.dsd_dimensions(xml_path)
        codelists = sdmx.load_codelists(xml_path)
        terr_dim, terr_label = find_territory_dim(xml_path, comune)
        print(f"\n=== {name} [{flow}] ===")
        for d in dims:
            n = len(codelists.get(d, {}))
            mark = "  <-- TERRITORIO (comune presente)" if d == terr_dim else ""
            ex = list(codelists.get(d, {}).items())[:4]
            print(f"  {d:<22} codelist:{n:>6} codici  es. {ex}{mark}")
        if terr_dim is None:
            print(f"  !! codice {comune} NON presente in nessuna codelist "
                  "(tavola non comunale o codifica territorio diversa)")
        else:
            print(f"  territorio: {terr_dim} = {comune} ({terr_label})")


def fetch_all(comune: str, tables: dict):
    out_dir = os.path.expanduser(f"~/progetti/gsp/data/comuni/{comune}")
    os.makedirs(out_dir, exist_ok=True)
    summary = []
    for name, cfg in tables.items():
        flow = cfg["flow"]
        xml_path = sdmx.get_structure(flow)
        terr_dim, terr_label = find_territory_dim(xml_path, comune)
        if terr_dim is None:
            print(f"[skip] {name}: comune {comune} non in codelist")
            summary.append((name, "SKIP", 0))
            continue
        spec = dict(cfg["spec"])
        spec[terr_dim] = comune
        try:
            df = sdmx.fetch(flow, spec)
        except Exception as e:
            print(f"[errore] {name}: {e}")
            summary.append((name, "ERR", 0))
            continue
        if df.empty:
            summary.append((name, "VUOTA", 0))
            continue
        df.to_csv(os.path.join(out_dir, f"{name}_raw.csv"), index=False)
        dec = sdmx.decode(df, xml_path)
        dec.to_csv(os.path.join(out_dir, f"{name}_decoded.csv"), index=False)
        periods = sorted(dec["TIME_PERIOD"].unique()) if "TIME_PERIOD" in dec else []
        summary.append((name, "OK", len(dec)))
        print(f"[ok] {name}: {len(dec)} righe, periodi {periods}")
    print(f"\n--- riepilogo ({out_dir}) ---")
    for name, status, n in summary:
        print(f"  {name:<30} {status:<6} {n:>7} righe")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("Uso: python fetch_comune.py <codice_comune> [--explore] [--only <tavola>]")
    comune = args[0]
    tables = CORE
    if "--only" in args:
        key = args[args.index("--only") + 1]
        tables = {key: CORE[key]}
    if "--explore" in args:
        explore(comune, tables)
    else:
        fetch_all(comune, tables)
