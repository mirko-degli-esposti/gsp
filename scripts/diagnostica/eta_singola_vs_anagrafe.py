"""
eta_singola_vs_anagrafe.py — distanza fra la distribuzione sesso × età
singola di una popolazione (`eta_anni`, anello 3) e l'anagrafe comunale
(c1_sex_age_marital.csv). Sola lettura.

    python scripts/diagnostica/eta_singola_vs_anagrafe.py 036023 037006 ...
    python scripts/diagnostica/eta_singola_vs_anagrafe.py 036023 --pop /percorso/popolazione_K9C_avq_full.csv

Per ogni comune stampa:
    TV            variazione totale su sesso × età singola (0..100+)
    TV_blocco     parte dovuta ai totali dei blocchi d'età di enrich
                  (quinquenni, con 5-8 / 9 separati)
    TV_entro      parte entro blocco (età singola dato il blocco)
    rapp_min/max  T / anagrafe sulle celle con almeno 50 residenti
Introdotto il 10/10/2026 per la correzione di enrich (3d), gemello_stato_v2.
"""

import argparse
import glob
import os

import numpy as np
import pandas as pd

import gsp.common as G

TAGLI = [-1, 4, 8, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59, 64, 69, 74, 200]


def misura(pop_path, c1_path):
    p = pd.read_csv(pop_path, usecols=["sesso", "eta_anni"])
    an = pd.read_csv(c1_path).groupby(["sex", "age"])["count"].sum()
    an.index.names = ["s", "a"]
    t = p.assign(a=p["eta_anni"].astype(int).clip(upper=100)) \
         .groupby(["sesso", "a"]).size()
    t.index.names = ["s", "a"]
    x = pd.DataFrame({"an": an, "t": t}).fillna(0.0).reset_index()
    x["pa"], x["pt"] = x.an / x.an.sum(), x.t / x.t.sum()
    x["b"] = pd.cut(x.a, TAGLI)
    g = x.groupby(["s", "b"], observed=True)
    pb = g[["pa", "pt"]].transform("sum")
    # entro blocco: distribuzione condizionata, pesata con la massa di T
    entro = (x.pt - pb.pt * np.where(pb.pa > 0, x.pa / pb.pa.where(pb.pa > 0, 1), 0))
    r = x.t / x.an.where(x.an >= 50)
    return {"N": int(x.t.sum()),
            "TV": 0.5 * (x.pa - x.pt).abs().sum(),
            "TV_blocco": 0.5 * g[["pa", "pt"]].sum().diff(axis=1)["pt"].abs().sum(),
            "TV_entro": 0.5 * entro.abs().sum(),
            "rapp_min": r.min(), "rapp_max": r.max()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comuni", nargs="+")
    ap.add_argument("--anno", type=int, default=2024)
    ap.add_argument("--pop", default=None,
                    help="file popolazione esplicito (un solo comune)")
    a = ap.parse_args()
    righe = []
    for cod in a.comuni:
        cdir = G.path_constraints(cod, a.anno)
        if a.pop:
            pp = a.pop
        else:
            c = sorted(glob.glob(os.path.join(cdir, "popolazione_K*C_avq_full.csv")))
            if not c:
                print(f"{cod}: nessun _avq_full in {cdir}")
                continue
            pp = c[-1]
        righe.append({"comune": cod, "file": os.path.basename(pp),
                      **misura(pp, os.path.join(cdir, "c1_sex_age_marital.csv"))})
    with pd.option_context("display.width", 200, "display.float_format", "{:.4f}".format):
        print(pd.DataFrame(righe).to_string(index=False))


if __name__ == "__main__":
    main()
