#!/usr/bin/env python3
"""Collaudo di `gsp.nucleo` sulla popolazione sintetica.

Versione 2, 10 agosto 2026. Due modifiche:

  (1) LA METRICA SULLO STATO CIVILE ERA TROPPO DEBOLE. La v1 contava i
      «coniugati in un nucleo di 2+ senza nessun altro coniugato», e
      dava 8,9% su Parma. Ma quella condizione NON verifica che i
      coniugati siano accoppiati FRA LORO: un nucleo `RPF` con padre,
      madre e figlio tutti coniugati la soddisfa, e contiene un figlio
      sposato con nessuno. Nella misura precedente il 21,3% dei ruoli
      `F` era `coniugato_unito`.

      La condizione corretta e' PER COPPIA: ogni `coniugato_unito` deve
      stare in una coppia (R,P) in cui anche l'altro e' coniugato. Chi
      e' coniugato con ruolo F, G, A o N e' incoerente per definizione,
      a meno che non viva solo.

      Ci si aspetta un numero PEGGIORE dell'8,9%. E' quello vero.

  (2) PIU' COMUNI IN UN SOLO GIRO. Il repertorio e' emiliano-lombardo ma
      la sua CODA (ampiezze oltre 6) viene dai microdati di Parma:
      collaudarlo solo su Parma non dice nulla sulla trasferibilita'.


COSA MISURA

  (A) coerenza con `stato_civile`, per coppia e per ruolo;
  (B) fattibilita': nuclei senza ripiego, non collocati, casi dei vincoli;
  (C) plausibilita' dei divari.


DUE COSE DA RICORDARE LEGGENDO

  · `eta_anni` nella popolazione sintetica e' pescata UNIFORME nel bin:
    i divari ottenuti sono piu' dispersi di quelli reali, e il rumore
    sta nell'eta', non nell'assemblaggio.
  · `stato_civile` NON viene mai modificato: entra in `assembla` in sola
    lettura, e i vincoli MaxEnt restano soddisfatti. L'incoerenza
    residua non e' eliminabile per costruzione -- se una sezione ha un
    numero dispari di coniugati in nuclei plurimi, uno resta spaiato
    qualunque cosa faccia l'algoritmo. L'anello 4 RIVELA
    un'incoerenza gia' presente nella popolazione (il constraint set non
    impone che ci si sposi a due a due), non la crea.

    python scripts/diagnostica/collaudo_nucleo.py
    python scripts/diagnostica/collaudo_nucleo.py 034027 037006 017029
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


def gira(comune, seme, salva=None):
    pop_path = trova_popolazione(comune)
    if not pop_path:
        print(f"[{comune}] popolazione non trovata")
        return None
    rep = N.carica_repertorio(REP)
    sez = pd.read_csv(G.path_sezioni(comune))
    sez["k"] = sez.SEZ21_ID.astype("Int64").astype(str)
    per_sez = sez.set_index("k").to_dict("index")

    pop = pd.read_csv(pop_path, low_memory=False)
    pop["k"] = pop["sezione"].astype(str)
    usa_sc = N.STATO_COL in pop.columns

    rng = np.random.default_rng(seme)
    tot, casi, rip = Counter(), Counter(), Counter()
    div_g, div_p, pezzi = [], [], []
    tieni = ["uid", "sezione"] + ([N.STATO_COL] if usa_sc else [])

    for s, ind in pop.groupby("k", sort=False):
        riga = per_sez.get(s)
        if riga is None:
            tot["sez_non_agganciate"] += 1
            continue
        v, d = N.vincoli_da_sezione(riga, len(ind), rep, rng)
        res, dd = N.assembla(ind, v, rep, rng, prefisso=f"{s}-")
        pezzi.append(ind[tieni].join(res))
        tot["ind"] += len(ind)
        for k in ("nuclei", "perfetti", "non_collocati", "coppie",
                  "coppie_omogenee"):
            tot[k] += dd[k]
        tot["convivenza"] += d["convivenza"]
        casi[d["caso"]] += 1
        rip.update(dd["ripieghi"])
        div_g += dd["divari"].get("generazionale", [])
        div_p += dd["divari"].get("partner", [])

    r = pd.concat(pezzi)
    if salva:
        r[["uid", "id_nucleo", "ruolo"]].to_csv(salva, index=False)
    return dict(comune=comune, file=os.path.basename(pop_path), r=r,
                tot=tot, casi=casi, rip=rip, div_g=div_g, div_p=div_p,
                usa_sc=usa_sc, rep=rep)


def coerenza(r):
    """Metrica PER COPPIA: un coniugato e' coerente solo se sta in una
    coppia (R,P) in cui anche l'altro e' coniugato, oppure vive solo."""
    d = r[r.id_nucleo.notna()].copy()
    g = d.groupby("id_nucleo")
    d["amp"] = g["uid"].transform("size")

    # per ogni nucleo: lo stato civile di R e di P
    rp = d[d.ruolo.isin(["R", "P"])]
    pv = rp.pivot_table(index="id_nucleo", columns="ruolo",
                        values=N.STATO_COL, aggfunc="first")
    for c in ("R", "P"):
        if c not in pv.columns:
            pv[c] = np.nan
    coppia_con = ((pv.R == CONIUGATO) & (pv.P == CONIUGATO))
    d["in_coppia_con"] = d.id_nucleo.map(coppia_con).fillna(False)

    con = d[d[N.STATO_COL] == CONIUGATO]
    solo = con.amp == 1                                   # legittimo
    in_cop = con.ruolo.isin(["R", "P"]) & con.in_coppia_con
    inc = con[~solo & ~in_cop]

    # la colonna va calcolata PRIMA del groupby: pandas esclude la
    # chiave dalle colonne viste dalla lambda
    con = con.assign(coerente=(con.ruolo.isin(["R", "P"]) & con.in_coppia_con)
                              | (con.amp == 1))
    per_ruolo = con.groupby("ruolo").agg(n=("coerente", "size"),
                                         coerenti=("coerente", "sum"))
    per_ruolo["quota_inc"] = 1 - per_ruolo.coerenti / per_ruolo.n
    return dict(n_con=len(con), solo=int(solo.sum()), inc=len(inc),
                quota=len(inc) / max(len(con), 1), per_ruolo=per_ruolo,
                pv=pv.dropna(subset=["R", "P"]))


def stampa(e):
    r, tot, rep = e["r"], e["tot"], e["rep"]
    print("\n" + "=" * 72)
    print(f"{e['comune']} · {e['file']}")
    print("=" * 72)

    if e["usa_sc"]:
        c = coerenza(r)
        om = tot["coppie_omogenee"] / max(tot["coppie"], 1)
        print(f"A. stato civile")
        print(f"   coppie con lo stesso stato civile: {om:.1%}"
              f"  ({tot['coppie_omogenee']:,}/{tot['coppie']:,})"
              .replace(",", "."))
        print(f"   coniugati {c['n_con']:,}".replace(",", ".")
              + f" · in nuclei unipersonali {c['solo']/max(c['n_con'],1):.1%}"
                " (legittimo)")
        print(f"   INCOERENTI (metrica per coppia): {c['inc']:,} "
              f"({c['quota']:.1%})".replace(",", "."))
        print("   per ruolo del coniugato:")
        print("      " + c["per_ruolo"][["n", "quota_inc"]].round(3)
              .to_string().replace("\n", "\n      "))
        pv = c["pv"]
        if len(pv):
            print(f"   coppie (R,P) {len(pv):,}".replace(",", ".")
                  + " · combinazioni piu' frequenti:")
            top = pv.groupby(["R", "P"]).size().sort_values(ascending=False)
            for (a, b), n in top.head(5).items():
                print(f"      {a:20s} + {b:20s} {n:6,}".replace(",", "."))

    print(f"\nB. fattibilita'")
    print(f"   {tot['ind']:,} individui · {tot['nuclei']:,} nuclei"
          .replace(",", ".")
          + f" · senza ripiego {tot['perfetti']/max(tot['nuclei'],1):.1%}")
    print(f"   non collocati {tot['non_collocati']/max(tot['ind'],1):.2%}"
          f" · convivenza dichiarata {tot['convivenza']:,}".replace(",", "."))
    print(f"   casi vincoli: {dict(e['casi'])}")
    print("   ripieghi principali: "
          + ", ".join(f"{k} {v}" for k, v in e["rip"].most_common(5)))

    print(f"\nC. divari")
    if e["div_g"]:
        g = np.array(e["div_g"])
        print(f"   generazionale mediana {np.median(g):.0f} (AVQ 33) · "
              f"fuori limiti {np.mean((g < rep.gen_min) | (g > rep.gen_max)):.2%}")
    if e["div_p"]:
        p = np.array(e["div_p"])
        print(f"   partner mediana {np.median(p):+.0f} · "
              f"p05 {np.percentile(p, 5):+.0f} · p95 {np.percentile(p, 95):+.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comuni", nargs="*", default=["034027", "037006", "017029"])
    ap.add_argument("--seme", type=int, default=1)
    ap.add_argument("--out-dir")
    a = ap.parse_args()

    esiti = []
    for c in a.comuni:
        salva = (os.path.join(a.out_dir, f"nuclei_{c}.csv")
                 if a.out_dir else None)
        e = gira(c, a.seme, salva)
        if e:
            stampa(e)
            esiti.append(e)

    if len(esiti) > 1:
        print("\n" + "=" * 72)
        print("riepilogo — la trasferibilita' del repertorio")
        print("=" * 72)
        print(f"   {'comune':10s} {'omogenee':>9s} {'incoer.':>8s} "
              f"{'senza rip.':>11s} {'non coll.':>10s} {'div.gen':>8s}")
        for e in esiti:
            t, r = e["tot"], e["r"]
            om = t["coppie_omogenee"] / max(t["coppie"], 1)
            inc = coerenza(r)["quota"] if e["usa_sc"] else float("nan")
            g = np.median(e["div_g"]) if e["div_g"] else float("nan")
            print(f"   {e['comune']:10s} {om:8.1%} {inc:7.1%} "
                  f"{t['perfetti']/max(t['nuclei'],1):10.1%} "
                  f"{t['non_collocati']/max(t['ind'],1):9.2%} {g:8.0f}")
        print("\n   La CODA del repertorio (ampiezze oltre 6) viene dai")
        print("   microdati di PARMA: se Bologna e Brescia danno numeri")
        print("   simili, il repertorio e' trasferibile; se Parma e'")
        print("   sistematicamente migliore, la coda e' locale e va")
        print("   ricostruita per comune o dichiarata come limite.")


if __name__ == "__main__":
    main()
