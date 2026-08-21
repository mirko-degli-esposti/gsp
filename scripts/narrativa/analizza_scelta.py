#!/usr/bin/env python3
"""analizza_scelta.py — la lettura delle campagne dell'esperimento priors.

    python scripts/narrativa/analizza_scelta.py dati/campagne/scelta/campagna_*.json
    python scripts/narrativa/analizza_scelta.py FILE... --md note/analisi.md
    python scripts/narrativa/analizza_scelta.py FILE... --png figure/

Accetta UNA O PIU' campagne (modelli diversi, stesso campione) e produce,
nell'ordine in cui le domande vanno poste:

  1. PULIZIA        risposte parse-abili, `pulito`, None — prima di
                    leggere i numeri, quanto ci si puo' fidare del parsing
  2. MUTISMO (H4)   distribuzione delle scelte per modello: una modalita'
                    sopra il 95% e' la firma di Brescia-SIVE
  3. STABILITA'     accordo fra repliche per agente (che sono anche
                    ROTAZIONI delle opzioni: l'accordo misura insieme
                    pavimento di rumore e controllo di posizione)
  4. ANCORE         quantizzazione del continuo: quota di massa sui
                    valori tondi, i primi valori per frequenza
  5. ASSI           quota `universita'` e prob media per diploma3, gen3,
                    sesso, background, eta', comune — il segno di H1-H3
  6. QUALIFICA (H5) professionali con e senza qualifica triennale: se
                    prob(qualifica) ~ prob(maturita' professionale), il
                    modello non distingue il NON-ACCESSO
  7. LOGIT          y = (scelta == universita') su diploma3 + gen3 +
                    sesso + straniero + eta' + comune, IRLS senza
                    dipendenze. I COEFFICIENTI sono il confronto con il
                    reale (MUR/AlmaDiploma): qui si stampano, il
                    confronto sta nella nota — i tassi di riferimento
                    NON sono cablati qui dentro perche' vanno verificati
                    su fonte prima di diventare un benchmark.
  8. CONFRONTO      con piu' campagne: quota per asse fianco a fianco e
                    concordanza per-agente fra modelli (rho di Spearman
                    sulla prob media per agente)

Le batterie si aggregano per (uid, replica); gli attributi dell'agente
(qualifica inclusa) vengono dal JSON del campione, che si trova dal
campo `campione` della campagna o si passa con --campione.
"""

import argparse
import glob
import json
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd


# ------------------------------------------------------------- caricamento

def carica(percorsi, campione_arg):
    """-> df righe (uid, replica, modello, situazione, prob, attributi),
    piu' l'etichetta `universita'` presa dagli items della campagna."""
    righe, univ, agenti = [], None, None
    for p in percorsi:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        mod = d["modello"].split("/")[-1]
        for it in d.get("items", []):
            if it.get("response_type") == "choice":
                univ = it["choices"][0]
        if agenti is None:
            pc = campione_arg or os.path.join("dati/agenti", d["campione"])
            if not os.path.exists(pc):
                sys.exit(f"campione non trovato: {pc} (usare --campione)")
            with open(pc, encoding="utf-8") as f:
                agenti = {x["uid"]: x for x in json.load(f)["agenti"]}
        for r in d.get("risultati", []):
            x = agenti.get(r["uid"])
            if not x:
                continue
            righe.append({
                "modello": mod, "uid": r["uid"], "replica": r["replica"],
                "situazione": r["risposte"].get("situazione"),
                "prob": r["risposte"].get("prob_universita"),
                "cella": x["cella"], "comune": x["comune"],
                "diploma3": x["diploma3"], "gen3": x["gen3"],
                "sesso": x["sesso"], "eta": int(x["eta_anni"]),
                "straniero": x["cella"].split("\u00b7")[-1] == "straniero",
                "qualifica": bool(x.get("qualifica")),
            })
        # la pulizia si legge dalle righe survey, che portano `pulito`
        for s in d.get("survey", []):
            pass
    df = pd.DataFrame(righe)
    if df.empty:
        sys.exit("nessuna batteria nelle campagne indicate")
    return df, univ, agenti


def pulizia(percorsi):
    out = []
    for p in percorsi:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        s = pd.DataFrame(d.get("survey", []))
        if s.empty:
            continue
        mod = d["modello"].split("/")[-1]
        for item, g in s.groupby("item"):
            out.append({"modello": mod, "item": item, "n": len(g),
                        "pulito": g["pulito"].mean(),
                        "none": g["valore"].isna().mean()})
    return pd.DataFrame(out)


# ------------------------------------------------------------------ logit

def logit_irls(X, y, ridge=1e-6, it=40):
    """IRLS con una punta di ridge. Ritorna (beta, se, avviso_separazione).
    Nessuna dipendenza: statsmodels non e' un requisito della pipeline."""
    b = np.zeros(X.shape[1])
    XtW = None
    for _ in range(it):
        p = 1.0 / (1.0 + np.exp(-X @ b))
        W = np.clip(p * (1 - p), 1e-9, None)
        z = X @ b + (y - p) / W
        XtW = X.T * W
        A = XtW @ X + ridge * np.eye(X.shape[1])
        b2 = np.linalg.solve(A, XtW @ z)
        if np.max(np.abs(b2 - b)) < 1e-9:
            b = b2
            break
        b = b2
    cov = np.linalg.inv(XtW @ X + ridge * np.eye(X.shape[1]))
    se = np.sqrt(np.diag(cov))
    # quasi-separazione: succede davvero (liceo -> 100% al collaudo).
    # Non si nasconde con piu' ridge: si SEGNALA, e il coefficiente si
    # legge come «oltre soglia», non come stima.
    return b, se, bool(np.any(np.abs(b) > 8))


def disegno(df):
    """Matrice del logit: riferimenti tecnico / bassa / M / ita / primo
    comune; eta' centrata sui 19 (il coefficiente e' per anno oltre il
    diploma «in corso»)."""
    cols, X = ["intercetta"], [np.ones(len(df))]
    for v, ref, livelli in (("diploma3", "tecnico",
                             ["liceo", "professionale"]),
                            ("gen3", "bassa", ["diploma", "laurea+"])):
        for l in livelli:
            cols.append(f"{v}={l}")
            X.append((df[v] == l).to_numpy(float))
    cols.append("sesso=F")
    X.append((df["sesso"] == "F").to_numpy(float))
    cols.append("straniero")
    X.append(df["straniero"].to_numpy(float))
    cols.append("eta-19")
    X.append((df["eta"] - 19).to_numpy(float))
    for c in sorted(df["comune"].unique())[1:]:
        cols.append(f"comune={c}")
        X.append((df["comune"] == c).to_numpy(float))
    return np.column_stack(X), cols


# ------------------------------------------------------------------- viste

def per_asse(df, univ, assi):
    out = []
    for asse in assi:
        for liv, g in df.groupby(asse):
            sit = g["situazione"].dropna()
            prb = g["prob"].dropna()
            out.append({"asse": asse, "livello": str(liv), "n": len(g),
                        "univ": (sit == univ).mean() if len(sit) else np.nan,
                        "prob": prb.mean() if len(prb) else np.nan})
    return pd.DataFrame(out)


def stampa(df, univ, agenti, percorsi, md_righe):
    P = md_righe.append
    modelli = sorted(df["modello"].unique())

    P("# Analisi campagne scelta post-diploma\n")
    P(f"batterie: {len(df)} · agenti: {df.uid.nunique()} · "
      f"modelli: {', '.join(modelli)}\n")

    # 1 --- pulizia
    P("## 1. Pulizia del parsing\n")
    pu = pulizia(percorsi)
    if not pu.empty:
        for _, r in pu.iterrows():
            P(f"- {r.modello} · {r['item']}: pulito {r.pulito:.1%}, "
              f"None {r['none']:.1%} (n {r.n})")
    P("")

    # 2 --- mutismo
    P("## 2. Distribuzione delle scelte (H4)\n")
    for m, g in df.groupby("modello"):
        c = Counter(g["situazione"].dropna())
        tot = sum(c.values())
        riga = "  ".join(f"{k}={v/tot:.1%}" for k, v in c.most_common())
        muto = " **<- possibile mutismo**" if c.most_common(1)[0][1] / tot > 0.95 else ""
        P(f"- {m}: {riga}{muto}")
    P("")

    # 3 --- stabilita' fra repliche (= rotazioni)
    P("## 3. Stabilita' fra repliche/rotazioni\n")
    for m, g in df.groupby("modello"):
        acc = g.groupby("uid")["situazione"].nunique()
        sd = g.groupby("uid")["prob"].std()
        P(f"- {m}: agenti con scelta identica su tutte le repliche "
          f"{(acc == 1).mean():.1%} · sd media della prob entro agente "
          f"{sd.mean():.2f}")
    P("\nLe repliche ruotano le opzioni: l'accordo copre insieme rumore "
      "e posizione.\n")

    # 4 --- ancore
    P("## 4. Ancore del continuo\n")
    for m, g in df.groupby("modello"):
        v = g["prob"].dropna().astype(int)
        if not len(v):
            continue
        top = Counter(v).most_common(6)
        P(f"- {m}: multipli di 10 {(v % 10 == 0).mean():.1%} · primi "
          "valori: " + ", ".join(f"{k} ({n/len(v):.0%})" for k, n in top))
    P("")

    # 5 --- assi
    P("## 5. Quota `" + univ + "` e prob media per asse\n")
    assi = ["diploma3", "gen3", "sesso", "straniero", "eta", "comune"]
    for m, g in df.groupby("modello"):
        P(f"\n### {m}\n")
        t = per_asse(g, univ, assi)
        for asse in assi:
            righe = t[t.asse == asse]
            P(f"- **{asse}**: " + "  ".join(
                f"{r.livello}: {r.univ:.1%}/{r.prob:.0f} (n{r.n})"
                for _, r in righe.iterrows()))
    P("\n(quota/prob; il segno di H1-H3 si legge qui, la stima nel §7)\n")

    # 6 --- qualifica
    P("## 6. La qualifica triennale (H5)\n")
    for m, g in df.groupby("modello"):
        for d3 in ("professionale", "tecnico"):
            gr = g[g.diploma3 == d3]
            a, b = gr[gr.qualifica], gr[~gr.qualifica]
            if len(a) and len(b):
                P(f"- {m} · {d3}: prob qualifica {a.prob.mean():.1f} "
                  f"(n{len(a)}) vs maturita' {b.prob.mean():.1f} "
                  f"(n{len(b)}) · univ {(a.situazione == univ).mean():.1%}"
                  f" vs {(b.situazione == univ).mean():.1%}")
            elif len(a):
                P(f"- {m} · {d3}: SOLO qualifiche (n{len(a)}, "
                  f"prob {a.prob.mean():.1f}) — riferimento reale ~0 "
                  "per non-accesso; confronto interno impossibile")
    P("\nSe le due colonne coincidono, il modello non distingue il "
      "non-accesso: H5 confermata.\n")

    # 7 --- logit
    P("## 7. Logit  P(scelta = universita')\n")
    for m, g in df.groupby("modello"):
        gg = g.dropna(subset=["situazione"])
        y = (gg["situazione"] == univ).to_numpy(float)
        if y.std() == 0:
            P(f"- {m}: nessuna variazione nella scelta — logit non "
              "stimabile (mutismo)")
            continue
        X, cols = disegno(gg)
        b, se, sep = logit_irls(X, y)
        P(f"\n### {m}" + ("  **[quasi-separazione: i beta oltre ~8 si "
                          "leggono come 'oltre soglia']**" if sep else ""))
        for c, bi, si in zip(cols, b, se):
            P(f"    {c:<22} beta {bi:+7.3f}  (se {si:.3f})")
    P("\nIl confronto con i coefficienti reali (MUR/AlmaDiploma, stessa "
      "specificazione) sta nella nota: i riferimenti vanno presi da "
      "fonte, non a memoria.\n")

    # 8 --- confronto fra modelli
    if len(modelli) > 1:
        P("## 8. Concordanza fra modelli\n")
        piv = (df.groupby(["modello", "uid"])["prob"].mean()
               .unstack(level=0))
        for i, m1 in enumerate(modelli):
            for m2 in modelli[i + 1:]:
                v = piv[[m1, m2]].dropna()
                r1 = v[m1].rank()
                r2 = v[m2].rank()
                rho = np.corrcoef(r1, r2)[0, 1]
                P(f"- rho Spearman prob per agente {m1} ~ {m2}: "
                  f"{rho:+.3f} (n {len(v)})")
        P("")


# ------------------------------------------------------------------ figure

def figure(df, univ, cartella):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(cartella, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 4))
    for m, g in df.groupby("modello"):
        v = g["prob"].dropna()
        ax.hist(v, bins=np.arange(-2.5, 103, 5), alpha=0.5, label=m)
    ax.set_xlabel("prob_universita (0-100)")
    ax.set_ylabel("risposte")
    ax.legend()
    ax.set_title("Il continuo e le sue ancore")
    fig.tight_layout()
    fig.savefig(os.path.join(cartella, "prob_ancore.png"), dpi=150)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    larg = 0.8 / df["modello"].nunique()
    for k, (m, g) in enumerate(df.groupby("modello")):
        q = (g.groupby(["diploma3", "gen3"])
             .apply(lambda x: (x["situazione"] == univ).mean()))
        etichette = [f"{d}\n{ge}" for d, ge in q.index]
        ax.bar(np.arange(len(q)) + k * larg, q.values, width=larg, label=m)
    ax.set_xticks(np.arange(len(q)) + 0.4 - larg / 2)
    ax.set_xticklabels(etichette, fontsize=7)
    ax.set_ylabel(f"quota `{univ}`")
    ax.set_title("diploma3 × gen3 — H1 e H2 a occhio")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(cartella, "quota_diploma_gen.png"), dpi=150)
    print(f"[figure in {cartella}]")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("campagne", nargs="+")
    ap.add_argument("--campione", default=None)
    ap.add_argument("--md", default=None)
    ap.add_argument("--png", default=None)
    a = ap.parse_args()

    percorsi = []
    for p in a.campagne:
        percorsi += glob.glob(p) if any(c in p for c in "*?[") else [p]
    percorsi = sorted(set(percorsi))
    df, univ, agenti = carica(percorsi, a.campione)

    righe = []
    stampa(df, univ, agenti, percorsi, righe)
    testo = "\n".join(righe)
    print(testo)
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(testo + "\n")
        print(f"[scritto {a.md}]")
    if a.png:
        figure(df, univ, a.png)


if __name__ == "__main__":
    main()
