"""
gsp.campagna_fetch — consumatore del manifest di campagna (v1.1)

Orchestratore MAGRO: la conoscenza SDMX (flow, spec, download, percorsi
di salvataggio) resta in fetch_comune.py, qui importata, mai copiata.
Questo modulo sa solo: leggere il manifest, scegliere la prossima cella
'mancante', delegare il fetch, controllare l'esito, aggiornare lo stato.

REGOLE DI CONDOTTA (dal disegno v1.1)
- tocca solo celle 'mancante': DIVERGE e 'scaricata' non si ritoccano
- un fallimento di rete lascia la cella 'mancante' (si ritenta), un
  file arrivato ma vuoto/malformato la marca DIVERGE (si guarda)
- stato salvato DOPO ogni cella, scrittura atomica: ammazzabile sempre
- ritmo: pausa fissa fra fetch + backoff sui fallimenti consecutivi;
  dopo MAX_FALLIMENTI consecutivi si ferma da solo (il rate limit non
  si combatte, si rispetta)
"""

import sys
import time
from datetime import datetime
from pathlib import Path


from gsp.campagna import carica, salva, TAVOLE, GSP_ROOT

# fetch_comune.py vive in scripts/, non nel pacchetto: import via path.
sys.path.insert(0, str(GSP_ROOT / "scripts" / "acquisizione"))
from fetch_comune import CORE, fetch_one, output_dir

# Il manifest usa gli id di registro (istat_*), il CORE le chiavi nude:
# mappatura meccanica, verificata all'import — se le due nomenclature
# divergono, si rompe QUI, non a metà campagna (il germe annotato).
assert all(t.removeprefix("istat_") in CORE for t in TAVOLE), \
    "id di manifest senza corrispondente nel CORE di fetch_comune"


# in testa, accanto agli altri import da fetch_comune:
from fetch_prov import fetch_molti, spacchetta, SHADOW


def prossimo_gruppo(m, salta=()):
    """Il prossimo gruppo (provincia, tavola) con celle 'mancante':
    l'unita' di FETCH del canale provinciale. L'unita' di STATO resta
    la cella (comune, tavola). Provincia = prefisso a 3 cifre del
    codice: nessuna semantica regionale, solo aritmetica dei codici.
    Ordine: prima la tavola del comune piu' grande ancora incompleto —
    eredita la politica del manifest (popolazione decrescente)."""
    for cod, c in m["comuni"].items():          # gia' ordinati per pop
        for t in TAVOLE:
            if c["tavole"][t]["stato"] != "mancante":
                continue
            prov = cod[:3]
            if (prov, t) in salta:
                continue
            gruppo = [k for k, v in m["comuni"].items()
                      if k[:3] == prov
                      and v["tavole"][t]["stato"] == "mancante"]
            return prov, t, gruppo
    return None


def campagna_prov(max_query=None):
    """Campagna a canale provinciale: una query per (provincia, tavola),
    file in SHADOW, celle marcate 'shadow'. La promozione a
    data/comuni/ e' un passo SEPARATO (--promuovi), dopo la --valida
    sui file shadow: la directory ufficiale riceve solo validato."""
    fatte, falliti_consecutivi = 0, 0
    saltati, tentativi = set(), {}
    while True:
        m = carica()
        g = prossimo_gruppo(m, saltati)
        if g is None:
            print("campagna: nessun gruppo con celle mancanti")
            return
        prov, t, comuni = g
        name = t.removeprefix("istat_")
        print(f"[{prov}] {name}: {len(comuni)} comuni in una query...")
        try:
            df, xml, terr = fetch_molti(comuni, name)
            esiti = spacchetta(df, xml, terr, comuni, name)
        except Exception as e:
            falliti_consecutivi += 1
            chiave = (prov, t)
            tentativi[chiave] = tentativi.get(chiave, 0) + 1
            print(f"[{prov}] {name}: FALLITO ({e}) — "
                  f"tentativi gruppo: {tentativi[chiave]}, "
                  f"consecutivi: {falliti_consecutivi}")
            if tentativi[chiave] >= 3:
                saltati.add(chiave)
                print(f"[{prov}] {name}: 3 tentativi, salto il gruppo "
                      f"per questa sessione")
            if falliti_consecutivi >= MAX_FALLIMENTI:
                print("mi fermo: il rate limit non si combatte.")
                return
            time.sleep(BACKOFF[min(falliti_consecutivi - 1, len(BACKOFF) - 1)])
            continue

        # esiti per cella: OK -> shadow; ASSENTE -> DIVERGE (il server
        # non ha il comune: si guarda, non si ritenta)
        quando = datetime.now().isoformat(timespec="seconds")
        n_ok = 0
        for cod, st, n in esiti:
            cella = m["comuni"][cod]["tavole"][t]
            if st == "OK":
                m["comuni"][cod]["tavole"][t].update({
                    "stato": "shadow", "quando": quando, "righe": n})
                n_ok += 1
            else:
                m["comuni"][cod]["tavole"][t].update({
                    "stato": "DIVERGE",
                    "motivo": f"ASSENTE nella query provinciale {prov}"})
        salva(m)
        falliti_consecutivi = 0
        fatte += 1
        print(f"[{prov}] {name}: {n_ok}/{len(comuni)} in shadow")
        if max_query and fatte >= max_query:
            print(f"fermato dopo {fatte} query come richiesto")
            return
        time.sleep(PAUSA)

# --- INNESTO 1: la funzione di fetch ---------------------------------
# from scripts.acquisizione.fetch_comune import fetch_tavola   # ipotesi
# Serve: fetch(comune, tavola) -> percorso del file scaricato (o eccezione)

PAUSA = 15          # secondi fra fetch andati a buon fine
BACKOFF = [60, 300, 900]   # dopo 1, 2, 3 fallimenti consecutivi
MAX_FALLIMENTI = 4  # poi ci si ferma: è il rate limit che parla




def prossima_cella(m, solo_comune=None, salta=()):
    """Prima cella 'mancante' in ordine (comune, tavola). L'ordine per
    comune — completare un comune prima del prossimo — avvicina i gate
    uno alla volta. solo_comune restringe (pilota); salta esclude celle
    (cod, tavola) per la sessione: tattica del processo, non stato
    della campagna — il manifest non le vede, restano 'mancante'."""
    for cod, c in m["comuni"].items():
        if solo_comune and cod != solo_comune:
            continue
        for t in TAVOLE:
            if (cod, t) in salta:
                continue
            if c["tavole"][t]["stato"] == "mancante":
                return cod, t
    return None


def controlla(percorso):
    """Controlli post-download, PRIMA di promuovere: file esiste e non
    è vuoto (SHA_VUOTO: e3b0c442... è l'impronta del nulla).
    --- INNESTO 2: qui si aggancia il normalizzatore per la promozione
    a 'validata'; per ora il fetcher promuove solo a 'scaricata'. ---"""
    p = Path(percorso)
    return p.exists() and p.stat().st_size > 0


def campagna(max_celle=None, solo_comune=None):
    fatti, falliti_consecutivi = 0, 0
    saltate, tentativi = set(), {}
    while True:
        m = carica()
        cella = prossima_cella(m, solo_comune, saltate)
        if cella is None:
            print("campagna: niente da fare, tutte le celle avanzate")
            return
        cod, t = cella
        nome = m["comuni"][cod]["nome"]
        try:
            percorso = fetch_tavola(cod, t)
        except TavolaVuota as e:
            m["comuni"][cod]["tavole"][t].update({"stato": "DIVERGE",
                                                  "motivo": str(e)})
            salva(m)
            print(f"[{cod} {nome}] {t}: DIVERGE (vuota) — da guardare")
            fatti += 1
            if max_celle and fatti >= max_celle:
                print(f"fermato dopo {fatti} celle come richiesto")
                return
            time.sleep(PAUSA)
            continue
        except Exception as e:
            falliti_consecutivi += 1
            tentativi[cella] = tentativi.get(cella, 0) + 1
            print(f"[{cod} {nome}] {t}: FALLITO ({e}) — "
                  f"tentativi cella: {tentativi[cella]}, "
                  f"consecutivi: {falliti_consecutivi}")
            if tentativi[cella] >= 3:
                saltate.add(cella)
                print(f"[{cod} {nome}] {t}: 3 tentativi, la salto per questa "
                      f"sessione (resta 'mancante', si ritenta al rilancio)")
            if falliti_consecutivi >= MAX_FALLIMENTI:
                print("mi fermo: il rate limit non si combatte. "
                      "Rilanciare più tardi, lo stato è salvo.")
                return
            time.sleep(BACKOFF[min(falliti_consecutivi - 1, len(BACKOFF) - 1)])
            continue                      # cella resta 'mancante'

        if controlla(percorso):
            m["comuni"][cod]["tavole"][t].update({
                "stato": "scaricata",
                "quando": datetime.now().isoformat(timespec="seconds"),
            })
            falliti_consecutivi = 0
        else:
            m["comuni"][cod]["tavole"][t].update({
                "stato": "DIVERGE",
                "motivo": "file vuoto o assente"})
            print(f"[{cod} {nome}] {t}: DIVERGE — da guardare, non ritento")
        salva(m)                           # atomico, dopo OGNI cella
        fatti += 1
        if max_celle and fatti >= max_celle:
            print(f"fermato dopo {fatti} celle come richiesto")
            return
        time.sleep(PAUSA)





def fetch_tavola(cod: str, tavola_id: str):
    """Adattatore manifest -> fetch_one. Ritorna il percorso del decoded,
    solleva TavolaVuota se la query non ha osservazioni."""
    name = tavola_id.removeprefix("istat_")
    status, path, _ = fetch_one(cod, name, CORE[name], output_dir(cod))
    if status == "VUOTA":
        raise TavolaVuota(f"{cod}/{name}: query senza osservazioni")
    return path


class TavolaVuota(Exception):
    pass

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-celle", type=int, default=None,
                    help="canale singolo: fermati dopo N celle")
    ap.add_argument("--comune", metavar="COD", default=None,
                    help="canale singolo: limita a un comune (pilota)")
    ap.add_argument("--prov", action="store_true",
                    help="canale provinciale: una query per (provincia, tavola), "
                         "file in shadow, celle marcate 'shadow'")
    ap.add_argument("--max-query", type=int, default=None,
                    help="canale provinciale: fermati dopo N query")
    a = ap.parse_args()

    # i due canali non si mescolano: le opzioni dell'uno non valgono per l'altro
    if a.prov and (a.max_celle or a.comune):
        ap.error("--prov non accetta --max-celle/--comune "
                 "(usare --max-query per limitare)")

    try:
        if a.prov:
            campagna_prov(max_query=a.max_query)
        else:
            campagna(max_celle=a.max_celle, solo_comune=a.comune)
    except KeyboardInterrupt:
        sys.exit("\ninterrotto: lo stato è salvo, rilanciare quando vuoi")