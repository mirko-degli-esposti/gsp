#!/usr/bin/env python3
"""indovina_citta.py — il modello sa dove vive l'agente?

    python scripts/narrativa/indovina_citta.py 017029 034027 037006
    python scripts/narrativa/indovina_citta.py 017029 --n 20
    python scripts/narrativa/indovina_citta.py 017029 --con-via

PERCHE'. Il prompt di sistema dell'harness da' il QUARTIERE — «Crocifissa
Di Rosa», «Fiumicello», «Chiesanuova» — ma non il comune ne' la regione.

Restano due situazioni molto diverse, e non sappiamo quale sia la nostra:

  - il modello RICONOSCE il toponimo, e allora attinge a quello che sa
    della citta': la sua amministrazione, la sua storia, i suoi problemi.
    Quella conoscenza e' rumore rispetto a cio' che l'esperimento misura,
    perche' la fiducia dovrebbe venire dal profilo e dalla storia;
  - il modello NON lo riconosce, e il quartiere e' una stringa senza
    contenuto.

Montelago era un comune fittizio proprio per escludere il primo caso.
Omettendo il comune, l'esperimento su Brescia preserva quella proprieta'
— ma per caso, non per progetto, e vale la pena saperlo.

PIU' COMUNI INSIEME. Se il modello riconoscesse Brescia ma non Piacenza,
l'effetto dipenderebbe dalla notorieta' della citta': un bias in piu', e
di quelli che non si sospettano finche' non si guarda.

COSA NON E'. Non e' un item della batteria e non entra nelle campagne: e'
una diagnostica sul prompt. Per questo chiede direttamente, in una forma
che nell'esperimento non comparirebbe mai.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

# La domanda e' diretta di proposito: qui non si misura una disposizione
# ma cosa il modello sa. Chiedere di travestirla renderebbe la risposta
# meno leggibile senza renderla piu' valida.
DOMANDA = ("In quale citta' italiana vivi? Rispondi SOLO con il nome "
           "della citta'. Se non lo sai con ragionevole certezza, "
           "rispondi esattamente: NON SO.")

NOMI = {"017029": "Brescia", "033032": "Piacenza", "034027": "Parma",
        "035033": "Reggio", "036023": "Modena", "037006": "Bologna",
        "037021": "Castenaso", "038008": "Ferrara", "039014": "Ravenna",
        "040012": "Forlì", "099014": "Rimini"}


def profilo(a, con_via=False):
    p = [f"Sei {a['nome']}, {a.get('eta_anni', a.get('eta'))} anni, "
         f"{'donna' if a.get('sesso') == 'F' else 'uomo'}."]
    if a.get("titolo_studio"):
        p.append(f"Titolo di studio: {a['titolo_studio']}.")
    if a.get("posizione") and a.get("settore"):
        p.append(f"Lavoro: {a['posizione']}, {a['settore']}.")
    q = a.get("quartiere") or a.get("zona")
    if q:
        p.append(f"Vivi nel quartiere {q}.")
    if con_via and a.get("via"):
        v = a["via"]
        p.append(f"Abiti in {v.title() if v.isupper() else v}.")
    p.append("Rispondi sempre in italiano, in prima persona. Non rivelare "
             "mai di essere un modello linguistico.")
    return " ".join(p)


def chiama(sistema, modello, chiave, temperatura=0.0):
    corpo = json.dumps({
        "model": modello, "temperature": temperatura, "max_tokens": 30,
        "messages": [{"role": "system", "content": sistema},
                     {"role": "user", "content": DOMANDA}]}).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=corpo,
        headers={"Authorization": f"Bearer {chiave}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://github.com/mirko-degli-esposti",
                 "X-Title": "GSP indovina_citta"})
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as f:
                return json.load(f)["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and k < 2:
                time.sleep(5 * (k + 1))
                continue
            raise SystemExit(f"OpenRouter {e.code}: {e.read().decode()[:200]}")
    return None


def valuta(r, atteso):
    """(esito, testo). Esiti: giusto · sbagliato · non_so."""
    b = re.sub(r"[^\w\s]", " ", str(r).lower())
    if "non so" in b or "non lo so" in b or "non saprei" in b:
        return "non_so", r
    if atteso.lower() in b:
        return "giusto", r
    return "sbagliato", r


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comuni", nargs="+")
    ap.add_argument("--n", type=int, default=12, help="agenti per comune")
    ap.add_argument("--modello", default="deepseek/deepseek-chat")
    ap.add_argument("--con-via", action="store_true",
                    help="aggiungi la via: un indirizzo e' un indizio molto "
                         "piu' forte di un quartiere, e vale la pena sapere "
                         "quanto")
    ap.add_argument("--out", default="dati/campagne/citta")
    ap.add_argument("--pausa", type=float, default=0.4)
    a = ap.parse_args()

    chiave = os.environ.get("OPENROUTER_API_KEY")
    if not chiave:
        sys.exit("manca OPENROUTER_API_KEY (sta in ~/.config/gsp/env)")

    import gsp.individui as I
    import gsp.nomi as N
    from gsp import istruzione as IS, lavoro as L

    fuori = []
    print(f"{a.modello} · {a.n} agenti per comune · "
          f"{'con' if a.con_via else 'senza'} via\n")
    for c in a.comuni:
        d = I.carica(c)
        d = d[d.condizione == "occupato"].sample(a.n, random_state=0)
        esiti = {"giusto": 0, "sbagliato": 0, "non_so": 0}
        risposte = []
        for _, x in d.iterrows():
            nome, cog = N.nome_agente(x.uid, sesso=x.get("sesso"),
                                      eta=x.get("eta"),
                                      background=x.get("background"),
                                      origine_genitori=x.get("origine_genitori"),
                                      paese=x.get("paese"))
            ag = {"nome": f"{nome} {cog}".title(),
                  "eta_anni": x.get("eta_anni"), "sesso": x.get("sesso"),
                  "quartiere": x.get("quartiere") or x.get("zona"),
                  "via": x.get("via"),
                  "titolo_studio": IS.titolo_agente(
                      x.uid, x.get("istruzione"), sesso=x.get("sesso"),
                      eta=x.get("eta"))}
            s, p = L.lavoro_agente(x.uid, condizione=x.get("condizione"),
                                   sesso=x.get("sesso"), comune=c,
                                   istruzione=x.get("istruzione"))
            ag["settore"], ag["posizione"] = s, p
            r = chiama(profilo(ag, a.con_via), a.modello, chiave)
            e, t = valuta(r, NOMI.get(c, c))
            esiti[e] += 1
            risposte.append({"uid": x.uid, "quartiere": ag["quartiere"],
                             "risposta": t, "esito": e})
            time.sleep(a.pausa)
        n = sum(esiti.values())
        print(f"  {NOMI.get(c, c):<11} giusto {esiti['giusto']:>3}/{n}  "
              f"({esiti['giusto']/n:>4.0%})   sbagliato "
              f"{esiti['sbagliato']:>3}   non so {esiti['non_so']:>3}")
        # cosa dice quando sbaglia: se nominasse sempre la stessa citta',
        # sarebbe un default invece di un'inferenza
        sb = [x["risposta"] for x in risposte if x["esito"] == "sbagliato"]
        if sb:
            import collections
            cc = collections.Counter(s[:24] for s in sb)
            print(f"     quando sbaglia: "
                  + " · ".join(f"{k} ×{v}" for k, v in cc.most_common(4)))
        fuori.append({"comune": c, "nome": NOMI.get(c, c), "esiti": esiti,
                      "risposte": risposte})

    os.makedirs(a.out, exist_ok=True)
    f = os.path.join(a.out, f"citta_{'-'.join(a.comuni)}_"
                            f"{'via' if a.con_via else 'quartiere'}.json")
    with open(f, "w", encoding="utf-8") as g:
        json.dump({"modello": a.modello, "con_via": a.con_via,
                   "domanda": DOMANDA,
                   "momento": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "comuni": fuori}, g, ensure_ascii=False, indent=1)
    print(f"\n[salvato] {f}")
    print("\n   Se indovina, il modello porta nell'esperimento quello che sa\n"
          "   della citta' — e quella conoscenza e' rumore rispetto alla\n"
          "   fiducia che si vuole misurare. Se indovina per una citta' e\n"
          "   non per un'altra, l'effetto dipende dalla notorieta'.")


if __name__ == "__main__":
    main()
