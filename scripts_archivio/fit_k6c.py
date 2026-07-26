"""
fit_k6c.py — fit del ConstraintSet K6C: solver esatto (ground truth) + GibbsPCD.

Con |X|=5376 il dominio comunale è enumerabile: il solver esatto fa da
riferimento e GibbsPCD viene validato contro di esso (MRE, KL, recupero
parametri) — stessa logica degli esperimenti A0/A1 del repo, ma su dati reali.

Gestione vincoli alpha=0 (esclusioni strutturali, es. vedovi 15-24):
    - esclusi dalla MRE (divisione per alpha)
    - riportata la massa di probabilità residua sulle celle escluse
    - opzione --eps per floorarli (default: tenuti a 0)

Uso:
    python fit_k6c.py 017029 --anno 2025 [--eps 0] [--pool 20000] [--outer 500]
Output in constraints_<anno>/:
    fit_K6C.json           lambdas (exact e gibbs) + diagnostiche
    popolazione_K6C.csv    campione sintetico n=pop dal modello esatto
"""

import os
import sys
import glob
import json
import time
import importlib
import numpy as np
import pandas as pd

REPO_CANDIDATES = ["~/progetti/maxent-popsynth-pcd", "/content/maxent-popsynth-pcd"]


def import_repo():
    for base in REPO_CANDIDATES:
        base = os.path.expanduser(base)
        hits = glob.glob(f"{base}/**/constraint_set.py", recursive=True)
        if hits:
            moddir = os.path.dirname(hits[0])          # .../src
            parent = os.path.dirname(moddir)           # radice del repo
            sys.path.insert(0, parent)
            pkg = os.path.basename(moddir)             # 'src'
            cs_mod = importlib.import_module(f"{pkg}.constraint_set")
            sol_mod = importlib.import_module(f"{pkg}.solvers")
            gib_mod = importlib.import_module(f"{pkg}.gibbs_pcd_solver")
            try:
                ev_mod = importlib.import_module(f"{pkg}.evaluator")
            except Exception:
                ev_mod = None
            return cs_mod.ConstraintSet, sol_mod.ExactMaxEntSolver, \
                gib_mod.GibbsPCDSolver, ev_mod
    raise ImportError("repo maxent-popsynth-pcd non trovato in ~/progetti/")

BLOCK_SIG = {  # firma attrs -> blocco (ordine vars: sesso,eta,statociv,cittad,istruz,condiz)
    (0, 1, 2): "A", (0, 1, 3): "B", (0, 1, 4): "C", (0, 1, 5): "D",
    (3, 4): "E", (3, 5): "F", (1, 4): "Si", (1, 5): "Sc",
}

def load_cs(path, ConstraintSet, eps=0.0, min_alpha=0.0, blocks=None):
    spec = json.load(open(path))
    cs = ConstraintSet(spec["domain_sizes"])
    n_zero = n_drop = 0
    kept_blocks = {}
    for c in spec["constraints"]:
        blk = BLOCK_SIG.get(tuple(c["attrs"]), "?")
        if blocks and blk not in blocks:
            continue
        a = c["alpha"]
        if a <= 0:
            n_zero += 1
            if eps > 0:
                a = eps
            else:
                n_drop += 1
                continue
        elif a < min_alpha:
            n_drop += 1
            continue
        cs.add(c["attrs"], c["vals"], a)
        kept_blocks[blk] = kept_blocks.get(blk, 0) + 1
    print(f"[cs] blocchi tenuti: {kept_blocks} | zeri->eps: {n_zero} | droppati (<min_alpha o 0): {n_drop}")
    return cs, spec, n_zero


def all_tuples_of(domain_sizes):
    grids = np.meshgrid(*[np.arange(d) for d in domain_sizes], indexing="ij")
    return np.stack([g.ravel() for g in grids], axis=1).astype(np.int32)


def probs_from(obj, F=None):
    """Estrae le probabilità su X da un solver, con fallback via lambdas."""
    for attr in ("p", "probs", "p_hat", "p_model"):
        v = getattr(obj, attr, None)
        if v is not None and np.ndim(v) == 1:
            return np.asarray(v, dtype=float)
    lam = getattr(obj, "lambdas", None)
    if lam is not None and F is not None:
        logits = F @ np.asarray(lam, dtype=float)
        logits -= logits.max()
        p = np.exp(logits)
        return p / p.sum()
    raise AttributeError(f"probabilità non trovate su {type(obj).__name__}: "
                         f"attributi={[a for a in dir(obj) if not a.startswith('_')]}")


def diagnostics(name, p, F, alphas, zero_mask):
    alpha_hat = p @ F
    pos = ~zero_mask
    mre = float(np.mean(np.abs(alpha_hat[pos] - alphas[pos]) / alphas[pos]))
    zero_mass = alpha_hat[zero_mask]
    H = float(-(p[p > 0] * np.log(p[p > 0])).sum())
    supp = int((p > 1e-12).sum())
    print(f"[{name}] MRE(alpha>0)={mre:.3e} | massa su celle escluse: "
          f"{[f'{z:.2e}' for z in zero_mass]} | H={H:.3f} nat | supporto~{supp}/{len(p)}")
    return {"mre_pos": mre, "zero_cell_mass": [float(z) for z in zero_mass],
            "entropy_nats": H, "support": supp}


def main(comune, anno, eps, pool, outer, use_numba):
    ConstraintSet, ExactMaxEntSolver, GibbsPCDSolver, ev = import_repo()
    cdir = os.path.expanduser(f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")
    cs, spec, n_zero = load_cs(os.path.join(cdir, "cs_K6C.json"), ConstraintSet,
                               eps, MIN_ALPHA, BLOCKS)
    alphas = cs.alphas_array
    zero_mask = (alphas <= eps) if eps > 0 else np.zeros(len(alphas), dtype=bool)
    print(f"[cs] m={cs.m}, |X|={int(np.prod(spec['domain_sizes']))}, "
          f"vincoli alpha=0: {n_zero} (eps={eps})")

    all_tuples = all_tuples_of(spec["domain_sizes"])
    F = cs.build_indicator_matrix(all_tuples)
    # CS per i solver: senza esclusioni (eps=0 -> zeri droppati);
    # le esclusioni si applicano post-hoc sul supporto
    cs_g, _, _ = load_cs(os.path.join(cdir, "cs_K6C.json"), ConstraintSet,
                         0.0, MIN_ALPHA, BLOCKS)
    F_g = cs_g.build_indicator_matrix(all_tuples)
    excl_cells = (np.where(F[:, zero_mask].sum(axis=1) > 0)[0]
                  if zero_mask.any() else np.array([], dtype=int))

    # ---------- solver esatto ----------
    t0 = time.time()
    exact = ExactMaxEntSolver(cs_g, verbose=False)
    exact.fit(max_iter=5000)
    t_exact = time.time() - t0
    p_exact = probs_from(exact, F_g)
    p_exact[excl_cells] = 0.0
    p_exact /= p_exact.sum()
    print(f"[exact] fit in {t_exact:.1f}s | celle escluse post-hoc: {len(excl_cells)}")
    d_exact = diagnostics("exact", p_exact, F, alphas, zero_mask)

    # ---------- GibbsPCD + confronto ----------
    d_gibbs, kl_eg, kl_ge, t_gibbs, gibbs = None, None, None, None, None
    if not NO_GIBBS:
        t0 = time.time()
        gibbs = GibbsPCDSolver(cs_g, use_numba=use_numba)
        gibbs.fit(N_pool=pool, n_outer=outer)
        t_gibbs = time.time() - t0
        print(f"[gibbs] fit in {t_gibbs:.1f}s | "
              f"final_mre(repo)={getattr(gibbs, 'final_mre', float('nan')):.4f}")
        p_gibbs = probs_from(gibbs, F_g)
        if len(excl_cells):
            print(f"[gibbs] massa spontanea su celle escluse (pre-azzeramento): "
                  f"{p_gibbs[excl_cells].sum():.2e}")
        p_gibbs[excl_cells] = 0.0
        p_gibbs /= p_gibbs.sum()
        d_gibbs = diagnostics("gibbs", p_gibbs, F, alphas, zero_mask)

        if ev is not None and hasattr(ev, "kl"):
            kl_eg = float(ev.kl(p_exact, p_gibbs))
            kl_ge = float(ev.kl(p_gibbs, p_exact))
        else:
            e = 1e-15
            pe = np.clip(p_exact, e, None); pe /= pe.sum()
            pg = np.clip(p_gibbs, e, None); pg /= pg.sum()
            kl_eg = float((pe * np.log(pe / pg)).sum())
            kl_ge = float((pg * np.log(pg / pe)).sum())
        print(f"[cmp] KL(exact||gibbs)={kl_eg:.3e} | KL(gibbs||exact)={kl_ge:.3e}")

    # ---------- popolazione sintetica dal modello esatto ----------
    rng = np.random.default_rng(42)
    n = spec["pop_size"]
    idx = rng.choice(len(p_exact), size=n, p=p_exact)
    sample = all_tuples[idx]
    dfp = pd.DataFrame({v: [spec["categories"][v][k] for k in sample[:, i]]
                        for i, v in enumerate(spec["vars"])})
    out_pop = os.path.join(cdir, "popolazione_K6C.csv")
    dfp.to_csv(out_pop, index=False)
    print(f"[pop] campione n={n:,} -> {out_pop}")
    m_samp = dfp.groupby(["sesso", "eta"]).size() / n
    print("[pop] check marginale sesso x eta (campione, prime 4 righe):")
    print(m_samp.head(4).round(4).to_string())

    # ---------- salvataggio ----------
    out = {"comune": comune, "anno": anno, "eps": eps,
           "pool": pool, "outer": outer,
           "t_exact_s": t_exact, "t_gibbs_s": t_gibbs,
           "exact": d_exact, "gibbs": d_gibbs,
           "kl_exact_gibbs": kl_eg, "kl_gibbs_exact": kl_ge,
           "lambdas_exact": [float(x) for x in np.asarray(exact.lambdas).ravel()]
           if getattr(exact, "lambdas", None) is not None else None,
           "lambdas_gibbs": [float(x) for x in np.asarray(gibbs.lambdas).ravel()]
           if (gibbs is not None and getattr(gibbs, "lambdas", None) is not None) else None}
    with open(os.path.join(cdir, "fit_K6C.json"), "w") as f:
        json.dump(out, f)
    print(f"[done] diagnostiche e lambdas -> fit_K6C.json")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("Uso: python fit_k6c.py <comune> [--anno 2025] [--eps 0] "
                 "[--pool 20000] [--outer 500] [--numba] "
                 "[--min-alpha 0] [--blocks A,B,...] [--no-gibbs]")
    comune = args[0]
    getf = lambda k, d: float(args[args.index(k) + 1]) if k in args else d
    geti = lambda k, d: int(args[args.index(k) + 1]) if k in args else d
    MIN_ALPHA = getf("--min-alpha", 0.0)
    BLOCKS = set(args[args.index("--blocks") + 1].split(",")) if "--blocks" in args else None
    NO_GIBBS = "--no-gibbs" in args
    main(comune, geti("--anno", 2025), getf("--eps", 0.0),
         geti("--pool", 20000), geti("--outer", 500), "--numba" in args)
