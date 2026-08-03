#!/usr/bin/env python3
"""
test_invariance.py — il kernel Gibbs lascia invariante p_lambda?

Test decisivo, e senza alcuna ottimizzazione di mezzo. La popolazione
salvata e' un campione i.i.d. da p_exact = softmax(F lambda_exact); quella
distribuzione E' per costruzione la stazionaria della catena di Gibbs a
lambda_exact fissati. Un kernel corretto deve quindi lasciarla invariante:
le alpha_hat devono restare al pavimento di campionamento per sempre.

  - restano al pavimento  -> il campionatore e' corretto, il colpevole
                             delle derive osservate e' l'ottimizzatore
  - degradano sweep dopo  -> il kernel NON ha p_lambda come stazionaria:
    sweep                    e' un bug, non un problema di mixing

Confronta i due kernel (NumPy e Numba): se solo uno dei due rompe
l'invarianza, il bug e' localizzato.

    python scripts/gibbs/test_invariance.py 017029 --anno 2024 --livello K10C \
        --min-alpha 2e-4 --sweeps 20 --kernel both
    ... --n 50000        # sottocampiona la popolazione (il NumPy e' lento)

TEST DI MIXING (--scramble). Con --scramble si randomizzano una o piu'
colonne prima di partire, e si misura in quanti sweep il sistema torna
all'equilibrio, blocco per blocco. L'invarianza dice che l'equilibrio e'
quello giusto; il mixing dice se ci si arriva in tempo utile.

    ... --scramble settore                       # la condizione iniziale
    ... --scramble background,origine_genitori   #   esatta del warm start
    ... --scramble all --sweeps 200
"""

import os
import sys
import glob
import json
import time
import importlib
import numpy as np
import pandas as pd

SIG_BY_NAMES = {
    ("eta", "sesso", "stato_civile"): "A",
    ("cittadinanza", "eta", "sesso"): "B",
    ("eta", "istruzione", "sesso"): "C",
    ("condizione", "eta", "sesso"): "D",
    ("cittadinanza", "istruzione"): "E",
    ("cittadinanza", "condizione"): "F",
    ("eta", "istruzione"): "Si",
    ("condizione", "eta"): "Sc",
    ("eta", "sesso", "zona"): "Z1",
    ("cittadinanza", "eta", "sesso", "zona"): "Z2",
    ("istruzione", "sesso", "zona"): "Z3",
    ("condizione", "eta", "sesso", "zona"): "Z4",
    ("background", "sesso"): "G",
    ("background", "origine_genitori", "sesso"): "H",
    ("background", "sesso", "zona"): "Z5",
    ("background", "cittadinanza"): "GC",
    ("sesso", "settore"): "M",
    ("condizione", "settore"): "MC",
}


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


def build_blocks(cs):
    ds = np.asarray(cs.domain_sizes, dtype=np.int64)
    groups = {}
    for j in range(cs.m):
        groups.setdefault(tuple(cs.attrs_list[j].tolist()), []).append(j)
    out = []
    for sig, js in groups.items():
        attrs = np.array(sig, dtype=np.int64)
        sizes = ds[attrs]
        cells = np.empty(len(js), dtype=np.int64)
        for t, j in enumerate(js):
            code = 0
            for p in range(len(attrs)):
                code = code * int(sizes[p]) + int(cs.vals_list[j][p])
            cells[t] = code
        out.append((attrs, sizes, int(np.prod(sizes)), cells,
                    np.array(js, dtype=np.int64)))
    return out


def alphas_of(pool, blocks, m):
    N = len(pool)
    a = np.empty(m, dtype=np.float64)
    code = np.empty(N, dtype=np.int64)
    for attrs, sizes, n_cells, cells, js in blocks:
        code[:] = pool[:, attrs[0]]
        for p in range(1, len(attrs)):
            code *= sizes[p]
            code += pool[:, attrs[p]]
        a[js] = np.bincount(code, minlength=n_cells)[cells] / N
    return a


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
    max_sweeps = geti("--sweeps", 20)
    which = a[a.index("--kernel") + 1] if "--kernel" in a else "both"
    scr = a[a.index("--scramble") + 1] if "--scramble" in a else None

    ConstraintSet, GibbsPCDSolver = import_repo()
    cdir = os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")
    spec = json.load(open(os.path.join(cdir, f"cs_{liv}.json")))
    fit = json.load(open(os.path.join(cdir, f"fit_{liv}.json")))

    # --- CS nell'ORDINE ESATTO dei lambda salvati (eps=0, come cs_g) ---
    cs = ConstraintSet(spec["domain_sizes"])
    sig = []
    for c in spec["constraints"]:
        al = c["alpha"]
        if al <= 0 or al < ma:
            continue
        cs.add(c["attrs"], c["vals"], al)
        sig.append([list(c["attrs"]), list(c["vals"])])
    lam = np.asarray(fit["lambdas_exact"], dtype=np.float64)
    if len(lam) != cs.m:
        sys.exit(f"m={cs.m} ma lambdas_exact ha {len(lam)} elementi: "
                 f"min_alpha diverso da quello del fit "
                 f"({fit.get('min_alpha')})?")
    ks = fit.get("kept_sig_exact")
    if ks and not all(list(x[0]) == y[0] and list(x[1]) == y[1]
                      for x, y in zip(ks, sig)):
        sys.exit("l'ordine dei vincoli NON coincide con kept_sig_exact")
    print(f"[cs] {liv}: K={cs.K} m={cs.m} | ordine dei lambda verificato "
          f"contro kept_sig_exact")

    # --- popolazione (campione i.i.d. da p_exact) ---
    df = pd.read_csv(os.path.join(cdir, f"popolazione_{liv}.csv"))
    varn = spec["vars"]
    pool0 = np.empty((len(df), len(varn)), dtype=np.int32)
    for i, v in enumerate(varn):
        idx = {c: k for k, c in enumerate(spec["categories"][v])}
        pool0[:, i] = df[v].astype(str).map(idx).to_numpy(dtype=np.int32)
    if n_sub and n_sub < len(pool0):
        pool0 = pool0[np.random.default_rng(0).choice(len(pool0), n_sub,
                                                      replace=False)]
    N = len(pool0)
    print(f"[pop] N={N:,} individui da popolazione_{liv}.csv")

    if scr:
        rng_s = np.random.default_rng(7)
        cols = varn if scr == "all" else [c.strip() for c in scr.split(",")]
        bad = [c for c in cols if c not in varn]
        if bad:
            sys.exit(f"--scramble: variabili sconosciute {bad}")
        for c in cols:
            k = varn.index(c)
            pool0[:, k] = rng_s.integers(0, spec["domain_sizes"][k], size=N)
        print(f"[scr] randomizzate uniformemente: {cols}  "
              f"(l'equilibrio resta p_lambda: si misura il MIXING)")

    tgt = cs.alphas_array
    sd = np.sqrt(tgt * (1 - tgt) / N)
    blocks = build_blocks(cs)
    blk = np.array([SIG_BY_NAMES.get(
        tuple(sorted(varn[i] for i in cs.attrs_list[j])), "?")
        for j in range(cs.m)])
    names = sorted(set(blk))

    g = GibbsPCDSolver(cs, use_numba=True)
    have_nb = getattr(g, "_numba_kernel", None) is not None
    kernels = []
    if which in ("both", "numba") and have_nb:
        kernels.append(("numba", g._gibbs_sweep_numba))
    if which in ("both", "numpy"):
        kernels.append(("numpy", g._gibbs_sweep))
    if not kernels:
        sys.exit("nessun kernel disponibile")

    checkpoints = sorted({0, 1, 2, 3, 5, 8, 10, 15, 20, 30, 50, 75, 100, 150, 200,
                          300, 500} & set(range(max_sweeps + 1)))

    for kname, sweep in kernels:
        print(f"\n{'='*78}\nKERNEL: {kname}\n{'='*78}")
        print(f"{'sweep':>6} {'|z| med':>8} {'|z|>3':>7} " +
              " ".join(f"{b:>6}" for b in names))
        pool = pool0.copy()
        done = 0
        for cp in checkpoints:
            while done < cp:
                t0 = time.time()
                pool = sweep(pool, lam)
                done += 1
                if done == 1:
                    t1 = time.time() - t0
            ah = alphas_of(pool, blocks, cs.m)
            z = np.abs(ah - tgt) / sd
            row = " ".join(f"{np.median(z[blk == b]):6.2f}" for b in names)
            print(f"{cp:>6} {np.median(z):8.2f} "
                  f"{(z>3).mean()*100:6.1f}% {row}")
        print(f"  (riferimento: |z| mediano 0.67 se la distribuzione "
              f"e' invariante; primo sweep {t1:.1f}s)")


if __name__ == "__main__":
    main()
