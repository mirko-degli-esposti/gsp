#!/usr/bin/env python3
"""harness_scelta.py — l'esperimento sui priors: profilo nudo, due item.

    python scripts/narrativa/harness_scelta.py dati/agenti/agenti_scelta_n426_s0.json
    python scripts/narrativa/harness_scelta.py FILE --da 0 --a 5      # prova
    python scripts/narrativa/harness_scelta.py FILE --modello openai/gpt-4o-mini

ADATTATO da harness.py (SIVE). Si riusano intatti `call_llm` con il
CALL_LOG, la cascata di `normalize_choice`, il log piatto SURVEY_ROWS;
dal generatore di storie si prende il pattern di RIPRESA (che l'harness
non aveva, e su ~2.600 chiamate per modello serve). Sono rifatti il
profilo — che non contiene `condizione`, l'ESITO — e gli item.

NEL LESSICO SIVE QUESTO E' TUTTO CONDIZIONE C: solo profilo, nessuna
storia, nessun latente. Cio' che a Brescia era il controllo qui e' la
misura: i priors del modello sono l'oggetto, non il confondimento.

DUE ITEM INDIPENDENTI, non un JSON unico. Se il modello scrivesse
scelta e probabilita' nella stessa risposta, la seconda sarebbe
coerentizzata alla prima per costruzione autoregressiva: si misurerebbe
P(universita' | la propria scelta appena dichiarata), non il prior.
Ogni item riparte dal solo prompt di sistema, come nella batteria SIVE.

LA CORNICE E' DI STATO, NON DI SCELTA (decisione (a), nota §7b): «la tua
situazione per ottobre» vale per il 19enne appena diplomato come per il
22enne al terzo anno, e combacia col benchmark interno, che e' una
quantita' di bin. Il sottocampione dei 19enni da' gratis la lettura
tipo-passaggio.

TRE REPLICHE per agente (pavimento di rumore), e la ROTAZIONE delle
opzioni segue la replica: l'unico controllo di posizione che serve, a
costo zero. T 0,3 — bassa, come nelle risposte SIVE: qui la variabilita'
e' rumore che si somma a quello che si vuole misurare.

IPOTESI REGISTRATE PRIMA DEI DATI (nota_campione_diplomati_v1 §6):
  H1  beta(diploma) LLM > reale        (associazione narrata)
  H2  beta(genitori) LLM < reale       (regolarita' poco raccontata)
  H3  beta(eta') < 0 su prob           (come nel reale)
  H4  possibile mutismo categoriale di GPT/Haiku (registro SIVE §10):
      se accade, il continuo resta la misura. Muto, non neutro.
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

# Etichette corte e distinguibili anche alla prima parola: la cascata di
# normalize_choice usa l'inclusione e la prima parola come ripieghi, e
# «iscrivermi a X» / «iscrivermi a Y» collasserebbero.
SCELTE = ["università", "ITS o altra formazione",
          "lavoro o ricerca di un lavoro", "altro"]

NUM100 = ("IMPORTANTE: rispondi SOLO con un numero intero da 0 a 100, "
          "nessuna parola, nessuna spiegazione.")
SCELTA = ("IMPORTANTE: rispondi SOLO con una delle opzioni elencate, "
          "esattamente come scritta, senza aggiungere altro testo.")

# Nessun verbo di intenzione, nessuna valutazione: la versione qui del
# «senza numeri» delle storie. La domanda chiede uno STATO.
ITEMS = [
    dict(name="situazione",
         prompt="E' la fine dell'estate. Qual e' la tua situazione piu' "
                "probabile per il prossimo ottobre? " + SCELTA,
         response_type="choice", choices=SCELTE),
    dict(name="prob_universita",
         prompt="Da 0 a 100, quanto e' probabile che il prossimo ottobre "
                "tu sia iscritto/a all'università? (0 = per niente "
                "probabile, 100 = certo). " + NUM100,
         response_type="integer"),
]

# --------------------------------------------------------------- i prompt

# «situazione ed esperienza», non «carattere»: questi agenti un carattere
# non ce l'hanno — niente latente, niente storia — e chiederne la
# fedelta' inviterebbe il modello a inventarne uno.
CHIUSA = ("Rispondi sempre in italiano, in prima persona, restando "
          "coerente con la tua situazione e la tua esperienza. Non "
          "rivelare mai di essere un modello linguistico o un personaggio "
          "simulato.")

# resa leggibile delle categorie di istruzione dei genitori
ISTR_RESA = {
    "nessun_titolo": "nessun titolo di studio",
    "elementare": "la licenza elementare",
    "media": "la licenza media",
    "diploma": "un diploma di scuola superiore",
    "laurea": "una laurea",
    "post_laurea": "un titolo post-laurea",
    "laurea_o_its": "una laurea o un titolo ITS",
}


def _istr(v):
    return ISTR_RESA.get(str(v), str(v).replace("_", " "))


def profilo_riga(x, nomi_comune):
    """Il profilo congelato: nome, eta', luogo, famiglia, origine,
    titolo alla foglia, titolo dei genitori. NIENTE condizione (esito),
    niente lavoro (ramo debole), niente AVQ."""
    ORIG_MUTI = {"non_applicabile", "entrambi_italiani", "nd", "None", ""}

    nome = str(x["nome"]).title() if str(x["nome"]).isupper() else x["nome"]
    cogn = str(x.get("cognome", ""))
    cogn = cogn.title() if cogn.isupper() else cogn
    fr = x.get("fratelli") or 0
    conv = "con i tuoi genitori" if len(x.get("genitori", [])) > 1 else (
        "con tua madre" if x.get("genitori")
        and x["genitori"][0].get("sesso") == "F" else "con tuo padre")
    if fr:
        conv += (f" e {fr} " + ("fratello o sorella" if fr == 1
                                else "fra fratelli e sorelle"))
    p = [f"Sei {nome} {cogn}".strip()
         + f", hai {x['eta_anni']} anni e vivi a "
         f"{nomi_comune.get(x['comune'], x['comune'])}"
         + (f", nel quartiere {x['quartiere']}" if x.get("quartiere")
            else "") + f", {conv}."]
    if str(x.get("cittadinanza", "ITL")) not in ("ITL", "italiana") \
            and x.get("paese"):
        p.append(f"Hai cittadinanza straniera, {x['paese']}.")
    elif str(x.get("origine_genitori")) not in ORIG_MUTI \
            and x.get("origine_genitori"):
        p.append(f"Sei {'nata' if x['sesso']=='F' else 'nato'} in Italia "
                 f"da genitori di origine "
                 f"{str(x['origine_genitori']).replace('_', ' ')}.")

    p.append(f"Titolo di studio: {x['titolo_dettaglio']}.")
    for g in x.get("genitori", []):
        chi = "Tua madre" if g.get("sesso") == "F" else "Tuo padre"
        p.append(f"{chi} ha {_istr(g.get('istruzione'))}.")
    return " ".join(p)


def build_system_prompt(x, nomi_comune):
    return f"{profilo_riga(x, nomi_comune)}\n\n{CHIUSA}"


# ------------------------------------------------------ normalizzazione

import unicodedata

def _norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", "", s.lower().strip())


def normalize_rating_100(raw):
    """Un intero 0-100. (valore, pulito). Lo ZERO va riconosciuto, come
    sulla scala 0-10: «0» e' una risposta legittima e frequente."""
    m = re.search(r"\b(100|\d{1,2})\b", str(raw))
    if not m:
        return None, False
    v = int(m.group(1))
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
             agent_id=None, cella=None, replica=None, tentativi=3):
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
                     "X-Title": "GSP harness_scelta"})
        try:
            with urllib.request.urlopen(req, timeout=120) as f:
                d = json.load(f)
            u = d.get("usage") or {}
            CALL_LOG.append({
                "momento": datetime.now().isoformat(), "agent_id": agent_id,
                "cella": cella, "replica": replica, "modello": modello,
                "temperatura": temperatura,
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


def batteria(sistema, x, replica, modello, temperatura, chiave):
    """I due item, ciascuno come turno indipendente sul system prompt —
    la ragione e' nel docstring in testa. La rotazione delle opzioni
    segue la replica."""
    fuori = {}
    for it in ITEMS:
        testo = it["prompt"]
        if it["response_type"] == "choice":
            r = replica % len(it["choices"])
            opzioni = it["choices"][r:] + it["choices"][:r]
            testo += " Opzioni: " + ", ".join(opzioni) + "."
        raw = call_llm([{"role": "system", "content": sistema},
                        {"role": "user", "content": testo}],
                       modello, temperatura, chiave,
                       agent_id=x["uid"], cella=x["cella"], replica=replica)
        if it["response_type"] == "integer":
            v, ok = normalize_rating_100(raw)
        else:
            v, ok = normalize_choice(raw, it["choices"])
        SURVEY_ROWS.append({
            "momento": datetime.now().isoformat(), "agent_id": x["uid"],
            "cella": x["cella"], "comune": x["comune"],
            "diploma3": x["diploma3"], "gen3": x["gen3"],
            "sesso": x["sesso"], "eta_anni": x["eta_anni"],
            "replica": replica, "modello": modello,
            "item": it["name"], "valore": v, "grezzo": raw, "pulito": ok})
        fuori[it["name"]] = v
    return fuori


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("campione", help="il json di campiona_diplomati")
    ap.add_argument("--modello", default="deepseek/deepseek-chat")
    ap.add_argument("--temperatura", type=float, default=0.3)
    ap.add_argument("--repliche", type=int, default=3)
    ap.add_argument("--da", type=int, default=0)
    ap.add_argument("--a", type=int, default=None)
    ap.add_argument("--pausa", type=float, default=0.4)
    ap.add_argument("--out", default="dati/campagne/scelta")
    ap.add_argument("--solo-diploma3", default=None,
                    choices=["liceo", "tecnico", "professionale"],
                    help="restringe la corsa a una classe (vista sul "
                         "campione, che resta intatto)")    
    a = ap.parse_args()

    with open(a.campione, encoding="utf-8") as f:
        C = json.load(f)
    agenti = C["agenti"]
    if a.solo_diploma3:
        agenti = [x for x in agenti if x["diploma3"] == a.solo_diploma3]
    agenti = agenti[a.da:a.a]

    # nomi leggibili dei comuni, dal registro
    nomi_comune = {}
    try:
        sys.path.insert(0, "src")
        from gsp import common as G
        for c in C.get("comuni", []):
            nomi_comune[c] = G.info(c).get("nome", c)
    except Exception:
        pass
    profili = {x["uid"]: build_system_prompt(x, nomi_comune) for x in agenti}
    chiave = os.environ.get("OPENROUTER_API_KEY")
    if not chiave:
        sys.exit("manca OPENROUTER_API_KEY (sta in ~/.config/gsp/env)")

    # ------- ripresa: cio' che il file d'uscita gia' contiene non si
    # richiama. La chiave e' (uid, replica): la batteria e' atomica.
    fpath = _percorso(a, C)
    fatte, ris = set(), []
    if os.path.exists(fpath):
        with open(fpath, encoding="utf-8") as f:
            v = json.load(f)
        ris = v.get("risultati", [])
        SURVEY_ROWS.extend(v.get("survey", []))
        CALL_LOG.extend(v.get("chiamate", []))
        profili.update(v.get("profili", {}))        # <- NUOVA
        fatte = {(r["uid"], r["replica"]) for r in ris}
        print(f"[riprendo] {len(fatte)} batterie gia' in {fpath}")

    tot = len(agenti) * a.repliche
    print(f"{len(agenti)} agenti × {a.repliche} repliche × {len(ITEMS)} "
          f"item = {tot * len(ITEMS)} chiamate\n"
          f"modello {a.modello} · T {a.temperatura}\n")

    k = len(fatte)
    for x in agenti:
        for rep in range(a.repliche):
            if (x["uid"], rep) in fatte:
                continue
            k += 1
            sistema = build_system_prompt(x, nomi_comune)
            r = batteria(sistema, x, rep, a.modello, a.temperatura, chiave)
            ris.append({"uid": x["uid"], "cella": x["cella"],
                        "comune": x["comune"], "replica": rep,
                        "risposte": r})
            s = r.get("situazione") or "—"
            p = r.get("prob_universita")
            print(f"  {k:>4}/{tot}  r{rep}  {x['nome'][:22]:<24} "
                  f"{s[:24]:<26} p={p if p is not None else '—'}")
            if k % 10 == 0:
                _salva(fpath, a, C, ris, profili)
            time.sleep(a.pausa)
    _salva(fpath, a, C, ris, profili)
    print(f"\n[salvato] {fpath} · {len(ris)} batterie")

    # ------- riepilogo: solo il segno, l'analisi e' altrove
    _riassumi(C, ris)


def _riassumi(C, ris):
    per_uid = {x["uid"]: x for x in C["agenti"]}
    univ = SCELTE[0]          # l'etichetta vera, non una copia cablata
    print(f"\nquota `{univ}` e prob media, per diploma3:")
    for d3 in ("liceo", "tecnico", "professionale"):
        sit = [r["risposte"].get("situazione") for r in ris
               if per_uid[r["uid"]]["diploma3"] == d3]
        prb = [r["risposte"].get("prob_universita") for r in ris
               if per_uid[r["uid"]]["diploma3"] == d3]
        sit = [s for s in sit if s]
        prb = [p for p in prb if p is not None]
        if not sit:
            continue
        qu = sum(s == univ for s in sit) / len(sit)
        pm = sum(prb) / len(prb) if prb else float("nan")
        print(f"   {d3:<15} univ {qu:5.1%}   prob {pm:5.1f}   n {len(sit)}")
    print("per gen3:")
    for g3 in ("bassa", "diploma", "laurea+"):
        sit = [r["risposte"].get("situazione") for r in ris
               if per_uid[r["uid"]]["gen3"] == g3]
        sit = [s for s in sit if s]
        if not sit:
            continue
        qu = sum(s == univ for s in sit) / len(sit)
        print(f"   {g3:<15} univ {qu:5.1%}   n {len(sit)}")
    # il segnale di mutismo (H4): una modalita' sopra il 95% e' la firma
    sit = [r["risposte"].get("situazione") for r in ris
           if r["risposte"].get("situazione")]
    if sit:
        import collections
        top, ntop = collections.Counter(sit).most_common(1)[0]
        if ntop / len(sit) > 0.95:
            print(f"\n!! {ntop}/{len(sit)} risposte = «{top}»: possibile "
                  f"mutismo categoriale (H4). Il continuo e' la misura.")
    print("\n   Benchmark, ipotesi e logit stanno nella nota e "
          "nell'analisi: qui c'e' solo il segno.")


def _percorso(a, C):
    os.makedirs(a.out, exist_ok=True)
    m = a.modello.split("/")[-1].replace(".", "")
    n = os.path.basename(a.campione).replace(".json", "")
    f3 = f"_{a.solo_diploma3}" if a.solo_diploma3 else ""
    return os.path.join(
        a.out, f"campagna_{n}{f3}_{m}_r{a.repliche}_"
               f"t{str(a.temperatura).replace('.', '')}.json")


def _salva(fpath, a, C, ris, profili):
    with open(fpath, "w", encoding="utf-8") as g:
        json.dump({"campione": os.path.basename(a.campione),
                   "comuni": C.get("comuni"), "seed_campione": C.get("seed"),
                   "modello": a.modello, "temperatura": a.temperatura,
                   "repliche": a.repliche,
                   "momento": datetime.now().isoformat(),
                   "items": [{k: v for k, v in i.items() if k != "prompt"}
                             for i in ITEMS],
                   "ipotesi": ["H1 beta(diploma) LLM > reale",
                               "H2 beta(genitori) LLM < reale",
                               "H3 beta(eta) < 0 su prob",
                               "H4 possibile mutismo categoriale",
                               "H5 prob(qualifica) ~ prob(professionale "
                               "non-qualifica): il modello non distingue "
                               "il non-accesso"] + ([
                       "P1 a T=1,0 la quota categoriale migra dalle "
                       "soglie verso le credenze dichiarate a T=0,3",
                       "P2 il primacy di GPT persiste a T alta "
                       "(strutturale), misurato a ciclo completo",
                       "P3 quote T=1,0 per cella ~ prob medie T=0,3 "
                       "entro la risoluzione delle ancore"]
                       if a.temperatura >= 0.9 else []),
                    "profili": profili,
                   "risultati": ris, "survey": SURVEY_ROWS,
                   "chiamate": CALL_LOG}, g, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
