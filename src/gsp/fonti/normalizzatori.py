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


REGISTRO = {
    "distribuzione_csv": distribuzione_csv,
    "sdmx_csv": sdmx_csv,
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
