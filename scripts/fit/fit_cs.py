"""
fit_cs.py — fit del ConstraintSet (K6C o K7C): solver esatto + GibbsPCD.

Generalizza fit_k6c.py: il livello e' un parametro, le firme dei blocchi sono
risolte per NOME variabile contro spec['vars'] (robuste allo shift di indici
introdotto da 'zona' in K7C).

K7C: |X| = 33 x 5376 = 177.408, m ~ 2.400 -> F densa ~3.4 GB float64 (x2 per
F e F_g): dentro i 64 GB della macchina; fit esatto atteso in minuti.

Uso:
    python scripts/fit/fit_cs.py 017029 --anno 2024 --livello K7C --eps 1e-8 --min-alpha 2e-4 --no-gibbs
    python scripts/fit/fit_cs.py 017029 --anno 2025                      # K6C, come fit_k6c
Output in constraints_<anno>/: fit_<LIV>.json, popolazione_<LIV>.csv
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

# firme dei blocchi per NOME variabile (ordine irrilevante: si confrontano sorted)
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
    for base in REPO_CANDIDATES:
        base = os.path.expanduser(base)
        hits = glob.glob(f"{base}/**/constraint_set.py", recursive=True)
        if hits:
            moddir = os.path.dirname(hits[0])
            parent = os.path.dirname(moddir)
            sys.path.insert(0, parent)
            pkg = os.path.basename(moddir)
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


def block_of(attrs, varnames):
    names = tuple(sorted(varnames[a] for a in attrs))
    return SIG_BY_NAMES.get(names, "?")


def load_cs(spec, ConstraintSet, eps=0.0, min_alpha=0.0, blocks=None):
    varnames = spec["vars"]
    cs = ConstraintSet(spec["domain_sizes"])
    n_zero = n_drop = 0
    kept_blocks = {}
    kept_sig = []                      # <-- NUOVO: firma dei vincoli tenuti
    for c in spec["constraints"]:
        blk = block_of(c["attrs"], varnames)
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
        kept_sig.append((list(c["attrs"]), list(c["vals"])))     # <-- NUOVO
        kept_blocks[blk] = kept_blocks.get(blk, 0) + 1
    print(f"[cs] blocchi tenuti: {kept_blocks} | zeri->eps: {n_zero} | "
          f"droppati (<min_alpha o 0): {n_drop}")
    return cs, n_zero, kept_sig          # <-- NUOVO: terzo valore


def all_tuples_of(domain_sizes):
    grids = np.meshgrid(*[np.arange(d) for d in domain_sizes], indexing="ij")
    return np.stack([g.ravel() for g in grids], axis=1).astype(np.int32)


def probs_from(obj, F=None):
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
    raise AttributeError(f"probabilità non trovate su {type(obj).__name__}")

def probs_from_lambdas(lam, F):
    """p_lambda su X a partire dai soli lambdas (senza oggetto solver)."""
    logits = F @ np.asarray(lam, dtype=float)
    logits -= logits.max()
    p = np.exp(logits)
    return p / p.sum()

def diagnostics(name, p, F, alphas, zero_mask):
    alpha_hat = p @ F
    pos = ~zero_mask
    mre = float(np.mean(np.abs(alpha_hat[pos] - alphas[pos]) / alphas[pos]))
    zero_mass = alpha_hat[zero_mask]
    H = float(-(p[p > 0] * np.log(p[p > 0])).sum())
    supp = int((p > 1e-12).sum())
    print(f"[{name}] MRE(alpha>0)={mre:.3e} | massa su celle escluse: "
          f"somma={zero_mass.sum():.2e} (n={len(zero_mass)}) | "
          f"H={H:.3f} nat | supporto~{supp}/{len(p)}")
    return {"mre_pos": mre, "zero_cell_mass_sum": float(zero_mass.sum()),
            "n_zero_constraints": int(len(zero_mass)),
            "entropy_nats": H, "support": supp}

def build_warm_start(spec_new, cdir, from_livello, rng):
    """
    Costruisce (pool_init, lambdas_init) per il CS nuovo a partire dal fit
    di un livello piu' piccolo, le cui variabili sono un PREFISSO di quelle
    nuove (nuovi attributi in coda a VAR_ORDER).

    pool: popolazione del livello vecchio, ricodificata in indici, estesa
          con le colonne nuove campionate dalle loro marginali (dai vincoli
          di arita' 1 se presenti, altrimenti uniforme).
    lambdas: quelli del vecchio fit, rimappati sugli indici dei vincoli
          nuovi via matching su (attrs, vals); zero per i vincoli nuovi.
    """
    fit_old_path = os.path.join(cdir, f"fit_{from_livello}.json")
    pop_old_path = os.path.join(cdir, f"popolazione_{from_livello}.csv")
    if not (os.path.exists(fit_old_path) and os.path.exists(pop_old_path)):
        sys.exit(f"warm start: servono {fit_old_path} e {pop_old_path}")
    fit_old = json.load(open(fit_old_path))

    vars_new = spec_new["vars"]
    vars_old = fit_old.get("vars")
    if vars_old is None:
        sys.exit(f"warm start: {fit_old_path} non contiene 'vars' "
                 f"(rigenerare il fit del livello {from_livello} con la "
                 f"versione aggiornata di fit_cs.py)")
    if vars_new[:len(vars_old)] != vars_old:
        sys.exit(f"warm start: le variabili di {from_livello} non sono un "
                 f"prefisso di quelle nuove.\n  vecchie: {vars_old}\n"
                 f"  nuove:   {vars_new}")

    # ---- pool: etichette -> indici, poi estensione ----
    dfp = pd.read_csv(pop_old_path)
    cat_idx = {v: {c: i for i, c in enumerate(spec_new["categories"][v])}
               for v in vars_new}
    N = len(dfp)
    pool = np.zeros((N, len(vars_new)), dtype=np.int32)
    for j, v in enumerate(vars_old):
        col = dfp[v].astype(str)
        unknown = set(col.unique()) - set(cat_idx[v])
        if unknown:
            sys.exit(f"warm start: valori non mappabili in '{v}': "
                     f"{sorted(unknown)[:5]}")
        pool[:, j] = col.map(cat_idx[v]).to_numpy(dtype=np.int32)

    # marginali dei nuovi attributi dai vincoli di arita' 1, se ci sono
    marg = {}
    for c in spec_new["constraints"]:
        if len(c["attrs"]) == 1:
            marg.setdefault(int(c["attrs"][0]), {})[int(c["vals"][0])] = c["alpha"]
    for j in range(len(vars_old), len(vars_new)):
        d = spec_new["domain_sizes"][j]
        if j in marg and sum(marg[j].values()) > 0:
            p = np.zeros(d)
            for k, a in marg[j].items():
                p[k] = a
            p = p / p.sum()
            src = "marginale del CS"
        else:
            p = np.full(d, 1.0 / d)
            src = "uniforme"
        pool[:, j] = rng.choice(d, size=N, p=p)
        print(f"[warm] '{vars_new[j]}' inizializzata da {src} ({d} modalita')")

    # ---- lambdas: matching su (attrs, vals) ----
    lam_old = fit_old.get("lambdas_exact")
    sig_old = fit_old.get("kept_sig_exact")
    if lam_old is None or sig_old is None:
        print("[warm] lambdas del fit vecchio non disponibili: parto da zero")
        return pool, None
    old_map = {(tuple(a), tuple(v)): lam_old[i]
               for i, (a, v) in enumerate(sig_old)}
    return pool, old_map          # la mappatura sugli indici nuovi
                                  # avviene in main, dove si conosce kept_sig

def main(comune, anno, livello, eps, pool, outer, use_numba, use_sparse):
    ConstraintSet, ExactMaxEntSolver, GibbsPCDSolver, ev = import_repo()
    cdir = os.path.expanduser(f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")
    spec = json.load(open(os.path.join(cdir, f"cs_{livello}.json")))
    print(f"[cs] livello {livello}: vars={spec['vars']}")

    cs, n_zero, kept_sig = load_cs(spec, ConstraintSet, eps, MIN_ALPHA, BLOCKS)
    alphas = cs.alphas_array
    zero_mask = (alphas <= eps) if eps > 0 else np.zeros(len(alphas), dtype=bool)
    X = int(np.prod(spec["domain_sizes"]))
    print(f"[cs] m={cs.m}, |X|={X:,}, vincoli alpha=0: {n_zero} (eps={eps})")

    if use_sparse:
        print(f"[mem] F sparsa: costruzione in corso (stima densa di "
              f"riferimento: {X*cs.m*8/1e9:.2f} GB)")
    else:
        print(f"[mem] F stimata: {X*cs.m*8/1e9:.2f} GB (x2 con F_g)")

    all_tuples = all_tuples_of(spec["domain_sizes"])
    t0 = time.time()
    if use_sparse:
        F = cs.build_indicator_matrix_sparse(all_tuples)
    else:
        F = cs.build_indicator_matrix(all_tuples)
    print(f"[mem] F costruita in {time.time()-t0:.1f}s")

    if eps == 0.0:
        # load_cs(..., eps=0, ...) e' la stessa chiamata che ha prodotto cs:
        # stesso CS, stesse firme, stessa F. Niente ricostruzione, niente
        # seconda copia da |X|*m*8 byte.
        cs_g, kept_sig_g = cs, kept_sig
    else:
        cs_g, _, kept_sig_g = load_cs(spec, ConstraintSet, 0.0, MIN_ALPHA, BLOCKS)

    pool_init = lam_init = None
    if WARM_FROM:
        rng_w = np.random.default_rng(123)
        pool_init, old_map = build_warm_start(spec, cdir, WARM_FROM, rng_w)
        if old_map is not None:
            lam_init = np.array([old_map.get((tuple(a), tuple(v)), 0.0)
                                 for a, v in kept_sig_g], dtype=np.float64)
            n_hit = int((lam_init != 0).sum())
            print(f"[warm] lambdas rimappati: {n_hit}/{len(lam_init)} "
                  f"da {WARM_FROM}, {len(lam_init)-n_hit} nuovi a zero")
            
    if cs_g is cs:
        F_g = F
    elif use_sparse:
        F_g = cs_g.build_indicator_matrix_sparse(all_tuples)
    else:
        F_g = cs_g.build_indicator_matrix(all_tuples)

    if zero_mask.any():
        sub = F[:, zero_mask]
        summed = sub.sum(axis=1)
        summed = np.asarray(summed).ravel() if use_sparse else summed
        excl_cells = np.where(summed > 0)[0]
    else:
        excl_cells = np.array([], dtype=int)

    # ---------- solver esatto (o riuso del fit salvato) ----------
    fit_path = os.path.join(cdir, f"fit_{livello}.json")
    exact = None
    reused = False
    lam_prev = None 
    p_exact = None

    if NO_EXACT and os.path.exists(fit_path):
        prev = json.load(open(fit_path))
        lam_prev = prev.get("lambdas_exact")
        sig_prev = prev.get("kept_sig_exact")
        ok = (lam_prev is not None and sig_prev is not None
              and len(lam_prev) == cs_g.m
              and prev.get("min_alpha") == MIN_ALPHA
              and prev.get("vars") == spec["vars"])
        if ok and sig_prev is not None:
            # verifica che le firme coincidano una per una
            ok = all(tuple(a) == tuple(b[0]) and tuple(v) == tuple(b[1])
                     for (a, v), b in zip(kept_sig_g, sig_prev))
        if ok:
            p_exact = probs_from_lambdas(np.asarray(lam_prev), F_g)
            t_exact = prev.get("t_exact_s")
            d_exact = prev.get("exact")
            reused = True
            print(f"[exact] riuso lambdas da {os.path.basename(fit_path)} "
                  f"(m={len(lam_prev)}, min_alpha={prev.get('min_alpha')}); "
                  f"fit saltato")
        else:
            print(f"[exact] fit salvato non compatibile "
                  f"(m, min_alpha o vars diversi): ricalcolo")

    if not reused:
        if NO_EXACT:
            # semantica --no-exact: riusa se disponibile, altrimenti SALTA
            # (regime "solo Gibbs": il pool diventa il deliverable)
            p_exact = None
            t_exact = None
            d_exact = None
            print("[exact] --no-exact e nessun fit riusabile: solver esatto "
                  "saltato (la popolazione sara' campionata dal pool Gibbs)")
        else:
            t0 = time.time()
            exact = ExactMaxEntSolver(cs_g, verbose=False, sparse=use_sparse,
                                      F=F_g, all_tuples=all_tuples)
            exact.fit(max_iter=5000)
            t_exact = time.time() - t0
            p_exact = probs_from(exact, F_g)

    if p_exact is not None:
        p_exact = np.asarray(p_exact, dtype=float)
        p_exact[excl_cells] = 0.0
        p_exact /= p_exact.sum()
        if not reused:
            print(f"[exact] fit in {t_exact:.1f}s | "
                  f"celle escluse post-hoc: {len(excl_cells)}")
            d_exact = diagnostics("exact", p_exact, F, alphas, zero_mask)

    # ---------- GibbsPCD + confronto ----------
    d_gibbs, kl_eg, kl_ge, t_gibbs, gibbs = None, None, None, None, None
    pool_arr = None
    if not NO_GIBBS:
        t0 = time.time()
        gibbs = GibbsPCDSolver(cs_g, use_numba=use_numba)
        gibbs.fit(N_pool=pool, n_outer=outer, n_gibbs_sweeps=SWEEPS, tol=TOL,
                  lr=LR, lr_tau=LR_TAU, verbose_every=10,
                  pool_init=pool_init, lambdas_init=lam_init,
                  anneal_steps=ANNEAL)
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

        # il pool e' esso stesso una popolazione sintetica: salvarlo
        pool_arr = getattr(gibbs, "pool_", None)
        if pool_arr is not None:
            pa = np.asarray(pool_arr)
            dfpool = pd.DataFrame(
                {v: [spec["categories"][v][k] for k in pa[:, i]]
                 for i, v in enumerate(spec["vars"])})
            if "zona_nomi" in spec and "zona" in dfpool.columns:
                dfpool["quartiere"] = dfpool["zona"].map(spec["zona_nomi"])
            out_pool = os.path.join(cdir, f"pool_{livello}.csv")
            dfpool.to_csv(out_pool, index=False)
            print(f"[pool] N={len(dfpool):,} salvato -> {out_pool}")

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
    if p_exact is not None:
        idx = rng.choice(len(p_exact), size=n, p=p_exact)
        sample = all_tuples[idx]
        fonte_pop = "modello esatto"
    elif pool_arr is not None:
        pa = np.asarray(pool_arr)
        idx = rng.choice(len(pa), size=n, replace=(len(pa) < n))
        sample = pa[idx]
        fonte_pop = f"sottocampione del pool Gibbs (N={len(pa):,})"
    else:
        sys.exit("nessuna sorgente per la popolazione: servono il solver "
                 "esatto (p_exact) oppure il pool del Gibbs")

    dfp = pd.DataFrame({v: [spec["categories"][v][k] for k in sample[:, i]]
                        for i, v in enumerate(spec["vars"])})
    if "zona_nomi" in spec and "zona" in dfp.columns:
        dfp["quartiere"] = dfp["zona"].map(spec["zona_nomi"])

    # Identificatore STABILE dell'individuo. Nasce qui perche' l'individuo
    # nasce qui: assign_nationality, assign_avq ed enrich aggiungono
    # colonne e non riordinano mai le righe, quindi l'uid sopravvive
    # inalterato a tutta la catena.
    #
    # NON e' l'`id` del Parquet, che to_parquet assegna DOPO l'ordinamento
    # per zona,sezione e usa per i permalink: quello e' progressivo per
    # costruzione, questo deve restare attaccato alla persona.
    #
    # Serve a due cose indipendenti: e' la chiave dell'onomastica
    # (gsp.nomi genera nome e cognome da qui, deterministicamente, senza
    # che nessun nome finisca mai in un file), ed e' cio' che rende
    # RIPRODUCIBILE un campione narrativo — «i venti di Cittadella» sono
    # gli stessi a ogni esecuzione, quindi una demo si puo' provare prima
    # e una biografia mostrata in un articolo si puo' citare.
    dfp.insert(0, "uid", [f"{comune}-{i:07d}" for i in range(len(dfp))])

    out_pop = os.path.join(cdir, f"popolazione_{livello}.csv")
    dfp.to_csv(out_pop, index=False)
    print(f"[pop] campione n={n:,} da {fonte_pop} -> {out_pop}")
    key = ["zona"] if "zona" in dfp.columns else ["sesso", "eta"]
    m_samp = dfp.groupby(key).size() / n
    print(f"[pop] check marginale {key} (campione, prime 5 righe):")
    print(m_samp.head(5).round(4).to_string())

    # ---------- salvataggio ----------
    out = {"comune": comune, "anno": anno, "livello": livello, "eps": eps,
           "min_alpha": MIN_ALPHA, "pool": pool, "outer": outer, "sparse": use_sparse,
           "t_exact_s": t_exact, "t_gibbs_s": t_gibbs,
           "exact": d_exact, "gibbs": d_gibbs,
           "kl_exact_gibbs": kl_eg, "kl_gibbs_exact": kl_ge,
          "lambdas_exact": ([float(x) for x in np.asarray(exact.lambdas).ravel()]
                             if (exact is not None
                                 and getattr(exact, "lambdas", None) is not None)
                             else (lam_prev if reused else None)),
           "lambdas_gibbs": [float(x) for x in np.asarray(gibbs.lambdas).ravel()]
           if (gibbs is not None and getattr(gibbs, "lambdas", None) is not None) else None,
           "gibbs_mre_curve": ([float(h["mre"]) for h in gibbs.history]
                               if gibbs is not None else None),
           "vars": spec["vars"],
           "domain_sizes": spec["domain_sizes"],
           "kept_sig_exact": [[a, v] for a, v in kept_sig_g]}
    with open(os.path.join(cdir, f"fit_{livello}.json"), "w") as f:
        json.dump(out, f)
    print(f"[done] diagnostiche e lambdas -> fit_{livello}.json")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("Uso: python scripts/fit/fit_cs.py <comune> [--anno 2025] [--livello K6C|K7C|K8C|K9C] "
                 "[--eps 0] [--pool 20000] [--outer 500] [--numba] [--sparse] "
                 "[--min-alpha 0] [--blocks A,B,Z1,...] [--no-gibbs] [--no-exact] "
                 "[--tol 0.02] [--warm-from K9C] [--anneal 0]")
    comune = args[0]
    getf = lambda k, d: float(args[args.index(k) + 1]) if k in args else d
    geti = lambda k, d: int(args[args.index(k) + 1]) if k in args else d
    livello = args[args.index("--livello") + 1] if "--livello" in args else "K6C"
    MIN_ALPHA = getf("--min-alpha", 0.0)
    BLOCKS = set(args[args.index("--blocks") + 1].split(",")) if "--blocks" in args else None
    NO_GIBBS = "--no-gibbs" in args
    NO_EXACT = "--no-exact" in args
    TOL = getf("--tol", 0.02)
    WARM_FROM = args[args.index("--warm-from") + 1] if "--warm-from" in args else None
    ANNEAL = geti("--anneal", 0)
    SWEEPS = geti("--sweeps", 5)
    LR     = getf("--lr", 0.01)
    LR_TAU = getf("--lr-tau", 0.0)
    main(comune, geti("--anno", 2025), livello, getf("--eps", 0.0),
         geti("--pool", 20000), geti("--outer", 500), "--numba" in args, "--sparse" in args)

