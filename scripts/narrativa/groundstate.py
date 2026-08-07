#!/usr/bin/env python3
"""groundstate.py — cosa il modello porta di suo, prima del profilo.

    python scripts/narrativa/groundstate.py --livello 0
    python scripts/narrativa/groundstate.py --livello 0,1 --n 80
    python scripts/narrativa/groundstate.py --livello 0,1,2 \\
        --modelli deepseek/deepseek-chat,openai/gpt-4o-mini

LA DOMANDA. Le campagne hanno mostrato che in condizione C — solo profilo,
nessuna narrazione — il modello risponde 5 sulle scale numeriche ma NON e'
neutro sui categoriali: 62-75% «preoccupazione», zero «sollievo». E su 600
agenti l'emozione dipende dal SESSO (chi2 71,6) e dall'ISTRUZIONE (36,3),
non dall'eta' (p 0,28).

Quindi il profilo sposta le risposte. Ma di quanto, rispetto a cosa, e
sono effetti indipendenti o si sommano?

Serve un riferimento: **cosa risponde il modello quando non c'e' nessuno.**
Tutto il resto si misura come scostamento da li'.

IL DISEGNO, in tre livelli e senza fattoriale completo.

    livello 0   nessun profilo, solo la domanda
                il vero zero: 1 cella

    livello 1   UN attributo alla volta, gli altri assenti
                «Sei una donna.» e nient'altro
                effetto principale isolato: 10 celle

    livello 2   solo le interazioni sospette — sesso x istruzione,
                le due con effetto forte: 6 celle

Il fattoriale completo (sesso x eta' x istruzione x posizione x settore)
farebbe 756 celle, e il settore da solo le fa esplodere. Ma la domanda non
e' «qual e' la risposta per ogni combinazione»: e' quanto ciascun
attributo sposta e se gli attributi interagiscono. Per quello bastano 17
celle.

PERCHE' UN PROFILO CON SOLO IL SESSO. «Sei una donna.» non e' una persona,
ed e' il punto: elimina ogni confondimento. Se sposta la risposta rispetto
al livello 0, l'effetto e' quello e nient'altro. Un profilo realistico
mescolerebbe sesso, eta' e mestiere senza modo di separarli.
"""

import argparse
import collections
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request

EMOZIONI = ["sollievo", "preoccupazione", "rabbia", "speranza",
            "indifferenza"]

DOMANDA = ("Quale emozione descrive meglio il tuo stato d'animo riguardo "
           "ai servizi comunali del tuo quartiere? "
           "IMPORTANTE: rispondi SOLO con una delle opzioni elencate, "
           "esattamente come scritta, senza aggiungere altro testo. "
           "Opzioni: " + ", ".join(EMOZIONI) + ".")

CHIUSA = ("Rispondi sempre in italiano, in prima persona. Non rivelare "
          "mai di essere un modello linguistico o un personaggio "
          "simulato.")

# Le modalita' del livello 1. Ciascuna e' una frase sola: il profilo NON
# deve contenere altro, o l'effetto non sarebbe isolato.
LIVELLO1 = {
    "sesso": {"F": "Sei una donna.", "M": "Sei un uomo."},
    "eta": {"giovane": "Hai 28 anni.", "adulto": "Hai 45 anni.",
            "anziano": "Hai 68 anni."},
    "istruzione": {"bassa": "Hai la licenza media.",
                   "media": "Hai un diploma di scuola superiore.",
                   "alta": "Hai una laurea."},
    "posizione": {"dipendente": "Sei un lavoratore dipendente.",
                  "autonomo": "Sei un lavoratore autonomo."},
}

# Il livello 2 incrocia solo le due variabili con effetto forte misurato.
# Aggiungerne altre moltiplicherebbe le celle senza rispondere a una
# domanda che ci si e' posti.
LIVELLO2 = [("sesso", "istruzione")]


def prompt(pezzi):
    """Il prompt di sistema. Con `pezzi` vuoto e' il livello 0."""
    if not pezzi:
        # Nemmeno «Sei una persona»: qualunque frase e' gia' un attributo.
        # Resta solo l'istruzione di formato, che serve al parsing.
        return CHIUSA
    return " ".join(pezzi) + "\n\n" + CHIUSA


def celle(livelli, n):
    """(etichetta, {var: modalita'}, prompt) per ogni cella da eseguire."""
    fuori = []
    if 0 in livelli:
        fuori.append(("livello0", {}, prompt([])))
    if 1 in livelli:
        for var, mod in LIVELLO1.items():
            for k, frase in mod.items():
                fuori.append((f"{var}={k}", {var: k}, prompt([frase])))
    if 2 in livelli:
        for a, b in LIVELLO2:
            for ka, fa in LIVELLO1[a].items():
                for kb, fb in LIVELLO1[b].items():
                    fuori.append((f"{a}={ka}+{b}={kb}", {a: ka, b: kb},
                                  prompt([fa, fb])))
    return fuori


def chiama(sistema, modello, chiave, temperatura, tentativi=3):
    corpo = json.dumps({
        "model": modello, "temperature": temperatura, "max_tokens": 30,
        "messages": [{"role": "system", "content": sistema},
                     {"role": "user", "content": DOMANDA}]}).encode()
    for k in range(tentativi):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=corpo,
            headers={"Authorization": f"Bearer {chiave}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://github.com/mirko-degli-esposti",
                     "X-Title": "GSP groundstate"})
        try:
            with urllib.request.urlopen(req, timeout=60) as f:
                return json.load(f)["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and k < tentativi - 1:
                time.sleep(5 * (k + 1))
                continue
            raise SystemExit(f"OpenRouter {e.code}: {e.read().decode()[:200]}")
        except Exception:                                    # noqa: BLE001
            if k < tentativi - 1:
                time.sleep(4)
                continue
            raise
    return None


def normalizza(raw):
    b = str(raw).lower().strip().strip(".")
    for e in EMOZIONI:
        if b == e:
            return e, True
    for e in EMOZIONI:
        if e in b:
            return e, False
    return None, False


# --------------------------------------------------------------- analisi

def _gamma_q(s, x):
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


def chi2_p(chi2, g):
    return 1.0 if g <= 0 or chi2 <= 0 else _gamma_q(g / 2, chi2 / 2)


def tvd(a, b):
    """Quota di massa da spostare: la distanza fra due celle."""
    k = set(a) | set(b)
    na, nb = sum(a.values()) or 1, sum(b.values()) or 1
    return 0.5 * sum(abs(a.get(x, 0) / na - b.get(x, 0) / nb) for x in k)


def riassumi(ris, stampa=True):
    per = collections.defaultdict(collections.Counter)
    for r in ris:
        if r["valore"]:
            per[r["cella"]][r["valore"]] += 1
    if not per:
        return per
    base = per.get("livello0")
    col = [e for e in EMOZIONI if any(e in c for c in per.values())]
    if stampa:
        print(f"\n   {'cella':<26}" + "".join(f"{e[:11]:>13}" for e in col)
              + f"{'n':>6}" + ("      TVD da 0" if base else ""))
        for k in sorted(per, key=lambda x: (x != "livello0", x)):
            c = per[k]
            n = sum(c.values())
            riga = f"   {k:<26}" + "".join(f"{c[e]/n:>13.0%}" for e in col) \
                   + f"{n:>6}"
            if base and k != "livello0":
                riga += f"{tvd(c, base):>14.3f}"
            print(riga)
    return per


def effetti(per, stampa=True):
    """Per ogni variabile: le sue modalita' differiscono fra loro?"""
    if stampa:
        print(f"\n   {'variabile':<14}{'chi2':>9}{'g':>4}{'p':>9}"
              f"{'TVD max':>10}   esito")
    for var in LIVELLO1:
        mod = {k: per[f"{var}={k}"] for k in LIVELLO1[var]
               if f"{var}={k}" in per}
        if len(mod) < 2:
            continue
        col = sorted({e for c in mod.values() for e in c})
        N = sum(sum(c.values()) for c in mod.values())
        tr = {k: sum(c.values()) for k, c in mod.items()}
        tc = {e: sum(c[e] for c in mod.values()) for e in col}
        chi2 = sum((mod[k][e] - tr[k] * tc[e] / N) ** 2 / (tr[k] * tc[e] / N)
                   for k in mod for e in col if tr[k] * tc[e] > 0)
        g = (len(mod) - 1) * (len(col) - 1)
        p = chi2_p(chi2, g)
        t = max(tvd(mod[a], mod[b]) for a in mod for b in mod if a < b)
        e = "EFFETTO" if p < 0.01 else "forse" if p < 0.10 else "nessuno"
        if stampa:
            print(f"   {var:<14}{chi2:>9.1f}{g:>4}{p:>9.3f}{t:>10.3f}   {e}")


def interazioni(per, stampa=True):
    """La cella doppia e' la somma delle due singole?

    Se «donna laureata» fosse la somma di «donna» e «laureata», la sua
    distribuzione starebbe a meta' strada. Se non lo fosse, c'e'
    interazione — e allora l'effetto di un attributo dipende dall'altro.
    """
    fatte = [(a, b) for a, b in LIVELLO2
             if any(k.startswith(f"{a}=") and f"+{b}=" in k for k in per)]
    if not fatte or stampa is False:
        return
    print(f"\n   interazioni — la cella doppia sta fra le due singole?\n")
    print(f"   {'cella':<26}{'TVD da A':>10}{'TVD da B':>10}"
          f"{'atteso*':>10}{'scarto':>9}")
    for a, b in fatte:
        for ka in LIVELLO1[a]:
            for kb in LIVELLO1[b]:
                k = f"{a}={ka}+{b}={kb}"
                if k not in per or f"{a}={ka}" not in per \
                        or f"{b}={kb}" not in per:
                    continue
                ca, cb, cd = per[f"{a}={ka}"], per[f"{b}={kb}"], per[k]
                # media delle due singole: e' la previsione additiva piu'
                # semplice, e basta a vedere se lo scarto sia grande
                med = collections.Counter()
                for e in EMOZIONI:
                    na = sum(ca.values()) or 1
                    nb = sum(cb.values()) or 1
                    med[e] = (ca[e] / na + cb[e] / nb) / 2 * 1000
                print(f"   {k:<26}{tvd(cd, ca):>10.3f}{tvd(cd, cb):>10.3f}"
                      f"{tvd(ca, cb) / 2:>10.3f}{tvd(cd, med):>9.3f}")
    print("\n   *«atteso» e' meta' della distanza fra le due singole: se la\n"
          "    cella doppia stesse esattamente in mezzo, le due TVD\n"
          "    sarebbero entrambe pari a quello. Lo «scarto» misura la\n"
          "    distanza dalla previsione additiva: grande = interazione.")


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--livello", default="0,1",
                    help="quali eseguire: 0, 1, 2 separati da virgola")
    ap.add_argument("--n", type=int, default=80, help="repliche per cella")
    ap.add_argument("--modelli", default="deepseek/deepseek-chat")
    ap.add_argument("--temperatura", type=float, default=1.0,
                    help="ALTA di proposito: qui non si misura una "
                         "risposta ma una DISTRIBUZIONE, e a T bassa il "
                         "modello darebbe sempre la stessa parola")
    ap.add_argument("--out", default="dati/campagne/groundstate")
    ap.add_argument("--pausa", type=float, default=0.25)
    ap.add_argument("--solo-analisi", default=None,
                    help="rilegge un file invece di chiamare")
    a = ap.parse_args()

    if a.solo_analisi:
        with open(a.solo_analisi, encoding="utf-8") as f:
            d = json.load(f)
        for m, ris in d["per_modello"].items():
            print(f"\n{'═'*76}\n{m}")
            per = riassumi(ris)
            effetti(per)
            interazioni(per)
        return

    liv = {int(x) for x in a.livello.split(",")}
    cc = celle(liv, a.n)
    modelli = [x.strip() for x in a.modelli.split(",")]
    tot = len(cc) * a.n * len(modelli)
    print(f"livelli {sorted(liv)} · {len(cc)} celle × {a.n} repliche × "
          f"{len(modelli)} modelli = {tot} chiamate")
    print(f"T {a.temperatura}\n")

    chiave = os.environ.get("OPENROUTER_API_KEY")
    if not chiave:
        sys.exit("manca OPENROUTER_API_KEY (sta in ~/.config/gsp/env)")

    os.makedirs(a.out, exist_ok=True)
    f = os.path.join(a.out, f"gs_l{a.livello.replace(',','')}_n{a.n}.json")
    tutto = {}
    for m in modelli:
        print(f"── {m}")
        ris = []
        for et, var, sis in cc:
            c = collections.Counter()
            for _ in range(a.n):
                raw = chiama(sis, m, chiave, a.temperatura)
                v, pulita = normalizza(raw)
                ris.append({"cella": et, "vars": var, "valore": v,
                            "grezzo": raw, "pulita": pulita})
                if v:
                    c[v] += 1
                time.sleep(a.pausa)
            top = c.most_common(1)
            print(f"   {et:<26} {top[0][0] if top else '?':<16}"
                  f"{top[0][1]/max(sum(c.values()),1):>5.0%}")
            tutto[m] = ris
            with open(f, "w", encoding="utf-8") as g:
                json.dump({"livelli": sorted(liv), "n": a.n,
                           "temperatura": a.temperatura,
                           "domanda": DOMANDA, "chiusa": CHIUSA,
                           "momento": time.strftime("%Y-%m-%dT%H:%M:%S"),
                           "per_modello": tutto}, g,
                          ensure_ascii=False, indent=1)
        print()
        per = riassumi(ris)
        effetti(per)
        interazioni(per)
    print(f"\n[salvato] {f}")


if __name__ == "__main__":
    main()
