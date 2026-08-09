#!/usr/bin/env python3
"""Quanto di `EM` e' gia' catturato da `area`? (nota_background_sezione §7)

M-EM ha misurato il residuo zona->sezione della composizione A =
[EM5, EM6] (stranieri per luogo di nascita): +0,018-0,023. Ma
`misura_composizioni.py` ha poi mostrato che la composizione B =
[UE, extra-UE] ha residuo maggiore (+0,037-0,040) ED E' GIA' CONDIZIONATA
PER SEZIONE da `enrich.py` in anello 2 (`assegna_area_paese`, campi
ST17/18/20/21).

Se A e B sono associate, parte del segnale di A e' gia' assorbita da
`area`, e il guadagno reale del raffinamento `EM` e' inferiore a quanto
misurato. Questo script quantifica l'associazione, in tre modi con
robustezza decrescente.


(1) CORRELAZIONE FRA LE QUOTE A LIVELLO DI ZONA  -- la misura pulita

    q_A(z) = EM5 / (EM5+EM6)          quota di nati in Italia
    q_B(z) = UE  / (UE+extraUE)       quota di cittadini UE

    Con 4-33 zone da migliaia di stranieri ciascuna, le due quote sono
    di fatto esatte: la correlazione osservata e' associazione reale, non
    rumore. E' l'unico dei tre numeri che non richiede cautele.

    Limite: poche unita' (4-33), quindi intervallo largo.


(2) LA STESSA CORRELAZIONE A LIVELLO DI SEZIONE

    Piu' unita', ma le quote su 30-200 individui sono rumorose. Il
    confronto (1) vs (2) dice quanto il rumore attenui o gonfi: se (2)
    e' molto sotto (1), e' attenuazione classica; se e' sopra, c'e'
    struttura fine che le zone non vedono.


(3) TVD DI A CONDIZIONATA SU (zona x strato di q_B)  -- da leggere con
    cautela

    Si stratificano le sezioni per terzile di q_B DENTRO la zona, e si
    misura il residuo di A contro la composizione dello strato invece
    che della zona. La caduta del netto rispetto a M-EMb e' la stima
    diretta di quanto `area` assorba.

    CAUTELA, e non e' formale: q_B e' calcolata sugli STESSI individui
    di q_A, partizionati diversamente. Se le due partizioni fossero
    indipendenti ma entrambe rumorose sulla stessa n, stratificare per
    q_B potrebbe comunque catturare una parte di variazione condivisa.
    Il pavimento qui simula A dentro lo strato tenendo FISSA
    l'assegnazione di strato osservata, quindi non corregge questo
    effetto. La caduta va perci
o letta come LIMITE SUPERIORE
    dell'assorbimento.

    La misura senza cautele richiederebbe l'incrocio EM x area per
    sezione, che nel file regionale non esiste (§8.4 della nota).


COSA DECIDE

    associazione debole  -> il raffinamento EM aggiunge quasi tutto il
                            suo +0,018-0,023: si procede su enrich.py
    associazione forte   -> il guadagno netto e' piccolo, e conviene
                            spostare l'effort sull'anello 4

In ogni caso la partizione C (italiani nativi / altri, +0,021-0,023)
NON e' toccata: per gli italiani non esiste alcun condizionamento di
sezione, quindi quel guadagno e' pulito qualunque cosa dicano i numeri
qui sotto.

    python scripts/diagnostica/misura_assorbimento.py 034027 037006
    python scripts/diagnostica/misura_assorbimento.py

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
    s["n"] = s[["A_g2", "A_imm"]].sum(axis=1)
    return s, None


def _corr(q_a, q_b, w):
    """Pearson pesata e Spearman sui ranghi (non pesata)."""
    m = np.isfinite(q_a) & np.isfinite(q_b) & (w > 0)
    a, b, ww = q_a[m], q_b[m], w[m]
    if len(a) < 4:
        return np.nan, np.nan, int(len(a))
    ma = np.average(a, weights=ww)
    mb = np.average(b, weights=ww)
    cov = np.average((a - ma) * (b - mb), weights=ww)
    va = np.average((a - ma) ** 2, weights=ww)
    vb = np.average((b - mb) ** 2, weights=ww)
    pear = cov / np.sqrt(va * vb) if va > 0 and vb > 0 else np.nan
    sp = pd.Series(a).corr(pd.Series(b), method="spearman")
    return float(pear), float(sp), int(len(a))


def quote(d):
    na = d[["A_g2", "A_imm"]].sum(axis=1).to_numpy(float)
    nb = d[["B_ue", "B_xue"]].sum(axis=1).to_numpy(float)
    q_a = np.where(na > 0, d["A_g2"].to_numpy(float) / np.where(na > 0, na, 1),
                   np.nan)
    q_b = np.where(nb > 0, d["B_ue"].to_numpy(float) / np.where(nb > 0, nb, 1),
                   np.nan)
    return q_a, q_b, na


def _tvd(a, b, campi):
    sa = pd.Series(np.asarray(a, float), index=campi)
    sb = pd.Series(np.asarray(b, float), index=campi)
    if sa.sum() <= 0 or sb.sum() <= 0:
        return np.nan
    return T.tvd(sa, sb)


def netto_su(s, gruppo_col, campi=("A_g2", "A_imm"), min_n=MIN_N):
    """TVD(P(A|sezione), P(A|gruppo)) con pavimento multinomiale."""
    campi = list(campi)
    agg = s.groupby("SEZ21_ID")[campi].sum()
    key = s.groupby("SEZ21_ID")[gruppo_col].first()
    basi = s.groupby(gruppo_col)[campi].sum()
    p = basi.div(basi.sum(axis=1), axis=0)

    n_u = agg.sum(axis=1)
    tenute = [u for u in n_u.index if n_u.loc[u] >= min_n]
    if not tenute:
        return None, None, 0

    o_v, o_w = [], []
    for u in tenute:
        d = _tvd(agg.loc[u].to_numpy(), basi.loc[key.loc[u]].to_numpy(), campi)
        if np.isfinite(d):
            o_v.append(d)
            o_w.append(n_u.loc[u])
    if not o_v:
        return None, None, 0
    oss = float(np.average(o_v, weights=o_w))

    sim = []
    for _ in range(N_PERM):
        t, w = [], []
        for u in tenute:
            pu = p.loc[key.loc[u]].to_numpy(float)
            if not np.isfinite(pu).all() or pu.sum() <= 0:
                continue
            n = int(round(n_u.loc[u]))
            d = _tvd(RNG.multinomial(n, pu / pu.sum()), pu, campi)
            if np.isfinite(d):
                t.append(d)
                w.append(n)
        if t:
            sim.append(float(np.average(t, weights=w)))
    if not sim:
        return None, None, len(tenute)
    mu = float(np.mean(sim))
    p95 = float(np.percentile(sim, 95))
    if oss < p95:
        return None, p95, len(tenute)
    return oss - mu, p95, len(tenute)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comuni", nargs="*")
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
        n_zone = s["zona"].nunique()
        print("\n" + "=" * 72)
        print(f"{nome} ({c}) · {n_zone} zone · {len(s)} sezioni")
        print("=" * 72)

        # (1) zone
        z = s.groupby("zona")[["A_g2", "A_imm", "B_ue", "B_xue"]].sum()
        qa_z, qb_z, n_z = quote(z)
        pz, sz, kz = _corr(qa_z, qb_z, n_z)
        print(f"   (1) zone      r_pearson {pz:+.3f}  spearman {sz:+.3f}  "
              f"({kz} zone)")
        if kz >= 4:
            print(f"       q_A (nati in Italia) {np.average(qa_z, weights=n_z):.3f} "
                  f"± {np.sqrt(np.average((qa_z-np.average(qa_z,weights=n_z))**2, weights=n_z)):.3f}"
                  f" · q_B (UE) {np.average(qb_z, weights=n_z):.3f}")

        # (2) sezioni
        sm = s[s.n >= MIN_N]
        qa_s, qb_s, n_s = quote(sm)
        ps, ss, ks = _corr(qa_s, qb_s, n_s)
        print(f"   (2) sezioni   r_pearson {ps:+.3f}  spearman {ss:+.3f}  "
              f"({ks} sezioni con n>={MIN_N})")

        # (3) TVD condizionata
        s = s.copy()
        s["q_b"] = np.where(s[["B_ue", "B_xue"]].sum(axis=1) > 0,
                            s["B_ue"] / s[["B_ue", "B_xue"]].sum(axis=1)
                            .replace(0, np.nan), np.nan)
        strato = []
        for zz, g in s.groupby("zona"):
            q = g["q_b"]
            try:
                t = pd.qcut(q.rank(method="first"), 3,
                            labels=["b1", "b2", "b3"]).astype(str)
            except ValueError:
                t = pd.Series("b0", index=g.index)
            strato.append(t)
        s["strato_b"] = pd.concat(strato).reindex(s.index).fillna("b0")
        s["zona_b"] = s["zona"] + "|" + s["strato_b"]

        n1, _, k1 = netto_su(s, "zona")
        n2, _, k2 = netto_su(s, "zona_b")
        f = lambda v: f"{v:+.4f}" if v is not None else "  n.m."
        cad = (f"{(1 - n2 / n1) * 100:.0f}%"
               if (n1 and n2 and n1 > 1e-9) else "n/d")
        print(f"   (3) netto A | zona      {f(n1)}   ({k1} sezioni)")
        print(f"       netto A | zona,q_B  {f(n2)}   caduta {cad}")

        righe.append({"comune": nome, "zone": n_zone, "r_zona": pz,
                      "r_sez": ps, "A_zona": n1, "A_zona_b": n2})

    e = pd.DataFrame(righe)
    print("\n" + "=" * 72)
    print("riepilogo")
    print("=" * 72)
    print(f"   {'comune':18s} {'zone':>5s} {'r zona':>8s} {'r sez':>8s} "
          f"{'A|zona':>9s} {'A|zona,B':>9s} {'caduta':>7s}")
    for _, r in e.iterrows():
        f = lambda v: f"{v:+.4f}" if pd.notna(v) and v is not None else "   n.m."
        g = lambda v: f"{v:+.3f}" if pd.notna(v) else "    n/d"
        cad = (f"{(1 - r.A_zona_b / r.A_zona) * 100:.0f}%"
               if (r.A_zona and r.A_zona_b and r.A_zona > 1e-9) else "  n/d")
        print(f"   {r.comune:18s} {r.zone:5d} {g(r.r_zona):>8s} "
              f"{g(r.r_sez):>8s} {f(r.A_zona):>9s} {f(r.A_zona_b):>9s} "
              f"{cad:>7s}")

    print("\n   (1) e' il numero pulito: le quote di zona sono di fatto esatte.")
    print("   (3) e' un LIMITE SUPERIORE dell'assorbimento -- vedi la cautela")
    print("       nel docstring: q_B e' calcolata sugli stessi individui di q_A.")
    print("\n   |r| basso e caduta piccola -> il raffinamento EM aggiunge")
    print("      quasi tutto il suo valore: si procede su enrich.py.")
    print("   |r| alto e caduta grande   -> il guadagno netto e' piccolo;")
    print("      l'effort va sull'anello 4. Resta comunque valida la")
    print("      partizione C (italiani), che nessuno condiziona oggi.")


if __name__ == "__main__":
    main()
