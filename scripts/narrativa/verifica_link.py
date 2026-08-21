#!/usr/bin/env python3
"""verifica_link.py — la link function fuori dalla classe che l'ha stimata.

    python scripts/narrativa/verifica_link.py
    python scripts/narrativa/verifica_link.py --md note/verifica_link.md

Fase 2 ha stimato quota = sigma(a + b*logit(credenza)) su 12 celle dei
TECNICI (quota a T=1,0). Qui la stessa forma si stima sulle 36 celle a
T=0,3 — liceo e professionale COMPRESI, mai usati nella stima — per
decidere se (a, b) e' una proprieta' del modello o dei tecnici.

PREDIZIONI, registrate prima dei numeri:

  L1  b(T=0,3) > b(T=1,0) per ciascun modello: piu' freddo = piu'
      ripido. E' la controprova di P1 letta al contrario.
  L2  l'ordinamento dei bias si conserva: a(Haiku) < a(DeepSeek) —
      il pessimista resta pessimista fuori classe.
  L3  R² nella fascia della fase 2 (~0,6-0,9) per Haiku e DeepSeek:
      canali accoppiati anche dove la credenza e' estrema.
  GPT resta dichiarato non identificabile (credenza in 0,66-0,75);
      si stampa per completezza, non si interpreta.

TRAPPOLA DICHIARATA — il clipping. Liceo e professionale sono saturi
(quote 0 o 1 in molte celle): il logit vive nell'epsilon di clip, e la
b stimata ne dipende. Difesa: la stima e' riportata a DUE epsilon
(0,02 e 0,05) e il verdetto su L1 vale solo se regge a entrambi;
la quota satura e' essa stessa un dato (b grande comunque), ma il suo
VALORE numerico non va citato senza l'epsilon accanto.

GPT: la quota T=0,3 e' calcolata su r0+r2 (primacy, v. nota risultati
§7); DeepSeek e Haiku su tutte le repliche.

Riferimenti fase 2 (12 celle tecnici, quota T=1,0, eps 0,02):
  Haiku (-1,28; 3,04; R² 0,88) · DeepSeek (+0,68; 1,67; 0,61) ·
  GPT n.i.
"""

import argparse
import glob
import json
import os

import numpy as np
import pandas as pd

UNIV = "università"

FASE2 = {"claude-haiku-4.5": (-1.28, 3.04, 0.88),
         "deepseek-chat": (0.68, 1.67, 0.61),
         "gpt-4o-mini": (None, None, 0.38)}


def lgt(v, eps):
    v = np.clip(np.asarray(v, dtype=float), eps, 1 - eps)
    return np.log(v / (1 - v))


def stima(x, y, eps):
    A = np.column_stack([np.ones(len(x)), lgt(x, eps)])
    b, *_ = np.linalg.lstsq(A, lgt(y, eps), rcond=None)
    yh = A @ b
    ly = lgt(y, eps)
    r2 = 1 - np.sum((ly - yh) ** 2) / np.sum((ly - ly.mean()) ** 2)
    return float(b[0]), float(b[1]), float(r2)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default="dati/campagne/scelta")
    ap.add_argument("--md", default=None)
    a = ap.parse_args()

    L = []
    P = L.append
    P("# Verifica fuori-campione della link function — 36 celle, T=0,3\n")
    P("Predizioni L1-L3 e trappola del clipping: docstring dello "
      "script.\n")

    verdetti = {}
    for p in sorted(glob.glob(os.path.join(a.dir, "*_r3_t03.json"))):
        if "_tecnico_" in p:
            continue
        d = json.load(open(p, encoding="utf-8"))
        mod = d["modello"].split("/")[-1]
        s = pd.DataFrame(d["survey"])

        sit = s[s["item"] == "situazione"].dropna(subset=["valore"])
        if mod == "gpt-4o-mini":
            sit = sit[sit["replica"].astype(int).isin([0, 2])]
        prb = (s[s["item"] == "prob_universita"].dropna(subset=["valore"])
               .assign(valore=lambda x: pd.to_numeric(x["valore"])))

        cred = prb.groupby("cella")["valore"].mean() / 100
        quo = sit.groupby("cella")["valore"].apply(
            lambda v: (v == UNIV).mean())
        idx = cred.index.intersection(quo.index)
        x = cred[idx].to_numpy(dtype=float)
        y = quo[idx].to_numpy(dtype=float)

        P(f"\n## {mod}  (celle: {len(idx)}; quota "
          + ("r0+r2 per il primacy" if mod == "gpt-4o-mini"
             else "tutte le repliche") + ")\n")
        sature = int(((y <= 0.001) | (y >= 0.999)).sum())
        P(f"- celle sature (quota 0 o 1): {sature}/{len(idx)} — il "
          "clipping lavora li'")
        righe = {}
        for eps in (0.02, 0.05):
            a_, b_, r2 = stima(x, y, eps)
            righe[eps] = (a_, b_, r2)
            P(f"- eps {eps}:  a {a_:+.2f}  b {b_:.2f}  R² {r2:.2f}")
        f2 = FASE2.get(mod, (None, None, None))
        if f2[1] is not None:
            ok_l1 = all(righe[e][1] > f2[1] for e in righe)
            verdetti[(mod, "L1")] = ok_l1
            P(f"- fase 2 (tecnici, T=1,0): a {f2[0]:+.2f}  b {f2[1]:.2f}"
              f"  R² {f2[2]:.2f}  ->  L1 (b piu' ripida al freddo): "
              + ("regge a entrambi gli eps" if ok_l1 else "**NO**"))
            verdetti[(mod, "L3")] = all(r[2] >= 0.55 for r in righe.values())
        else:
            P("- fase 2: non identificabile; qui si stampa e non si "
              "interpreta")
        verdetti[(mod, "_a")] = righe[0.02][0]

    # L2: ordinamento dei bias
    ah = verdetti.get(("claude-haiku-4.5", "_a"))
    ad = verdetti.get(("deepseek-chat", "_a"))
    P("\n## Verdetti\n")
    if ah is not None and ad is not None:
        ok_l2 = ah < ad
        P(f"- L2 (a_Haiku < a_DeepSeek): {ah:+.2f} vs {ad:+.2f} -> "
          + ("regge" if ok_l2 else "**NO**"))
    for (mod, ll), ok in sorted(verdetti.items()):
        if ll.startswith("_"):
            continue
        P(f"- {mod} · {ll}: {'regge' if ok else 'NO'}")
    P("\nSe L1-L3 reggono, (a,b) e' del MODELLO — con b funzione della "
      "temperatura — e la link function e' promossa da descrizione dei "
      "tecnici a proprieta' dello strumento. Se cadono, era locale, e "
      "la nota lo dice.")

    testo = "\n".join(L)
    print(testo)
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(testo + "\n")
        print(f"\n[scritto {a.md}]")


if __name__ == "__main__":
    main()
