#!/usr/bin/env python3
"""Chiusura del cerchio: `EM` contro `ST` sulla stessa popolazione.

M-EM ha misurato un netto zona->sezione positivo su tutte e undici le
citta' (nota_background_sezione_v1). `nota_segnale_compositivo_v3` aveva
concluso che sotto il quartiere si perde l'85-98% del segnale
compositivo. Le due cose sembrano in conflitto, e ci sono DUE
spiegazioni possibili:

  (1) COMPOSIZIONI DIVERSE. Quella nota misura la composizione per AREA
      DI CITTADINANZA (UE / extra-UE), M-EM il BACKGROUND GENERAZIONALE
      (nato in Italia / nato all'estero). Due partizioni diverse degli
      stessi stranieri, potenzialmente con geografie diverse: la seconda
      generazione si concentra dove c'e' edilizia popolare e scuole, non
      dove si concentra una nazionalita'.

  (2) STIMATORI DIVERSI. Quella nota usa una decomposizione della
      varianza compositiva, M-EM la TVD con pavimento multinomiale. Un
      conflitto apparente potrebbe essere un artefatto del confronto fra
      due metriche, non un fatto sul territorio.

QUESTO SCRIPT LE SEPARA, perche' misura le due composizioni con lo
STESSO stimatore, sulla STESSA popolazione, nelle STESSE sezioni:

    A   [EM5, EM6]                    stranieri per luogo di nascita
    B   [ST17+ST18, ST20+ST21]        stranieri per area di cittadinanza

Stesso denominatore (gli stranieri della sezione), due modalita'
ciascuna, stesso pavimento, stesse soglie. La sola differenza e' QUALE
partizione binaria si guarda.

  A >> B  ->  spiegazione (1): le geografie sono diverse, la
              riconciliazione di nota_background_sezione_v1 §6 regge.
  A ~= B  ->  spiegazione (2): il conflitto e' fra stimatori, e la
              conclusione di nota_segnale_compositivo_v3 va riletta
              alla luce del pavimento.

Come controllo si misura anche C = [EM1, EM2+EM3+EM4] sugli italiani:
nativi contro tutto il resto, sempre due modalita', per avere un terzo
punto sulla stessa scala.

NESSUNA PREVISIONE REGISTRATA. Le ultime tre di questa linea di lavoro
(M3', M4, M-EM) sono state tutte falsificate nella stessa direzione, e
una quarta congettura a priori non aggiungerebbe informazione: qui si
guarda il numero.

    python scripts/diagnostica/misura_composizioni.py 034027
    python scripts/diagnostica/misura_composizioni.py

Fonte: `istat_sezioni_2023`, derivati in `data/submun/`.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

import gsp.common as G
import gsp.tvd as T

# ST17/18 = UE (M/F), ST20/21 = extra-UE (M/F). Corrisponde a `area` in
# anello 2 (riferimento v22 §2.2). La verifica di integrita' sotto
# controlla la somma contro EM5+EM6: se i campi fossero altri, si vede.
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

    serve = ([f"EM{i}" for i in range(1, 7)] + ST_UE + ST_XUE + ["P1"])
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

    # le due partizioni, costruite sullo stesso denominatore
    s["A_g2"] = s["EM5"]
    s["A_imm"] = s["EM6"]
    s["B_ue"] = s[ST_UE].sum(axis=1)
    s["B_xue"] = s[ST_XUE].sum(axis=1)
    s["C_nat"] = s["EM1"]
    s["C_altro"] = s[["EM2", "EM3", "EM4"]].sum(axis=1)
    return s, None


def integrita(s, nome):
    """I due totali devono coincidere: se no, i campi ST sono altri."""
    a = float(s[["A_g2", "A_imm"]].sum().sum())
    b = float(s[["B_ue", "B_xue"]].sum().sum())
    scarto = (b - a) / a * 100 if a > 0 else float("nan")
    print(f"   stranieri: EM5+EM6 = {a:,.0f} · ST = {b:,.0f} "
          f"(scarto {scarto:+.2f}%)".replace(",", "."))
    if abs(scarto) > 2:
        print("   !! i due totali divergono oltre il 2%: le due "
              "composizioni NON hanno lo stesso\n      denominatore e il "
              "confronto A contro B non e' controllato. Verificare i "
              "campi ST.")
        return False
    return True


def _tvd(a, b, campi):
    sa = pd.Series(np.asarray(a, float), index=campi)
    sb = pd.Series(np.asarray(b, float), index=campi)
    if sa.sum() <= 0 or sb.sum() <= 0:
        return np.nan
    return T.tvd(sa, sb)


def netto(s, campi, etichetta, min_n=MIN_N, n_perm=N_PERM):
    """M-EMb: TVD(P|sezione, P|zona), con pavimento multinomiale."""
    agg = s.groupby("SEZ21_ID")[campi].sum()
    key = s.groupby("SEZ21_ID")["zona"].first()
    basi = s.groupby("zona")[campi].sum()
    p = basi.div(basi.sum(axis=1), axis=0)

    n_u = agg.sum(axis=1)
    tenute = [u for u in n_u.index if n_u.loc[u] >= min_n]
    n_tot = float(agg.sum().sum())
    if not tenute:
        print(f"   {etichetta:34s} non misurabile: nessuna sezione con "
              f"n >= {min_n}")
        return None

    oss = []
    for u in tenute:
        d = _tvd(agg.loc[u].to_numpy(), basi.loc[key.loc[u]].to_numpy(), campi)
        if np.isfinite(d):
            oss.append((d, n_u.loc[u]))
    if not oss:
        return None
    o = float(np.average([x[0] for x in oss],
                         weights=[x[1] for x in oss]))

    sim = []
    for _ in range(n_perm):
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
        return None
    mu, p95 = float(np.mean(sim)), float(np.percentile(sim, 95))
    massa = sum(x[1] for x in oss) / n_tot

    # l'avviso che mancava in misura_em.py (nota_background_sezione §7.1)
    if o < p95:
        print(f"   {etichetta:34s} NON MISURABILE: osservata {o:.4f} sotto "
              f"il p95 del pavimento ({p95:.4f})")
        print(f"      {len(tenute)} sezioni, massa usata {massa:.1%}")
        return None

    print(f"   {etichetta:34s} oss {o:.4f}  pav {mu:.4f} (p95 {p95:.4f})  "
          f"NETTO {o - mu:+.4f}")
    print(f"      {len(tenute)} sezioni, massa usata {massa:.1%}")
    return o - mu


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
        ok = integrita(s, nome)

        nA = netto(s, ["A_g2", "A_imm"], "A  stranieri: g2 / immigrati")
        nB = netto(s, ["B_ue", "B_xue"], "B  stranieri: UE / extra-UE")
        nC = netto(s, ["C_nat", "C_altro"], "C  italiani: nativi / altri")
        righe.append({"comune": nome, "zone": n_zone, "integro": ok,
                      "A": nA, "B": nB, "C": nC})

    e = pd.DataFrame(righe)
    print("\n" + "=" * 72)
    print("riepilogo — netto zona->sezione, tre partizioni binarie")
    print("=" * 72)
    print(f"   {'comune':18s} {'zone':>5s} {'A g2/imm':>10s} "
          f"{'B UE/xUE':>10s} {'C ita':>10s} {'A/B':>6s}")
    for _, r in e.iterrows():
        f = lambda v: f"{v:+.4f}" if pd.notna(v) and v is not None else "   n.m."
        ab = (f"{r.A / r.B:.2f}" if (r.A and r.B and r.B > 1e-9) else "  n/d")
        print(f"   {r.comune:18s} {r.zone:5d} {f(r.A):>10s} {f(r.B):>10s} "
              f"{f(r.C):>10s} {ab:>6s}")

    for col, nome in (("A", "A g2/immigrati"), ("B", "B UE/extra-UE"),
                      ("C", "C italiani")):
        v = e[col].dropna()
        if len(v):
            print(f"\n   {nome:18s} mediana {v.median():+.4f}  "
                  f"({int((v > 0).sum())}/{len(v)} positivi)")

    print("\n   A >> B  -> composizioni con geografie diverse: la")
    print("             riconciliazione di nota_background_sezione §6 regge.")
    print("   A ~= B  -> il conflitto con nota_segnale_compositivo_v3 e' fra")
    print("             STIMATORI, non fra composizioni: quella conclusione")
    print("             va riletta alla luce del pavimento.")


if __name__ == "__main__":
    main()
