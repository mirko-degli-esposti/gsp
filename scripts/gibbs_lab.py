#!/usr/bin/env python3
"""
gibbs_lab.py — banco di prova per il GibbsPCD, indipendente da fit_cs.py.

Non sovrascrive pool_<LIV>.csv ne' fit_<LIV>.json: ogni run scrive in una
propria directory. Traccia la traiettoria completa di ||lambda_t|| e
||lambda_t - lambda*||, che e' l'unico modo per sapere se un run e'
davvero convergiuto (la MRE si appiattisce mentre lambda cresce ancora).

    python gibbs_lab.py 017029 --livello K10C --min-alpha 2e-4 \\
        --pool 100000 --outer 2500 --sweeps 5 --lr 0.01 --kl \\
        --tag base --out ~/progetti/gsp/regress/lab

    ... --lr-tau 600      # decadimento armonico lr/(1+t/tau)
    ... --no-kl           # salta il calcolo di KL (risparmia ~2 min e 6 GB)
"""

import os
import re
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
            d = os.path.dirname(hits[0])
            sys.path.insert(0, os.path.dirname(d))
            pkg = os.path.basename(d)
            return (importlib.import_module(f"{pkg}.constraint_set").ConstraintSet,
                    importlib.import_module(f"{pkg}.gibbs_pcd_solver").GibbsPCDSolver,
                    importlib.import_module(f"{pkg}.fast_F").constraint_indices)
    sys.exit("repo maxent-popsynth-pcd non trovato")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    comune = a[0]
    gi = lambda k, d: int(a[a.index(k) + 1]) if k in a else d
    gf = lambda k, d: float(a[a.index(k) + 1]) if k in a else d
    gs = lambda k, d: a[a.index(k) + 1] if k in a else d

    anno = gi("--anno", 2024)
    liv = gs("--livello", "K10C")
    ma = gf("--min-alpha", 2e-4)
    N = gi("--pool", 100_000)
    outer = gi("--outer", 2500)
    sweeps = gi("--sweeps", 5)
    lr = gf("--lr", 0.01)
    lr_tau = gf("--lr-tau", 0.0)
    seed = gi("--seed", 1)
    do_kl = "--no-kl" not in a
    tag = gs("--tag", f"lr{lr}_tau{lr_tau}_N{N}_s{sweeps}")
    outdir = os.path.expanduser(gs("--out", "~/progetti/gsp/regress/lab"))
    os.makedirs(outdir, exist_ok=True)

    ConstraintSet, GibbsPCDSolver, constraint_indices = import_repo()
    cdir = os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")
    spec = json.load(open(os.path.join(cdir, f"cs_{liv}.json")))
    fitj = json.load(open(os.path.join(cdir, f"fit_{liv}.json")))

    # --- cs_g: alpha>0 e >=min_alpha, nell'ordine dei lambda salvati -----
    cs = ConstraintSet(spec["domain_sizes"])
    sig = []
    zero_cons = []
    for c in spec["constraints"]:
        al = c["alpha"]
        if al <= 0:
            zero_cons.append(c)
            continue
        if al < ma:
            continue
        cs.add(c["attrs"], c["vals"], al)
        sig.append([list(c["attrs"]), list(c["vals"])])

    lam_star = np.asarray(fitj.get("lambdas_exact") or [], dtype=np.float64)
    if len(lam_star) != cs.m:
        sys.exit(f"m={cs.m} ma lambdas_exact ne ha {len(lam_star)}: "
                 f"min_alpha del fit = {fitj.get('min_alpha')}")
    ks = fitj.get("kept_sig_exact")
    if ks and not all(list(x[0]) == y[0] and list(x[1]) == y[1]
                      for x, y in zip(ks, sig)):
        sys.exit("l'ordine dei vincoli NON coincide con kept_sig_exact")

    X = int(np.prod(spec["domain_sizes"]))
    print(f"[lab] {tag}")
    print(f"[cs]  {liv}: K={cs.K} m={cs.m} |X|={X:,} | lambda* caricati e "
          f"verificati contro kept_sig_exact")
    print(f"[cfg] N={N:,} outer={outer} sweeps={sweeps} lr={lr} "
          f"lr_tau={lr_tau} seed={seed}")
    print(f"[ref] |lambda*| = {np.linalg.norm(lam_star):.3f}")

    # --- fit -------------------------------------------------------------
    g = GibbsPCDSolver(cs, use_numba=True)
    kw = dict(N_pool=N, n_outer=outer, n_gibbs_sweeps=sweeps, tol=0.0,
              lr=lr, seed=seed, verbose_every=10)
    import inspect
    par = inspect.signature(g.fit).parameters
    if "lr_tau" in par:
        kw["lr_tau"] = lr_tau
    elif lr_tau > 0:
        sys.exit("il solver non espone lr_tau: applica la patch")
    if "lambdas_ref" in par:
        kw["lambdas_ref"] = lam_star
    else:
        print("  ATTENZIONE: il solver non espone lambdas_ref, "
              "nessuna traccia di ||lam-lam*||")
    t0 = time.time()
    g.fit(**kw)
    t_fit = time.time() - t0
    lam_g = np.asarray(g.lambdas if getattr(g, "lambdas", None) is not None
                       else g.lam, dtype=np.float64)

    # --- traiettoria -----------------------------------------------------
    hist = g.history
    csvp = os.path.join(outdir, f"traj_{tag}.csv")
    keys = ["iter", "mre", "lr", "lam_norm", "lam_dist"]
    with open(csvp, "w") as f:
        f.write(",".join(keys) + "\n")
        for h in hist:
            f.write(",".join(str(h.get(k, "")) for k in keys) + "\n")
    print(f"[traj] {len(hist)} punti -> {csvp}")

    res = dict(tag=tag, comune=comune, livello=liv, min_alpha=ma, N=N,
               outer=outer, sweeps=sweeps, lr=lr, lr_tau=lr_tau, seed=seed,
               m=cs.m, t_fit_s=t_fit,
               lam_star_norm=float(np.linalg.norm(lam_star)),
               lam_norm=float(np.linalg.norm(lam_g)),
               lam_dist=float(np.linalg.norm(lam_g - lam_star)),
               mre_final=float(hist[-1]["mre"]) if hist else None)

    # somma cumulata di lr: la vera misura di "quanto lontano e' andato"
    res["sum_lr"] = float(sum(h.get("lr", lr) for h in hist)
                          * (outer / max(len(hist), 1)))

    # --- KL, entropia, supporto -----------------------------------------
    if do_kl:
        from scipy.special import logsumexp
        print("[kl]  costruzione F...")
        t0 = time.time()
        F = cs.build_indicator_matrix_sparse()
        print(f"[kl]  F in {time.time()-t0:.1f}s")

        # celle da escludere: quelle che soddisfano un vincolo con alpha=0
        excl = np.zeros(X, dtype=bool)
        if zero_cons:
            cz = ConstraintSet(spec["domain_sizes"])
            for c in zero_cons:
                cz.add(c["attrs"], c["vals"], 1.0)
            for j in range(cz.m):
                excl[constraint_indices(cz, j)] = True
        print(f"[kl]  celle escluse: {excl.sum():,} / {X:,}")

        def probs(lam):
            u = F @ lam
            p = np.exp(u - logsumexp(u))
            m_out = float(p[excl].sum())
            p[excl] = 0.0
            p /= p.sum()
            return p, m_out

        p_e, _ = probs(lam_star)
        p_g, mass_out = probs(lam_g)
        ok = (p_e > 0) & (p_g > 0)
        res["kl_exact_gibbs"] = float(np.sum(p_e[ok] * np.log(p_e[ok] / p_g[ok])))
        res["kl_gibbs_exact"] = float(np.sum(p_g[ok] * np.log(p_g[ok] / p_e[ok])))
        res["H_gibbs"] = float(-np.sum(p_g[p_g > 0] * np.log(p_g[p_g > 0])))
        res["H_exact"] = float(-np.sum(p_e[p_e > 0] * np.log(p_e[p_e > 0])))
        res["mass_excluded_gibbs"] = mass_out
        res["support_gibbs"] = int((p_g > 1e-12).sum())
        res["support_exact"] = int((p_e > 1e-12).sum())
        # errore marginale analitico di p_gibbs
        ah = F.T @ p_g
        al = cs.alphas_array
        res["mre_analytic"] = float(np.mean(np.abs(ah - al) / al))
        del F, p_e, p_g

    jp = os.path.join(outdir, f"res_{tag}.json")
    json.dump(res, open(jp, "w"), indent=1)
    print()
    for k in ("t_fit_s", "sum_lr", "mre_final", "mre_analytic", "lam_norm",
              "lam_star_norm", "lam_dist", "kl_exact_gibbs", "kl_gibbs_exact",
              "H_gibbs", "H_exact", "mass_excluded_gibbs", "support_gibbs"):
        if k in res and res[k] is not None:
            v = res[k]
            print(f"  {k:22s} {v:.4f}" if isinstance(v, float) else
                  f"  {k:22s} {v}")
    print(f"\n[out] {jp}")


if __name__ == "__main__":
    main()
