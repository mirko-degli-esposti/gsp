#!/usr/bin/env python3
"""residuo.py — residuo compositivo per sezione, con base leave-one-out.

MODULO CONDIVISO. Lo importano `misura_em.py`, `misura_composizioni.py` e
`misura_assorbimento.py`, che oggi ne duplicano una versione difettosa.
Si importa direttamente (`import residuo as R`) perche' la directory
dello script e' su sys.path quando si lancia
`python scripts/diagnostica/...`.


IL DIFETTO CHE CORREGGE

Le misure M-EM, M-EMb e l'assorbimento calcolavano il residuo di una
sezione contro la composizione del suo gruppo (zona, o zona x strato)
con la base costruita cosi':

    basi = s.groupby(gruppo)[campi].sum()      # <-- include la sezione

La sezione fa parte della propria base. Le conseguenze sono due, e la
seconda ha prodotto un numero sbagliato:

  1. I netti riportati sono SOTTOSTIMATI. Con ~29 sezioni per zona, la
     sezione pesa ~1/29 della base verso cui la si confronta, e la base
     e' tirata verso di lei. Errore conservativo: nessuna conclusione
     di `nota_background_sezione` cambia, ma i numeri vanno rifatti.

  2. STRATIFICARE ABBASSA IL NETTO ANCHE SENZA SPIEGARE NULLA. Dividendo
     la zona in tre strati il peso della sezione nella propria base
     triplica, la base si sposta verso di lei e la TVD scende. E' il
     «costo meccanico» che il placebo aveva misurato al 6-8% e che aveva
     reso illeggibile la caduta del 10-11% attribuita a `q_B`.

     Segno diagnostico che aveva messo sulla strada: la stratificazione
     CASUALE costava PIU' (8,4% a Parma) di quella per terzile di n
     (6,0%), ed era molto piu' variabile (5,3-10,6 su dieci semi). Con i
     terzili di n le sezioni grandi finiscono insieme e ciascuna pesa
     ~1/3 del proprio strato; coi terzili casuali una sezione grande puo'
     cadere fra piccole e dominare la base contro cui viene confrontata.


LA CORREZIONE

    base(u) = somma del gruppo - conteggi di u

Con la base leave-one-out il costo meccanico sparisce per costruzione:
raffinare la partizione non avvicina piu' la base alla sezione. Il
placebo con stratificazione casuale deve quindi dare caduta ~0, ed e' il
test di regressione del modulo (`--placebo`).


IL PAVIMENTO E' UN BOOTSTRAP PARAMETRICO DELL'INTERO STIMATORE

Non basta simulare la sezione: sotto l'ipotesi nulla anche la base e'
aleatoria. Ogni replica simula TUTTE le sezioni del gruppo dalla
composizione del gruppo, a n fissato, e poi applica lo STESSO stimatore
-- leave-one-out compreso -- ai conteggi simulati. Cosi' il pavimento
riflette esattamente la statistica che si usa, e non una sua versione
semplificata.

Le sezioni sotto `min_n` entrano nella BASE ma non nella media: la
composizione di riferimento va stimata su tutta l'informazione
disponibile, il residuo si misura solo dove e' misurabile. Stessa regola
nell'osservato e nel simulato.


USO COME LIBRERIA

    import residuo as R
    r = R.netto(s, ["EM5", "EM6"], "zona", min_n=30)
    r["netto"], r["oss"], r["pav"], r["p95"], r["k"], r["massa"]

`r["netto"]` e' None quando l'osservata sta sotto il p95 del pavimento:
in quel caso il numero non si legge e va dichiarato non misurabile.


USO COME SCRIPT

    python scripts/diagnostica/residuo.py 034027 037006
    python scripts/diagnostica/residuo.py --placebo 034027

Senza `--placebo` misura, per ciascun comune, il residuo di
A = [EM5, EM6] contro la zona, con e senza leave-one-out, per quantificare
la correzione ai numeri gia' pubblicati. Con `--placebo` ripete
l'esperimento di stratificazione (q_B, terzile di n, casuale) che con la
base LOO deve dare cadute ~0 tranne l'eventuale assorbimento vero.
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


def elenco_comuni():
    for attr in ("COMUNI", "REGISTRO", "REGISTRO_COMUNI", "INFO"):
        v = getattr(G, attr, None)
        if isinstance(v, dict) and v:
            return sorted(v)
    return None


def carica(comune):
    """Sezioni del comune con le composizioni A (EM5/EM6) e B (UE/extra-UE)."""
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
    s["n_A"] = s[["A_g2", "A_imm"]].sum(axis=1)
    nb = s[["B_ue", "B_xue"]].sum(axis=1)
    s["q_b"] = np.where(nb > 0, s["B_ue"] / nb.replace(0, np.nan), np.nan)
    return s, None


# --------------------------------------------------------------- stimatore

def _tvd_pieno(a, b, campi):
    """TVD su supporto PIENO: gli zeri sono conteggi nulli, non modalita'
    assenti, quindi la guardia di T.tvd passa legittimamente."""
    sa = pd.Series(np.asarray(a, float), index=campi)
    sb = pd.Series(np.asarray(b, float), index=campi)
    if sa.sum() <= 0 or sb.sum() <= 0:
        return np.nan
    return T.tvd(sa, sb)


def _media(X, tot, gid, n_u, tenute, campi, loo):
    """Media pesata dei residui delle unita' in `tenute`.

    X    (m, k) conteggi per unita'      tot  (G, k) totali per gruppo
    gid  (m,)   indice di gruppo         n_u  (m,)   numerosita' per unita'
    """
    v, w = [], []
    for i in tenute:
        b = tot[gid[i]] - X[i] if loo else tot[gid[i]]
        d = _tvd_pieno(X[i], b, campi)
        if np.isfinite(d):
            v.append(d)
            w.append(n_u[i])
    if not v:
        return np.nan
    return float(np.average(v, weights=w))


def netto(s, campi, gruppo_col, min_n=MIN_N, n_perm=N_PERM, loo=True,
          seme=20260809):
    """Residuo medio delle sezioni contro la composizione del gruppo.

    Con `loo=True` la base esclude la sezione stessa. Il pavimento e' un
    bootstrap parametrico dello stesso stimatore.
    """
    rng = np.random.default_rng(seme)
    campi = list(campi)
    agg = s.groupby("SEZ21_ID")[campi].sum()
    grp = s.groupby("SEZ21_ID")[gruppo_col].first()

    X = agg.to_numpy(float)
    n_u = X.sum(axis=1)
    gruppi = pd.Index(sorted(grp.unique()))
    gid = gruppi.get_indexer(grp.reindex(agg.index).to_numpy())

    tot = np.zeros((len(gruppi), len(campi)))
    np.add.at(tot, gid, X)

    tenute = [i for i in range(len(X)) if n_u[i] >= min_n]
    massa = n_u[tenute].sum() / n_u.sum() if n_u.sum() > 0 else 0.0
    vuoto = {"netto": None, "oss": None, "pav": None, "p95": None,
             "k": len(tenute), "massa": float(massa)}
    if not tenute:
        return vuoto

    oss = _media(X, tot, gid, n_u, tenute, campi, loo)
    if not np.isfinite(oss):
        return vuoto

    p = tot / np.where(tot.sum(axis=1, keepdims=True) > 0,
                       tot.sum(axis=1, keepdims=True), 1)
    sim = []
    for _ in range(n_perm):
        S = np.zeros_like(X)
        for i in range(len(X)):
            pu = p[gid[i]]
            if pu.sum() <= 0:
                continue
            S[i] = rng.multinomial(int(round(n_u[i])), pu / pu.sum())
        tot_s = np.zeros_like(tot)
        np.add.at(tot_s, gid, S)
        m = _media(S, tot_s, gid, S.sum(axis=1), tenute, campi, loo)
        if np.isfinite(m):
            sim.append(m)
    if not sim:
        return vuoto

    mu, p95 = float(np.mean(sim)), float(np.percentile(sim, 95))
    out = {"oss": float(oss), "pav": mu, "p95": p95,
           "k": len(tenute), "massa": float(massa)}
    out["netto"] = None if oss < p95 else float(oss) - mu
    return out


def terzili_in_zona(s, valori, etichetta="t"):
    """Terzili di `valori` calcolati DENTRO ogni zona."""
    out = []
    for _, g in s.groupby("zona"):
        v = valori.loc[g.index]
        try:
            t = pd.qcut(v.rank(method="first"), 3,
                        labels=[f"{etichetta}1", f"{etichetta}2",
                                f"{etichetta}3"]).astype(str)
        except ValueError:
            t = pd.Series(f"{etichetta}0", index=g.index)
        out.append(t.fillna(f"{etichetta}0"))
    return pd.concat(out).reindex(s.index).fillna(f"{etichetta}0")


# ------------------------------------------------------------------- CLI

def _f(v):
    return f"{v:+.4f}" if v is not None else "  n.m."


def confronto(s, nome):
    """Quanto vale la correzione leave-one-out sui numeri gia' pubblicati."""
    campi = ["A_g2", "A_imm"]
    a = netto(s, campi, "zona", loo=False)
    b = netto(s, campi, "zona", loo=True)
    print(f"   A | zona   senza LOO {_f(a['netto'])}   con LOO "
          f"{_f(b['netto'])}", end="")
    if a["netto"] and b["netto"]:
        print(f"   sottostima {(1 - a['netto'] / b['netto']) * 100:+.1f}%")
    else:
        print()
    print(f"      {b['k']} sezioni, massa {b['massa']:.1%}")
    return b["netto"]


def placebo(s, nome, base, ripetizioni=10):
    """Con la base LOO la stratificazione casuale deve costare ~0."""
    campi = ["A_g2", "A_imm"]
    if not base:
        print("   base non misurabile: placebo saltato")
        return

    def cad(col):
        r = netto(s, campi, col)
        return None if r["netto"] is None else (1 - r["netto"] / base) * 100

    s = s.copy()
    s["g_qb"] = s["zona"] + "|" + terzili_in_zona(s, s["q_b"], "q")
    s["g_n"] = s["zona"] + "|" + terzili_in_zona(s, s["n_A"], "n")
    cq, cn = cad("g_qb"), cad("g_n")

    val = []
    for i in range(ripetizioni):
        r = np.random.default_rng(1000 + i)
        s["g_rnd"] = s["zona"] + "|" + terzili_in_zona(
            s, pd.Series(r.random(len(s)), index=s.index), "r")
        c = cad("g_rnd")
        if c is not None:
            val.append(c)

    g = lambda v: f"{v:6.1f}%" if v is not None else "  n.m."
    print(f"   caduta stratificando per q_B      {g(cq)}")
    print(f"   caduta stratificando per n        {g(cn)}")
    if val:
        m, lo, hi = np.mean(val), np.min(val), np.max(val)
        print(f"   caduta stratificazione CASUALE  {m:6.1f}%   "
              f"(min {lo:.1f}, max {hi:.1f}, {len(val)} semi)")
        print(f"      con la base LOO deve stare intorno a zero: "
              f"e' il test di regressione")
        if cq is not None:
            print(f"   ECCESSO q_B sul placebo: {cq - m:+.1f} punti")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comuni", nargs="*")
    ap.add_argument("--placebo", action="store_true",
                    help="ripete l'esperimento di stratificazione con LOO")
    ap.add_argument("--ripetizioni", type=int, default=10)
    a = ap.parse_args()
    comuni = a.comuni or elenco_comuni()
    if not comuni:
        sys.exit("passare i codici ISTAT come argomenti")

    for c in comuni:
        s, err = carica(c)
        if s is None:
            print(f"\n[{c}] saltato: {err}")
            continue
        nome = G.info(c).get("nome", c)
        print("\n" + "=" * 72)
        print(f"{nome} ({c}) · {s['zona'].nunique()} zone · {len(s)} sezioni")
        print("=" * 72)
        base = confronto(s, nome)
        if a.placebo:
            print()
            placebo(s, nome, base, a.ripetizioni)

    print("\n   La base leave-one-out elimina il costo meccanico della")
    print("   stratificazione: con LOO la caduta per stratificazione casuale")
    print("   deve essere ~0, e la caduta per q_B e' direttamente")
    print("   l'assorbimento, senza sottrazioni fra numeri rumorosi.")


if __name__ == "__main__":
    main()
