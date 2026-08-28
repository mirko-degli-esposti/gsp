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


# --- INNESTO 1: la funzione di fetch ---------------------------------
# DA_COMPILARE: come si invoca il fetch di UNA tavola per UN comune?
# from scripts.acquisizione.fetch_comune import fetch_tavola   # ipotesi
# Serve: fetch(comune, tavola) -> percorso del file scaricato (o eccezione)

PAUSA = 15          # secondi fra fetch andati a buon fine
BACKOFF = [60, 300, 900]   # dopo 1, 2, 3 fallimenti consecutivi
MAX_FALLIMENTI = 4  # poi ci si ferma: è il rate limit che parla


def prossima_cella(m):
    """Prima cella 'mancante' in ordine (comune, tavola). L'ordine per
    comune — completare un comune prima di passare al prossimo — è
    deliberato: avvicina i gate uno alla volta invece di lasciare 47
    comuni tutti al 70%."""
    for cod, c in m["comuni"].items():
        for t in TAVOLE:
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


def campagna(max_celle=None):
    fatti, falliti_consecutivi = 0, 0
    while True:
        m = carica()                      # riletto: stato sempre fresco
        cella = prossima_cella(m)
        if cella is None:
            print("campagna: niente da fare, tutte le celle avanzate")
            return
        cod, t = cella
        nome = m["comuni"][cod]["nome"]
        try:
            percorso = fetch_tavola(cod, t)
        except TavolaVuota as e:
            m["comuni"][cod]["tavole"][t] = {"stato": "DIVERGE",
                                             "motivo": str(e)}
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
            print(f"[{cod} {nome}] {t}: FALLITO ({e}) — "
                  f"consecutivi: {falliti_consecutivi}")
            if falliti_consecutivi >= MAX_FALLIMENTI:
                print("mi fermo: il rate limit non si combatte. "
                      "Rilanciare più tardi, lo stato è salvo.")
                return
            time.sleep(BACKOFF[min(falliti_consecutivi - 1,
                                   len(BACKOFF) - 1)])
            continue                       # cella resta 'mancante'

        if controlla(percorso):
            m["comuni"][cod]["tavole"][t] = {
                "stato": "scaricata",
                "quando": datetime.now().isoformat(timespec="seconds"),
            }
            falliti_consecutivi = 0
        else:
            m["comuni"][cod]["tavole"][t] = {"stato": "DIVERGE",
                                             "motivo": "file vuoto o assente"}
            print(f"[{cod} {nome}] {t}: DIVERGE — da guardare, non ritento")
        salva(m)                           # atomico, dopo OGNI cella
        fatti += 1
        if max_celle and fatti >= max_celle:
            print(f"fermato dopo {fatti} celle come richiesto")
            return
        time.sleep(PAUSA)


# fetch_comune.py vive in scripts/, non nel pacchetto: import via path.
sys.path.insert(0, str(GSP_ROOT / "scripts" / "acquisizione"))
from fetch_comune import CORE, fetch_one, output_dir

# Il manifest usa gli id di registro (istat_*), il CORE le chiavi nude:
# mappatura meccanica, verificata all'import — se le due nomenclature
# divergono, si rompe QUI, non a metà campagna (il germe annotato).
assert all(t.removeprefix("istat_") in CORE for t in TAVOLE), \
    "id di manifest senza corrispondente nel CORE di fetch_comune"

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
                    help="fermati dopo N celle (per il pilota)")
    a = ap.parse_args()
    try:
        campagna(max_celle=a.max_celle)
    except KeyboardInterrupt:
        sys.exit("\ninterrotto: lo stato è salvo, rilanciare quando vuoi")