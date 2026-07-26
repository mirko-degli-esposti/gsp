#!/usr/bin/env python3
"""
regress_fit.py — confronto di regressione fra due fit_<LIV>.json.

Serve a verificare che una modifica *puramente implementativa* (dedup di F_g,
riuso di F nel solver, nuovo builder) non cambi la matematica: lambdas e
diagnostiche devono uscire IDENTICHE bit per bit.

    python regress_fit.py baseline/fit_K7C.json constraints_2024/fit_K7C.json
    python regress_fit.py base.json new.json --csv baseline/popolazione_K7C.csv \\
                                                   constraints_2024/popolazione_K7C.csv

Campi ignorati: t_exact_s, t_gibbs_s (tempi di esecuzione).
Campi ignorati di default: tutto il ramo Gibbs (non e' seeded, quindi non
riproducibile run-to-run). Usa --with-gibbs solo se hai reso deterministico
GibbsPCDSolver.

Exit code 0 se identici, 1 altrimenti.
"""

import sys
import json
import struct
import hashlib
import math

IGNORE_ALWAYS = {"t_exact_s", "t_gibbs_s"}
IGNORE_GIBBS = {"lambdas_gibbs", "gibbs", "kl_exact_gibbs", "kl_gibbs_exact",
                "t_gibbs_s"}
# campi che devono coincidere perche' i due run siano confrontabili
COMPARABILITY = ["comune", "anno", "livello", "eps", "min_alpha", "pool",
                 "outer", "sparse", "vars", "domain_sizes"]

GREEN, RED, YEL, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def bits(x):
    return struct.pack("<d", float(x)).hex()


def ulp_diff(a, b):
    """Distanza in ULP fra due float64 (0 = bitwise identici)."""
    if a == b:
        return 0
    if math.isnan(a) or math.isnan(b):
        return float("inf")
    ia = struct.unpack("<q", struct.pack("<d", float(a)))[0]
    ib = struct.unpack("<q", struct.pack("<d", float(b)))[0]
    if ia < 0:
        ia = -(ia & 0x7FFFFFFFFFFFFFFF) - (1 << 63)
    if ib < 0:
        ib = -(ib & 0x7FFFFFFFFFFFFFFF) - (1 << 63)
    return abs(ia - ib)


def cmp_lambdas(name, a, b, out):
    if a is None and b is None:
        out.append((name, True, "entrambi None"))
        return
    if a is None or b is None:
        out.append((name, False, f"uno dei due e' None ({a is None}/{b is None})"))
        return
    if len(a) != len(b):
        out.append((name, False, f"lunghezze diverse: {len(a)} vs {len(b)}"))
        return
    diffs = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if bits(x) != bits(y)]
    if not diffs:
        out.append((name, True, f"{len(a)} valori bitwise identici"))
        return
    worst = max(diffs, key=lambda t: ulp_diff(t[1], t[2]))
    maxrel = max(abs(x - y) / max(abs(x), abs(y), 1e-300) for _, x, y in diffs)
    out.append((name, False,
                f"{len(diffs)}/{len(a)} valori differiscono | "
                f"max ULP={ulp_diff(worst[1], worst[2])} a j={worst[0]} "
                f"({worst[1]!r} vs {worst[2]!r}) | max diff relativa={maxrel:.3e}"))


def cmp_value(name, a, b, out):
    if isinstance(a, float) or isinstance(b, float):
        ok = (a is None and b is None) or (
            a is not None and b is not None and bits(a) == bits(b))
        msg = "bitwise identico" if ok else \
              f"{a!r} vs {b!r} (ULP={ulp_diff(a, b) if None not in (a, b) else 'n/a'})"
    else:
        ok = a == b
        msg = "identico" if ok else f"{a!r} vs {b!r}"
    out.append((name, ok, msg))


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    p_old, p_new = args[0], args[1]
    with_gibbs = "--with-gibbs" in args
    csv_pair = None
    if "--csv" in args:
        i = args.index("--csv")
        csv_pair = (args[i + 1], args[i + 2])

    A = json.load(open(p_old))
    B = json.load(open(p_new))

    print("=" * 72)
    print(f"baseline : {p_old}")
    print(f"nuovo    : {p_new}")
    print("=" * 72)

    # --- 0. confrontabilita' ---
    incomp = [k for k in COMPARABILITY if A.get(k) != B.get(k)]
    if incomp:
        print(f"{RED}I due run NON sono confrontabili: differiscono su "
              f"{incomp}{OFF}")
        for k in incomp:
            print(f"    {k}: {A.get(k)!r}  vs  {B.get(k)!r}")
        print("Rilancia con la stessa riga di comando del baseline.")
        return 1
    print(f"{GREEN}[ok]{OFF} run confrontabili "
          f"(livello={A.get('livello')}, min_alpha={A.get('min_alpha')}, "
          f"eps={A.get('eps')}, sparse={A.get('sparse')})")

    ignore = set(IGNORE_ALWAYS) | (set() if with_gibbs else IGNORE_GIBBS)
    if not with_gibbs:
        print(f"{YEL}[nota]{OFF} ramo Gibbs ignorato (non seeded). "
              f"Usa --no-gibbs nel run per un test pulito.")

    out = []
    keys = sorted((set(A) | set(B)) - ignore)
    for k in keys:
        a, b = A.get(k), B.get(k)
        if k in ("lambdas_exact", "lambdas_gibbs"):
            cmp_lambdas(k, a, b, out)
        elif isinstance(a, dict) and isinstance(b, dict):
            for kk in sorted(set(a) | set(b)):
                cmp_value(f"{k}.{kk}", a.get(kk), b.get(kk), out)
        else:
            cmp_value(k, a, b, out)

    print("-" * 72)
    w = max(len(n) for n, _, _ in out)
    for name, ok, msg in out:
        tag = f"{GREEN}OK  {OFF}" if ok else f"{RED}DIFF{OFF}"
        print(f"  {tag} {name:<{w}}  {msg}")

    # --- csv ---
    csv_ok = True
    if csv_pair:
        print("-" * 72)
        h = []
        for p in csv_pair:
            with open(p, "rb") as f:
                h.append(hashlib.sha256(f.read()).hexdigest())
        csv_ok = h[0] == h[1]
        tag = f"{GREEN}OK  {OFF}" if csv_ok else f"{RED}DIFF{OFF}"
        print(f"  {tag} popolazione csv (sha256)  {h[0][:16]} vs {h[1][:16]}")

    bad = [n for n, ok, _ in out if not ok]
    print("=" * 72)
    if not bad and csv_ok:
        print(f"{GREEN}REGRESSIONE PULITA — output identico bit per bit{OFF}")
        return 0
    print(f"{RED}*** {len(bad) + (0 if csv_ok else 1)} DIFFERENZE ***{OFF}")
    if bad:
        print("campi:", ", ".join(bad))
    return 1


if __name__ == "__main__":
    sys.exit(main())
