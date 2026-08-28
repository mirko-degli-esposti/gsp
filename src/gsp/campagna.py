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
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import yaml
import geopandas as gpd
import gsp.common as G



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


def verifica_articolazione(cod):
    """Misura l'articolazione sub-comunale dalle basi territoriali
    (COM_ASC1 delle sezioni 2021) e la registra nel manifest.

    Tutto offline: lo shapefile regionale è già su disco. Registra il
    VALORE misurato, non solo il verdetto — un comune con 3 sub-aree è
    informazione per decidere un domani se merita più del K6C.
    Criterio: nunique(COM_ASC1) == 1 -> assente (caso San Vito dei
    Normanni: un solo valore, nessuna articolazione)."""
  

    m = carica()
    c = m["comuni"].get(cod) or sys.exit(f"{cod}: non in manifest")

    # Regione geodata: proprietà della CAMPAGNA, non del comune (il
    # manifest resta senza assunzioni regionali; qui è il consumatore
    # ER-specifico che la dichiara).
    shp = G.path_shp("emilia_romagna")
    s = gpd.read_file(shp)
    s = s[s.PRO_COM == G.procom(cod)]     # conversione codice: SUA, non nostra
    if s.empty:
        sys.exit(f"{cod}: nessuna sezione nello shapefile — codice o regione errati")

    n1 = s["COM_ASC1"].nunique(dropna=True)
    nan1 = int(s["COM_ASC1"].isna().sum())
    n2 = s["COM_ASC2"].nunique(dropna=True) if "COM_ASC2" in s.columns else 0

    esito = "assente" if n1 <= 1 else "presente"
    c["articolazione"] = esito
    c["articolazione_misura"] = {
        "sezioni": int(len(s)),
        "asc1": int(n1), "asc1_nan": nan1, "asc2": int(n2),
        "quando": str(date.today()),
    }
    salva(m)
    print(f"{cod} {c['nome']}: articolazione {esito} "
          f"({len(s)} sezioni, ASC1={n1}, ASC2={n2}, nan={nan1})")

# ------------------------------------------------------- validazione
# Attesi di conteggio righe (dati, senza header: len(df), non wc -l).
# Provenienza di ogni numero: misurato su 033021 e 040007 (estremi
# 15k/95k del pilota); anag confermata anche su 020030.
# Esatti = griglie piene o sparse-per-costruzione; range = dipendono
# dal comune, calibrati su DUE punti: provvisori, si allargano solo
# per decisione davanti a un caso vero, mai in silenzio.
ATTESI = {
    "istat_anag_sesso_eta_statociv":       {"esatto": 8568},
    "istat_cens_istruzione_eta":           {"esatto": 819},
    "istat_cens_istruzione_cittadinanza":  {"esatto": 441},
    "istat_cens_condprof_eta":             {"esatto": 819},
    "istat_cens_condprof_cittadinanza":    {"esatto": 486},
    "istat_cens_settore_prof":             {"esatto": 21},
    "istat_cens_posizione_prof":           {"esatto": 9},
    "istat_cens_sesso_eta_cittadinanza":   {"range": (2500, 6000)},
    "istat_cens_migr_backg":               {"range": (400, 600)},
    "istat_cens_stranieri_paesi":          {"range": (700, 3500)},
}

TOLLERANZA_C5 = 0.02   # anag JAN 2025 vs POSAS 1/1/2026: un anno di deriva


def _controlla_tavola(cod, tavola_id, pop_posas):
    """Ritorna None se tutto passa, altrimenti il motivo MISURATO del
    fallimento (mai 'controllo fallito': sempre il numero visto contro
    l'atteso)."""
    name = tavola_id.removeprefix("istat_")
    path = Path(os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{cod}/{name}_decoded.csv"))

    # C1 — esistenza e non-vuotezza
    if not path.exists() or path.stat().st_size == 0:
        return f"C1: {path.name} assente o vuoto"

    df = pd.read_csv(path)

    # C2 — conteggio righe contro l'atteso
    att = ATTESI[tavola_id]
    if "esatto" in att and len(df) != att["esatto"]:
        return f"C2: righe {len(df)} != atteso {att['esatto']}"
    if "range" in att and not (att["range"][0] <= len(df) <= att["range"][1]):
        return f"C2: righe {len(df)} fuori range {att['range']}"

 # C3 — territorio. Lo zero iniziale è perso A MONTE (nel parsing di
    # sdmx.fetch): i decoded portano 33021, non 033021. Si accetta il
    # codice in entrambe le forme; pre-filtro sulle colonne monovalore
    # (la territoriale lo è per definizione in un fetch comunale).
    attesi_terr = {cod, str(int(cod))}
    terr_ok = any({str(v).strip() for v in df[c].dropna().unique()} <= attesi_terr
                  for c in df.columns if df[c].nunique(dropna=True) == 1)
    if not terr_ok:
        return f"C3: nessuna colonna territoriale con solo {cod}"
    
    # C4 — OBS_VALUE sano
    obs = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    if obs.isna().all() or (obs < 0).any() or obs.sum() <= 0:
        return (f"C4: OBS_VALUE sospetto (nan={obs.isna().sum()}, "
                f"neg={(obs < 0).sum()}, somma={obs.sum():.0f})")

    # C5 — coerenza di livello, SOLO anagrafica per ora: le censuarie
    # imbarcano totali multiformi in posizioni diverse per tavola e un
    # C5 non filtrato validerebbe rumore (estensione futura, col profilo)
    if tavola_id == "istat_anag_sesso_eta_statociv":
        ultimo = df["TIME_PERIOD"].max()
        tot = obs[(df["TIME_PERIOD"] == ultimo) & (df["AGE"] == "TOTAL")].sum()
        scarto = abs(tot - pop_posas) / pop_posas
        if scarto > TOLLERANZA_C5:
            return (f"C5: anag {ultimo} = {tot:.0f} vs posas {pop_posas} "
                    f"(scarto {scarto:.1%} > {TOLLERANZA_C5:.0%})")
    return None


def valida(cod):
    """Promuove a 'validata' le tavole 'scaricata' che passano C1-C5;
    quelle che falliscono vanno DIVERGE col motivo misurato. Non tocca
    DIVERGE esistenti, non retrocede validate."""
    m = carica()
    c = m["comuni"].get(cod) or sys.exit(f"{cod}: non in manifest")
    for t in TAVOLE:
        if c["tavole"][t]["stato"] != "scaricata":
            continue
        motivo = _controlla_tavola(cod, t, c["pop_posas"])
        if motivo is None:
            c["tavole"][t]["stato"] = "validata"
            c["tavole"][t]["quando_validata"] = \
                datetime.now().isoformat(timespec="seconds")
            print(f"[{cod}] {t}: validata")
        else:
            c["tavole"][t] = {"stato": "DIVERGE", "motivo": motivo}
            print(f"[{cod}] {t}: DIVERGE — {motivo}")
    salva(m)
    print(f"gate {cod} ({c['nome']}): "
          f"{'CHIUSO' if gate_chiuso(c) else 'aperto'}")

def riapri(cod, motivo):
    """Riporta a 'scaricata' le celle DIVERGE di un comune, registrando
    PERCHÉ: la storia delle riaperture resta nel manifest (e nei suoi
    commit). Mai automatico, mai senza motivo — un DIVERGE riaperto
    senza spiegazione è un DIVERGE corretto in silenzio."""
    m = carica()
    c = m["comuni"].get(cod) or sys.exit(f"{cod}: non in manifest")
    n = 0
    for t in TAVOLE:
        if c["tavole"][t]["stato"] == "DIVERGE":
            c["tavole"][t] = {
                "stato": "scaricata",
                "riaperta": {"quando": datetime.now().isoformat(timespec="seconds"),
                             "motivo": motivo},
            }
            n += 1
    salva(m)
    print(f"{cod} ({c['nome']}): riaperte {n} celle DIVERGE — {motivo}")


def verifica_articolazione_tutti():
    """Come verifica_articolazione, ma su tutti i comuni del manifest
    in UNA lettura dello shapefile. Registra le misure e stampa la
    tabella dei 'presente' — la risposta alla domanda 'chi ha zone?'."""
    import geopandas as gpd
    import gsp.common as G
    m = carica()
    s = gpd.read_file(G.path_shp("emilia_romagna"))
    for cod, c in m["comuni"].items():
        ss = s[s.PRO_COM == G.procom(cod)]
        n1 = ss["COM_ASC1"].nunique(dropna=True)
        c["articolazione"] = "assente" if n1 <= 1 else "presente"
        c["articolazione_misura"] = {
            "sezioni": int(len(ss)), "asc1": int(n1),
            "asc1_nan": int(ss["COM_ASC1"].isna().sum()),
            "asc2": int(ss["COM_ASC2"].nunique(dropna=True)) if "COM_ASC2" in ss.columns else 0,
            "quando": str(date.today()),
        }
    salva(m)
    for cod, c in m["comuni"].items():
        if c["articolazione"] == "presente":
            mi = c["articolazione_misura"]
            print(f"{cod} {c['nome']}: ASC1={mi['asc1']} "
                  f"({mi['sezioni']} sezioni, nan={mi['asc1_nan']})")

# --------------------------------------------------------------- CLI

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--inizializza", action="store_true")
    ap.add_argument("--stato", action="store_true")
    ap.add_argument("--emetti", metavar="COD")
    ap.add_argument("--verifica-articolazione-tutti", action="store_true",
                    help="misura COM_ASC1/ASC2 per TUTTI i comuni del manifest "
                         "in una sola lettura dello shapefile")
    ap.add_argument("--verifica-articolazione", metavar="COD")
    ap.add_argument("--valida", metavar="COD",
                    help="controlla C1-C5 e promuove a 'validata' le tavole scaricate") 
    ap.add_argument("--riapri", metavar="COD")
    ap.add_argument("--motivo", default=None)  
    a = ap.parse_args()
    if a.inizializza:
        inizializza()
    elif a.stato:
        stato()
    elif a.emetti:
        emetti(a.emetti)
    elif a.verifica_articolazione_tutti:
        verifica_articolazione_tutti()
    elif a.verifica_articolazione:
        verifica_articolazione(a.verifica_articolazione)
    elif a.valida:
        valida(a.valida)
    elif a.riapri:
        if not a.motivo:
            ap.error("--riapri richiede --motivo")
        riapri(a.riapri, a.motivo)
    else:
        ap.print_help()