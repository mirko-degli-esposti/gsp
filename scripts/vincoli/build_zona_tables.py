"""
build_zona_tables.py — v3 (generico) — dalle sezioni di censimento alle
tabelle sub-comunali Z1-Z4 + Z6, per qualunque comune registrato.

Architettura: registro COMUNI (configurazione territoriale per comune:
CSV sezioni di default, livelli disponibili con colonna COM_ASC*, numero
atteso di unita', denominazioni, eventuale gerarchia) + motore unico.
Aggiungere un comune = aggiungere una voce al registro.

Comuni registrati (il registro vive in gsp_common.py, non qui):
    017029  Brescia   quartieri (COM_ASC1, 33)                    [default]
    034027  Parma     quartieri (COM_ASC1, 13)                    [default]
    036023  Modena    quartieri (COM_ASC1, 4)                     [default]
    037006  Bologna   quartieri (COM_ASC1, 6)
                      zone      (COM_ASC2, 18, parent=quartieri)  [default]

Uso:
    python build_zona_tables.py 017029                       # Brescia, 33 quartieri
    python build_zona_tables.py 036023                       # Modena, 4 quartieri
    python build_zona_tables.py 037006                       # Bologna, 18 zone (default!)
    python build_zona_tables.py 037006 --level quartieri     # Bologna, 6 quartieri
    opzioni: --sez-csv, --com-dir, --out-dir

Output (default: <com_dir>/zona_2023/ — la directory letta da cs_build;
usare --out-dir per archiviare un livello alternativo):
    z1_zona_sesso_eta5.csv           zona x sesso x classi quinquennali
    z2_zona_sesso_macroeta_citt.csv  zona x sesso x macroeta x ITL/FRG
    z3_zona_sesso_istruzione.csv     zona x sesso x istruzione (5 livelli)
    z4_zona_sesso_occup.csv          zona x sesso x occupato/non (15-64)
    z6_zona_background.csv           zona x background (EM1-6; se presenti)
    zona_nomi.csv                    codice -> nome (+ livello, + parent)

Convenzioni (decisioni di sessione):
  - la colonna identificativa resta 'zona' a ogni livello, per compatibilita'
    con cs_build/assign_nationality;
  - sezioni fittizie 888888x/999999x TENUTE nell'unita' assegnata da ISTAT
    (coerenza contabile con i totali ufficiali);
  - i margini comunali dei blocchi Z sono imposti in cs_build via
    P(zona | margine) x conteggi comunali (+IPF): qui solo audit grezzi.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import gsp.common as G


# ----------------------------------------------------------------------
# Registro dei comuni
# ----------------------------------------------------------------------




# ----------------------------------------------------------------------
# Mapping colonne del tracciato -> variabili tidy
# ----------------------------------------------------------------------

ETA5 = ["Y0-4", "Y5-9", "Y10-14", "Y15-19", "Y20-24", "Y25-29", "Y30-34",
        "Y35-39", "Y40-44", "Y45-49", "Y50-54", "Y55-59", "Y60-64",
        "Y65-69", "Y70-74", "Y_GE75"]
COLS_ETA_M = [f"P{i}" for i in range(30, 46)]
COLS_ETA_F = [f"P{i}" for i in range(67, 83)]

EDU5 = ["nessun_titolo", "elementare", "media", "diploma", "terziario"]
COLS_EDU_M = [f"P{i}" for i in range(91, 96)]
COLS_EDU_F = [f"P{i}" for i in range(96, 101)]

MACROETA = ["Y0-14", "Y15-64", "Y_GE65"]
COLS_IT_M, COLS_IT_F = ["IT4", "IT5", "IT6"], ["IT7", "IT8", "IT9"]
COLS_ST_M, COLS_ST_F = ["ST25", "ST26", "ST27"], ["ST28", "ST29", "ST30"]

# EM1-6: background migratorio (senza sesso) -> z6; opzionali nel CSV
EM_MAP = {"EM1": "italiano_nativo", "EM2": "italiano_rientrato",
          "EM3": "naturalizzato_g2", "EM4": "naturalizzato_immigrato",
          "EM5": "straniero_g2", "EM6": "straniero_immigrato"}

NUMERIC_COLUMNS = sorted(
    set(COLS_ETA_M + COLS_ETA_F + COLS_EDU_M + COLS_EDU_F
        + COLS_IT_M + COLS_IT_F + COLS_ST_M + COLS_ST_F
        + ["P1", "P2", "P3", "ST1", "P102", "P103"])
)


def normalize_code(series: pd.Series) -> pd.Series:
    """Normalizza codici letti come interi o float, senza '.0'."""
    return pd.to_numeric(series, errors="coerce").astype("Int64").astype("string")


def melt_block(groups, cols, labels, sex, extra: dict) -> list[dict]:
    rows: list[dict] = []
    for zona, sub in groups:
        vals = sub[cols].sum()
        for col, label in zip(cols, labels):
            rows.append({"zona": str(zona), "sesso": sex, **extra,
                         "cat": label, "count": float(vals[col])})
    return rows


def validate_columns(df: pd.DataFrame, group_column: str) -> None:
    required = set(NUMERIC_COLUMNS) | {group_column}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError("Nel CSV mancano colonne richieste dal tracciato: "
                         + ", ".join(missing))


def build_names_table(comune: str, level: str, observed_codes: set[str],
                      parent_map: dict | None = None) -> pd.DataFrame:
    names = G.zona_nomi(comune, level)
    unknown = sorted(observed_codes - set(names))
    absent = sorted(set(names) - observed_codes)
    if unknown:
        raise ValueError(f"Codici '{level}' senza denominazione: {unknown}")
    if absent:
        raise ValueError(f"Codici attesi non presenti nel CSV: {absent}")

    parent_liv = G.info(comune)["livelli"][level].get("parent")
    parent_names = G.zona_nomi(comune, parent_liv) if parent_liv else None

    rows = []
    for code in sorted(observed_codes):
        row = {"zona": code, "nome": names[code], "livello": level}
        if parent_liv and parent_map:
            p = parent_map.get(code)
            row["quartiere"] = p
            row["quartiere_nome"] = parent_names.get(p) if parent_names else None
        rows.append(row)
    return pd.DataFrame(rows)


def audit_against_comune(z1: pd.DataFrame, z2: pd.DataFrame,
                         com_dir: Path) -> None:
    communal_file = com_dir / "cens_sesso_eta_cittadinanza_decoded.csv"
    if not communal_file.exists():
        print(f"[audit] file comunale non trovato, confronto SDMX saltato: "
              f"{communal_file}")
        return
    s = pd.read_csv(communal_file, dtype=str, keep_default_na=False)
    required = {"TIME_PERIOD", "AGE_NOCLASS", "GENDER", "CITIZENSHIP", "OBS_VALUE"}
    missing = sorted(required - set(s.columns))
    if missing:
        print(f"[audit] confronto SDMX saltato: colonne mancanti {missing}")
        return
    s["OBS_VALUE"] = pd.to_numeric(s["OBS_VALUE"], errors="coerce")
    s23 = s[(s["TIME_PERIOD"] == "2023")
            & s["AGE_NOCLASS"].str.fullmatch(r"Y\d+|Y_GE\d+", na=False)
            & s["GENDER"].isin(["M", "F"])]
    checks = [
        (z1["count"].sum(), "TOTAL", "totale"),
        (z2.loc[z2["cittadinanza"] == "FRG", "count"].sum(), "FRGAPO",
         "stranieri"),
    ]
    for sez_tot, citizenship, label in checks:
        selected = s23[s23["CITIZENSHIP"] == citizenship]
        if selected.empty:
            print(f"[audit] {label}: codice comunale {citizenship!r} non "
                  "trovato; confronto saltato")
            continue
        com_tot = selected["OBS_VALUE"].sum()
        print(f"[audit] {label}: sezioni {sez_tot:,.0f} vs comunale 2023 "
              f"{com_tot:,.1f} (scarto {sez_tot - com_tot:+,.1f})")


def build_tables(*, comune: str, level: str, sez_csv: Path, com_dir: Path,
                 out_dir: Path) -> None:
    cfg = G.info(comune)["livelli"][level]
    group_column: str = cfg["col"]
    expected: int = cfg["n"]
    level_label: str = level          # la chiave del livello e' gia' l'etichetta

    if not sez_csv.exists():
        raise FileNotFoundError(f"CSV delle sezioni non trovato: {sez_csv}")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[cfg] {G.info(comune)['nome']} ({comune}) | livello '{level}' "
          f"({group_column}, attesi {expected}) | out: {out_dir}")

    b = pd.read_csv(sez_csv, dtype=str, keep_default_na=False)
    validate_columns(b, group_column)
    b[group_column] = normalize_code(b[group_column])
    if b[group_column].isna().any():
        n = int(b[group_column].isna().sum())
        raise ValueError(f"{n} righe senza codice valido in {group_column}")
    for column in NUMERIC_COLUMNS:
        b[column] = pd.to_numeric(b[column], errors="coerce").fillna(0.0)
    em_cols = [c for c in EM_MAP if c in b.columns]
    for column in em_cols:
        b[column] = pd.to_numeric(b[column], errors="coerce").fillna(0.0)

    observed_codes = set(b[group_column].astype(str).unique())
    if len(observed_codes) != expected:
        raise ValueError(f"attesi {expected} {level_label}, trovati "
                         f"{len(observed_codes)}: {sorted(observed_codes)}")
    if observed_codes == {"0"} or observed_codes == {0}:
        raise SystemExit(
            f"{group_column} = 0 per tutte le sezioni: {G.info(comune)['nome']} "
            "non ha sub-aree amministrative assegnate da ISTAT (codice "
            "convenzionale 'nessuna partizione'). Il livello zona non è "
            "costruibile per questo comune: procedere con K6C/K8C comunale-only.")

    # La gerarchia fra livelli si ricava dalle sezioni: ogni sezione porta
    # sia COM_ASC1 sia COM_ASC2, quindi non serve un dizionario a mano.
    parent_liv = cfg.get("parent")
    parent_map = None
    if parent_liv:
        pcol = G.livello_col(comune, parent_liv)
        if pcol in b.columns:
            pm = b[[group_column, pcol]].copy()
            pm[pcol] = normalize_code(pm[pcol]).astype(str)
            n_par = pm.groupby(group_column)[pcol].nunique()
            if (n_par > 1).any():
                raise ValueError(
                    f"Mappatura '{level}' -> '{parent_liv}' non funzionale: "
                    f"{list(n_par[n_par > 1].index)}")
            parent_map = (pm.drop_duplicates(group_column)
                          .set_index(group_column)[pcol].to_dict())
            from collections import Counter
            taglie = sorted(Counter(parent_map.values()).values(), reverse=True)
            print(f"[audit] gerarchia: {len(parent_map)} {level} in "
                  f"{len(set(parent_map.values()))} {parent_liv} | "
                  f"taglie {taglie}")
            # Composizione per nome: e' l'unico modo di accorgersi che un
            # dizionario codice->nome e' permutato. I controlli strutturali
            # non lo vedono, perche' una permutazione resta una biiezione.
            pn = G.zona_nomi(comune, parent_liv)
            zn = G.zona_nomi(comune, level)
            comp = {}
            for z, q in sorted(parent_map.items()):
                comp.setdefault(pn.get(q, q), []).append(zn.get(z, z))
            for q, zs in sorted(comp.items()):
                print(f"           {q:<24} {sorted(zs)}")
        else:
            print(f"[warn] colonna {pcol} assente: gerarchia non ricostruita")

    names = build_names_table(comune, level, observed_codes, parent_map)
    names.to_csv(out_dir / "zona_nomi.csv", index=False)
    groups = list(b.groupby(group_column, sort=True))

    # Z1: territorio x sesso x classi quinquennali
    z1 = pd.DataFrame(melt_block(groups, COLS_ETA_M, ETA5, "M", {})
                      + melt_block(groups, COLS_ETA_F, ETA5, "F", {})
                      ).rename(columns={"cat": "eta5"})
    z1.to_csv(out_dir / "z1_zona_sesso_eta5.csv", index=False)

    # Z2: territorio x sesso x macroeta x cittadinanza
    z2 = pd.DataFrame(
        melt_block(groups, COLS_IT_M, MACROETA, "M", {"cittadinanza": "ITL"})
        + melt_block(groups, COLS_IT_F, MACROETA, "F", {"cittadinanza": "ITL"})
        + melt_block(groups, COLS_ST_M, MACROETA, "M", {"cittadinanza": "FRG"})
        + melt_block(groups, COLS_ST_F, MACROETA, "F", {"cittadinanza": "FRG"})
    ).rename(columns={"cat": "macroeta"})
    z2.to_csv(out_dir / "z2_zona_sesso_macroeta_citt.csv", index=False)

    # Z3: territorio x sesso x istruzione (universo 9+)
    z3 = pd.DataFrame(melt_block(groups, COLS_EDU_M, EDU5, "M", {})
                      + melt_block(groups, COLS_EDU_F, EDU5, "F", {})
                      ).rename(columns={"cat": "istruzione5"})
    z3.to_csv(out_dir / "z3_zona_sesso_istruzione.csv", index=False)

    # Z4: territorio x sesso x occupato/non occupato (universo 15-64)
    rows, over_res = [], []
    for zona, sub in groups:
        pop_m = float(sub[["IT5", "ST26"]].sum().sum())
        pop_f = float(sub[["IT8", "ST29"]].sum().sum())
        occ_m, occ_f = float(sub["P102"].sum()), float(sub["P103"].sum())
        if occ_m > pop_m:
            over_res.append((str(zona), "M", occ_m - pop_m))
        if occ_f > pop_f:
            over_res.append((str(zona), "F", occ_f - pop_f))
        rows += [
            {"zona": str(zona), "sesso": "M", "occup": "occupato", "count": occ_m},
            {"zona": str(zona), "sesso": "M", "occup": "non_occupato",
             "count": max(pop_m - occ_m, 0.0)},
            {"zona": str(zona), "sesso": "F", "occup": "occupato", "count": occ_f},
            {"zona": str(zona), "sesso": "F", "occup": "non_occupato",
             "count": max(pop_f - occ_f, 0.0)},
        ]
    z4 = pd.DataFrame(rows)
    z4.to_csv(out_dir / "z4_zona_sesso_occup.csv", index=False)
    if over_res:
        print(f"[warn] Z4: occupati > pop 15-64 in {len(over_res)} celle "
              f"(residuo azzerato): {over_res[:5]}")

    # Z6: territorio x background (EM1-6, senza sesso) — se disponibili
    z6 = None
    if len(em_cols) == len(EM_MAP):
        rows = []
        for zona, sub in groups:
            for em, bg in EM_MAP.items():
                rows.append({"zona": str(zona), "background": bg,
                             "count": float(sub[em].sum())})
        z6 = pd.DataFrame(rows)
        z6.to_csv(out_dir / "z6_zona_background.csv", index=False)
    else:
        print(f"[warn] colonne EM1-6 assenti o incomplete nel CSV "
              f"({sorted(em_cols)}): z6 saltata (necessaria per K9C)")

    # ---- audit -----------------------------------------------------------
    fake = 0
    if "SEZ21_ID" in b.columns:
        m = b["SEZ21_ID"].astype(str).str.contains(r"888888|999999", regex=True)
        fake = int(m.sum())
        if fake:
            fpop = b.loc[m, "P1"].sum()
            fz = sorted(b.loc[m, group_column].astype(str).unique())
            print(f"[audit] sezioni fittizie: {fake} (P1={fpop:,.0f}) "
                  f"tenute in {fz}")
    print(f"[zona] {len(observed_codes)} {level_label} | Z1 {len(z1)} righe | "
          f"Z2 {len(z2)} | Z3 {len(z3)} | Z4 {len(z4)}"
          + (f" | Z6 {len(z6)}" if z6 is not None else ""))
    print(f"[audit] Z1 totale: {z1['count'].sum():,.0f} | "
          f"Z3 (9+): {z3['count'].sum():,.0f} | "
          f"Z4 (15-64): {z4['count'].sum():,.0f}"
          + (f" | Z6: {z6['count'].sum():,.0f}" if z6 is not None else ""))
    audit_against_comune(z1, z2, com_dir)

    # sanity qualitativa: quota stranieri per unita'
    shares = z2.groupby(["zona", "cittadinanza"])["count"].sum().unstack(fill_value=0)
    den = shares.get("FRG", 0) + shares.get("ITL", 0)
    shares["quota_frg"] = shares.get("FRG", 0).div(den.where(den != 0))
    shares = shares.join(names.set_index("zona")) \
                   .sort_values("quota_frg", ascending=False)
    print(f"\n[sanity] top-5 {level_label} per quota stranieri:")
    print(shares.head(5)[["nome", "quota_frg"]].round(3).to_string())
    print(f"\n[done] tabelle in {out_dir}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Tabelle sub-comunali Z1-Z4+Z6 da sezioni di censimento "
                    f"(comuni registrati: {', '.join(sorted(G.COMUNI))}).")
    p.add_argument("comune", help="codice comune ITTER107 (es. 017029)")
    p.add_argument("--level", default=None,
                   help="livello territoriale (default: quello del comune)")
    p.add_argument("--sez-csv", type=Path, default=None,
                   help="CSV sezioni (default: dal registro)")
    p.add_argument("--com-dir", type=Path, default=None,
                   help="directory dati comunali (default: "
                        "~/progetti/gsp/data/comuni/<comune>)")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="output (default: <com_dir>/zona_2023 — la directory "
                        "letta da cs_build)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    comune = args.comune.zfill(6)
    if comune not in G.COMUNI:
        raise SystemExit(
            f"comune {comune} non registrato (registrati: {sorted(G.COMUNI)}); "
            "aggiungere una voce a COMUNI in gsp_common.py")
    cfg_c = G.info(comune)
    level = args.level or cfg_c["livello"]
    if level is None:
        raise SystemExit(f"{cfg_c['nome']} non ha articolazione sub-comunale: "
                         f"procedere con un livello K senza zona")
    if level not in cfg_c["livelli"]:
        raise SystemExit(f"livello '{level}' non definito per "
                         f"{cfg_c['nome']} (validi: {sorted(cfg_c['livelli'])})")
    sez_csv = args.sez_csv or Path(G.path_sezioni(comune))
    com_dir = args.com_dir or Path(G.path_comune(comune))
    out_dir = args.out_dir or (com_dir / "zona_2023")
    
    build_tables(comune=comune, level=level, sez_csv=sez_csv.expanduser(),
                 com_dir=com_dir.expanduser(), out_dir=out_dir.expanduser())


if __name__ == "__main__":
    main()
