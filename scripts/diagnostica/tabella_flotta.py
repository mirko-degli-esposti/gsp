"""
scripts/diagnostica/tabella_flotta.py — la tabella di flotta dai log di rigenera.

Per ogni comune della corsa, estrae dal log le misure che il pilota di
soglia ha reso canoniche (note/misure/soglia_taglia_er.md):
  anello 1  MRE finale, supporto (stati con massa / lattice), H,
            individui per stato (= pop / supporto: IL criterio di soglia)
  anello 2  donatori distinti, riuso medio, scarto max e mediano delle
            correlazioni sintetico-vs-AVQ
  anello 3  MAE per sezione (popolazione, stranieri, UE) e correlazioni
  riepilogo esito, tempo, tier
piu' pop e livello dal registro. Scrive un CSV (una riga per comune:
nessuno la scrive a mano) e stampa le distribuzioni per fascia di
popolazione — la verifica EX POST del criterio di soglia su tutta la
flotta invece che su tre comuni.

Uso:
    python scripts/diagnostica/tabella_flotta.py log/rigenera_20260902_HHMM \
        --out note/misure/rilancio_v2/tabella_flotta.csv
Piu' corse (es. i 14 storici in un'altra directory):
    python scripts/diagnostica/tabella_flotta.py log/rigenera_A log/rigenera_B --out ...
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

import gsp.common as G

# --- i pattern, uno per riga di log; i gruppi hanno il nome della colonna
PATTERNS = {
    "fit": re.compile(
        r"\[exact\] MRE\(alpha>0\)=(?P<mre>[\d.e+-]+) \| massa su celle escluse: "
        r"somma=(?P<massa_escl>[\d.e+-]+) \(n=(?P<n_escl>\d+)\) \| H=(?P<H>[\d.]+) nat "
        r"\| supporto~(?P<supporto>\d+)/(?P<lattice>\d+)"),
    "donor": re.compile(
        r"\[donor\] donatori distinti usati: (?P<donatori>[\d,]+) su [\d,]+ "
        r"\((?P<donatori_pct>[\d.]+)%\) \| riuso medio (?P<riuso>[\d.]+)x"),
    "corr": re.compile(
        r"\[val\] scarto \|sintetico - donatori\| su (?P<coppie>\d+) coppie: "
        r"max (?P<corr_max>[\d.]+) \| mediano (?P<corr_med>[\d.]+)"),
    "mae_pop": re.compile(
        r"popolazione\s+MAE\s+(?P<mae_pop>[\d.]+) su media\s+(?P<sez_media>[\d.]+) "
        r"\| corr (?P<corr_pop>[\d.]+) \| totale (?P<tot_pop>[\d,]+) vs (?P<tot_cens>[\d,]+)"),
    "mae_str": re.compile(
        r"stranieri\s+MAE\s+(?P<mae_str>[\d.]+) su media\s+[\d.]+ \| corr (?P<corr_str>[\d.]+)"),
    "mae_ue": re.compile(
        r"UE\s+MAE\s+(?P<mae_ue>[\d.]+) su media\s+[\d.]+ \| corr (?P<corr_ue>[\d.]+)"),
    "tier": re.compile(r"^\[3c\] paese.*tier (?P<tier>\d+)"),
}


def _num(s):
    return float(str(s).replace(",", ""))


def leggi_log(path):
    riga = {"cod": path.stem}
    for l in path.read_text(encoding="utf-8", errors="replace").splitlines():
        for nome, pat in PATTERNS.items():
            m = pat.search(l)
            if m:
                riga.update({k: v for k, v in m.groupdict().items()})
    return riga


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logdir", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    righe = []
    for d in a.logdir:
        for p in sorted(Path(d).glob("[0-9]*.log")):
            r = leggi_log(p)
            if "mre" not in r:
                print(f"  [!] {p.name}: fit non trovato nel log (KO?)", file=sys.stderr)
            righe.append(r)
    t = pd.DataFrame(righe)

    # tipi e derivate
    for c in ["mre", "massa_escl", "H", "supporto", "lattice", "donatori",
              "donatori_pct", "riuso", "coppie", "corr_max", "corr_med",
              "mae_pop", "sez_media", "corr_pop", "tot_pop", "tot_cens",
              "mae_str", "corr_str", "mae_ue", "corr_ue", "n_escl", "tier"]:
        if c in t:
            t[c] = t[c].map(_num)
    t["nome"] = t["cod"].map(lambda c: G.info(c)["nome"])
    t["livello"] = t["cod"].map(lambda c: "K6C" if G.info(c)["livello"] is None else "K9C")
    t["stato"] = t["cod"].map(lambda c: G.info(c).get("stato"))
    t["pop"] = t["tot_pop"]
    t["ind_per_stato"] = t["pop"] / t["supporto"]          # IL criterio
    t["mae_pop_rel"] = t["mae_pop"] / t["sez_media"]
    t["rumore_corr"] = 1 / t["pop"] ** 0.5                 # 1/sqrt(n)
    t["corr_max_sigma"] = t["corr_max"] / t["rumore_corr"]

    cols = ["cod", "nome", "stato", "livello", "pop", "tot_cens", "mre", "supporto",
            "ind_per_stato", "H", "n_escl", "massa_escl", "donatori",
            "donatori_pct", "riuso", "corr_max", "corr_med", "corr_max_sigma",
            "mae_pop", "sez_media", "mae_pop_rel", "corr_pop", "mae_str",
            "corr_str", "mae_ue", "corr_ue", "tier"]

     # --- verifiche di flotta
    print(f"\nmassa su celle escluse: max {t['massa_escl'].max():.1e}  "
          f"(atteso 0: le 34-36 esclusioni a massa zero ovunque)")
    print(f"totale pop vs cens: {int((t['tot_pop'] != t['tot_cens']).sum())} "
          f"comuni con scarto (atteso 0)")

    t = t[[c for c in cols if c in t]].sort_values("pop", ascending=False)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(out, index=False)
    print(f"scritto {out}: {len(t)} comuni")

   

    # --- distribuzioni per fascia: la verifica ex post della soglia
    t["fascia"] = pd.cut(t["pop"], [0, 3000, 5000, 10000, 20000, 50000, 10**7],
                         labels=["<3k", "3-5k", "5-10k", "10-20k", "20-50k", ">50k"])
    agg = t.groupby("fascia", observed=True).agg(
        n=("cod", "size"),
        mre=("mre", "median"),
        ind_per_stato=("ind_per_stato", "median"),
        riuso=("riuso", "median"),
        corr_max_sigma=("corr_max_sigma", "median"),
        mae_pop_rel=("mae_pop_rel", "median"),
        corr_str=("corr_str", "median"),
    )
    pd.set_option("display.width", 140)
    print("\nmediane per fascia (il criterio di soglia su tutta la flotta):")
    print(agg.round(3).to_string())
    print("\nind_per_stato: sotto 1 = campione piu' piccolo del proprio modello")
    print(f"comuni con ind_per_stato < 1: {int((t['ind_per_stato'] < 1).sum())}"
          f"  (atteso: solo i pilota sotto soglia, se inclusi)")


if __name__ == "__main__":
    main()