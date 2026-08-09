#!/usr/bin/env python3
"""Configurazioni interne dei nuclei — cosa vuol dire «compatibile».

Secondo mattone dell'anello 4. `avq_firme.py` ha stabilito QUALI
configurazioni esistono (le firme: `R`, `RP`, `RPF`, `RPFF`... 90% dei
nuclei in sei firme). Questo script stabilisce CHI CI STA DENTRO: quanti
anni ha il partner rispetto al riferimento, quanto separa genitore e
figlio, se il riferimento e' piu' spesso maschio, se la cittadinanza si
condivide.

Senza queste distribuzioni l'assemblaggio produrrebbe `RPFF` con il
figlio di sessant'anni e il padre di trenta.


A COSA SERVE, ESATTAMENTE

L'anello 4 NON tocca la popolazione sintetica: aggiunge una colonna
`id_nucleo` e basta. Gli individui restano quelli vincolati dall'anello 1
e allocati per sezione dall'anello 3. Il repertorio AVQ serve quindi a
dire QUALI CONFIGURAZIONI SONO PLAUSIBILI, non a fornire persone --
donare il nucleo AVQ intero significherebbe sostituire individui
vincolati con componenti campionari, e distruggerebbe l'anello 1.

Le distribuzioni misurate qui diventano il criterio di compatibilita' con
cui gli slot di una firma (`RPFF` = un riferimento, un partner, due figli)
si riempiono con gli individui della sezione.


LE CLASSI D'ETA' SONO IRREGOLARI

`ETAMi` ha quindici classi da 3 a 10 anni, l'ultima aperta
(METADATI/Classificazioni/..._var6.html). Le differenze fra CODICI non
sono differenze in anni: dalla 003 alla 004 sono cinque anni, dalla 009
alla 010 sono dieci. I divari si calcolano quindi sui CENTRI di classe.

La classe 15 e' aperta («75 e piu'») e il suo centro e' una convenzione,
non una misura: i divari che la coinvolgono sono marcati e vanno letti
con quella riserva. Sono pochi, ma stanno proprio dove servirebbero --
nuclei con anziani conviventi.


COSA MISURA

  (1) il RIFERIMENTO: sesso ed eta' per firma. Chi viene designato
      persona di riferimento non e' neutro rispetto al genere.
  (2) il PARTNER: divario d'eta' col riferimento, con segno, e quota di
      coppie dello stesso sesso.
  (3) i FIGLI: divario col riferimento (proxy del divario generazionale)
      e divario fra fratelli.
  (4) i GENITORI conviventi: divario col riferimento, in negativo.
  (5) la CITTADINANZA: quanto e' omogenea dentro il nucleo. Serve a
      decidere se l'assemblaggio debba trattarla come vincolo forte --
      e ha un precedente: rho ~ 0,6 per la fiducia istituzionale (v22
      §13.5), cioe' in famiglia si condividono le opinioni.

    python scripts/diagnostica/avq_configurazioni.py
    python scripts/diagnostica/avq_configurazioni.py --regioni 80 30
"""

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

ANNI = (2022, 2023, 2024)
PAT = "data/avq/anni/avq{a}/MICRODATI/AVQ_Microdati_{a}.txt"

MAPPA = {1: "R", 2: "P", 3: "P", 4: "G", 5: "G", 6: "F", 7: "F",
         **{k: "A" for k in range(8, 17)}, 17: "N"}
ORDINE = {"R": 0, "P": 1, "F": 2, "G": 3, "A": 4, "N": 5}

ETAMI = {1: "0-2", 2: "3-5", 3: "6-10", 4: "11-13", 5: "14-15", 6: "16-17",
         7: "18-19", 8: "20-24", 9: "25-34", 10: "35-44", 11: "45-54",
         12: "55-59", 13: "60-64", 14: "65-74", 15: "75+"}
CENTRO = {1: 1, 2: 4, 3: 8, 4: 12, 5: 14.5, 6: 16.5, 7: 18.5, 8: 22,
          9: 29.5, 10: 39.5, 11: 49.5, 12: 57, 13: 62, 14: 69.5, 15: 82}
APERTA = 15


def percorso(anno):
    p = PAT.format(a=anno)
    if os.path.exists(p):
        return p
    g = glob.glob(f"data/avq/**/*Microdati_{anno}*.txt", recursive=True)
    return g[0] if g else None


def carica(regioni):
    keep = {"PROFAM", "NCOMP", "RELPAR", "ETAMi", "SESSO", "CITTMi",
            "REGMf", "COEFIN"}
    pezzi = []
    for anno in ANNI:
        p = percorso(anno)
        if not p:
            continue
        d = pd.read_csv(p, sep="\t", low_memory=False,
                        usecols=lambda c: c in keep)
        d["ANNO"] = anno
        pezzi.append(d)
    if not pezzi:
        sys.exit("microdati AVQ non trovati")
    d = pd.concat(pezzi, ignore_index=True)
    for c in ("REGMf", "RELPAR", "ETAMi", "COEFIN", "CITTMi", "SESSO"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["COEFIN"] = d["COEFIN"] / 10000.0
    d = d[d.REGMf.isin(regioni)].copy()
    d["nucleo"] = d["ANNO"].astype(str) + "|" + d["PROFAM"].astype(str)
    d["ruolo"] = d["RELPAR"].map(MAPPA)
    d["eta_c"] = d["ETAMi"].map(CENTRO)
    d["aperta"] = d["ETAMi"] == APERTA
    return d


def firma(g):
    v = sorted(g["ruolo"].dropna(), key=lambda x: ORDINE.get(x, 9))
    return "".join(v)


def riepilogo(v, w, et, apert=None):
    """Quantili pesati di una distribuzione di divari."""
    if not len(v):
        print(f"   {et:28s} nessun caso")
        return
    v = np.asarray(v, float)
    w = np.asarray(w, float)
    o = np.argsort(v)
    cum = np.cumsum(w[o]) / w.sum()
    q = {p: float(v[o][np.searchsorted(cum, p)])
         for p in (0.05, 0.25, 0.50, 0.75, 0.95)}
    nota = ""
    if apert is not None and len(v):
        f = float(np.mean(apert))
        if f > 0.02:
            nota = f"   [{f:.0%} tocca la classe aperta]"
    print(f"   {et:28s} n={len(v):5d}  p05 {q[0.05]:+6.1f}  "
          f"p25 {q[0.25]:+6.1f}  MEDIANA {q[0.50]:+6.1f}  "
          f"p75 {q[0.75]:+6.1f}  p95 {q[0.95]:+6.1f}{nota}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regioni", type=int, nargs="+", default=[80, 30])
    a = ap.parse_args()

    d = carica(a.regioni)
    g = d.groupby("nucleo")
    firme = g.apply(firma)
    amp = g.size()
    peso = g["COEFIN"].first()
    d = d.merge(firme.rename("f_op"), left_on="nucleo", right_index=True)
    print(f"pool: {len(d):,} componenti in {len(firme):,} nuclei"
          .replace(",", "."))

    rif = d[d.ruolo == "R"].set_index("nucleo")

    # ---------------------------------------------------- (1) riferimento
    print("\n" + "=" * 72)
    print("1. chi e' la persona di riferimento")
    print("=" * 72)
    for f in ("R", "RP", "RF", "RPF", "RPFF"):
        s = rif[rif.f_op == f]
        if len(s) < 20:
            continue
        w = s["COEFIN"]
        qm = float(np.average((s.SESSO == 1).to_numpy(float), weights=w))
        o = np.argsort(s.eta_c.to_numpy())
        cum = np.cumsum(w.to_numpy()[o]) / w.sum()
        med = float(s.eta_c.to_numpy()[o][np.searchsorted(cum, 0.5)])
        print(f"   firma {f:6s} n={len(s):5d}  quota maschi {qm:.3f}  "
              f"eta' mediana ~{med:.0f}")
    print("\n   Nelle coppie il riferimento e' designato, non neutro: la")
    print("   quota di maschi va riprodotta, altrimenti l'assemblaggio")
    print("   sbilancia il genere del capofamiglia sintetico.")

    # ---------------------------------------------------- (2) partner
    print("\n" + "=" * 72)
    print("2. partner — divario d'eta' col riferimento (partner − rif)")
    print("=" * 72)
    par = d[d.ruolo == "P"].merge(
        rif[["eta_c", "SESSO", "aperta", "CITTMi"]].add_suffix("_r"),
        left_on="nucleo", right_index=True)
    dv = par.eta_c - par.eta_c_r
    ap_fl = (par.aperta | par.aperta_r).to_numpy()
    riepilogo(dv.to_numpy(), par.COEFIN.to_numpy(), "tutti i partner", ap_fl)
    for cod, et in ((2, "02 coniuge"), (3, "03 convivente")):
        s = par[par.RELPAR == cod]
        if len(s) > 20:
            riepilogo((s.eta_c - s.eta_c_r).to_numpy(), s.COEFIN.to_numpy(),
                      et, (s.aperta | s.aperta_r).to_numpy())
    ss = float(np.average((par.SESSO == par.SESSO_r).to_numpy(float),
                          weights=par.COEFIN))
    print(f"\n   coppie dello stesso sesso: {ss:.3f}")

    # ---------------------------------------------------- (3) figli
    print("\n" + "=" * 72)
    print("3. figli — divario col riferimento (rif − figlio) e fra fratelli")
    print("=" * 72)
    fig = d[d.ruolo == "F"].merge(
        rif[["eta_c", "aperta", "CITTMi"]].add_suffix("_r"),
        left_on="nucleo", right_index=True)
    riepilogo((fig.eta_c_r - fig.eta_c).to_numpy(), fig.COEFIN.to_numpy(),
              "divario generazionale", (fig.aperta | fig.aperta_r).to_numpy())

    frat = []
    for _, s in fig.groupby("nucleo"):
        if len(s) < 2:
            continue
        e = np.sort(s.eta_c.to_numpy())
        frat += [(e[i + 1] - e[i], s.COEFIN.iloc[0]) for i in range(len(e) - 1)]
    if frat:
        riepilogo([x[0] for x in frat], [x[1] for x in frat],
                  "fra fratelli consecutivi")
    print("\n   Il divario generazionale e' il vincolo piu' stringente")
    print("   dell'assemblaggio: definisce quali individui della sezione")
    print("   possono riempire uno slot 'figlio' dato il riferimento.")

    # ---------------------------------------------------- (4) genitori
    print("\n" + "=" * 72)
    print("4. genitori conviventi — divario col riferimento (gen − rif)")
    print("=" * 72)
    gen = d[d.ruolo == "G"].merge(
        rif[["eta_c", "aperta"]].add_suffix("_r"),
        left_on="nucleo", right_index=True)
    if len(gen):
        riepilogo((gen.eta_c - gen.eta_c_r).to_numpy(), gen.COEFIN.to_numpy(),
                  "genitore − riferimento", (gen.aperta | gen.aperta_r).to_numpy())

    # ---------------------------------------------------- (5) cittadinanza
    print("\n" + "=" * 72)
    print("5. omogeneita' della cittadinanza dentro il nucleo")
    print("=" * 72)
    noto = d[d.CITTMi.isin([1, 3])]
    per_n = noto.groupby("nucleo")["CITTMi"].agg(["nunique", "size", "first"])
    multi = per_n[per_n["size"] > 1]
    if len(multi):
        om = float((multi["nunique"] == 1).mean())
        print(f"   nuclei con 2+ componenti a cittadinanza nota: {len(multi):,}"
              .replace(",", "."))
        print(f"   omogenei: {om:.3f}")
        # solo nuclei con almeno uno straniero
        conste = noto[noto.CITTMi == 3].nucleo.unique()
        m2 = multi[multi.index.isin(conste)]
        if len(m2):
            print(f"   fra i nuclei con almeno uno straniero ({len(m2):,}): "
                  .replace(",", ".") + f"omogenei {float((m2['nunique'] == 1).mean()):.3f}")
    print("\n   Se l'omogeneita' e' alta, la cittadinanza va trattata come")
    print("   vincolo dell'assemblaggio e non come esito. Precedente: rho")
    print("   ~0,6 per la fiducia istituzionale (v22 §13.5) — in famiglia")
    print("   si condividono anche le opinioni.")


if __name__ == "__main__":
    main()
