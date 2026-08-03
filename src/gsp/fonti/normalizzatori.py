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


def avq_microdati(path, col_peso="COEFIN", col_regione="REGMf",
                  col_eta="ETAMi", col_sesso="SESSO", **kw):
    """Microdati campionari AVQ (mIcro.STAT), TSV a centinaia di colonne.

    L'unita' e' l'individuo CAMPIONARIO: ogni record porta COEFIN, il
    coefficiente di riporto all'universo. Due misure entrambe corrette
    della stessa fonte - i record e la somma dei pesi - e il registro deve
    dire quale sta registrando.

    Legge solo le colonne di struttura: il file intero e' troppo grande e
    le variabili di contenuto cambiano da un'annata all'altra.
    """
    intestazione = pd.read_csv(path, sep="\t", nrows=0)
    colonne = [str(c).strip() for c in intestazione.columns]
    volute = [c for c in (col_peso, col_regione, col_eta, col_sesso)
              if c in colonne]
    d = pd.read_csv(path, sep="\t", usecols=volute, low_memory=False)

    diag = {"righe": len(d), "colonne": len(colonne)}
    if col_regione in d.columns:
        diag["regioni"] = int(d[col_regione].nunique())
    if col_eta in d.columns:
        e = pd.to_numeric(d[col_eta], errors="coerce")
        diag["eta_min"] = float(e.min())
        diag["eta_max"] = float(e.max())
    if col_peso in d.columns:
        w = pd.to_numeric(d[col_peso], errors="coerce").fillna(0.0)
        diag["somma_pesi"] = float(w.sum())
        diag["peso_min"] = float(w[w > 0].min()) if (w > 0).any() else None
        diag["peso_max"] = float(w.max())
        # numerosita' efficace di Kish: quanti record "veri" valgono i
        # pesi. E' il numero da citare accanto a qualunque statistica AVQ,
        # perche' la dimensione del pool da sola la sovrastima.
        s2 = float((w ** 2).sum())
        diag["n_eff_kish"] = round(float(w.sum()) ** 2 / s2, 1) if s2 else None
    return d, diag


def tracciato_csv(path, sep=",", col_chiave="variabile",
                  col_definizione="descrizione", encoding="utf-8", **kw):
    """Codebook in CSV: variabile -> descrizione.

    Gemello di tracciato_xlsx: stessa forma canonica, sorgente diversa.
    Come quello, non produce `peso`: non e' una distribuzione ma un
    dizionario, e l'impronta lo tratta di conseguenza.
    """
    d = pd.read_csv(path, sep=sep, encoding=encoding,
                    keep_default_na=False, na_values=[], dtype=str)
    d.columns = [str(c).strip().lower() for c in d.columns]
    ck, cd = col_chiave.lower(), col_definizione.lower()
    mancanti = [c for c in (ck, cd) if c not in d.columns]
    if mancanti:
        raise KeyError(
            f"colonne {mancanti} assenti in {path}; presenti: "
            + ", ".join(d.columns))
    d = d.rename(columns={ck: "chiave", cd: "definizione"})
    d["chiave"] = d["chiave"].str.strip()
    d["definizione"] = d["definizione"].str.strip()

    diag = {"campi": len(d),
            "senza_definizione": int((d["definizione"] == "").sum())}
    n_vuote = int((d["chiave"] == "").sum())
    if n_vuote:
        diag["chiave_vuota"] = n_vuote
        d = d[d["chiave"] != ""]
    dupl = int(d["chiave"].duplicated().sum())
    if dupl:
        diag["chiavi_ripetute"] = dupl
    return d[["chiave", "definizione"]].reset_index(drop=True), diag


def matrice_csv(path, sep=None, encoding="utf-8", col_chiave=None,
                dimensione="zona", etichette_residuo=None, **kw):
    """Matrice larga: prima colonna la modalita', le altre le unita'
    territoriali, le celle i conteggi.

    Scioglie in formato lungo `chiave, <dimensione>, peso`. E' il primo
    caso in cui il campo `dimensioni` del registro serve davvero.

    NON riconcilia i nomi: la traduzione delle denominazioni comunali in
    codici ISTAT vive gia' in gsp.common.COMUNI[...]["opendata_paese"]
    (mappa_unita, alias_paese) ed e' referenziata con `parametri_da`.
    Qui si misura soltanto.

    `sep=None` con engine python lascia sniffare il separatore, come fa
    load_reggio.
    """
    etichette_residuo = etichette_residuo or []
    d = pd.read_csv(path, sep=sep, engine="python", encoding=encoding)
    if col_chiave is None:
        col_chiave = d.columns[0]
    unita = [c for c in d.columns if c != col_chiave]

    lungo = d.melt(id_vars=[col_chiave], value_vars=unita,
                   var_name=dimensione, value_name="peso")
    lungo = lungo.rename(columns={col_chiave: "chiave"})
    lungo["chiave"] = lungo["chiave"].astype(str).str.strip()
    lungo[dimensione] = lungo[dimensione].astype(str).str.strip()
    lungo["peso"] = pd.to_numeric(lungo["peso"], errors="coerce")

    diag = {"modalita": int(d[col_chiave].nunique()),
            f"{dimensione}_n": len(unita),
            f"{dimensione}_nomi": [str(c).strip() for c in unita]}

    n_na = int(lungo["peso"].isna().sum())
    if n_na:
        diag["celle_non_numeriche"] = n_na
        lungo = lungo[lungo["peso"].notna()]
    vuote = int((lungo["chiave"] == "").sum())
    if vuote:
        diag["chiave_vuota"] = vuote
        lungo = lungo[lungo["chiave"] != ""]

    lungo["peso"] = lungo["peso"].astype("float64")
    tot = float(lungo["peso"].sum())
    diag["n_misurato"] = tot

    # quanto della massa sta nella modalita' residuale: dice quanta
    # informazione la fonte porta davvero, ed e' il numero che l'IPF
    # tratta come complemento invece che come paese.
    if etichette_residuo:
        res = {str(x).strip().lower() for x in etichette_residuo}
        m = lungo["chiave"].str.lower().isin(res)
        if m.any():
            diag["residuo_peso"] = float(lungo.loc[m, "peso"].sum())
            diag["residuo_quota"] = round(diag["residuo_peso"] / tot, 4) if tot else None

    lungo = lungo.sort_values("peso", ascending=False,
                              kind="stable").reset_index(drop=True)
    return lungo[["chiave", dimensione, "peso"]], diag


def excel_aree_sesso(path, riga_aree=1, riga_sessi=2, prima_riga_dati=3,
                     dimensione="zona", colonne_sesso=("M", "F"),
                     escludi_aree=("AREE TERRITORIALI", "TOTALI"),
                     escludi_righe=("TOTALE",), **kw):
    """Foglio Excel formattato per la stampa, a doppia intestazione.

        riga 1   AREE TERRITORIALI:  CENTRO URBANO | RAVENNA SUD | ...
        riga 2   NAZIONALITA':       M  F  T       | M  F  T     | ...
        riga 3+  AFGANISTAN          18  2  20     | 24  4  28   | ...

    Le celle unite di Excel diventano NaN in pandas: il nome dell'area
    compare solo sopra la prima delle tre colonne, e si propaga in avanti.

    Si sommano M e F e si SCARTA T, come fa load_ravenna: la colonna dei
    totali e' ridondante e in alcune celle e' l'unico valore presente
    (formattazione, non informazione). Si escludono l'area 'T O T A L I'
    e la riga 'TOTALE', che sono aggregati: contarli raddoppia.

    NON riconcilia le denominazioni proprie ('S.P.VINCOLI', 'ARABIA'):
    quelle vivono in gsp.common e sono referenziate con `parametri_da`.
    """
    d = pd.read_excel(path, header=None)
    norm = lambda x: str(x).strip().upper().replace(" ", "")  # noqa: E731
    fuori_aree = {norm(x) for x in escludi_aree}
    fuori_righe = {norm(x) for x in escludi_righe}

    # riga delle aree: propaga il nome sulle colonne unite
    aree, corrente = {}, None
    for i, v in d.iloc[riga_aree].items():
        if not pd.isna(v) and str(v).strip():
            corrente = str(v).strip()
        if corrente and norm(corrente) not in fuori_aree:
            aree[i] = corrente

    sessi = {i: str(v).strip().upper()
             for i, v in d.iloc[riga_sessi].items() if not pd.isna(v)}
    volute = {s.upper() for s in colonne_sesso}

    righe = []
    for _, r in d.iloc[prima_riga_dati:].iterrows():
        et = str(r.iloc[0]).strip()
        if not et or et.lower() == "nan" or norm(et) in fuori_righe:
            continue
        for i, area in aree.items():
            if sessi.get(i) not in volute:
                continue
            v = pd.to_numeric(r.iloc[i], errors="coerce")
            if pd.isna(v):
                continue                    # cella unita': zero, non dato
            righe.append((et, area, sessi[i], float(v)))

    lungo = pd.DataFrame(righe, columns=["chiave", dimensione, "sesso",
                                         "peso"])
    diag = {"modalita": int(lungo["chiave"].nunique()),
            f"{dimensione}_n": int(lungo[dimensione].nunique()),
            f"{dimensione}_nomi": sorted(set(aree.values())),
            "sessi": sorted(volute),
            "celle": len(lungo),
            "n_misurato": float(lungo["peso"].sum())}
    for s in sorted(volute):
        diag[f"n_{s}"] = float(lungo.loc[lungo["sesso"] == s, "peso"].sum())

    lungo = lungo.sort_values("peso", ascending=False,
                              kind="stable").reset_index(drop=True)
    return lungo, diag


def formato_lungo(path, col_chiave="STATO", col_dimensione="QUARTIERE",
                  dimensione="zona", colonne_valore=("F", "M"),
                  nome_valore="sesso", escludi_dimensione=(),
                  etichette_residuo=(), sep=",", encoding="utf-8", **kw):
    """Tabella gia' in formato lungo, con il sesso su colonne affiancate.

        QUARTIERE   STATO     F   M   TOTALE
        BAGNOLO     ROMANIA  10   9       19
        BAGNOLO     altro    26  15       41

    Scioglie le colonne di `colonne_valore` in righe, scartando la
    colonna dei totali che e' ridondante. Legge xlsx (calamine, con
    openpyxl come ripiego) o csv, dall'estensione.

    NON aggrega le unita' territoriali: la mappa 41 -> 21 quartieri vive
    in gsp.common ed e' referenziata con `parametri_da`. Qui si misura la
    fonte come sta sul disco.
    """
    if str(path).lower().endswith((".xlsx", ".xls")):
        try:
            d = pd.read_excel(path, header=0, engine="calamine")
        except (ImportError, ValueError):
            # xlsx senza sharedStrings: openpyxl solleva KeyError
            d = pd.read_excel(path, header=0)
    else:
        d = pd.read_csv(path, sep=sep, encoding=encoding)
    d.columns = [str(c).strip().upper() for c in d.columns]

    ck, cd = col_chiave.upper(), col_dimensione.upper()
    valori = [c.upper() for c in colonne_valore]
    attese = {ck, cd, *valori}
    mancanti = sorted(attese - set(d.columns))
    if mancanti:
        raise KeyError(f"colonne {mancanti} assenti in {path}; "
                       f"presenti: {list(d.columns)}")

    d[ck] = d[ck].astype(str).str.strip()
    d[cd] = d[cd].astype(str).str.strip()

    diag = {"righe_grezze": len(d)}
    fuori = {str(x).strip().lower() for x in escludi_dimensione}
    if fuori:
        m = d[cd].str.lower().isin(fuori)
        if m.any():
            diag["unita_escluse"] = sorted(set(d.loc[m, cd]))
            diag["unita_escluse_peso"] = float(
                pd.to_numeric(d.loc[m, valori].stack(), errors="coerce").sum())
            d = d[~m]

    lungo = d.melt(id_vars=[ck, cd], value_vars=valori,
                   var_name=nome_valore, value_name="peso")
    lungo = lungo.rename(columns={ck: "chiave", cd: dimensione})
    lungo["peso"] = pd.to_numeric(lungo["peso"], errors="coerce").fillna(0.0)
    lungo = lungo[lungo["peso"] != 0]

    tot = float(lungo["peso"].sum())
    diag.update({"modalita": int(lungo["chiave"].nunique()),
                 f"{dimensione}_n": int(lungo[dimensione].nunique()),
                 nome_valore: sorted(set(lungo[nome_valore])),
                 "n_misurato": tot})
    for v in sorted(set(lungo[nome_valore])):
        diag[f"n_{v}"] = float(lungo.loc[lungo[nome_valore] == v, "peso"].sum())

    if etichette_residuo:
        res = {str(x).strip().lower() for x in etichette_residuo}
        m = lungo["chiave"].str.lower().isin(res)
        if m.any():
            diag["residuo_peso"] = float(lungo.loc[m, "peso"].sum())
            diag["residuo_quota"] = round(diag["residuo_peso"] / tot, 4) if tot else None

    lungo = lungo.sort_values("peso", ascending=False,
                              kind="stable").reset_index(drop=True)
    return lungo[["chiave", dimensione, nome_valore, "peso"]], diag


def tabella_parquet(path, col_chiave=None, col_dimensione=None,
                    dimensione="zona", col_peso=None, col_anno=None,
                    solo_ultimo_anno=False, dimensioni=None,
                    escludi_dimensione=(), etichette_residuo=(), **kw):
    """Tabella gia' in formato lungo, salvata in Parquet.

    E' il formato migliore fra quelli incontrati: colonne dichiarate,
    tipi conservati, nessuna formattazione da sciogliere. Con `col_anno`
    e `solo_ultimo_anno` si misura l'annata che la pipeline usa davvero
    invece di tutta la serie storica.
    """
    d = pd.read_parquet(path)
    d.columns = [str(c).strip() for c in d.columns]
    diag = {"righe_grezze": len(d), "colonne": len(d.columns)}

    if col_anno and col_anno in d.columns:
        anni = pd.to_datetime(d[col_anno], errors="coerce").dt.year
        diag["anni_n"] = int(anni.nunique())
        diag["anno_min"] = int(anni.min())
        diag["anno_max"] = int(anni.max())
        if solo_ultimo_anno:
            d = d[anni == anni.max()].copy()
            diag["anno_usato"] = int(anni.max())
            diag["righe_anno"] = len(d)

    ck = col_chiave or d.columns[0]
    cd = col_dimensione
    cp = col_peso or d.columns[-1]

    fuori = {str(x).strip().lower() for x in escludi_dimensione}
    if cd and fuori:
        m = d[cd].astype(str).str.strip().str.lower().isin(fuori)
        if m.any():
            diag["unita_escluse"] = sorted(set(d.loc[m, cd].astype(str)))
            diag["unita_escluse_peso"] = float(
                pd.to_numeric(d.loc[m, cp], errors="coerce").sum())
            d = d[~m]

    out = d.rename(columns={ck: "chiave", cp: "peso"})
    if cd:
        out = out.rename(columns={cd: dimensione})
    out["peso"] = pd.to_numeric(out["peso"], errors="coerce").fillna(0.0)

    tot = float(out["peso"].sum())
    diag.update({"modalita": int(out["chiave"].nunique()),
                 "n_misurato": tot})
    if cd:
        diag[f"{dimensione}_n"] = int(out[dimensione].nunique())
    for c in (dimensioni or []):
        if c in out.columns and c != dimensione:
            diag[f"{c}_valori"] = sorted(set(out[c].astype(str)))[:20]

    if etichette_residuo:
        res = {str(x).strip().lower() for x in etichette_residuo}
        m = out["chiave"].astype(str).str.lower().isin(res)
        diag["residuo_peso"] = float(out.loc[m, "peso"].sum())
        diag["residuo_quota"] = round(diag["residuo_peso"] / tot, 4) if tot else None

    cols = ["chiave"] + ([dimensione] if cd else []) \
        + [c for c in (dimensioni or []) if c in out.columns and c != dimensione] \
        + ["peso"]
    out = out[cols].sort_values("peso", ascending=False,
                                kind="stable").reset_index(drop=True)
    return out, diag


def microdati_csv(path, sep=None, encoding="utf-8", col_geo=None,
                  col_chiave=None, conteggi=(), **kw):
    """Microdati individuali: una riga per persona, non conteggi.

    L'unita' e' l'individuo vero e n_misurato sono i RECORD, non una
    somma di pesi: a differenza di AVQ questi non sono campionari ma
    l'anagrafe intera. Torna il frame intatto e riassume la struttura.

    `conteggi` elenca le colonne di cui riportare il numero di modalita'
    distinte; `col_geo` quella territoriale.
    """
    d = pd.read_csv(path, sep=sep, engine="python" if sep is None else "c",
                    encoding=encoding, low_memory=False)
    d.columns = [str(c).strip() for c in d.columns]
    diag = {"righe": len(d), "colonne": len(d.columns),
            "campi": list(d.columns)}

    for c in conteggi:
        if c in d.columns:
            diag[f"{c}_n"] = int(d[c].nunique())
    if col_geo and col_geo in d.columns:
        diag["geo_n"] = int(d[col_geo].nunique())
    if col_chiave and col_chiave in d.columns:
        diag["modalita"] = int(d[col_chiave].nunique())

    # controllo di plausibilita' sui campi numerici: un'eta' negativa o
    # un conteggio a zero sono difetti della fonte, non del lettore.
    for c in d.columns:
        v = pd.to_numeric(d[c], errors="coerce")
        if v.notna().mean() < 0.9:
            continue
        mn, mx = float(v.min()), float(v.max())
        diag[f"{c}_min"], diag[f"{c}_max"] = mn, mx
        if mn < 0:
            diag[f"{c}_negativi"] = int((v < 0).sum())
    diag["n_misurato"] = float(len(d))
    return d, diag


def codebook_csv(path, sep=None, encoding="latin-1", col_campo="CAMPO",
                 col_descrizione="DESCRIZIONE CAMPO", col_codice="CODICE",
                 col_etichetta="DESCRIZIONE CODICE",
                 segnaposto=("numerico", "non applicabile", "n.a.", "-"),
                 **kw):
    """Codebook a DUE livelli: campo -> codice -> etichetta.

    Diverso da tracciato_csv, che e' a un livello (variabile ->
    descrizione). Alcuni campi hanno decine di codici (Cittad: 225,
    Relpar: 30) e altri nessuno.

    I campi senza codifica non hanno la cella vuota: hanno una riga
    SEGNAPOSTO con codice 0 ed etichetta 'numerico' o 'Non applicabile'.
    Contarla come un codice vero direbbe che ETA ha una codifica, che e'
    falso — ed e' la differenza fra sapere che un valore anomalo e' un
    codice convenzionale o un dato sporco.
    """
    d = pd.read_csv(path, sep=sep, engine="python" if sep is None else "c",
                    encoding=encoding, keep_default_na=False, na_values=[],
                    dtype=str)
    d.columns = [str(c).strip() for c in d.columns]
    for c in (col_campo, col_descrizione, col_codice, col_etichetta):
        if c not in d.columns:
            raise KeyError(f"colonna '{c}' assente in {path}; "
                           f"presenti: {list(d.columns)}")
    out = d.rename(columns={col_campo: "chiave",
                            col_descrizione: "descrizione",
                            col_codice: "codice",
                            col_etichetta: "etichetta"})
    for c in ("chiave", "descrizione", "codice", "etichetta"):
        out[c] = out[c].str.strip()

    segna = {str(x).strip().lower() for x in segnaposto}
    e = out["etichetta"].str.lower()
    out["segnaposto"] = (out["codice"] == "") | e.isin(segna) | \
        e.str.startswith("numero progressivo")

    veri = out[~out["segnaposto"]]
    per_campo = veri.groupby("chiave").size()
    tutti = sorted(set(out["chiave"]))
    diag = {"campi": len(tutti),
            "righe": len(out),
            "codici_per_campo": {k: int(per_campo.get(k, 0)) for k in tutti},
            "campi_senza_codici": [k for k in tutti if per_campo.get(k, 0) == 0],
            "codici_veri": int(len(veri)),
            "modalita": len(tutti),
            "n_misurato": float(len(out))}
    return out[["chiave", "descrizione", "codice", "etichetta"]], diag


REGISTRO = {
    "distribuzione_csv": distribuzione_csv,
    "matrice_csv": matrice_csv,
    "formato_lungo": formato_lungo,
    "tabella_parquet": tabella_parquet,
    "excel_aree_sesso": excel_aree_sesso,
    "microdati_csv": microdati_csv,
    "codebook_csv": codebook_csv,
    "sdmx_csv": sdmx_csv,
    "sezioni_xlsx": sezioni_xlsx,
    "tracciato_xlsx": tracciato_xlsx,
    "tracciato_csv": tracciato_csv,
    "avq_microdati": avq_microdati,
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
