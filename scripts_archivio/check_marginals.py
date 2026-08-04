#!/usr/bin/env python3
"""
check_marginals.py — marginali osservati vs vincoli, normalizzati al
pavimento di campionamento.

L'errore relativo grezzo non e' interpretabile da solo: a N individui, un
vincolo con target alpha ha una deviazione standard di campionamento
    sd(alpha_hat) = sqrt(alpha (1-alpha) / N)
cioe' un errore RELATIVO atteso di sqrt((1-alpha)/(alpha N)) anche con un
modello perfetto. A N=400.000 sono l'11% per alpha=2e-4 e lo 0,7% per
alpha=0,05.

La quantita' informativa e' quindi
    z = (alpha_oss - alpha) / sqrt(alpha (1-alpha) / N)
Per un modello perfetto z ~ N(0,1), quindi i valori di riferimento sono
    mediana |z|            = 0,674
    media |z| = E|z|       = sqrt(2/pi) = 0,798  ( = MRE / pavimento )
    frazione con |z| > 3   = 0,27%
Valori vicini a questi significano "indistinguibile dal campionamento";
valori molto sopra indicano bias reale. Nota che |z| coincide con
(errore relativo)/(pavimento predetto).

Valuta TUTTI i vincoli del CS, inclusi quelli scartati dal pruning: su
quelli il modello non e' stato addestrato, quindi il loro |z| misura
generalizzazione, non aderenza.

    python scripts/diagnostica/check_marginals.py 017029 --anno 2024 --livello K10C \
        --pops popolazione_K10C.csv,pool_K10C.csv --min-alpha 2e-4
    ... --csv report_K10C.csv     # dettaglio per vincolo
"""

import os
import sys
import json
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


def block_of(attrs, varnames):
    return SIG_BY_NAMES.get(tuple(sorted(varnames[a] for a in attrs)), "?")


def encode(df, spec):
    """CSV di etichette -> matrice (N, K) di indici, nell'ordine spec['vars']."""
    varn = spec["vars"]
    miss = [v for v in varn if v not in df.columns]
    if miss:
        sys.exit(f"colonne mancanti nel CSV: {miss}")
    out = np.empty((len(df), len(varn)), dtype=np.int32)
    for i, v in enumerate(varn):
        idx = {c: k for k, c in enumerate(spec["categories"][v])}
        col = df[v].astype(str).map(idx)
        if col.isna().any():
            bad = sorted(set(df[v].astype(str)) - set(idx))[:5]
            sys.exit(f"valori non mappabili in '{v}': {bad}")
        out[:, i] = col.to_numpy(dtype=np.int32)
    return out


def observed_alphas(pool, cons, domain_sizes):
    """alpha osservati per tutti i vincoli, per blocchi (bincount mixed-radix)."""
    ds = np.asarray(domain_sizes, dtype=np.int64)
    N = len(pool)
    groups = {}
    for i, c in enumerate(cons):
        key = tuple(sorted(c["attrs"]))
        groups.setdefault(key, []).append(i)
    out = np.empty(len(cons), dtype=np.float64)
    code = np.empty(N, dtype=np.int64)
    for sig, ids in groups.items():
        attrs = np.array(sig, dtype=np.int64)
        sizes = ds[attrs]
        n_cells = int(np.prod(sizes))
        code[:] = pool[:, attrs[0]]
        for p in range(1, len(attrs)):
            code *= sizes[p]
            code += pool[:, attrs[p]]
        cnt = np.bincount(code, minlength=n_cells)
        for i in ids:
            c = cons[i]
            order = np.argsort(c["attrs"])
            vals = np.array(c["vals"])[order]
            cell = 0
            for p in range(len(attrs)):
                cell = cell * int(sizes[p]) + int(vals[p])
            out[i] = cnt[cell] / N
    return out


def report(name, pool, spec, min_alpha):
    cons = [c for c in spec["constraints"] if c["alpha"] > 0]
    tgt = np.array([c["alpha"] for c in cons])
    obs = observed_alphas(pool, cons, spec["domain_sizes"])
    N = len(pool)

    floor_rel = np.sqrt((1 - tgt) / (tgt * N))       # errore rel. atteso
    err_rel = np.abs(obs - tgt) / tgt
    z = (obs - tgt) / np.sqrt(tgt * (1 - tgt) / N)
    trained = tgt >= min_alpha
    blocks = np.array([block_of(c["attrs"], spec["vars"]) for c in cons])
    arity = np.array([len(c["attrs"]) for c in cons])

    print(f"\n{'='*74}\n{name}   N={N:,}   vincoli con alpha>0: {len(cons)}"
          f"   (addestrati: {trained.sum()}, scartati: {(~trained).sum()})")
    print("=" * 74)

    for lab, msk in (("ADDESTRATI", trained), ("SCARTATI", ~trained)):
        if not msk.any():
            continue
        print(f"\n{lab}  (n={msk.sum()})")
        print(f"  MRE (errore rel. medio)      {err_rel[msk].mean():.4f}")
        print(f"  pavimento predetto           {floor_rel[msk].mean():.4f}")
        rap = err_rel[msk].mean() / floor_rel[msk].mean()
        med = np.median(np.abs(z[msk]))
        fr3 = (np.abs(z[msk]) > 3).mean()
        print(f"  rapporto MRE/pavimento       {rap:6.2f}   "
              f"(atteso 0.80 se al rumore)")
        print(f"  |z| mediano                  {med:6.2f}   "
              f"(atteso 0.67 se al rumore)")
        print(f"  |z| > 3                      {(np.abs(z[msk])>3).sum():4d}  "
              f"({fr3*100:5.1f}%)  (atteso 0.3%)")
        print(f"  errore assoluto totale       {np.abs(obs-tgt)[msk].sum():.4f}")

    # ---- per decile di alpha, sui soli addestrati ----
    m = trained
    print(f"\n  per decile di alpha (addestrati)")
    print(f"  {'alpha mediano':>14} {'n':>5} {'err.rel':>9} {'pavim.':>9} "
          f"{'|z| med':>8}")
    q = np.quantile(tgt[m], np.linspace(0, 1, 11))
    for a, b in zip(q[:-1], q[1:]):
        s = m & (tgt >= a) & (tgt <= b)
        if s.sum() == 0:
            continue
        print(f"  {np.median(tgt[s]):14.2e} {s.sum():5d} "
              f"{err_rel[s].mean():9.4f} {floor_rel[s].mean():9.4f} "
              f"{np.median(np.abs(z[s])):8.2f}")

    # ---- per blocco ----
    print(f"\n  per blocco (addestrati)")
    print(f"  {'blk':>4} {'n':>5} {'alpha med':>10} {'err.rel':>9} "
          f"{'pavim.':>9} {'|z| med':>8} {'|z|>3':>6}")
    for b in sorted(set(blocks[m])):
        s = m & (blocks == b)
        print(f"  {b:>4} {s.sum():5d} {np.median(tgt[s]):10.2e} "
              f"{err_rel[s].mean():9.4f} {floor_rel[s].mean():9.4f} "
              f"{np.median(np.abs(z[s])):8.2f} {(np.abs(z[s])>3).sum():6d}")

    # ---- per arita' ----
    print(f"\n  per arita' (addestrati)")
    for a in sorted(set(arity[m])):
        s = m & (arity == a)
        print(f"    arita' {a}: n={s.sum():5d}  err.rel={err_rel[s].mean():.4f}  "
              f"pavim.={floor_rel[s].mean():.4f}  |z| med={np.median(np.abs(z[s])):.2f}")

    return pd.DataFrame({
        "pop": name, "blocco": blocks, "arita": arity,
        "attrs": [str(c["attrs"]) for c in cons],
        "vals": [str(c["vals"]) for c in cons],
        "alpha_target": tgt, "alpha_oss": obs,
        "err_rel": err_rel, "pavimento_rel": floor_rel, "z": z,
        "addestrato": trained,
    })


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
    cdir = os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")
    pops = (a[a.index("--pops") + 1].split(",") if "--pops" in a
            else [f"popolazione_{liv}.csv"])
    out_csv = a[a.index("--csv") + 1] if "--csv" in a else None

    spec = json.load(open(os.path.join(cdir, f"cs_{liv}.json")))
    print(f"[cs] {liv}: vars={spec['vars']}")
    print(f"[cs] |X|={int(np.prod(spec['domain_sizes'])):,}  "
          f"vincoli={len(spec['constraints'])}  min_alpha={ma}")

    frames = []
    for p in pops:
        path = p if os.path.isabs(p) else os.path.join(cdir, p)
        if not os.path.exists(path):
            print(f"  [salto] {p} non trovato")
            continue
        df = pd.read_csv(path)
        frames.append(report(os.path.basename(path), encode(df, spec), spec, ma))

    if out_csv and frames:
        pd.concat(frames).to_csv(out_csv, index=False)
        print(f"\n[csv] dettaglio per vincolo -> {out_csv}")


if __name__ == "__main__":
    main()
