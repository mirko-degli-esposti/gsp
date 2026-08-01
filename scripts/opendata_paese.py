"""
opendata_paese.py — condizionale geografico del paese di cittadinanza.

Il censimento ISTAT pubblica la cittadinanza di dettaglio solo a livello
COMUNALE: la pipeline assume percio' (4) paese ⊥ geografia | (area, sesso).
Diversi comuni pubblicano pero' la stessa informazione a livello
sub-comunale, con risoluzione e ricchezza molto diverse:

    tier 0   comune      solo censimento           P(paese | sesso)
    tier 1   quartiere   tabella aggregata         Brescia, 33 file
    tier 2   zona        tabella con sesso         Bologna, 18 zone
    tier 3   sezione     microdati individuali     Parma, 1.357 sezioni

Le fonti non sono alternative al censimento ma COMPLEMENTARI: il censimento
porta i ~150 paesi, i livelli corretti e il sesso; le fonti locali portano
la geografia. Si combinano con IPF su due margini:

    A   sum_geo  T(paese, sesso, geo)   = censimento comunale (paese, sesso)
    B   sum_{paese in g} T(·, ·, geo)   = fonte locale (gruppo, geo [, sesso])

dove 'g' e' un gruppo di paesi definito dalla fonte. Per Brescia i file
nominano ~19 paesi piu' 'ALTRE CITTADINANZE', e il gruppo residuale e' il
complemento dei paesi nominati IN QUEL QUARTIERE: cambia da file a file, e
l'IPF lo gestisce senza inventare informazione.

Con la fonte assente, il margine B si riduce alla replica di A su ogni zona
e il risultato coincide esattamente con il comportamento attuale (tier 0).

Assunzioni:
    - le fonti comunali sono ANAGRAFICHE e di data diversa dal censimento
      (Bologna 1/1/2024, Parma 1/1/2025, Brescia non dichiarata). Si usano
      solo come FORMA CONDIZIONALE: i livelli restano quelli censuari,
      coerenti con il MaxEnt. Il rapporto anagrafe/censimento misurato e'
      ~1.05, stabile, il che rende il condizionale utilizzabile.
    - il sesso, dove la fonte non lo distingue (Brescia), viene ricostruito
      dall'IPF a partire dal margine comunale.
    - l'eta' NON entra nel condizionale, nemmeno dove disponibile (Parma):
      resta riservata alla validazione esterna.

Uso:
    python opendata_paese.py --check                  # tutti i comuni
    python opendata_paese.py --check 034027
    python opendata_paese.py --dump 037006 --top 15   # tabella risultante
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd

import gsp_common as G

OPENDATA = os.path.join(G.DATA, "opendata")
ANNO_CENS = 2023
RESIDUALE = "__altro__"


# ----------------------------------------------------------------------
# Caricatori: ogni fonte -> formato comune (geo, sesso, paese, n)
# ----------------------------------------------------------------------

def _lungo(righe: list[dict]) -> pd.DataFrame:
    d = pd.DataFrame(righe, columns=["geo", "sesso", "paese", "n"])
    return d[d["n"] > 0].reset_index(drop=True)


def load_brescia(comune: str, cfg: dict, rif: dict) -> pd.DataFrame:
    """Un CSV per quartiere, colonne (Cittadinanze, Num), senza sesso.

    Il nome del file identifica il quartiere; alcuni non coincidono con la
    denominazione ISTAT e stanno in cfg['override_nome'].
    """
    nomi = G.zona_nomi(comune, cfg["geo_liv"])
    per_nome = {G.norm_nome(v): k for k, v in nomi.items()}
    override = cfg.get("override_nome", {})
    files = sorted(glob.glob(os.path.join(
        OPENDATA, comune, cfg.get("dir", "cittadinanza"), "*.csv")))
    if not files:
        raise FileNotFoundError(f"nessun CSV in {OPENDATA}/{comune}/"
                                f"{cfg.get('dir', 'cittadinanza')}")
    righe, orfani = [], []
    for f in files:
        stem = os.path.splitext(os.path.basename(f))[0]
        geo = override.get(stem) or per_nome.get(G.norm_nome(stem))
        if geo is None:
            orfani.append(stem)
            continue
        t = pd.read_csv(f)
        t.columns = ["etichetta", "n"]
        t["n"] = pd.to_numeric(t["n"], errors="coerce").fillna(0)
        for r in t.itertuples():
            p = G.risolvi_paese(r.etichetta, rif)
            if G.norm_nome(r.etichetta) == "italia":
                continue
            righe.append({"geo": geo, "sesso": None,
                          "paese": p or RESIDUALE, "n": float(r.n)})
    if orfani:
        raise ValueError(f"file senza quartiere: {orfani}")
    return _lungo(righe)


def load_bologna(comune: str, cfg: dict, rif: dict) -> pd.DataFrame:
    """Parquet con (anno, quartiere, zona, stato_cittadinanza, sesso,
    residenti). Si prende l'anno piu' recente."""
    f = sorted(glob.glob(os.path.join(OPENDATA, comune, "*.parquet")))
    if not f:
        raise FileNotFoundError(f"nessun parquet in {OPENDATA}/{comune}")
    b = pd.read_parquet(f[0])
    b["y"] = pd.to_datetime(b["anno"]).dt.year
    b = b[b["y"] == b["y"].max()].copy()

    nomi = G.zona_nomi(comune, cfg["geo_liv"])
    per_nome = {G.norm_nome(v): k for k, v in nomi.items()}
    b["geo"] = b["zona"].map(lambda z: per_nome.get(G.norm_nome(z)))
    # 'Senza fissa dimora' non e' una zona: cade nel residuale territoriale
    persi = b[b["geo"].isna()]["zona"].unique()
    if len(persi):
        print(f"[bologna] zone non agganciate (escluse): {list(persi)}")
    b = b[b["geo"].notna()]

    b["sesso"] = b["sesso"].map({"Maschi": "M", "Femmine": "F"})
    b["paese"] = b["stato_cittadinanza"].map(
        lambda x: G.risolvi_paese(x, rif) or RESIDUALE)
    g = b.groupby(["geo", "sesso", "paese"])["residenti"].sum().reset_index()
    return _lungo(g.rename(columns={"residenti": "n"}).to_dict("records"))


def load_parma(comune: str, cfg: dict, rif: dict) -> pd.DataFrame:
    """Microdati individuali: una riga per residente, con SEZ21 locale.

    SEZ21_ID = '34027' + SEZ21 su sette cifre. L'aggancio copre il 99.9%
    degli individui; le sezioni residue sono presenti in anagrafe ma senza
    popolazione censuaria pubblicata.
    """
    fd = sorted(glob.glob(os.path.join(OPENDATA, comune,
                                       "Popolazione_residente*.csv")))
    fc = sorted(glob.glob(os.path.join(OPENDATA, comune,
                                       "Descrizione_codifica*.csv")))
    if not fd or not fc:
        raise FileNotFoundError(f"microdati o codifica assenti in "
                                f"{OPENDATA}/{comune}")
    p = pd.read_csv(fd[0], sep=None, engine="python")
    c = pd.read_csv(fc[0], encoding="latin-1", sep=None, engine="python")

    sel = c["CAMPO"].astype(str).str.strip().str.lower() == "cittad"
    dec = dict(zip(pd.to_numeric(c.loc[sel, "CODICE"], errors="coerce"),
                   c.loc[sel, "DESCRIZIONE CODICE"]))

    p = p[p["Cittad"] != 100].copy()                 # solo stranieri
    pref = str(G.procom(comune))
    p["geo"] = pref + p["SEZ21"].astype(int).astype(str).str.zfill(7)
    p["sesso"] = p["Sesso"].map({1: "M", 2: "F"})
    p["paese"] = p["Cittad"].map(dec).map(
        lambda x: G.risolvi_paese(x, rif) or RESIDUALE)

    # sezioni anagrafiche assenti dal censimento -> residuale territoriale
    sez = pd.read_csv(G.path_sezioni(comune), low_memory=False)
    vere = set(sez["SEZ21_ID"].astype("Int64").astype(str))
    fuori = ~p["geo"].isin(vere)
    if fuori.any():
        print(f"[parma] {int(fuori.sum())} individui in {p.loc[fuori,'geo'].nunique()} "
              f"sezioni assenti dal censimento: esclusi")
        p = p[~fuori]

    g = p.groupby(["geo", "sesso", "paese"]).size().reset_index(name="n")
    return _lungo(g.to_dict("records"))


def load_ravenna(comune: str, cfg: dict, rif: dict) -> pd.DataFrame:
    """XLS a doppia intestazione: riga 1 = aree, riga 2 = M/F/T.
 
    Layout: colonna 0 = nazionalita', poi per ogni area tre colonne
    contigue (M, F, T). Si usano M e F, si scarta T. L'ultima area e'
    'T O T A L I' e va esclusa. L'ultima riga e' 'TOTALE'.
 
    Il file usa denominazioni proprie sia per le aree ('S.P.VINCOLI') sia
    per i paesi ('ARABIA', 'MACEDONIA'): entrambe passano da cfg. Gli alias
    dei paesi sono applicati PRIMA di G.risolvi_paese, cosi' il resolver
    condiviso vede etichette gia' nella forma censuaria.
    """
    f = (sorted(glob.glob(os.path.join(OPENDATA, comune, "*.xls")))
         + sorted(glob.glob(os.path.join(OPENDATA, comune, "*.xlsx"))))
    if not f:
        raise FileNotFoundError(f"nessun xls in {OPENDATA}/{comune}")
    try:
        d = pd.read_excel(f[0], header=None)
    except ImportError as exc:                       # xlrd assente
        raise ImportError(f"lettura di {os.path.basename(f[0])} richiede "
                          f"xlrd >= 2.0.1: conda install xlrd") from exc
 
    nomi = G.zona_nomi(comune, cfg["geo_liv"])
    per_nome = {G.norm_nome(v): k for k, v in nomi.items()}
    override = cfg.get("override_nome", {})
    alias = {G.norm_nome(k): v for k, v in cfg.get("alias_paese", {}).items()}
 
    # colonne d'area dalla riga 1, escludendo intestazione e totale
    aree = []
    for i, v in d.iloc[1].items():
        if pd.isna(v):
            continue
        et = str(v).strip()
        if et == "AREE TERRITORIALI" or et.replace(" ", "") == "TOTALI":
            continue
        geo = override.get(et) or per_nome.get(G.norm_nome(et))
        if geo is None:
            raise ValueError(f"[ravenna] area non agganciata: {et!r}. "
                             f"Aggiungerla a override_nome nel registro.")
        aree.append((i, geo))
    if len(aree) != len(nomi):
        raise ValueError(f"[ravenna] {len(aree)} aree nel file contro "
                         f"{len(nomi)} nel registro")
 
    etichette = d.iloc[3:, 0]
    ultima = etichette[etichette.astype(str).str.strip().str.upper()
                       == "TOTALE"].index
    fine = int(ultima[0]) if len(ultima) else len(d)
 
    righe, residuali = [], {}
    for col, geo in aree:
        for k, sesso in ((0, "M"), (1, "F")):
            n = pd.to_numeric(d.iloc[3:fine, col + k], errors="coerce").fillna(0)
            for et, v in zip(d.iloc[3:fine, 0], n):
                if pd.isna(et) or v <= 0:
                    continue
                lab = alias.get(G.norm_nome(et), str(et).strip())
                p = G.risolvi_paese(lab, rif)
                if p is None:
                    residuali[str(et).strip()] = residuali.get(
                        str(et).strip(), 0) + v
                righe.append({"geo": geo, "sesso": sesso,
                              "paese": p or RESIDUALE, "n": float(v)})
 
    if residuali:
        tot = sum(residuali.values())
        top = sorted(residuali.items(), key=lambda x: -x[1])[:8]
        print(f"[ravenna] {len(residuali)} etichette non risolte "
              f"({tot:,.0f} persone, {100 * tot / sum(r['n'] for r in righe):.1f}%) "
              f"-> residuale: {[f'{k} ({v:.0f})' for k, v in top]}")
    return _lungo(righe)

def load_forli(comune: str, cfg: dict, rif: dict) -> pd.DataFrame:
    """Formato lungo (QUARTIERE, STATO, F, M, TOTALE).
 
    La fonte disaggrega in 41 unita' sub-quartiere: la mappa 41 -> 21 sta
    in cfg['mappa_unita'] ed e' ricavata dall'elenco ufficiale dei
    quartieri. 'in corso di definizione' non e' un'unita' territoriale e
    viene escluso.
 
    L'etichetta 'altro' e' il gruppo residuale dichiarato dalla fonte: va
    a RESIDUALE senza passare dal resolver, altrimenti verrebbe cercata
    fra i paesi censuari.
    """
    f = (sorted(glob.glob(os.path.join(OPENDATA, comune, "*.xlsx")))
         + sorted(glob.glob(os.path.join(OPENDATA, comune, "*.xls"))))
    if not f:
        raise FileNotFoundError(f"nessun xlsx in {OPENDATA}/{comune}")
    try:
        d = pd.read_excel(f[0], header=0, engine="calamine")
    except (ImportError, ValueError):
        try:                                   # xlsx non standard: openpyxl fallisce
            d = pd.read_excel(f[0], header=0)
        except KeyError as exc:
            raise ImportError(
                f"{os.path.basename(f[0])} e' un xlsx senza sharedStrings: "
                f"openpyxl non lo apre. Installare python-calamine.") from exc
 
    d.columns = [str(c).strip().upper() for c in d.columns]
    attese = {"QUARTIERE", "STATO", "F", "M"}
    if not attese <= set(d.columns):
        raise ValueError(f"[forli] colonne attese {sorted(attese)}, "
                         f"trovate {list(d.columns)}")
 
    mappa = {G.norm_nome(k): v for k, v in cfg["mappa_unita"].items()}
    alias = {G.norm_nome(k): v for k, v in cfg.get("alias_paese", {}).items()}
    residuo = {G.norm_nome(x) for x in cfg.get("etichette_residuo", ["altro"])}
 
    d["_u"] = d["QUARTIERE"].astype(str).map(G.norm_nome)
    d["geo"] = d["_u"].map(mappa)
 
    fuori = d[d["geo"].isna()]
    if len(fuori):
        n = pd.to_numeric(fuori.get("TOTALE", fuori["F"] + fuori["M"]),
                          errors="coerce").fillna(0).sum()
        print(f"[forli] unita' non mappate (escluse): "
              f"{sorted(fuori['QUARTIERE'].astype(str).unique())} "
              f"-> {n:,.0f} persone")
        d = d[d["geo"].notna()]
 
    atteso = len(set(cfg["mappa_unita"].values()))
    if d["geo"].nunique() != atteso:
        mancanti = sorted(set(cfg["mappa_unita"].values()) - set(d["geo"]))
        raise ValueError(f"[forli] {d['geo'].nunique()} quartieri nel file "
                         f"contro {atteso} nella mappa; mancanti: {mancanti}")
 
    righe, non_risolti = [], {}
    for r in d.itertuples():
        et = str(r.STATO).strip()
        if G.norm_nome(et) in residuo:
            p = RESIDUALE
        else:
            p = G.risolvi_paese(alias.get(G.norm_nome(et), et), rif)
            if p is None:
                v = pd.to_numeric(getattr(r, "F", 0), errors="coerce") or 0
                v += pd.to_numeric(getattr(r, "M", 0), errors="coerce") or 0
                non_risolti[et] = non_risolti.get(et, 0) + float(v)
                p = RESIDUALE
        for col, sesso in (("F", "F"), ("M", "M")):
            v = pd.to_numeric(getattr(r, col), errors="coerce")
            if pd.notna(v) and v > 0:
                righe.append({"geo": r.geo, "sesso": sesso,
                              "paese": p, "n": float(v)})
 
    if non_risolti:
        tot = sum(non_risolti.values())
        top = sorted(non_risolti.items(), key=lambda x: -x[1])[:8]
        print(f"[forli] {len(non_risolti)} etichette non risolte "
              f"({tot:,.0f} persone) -> residuale: "
              f"{[f'{k} ({v:.0f})' for k, v in top]}")
    return _lungo(righe)

LOADERS = {"brescia": load_brescia, "bologna": load_bologna,
           "parma": load_parma, "ravenna": load_ravenna,
           "forli": load_forli}
 

# ----------------------------------------------------------------------
# Margine comunale (censimento) e IPF
# ----------------------------------------------------------------------

def margine_censuario(comune: str, anno_cens: int = ANNO_CENS) -> pd.DataFrame:
    """(paese, sesso) -> conteggio, dal censimento comunale."""
    d = pd.read_csv(os.path.join(G.path_comune(comune),
                                 "cens_stranieri_paesi_decoded.csv"),
                    low_memory=False)
    d = d[(d["TIME_PERIOD"].astype(str) == str(anno_cens))
          & (d["GENDER"].astype(str).isin(["M", "F"]))].copy()
    d = d[~d["AREA_CONTRY_CITIZEN"].astype(str).isin(G.AGGREGATI_PAESE)]
    d["n"] = pd.to_numeric(d["OBS_VALUE"], errors="coerce").fillna(0)
    g = (d.groupby(["AREA_CONTRY_CITIZEN", "GENDER"])["n"].sum()
         .reset_index()
         .rename(columns={"AREA_CONTRY_CITIZEN": "paese", "GENDER": "sesso"}))
    return g[g["n"] > 0].reset_index(drop=True)


def costruisci_tabella(A: pd.DataFrame, B: pd.DataFrame, peso: pd.Series,
                       iters: int = 100, tol: float = 1e-10):
    """T(paese, sesso, geo) dalla struttura locale, calibrata sul censimento.

    La fonte locale e' anagrafica e di data diversa: entra come SEED, cioe'
    come forma della distribuzione, non come vincolo sui conteggi. I margini
    imposti sono due, entrambi censuari e con lo stesso totale, quindi il
    sistema e' sempre risolubile:
        (1) (paese, sesso) comunale;
        (2) popolazione straniera per unita' territoriale.
    Imporre anche i conteggi locali renderebbe i margini incompatibili.
    """
    paesi = sorted(A["paese"].unique())
    geos = sorted(peso.index)
    ip = {p: i for i, p in enumerate(paesi)}
    ig = {g: i for i, g in enumerate(geos)}
    isx = {"M": 0, "F": 1}
    N = float(A["n"].sum())

    MA = np.zeros((len(paesi), 2))
    for r in A.itertuples():
        MA[ip[r.paese], isx[r.sesso]] = r.n
    Mg = peso.reindex(geos).to_numpy(float) * N

    nat = MA.sum(axis=1)
    nat = nat / nat.sum()                       # quota nazionale per paese
    quota_sx = np.divide(MA, MA.sum(axis=1, keepdims=True),
                         out=np.full_like(MA, 0.5),
                         where=MA.sum(axis=1, keepdims=True) > 0)

    # ---- seed: struttura locale ----
    T = np.zeros((len(paesi), 2, len(geos)))
    for geo, sub in B.groupby("geo"):
        j = ig[geo]
        for sesso, s2 in sub.groupby(sub["sesso"].fillna("*")):
            agg = s2.groupby("paese")["n"].sum()
            nominati = [p for p in agg.index if p != RESIDUALE and p in ip]
            idx_nom = {ip[p] for p in nominati}
            col = np.zeros(len(paesi))
            for p in nominati:
                col[ip[p]] = agg[p]
            resto = float(agg.get(RESIDUALE, 0.0))
            if resto > 0:
                altri = np.array([i for i in range(len(paesi))
                                  if i not in idx_nom])
                w = nat[altri]
                if w.sum() > 0:
                    col[altri] = resto * w / w.sum()
            if sesso == "*":
                T[:, :, j] += col[:, None] * quota_sx
            else:
                T[:, isx[sesso], j] += col
    T = np.maximum(T, 1e-12)

    # ---- calibrazione ai due margini censuari ----
    for it in range(iters):
        cur = T.sum(axis=2)
        T *= np.divide(MA, cur, out=np.zeros_like(cur), where=cur > 0)[:, :, None]
        cur = T.sum(axis=(0, 1))
        T *= np.divide(Mg, cur, out=np.zeros_like(cur), where=cur > 0)[None, None, :]
        scarto = np.abs(T.sum(axis=2) - MA).max() / max(MA.max(), 1)
        if scarto < tol:
            break
    return T, paesi, geos, it + 1, scarto


# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------

def tabella_paese(comune: str, anno_cens: int = ANNO_CENS, verbose: bool = True):
    """P(paese | sesso, geo) per il comune. Tier 0 se la fonte manca."""
    i = G.info(comune)
    cfg = i.get("opendata_paese")
    A = margine_censuario(comune, anno_cens)
    rif = G.paesi_censuari(comune, anno_cens)

    # peso dei geo: quota di stranieri per unita' territoriale
    sez = pd.read_csv(G.path_sezioni(comune), low_memory=False)
    liv = cfg["geo_liv"] if cfg else i["livello"]
    if liv == "sezione":
        key = sez["SEZ21_ID"].astype("Int64").astype(str)
    elif liv is None:
        # Comune non articolato: zona degenere unica. Il condizionale
        # geografico si riduce alla composizione comunale, che e'
        # esattamente il tier 0. Non e' un errore ma una configurazione.
        key = pd.Series("0", index=sez.index)
    else:
        key = sez[G.livello_col(comune, liv)].astype("Int64").astype(str)
    peso = sez.groupby(key)["ST1"].sum()
    peso = peso[peso > 0]
    peso = peso / peso.sum()

    tot_A = float(A["n"].sum())

    if cfg is None:
        if verbose:
            print(f"[{comune}] {i['nome']}: nessuna fonte locale -> tier 0 "
                  f"(paese condizionato al solo sesso)")
        # Un solo gruppo residuale per unita': l'IPF distribuisce la
        # composizione comunale proporzionalmente alla popolazione, quindi
        # il risultato coincide con il comportamento senza condizionale.
        B = pd.DataFrame([{"geo": g, "sesso": None, "paese": RESIDUALE,
                           "n": float(w) * tot_A} for g, w in peso.items()])
        tier = 0
    else:
        B = LOADERS[cfg["loader"]](comune, cfg, rif)

        # unita' con residenti in anagrafe ma senza stranieri censiti
        fuori = ~B["geo"].isin(peso.index)
        if fuori.any() and verbose:
            print(f"[{comune}] {B.loc[fuori, 'n'].sum():,.0f} persone in "
                  f"{B.loc[fuori, 'geo'].nunique()} unita' senza stranieri "
                  f"censiti: escluse")
        B = B[~fuori].copy()

        # La fonte locale e' anagrafica: se ne usa la FORMA, non i livelli.
        # Ogni unita' viene riscalata al proprio totale censuario, cosi' i
        # due margini hanno lo stesso totale e l'IPF puo' convergere.
        
        tier = {"quartieri": 1, "zone": 2, "sezione": 3}.get(liv, 1)

    T, paesi, geos, n_it, scarto = costruisci_tabella(A, B, peso)
    if verbose:
        print(f"[{comune}] {i['nome']}: tier {tier} ({liv or 'comune'}) | "
              f"{len(paesi)} paesi x 2 sessi x {len(geos)} unita' | "
              f"IPF {n_it} iter, scarto {scarto:.2e}")
    return T, paesi, geos, {"tier": tier, "livello": liv, "B": B, "A": A}


def check(comuni: list[str] | None = None) -> int:
    err = 0
    for c in (comuni or sorted(G.COMUNI)):
        try:
            i = G.info(c)
            if not os.path.isdir(G.path_comune(c)):
                print(f"[{c}] {i['nome']}: dati comunali assenti, saltato")
                continue
            T, paesi, geos, meta = tabella_paese(c)
            A = meta["A"]
            tot = T.sum()
            print(f"      totale {tot:,.0f} vs censimento {A['n'].sum():,.0f} "
                  f"(scarto {tot - A['n'].sum():+,.1f})")
            # concentrazione: quanto la geografia cambia la composizione
            P = T / T.sum(axis=(0, 1), keepdims=True)
            glob_ = T.sum(axis=2) / T.sum()
            tv = 0.5 * np.abs(P - glob_[:, :, None]).sum(axis=(0, 1))
            w = T.sum(axis=(0, 1)) / T.sum()
            print(f"      distanza media dalla composizione comunale: "
                  f"{np.average(tv, weights=w):.3f} "
                  f"(0 = nessuna informazione geografica)")
        except Exception as e:
            print(f"[{c}] ERRORE: {type(e).__name__}: {e}")
            err += 1
    return err


def dump(comune: str, top: int = 10) -> None:
    T, paesi, geos, meta = tabella_paese(comune)
    lab = {v: k for k, v in G.paesi_censuari(comune).items()}
    tot = T.sum(axis=1)                       # (paese, geo), sommato sui sessi
    nomi = G.zona_nomi(comune, meta["livello"]) if meta["livello"] != "sezione" else {}
    print(f"\ntop-{top} paesi per unita' territoriale (prime 6 unita'):")
    for j, g in enumerate(geos[:6]):
        etichetta = nomi.get(g, g)
        ordine = np.argsort(-tot[:, j])[:top]
        voci = ", ".join(f"{lab.get(paesi[k], paesi[k])} {tot[k, j]:.0f}"
                         for k in ordine if tot[k, j] >= 1)
        print(f"  {etichetta:<22} {voci}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--dump" in args:
        k = args.index("--dump")
        top = int(args[args.index("--top") + 1]) if "--top" in args else 10
        dump(args[k + 1], top)
    elif "--check" in args:
        k = args.index("--check")
        c = [a for a in args[k + 1:] if not a.startswith("--")]
        sys.exit(1 if check(c or None) else 0)
    else:
        print(__doc__)
