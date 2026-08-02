"""Normalizzatori: da file grezzo a tabella canonica.

Ogni normalizzatore e' una funzione pura
    f(path, **opzioni) -> (DataFrame, diagnostica)

Il DataFrame ha sempre le colonne `chiave` (string) e `peso` (float64),
piu' le colonne di `dimensioni` dichiarate nel registro.
La diagnostica e' un dict di conteggi: finisce nel log di verifica, non
nel Parquet.

REGOLA: il normalizzatore non corregge mai il grezzo sul disco. Tutto
cio' che ripulisce va dichiarato in `diagnostica` e, se e' strutturale,
in `anomalie` nel registro.
"""

import pandas as pd

# ---------------------------------------------------------------- generici


def distribuzione_csv(path, sep=",", col_chiave=None, col_peso=None,
                      encoding="utf-8", dimensioni=None, decimale="."):
    """Distribuzione categorica da CSV: una riga per modalita'.

    Copre elenchi cognomi/nomi, titoli di studio, condizione professionale
    e in generale ogni tavola `modalita' -> conteggio`.
    """
    dimensioni = dimensioni or []
    d = pd.read_csv(
        path, sep=sep, encoding=encoding, decimal=decimale,
        keep_default_na=False, na_values=[], dtype=str,
    )
    d.columns = [c.strip().lower() for c in d.columns]

    if col_chiave is None:
        col_chiave = d.columns[0]
    if col_peso is None:
        col_peso = d.columns[-1]

    n_righe = len(d)
    d = d.rename(columns={col_chiave: "chiave", col_peso: "peso"})
    d["chiave"] = d["chiave"].str.strip()
    d["peso"] = pd.to_numeric(d["peso"].str.strip(), errors="coerce")

    diag = {"righe_grezze": n_righe}

    n_peso_nullo = int(d["peso"].isna().sum())
    if n_peso_nullo:
        diag["peso_non_numerico"] = n_peso_nullo
        d = d[d["peso"].notna()]

    n_vuote = int((d["chiave"] == "").sum())
    if n_vuote:
        diag["chiave_vuota_righe"] = n_vuote
        diag["chiave_vuota_peso"] = float(d.loc[d["chiave"] == "", "peso"].sum())
        d = d[d["chiave"] != ""]

    cols = ["chiave"] + dimensioni + ["peso"]
    d = d[[c for c in cols if c in d.columns]]

    prima = len(d)
    d = d.groupby(["chiave"] + dimensioni, as_index=False)["peso"].sum()
    if len(d) < prima:
        diag["chiavi_fuse"] = prima - len(d)

    d["peso"] = d["peso"].astype("float64")
    d = d.sort_values("peso", ascending=False, kind="stable").reset_index(drop=True)

    diag["modalita"] = len(d)
    diag["n_misurato"] = float(d["peso"].sum())
    return d, diag


def sdmx_csv(path, **kw):
    """Risposta SDMX-CSV di esploradati.istat.it, come arriva dal server.

    Non e' una distribuzione `chiave/peso`: ha molte dimensioni e una
    colonna OBS_VALUE. Torna il frame intatto; la diagnostica riassume cio'
    che serve a riconoscerlo (anni presenti, somma delle osservazioni,
    territorio, dataflow).
    """
    d = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[],
                    low_memory=False)
    d.columns = [c.strip() for c in d.columns]
    diag = {"righe": len(d), "colonne": len(d.columns)}

    if "DATAFLOW" in d.columns:
        fl = sorted(set(d["DATAFLOW"]))
        diag["dataflow"] = fl[0] if len(fl) == 1 else fl
    if "REF_AREA" in d.columns:
        diag["ref_area"] = sorted(set(d["REF_AREA"]))
    if "TIME_PERIOD" in d.columns:
        diag["anni"] = sorted(set(d["TIME_PERIOD"]))
    if "OBS_VALUE" in d.columns:
        v = pd.to_numeric(d["OBS_VALUE"], errors="coerce")
        diag["obs_somma"] = float(v.sum())
        n_na = int(v.isna().sum())
        if n_na:
            diag["obs_non_numerici"] = n_na
        if "TIME_PERIOD" in d.columns:
            diag["obs_per_anno"] = {
                a: float(s) for a, s in
                d.assign(_v=v).groupby("TIME_PERIOD")["_v"].sum().items()
            }
    return d, diag


def sezioni_xlsx(path, foglio=0, col_popolazione="P1", col_comune="PROCOM",
                 col_sezione="SEZ21_ID", **kw):
    """Tavola dei dati per sezione di censimento (file regionali ISTAT).

    L'unita' NON e' l'individuo ma la SEZIONE: ogni riga porta ~130
    conteggi. Torna il frame intatto; la diagnostica riassume cio' che
    serve a riconoscerlo e a confrontarlo con le altre fonti.
    """
    d = pd.read_excel(path, sheet_name=foglio)
    d.columns = [str(c).strip() for c in d.columns]
    diag = {"righe": len(d), "colonne": len(d.columns)}

    if {"P1", "P2", "P3"} <= set(d.columns):
        s = pd.to_numeric(d["P1"], errors="coerce") \
            - pd.to_numeric(d["P2"], errors="coerce") \
            - pd.to_numeric(d["P3"], errors="coerce")
        diag["scarto_P1_P2P3"] = int(s.abs().sum())

    if col_sezione in d.columns:
        diag["sezioni"] = int(d[col_sezione].nunique())
        if diag["sezioni"] != len(d):
            diag["sezioni_ripetute"] = len(d) - diag["sezioni"]
    if col_comune in d.columns:
        diag["comuni"] = int(d[col_comune].nunique())
    if col_popolazione in d.columns:
        v = pd.to_numeric(d[col_popolazione], errors="coerce")
        diag["popolazione"] = float(v.sum())
        n_vuote = int((v.fillna(0) == 0).sum())
        if n_vuote:
            diag["sezioni_senza_residenti"] = n_vuote
    for pref in ("P", "IT", "ST", "EM", "PF", "NA", "A"):
        n = sum(1 for c in d.columns
                if c.startswith(pref) and c[len(pref):].split("_")[0].isdigit())
        if n:
            diag[f"var_{pref}"] = n
    return d, diag


def tracciato_xlsx(path, foglio=0, col_chiave="NOME_CAMPO",
                   col_definizione="DEFINIZIONE", **kw):
    """Codebook: NOME_CAMPO -> DEFINIZIONE. Non e' un dato, e' il suo
    dizionario: senza, le colonne P14 e ST2_B non vogliono dire niente."""
    d = pd.read_excel(path, sheet_name=foglio)
    d.columns = [str(c).strip() for c in d.columns]
    d = d.rename(columns={col_chiave: "chiave",
                          col_definizione: "definizione"})
    d["chiave"] = d["chiave"].astype(str).str.strip()
    d["definizione"] = d["definizione"].astype(str).str.strip()
    diag = {"campi": len(d),
            "senza_definizione": int((d["definizione"] == "").sum())}
    return d[["chiave", "definizione"]], diag


REGISTRO = {
    "distribuzione_csv": distribuzione_csv,
    "sdmx_csv": sdmx_csv,
    "sezioni_xlsx": sezioni_xlsx,
    "tracciato_xlsx": tracciato_xlsx,
}


def applica(nome, path, opzioni=None, dimensioni=None):
    if nome not in REGISTRO:
        raise KeyError(
            f"normalizzatore '{nome}' non definito. Disponibili: "
            + ", ".join(sorted(REGISTRO))
        )
    kw = dict(opzioni or {})
    if dimensioni:
        kw["dimensioni"] = dimensioni
    return REGISTRO[nome](path, **kw)
