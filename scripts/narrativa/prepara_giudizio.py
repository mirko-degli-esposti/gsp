#!/usr/bin/env python3
"""prepara_giudizio.py — un questionario cieco per valutatori umani.

    python scripts/narrativa/prepara_giudizio.py \\
        dati/agenti/agenti_017029_PUNTIFI10_n120_s0_storie.json \\
        dati/agenti/agenti_017029_PUNTIFI10_n120_s0_neutre.json
    python scripts/narrativa/prepara_giudizio.py A B --n-gruppo 8 --seed 3

Produce due file:

    giudizio_<seed>.html    autonomo, da aprire su telefono o computer
    chiave_<seed>.json      quale storia e' quale — resta a chi conduce

PERCHE' UN GIUDICE UMANO. Il controllo automatico sulle storie cerca
parole, non intenzioni: «finalmente» e «da mesi» tradiscono un giudizio,
ma una storia puo' essere carica di valenza senza usarne nessuna. E
chiedere al modello di valutare le proprie storie e' circolare.

Un lettore che non sappia nulla del progetto e' il solo modo di sapere se
le storie neutre siano davvero neutre e se le altre siano ordinate.

COSA SI CHIEDE, E COSA NO. Non si chiede se la storia sia bella,
credibile, ben scritta o verosimile: si chiede solo cosa ci si legge
dentro. Un racconto brutto che trasmette il livello giusto e' un successo
per questo esperimento; uno bellissimo che non lo trasmette e' un
fallimento.

IL VALUTATORE NON DEVE SAPERE che esistono categorie, quante siano, ne'
che alcune storie sono di controllo. Per questo sono mescolate e il file
non le raggruppa.

LA SECONDA DOMANDA SERVE ALLE NEUTRE — «il racconto esprime un giudizio?»
— ma si chiede per tutte, altrimenti si tradirebbe quali siano.
"""

import argparse
import json
import os
import random
import time

ISTRUZIONI = """Ti chiedo una mano per un lavoro di ricerca.

Qui sotto ci sono <b>{n} brevi racconti</b>. Ognuno e' la voce di una
persona che parla di come vive il proprio quartiere e di quello che ci
succede.

Per ciascuno ti chiedo due cose, e ti bastano pochi secondi.

<p><b>Non sto valutando i racconti.</b> Non mi interessa se siano belli,
credibili, ben scritti o verosimili, e non c'e' una risposta giusta. Mi
interessa solo <i>cosa ci leggi dentro tu</i>.</p>

<p>Se un racconto non ti dice niente sull'argomento, la risposta
<b>«non si capisce»</b> e' una risposta legittima e utile quanto le
altre: usala senza esitare, e' importante che tu non provi a
indovinare.</p>

<p>Vai a istinto, non rileggere. Ci vogliono una ventina di minuti.
Quando hai finito, in fondo c'e' un pulsante che mi manda le risposte su
WhatsApp: non devi copiare niente.</p>"""

HTML = """<!doctype html>
<html lang="it">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Racconti — una valutazione</title>
<style>
  :root {{ --b: #1a1a1a; --g: #666; --l: #e4e4e4; --a: #2b5c8a; }}
  * {{ box-sizing: border-box; }}
  body {{ font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI",
          Roboto, Helvetica, sans-serif; color: var(--b);
          max-width: 620px; margin: 0 auto; padding: 20px 16px 80px; }}
  h1 {{ font-size: 21px; margin: 0 0 18px; font-weight: 600; }}
  .intro {{ background: #f6f6f4; border-radius: 10px; padding: 16px 18px;
            font-size: 15px; margin-bottom: 30px; }}
  .intro p {{ margin: 12px 0 0; }}
  .card {{ border-top: 1px solid var(--l); padding: 26px 0 8px; }}
  .num {{ font-size: 12px; letter-spacing: .09em; color: var(--g);
          text-transform: uppercase; margin-bottom: 10px; }}
  .storia {{ font-size: 16.5px; line-height: 1.65; margin-bottom: 20px;
             white-space: pre-wrap; }}
  .dom {{ font-size: 14.5px; color: #333; margin: 16px 0 9px; }}
  .scala {{ display: flex; flex-wrap: wrap; gap: 5px; }}
  .scala label {{ flex: 1 1 auto; min-width: 38px; }}
  .scala input, .bin input {{ position: absolute; opacity: 0;
                              pointer-events: none; }}
  .scala span, .bin span {{ display: block; text-align: center;
      padding: 9px 4px; border: 1px solid var(--l); border-radius: 7px;
      cursor: pointer; font-size: 14px; background: #fff;
      -webkit-user-select: none; user-select: none; }}
  .scala input:checked + span, .bin input:checked + span {{
      background: var(--a); border-color: var(--a); color: #fff;
      font-weight: 600; }}
  .estremi {{ display: flex; justify-content: space-between;
              font-size: 11.5px; color: var(--g); margin-top: 5px; }}
  .nc {{ margin-top: 8px; }}
  .nc span {{ font-size: 13.5px; padding: 8px; }}
  .bin {{ display: flex; gap: 6px; }}
  .bin label {{ flex: 1; }}
  #fine {{ margin-top: 40px; padding: 20px; background: #f6f6f4;
           border-radius: 10px; }}
  textarea {{ width: 100%; height: 130px; font: 12px/1.4 ui-monospace,
              Menlo, Consolas, monospace; padding: 10px;
              border: 1px solid var(--l); border-radius: 7px; }}
  button {{ background: var(--a); color: #fff; border: 0; padding: 13px 20px;
            border-radius: 8px; font-size: 15px; cursor: pointer;
            width: 100%; margin-bottom: 10px; }}
  button.alt {{ background: #fff; color: var(--a);
                border: 1px solid var(--a); }}
  #stato {{ font-size: 13.5px; color: var(--g); text-align: center;
            margin-bottom: 14px; }}
  .oppure {{ font-size: 12.5px; color: var(--g); text-align: center;
             margin: 14px 0 10px; }}
  #manca {{ font-size: 13px; color: #a04; text-align: center;
            margin-bottom: 10px; display: none; }}
</style>

<h1>Racconti — una valutazione</h1>
<div class="intro">{istruzioni}</div>
<div id="lista"></div>

<div id="fine">
  <div id="stato">—</div>
  <div id="manca"></div>
  <button onclick="wapp()">Ho finito — mandami le risposte</button>
  <div class="oppure">oppure, se preferisci</div>
  <button class="alt" onclick="invia()">Per email</button>
  <button class="alt" onclick="mostra()">Mostra il testo da copiare</button>
  <button class="alt" onclick="scarica()">Scarica come file</button>
  <textarea id="out" readonly placeholder="Se il pulsante non funziona, le
risposte compariranno qui: copiale e rimandamele come preferisci."></textarea>
</div>

<script>
const STORIE = {storie};
const RIF = "{rif}";
const lista = document.getElementById("lista");

STORIE.forEach((s, i) => {{
  const scala = [...Array(11).keys()].map(v =>
    `<label><input type="radio" name="f${{i}}" value="${{v}}"
      onchange="agg()"><span>${{v}}</span></label>`).join("");
  lista.insertAdjacentHTML("beforeend", `
    <div class="card">
      <div class="num">racconto ${{i + 1}} di ${{STORIE.length}}</div>
      <div class="storia">${{s.t}}</div>

      <div class="dom">Leggendo questo racconto, <b>quanta fiducia nel
        Comune</b> diresti che ha questa persona?</div>
      <div class="scala">${{scala}}</div>
      <div class="estremi"><span>0 · nessuna</span><span>10 · piena</span></div>
      <div class="scala nc"><label style="flex:1">
        <input type="radio" name="f${{i}}" value="nc" onchange="agg()">
        <span>non si capisce</span></label></div>

      <div class="dom">Il racconto esprime <b>un giudizio</b> sul Comune?</div>
      <div class="bin">
        <label><input type="radio" name="g${{i}}" value="si"
          onchange="agg()"><span>sì</span></label>
        <label><input type="radio" name="g${{i}}" value="no"
          onchange="agg()"><span>no</span></label>
        <label><input type="radio" name="g${{i}}" value="ns"
          onchange="agg()"><span>non saprei</span></label>
      </div>
    </div>`);
}});

function raccogli() {{
  return STORIE.map((s, i) => {{
    const f = document.querySelector(`input[name=f${{i}}]:checked`);
    const g = document.querySelector(`input[name=g${{i}}]:checked`);
    return {{ id: s.id, fiducia: f ? f.value : null,
              giudizio: g ? g.value : null }};
  }});
}}
function agg() {{
  const r = raccogli();
  const n = r.filter(x => x.fiducia !== null && x.giudizio !== null).length;
  document.getElementById("stato").textContent =
    `${{n}} di ${{STORIE.length}} completi`;
}}
function testo() {{
  return JSON.stringify({{ rif: RIF, quando: new Date().toISOString(),
                           risposte: raccogli() }});
}}
// Il `mailto:` apre l'app di posta con tutto gia' dentro: un tap invece
// di copia-incolla-allega. Il limite pratico degli URL sta intorno ai
// 2000 caratteri su alcuni client, ma le risposte compattate stanno in
// molto meno — venti racconti fanno circa 700 caratteri.
function invia() {{
  controllaVuoti();
  const corpo = encodeURIComponent(
    "Ecco le mie risposte." + String.fromCharCode(10, 10) + testo());
  location.href = `mailto:{posta}?subject=`
    + encodeURIComponent(`Racconti — risposte ${{RIF}}`)
    + `&body=${{corpo}}`;
}}
// WhatsApp accetta un testo precompilato nell'URL. Con `WAPP` vuoto si
// usa lo schema senza destinatario: apre l'app e lascia scegliere la
// chat, cosi' il numero non finisce in una pagina pubblica.
//
// Limite pratico: il testo sta nell'URL e alcune versioni troncano
// intorno ai 4.000 caratteri. Ventiquattro racconti fanno ~900, quindi
// c'e' margine — ma un questionario da cento salterebbe.
function wapp() {{
  controllaVuoti();
  const t = encodeURIComponent(
    "Ecco le mie risposte." + String.fromCharCode(10, 10) + testo());
  const WAPP = "{wapp}";
  location.href = WAPP ? `https://wa.me/${{WAPP}}?text=${{t}}`
                       : `whatsapp://send?text=${{t}}`;
}}
function controllaVuoti() {{
  const v = raccogli().filter(x => x.fiducia === null || x.giudizio === null);
  const m = document.getElementById("manca");
  if (v.length) {{
    m.style.display = "block";
    m.textContent = `Mancano ${{v.length}} racconti. Puoi mandarmele lo `
      + `stesso, ma controlla di non averne saltato qualcuno per sbaglio.`;
  }} else {{ m.style.display = "none"; }}
}}
function mostra() {{
  const o = document.getElementById("out");
  o.value = testo();
  o.select();
  try {{ navigator.clipboard.writeText(o.value); }} catch (e) {{}}
  o.scrollIntoView({{ behavior: "smooth" }});
}}
function scarica() {{
  const b = new Blob([testo()], {{ type: "application/json" }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(b);
  a.download = `risposte_${{RIF}}.json`;
  a.click();
}}
agg();
</script>
</html>
"""


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("storie", help="il json delle storie con latente (B)")
    ap.add_argument("neutre", nargs="?", default=None,
                    help="il json delle storie neutre (D)")
    ap.add_argument("--n-gruppo", type=int, default=8,
                    help="quante per LOW, MED, HIGH")
    ap.add_argument("--n-neutre", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1,
                    help="l'ordine di mescolamento. Semi diversi danno "
                         "questionari diversi sulle stesse storie: utile "
                         "per capire se l'ordine influenzi i giudizi")
    ap.add_argument("--posta", default="mirko.degliesposti@unibo.it")
    ap.add_argument("--whatsapp", default="",
                    help="numero internazionale senza +, es. 393371478090. "
                         "ATTENZIONE: finisce nel sorgente della pagina, "
                         "quindi se la pagina e' pubblica il numero e' "
                         "raccoglibile dai bot. Senza, il pulsante apre "
                         "WhatsApp e lascia scegliere la chat")
    ap.add_argument("--out", default="dati/giudizio")
    a = ap.parse_args()

    rng = random.Random(a.seed)
    with open(a.storie, encoding="utf-8") as f:
        B = json.load(f)["storie"]

    scelte = []
    for g in ("LOW", "MED", "HIGH"):
        s = [x for x in B if x["gruppo"] == g]
        rng.shuffle(s)
        for x in s[:a.n_gruppo]:
            scelte.append({**x, "cond": "B"})
    if a.neutre:
        with open(a.neutre, encoding="utf-8") as f:
            D = json.load(f)["storie"]
        rng.shuffle(D)
        for x in D[:a.n_neutre]:
            scelte.append({**x, "cond": "D"})

    rng.shuffle(scelte)
    rif = f"s{a.seed}n{len(scelte)}"

    # Al questionario va SOLO il testo e un id opaco: gruppo, latente e
    # condizione restano nella chiave. Un identificativo parlante — «B_LOW_3»
    # — nel sorgente della pagina sarebbe visibile a chiunque guardi, e
    # basterebbe una curiosita' per rovinare il cieco.
    fuori = [{"id": f"{a.seed}{i:03d}", "t": x["storia"]}
             for i, x in enumerate(scelte)]
    chiave = [{"id": f"{a.seed}{i:03d}", "uid": x["uid"],
               "cond": x["cond"], "gruppo": x["gruppo"],
               "latente": x["latente"], "profilo": x["profilo_testo"]}
              for i, x in enumerate(scelte)]

    os.makedirs(a.out, exist_ok=True)
    fh = os.path.join(a.out, f"giudizio_{rif}.html")
    fk = os.path.join(a.out, f"chiave_{rif}.json")
    with open(fh, "w", encoding="utf-8") as f:
        f.write(HTML.format(
            istruzioni=ISTRUZIONI.format(n=len(fuori)),
            storie=json.dumps(fuori, ensure_ascii=False), rif=rif,
            posta=a.posta, wapp=a.whatsapp))
    with open(fk, "w", encoding="utf-8") as f:
        json.dump({"rif": rif, "seed": a.seed,
                   "storie_b": os.path.basename(a.storie),
                   "storie_d": (os.path.basename(a.neutre)
                                if a.neutre else None),
                   "creato": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "chiave": chiave}, f, ensure_ascii=False, indent=1)

    import collections
    c = collections.Counter((x["cond"], x["gruppo"]) for x in scelte)
    print(f"{len(fuori)} racconti mescolati · rif {rif}\n")
    for k, v in sorted(c.items()):
        print(f"   {k[0]}  {k[1]:<5} {v}")
    print(f"\n   questionario  {fh}")
    print(f"   chiave        {fk}   ← non mandarla a nessuno")
    print(f"\n   L'HTML e' autonomo: nessun server, nessuna libreria, "
          f"nessun dato\n   che esce. Si apre da file o da un URL, "
          f"funziona da telefono.")
    if a.whatsapp:
        print(f"   Le risposte tornano su WhatsApp al {a.whatsapp} con un "
              f"tap.")
        print(f"\n   !! IL NUMERO E' NEL SORGENTE della pagina. Se la "
              f"pubblichi, e'\n      raccoglibile dai bot che scandagliano "
              f"i siti in cerca di\n      numeri — una delle fonti tipiche "
              f"dello spam. Mandare l'HTML\n      come allegato evita il "
              f"problema, e senza --whatsapp il\n      pulsante apre l'app "
              f"lasciando scegliere la chat.")
    else:
        print(f"   Il pulsante apre WhatsApp senza destinatario: il "
              f"valutatore\n   sceglie la chat. Con --whatsapp NUMERO si "
              f"apre direttamente\n   la tua, al prezzo di pubblicare il "
              f"numero.")
    print(f"   In alternativa: email a {a.posta}, copia, o scarica.")
    print(f"\n   Un sito statico NON PUO' ricevere dati: e' un limite "
          f"strutturale,\n   non una scelta. Per una raccolta automatica "
          f"servirebbe un servizio\n   terzo che vedrebbe le risposte.")


if __name__ == "__main__":
    main()
