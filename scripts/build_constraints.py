"""
build_constraints.py — v2 — dal set di tavole comunali ISTAT al constraint set per GibbsPCD.

Uso:
    python build_constraints.py 017029 --anno 2025

Convenzioni:
    --anno N  = ancoraggio anagrafico all'1/1/N (TIME_PERIOD=N nella tavola anagrafica);
                lo strato censuario usa TIME_PERIOD=N-1 (fotografia ~ottobre N-1).

Input:  ~/progetti/gsp/data/comuni/<comune>/<chiave>_decoded.csv   (da fetch_comune.py)
    obbligatorie:  anag_sesso_eta_statociv (anno N)
                   cens_sesso_eta_cittadinanza, cens_istruzione_eta,
                   cens_istruzione_cittadinanza, cens_condprof_eta,
                   cens_condprof_cittadinanza, cens_stranieri_paesi  (anno N-1)
    opzionali:     cens_migr_backg (anno N-1)  -> C7/C8
                   cens_posizione_prof, cens_settore_prof (qualunque anno) -> C9/C10
    preflight() verifica la copertura temporale di tutte le tavole PRIMA di
    costruire qualsiasi blocco: assenza di una obbligatoria = errore fatale,
    assenza di una opzionale = skip dichiarato a video.

Output: ~/progetti/gsp/data/comuni/<comune>/constraints_<anno>/
    c1_sex_age_marital.csv        vincolo HARD  (anagrafe, conteggi esatti)
    c2_sex_age_citizenship.csv    vincolo SOFT  (censimento -> condizionale su spine anagrafica)
    c3_sex_ageclass_edu.csv       vincolo SOFT  (idem, classi d'età censuarie)
    c4_sex_ageclass_condprof.csv  vincolo SOFT  (idem)
    c5_edu_citizenship.csv        vincolo SOFT
    c6_condprof_citizenship.csv   vincolo SOFT
    c7_sex_background.csv         vincolo SOFT  (condizionale: serve cens_migr_backg)
    c8_background_origine.csv     vincolo SOFT  (idem; non_applicabile per nati estero)
    c9_sex_posizione_prof.csv     vincolo SOFT  (condizionale: universo occupati)
    c10_sex_settore.csv           vincolo SOFT  (idem)
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

Note v2 (blocchi C7-C10):
    - C7/C8: background migratorio a 6 livelli (IT_BIRT_IT ... FOR_B_AB); la
      cittadinanza ITL/FRG e' funzione deterministica del background (ITL_GROUP),
      da cui il blocco GC costruito a valle in cs_build.py
    - C8: origine_genitori e' definita solo per i nati in Italia (NATI_IT); per i
      nati all'estero il livello e' 'non_applicabile'
    - C9/C10: fonte EMPLP_1/EMPLP_2, censimento 2021 (il dettaglio non e' rilasciato
      per anni successivi). Assunzione (7) di stabilita' strutturale 2021 -> anno di
      ancoraggio: si usano le QUOTE riscalate sul totale occupati del C4 corrente,
      non i livelli. Se il C4 non e' leggibile i blocchi escono senza riscalatura.
    - il manifest marca C9/C10 come "hard": e' un residuo, l'universo e' derivato
      per riscalatura e andrebbe riclassificato "soft"
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

# tavole consumate: (nome, anno richiesto, fatale se manca, blocco)
TAVOLE_ATTESE = [
    ("anag_sesso_eta_statociv",      "anno",  True,  "C1 spine anagrafica"),
    ("cens_sesso_eta_cittadinanza",  "cens",  True,  "C2 sesso x eta x cittadinanza"),
    ("cens_istruzione_eta",          "cens",  True,  "C3 istruzione x eta"),
    ("cens_istruzione_cittadinanza", "cens",  True,  "C3 istruzione x cittadinanza"),
    ("cens_condprof_eta",            "cens",  True,  "C4 condizione prof. x eta"),
    ("cens_condprof_cittadinanza",   "cens",  True,  "C4 condizione prof. x citt."),
    ("cens_stranieri_paesi",         "cens",  True,  "C6 paesi di cittadinanza"),
    ("cens_migr_backg",              "cens",  False, "C7/C8 background migratorio"),
    ("cens_posizione_prof",          None,    False, "C9 posizione professionale"),
    ("cens_settore_prof",            None,    False, "C10 settore economico"),
]


def preflight(comune_dir: str, anno: int, cens_anno: int) -> None:
    """Copertura temporale delle tavole prima di costruire qualsiasi blocco.

    Serve a trasformare in errore immediato due fallimenti altrimenti tardivi
    o silenziosi: il sys.exit di pick_year a meta' elaborazione, e lo skip
    stampato ma non fatale dei blocchi C7/C8 quando cens_migr_backg non copre
    l'anno censuario richiesto.
    """
    print(f"[pre] ancoraggio anagrafico 1/1/{anno} | strato censuario {cens_anno}")
    fatali, saltati, anni_cens = [], [], []

    for name, quale, hard, desc in TAVOLE_ATTESE:
        path = os.path.join(comune_dir, f"{name}_decoded.csv")
        if not os.path.exists(path):
            (fatali if hard else saltati).append(f"{name}: file assente")
            continue
        anni = sorted(pd.read_csv(path, usecols=["TIME_PERIOD"])["TIME_PERIOD"]
                      .astype(str).unique())
        if quale is None:
            print(f"[pre] {name:<30} anni {anni} -> pool + riscalatura")
            continue
        serve = anno if quale == "anno" else cens_anno
        if quale == "cens" and hard:
            anni_cens.append(set(anni))
        if str(serve) in anni:
            print(f"[pre] {name:<30} {serve} ok")
        else:
            (fatali if hard else saltati).append(
                f"{name}: {serve} assente (disponibili {anni}) -> {desc}")

    for m in saltati:
        print(f"[pre] !! blocco SALTATO: {m}")
    if fatali:
        print()
        for m in fatali:
            print(f"[pre] FATALE: {m}")
        if anni_cens:
            comuni_anni = sorted(set.intersection(*anni_cens))
            if comuni_anni:
                print(f"[pre] anni censuari coperti da tutte le tavole hard: "
                      f"{comuni_anni} -> provare --anno {int(comuni_anni[-1]) + 1}")
        sys.exit(f"[pre] interrotto: --anno {anno} non sostenibile.")
    if saltati:
        print(f"[pre] {len(saltati)} blocchi verranno saltati: il constraint "
              f"set sara' piu' piccolo del previsto.")

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
    preflight(comune_dir, anno, cens_anno)
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

    # ---------- C7/C8: background migratorio e origine genitori ----------
    BACKGROUND_MAP = {
        "IT_BIRT_IT": "italiano_nativo", "IT_BIRT_AB": "italiano_rientrato",
        "NATIT_B_IT": "naturalizzato_g2", "NATIT_B_AB": "naturalizzato_immigrato",
        "FOR_B_IT": "straniero_g2", "FOR_B_AB": "straniero_immigrato",
    }
    ITL_GROUP = {"italiano_nativo", "italiano_rientrato",
                 "naturalizzato_g2", "naturalizzato_immigrato"}
    ORIGINE_MAP = {
        "BPBIT": "entrambi_italiani", "BPBAB": "entrambi_stranieri",
        "MBAB_FBIT": "madre_straniera_padre_italiano",
        "MBIT_FBAB": "madre_italiana_padre_straniero",
    }
    NATI_IT = {"italiano_nativo", "naturalizzato_g2", "straniero_g2"}

    mb_path = os.path.join(comune_dir, "cens_migr_backg_decoded.csv")
    if not os.path.exists(mb_path):
        print("[c7/c8] cens_migr_backg assente: blocchi background saltati "
              "(eseguire fetch_comune con la tavola DF_DCSS_MIGR_BACKG_PAR_TV_1_COM)")
    else:
        mb = pd.read_csv(mb_path)
        # TIME_PERIOD arriva come stringa in alcune tavole: normalizzare
        mb = mb[mb["TIME_PERIOD"].astype(str) == str(cens_anno)]
        if mb.empty:
            print(f"[c7/c8] cens_migr_backg: TIME_PERIOD={cens_anno} assente; "
                  f"disponibili {sorted(pd.read_csv(mb_path)['TIME_PERIOD'].astype(str).unique())} — saltati")
        else:
            mb = mb[mb["GENDER"].isin(["M", "F"])].copy()
            mb["sex"] = mb["GENDER"]

            # C7: sesso x background (6 elementari), PBP al totale
            c7 = mb[(mb["PLACE_BIRTH_PAR"] == "ALL")
                    & (mb["INDICATOR"].isin(BACKGROUND_MAP))].copy()
            c7["background"] = c7["INDICATOR"].map(BACKGROUND_MAP)
            c7 = c7.groupby(["sex", "background"])["OBS_VALUE"] \
                   .sum().reset_index(name="count")
            # armonizzazione 1D sui margini di C2 (ITL/FRG per sesso):
            # stessa base riconciliata -> fattori attesi ~1
            c2m = c2.copy()
            c2m["grp"] = c2m["citizenship"]
            c2_tot = c2m.groupby(["sex", "grp"])["count"].sum()
            c7["grp"] = c7["background"].map(
                lambda b: "ITL" if b in ITL_GROUP else "FRG")
            c7_tot = c7.groupby(["sex", "grp"])["count"].sum()
            factors = (c2_tot / c7_tot).rename("f").reset_index()
            c7 = c7.merge(factors, on=["sex", "grp"])
            c7["count"] = c7["count"] * c7["f"]
            devmax = (factors["f"] - 1).abs().max()
            print(f"[c7] sesso x background: {len(c7)} celle, "
                  f"somma={c7['count'].sum():,.0f}; "
                  f"fattori armonizzazione su C2: max|f-1|={devmax:.2e}")
            c7[["sex", "background", "count"]].to_csv(
                os.path.join(out_dir, "c7_sex_background.csv"), index=False)
            manifest["c7_sex_background"] = {
                "type": "hard", "source": f"censimento {cens_anno} (migr backg)",
                "harmonization_max_dev": float(devmax)}

            # C8: sesso x background x origine genitori — partizione completa:
            #   rami nati in Italia: 4 origini elementari, riscalate su C7
            #   rami nati all'estero: origine = non_applicabile (da C7)
            c8a = mb[(mb["INDICATOR"].isin(BACKGROUND_MAP))
                     & (mb["PLACE_BIRTH_PAR"].isin(ORIGINE_MAP))].copy()
            c8a["background"] = c8a["INDICATOR"].map(BACKGROUND_MAP)
            c8a = c8a[c8a["background"].isin(NATI_IT)]
            c8a["origine"] = c8a["PLACE_BIRTH_PAR"].map(ORIGINE_MAP)
            c8a = c8a.groupby(["sex", "background", "origine"])["OBS_VALUE"] \
                     .sum().reset_index(name="count")
            # riscala ogni (sex, background) sul totale C7 armonizzato
            c7_bg = c7.set_index(["sex", "background"])["count"]
            c8a_tot = c8a.groupby(["sex", "background"])["count"].transform("sum")
            c8a["count"] = c8a["count"] / c8a_tot * c8a.set_index(
                ["sex", "background"]).index.map(c7_bg).values
            c8b = c7[~c7["background"].isin(NATI_IT)][
                ["sex", "background", "count"]].copy()
            c8b["origine"] = "non_applicabile"
            c8 = pd.concat([c8a[["sex", "background", "origine", "count"]],
                            c8b[["sex", "background", "origine", "count"]]],
                           ignore_index=True)
            dev8 = abs(c8["count"].sum() - c7["count"].sum())
            print(f"[c8] sesso x background x origine: {len(c8)} celle, "
                  f"somma={c8['count'].sum():,.0f} (scarto vs C7: {dev8:.2e})")
            c8.to_csv(os.path.join(out_dir, "c8_background_origine.csv"),
                      index=False)
            manifest["c8_background_origine"] = {
                "type": "hard", "source": f"censimento {cens_anno} (migr backg)",
                "note": "partizione completa; non_applicabile per nati all'estero"}
    # ---------- C9/C10: posizione professionale e settore (occupati) ------
    # Universo: occupati 15+. Fonte EMPLP_1/EMPLP_2 (censimento 2021: il
    # dettaglio non e' rilasciato per anni successivi) -> assunzione (7) di
    # stabilita' strutturale 2021 -> anno di ancoraggio. Si usano le QUOTE,
    # riscalate sul totale occupati del CS corrente (blocco C4), non i livelli.
    EMPL_STATUS_MAP = {"9": "dipendente", "22": "indipendente"}
    BRANCH_MAP = {
        "A": "agricoltura", "0011": "industria",
        "0026": "commercio_alberghi_ristoranti", "0091": "trasporti_ict",
        "0092": "servizi_professionali", "0093": "altre_attivita",
    }

    # totale occupati per sesso, dal C4 appena scritto
    occ_by_sex = None
    c4_path = os.path.join(out_dir, "c4_sex_ageclass_condprof.csv")
    if os.path.exists(c4_path):
        c4f = pd.read_csv(c4_path)
        att = c4f["attr"].astype(str).str.lower()
        is_occ = att.str.startswith("occupat")      # esclude "in cerca di occupazione"
        if is_occ.any():
            occ_by_sex = c4f[is_occ].groupby("sex")["count"].sum()
            print(f"[c9/c10] occupati per sesso dal C4: "
                  f"{ {k: round(v) for k, v in occ_by_sex.items()} } "
                  f"(tot {occ_by_sex.sum():,.0f})")
    if occ_by_sex is None:
        print("[c9/c10] totale occupati non ricavabile dal C4: "
              "i blocchi saranno salvati senza riscalatura")

    for key, fname, colname, mapping, src in [
        ("cens_posizione_prof", "c9_sex_posizione_prof.csv", "posizione_prof",
         EMPL_STATUS_MAP, "EMPLOYMENT_STATUS"),
        ("cens_settore_prof", "c10_sex_settore.csv", "settore",
         BRANCH_MAP, "BRANCH_ECON_ACT"),
    ]:
        tag = fname.split("_")[0]
        path = os.path.join(comune_dir, f"{key}_decoded.csv")
        if not os.path.exists(path):
            print(f"[{tag}] {key} assente: blocco saltato "
                  f"(aggiungere la tavola a CORE ed eseguire fetch_comune)")
            continue
        e = pd.read_csv(path, dtype={src: str})
        anni = sorted(e["TIME_PERIOD"].astype(str).unique())
        e["sex"] = e["GENDER"].astype(str).map(SEX_NORM)
        e = e.dropna(subset=["sex"])
        e = e[e[src].astype(str).str.strip().isin(mapping)].copy()
        if e.empty:
            print(f"[{tag}] nessun record utile in {key} "
                  f"(anni disponibili: {anni}); blocco saltato")
            continue
        e[colname] = e[src].astype(str).str.strip().map(mapping)
        t = e.groupby(["sex", colname])["OBS_VALUE"].sum().reset_index(name="count")

        if occ_by_sex is not None:
            tot_src = t.groupby("sex")["count"].sum()
            fac = (occ_by_sex / tot_src).rename("f").reset_index()
            t = t.merge(fac, on="sex")
            t["count"] = t["count"] * t["f"]
            t = t.drop(columns="f")
            print(f"[{tag}] riscalatura quote {anni} -> occupati {anno}: "
                  f"fattori { {r['sex']: round(r['f'], 3) for _, r in fac.iterrows()} }")

        t[["sex", colname, "count"]].to_csv(os.path.join(out_dir, fname), index=False)
        print(f"[{tag}] {len(t)} celle, somma={t['count'].sum():,.0f} (fonte {anni})")
        manifest[fname.replace(".csv", "")] = {
            "type": "hard", "source": f"censimento {anni} ({key})",
            "note": "universo occupati; assunzione (7) di stabilita' strutturale"}
        
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
