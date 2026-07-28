#!/usr/bin/env python3
"""
profile_gibbs.py — dove va il tempo di una iterazione esterna del GibbsPCD.

Separa i due addendi di un'iterazione:
    n_gibbs_sweeps x _gibbs_sweep   (campionamento)
    1 x _estimate_expectations      (stima di alpha_hat)

Non costruisce F e non fa alcun fit: parte in secondi.

    python profile_gibbs.py 017029 --anno 2024 --livello K10C \
           --min-alpha 2e-4 --pool 400000 --numba
"""

import os
import sys
import glob
import json
import time
import importlib
import numpy as np


def import_repo():
    for base in ["~/progetti/maxent-popsynth-pcd", "/content/maxent-popsynth-pcd"]:
        hits = glob.glob(os.path.expanduser(base) + "/**/constraint_set.py",
                         recursive=True)
        if hits:
            moddir = os.path.dirname(hits[0])
            sys.path.insert(0, os.path.dirname(moddir))
            pkg = os.path.basename(moddir)
            cs_mod = importlib.import_module(f"{pkg}.constraint_set")
            gib = importlib.import_module(f"{pkg}.gibbs_pcd_solver")
            return cs_mod.ConstraintSet, gib.GibbsPCDSolver
    sys.exit("repo maxent-popsynth-pcd non trovato")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    comune = a[0]
    getf = lambda k, d: float(a[a.index(k) + 1]) if k in a else d
    geti = lambda k, d: int(a[a.index(k) + 1]) if k in a else d
    anno = geti("--anno", 2024)
    liv = a[a.index("--livello") + 1] if "--livello" in a else "K10C"
    ma = getf("--min-alpha", 0.0)
    N = geti("--pool", 400_000)
    s = geti("--sweeps", 5)
    use_numba = "--numba" in a

    ConstraintSet, GibbsPCDSolver = import_repo()
    cdir = os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")
    spec = json.load(open(os.path.join(cdir, f"cs_{liv}.json")))

    cs = ConstraintSet(spec["domain_sizes"])
    for c in spec["constraints"]:
        al = c["alpha"]
        if al <= 0 or al < ma:
            continue
        cs.add(c["attrs"], c["vals"], al)

    X = int(np.prod(spec["domain_sizes"]))
    print(f"[cs] {liv}: K={cs.K} m={cs.m} |X|={X:,} | pool N={N:,} "
          f"sweeps={s} numba={use_numba}")

    t0 = time.time()
    g = GibbsPCDSolver(cs, use_numba=use_numba)
    print(f"[init] solver in {time.time()-t0:.2f}s | "
          f"numba attivo: {getattr(g, '_numba_kernel', None) is not None}")

    pool = g._init_pool(N, seed=1)
    lam = np.random.default_rng(0).normal(scale=0.5, size=cs.m)

    sweep_fn = (g._gibbs_sweep_numba
                if (use_numba and getattr(g, "_numba_kernel", None) is not None)
                else g._gibbs_sweep)

    # warm-up: la prima chiamata Numba paga la compilazione JIT
    t0 = time.time(); pool = sweep_fn(pool, lam); t_jit = time.time() - t0
    print(f"[jit ] primo sweep (include compilazione): {t_jit:.2f}s")

    # --- campionamento ---
    ts = []
    for _ in range(s):
        t0 = time.time(); pool = sweep_fn(pool, lam); ts.append(time.time() - t0)
    t_sweeps = sum(ts)
    print(f"[sweep] {s} sweep: {t_sweeps:6.2f}s  "
          f"({np.mean(ts):.2f}s l'uno, min {min(ts):.2f} max {max(ts):.2f})")

    # --- stima delle aspettative ---
    te = []
    for _ in range(3):
        t0 = time.time(); ah = g._estimate_expectations(pool); te.append(time.time() - t0)
    t_est = float(np.median(te))
    print(f"[est  ] _estimate_expectations: {t_est:6.2f}s  "
          f"(mediana su 3; O(N*m) = {N*cs.m:.2e} confronti)")

    tot = t_sweeps + t_est
    print()
    print(f"[iter ] costo di UNA iterazione esterna: {tot:.2f}s")
    print(f"          campionamento        {t_sweeps:6.2f}s  {t_sweeps/tot*100:5.1f}%")
    print(f"          stima aspettative    {t_est:6.2f}s  {t_est/tot*100:5.1f}%")

    # --- quanto costerebbe la stima per blocchi ---
    sigs = {}
    for j in range(cs.m):
        sigs.setdefault(tuple(cs.attrs_list[j].tolist()), []).append(j)
    B = len(sigs)
    print()
    print(f"[blocchi] {B} firme distinte di attributi su m={cs.m} vincoli")
    print(f"          O(N*m) attuale   = {N*cs.m:.2e}")
    print(f"          O(N*B) possibile = {N*B:.2e}   "
          f"(fattore {cs.m/B:.0f}x sulla stima)")
    speranza = t_sweeps + t_est * B / cs.m
    print(f"          iterazione stimata dopo: {speranza:.2f}s "
          f"({tot/speranza:.1f}x sul totale)")

    # coerenza: le alpha_hat devono sommare a 1 dentro ogni blocco completo
    ds = np.asarray(cs.domain_sizes, dtype=np.int64)
    n_part = 0
    for sig, cols in sigs.items():
        if len(cols) == int(np.prod(ds[list(sig)])):
            n_part += 1
            tot_blk = ah[cols].sum()
            if abs(tot_blk - 1.0) > 1e-9:
                print(f"  ATTENZIONE blocco {sig}: somma alpha_hat = {tot_blk:.6f}")
    print(f"[check ] {n_part} blocchi completi, somma alpha_hat = 1: ok")


if __name__ == "__main__":
    main()
