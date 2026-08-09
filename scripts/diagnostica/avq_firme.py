#!/usr/bin/env python3
"""Il repertorio delle configurazioni di nucleo — quante firme, e quali.

Primo mattone dell'anello 4. Con una classificazione operativa del ruolo,
un nucleo diventa una FIRMA -- l'insieme ordinato dei ruoli dei suoi
componenti, per esempio `riferimento+partner+figlio+figlio` -- e la
distribuzione delle firme E' il repertorio da cui l'assemblaggio pesca.

Questo script misura se la classificazione scelta sia adeguata:

  · quante firme distinte produce, contro quante ne producono le 17
    modalita' grezze;
  · quante firme servono per coprire il 90% e il 95% dei nuclei;
  · se le firme siano coerenti (un solo riferimento, al piu' un partner);
  · come cambia la distribuzione delle firme dentro ogni classe di
    ampiezza, che e' il modo in cui l'assemblaggio la usera': l'ampiezza
    viene dai vincoli di sezione (`PF3`-`PF8`), la firma dal repertorio.


LA CLASSIFICAZIONE OPERATIVA

Decisa il 9/8/2026, da `METADATI/Classificazioni/AVQ_Classificazione_2024_var5`:

    riferimento     01
    partner         02 coniuge · 03 convivente coniugalmente
    figlio          06 dell'ultima unione · 07 di unione precedente
    genitore        04 di PR · 05 del partner di PR
    altro_parente   08-16
    non_parente     17 persona legata da amicizia

Due decisioni prese esplicitamente, non dedotte dai dati:

  · `partner` TIENE DISTINTI 02 e 03 nella colonna `relpar_fine`. La
    fusione costerebbe l'unica distinzione capace di sciogliere il codice
    11 dei microdati di Parma quando arrivera' la risposta del Comune, e
    coppie di fatto e coniugate hanno profili d'eta' e cittadinanza
    diversi.

  · `altro_parente` accorpa NOVE modalita' in una classe da ~250 nuclei:
    grossolano, ma separare i nipoti (10, 11) darebbe classi da 56 e da
    poche decine. La mappa sta in un dizionario esplicito, quindi
    cambiarla e' una riga.


DUE DIFFERENZE DELIBERATE RISPETTO A `assign_avq.py` (vedi avq_nuclei.py)

  · si usano TUTTE E TRE le annate: il 2022 e' escluso dal pool
    dell'anello 2 perche' manca `CRONI`, che alla struttura familiare non
    serve;
  · NON si filtra `ISTRMi = 99`: scartare un componente mutila il nucleo.

Chiave del nucleo: `ANNO|PROFAM`. `PROFAM` riparte da 1 ogni anno.

    python scripts/diagnostica/avq_firme.py
    python scripts/diagnostica/avq_firme.py --regioni 80 30 --unisci
"""

import argparse
import glob
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

ANNI = (2022, 2023, 2024)
PAT = "data/avq/anni/avq{a}/MICRODATI/AVQ_Microdati_{a}.txt"

# mappa esplicita: modalita' RELPAR (AVQ) -> classe operativa
MAPPA = {
    1: "riferimento",
    2: "partner", 3: "partner",
    4: "genitore", 5: "genitore",
    6: "figlio", 7: "figlio",
    8: "altro_parente", 9: "altro_parente", 10: "altro_parente",
    11: "altro_parente", 12: "altro_parente", 13: "altro_parente",
    14: "altro_parente", 15: "altro_parente", 16: "altro_parente",
    17: "non_parente",
}
# ordine di stampa nelle firme: strutturale, non alfabetico
ORDINE = {"riferimento": 0, "partner": 1, "figlio": 2, "genitore": 3,
          "altro_parente": 4, "non_parente": 5}
SIGLA = {"riferimento": "R", "partner": "P", "figlio": "F",
         "genitore": "G", "altro_parente": "A", "non_parente": "N"}
NOMI_REG = {80: "Emilia-Romagna", 30: "Lombardia"}


def percorso(anno):
    p = PAT.format(a=anno)
    if os.path.exists(p):
        return p
    g = glob.glob(f"data/avq/**/*Microdati_{anno}*.txt", recursive=True)
    return g[0] if g else None


def carica(regioni):
    keep = {"PROFAM", "NCOMP", "RELPAR", "ETAMi", "SESSO", "ISTRMi",
            "REGMf", "COEFIN"}
    pezzi = []
    for anno in ANNI:
        p = percorso(anno)
        if not p:
            print(f"   {anno}: file non trovato")
            continue
        d = pd.read_csv(p, sep="\t", low_memory=False,
                        usecols=lambda c: c in keep)
        d["ANNO"] = anno
        pezzi.append(d)
    if not pezzi:
        sys.exit("nessun file AVQ trovato")
    d = pd.concat(pezzi, ignore_index=True)

    for c in ("REGMf", "RELPAR", "NCOMP", "ETAMi", "COEFIN"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["COEFIN"] = d["COEFIN"] / 10000.0
    d = d[d.REGMf.isin(regioni)].copy()
    d["nucleo"] = d["ANNO"].astype(str) + "|" + d["PROFAM"].astype(str)
    d["classe"] = d["RELPAR"].map(MAPPA)
    return d


def firma(serie, col):
    """Firma del nucleo: sigle ordinate per ruolo strutturale."""
    v = sorted(serie[col].dropna(),
               key=lambda x: ORDINE.get(x, 99) if col == "classe" else x)
    if col == "classe":
        return "".join(SIGLA.get(x, "?") for x in v)
    return "-".join(f"{int(x):02d}" for x in v)


def analizza(d, etichetta):
    print("\n" + "=" * 72)
    print(f"{etichetta} · {len(d):,} individui".replace(",", "."))
    print("=" * 72)

    g = d.groupby("nucleo")
    nuc = pd.DataFrame({
        "amp": g.size(),
        "peso": g["COEFIN"].first(),
        "f_fine": g.apply(lambda x: firma(x, "RELPAR")),
        "f_op": g.apply(lambda x: firma(x, "classe")),
        "n_rif": g["classe"].apply(lambda s: (s == "riferimento").sum()),
        "n_par": g["classe"].apply(lambda s: (s == "partner").sum()),
        "n_nan": g["classe"].apply(lambda s: s.isna().sum()),
    })
    print(f"   nuclei: {len(nuc):,}".replace(",", ".")
          + f" · ampiezza media {nuc.amp.mean():.2f}"
          + f" · max {nuc.amp.max()}")

    # coerenza: un solo riferimento, al piu' un partner
    print("\n   coerenza delle firme")
    for et, cond in (("nuclei senza riferimento", nuc.n_rif == 0),
                     ("nuclei con 2+ riferimenti", nuc.n_rif > 1),
                     ("nuclei con 2+ partner", nuc.n_par > 1),
                     ("individui con RELPAR non mappata", nuc.n_nan > 0)):
        n = int(cond.sum())
        print(f"      {et:36s} {n:5d}" + ("   <-- da capire" if n else ""))

    # quante firme
    n_fine, n_op = nuc.f_fine.nunique(), nuc.f_op.nunique()
    print(f"\n   firme distinte: {n_fine} con le 17 modalita' grezze, "
          f"{n_op} con la classificazione operativa")

    for et, col in (("operativa", "f_op"), ("grezza", "f_fine")):
        c = nuc[col].value_counts(normalize=True).sort_values(ascending=False)
        cum = c.cumsum()
        k90 = int((cum < 0.90).sum()) + 1
        k95 = int((cum < 0.95).sum()) + 1
        print(f"      {et:10s} 90% dei nuclei in {k90:3d} firme · "
              f"95% in {k95:3d}")

    print("\n   le venti firme operative piu' frequenti")
    top = (nuc.groupby("f_op")
              .agg(n=("amp", "size"), amp=("amp", "first"),
                   peso=("peso", "sum"))
              .sort_values("n", ascending=False).head(20))
    top["quota"] = top.n / len(nuc)
    top["quota_pes"] = top.peso / nuc.peso.sum()
    print(top[["amp", "n", "quota", "quota_pes"]].round(4).to_string())

    # firme per classe di ampiezza: e' cosi' che l'assemblaggio le usera'
    print("\n   firme per classe di ampiezza (l'ampiezza viene da PF3-PF8,")
    print("   la firma dal repertorio)")
    for k in sorted(nuc.amp.unique()):
        sub = nuc[nuc.amp == k]
        c = sub.f_op.value_counts(normalize=True)
        cum = c.cumsum()
        k90 = int((cum < 0.90).sum()) + 1
        prime = ", ".join(f"{a} {b:.2f}" for a, b in c.head(4).items())
        print(f"      amp {int(k)}: {len(sub):5d} nuclei · "
              f"{sub.f_op.nunique():3d} firme · 90% in {k90:3d} · {prime}")

    return nuc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regioni", type=int, nargs="+", default=[80, 30])
    ap.add_argument("--unisci", action="store_true",
                    help="analizza anche i due pool uniti")
    a = ap.parse_args()

    d = carica(a.regioni)
    print("mappa RELPAR -> classe operativa")
    for cl in sorted(set(MAPPA.values()), key=lambda x: ORDINE[x]):
        cod = [k for k, v in MAPPA.items() if v == cl]
        print(f"   {SIGLA[cl]} {cl:15s} {cod}")

    quadri = {}
    for r in a.regioni:
        sub = d[d.REGMf == r]
        if len(sub):
            quadri[r] = analizza(sub, NOMI_REG.get(r, str(r)))

    if a.unisci and len(quadri) > 1:
        analizza(d, "POOL UNITO")
        # le due regioni si possono unire?
        chiavi = set().union(*(set(q.f_op) for q in quadri.values()))
        t = pd.DataFrame({NOMI_REG.get(r, str(r)):
                          q.f_op.value_counts(normalize=True)
                          for r, q in quadri.items()}).reindex(chiavi).fillna(0)
        tvd = 0.5 * float((t.iloc[:, 0] - t.iloc[:, 1]).abs().sum())
        print(f"\n   TVD fra le distribuzioni di firme delle due regioni: "
              f"{tvd:.4f}")
        print("   piccola -> i pool si possono unire per il repertorio, che")
        print("   e' un'assunzione IN PIU' rispetto all'anello 2 (dove le")
        print("   regioni restano separate perche' le AVQ sono attitudinali).")


if __name__ == "__main__":
    main()
