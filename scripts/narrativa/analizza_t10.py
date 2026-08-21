#!/usr/bin/env python3
"""analizza_t10.py — il test della scomposizione credenza/argmax (P1-P3).

    python scripts/narrativa/analizza_t10.py
    python scripts/narrativa/analizza_t10.py --dir dati/campagne/scelta --md note/analisi_t10.md

Confronta, PER I SOLI TECNICI (la classe viva), le campagne T=0,3 r3 con
le corse T=1,0 r4 a ciclo completo di rotazioni. Le predizioni sono
registrate in nota_risultati_scelta_v1 §8 e nei file di campagna T=1,0:

  P1  a T=1,0 la quota categoriale migra dalle soglie verso le credenze
      dichiarate a T=0,3.
      CRITERIO: |quota_T10 − credenza| < |quota_T03 − credenza|,
      per modello.
  P2  il primacy di GPT persiste a T alta (strutturale).
      CRITERIO: a T=1,0, quota della prima posizione >> 1/4 per GPT, e
      ITS quando primo >> ITS altrove. Il ciclo r0-r3 e' completo:
      OGNI opzione e' prima esattamente una volta — la preferenza di
      posizione e' finalmente misurata bilanciata.
  P3  (se P1) le quote T=1,0 per cella coincidono con le prob medie
      T=0,3 entro la risoluzione delle ancore.
      CRITERIO: scarto assoluto medio per cella ≤ ~10 punti.

In piu', i numeri di contorno che decidono quanto credere ai verdetti:
parsing a T alta, dispersione delle prob entro agente (deve salire se
il campionamento e' vero), stabilita' della scelta (deve SCENDERE se P1
e' vera: l'instabilita' a T=1,0 non e' rumore, e' il meccanismo).
"""

import argparse
import glob
import json
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

SCELTE = ["università", "ITS o altra formazione",
          "lavoro o ricerca di un lavoro", "altro"]
UNIV = SCELTE[0]


def carica_survey(percorso, solo_uid=None):
    with open(percorso, encoding="utf-8") as f:
        d = json.load(f)
    s = pd.DataFrame(d["survey"])
    if solo_uid is not None:
        s = s[s["agent_id"].isin(solo_uid)]
    s["modello"] = d["modello"].split("/")[-1]
    return s, d


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default="dati/campagne/scelta")
    ap.add_argument("--campione",
                    default="dati/agenti/agenti_scelta_n432_s0.json")
    ap.add_argument("--md", default=None)
    a = ap.parse_args()

    with open(a.campione, encoding="utf-8") as f:
        agenti = {x["uid"]: x for x in json.load(f)["agenti"]}
    tecnici = {u for u, x in agenti.items() if x["diploma3"] == "tecnico"}

    f10 = sorted(glob.glob(os.path.join(a.dir, "*_tecnico_*_r4_t10.json")))
    f03 = sorted(p for p in glob.glob(os.path.join(a.dir, "*_r3_t03.json"))
                 if "_tecnico_" not in p)
    if not f10 or not f03:
        sys.exit(f"file mancanti: t10={len(f10)}, t03={len(f03)}")

    L = []
    P = L.append
    P("# Confronto T=0,3 vs T=1,0 — soli tecnici (P1-P3)\n")

    verdetti = {}
    for p10 in f10:
        s10, d10 = carica_survey(p10)
        mod = s10["modello"].iloc[0]
        p03 = [p for p in f03 if mod.replace(".", "") in
               os.path.basename(p).replace(".", "")]
        if not p03:
            P(f"**{mod}: campagna T=0,3 non trovata, salto**")
            continue
        s03, _ = carica_survey(p03[0], solo_uid=tecnici)

        sit10 = s10[s10["item"] == "situazione"].dropna(subset=["valore"])
        prb10 = s10[s10["item"] == "prob_universita"].dropna(subset=["valore"])
        sit03 = s03[s03["item"] == "situazione"].dropna(subset=["valore"])
        prb03 = s03[s03["item"] == "prob_universita"].dropna(subset=["valore"])

        P(f"\n## {mod}\n")

        # ------- contorno: parsing e dispersione
        with open(p10, encoding="utf-8") as f:
            raw = json.load(f)
        sv = pd.DataFrame(raw["survey"])
        P(f"- parsing T=1,0: pulito "
          f"{sv.groupby('item')['pulito'].mean().round(3).to_dict()} · "
          f"None {sv['valore'].isna().mean():.1%}")
        sd10 = prb10.groupby("agent_id")["valore"].std().mean()
        sd03 = prb03.groupby("agent_id")["valore"].std().mean()
        st10 = (sit10.groupby("agent_id")["valore"].nunique() == 1).mean()
        st03 = (sit03.groupby("agent_id")["valore"].nunique() == 1).mean()
        P(f"- dispersione prob entro agente: {sd03:.2f} (T03) -> "
          f"{sd10:.2f} (T10) · scelta identica su tutte le repliche: "
          f"{st03:.1%} -> {st10:.1%}")

        # ------- P1: quota vs credenza
        credenza = prb03.groupby("agent_id")["valore"].mean().mean() / 100
        q03 = (sit03["valore"] == UNIV).mean()
        q10 = (sit10["valore"] == UNIV).mean()
        d03, d10 = abs(q03 - credenza), abs(q10 - credenza)
        ok1 = d10 < d03
        verdetti[(mod, "P1")] = ok1
        P(f"- **P1**: credenza (prob media T03) {credenza:.1%} · quota "
          f"T03 {q03:.1%} (scarto {d03:.1%}) · quota T10 {q10:.1%} "
          f"(scarto {d10:.1%}) -> "
          + ("**MIGRA** (P1 regge)" if ok1 else "**non migra** (P1 no)"))

        # ------- P2: posizione a ciclo completo
        pos = sit10.apply(
            lambda r: (SCELTE[int(r["replica"]) % 4:]
                       + SCELTE[:int(r["replica"]) % 4]
                       ).index(r["valore"]), axis=1)
        qpos = pos.value_counts(normalize=True).sort_index()
        P("- **P2** posizione presentata (ciclo completo, attesa 25% se "
          "indifferente): "
          + "  ".join(f"p{k}={v:.1%}" for k, v in qpos.items()))
        its = sit10.assign(
            primo=lambda x: x["replica"].astype(int) % 4 == 1)
        qi = its.groupby("primo")["valore"].apply(
            lambda v: (v == "ITS o altra formazione").mean())
        P(f"  ITS quando primo {qi.get(True, 0):.1%} vs altrove "
          f"{qi.get(False, 0):.1%}")
        verdetti[(mod, "P2")] = qpos.get(0, 0) > 0.40  # soglia dichiarata

        # ------- P3: per cella, quota T10 vs prob media T03
        cel10 = sit10.groupby("cella")["valore"].apply(
            lambda v: (v == UNIV).mean())
        celp = prb03.groupby("cella")["valore"].mean() / 100
        comuni_ = cel10.index.intersection(celp.index)
        gap = (cel10[comuni_] - celp[comuni_]).abs()
        ok3 = gap.mean() <= 0.10
        verdetti[(mod, "P3")] = ok3
        P(f"- **P3** per cella (n={len(comuni_)}): scarto medio "
          f"{gap.mean():.1%}, max {gap.max():.1%} "
          f"({gap.idxmax()}) -> "
          + ("entro le ancore (P3 regge)" if ok3 else "oltre (P3 no)"))
        peggio = (cel10[comuni_] - celp[comuni_]).sort_values()
        P("  celle estreme: "
          + " · ".join(f"{k}: quota {cel10[k]:.0%} vs cred {celp[k]:.0%}"
                       for k in [peggio.index[0], peggio.index[-1]]))

    # ------- il quadro
    P("\n## Verdetti\n")
    for (mod, pp), ok in sorted(verdetti.items()):
        P(f"- {mod} · {pp}: {'regge' if ok else 'NO'}")
    P("\nLettura d'insieme: P1 vera per tutti = la scomposizione "
      "credenza/argmax e' dimostrata; P1 vera solo per alcuni = la "
      "regola di decisione e' essa stessa idiosincratica anche nella "
      "sua sensibilita' alla temperatura — che sarebbe il finding.")

    testo = "\n".join(L)
    print(testo)
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(testo + "\n")
        print(f"\n[scritto {a.md}]")


if __name__ == "__main__":
    main()
