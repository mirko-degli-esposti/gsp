#!/usr/bin/env python3
"""
test_moves.py — quanto si muove ciascun attributo durante uno sweep?

Un Gibbs a coordinata singola si blocca quando due attributi sono legati
quasi deterministicamente: nessuno dei due puo' cambiare da solo, e la
coppia resta congelata sul valore iniziale. La diagnosi diretta e' il
tasso di cambiamento per attributo: quante volte, su N individui, la
coordinata k esce da uno sweep con un valore diverso da quello con cui
e' entrata.

Misura anche l'entropia media della condizionale p(x_k | x_-k): se e'
prossima a zero la condizionale e' quasi deterministica e il valore e'
di fatto imposto dal resto della tupla.

    python scripts/gibbs/test_moves.py 017029 --anno 2024 --livello K10C --min-alpha 2e-4
    ... --scramble background,origine_genitori    # dallo stato perturbato
    ... --sweeps 5 --n 50000
"""

import os
import sys
import glob
import json
import importlib
import numpy as np
import pandas as pd


def import_repo():
    for base in ["~/progetti/maxent-popsynth-pcd", "/content/maxent-popsynth-pcd"]:
        hits = glob.glob(os.path.expanduser(base) + "/**/constraint_set.py",
                         recursive=True)
        if hits:
            d = os.path.dirname(hits[0])
            sys.path.insert(0, os.path.dirname(d))
            pkg = os.path.basename(d)
            return (importlib.import_module(f"{pkg}.constraint_set").ConstraintSet,
                    importlib.import_module(f"{pkg}.gibbs_pcd_solver").GibbsPCDSolver)
    sys.exit("repo maxent-popsynth-pcd non trovato")


def conditional_stats(g, cs, pool, lam, k, n_sample=4000, rng=None):
    """
    Entropia media (nat) di p(x_k | x_-k) e probabilita' media della
    modalita' piu' probabile, su un campione di individui.
    Ricostruisce la condizionale con la stessa logica di _gibbs_sweep.
    """
    rng = rng or np.random.default_rng(0)
    d_k = int(cs.domain_sizes[k])
    idx = rng.choice(len(pool), size=min(n_sample, len(pool)), replace=False)
    sub = pool[idx]
    logits = np.zeros((len(sub), d_k), dtype=np.float64)
    for (j, v_k, oth_attrs, oth_vals) in g.lookup[k]:
        if len(oth_attrs):
            ok = np.all(sub[:, oth_attrs] == oth_vals[np.newaxis, :], axis=1)
        else:
            ok = np.ones(len(sub), dtype=bool)
        logits[ok, v_k] += lam[j]
    logits -= logits.max(axis=1, keepdims=True)
    p = np.exp(logits)
    p /= p.sum(axis=1, keepdims=True)
    H = -np.sum(np.where(p > 0, p * np.log(p), 0.0), axis=1)
    return float(H.mean()), float(p.max(axis=1).mean()), d_k


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    comune = a[0]
    geti = lambda k, d: int(a[a.index(k) + 1]) if k in a else d
    getf = lambda k, d: float(a[a.index(k) + 1]) if k in a else d
    anno = geti("--anno", 2024)
    liv = a[a.index("--livello") + 1] if "--livello" in a else "K10C"
    ma = getf("--min-alpha", 0.0)
    n_sub = geti("--n", 0)
    n_sweeps = geti("--sweeps", 5)
    scr = a[a.index("--scramble") + 1] if "--scramble" in a else None

    ConstraintSet, GibbsPCDSolver = import_repo()
    cdir = os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")
    spec = json.load(open(os.path.join(cdir, f"cs_{liv}.json")))
    fit = json.load(open(os.path.join(cdir, f"fit_{liv}.json")))

    cs = ConstraintSet(spec["domain_sizes"])
    for c in spec["constraints"]:
        if c["alpha"] > 0 and c["alpha"] >= ma:
            cs.add(c["attrs"], c["vals"], c["alpha"])
    lam = np.asarray(fit["lambdas_exact"], dtype=np.float64)
    if len(lam) != cs.m:
        sys.exit(f"m={cs.m} ma lambdas_exact ne ha {len(lam)}")

    varn = spec["vars"]
    df = pd.read_csv(os.path.join(cdir, f"popolazione_{liv}.csv"))
    pool = np.empty((len(df), len(varn)), dtype=np.int32)
    for i, v in enumerate(varn):
        m_ = {c: k for k, c in enumerate(spec["categories"][v])}
        pool[:, i] = df[v].astype(str).map(m_).to_numpy(dtype=np.int32)
    rng = np.random.default_rng(0)
    if n_sub and n_sub < len(pool):
        pool = pool[rng.choice(len(pool), n_sub, replace=False)]
    if scr:
        for c in [x.strip() for x in scr.split(",")]:
            k = varn.index(c)
            pool[:, k] = rng.integers(0, spec["domain_sizes"][k], size=len(pool))
        print(f"[scr] randomizzate: {scr}")

    N = len(pool)
    print(f"[cs] {liv}: m={cs.m}  N={N:,}  sweeps={n_sweeps}\n")

    g = GibbsPCDSolver(cs, use_numba=True)
    sweep = (g._gibbs_sweep_numba
             if getattr(g, "_numba_kernel", None) is not None
             else g._gibbs_sweep)

    # entropia delle condizionali nello stato iniziale
    print(f"{'attributo':>20} {'d_k':>4} {'H(cond)':>9} {'H/H_max':>8} "
          f"{'p_max':>7}   condizionale")
    stats = {}
    for k, v in enumerate(varn):
        H, pmax, d_k = conditional_stats(g, cs, pool, lam, k, rng=rng)
        Hmax = np.log(d_k)
        stats[v] = (H, Hmax, pmax)
        flag = ("QUASI DETERMINISTICA" if H < 0.15 * Hmax else
                "stretta" if H < 0.45 * Hmax else "larga")
        print(f"{v:>20} {d_k:>4} {H:9.4f} {H/Hmax:8.3f} {pmax:7.3f}   {flag}")

    # tasso di cambiamento per sweep
    print(f"\n{'attributo':>20} " +
          " ".join(f"{'sw'+str(s+1):>8}" for s in range(n_sweeps)) +
          "     media")
    rates = np.zeros((n_sweeps, len(varn)))
    for s in range(n_sweeps):
        before = pool.copy()
        pool = sweep(pool, lam)
        rates[s] = (pool != before).mean(axis=0)
    for k, v in enumerate(varn):
        row = " ".join(f"{rates[s, k]*100:7.2f}%" for s in range(n_sweeps))
        print(f"{v:>20} {row}  {rates[:, k].mean()*100:7.2f}%")

    print(f"\n  Nota: il tasso e' la frazione di individui in cui la "
          f"coordinata cambia valore.")
    print(f"  Se una coordinata si muove nell'ordine dell'1% o meno, il "
          f"tempo di rilassamento")
    print(f"  su quella direzione e' di ~100 sweep o piu': con "
          f"n_gibbs_sweeps=5 il pool non")
    print(f"  la riequilibra mai fra un aggiornamento di lambda e il "
          f"successivo.")

    slow = [v for k, v in enumerate(varn) if rates[:, k].mean() < 0.02]
    if slow:
        print(f"\n  COORDINATE LENTE (<2% per sweep): {slow}")
        print(f"  -> candidate per l'aggiornamento a blocchi congiunto.")


if __name__ == "__main__":
    main()
