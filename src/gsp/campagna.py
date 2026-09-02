"""
gsp.campagna — manifest di campagna per l'estensione della flotta (v1.1)

COSA È
Un oggetto di ORCHESTRAZIONE, separato dal registro fonti: il registro
dichiara cosa esiste, il manifest dichiara a che punto siamo. Traccia,
per ogni comune candidato, lo stato di acquisizione delle tavole e il
gate di ingresso alla fase di build. Nato per la campagna ER 2026
(47 candidati >15k da istat_posas_comuni_2026, poi estesa a tutta la
regione), disegnato per essere portabile ad altre regioni.

PRINCIPI DI DISEGNO (le ragioni, non solo le regole)
1. Dentro il manifest solo CODICI ISTAT, mai assunzioni regionali.
   La regione è un filtro a monte che produce la lista dei comuni, non
   una proprietà dell'oggetto. (Il caso Rimini-099 è la dimostrazione:
   le convenzioni regionali tradiscono, i codici no.)
2. La fase fragile (rete) è separata dalla fase deterministica (build).
   Il fetcher — che NON sta in questo modulo — consuma il manifest:
   prende la prossima cella 'mancante', scarica, e la validazione
   promuove. Ammazzabile e rilanciabile senza memoria umana.
3. Gli stati per tavola: mancante -> (scaricata | shadow) -> validata,
   più DIVERGE. 'scaricata' = canale singolo, file in data/comuni/;
   'shadow' = canale provinciale, file in data/prov_shadow/ finché
   --promuovi non li porta in ufficiale. DIVERGE non si sovrascrive
   con un re-fetch automatico: si guarda. (Regola di casa: le
   rettifiche restano esplicite, niente viene corretto in silenzio.)
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
7. Le celle si AGGIORNANO, mai si sostituiscono (update, non `= {}`):
   'righe', 'quando' e la storia sopravvivono a ogni verdetto. La
   sostituzione è ammessa solo alla nascita (--inizializza/--estendi)
   e alla prima promozione da 'mancante'. Un DIVERGE che cancella le
   misure precedenti è lui stesso una correzione silenziosa (pagato:
   40 celle azzerate al primo collaudo della --valida --shadow).

COERENZA A VALLE (non in questo modulo, da aggiungere a --verifica)
Finché rigenera.sh e gsp.common.COMUNI restano due posti scritti a mano,
il confronto fra loro è un test di regressione permanente — due code
path che devono dire la stessa cosa.

COMANDI
  python -m gsp.campagna --inizializza                 crea il manifest coi 47
  python -m gsp.campagna --estendi                     estende a tutta l'ER (esclusa flotta)
  python -m gsp.campagna --stato                       fotografia della campagna
  python -m gsp.campagna --valida COD [--shadow]       C1-C5 -> 'validata' (o DIVERGE)
  python -m gsp.campagna --riapri COD --motivo "..." [--shadow]
  python -m gsp.campagna --promuovi COD                shadow -> data/comuni (comune intero)
  python -m gsp.campagna --promuovi-tutti              idem, tutti i validati in shadow
  python -m gsp.campagna --verifica-articolazione COD  misura COM_ASC dallo shapefile
  python -m gsp.campagna --verifica-articolazione-tutti
  python -m gsp.campagna --emetti COD                  frammenti per la promozione in flotta

RIFERIMENTI
  fonte candidati : fonti/registro.yaml -> istat_posas_comuni_2026
  lettura POSAS   : scripts/diagnostica/lista_comuni_er.py (stessi filtri)
  articolazione   : COM_ASC1 dalle basi territoriali, nunique() == 1
                    -> assente (caso San Vito dei Normanni)
  canale prov.    : scripts/acquisizione/fetch_prov.py + confronta_prov.py
"""

import argparse
import hashlib
import math
import os
import shutil
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

STATI_TAVOLA = {"mancante", "shadow", "scaricata", "validata", "DIVERGE"}
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
    gruppi = {(cod[:3], t)
              for cod, c in m["comuni"].items()
              for t in TAVOLE if c["tavole"][t]["stato"] == "mancante"}
    if gruppi:
        print(f"gruppi (provincia, tavola) da fetchare: {len(gruppi)}")


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
        print(f"# ATTENZIONE: articolazione {c['articolazione']}: "
              f"livello da decidere a mano.")

    pool = math.ceil(c["pop_posas"] * POOL_FATTORE)

    print(f"# --- {cod} {c['nome']} — frammenti da incollare, "
          f"verificare, committare ---")
    print(f"# rigenera.sh, array COMUNI:")
    print(f"{cod}:{liv}:{pool}")
    print(f"# gsp.common.COMUNI — completare secondo lo schema "
          f"delle voci esistenti (DA_COMPILARE):")
    print(f'"{cod}": {{...}}   # {c["nome"]}, pop {c["pop_posas"]}')


# ----------------------------------------------------- articolazione

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


def verifica_articolazione_tutti():
    """Come verifica_articolazione, ma su tutti i comuni del manifest
    in UNA lettura dello shapefile. Registra le misure e stampa la
    tabella dei 'presente' — la risposta alla domanda 'chi ha zone?'."""
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


# ------------------------------------------------------- validazione
# ATTESI v2 — calibrati sui 'righe' di 318 comuni (campagna provinciale,
# 29/8; tabella completa nel diario e nel commit). Tre regimi misurati:
#   esatto     : posizione_prof, 9 su 318/318 — l'unico invariante universale
#   anagrafica : griglia piena PER PERIODO (multiplo di 1224, <= 8568);
#                sotto tetto solo per finestra corta: fusioni 1/1/2019 e
#                distacco Marche->Romagna 2021 — amministrativo, non sparsita'
#   tetto      : censuarie — la saturazione e' probabilistica al bordo, non
#                una soglia (Castelnuovo Rangone, 15.116: 818/819). Tetto
#                DURO (mai sopra: sopra = duplicati o territorio sbagliato),
#                pavimento = meta' del minimo osservato su 318: morde solo
#                il patologico, il legittimo passa. Pavimenti [m], non teoria.
ATTESI = {
    "istat_anag_sesso_eta_statociv":      {"anag": True},
    "istat_cens_posizione_prof":          {"esatto": 9},
    "istat_cens_istruzione_eta":          {"tetto": 819,  "pavimento": 217},
    "istat_cens_istruzione_cittadinanza": {"tetto": 441,  "pavimento": 117},
    "istat_cens_condprof_eta":            {"tetto": 819,  "pavimento": 270},
    "istat_cens_condprof_cittadinanza":   {"tetto": 486,  "pavimento": 162},
    "istat_cens_settore_prof":            {"tetto": 21,   "pavimento": 7},
    "istat_cens_migr_backg":              {"tetto": 495,  "pavimento": 107},
    "istat_cens_sesso_eta_cittadinanza":  {"tetto": 3647, "pavimento": 466},
    "istat_cens_stranieri_paesi":         {"tetto": 2670, "pavimento": 52},
}
#TOLLERANZA_C5 = 0.02        # componente relativa: un anno di deriva
#C5_ASSOLUTO = 25            # componente assoluta: il rumore anagrafico non
                            # scala con la taglia — su un comune da 100
                            # abitanti 6 persone sono il 5,5%, su Bologna
                            # sarebbero lo 0,0015%. Tarato sui 20 casi ER
                            # (max osservato: 141 su Farini, 4,5%).

# C5 — coerenza anagrafe/POSAS, normalizzata su taglia E centrata sul bias.
# Due fatti misurati su 320 comuni ER (29/8):
#  (a) lo scarto relativo scala come 1/sqrt(pop) — mediana per fascia da
#      0,12% (>30k) a 1,58% (<1k): una soglia costante boccia per TAGLIA
#      invece che per anomalia (il 2% ne bocciava 20, quasi tutti piccoli);
#  (b) c'e' un bias generale mite: 67% dei comuni sotto la proiezione,
#      mediana -0,35% — POSAS 2026 stima in avanti rispetto all'anagrafe
#      1/1/2025, e la differenza va tolta prima di misurare l'anomalia.
# Soglia = C5_K/sqrt(pop) sullo scarto CENTRATO. A k=1.6 boccia 10 comuni
# (3,1%): un blocco contiguo della Bassa modenese-ferrarese (Mirandola,
# San Felice, Finale Emilia, Cento, Carpi, Terre del Reno) piu' quattro,
# tutti dallo stesso lato e a 3-13x la mediana regionale — segnale
# demografico locale, non rumore. k=2.0 lo cancellerebbe, k=1.3
# ripescherebbe il rumore di taglia.
C5_K = 1.6
C5_BIAS = -0.0035     # mediana regionale [m]; ricalibrare per altre regioni

SHADOW_ROOT = GSP_ROOT / "data" / "prov_shadow"


def _controlla_tavola(cod, tavola_id, pop_posas, radice=None):
    """Controlli C1-C5 su un decoded. Ritorna None se tutto passa,
    altrimenti il motivo MISURATO del fallimento (mai 'controllo
    fallito': sempre il numero visto contro l'atteso).

    radice: dove cercare i decoded. None = data/comuni/ (canale
    singolo; coincide con output_dir di fetch_comune — la convenzione
    resta citata qui senza essere duplicata nel codice);
    SHADOW_ROOT = prov_shadow (canale provinciale, pre-promozione).
    Il controllo e' identico: cambia solo dove vive il file."""
    name = tavola_id.removeprefix("istat_")
    base = radice if radice is not None else (GSP_ROOT / "data" / "comuni")
    path = base / cod / f"{name}_decoded.csv"

    # C1 — esistenza e non-vuotezza
    if not path.exists() or path.stat().st_size == 0:
        return f"C1: {path.name} assente o vuoto"

    df = pd.read_csv(path)

    # C2 — conteggio righe, tre regimi (v. ATTESI)
    att = ATTESI[tavola_id]
    n = len(df)
    if "esatto" in att and n != att["esatto"]:
        return f"C2: righe {n} != esatto {att['esatto']}"
    if att.get("anag"):
        if n % 1224 != 0 or n > 8568:
            return (f"C2: anagrafica {n} righe — non multiplo di 1224 "
                    f"o sopra 8568 (periodi attesi interi, max 7)")
    if "tetto" in att:
        if n > att["tetto"]:
            return f"C2: righe {n} SOPRA il tetto {att['tetto']} (duplicati?)"
        if n < att["pavimento"]:
            return f"C2: righe {n} sotto il pavimento {att['pavimento']}"

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
        soglia = C5_K / math.sqrt(pop_posas)
        scarto = (tot - pop_posas) / pop_posas - C5_BIAS   # centrato
        if abs(scarto) > soglia:
            return (f"C5: anag {ultimo} = {tot:.0f} vs posas {pop_posas} "
                    f"(scarto centrato {scarto:+.1%} > soglia {soglia:.1%} "
                    f"= {C5_K}/sqrt(pop))")
    return None


def valida(cod, shadow=False):
    """Promuove a 'validata' le tavole che passano C1-C5; quelle che
    falliscono vanno DIVERGE col motivo misurato (update: 'righe' e
    'quando' sopravvivono al verdetto). Non tocca DIVERGE esistenti,
    non retrocede validate.

    Con shadow=True: controlla le celle 'shadow' leggendo da
    prov_shadow/, e le promuove a 'validata' con in_shadow=True — il
    file NON e' ancora in data/comuni/: ce lo porta --promuovi."""
    m = carica()
    c = m["comuni"].get(cod) or sys.exit(f"{cod}: non in manifest")
    stato_atteso = "shadow" if shadow else "scaricata"
    radice = SHADOW_ROOT if shadow else None
    n_processate = 0
    for t in TAVOLE:
        if c["tavole"][t]["stato"] != stato_atteso:
            continue
        n_processate += 1
        motivo = _controlla_tavola(cod, t, c["pop_posas"], radice=radice)
        if motivo is None:
            c["tavole"][t]["stato"] = "validata"
            c["tavole"][t]["quando_validata"] = \
                datetime.now().isoformat(timespec="seconds")
            if shadow:
                c["tavole"][t]["in_shadow"] = True
            print(f"[{cod}] {t}: validata" + (" (shadow)" if shadow else ""))
        else:
            # update, non sostituzione: righe/quando/storia sopravvivono
            # al verdetto — un DIVERGE che cancella le misure precedenti
            # e' lui stesso una correzione silenziosa (principio 7)
            c["tavole"][t].update({"stato": "DIVERGE", "motivo": motivo})
            print(f"[{cod}] {t}: DIVERGE — {motivo}")
    salva(m)
    if n_processate == 0:
        # "niente da fare" e "non ho fatto" devono suonare diversi:
        # un comando muto su zero celle e' un mezzogiorno perso domani
        print(f"  (nessuna cella '{stato_atteso}' da controllare per {cod})")
    print(f"gate {cod} ({c['nome']}): "
          f"{'CHIUSO' if gate_chiuso(c) else 'aperto'}")


# -------------------------------------------------------- promozione

def _sha256(p, blocco=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(blocco):
            h.update(chunk)
    return h.hexdigest()


def promuovi(cod=None, tutti=False):
    """Copia prov_shadow/<cod>/ -> data/comuni/<cod>/ SOLO per comuni
    con tutte le tavole validate in shadow. Registra lo sha256 di ogni
    decoded nella cella (la memoria contro le sovrascritture) e spegne
    in_shadow. Rifiuta i parziali: la directory ufficiale riceve solo
    comuni interi e validati."""
    m = carica()
    codici = ([cod] if cod else
              [k for k, c in m["comuni"].items()
               if all(v["stato"] == "validata" and v.get("in_shadow")
                      for v in c["tavole"].values())] if tutti else
              sys.exit("--promuovi COD oppure --promuovi-tutti"))
    fatti = 0
    for k in codici:
        c = m["comuni"].get(k) or sys.exit(f"{k}: non in manifest")
        celle = c["tavole"]
        if not all(v["stato"] == "validata" and v.get("in_shadow")
                   for v in celle.values()):
            print(f"[{k}] {c['nome']}: NON promosso — celle non tutte "
                  f"validate in shadow")
            continue
        src, dst = SHADOW_ROOT / k, GSP_ROOT / "data" / "comuni" / k
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src.iterdir()):
            shutil.copy2(f, dst / f.name)
        for t, v in celle.items():
            name = t.removeprefix("istat_")
            v["sha256"] = _sha256(dst / f"{name}_decoded.csv")
            v["in_shadow"] = False
        fatti += 1
        print(f"[{k}] {c['nome']}: promosso ({len(list(src.iterdir()))} file)")
    salva(m)
    print(f"promossi {fatti}/{len(codici)}")


def riapri(cod, motivo, a_stato="scaricata"):
    """Riporta le celle DIVERGE di un comune allo stato indicato,
    registrando PERCHÉ: la storia delle riaperture resta nel manifest
    (e nei suoi commit). Mai automatico, mai senza motivo — un DIVERGE
    riaperto senza spiegazione è un DIVERGE corretto in silenzio.

    a_stato: 'scaricata' (default, canale singolo: i file vivono in
    data/comuni/) oppure 'shadow' (celle nate dal canale provinciale:
    i file vivono in prov_shadow/ finche' --promuovi non li porta in
    ufficiale — riaprirle a 'scaricata' le farebbe cercare nel posto
    sbagliato al giro dopo, C1 garantito).

    Update, non sostituzione (principio 7): 'righe' e 'quando'
    originali sopravvivono; il motivo del DIVERGE viene preservato
    dentro 'riaperta' come motivo_diverge."""
    assert a_stato in {"scaricata", "shadow"}, a_stato
    m = carica()
    c = m["comuni"].get(cod) or sys.exit(f"{cod}: non in manifest")
    n = 0
    for t in TAVOLE:
        if c["tavole"][t]["stato"] == "DIVERGE":
            motivo_diverge = c["tavole"][t].pop("motivo", None)
            c["tavole"][t].update({
                "stato": a_stato,
                "riaperta": {
                    "quando": datetime.now().isoformat(timespec="seconds"),
                    "motivo": motivo,
                    "motivo_diverge": motivo_diverge,
                },
            })
            n += 1
    salva(m)
    print(f"{cod} ({c['nome']}): riaperte {n} celle DIVERGE -> "
          f"'{a_stato}' — {motivo}")


def accetta(cod, motivo):
    """Il terzo esito di un DIVERGE, dopo 'riparato' e 'lasciato li'':
    GUARDATO, COMPRESO, ACCETTATO con motivo. Promuove a 'validata'
    registrando l'accettazione nella cella — l'asterisco resta per
    sempre, e il gate puo' chiudere.

    Non e' una scorciatoia: serve per le anomalie VERE che il controllo
    ha fatto bene a segnalare (Carpi: scarto anagrafe/proiezione -1,0%
    su 74k, un blocco demografico della Bassa, non un difetto del dato)
    e che una persona ha esaminato. Il motivo e' obbligatorio e finisce
    nel manifest e nei suoi commit: un'accettazione senza spiegazione
    sarebbe un DIVERGE corretto in silenzio (principio 3)."""
    m = carica()
    c = m["comuni"].get(cod) or sys.exit(f"{cod}: non in manifest")
    n = 0
    for t in TAVOLE:
        v = c["tavole"][t]
        if v["stato"] != "DIVERGE":
            continue
        v.update({
            "stato": "validata",
            "quando_validata": datetime.now().isoformat(timespec="seconds"),
            "accettata": {
                "quando": datetime.now().isoformat(timespec="seconds"),
                "motivo": motivo,
                "motivo_diverge": v.pop("motivo", None),
            },
        })
        # in_shadow: il file sta ancora in prov_shadow se la cella veniva
        # dal canale provinciale — lo si deduce dalla presenza di 'righe',
        # che solo campagna_prov scrive
        if "righe" in v:
            v["in_shadow"] = True
        n += 1
    salva(m)
    print(f"{cod} ({c['nome']}): accettate {n} celle DIVERGE — {motivo}")
    print(f"gate {cod}: {'CHIUSO' if gate_chiuso(c) else 'aperto'}")


# ------------------------------------------------------------ estendi

def estendi():
    """Estende il manifest a TUTTI i comuni ER dal POSAS, esclusa la
    flotta (gsp.common.COMUNI: le popolazioni generate non si toccano
    ne' si tracciano — il manifest e' della campagna, la flotta della
    flotta).

    Preserva integralmente i comuni gia' presenti con i loro stati:
    per questo NON e' --inizializza. I nuovi entrano tutti 'mancante',
    e l'intero dizionario viene riordinato per popolazione decrescente:
    ogni interruzione della campagna lascia una flotta coerente
    (i piu' grandi prima). Idempotente: rilanciarlo a POSAS invariato
    non cambia nulla."""
    m = carica()

    # tutti i comuni ER dal POSAS, stessi filtri collaudati
    csv = GSP_ROOT / "data/istat/posas_2026_comuni/POSAS_2026_it_Comuni.csv"
    df = pd.read_csv(csv, sep=";", skiprows=1,
                     encoding="utf-8-sig", dtype={"Codice comune": str})
    df = df[df["Età"].between(0, 100)]
    prov_er = {"033", "034", "035", "036", "037", "038", "039", "040", "099"}
    er = df[df["Codice comune"].str[:3].isin(prov_er)]
    pop = (er.groupby(["Codice comune", "Comune"])["Totale"]
             .sum().astype(int))
    assert pop.shape[0] == 330, f"attesi 330 comuni ER, trovati {pop.shape[0]}"

    from gsp.common import COMUNI
    flotta = set(COMUNI)

    presenti = set(m["comuni"])
    nuovi, saltati_flotta = 0, 0
    for (cod, nome), p in pop.items():
        if cod in flotta:
            saltati_flotta += 1
            continue
        if cod in presenti:
            continue                      # preservato con i suoi stati
        m["comuni"][cod] = {
            "nome": nome,
            "pop_posas": int(p),
            "articolazione": "da_verificare",
            "tavole": {t: {"stato": "mancante"} for t in TAVOLE},
        }
        nuovi += 1

    # riordino per popolazione decrescente (i presenti conservano tutto,
    # cambia solo la posizione — l'ordine E' la politica di campagna)
    m["comuni"] = dict(sorted(m["comuni"].items(),
                              key=lambda kv: -kv[1]["pop_posas"]))
    m["estesa"] = {"quando": str(date.today()),
                   "criterio": "tutti i comuni ER (POSAS 2026), esclusa flotta"}
    salva(m)
    print(f"manifest esteso: {nuovi} nuovi, {len(presenti)} preservati, "
          f"{saltati_flotta} in flotta (esclusi), totale {len(m['comuni'])}")

# ------------------------------------------------- promozione in flotta


SOGLIA_V2 = 3000   # [m] note/misure/soglia_taglia_er.md: pop/supporto >= 1
                   # attraversa 1 a ~2.500-2.800 a K6C; 3.000 sta dal lato
                   # sicuro (Vernasca 2.014 marginale su 4 indicatori, Sissa
                   # 7.901 dentro). Copre il 95,2% della popolazione ER.

COMUNI_YAML = GSP_ROOT / "flotta" / "comuni.yaml"


class _DumperQuotato(yaml.SafeDumper):
    """Codici SEMPRE quotati: senza virgolette, un codice con sole cifre
    0-7 e' letto da YAML 1.1 come OTTALE (015146 -> 6758)."""
    pass


def _rappresenta_str(dumper, s):
    if "\n" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
    style = "'" if s.isdigit() else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", s, style=style)


_DumperQuotato.add_representer(str, _rappresenta_str)


def _salva_registro(reg):
    """Riscrittura atomica di flotta/comuni.yaml. L'intestazione — il
    blocco iniziale di righe '#' o vuote, che yaml.dump perderebbe —
    viene preservata per STRUTTURA, non cercando un carattere: la prima
    versione cercava la prima virgoletta e la trovava in un apostrofo
    dell'intestazione stessa (file rotto, 2/9). Mai append."""
    righe = COMUNI_YAML.read_text(encoding="utf-8").splitlines(keepends=True)
    testa = []
    for l in righe:
        if l.startswith("#") or not l.strip():
            testa.append(l)
        else:
            break
    fd, tmp = tempfile.mkstemp(dir=COMUNI_YAML.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("".join(testa))
        yaml.dump(reg, f, Dumper=_DumperQuotato, allow_unicode=True,
                  sort_keys=False)
    os.replace(tmp, COMUNI_YAML)


def _slug(nome):
    """Convenzione degli slug esistenti: minuscolo, spazi e trattini ->
    underscore, apostrofi rimossi. I casi strani (accenti, 'Sant'Ilario
    d'Enza') si guardano nel dry-run e si correggono a mano nel yaml:
    lo slug e' un nome di file, non una chiave."""
    return (nome.lower().replace("'", "").replace(" ", "_")
                .replace("-", "_"))


def promuovi_in_flotta(soglia=SOGLIA_V2, dry_run=False):
    """L'emettitore promosso a scrittore. Per ogni comune del manifest:
      - gate aperto        -> salta (non e' pronto)
      - pop_posas < soglia -> 'sotto_soglia' nel manifest: esclusione
                              DICHIARATA, non implicita nel filtro
      - gia' nel registro  -> salta (idempotente; le voci esistenti non si
                              toccano MAI)
      - altrimenti         -> promuove i file se ancora in shadow (gradino
                              zero della staffetta) e scrive la voce minima
    La deliberazione umana e' salita a monte, nel criterio di soglia: qui
    non c'e' piu' niente da decidere per comune."""
    m = carica()
    reg = yaml.safe_load(open(COMUNI_YAML, encoding="utf-8"))
    nuovi, sotto, saltati = [], [], []

    for cod, c in m["comuni"].items():
        if not gate_chiuso(c):
            saltati.append(cod)
            continue
        if c["pop_posas"] < soglia:
            c["stato_v2"] = "sotto_soglia"
            sotto.append(cod)
            continue
        if cod in reg:
            continue
        if not dry_run and any(v.get("in_shadow") for v in c["tavole"].values()):
            promuovi(cod=cod)                       # gradino zero: i file
            m = carica()                            # promuovi ha salvato: rileggo
            c = m["comuni"][cod]
        reg[cod] = {
            "nome": c["nome"], "slug": _slug(c["nome"]),
            "regione": "emilia_romagna",            # proprieta' della CAMPAGNA
            "pool": math.ceil(c["pop_posas"] * POOL_FATTORE),
            "stato": "v2",
        }
        c["stato_v2"] = "in_flotta"
        nuovi.append(cod)
        if dry_run:
            print(f"  {cod} {c['nome']:<28} -> {reg[cod]['slug']:<28} pool {reg[cod]['pool']}")

    if not dry_run:
        salva(m)
        _salva_registro(reg)
    print(f"soglia {soglia}: {len(nuovi)} promossi in flotta, "
          f"{len(sotto)} sotto soglia, {len(saltati)} con gate aperto"
          + ("  [dry-run: nulla scritto]" if dry_run else ""))
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
                    help="controlla C1-C5 e promuove a 'validata' le tavole "
                         "scaricate (o shadow, con --shadow)")
    ap.add_argument("--riapri", metavar="COD")
    ap.add_argument("--motivo", default=None)
    ap.add_argument("--estendi", action="store_true",
                    help="estende il manifest a tutti i comuni ER (POSAS), "
                         "esclusa la flotta")
    ap.add_argument("--shadow", action="store_true",
                    help="con --valida/--riapri: le celle del canale "
                         "provinciale, file in prov_shadow/ (pre-promozione)")
    ap.add_argument("--promuovi", metavar="COD",
                    help="copia prov_shadow/<COD>/ in data/comuni/ (solo se "
                         "tutte le tavole sono validate in shadow)")
    ap.add_argument("--promuovi-tutti", action="store_true",
                    help="promuove tutti i comuni interamente validati in shadow")
    ap.add_argument("--accetta", metavar="COD",
                    help="promuove a 'validata' le celle DIVERGE guardate e "
                         "comprese, registrando --motivo (obbligatorio)")
    ap.add_argument("--promuovi-in-flotta", action="store_true",
                    help="scrive nel registro le voci dei comuni con gate chiuso "
                         "e pop >= soglia; marca sotto_soglia gli altri")
    ap.add_argument("--soglia", type=int, default=SOGLIA_V2)
    ap.add_argument("--dry-run", action="store_true",
                    help="con --promuovi-in-flotta: mostra senza scrivere")
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
    elif a.estendi:
        estendi()
    elif a.valida:
        valida(a.valida, shadow=a.shadow)
    elif a.promuovi:
        promuovi(cod=a.promuovi)
    elif a.promuovi_tutti:
        promuovi(tutti=True)
    elif a.accetta:
        if not a.motivo:
            ap.error("--accetta richiede --motivo")
        accetta(a.accetta, a.motivo)
    elif a.riapri:
        if not a.motivo:
            ap.error("--riapri richiede --motivo")
        riapri(a.riapri, a.motivo,
               a_stato="shadow" if a.shadow else "scaricata")
    elif a.promuovi_in_flotta:
        promuovi_in_flotta(soglia=a.soglia, dry_run=a.dry_run)
    else:
        ap.print_help()