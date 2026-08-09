#!/usr/bin/env python3
"""Prototipo dell'assemblaggio — quanto costa comporre i nuclei?

Terzo mattone dell'anello 4, dopo `nota_nucleo_familiare_v3` (dove entra)
e `nota_repertorio_avq_v1` (con quale materiale). Qui si misura la sola
cosa che decide l'algoritmo definitivo:

    dati gli individui di una sezione e i vincoli di ampiezza,
    quanti slot restano senza candidato plausibile?

  ~1%   -> si rilassa la compatibilita' e non se ne parla piu'
  ~15%  -> serve un algoritmo che OTTIMIZZI invece di riempire avidamente

Il prototipo e' deliberatamente AVIDO e non ottimizza: serve a stimare la
difficolta' del problema, non a risolverlo. Un algoritmo migliore puo'
solo fare meglio di questi numeri, quindi sono un limite superiore al
tasso di fallimento.


PERCHE' PARMA E NON LA POPOLAZIONE SINTETICA

I microdati di Parma hanno `Relpar` per individuo, cioe' il ruolo VERO.
Si puo' quindi misurare non solo la fattibilita' ma anche l'ACCURATEZZA:
degli individui a cui il prototipo assegna il ruolo R, quanti avevano
davvero `Relpar = 1`? E' una verita' di riferimento che la popolazione
sintetica non ha.

Il prototipo usa solo gli attributi che l'anello 1 fornisce -- sesso,
eta', cittadinanza -- e ignora `Ncomp` e `Relpar` durante l'assemblaggio.
`Ncomp` serve solo a costruire il vincolo di ampiezza (l'analogo di
`PF3`-`PF8`, qui esatto perche' i nuclei di Parma chiudono: 96.984 contro
96.985 riferimenti); `Relpar` solo a valutare a posteriori.

*Limite dichiarato*: la valutazione del ruolo usa la mappa di Parma, di
cui sono certi solo 1 = riferimento, 2 = partner, 3 = figlio -- il 90%
dei casi. Il codice 11 e' una categoria residua larga
(`nota_nucleo_familiare_v3` §2.4) e non e' valutabile.


I CRITERI DI COMPATIBILITA'

Da `nota_repertorio_avq_v1` §5, misurati sul repertorio AVQ:

    slot   vincolo                                   forza
    R      maschio p~0,80 in coppia, femmina         preferenza
           p~0,81 se monogenitore
    P      stessa classe d'eta' o adiacente,         eta' debole
           sesso opposto                             sesso RIGIDO
    F      riferimento - figlio in [21, 45]          FORTE
    F 2°   entro 11 anni dal fratello                forte
    G      riferimento + [20, 40], per analogia      dichiarato
    citt.  omogenea con p~0,55 nei nuclei misti      preferenza

Le classi d'eta' sono quelle di `ETAMi` (quindici, irregolari): il
vincolo sul partner e' «stessa classe o adiacente» perche' con classi
larghe 5-10 anni il divario reale fra partner e' sotto la risoluzione
dell'AVQ (§4.2 della nota). E' grossolano, ed e' il motivo per cui serve
il SUF di EU-SILC.


    python scripts/diagnostica/proto_assembla.py
    python scripts/diagnostica/proto_assembla.py --sezioni 5 --seme 7
"""

import argparse
import glob
import os
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

ANNI = (2022, 2023, 2024)
PAT_AVQ = "data/avq/anni/avq{a}/MICRODATI/AVQ_Microdati_{a}.txt"
PARMA = "data/opendata/034027/Popolazione_residente_2025.csv"

MAPPA_AVQ = {1: "R", 2: "P", 3: "P", 4: "G", 5: "G", 6: "F", 7: "F",
             **{k: "A" for k in range(8, 17)}, 17: "N"}
ORDINE = {"R": 0, "P": 1, "F": 2, "G": 3, "A": 4, "N": 5}

# confini superiori delle 15 classi ETAMi
BORDI = [2, 5, 10, 13, 15, 17, 19, 24, 34, 44, 54, 59, 64, 74, 200]

# criteri (nota_repertorio_avq §5)
GEN_MIN, GEN_MAX = 21, 45        # riferimento - figlio
FRAT_MAX = 11                    # fra fratelli
GEN_MIN_G, GEN_MAX_G = 20, 40    # genitore - riferimento
P_MASCHIO_COPPIA = 0.80
P_FEMMINA_MONO = 0.81


def classe_eta(anni):
    return int(np.searchsorted(BORDI, anni, side="left")) + 1


# ------------------------------------------------------------ repertorio

def carica_repertorio():
    keep = {"PROFAM", "RELPAR", "REGMf", "COEFIN"}
    pezzi = []
    for anno in ANNI:
        p = PAT_AVQ.format(a=anno)
        if not os.path.exists(p):
            g = glob.glob(f"data/avq/**/*Microdati_{anno}*.txt", recursive=True)
            p = g[0] if g else None
        if not p:
            continue
        d = pd.read_csv(p, sep="\t", low_memory=False,
                        usecols=lambda c: c in keep)
        d["ANNO"] = anno
        pezzi.append(d)
    if not pezzi:
        sys.exit("microdati AVQ non trovati")
    d = pd.concat(pezzi, ignore_index=True)
    for c in ("REGMf", "RELPAR", "COEFIN"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[d.REGMf.isin([80, 30])].copy()
    d["nucleo"] = d.ANNO.astype(str) + "|" + d.PROFAM.astype(str)
    d["ruolo"] = d.RELPAR.map(MAPPA_AVQ)

    g = d.groupby("nucleo")
    rep = pd.DataFrame({
        "amp": g.size(),
        "peso": g["COEFIN"].first() / 10000.0,
        "firma": g.apply(lambda x: "".join(sorted(x.ruolo.dropna(),
                                                  key=lambda r: ORDINE[r]))),
    })
    # P(firma | ampiezza), pesata
    out = {}
    for k, s in rep.groupby("amp"):
        v = s.groupby("firma")["peso"].sum()
        out[int(k)] = (v.index.to_numpy(), (v / v.sum()).to_numpy())
    print(f"[rep] {len(rep):,} nuclei AVQ · ampiezze {sorted(out)}"
          .replace(",", "."))
    return out


# ------------------------------------------------------------ popolazione

def carica_parma():
    d = pd.read_csv(PARMA, sep=";", dtype=str)
    d["ETA"] = pd.to_numeric(d.ETA, errors="coerce")
    d["Ncomp"] = pd.to_numeric(d.Ncomp, errors="coerce")
    d = d.dropna(subset=["ETA", "Ncomp", "Relpar", "Sesso", "SEZ21"])
    d = d[d.Tipores == "1"]
    d = d[~((d.Ncomp == 1) & (d.Relpar != "1"))]
    d["maschio"] = d.Sesso == "1"
    d["straniero"] = d.Cittad != "100"
    d["cls"] = d.ETA.apply(classe_eta)
    print(f"[pop] {len(d):,} individui in famiglia, {d.SEZ21.nunique()} sezioni"
          .replace(",", "."))
    return d


# ------------------------------------------------------------ assemblaggio

def assembla(ind, rep, rng):
    """Avido: nuclei dal piu' grande al piu' piccolo, slot piu' vincolati
    per primi. Restituisce l'assegnazione e il conto dei fallimenti."""
    # vincolo di ampiezza: l'analogo di PF3-PF8
    conta = Counter()
    for k, n in ind.Ncomp.value_counts().items():
        conta[int(min(k, 6))] += n / k
    conta = {k: int(round(v)) for k, v in conta.items() if round(v) > 0}

    # firme estratte dal repertorio, condizionate all'ampiezza
    nuclei = []
    for k, n in conta.items():
        if k not in rep:
            k_uso = max(x for x in rep if x <= k)
        else:
            k_uso = k
        firme, p = rep[k_uso]
        for f in rng.choice(firme, size=n, p=p):
            nuclei.append(f if len(f) == k else "R" + "F" * (k - 1))

    lib = set(ind.index)
    eta = ind.ETA.to_dict()
    cls = ind.cls.to_dict()
    masc = ind.maschio.to_dict()
    stra = ind.straniero.to_dict()

    assegn = {}
    esiti = Counter()
    slot_falliti = Counter()
    divari = defaultdict(list)

    for i_n, firma in enumerate(sorted(nuclei, key=len, reverse=True)):
        if not lib:
            esiti["nuclei senza individui"] += 1
            continue
        n_f = firma.count("F")
        n_p = firma.count("P")

        # --- riferimento: deve avere figli plausibili se la firma li chiede
        cand = list(lib)
        if n_f:
            ok = [j for j in cand
                  if sum(1 for h in lib
                         if GEN_MIN <= eta[j] - eta[h] <= GEN_MAX) >= n_f]
            if not ok:
                slot_falliti["R (senza figli disponibili)"] += 1
                ok = cand
            cand = ok
        # preferenza di genere
        vuole_m = (n_p > 0)
        pref = [j for j in cand if masc[j] == vuole_m]
        p_gen = P_MASCHIO_COPPIA if n_p else (1 - P_FEMMINA_MONO)
        usa_pref = pref and rng.random() < p_gen
        r = rng.choice(pref if usa_pref else cand)
        lib.discard(r)
        assegn[r] = (i_n, "R")

        # --- figli: lo slot piu' vincolato
        figli = []
        for _ in range(n_f):
            c = [j for j in lib if GEN_MIN <= eta[r] - eta[j] <= GEN_MAX
                 and (not figli or
                      min(abs(eta[j] - eta[f]) for f in figli) <= FRAT_MAX)]
            if not c:
                c = [j for j in lib if eta[r] - eta[j] >= 15]  # ripiego
                slot_falliti["F"] += 1
            if not c:
                slot_falliti["F (nessun ripiego)"] += 1
                continue
            j = rng.choice(c)
            lib.discard(j)
            figli.append(j)
            assegn[j] = (i_n, "F")
            divari["gen"].append(eta[r] - eta[j])

        # --- partner: sesso rigido, eta' stessa classe o adiacente
        for _ in range(n_p):
            c = [j for j in lib if masc[j] != masc[r]
                 and abs(cls[j] - cls[r]) <= 1]
            if not c:
                c = [j for j in lib if masc[j] != masc[r]]
                slot_falliti["P (eta')"] += 1
            if not c:
                slot_falliti["P (nessun ripiego)"] += 1
                continue
            j = rng.choice(c)
            lib.discard(j)
            assegn[j] = (i_n, "P")
            divari["part"].append(eta[j] - eta[r])

        # --- genitori, altri, non parenti
        for ruolo in firma:
            if ruolo in "RPF":
                continue
            if ruolo == "G":
                c = [j for j in lib
                     if GEN_MIN_G <= eta[j] - eta[r] <= GEN_MAX_G]
                if not c:
                    slot_falliti["G"] += 1
                    c = [j for j in lib if eta[j] > eta[r]]
            else:
                c = list(lib)
            if not c:
                slot_falliti[ruolo + " (nessun ripiego)"] += 1
                continue
            j = rng.choice(c)
            lib.discard(j)
            assegn[j] = (i_n, ruolo)

    esiti["individui non collocati"] = len(lib)
    return assegn, esiti, slot_falliti, divari, len(nuclei)


def valuta(ind, assegn, esiti, falliti, divari, n_nuclei, et):
    print(f"\n--- {et} ---")
    n = len(ind)
    coll = len(assegn)
    print(f"   individui {n:5d} · nuclei richiesti {n_nuclei:4d} · "
          f"collocati {coll:5d} ({coll/n:.1%})")

    tot_f = sum(falliti.values())
    print(f"   slot con ripiego o fallimento: {tot_f} "
          f"({tot_f/max(coll,1):.1%} degli slot)")
    for k, v in falliti.most_common():
        print(f"      {k:28s} {v:4d}")
    for k, v in esiti.items():
        if v:
            print(f"      {k:28s} {v:4d}")

    # accuratezza del ruolo contro Relpar vero (1=R, 2=P, 3=F a Parma)
    vero = {"1": "R", "2": "P", "3": "F"}
    ok = tot = 0
    conf = Counter()
    for i, (_, ruolo) in assegn.items():
        v = vero.get(ind.at[i, "Relpar"])
        if v is None:
            continue
        tot += 1
        conf[(v, ruolo)] += 1
        ok += (v == ruolo)
    if tot:
        print(f"   accuratezza del ruolo (solo Relpar 1/2/3, {tot} casi): "
              f"{ok/tot:.3f}")
        for (v, p), c in sorted(conf.items(), key=lambda x: -x[1])[:6]:
            print(f"      vero {v} -> assegnato {p}: {c}")

    if divari["gen"]:
        g = np.array(divari["gen"])
        print(f"   divario generazionale ottenuto: mediana {np.median(g):.0f}"
              f" (AVQ 33) · fuori [21,45]: {np.mean((g<21)|(g>45)):.1%}")
    if divari["part"]:
        p = np.array(divari["part"])
        print(f"   divario fra partner: mediana {np.median(p):.0f}, "
              f"p05 {np.percentile(p,5):.0f}, p95 {np.percentile(p,95):.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sezioni", type=int, default=3)
    ap.add_argument("--seme", type=int, default=20260809)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seme)

    rep = carica_repertorio()
    pop = carica_parma()

    # una sezione piccola, una mediana, una grande
    dim = pop.groupby("SEZ21").size().sort_values()
    scelte = [dim.index[int(q * (len(dim) - 1))]
              for q in np.linspace(0.25, 1.0, a.sezioni)]

    for s in scelte:
        ind = pop[pop.SEZ21 == s].copy()
        r = assembla(ind, rep, rng)
        valuta(ind, *r, f"sezione {s} · {len(ind)} individui")

    print("\n   Il prototipo e' AVIDO e non ottimizza: questi tassi di")
    print("   fallimento sono un LIMITE SUPERIORE. Se sono gia' bassi, un")
    print("   algoritmo semplice basta; se sono alti, non e' detto che il")
    print("   problema sia difficile -- va riprovato ottimizzando.")


if __name__ == "__main__":
    main()
