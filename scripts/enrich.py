"""
enrich.py — anello 3: risoluzione fine sulla popolazione sintetica.

Il MaxEnt (anello 1) assegna il quartiere, che e' il livello piu' fine a cui
il censimento pubblica gli INCROCI necessari al solver. Sotto il quartiere
esistono solo marginali di sezione, che si sfruttano meglio come condizionali
post-hoc. Questo script aggiunge, nell'ordine:

    (3a) sezione di censimento   P(sigma | zona, sesso, eta3, cittadinanza)
    (3b) area UE/EXTRA_UE        P(area | SEZIONE, sesso)      [ri-assegnata]
    (3c) paese                   P(paese | area, sesso)        [ri-assegnato]
    (3d) eta esatta in anni      sezione -> quinquennio -> anno singolo
    (3e) indirizzo e coordinate  civico ANNCSU dentro la sezione

Perche' (3b) e (3c) vengono RI-assegnati: assign_nationality.py condiziona
l'area sulla zona, sommando ST17/18/20/21 dalle sezioni ai quartieri. Ma la
decomposizione della varianza della quota UE su Parma da':

    tra zone            0.00110  (sd 0.033)
    dentro le zone      0.01748  (sd 0.132)   di cui 0.00499 da discretizzazione
    struttura REALE di sezione / struttura di zona  =  11.4x

Cioe' quasi tutta la struttura spaziale sta sotto il quartiere. Nota che i
conteggi censuari sono enumerazione completa, non stime: la sovradispersione
(rapporto 3.50 contro l'assegnazione casuale entro zona) misura struttura
reale, non rumore campionario.

Assunzioni dichiarate:
    (8) sezione ⊥ (istruzione, condizione, background, origine_genitori)
        | (zona, sesso, eta3, cittadinanza).
        Sotto il quartiere il censimento non pubblica quegli incroci.
    (9) entro il quinquennio, la distribuzione per anno singolo e' quella
        comunale (anagrafe 1/1/anno), non quella di sezione.
    (10) l'indirizzo e' estratto uniformemente fra i civici della sezione:
        ANNCSU non fornisce il numero di residenti per civico.
    (11) nessuna struttura familiare: ogni individuo riceve un indirizzo
        indipendente.

Uso:
    python enrich.py 034027 --anno 2024
    python enrich.py 037006 --anno 2024 --pop-file popolazione_K9C_avq.csv
    python enrich.py 034027 --anno 2024 --keep-naz     # non ri-assegna area/paese
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd



import gsp.common as G
import gsp.opendata as OP

# Colonne P del tracciato: P30+k maschi, P67+k femmine, k=0..15 sui
# quinquennali da '<5' a '>74'.
OFF_SESSO = {"M": 30, "F": 67}
QUINQ = [(0, 0, 4), (1, 5, 9), (2, 10, 14), (3, 15, 19), (4, 20, 24),
         (5, 25, 29), (6, 30, 34), (7, 35, 39), (8, 40, 44), (9, 45, 49),
         (10, 50, 54), (11, 55, 59), (12, 60, 64), (13, 65, 69),
         (14, 70, 74), (15, 75, 100)]

# bin del constraint set -> (k del quinquennio, frazione, eta_min, eta_max).
# I due bin infantili attraversano la classe 5-9: il taglio a 9 anni viene
# dall'universo istruzione ISTAT ('9 anni e piu'), non dalla griglia
# quinquennale. Si spezza 4/5 - 1/5 assumendo uniformita' entro il
# quinquennio, la stessa assunzione gia' implicita nel resto del metodo.
BIN_QUINQ = {
    "0-8":   [(0, 1.0, 0, 4), (1, 0.8, 5, 8)],
    "9-14":  [(1, 0.2, 9, 9), (2, 1.0, 10, 14)],
    "15-24": [(3, 1.0, 15, 19), (4, 1.0, 20, 24)],
    "25-34": [(5, 1.0, 25, 29), (6, 1.0, 30, 34)],
    "35-49": [(7, 1.0, 35, 39), (8, 1.0, 40, 44), (9, 1.0, 45, 49)],
    "50-64": [(10, 1.0, 50, 54), (11, 1.0, 55, 59), (12, 1.0, 60, 64)],
    "65-74": [(13, 1.0, 65, 69), (14, 1.0, 70, 74)],
    "75+":   [(15, 1.0, 75, 100)],
}

# I bin non attraversano mai i confini delle tre classi ST.
BIN_ETA3 = {"0-8": "0-14", "9-14": "0-14", "15-24": "15-64",
            "25-34": "15-64", "35-49": "15-64", "50-64": "15-64",
            "65-74": "65+", "75+": "65+"}
ST_ETA3 = {("M", "0-14"): "ST25", ("M", "15-64"): "ST26", ("M", "65+"): "ST27",
           ("F", "0-14"): "ST28", ("F", "15-64"): "ST29", ("F", "65+"): "ST30"}
K_ETA3 = {"0-14": [0, 1, 2], "15-64": list(range(3, 13)), "65+": [13, 14, 15]}
ST_AREA = {("M", "UE"): "ST17", ("F", "UE"): "ST18",
           ("M", "EXTRA_UE"): "ST20", ("F", "EXTRA_UE"): "ST21"}
AREAS = ["UE", "EXTRA_UE"]

# EU27 = {
#     "austria", "belgio", "bulgaria", "cechia", "repubblica ceca", "cipro",
#     "croazia", "danimarca", "estonia", "finlandia", "francia", "germania",
#     "grecia", "irlanda", "lettonia", "lituania", "lussemburgo", "malta",
#     "paesi bassi", "polonia", "portogallo", "romania", "slovacchia",
#     "slovenia", "spagna", "svezia", "ungheria",
# }
# AGGREG_RE = ("tutte le voci|unione europea|countries|europ|africa|america|asia|"
#              "oceania|total|apolidi|aggregat|eea|efta")

SPECIALI = ("888888", "999999")


# ----------------------------------------------------------------------
# utilita'
# ----------------------------------------------------------------------




# ----------------------------------------------------------------------
# caricamenti
# ----------------------------------------------------------------------

def load_sezioni(comune: str) -> pd.DataFrame:
    """Sezioni del comune, con pesi demografici e quote straniere."""
    path = G.path_sezioni(comune)
    if not os.path.exists(path):
        sys.exit(f"File sezioni assente: {path}\n"
                 f"  generarlo con build_sezioni.py {comune}")
    s = pd.read_csv(path)
     # Comune non articolato: zona degenere unica. Il condizionamento si
    # sposta interamente sulla sezione, che e' il livello piu' fine
    # disponibile e anche il piu' informativo (cfr. nota sul segnale
    # compositivo: la zona ne trattiene fra il 2% e il 20%).
    liv = G.livello_col(comune) if G.info(comune)["livello"] else None
    if liv is not None and liv not in s.columns:
        sys.exit(f"Colonna {liv} assente in {path}")
 
    sez_str = s["SEZ21_ID"].astype("Int64").astype(str)
    zona_col = (s[liv].astype("Int64").astype(str) if liv is not None
                else pd.Series("0", index=s.index))
    s = pd.concat([s, pd.DataFrame({
        "zona": zona_col,
        "SEZ": sez_str,
        "speciale": sez_str.str.contains("|".join(SPECIALI), regex=True),
    }, index=s.index)], axis=1)

    # pesi demografici per (sesso, quinquennio) e quote straniere per eta3
    nuove = {}
    for sesso, off in OFF_SESSO.items():
        for k, _, _ in QUINQ:
            nuove[f"w_{sesso}_{k}"] = pd.to_numeric(
                s[f"P{off + k}"], errors="coerce").fillna(0).to_numpy(float)
        for e3, ks in K_ETA3.items():
            tot = sum(nuove[f"w_{sesso}_{k}"] for k in ks)
            st = pd.to_numeric(s[ST_ETA3[(sesso, e3)]],
                               errors="coerce").fillna(0).to_numpy(float)
            # quota di stranieri nella cella (sesso, eta3) della sezione
            nuove[f"q_{sesso}_{e3}"] = np.where(
                tot > 0, np.clip(st / np.where(tot > 0, tot, 1), 0, 1), 0.0)
    s = pd.concat([s, pd.DataFrame(nuove, index=s.index)], axis=1)

    print(f"[sez] {len(s):,} sezioni | P1 = {int(s['P1'].sum()):,} | "
          f"speciali: {int(s['speciale'].sum())}")
    return s


def load_civici(comune: str) -> pd.DataFrame:
    """Civici ANNCSU gia' agganciati alle sezioni, filtrati sul comune."""
    path = G.path_civici(comune)
    if not os.path.exists(path):
        sys.exit(f"File civici assente: {path}\n"
                 f"  generarlo con join_civici_sezioni.py <regione>")
    c = pd.read_csv(path, dtype={"CODICE_ISTAT": str}, low_memory=False)
    n0 = len(c)
    c = c[c["CODICE_ISTAT"] == comune].copy()
    c["SEZ"] = pd.to_numeric(c["SEZ21_ID"], errors="coerce").astype("Int64")
    c = c[c["SEZ"].notna()].copy()

    # ANNCSU attribuisce il civico al comune, il join spaziale lo colloca in
    # una sezione: al confine le due attribuzioni possono divergere.
    procom = str(int(comune))
    fuori = ~c["SEZ"].astype(str).str.startswith(procom)
    if fuori.any():
        print(f"[civ] {int(fuori.sum())} civici in sezioni di altri comuni: "
              f"scartati")
        c = c[~fuori].copy()
    c["SEZ"] = c["SEZ"].astype(str)

    print(f"[civ] {len(c):,} civici del comune (su {n0:,} provinciali) | "
          f"{c['SEZ'].nunique():,} sezioni coperte")
    return c[["SEZ", "ODONIMO", "CIVICO", "ESPONENTE",
              "COORD_X_COMUNE", "COORD_Y_COMUNE"]]


def load_eta_singola(comune: str, anno: int) -> dict:
    """Distribuzione comunale per anno singolo, dall'anagrafe SDMX."""
    path = os.path.join(G.path_comune(comune),
                        "anag_sesso_eta_statociv_decoded.csv")
    if not os.path.exists(path):
        print(f"[eta] anagrafe assente: distribuzione uniforme entro "
              f"il quinquennio")
        return {}
    a = pd.read_csv(path, low_memory=False)
    a = a[a["TIME_PERIOD"].astype(str) == str(anno)].copy()
    a = a[a["SEX"].astype(str).isin(["1", "2"])]
    age = a["AGE"].astype(str)
    ok = age.str.fullmatch(r"Y\d+|Y_GE100")
    a = a[ok].copy()
    a["anni"] = np.where(a["AGE"].astype(str) == "Y_GE100", 100,
                         pd.to_numeric(a["AGE"].astype(str).str[1:],
                                       errors="coerce"))
    a["sesso"] = a["SEX"].astype(str).map({"1": "M", "2": "F"})
    a["v"] = pd.to_numeric(a["OBS_VALUE"], errors="coerce").fillna(0)
    g = a.groupby(["sesso", "anni"])["v"].sum()
    print(f"[eta] anagrafe {anno}: {int(g.sum()):,} individui, "
          f"eta 0-{int(g.index.get_level_values(1).max())}")
    return {s: g.loc[s] for s in ("M", "F") if s in g.index.levels[0]}


# ----------------------------------------------------------------------
# (3a) sezione
# ----------------------------------------------------------------------

def assegna_sezione(pop, sez, rng):
    """P(sigma | zona, sesso, eta3, cittadinanza), allocazione esatta."""
    sez_by_zona = {z: g for z, g in sez.groupby("zona")}
    manca = set(pop["zona"].astype(str)) - set(sez_by_zona)
    if manca:
        sys.exit(f"Zone della popolazione assenti nelle sezioni: "
                 f"{sorted(manca)[:5]}\n  livello sbagliato nel registro?")

    out = pd.Series(index=pop.index, dtype=object)
    liv_uso = {"cella": 0, "demografico": 0}

    chiavi = pop.groupby(["zona", "sesso", "eta", "cittadinanza"]).indices
    for key in sorted(chiavi):
        z, s, e, cit = key
        pos = chiavi[key]
        g = sez_by_zona[str(z)]
        e3 = BIN_ETA3[e]

        # peso demografico del bin: somma dei quinquennali con le frazioni
        base = sum(f * g[f"w_{s}_{k}"].to_numpy()
                   for k, f, _, _ in BIN_QUINQ[e])
        quota = g[f"q_{s}_{e3}"].to_numpy()
        w = base * quota if cit == "FRG" else base * (1.0 - quota)

        if w.sum() <= 0:                 # cella vuota: solo demografia
            w = base
            liv_uso["demografico"] += len(pos)
            if w.sum() <= 0:
                w = g["P1"].to_numpy(dtype=float)
        else:
            liv_uso["cella"] += len(pos)

        idx = pop.index.to_numpy()[pos].copy()
        rng.shuffle(idx)
        conta = G.largest_remainder(len(idx), w)
        out.loc[idx] = G.spartisci(idx, conta, g["SEZ"].to_numpy())

    pop["sezione"] = out
    tot = len(pop)
    print(f"\n[3a] sezione assegnata | celle usate: "
          f"{liv_uso['cella']:,} ({liv_uso['cella']/tot:.1%}) piene, "
          f"{liv_uso['demografico']:,} ({liv_uso['demografico']/tot:.1%}) "
          f"solo demografiche")
    print(f"[3a] sezioni distinte occupate: {pop['sezione'].nunique():,} "
          f"su {len(sez):,}")
    return pop


# ----------------------------------------------------------------------
# (3b/3c) area e paese
# ----------------------------------------------------------------------

def tab_paesi(comune, anno):
    """P(paese | area, sesso) dal censimento comunale."""
    path = os.path.join(G.path_comune(comune),
                        "cens_stranieri_paesi_decoded.csv")
    d = pd.read_csv(path, low_memory=False)
    d = d[(d["TIME_PERIOD"].astype(str) == str(anno - 1))
          & (d["GENDER"].astype(str).isin(["M", "F"]))].copy()
    # Aggregati filtrati per CODICE e non per etichetta: una regex su
    # 'africa' catturava anche 'Sud Africa', che e' un paese. I codici
    # aggregati sono una ventina e fissi; i paesi duecento e in crescita.
    d = d[~d["AREA_CONTRY_CITIZEN"].astype(str).isin(G.AGGREGATI_PAESE)]
    d = d[d["AREA_CONTRY_CITIZEN_label"].notna()
          & (pd.to_numeric(d["OBS_VALUE"], errors="coerce").fillna(0) > 0)]
    d["paese"] = d["AREA_CONTRY_CITIZEN_label"].astype(str)
    # Classificare per codice ISO e non per etichetta: le denominazioni
    # ISTAT sono invertite ('Ceca, Repubblica'), quindi il confronto per
    # stringa le manca.
    d["area"] = d["AREA_CONTRY_CITIZEN"].map(
        lambda c: "UE" if c in G.EU27_ISO else "EXTRA_UE")

    d["v"] = pd.to_numeric(d["OBS_VALUE"], errors="coerce")
    cp = d.groupby(["area", "GENDER", "paese"])["v"].sum().reset_index()
    print(f"[3c] paesi: {d['paese'].nunique()} | "
          f"UE: {cp[cp.area == 'UE']['paese'].nunique()}")
    return {(a, s): (g["paese"].tolist(), g["v"].to_numpy(float))
            for (a, s), g in cp.groupby(["area", "GENDER"])}


def assegna_area_paese(pop, sez, comune, anno, rng, usa_tier=True):
    """(3b) area condizionata alla SEZIONE; (3c) paese condizionato ad area."""
    #paesi = tab_paesi(comune, anno)
    sez_i = sez.set_index("SEZ")
    z_area = sez.groupby("zona")[[ST_AREA[(s, a)] for s in ("M", "F")
                                  for a in AREAS]].sum()

    frg = pop.index[pop["cittadinanza"] == "FRG"]
    pop["area"] = pd.NA
    pop["paese"] = pd.NA
    pop.loc[pop["cittadinanza"] == "ITL", "paese"] = "Italia"
    uso = {"sezione": 0, "zona": 0}

    chiavi = pop.loc[frg].groupby(["sezione", "sesso"]).indices
    idx_frg = pop.loc[frg].index.to_numpy()
    for key in sorted(chiavi):
        sg, s = key
        idx = idx_frg[chiavi[key]].copy()
        r = sez_i.loc[sg]
        w = np.array([r[ST_AREA[(s, a)]] for a in AREAS], dtype=float)
        if w.sum() <= 0:                      # sezione senza stranieri di quel sesso
            zr = z_area.loc[r["zona"]]
            w = np.array([zr[ST_AREA[(s, a)]] for a in AREAS], dtype=float)
            uso["zona"] += len(idx)
        else:
            uso["sezione"] += len(idx)
        rng.shuffle(idx)
        conta = G.largest_remainder(len(idx), w)
        pop.loc[idx, "area"] = G.spartisci(idx, conta, AREAS)

    n = len(frg)
    print(f"\n[3b] area: {uso['sezione']:,} ({uso['sezione']/max(n,1):.1%}) "
          f"dalla sezione, {uso['zona']:,} ({uso['zona']/max(n,1):.1%}) "
          f"dalla zona")

    # ---- (3c) paese, condizionato alla geografia se la fonte c'e' ----
    if usa_tier:
        T, codici, geos, meta = OP.tabella_paese(comune, anno - 1, verbose=True)
        lab = G.etichette_paese(comune, anno - 1)
        nomi = np.array([lab.get(c, c) for c in codici])
        ue = np.array([c in G.EU27_ISO for c in codici])
        mask = {"UE": ue, "EXTRA_UE": ~ue}
        ig = {g: i for i, g in enumerate(geos)}
        isx = {"M": 0, "F": 1}
        Tc = T.sum(axis=2)                      # riserva comunale (paese, sesso)

        # tier 3 -> sezione (assegnata in 3a), altrimenti la zona
         # tier 3 -> sezione (assegnata in 3a); tier 0 su comune non
        # articolato -> zona degenere, che e' comunque una colonna valida
        geo_col = "sezione" if meta["livello"] == "sezione" else "zona"
        uso = {"geo": 0, "comune": 0}

        for key, g in pop.loc[frg].groupby(["area", "sesso", geo_col]):
            area, sesso, geo = key
            idx = g.index.to_numpy().copy()
            m = mask[area]
            j = ig.get(str(geo))
            w = T[m, isx[sesso], j] if j is not None else None
            if w is None or w.sum() <= 0:
                # l'area viene dalle colonne ST della sezione, T dal seed
                # locale: possono non concordare su celle minuscole
                w = Tc[m, isx[sesso]]
                uso["comune"] += len(idx)
            else:
                uso["geo"] += len(idx)
            rng.shuffle(idx)
            pop.loc[idx, "paese"] = G.spartisci(
                idx, G.largest_remainder(len(idx), w), nomi[m])

        n = max(len(frg), 1)
        print(f"[3c] paese: tier {meta['tier']} su "
              f"{meta['livello'] or 'comune'} | "
              f"{uso['geo']:,} ({uso['geo']/n:.1%}) dalla geografia, "
              f"{uso['comune']:,} ({uso['comune']/n:.1%}) riserva comunale")
    else:
        paesi = tab_paesi(comune, anno)
        for key, g in pop.loc[frg].groupby(["area", "sesso"]):
            if key not in paesi:
                continue
            nomi_, w = paesi[key]
            idx = g.index.to_numpy().copy()
            rng.shuffle(idx)
            pop.loc[idx, "paese"] = G.spartisci(
                idx, G.largest_remainder(len(idx), w), nomi_)
        print(f"[3c] paese: condizionale comunale (--no-tier)")

    return pop
   


# ----------------------------------------------------------------------
# (3d) eta esatta
# ----------------------------------------------------------------------

def assegna_eta(pop, sez, eta_w, rng):
    """Sezione -> quinquennio -> anno singolo (distribuzione comunale)."""
    sez_i = sez.set_index("SEZ")
    out = pd.Series(index=pop.index, dtype="float64")

    chiavi = pop.groupby(["sezione", "sesso", "eta"]).indices
    for key in sorted(chiavi):
        sg, s, e = key
        idx = pop.index.to_numpy()[chiavi[key]].copy()
        blocchi = BIN_QUINQ[e]
        r = sez_i.loc[sg]
        w = np.array([f * r[f"w_{s}_{k}"] for k, f, _, _ in blocchi],
                     dtype=float)
        if w.sum() <= 0:
            w = np.ones(len(blocchi))
        rng.shuffle(idx)
        conta = G.largest_remainder(len(idx), w)

        s2 = 0
        for (k, _, lo, hi), c in zip(blocchi, conta):
            if c == 0:
                continue
            anni = np.arange(lo, hi + 1)
            if s in eta_w:
                pw = np.array([float(eta_w[s].get(a, 0.0)) for a in anni])
            else:
                pw = np.ones(len(anni))
            if pw.sum() <= 0:
                pw = np.ones(len(anni))
            n_anno = G.largest_remainder(c, pw)
            val = np.repeat(anni, n_anno)
            out.loc[idx[s2:s2 + c]] = rng.permutation(val)
            s2 += c

    pop["eta_anni"] = out.astype("Int64")
    print(f"\n[3d] eta esatta | media {out.mean():.1f} | "
          f"min {int(out.min())} max {int(out.max())}")
    return pop


# ----------------------------------------------------------------------
# (3e) indirizzo
# ----------------------------------------------------------------------

def assegna_indirizzo(pop, sez, civ, rng):
    """Civico dentro la sezione; fallback di zona; convivenze senza indirizzo."""
    civ_by_sez = {s: g.reset_index(drop=True) for s, g in civ.groupby("SEZ")}
    sez_zona = dict(zip(sez["SEZ"], sez["zona"]))
    speciali = set(sez.loc[sez["speciale"], "SEZ"])

    civ = civ.assign(zona=civ["SEZ"].map(sez_zona))
    civ_by_zona = {z: g.reset_index(drop=True)
                   for z, g in civ[civ["zona"].notna()].groupby("zona")}
    # centroide di zona per le convivenze (media dei civici, niente geometrie)
    cen = {z: (g["COORD_X_COMUNE"].mean(), g["COORD_Y_COMUNE"].mean())
           for z, g in civ_by_zona.items()}

    for c in ("via", "civico", "lon", "lat"):
        pop[c] = pd.NA
    pop["indirizzo_fonte"] = pd.NA
    uso = {"sezione": 0, "zona": 0, "convivenza": 0}

    for sg, g in pop.groupby("sezione"):
        idx = g.index.to_numpy()
        if sg in speciali:
            z = sez_zona.get(sg)
            x, y = cen.get(z, (np.nan, np.nan))
            pop.loc[idx, ["lon", "lat"]] = [x, y]
            pop.loc[idx, "indirizzo_fonte"] = "convivenza"
            uso["convivenza"] += len(idx)
            continue
        pool = civ_by_sez.get(sg)
        fonte = "sezione"
        if pool is None or len(pool) == 0:
            pool = civ_by_zona.get(sez_zona.get(sg))
            fonte = "zona"
            if pool is None or len(pool) == 0:
                uso["zona"] += len(idx)
                continue
        sel = pool.iloc[rng.integers(0, len(pool), size=len(idx))]
        
        pop.loc[idx, "via"] = sel["ODONIMO"].values

        civico = (sel["CIVICO"].astype(str).str.strip()
                  + sel["ESPONENTE"].fillna("").astype(str).str.strip())
        pop.loc[idx, "civico"] = civico.to_numpy()
        pop.loc[idx, "lon"] = sel["COORD_X_COMUNE"].values
        pop.loc[idx, "lat"] = sel["COORD_Y_COMUNE"].values
        pop.loc[idx, "indirizzo_fonte"] = fonte
        uso[fonte] += len(idx)

    n = len(pop)
    print(f"\n[3e] indirizzo | {uso['sezione']:,} ({uso['sezione']/n:.2%}) "
          f"dalla sezione, {uso['zona']:,} ({uso['zona']/n:.2%}) fallback "
          f"di zona, {uso['convivenza']:,} ({uso['convivenza']/n:.2%}) "
          f"convivenze")
    return pop


# ----------------------------------------------------------------------
# validazione
# ----------------------------------------------------------------------

def valida(pop, sez):
    s = sez.set_index("SEZ")
    print("\n[val] sintetico vs censimento, per sezione:")

    for nome, syn, cens in [
        ("popolazione", pop.groupby("sezione").size(), s["P1"]),
        ("stranieri",
         pop[pop.cittadinanza == "FRG"].groupby("sezione").size(), s["ST1"]),
        ("UE", pop[pop.area == "UE"].groupby("sezione").size(), s["ST16"]),
    ]:
        a = syn.reindex(s.index).fillna(0)
        b = pd.to_numeric(cens, errors="coerce").fillna(0)
        mae = float((a - b).abs().mean())
        r = float(np.corrcoef(a, b)[0, 1]) if b.std() > 0 else float("nan")
        print(f"  {nome:<12} MAE {mae:6.2f} su media {b.mean():7.1f} "
              f"| corr {r:.4f} | totale {int(a.sum()):,} vs {int(b.sum()):,}")

    # decomposizione della varianza: quanto la sezione aggiunge alla zona
    q = s[(s.ST16 + s.ST19) > 0].copy()
    q["n"] = q.ST16 + q.ST19
    q["sh"] = q.ST16 / q["n"]
    zt = q.groupby("zona").apply(
        lambda g: np.average(g.sh, weights=g["n"]))
    q["pz"] = q["zona"].map(zt)
    gl = q.ST16.sum() / q["n"].sum()
    v_b = np.average((zt - gl) ** 2, weights=q.groupby("zona")["n"].sum())
    v_o = np.average((q.sh - q.pz) ** 2, weights=q["n"])
    v_n = np.average(q.pz * (1 - q.pz) / q["n"], weights=q["n"])
    v_r = max(v_o - v_n, 0.0)
    print(f"\n[val] quota UE: varianza tra zone {v_b:.5f} | "
          f"dentro le zone {v_o:.5f} (di cui {v_n:.5f} da discretizzazione)")
    if v_b > 0:
        print(f"      sovradispersione {v_o/v_n:.2f}x | struttura reale di "
              f"sezione / di zona = {v_r/v_b:.1f}x")
    else:
        # zona unica: il rapporto non e' definito, tutta la struttura
        # spaziale sta per costruzione dentro l'unica zona.
        print(f"      sovradispersione {v_o/v_n:.2f}x | zona unica: "
              f"struttura reale di sezione {v_r:.5f} (rapporto non definito)")


# ----------------------------------------------------------------------

def main(comune, anno, pop_file, out_name, keep_naz, no_tier, seed):
    try:
        G.info(comune)
        cdir = G.path_constraints(comune, anno)
    except KeyError as e:
        sys.exit(str(e))

    pop_file = G.resolve_pop_file(cdir, pop_file, "_avq")
    pop = pd.read_csv(os.path.join(cdir, pop_file)).reset_index(drop=True)

    if out_name is None:
        # Le varianti di confronto non devono mai atterrare sul nome
        # canonico: sono run diagnostici, non output di produzione.
        suff = "_full"
        if keep_naz:
            suff += "_keepnaz"
        elif no_tier:
            suff += "_tier0"
        out_name = pop_file.replace(".csv", suff + ".csv")
        
    print(f"[pop] {pop_file}: {len(pop):,} individui -> {out_name}")
    if G.info(comune)["livello"] is None:
        pop["zona"] = "0"                    # zona degenere: vedi load_sezioni
        print("[cfg] comune non articolato: zona degenere, "
              "condizionamento sulla sola sezione")
    else:
        pop["zona"] = pop["zona"].astype("Int64").astype(str)
        G.verifica_livello(pop["zona"], comune)
    sez = load_sezioni(comune)
    civ = load_civici(comune)
    eta_w = load_eta_singola(comune, anno)

    rng = np.random.default_rng(seed)
    pop = assegna_sezione(pop, sez, rng)
    if keep_naz:
        if not {"area", "paese"} <= set(pop.columns):
            sys.exit(f"--keep-naz richiede che {pop_file} abbia gia' le "
                     f"colonne 'area' e 'paese' (file _naz da "
                     f"assign_nationality.py): non ci sono.")
        print("\n[3b/3c] --keep-naz: area e paese lasciati invariati")
    else:
        pop = assegna_area_paese(pop, sez, comune, anno, rng, not no_tier)
    pop = assegna_eta(pop, sez, eta_w, rng)
    pop = assegna_indirizzo(pop, sez, civ, rng)

    valida(pop, sez)

    out = os.path.join(cdir, out_name)
    pop.to_csv(out, index=False)
    print(f"\n[done] -> {out}  ({len(pop):,} x {pop.shape[1]})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Anello 3: sezione, area, paese, eta esatta, indirizzo.")
    ap.add_argument("comune", help="codice ISTAT (es. 034027)")
    ap.add_argument("--anno", type=int, default=2024)
    ap.add_argument("--pop-file", default=None,
                    help="default: auto-detect popolazione_K10C_avq.csv -> "
                         "K9C_avq -> ... -> K6C_avq in constraints_<anno>/")
    ap.add_argument("--out", default=None,
                    help="default: <file popolazione>_full.csv")
    ap.add_argument("--keep-naz", action="store_true",
                    help="non ri-assegna area e paese. Ha senso SOLO con "
                         "--pop-file su un file _naz prodotto da "
                         "assign_nationality.py: sui file _avq quelle "
                         "colonne non esistono e resterebbero assenti")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-tier", action="store_true",
                    help="paese condizionato al solo (area, sesso) comunale, "
                         "come prima dell'introduzione dei tier")
    x = ap.parse_args()
    main(x.comune, x.anno, x.pop_file, x.out, x.keep_naz, x.no_tier, x.seed)
