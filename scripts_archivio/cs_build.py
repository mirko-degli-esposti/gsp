"""
cs_build.py — v2 — ConstraintSet modulare da dati censuari comunali e sub-comunali.

Livelli:
    K6C  sesso, eta, stato_civile, cittadinanza, istruzione, condizione   (v1)
    K7C  zona + K6C  (zona = 33 quartieri Brescia da sezioni di censimento)

Principio blocchi Z (lezione E/F applicata in anticipo): ogni tabella di zona
entra come P(zona | gruppo) x conteggi comunali del gruppo -> i margini sommati
sulle zone coincidono ESATTAMENTE coi blocchi comunali, per costruzione.

Assunzioni dichiarate:
    (1) distribuzione dell'attributo costante entro la classe censuaria
        (allocazione classe->bin sui pesi anagrafici a singolo anno) [v1]
    (2) quota di zona costante entro la classe quinquennale (Z1/Z3-under9)
        e entro la macro-classe (Z2) [v2]
    (3) P(zona | sesso, occupato) costante sui bin 15-64 (Z4: la tabella di
        zona non ha dettaglio d'eta' per gli occupati) [v2]
    Z4 vincola solo il lato 'occupato': lo split di zona dei non-occupati per
    categoria non e' esprimibile come pattern atomico senza assunzioni extra.

Uso:
    python cs_build.py 017029 --anno 2025                    # K6C
    python cs_build.py 017029 --anno 2024 --livello K7C      # K7C (zona 2023)
Output in constraints_<anno>/: cs_<LIV>.json, targets_<LIV>.json
Richiede per K7C: ~/progetti/gsp/data/comuni/<comune>/zona_2023/ (build_zona_tables.py)
"""

import os
import re
import sys
import glob
import json
import importlib
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Configurazione
# ----------------------------------------------------------------------
VAR_ORDER_K6 = ["sesso", "eta", "stato_civile", "cittadinanza", "istruzione", "condizione"]
VAR_ORDER_K7 = ["zona"] + VAR_ORDER_K6

DEFAULT_BINS = ["0-8", "9-14", "15-24", "25-34", "35-49", "50-64", "65-74", "75+"]

CAT_ORDER = {
    "sesso": ["M", "F"],
    "stato_civile": ["celibe_nubile", "coniugato_unito", "divorziato_sciolto", "vedovo"],
    "cittadinanza": ["ITL", "FRG"],
    "istruzione": ["nessun_titolo", "elementare", "media", "diploma",
                   "laurea_o_its", "post_laurea"],
}

STRUCTURAL_FILL = {
    "istruzione": ("nessun_titolo", 9),
    "condizione": ("non_applicabile", 15),
}

REPO_CANDIDATES = ["~/progetti/maxent-popsynth-pcd", "/content/maxent-popsynth-pcd"]


def import_constraint_set():
    for base in REPO_CANDIDATES:
        base = os.path.expanduser(base)
        hits = glob.glob(f"{base}/**/constraint_set.py", recursive=True)
        if hits:
            sys.path.insert(0, os.path.dirname(hits[0]))
            return importlib.import_module("constraint_set").ConstraintSet
    raise ImportError("constraint_set.py non trovato: clonare il repo in ~/progetti/")


# ----------------------------------------------------------------------
# Età
# ----------------------------------------------------------------------
def parse_bin(lbl: str):
    m = re.fullmatch(r"(\d+)-(\d+)", lbl)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r"(\d+)\+", lbl)
    if m:
        return int(m.group(1)), 199
    raise ValueError(f"bin non riconosciuto: {lbl}")

def parse_class(code: str):
    m = re.fullmatch(r"Y(\d+)-(\d+)", str(code))
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r"Y_GE(\d+)", str(code))
    if m:
        return int(m.group(1)), 199
    raise ValueError(f"classe non riconosciuta: {code}")

class AgeBins:
    def __init__(self, labels, min_age=0, max_age=199):
        self.labels, self.bounds = [], {}
        for lbl in labels:
            lo, hi = parse_bin(lbl)
            lo2, hi2 = max(lo, min_age), min(hi, max_age)
            if lo2 <= hi2:
                self.labels.append(lbl)
                self.bounds[lbl] = (lo2, hi2)

    def bin_of(self, age: int):
        for lbl, (lo, hi) in self.bounds.items():
            if lo <= age <= hi:
                return lbl
        return None

def quinq_of(age: int) -> str:
    lo = min((age // 5) * 5, 75)
    return "Y_GE75" if lo == 75 else f"Y{lo}-{lo+4}"

def macro_of(age: int) -> str:
    return "Y0-14" if age <= 14 else ("Y15-64" if age <= 64 else "Y_GE65")


# ----------------------------------------------------------------------
# Input
# ----------------------------------------------------------------------
def load_inputs(cdir: str):
    f = lambda n: pd.read_csv(os.path.join(cdir, n))
    return {
        "c1": f("c1_sex_age_marital.csv"),
        "c2": f("c2_sex_age_citizenship.csv"),
        "c3": f("c3_sex_ageclass_edu.csv"),
        "c4": f("c4_sex_ageclass_condprof.csv"),
        "c5": f("c5_edu_citizenship.csv"),
        "c6": f("c6_condprof_citizenship.csv"),
    }

def load_zona(zdir: str):
    f = lambda n: pd.read_csv(os.path.join(zdir, n), dtype={"zona": str})
    return {
        "z1": f("z1_zona_sesso_eta5.csv"),
        "z2": f("z2_zona_sesso_macroeta_citt.csv"),
        "z3": f("z3_zona_sesso_istruzione.csv"),
        "z4": f("z4_zona_sesso_occup.csv"),
        "nomi": f("zona_nomi.csv"),
    }

CONDPROF_RENAME = {
    "occupato": "occupato",
    "in cerca di occupazione": "in_cerca",
    "casalinga/o": "casalinga",
    "studente/ssa": "studente",
    "percettore/rice di una o più pensioni per effetto di attività lavorativa "
    "precedente o di redditi da capitale": "percettore_pensioni",
    "in altra condizione": "altra_condizione",
}

def norm_condprof(s: pd.Series) -> pd.Series:
    out = s.map(CONDPROF_RENAME)
    unknown = s[out.isna()].unique()
    if len(unknown):
        print(f"[warn] etichette condprof non mappate (tenute com'erano): {list(unknown)}")
    return out.fillna(s)


# ----------------------------------------------------------------------
# Primitive comunali (v1, invariate)
# ----------------------------------------------------------------------
def block_exact(df: pd.DataFrame, colmap: dict, bins: AgeBins) -> pd.DataFrame:
    t = df.rename(columns=colmap).copy()
    t["eta"] = t["eta"].astype(int).map(bins.bin_of)
    t = t.dropna(subset=["eta"])
    keys = [("eta" if k == "eta" else k) for k in colmap.values()]
    return t.groupby(keys)["count"].sum().reset_index()

def block_from_class(df: pd.DataFrame, attr_var: str, anag_w: pd.DataFrame,
                     bins: AgeBins) -> pd.DataFrame:
    d = df.rename(columns={"attr": attr_var, "age_class": "cls"}).copy()
    cls_bounds = {c: parse_class(c) for c in d["cls"].unique()}
    tot = d.groupby(["sex", "cls"])[["count"]].transform("sum")["count"]
    d["share"] = d["count"] / tot.replace(0, np.nan)
    rows = []
    for (sex, cls), g in d.groupby(["sex", "cls"]):
        lo, hi = cls_bounds[cls]
        w = anag_w[(anag_w["sex"] == sex) & (anag_w["age"].between(lo, hi))]
        for _, arow in w.iterrows():
            b = bins.bin_of(int(arow["age"]))
            if b is None:
                continue
            for _, r in g.iterrows():
                rows.append((sex, b, r[attr_var], r["share"] * arow["anag"]))
    out = pd.DataFrame(rows, columns=["sesso", "eta", attr_var, "count"])
    return out.groupby(["sesso", "eta", attr_var])["count"].sum().reset_index()


# ----------------------------------------------------------------------
# Primitive di zona (v2): P(zona | gruppo) x conteggi comunali
# ----------------------------------------------------------------------
def zona_shares(df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    """P(zona | group_cols) dalla tabella di zona (colonne group_cols+zona+count)."""
    g = df.groupby(group_cols + ["zona"])["count"].sum().reset_index()
    tot = g.groupby(group_cols)["count"].transform("sum")
    g["share"] = g["count"] / tot.replace(0, np.nan)
    return g[group_cols + ["zona", "share"]].dropna(subset=["share"])

def expand_z1(z1: pd.DataFrame, anag_w: pd.DataFrame) -> pd.DataFrame:
    """(zona, sesso, età singola, count): quote quinquennali x anagrafe.
    Base per il blocco Z1 e per le quote under-9 di Z3."""
    sh = zona_shares(z1.rename(columns={"eta5": "cls"}), ["sesso", "cls"])
    a = anag_w.rename(columns={"sex": "sesso"}).copy()
    a["cls"] = a["age"].map(quinq_of)
    t = a.merge(sh, on=["sesso", "cls"], how="left")
    miss = t["share"].isna().sum()
    if miss:
        print(f"[warn] Z1: {miss} celle anagrafiche senza quota di zona (share NaN)")
    t["count"] = t["share"] * t["anag"]
    return t.dropna(subset=["count"])[["zona", "sesso", "age", "count"]]

def ipf_2d(M: pd.DataFrame, row_t: pd.Series, col_t: pd.Series,
           iters: int = 300, tol: float = 1e-10) -> pd.DataFrame:
    """IPF su matrice piccola: margini riga/colonna esatti. Init +1e-9 per supporto."""
    A = M.values.astype(float) + 1e-9
    r = row_t.reindex(M.index).fillna(0).values
    c = col_t.reindex(M.columns).fillna(0).values
    for _ in range(iters):
        rs = A.sum(1); rs[rs == 0] = 1; A *= (r / rs)[:, None]
        cs_ = A.sum(0); cs_[cs_ == 0] = 1; A *= (c / cs_)[None, :]
        if max(np.abs(A.sum(1) - r).max(), np.abs(A.sum(0) - c).max()) < tol:
            break
    return pd.DataFrame(A, index=M.index, columns=M.columns)

# ----------------------------------------------------------------------
# Builder
# ----------------------------------------------------------------------
class CSBuilder:
    def __init__(self, var_order, ConstraintSet):
        self.var_order = list(var_order)
        self.CS = ConstraintSet
        self.categories = {v: [] for v in var_order}
        self.blocks = []

    def register_categories(self, var, values):
        pref = CAT_ORDER.get(var, [])
        seen = [c for c in pref if c in set(values)]
        extra = sorted(set(values) - set(seen))
        self.categories[var] = seen + extra

    def add_block(self, name, df, fonte):
        attrs = [c for c in df.columns if c != "count"]
        for v in attrs:
            vals = set(self.categories[v]) | set(df[v].unique())
            self.register_categories(v, vals)
        self.blocks.append((name, attrs, df.copy(), fonte))

    def get_block(self, name):
        for n, attrs, df, _ in self.blocks:
            if n == name:
                return df
        raise KeyError(name)

    def build(self, pop_size):
        idx = {v: i for i, v in enumerate(self.var_order)}
        cat_idx = {v: {c: i for i, c in enumerate(cats)}
                   for v, cats in self.categories.items()}
        cs = self.CS([len(self.categories[v]) for v in self.var_order])
        for name, attrs, df, _ in self.blocks:
            ai = [idx[v] for v in attrs]
            for _, r in df.iterrows():
                vals = [cat_idx[v][r[v]] for v in attrs]
                cs.add(ai, vals, float(r["count"]) / pop_size)
        return cs

    def spec(self, cs, pop_size, livello):
        return {
            "livello": livello,
            "vars": self.var_order,
            "categories": {v: self.categories[v] for v in self.var_order},
            "domain_sizes": [len(self.categories[v]) for v in self.var_order],
            "pop_size": int(round(pop_size)),
            "constraints": [
                {"attrs": [int(a) for a in attrs], "vals": [int(v) for v in vals],
                 "alpha": float(al)}
                for attrs, vals, al in zip(cs.attrs_list, cs.vals_list, cs.alphas)
            ],
        }

    def targets(self, pop_size):
        out = {"vars": self.var_order,
               "categories": {v: self.categories[v] for v in self.var_order},
               "pop_size": int(round(pop_size)), "blocks": {}}
        for name, attrs, df, fonte in self.blocks:
            vals = {"|".join(str(r[v]) for v in attrs): round(float(r["count"]) / pop_size, 6)
                    for _, r in df.iterrows()}
            out["blocks"][name] = {"attrs": attrs, "fonte": fonte,
                                   "target": {"attrs": attrs, "values": vals}}
        return out


# ----------------------------------------------------------------------
def main(comune, anno, min_age, max_age, bins_labels, livello):
    ConstraintSet = import_constraint_set()
    cdir = os.path.expanduser(f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")
    T = load_inputs(cdir)
    bins = AgeBins(bins_labels, min_age, max_age)
    var_order = VAR_ORDER_K7 if livello == "K7C" else VAR_ORDER_K6
    print(f"[cs] livello {livello} | universo età [{min_age},{max_age}], bin: {bins.labels}")
    if livello == "K7C" and min_age > 0:
        print("[warn] K7C con min_age>0: le quote di zona sono su popolazione intera")

    c1 = T["c1"][T["c1"]["age"].between(min_age, max_age)].copy()
    pop = c1["count"].sum()
    anag_w = c1.groupby(["sex", "age"])["count"].sum().reset_index(name="anag")
    print(f"[cs] popolazione universo: {pop:,.0f}")

    B = CSBuilder(var_order, ConstraintSet)

    # ---------------- blocchi comunali A-F, S (v1) ----------------
    B.add_block("A_sesso_eta_statociv",
                block_exact(c1, {"sex": "sesso", "age": "eta",
                                 "marital": "stato_civile"}, bins),
                f"anagrafe 1/1/{anno} (esatto)")
    c2 = T["c2"][T["c2"]["age"].between(min_age, max_age)]
    B.add_block("B_sesso_eta_cittad",
                block_exact(c2, {"sex": "sesso", "age": "eta",
                                 "citizenship": "cittadinanza"}, bins),
                f"censimento {anno-1} (riconciliato, esatto)")
    B.add_block("C_sesso_eta_istruz",
                block_from_class(T["c3"], "istruzione", anag_w, bins),
                f"censimento {anno-1}, allocazione su anagrafe")
    c4 = T["c4"].copy(); c4["attr"] = norm_condprof(c4["attr"])
    B.add_block("D_sesso_eta_condiz",
                block_from_class(c4, "condizione", anag_w, bins),
                f"censimento {anno-1}, allocazione su anagrafe")
    for name, key, var, fix in [("E_istruz_cittad", "c5", "istruzione", None),
                                ("F_condiz_cittad", "c6", "condizione", norm_condprof)]:
        d = T[key].rename(columns={"citizenship": "cittadinanza", "attr": var}).copy()
        if fix:
            d[var] = fix(d[var])
        u_min = STRUCTURAL_FILL[var][1] if var in STRUCTURAL_FILL else 0
        u_pop = c1[c1["age"] >= max(u_min, min_age)]["count"].sum()
        d["count"] = d["count"] * u_pop / d["count"].sum()
        if var in STRUCTURAL_FILL and min_age < STRUCTURAL_FILL[var][1]:
            fill_cat, age_from = STRUCTURAL_FILL[var]
            extra = (T["c2"][(T["c2"]["age"] >= min_age) & (T["c2"]["age"] < age_from)]
                     .groupby("citizenship")["count"].sum().reset_index()
                     .rename(columns={"citizenship": "cittadinanza"}))
            extra[var] = fill_cat
            d = pd.concat([d, extra[["cittadinanza", var, "count"]]], ignore_index=True)
            d = d.groupby(["cittadinanza", var], as_index=False)["count"].sum()
        B.add_block(name, d[["cittadinanza", var, "count"]],
                    f"censimento {anno-1}, riscalato a universo {max(u_min, min_age)}+")

    for var, (fill_cat, age_from) in STRUCTURAL_FILL.items():
        below = c1[c1["age"] < age_from]
        if len(below) and min_age < age_from:
            g = below.copy()
            g["eta"] = g["age"].map(bins.bin_of)
            g = g.dropna(subset=["eta"]).groupby(["eta"])["count"].sum().reset_index()
            g[var] = fill_cat
            B.add_block(f"S_{var}_under{age_from}", g[["eta", var, "count"]],
                        f"strutturale: {var}={fill_cat} sotto i {age_from} anni")

    # ---------------- blocchi di zona Z1-Z4 (v2, solo K7C) ----------------
    nomi = None
    if livello == "K7C":
        zdir = os.path.expanduser(f"~/progetti/gsp/data/comuni/{comune}/zona_2023")
        Z = load_zona(zdir)
        fonte_z = f"sezioni censimento {anno-1} (quote, armonizzate IPF) x conteggi comunali"

        # Z1: backbone (zona,sesso,eta) = P(zona|sesso,quinq) x anagrafe
        e1 = expand_z1(Z["z1"], anag_w)
        z1b = e1.copy()
        z1b["eta"] = z1b["age"].astype(int).map(bins.bin_of)
        z1b = z1b.dropna(subset=["eta"]).groupby(
            ["zona", "sesso", "eta"])["count"].sum().reset_index()
        B.add_block("Z1_zona_sesso_eta", z1b, fonte_z)

        # Z2 init: P(zona|sesso,macro,citt) x C2, poi IPF per (sesso,bin):
        #   righe = Z1(zona) , colonne = blocco B comunale (cittadinanza)
        sh2 = zona_shares(Z["z2"].rename(columns={"macroeta": "cls"}),
                          ["sesso", "cls", "cittadinanza"])
        b2 = c2.rename(columns={"sex": "sesso", "citizenship": "cittadinanza"}).copy()
        b2["cls"] = b2["age"].map(macro_of)
        t2 = b2.merge(sh2, on=["sesso", "cls", "cittadinanza"], how="left")
        t2["cz"] = t2["share"] * t2["count"]
        t2["eta"] = t2["age"].astype(int).map(bins.bin_of)
        z2_init = (t2.dropna(subset=["cz", "eta"])
                   .groupby(["zona", "sesso", "eta", "cittadinanza"])["cz"]
                   .sum().reset_index(name="count"))
        Bblk = B.get_block("B_sesso_eta_cittad")
        parts = []
        for (s, e), grp in z2_init.groupby(["sesso", "eta"]):
            M = grp.pivot(index="zona", columns="cittadinanza", values="count").fillna(0)
            row_t = z1b[(z1b.sesso == s) & (z1b.eta == e)].set_index("zona")["count"]
            col_t = Bblk[(Bblk.sesso == s) & (Bblk.eta == e)] \
                .set_index("cittadinanza")["count"]
            M = M.reindex(index=row_t.index, columns=col_t.index).fillna(0)
            A = ipf_2d(M, row_t, col_t)
            parts.append(A.stack().rename("count").reset_index()
                         .assign(sesso=s, eta=e))
        z2b = pd.concat(parts, ignore_index=True)[
            ["zona", "sesso", "eta", "cittadinanza", "count"]]
        B.add_block("Z2_zona_sesso_eta_cittad", z2b, fonte_z)

        # Z3 init: 9+ P(zona|sesso,edu5) x C-aggregato + under-9 da Z1;
        #   IPF per sesso: righe = Z1 totali (zona), colonne = totali comunali edu6
        EDU6TO5 = {"laurea_o_its": "terziario", "post_laurea": "terziario"}
        sh3 = zona_shares(Z["z3"].rename(columns={"istruzione5": "edu5"}),
                          ["sesso", "edu5"])
        cblk = B.get_block("C_sesso_eta_istruz")
        com6 = cblk.groupby(["sesso", "istruzione"])["count"].sum().reset_index()
        com6["edu5"] = com6["istruzione"].map(lambda x: EDU6TO5.get(x, x))
        t3 = com6.merge(sh3, on=["sesso", "edu5"], how="left")
        t3["cz"] = t3["share"] * t3["count"]
        z3a = t3.dropna(subset=["cz"])[["zona", "sesso", "istruzione", "cz"]] \
                .rename(columns={"cz": "count"})
        u9 = e1[e1["age"] < 9].groupby(["zona", "sesso"])["count"].sum().reset_index()
        u9["istruzione"] = "nessun_titolo"
        z3_init = pd.concat([z3a, u9[["zona", "sesso", "istruzione", "count"]]],
                            ignore_index=True) \
            .groupby(["zona", "sesso", "istruzione"])["count"].sum().reset_index()
        parts = []
        for s, grp in z3_init.groupby("sesso"):
            M = grp.pivot(index="zona", columns="istruzione", values="count").fillna(0)
            row_t = z1b[z1b.sesso == s].groupby("zona")["count"].sum()
            col_t = grp.groupby("istruzione")["count"].sum()
            M = M.reindex(index=row_t.index, columns=col_t.index).fillna(0)
            A = ipf_2d(M, row_t, col_t)
            parts.append(A.stack().rename("count").reset_index().assign(sesso=s))
        z3b = pd.concat(parts, ignore_index=True)[
            ["zona", "sesso", "istruzione", "count"]]
        B.add_block("Z3_zona_sesso_istruz", z3b, fonte_z)

        # Z4: occupato per (sesso,bin 15-64); margine su zona = D, cap = Z1
        sh4 = zona_shares(Z["z4"][Z["z4"]["occup"] == "occupato"], ["sesso"])
        dblk = B.get_block("D_sesso_eta_condiz")
        bins_1564 = [b for b, (lo, hi) in bins.bounds.items() if lo >= 15 and hi <= 64]
        docc = dblk[(dblk["condizione"] == "occupato") & (dblk["eta"].isin(bins_1564))]
        rows4, n_cap = [], 0
        for (s, e), grp in docc.groupby(["sesso", "eta"]):
            target = float(grp["count"].sum())
            sh = sh4[sh4.sesso == s].set_index("zona")["share"]
            cap = z1b[(z1b.sesso == s) & (z1b.eta == e)].set_index("zona")["count"] \
                .reindex(sh.index).fillna(0)
            v = (sh * target).values.copy()
            capv = cap.values
            for _ in range(60):
                over = v > capv
                if not over.any():
                    break
                n_cap += int(over.sum())
                excess = float((v[over] - capv[over]).sum())
                v[over] = capv[over]
                free = ~over
                if v[free].sum() > 0:
                    v[free] += excess * v[free] / v[free].sum()
            for z, val in zip(sh.index, v):
                rows4.append({"zona": z, "sesso": s, "eta": e,
                              "condizione": "occupato", "count": val})
        if n_cap:
            print(f"[warn] Z4: {n_cap} celle cappate su Z1 e ridistribuite")
        z4b = pd.DataFrame(rows4)
        B.add_block("Z4_zona_sesso_eta_occ", z4b, fonte_z)

        # ---- audit Z-vs-Z (la lezione generalizzata) ----
        d21 = (z2b.groupby(["zona", "sesso", "eta"])["count"].sum()
               - z1b.set_index(["zona", "sesso", "eta"])["count"]).abs().max()
        d31 = (z3b.groupby(["zona", "sesso"])["count"].sum()
               - z1b.groupby(["zona", "sesso"])["count"].sum()).abs().max()
        print(f"[audit] Z2 somma citt vs Z1: max|diff| = {d21:.2e}")
        print(f"[audit] Z3 somma edu  vs Z1: max|diff| = {d31:.2e}")

        nomi = dict(zip(Z["nomi"]["zona"], Z["nomi"]["nome"]))

    # ---------------- build + validazione ----------------
    cs = B.build(pop)
    print(cs.summary())
    print("\n[cs] somme per blocco (attese ~1 per blocchi completi):")
    for name, attrs, df, _ in B.blocks:
        print(f"  {name:<26} {'x'.join(attrs):<44} somma={df['count'].sum()/pop:.4f}")

    if livello == "K7C":
        # audit margini: Z sommati sulle zone vs blocchi comunali
        for zname, cname, keys in [
            ("Z1_zona_sesso_eta", "A_sesso_eta_statociv", ["sesso", "eta"]),
            ("Z2_zona_sesso_eta_cittad", "B_sesso_eta_cittad",
             ["sesso", "eta", "cittadinanza"]),
        ]:
            zm = B.get_block(zname).groupby(keys)["count"].sum()
            cm = B.get_block(cname).groupby(keys)["count"].sum()
            diff = (zm - cm).abs().max()
            print(f"[audit] margine {zname} vs {cname}: max|diff| = {diff:.6f}")

    spec = B.spec(cs, pop, livello)
    if livello == "K7C":
        spec["zona_nomi"] = nomi
    with open(os.path.join(cdir, f"cs_{livello}.json"), "w") as f:
        json.dump(spec, f)
    with open(os.path.join(cdir, f"targets_{livello}.json"), "w") as f:
        json.dump(B.targets(pop), f, ensure_ascii=False, indent=1)
    print(f"\n[done] cs_{livello}.json: m={len(spec['constraints'])} vincoli, "
          f"|X|={int(np.prod(spec['domain_sizes']))}  -> {cdir}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("Uso: python cs_build.py <comune> [--anno 2025] "
                 "[--min-age 0] [--max-age 199] [--livello K6C|K7C]")
    comune = args[0]
    getv = lambda k, d: int(args[args.index(k) + 1]) if k in args else d
    livello = args[args.index("--livello") + 1] if "--livello" in args else "K6C"
    main(comune, getv("--anno", 2025), getv("--min-age", 0),
         getv("--max-age", 199), DEFAULT_BINS, livello)
