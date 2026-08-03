from __future__ import annotations

import csv
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import gsp.common as G


# ---------------------------------------------------------------------
# Regioni
# ---------------------------------------------------------------------



# Assegnati da setup_regione().
BASE = SEZ_SHP = ANNCSU_CSV = OUT_DIR = None


def setup_regione(regione: str) -> None:
    """Fissa i path globali per la regione scelta."""
    global BASE, SEZ_SHP, ANNCSU_CSV, OUT_DIR
    if regione not in G.REGIONI:
        raise SystemExit(f"Regione '{regione}' sconosciuta. "
                         f"Disponibili: {sorted(G.REGIONI)}")
    BASE = Path(G.GEODATA) / regione
    SEZ_SHP = Path(G.path_shp(regione))
    ANNCSU_CSV = Path(G.path_anncsu(regione))
    OUT_DIR = BASE / "civici_sezioni_province"


# ---------------------------------------------------------------------
# Parametri
# ---------------------------------------------------------------------

CHUNK_SIZE = 200_000

# CRS metrico usato per il join e per le distanze.
# ETRS89 / UTM zone 32N: metri.
METRIC_CRS = "EPSG:25832"

# Fallback per punti non contenuti in alcun poligono.
NEAREST_MAX_DISTANCE = 20.0  # metri

# Margine attorno al bounding box della regione, in gradi. Serve a
# intercettare coordinate palesemente sbagliate senza scartare i civici
# ai bordi. I quattro estremi sono riempiti da load_sections() a partire
# dalle sezioni stesse, quindi lo script non va ritoccato per regione.
BBOX_MARGIN = 0.2
X_MIN = X_MAX = Y_MIN = Y_MAX = None
# Solo per dare un nome leggibile ai file di output: i codici provincia
# effettivi si ricavano dallo shapefile, così non c'è nulla da aggiornare
# quando si aggiunge una regione.


# Campi ANNCSU che vale la pena conservare, se presenti.
ANNCSU_OPTIONAL_COLUMNS = [
    "CODICE_COMUNE",
    "PROGRESSIVO_NAZIONALE",
    "PROGRESSIVO_ACCESSO",
    "ODONIMO",
    "DENOMINAZIONE",
    "LOCALITA",
    "CIVICO",
    "ESPONENTE",
    "SPECIFICITA",
    "METODO",
]


# ---------------------------------------------------------------------
# Funzioni di supporto
# ---------------------------------------------------------------------

def normalize_comune(series: pd.Series) -> pd.Series:
    """Normalizza i codici comunali ISTAT nel formato a sei cifre."""
    return (
        pd.to_numeric(series, errors="coerce")
        .astype("Int64")
        .astype("string")
        .str.zfill(6)
    )


def parse_coordinate(series: pd.Series) -> pd.Series:
    """
    Converte le coordinate ANNCSU in float.

    Gestisce sia il punto sia la virgola come separatore decimale e
    rimuove spazi ordinari/non separabili.
    """
    cleaned = (
        series.astype("string")
        .str.strip()
        .str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    return pd.to_numeric(cleaned, errors="coerce")


def detect_separator(csv_path: Path) -> str:
    """Prova a riconoscere il separatore del CSV ANNCSU."""
    with csv_path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
    ) as file:
        sample = file.read(200_000)

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=";,|\t",
        )
        return dialect.delimiter
    except csv.Error:
        return ";"


def check_paths() -> None:
    """Controlla che shapefile e indirizzario esistano."""
    print("[path] shapefile:", SEZ_SHP)
    print("[path] ANNCSU:    ", ANNCSU_CSV)

    if not SEZ_SHP.exists():
        raise FileNotFoundError(
            f"Shapefile non trovato:\n{SEZ_SHP}"
        )

    if not ANNCSU_CSV.exists():
        raise FileNotFoundError(
            f"CSV ANNCSU non trovato:\n{ANNCSU_CSV}"
        )


def anncsu_columns(separator: str) -> list[str]:
    """Determina le sole colonne ANNCSU necessarie e disponibili."""
    header = pd.read_csv(
        ANNCSU_CSV,
        sep=separator,
        encoding="utf-8-sig",
        nrows=0,
    )

    available = list(header.columns)
    required = [
        "CODICE_ISTAT",
        "COORD_X_COMUNE",
        "COORD_Y_COMUNE",
    ]

    missing = sorted(set(required) - set(available))
    if missing:
        raise RuntimeError(
            "Colonne ANNCSU mancanti: "
            f"{missing}\nColonne disponibili: {available}"
        )

    selected = required + [
        col for col in ANNCSU_OPTIONAL_COLUMNS
        if col in available
    ]

    print(f"[ANNCSU] colonne lette: {selected}")
    return selected


def load_sections() -> gpd.GeoDataFrame:
    """Carica e prepara le sezioni censuarie dell'Emilia-Romagna."""
    print("\n[sezioni] caricamento shapefile...")
    sections = gpd.read_file(SEZ_SHP)

    print(f"[sezioni] righe: {len(sections):,}")
    print(f"[sezioni] CRS originale: {sections.crs}")
    print(f"[sezioni] colonne: {list(sections.columns)}")

    if sections.crs is None:
        raise RuntimeError(
            "Lo shapefile non ha un CRS dichiarato."
        )

    required = {"PRO_COM", "SEZ21_ID", "geometry"}
    missing = sorted(required - set(sections.columns))
    if missing:
        raise RuntimeError(
            "Campi mancanti nello shapefile: "
            f"{missing}\nColonne disponibili: {list(sections.columns)}"
        )

    sections["_CODICE_ISTAT_SEZ"] = normalize_comune(
        sections["PRO_COM"]
    )
    sections["SEZ_COD_PROV"] = (
        sections["_CODICE_ISTAT_SEZ"].str[:3]
    )

    preferred = [
        "SEZ_COD_PROV",
        "PRO_COM",
        "SEZ21",
        "SEZ21_ID",
        "COM_ASC1",
        "COM_ASC2",
        "COM_ASC3",
        "geometry",
    ]
    sections = sections[
        [col for col in preferred if col in sections.columns]
    ].copy()

    # Bounding box in gradi: una sola trasformazione, non 60.000 poligoni.
    global X_MIN, X_MAX, Y_MIN, Y_MAX
    from shapely.geometry import box
    bb = gpd.GeoSeries([box(*sections.total_bounds)],
                       crs=sections.crs).to_crs("EPSG:4258").total_bounds
    X_MIN, X_MAX = bb[0] - BBOX_MARGIN, bb[2] + BBOX_MARGIN
    Y_MIN, Y_MAX = bb[1] - BBOX_MARGIN, bb[3] + BBOX_MARGIN
    print(f"[sezioni] bbox valido: X [{X_MIN:.3f}, {X_MAX:.3f}] "
          f"Y [{Y_MIN:.3f}, {Y_MAX:.3f}]")

    sections = sections.to_crs(METRIC_CRS)

    # Tutti i calcoli geometrici e le distanze avvengono in metri.
    sections = sections.to_crs(METRIC_CRS)

    print(f"[sezioni] CRS operativo: {sections.crs}")
    print("\n[sezioni] ripartizione per provincia:")

    codes = sorted(sections["SEZ_COD_PROV"].dropna().unique())
    province = {c: G.PROVINCE_NOMI.get(c, f"prov{c}") for c in codes}

    
    for code, name in province.items():
        n = int(sections["SEZ_COD_PROV"].eq(code).sum())
        print(f"  {code} {name:<22} {n:>8,} sezioni")
    ignoti = [c for c in codes if c not in G.PROVINCE_NOMI]
    if ignoti:
        print(f"[warning] province senza nome in gsp_common.PROVINCE_NOMI: {ignoti}")

    return sections, province


def available_output_columns(frame: pd.DataFrame) -> list[str]:
    """Seleziona le colonne da conservare negli output provinciali."""
    preferred = [
        "CODICE_ISTAT",
        "COD_PROV",
        "CODICE_COMUNE",
        "PROGRESSIVO_NAZIONALE",
        "PROGRESSIVO_ACCESSO",
        "ODONIMO",
        "DENOMINAZIONE",
        "LOCALITA",
        "CIVICO",
        "ESPONENTE",
        "SPECIFICITA",
        "COORD_X_COMUNE",
        "COORD_Y_COMUNE",
        "METODO",
        "PRO_COM",
        "SEZ21",
        "SEZ21_ID",
        "COM_ASC1",
        "COM_ASC2",
        "COM_ASC3",
        "join_method",
        "distanza_m",
    ]

    return [col for col in preferred if col in frame.columns]

INT_CODE_COLS = ["PRO_COM", "SEZ21", "SEZ21_ID",
                 "COM_ASC1", "COM_ASC2", "COM_ASC3"]


def cast_codes(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Codici territoriali come interi nullable.

    Il join spaziale con how='left' introduce NaN e promuove i codici a
    float64: senza questo cast i CSV contengono '34027001.0' e il merge
    contro i file sezioni (SEZ21_ID int64) non trova alcuna corrispondenza,
    silenziosamente.
    """
    out = frame.copy()
    for col in INT_CODE_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
    return out

def _one_match_per_point(
    joined: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Garantisce al massimo un poligono assegnato a ogni civico."""
    sort_cols = ["_row_id"]
    if "distanza_m" in joined.columns:
        sort_cols.append("distanza_m")
    if "SEZ21_ID" in joined.columns:
        sort_cols.append("SEZ21_ID")

    return (
        joined.sort_values(sort_cols, na_position="last")
        .drop_duplicates("_row_id", keep="first")
        .copy()
    )


def spatial_join(
    points: gpd.GeoDataFrame,
    sections: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Assegna ogni civico a una sezione:

    1. point-in-polygon con predicate='within';
    2. per i civici non assegnati, nearest entro 20 metri.
    """
    joined = gpd.sjoin(
        points,
        sections,
        how="left",
        predicate="within",
    )
    joined = _one_match_per_point(joined)

    joined["join_method"] = pd.NA
    joined["distanza_m"] = pd.NA
    joined.loc[
        joined["SEZ21_ID"].notna(),
        "join_method",
    ] = "within"

    missing_ids = joined.loc[
        joined["SEZ21_ID"].isna(),
        "_row_id",
    ]

    if missing_ids.empty:
        return joined.sort_values("_row_id").reset_index(drop=True)

    matched = joined.loc[
        joined["SEZ21_ID"].notna()
    ].copy()

    missing_points = points.loc[
        points["_row_id"].isin(missing_ids)
    ].copy()

    nearest = gpd.sjoin_nearest(
        missing_points,
        sections,
        how="left",
        max_distance=NEAREST_MAX_DISTANCE,
        distance_col="distanza_m",
    )
    nearest = _one_match_per_point(nearest)

    nearest["join_method"] = pd.NA
    nearest.loc[
        nearest["SEZ21_ID"].notna(),
        "join_method",
    ] = "nearest"

    result = pd.concat(
        [matched, nearest],
        ignore_index=True,
    )

    result = result.sort_values("_row_id").reset_index(drop=True)

    return gpd.GeoDataFrame(
        result,
        geometry="geometry",
        crs=points.crs,
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main(regione: str) -> None:
    setup_regione(regione)
    check_paths()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sections, PROVINCE = load_sections()

    separator = detect_separator(ANNCSU_CSV)
    print(
        f"\n[ANNCSU] separatore riconosciuto: {separator!r}"
    )
    usecols = anncsu_columns(separator)

    sections_by_province: dict[str, gpd.GeoDataFrame] = {}
    for code in PROVINCE:
        subset = sections.loc[
            sections["SEZ_COD_PROV"] == code
        ].copy()

        if subset.empty:
            raise RuntimeError(
                f"Nessuna sezione trovata per la provincia {code}"
            )

        # Il codice provincia delle sezioni è servito solo per separarle;
        # lo rimuoviamo per evitare collisioni con COD_PROV dei civici.
        sections_by_province[code] = subset.drop(
            columns=["SEZ_COD_PROV"],
            errors="ignore",
        )

    written = {code: False for code in PROVINCE}

    totals = {
        code: {
            "input": 0,
            "geocoded": 0,
            "no_coordinates": 0,
            "within": 0,
            "nearest": 0,
            "unmatched": 0,
            "fuori_comune": 0,
        }
        for code in PROVINCE
    }

    # Elimina gli output di eventuali esecuzioni precedenti.
    for code, name in PROVINCE.items():
        output_file = (
            OUT_DIR
            / f"{code}_{name}_civici_sezioni_asc.csv"
        )
        if output_file.exists():
            output_file.unlink()
            print(
                f"[output] eliminato file precedente: "
                f"{output_file.name}"
            )

    chunks = pd.read_csv(
        ANNCSU_CSV,
        sep=separator,
        encoding="utf-8-sig",
        dtype="string",
        usecols=usecols,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )

    for chunk_number, chunk in enumerate(chunks, start=1):
        chunk = chunk.copy()

        chunk["CODICE_ISTAT"] = normalize_comune(
            chunk["CODICE_ISTAT"]
        )
        chunk["COD_PROV"] = chunk["CODICE_ISTAT"].str[:3]

        chunk["COORD_X_COMUNE"] = parse_coordinate(
            chunk["COORD_X_COMUNE"]
        )
        chunk["COORD_Y_COMUNE"] = parse_coordinate(
            chunk["COORD_Y_COMUNE"]
        )

        # Identificativo unico entro l'intera esecuzione, utile per
        # eliminare eventuali match multipli.
        start_id = (chunk_number - 1) * CHUNK_SIZE
        chunk["_row_id"] = (
            np.arange(len(chunk), dtype=np.int64) + start_id
        )

        valid_coords = (
            chunk["COORD_X_COMUNE"].between(X_MIN, X_MAX)
            & chunk["COORD_Y_COMUNE"].between(Y_MIN, Y_MAX)
        )

        print(
            f"\n[chunk {chunk_number}] {len(chunk):,} righe | "
            f"coordinate valide: {int(valid_coords.sum()):,}"
        )

        if valid_coords.any():
            print(
                "  intervallo X:",
                f"{chunk.loc[valid_coords, 'COORD_X_COMUNE'].min():.6f}",
                "→",
                f"{chunk.loc[valid_coords, 'COORD_X_COMUNE'].max():.6f}",
            )
            print(
                "  intervallo Y:",
                f"{chunk.loc[valid_coords, 'COORD_Y_COMUNE'].min():.6f}",
                "→",
                f"{chunk.loc[valid_coords, 'COORD_Y_COMUNE'].max():.6f}",
            )

        for province_code, province_name in PROVINCE.items():
            part = chunk.loc[
                chunk["COD_PROV"] == province_code
            ].copy()

            if part.empty:
                continue

            totals[province_code]["input"] += len(part)

            part_valid = (
                part["COORD_X_COMUNE"].between(X_MIN, X_MAX)
                & part["COORD_Y_COMUNE"].between(Y_MIN, Y_MAX)
            )

            n_valid = int(part_valid.sum())
            totals[province_code]["geocoded"] += n_valid
            totals[province_code]["no_coordinates"] += (
                len(part) - n_valid
            )

            part = part.loc[part_valid].copy()

            if part.empty:
                print(
                    f"  {province_code} {province_name:<17} "
                    f"input={len(part_valid):>8,} coordinate=0"
                )
                continue

            # ANNCSU: X=longitudine, Y=latitudine in ETRS89.
            points = gpd.GeoDataFrame(
                part,
                geometry=gpd.points_from_xy(
                    part["COORD_X_COMUNE"],
                    part["COORD_Y_COMUNE"],
                ),
                crs="EPSG:4258",
            ).to_crs(METRIC_CRS)

            result = spatial_join(
                points,
                sections_by_province[province_code],
            )

            # ANNCSU attribuisce il civico a un comune, il join spaziale lo
            # colloca in una sezione: al confine le due attribuzioni possono
            # divergere. Non si corregge qui, si conta e si filtra a valle.
            pro_sez = pd.to_numeric(result["PRO_COM"],
                                    errors="coerce").astype("Int64")
            pro_civ = pd.to_numeric(result["CODICE_ISTAT"],
                                    errors="coerce").astype("Int64")
            n_fuori = int((pro_sez.notna() & (pro_sez != pro_civ)).sum())
            totals[province_code]["fuori_comune"] += n_fuori


            n_within = int(
                result["join_method"].eq("within").sum()
            )
            n_nearest = int(
                result["join_method"].eq("nearest").sum()
            )
            n_unmatched = int(result["SEZ21_ID"].isna().sum())

            totals[province_code]["within"] += n_within
            totals[province_code]["nearest"] += n_nearest
            totals[province_code]["unmatched"] += n_unmatched

            print(
                f"  {province_code} {province_name:<17} "
                f"input={len(part_valid):>8,} "
                f"coordinate={len(part):>8,} "
                f"within={n_within:>8,} "
                f"nearest={n_nearest:>6,} "
                f"fuori={n_unmatched:>6,} "
                f"fuori_comune={n_fuori:>6,}"
            )

            columns = available_output_columns(result)
            output_file = (
                OUT_DIR
                / f"{province_code}_{province_name}_"
                  "civici_sezioni_asc.csv"
            )

            cast_codes(result[columns]).to_csv(
                output_file, mode="a",
                header=not written[province_code], index=False)
            written[province_code] = True

    # Riepilogo finale.
    print("\n" + "=" * 115)
    print("RIEPILOGO")
    print("=" * 115)

    summary_rows = []

    for code, name in PROVINCE.items():
        stats = totals[code]
        summary_rows.append(
            {
                "cod_prov": code,
                "provincia": name,
                **stats,
            }
        )

        print(
            f"{code} {name:<17} "
            f"input={stats['input']:>10,}  "
            f"coordinate={stats['geocoded']:>10,}  "
            f"senza_coordinate={stats['no_coordinates']:>10,}  "
            f"within={stats['within']:>10,}  "
            f"nearest={stats['nearest']:>8,}  "
            f"fuori_sezione={stats['unmatched']:>8,}  "
            f"fuori_comune={stats['fuori_comune']:>7,}"
        )

    summary = pd.DataFrame(summary_rows)
    summary_file = OUT_DIR / "riepilogo_join_civici_sezioni.csv"
    summary.to_csv(summary_file, index=False)

    print(f"\nOutput salvati in:\n{OUT_DIR}")
    print(f"Riepilogo CSV:\n{summary_file}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="Aggancia i civici ANNCSU alle sezioni di censimento.")
    ap.add_argument("regione", choices=sorted(G.REGIONI),
                    help="regione da elaborare")
    main(ap.parse_args().regione)