"""
build_constraints.py — v1 — dal set di tavole comunali ISTAT al constraint set per GibbsPCD.

Uso:
    python build_constraints.py 017029 --anno 2025

Convenzioni:
    --anno N  = ancoraggio anagrafico all'1/1/N (TIME_PERIOD=N nella tavola anagrafica);
                lo strato censuario usa TIME_PERIOD=N-1 (fotografia ~ottobre N-1).

Input:  ~/progetti/gsp/data/comuni/<comune>/*_decoded.csv   (da fetch_comune.py)
Output: ~/progetti/gsp/data/comuni/<comune>/constraints_<anno>/
    c1_sex_age_marital.csv        vincolo HARD  (anagrafe, conteggi esatti)
    c2_sex_age_citizenship.csv    vincolo SOFT  (censimento -> condizionale su spine anagrafica)
    c3_sex_ageclass_edu.csv       vincolo SOFT  (idem, classi d'età censuarie)
    c4_sex_ageclass_condprof.csv  vincolo SOFT  (idem)
    c5_edu_citizenship.csv        vincolo SOFT
    c6_condprof_citizenship.csv   vincolo SOFT
    nationality_conditional.csv   P(paese | straniero)  (two-stage, fuori dal MaxEnt)
    manifest.json                 descrizione vincoli + sigma arrotondamento per tavola
    report.md                     consistenza anagrafe<->censimento e arrotondamenti

Filosofia: il censimento entra come distribuzione condizionale applicata ai conteggi
anagrafici (riscalatura per gruppo), così i marginali demografici restano esatti e
lo strato socio-economico eredita la struttura censuaria con incertezza esplicita.

Note v1 (lezioni dal primo run su Brescia 017029):
    - il dato censuario SDMX è in stime NON arrotondate (decimali), internamente
      additive: sigma di arrotondamento ~0; l'incertezza vera sta nel raccordo
      anagrafe<->censimento (report.md)
    - codice stranieri nel dato: FRGAPO (stranieri/apolidi), non FRG; normalizzato
      a FRG in uscita per stabilità dello schema
    - gerarchia condprof: 22 = 1+12 (forze di lavoro); 23 = 4+5+7+24 (non forze
      di lavoro); gli aggregati vengono scartati solo se il dettaglio è presente
"""

import os
import re
import sys
import json
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Collassi (verificare i mapping stampati a video al primo run)
# ----------------------------------------------------------------------
MARITAL_COLLAPSE = {          # 7 -> 4, unioni civili assimilate
    "1": "celibe_nubile",
    "2": "coniugato_unito", "15": "coniugato_unito",
    "3": "divorziato_sciolto", "17": "divorziato_sciolto",
    "4": "vedovo", "16": "vedovo",
}

def edu_collapse(label: str) -> str | None:
    """10 -> 6 livelli, guidato dalle etichette (ordine dei check rilevante)."""
    s = str(label).lower()
    if "totale" in s:
        return None
    if "its" in s or "primo livello" in s:
        return "laurea_o_its"
    if "secondo livello" in s or "dottorato" in s:
        return "post_laurea"
    if "nessun" in s or "analfabeta" in s or "alfabeta privo" in s:
        return "nessun_titolo"
    if "elementare" in s:
        return "elementare"
    if "media inferiore" in s or "avviamento" in s:
        return "media"
    if "diploma" in s or "maturit" in s or "secondaria superiore" in s or "qualifica" in s:
        return "diploma"
    return f"?{label}"          # non riconosciuto: emerge nel print di verifica

SEX_NORM = {"1": "M", "2": "F", "M": "M", "F": "F"}
CONDPROF_AGGREGATES = {"99", "ALL"}   # '22'/'23' gestiti dinamicamente sotto
CONDPROF_NONLF_DETAIL = {"4", "5", "7", "24"}   # dettaglio di 23 (non forze di lavoro)


# ----------------------------------------------------------------------
# Utilità
# ----------------------------------------------------------------------
def parse_age(code: str):
    """'Y7'->(7,7)  'Y9-24'->(9,24)  'Y_GE65'->(65,199)  altrimenti None."""
    code = str(code)
    m = re.fullmatch(r"Y(\d+)", code)
    if m:
        a = int(m.group(1)); return (a, a)
    m = re.fullmatch(r"Y(\d+)-(\d+)", code)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = re.fullmatch(r"Y_GE(\d+)", code)
    if m:
        return (int(m.group(1)), 199)
    return None

def elementary_classes(codes):
    """Scarta i codici classe che contengono interamente un'altra classe (aggregati)."""
    parsed = {c: parse_age(c) for c in codes}
    parsed = {c: p for c, p in parsed.items() if p}
    out = []
    for c, (lo, hi) in parsed.items():
        contains_other = any(o != c and lo <= plo and phi <= hi
                             for o, (plo, phi) in parsed.items())
        if not contains_other:
            out.append(c)
    return sorted(out, key=lambda c: parsed[c][0])

def load(comune_dir: str, name: str) -> pd.DataFrame:
    path = os.path.join(comune_dir, f"{name}_decoded.csv")
    if not os.path.exists(path):
        sys.exit(f"Manca {path}: eseguire prima fetch_comune.py")
    return pd.read_csv(path)

def pick_year(df: pd.DataFrame, year: int, name: str) -> pd.DataFrame:
    years = sorted(df["TIME_PERIOD"].unique())
    if year not in years:
        sys.exit(f"{name}: TIME_PERIOD={year} assente; disponibili {years}")
    return df[df["TIME_PERIOD"] == year].copy()

def rounding_sigma(df, group_cols, attr_col, total_code, value="OBS_VALUE"):
    """Residui totale_pubblicato - somma_modalità per gruppo -> (sigma, residui)."""
    el = df[df[attr_col] != total_code]
    tot = df[df[attr_col] == total_code]
    if tot.empty:
        return None, pd.DataFrame()
    s = el.groupby(group_cols)[value].sum().rename("somma_modalita")
    t = tot.groupby(group_cols)[value].sum().rename("totale_pubblicato")
    cmp_ = pd.concat([s, t], axis=1).dropna()
    cmp_["residuo"] = cmp_["totale_pubblicato"] - cmp_["somma_modalita"]
    sigma = float(cmp_["residuo"].std(ddof=1)) if len(cmp_) > 1 else float(abs(cmp_["residuo"]).max() or 0)
    return sigma, cmp_.reset_index()

def condprof_drop_set(codes: set) -> set:
    """Aggregati condprof da scartare, in base al dettaglio presente nel dato."""
    drop = set(CONDPROF_AGGREGATES)
    if {"1", "12"} <= codes:
        drop.add("22")                      # 'forze di lavoro' = aggregato di 1+12
    if codes & CONDPROF_NONLF_DETAIL:
        drop.add("23")                      # 'non forze di lavoro' = aggregato del dettaglio
    return drop

def frg_normalize_code(cit_values: set) -> str | None:
    """Codice stranieri effettivo nel dato (FRG o FRGAPO), None se assente."""
    return next((c for c in ("FRG", "FRGAPO") if c in cit_values), None)

def apply_conditional(anag_groups: pd.DataFrame, cens: pd.DataFrame,
                      group_cols, attr_col, value="OBS_VALUE"):
    """Quote censuarie per gruppo x anag conteggi di gruppo -> vincolo riscalato.
    anag_groups: colonne group_cols + 'anag_total'."""
    g = cens.groupby(group_cols + [attr_col])[value].sum().reset_index()
    tot = g.groupby(group_cols)[value].transform("sum")
    g["share"] = g[value] / tot.replace(0, np.nan)
    out = g.merge(anag_groups, on=group_cols, how="inner")
    out["count"] = out["share"] * out["anag_total"]
    missing = anag_groups.merge(g[group_cols].drop_duplicates(), on=group_cols,
                                how="left", indicator=True)
    n_missing = int((missing["_merge"] == "left_only").sum())
    return out[group_cols + [attr_col, "count"]], n_missing


# ----------------------------------------------------------------------
def main(comune: str, anno: int):
    cens_anno = anno - 1
    comune_dir = os.path.expanduser(f"~/progetti/gsp/data/comuni/{comune}")
    out_dir = os.path.join(comune_dir, f"constraints_{anno}")
    os.makedirs(out_dir, exist_ok=True)
    manifest, report = {}, []
    report.append(f"# Constraint set {comune} — ancoraggio 1/1/{anno}, censimento {cens_anno}\n")

    # ---------- C1: spine anagrafica (HARD) ----------
    a = load(comune_dir, "anag_sesso_eta_statociv")
    a = pick_year(a, anno, "anagrafe")
    a = a[a["AGE"].astype(str).str.fullmatch(r"Y\d+|Y_GE100")]
    a = a[a["SEX"].astype(str).isin(["1", "2"])]
    a["sex"] = a["SEX"].astype(str).map(SEX_NORM)
    a["age"] = a["AGE"].map(lambda c: parse_age(c)[0])
    a["marital"] = a["MARITAL_STATUS"].astype(str).map(MARITAL_COLLAPSE)
    dropped = a["marital"].isna().sum()
    a = a.dropna(subset=["marital"])
    c1 = a.groupby(["sex", "age", "marital"])["OBS_VALUE"].sum().reset_index(name="count")
    c1.to_csv(os.path.join(out_dir, "c1_sex_age_marital.csv"), index=False)
    pop_tot = c1["count"].sum()
    print(f"[c1] anagrafe {anno}: {len(c1)} celle, pop={pop_tot:,.0f} "
          f"(scartate {dropped} righe con stato civile fuori collasso)")
    print("     collasso stato civile:", MARITAL_COLLAPSE)
    manifest["c1_sex_age_marital"] = {"type": "hard", "source": f"anagrafe 1/1/{anno}",
                                      "population": int(pop_tot)}
    anag_sex_age = c1.groupby(["sex", "age"])["count"].sum().reset_index(name="anag_total")

    # ---------- C2: sesso x età x cittadinanza (SOFT) ----------
    s = load(comune_dir, "cens_sesso_eta_cittadinanza")
    s = pick_year(s, cens_anno, "cens SETA")
    s = s[s["AGE_NOCLASS"].astype(str).str.fullmatch(r"Y\d+|Y_GE\d+")]
    s["sex"] = s["GENDER"].astype(str).map(SEX_NORM)
    s = s.dropna(subset=["sex"])
    s["age"] = s["AGE_NOCLASS"].map(lambda c: parse_age(c)[0])
    frg_code = frg_normalize_code(set(s["CITIZENSHIP"]))
    if frg_code:
        s_el = s[s["CITIZENSHIP"].isin(["ITL", frg_code])].copy()
        s_el["citizenship"] = s_el["CITIZENSHIP"].map({"ITL": "ITL", frg_code: "FRG"})
    else:  # fallback: differenza TOTAL - ITL
        piv = s.pivot_table(index=["sex", "age"], columns="CITIZENSHIP",
                            values="OBS_VALUE", aggfunc="sum").reset_index()
        piv["FRG"] = (piv["TOTAL"] - piv["ITL"]).clip(lower=0)
        s_el = piv.melt(id_vars=["sex", "age"], value_vars=["ITL", "FRG"],
                        var_name="citizenship", value_name="OBS_VALUE")
        print("[c2] straniero derivato per differenza TOTAL - ITL")
    c2, miss2 = apply_conditional(anag_sex_age, s_el, ["sex", "age"], "citizenship")
    c2.to_csv(os.path.join(out_dir, "c2_sex_age_citizenship.csv"), index=False)
    sig2, cmp2 = rounding_sigma(s, ["sex", "age"], "CITIZENSHIP", "TOTAL")
    print(f"[c2] {len(c2)} celle; gruppi anagrafici senza dato censuario: {miss2}"
          + (f"; sigma arrotondamento={sig2:.2f}" if sig2 is not None else ""))
    manifest["c2_sex_age_citizenship"] = {"type": "soft", "source": f"censimento {cens_anno}",
                                          "sigma_rounding": sig2, "missing_groups": miss2,
                                          "frg_source_code": frg_code or "TOTAL-ITL"}

    # confronto spine: anagrafe vs censimento su sesso x età
    cens_sex_age = s_el.groupby(["sex", "age"])["OBS_VALUE"].sum().reset_index(name="cens_total")
    cmp_spine = anag_sex_age.merge(cens_sex_age, on=["sex", "age"], how="outer").fillna(0)
    cmp_spine["diff"] = cmp_spine["cens_total"] - cmp_spine["anag_total"]
    mae = cmp_spine["diff"].abs().mean()
    report.append(f"## Raccordo anagrafe 1/1/{anno} <-> censimento {cens_anno} (sesso x età)\n"
                  f"- MAE per cella: {mae:.1f}  |  scarto totale: "
                  f"{cmp_spine['cens_total'].sum() - cmp_spine['anag_total'].sum():+,.0f} "
                  f"su {pop_tot:,.0f}\n- top-5 scarti:\n"
                  + cmp_spine.reindex(cmp_spine['diff'].abs().sort_values(ascending=False).index)
                    .head(5).to_string(index=False) + "\n")

    # ---------- C3/C4: istruzione e condizione professionale per classi ----------
    for cname, table, attr_raw, out_file in [
        ("c3_sex_ageclass_edu", "cens_istruzione_eta", "EDU", "c3_sex_ageclass_edu.csv"),
        ("c4_sex_ageclass_condprof", "cens_condprof_eta", "CPROF", "c4_sex_ageclass_condprof.csv"),
    ]:
        d = load(comune_dir, table)
        d = pick_year(d, cens_anno, table)
        d["sex"] = d["GENDER"].astype(str).map(SEX_NORM)
        d = d.dropna(subset=["sex"])
        classes = elementary_classes(d["AGE_NOCLASS"].astype(str).unique())
        d = d[d["AGE_NOCLASS"].isin(classes)].copy()
        print(f"[{cname}] classi d'età elementari: {classes}")
        if attr_raw == "EDU":
            d["attr"] = d["EDU_ATTAIN_label"].map(edu_collapse)
            d = d.dropna(subset=["attr"])
            mapping = (d.groupby(["EDU_ATTAIN", "EDU_ATTAIN_label", "attr"]).size()
                       .reset_index()[["EDU_ATTAIN", "EDU_ATTAIN_label", "attr"]])
            print(f"[{cname}] collasso istruzione:\n{mapping.to_string(index=False)}")
            full = pick_year(load(comune_dir, table), cens_anno, table)
            full["sex"] = full["GENDER"].astype(str).map(SEX_NORM)
            full = full.dropna(subset=["sex"])
            full = full[full["AGE_NOCLASS"].isin(classes)]
            sig, _ = rounding_sigma(full, ["sex", "AGE_NOCLASS"], "EDU_ATTAIN", "ALL")
        else:
            codes = set(d["CUR_ACT_STAT"].astype(str).unique())
            drop = condprof_drop_set(codes)
            d = d[~d["CUR_ACT_STAT"].astype(str).isin(drop)].copy()
            d["attr"] = d["CUR_ACT_STAT_label"].astype(str)
            print(f"[{cname}] codici condprof tenuti: "
                  f"{sorted(d['CUR_ACT_STAT'].astype(str).unique())} (scartati {sorted(drop)})")
            full = pick_year(load(comune_dir, table), cens_anno, table)
            full["sex"] = full["GENDER"].astype(str).map(SEX_NORM)
            full = full.dropna(subset=["sex"])
            full = full[full["AGE_NOCLASS"].isin(classes)]
            sig, _ = rounding_sigma(full, ["sex", "AGE_NOCLASS"], "CUR_ACT_STAT", "99")
        # anagrafe aggregata sulle stesse classi
        bounds = {c: parse_age(c) for c in classes}
        def to_class(age):
            for c, (lo, hi) in bounds.items():
                if lo <= age <= hi:
                    return c
            return None
        ag = anag_sex_age.copy()
        ag["age_class"] = ag["age"].map(to_class)
        ag = ag.dropna(subset=["age_class"]).groupby(["sex", "age_class"])["anag_total"] \
               .sum().reset_index()
        d = d.rename(columns={"AGE_NOCLASS": "age_class"})
        cts, miss = apply_conditional(ag, d, ["sex", "age_class"], "attr")
        cts.to_csv(os.path.join(out_dir, out_file), index=False)
        print(f"[{cname}] {len(cts)} celle; gruppi senza dato: {miss}; "
              + (f"sigma arrotondamento={sig:.2f}" if sig is not None else "no totali per sigma"))
        manifest[cname] = {"type": "soft", "source": f"censimento {cens_anno}",
                           "age_classes": classes, "sigma_rounding": sig,
                           "missing_groups": miss}

    # ---------- C5/C6: incroci con cittadinanza (universo intero) ----------
    for cname, table, attr_fn in [
        ("c5_edu_citizenship", "cens_istruzione_cittadinanza",
         lambda d: d["EDU_ATTAIN_label"].map(edu_collapse)),
        ("c6_condprof_citizenship", "cens_condprof_cittadinanza",
         lambda d: d["CUR_ACT_STAT_label"].astype(str)),
    ]:
        d = load(comune_dir, table)
        d = pick_year(d, cens_anno, table)
        d["sex"] = d["GENDER"].astype(str).map(SEX_NORM)
        d = d.dropna(subset=["sex"])
        if "condprof" in cname:
            codes = set(d["CUR_ACT_STAT"].astype(str).unique())
            drop = condprof_drop_set(codes)
            d = d[~d["CUR_ACT_STAT"].astype(str).isin(drop)]
        d["attr"] = attr_fn(d)
        scarti = d[d["attr"].astype(str).str.startswith("?")]["attr"].unique()
        if len(scarti):
            print(f"[{cname}] ATTENZIONE etichette non mappate: {list(scarti)}")
        d = d.dropna(subset=["attr"])
        d = d[~d["attr"].astype(str).str.startswith("?")]
        frg_code = frg_normalize_code(set(d["CITIZENSHIP"]))
        if frg_code:
            c = d[d["CITIZENSHIP"].isin(["ITL", frg_code])] \
                .groupby(["CITIZENSHIP", "attr"])["OBS_VALUE"].sum() \
                .reset_index(name="count")
            c["citizenship"] = c["CITIZENSHIP"].map({"ITL": "ITL", frg_code: "FRG"})
        else:
            piv = d.pivot_table(index="attr", columns="CITIZENSHIP",
                                values="OBS_VALUE", aggfunc="sum").reset_index()
            piv["FRG"] = (piv["TOTAL"] - piv["ITL"]).clip(lower=0)
            c = piv.melt(id_vars="attr", value_vars=["ITL", "FRG"],
                         var_name="citizenship", value_name="count")
            print(f"[{cname}] straniero derivato per differenza TOTAL - ITL")
        c = c[["citizenship", "attr", "count"]]
        c.to_csv(os.path.join(out_dir, f"{cname}.csv"), index=False)
        print(f"[{cname}] {len(c)} celle, somma={c['count'].sum():,.0f}")
        manifest[cname] = {"type": "soft", "source": f"censimento {cens_anno}",
                           "note": "quote su universo tavola; riscalare in fase solver"}

    # ---------- Nazionalità: P(paese | FRG), two-stage ----------
    n = load(comune_dir, "cens_stranieri_paesi")
    n = pick_year(n, cens_anno, "stranieri paesi")
    lab = n["AREA_CONTRY_CITIZEN_label"].astype(str).str.lower()
    aggregates = lab.str.contains("tutte le voci|unione europea|countries|europ|africa|america|asia|oceania|total|"
                                  "apolidi|aggregat|eea|efta", regex=True)
    n_el = n[~aggregates & (n["OBS_VALUE"] > 0)]
    nat = n_el.groupby(["AREA_CONTRY_CITIZEN", "AREA_CONTRY_CITIZEN_label"])[
        "OBS_VALUE"].sum().reset_index(name="count").sort_values("count", ascending=False)
    nat["share_frg"] = nat["count"] / nat["count"].sum()
    nat.to_csv(os.path.join(out_dir, "nationality_conditional.csv"), index=False)
    print(f"[naz] {len(nat)} paesi, top-5: "
          f"{nat.head(5)['AREA_CONTRY_CITIZEN_label'].tolist()}")
    manifest["nationality_conditional"] = {"type": "two_stage",
                                           "source": f"censimento {cens_anno}",
                                           "n_countries": int(len(nat))}

    # ---------- manifest + report ----------
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(report))
    print(f"\n[done] constraint set in {out_dir}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("Uso: python build_constraints.py <codice_comune> [--anno 2025]")
    comune = args[0]
    anno = int(args[args.index("--anno") + 1]) if "--anno" in args else 2025
    main(comune, anno)
