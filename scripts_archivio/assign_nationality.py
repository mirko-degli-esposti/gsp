"""
assign_nationality.py — nazionalità two-stage sulla popolazione K7C (livello 1).

Gerarchia:  (2a) area UE/EXTRA_UE ~ P(area | zona, sesso)   [sezioni ST17/18/20/21]
            (2b) paese            ~ P(paese | area, sesso)  [comunale, censimento 2023]
Allocazione ESATTA (largest remainder) a ogni livello: i conteggi di gruppo
riproducono i target attesi all'unità, non solo in media.

ITL -> paese = 'Italia'. Output: popolazione_K7C_naz.csv (colonne + area, paese).

Assunzioni dichiarate:
    (4) paese ⊥ zona | (area, sesso): la struttura territoriale entra al
        livello area (UE/extra-UE per quartiere), il dettaglio paese è
        condizionato solo ad area e sesso (il dato non consente di più).

Uso:  python assign_nationality.py 017029 --anno 2024
"""

import os
import sys
import numpy as np
import pandas as pd

#SEZ_CSV = os.path.expanduser("~/progetti/gsp/data/submun/brescia_sezioni_2023.csv")
SEZ_CSV = os.path.expanduser("~/progetti/gsp/data/submun/bologna_sezioni_2023.csv")
EU27 = {  # etichette italiane ISTAT, Italia esclusa
    "austria", "belgio", "bulgaria", "cechia", "repubblica ceca", "cipro",
    "croazia", "danimarca", "estonia", "finlandia", "francia", "germania",
    "grecia", "irlanda", "lettonia", "lituania", "lussemburgo", "malta",
    "paesi bassi", "polonia", "portogallo", "romania", "slovacchia",
    "slovenia", "spagna", "svezia", "ungheria",
}

AGGREG_RE = ("tutte le voci|unione europea|countries|europ|africa|america|asia|"
             "oceania|total|apolidi|aggregat|eea|efta")


def largest_remainder(n: int, shares: np.ndarray) -> np.ndarray:
    """Alloca n unità intere secondo shares (somma 1), largest remainder."""
    if n == 0 or shares.sum() == 0:
        return np.zeros(len(shares), dtype=int)
    exp = n * shares / shares.sum()
    base = np.floor(exp).astype(int)
    resto = n - base.sum()
    if resto > 0:
        order = np.argsort(-(exp - base))
        base[order[:resto]] += 1
    return base


def main(comune, anno):
    cdir = os.path.expanduser(f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")
    cens_anno = anno - 1

    # ---------- (2a) P(area | zona, sesso) dalle sezioni ----------
    b = pd.read_csv(SEZ_CSV)
    b["zona"] = b["COM_ASC1"].astype(int).astype(str)
    z5 = b.groupby("zona")[["ST17", "ST18", "ST20", "ST21"]].sum()
    area_p = {}
    for zona, r in z5.iterrows():
        area_p[(zona, "M")] = np.array([r["ST17"], r["ST20"]], dtype=float)
        area_p[(zona, "F")] = np.array([r["ST18"], r["ST21"]], dtype=float)
    AREAS = ["UE", "EXTRA_UE"]
    print(f"[2a] quote area per (zona,sesso): {len(area_p)} gruppi | "
          f"UE tot={z5[['ST17','ST18']].values.sum():,.0f} "
          f"extraUE tot={z5[['ST20','ST21']].values.sum():,.0f}")

    # ---------- (2b) P(paese | area, sesso) comunale ----------
    d = pd.read_csv(os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/cens_stranieri_paesi_decoded.csv"))
    d = d[(d["TIME_PERIOD"] == cens_anno) & (d["GENDER"].isin(["M", "F"]))].copy()
    lab = d["AREA_CONTRY_CITIZEN_label"].astype(str)
    d = d[~lab.str.lower().str.contains(AGGREG_RE, regex=True) & (d["OBS_VALUE"] > 0)]
    d["paese"] = d["AREA_CONTRY_CITIZEN_label"].astype(str)
    d["area"] = d["paese"].str.lower().map(
        lambda s: "UE" if any(s == e or s.startswith(e) for e in EU27) else "EXTRA_UE")
    ue_found = sorted(d[d.area == "UE"]["paese"].unique())
    print(f"[2b] paesi: {d['paese'].nunique()} | classificati UE: {len(ue_found)}")
    print(f"     UE trovati: {ue_found}")
    cp = d.groupby(["area", "GENDER", "paese"])["OBS_VALUE"].sum().reset_index()
    paese_p = {}
    for (area, sex), g in cp.groupby(["area", "GENDER"]):
        paese_p[(area, sex)] = (g["paese"].tolist(),
                                g["OBS_VALUE"].values.astype(float))

    # sanity incrociata: quote sesso per area, comunale vs sezioni
    for area, st_m, st_f in [("UE", "ST17", "ST18"), ("EXTRA_UE", "ST20", "ST21")]:
        com = cp[cp.area == area].groupby("GENDER")["OBS_VALUE"].sum()
        sez = {"M": z5[st_m].sum(), "F": z5[st_f].sum()}
        print(f"[check] {area}: comunale M/F {com.get('M',0):,.0f}/{com.get('F',0):,.0f}"
              f"  sezioni M/F {sez['M']:,.0f}/{sez['F']:,.0f}")

    # ---------- assegnazione sulla popolazione ----------
    pop = pd.read_csv(os.path.join(cdir, "popolazione_K7C.csv"),
                      dtype={"zona": str})
    pop["area"] = pd.NA
    pop["paese"] = pd.NA
    pop.loc[pop["cittadinanza"] == "ITL", "paese"] = "Italia"

    rng = np.random.default_rng(42)
    frg_idx = pop.index[pop["cittadinanza"] == "FRG"]
    print(f"[pop] FRG da assegnare: {len(frg_idx):,}")

    for (zona, sesso), grp in pop.loc[frg_idx].groupby(["zona", "sesso"]):
        idx = grp.index.to_numpy().copy()
        rng.shuffle(idx)
        n_area = largest_remainder(len(idx), area_p.get((zona, sesso),
                                                        np.array([1.0, 1.0])))
        start = 0
        for area, n_a in zip(AREAS, n_area):
            sub = idx[start:start + n_a]
            start += n_a
            if n_a == 0:
                continue
            pop.loc[sub, "area"] = area
            paesi, w = paese_p[(area, sesso)]
            n_paese = largest_remainder(n_a, w)
            s2 = 0
            for paese, n_p in zip(paesi, n_paese):
                pop.loc[sub[s2:s2 + n_p], "paese"] = paese
                s2 += n_p

    out = os.path.join(cdir, "popolazione_K7C_naz.csv")
    pop.to_csv(out, index=False)

    # ---------- validazione ----------
    frg = pop[pop["cittadinanza"] == "FRG"]
    print(f"\n[val] assegnati: {frg['paese'].notna().sum():,} / {len(frg):,} | "
          f"aree: {dict(frg['area'].value_counts())}")
    print("\n[val] top-10 paesi (campione):")
    print(frg["paese"].value_counts().head(10).to_string())
    print("\n[val] paese più frequente nei 5 quartieri a maggior quota straniera:")
    top_q = frg["quartiere"].value_counts(normalize=False)
    qsh = (pop.groupby("quartiere")["cittadinanza"]
           .apply(lambda s: (s == "FRG").mean()).sort_values(ascending=False))
    for q in qsh.head(5).index:
        top = frg[frg["quartiere"] == q]["paese"].value_counts()
        print(f"  {q:<22} quota FRG={qsh[q]:.3f}  top: {top.index[0]} ({top.iloc[0]})")
    print(f"\n[done] -> {out}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("Uso: python assign_nationality.py <comune> [--anno 2024]")
    comune = args[0]
    anno = int(args[args.index("--anno") + 1]) if "--anno" in args else 2024
    main(comune, anno)
