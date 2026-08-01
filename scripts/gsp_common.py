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

# Verificato su due assi indipendenti (29/07/2026): baricentri dei civici
# ANNCSU — Centro Storico compatto (raggio 0,68 km contro 2,2–3,1) e le tre
# direzioni cardinali coerenti coi nomi — e concentrazione dei toponimi,
# 5 su 5 al 100% nel quartiere che li nomina.
ASC_NOMI_MODENA = {
    "36023001": "Centro Storico",
    "36023002": "Crocetta, San Lazzaro, Modena Est",
    "36023003": "Buon Pastore, Sant'Agnese, San Damaso",
    "36023004": "San Faustino, Madonnina, Quattro Ville",
}

# Verificato con zona_probe.py (31/07/2026): baricentri dei civici ANNCSU e
# concentrazione dei toponimi. ATTENZIONE: i codici NON sono 001-010, c'e' un
# salto su 004-006. L'ordinamento ufficiale del Comune (1 Centro Urbano ...
# 10 Del Mare) e' pero' preservato. Riscontri diretti: PIANGIPANE 97% su 009,
# RONCALCECI 100% su 010, toponimi marittimi su 013 (raggio 5,48 km, massimo).
ASC_NOMI_RAVENNA = {
    "39014001": "Centro Urbano",
    "39014002": "Ravenna Sud",
    "39014003": "Darsena",
    "39014007": "Sant'Alberto",
    "39014008": "Mezzano",
    "39014009": "Piangipane",
    "39014010": "Roncalceci",
    "39014011": "San Pietro in Vincoli",
    "39014012": "Castiglione",
    "39014013": "Del Mare",
}

# Verificato con zona_probe.py (31/07/2026). Codici 001-021 consecutivi.
# Riscontri diretti: SISA/CARPENELLA/BAGNOLINA su 005, CAVA su 010,
# CAMPO MARTE su 013, toponimi aeronautici su 015, MAGLIANELLA su 021.
# Da verificare: 016 e 017 (il toponimo OSSI cade su 018).
# I 21 quartieri sono raggruppati in 8 comitati territoriali, ma il
# raggruppamento NON e' nel file ISTAT (COM_ASC2/3 sono a zero).
ASC_NOMI_FORLI = {
    "40012001": "Centro Storico",
    "40012002": "Villafranca, San Martino in Villafranca",
    "40012003": "Roncadello, Branzolino, San Tomè, Barisano",
    "40012004": "Pieve Acquedotto, Durazzanino, Malmissole, Poggio, San Giorgio",
    "40012005": "Carpinello, Castellaccio, Bagnolo, Borgo Sisa",
    "40012006": "Pievequinta, Casemurate, Caserma",
    "40012007": "La Selva, Forniolo, San Leonardo",
    "40012008": "Pianta, Ospedaletto, Coriano",
    "40012009": "Foro Boario, San Benedetto",
    "40012010": "Cava, Villanova",
    "40012011": "Romiti",
    "40012012": "Resistenza",
    "40012013": "Spazzoli, Campo di Marte, Benefattori",
    "40012014": "Musicisti, Grandi Italiani",
    "40012015": "Ronco",
    "40012016": "Bussecchio",
    "40012017": "Ca' Ossi",
    "40012018": "Villagrappa, Castiglione, Petrignone, San Varano, Rovere",
    "40012019": "Vecchiazzano, Massa, Ladino",
    "40012020": "San Martino in Strada, San Lorenzo in Noceto, Grisignano",
    "40012021": "Magliano, Carpena, Ravaldino in Monte, Lardiano",
}

# Verificato con zona_probe.py (1/8/2026): i quattro baricentri
# corrispondono ai nomi. 001 al raggio minimo (0,60 km) e' il centro;
# 002 a -3,60 km est = Ovest; 003 a -2,58 km nord = Sud;
# 004 a +2,87 km est = Nordest.
ASC_NOMI_REGGIO = {
    "35033001": "Città storica",
    "35033002": "Ovest",
    "35033003": "Sud",
    "35033004": "Nordest",
}
# verificato .....
ASC_NOMI_RIMINI = {
    "99014001": "Centro storico - Marina Centro - San Giuliano",
    "99014002": "Borgo San Giovanni - Lagomaggio",
    "99014003": "Bellariva - Miramare",
    "99014004": "Borgo Mazzini - INA Casa - Vergiano - Corpolò",
    "99014005": "Celle - Viserba - San Vito - Santa Giustina",
    "99014006": "V PEEP Ausa - Grotta Rossa - Gaiofana",
}

# Piacenza non ha denominazioni ufficiali sintetiche: le fonti comunali
# usano "ex Quartiere N". La lettura geografica fra parentesi e' NOSTRA,
# ricavata dai baricentri ANNCSU (zona_probe, 1/8/2026) e coerente con
# l'elenco comunale delle strade per ex quartiere.
# Ancore: CORNEGLIANA 100% su 003 (elenco: Q3), FARNESIANA 401 civici
# 100% su 004 (la sede della circoscrizione 4 era al c.c. Farnesiana),
# STRADONE FARNESE e CITTADELLA su 001 con raggio 0,62 km (il minimo).
# DISSONANZA: l'elenco comunale mette via Malchioda nel Q4, ma i civici
# la danno 118 al 100% su 002. Una strada sola; da riverificare se
# emergessero altre incoerenze.
ASC_NOMI_PIACENZA = {
    "33032001": "Ex Quartiere 1 (Centro storico)",
    "33032002": "Ex Quartiere 2 (Ovest)",
    "33032003": "Ex Quartiere 3 (Sud)",
    "33032004": "Ex Quartiere 4 (Est)",
}

# Ordine di preferenza dei file popolazione, dal livello piu' ricco al piu'
# povero. Condiviso fra enrich.py e assign_nationality.py: due auto-detect
# divergenti sono un modo sicuro di generare confusione.
POP_CANDIDATES = ["popolazione_K10C.csv", "popolazione_K9C.csv",
                  "popolazione_K8C.csv", "popolazione_K7C.csv",
                  "popolazione_K6C.csv"]


def resolve_pop_file(cdir, override=None, suffisso=""):
    """Nome del file popolazione da usare in cdir.

    override  nome esplicito: restituito senza controlli
    suffisso  variante da cercare (es. '_avq' -> popolazione_K9C_avq.csv)
    """
    if override:
        return override
    cercati = [n.replace(".csv", f"{suffisso}.csv") if suffisso else n
               for n in POP_CANDIDATES]
    for name in cercati:
        if os.path.exists(os.path.join(cdir, name)):
            return name
    raise SystemExit(f"Nessun file popolazione in {cdir}\n"
                     f"  cercati: {cercati}\n"
                     f"  usare --pop-file per specificarlo")


# Set standard delle variabili AVQ (v2, 1 ago 2026).
#
# FIDUCIA e' fiducia INTERPERSONALE generalizzata, a polarita' invertita.
# La fiducia ISTITUZIONALE sta nelle PUNTIFI* e in FIDMED/FIDINF, tutte
# su scala 0-10 (0 = per niente, 10 = completamente):
#   PUNTIFI1  Parlamento italiano      PUNTIFI8   Governo regionale
#   PUNTIFI2  sistema giudiziario      PUNTIFI10  Governo comunale
#   PUNTIFI3  forze dell'ordine        PUNTIFI12  vigili del fuoco
#   PUNTIFI4  partiti politici         FIDMED     medici del SSN
#   PUNTIFI5  Parlamento europeo       FIDINF     infermieri del SSN
#   PUNTIFI6  Pres. della Repubblica   PUNTIFI13  banche
#   PUNTIFI7  Governo italiano         FORZE_ARMATE
# PUNTIFI9 e PUNTIFI11 non esistono nel tracciato.
#
# Copertura attesa nel pool 2023+2024 (il 2022 e' escluso: manca CRONI):
#   ~97%  CPESO
#   ~88%  FIDMED, FIDINF, PUNTIFI1/2/3/4/5/8/10/12, BMI
#   ~43%  PUNTIFI6, PUNTIFI7, PUNTIFI13   (solo annata 2024)
#   ~21%  FORZE_ARMATE                    (solo 2024, e ivi al 42,7%)
#   ~19%  VOTOUSL                         (solo 2024, e ivi al 37,9%)
# Il missing e' STRUTTURALE (annata del donatore o universo della domanda),
# non individuale: il sottocampione con valore e' casuale.
#
# Esclusa BMIMIN: e' l'indice di massa corporea per MINORI (cut-off IOTF),
# universo diverso da BMI (18+), non una variabile a bassa copertura.
AVQ_TARGETS = ["AMBIENTE", "FIDUCIA", "SALUTE", "CRONI", "FUMO", "MH"]
AVQ_OPZIONALI = [
    "FIDMED", "FIDINF",
    "PUNTIFI1", "PUNTIFI2", "PUNTIFI3", "PUNTIFI4", "PUNTIFI5",
    "PUNTIFI8", "PUNTIFI10", "PUNTIFI12",
    "PUNTIFI6", "PUNTIFI7", "PUNTIFI13",
    "FORZE_ARMATE", "VOTOUSL",
    "BMI", "CPESO",
]

# Combinazioni logicamente IMPOSSIBILI, per nome di categoria.
# (variabile A, valori A, variabile B, valori B, motivo)
#
# Servono perche' assenza di vincolo NON e' vincolo a zero: una cella che
# nessun blocco copre riceve dalla MaxEnt la probabilita' che le compete
# per indipendenza. Su Parma questo produceva 9-14enni con diploma o
# laurea; il tasso di combinazioni impossibili misurato e' 2,64-2,74%.
#
# Le soglie sono AMMINISTRATIVE, non stimate: l'universo dell'istruzione
# censuaria parte da 9 anni, quello della condizione professionale da 15,
# e i titoli si conseguono a 18/20/22 anni.
#
# Usate da cs_build.py (--esclusioni) e da animarium/build/ispeziona_cs.py.
IMPOSSIBILI = [
    ("eta", ["0-8", "9-14"],
     "condizione", ["occupato", "in_cerca", "studente", "casalinga",
                    "percettore_pensioni", "altra_condizione"],
     "condizione professionale ha universo 15 anni e piu'"),
    ("eta", ["15-24", "25-34", "35-49", "50-64", "65-74", "75+"],
     "condizione", ["non_applicabile"],
     "sopra i 15 anni la condizione e' sempre applicabile"),
    ("eta", ["0-8"],
     "istruzione", ["elementare", "media", "diploma", "laurea_o_its",
                    "post_laurea"],
     "universo dell'istruzione: 9 anni e piu'"),
    ("eta", ["9-14"],
     "istruzione", ["diploma", "laurea_o_its", "post_laurea"],
     "soglie minime di conseguimento: 18, 20, 22 anni"),
]
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
    "036023": {
        "nome": "Modena", "slug": "modena", "regione": "emilia_romagna",
        "livello": "quartieri",
        "livelli": {
            # Solo ASC1, 4 zone da ~46.000 abitanti: la partizione piu'
            # grossolana fra i comuni in pipeline. Il lavoro geografico lo
            # fa l'anello 3 (546 sezioni per zona).
            "quartieri": {"col": "COM_ASC1", "n": 4,
                          "nomi": ASC_NOMI_MODENA, "parent": None},
        },
    },

    "039014": {
        "nome": "Ravenna", "slug": "ravenna", "regione": "emilia_romagna",
        "livello": "aree",
        "livelli": {
            # Il Comune le chiama "aree territoriali", non quartieri: 3 urbane
            # (001-003) e 7 rurali su 652 km2. Codici non contigui.
            "aree": {"col": "COM_ASC1", "n": 10,
                     "nomi": ASC_NOMI_RAVENNA, "parent": None},
        },
        "opendata_paese": {
            "loader": "ravenna",
            "geo_liv": "aree",
            # il file usa abbreviazioni proprie per le aree
            "override_nome": {
                "CENTRO URBANO": "39014001",
                "RAVENNA SUD":   "39014002",
                "DARSENA":       "39014003",
                "S. ALBERTO":    "39014007",
                "MEZZANO":       "39014008",
                "PIANGIPANE":    "39014009",
                "RONCALCECI":    "39014010",
                "S.P.VINCOLI":   "39014011",
                "CASTIGLIONE":   "39014012",
                "MARE":          "39014013",
            },
            # denominazioni comunali -> etichette censuarie ISTAT.
            # Ricavate dal confronto delle due liste (2023): 20 coppie su 21
            # ISTAT non appaiate. L'unica orfana e' 'Maldive' (2 persone),
            # assente dal file comunale.
            "alias_paese": {
                "MACEDONIA":                  "Macedonia, Ex Repubblica Jugoslava di",
                "RUSSA, Federazione":         "Russia",
                "REP. S.MARINO":              "San Marino",
                "AFGANISTAN":                 "Afghanistan",
                "IRAN":                       "Iran, Repubblica islamica dell'",
                "REP. DOMINICANA":            "Dominicana, Repubblica",
                "GRAN BRETAGNA":              "Regno unito",
                "REP. CECA":                  "Ceca, Repubblica",
                "REP. SLOVACCA":              "Slovacchia",
                "KAZAKISTAN":                 "Kazakhstan",
                "PERU'":                      "Perù",
                "TAILANDIA":                  "Thailandia",
                "CONGO rep.":                 "Congo (Repubblica del)",
                "PALESTINA":                  "Territori dell'Autonomia Palestinese",
                "KENIA":                      "Kenya",
                "CAPOVERDE":                  "Capo Verde",
                "CONGO rep.Dem.(Zaire)":      "Congo, Repubblica democratica del (ex Zaire)",
                "SALVADOR":                   "El Salvador",
                "COREA rep.(Corea del sud)":  "Corea del sud",
                "ARABIA":                     "Arabia Saudita",
                "BENIN (Dahomey)":     "Benin (ex Dahomey)",
                "ZIMBABWE (Rhodesia)": "Zimbabwe (ex Rhodesia)",
            },
        },
    },
    "040012": {
        "nome": "Forlì", "slug": "forli", "regione": "emilia_romagna",
        "livello": "quartieri",
        "livelli": {
            # Partizione ibrida: 11 quartieri urbani entro 2,3 km dal centro
            # e 10 ambiti rurali fra 4 e 10 km. Zona piu' piccola: 1.588 ab.
            "quartieri": {"col": "COM_ASC1", "n": 21,
                          "nomi": ASC_NOMI_FORLI, "parent": None},
        },
        "opendata_paese": {
            "loader": "forli",
            "geo_liv": "quartieri",
            "etichette_residuo": ["altro"],
            # La fonte disaggrega in 41 unita' che si aggregano nei 21
            # quartieri COM_ASC1. Mappa ricavata dall'elenco ufficiale;
            # 'in corso di definizione' (9 persone) non e' territoriale.
            "mappa_unita": {
                "SCHIAVONIA SAN BIAGIO": "40012001",
                "SAN PIETRO": "40012001",
                "RAVALDINO": "40012001",
                "COTOGNI": "40012001",
                "VILLAFRANCA": "40012002",
                "SAN MARTINO IN VILLAFRANCA": "40012002",
                "RONCADELLO": "40012003",
                "BRANZOLINO": "40012003",
                "SAN TOME'": "40012003",
                "BARISANO": "40012003",
                "PIEVE ACQUEDOTTO": "40012004",
                "DURAZZANINO": "40012004",
                "MALMISSOLE": "40012004",
                "POGGIO": "40012004",
                "SAN GIORGIO": "40012004",
                "CARPINELLO CASTELLACCIO ROTTA": "40012005",
                "BAGNOLO": "40012005",
                "DURAZZANO BORGO SISA": "40012005",
                "PIEVEQUINTA CASEMURATE CASERMA": "40012006",
                "LA SELVA FORNIOLO": "40012007",
                "SAN LEONARDO": "40012007",
                "PIANTA OSPEDALETTO CORIANO": "40012008",
                "FORO BOARIO": "40012009",
                "SAN BENEDETTO": "40012009",
                "CAVA": "40012010",
                "VILLANOVA": "40012010",
                "ROMITI": "40012011",
                "RESISTENZA": "40012012",
                "SPAZZOLI CAMPO DI MARTE BENEFATTORI": "40012013",
                "MUSICISTI GRANDI ITALIANI": "40012014",
                "RONCO": "40012015",
                "BUSSECCHIO": "40012016",
                "CA'OSSI": "40012017",
                "VILLAGRAPPA CASTIGLIONE PETRIGNONE CIOLA": "40012018",
                "SAN VARANO": "40012018",
                "ROVERE": "40012018",
                "VECCHIAZZANO MASSA LADINO": "40012019",
                "SAN MARTINO IN STRADA GRISIGNANO COLLINA": "40012020",
                "SAN LORENZO IN NOCETO": "40012020",
                "MAGLIANO RAVALDINO IN MONTE LARDIANO": "40012021",
                "CARPENA": "40012021",
            },
            
            # DA VERIFICARE contro cens_stranieri_paesi_decoded.csv:
            # le etichette ISTAT sotto sono ricostruite per analogia con
            # Ravenna, non lette. La Cina e' il secondo gruppo (1.962
            # persone): se il suo alias non fa presa, il loader lo segnala.
            "alias_paese": {
                "REPUBBLICA POPOLARE CINESE": "Cina",
                "MACEDONIA DEL NORD":         "Macedonia, Ex Repubblica Jugoslava di",
                "FEDERAZIONE RUSSA":          "Russia",
                "REPUBBLICA DOMINICANA":      "Dominicana, Repubblica",
                "BURKINA FASO":               "Burkina Faso (ex Alto Volta)",
                "PERU'":                      "Perù",
            },
        },
    },
    "037021": {
        "nome": "Castenaso", "slug": "castenaso", "regione": "emilia_romagna",
        # Nessun livello ASC popolato nel file regionale 2023: le quattro
        # frazioni dello Statuto (Fiesso, Marano, Veduro, Villanova) non
        # sono codificate da ISTAT. Comune K6C, senza coordinata zona.
        "livello": None,
        "livelli": {},
    },
    "038008": {
        "nome": "Ferrara", "slug": "ferrara", "regione": "emilia_romagna",
        # COM_ASC1/2/3 tutti a zero nel file regionale 2023: ISTAT non
        # codifica alcuna partizione sub-comunale. Comune K6C, gestito con
        # zona degenere unica (vedi load_sezioni in enrich.py). Terzo caso
        # dopo Castenaso; qui pero' su scala reale, 129.391 abitanti e
        # 1.761 sezioni.
        "livello": None,
        "livelli": {},
    },
    "035033": {
        "nome": "Reggio nell'Emilia", "slug": "reggio_emilia",
        "regione": "emilia_romagna",
        "livello": "circoscrizioni",
        "livelli": {
            # Partizione per quadranti: centro storico piu' tre settori
            # cardinali. 42.800 abitanti per zona, la seconda piu'
            # grossolana in pipeline dopo Modena (46.149).
            "circoscrizioni": {"col": "COM_ASC1", "n": 4,
                               "nomi": ASC_NOMI_REGGIO, "parent": None},
        },
        "opendata_paese": {
            "loader": "reggio",
            "geo_liv": "circoscrizioni",
            "encoding": "latin-1",
            "etichette_residuo": ["Altre nazionalità"],
            # ATTENZIONE: la fonte comunale e' del 2013, contro il 2023
            # delle sezioni. L'assunzione di stabilita' strutturale e'
            # stata VERIFICATA il 1/8/2026 sulla quota UE per zona: ranghi
            # 4-2-1-3 nel 2013 contro 4-1-2-3 nel 2023, con l'unico
            # scambio fra due zone che nel 2023 distano 0,003 (rumore).
            # Le quote sono cresciute di 2-4 punti in modo uniforme, quindi
            # la FORMA condizionale regge anche se i livelli no.
            # La fonte non distingue il sesso: lo ricostruisce l'IPF dal
            # margine comunale, come per Brescia.
            "mappa_unita": {
                "Città storica": "35033001",
                "Ovest":         "35033002",
                "Sud":           "35033003",
                "Nordest":       "35033004",
            },
            "alias_paese": {
                "Moldavia":              "Moldova",
                "Russia, Federazione":   "Russia",
                "Repubblica Dominicana": "Dominicana, Repubblica",
                "Costa Avorio":          "Costa d'Avorio",
                "Burkina Faso":          "Burkina Faso (ex Alto Volta)",
                "Repubblica Ceca":       "Ceca, Repubblica",
            },
        },
    },
    "099014": {
        "nome": "Rimini", "slug": "rimini", "regione": "emilia_romagna",
        "livello": "quartieri",
        "livelli": {
            # Sei ex-quartieri, disposti lungo l'asse litoraneo: 001 centro
            # (raggio 0,70 km, il minimo), 003 e 005 agli estremi opposti
            # della costa, 006 entroterra verso San Marino. Denominazioni
            # verificate con zona_probe.py (1/8/2026): LAGOMAGGIO 100% su
            # 002, CORIANO/MONTESCUDO/MONTE TITANO su 006, D'AUGUSTO e
            # DESTRA PORTO su 001.
            # NOTA: nel 2025 il Comune ha istituito 12 NUOVI quartieri.
            # I dati comunali dal 2025 in poi NON sono agganciabili a
            # COM_ASC1, che resta sui 6 del censimento 2023.
            "quartieri": {"col": "COM_ASC1", "n": 6,
                          "nomi": ASC_NOMI_RIMINI, "parent": None},
        },
        # tier 0: il portale statistico pubblica gli stranieri per
        # quartiere solo come totali, non per paese di cittadinanza.
        # Bollettini demografici in PDF, nessun CSV con paese x geografia.
        # Contatto per una eventuale richiesta: opendata@comune.rimini.it
    },
    "033032": {
        "nome": "Piacenza", "slug": "piacenza", "regione": "emilia_romagna",
        "livello": "quartieri",
        "livelli": {
            # Quattro ex circoscrizioni disposte a quadranti attorno al
            # centro: 25.700 abitanti per zona, configurazione analoga a
            # Modena e Reggio.
            "quartieri": {"col": "COM_ASC1", "n": 4,
                          "nomi": ASC_NOMI_PIACENZA, "parent": None},
        },
        # tier 0: l'Annuario Statistico comunale rielabora AP11, POSAS e
        # STRASA, tutte fonti ISTAT a livello COMUNALE — quindi il
        # dettaglio paese x quartiere non puo' esistere in quel canale.
        # Da riprovare se l'Ufficio Statistica pubblicasse elaborazioni
        # dall'anagrafe interna. Contatto: portale opendata.comune.piacenza.it
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

# Paesi UE27 in codice ISO alpha-2. Classificare per codice e non per
# etichetta e' piu' robusto: le denominazioni ISTAT sono invertite
# ('Ceca, Repubblica') e il confronto per stringa e' fragile.
# La lista si verifica sommando i 27 e confrontando con l'aggregato 'EU'
# della stessa tavola censuaria.
EU27_ISO = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR",
    "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL",
    "PT", "RO", "SE", "SI", "SK",
}


def etichette_paese(comune: str, anno_cens: int = 2023) -> dict:
    """{codice: etichetta ISTAT} dei paesi censiti nel comune."""
    d = pd.read_csv(os.path.join(path_comune(comune),
                                 "cens_stranieri_paesi_decoded.csv"),
                    low_memory=False)
    d = d[d["TIME_PERIOD"].astype(str) == str(anno_cens)]
    t = (d[["AREA_CONTRY_CITIZEN", "AREA_CONTRY_CITIZEN_label"]]
         .dropna().drop_duplicates())
    t = t[~t["AREA_CONTRY_CITIZEN"].astype(str).isin(AGGREGATI_PAESE)]
    return dict(zip(t["AREA_CONTRY_CITIZEN"],
                    t["AREA_CONTRY_CITIZEN_label"]))


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

def tier(comune: str) -> int:
    """Tier del condizionale geografico per `paese`.

    Derivato da `opendata_paese` invece che dichiarato in un campo proprio:
    un campo puo' divergere dalla fonte che descrive, una derivazione no.

        0  nessuna fonte locale: `paese` non ha struttura sub-comunale, e
           ogni sua variazione spaziale e' compositiva per costruzione
        1  fonte a livello di zona/quartiere/area/circoscrizione
        2  fonte a livello di zona con dettaglio di sesso
        3  microdati per sezione
    """
    od = info(comune).get("opendata_paese")
    if not od:
        return 0
    liv = od.get("geo_liv")
    if liv is None:
        raise ValueError(f"{comune}: opendata_paese senza geo_liv")
    return {"sezione": 3, "zone": 2}.get(liv, 1)

    if not od:
        return 0
    return {"sezione": 3, "zone": 2}.get(od.get("geo_liv"), 1)


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
