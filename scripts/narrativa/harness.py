#!/usr/bin/env python3
"""harness.py — la taratura: tre condizioni, batteria PRE, nessuno stimolo.

    python scripts/narrativa/harness.py \\
        dati/agenti/agenti_017029_PUNTIFI10_n120_s0_storie.json
    python scripts/narrativa/harness.py FILE --condizioni B         # solo una
    python scripts/narrativa/harness.py FILE --da 0 --a 5           # prova

ADATTATO da montelago-explorer/sive_harness.ipynb. Si riusano quasi
intatti lo strato di registrazione, la normalizzazione delle risposte e
il ciclo della batteria; sono rifatti `build_system_prompt` — che non
riceve piu' un campo `persona` — e la lettura del campione.

LE TRE CONDIZIONI (nota_biografia_v2 §7):

    A  persona + storia      SIVE-Montelago. NON implementata: richiede
                             di generare etichette dell'atteggiamento
                             misurato, che e' cio' che il disegno critica
    B  solo storia           il latente passa solo per la narrazione
    C  solo profilo          nessun latente nel prompt
    D  storia NEUTRA         c'e' una narrazione, ma non porta il latente

**B − C** dice quanto la narrazione aggiunge rispetto al profilo nudo.

**D e' il controllo che rende difendibile il claim.** C piatta esclude che
i tratti demografici DA SOLI producano differenziazione; non esclude che
sia la PRESENZA di una narrazione qualsiasi a sbloccare i priors del
modello. Forse l'agente risponde 5 perche' non ha niente da dire, e una
storia muta sulla fiducia lo farebbe passare a usare il profilo.

    se D resta piatta   ogni variazione in B viene dal CONTENUTO della
                        narrazione, non dalla sua presenza
    se D si differenzia e' la narrazione in quanto tale a sbloccare i
                        priors: il modello i pregiudizi ce li ha, gli
                        serve solo un pretesto per usarli

Le storie neutre sono state validate da un giudice umano cieco: sei su
sei hanno ricevuto «non si capisce» alla domanda sulla fiducia e «nessun
giudizio» alla seconda.

E la condizione C e' la piu' scomoda da interpretare: se la fedelta' non
fosse nulla, il modello starebbe inferendo la fiducia da mestiere, titolo
e quartiere — associazioni che sono uno STEREOTIPO DEL MODELLO, non un
dato della popolazione. E' il risultato piu' interessante dei tre proprio
perche' non riguarda la popolazione.

SOLO IL PRE. Nessuno stimolo, nessuna reazione, nessun POST: questa e' la
taratura, e finche' non si sa se gli agenti esibiscano il latente, uno
spostamento POST-PRE sarebbe ininterpretabile. Il codice per lo stimolo
va aggiunto dopo, quando la scelta sara' informata.

Costo: 120 agenti × 2 condizioni × 5 item = 1.200 chiamate. Con lo
stimolo e il POST sarebbero oltre 3.500.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

# ----------------------------------------------------------- lo strumento

EMOZIONI = ["sollievo", "preoccupazione", "rabbia", "speranza",
            "indifferenza"]
INTENZIONI = ["cercare più informazioni sui servizi del quartiere",
              "parlare con i vicini della situazione",
              "partecipare a incontri pubblici sul tema",
              "non cambierà nulla per me",
              "contattare il Comune per avere chiarimenti"]

# LA SCALA E' 0-10, NON 1-10.
#
# SIVE-Montelago usava 1-10 perche' i latenti erano scelti (2, 5, 8) e lo
# zero non serviva. Qui il latente e' `PUNTIFI10` dell'indagine AVQ, che
# va da 0 a 10 — e nel campione di Brescia 27 agenti su 40 del gruppo LOW
# hanno esattamente 0.
#
# Chiedendo «da 1 a 10» a chi ha latente 0 si rende il suo valore
# INESPRIMIBILE: due terzi del gruppo basso non puo' rispondere quello che
# la storia gli ha dato. Non e' un dettaglio di formulazione, e' un
# disallineamento fra strumento e riferimento.
#
# Il prezzo: il confronto con i numeri di SIVE non e' piu' diretto. Vale
# la pena, perche' quel confronto era comunque approssimativo — comune
# diverso, personas diverse, stimolo diverso — mentre l'allineamento
# latente-osservato e' il cuore di questo esperimento.
NUM = ("IMPORTANTE: rispondi SOLO con un numero intero da 0 a 10, "
       "nessuna parola, nessuna spiegazione.")
SCELTA = ("IMPORTANTE: rispondi SOLO con una delle opzioni elencate, "
          "esattamente come scritta, senza aggiungere altro testo.")

# I cinque item di SIVE, con il riferimento territoriale generalizzato.
# `fiducia_istituzione` e' l'unico che ha un LATENTE nella popolazione:
# corrisponde a PUNTIFI10 del donatore AVQ. Sugli altri quattro non c'e'
# taratura da fare, solo coerenza da osservare.
ITEMS = [
    dict(name="fiducia_istituzione", latente=True,
         prompt="Quanto ti fidi del Comune nella gestione dei servizi "
                "del tuo quartiere? (0=nessuna fiducia, 10=piena "
                "fiducia). " + NUM,
         response_type="integer"),
    dict(name="credibilita", latente=False,
         prompt="Quanto ritieni credibile la comunicazione del Comune "
                "sui servizi del tuo quartiere? (0=per nulla credibile, "
                "10=del tutto credibile). " + NUM,
         response_type="integer"),
    dict(name="adeguatezza_info", latente=False,
         prompt="Quanto ritieni adeguata l'informazione che ricevi sui "
                "servizi del tuo quartiere? (0=del tutto inadeguata, "
                "10=molto adeguata). " + NUM,
         response_type="integer"),
    dict(name="emozione", latente=False,
         prompt="Quale emozione descrive meglio il tuo stato d'animo "
                "riguardo ai servizi comunali del tuo quartiere? "
                + SCELTA,
         response_type="choice", choices=EMOZIONI),
    dict(name="intenzione", latente=False,
         prompt="Cosa pensi di fare nei prossimi giorni riguardo ai "
                "servizi del tuo quartiere? " + SCELTA,
         response_type="choice", choices=INTENZIONI),
]

# --------------------------------------------------------------- i prompt

CHIUSA = ("Rispondi sempre in italiano, in prima persona, restando "
          "fedele al tuo carattere e alla tua esperienza. Non rivelare "
          "mai di essere un modello linguistico o un personaggio "
          "simulato.")


def profilo_riga(a):
    """Il livello A e B in prosa. Identico nelle due condizioni: e' cio'
    che le rende confrontabili."""
    p = [f"Sei {a['nome']}, {a.get('eta_anni', a.get('eta'))} anni, "
         f"{'donna' if a.get('sesso') == 'F' else 'uomo'}."]
    if a.get("stato_civile"):
        p.append(f"Stato civile: {str(a['stato_civile']).replace('_',' ')}.")
    if a.get("titolo_studio"):
        p.append(f"Titolo di studio: {a['titolo_studio']}.")
    if a.get("posizione") and a.get("settore"):
        p.append(f"Lavoro: {a['posizione']}, {a['settore']}.")
    elif a.get("condizione"):
        p.append(f"Condizione: {str(a['condizione']).replace('_',' ')}.")
    q = a.get("quartiere") or a.get("zona")
    if q:
        p.append(f"Vivi nel quartiere {q}.")
    if str(a.get("cittadinanza")) != "ITL" and a.get("paese"):
        p.append(f"Hai cittadinanza straniera, {a['paese']}.")
    return " ".join(p)


def build_system_prompt(a, condizione, storia=None):
    """Il prompt di sistema per una condizione.

    NON contiene un campo `persona`. A Montelago c'era — «sfiduciato
    critico», «gioviale fiducioso» — ed era un'etichetta diretta
    dell'atteggiamento che la batteria misura: il prompt diceva
    all'agente due volte cosa pensare, una in forma di aggettivo e una in
    forma di racconto.
    """
    base = profilo_riga(a)
    # B e D hanno la STESSA FORMA — profilo, «La tua esperienza:», storia —
    # e differiscono solo per il contenuto della storia. E' cio' che li
    # rende confrontabili: se il prompt di D fosse strutturato
    # diversamente, una differenza nelle risposte potrebbe venire dalla
    # forma invece che dal contenuto.
    if condizione in ("B", "D"):
        if not storia:
            raise ValueError(f"condizione {condizione} senza storia per "
                             f"{a['uid']}")
        return f"{base}\n\nLa tua esperienza:\n{storia}\n\n{CHIUSA}"
    if condizione == "C":
        return f"{base}\n\n{CHIUSA}"
    raise ValueError(f"condizione '{condizione}' sconosciuta")


# ------------------------------------------------------ normalizzazione

def _norm(s):
    return re.sub(r"[^\w\s]", "", str(s).lower().strip())


def normalize_rating(raw):
    """Un intero 0-10 dalla risposta. (valore, ha_risposto_bene).

    Lo ZERO va riconosciuto: e' il valore di due terzi del gruppo LOW, e
    un'espressione regolare che lo saltasse renderebbe quelle risposte
    illeggibili proprio dove la taratura si misura.
    """
    m = re.search(r"\b(10|[0-9])\b", str(raw))
    if not m:
        return None, False
    v = int(m.group(1))
    # pulito se la risposta e' SOLO il numero: altrimenti il modello ha
    # aggiunto testo, e va saputo quanto spesso accade
    return v, _norm(raw) == str(v)


def normalize_choice(raw, scelte):
    b = _norm(raw)
    for c in scelte:
        if _norm(c) == b:
            return c, True
    for c in scelte:                      # contenuta ma con altro intorno
        if _norm(c) in b:
            return c, False
    for c in scelte:                      # prima parola distintiva
        if _norm(c).split()[0] in b:
            return c, False
    return None, False


# ------------------------------------------------------------- chiamate

CALL_LOG, SURVEY_ROWS = [], []


def call_llm(messages, modello, temperatura, chiave, max_tokens=60,
             agent_id=None, gruppo=None, condizione=None, tentativi=3):
    corpo = json.dumps({"model": modello, "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperatura}).encode("utf-8")
    for k in range(tentativi):
        t0 = time.time()
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=corpo,
            headers={"Authorization": f"Bearer {chiave}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://github.com/mirko-degli-esposti",
                     "X-Title": "GSP harness"})
        try:
            with urllib.request.urlopen(req, timeout=120) as f:
                d = json.load(f)
            u = d.get("usage") or {}
            CALL_LOG.append({
                "momento": datetime.now().isoformat(), "agent_id": agent_id,
                "gruppo": gruppo, "condizione": condizione,
                "modello": modello, "temperatura": temperatura,
                "latenza_s": round(time.time() - t0, 3),
                "tok_in": u.get("prompt_tokens"),
                "tok_out": u.get("completion_tokens")})
            return d["choices"][0]["message"]["content"].strip()
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


def batteria(sistema, a, condizione, modello, temperatura, chiave):
    """I cinque item, ciascuno come turno indipendente sul system prompt.

    Non si accumula la conversazione fra item: ogni domanda parte dal solo
    prompt di sistema. Cosi' la risposta al secondo item non e'
    condizionata da quella al primo — che a Montelago accadeva, perche' la
    narrativa cresceva.
    """
    fuori = {}
    for it in ITEMS:
        testo = it["prompt"]
        if it["response_type"] == "choice":
            testo += " Opzioni: " + ", ".join(it["choices"]) + "."
        raw = call_llm([{"role": "system", "content": sistema},
                        {"role": "user", "content": testo}],
                       modello, temperatura, chiave,
                       agent_id=a["uid"], gruppo=a["gruppo"],
                       condizione=condizione)
        if it["response_type"] == "integer":
            v, ok = normalize_rating(raw)
        else:
            v, ok = normalize_choice(raw, it["choices"])
        SURVEY_ROWS.append({
            "momento": datetime.now().isoformat(), "agent_id": a["uid"],
            "gruppo": a["gruppo"], "latente": a["latente"],
            "condizione": condizione, "modello": modello,
            "item": it["name"], "valore": v, "grezzo": raw, "pulito": ok})
        fuori[it["name"]] = v
    return fuori


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("storie",
                    help="il json di genera_storie, OPPURE quello di "
                         "campiona_agenti se si esegue la sola condizione "
                         "C — che non usa storie")
    ap.add_argument("--neutre", default=None,
                    help="il json di genera_storie_neutre. Serve per la "
                         "condizione D; senza, D viene saltata")
    ap.add_argument("--condizioni", default="BC",
                    help="quali eseguire, es. 'BC', 'BCD', 'D'")
    ap.add_argument("--modello", default="deepseek/deepseek-chat")
    ap.add_argument("--temperatura", type=float, default=0.3,
                    help="BASSA di proposito, ed e' l'uso OPPOSTO a quello "
                         "delle storie: li' la varieta' serve, qui la "
                         "variabilita' e' rumore che si somma a quello che "
                         "si vuole misurare")
    ap.add_argument("--da", type=int, default=0)
    ap.add_argument("--a", type=int, default=None)
    ap.add_argument("--pausa", type=float, default=0.4)
    ap.add_argument("--item", default=None,
                    help="esegui solo questi item, separati da virgola. "
                         "Per un test su una domanda sola gli altri "
                         "quattro sono chiamate sprecate")
    ap.add_argument("--out", default="dati/campagne")
    a = ap.parse_args()

    with open(a.storie, encoding="utf-8") as f:
        S = json.load(f)

    # La condizione C non usa storie: si puo' quindi passare direttamente
    # il campione. Serve per le campagne di solo profilo, che costano poco
    # — nessuna generazione — e permettono di alzare N dove le celle sono
    # troppo sottili per un test.
    solo_campione = "storie" not in S and "agenti" in S
    if solo_campione:
        if set(a.condizioni) - {"C"}:
            sys.exit(f"il file passato e' un CAMPIONE, non delle storie: "
                     f"si puo' eseguire solo la condizione C, non "
                     f"'{a.condizioni}'")
        storie = {}
    else:
        storie = {x["uid"]: x for x in S["storie"]}

    neutre = {}
    if a.neutre:
        with open(a.neutre, encoding="utf-8") as f:
            neutre = {x["uid"]: x for x in json.load(f)["storie"]}
    elif "D" in a.condizioni:
        sys.exit("la condizione D richiede --neutre FILE\n"
                 "  prodotto da genera_storie_neutre.py")

    if solo_campione:
        camp, agenti = a.storie, S["agenti"]
    else:
        camp = os.path.join(os.path.dirname(a.storie),
                            S["campione"]) if S.get("campione") else None
        if not camp or not os.path.exists(camp):
            sys.exit(f"campione non trovato: {camp}\n"
                     "  serve il json di campiona_agenti accanto alle storie")
        with open(camp, encoding="utf-8") as f:
            agenti = json.load(f)["agenti"]
    if storie:
        agenti = [x for x in agenti if x["uid"] in storie]
    if "D" in a.condizioni:
        # Le storie neutre sono in genere meno delle B: si tengono solo gli
        # agenti che le hanno, cosi' il confronto resta APPAIATO — stesso
        # individuo in tutte le condizioni. Confrontare insiemi diversi
        # farebbe rientrare la distorsione demografica del campione, che il
        # disegno appaiato serve proprio a cancellare.
        prima = len(agenti)
        agenti = [x for x in agenti if x["uid"] in neutre]
        if len(agenti) < prima:
            print(f"[appaiato] {len(agenti)} agenti su {prima}: solo quelli "
                  f"che hanno anche la storia neutra")
    agenti = agenti[a.da:a.a]

    chiave = os.environ.get("OPENROUTER_API_KEY")
    if not chiave:
        sys.exit("manca OPENROUTER_API_KEY (sta in ~/.config/gsp/env)")

    global ITEMS
    if a.item:
        voluti = {x.strip() for x in a.item.split(",")}
        ignoti = voluti - {i["name"] for i in ITEMS}
        if ignoti:
            sys.exit(f"item sconosciuti: {sorted(ignoti)}\n"
                     f"  disponibili: {[i['name'] for i in ITEMS]}")
        ITEMS = [i for i in ITEMS if i["name"] in voluti]

    cond = list(a.condizioni)
    tot = len(agenti) * len(cond)
    print(f"{len(agenti)} agenti × {len(cond)} condizioni ({', '.join(cond)}) "
          f"× {len(ITEMS)} item = {tot * len(ITEMS)} chiamate")
    print(f"modello {a.modello} · T {a.temperatura}\n")

    if solo_campione:
        print("[solo profilo] il file passato e' un campione: nessuna "
              "storia, condizione C\n")

    ris, k = [], 0
    for x in agenti:
        for c in cond:
            k += 1
            st_ = None
            if c == "B":
                st_ = storie[x["uid"]]["storia"]
            elif c == "D":
                st_ = neutre[x["uid"]]["storia"]
            sistema = build_system_prompt(x, c, storia=st_)
            r = batteria(sistema, x, c, a.modello, a.temperatura, chiave)
            ris.append({"uid": x["uid"], "gruppo": x["gruppo"],
                        "latente": x["latente"], "condizione": c,
                        "risposte": r})
            d = r.get("fiducia_istituzione")
            seg = "" if d is None else f"{d:>2}  (lat {x['latente']:>2})"
            print(f"  {k:>4}/{tot}  {c}  {x['nome'][:24]:<26} {seg}")
            time.sleep(a.pausa)
        if k % 20 < len(cond):
            _salva(a, S, ris)
    _salva(a, S, ris)

    # --- riepilogo: la fedelta' grezza, senza analisi
    print()
    for c in cond:
        v = [(r["latente"], r["risposte"].get("fiducia_istituzione"))
             for r in ris if r["condizione"] == c]
        v = [(l, o) for l, o in v if o is not None]
        if not v:
            continue
        import statistics as st
        print(f"  condizione {c}: {len(v)} risposte")
        for g, lo, hi in (("LOW", 0, 2), ("MED", 4, 6), ("HIGH", 8, 10)):
            s = [o for l, o in v if lo <= l <= hi]
            if s:
                print(f"     {g:<5} latente {lo}-{hi} → osservato "
                      f"mediana {st.median(s):>4.1f}  media "
                      f"{st.mean(s):>4.1f}  n {len(s)}")
    # La COMPRESSIONE VERSO IL CENTRO non e' un difetto del disegno: e' un
    # comportamento noto degli LLM sulle scale numeriche, che evitano gli
    # estremi. Non si corregge nel prompt — dire «usa tutta la scala»
    # funziona poco e introduce una manipolazione — ma si misura: se la
    # relazione fosse osservato = a + b·latente con b < 1, lo strumento e'
    # lineare con guadagno inferiore a uno, come un termometro che legge in
    # un'altra unita'. La taratura resta valida.
    for c in cond:
        v = [(r["latente"], r["risposte"].get("fiducia_istituzione"))
             for r in ris if r["condizione"] == c]
        v = [(l, o) for l, o in v if o is not None]
        if len(v) < 10:
            continue
        lx = [l for l, _ in v]
        ox = [o for _, o in v]
        ml, mo = sum(lx) / len(lx), sum(ox) / len(ox)
        num = sum((l - ml) * (o - mo) for l, o in v)
        den = sum((l - ml) ** 2 for l in lx)
        if den > 0:
            b = num / den
            print(f"\n  condizione {c}: osservato ≈ {mo - b * ml:.2f} + "
                  f"{b:.2f} × latente")
            if b < 0.6:
                print(f"     guadagno {b:.2f}: forte compressione verso il "
                      f"centro.\n     L'ordine puo' reggere anche cosi' — "
                      f"si guardi Spearman.")

    print("\n   La fedelta' vera si misura in analisi: qui c'e' solo il "
          "segno.\n   Se le tre mediane non sono ordinate, la taratura non "
          "regge.")


def _salva(a, S, ris):
    os.makedirs(a.out, exist_ok=True)
    n = os.path.basename(a.storie).replace("_storie.json", "").replace(
        ".json", "")
    if a.item:
        n += "_" + a.item.replace(",", "-")[:24]
    f = os.path.join(a.out, f"campagna_{n}_{a.condizioni}_"
                            f"t{str(a.temperatura).replace('.','')}.json")
    with open(f, "w", encoding="utf-8") as g:
        json.dump({"storie": os.path.basename(a.storie),
                   "neutre": (os.path.basename(a.neutre)
                              if a.neutre else None),
                   "comune": S.get("comune"), "variabile": S.get("variabile"),
                   "modello": a.modello, "temperatura": a.temperatura,
                   "condizioni": a.condizioni,
                   "momento": datetime.now().isoformat(),
                   "items": [{k: v for k, v in i.items()
                              if k != "prompt"} for i in ITEMS],
                   "risultati": ris, "survey": SURVEY_ROWS,
                   "chiamate": CALL_LOG}, g, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
