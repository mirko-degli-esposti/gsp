"""
gsp.campagna — manifest di campagna per l'estensione della flotta (v1.1)

COSA È
Un oggetto di ORCHESTRAZIONE, separato dal registro fonti: il registro
dichiara cosa esiste, il manifest dichiara a che punto siamo. Traccia,
per ogni comune candidato, lo stato di acquisizione delle tavole e il
gate di ingresso alla fase di build. Nato per la campagna ER 2026
(47 candidati >15k da istat_posas_comuni_2026), disegnato per essere
portabile ad altre regioni.

PRINCIPI DI DISEGNO (le ragioni, non solo le regole)
1. Dentro il manifest solo CODICI ISTAT, mai assunzioni regionali.
   La regione è un filtro a monte che produce la lista dei comuni, non
   una proprietà dell'oggetto. (Il caso Rimini-099 è la dimostrazione:
   le convenzioni regionali tradiscono, i codici no.)
2. La fase fragile (rete) è separata dalla fase deterministica (build).
   Il fetcher — che NON sta in questo modulo — consuma il manifest:
   prende la prossima cella 'mancante', scarica, e la validazione
   promuove. Ammazzabile e rilanciabile senza memoria umana.
3. Gli stati per tavola: mancante -> scaricata -> validata, più DIVERGE.
   DIVERGE non si sovrascrive con un re-fetch automatico: si guarda.
   (Regola di casa: le rettifiche restano esplicite, niente viene
   corretto in silenzio.)
4. Il gate è DERIVATO dagli stati, mai scritto a mano: un campo che si
   può calcolare e anche impostare prima o poi mente. Gate chiuso =
   tutte le tavole 'validata' E articolazione verificata.
5. Scrittura ATOMICA dell'intero file (tmp + os.replace), mai append:
   un manifest troncato da un Ctrl+C è corruzione silenziosa, e le
   chiavi YAML duplicate da append spariscono nel parser (già pagato).
6. L'emettitore STAMPA, non scrive: entrare in flotta è una decisione,
   non un effetto collaterale di un gate che si chiude. I frammenti per
   rigenera.sh e gsp.common.COMUNI si incollano a mano, si guardano,
   si committano. Se a regime l'incolla diventa puro attrito, promuovere
   l'emettitore a scrittore sarà una riga di decisione, non un
   ripensamento: l'interfaccia resta questa.

COERENZA A VALLE (non in questo modulo, da aggiungere a --verifica)
Finché rigenera.sh e gsp.common.COMUNI restano due posti scritti a mano,
il confronto fra loro è un test di regressione permanente — due code
path che devono dire la stessa cosa.

COMANDI
  python -m gsp.campagna --inizializza        crea il manifest coi 47
  python -m gsp.campagna --stato              fotografia della campagna
  python -m gsp.campagna --emetti 040007      frammenti per la promozione

RIFERIMENTI
  fonte candidati : fonti/registro.yaml -> istat_posas_comuni_2026
  lettura POSAS   : scripts/diagnostica/lista_comuni_er.py (stessi filtri)
  articolazione   : COM_ASC1 dalle basi territoriali, nunique() == 1
                    -> assente (caso San Vito dei Normanni)
"""

import argparse
import math
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

GSP_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = GSP_ROOT / "campagne" / "manifest_er_2026.yaml"

# Tutte le tavole della campagna: il fetcher le consuma tutte.
# Esclusa per decisione (non per dimenticanza): istat_cens_posizione_famiglia,
# mai usata dalla pipeline (ferma a 11 istanze) — se un giorno serve,
# aggiungerla qui è la revoca esplicita.
TAVOLE = [
    "istat_anag_sesso_eta_statociv",
    "istat_cens_sesso_eta_cittadinanza",
    "istat_cens_istruzione_eta",
    "istat_cens_istruzione_cittadinanza",
    "istat_cens_condprof_eta",
    "istat_cens_condprof_cittadinanza",
    "istat_cens_migr_backg",
    "istat_cens_stranieri_paesi",
    "istat_cens_settore_prof",       # gate NO: gsp.lavoro, servirà agli anelli
    "istat_cens_posizione_prof",     # gate NO: idem
]

# Sottoinsieme che chiude il gate K6C: le prime otto.
TAVOLE_GATE = TAVOLE[:8]

STATI_TAVOLA = {"mancante", "scaricata", "validata", "DIVERGE"}
POOL_FATTORE = 1.3   # sovracampionamento, convenzione di rigenera.sh


# ---------------------------------------------------------------- I/O

def carica():
    with open(MANIFEST, encoding="utf-8") as f:
        return yaml.safe_load(f)


def salva(m):
    """Riscrittura atomica dell'intero manifest: tmp + os.replace.
    Mai append (chiavi duplicate spariscono nel parser), mai scrittura
    in place (un Ctrl+C a metà lascia un file troncato)."""
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=MANIFEST.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        yaml.safe_dump(m, f, allow_unicode=True, sort_keys=False)
    os.replace(tmp, MANIFEST)


# ------------------------------------------------------- inizializza

def candidati_da_posas():
    """Rilegge POSAS con gli stessi filtri collaudati di
    lista_comuni_er.py (la lista non è salvata: si rigenera).
    I dettagli dei filtri sono documentati là e nella scheda."""
    csv = GSP_ROOT / "data/istat/posas_2026_comuni/POSAS_2026_it_Comuni.csv"
    df = pd.read_csv(csv, sep=";", skiprows=1,
                     encoding="utf-8-sig", dtype={"Codice comune": str})
    df = df[df["Età"].between(0, 100)]
    prov_er = {"033", "034", "035", "036", "037", "038", "039", "040", "099"}
    er = df[df["Codice comune"].str[:3].isin(prov_er)]
    pop = er.groupby(["Codice comune", "Comune"])["Totale"].sum().astype(int)

    from gsp.common import COMUNI            # esclude la flotta attuale
    fatti = set(COMUNI)
    pop = pop[pop > 15_000]
    return {cod: {"nome": nome, "pop": int(p)}
            for (cod, nome), p in pop.items() if cod not in fatti}


def inizializza():
    if MANIFEST.exists():
        sys.exit(f"GIA' PRESENTE: {MANIFEST} — non sovrascrivo.")
    cand = candidati_da_posas()
    assert len(cand) == 47, f"attesi 47 candidati, trovati {len(cand)}"
    m = {
        "versione": "1.1",
        "campagna": "estensione_er_2026",
        "creato": str(date.today()),
        "fonte_candidati": "istat_posas_comuni_2026",
        "comuni": {
            cod: {
                "nome": v["nome"],          # cortesia di lettura, mai chiave
                "pop_posas": v["pop"],
                "articolazione": "da_verificare",   # misurato, non assunto
                "tavole": {t: {"stato": "mancante"} for t in TAVOLE},
            }
            for cod, v in sorted(cand.items())
        },
    }
    salva(m)
    print(f"manifest creato: {MANIFEST} — {len(cand)} comuni")


# ------------------------------------------------------------- stato

def gate_chiuso(c):
    """Derivato, mai scritto. Guarda solo TAVOLE_GATE: le tavole
    extra-gate (gsp.lavoro) si scaricano ma non bloccano il K6C."""
    tavole_ok = all(c["tavole"][t]["stato"] == "validata"
                    for t in TAVOLE_GATE)
    return tavole_ok and c["articolazione"] != "da_verificare"


def stato():
    m = carica()
    conta = {}
    for c in m["comuni"].values():
        for t in c["tavole"].values():
            conta[t["stato"]] = conta.get(t["stato"], 0) + 1
    chiusi = [cod for cod, c in m["comuni"].items() if gate_chiuso(c)]
    diverge = [cod for cod, c in m["comuni"].items()
               if any(t["stato"] == "DIVERGE" for t in c["tavole"].values())]

    print(f"campagna {m['campagna']} — {len(m['comuni'])} comuni")
    print("celle per stato:", dict(sorted(conta.items())))
    print(f"gate chiusi: {len(chiusi)}", chiusi or "")
    if diverge:
        print(f"DIVERGE da guardare: {diverge}")     # mai auto-risolti


# ------------------------------------------------------------ emetti

def emetti(cod):
    m = carica()
    c = m["comuni"].get(cod) or sys.exit(f"{cod}: non in manifest")
    if not gate_chiuso(c):
        sys.exit(f"{cod} ({c['nome']}): gate APERTO — niente frammenti.\n"
                 "La promozione segue il collaudo, non lo anticipa.")

    # LIV dall'articolazione misurata: senza sub-aree il livello è K6C;
    # con articolazione la scelta (K6C comunque, o salire) è una
    # decisione da prendere guardando quante e quali sub-aree.
    if c["articolazione"] == "assente":
        liv = "K6C"
    else:
        liv = "DA_DECIDERE"
        print(f"# ATTENZIONE: articolazione presente "
              f"({c['articolazione']}): livello da decidere a mano.")

    pool = math.ceil(c["pop_posas"] * POOL_FATTORE)

    print(f"# --- {cod} {c['nome']} — frammenti da incollare, "
          f"verificare, committare ---")
    print(f"# rigenera.sh, array COMUNI:")
    print(f"{cod}:{liv}:{pool}")
    print(f"# gsp.common.COMUNI — completare secondo lo schema "
          f"delle voci esistenti (DA_COMPILARE):")
    print(f'"{cod}": {{...}}   # {c["nome"]}, pop {c["pop_posas"]}')


# --------------------------------------------------------------- CLI

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--inizializza", action="store_true")
    ap.add_argument("--stato", action="store_true")
    ap.add_argument("--emetti", metavar="COD")
    a = ap.parse_args()
    if a.inizializza:
        inizializza()
    elif a.stato:
        stato()
    elif a.emetti:
        emetti(a.emetti)
    else:
        ap.print_help()