#!/usr/bin/env python3
"""analizza_demo.py — le risposte dipendono dal PROFILO?

    python scripts/narrativa/analizza_demo.py dati/campagne/campagna_*.json
    python scripts/narrativa/analizza_demo.py FILE --item emozione
    python scripts/narrativa/analizza_demo.py FILE --condizione C

LA DOMANDA. In condizione C — solo profilo, nessuna narrazione — il
modello risponde 5 sulle scale numeriche e non usa il latente: Spearman
+0,06, guadagno 0,00.

Ma sui CATEGORIALI la neutralita' sparisce: 62-75% «preoccupazione» e
ZERO «sollievo». Il modello, costretto a nominare un'emozione invece che
a dare un numero, ha una posizione.

Da cui la domanda che questo script risponde:

    quella posizione e' UNIFORME, o dipende dal profilo?

Se l'emozione variasse con eta', sesso o istruzione, il modello USEREBBE
il profilo — solo che sui numeri si astiene e sui categoriali no. E la
piattezza di C sulle scale numeriche non implicherebbe assenza di priors
demografici, ma solo che quei priors non arrivano a spostare un numero.

E' un test piu' sensibile proprio perche' scegliere fra cinque opzioni non
ha una risposta «sicura» come il 5.

PERCHE' IL CHI QUADRO E NON L'OCCHIO. Con 120 agenti, cinque opzioni e
tre fasce d'eta' le celle scendono sotto la decina: differenze del 10-15%
fra righe sono compatibili col caso. Guardare le percentuali senza un
test porta a vedere strutture che non ci sono — ed e' lo stesso errore
dei supporti disuguali, in un'altra forma.

Il test e' approssimato (chi quadro di Pearson, p da una implementazione
della gamma incompleta senza scipy, verificata sui valori tabulati) e va
letto come indicazione: sotto 0,01 c'e' struttura, sopra 0,10 non c'e',
in mezzo servono piu' dati.
"""

import argparse
import collections
import glob
import json
import math

CATEGORIALI = ["emozione", "intenzione"]


# Le fasce: con cinque opzioni e 120 agenti, piu' di tre livelli per
# variabile svuota le celle.
def fascia_eta(a):
    e = a.get("eta_anni")
    if e is None:
        return None
    return "≤34" if e <= 34 else "35-54" if e <= 54 else "55+"


def fascia_istr(a):
    i = str(a.get("istruzione", ""))
    if i in ("nessun_titolo", "elementare", "media"):
        return "bassa"
    if i == "diploma":
        return "media"
    if i in ("laurea_o_its", "post_laurea"):
        return "alta"
    return None


def fascia_pos(a):
    p = str(a.get("posizione", ""))
    return "dipendente" if p.startswith("dipendent") else (
        "autonomo" if p else None)


VARIABILI = {
    "eta": fascia_eta,
    "sesso": lambda a: a.get("sesso"),
    "istruzione": fascia_istr,
    "posizione": fascia_pos,
}


# ------------------------------------------------------------ chi quadro

def _gamma_q(s, x):
    """Q(s,x), la gamma incompleta superiore normalizzata.

    Serve solo per il p-value del chi quadro con s = gradi/2. Serie per
    x < s+1, frazione continua di Lentz altrove: e' il metodo classico, e
    fuori da quei regimi ciascuno dei due perde precisione.
    """
    if x <= 0:
        return 1.0
    if x < s + 1:
        somma = termine = 1.0 / s
        n = 0
        for _ in range(300):
            n += 1
            termine *= x / (s + n)
            somma += termine
            if abs(termine) < abs(somma) * 1e-12:
                break
        return 1.0 - somma * math.exp(-x + s * math.log(x) - math.lgamma(s))
    tiny = 1e-300
    b, c, d = x + 1 - s, 1 / tiny, 1 / (x + 1 - s)
    h = d
    for i in range(1, 300):
        an = -i * (i - s)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        de = d * c
        h *= de
        if abs(de - 1) < 1e-12:
            break
    return math.exp(-x + s * math.log(x) - math.lgamma(s)) * h


def chi2_p(chi2, gradi):
    if gradi <= 0 or chi2 <= 0:
        return 1.0
    return _gamma_q(gradi / 2, chi2 / 2)


def chi2_tabella(t):
    """t = {riga: Counter(colonna)}. (chi2, gradi, p, celle_scarse)."""
    righe = sorted(t)
    col = sorted({c for r in t.values() for c in r})
    if len(righe) < 2 or len(col) < 2:
        return None
    N = sum(sum(t[r].values()) for r in righe)
    tr = {r: sum(t[r].values()) for r in righe}
    tc = {c: sum(t[r][c] for r in righe) for c in col}
    chi2, scarse = 0.0, 0
    for r in righe:
        for c in col:
            att = tr[r] * tc[c] / N
            if att < 5:
                scarse += 1
            if att > 0:
                chi2 += (t[r][c] - att) ** 2 / att
    g = (len(righe) - 1) * (len(col) - 1)
    return chi2, g, chi2_p(chi2, g), scarse


# ------------------------------------------------------------------ main

def analizza(ris, prof, cond, item):
    r = [x for x in ris if x["condizione"] == cond]
    print(f"\n{'═' * 70}\ncondizione {cond} · «{item}» · {len(r)} agenti")
    for nome, f in VARIABILI.items():
        t = collections.defaultdict(collections.Counter)
        for x in r:
            p = prof.get(x["uid"])
            v = x["risposte"].get(item)
            if not p or not v:
                continue
            k = f(p)
            if k is not None:
                t[k][v] += 1
        if len(t) < 2:
            continue
        res = chi2_tabella(t)
        col = sorted({c for x in t.values() for c in x})
        corti = {c: (c[:12] + "…" if len(c) > 13 else c) for c in col}
        print(f"\n  ── per {nome}")
        print("     " + f"{'':10}" + "".join(f"{corti[c]:>15}" for c in col)
              + f"{'n':>6}")
        for k in sorted(t):
            n = sum(t[k].values())
            print(f"     {k:<10}"
                  + "".join(f"{t[k][c] / n:>15.0%}" for c in col)
                  + f"{n:>6}")
        if res:
            chi2, g, p, scarse = res
            segno = ("STRUTTURA" if p < 0.01 else
                     "forse" if p < 0.10 else "nessuna")
            print(f"     χ²={chi2:.1f} g={g} p={p:.3f} → {segno}"
                  + (f"   ({scarse} celle attese <5: il test e' "
                     f"inaffidabile)" if scarse else ""))
        if len(col) > 12:
            for c in col:
                if len(c) > 13:
                    print(f"        {corti[c]:<14} = {c}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("campagna")
    ap.add_argument("--campione", default=None,
                    help="default: dedotto cercando in dati/agenti/")
    ap.add_argument("--item", default=None, help="uno solo")
    ap.add_argument("--condizione", default=None)
    a = ap.parse_args()

    camp = a.campione
    if not camp:
        g = [x for x in glob.glob("dati/agenti/agenti_*_n*_s*.json")
             if "storie" not in x and "neutre" not in x]
        if not g:
            raise SystemExit("campione non trovato: usare --campione")
        camp = sorted(g)[0]
    with open(a.campagna, encoding="utf-8") as f:
        d = json.load(f)
    with open(camp, encoding="utf-8") as f:
        prof = {x["uid"]: x for x in json.load(f)["agenti"]}

    print(f"{a.campagna}")
    print(f"{d.get('modello')} · T {d.get('temperatura')} · "
          f"profili da {camp}")

    cond = ([a.condizione] if a.condizione
            else sorted({x["condizione"] for x in d["risultati"]}))
    item = [a.item] if a.item else CATEGORIALI
    for c in cond:
        for i in item:
            analizza(d["risultati"], prof, c, i)

    print(f"\n{'─' * 70}")
    print("  In condizione C il latente NON e' nel prompt: se una tabella\n"
          "  mostrasse struttura, il modello starebbe usando il PROFILO —\n"
          "  cioe' avrebbe priors demografici che sulle scale numeriche non\n"
          "  arrivano a spostare un numero, ma sui categoriali si'.\n\n"
          "  In condizione B invece la struttura e' ATTESA e non dice nulla\n"
          "  sui priors: eta' e istruzione correlano col latente perche' il\n"
          "  campione e' stratificato su di esso, non perche' il modello le\n"
          "  usi. La condizione da guardare e' C.")


if __name__ == "__main__":
    main()
