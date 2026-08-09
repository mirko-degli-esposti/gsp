#!/usr/bin/env python3
"""Placebo per la «caduta» di misura_assorbimento.py.

`misura_assorbimento.py` ha misurato che stratificare le sezioni per
terzile di q_B (quota UE) dentro la zona abbassa il netto di A
(EM5/EM6) del 10-11%. La lettura naturale sarebbe: `area`, che la
pipeline gia' condiziona per sezione, assorbe il 10% del segnale di
`EM`.

MA LA CADUTA NON SEGUE L'ASSOCIAZIONE. La correlazione fra le due quote
a livello di zona differisce di un fattore quattro fra le due citta'
(Parma +0,467, Bologna +0,118) e la caduta e' identica (11% e 10%). Se
misurasse assorbimento reale dovrebbe seguire l'associazione.

L'ipotesi alternativa e' che il ~10% sia il COSTO MECCANICO DELLA
STRATIFICAZIONE: triplicando le basi, ogni sezione viene confrontata con
un gruppo piu' piccolo e quindi piu' vicino a lei per costruzione, e il
pavimento multinomiale non corregge questo effetto perche' l'assegnazione
di strato resta fissa nella simulazione.

Il test e' un placebo: stessa procedura, stesso numero di strati, stesse
dimensioni, ma stratificando per una variabile CASUALE invece che per
q_B.

    caduta_placebo ~= caduta_vera   ->  assorbimento non misurabile:
                                        la caduta e' artefatto della
                                        stratificazione
    caduta_vera >> caduta_placebo   ->  assorbimento reale, e la sua
                                        entita' e' la differenza

Si misura anche un terzo caso, la stratificazione per DIMENSIONE della
sezione (terzili di n): non ha alcun rapporto con la composizione, ma
raggruppa sezioni simili per rumore, e serve a distinguere l'effetto
«basi piu' piccole» da quello «sezioni piu' omogenee».

Per stabilita' il placebo casuale si ripete `--ripetizioni` volte con
semi diversi e se ne riporta media e intervallo: una singola
assegnazione casuale e' essa stessa rumorosa.

    python scripts/diagnostica/placebo_assorbimento.py 034027 037006
    python scripts/diagnostica/placebo_assorbimento.py --ripetizioni 20

Fonte: `istat_sezioni_2023`, derivati in `data/submun/`.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

import gsp.common as G
import gsp.tvd as T

ST_UE = ["ST17", "ST18"]
ST_XUE = ["ST20", "ST21"]
CAMPI_A = ["A_g2", "A_imm"]
SPECIALI = ("888888", "999999")
MIN_N = 30
N_PERM = 50
RNG = np.random.default_rng(20260809)


def elenco_comuni():
    for attr in ("COMUNI", "REGISTRO", "REGISTRO_COMUNI", "INFO"):
        v = getattr(G, attr, None)
        if isinstance(v, dict) and v:
            return sorted(v)
    return None


def carica(comune):
    path = G.path_sezioni(comune)
    if not os.path.exists(path):
        return None, f"file sezioni assente: {path}"
    s = pd.read_csv(path)
    serve = ["EM5", "EM6"] + ST_UE + ST_XUE
    manca = [c for c in serve if c not in s.columns]
    if manca:
        return None, f"campi assenti: {manca}"

    sez = s["SEZ21_ID"].astype("Int64").astype(str)
    s = s[~sez.str.contains("|".join(SPECIALI), regex=True)].copy()
    liv = G.livello_col(comune) if G.info(comune)["livello"] else None
    if liv is not None and liv not in s.columns:
        return None, f"colonna zona {liv} assente"
    s["zona"] = (s[liv].astype("Int64").astype(str) if liv is not None
                 else "0")
    for c in serve:
        s[c] = pd.to_numeric(s[c], errors="coerce").fillna(0.0)

    s["A_g2"], s["A_imm"] = s["EM5"], s["EM6"]
    s["B_ue"] = s[ST_UE].sum(axis=1)
    s["B_xue"] = s[ST_XUE].sum(axis=1)
    s["n"] = s[CAMPI_A].sum(axis=1)
    nb = s[["B_ue", "B_xue"]].sum(axis=1)
    s["q_b"] = np.where(nb > 0, s["B_ue"] / nb.replace(0, np.nan), np.nan)
    return s, None


def _tvd(a, b):
    sa = pd.Series(np.asarray(a, float), index=CAMPI_A)
    sb = pd.Series(np.asarray(b, float), index=CAMPI_A)
    if sa.sum() <= 0 or sb.sum() <= 0:
        return np.nan
    return T.tvd(sa, sb)


def terzili_in_zona(s, valori, etichetta_nan="b0"):
    """Terzili di `valori` calcolati DENTRO ogni zona."""
    out = []
    for _, g in s.groupby("zona"):
        v = valori.loc[g.index]
        try:
            t = pd.qcut(v.rank(method="first"), 3,
                        labels=["t1", "t2", "t3"]).astype(str)
        except ValueError:
            t = pd.Series(etichetta_nan, index=g.index)
        out.append(t.fillna(etichetta_nan))
    return pd.concat(out).reindex(s.index).fillna(etichetta_nan)


def netto(s, gruppo_col, min_n=MIN_N, n_perm=N_PERM):
    agg = s.groupby("SEZ21_ID")[CAMPI_A].sum()
    key = s.groupby("SEZ21_ID")[gruppo_col].first()
    basi = s.groupby(gruppo_col)[CAMPI_A].sum()
    p = basi.div(basi.sum(axis=1), axis=0)

    n_u = agg.sum(axis=1)
    tenute = [u for u in n_u.index if n_u.loc[u] >= min_n]
    if not tenute:
        return None

    v, w = [], []
    for u in tenute:
        d = _tvd(agg.loc[u].to_numpy(), basi.loc[key.loc[u]].to_numpy())
        if np.isfinite(d):
            v.append(d)
            w.append(n_u.loc[u])
    if not v:
        return None
    oss = float(np.average(v, weights=w))

    sim = []
    for _ in range(n_perm):
        t, ww = [], []
        for u in tenute:
            pu = p.loc[key.loc[u]].to_numpy(float)
            if not np.isfinite(pu).all() or pu.sum() <= 0:
                continue
            n = int(round(n_u.loc[u]))
            d = _tvd(RNG.multinomial(n, pu / pu.sum()), pu)
            if np.isfinite(d):
                t.append(d)
                ww.append(n)
        if t:
            sim.append(float(np.average(t, weights=ww)))
    if not sim:
        return None
    mu = float(np.mean(sim))
    if oss < float(np.percentile(sim, 95)):
        return None
    return oss - mu


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comuni", nargs="*")
    ap.add_argument("--ripetizioni", type=int, default=10,
                    help="assegnazioni casuali indipendenti per il placebo")
    a = ap.parse_args()
    comuni = a.comuni or elenco_comuni()
    if not comuni:
        sys.exit("passare i codici ISTAT come argomenti")

    righe = []
    for c in comuni:
        s, err = carica(c)
        if s is None:
            print(f"\n[{c}] saltato: {err}")
            continue
        nome = G.info(c).get("nome", c)
        print("\n" + "=" * 72)
        print(f"{nome} ({c}) · {s['zona'].nunique()} zone · {len(s)} sezioni")
        print("=" * 72)

        base = netto(s, "zona")
        if base is None or base <= 0:
            print("   netto A|zona non misurabile: saltato")
            continue
        print(f"   A | zona                      {base:+.4f}   (riferimento)")

        def caduta(col):
            n = netto(s, col)
            return (None, None) if n is None else (n, (1 - n / base) * 100)

        s["g_qb"] = s["zona"] + "|" + terzili_in_zona(s, s["q_b"])
        nq, cq = caduta("g_qb")
        print(f"   A | zona, terzile q_B         {nq:+.4f}   caduta {cq:5.1f}%")

        s["g_n"] = s["zona"] + "|" + terzili_in_zona(s, s["n"])
        nn, cn = caduta("g_n")
        print(f"   A | zona, terzile n           {nn:+.4f}   caduta {cn:5.1f}%")

        cad_p = []
        for i in range(a.ripetizioni):
            r = np.random.default_rng(1000 + i)
            s["g_rnd"] = s["zona"] + "|" + terzili_in_zona(
                s, pd.Series(r.random(len(s)), index=s.index))
            _, cp = caduta("g_rnd")
            if cp is not None:
                cad_p.append(cp)
        if cad_p:
            m, lo, hi = (float(np.mean(cad_p)), float(np.min(cad_p)),
                         float(np.max(cad_p)))
            print(f"   A | zona, terzile CASUALE     "
                  f"caduta {m:5.1f}%   (min {lo:.1f}, max {hi:.1f}, "
                  f"{len(cad_p)} ripetizioni)")
            eccesso = cq - m if cq is not None else None
            if eccesso is not None:
                print(f"\n   ECCESSO q_B sul placebo: {eccesso:+.1f} punti "
                      f"percentuali")
                if abs(eccesso) < (hi - lo):
                    print("   -> dentro la dispersione del placebo: "
                          "ASSORBIMENTO NON MISURABILE.\n"
                          "      La caduta e' costo meccanico della "
                          "stratificazione.")
                else:
                    print("   -> fuori dalla dispersione del placebo: "
                          "assorbimento reale,\n"
                          "      di entita' pari all'eccesso.")
            righe.append({"comune": nome, "base": base, "cad_qB": cq,
                          "cad_n": cn, "cad_rnd": m,
                          "disp": hi - lo})

    if righe:
        e = pd.DataFrame(righe)
        print("\n" + "=" * 72)
        print("riepilogo — cadute in punti percentuali sul netto A|zona")
        print("=" * 72)
        print(f"   {'comune':18s} {'A|zona':>9s} {'q_B':>7s} {'n':>7s} "
              f"{'casual':>7s} {'ecc.':>7s}")
        for _, r in e.iterrows():
            print(f"   {r.comune:18s} {r.base:+9.4f} {r.cad_qB:6.1f}% "
                  f"{r.cad_n:6.1f}% {r.cad_rnd:6.1f}% "
                  f"{r.cad_qB - r.cad_rnd:+6.1f}")

    print("\n   La colonna che decide e' l'ECCESSO: caduta per q_B meno")
    print("   caduta per stratificazione casuale, a parita' di numero e")
    print("   dimensione degli strati. Se sta dentro la dispersione del")
    print("   placebo, l'assorbimento non e' misurabile e va scritto cosi'.")


if __name__ == "__main__":
    main()
