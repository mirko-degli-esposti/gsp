#!/usr/bin/env python3
"""analizza.py — la fedelta' di una campagna di taratura.

    python scripts/narrativa/analizza.py dati/campagne/campagna_*.json
    python scripts/narrativa/analizza.py FILE --item credibilita
    python scripts/narrativa/analizza.py FILE --dettaglio

ADATTATO da montelago-explorer/sive_temperature_analysis.ipynb, dove
c'erano `fidelity_by_item`, `stability_matrix`, `delta_series_full`. Qui
manca la stabilita' — richiede due campagne con semi diversi — e c'e' in
piu' il confronto **B − C appaiato**, che e' la misura nuova.

COSA SI GUARDA, in ordine.

**L'ordine prima del valore.** La domanda della taratura e' «l'agente
esibisce il livello che gli e' stato dato», non «lo esibisce con lo
stesso numero». Spearman risponde alla prima, Pearson alla seconda, e la
prima e' quella che conta.

**Il guadagno, che sara' minore di uno.** Gli LLM comprimono le scale
numeriche verso il centro: e' un comportamento noto, non un difetto del
disegno. Se `osservato = a + b·latente` con b ~ 0,5, lo strumento e'
lineare con guadagno dimezzato — come un termometro che legge in
un'altra unita'. La taratura resta valida e il guadagno si dichiara.

**Il confronto appaiato B − C**, sullo stesso agente. E' la misura di
quanto la narrazione aggiunge rispetto al profilo nudo, e il fatto che
sia appaiata la rende immune alla distorsione demografica del campione
(nota_code_puntifi10_v2 §5).

**E la qualita' delle risposte**, che non e' un dettaglio: se il modello
risponde «direi 7 su 10» invece di «7», la normalizzazione ha funzionato
ma il modello non ha seguito l'istruzione, e vale la pena sapere quanto
spesso accade.
"""

import argparse
import collections
import json
import math
import statistics as st
import sys

ITEM_PRINCIPALE = "fiducia_istituzione"
GRUPPI = [("LOW", 0, 2), ("MED", 4, 6), ("HIGH", 8, 10)]


# ---------------------------------------------------------- correlazioni

def pearson(x, y):
    if len(x) < 3:
        return None
    mx, my = st.mean(x), st.mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    dx = math.sqrt(sum((a - mx) ** 2 for a in x))
    dy = math.sqrt(sum((b - my) ** 2 for b in y))
    return num / (dx * dy) if dx and dy else None


def _ranghi(v):
    """Ranghi con media sui pari merito: senza, Spearman su una scala a
    undici valori — dove i pari merito sono la norma — sarebbe distorto."""
    ord_ = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(ord_):
        j = i
        while j + 1 < len(ord_) and v[ord_[j + 1]] == v[ord_[i]]:
            j += 1
        m = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[ord_[k]] = m
        i = j + 1
    return r


def spearman(x, y):
    if len(x) < 3:
        return None
    return pearson(_ranghi(x), _ranghi(y))


def retta(x, y):
    """(intercetta, guadagno) dei minimi quadrati."""
    if len(x) < 3:
        return None, None
    mx, my = st.mean(x), st.mean(y)
    den = sum((a - mx) ** 2 for a in x)
    if den == 0:
        return None, None
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / den
    return my - b * mx, b


# ------------------------------------------------------------- lettura

def carica(f, item):
    with open(f, encoding="utf-8") as g:
        d = json.load(g)
    per = collections.defaultdict(dict)
    for r in d["risultati"]:
        v = r["risposte"].get(item)
        if v is not None:
            per[r["uid"]][r["condizione"]] = v
        per[r["uid"]]["latente"] = r["latente"]
        per[r["uid"]]["gruppo"] = r["gruppo"]
    return d, per


def gruppo_di(l):
    for g, lo, hi in GRUPPI:
        if lo <= l <= hi:
            return g
    return "?"


# --------------------------------------------------------------- stampe

def per_condizione(per, cond, stampa=True):
    v = [(x["latente"], x[c]) for x in per.values()
         for c in [cond] if c in x]
    if len(v) < 3:
        return None
    lx, ox = [a for a, _ in v], [b for _, b in v]
    a_, b_ = retta(lx, ox)
    r = {"n": len(v), "pearson": pearson(lx, ox), "spearman": spearman(lx, ox),
         "intercetta": a_, "guadagno": b_,
         "media": st.mean(ox), "sd": st.pstdev(ox)}
    if stampa:
        print(f"\n── condizione {cond} · {r['n']} agenti")
        print(f"   Spearman {r['spearman']:+.3f}   Pearson "
              f"{r['pearson']:+.3f}   media {r['media']:.2f}  "
              f"sd {r['sd']:.2f}")
        if b_ is not None:
            print(f"   osservato ≈ {a_:.2f} + {b_:.2f} × latente")
        print()
        print(f"   {'gruppo':<6} {'lat':>5} {'n':>4} {'mediana':>8} "
              f"{'media':>7} {'sd':>6}  distribuzione")
        for g, lo, hi in GRUPPI:
            s = [o for l, o in v if lo <= l <= hi]
            if not s:
                continue
            c = collections.Counter(s)
            barra = " ".join(f"{k}×{n}" for k, n in sorted(c.items()))
            print(f"   {g:<6} {f'{lo}-{hi}':>5} {len(s):>4} "
                  f"{st.median(s):>8.1f} {st.mean(s):>7.2f} "
                  f"{st.pstdev(s):>6.2f}  {barra}")
    return r


def appaiato(per, stampa=True):
    """B − C sullo stesso agente."""
    d = [(x["latente"], x["B"] - x["C"]) for x in per.values()
         if "B" in x and "C" in x]
    if len(d) < 3:
        return None
    if stampa:
        print(f"\n── B − C appaiato · {len(d)} agenti")
        print(f"   {'gruppo':<6} {'n':>4} {'media Δ':>9} {'sd':>6} "
              f"{'Δ>0':>5} {'Δ<0':>5}")
        for g, lo, hi in GRUPPI:
            s = [x for l, x in d if lo <= l <= hi]
            if not s:
                continue
            print(f"   {g:<6} {len(s):>4} {st.mean(s):>+9.2f} "
                  f"{st.pstdev(s):>6.2f} {sum(1 for x in s if x > 0):>5} "
                  f"{sum(1 for x in s if x < 0):>5}")
        print("\n   Il segno del Δ deve seguire il gruppo: negativo nel "
              "LOW,\n   positivo nell'HIGH. Se fosse piatto, la narrazione "
              "non\n   aggiunge nulla al profilo.")
    return d


def qualita(d, stampa=True):
    s = d.get("survey", [])
    if not s:
        return
    per_item = collections.defaultdict(lambda: [0, 0, 0])
    for r in s:
        k = per_item[r["item"]]
        k[0] += 1
        k[1] += 1 if r.get("pulito") else 0
        k[2] += 1 if r.get("valore") is None else 0
    if stampa:
        print(f"\n── qualita' delle risposte · {len(s)} totali")
        print(f"   {'item':<22} {'n':>5} {'pulite':>8} {'perse':>7}")
        for k, (n, ok, ko) in sorted(per_item.items()):
            print(f"   {k:<22} {n:>5} {ok / n:>7.0%} {ko:>7}")
        perse = sum(v[2] for v in per_item.values())
        if perse:
            print(f"\n   !! {perse} risposte non interpretabili: se sono "
                  f"molte,\n      la normalizzazione va rivista prima "
                  f"dell'analisi")


def dettaglio(per, n=12):
    print(f"\n── i {n} casi con lo scarto maggiore in condizione B")
    v = [(abs(x["B"] - x["latente"]), x["latente"], x["B"], x.get("C"), u)
         for u, x in per.items() if "B" in x]
    for s, l, b, c, u in sorted(v, reverse=True)[:n]:
        print(f"   {u}  latente {l:>2} → B {b:>2} (scarto {s:>2})"
              f"{'' if c is None else f'  C {c:>2}'}")
    print("\n   Storie che non hanno trasmesso il latente: da leggere con\n"
          "   leggi_storie.py --nudo e capire se il difetto sia nella\n"
          "   storia o nella risposta.")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("campagna")
    ap.add_argument("--item", default=ITEM_PRINCIPALE)
    ap.add_argument("--dettaglio", action="store_true")
    a = ap.parse_args()

    d, per = carica(a.campagna, a.item)
    cond = sorted({r["condizione"] for r in d["risultati"]})
    print(f"{a.campagna}")
    print(f"{d.get('comune')} · {d.get('modello')} · T "
          f"{d.get('temperatura')} · item «{a.item}»")
    print(f"{len(per)} agenti · condizioni {', '.join(cond)}")

    ris = {c: per_condizione(per, c) for c in cond}
    if len(cond) > 1 and "B" in cond and "C" in cond:
        appaiato(per)
    qualita(d)
    if a.dettaglio:
        dettaglio(per)

    # --- il verdetto, in tre righe
    print("\n" + "─" * 62)
    b = ris.get("B")
    if b and b["spearman"] is not None:
        s = b["spearman"]
        if s > 0.6:
            g = "la narrazione trasmette il latente"
        elif s > 0.3:
            g = "trasmissione debole ma presente"
        else:
            g = "la narrazione NON trasmette il latente"
        print(f"  B: Spearman {s:+.2f} — {g}")
        if b["guadagno"] and b["guadagno"] < 0.6:
            print(f"     guadagno {b['guadagno']:.2f}: compressione verso "
                  f"il centro,\n     attesa e non problematica se l'ordine "
                  f"regge")
    c = ris.get("C")
    if c and c["spearman"] is not None:
        s = c["spearman"]
        if abs(s) < 0.2 and c["sd"] < 1.2:
            g = ("il profilo da solo non fa agire l'agente in modo "
                 "differenziato")
        elif s > 0.3:
            g = ("ATTENZIONE: il modello inferisce dal profilo. E' uno "
                 "stereotipo\n     suo, non un dato della popolazione")
        else:
            g = "segnale debole dal profilo"
        print(f"  C: Spearman {s:+.2f}, sd {c['sd']:.2f} — {g}")


if __name__ == "__main__":
    main()
