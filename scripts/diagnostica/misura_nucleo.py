#!/usr/bin/env python3
"""M0-M3 — il ruolo familiare si deriva a valle, o serve il vincolo di sezione?

Fonte: `data/opendata/034027/Popolazione_residente_2025.csv`, fornitura del
Comune di Parma. 202.111 righe, una per residente, separatore `;`.

    Tipores  1 = famiglia (199.015) · 2 = convivenza (3.096)
    Sesso    1 = M · 2 = F
    ETA      anni compiuti
    Cittad   codice paese ISTAT, 151 modalita', 100 = Italia (82,03%)
    Ncomp    componenti del nucleo
    Relpar   1 persona di riferimento · 2 partner · 3 figlio
             11 coabitante (INFERITO dai conteggi, vedi sotto)
    Quartiere  13 modalita' in chiaro = COM_ASC1, la zona di anello 1
    SEZ21    sezione 2021, NON zero-paddata


COSA E' GIA' STATO MISURATO SU QUESTO FILE (9 agosto 2026)

  · Le convivenze spiegano TUTTE le anomalie di Ncomp: i valori 319, 111,
    110, 108, 40 comparivano esattamente quel numero di volte -- e' la
    firma di una convivenza, non un errore. Con Tipores=1 il massimo
    scende da 319 a 12.

  · I nuclei CHIUDONO. Somma di 1/Ncomp = 96.984 contro 96.985 persone di
    riferimento: scarto -0,00%. Il numero di famiglie per sezione e' un
    vincolo ESATTO, non stimato.
    (Ritratta un'ipotesi precedente su nuclei a cavallo di sezione: lo
    scarto di ~30 per classe di ampiezza era l'effetto delle convivenze
    mescolate al conteggio.)

  · Residuo frazionario massimo per sezione = 1/3 su 1.314 sezioni: UN
    SOLO nucleo in tutta Parma sta a cavallo di due sezioni. Il vincolo
    vale al livello dove serve.

  · Relpar=11 e' coabitazione: 14.724 persone (7,4%), eta' mediana 38,
    stranieri al 51,7% contro il 17,4% della popolazione. Non studenti --
    lavoratori migranti, con una coda universitaria.
    LA CODIFICA E' INFERITA DAI CONTEGGI, NON LETTA SU UN CODEBOOK. Va
    confermata con l'ufficio statistica prima che finisca in un paper.


LE MISURE

  M0  indipendenza(Relpar, Ncomp). La coppia si estrae insieme o
      separatamente? Da qui in poi le due variabili si misurano SEPARATE:
      la composita ha ~30 modalita' e fa scattare la guardia sui supporti
      dentro ogni cella.

  M1/M2  d(S) = TVD( P(ruolo | S), P(ruolo) ) per ogni condizionante.

  M3  TVD( P(ruolo | C4, quartiere), P(ruolo | C4) ) -- IL NUMERO CHE
      DECIDE. Residuo geografico a demografia fissata, cioe' l'analogo
      dell'assunzione (8) per la struttura familiare.
        netto < ~0,02  -> derivazione a valle, anello 1 intatto
        netto > ~0,08  -> serve il vincolo di sezione nell'assemblaggio
      Il pavimento di rumore si misura per permutazione delle etichette
      di quartiere dentro la cella: la TVD cresce con la rarefazione, e
      senza pavimento il numero non e' confrontabile.

  M3'  la stessa misura ESCLUDENDO Relpar=11.
      PREVISIONE REGISTRATA PRIMA DELLA MISURA (9 agosto 2026): se M3 su
      `relpar` esce grande, il netto deve CROLLARE togliendo la
      coabitazione, perche' la coabitazione migrante e' geograficamente
      concentrata mentre la struttura coniugale lo e' molto meno. Se
      crolla, la conclusione non e' «serve il vincolo di sezione» ma
      «serve per la TIPOLOGIA del nucleo, non per il ruolo dentro la
      famiglia» -- piu' preciso e piu' utile. Se non crolla, la
      previsione e' falsificata e va scritto che lo e'.


IL LIMITE DA DICHIARARE

Il file NON contiene lo stato civile, che e' la variabile che spiegherebbe
gran parte di Relpar. Il condizionamento demografico e' quindi piu' debole
di quello disponibile in anello 1, e la lettura di M3 e' ASIMMETRICA:

  · M3 piccolo -> conclusione SOLIDA: la geografia non aggiunge nulla
    neanche con la demografia zoppa.
  · M3 grande  -> AMBIGUO: potrebbe essere stato civile che si traveste da
    geografia, perche' i quartieri differiscono per quota di coniugati.
    Servirebbe un controllo su una fonte che abbia entrambi.

Inoltre il file e' del 2025 mentre la popolazione sintetica e' calibrata su
dati 2023: due istanti diversi, da dichiarare quando i numeri finiscono in
un articolo.

    python scripts/diagnostica/misura_nucleo.py \
        2>&1 | tee note/misure/tvd_nucleo_parma_AAAAMMGG.txt
"""

import sys

import numpy as np
import pandas as pd

import gsp.tvd as T

SRC = "data/opendata/034027/Popolazione_residente_2025.csv"
SEP = ";"

MIN_CELLA = 400      # unita' minime nella cella demografica perche' entri in M3
MIN_ZONA = 100       # unita' minime nella coppia (cella, quartiere)
MIN_UNITA = 200      # unita' minime per una modalita' in M1/M2
N_PERM = 100         # permutazioni per il pavimento di rumore di M3
RNG = np.random.default_rng(20260809)

# `auto_totali=False` OVUNQUE. Le modalita' di Relpar e Ncomp sono codici
# numerici e T.TOTALI contiene "0", "9", "99": col default il modulo
# scarterebbe in silenzio Relpar=9. I prefissi "n"/"r" sotto sono una
# seconda cintura sulla stessa trappola.
KW = dict(auto_totali=False)

C = ["Sesso", "eta8", "citt"]        # condizionanti per M1/M2
C4 = ["Sesso", "eta4", "citt"]       # griglia ridotta per M3


def carica():
    try:
        d = pd.read_csv(SRC, sep=SEP, dtype=str)
    except FileNotFoundError:
        sys.exit(f"non trovato: {SRC}\nlanciare dalla radice di ~/progetti/gsp")

    attesi = {"Tipores", "Sesso", "ETA", "Cittad", "Ncomp", "Relpar",
              "Quartiere", "SEZ21"}
    manca = attesi - set(d.columns)
    if manca:
        sys.exit(f"colonne assenti: {sorted(manca)}\n"
                 f"presenti: {sorted(d.columns)}")

    n0 = len(d)
    d["ETA"] = pd.to_numeric(d["ETA"], errors="coerce")
    d["Ncomp"] = pd.to_numeric(d["Ncomp"], errors="coerce")
    d = d.dropna(subset=["ETA", "Ncomp", "Relpar", "Sesso", "SEZ21",
                         "Quartiere"])

    # convivenze: universo diverso, Ncomp e Relpar vi misurano un'altra cosa
    n_conv = int((d.Tipores != "1").sum())
    d = d[d.Tipores == "1"]

    # incoerenza logica: unipersonale che non e' persona di riferimento
    inc = ((d.Ncomp == 1) & (d.Relpar != "1"))
    n_inc = int(inc.sum())
    d = d[~inc]

    print(f"righe lette {n0:,}".replace(",", "."))
    print(f"   convivenze escluse (Tipores=2)   {n_conv:,}".replace(",", "."))
    print(f"   incoerenti (Ncomp=1, Relpar!=1)  {n_inc:,}".replace(",", "."))
    print(f"   in analisi {len(d):,}".replace(",", "."))
    if d.Ncomp.max() > 20:
        print(f"   !! Ncomp max = {d.Ncomp.max()} dopo il filtro: "
              f"il filtro sulle convivenze non ha funzionato")

    bin8 = [-1, 8, 14, 24, 34, 49, 64, 74, 200]
    eti8 = ["0-8", "9-14", "15-24", "25-34", "35-49", "50-64", "65-74", "75+"]
    d["eta8"] = pd.cut(d["ETA"], bin8, labels=eti8).astype(str)
    d["eta4"] = pd.cut(d["ETA"], [-1, 24, 49, 64, 200],
                       labels=["u25", "25-49", "50-64", "65p"]).astype(str)

    # binaria, per allinearsi alla `cittadinanza` di anello 1
    d["citt"] = np.where(d["Cittad"] == "100", "ITL", "FRG")

    d["ncomp5"] = "n" + d["Ncomp"].clip(upper=5).astype(int).astype(str)
    d["relpar"] = "r" + d["Relpar"].astype(str)

    print(f"   quartieri {d.Quartiere.nunique()}  ·  "
          f"sezioni {d.SEZ21.nunique()}  ·  "
          f"stranieri {(d.citt == 'FRG').mean():.3f}")
    return d


def m3(d, y, permuta=False):
    """TVD( P(y | cella, quartiere), P(y | cella) ), cella per cella.

    Il parametro `base` di T.profilo sostituisce la marginale con la
    composizione condizionata sulla cella: e' quello che rende la misura
    incrementale usando il modulo cosi' com'e', guardia sui supporti
    compresa.
    """
    righe = []
    for chiave, g in d.groupby(C4, observed=True):
        if len(g) < MIN_CELLA:
            continue
        if permuta:
            g = g.assign(Quartiere=RNG.permutation(g["Quartiere"].values))
        p = T.profilo(g, y, ["Quartiere"], base=T.composizione(g, y),
                      min_unita=MIN_ZONA, stampa=False, **KW)
        if p.empty:
            continue
        righe.append(p.assign(cella="|".join(map(str, chiave))))
    if not righe:
        return pd.DataFrame(), float("nan")
    r = pd.concat(righe, ignore_index=True)
    v = r.dropna(subset=["TVD"])
    med = float(np.average(v.TVD, weights=v.n)) if len(v) else float("nan")
    return r, med


def blocco_m3(d, y, etichetta):
    r, oss = m3(d, y)
    if not np.isfinite(oss):
        print(f"\n{etichetta}: nessuna cella misurabile. Abbassare MIN_CELLA "
              f"o MIN_ZONA.")
        return None
    floor = [m3(d, y, permuta=True)[1] for _ in range(N_PERM)]
    floor = [x for x in floor if np.isfinite(x)]
    mu, p95 = float(np.mean(floor)), float(np.percentile(floor, 95))
    netto = oss - mu
    print(f"\n{etichetta}")
    print(f"   osservata {oss:.4f}   pavimento {mu:.4f} (p95 {p95:.4f})"
          f"   NETTO {netto:+.4f}")
    print(f"   coppie (cella,quartiere): misurate {int(r.TVD.notna().sum())}, "
          f"non misurate {int(r.TVD.isna().sum())}")
    if r.TVD.isna().sum() > r.TVD.notna().sum():
        print("   !! la maggioranza non e' misurabile: non e' «la geografia "
              "non conta»,\n      e' «la fonte non incrocia abbastanza». "
              "Da dichiarare, non da confondere.")
    top = r.dropna(subset=["TVD"]).nlargest(8, "TVD")
    print(top[["cella", "modalita", "n", "supporto", "TVD"]]
          .to_string(index=False))
    return netto


def main():
    d = carica()

    print("\n" + "=" * 72)
    print("M0 — la coppia (Relpar, Ncomp) si estrae insieme o separatamente?")
    print("=" * 72)
    T.indipendenza(d, "relpar", "ncomp5")

    for y in ("ncomp5", "relpar"):
        print("\n" + "=" * 72)
        print(f"M1/M2 — quanto ciascun condizionante sposta `{y}`  "
              f"(supporto {d[y].nunique()})")
        print("=" * 72)
        T.riassunto(d, y, C, min_unita=MIN_UNITA, **KW)

    print("\n" + "=" * 72)
    print("M3 — residuo geografico a demografia fissata")
    print("=" * 72)
    blocco_m3(d, "ncomp5", "ncomp5")
    n_full = blocco_m3(d, "relpar", "relpar — tutti")

    print("\n" + "=" * 72)
    print("M3' — la stessa misura senza la coabitazione (Relpar=11)")
    print("=" * 72)
    d2 = d[d.relpar != "r11"]
    print(f"escluse {len(d) - len(d2):,} righe".replace(",", "."))
    n_cut = blocco_m3(d2, "relpar", "relpar — senza coabitazione")

    if n_full is not None and n_cut is not None:
        print("\n" + "-" * 72)
        print("previsione registrata: il netto deve CROLLARE.")
        print(f"   con coabitazione  {n_full:+.4f}")
        print(f"   senza             {n_cut:+.4f}")
        if n_full > 1e-9:
            print(f"   caduta {(1 - n_cut / n_full) * 100:.0f}%")
        print("   se la caduta e' forte: il vincolo di sezione serve per la "
              "TIPOLOGIA\n   del nucleo, non per il ruolo dentro la famiglia. "
              "Se non cade, la\n   previsione e' falsificata e va scritto "
              "che lo e'.")

    print("\n" + "=" * 72)
    print("famiglie per sezione — vincolo di conteggio per l'assemblaggio")
    print("=" * 72)
    g = d.groupby("SEZ21")["Ncomp"].agg(pers="size",
                                        fam=lambda s: (1.0 / s).sum())
    res = (g.fam - g.fam.round()).abs()
    print(g.fam.describe().round(1).to_string())
    print(f"\ntotale {g.fam.sum():,.0f}".replace(",", ".")
          + f"   riferimenti {int((d.Relpar == '1').sum()):,}".replace(",", ".")
          + f"   residuo frazionario max {res.max():.4f}")
    print("   residuo ~0 -> i nuclei stanno dentro una sola sezione e il "
          "vincolo\n   di conteggio e' esatto al livello dove serve.")


if __name__ == "__main__":
    main()
