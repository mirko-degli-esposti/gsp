"""
gsp_common.py — registri, percorsi e primitive condivise della pipeline GSP.

Consolida i cinque registri di comuni che erano duplicati in build_sezioni.py,
build_zona_tables.py, assign_nationality.py, assign_avq.py, enrich.py e
join_civici_sezioni.py. Aggiungere un comune richiedeva sei modifiche
coordinate; ora ne richiede una.

Principio: nel registro sta SOLO cio' che non e' derivabile. Il codice ISTAT
a sei cifre contiene gia' provincia e comune, e i percorsi sono formule:

    "034027"  ->  procom 34027, provincia "034"
    sezioni   ->  submun/{slug}_sezioni_2023.csv
    civici    ->  geodata/{regione}/civici_sezioni_province/{prov}_{nome}_...csv

Uso come modulo:
    import gsp_common as G
    info = G.info("034027")
    p    = pd.read_csv(G.path_sezioni("034027"))
    q    = G.zona_nomi("034027")

Uso da riga di comando:
    python gsp_common.py --check              # verifica tutti i comuni
    python gsp_common.py --check 034027       # un comune solo
    python gsp_common.py --dump-nomi 037006   # nomi zona da zona_2023/, da incollare
"""

from __future__ import annotations

import glob
import os
import re
import sys
import unicodedata

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Radici
# ----------------------------------------------------------------------

GSP = os.path.expanduser("~/progetti/gsp")
DATA = os.path.join(GSP, "data")
SUBMUN = os.path.join(DATA, "submun")
GEODATA = os.path.join(DATA, "geodata")
COMUNI_DIR = os.path.join(DATA, "comuni")
AVQ_DIR = os.path.join(DATA, "avq", "anni")

ANNO_SEZIONI = 2023          # edizione dei dati sezione (geometrie: 2021)


# ----------------------------------------------------------------------
# Regioni
# ----------------------------------------------------------------------

# 'cod_avq' e' il codice REGMf nei microdati AVQ. Di norma vale cod*10, ma
# la regola si rompe sul Trentino-Alto Adige, che in AVQ e' separato fra
# Bolzano e Trento: va tenuto esplicito.
REGIONI = {
    "lombardia": {
        "nome": "Lombardia", "cod": 3, "cod_avq": 30,
        "shp": "R03_21/SHP/R03_21_WGS84.shp",
        "anncsu": "indirizzarioLombardia20260703/INDIR_LOMB_20260703.csv",
    },
    "emilia_romagna": {
        "nome": "Emilia-Romagna", "cod": 8, "cod_avq": 80,
        "shp": "R08_21/SHP/R08_21_WGS84.shp",
        "anncsu": "indirizzarioEmilia-romagna20260703/INDIR_EMIL_20260703.csv",
    },
    "puglia": {
        "nome": "Puglia", "cod": 16, "cod_avq": 160,
        "shp": "R16_21/SHP/R16_21_WGS84.shp",
        "anncsu": "indirizzarioPuglia20260703/INDIR_PUGL_20260703.csv",
    },
}

# File dentro Dati_regionali_2023.zip, per codice regione ISTAT.
REGIONE_FILE = {
    1: "R01_Piemonte_2023_sezioni.xlsx",
    2: "R02_Valle d'Aosta_2023_sezioni.xlsx",
    3: "R03_Lombardia_2023_sezioni.xlsx",
    4: "R04_Trentino-Alto Adige_2023_sezioni.xlsx",
    5: "R05_Veneto_2023_sezioni.xlsx",
    6: "R06_Friuli-Venezia Giulia_2023_sezioni.xlsx",
    7: "R07_Liguria_2023_sezioni.xlsx",
    8: "R08_Emilia-Romagna_2023_sezioni.xlsx",
    9: "R09_Toscana_2023_sezioni.xlsx",
    10: "R10_Umbria_2023_sezioni.xlsx",
    11: "R11_Marche_2023_sezioni.xlsx",
    12: "R12_Lazio_2023_sezioni.xlsx",
    13: "R13_Abruzzo_2023_sezioni.xlsx",
    14: "R14_Molise_2023_sezioni.xlsx",
    15: "R15_Campania_2023_sezioni.xlsx",
    16: "R16_Puglia_2023_sezioni.xlsx",
    17: "R17_Basilicata_2023_sezioni.xlsx",
    18: "R18_Calabria_2023_sezioni.xlsx",
    19: "R19_Sicilia_2023_sezioni.xlsx",
    20: "R20_Sardegna_2023_sezioni.xlsx",
}

# Solo per dare un nome leggibile ai file provinciali dei civici.
PROVINCE_NOMI = {
    "012": "varese", "013": "como", "014": "sondrio", "015": "milano",
    "016": "bergamo", "017": "brescia", "018": "pavia", "019": "cremona",
    "020": "mantova", "097": "lecco", "098": "lodi", "108": "monza_brianza",
    "033": "piacenza", "034": "parma", "035": "reggio_emilia",
    "036": "modena", "037": "bologna", "038": "ferrara", "039": "ravenna",
    "040": "forli_cesena", "099": "rimini",
    "071": "foggia", "072": "bari", "073": "taranto", "074": "brindisi",
    "075": "lecce", "110": "barletta_andria_trani",
}


# ----------------------------------------------------------------------
# Denominazioni delle zone
# ----------------------------------------------------------------------

ASC_NOMI_BRESCIA = {
    "17029001": "Brescia Antica", "17029002": "Borgo Trento",
    "17029003": "Porta Milano", "17029004": "Centro Storico Nord",
    "17029005": "Chiusure", "17029006": "Don Bosco",
    "17029007": "Fiumicello", "17029008": "Folzano",
    "17029009": "Fornaci", "17029010": "Lamarmora",
    "17029011": "Mompiano", "17029012": "Porta Cremona",
    "17029013": "Buffalora", "17029014": "Porta Venezia",
    "17029015": "Villaggio Prealpino", "17029016": "Caionvico",
    "17029017": "S. Bartolomeo", "17029018": "S. Eufemia",
    "17029019": "S. Polo Case", "17029020": "Chiesanuova",
    "17029021": "Urago", "17029022": "Casazza",
    "17029023": "Villaggio Badia", "17029024": "Villaggio Sereno",
    "17029025": "Villaggio Violino", "17029026": "Primo Maggio",
    "17029027": "Centro Storico Sud", "17029028": "S. Eustacchio",
    "17029029": "S. Rocchino", "17029030": "Crocifissa Di Rosa",
    "17029031": "S. Polo Cimabue", "17029032": "San Polino",
    "17029033": "S. Polo Parco",
}

ASC_NOMI_PARMA = {
    "34027001": "Parma Centro", "34027002": "Oltretorrente",
    "34027003": "Molinetto", "34027004": "Pablo",
    "34027005": "Golese", "34027006": "San Pancrazio",
    "34027007": "San Leonardo", "34027008": "Cortile San Martino",
    "34027009": "Lubiana", "34027010": "San Lazzaro",
    "34027011": "Cittadella", "34027012": "Montanara",
    "34027013": "Vigatto",
}

# DA COMPLETARE: incollare i due dizionari dal registro di
# build_zona_tables.py, oppure generarli con
#     python gsp_common.py --dump-nomi 037006
ASC1_NOMI_BOLOGNA={
    "37006011": "Borgo Panigale-Reno",
    "37006012": "Navile",
    "37006013": "Porto-Saragozza",
    "37006014": "San Donato-San Vitale",
    "37006015": "Santo Stefano",
    "37006016": "Savena",
}      # 6 quartieri
# da zona_nomi.csv  (18 zone)
ASC2_NOMI_BOLOGNA = {
    "37006001": "Barca",           "37006010": "Malpighi",
    "37006002": "Bolognina",       "37006011": "Marconi",
    "37006003": "Borgo Panigale",  "37006012": "Mazzini",
    "37006004": "Colli",           "37006013": "Murri",
    "37006005": "Corticella",      "37006014": "Saffi",
    "37006006": "Costa Saragozza", "37006015": "San Donato",
    "37006007": "Galvani",         "37006016": "San Ruffillo",
    "37006008": "Irnerio",         "37006017": "Santa Viola",
    "37006009": "Lame",            "37006018": "San Vitale",
}    # 18 zone statistiche


# ----------------------------------------------------------------------
# Comuni — solo il non derivabile
# ----------------------------------------------------------------------

COMUNI = {
    "017029": {
        "nome": "Brescia", "slug": "brescia", "regione": "lombardia",
        "livello": "quartieri",
        "livelli": {
            "quartieri": {"col": "COM_ASC1", "n": 33,
                          "nomi": ASC_NOMI_BRESCIA, "parent": None},
        },
        # Fonte locale per il paese di cittadinanza: un CSV per quartiere.
        # Il nome del file non sempre coincide con la denominazione ISTAT.
        "opendata_paese": {
            "loader": "brescia",
            "geo_liv": "quartieri",      # livello ASC di riferimento
            "geo_col": "zona",           # colonna della popolazione su cui agganciare
            "sesso": False,              # la fonte distingue il sesso?
            "dir": "cittadinanza",
            "override_nome": {"chiesanuova-noce-girelli": "17029020"},
        },
    },
    "034027": {
        "nome": "Parma", "slug": "parma", "regione": "emilia_romagna",
        "livello": "quartieri",
        "livelli": {
            # ISTAT pubblica per Parma il solo COM_ASC1.
            "quartieri": {"col": "COM_ASC1", "n": 13,
                          "nomi": ASC_NOMI_PARMA, "parent": None},
        },
         "opendata_paese": {
            "loader": "parma",
            "geo_liv": "sezione",
            "geo_col": "sezione",
            "sesso": True,
        },
    },
    "037006": {
        "nome": "Bologna", "slug": "bologna", "regione": "emilia_romagna",
        # ASC1 = 6 quartieri: troppo pochi. ASC3 = 90 aree: coda di zone
        # da 13 abitanti, inutilizzabile. Si usa ASC2.
        "livello": "zone",
        "livelli": {
            "quartieri": {"col": "COM_ASC1", "n": 6,
                          "nomi": ASC1_NOMI_BOLOGNA, "parent": None},
            "zone": {"col": "COM_ASC2", "n": 18,
                     "nomi": ASC2_NOMI_BOLOGNA, "parent": "quartieri"},
        },
        "opendata_paese": {
            "loader": "bologna",
            "geo_liv": "zone",
            "geo_col": "zona",
            "sesso": True,
        },
    },
    "074017": {
        "nome": "San Vito dei Normanni", "slug": "san_vito_dei_normanni",
        "regione": "puglia",
        # ASC1 ha un solo valore: nessuna articolazione sub-comunale.
        "livello": None,
        "livelli": {},
    },
}

# ----------------------------------------------------------------------
# Traduzione delle denominazioni di paese
# ----------------------------------------------------------------------

# Le fonti comunali usano denominazioni diverse da quelle ISTAT, e sbagliano
# sugli stessi paesi in tutte e tre le citta': una sola tabella nazionale.
# Chiave e valore sono normalizzati con norm_nome().
SINONIMI_PAESE = {
    # forma ISTAT con denominazione storica fra parentesi
    "srilanka": "srilankaexceylon",
    "srilankaceylon": "srilankaexceylon",
    "burkinafaso": "burkinafasoexaltovolta",
    "benin": "beninexdahomey",
    "taiwan": "taiwanexformosa",
    "taiwanformosa": "taiwanexformosa",
    "zimbabwe": "zimbabweexrhodesia",
    "myanmarbirmania": "myanmarexbirmania",
    "myanmar": "myanmarexbirmania",
    # forma ISTAT invertita (sostantivo, qualificatore)
    "iran": "iranrepubblicaislamicadell",
    "repubblicaceca": "cecarepubblica",
    "repceca": "cecarepubblica",
    "repubblicadominicana": "dominicanarepubblica",
    "repdominicana": "dominicanarepubblica",
    "repubblicadiserbia": "serbiarepubblicadi",
    "serbia": "serbiarepubblicadi",
    "repcentrafricana": "centrafricanarepubblica",
    "macedoniadelnord": "macedoniaexrepubblicajugoslavadi",
    "macedonia": "macedoniaexrepubblicajugoslavadi",
    # nomi comuni vs ufficiali
    "federazionerussa": "russia",
    "russiafederazione": "russia",
    "repubblicapopolarechinese": "cina",
    "repubblicapopolarecinese": "cina",
    "statiunitidamerica": "statiuniti",
    "kenia": "kenya",
    "maurizio": "mauritius",
    "kazakistan": "kazakhstan",
    "coreadelsudrep": "coreadelsud",
    "repsudafricana": "sudafrica",
    # i due Congo: 'Congo' senza qualificatore e' Brazzaville, perche' le
    # fonti elencano separatamente la Repubblica Democratica
    "congo": "congorepubblicadel",
    "repdemdelcongozaire": "congorepubblicademocraticadelexzaire",
    "repubblicademocraticadelcongo": "congorepubblicademocraticadelexzaire",
    "sudsudan": "sudsudanrepubblicadel",
    "palestina": "territoridellautonomiapalestinese",
    "swaziland": "eswatini",
}

# Etichette che NON sono paesi: vanno nel gruppo residuale dell'IPF.
# 'ALTRE CITTADINANZE' e' la categoria residuale di Brescia, il cui
# contenuto cambia da quartiere a quartiere (e' il complemento della
# top-19 locale): non serve saperne il contenuto, basta sapere cosa esclude.
NON_PAESI = {
    "altrecittadinanze", "apolide", "apolidi", "italia",
    # stati storici senza corrispondente moderno
    "cecoslovacchia", "jugoslavia",
    "germaniarepdemocratica", "germaniarepfederale",
    "unionesovietica", "urss",
}

# Codici della codelist AREA_CONTRY_CITIZEN che NON sono paesi: continenti,
# macro-aree e totali. Filtrare per esclusione e non per forma del codice:
# i paesi hanno di norma un ISO alpha-2, ma non sempre (X95 Kosovo, che non
# ha codice ISO ufficiale; XSD_S Sud Sudan; 999 apolidi).
AGGREGATI_PAESE = {
    "ALL", "AFR", "AFR_C_S", "AFR_E", "AFR_N", "AFR_W",
    "AME", "AME_C_S", "AME_N", "ASI", "ASI_E", "ASI_W", "XASI_C_S",
    "EUR", "EUR_C_E", "EUR_OTH", "OCE",
    "EU",             # Unione europea: somma dei 27, gia' presenti singolarmente
    "999",            # apolidi: non uno Stato, va nel residuale
}


def paesi_censuari(comune: str, anno_cens: int = 2023) -> dict:
    """{nome normalizzato: codice} dei paesi censiti nel comune."""
    d = pd.read_csv(os.path.join(path_comune(comune),
                                 "cens_stranieri_paesi_decoded.csv"),
                    low_memory=False)
    d = d[d["TIME_PERIOD"].astype(str) == str(anno_cens)]
    t = d[["AREA_CONTRY_CITIZEN", "AREA_CONTRY_CITIZEN_label"]].dropna()
    t = t.drop_duplicates()
    t = t[~t["AREA_CONTRY_CITIZEN"].astype(str).isin(AGGREGATI_PAESE)]
    return {norm_nome(r.AREA_CONTRY_CITIZEN_label): r.AREA_CONTRY_CITIZEN
            for r in t.itertuples()}


def risolvi_paese(etichetta: str, riferimento: dict) -> str | None:
    """Etichetta di una fonte locale -> chiave normalizzata del censimento.

    Ritorna None se l'etichetta non e' un paese (categoria residuale,
    apolidi, stati storici) oppure se il paese non compare nel censimento
    di quel comune: in entrambi i casi va trattata come residuale.
    """
    k = norm_nome(etichetta)
    if k in NON_PAESI:
        return None
    k = SINONIMI_PAESE.get(k, k)
    return riferimento[k] if k in riferimento else None




# ----------------------------------------------------------------------
# Accesso e derivate
# ----------------------------------------------------------------------

def info(comune: str) -> dict:
    """Voce di registro del comune, con controllo di esistenza."""
    if comune not in COMUNI:
        raise KeyError(f"Comune {comune} non nel registro COMUNI di "
                       f"gsp_common.py. Presenti: {sorted(COMUNI)}")
    return COMUNI[comune]


def regione(comune: str) -> dict:
    """Voce di registro della regione del comune."""
    return REGIONI[info(comune)["regione"]]


def procom(comune: str) -> int:
    """017029 -> 17029. Chiave dei file sezioni e dei civici."""
    return int(comune)


def cod_prov(comune: str) -> str:
    """017029 -> '017'."""
    return comune[:3]


def cod_avq(comune: str) -> int:
    """Codice REGMf della regione nei microdati AVQ."""
    return regione(comune)["cod_avq"]


def livello_col(comune: str, livello: str | None = None) -> str:
    """Colonna COM_ASC* del livello zonale (default: quello del registro)."""
    i = info(comune)
    liv = livello or i["livello"]
    if liv is None:
        raise ValueError(f"{i['nome']} non ha articolazione sub-comunale")
    if liv not in i["livelli"]:
        raise KeyError(f"Livello '{liv}' non definito per {i['nome']}: "
                       f"disponibili {sorted(i['livelli'])}")
    return i["livelli"][liv]["col"]


def zona_nomi(comune: str, livello: str | None = None) -> dict:
    """{codice zona: denominazione} per il livello scelto."""
    i = info(comune)
    liv = livello or i["livello"]
    nomi = i["livelli"][liv]["nomi"]
    if nomi is None:
        raise ValueError(
            f"Denominazioni mancanti per {i['nome']} livello '{liv}'. "
            f"Generarle con: python gsp_common.py --dump-nomi {comune}")
    return nomi

def verifica_livello(codici, comune: str, livello: str | None = None) -> str:
    """Controlla che i codici zona appartengano al livello atteso.

    I livelli ASC sono numerati indipendentemente: a Bologna il codice
    37006011 vale 'Borgo Panigale-Reno' come COM_ASC1 e 'Marconi' come
    COM_ASC2. Un merge sul solo codice riesce e restituisce il nome
    sbagliato, senza errori ne' valori mancanti.
    """
    i = info(comune)
    liv = livello or i["livello"]
    if liv is None:
        return liv
    obs = {str(c).strip() for c in pd.Series(list(codici)).dropna().unique()}
    cop = {n: len(obs & set(c["nomi"])) / max(len(obs), 1)
           for n, c in i["livelli"].items() if c["nomi"]}
    if not cop:
        return liv
    if cop.get(liv, 0) < 1.0:
        best = max(cop, key=cop.get)
        raise ValueError(
            f"{i['nome']}: {len(obs)} codici zona, copertura sul livello "
            f"'{liv}' {cop.get(liv, 0):.0%}; livello piu' probabile "
            f"'{best}' ({cop[best]:.0%}). Verificare con quale --level e' "
            f"stata generata zona_{ANNO_SEZIONI}/.")
    return liv
# ----------------------------------------------------------------------
# Percorsi
# ----------------------------------------------------------------------

def path_sezioni(comune: str) -> str:
    return os.path.join(SUBMUN, f"{info(comune)['slug']}_sezioni_"
                                f"{ANNO_SEZIONI}.csv")


def path_civici(comune: str) -> str:
    p = cod_prov(comune)
    return os.path.join(GEODATA, info(comune)["regione"],
                        "civici_sezioni_province",
                        f"{p}_{PROVINCE_NOMI.get(p, 'prov' + p)}"
                        f"_civici_sezioni_asc.csv")


def path_comune(comune: str) -> str:
    return os.path.join(COMUNI_DIR, comune)


def path_constraints(comune: str, anno: int) -> str:
    return os.path.join(COMUNI_DIR, comune, f"constraints_{anno}")


def path_zona(comune: str) -> str:
    return os.path.join(COMUNI_DIR, comune, f"zona_{ANNO_SEZIONI}")


def path_shp(reg: str) -> str:
    return os.path.join(GEODATA, reg, REGIONI[reg]["shp"])


def path_anncsu(reg: str) -> str:
    return os.path.join(GEODATA, reg, REGIONI[reg]["anncsu"])


def path_regionale_xlsx(reg: str) -> str:
    """File regionale delle sezioni, dentro Dati_regionali_2023."""
    return os.path.join(SUBMUN, "Dati_regionali_2023",
                        REGIONE_FILE[REGIONI[reg]["cod"]])


# ----------------------------------------------------------------------
# Primitive
# ----------------------------------------------------------------------

def largest_remainder(n: int, shares) -> np.ndarray:
    """Alloca n unita' intere secondo shares (metodo del resto maggiore).

    Preferito al campionamento multinomiale ovunque nella pipeline: i
    conteggi censuari sono enumerazione completa, quindi vanno riprodotti
    e non campionati. Sul MAE per sezione la differenza e' un fattore ~6.
    """
    shares = np.asarray(shares, dtype=float)
    shares = np.where(np.isfinite(shares) & (shares > 0), shares, 0.0)
    if n == 0 or shares.sum() <= 0:
        return np.zeros(len(shares), dtype=int)
    exp = n * shares / shares.sum()
    base = np.floor(exp).astype(int)
    resto = n - base.sum()
    if resto > 0:
        base[np.argsort(-(exp - base))[:resto]] += 1
    return base


def spartisci(idx: np.ndarray, conta, valori) -> pd.Series:
    """Assegna i valori agli indici secondo i conteggi (idx gia' mescolato)."""
    out = np.empty(len(idx), dtype=object)
    s = 0
    for v, c in zip(valori, conta):
        out[s:s + c] = v
        s += c
    return pd.Series(out, index=idx)


def norm_code(s: pd.Series, comune: str) -> pd.Series:
    """Codice zona -> stringa intera senza '.0', zeri iniziali e prefisso
    PROCOM: '37006009' -> '9', '9.0' -> '9', '09' -> '9'."""
    pc = str(procom(comune))

    def f(x: str) -> str:
        x = str(x).strip()
        if x.endswith(".0"):
            x = x[:-2]
        if x.startswith(pc) and len(x) > len(pc):
            x = x[len(pc):]
        return x.lstrip("0") or "0"

    return s.astype(str).map(f)


def norm_nome(s) -> str:
    """Normalizza una denominazione per il confronto: minuscole, senza
    accenti ne' punteggiatura. Serve a incrociare i nomi di quartiere fra
    fonti diverse ('S.Leonardo' e 'San Leonardo' restano pero' distinti:
    le abbreviazioni vanno gestite con una mappa di eccezioni)."""
    t = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", t.lower())


# ----------------------------------------------------------------------
# Self-test
# ----------------------------------------------------------------------

def _check_comune(comune: str, anno: int = 2024) -> list[str]:
    """Verifica un comune. Ritorna la lista dei problemi trovati."""
    err = []
    i = info(comune)
    print(f"\n[{comune}] {i['nome']} ({i['regione']})")

    if i["regione"] not in REGIONI:
        err.append(f"regione '{i['regione']}' non in REGIONI")
        return err

    p = cod_prov(comune)
    if p not in PROVINCE_NOMI:
        err.append(f"provincia {p} senza nome in PROVINCE_NOMI")

    # --- file sezioni ---
    fs = path_sezioni(comune)
    if not os.path.exists(fs):
        err.append(f"sezioni assenti: {fs}")
        print(f"  sezioni      MANCANTE")
    else:
        sez = pd.read_csv(fs, low_memory=False)
        print(f"  sezioni      {len(sez):,} righe | P1 = {int(sez['P1'].sum()):,}")

        liv = i["livello"]
        if liv is None:
            print(f"  livello      nessuno (comune senza sub-aree)")
        elif liv not in i["livelli"]:
            err.append(f"livello '{liv}' non fra i livelli definiti")
        else:
            cfg = i["livelli"][liv]
            col = cfg["col"]
            if col not in sez.columns:
                err.append(f"colonna {col} assente nel file sezioni")
            else:
                v = pd.to_numeric(sez[col], errors="coerce").fillna(0)
                codici = sorted(str(int(x)) for x in v[v != 0].unique())
                n = len(codici)
                ok = "ok" if n == cfg["n"] else f"ATTESE {cfg['n']}"
                print(f"  livello      {liv} ({col}): {n} zone [{ok}]")
                if n != cfg["n"]:
                    err.append(f"{col}: {n} zone, attese {cfg['n']}")

                nomi = cfg["nomi"]
                if nomi is None:
                    err.append(f"denominazioni mancanti per '{liv}' "
                               f"(usare --dump-nomi {comune})")
                    print(f"  nomi         MANCANTI")
                else:
                    orfani = [c for c in codici if c not in nomi]
                    fantasmi = [c for c in nomi if c not in codici]
                    if orfani:
                        err.append(f"codici senza nome: {orfani[:5]}")
                    if fantasmi:
                        err.append(f"nomi senza codice: {fantasmi[:5]}")
                    if not orfani and not fantasmi:
                        print(f"  nomi         {len(nomi)} denominazioni [ok]")

    # --- civici ---
    fc = path_civici(comune)
    if not os.path.exists(fc):
        err.append(f"civici assenti: {fc}")
        print(f"  civici       MANCANTE")
    else:
        print(f"  civici       {os.path.getsize(fc)/1e6:.0f} MB "
              f"({os.path.basename(fc)})")

    # --- directory di lavoro ---
    for nome, pth in [("comune", path_comune(comune)),
                      ("vincoli", path_constraints(comune, anno)),
                      ("zona", path_zona(comune))]:
        stato = "ok" if os.path.isdir(pth) else "assente"
        if stato == "assente" and nome == "comune":
            err.append(f"directory comune assente: {pth}")
        print(f"  dir {nome:<9}{stato}")

    print(f"  AVQ          regione {cod_avq(comune)} "
          f"({REGIONI[i['regione']]['nome']})")
    return err


def check(comuni: list[str] | None = None, anno: int = 2024) -> int:
    """Verifica il registro contro i file su disco. Ritorna il n. di errori."""
    target = comuni or sorted(COMUNI)
    print("=" * 66)
    print(f"gsp_common — verifica registro ({len(target)} comuni)")
    print("=" * 66)

    # regioni
    print("\n[regioni]")
    tot = []
    for r, cfg in REGIONI.items():
        s_ok = "ok" if os.path.exists(path_shp(r)) else "MANCANTE"
        a_ok = "ok" if os.path.exists(path_anncsu(r)) else "MANCANTE"
        print(f"  {r:<16} shp {s_ok:<9} anncsu {a_ok}")
        if s_ok != "ok":
            tot.append(f"[{r}] shapefile assente")
        if a_ok != "ok":
            tot.append(f"[{r}] ANNCSU assente")

    for c in target:
        tot += [f"[{c}] {e}" for e in _check_comune(c, anno)]

    print("\n" + "=" * 66)
    if tot:
        print(f"{len(tot)} PROBLEMI:")
        for e in tot:
            print(f"  - {e}")
    else:
        print("tutto verde")
    print("=" * 66)
    return len(tot)


def dump_nomi(comune: str) -> None:
    """Stampa le denominazioni delle zone leggendole da zona_{anno}/,
    in forma pronta da incollare nel registro."""
    d = path_zona(comune)
    cand = sorted(glob.glob(os.path.join(d, "*nomi*.csv")))
    if not cand:
        sys.exit(f"Nessun file *nomi*.csv in {d}\n"
                 f"  eseguire prima build_zona_tables.py {comune}")
    for f in cand:
        t = pd.read_csv(f, dtype=str)
        cod_c = next((c for c in t.columns if "zona" in c.lower()
                      or "asc" in c.lower() or "cod" in c.lower()), t.columns[0])
        nom_c = next((c for c in t.columns if "nome" in c.lower()), t.columns[-1])
        print(f"\n# da {os.path.basename(f)}  ({len(t)} zone)")
        print("{")
        for _, r in t.iterrows():
            print(f'    "{str(r[cod_c]).strip()}": "{str(r[nom_c]).strip()}",')
        print("}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--dump-nomi" in args:
        k = args.index("--dump-nomi")
        if k + 1 >= len(args):
            sys.exit("--dump-nomi richiede il codice comune")
        dump_nomi(args[k + 1])
    elif "--check" in args:
        k = args.index("--check")
        c = [a for a in args[k + 1:] if not a.startswith("--")]
        sys.exit(1 if check(c or None) else 0)
    else:
        print(__doc__)
        print(f"comuni nel registro: {sorted(COMUNI)}")
        print(f"regioni nel registro: {sorted(REGIONI)}")
