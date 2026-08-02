"""
assign_nationality.py — v2. Nazionalità two-stage sulla popolazione KXC.

Generalizzato per più comuni (ora Bologna 037006, Brescia 017029; estendibile
via registro COMUNI o flag --sezioni) e per livello territoriale a scelta:
    --livello asc1  ->  P(area | COM_ASC1, sesso)   (Bologna: 6 quartieri)
    --livello asc2  ->  P(area | COM_ASC2, sesso)   (Bologna: 18 zone)

Gerarchia:  (2a) area UE/EXTRA_UE ~ P(area | zona, sesso)   [sezioni ST17/18/20/21]
            (2b) paese            ~ P(paese | area, sesso)  [comunale, censimento anno-1]
Allocazione ESATTA (largest remainder) a ogni livello.

ITL -> paese = 'Italia'. Output: popolazione_KXC_naz.csv (colonne + area, paese).

Assunzioni dichiarate:
    (4) paese ⊥ zona | (area, sesso): la struttura territoriale entra al
        livello area (UE/extra-UE per zona), il dettaglio paese è
        condizionato solo ad area e sesso (il dato non consente di più).

Codici zona: normalizzati come stringhe intere senza zeri iniziali e senza
l'eventuale prefisso PROCOM (es. Bologna '37006009' -> '9'), così i codici
della popolazione e quelli COM_ASC* delle sezioni combaciano a prescindere
dal formato. Se la popolazione è codificata ad ASC2 e si chiede --livello
asc1, la mappatura ASC2 -> ASC1 viene derivata automaticamente dalle sezioni.

Uso:
    python assign_nationality.py 017029 --anno 2024                      # Brescia, ASC1
    python assign_nationality.py 037006 --anno 2024 --livello asc2       # Bologna, 18 zone
    python assign_nationality.py 037006 --anno 2024 --livello asc1       # Bologna, 6 quartieri
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

import gsp.common as G

# Vocabolario locale della CLI. Il registro usa nomi semantici
# ('quartieri', 'zone'); qui restano i nomi di colonna.
LIVELLI = {"asc1": "COM_ASC1", "asc2": "COM_ASC2"}


COL_TO_ASC = {v: k for k, v in LIVELLI.items()}


    
AREAS = ["UE", "EXTRA_UE"]

# EU27 = {  # etichette italiane ISTAT, Italia esclusa
#     "austria", "belgio", "bulgaria", "cechia", "repubblica ceca", "cipro",
#     "croazia", "danimarca", "estonia", "finlandia", "francia", "germania",
#     "grecia", "irlanda", "lettonia", "lituania", "lussemburgo", "malta",
#     "paesi bassi", "polonia", "portogallo", "romania", "slovacchia",
#     "slovenia", "spagna", "svezia", "ungheria",
# }

# AGGREG_RE = ("tutte le voci|unione europea|countries|europ|africa|america|asia|"
#              "oceania|total|apolidi|aggregat|eea|efta")









def main(comune, anno, livello, col_pop, sezioni_csv, pop_file_override, out_name, seed):
    try:
        cdir = G.path_constraints(comune, anno)
        liv_reg = G.livello_col(comune) if G.info(comune)["livello"] else None
    except (KeyError, ValueError) as e:
        sys.exit(str(e))
    cens_anno = anno - 1

    # Il livello viene dal registro. --livello resta per override espliciti,
    # ma se diverge avverte: i codici ASC1 e ASC2 si sovrappongono (a Bologna
    # 37006011 vale 'Borgo Panigale-Reno' come ASC1 e 'San Donato' come ASC2),
    # quindi un merge sul codice sbagliato riesce e da' il nome sbagliato.
    if livello is None:
        if liv_reg is None:
            sys.exit(f"{G.info(comune)['nome']} non ha articolazione "
                     f"sub-comunale: usare --sezioni e --livello espliciti")
        livello = COL_TO_ASC[liv_reg]
        print(f"[cfg] livello dal registro: {livello} ({liv_reg})")
    elif liv_reg and LIVELLI[livello] != liv_reg:
        print(f"[warn] --livello {livello} ({LIVELLI[livello]}) diverge dal "
              f"registro ({liv_reg}): verificare i codici zona")

    if sezioni_csv is None:
        sezioni_csv = G.path_sezioni(comune)


    # ---------- (2a) P(area | zona, sesso) dalle sezioni ----------
    b = pd.read_csv(sezioni_csv)
    col_sez = LIVELLI[livello]
    if col_sez not in b.columns:
        sys.exit(f"Colonna {col_sez} assente in {sezioni_csv}. "
                 f"Colonne disponibili: {sorted(b.columns)}")
    newcols = {f"_{liv}": G.norm_code(b[col], comune)
               for liv, col in LIVELLI.items() if col in b.columns}
    b = pd.concat([b, pd.DataFrame(newcols, index=b.index)], axis=1)
    no_zona = b[col_sez].nunique(dropna=True) <= 1
    if no_zona:
        print(f"[2a] {col_sez} ha un solo valore osservato: nessuna "
              f"sub-area per questo comune -> P(area|sesso) comunale "
              f"(niente condizionamento di zona)")
    z5 = b.groupby(f"_{livello}")[["ST17", "ST18", "ST20", "ST21"]].sum()
    area_p = {}
    for zona, r in z5.iterrows():
        area_p[(zona, "M")] = np.array([r["ST17"], r["ST20"]], dtype=float)
        area_p[(zona, "F")] = np.array([r["ST18"], r["ST21"]], dtype=float)
    fb = {"M": np.array([z5["ST17"].sum(), z5["ST20"].sum()], dtype=float),
          "F": np.array([z5["ST18"].sum(), z5["ST21"].sum()], dtype=float)}
    print(f"[2a] livello={livello} ({col_sez}): {z5.shape[0]} zone, "
          f"{len(area_p)} gruppi (zona,sesso) | "
          f"UE tot={z5[['ST17','ST18']].values.sum():,.0f} "
          f"extraUE tot={z5[['ST20','ST21']].values.sum():,.0f}")

    # ---------- (2b) P(paese | area, sesso) comunale ----------
    d = pd.read_csv(os.path.join(G.path_comune(comune),
                                 "cens_stranieri_paesi_decoded.csv"))
    
    d = d[(d["TIME_PERIOD"] == cens_anno) & (d["GENDER"].isin(["M", "F"]))].copy()
    # Filtrare gli aggregati per CODICE e non per etichetta: la regex su
    # 'africa' catturava anche 'Sud Africa', che e' un paese. I codici
    # aggregati sono una ventina e fissi (G.AGGREGATI_PAESE); i paesi sono
    # duecento e in crescita.
    d = d[~d["AREA_CONTRY_CITIZEN"].astype(str).isin(G.AGGREGATI_PAESE)]
    d = d[d["AREA_CONTRY_CITIZEN_label"].notna()
          & (pd.to_numeric(d["OBS_VALUE"], errors="coerce").fillna(0) > 0)]

    d["paese"] = d["AREA_CONTRY_CITIZEN_label"].astype(str)
    d["area"] = d["AREA_CONTRY_CITIZEN"].map(
        lambda c: "UE" if c in G.EU27_ISO else "EXTRA_UE")
    
    ue_found = sorted(d[d.area == "UE"]["paese"].unique())
    print(f"[2b] paesi: {d['paese'].nunique()} | classificati UE: {len(ue_found)}")
    print(f"     UE trovati: {ue_found}")
    cp = d.groupby(["area", "GENDER", "paese"])["OBS_VALUE"].sum().reset_index()
    paese_p = {}
    for (area, sex), g in cp.groupby(["area", "GENDER"]):
        paese_p[(area, sex)] = (g["paese"].tolist(),
                                g["OBS_VALUE"].values.astype(float))

    for area, st_m, st_f in [("UE", "ST17", "ST18"), ("EXTRA_UE", "ST20", "ST21")]:
        com = cp[cp.area == area].groupby("GENDER")["OBS_VALUE"].sum()
        sez = {"M": z5[st_m].sum(), "F": z5[st_f].sum()}
        print(f"[check] {area}: comunale M/F {com.get('M',0):,.0f}/{com.get('F',0):,.0f}"
              f"  sezioni M/F {sez['M']:,.0f}/{sez['F']:,.0f}")

    # ---------- assegnazione sulla popolazione ----------
    pop_file = G.resolve_pop_file(cdir, pop_file_override)
    if out_name is None:                       # il nome di uscita segue l'ingresso
        out_name = pop_file.replace(".csv", "_naz.csv")
    pop = pd.read_csv(os.path.join(cdir, pop_file))
    print(f"[pop] file: {pop_file} -> {out_name}")

    if not no_zona:
        if col_pop not in pop.columns:
            sys.exit(f"Colonna --col-pop '{col_pop}' assente nella popolazione. "
                     f"Colonne disponibili: {sorted(pop.columns)}")
        pop[col_pop] = pop[col_pop].astype(str)
    if no_zona:
        pop["_zkey"] = "0"
    else:
        G.verifica_livello(pop[col_pop], comune)
        pop["_zkey"] = G.norm_code(pop[col_pop], comune)

    for c in ("area", "paese"):
        if c in pop.columns:
            sys.exit(f"La popolazione ha già una colonna '{c}': rinominarla "
                     f"prima di eseguire (rischio di sovrascrittura).")

    pop["area"] = pd.NA
    pop["paese"] = pd.NA
    pop.loc[pop["cittadinanza"] == "ITL", "paese"] = "Italia"

    frg_mask = pop["cittadinanza"] == "FRG"
    pop_codes = set(pop.loc[frg_mask, "_zkey"].unique())
    if not pop_codes <= set(z5.index):
        if livello == "asc1" and "_asc2" in b.columns \
                and pop_codes <= set(b["_asc2"].unique()):
            nun = b.groupby("_asc2")["_asc1"].nunique()
            if (nun > 1).any():
                sys.exit(f"Mappatura ASC2->ASC1 non funzionale nelle sezioni: "
                         f"{list(nun[nun > 1].index)}")
            m = b.drop_duplicates("_asc2").set_index("_asc2")["_asc1"]
            pop["_zkey"] = pop["_zkey"].map(m)
            print(f"[map] popolazione codificata ad ASC2: mappata su ASC1 "
                  f"via sezioni ({len(m)} zone -> {m.nunique()} quartieri).")
        else:
            missing = sorted(pop_codes - set(z5.index))
            print(f"[warn] {len(missing)} codici zona della popolazione assenti "
                  f"nelle sezioni {col_sez}: {missing} -> fallback quote comunali. "
                  f"Verifica --livello / --col-pop.")

    rng = np.random.default_rng(seed)
    frg_idx = pop.index[frg_mask]
    print(f"[pop] FRG da assegnare: {len(frg_idx):,}")

    for (zona, sesso), grp in pop.loc[frg_idx].groupby(["_zkey", "sesso"]):
        idx = grp.index.to_numpy().copy()
        rng.shuffle(idx)
        n_area = G.largest_remainder(len(idx), area_p.get((zona, sesso), fb[sesso]))
        start = 0
        for area, n_a in zip(AREAS, n_area):
            sub = idx[start:start + n_a]
            start += n_a
            if n_a == 0:
                continue
            pop.loc[sub, "area"] = area
            paesi, w = paese_p[(area, sesso)]
            n_paese = G.largest_remainder(n_a, w)
            s2 = 0
            for paese, n_p in zip(paesi, n_paese):
                pop.loc[sub[s2:s2 + n_p], "paese"] = paese
                s2 += n_p

    # ---------- validazione (prima del drop di _zkey) ----------
    frg = pop[pop["cittadinanza"] == "FRG"]
    print(f"\n[val] assegnati: {frg['paese'].notna().sum():,} / {len(frg):,} | "
          f"aree: {dict(frg['area'].value_counts())}")
    print("\n[val] top-10 paesi (campione):")
    print(frg["paese"].value_counts().head(10).to_string())
    gcol = "quartiere" if "quartiere" in pop.columns else (
        col_pop if col_pop in pop.columns else "_zkey")
    print(f"\n[val] paese più frequente nelle 5 unità ({gcol}) a maggior quota FRG:")
    qsh = (pop.groupby(gcol)["cittadinanza"]
           .apply(lambda s: (s == "FRG").mean()).sort_values(ascending=False))
    for q in qsh.head(5).index:
        top = frg[frg[gcol] == q]["paese"].value_counts()
        print(f"  {str(q):<22} quota FRG={qsh[q]:.3f}  top: {top.index[0]} ({top.iloc[0]})")

    # ---------- salvataggio (ora sì, senza _zkey) ----------
    out = os.path.join(cdir, out_name)
    pop.drop(columns="_zkey").to_csv(out, index=False)
    print(f"\n[done] -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Nazionalità two-stage (v2, multi-comune).")
    ap.add_argument("comune", help="codice ISTAT (es. 017029 Brescia, 037006 Bologna)")
    ap.add_argument("--anno", type=int, default=2024)
    ap.add_argument("--livello", choices=list(LIVELLI), default=None,
                    help="livello territoriale [default: dal registro di "
                         "gsp_common.py]")
    ap.add_argument("--col-pop", default="zona",
                    help="colonna della popolazione con i codici zona [default: zona]")
    ap.add_argument("--sezioni", default=None,
                    help="path CSV sezioni (default: <SUBMUN_DIR>/<nome>_sezioni_2023.csv)")
    ap.add_argument("--pop-file", default=None,
                    help="file popolazione da cui partire (default: auto-detect "
                         "K10C -> K9C -> K8C -> K7C -> K6C, il primo che esiste "
                         "in constraints_<anno>/)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None,
                    help="default: <file popolazione>_naz.csv")
    a = ap.parse_args()
    main(a.comune, a.anno, a.livello, a.col_pop, a.sezioni, a.pop_file, a.out, a.seed)
