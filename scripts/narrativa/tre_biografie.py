#!/usr/bin/env python3
"""tre_biografie.py — la stessa persona raccontata tre volte.

    export OPENROUTER_API_KEY=...          # da ~/.config/gsp/env
    python scripts/narrativa/tre_biografie.py 034027
    python scripts/narrativa/tre_biografie.py 034027 --uid 034027-0012345
    python scripts/narrativa/tre_biografie.py 034027 --modello anthropic/claude-3.5-sonnet

PERCHE' TRE E NON UNA. La tesi da verificare e' che una biografia sia
«una realizzazione plausibile fra molte compatibili con lo stesso
individuo sintetico, non la sua storia» (nota_biografia_v1 §4).

Una biografia sola non la mostra: sembra LA storia di quella persona.
Tre affiancate rendono visibile cosa e' vincolato e cosa e' inventato —
quello che resta uguale e' il livello A, quello che cambia e' il livello
C. Nessuna spiegazione lo comunica altrettanto bene.

IL PROFILO SI SCEGLIE CONTRASTANTE. Un individuo con tutti i valori
medi produce tre testi intercambiabili e non dimostra niente. Il default
cerca un occupato con fiducia istituzionale in tensione — alta nei medici
del SSN, bassa nel governo comunale — perche' e' li' che una narrazione
deve prendere posizione, e tre narrazioni prendono posizioni diverse.

QUESTO SCRIPT NON E' DETERMINISTICO, ed e' l'unico pezzo del progetto a
non esserlo. Non e' un'incoerenza: e' la linea di confine fra cio' che il
progetto garantisce — il profilo, che si riproduce dall'uid — e cio' che
dichiara arbitrario. Per questo salva TUTTO: profilo, prompt, risposte,
modello, temperatura, momento. Senza traccia, un testo generato e' un
testo di cui fra un mese non si sa piu' nulla.
"""

import argparse
import json
import os
import sys
import time

import pandas as pd

# --------------------------------------------------------------- profilo

# Le etichette leggibili delle variabili AVQ che si passano al modello.
# NON tutte le ventitre: molte sono `non_applicabile` per universo, e un
# elenco lungo invita il modello a elencarle invece che a raccontarle.
AVQ_ETICHETTE = {
    "SALUTE": "salute percepita (1 molto bene – 5 molto male)",
    "CRONI": "malattie croniche (1 sì, 2 no)",
    "FUMO": "abitudine al fumo (1 sì, 2 ex, 3 mai)",
    "MH": "indice di salute mentale (0–100, alto = meglio)",
    "BMI": "indice di massa corporea",
    "AMBIENTE": "soddisfazione per l'ambiente della zona (1 molto – 4 per niente)",
    "FIDUCIA": "fiducia interpersonale (1 la gente è degna di fiducia, 2 mai troppa prudenza)",
    "FIDMED": "fiducia nei medici del SSN (0–10)",
    "FIDINF": "fiducia negli infermieri del SSN (0–10)",
    "PUNTIFI10": "fiducia nel governo comunale (0–10)",
    "PUNTIFI8": "fiducia nel governo regionale (0–10)",
    "PUNTIFI1": "fiducia nel Parlamento italiano (0–10)",
    "PUNTIFI2": "fiducia nel sistema giudiziario (0–10)",
    "PUNTIFI3": "fiducia nelle forze dell'ordine (0–10)",
    "PUNTIFI4": "fiducia nei partiti politici (0–10)",
    "PUNTIFI12": "fiducia nei vigili del fuoco (0–10)",
    "VOTOUSL": "giudizio sul servizio ASL ricevuto (0–10)",
}


def scegli(comune, uid=None, seed=0):
    """Un individuo con fiducia istituzionale in TENSIONE.

    Il criterio non e' estetico: una biografia deve spiegare perche' una
    persona si fidi dei medici e non del Comune, e tre biografie lo
    spiegheranno in tre modi diversi. E' li' che il livello C si vede.
    """
    import gsp.individui as I

    d = I.carica(comune)
    if uid:
        r = d[d.uid == uid]
        if r.empty:
            raise LookupError(f"uid {uid} non trovato in {comune}")
        return r.iloc[0]

    m = (d.condizione == "occupato") & d.eta.isin(["35-49", "50-64"])
    for c, lo, hi in (("FIDMED", 7, 10), ("PUNTIFI10", 0, 3)):
        if c in d.columns:
            v = pd.to_numeric(d[c], errors="coerce")
            m &= v.between(lo, hi)
    s = d[m]
    if s.empty:
        print("[avviso] nessun profilo in tensione, ripiego su un occupato "
              "qualsiasi")
        s = d[(d.condizione == "occupato") & d.eta.isin(["35-49", "50-64"])]
    return s.sample(1, random_state=seed).iloc[0]


def profilo(r, comune):
    """Livello A + livello B, in forma leggibile.

    Restituisce (testo, tracciato): il testo va al modello, il tracciato
    serve a sapere dopo cosa gli era stato detto.
    """
    import gsp.individui as I
    import gsp.nomi as N
    from gsp import istruzione as IS, lavoro as L

    nome, cognome = N.nome_agente(r.uid, sesso=r.get("sesso"),
                                  eta=r.get("eta"),
                                  background=r.get("background"),
                                  origine_genitori=r.get("origine_genitori"),
                                  paese=r.get("paese"))
    tit = IS.titolo_agente(r.uid, r.get("istruzione"), sesso=r.get("sesso"),
                           eta=r.get("eta"), comune=comune)
    sett, pos = L.lavoro_agente(r.uid, condizione=r.get("condizione"),
                                sesso=r.get("sesso"), comune=comune,
                                istruzione=r.get("istruzione"))

    via = r.get("via")
    if isinstance(via, str) and via.isupper():
        via = via.title()          # ANNCSU scrive gli odonimi in maiuscolo
    # `ITL` e `FRG` sono codici: a un modello linguistico non dicono
    # niente, e lasciarli lo costringerebbe a indovinare.
    cit = {"ITL": "italiana", "FRG": "straniera"}.get(
        str(r.get("cittadinanza")), r.get("cittadinanza"))

    A = {"nome": f"{nome} {cognome}".title(),
         "eta": int(r.eta_anni) if pd.notna(r.get("eta_anni")) else None,
         "sesso": {"M": "uomo", "F": "donna"}.get(r.get("sesso")),
         "stato_civile": str(r.get("stato_civile", "")).replace("_", " "),
         "quartiere": r.get("quartiere") or r.get("zona"),
         "via": via,
         "cittadinanza": cit,
         "paese di cittadinanza": (r.get("paese")
                                   if str(r.get("cittadinanza")) != "ITL"
                                   else None),
         "condizione": str(r.get("condizione", "")).replace("_", " ")}
    B = {"titolo_studio": tit, "settore": sett, "posizione": pos}
    C = {}
    for k, et in AVQ_ETICHETTE.items():
        v = r.get(k)
        if v is None or pd.isna(v) or str(v) == "non_applicabile":
            continue
        try:
            v = int(float(v))
        except (TypeError, ValueError):
            pass
        C[et] = v

    righe = ["DATI ANAGRAFICI (vincolati dalla popolazione sintetica)"]
    for k, v in A.items():
        if v:
            righe.append(f"  {k}: {v}")
    righe += ["", "ISTRUZIONE E LAVORO (attribuiti da distribuzioni "
                  "censuarie condizionate)"]
    for k, v in B.items():
        if v:
            righe.append(f"  {k}: {v}")
    righe += ["", "RISPOSTE A UN'INDAGINE SU SALUTE, BENESSERE E FIDUCIA"]
    for k, v in C.items():
        righe.append(f"  {k}: {v}")
    return "\n".join(righe), {"A": A, "B": B, "AVQ": C}


# ---------------------------------------------------------------- prompt

SISTEMA = """Scrivi biografie brevi di persone italiane, in italiano, per
un progetto di ricerca sulle popolazioni sintetiche.

REGOLE, in ordine di importanza.

1. I dati che ricevi sono VINCOLI, non suggerimenti: non contraddirli,
   non modificarli, non arrotondarli. Se una persona ha 47 anni, ne ha
   47.

2. NON elencare i valori numerici e non tradurli meccanicamente. «Ha
   fiducia 3 nel Comune» e «ha poca fiducia nel Comune» sono entrambi
   sbagliati: il primo e' una tabella, il secondo una parafrasi. Un
   atteggiamento si mostra in cosa una persona fa, dice o evita, non si
   dichiara.

3. Puoi aggiungere dettagli plausibili che i dati non contengono —
   abitudini, oggetti, luoghi, piccoli fatti. DEVI marcarli fra
   parentesi quadre.

   Si marca tutto cio' che un'altra biografia della stessa persona
   potrebbe raccontare diversamente:
     «[va al mercato il sabato]»           inventato, si marca
     «[ha due figli grandi]»               inventato, si marca
     «[da vent'anni nello stesso reparto]» inventato, si marca
   Non si marca cio' che i dati dicono, ne' le conseguenze necessarie:
     «vive a Cittadella»                   e' nei dati
     «ha finito l'universita'»             segue dal titolo di studio
   Nel dubbio, marca.

4. Non inventare datori di lavoro con nomi propri ne' redditi.

5. Il SETTORE e la POSIZIONE sono vincoli; la mansione precisa non c'e'
   nei dati. Se la immagini, marcala fra parentesi quadre come gli altri
   dettagli inventati. NON usare «forse», «probabilmente», «potrebbe
   essere»: un condizionale nel testo fa sembrare che sia la persona a
   non sapere cosa fa, che e' un'altra cosa. Meglio
   «[si occupa di accettazione al pronto soccorso]» che «lavora nel
   settore sanitario, forse come amministrativa».

6. Da otto a dodici righe. Prosa, senza elenchi e senza titoli.

Scrivi una persona, non un profilo."""

RICHIESTA = """Ecco i dati di un individuo sintetico.

{profilo}

Scrivine una breve biografia seguendo le regole."""


def chiama(modello, sistema, richiesta, temperatura, chiave):
    import urllib.error
    import urllib.request

    corpo = json.dumps({
        "model": modello,
        "temperature": temperatura,
        "messages": [{"role": "system", "content": sistema},
                     {"role": "user", "content": richiesta}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=corpo,
        headers={"Authorization": f"Bearer {chiave}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://github.com/mirko-degli-esposti",
                 "X-Title": "GSP tre_biografie"})
    try:
        with urllib.request.urlopen(req, timeout=120) as f:
            d = json.load(f)
    except urllib.error.HTTPError as e:
        sys.exit(f"OpenRouter {e.code}: {e.read().decode()[:300]}")
    return d["choices"][0]["message"]["content"].strip(), d.get("usage", {})


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comune")
    ap.add_argument("--uid", default=None)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--modello", default="deepseek/deepseek-chat")
    ap.add_argument("--temperatura", type=float, default=1.0,
                    help="alta di proposito: la variabilita' e' l'oggetto "
                         "dell'esperimento, non rumore da ridurre")
    ap.add_argument("--seed", type=int, default=None,
                    help="sceglie QUALE individuo, non cosa il modello dice. "
                         "Senza, e' casuale: questo e' uno strumento di "
                         "esplorazione, e vedere sempre la stessa persona "
                         "non esplora. Il seme usato viene stampato e "
                         "salvato, quindi un individuo interessante si "
                         "ritrova.")
    ap.add_argument("--out", default="note/misure")
    ap.add_argument("--solo-profilo", action="store_true",
                    help="mostra cosa si manderebbe e non chiama nulla")
    a = ap.parse_args()

    seme = a.seed if a.seed is not None else int(time.time()) % 100000
    r = scegli(a.comune, a.uid, seme)
    testo, tracciato = profilo(r, a.comune)
    print("=" * 72)
    print(testo)
    print("=" * 72)
    print(f"uid {r.uid} · --seed {seme}  (per ritrovarlo: --uid {r.uid})")
    if a.solo_profilo:
        return

    chiave = os.environ.get("OPENROUTER_API_KEY")
    if not chiave:
        sys.exit("manca OPENROUTER_API_KEY.\n"
                 "  la chiave sta in ~/.config/gsp/env, e .bashrc la carica:\n"
                 "  [ -f ~/.config/gsp/env ] && source ~/.config/gsp/env")

    bio, costo = [], []
    for i in range(a.n):
        t, u = chiama(a.modello, SISTEMA,
                      RICHIESTA.format(profilo=testo), a.temperatura, chiave)
        bio.append(t)
        costo.append(u)
        print(f"\n───── {i + 1} " + "─" * 60 + "\n")
        print(t)
        time.sleep(1)

    os.makedirs(a.out, exist_ok=True)
    f = os.path.join(a.out, f"biografie_{r.uid}_{int(time.time())}.json")
    with open(f, "w", encoding="utf-8") as g:
        json.dump({"uid": str(r.uid), "comune": a.comune, "seed": seme,
                   "modello": a.modello, "temperatura": a.temperatura,
                   "momento": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "profilo": tracciato, "profilo_testo": testo,
                   "sistema": SISTEMA, "richiesta": RICHIESTA,
                   "biografie": bio, "uso": costo}, g,
                  ensure_ascii=False, indent=1)
    print(f"\n[salvato] {f}")
    print("   Il profilo si riproduce dall'uid; le biografie no, e non "
          "devono.\n   Guardare cosa resta uguale fra le tre: quello e' il "
          "livello A.")


if __name__ == "__main__":
    main()
