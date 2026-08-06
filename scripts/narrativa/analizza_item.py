#!/usr/bin/env python3
"""analizza_item.py — tutti e cinque gli item, non solo quello tarato.

    python scripts/narrativa/analizza_item.py dati/campagne/campagna_*.json
    python scripts/narrativa/analizza_item.py FILE --condizione B

COSA DISTINGUE I CINQUE ITEM.

    fiducia_istituzione   0-10   HA UN LATENTE: e' PUNTIFI10 del donatore
    credibilita           0-10   nessun riferimento
    adeguatezza_info      0-10   nessun riferimento
    emozione              scelta fra 5
    intenzione            scelta fra 5

Le storie sono state generate da `PUNTIFI10`, quindi per il primo item
sappiamo cosa l'agente DOVREBBE rispondere — ed e' la taratura. Sugli
altri quattro nessuna variabile AVQ dice cosa sia vero, quindi non c'e'
taratura da fare.

TRE COSE SI VERIFICANO LO STESSO.

**La storia trasmette una DISPOSIZIONE o una RISPOSTA?** Se credibilita e
adeguatezza correlassero col latente quanto la fiducia, la storia
trasmette un atteggiamento generale verso il Comune. Se solo la prima
correlasse, trasmette la risposta a una domanda specifica — che e' molto
meno.

E' la differenza fra aver costruito un agente con una disposizione e
averne costruito uno addestrato a dire un numero.

**Il test e' pulito per una ragione tecnica.** Nel nostro harness ogni
item parte dal SOLO prompt di sistema: l'agente non sa cosa ha risposto
prima. Una correlazione fra i tre non puo' quindi essere coerenza
conversazionale — e' la stessa storia che produce la stessa disposizione
su domande diverse. A Montelago la narrativa cresceva a ogni turno, e li'
la distinzione non era possibile.

**Le tre scale sono ridondanti?** Se correlassero fra loro sopra 0,9 a
parita' di latente, misurano la stessa cosa e averne tre e' inutile.

**E la traduzione regge?** `emozione` e `intenzione` richiedono di passare
da una disposizione a una SCELTA, non a un numero: e' il test piu' severo.
L'intenzione e' la piu' interessante perche' le opzioni NON sono ordinate
— «non cambiera' nulla per me» e' rassegnazione, «contattare il Comune»
e' attivismo, e un latente basso puo' portare a entrambe. Quale prevalga
dice come il modello immagina la sfiducia.
"""

import argparse
import collections
import json
import math
import statistics as st

NUMERICI = ["fiducia_istituzione", "credibilita", "adeguatezza_info"]
CATEGORIALI = ["emozione", "intenzione"]
GRUPPI = [("LOW", 0, 2), ("MED", 4, 6), ("HIGH", 8, 10)]


def pearson(x, y):
    if len(x) < 3:
        return None
    mx, my = st.mean(x), st.mean(y)
    dx = math.sqrt(sum((a - mx) ** 2 for a in x))
    dy = math.sqrt(sum((b - my) ** 2 for b in y))
    if not dx or not dy:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (dx * dy)


def ranghi(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    return pearson(ranghi(x), ranghi(y)) if len(x) >= 3 else None


def retta(x, y):
    mx, my = st.mean(x), st.mean(y)
    d = sum((a - mx) ** 2 for a in x)
    if d == 0:
        return None, None
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / d
    return my - b * mx, b


def gruppo(l):
    for g, lo, hi in GRUPPI:
        if lo <= l <= hi:
            return g
    return "?"


def numerici(ris, cond, stampa=True):
    """Latente → ciascuna delle tre scale."""
    r = [x for x in ris if x["condizione"] == cond]
    if stampa:
        print(f"\n── condizione {cond} · {len(r)} agenti · scale numeriche\n")
        print(f"   {'item':<22}{'n':>5}{'Spearman':>10}{'guadagno':>10}"
              f"{'LOW':>7}{'MED':>7}{'HIGH':>7}")
    fuori = {}
    for it in NUMERICI:
        v = [(x["latente"], x["risposte"].get(it)) for x in r]
        v = [(l, o) for l, o in v if o is not None]
        if len(v) < 3:
            continue
        lx, ox = [a for a, _ in v], [b for _, b in v]
        _, b = retta(lx, ox)
        fuori[it] = {"n": len(v), "spearman": spearman(lx, ox), "guadagno": b}
        if stampa:
            m = {g: st.mean([o for l, o in v if lo <= l <= hi])
                 for g, lo, hi in GRUPPI
                 if any(lo <= l <= hi for l, _ in v)}
            print(f"   {it:<22}{len(v):>5}{fuori[it]['spearman']:>+10.3f}"
                  f"{b:>10.2f}"
                  + "".join(f"{m.get(g, float('nan')):>7.1f}"
                            for g, _, _ in GRUPPI))
    if stampa and len(fuori) > 1:
        s = [fuori[i]["spearman"] for i in fuori]
        if max(s) - min(s) < 0.15:
            print("\n   le tre scale rispondono al latente in modo simile: "
                  "la storia\n   trasmette una DISPOSIZIONE, non la risposta "
                  "a una domanda")
        else:
            print("\n   le tre scale divergono: la storia trasmette piu' "
                  "l'una che\n   le altre, e va guardato quale")
    return fuori


def fra_scale(ris, cond, stampa=True):
    """Le tre scale fra loro, a parita' di latente.

    Se correlassero sopra 0,9 misurerebbero la stessa cosa, e averne tre
    sarebbe inutile. Il controllo per il latente serve: senza, la
    correlazione sarebbe alta per costruzione, dato che tutte e tre lo
    seguono.
    """
    r = [x for x in ris if x["condizione"] == cond]
    if stampa:
        print(f"\n── condizione {cond} · fra le scale\n")
        print(f"   {'coppia':<44}{'grezza':>9}{'entro gruppo':>14}")
    for i, a in enumerate(NUMERICI):
        for b in NUMERICI[i + 1:]:
            v = [(x["latente"], x["risposte"].get(a), x["risposte"].get(b))
                 for x in r]
            v = [(l, p, q) for l, p, q in v if p is not None and q is not None]
            if len(v) < 3:
                continue
            grezza = pearson([p for _, p, _ in v], [q for _, _, q in v])
            # dentro gruppo: si centra ciascuna variabile sulla media del
            # suo gruppo, cosi' la parte dovuta al latente sparisce
            mg = {}
            for g, lo, hi in GRUPPI:
                s = [(p, q) for l, p, q in v if lo <= l <= hi]
                if s:
                    mg[g] = (st.mean([p for p, _ in s]),
                             st.mean([q for _, q in s]))
            cp = [p - mg[gruppo(l)][0] for l, p, _ in v if gruppo(l) in mg]
            cq = [q - mg[gruppo(l)][1] for l, _, q in v if gruppo(l) in mg]
            dentro = pearson(cp, cq)
            if stampa:
                d = "  —" if dentro is None else f"{dentro:+.3f}"
                print(f"   {f'{a} ↔ {b}':<44}{grezza:>+9.3f}{d:>14}")
    if stampa:
        print("\n   «grezza» include il latente: e' alta per costruzione.\n"
              "   «entro gruppo» toglie il latente: se resta alta, le due\n"
              "   scale condividono anche il rumore — cioe' misurano la\n"
              "   stessa cosa.")


def categoriali(ris, cond, stampa=True):
    r = [x for x in ris if x["condizione"] == cond]
    for it in CATEGORIALI:
        t = collections.defaultdict(collections.Counter)
        for x in r:
            v = x["risposte"].get(it)
            if v:
                t[gruppo(x["latente"])][v] += 1
        if not t:
            continue
        scelte = sorted({s for c in t.values() for s in c})
        if stampa:
            print(f"\n── condizione {cond} · {it}\n")
            corti = {s: (s[:14] + "…" if len(s) > 15 else s) for s in scelte}
            print("   " + " " * 6
                  + "".join(f"{corti[s]:>17}" for s in scelte))
            for g, _, _ in GRUPPI:
                if g not in t:
                    continue
                n = sum(t[g].values())
                print(f"   {g:<6}"
                      + "".join(f"{t[g][s]/n:>17.0%}" for s in scelte))
            print(f"   {'':6}" + "".join(f"{'':>17}" for _ in scelte))
            for s_ in scelte:
                if len(s_) > 15:
                    print(f"      {corti[s_]:<16} = {s_}")
    return


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("campagna")
    ap.add_argument("--condizione", default=None,
                    help="una sola, invece di tutte")
    ap.add_argument("--salta-scale", action="store_true")
    a = ap.parse_args()

    with open(a.campagna, encoding="utf-8") as f:
        d = json.load(f)
    ris = d["risultati"]
    cond = ([a.condizione] if a.condizione
            else sorted({x["condizione"] for x in ris}))

    print(f"{a.campagna}")
    print(f"{d.get('comune')} · {d.get('modello')} · T {d.get('temperatura')}")

    for c in cond:
        numerici(ris, c)
        if not a.salta_scale:
            fra_scale(ris, c)
        categoriali(ris, c)

    print("\n" + "─" * 66)
    print("  L'unico item con un LATENTE e' `fiducia_istituzione`. Sugli\n"
          "  altri non c'e' taratura da fare: si guarda se la storia abbia\n"
          "  trasmesso una disposizione generale o solo quella risposta.")


if __name__ == "__main__":
    main()
