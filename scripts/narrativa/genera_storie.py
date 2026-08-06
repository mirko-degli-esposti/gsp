#!/usr/bin/env python3
"""genera_storie.py — le `background_story` che codificano il latente.

    python scripts/narrativa/genera_storie.py \\
        dati/agenti/agenti_017029_PUNTIFI10_n120_s0.json
    python scripts/narrativa/genera_storie.py FILE --da 0 --a 5   # prova
    python scripts/narrativa/genera_storie.py FILE --modello anthropic/claude-3.5-sonnet

COSA FA. Per ogni agente del campione genera una storia in prima persona
che codifica il valore latente di fiducia SENZA nominarlo, e la salva
accanto al profilo.

E' il braccio A dell'esperimento a tre condizioni
(nota_biografia_v2 §7):

    1. persona + storia          SIVE-Montelago, gia' fatto
    2. solo storia               <- questo script
    3. solo profilo fattuale     nessun latente nel prompt

QUATTRO VINCOLI, e ciascuno ha una ragione.

**Dal profilo PIU' il latente**, non dal solo latente. Se la storia
raccontasse una persona diversa da quella del profilo, la condizione 3 —
che riceve solo il profilo — avrebbe un individuo diverso, e il confronto
appaiato salterebbe.

**Senza numeri ne' scale.** La storia deve raccontare fatti da cui la
fiducia si deduce. Se dicesse «non mi fido del Comune» sarebbe
un'etichetta, cioe' esattamente il campo `persona` di Montelago che
questo disegno vuole togliere.

**Una volta sola, e si salva.** Rigenerandola a ogni campagna la
condizione 2 cambierebbe fra un esperimento e l'altro, e i confronti fra
campagne non varrebbero piu'. Lo script rifiuta di sovrascrivere.

**Un latente solo.** `PUNTIFI10` e' la fiducia nel governo comunale; la
batteria SIVE misura cinque cose. Sulle altre quattro non c'e' taratura
da fare, solo coerenza da osservare: la storia NON deve toccarle.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# Il valore esatto si passa al generatore anche se i gruppi sono
# dominati da un valore solo — nel campione di Brescia, 27 zeri su 40 nel
# LOW. Chiedere undici gradazioni riconoscibili sarebbe inutile, perche'
# in analisi quattro casi con valore 1 non sostengono nulla. Ma passarlo
# costa niente e serve se un giorno si campionasse per valore.
SISTEMA = """Scrivi brevi racconti in prima persona per un progetto di
ricerca sulle popolazioni sintetiche. Ogni racconto e' la voce di una
persona che parla di se' e del proprio rapporto con l'amministrazione
comunale.

REGOLE, in ordine di importanza.

1. I dati anagrafici sono VINCOLI: eta', mestiere, titolo di studio,
   quartiere, stato civile. Non contraddirli, non modificarli. La persona
   del racconto deve essere RICONOSCIBILMENTE quella dei dati.

2. Ti viene dato un livello di fiducia nel Comune da 0 a 10. Il racconto
   deve farlo TRASPARIRE senza mai nominarlo:
   - NON scrivere il numero, ne' la parola «fiducia», ne' «mi fido» o
     «non mi fido»;
   - NON usare etichette caratteriali: «sono una persona diffidente»,
     «sono un tipo ottimista» sono vietate;
   - MOSTRA fatti: un'attesa, un servizio, un incontro, una promessa
     mantenuta o disattesa, una cosa vista o sentita. Da quei fatti la
     disposizione deve emergere.

3. L'intensita' conta. 0 e' rassegnazione o rabbia sedimentata; 2 e'
   sfiducia con qualche eccezione; 5 e' ambivalenza, esperienze contrarie
   che convivono; 8 e' fiducia con qualche riserva; 10 e' adesione piena.
   Non serve che il lettore indovini il numero: serve che la direzione e
   la forza siano giuste.

4. Il racconto riguarda il rapporto con l'AMMINISTRAZIONE COMUNALE, e
   deve nascere dalla vita di QUESTA persona. Scegli l'ambito in cui il
   suo profilo la porterebbe davvero a incontrare il Comune:

     manutenzione delle strade e del verde · rifiuti e raccolta
     differenziata · traffico, parcheggi, zone a traffico limitato ·
     trasporto pubblico locale · casa, affitti, edilizia · tasse e
     tributi locali · mercati, licenze, commercio · impianti sportivi,
     biblioteche, centri civici · asili e mense scolastiche · lavori
     pubblici e cantieri · avvisi e comunicazioni del Comune ·
     illuminazione, decoro, spazi pubblici

   NON usare come scena una pratica allo sportello o un permesso da
   richiedere: e' l'incontro piu' ovvio, il meno legato alla persona, e
   raccontato da tutti si assomiglia. Un pensionato che vive nello stesso
   quartiere da trent'anni ha altre occasioni; un commerciante ne ha
   altre ancora; chi ha figli piccoli altre ancora.

   NON parlare di sanita', medici, scuola come istituzione, inquinamento,
   sicurezza o polizia: sono temi che l'indagine misura separatamente.

5. Da cinque a otto righe. Prima persona, presente o passato prossimo,
   italiano piano. Nessun titolo, nessun elenco.

6. Non inventare nomi propri di persone o uffici, ne' cifre precise.

Scrivi la voce di una persona, non la sua scheda."""

RICHIESTA = """{profilo}

Livello di fiducia nel Comune (0 = nessuna, 10 = piena): {latente}

Scrivi il racconto seguendo le regole."""


def profilo_testo(a):
    """Solo il livello A e B, in prosa compatta. Le variabili AVQ NON
    entrano: la storia deve codificare il latente, e altre risposte
    dell'indagine la porterebbero a toccare temi che la batteria misura."""
    p = [f"{a['nome']}, {a.get('eta_anni', a.get('eta'))} anni, "
         f"{'donna' if a.get('sesso') == 'F' else 'uomo'}"]
    if a.get("stato_civile"):
        p.append(str(a["stato_civile"]).replace("_", " "))
    if a.get("titolo_studio"):
        p.append(a["titolo_studio"])
    if a.get("posizione") and a.get("settore"):
        p.append(f"{a['posizione']}, {a['settore']}")
    elif a.get("condizione"):
        p.append(str(a["condizione"]).replace("_", " "))
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
                     "X-Title": "GSP genera_storie"})
        try:
            with urllib.request.urlopen(req, timeout=120) as f:
                d = json.load(f)
            return d["choices"][0]["message"]["content"].strip(), d.get("usage", {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and k < tentativi - 1:
                time.sleep(5 * (k + 1))
                continue
            raise SystemExit(f"OpenRouter {e.code}: {e.read().decode()[:300]}")
        except Exception as e:                               # noqa: BLE001
            if k < tentativi - 1:
                time.sleep(5)
                continue
            raise SystemExit(f"errore: {e}")


# Parole che tradirebbero l'etichetta invece di mostrarla. Il controllo e'
# grossolano di proposito: segnala e non corregge, perche' correggere
# automaticamente nasconderebbe quanto il modello sbaglia.
SPIE = ["mi fido", "non mi fido", "fiducia", "sfiducia", "diffidente",
        "fiducioso", "sfiduciato", "su 10", "livello", "punteggio"]

# Scene che il modello sceglie per default e che, raccontate da tutti, si
# assomigliano. Nel primo giro «ufficio» compariva in 49 storie su 50 e
# «pratica» in 33: la fedelta' misurata avrebbe riguardato il tono, non
# la sostanza, e le storie sarebbero state intercambiabili fra profili.
# Il controllo NON blocca — segnala, e il conteggio finale dice se il
# repertorio si sia allargato davvero.
SCENE_LOGORE = ["sportello", "pratica", "permesso", "ufficio anagrafe",
                "carta d'identita", "carta d'identità", "residenza",
                "modulo", "burocra"]


def controlla(t, latente):
    """Cosa non va nella storia. Non corregge: elenca."""
    b = t.lower()
    fuori = [s for s in SPIE if s in b]
    n = len([r for r in t.split("\n") if r.strip()])
    d = {}
    if fuori:
        d["spie"] = fuori
    if any(c.isdigit() for c in t):
        d["cifre"] = [w for w in t.split() if any(c.isdigit() for c in w)][:5]
    if len(t.split()) < 50:
        d["corta"] = len(t.split())
    if len(t.split()) > 220:
        d["lunga"] = len(t.split())
    logore = [x for x in SCENE_LOGORE if x in b]
    if logore:
        d["scena"] = logore
    return d


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("campione", help="il json prodotto da campiona_agenti")
    ap.add_argument("--modello", default="deepseek/deepseek-chat")
    ap.add_argument("--temperatura", type=float, default=0.8)
    ap.add_argument("--da", type=int, default=0)
    ap.add_argument("--a", type=int, default=None)
    ap.add_argument("--out", default=None,
                    help="default: accanto al campione, con _storie")
    ap.add_argument("--pausa", type=float, default=0.7)
    ap.add_argument("--forza", action="store_true",
                    help="sovrascrive storie gia' generate. Da usare solo "
                         "sapendo che i confronti con le campagne "
                         "precedenti non varranno piu'")
    a = ap.parse_args()

    with open(a.campione, encoding="utf-8") as f:
        c = json.load(f)
    agenti = c["agenti"][a.da:a.a]
    out = a.out or a.campione.replace(".json", "_storie.json")

    fatte = {}
    if os.path.exists(out) and not a.forza:
        with open(out, encoding="utf-8") as f:
            v = json.load(f)
        fatte = {x["uid"]: x for x in v.get("storie", [])}
        print(f"[riprendo] {len(fatte)} storie gia' fatte in {out}")

    chiave = os.environ.get("OPENROUTER_API_KEY")
    if not chiave:
        sys.exit("manca OPENROUTER_API_KEY (sta in ~/.config/gsp/env)")

    fuori, problemi = list(fatte.values()), {}
    print(f"{len(agenti)} agenti · modello {a.modello} · T {a.temperatura}\n")
    for i, x in enumerate(agenti, 1):
        if x["uid"] in fatte:
            continue
        pt = profilo_testo(x)
        t, uso = chiama(a.modello, RICHIESTA.format(profilo=pt,
                                                    latente=x["latente"]),
                        a.temperatura, chiave)
        d = controlla(t, x["latente"])
        if d:
            problemi[x["uid"]] = d
        fuori.append({"uid": x["uid"], "gruppo": x["gruppo"],
                      "latente": x["latente"], "profilo_testo": pt,
                      "storia": t, "problemi": d, "uso": uso})
        stato = "ok" if not d else "  ".join(sorted(d))
        print(f"  {i:>3}/{len(agenti)}  [{x['latente']:>2}] "
              f"{x['nome'][:26]:<28} {stato}")
        if i % 10 == 0:
            _salva(out, c, a, fuori)
        time.sleep(a.pausa)

    _salva(out, c, a, fuori)
    print(f"\n[salvato] {out} · {len(fuori)} storie")
    # quante storie condividono la stessa scena: se una sola domina, il
    # modello leggera' il tipo di evento invece della disposizione
    import collections
    sc = collections.Counter(x for s_ in fuori
                             for x in s_.get("problemi", {}).get("scena", []))
    if sc and fuori:
        print("\nscene ricorrenti (su {} storie):".format(len(fuori)))
        for k, v in sc.most_common(6):
            q = v / len(fuori)
            segno = " !!" if q > 0.4 else ""
            print(f"   {k:<18} {v:>3}  {q:5.0%}{segno}")
        if any(v / len(fuori) > 0.4 for v in sc.values()):
            print("   una scena oltre il 40%: le storie si assomigliano "
                  "troppo, e la\n   fedelta' misurerebbe il registro "
                  "invece della disposizione")

    if problemi:
        gravi = {u: d for u, d in problemi.items()
                 if set(d) - {"scena"}}
        if not gravi:
            print(f"\n{len(problemi)} storie segnalate solo per la scena, "
                  f"nessun problema grave")
            return
        problemi = gravi
        print(f"\n{len(problemi)} storie con problemi — da guardare a mano:")
        for u, d in list(problemi.items())[:10]:
            print(f"   {u}  {d}")
        print("\n   Le spie sono parole che DICHIARANO invece di mostrare.\n"
              "   Se sono molte, il prompt va stretto: e' il difetto che\n"
              "   trasformerebbe la storia in un'etichetta, cioe' nel campo\n"
              "   `persona` che questo disegno vuole togliere.")


def _salva(out, c, a, fuori):
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"campione": os.path.basename(a.campione),
                   "comune": c.get("comune"), "variabile": c.get("variabile"),
                   "seed": c.get("seed"), "modello": a.modello,
                   "temperatura": a.temperatura,
                   "generato": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "sistema": SISTEMA, "richiesta": RICHIESTA,
                   "storie": fuori}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
