"""
fetch_comune_v2.py - scarica e profila tavole ISTAT SDMX per un comune.

Uso:
    python fetch_comune_v2.py 037006 --explore
    python fetch_comune_v2.py 037006
    python fetch_comune_v2.py 037006 --only cens_istruzione_eta
    python fetch_comune_v2.py 037006 --profile cens_condprof_eta
    python fetch_comune_v2.py 037006 --profile cens_condprof_eta --max-values 40

La modalita --profile:
    - scarica una sola tavola per il comune;
    - mostra quali dimensioni variano realmente e quali sono fisse;
    - elenca i codici effettivamente presenti, con etichetta e numero di righe;
    - salva il profilo completo in
      ~/progetti/gsp/data/comuni/<codice>/<tavola>_profile.csv.

Il modulo istat_sdmx.py deve essere nella stessa cartella o nel PYTHONPATH.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Any

import pandas as pd

import istat_sdmx as sdmx


# ----------------------------------------------------------------------
# Rosa dei fondamentali.
# spec: vincoli espliciti per dimensione; tutto il resto in wildcard.
# La dimensione territorio viene individuata e riempita automaticamente.
# ----------------------------------------------------------------------
CORE = {
    "anag_sesso_eta_statociv": {
        "flow": "22_289_DF_DCIS_POPRES1_26",
        "spec": {
            "FREQ": "A",
            "DATA_TYPE": "JAN",
            "SEX": ["1", "2"],
            "MARITAL_STATUS": ["1", "2", "3", "4", "15", "16", "17"],
        },
    },
    "cens_sesso_eta_cittadinanza": {
        "flow": "DF_DCSS_POP_DEMCITMIG_SETA_1",
        "spec": {},
    },
    "cens_istruzione_eta": {
        "flow": "DF_DCSS_ISTR_LAV_PEN_2_TV_1",
        "spec": {},
    },
    "cens_istruzione_cittadinanza": {
        "flow": "DF_DCSS_ISTR_LAV_PEN_2_TV_2",
        "spec": {},
    },
    "cens_condprof_eta": {
        "flow": "DF_DCSS_ISTR_LAV_PEN_2_TV_3",
        "spec": {},
    },
    "cens_condprof_cittadinanza": {
        "flow": "DF_DCSS_ISTR_LAV_PEN_2_TV_4",
        "spec": {},
    },
    "cens_stranieri_paesi": {
        "flow": "DF_DCSS_POP_DEMCITMIG_TV_3",
        "spec": {},
    },
    "cens_migr_backg":             {"flow": "DF_DCSS_MIGR_BACKG_PAR_TV_1_COM", "spec": {}},
    "cens_posizione_famiglia": {"flow": "DF_DCSS_HCUE_COM_2_COM", "spec": {}},
    "cens_posizione_prof":     {"flow": "DF_DCSS_EMPLP_1_COM", "spec": {}},
    "cens_settore_prof": {"flow": "DF_DCSS_EMPLP_2_COM", "spec": {}},
}


def output_dir(comune: str) -> str:
    """Cartella di output del comune."""
    path = os.path.expanduser(f"~/progetti/gsp/data/comuni/{comune}")
    os.makedirs(path, exist_ok=True)
    return path


def find_territory_dim(xml_path: str, comune: str):
    """Trova la dimensione la cui codelist contiene il codice comune."""
    codelists = sdmx.load_codelists(xml_path)
    for dim, codes in codelists.items():
        if comune in codes:
            return dim, codes[comune]
    return None, None


def make_spec(xml_path: str, comune: str, base_spec: dict[str, Any]):
    """Aggiunge alla spec il vincolo territoriale del comune."""
    terr_dim, terr_label = find_territory_dim(xml_path, comune)
    if terr_dim is None:
        raise ValueError(
            f"codice comune {comune} non presente in nessuna codelist territoriale"
        )

    spec = dict(base_spec)
    spec[terr_dim] = comune
    return spec, terr_dim, terr_label


def explore(comune: str, tables: dict):
    """Mostra DSD e codelist senza scaricare le osservazioni."""
    for name, cfg in tables.items():
        flow = cfg["flow"]
        try:
            xml_path = sdmx.get_structure(flow)
        except Exception as exc:
            print(f"\n=== {name} [{flow}] ===\n  ERRORE struttura: {exc}")
            continue

        dims = sdmx.dsd_dimensions(xml_path)
        codelists = sdmx.load_codelists(xml_path)
        terr_dim, terr_label = find_territory_dim(xml_path, comune)

        print(f"\n=== {name} [{flow}] ===")
        for dim in dims:
            n_codes = len(codelists.get(dim, {}))
            mark = "  <-- TERRITORIO (comune presente)" if dim == terr_dim else ""
            examples = list(codelists.get(dim, {}).items())[:4]
            print(
                f"  {dim:<22} codelist:{n_codes:>6} codici  "
                f"es. {examples}{mark}"
            )

        if terr_dim is None:
            print(
                f"  !! codice {comune} NON presente in nessuna codelist "
                "(tavola non comunale o codifica territorio diversa)"
            )
        else:
            print(f"  territorio: {terr_dim} = {comune} ({terr_label})")


def fetch_all(comune: str, tables: dict):
    """Scarica e salva tutte le tavole selezionate."""
    out_dir = output_dir(comune)
    summary = []

    for name, cfg in tables.items():
        flow = cfg["flow"]

        try:
            xml_path = sdmx.get_structure(flow)
            spec, _, _ = make_spec(xml_path, comune, cfg["spec"])
            df = sdmx.fetch(flow, spec)
        except Exception as exc:
            print(f"[errore] {name}: {exc}")
            summary.append((name, "ERR", 0))
            continue

        if df.empty:
            summary.append((name, "VUOTA", 0))
            continue

        raw_path = os.path.join(out_dir, f"{name}_raw.csv")
        decoded_path = os.path.join(out_dir, f"{name}_decoded.csv")

        df.to_csv(raw_path, index=False)
        decoded = sdmx.decode(df, xml_path)
        decoded.to_csv(decoded_path, index=False)

        periods = (
            sorted(decoded["TIME_PERIOD"].dropna().astype(str).unique())
            if "TIME_PERIOD" in decoded.columns
            else []
        )
        summary.append((name, "OK", len(decoded)))
        print(f"[ok] {name}: {len(decoded)} righe, periodi {periods}")

    print(f"\n--- riepilogo ({out_dir}) ---")
    for name, status, n_rows in summary:
        print(f"  {name:<30} {status:<6} {n_rows:>7} righe")


def _code_to_text(value: Any) -> str:
    """Converte un valore letto da pandas in una rappresentazione di codice."""
    if pd.isna(value):
        return "<NA>"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _resolve_codelist_code(code: str, mapping: dict[str, str]) -> str:
    """Riconcilia, quando univoco, un codice cui pandas ha tolto zeri iniziali."""
    if code in mapping or code == "<NA>":
        return code

    stripped = code.lstrip("0") or "0"
    candidates = [
        candidate
        for candidate in mapping
        if (candidate.lstrip("0") or "0") == stripped
    ]
    return candidates[0] if len(candidates) == 1 else code


def _natural_key(value: str):
    """Chiave per ordinare in modo naturale codici come 2, 10, Y2, Y10."""
    return [
        int(token) if token.isdigit() else token.casefold()
        for token in re.split(r"(\d+)", value)
    ]


def _format_constraint(value: Any) -> str:
    if value is None:
        return "wildcard"
    if isinstance(value, (list, tuple)):
        return "+".join(str(item) for item in value)
    return str(value)


def _profile_dimension(
    df: pd.DataFrame,
    dim: str,
    mapping: dict[str, str],
    query_constraint: Any,
) -> list[dict[str, Any]]:
    """Costruisce le righe del profilo per una dimensione."""
    raw_codes = df[dim].map(_code_to_text)
    # Risolvi ogni codice distinto una sola volta: REF_AREA puo avere
    # codelist con oltre 12.000 valori e la tavola puo contenere molte righe.
    resolution = {
        code: _resolve_codelist_code(code, mapping)
        for code in raw_codes.unique()
    }
    resolved_codes = raw_codes.map(resolution)
    counts = resolved_codes.value_counts(dropna=False)

    actual = set(counts.index.astype(str))
    ordered = [code for code in mapping if code in actual]
    ordered.extend(sorted(actual - set(ordered), key=_natural_key))

    n_distinct = len(ordered)
    status = "FISSA" if n_distinct == 1 else "VARIA"
    constraint_text = _format_constraint(query_constraint)

    rows = []
    for code in ordered:
        rows.append(
            {
                "dimension": dim,
                "status": status,
                "n_distinct": n_distinct,
                "query_constraint": constraint_text,
                "code": code,
                "label": mapping.get(code, "<etichetta non trovata>"),
                "rows": int(counts.get(code, 0)),
            }
        )
    return rows


def profile(comune: str, table_name: str, max_values: int = 30):
    """Scarica una tavola e profila i valori realmente presenti."""
    cfg = CORE[table_name]
    flow = cfg["flow"]
    xml_path = sdmx.get_structure(flow)
    spec, terr_dim, terr_label = make_spec(xml_path, comune, cfg["spec"])

    print(f"\n[profile] scarico {table_name} [{flow}]")
    df = sdmx.fetch(flow, spec)
    if df.empty:
        print("[profile] la query non ha restituito osservazioni")
        return

    codelists = sdmx.load_codelists(xml_path)
    dsd_dims = sdmx.dsd_dimensions(xml_path)
    profile_dims = [dim for dim in dsd_dims if dim in df.columns]
    if "TIME_PERIOD" in df.columns:
        profile_dims.append("TIME_PERIOD")

    print(f"\n=== PROFILO {table_name} ===")
    print(f"flow:       {flow}")
    print(f"territorio: {terr_dim} = {comune} ({terr_label})")
    print(f"righe:      {len(df)}")
    print(f"colonne:    {', '.join(df.columns)}")
    print("query:")
    for dim in dsd_dims:
        print(f"  {dim:<22} {_format_constraint(spec.get(dim))}")

    if "OBS_VALUE" in df.columns:
        obs = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
        if obs.notna().any():
            print(
                "OBS_VALUE:  "
                f"{obs.notna().sum()} valori numerici; "
                f"min={obs.min():g}; max={obs.max():g}; somma={obs.sum():,.0f}"
            )
        if "TIME_PERIOD" in df.columns:
            per_anno = df.assign(_v=obs).groupby("TIME_PERIOD")["_v"].agg(["sum", "size"])
            print("somme per periodo (utile per riconoscere aggregati e universi):")
            for anno, r in per_anno.iterrows():
                print(f"  {anno}: somma={r['sum']:,.0f} su {int(r['size'])} righe")

    all_rows: list[dict[str, Any]] = []

    for dim in profile_dims:
        mapping = codelists.get(dim, {})
        dim_rows = _profile_dimension(df, dim, mapping, spec.get(dim))
        all_rows.extend(dim_rows)

        n_distinct = dim_rows[0]["n_distinct"] if dim_rows else 0
        status = dim_rows[0]["status"] if dim_rows else "VUOTA"
        constraint = _format_constraint(spec.get(dim))

        print(
            f"\n{dim} - {status}, {n_distinct} codici effettivi, "
            f"vincolo query: {constraint}"
        )
        print(f"  {'codice':<18} {'righe':>10}  etichetta")

        shown = dim_rows[:max_values]
        for row in shown:
            print(f"  {row['code']:<18} {row['rows']:>10}  {row['label']}")

        omitted = len(dim_rows) - len(shown)
        if omitted > 0:
            print(
                f"  ... altri {omitted} codici non mostrati; "
                "sono inclusi nel CSV del profilo"
            )
    # somme di OBS_VALUE per codice: distingue aggregati da modalita' elementari
    if "OBS_VALUE" in df.columns:
        obs = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
        print("\n=== somme per codice (aggregati vs elementari) ===")
        for dim in profile_dims:
            if dim == "TIME_PERIOD":
                continue
            s = df.assign(_v=obs).groupby(df[dim].map(_code_to_text))["_v"].sum()
            if len(s) <= 1:
                continue
            mapping = codelists.get(dim, {})
            print(f"\n{dim}:")
            for code, val in s.sort_values(ascending=False).head(max_values).items():
                lbl = mapping.get(_resolve_codelist_code(str(code), mapping), "")
                print(f"  {str(code):<18} {val:>14,.0f}  {lbl[:60]}")

    profile_df = pd.DataFrame(all_rows)
    profile_df.insert(0, "table", table_name)
    profile_df.insert(1, "flow", flow)
    profile_df.insert(2, "comune", comune)
    profile_df.insert(3, "territory_label", terr_label)

    out_path = os.path.join(output_dir(comune), f"{table_name}_profile.csv")
    profile_df.to_csv(out_path, index=False)
    print(f"\n[profile] profilo completo salvato in: {out_path}")


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Scarica ed esplora tavole ISTAT SDMX per un comune."
    )
    parser.add_argument(
        "comune",
        help="codice ISTAT comunale a sei cifre, per esempio 037006 per Bologna",
    )
    parser.add_argument(
        "--explore",
        action="store_true",
        help="mostra DSD e codelist senza scaricare le osservazioni",
    )
    parser.add_argument(
        "--only",
        choices=sorted(CORE),
        help="limita --explore o il download ordinario a una sola tavola",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(CORE),
        metavar="TAVOLA",
        help="scarica e profila una singola tavola",
    )
    parser.add_argument(
        "--max-values",
        type=int,
        default=30,
        help="numero massimo di codici mostrati a video per dimensione (default: 30)",
    )
    args = parser.parse_args(argv)

    if not re.fullmatch(r"\d{6}", args.comune):
        parser.error("il codice comune deve contenere esattamente sei cifre")
    if args.max_values < 1:
        parser.error("--max-values deve essere almeno 1")
    if args.profile and args.explore:
        parser.error("--profile e --explore non possono essere usati insieme")
    if args.profile and args.only:
        parser.error("con --profile la tavola e gia specificata; non usare --only")

    return args


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    if args.profile:
        profile(args.comune, args.profile, args.max_values)
        return

    tables = {args.only: CORE[args.only]} if args.only else CORE
    if args.explore:
        explore(args.comune, tables)
    else:
        fetch_all(args.comune, tables)


if __name__ == "__main__":
    try:
        main()
    except KeyError as exc:
        sys.exit(f"Tavola sconosciuta: {exc}")
    except KeyboardInterrupt:
        sys.exit("\nInterrotto dall'utente")
