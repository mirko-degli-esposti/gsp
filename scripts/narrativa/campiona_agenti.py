#!/usr/bin/env python3
"""campiona_agenti.py — un campione stratificato per esperimenti con LLM.

    python scripts/narrativa/campiona_agenti.py 017029
    python scripts/narrativa/campiona_agenti.py 017029 --n 240 --seed 7
    python scripts/narrativa/campiona_agenti.py 034027 --variabile FIDMED

COSA FA. Estrae N individui stratificati sui valori di una variabile AVQ
— per default `PUNTIFI10`, la fiducia nel governo comunale — in tre
gruppi netti, e ne costruisce il profilo completo: anagrafica, titolo di
studio dettagliato, settore e posizione professionale, nome.

I tre gruppi replicano il disegno di SIVE-Montelago (LOW/MED/HIGH) con
una differenza sostanziale: **il valore latente non e' scelto, e'
osservato**. A Montelago era la variabile sperimentale, qui viene dal
donatore AVQ. Si perde il controllo e si guadagna validita' esterna.

PERCHE' SI SALTANO 3 E 7. I gruppi devono essere separati, altrimenti la
fedelta' misurata confonde i gruppi adiacenti. A Montelago i latenti
erano netti per costruzione; qui si ottiene la stessa cosa lasciando un
valore di margine da ciascun lato.

IL NUMERO CHE CONTA NON E' N. E' quanti `donor_id` DISTINTI ci sono nel
campione: due agenti con lo stesso vettore AVQ non sono evidenza
indipendente, sono la stessa risposta con un altro nome. Lo script lo
riporta sempre, e avvisa se la replica supera una soglia.

Il tetto di un esperimento non e' la popolazione sintetica ma il pool di
donatori nella cella che si campiona. A Brescia le code hanno ~1.130 e
~1.330 donatori distinti, negli altri comuni ~630 e ~840: Brescia regge
il doppio. Vedi note/nota_code_puntifi10_v1.md.
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

# I tre gruppi, con i valori di margine lasciati fuori.
GRUPPI = {"LOW": (0, 2), "MED": (4, 6), "HIGH": (8, 10)}

# Oltre questa quota di agenti che condividono il donatore con un altro,
# il campione non e' piu' evidenza indipendente e va detto.
SOGLIA_REPLICA = 0.10


def campiona(comune, variabile="PUNTIFI10", n=120, seed=0,
             solo_occupati=True, gruppi=None, per_donatore=False):
    """N individui stratificati, n/3 per gruppo.

    DUE MODI DI CAMPIONARE, e la scelta cambia cosa il campione
    rappresenta.

    `per_donatore=False` (default) estrae individui a caso. E' il
    campionamento naturale, ma le collisioni arrivano prima di quanto
    suggerisca il numero di donatori disponibili: e' il paradosso del
    compleanno. A Brescia la coda alta ha 1.326 donatori, e gia' a 200
    estrazioni il 15% degli agenti ne condivide uno con un altro.

    `per_donatore=True` estrae prima i DONATORI, senza reinserimento, e
    poi per ciascuno un individuo a caso fra quelli che lo portano.
    Replica ZERO per costruzione, e il tetto diventa il numero di
    donatori nella coda invece di una frazione di esso.

    IL PREZZO. Pescando per donatore si sovrarappresentano quelli rari:
    un donatore usato tre volte e uno usato ottanta entrano con la stessa
    probabilita', mentre nella popolazione il secondo pesa 27 volte
    tanto. Per una TARATURA va bene, anzi meglio — massimizza la
    diversita' delle risposte. Per un campione che voglia essere
    RAPPRESENTATIVO no, e andrebbe pesato per riuso.

    E' la stessa distinzione che si accetta gia' stratificando: il
    disegno con quaranta agenti per gruppo non rispetta le proporzioni
    vere, e non deve.
    """
    import gsp.individui as I

    gruppi = gruppi or GRUPPI
    d = I.carica(comune)
    if variabile not in d.columns:
        raise KeyError(f"`{variabile}` non e' nella popolazione")
    v = pd.to_numeric(d[variabile], errors="coerce")
    base = d[v.notna()]
    if solo_occupati:
        base = base[base.condizione == "occupato"]
    vb = pd.to_numeric(base[variabile], errors="coerce")

    per_gruppo, quota = {}, n // len(gruppi)
    rng = np.random.default_rng(seed)
    for g, (lo, hi) in gruppi.items():
        s = base[vb.between(lo, hi)]
        if len(s) < quota:
            raise LookupError(
                f"gruppo {g} ({lo}-{hi}): solo {len(s)} individui, "
                f"ne servono {quota}")
        if per_donatore:
            don = s.donor_id.unique()
            if len(don) < quota:
                raise LookupError(
                    f"gruppo {g} ({lo}-{hi}): solo {len(don)} donatori "
                    f"distinti, ne servono {quota}. E' il tetto vero "
                    f"dell'esperimento: ridurre n oppure usare un comune "
                    f"con un pool piu' ampio (Brescia ha 8.111 donatori "
                    f"contro i 4.629 dell'Emilia-Romagna).")
            scelti = rng.choice(don, size=quota, replace=False)
            # un individuo a caso fra quelli che portano quel donatore
            pos = [rng.choice(np.flatnonzero((s.donor_id == d_).to_numpy()))
                   for d_ in scelti]
            g_ = s.iloc[np.sort(np.asarray(pos))].copy()
        else:
            idx = rng.choice(len(s), size=quota, replace=False)
            g_ = s.iloc[np.sort(idx)].copy()
        g_["gruppo"] = g
        g_["latente"] = pd.to_numeric(g_[variabile], errors="coerce").astype(int)
        per_gruppo[g] = g_
    return pd.concat(per_gruppo.values(), ignore_index=True)


def arricchisci(c, comune):
    """Aggiunge nome, titolo di studio, settore e posizione.

    Sono LIVELLO B: derivazioni deterministiche dall'uid, con fonte
    registrata e criterio misurato. Non aggiungono informazione ma
    rendono il profilo leggibile — e questo, in un persona-prompt, e' un
    rischio oltre che un vantaggio (nota_biografia_v1 §6).
    """
    import gsp.nomi as N
    from gsp import istruzione as IS, lavoro as L

    nomi, tit, lav = [], [], []
    for _, x in c.iterrows():
        a, b = N.nome_agente(x.uid, sesso=x.get("sesso"), eta=x.get("eta"),
                             background=x.get("background"),
                             origine_genitori=x.get("origine_genitori"),
                             paese=x.get("paese"))
        nomi.append(f"{a} {b}".title())
        tit.append(IS.titolo_agente(x.uid, x.get("istruzione"),
                                    sesso=x.get("sesso"), eta=x.get("eta"),
                                    comune=comune))
        lav.append(L.lavoro_agente(x.uid, condizione=x.get("condizione"),
                                   sesso=x.get("sesso"), comune=comune,
                                   istruzione=x.get("istruzione")))
    c = c.copy()
    c["nome"] = nomi
    c["titolo_studio"] = tit
    c["settore"] = [a for a, _ in lav]
    c["posizione"] = [b for _, b in lav]
    return c


def diagnostica(c, variabile="PUNTIFI10", stampa=True):
    """Quanti agenti DISTINTI, non quanti agenti."""
    righe = []
    for g, s in c.groupby("gruppo"):
        don = s.donor_id.nunique()
        righe.append({"gruppo": g, "agenti": len(s), "donatori": don,
                      "replica": round(1 - don / len(s), 3),
                      "latente_min": int(s.latente.min()),
                      "latente_max": int(s.latente.max()),
                      "eta_media": round(float(s.eta_anni.mean()), 1),
                      "F": int((s.sesso == "F").sum())})
    t = pd.DataFrame(righe)
    tot_don = c.donor_id.nunique()
    rep_tot = 1 - tot_don / len(c)

    if stampa:
        print(t.to_string(index=False))
        print(f"\n  totale {len(c)} agenti · {tot_don} donatori distinti · "
              f"replica {rep_tot:.1%}")
        if rep_tot > SOGLIA_REPLICA:
            print(f"\n  !! oltre il {SOGLIA_REPLICA:.0%} degli agenti "
                  f"condivide il vettore AVQ con\n     un altro: quelle "
                  f"coppie NON sono evidenza indipendente, e la\n     "
                  f"varianza osservata sottostima quella vera.\n"
                  f"     Rimedi: --per-donatore (replica zero), ridurre N, "
                  f"oppure un\n     comune con un pool piu' ampio "
                  f"(Brescia: 8.111 donatori contro 4.629).")
        else:
            print(f"  quasi ogni agente ha un vettore AVQ diverso: il "
                  f"campione regge")
    return t


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comune")
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--variabile", default="PUNTIFI10")
    ap.add_argument("--seed", type=int, default=0,
                    help="il campione DEVE essere riproducibile: e' il "
                         "livello A dell'esperimento")
    ap.add_argument("--tutti", action="store_true",
                    help="non limitare agli occupati")
    ap.add_argument("--per-donatore", action="store_true",
                    help="estrai prima i donatori e poi un individuo per "
                         "ciascuno: replica zero, ma sovrarappresenta i "
                         "donatori rari. Per una taratura va bene; per un "
                         "campione rappresentativo no")
    ap.add_argument("--out", default="dati/agenti")
    ap.add_argument("--mostra", type=int, default=3,
                    help="quanti profili stampare per gruppo")
    a = ap.parse_args()

    c = campiona(a.comune, a.variabile, a.n, a.seed,
                 solo_occupati=not a.tutti, per_donatore=a.per_donatore)
    c = arricchisci(c, a.comune)

    modo = "per donatore" if a.per_donatore else "per individuo"
    print(f"{a.comune} · {len(c)} agenti stratificati su {a.variabile} "
          f"· seed {a.seed} · campionamento {modo}\n")
    diagnostica(c, a.variabile)

    if a.mostra:
        print()
        for g in GRUPPI:
            print(f"───── {g} " + "─" * 58)
            for _, x in c[c.gruppo == g].head(a.mostra).iterrows():
                luogo = x.get("quartiere") or x.get("zona")
                print(f"  [{x.latente:>2}] {x.nome}, {int(x.eta_anni)} anni, "
                      f"{luogo}")
                print(f"       {x.titolo_studio[:58]}")
                print(f"       {x.posizione}, {x.settore[:44]}")
            print()

    os.makedirs(a.out, exist_ok=True)
    col = [c_ for c_ in
           ["uid", "gruppo", "latente", "nome", "sesso", "eta", "eta_anni",
            "stato_civile", "cittadinanza", "paese", "background",
            "istruzione", "titolo_studio", "condizione", "settore",
            "posizione", "zona", "quartiere", "via", "donor_id"]
           if c_ in c.columns]
    avq = [c_ for c_ in c.columns
           if c_.isupper() and c_ not in col and not c_.endswith("_num")]
    f = os.path.join(a.out, f"agenti_{a.comune}_{a.variabile}_"
                            f"n{len(c)}_s{a.seed}.json")
    with open(f, "w", encoding="utf-8") as g:
        json.dump({
            "comune": a.comune, "variabile": a.variabile, "n": len(c),
            "seed": a.seed, "gruppi": {k: list(v) for k, v in GRUPPI.items()},
            "solo_occupati": not a.tutti,
            "campionamento": "per_donatore" if a.per_donatore else "per_individuo",
            "generato": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "donatori_distinti": int(c.donor_id.nunique()),
            "agenti": json.loads(c[col + avq].to_json(orient="records")),
        }, g, ensure_ascii=False, indent=1)
    print(f"[salvato] {f}")
    print(f"   {len(col)} campi di profilo + {len(avq)} variabili AVQ")
    print(f"   Il campione si riproduce da (comune, variabile, n, seed): "
          f"e' il\n   livello A, e deve essere identico a ogni esecuzione.")


if __name__ == "__main__":
    main()
