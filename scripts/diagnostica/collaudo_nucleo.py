#!/usr/bin/env python3
"""Collaudo di `gsp.nucleo` sulla popolazione sintetica.

Sostituisce il giro ad hoc e `coerenza_stato_civile.py`, che era scritto
sulla vecchia firma di `assembla` (Series invece di DataFrame) e doveva
ricostruire il ruolo dalla posizione nel nucleo. Ora il ruolo e' nel
risultato.

Misura tre famiglie di cose, in ordine di importanza:

  (A) COERENZA CON `stato_civile`. E' il numero che nella v1 del modulo
      era rotto senza che nulla lo segnalasse: 21.431 coniugati (26,6%)
      in un nucleo di 2+ senza nessun altro coniugato, e un rapporto
      2*coppie_coniugate/coniugati con mediana 0,301 dove dovrebbe
      stare vicino a 1. Cioe' due coniugati su tre sposati con nessuno.

      Il 99,3% di «nuclei perfetti» della v1 non lo vedeva: contava solo
      i ripieghi su eta' e sesso, cioe' cio' che l'algoritmo ottimizza.

  (B) FATTIBILITA'. Nuclei senza alcun ripiego, individui non collocati,
      casi dei vincoli di sezione.

  (C) PLAUSIBILITA' DEI DIVARI. Generazionale contro il target AVQ (33),
      e quota fuori dai limiti [21, 45].


DUE COSE DA RICORDARE LEGGENDO

  · `eta_anni` nella popolazione sintetica e' pescata UNIFORME nel bin.
    I divari ottenuti sono quindi piu' dispersi di quelli reali, e il
    rumore sta nell'eta', non nell'assemblaggio.
  · il caso `sovrastima` dei vincoli (i vincoli chiedono piu' persone di
    quante ce ne siano) NON e' un difetto: l'anello 3 alloca per sezione
    con MAE 0,74-1,58, e uno scarto di un'unita' basta a invertire il
    segno del residuo. Su Parma capita in ~370 sezioni su 1.301.

    python scripts/diagnostica/collaudo_nucleo.py
    python scripts/diagnostica/collaudo_nucleo.py 037006 --out /tmp/nuclei.csv
"""

import argparse
import glob
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

import gsp.common as G
import gsp.nucleo as N

REP = "data/repertorio_nuclei_v1.json"
CONIUGATO = "coniugato_unito"


def trova_popolazione(comune):
    pat = f"data/comuni/{comune}/constraints_*/popolazione_K*_avq_full.csv"
    c = [p for p in sorted(glob.glob(pat)) if "backup" not in p]
    return c[-1] if c else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comune", nargs="?", default="034027")
    ap.add_argument("--seme", type=int, default=1)
    ap.add_argument("--out", help="salva uid, id_nucleo, ruolo")
    a = ap.parse_args()

    pop_path = trova_popolazione(a.comune)
    if not pop_path:
        sys.exit(f"popolazione non trovata per {a.comune}")
    rep = N.carica_repertorio(REP)
    sez = pd.read_csv(G.path_sezioni(a.comune))
    sez["k"] = sez.SEZ21_ID.astype("Int64").astype(str)
    pop = pd.read_csv(pop_path, low_memory=False)
    pop["k"] = pop["sezione"].astype(str)

    print(f"{os.path.basename(pop_path)} · {len(pop):,} individui · "
          f"{pop.k.nunique()} sezioni".replace(",", "."))
    usa_sc = N.STATO_COL in pop.columns
    if not usa_sc:
        print(f"   !! `{N.STATO_COL}` assente: il blocco (A) non si misura")

    rng = np.random.default_rng(a.seme)
    per_sez = dict(sez.set_index("k").to_dict("index"))
    tot = Counter()
    casi, rip = Counter(), Counter()
    div_g, div_p, pezzi = [], [], []

    for s, ind in pop.groupby("k", sort=False):
        riga = per_sez.get(s)
        if riga is None:
            tot["sezioni_non_agganciate"] += 1
            continue
        v, d = N.vincoli_da_sezione(riga, len(ind), rep, rng)
        res, dd = N.assembla(ind, v, rep, rng, prefisso=f"{s}-")
        pezzi.append(ind[["uid", "sezione"] +
                         ([N.STATO_COL] if usa_sc else [])].join(res))
        tot["ind"] += len(ind)
        tot["nuclei"] += dd["nuclei"]
        tot["perfetti"] += dd["perfetti"]
        tot["non_collocati"] += dd["non_collocati"]
        tot["coppie"] += dd["coppie"]
        tot["coppie_omogenee"] += dd["coppie_omogenee"]
        tot["convivenza"] += d["convivenza"]
        casi[d["caso"]] += 1
        rip.update(dd["ripieghi"])
        div_g += dd["divari"].get("generazionale", [])
        div_p += dd["divari"].get("partner", [])

    r = pd.concat(pezzi)
    r = r[r.id_nucleo.notna()]

    # ------------------------------------------------------------- (A)
    if usa_sc:
        print("\n" + "=" * 72)
        print("A. coerenza con `stato_civile`")
        print("=" * 72)
        om = tot["coppie_omogenee"] / max(tot["coppie"], 1)
        print(f"   coppie con lo stesso stato civile: "
              f"{tot['coppie_omogenee']:,}/{tot['coppie']:,} ({om:.1%})"
              .replace(",", ".") + "     [v1 del modulo: 51,0%]")

        g = r.groupby("id_nucleo")
        r = r.assign(amp=g["uid"].transform("size"),
                     n_con=g[N.STATO_COL].transform(
                         lambda s: (s == CONIUGATO).sum()))
        con = r[r[N.STATO_COL] == CONIUGATO]
        inc = con[(con.n_con < 2) & (con.amp > 1)]
        print(f"   coniugati: {len(con):,}".replace(",", "."))
        print(f"   INCOERENTI (in nucleo di 2+ senza altro coniugato): "
              f"{len(inc):,} ({len(inc)/max(len(con),1):.1%})"
              .replace(",", ".") + "   [v1: 26,6%]")
        print(f"   in nuclei unipersonali (legittimo): "
              f"{(con.amp == 1).mean():.1%}")

        cop = r[r.ruolo.isin(["R", "P"])]
        cop = cop[cop.groupby("id_nucleo")["ruolo"].transform(
            lambda s: set(s) == {"R", "P"})]
        pv = cop.pivot_table(index="id_nucleo", columns="ruolo",
                             values=N.STATO_COL, aggfunc="first").dropna()
        if len(pv):
            print(f"\n   coppie (R,P): {len(pv):,}".replace(",", ".")
                  + f" · entrambi coniugati "
                    f"{((pv.R == CONIUGATO) & (pv.P == CONIUGATO)).mean():.1%}"
                    "   [v1: 29,6%]")
            print("   combinazioni piu' frequenti:")
            print(pv.groupby(["R", "P"]).size()
                    .sort_values(ascending=False).head(6).to_string())

        ps = r.groupby("sezione").apply(lambda s: pd.Series({
            "con": (s[N.STATO_COL] == CONIUGATO).sum(),
            "cop": s[s.ruolo.isin(["R", "P"])].groupby("id_nucleo")[N.STATO_COL]
                    .apply(lambda x: (x == CONIUGATO).sum() == 2).sum()}))
        q = (ps.cop * 2 / ps.con.replace(0, np.nan)).dropna()
        print(f"\n   VINCOLO DI CONTEGGIO 2*coppie_coniugate/coniugati:")
        print(f"      mediana {q.median():.3f} · p25 {q.quantile(.25):.3f} · "
              f"p75 {q.quantile(.75):.3f}     [v1: mediana 0,301]")
        soli = float((con.amp == 1).mean())
        print(f"      TETTO TEORICO {1 - soli:.3f}: il {soli:.1%} dei "
              f"coniugati vive in nuclei unipersonali\n"
              f"      (coniugi non conviventi, legittimi) e non puo' "
              f"formare coppia.\n"
              f"      Siamo al {q.median()/(1-soli):.0%} del massimo possibile.")

    # ------------------------------------------------------------- (B)
    print("\n" + "=" * 72)
    print("B. fattibilita'")
    print("=" * 72)
    print(f"   {tot['ind']:,} individui · {tot['nuclei']:,} nuclei"
          .replace(",", "."))
    print(f"   nuclei senza alcun ripiego: "
          f"{tot['perfetti']/max(tot['nuclei'],1):.1%}")
    print(f"   non collocati {tot['non_collocati']:,}".replace(",", ".")
          + f" ({tot['non_collocati']/max(tot['ind'],1):.2%})"
          + f" · di cui convivenza dichiarata {tot['convivenza']:,}"
            .replace(",", "."))
    print(f"   casi dei vincoli: {dict(casi)}")
    print("   ripieghi:")
    for k, n in rip.most_common():
        print(f"      {k:34s} {n:6,}".replace(",", "."))

    # ------------------------------------------------------------- (C)
    print("\n" + "=" * 72)
    print("C. plausibilita' dei divari")
    print("=" * 72)
    if div_g:
        g = np.array(div_g)
        print(f"   generazionale: mediana {np.median(g):.0f} (AVQ 33) · "
              f"fuori [{rep.gen_min:.0f},{rep.gen_max:.0f}] "
              f"{np.mean((g < rep.gen_min) | (g > rep.gen_max)):.2%}")
    if div_p:
        p = np.array(div_p)
        print(f"   partner: mediana {np.median(p):+.0f} · "
              f"p05 {np.percentile(p, 5):+.0f} · p95 {np.percentile(p, 95):+.0f}"
              f"   (limite convenzionale ±{rep.conv['PARTNER_MAX_DIFF']})")

    if a.out:
        r[["uid", "id_nucleo", "ruolo"]].to_csv(a.out, index=False)
        print(f"\n   salvato: {a.out}")


if __name__ == "__main__":
    main()
