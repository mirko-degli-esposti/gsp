"""
build_zona_tables_bologna.py — dalle sezioni di censimento alle tabelle
subcomunali di Bologna.

Supporta due livelli territoriali:

  quartieri  -> COM_ASC1, 6 quartieri amministrativi
  zone       -> COM_ASC2, 18 zone statistiche

Uso:
    python build_zona_tables_bologna.py --level quartieri
    python build_zona_tables_bologna.py --level zone

Input predefinito:
    ~/progetti/gsp/data/submun/bologna_sezioni_2023.csv

Output predefiniti:
    quartieri -> ~/progetti/gsp/data/comuni/037006/quartiere_2023/
    zone      -> ~/progetti/gsp/data/comuni/037006/zona_2023/

In entrambi i casi vengono prodotti:
    z1_zona_sesso_eta5.csv
    z2_zona_sesso_macroeta_citt.csv
    z3_zona_sesso_istruzione.csv
    z4_zona_sesso_occup.csv
    zona_nomi.csv

La colonna di identificazione resta denominata ``zona`` per compatibilita'
con la pipeline costruita per Brescia; il file zona_nomi.csv specifica anche
il livello territoriale.

Le sezioni fittizie 888888x/999999x sono mantenute nell'unita' territoriale
assegnata da ISTAT, così da preservare la coerenza contabile dei totali.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


DEFAULT_SEZ_CSV = Path(
    os.path.expanduser("~/progetti/gsp/data/submun/bologna_sezioni_2023.csv")
)
DEFAULT_COM_DIR = Path(
    os.path.expanduser("~/progetti/gsp/data/comuni/037006")
)


# ----------------------------------------------------------------------
# Denominazioni territoriali
# ----------------------------------------------------------------------

QUARTIERI_NOMI = {
    "37006011": "Borgo Panigale-Reno",
    "37006012": "Navile",
    "37006013": "Porto-Saragozza",
    "37006014": "San Donato-San Vitale",
    "37006015": "Santo Stefano",
    "37006016": "Savena",
}

# Le 18 zone statistiche sono le articolazioni storiche usate dal Comune.
ZONE_NOMI = {
    "37006001": "Barca",
    "37006002": "Borgo Panigale",
    "37006003": "Santa Viola",
    "37006004": "Bolognina",
    "37006005": "Corticella",
    "37006006": "Lame",
    "37006007": "Costa Saragozza",
    "37006008": "Malpighi",
    "37006009": "Marconi",
    "37006010": "Saffi",
    "37006011": "San Donato",
    "37006012": "San Vitale",
    "37006013": "Colli",
    "37006014": "Galvani",
    "37006015": "Irnerio",
    "37006016": "Murri",
    "37006017": "Mazzini",
    "37006018": "San Ruffillo",
}

ZONE_TO_QUARTIERE = {
    "37006001": "37006011",
    "37006002": "37006011",
    "37006003": "37006011",
    "37006004": "37006012",
    "37006005": "37006012",
    "37006006": "37006012",
    "37006007": "37006013",
    "37006008": "37006013",
    "37006009": "37006013",
    "37006010": "37006013",
    "37006011": "37006014",
    "37006012": "37006014",
    "37006013": "37006015",
    "37006014": "37006015",
    "37006015": "37006015",
    "37006016": "37006015",
    "37006017": "37006016",
    "37006018": "37006016",
}

LEVELS = {
    "quartieri": {
        "column": "COM_ASC1",
        "expected": 6,
        "names": QUARTIERI_NOMI,
        "label": "quartieri",
        "default_out": "quartiere_2023",
    },
    "zone": {
        "column": "COM_ASC2",
        "expected": 18,
        "names": ZONE_NOMI,
        "label": "zone statistiche",
        "default_out": "zona_2023",
    },
}


# ----------------------------------------------------------------------
# Mapping colonne del tracciato -> variabili tidy
# ----------------------------------------------------------------------

ETA5 = [
    "Y0-4", "Y5-9", "Y10-14", "Y15-19", "Y20-24", "Y25-29",
    "Y30-34", "Y35-39", "Y40-44", "Y45-49", "Y50-54", "Y55-59",
    "Y60-64", "Y65-69", "Y70-74", "Y_GE75",
]
COLS_ETA_M = [f"P{i}" for i in range(30, 46)]
COLS_ETA_F = [f"P{i}" for i in range(67, 83)]

EDU5 = ["nessun_titolo", "elementare", "media", "diploma", "terziario"]
COLS_EDU_M = [f"P{i}" for i in range(91, 96)]
COLS_EDU_F = [f"P{i}" for i in range(96, 101)]

MACROETA = ["Y0-14", "Y15-64", "Y_GE65"]
COLS_IT_M, COLS_IT_F = ["IT4", "IT5", "IT6"], ["IT7", "IT8", "IT9"]
COLS_ST_M, COLS_ST_F = ["ST25", "ST26", "ST27"], ["ST28", "ST29", "ST30"]

NUMERIC_COLUMNS = sorted(
    set(
        COLS_ETA_M
        + COLS_ETA_F
        + COLS_EDU_M
        + COLS_EDU_F
        + COLS_IT_M
        + COLS_IT_F
        + COLS_ST_M
        + COLS_ST_F
        + ["P1", "P2", "P3", "ST1", "P102", "P103"]
    )
)


def normalize_code(series: pd.Series) -> pd.Series:
    """Normalizza codici letti come interi o float, senza '.0'."""
    return pd.to_numeric(series, errors="coerce").astype("Int64").astype("string")


def melt_block(groups, cols, labels, sex, extra: dict) -> list[dict]:
    rows: list[dict] = []
    for zona, sub in groups:
        vals = sub[cols].sum()
        for col, label in zip(cols, labels):
            rows.append(
                {
                    "zona": str(zona),
                    "sesso": sex,
                    **extra,
                    "cat": label,
                    "count": float(vals[col]),
                }
            )
    return rows


def validate_columns(df: pd.DataFrame, group_column: str) -> None:
    required = set(NUMERIC_COLUMNS) | {group_column}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(
            "Nel CSV mancano colonne richieste dal tracciato: "
            + ", ".join(missing)
        )


def build_names_table(level: str, observed_codes: set[str]) -> pd.DataFrame:
    cfg = LEVELS[level]
    names: dict[str, str] = cfg["names"]

    unknown = sorted(observed_codes - set(names))
    absent = sorted(set(names) - observed_codes)
    if unknown:
        raise ValueError(
            f"Codici {cfg['label']} senza denominazione: {unknown}"
        )
    if absent:
        raise ValueError(
            f"Codici attesi non presenti nel CSV: {absent}"
        )

    rows = []
    for code in sorted(observed_codes):
        row = {
            "zona": code,
            "nome": names[code],
            "livello": level,
        }
        if level == "zone":
            parent = ZONE_TO_QUARTIERE[code]
            row["quartiere"] = parent
            row["quartiere_nome"] = QUARTIERI_NOMI[parent]
        rows.append(row)

    return pd.DataFrame(rows)


def audit_against_comune(z1: pd.DataFrame, z2: pd.DataFrame, com_dir: Path) -> None:
    communal_file = com_dir / "cens_sesso_eta_cittadinanza_decoded.csv"
    if not communal_file.exists():
        print(f"[audit] file comunale non trovato, confronto SDMX saltato: {communal_file}")
        return

    s = pd.read_csv(communal_file, dtype=str, keep_default_na=False)
    required = {
        "TIME_PERIOD", "AGE_NOCLASS", "GENDER", "CITIZENSHIP", "OBS_VALUE"
    }
    missing = sorted(required - set(s.columns))
    if missing:
        print(f"[audit] confronto SDMX saltato: colonne mancanti {missing}")
        return

    s["OBS_VALUE"] = pd.to_numeric(s["OBS_VALUE"], errors="coerce")
    s23 = s[
        (s["TIME_PERIOD"] == "2023")
        & s["AGE_NOCLASS"].str.fullmatch(r"Y\d+|Y_GE\d+", na=False)
        & s["GENDER"].isin(["M", "F"])
    ]

    checks = [
        (z1["count"].sum(), "TOTAL", "totale"),
        (
            z2.loc[z2["cittadinanza"] == "FRG", "count"].sum(),
            "FRGAPO",
            "stranieri",
        ),
    ]

    for sez_tot, citizenship, label in checks:
        selected = s23[s23["CITIZENSHIP"] == citizenship]
        if selected.empty:
            print(
                f"[audit] {label}: codice comunale {citizenship!r} non trovato; "
                "confronto saltato"
            )
            continue
        com_tot = selected["OBS_VALUE"].sum()
        print(
            f"[audit] {label}: sezioni {sez_tot:,.0f} vs comunale 2023 "
            f"{com_tot:,.1f} (scarto {sez_tot - com_tot:+,.1f})"
        )


def build_tables(
    *,
    level: str,
    sez_csv: Path,
    com_dir: Path,
    out_dir: Path,
) -> None:
    cfg = LEVELS[level]
    group_column: str = cfg["column"]
    expected: int = cfg["expected"]
    level_label: str = cfg["label"]

    if not sez_csv.exists():
        raise FileNotFoundError(f"CSV delle sezioni non trovato: {sez_csv}")

    out_dir.mkdir(parents=True, exist_ok=True)

    # Leggiamo i codici territoriali come stringhe; le variabili quantitative
    # vengono convertite esplicitamente subito dopo.
    b = pd.read_csv(sez_csv, dtype=str, keep_default_na=False)
    validate_columns(b, group_column)

    b[group_column] = normalize_code(b[group_column])
    if b[group_column].isna().any():
        n = int(b[group_column].isna().sum())
        raise ValueError(f"{n} righe senza codice valido in {group_column}")

    for column in NUMERIC_COLUMNS:
        b[column] = pd.to_numeric(b[column], errors="coerce").fillna(0.0)

    observed_codes = set(b[group_column].astype(str).unique())
    if len(observed_codes) != expected:
        raise ValueError(
            f"attesi {expected} {level_label}, trovati {len(observed_codes)}: "
            f"{sorted(observed_codes)}"
        )

    names = build_names_table(level, observed_codes)
    names.to_csv(out_dir / "zona_nomi.csv", index=False)

    groups = list(b.groupby(group_column, sort=True))

    # Z1: territorio x sesso x classi quinquennali
    z1 = pd.DataFrame(
        melt_block(groups, COLS_ETA_M, ETA5, "M", {})
        + melt_block(groups, COLS_ETA_F, ETA5, "F", {})
    ).rename(columns={"cat": "eta5"})
    z1.to_csv(out_dir / "z1_zona_sesso_eta5.csv", index=False)

    # Z2: territorio x sesso x macroeta x cittadinanza
    rows = (
        melt_block(groups, COLS_IT_M, MACROETA, "M", {"cittadinanza": "ITL"})
        + melt_block(groups, COLS_IT_F, MACROETA, "F", {"cittadinanza": "ITL"})
        + melt_block(groups, COLS_ST_M, MACROETA, "M", {"cittadinanza": "FRG"})
        + melt_block(groups, COLS_ST_F, MACROETA, "F", {"cittadinanza": "FRG"})
    )
    z2 = pd.DataFrame(rows).rename(columns={"cat": "macroeta"})
    z2.to_csv(out_dir / "z2_zona_sesso_macroeta_citt.csv", index=False)

    # Z3: territorio x sesso x istruzione (universo 9+)
    z3 = pd.DataFrame(
        melt_block(groups, COLS_EDU_M, EDU5, "M", {})
        + melt_block(groups, COLS_EDU_F, EDU5, "F", {})
    ).rename(columns={"cat": "istruzione5"})
    z3.to_csv(out_dir / "z3_zona_sesso_istruzione.csv", index=False)

    # Z4: territorio x sesso x occupato/non occupato (universo 15-64)
    rows = []
    negative_residuals = []
    for zona, sub in groups:
        pop_m = float(sub[["IT5", "ST26"]].sum().sum())
        pop_f = float(sub[["IT8", "ST29"]].sum().sum())
        occ_m = float(sub["P102"].sum())
        occ_f = float(sub["P103"].sum())

        if occ_m > pop_m:
            negative_residuals.append((str(zona), "M", occ_m - pop_m))
        if occ_f > pop_f:
            negative_residuals.append((str(zona), "F", occ_f - pop_f))

        rows.extend(
            [
                {"zona": str(zona), "sesso": "M", "occup": "occupato", "count": occ_m},
                {
                    "zona": str(zona),
                    "sesso": "M",
                    "occup": "non_occupato",
                    "count": max(pop_m - occ_m, 0.0),
                },
                {"zona": str(zona), "sesso": "F", "occup": "occupato", "count": occ_f},
                {
                    "zona": str(zona),
                    "sesso": "F",
                    "occup": "non_occupato",
                    "count": max(pop_f - occ_f, 0.0),
                },
            ]
        )

    z4 = pd.DataFrame(rows)
    z4.to_csv(out_dir / "z4_zona_sesso_occup.csv", index=False)

    # Audit delle sezioni e dei margini prodotti
    fake_count = 0
    if "SEZ21_ID" in b.columns:
        fake_count = int(
            b["SEZ21_ID"].astype(str).str.contains(r"888888|999999", regex=True).sum()
        )

    total_p1 = float(b["P1"].sum())
    total_sex = float(b["P2"].sum() + b["P3"].sum())
    total_foreign = float(b["ST1"].sum())

    print(
        f"[{level}] {expected} {level_label} | sezioni {len(b):,} | "
        f"fittizie {fake_count}"
    )
    print(
        f"[{level}] Z1 {len(z1)} righe | Z2 {len(z2)} | "
        f"Z3 {len(z3)} | Z4 {len(z4)}"
    )
    print(
        f"[audit] P1 sezioni: {total_p1:,.0f} | P2+P3: {total_sex:,.0f} "
        f"(scarto {total_sex - total_p1:+,.0f})"
    )
    print(
        f"[audit] Z1 totale: {z1['count'].sum():,.0f} "
        f"(scarto da P1 {z1['count'].sum() - total_p1:+,.0f})"
    )
    print(
        f"[audit] Z2 totale: {z2['count'].sum():,.0f} "
        f"(scarto da P1 {z2['count'].sum() - total_p1:+,.0f}) | "
        f"FRG: {z2.loc[z2['cittadinanza'] == 'FRG', 'count'].sum():,.0f} "
        f"(ST1 {total_foreign:,.0f})"
    )
    print(f"[audit] Z3 totale (universo 9+): {z3['count'].sum():,.0f}")
    print(
        f"[audit] Z4 totale (universo 15-64): {z4['count'].sum():,.0f} | "
        f"occupati: {z4.loc[z4['occup'] == 'occupato', 'count'].sum():,.0f}"
    )

    if negative_residuals:
        print("[warning] occupati superiori alla popolazione 15-64 in:")
        for zona, sex, excess in negative_residuals:
            print(f"  {zona} sesso={sex}: eccedenza {excess:,.1f}")

    audit_against_comune(z1, z2, com_dir)

    # Sanity qualitativa: unita' con maggiore quota di stranieri
    shares = z2.groupby(["zona", "cittadinanza"])["count"].sum().unstack(fill_value=0)
    denominator = shares.get("FRG", 0) + shares.get("ITL", 0)
    shares["quota_frg"] = shares.get("FRG", 0).div(denominator.where(denominator != 0))
    shares = shares.join(names.set_index("zona")).sort_values("quota_frg", ascending=False)

    print(f"\n[sanity] top-5 {level_label} per quota stranieri:")
    print(shares.head(5)[["nome", "quota_frg"]].round(3).to_string())
    print(f"\n[done] tabelle in {out_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Costruisce i blocchi territoriali Z1-Z4 per Bologna."
    )
    parser.add_argument(
        "--level",
        choices=sorted(LEVELS),
        default="quartieri",
        help="quartieri=COM_ASC1 (6); zone=COM_ASC2 (18). Default: quartieri",
    )
    parser.add_argument(
        "--sez-csv",
        type=Path,
        default=DEFAULT_SEZ_CSV,
        help=f"CSV delle sezioni (default: {DEFAULT_SEZ_CSV})",
    )
    parser.add_argument(
        "--com-dir",
        type=Path,
        default=DEFAULT_COM_DIR,
        help=f"Directory dei dati comunali SDMX (default: {DEFAULT_COM_DIR})",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Directory di output; se omessa dipende dal livello.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    if out_dir is None:
        out_dir = args.com_dir / LEVELS[args.level]["default_out"]

    build_tables(
        level=args.level,
        sez_csv=args.sez_csv.expanduser(),
        com_dir=args.com_dir.expanduser(),
        out_dir=out_dir.expanduser(),
    )


if __name__ == "__main__":
    main()
