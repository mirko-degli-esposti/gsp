#!/usr/bin/env python3
"""Che cos'e' il codice 11 dei microdati di Parma?

Versione 2, 9 agosto 2026: `ETAMi` decodificato. La v1 trattava i codici
come anni e stampava scarti d'eta' di -28: privi di significato. `ETAMi`
e' CATEGORICA («ricostruita», posizione 6 del tracciato), quindici classi
IRREGOLARI da 3 a 10 anni con l'ultima aperta. I codici sono pero'
monotoni nell'eta', quindi la mediana pesata del codice E' la classe
mediana: i numeri erano validi, la lettura no.


LA QUESTIONE

Il codice 11 vale 14.725 persone, il 7,4% dei residenti in famiglia,
eta' mediana 38, stranieri al 52% contro il 15% degli intestatari. Il
codebook della fornitura e' refutato (dice «Zio/Zia», impossibile per
eta'), quindi la classe va inferita. Tre letture si sono succedute:

  (1) «coabitazione / non parente», dal profilo demografico;
  (2) «convivente more uxorio», da un confronto di RAPPORTI (nell'AVQ i
      conviventi sono il 18% dei coniugi, a Parma il codice 11 e' il 44%);
  (3) CATEGORIA RESIDUA LARGA -- tutto cio' che non e' riferimento,
      partner, figlio, genitore.

Il confronto per RAPPORTI di (2) e' fragile: dipende da quanti coniugi
ci sono. Il test pulito e' la quota sul TOTALE dei componenti.


IL TEST, E COSA HA DATO

    criterio            esito
    eta'                compatibile con TUTTI i candidati: 03, 17 e ogni
                        miscela hanno mediana nella classe 010 (35-44),
                        che contiene i 38 anni di Parma. NON DISCRIMINA.
    quota sui           solo la miscela larga si avvicina:
    componenti            03 solo         3,8%   contro 7,4%
                          17 solo         0,6%
                          03+17           4,4%
                          03+17+08-16     6,4%   <- scarto -1,0 punti
                        e lo scarto e' nella direzione attesa, perche'
                        una citta' ha piu' conviventi della sua regione.
    cittadinanza        NESSUN candidato arriva al 52%: il massimo e' il
                        37% del solo 17, la miscela sta al 20%.

Conclusione: **categoria residua larga**, compatibile per quota ed eta'.
**La quota straniera al 52% resta non spiegata** e va registrata come
anomalia aperta, non risolta a forza.

Ipotesi non verificata sull'anomalia: le convivenze migranti sono cio'
che l'AVQ cattura peggio -- autoselezione linguistica (v22 §8), e
un'indagine su famiglie anagrafiche fatica a intercettare coabitazioni
instabili. Se fosse cosi', il 52% di Parma sarebbe il dato buono e il 20%
dell'AVQ quello distorto, il che renderebbe l'AVQ un repertorio
inadeguato proprio per la tipologia di nucleo piu' difficile da
assemblare. Limite da registrare.


VALIDAZIONE ESTERNA OTTENUTA PER STRADA

Le classi d'eta' AVQ decodificate coincidono con le eta' mediane di Parma
su tutte le classi identificate per via aritmetica in
`nota_nucleo_familiare` §2.3:

    riferimento   AVQ 012 (55-59)   Parma 55
    coniuge       AVQ 012 (55-59)   Parma 57
    figlio        AVQ 006 (16-17)   Parma 16

Due fonti indipendenti, universi e anni diversi, profili coincidenti.


CAUTELE

  · l'AVQ e' regionale, Parma comunale: le quote di Parma sono attese
    PIU' ALTE anche a parita' di classe;
  · anni diversi (AVQ 2022-2024, Parma 2025);
  · ~430 non italiani nel pool emiliano: le celle di 03 e 17 incrociate
    con la cittadinanza sono sottili;
  · il campione AVQ di stranieri e' autoselezionato sulla lingua.

Il test puo' ESCLUDERE una lettura, non confermarne una.

    python scripts/diagnostica/parma_codice11.py
"""

import glob
import os
import sys

import numpy as np
import pandas as pd

ANNI = (2022, 2023, 2024)
PAT = "data/avq/anni/avq{a}/MICRODATI/AVQ_Microdati_{a}.txt"

# ETAMi, da METADATI/Classificazioni/AVQ_Classificazione_2024_var6.html
ETAMI = {1: "0-2", 2: "3-5", 3: "6-10", 4: "11-13", 5: "14-15", 6: "16-17",
         7: "18-19", 8: "20-24", 9: "25-34", 10: "35-44", 11: "45-54",
         12: "55-59", 13: "60-64", 14: "65-74", 15: "75+"}
# centro della classe, per un confronto numerico con Parma (la 15 e'
# aperta: 82 e' una convenzione, non una misura)
CENTRO = {1: 1, 2: 4, 3: 8, 4: 12, 5: 14.5, 6: 16.5, 7: 18.5, 8: 22,
          9: 29.5, 10: 39.5, 11: 49.5, 12: 57, 13: 62, 14: 69.5, 15: 82}

BERSAGLIO = {"eta": 38.0, "str": 0.52, "quota": 0.074}

ETICHETTE = {1: "persona di riferimento", 2: "coniuge di PR",
             3: "convivente coniugalmente di PR", 6: "figlio (ultima unione)",
             17: "persona legata da amicizia"}


def percorso(anno):
    p = PAT.format(a=anno)
    if os.path.exists(p):
        return p
    g = glob.glob(f"data/avq/**/*Microdati_{anno}*.txt", recursive=True)
    return g[0] if g else None


def carica_avq(regione=80):
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
    for c in ("REGMf", "RELPAR", "ETAMi", "COEFIN", "CITTMi"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["COEFIN"] = d["COEFIN"] / 10000.0
    return d[d.REGMf == regione].copy()


def profilo(d, mask, etichetta, tot):
    s = d[mask]
    if not len(s):
        print(f"   {etichetta:34s} nessun record")
        return None
    w = s["COEFIN"].to_numpy(float)
    cls = s["ETAMi"].to_numpy(float)
    o = np.argsort(cls)
    cum = np.cumsum(w[o]) / w.sum()
    k = int(cls[o][np.searchsorted(cum, 0.5)])
    # eta' mediana approssimata: centro della classe mediana pesata
    eta = CENTRO.get(k, np.nan)
    noto = s["CITTMi"].isin([1, 3])          # 9 = non disponibile, escluso
    q_str = (float(np.average((s.loc[noto, "CITTMi"] == 3).to_numpy(float),
                              weights=s.loc[noto, "COEFIN"]))
             if noto.any() else np.nan)
    quota = float(w.sum() / tot)
    print(f"   {etichetta:34s} n={len(s):5d}  classe {k:02d} "
          f"({ETAMI.get(k, '?'):>5s})  ~{eta:4.1f}  "
          f"stran {q_str:5.3f}  quota {quota:6.4f}")
    return {"k": k, "eta": eta, "str": q_str, "quota": quota}


def main():
    d = carica_avq()
    tot = float(d["COEFIN"].sum())
    print("=" * 72)
    print(f"AVQ Emilia-Romagna, {len(d):,} componenti, quote pesate COEFIN"
          .replace(",", "."))
    print("   ETAMi decodificata: 15 classi irregolari, la 15 aperta.")
    print("   L'eta' `~` e' il CENTRO della classe mediana, non una mediana.")
    print("=" * 72)
    print(f"   BERSAGLIO (Parma, codice 11)       n=14725  "
          f"classe -- (35-44)   ~{BERSAGLIO['eta']:4.1f}  "
          f"stran {BERSAGLIO['str']:5.3f}  quota {BERSAGLIO['quota']:6.4f}\n")

    p = {}
    for cod in (1, 2, 3, 6, 17):
        p[cod] = profilo(d, d.RELPAR == cod,
                         f"{cod:02d} {ETICHETTE.get(cod, '?')}", tot)
    p["A"] = profilo(d, d.RELPAR.isin(range(8, 17)), "08-16 altri parenti", tot)
    print()
    mix = profilo(d, d.RELPAR.isin([3, 17]), "03+17 (fusa stretta)", tot)
    larga = profilo(d, d.RELPAR.isin([3, 17]) | d.RELPAR.isin(range(8, 17)),
                    "03+17+08-16 (fusa LARGA)", tot)

    print("\n" + "=" * 72)
    print("scarti dal bersaglio")
    print("=" * 72)
    for et, v in (("03 solo", p.get(3)), ("17 solo", p.get(17)),
                  ("03+17", mix), ("03+17+08-16", larga)):
        if v:
            print(f"   {et:14s} eta {v['eta'] - BERSAGLIO['eta']:+6.1f}  "
                  f"stranieri {v['str'] - BERSAGLIO['str']:+6.3f}  "
                  f"quota {v['quota'] - BERSAGLIO['quota']:+7.4f}")

    print("\n   ETA': non discrimina. Tutti i candidati cadono nella classe")
    print("   010 (35-44), che contiene i 38 anni di Parma.")
    print("   QUOTA: solo la fusa LARGA si avvicina, e lo scarto residuo e'")
    print("   nella direzione attesa (citta' contro regione).")
    print("   CITTADINANZA: nessun candidato arriva al 52%. ANOMALIA APERTA.")

    print("\n" + "=" * 72)
    print("validazione esterna: classi AVQ contro eta' mediane di Parma")
    print("=" * 72)
    for cod, eta_parma in ((1, 55), (2, 57), (6, 16)):
        v = p.get(cod)
        if v:
            print(f"   {ETICHETTE[cod]:34s} AVQ {ETAMI[v['k']]:>6s}   "
                  f"Parma {eta_parma}")
    print("   Due fonti indipendenti, universi e anni diversi: le classi")
    print("   coincidono. Rafforza la mappa inferita in §2.3 della nota.")


if __name__ == "__main__":
    main()
