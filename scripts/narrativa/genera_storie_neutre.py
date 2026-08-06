#!/usr/bin/env python3
"""genera_storie_neutre.py — le storie di controllo, condizione D.

    python scripts/narrativa/genera_storie_neutre.py \\
        dati/agenti/agenti_017029_PUNTIFI10_n120_s0.json --da 0 --a 8
    python scripts/narrativa/genera_storie_neutre.py FILE --n-gruppo 14

A COSA SERVE. La condizione C — solo profilo, nessuna narrazione — ha dato
risposte piatte: Spearman +0,06 e trenta agenti su quaranta che rispondono
esattamente 5 anche nel gruppo HIGH. Da cui la conclusione:

    «il profilo demografico da solo non fa agire l'agente in modo
    differenziato»

Ma quella conclusione ha un buco. C piatta esclude che i tratti
demografici DA SOLI producano differenziazione; NON esclude che sia la
presenza di una narrazione QUALSIASI a sbloccare i priors del modello.

Forse l'agente risponde 5 perche' non ha niente da dire, e una storia
qualunque — anche muta sulla fiducia — lo farebbe passare a usare il
profilo.

    C   solo profilo                      piatta, misurata
    D   profilo + storia SENZA valenza    <- questo script
    B   profilo + storia CON il latente   ordinata, Spearman 0,90

**Se D resta piatta**, ogni variazione osservata in B e' attribuibile al
contenuto della narrazione, non alla sua presenza. E' il controllo che
rende il claim difendibile.

**Se D si differenzia**, allora e' la narrazione in quanto tale a
sbloccare i priors demografici, e la conclusione cambia parecchio: il
modello i pregiudizi ce li ha, gli serve solo un pretesto per usarli.

IL PUNTO DELICATO. Una storia neutra che parlasse solo di vita privata —
«mi alzo alle sei, porto i figli a scuola» — sarebbe un controllo DEBOLE:
il modello potrebbe restare a 5 semplicemente perche' nulla riguarda il
Comune.

La storia deve toccare il Comune SENZA valenza: il camion dei rifiuti che
passa, la biblioteca dove si va a leggere, il cartello di un cantiere. Ci
sono narrazione e tema; manca solo la disposizione. E' piu' difficile da
generare, perche' il modello tende a metterci un giudizio.

Per questo lo script CONTROLLA la neutralita' invece di assumerla.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

SISTEMA = """Scrivi brevi racconti in prima persona per un progetto di
ricerca. Ogni racconto e' la voce di una persona che descrive un momento
qualsiasi della propria settimana, in cui capita di incrociare un
servizio o uno spazio del Comune.

REGOLE, in ordine di importanza.

1. I dati anagrafici sono VINCOLI: eta', mestiere, titolo di studio,
   quartiere, stato civile. Non contraddirli. La persona del racconto
   deve essere RICONOSCIBILMENTE quella dei dati.

2. NESSUN GIUDIZIO sul Comune, in nessuna direzione. E' la regola
   principale e la piu' difficile.
   - VIETATO: «finalmente», «come al solito», «ancora una volta»,
     «meno male», «nessuno fa niente», «hanno fatto un buon lavoro»,
     «era ora», «non cambia mai nulla»;
   - VIETATO lamentarsi, apprezzare, sperare, rassegnarsi, ironizzare;
   - VIETATO raccontare una richiesta, una segnalazione, un'attesa o una
     risposta: sono situazioni che HANNO un esito, e l'esito e' un
     giudizio.

   Racconta solo COSA C'E' e COSA SI FA. Il camion dei rifiuti passa alle
   sei. La biblioteca chiude alle sette. Al parco ci sono due panchine
   nuove e un cartello. Il mercato il martedi'.

3. Il Comune deve ESSERCI ma come sfondo, non come interlocutore. La
   persona non ci parla, non lo pensa, non lo valuta: ci passa accanto.

4. Scegli l'ambito coerente col profilo: rifiuti, strade, verde,
   trasporto, mercati, biblioteche, impianti sportivi, cantieri, avvisi,
   illuminazione, parcheggi.
   NON sanita', NON scuola come istituzione, NON inquinamento, NON
   sicurezza.

5. Da cinque a otto righe. Prima persona, presente o passato prossimo,
   italiano piano. Nessun titolo, nessun elenco.

6. Non inventare nomi propri di persone, ne' cifre precise.

La prova che il racconto e' riuscito: chi lo legge NON deve poter dire se
questa persona sia soddisfatta o insoddisfatta del Comune. Non perche'
sia ambivalente — l'ambivalenza e' anch'essa una posizione — ma perche'
la domanda non si pone."""

RICHIESTA = """{profilo}

Scrivi il racconto seguendo le regole. Ricorda: nessun giudizio, nemmeno
implicito. Solo cosa c'e' e cosa si fa."""

# Il giudizio si nasconde nelle congiunzioni e negli avverbi piu' che
# negli aggettivi: «finalmente» e «ancora» dicono piu' di «bello» e
# «brutto». Il controllo cerca quelli.
VALENZA = [
    "finalmente", "come al solito", "ancora una volta", "meno male",
    "era ora", "purtroppo", "per fortuna", "almeno", "nessuno",
    "non cambia", "sempre la stessa", "mai", "eppure", "nonostante",
    "peccato", "speriamo", "chissa", "chissà", "inutile", "vergogna",
    "ho segnalato", "ho chiamato", "ho chiesto", "ho scritto",
    "mi hanno detto", "avrebbero", "promesso", "aspetto da",
    "da mesi", "da anni", "buon lavoro", "efficient", "abbandonat",
]


def controlla(t):
    b = t.lower()
    d = {}
    v = [w for w in VALENZA if w in b]
    if v:
        d["valenza"] = v
    n = len(t.split())
    if n < 45:
        d["corta"] = n
    if n > 200:
        d["lunga"] = n
    return d


def profilo_testo(a):
    p = [f"{a['nome']}, {a.get('eta_anni', a.get('eta'))} anni, "
         f"{'donna' if a.get('sesso') == 'F' else 'uomo'}"]
    if a.get("stato_civile"):
        p.append(str(a["stato_civile"]).replace("_", " "))
    if a.get("titolo_studio"):
        p.append(a["titolo_studio"])
    if a.get("posizione") and a.get("settore"):
        p.append(f"{a['posizione']}, {a['settore']}")
    q = a.get("quartiere") or a.get("zona")
    if q:
        p.append(f"vive nel quartiere {q}")
    if str(a.get("cittadinanza")) != "ITL" and a.get("paese"):
        p.append(f"cittadinanza straniera, {a['paese']}")
    return " · ".join(str(x) for x in p)


def chiama(modello, richiesta, temperatura, chiave, tentativi=3):
    corpo = json.dumps({
        "model": modello, "temperature": temperatura,
        "messages": [{"role": "system", "content": SISTEMA},
                     {"role": "user", "content": richiesta}],
    }).encode("utf-8")
    for k in range(tentativi):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=corpo,
            headers={"Authorization": f"Bearer {chiave}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://github.com/mirko-degli-esposti",
                     "X-Title": "GSP storie neutre"})
        try:
            with urllib.request.urlopen(req, timeout=120) as f:
                d = json.load(f)
            return d["choices"][0]["message"]["content"].strip(), d.get("usage", {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and k < tentativi - 1:
                time.sleep(5 * (k + 1))
                continue
            raise SystemExit(f"OpenRouter {e.code}: {e.read().decode()[:300]}")
        except Exception:                                    # noqa: BLE001
            if k < tentativi - 1:
                time.sleep(5)
                continue
            raise


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("campione")
    ap.add_argument("--modello", default="deepseek/deepseek-chat")
    ap.add_argument("--temperatura", type=float, default=0.8)
    ap.add_argument("--da", type=int, default=0)
    ap.add_argument("--a", type=int, default=None)
    ap.add_argument("--n-gruppo", type=int, default=None,
                    help="quanti per gruppo, invece di --da/--a. La "
                         "condizione D deve coprire i tre gruppi: se il "
                         "modello usasse i priors demografici, li userebbe "
                         "in modo diverso su profili diversi")
    ap.add_argument("--out", default=None)
    ap.add_argument("--pausa", type=float, default=0.7)
    ap.add_argument("--forza", action="store_true")
    a = ap.parse_args()

    with open(a.campione, encoding="utf-8") as f:
        c = json.load(f)
    if a.n_gruppo:
        agenti, visti = [], {}
        for x in c["agenti"]:
            g = x["gruppo"]
            if visti.get(g, 0) < a.n_gruppo:
                agenti.append(x)
                visti[g] = visti.get(g, 0) + 1
    else:
        agenti = c["agenti"][a.da:a.a]
    out = a.out or a.campione.replace(".json", "_neutre.json")

    fatte = {}
    if os.path.exists(out) and not a.forza:
        with open(out, encoding="utf-8") as f:
            fatte = {x["uid"]: x for x in json.load(f).get("storie", [])}
        print(f"[riprendo] {len(fatte)} gia' fatte")

    chiave = os.environ.get("OPENROUTER_API_KEY")
    if not chiave:
        sys.exit("manca OPENROUTER_API_KEY (sta in ~/.config/gsp/env)")

    fuori = list(fatte.values())
    print(f"{len(agenti)} storie NEUTRE · {a.modello} · T {a.temperatura}\n")
    for i, x in enumerate(agenti, 1):
        if x["uid"] in fatte:
            continue
        pt = profilo_testo(x)
        t, uso = chiama(a.modello, RICHIESTA.format(profilo=pt),
                        a.temperatura, chiave)
        d = controlla(t)
        fuori.append({"uid": x["uid"], "gruppo": x["gruppo"],
                      "latente": x["latente"], "profilo_testo": pt,
                      "storia": t, "problemi": d, "uso": uso})
        print(f"  {i:>3}/{len(agenti)}  {x['gruppo']:<5} "
              f"{x['nome'][:24]:<26} "
              f"{'ok' if not d else ' '.join(sorted(d))}")
        if i % 10 == 0:
            _salva(out, c, a, fuori)
        time.sleep(a.pausa)
    _salva(out, c, a, fuori)

    con = [x for x in fuori if "valenza" in x.get("problemi", {})]
    print(f"\n[salvato] {out} · {len(fuori)} storie")
    print(f"   {len(con)} con parole di valenza "
          f"({len(con)/max(len(fuori),1):.0%})")
    if con:
        import collections
        c_ = collections.Counter(w for x in con
                                 for w in x["problemi"]["valenza"])
        for k, v in c_.most_common(8):
            print(f"      {k:<18} {v}")
        print("\n   Il controllo e' GROSSOLANO: cerca parole, non "
              "intenzioni.\n   La neutralita' vera va giudicata leggendo, e "
              "meglio ancora da\n   qualcuno che non sappia cosa "
              "l'esperimento vuole dimostrare.")


def _salva(out, c, a, fuori):
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"campione": os.path.basename(a.campione),
                   "comune": c.get("comune"), "condizione": "D",
                   "modello": a.modello, "temperatura": a.temperatura,
                   "generato": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "sistema": SISTEMA, "richiesta": RICHIESTA,
                   "storie": fuori}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
