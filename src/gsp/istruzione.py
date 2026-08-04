"""Titoli di studio dettagliati, dal censimento 2011.

    import gsp.istruzione as I

    I.verifica()                     # la partizione regge?
    I.repertorio("diploma", sesso="M", eta="35-49")

PERCHE'. La popolazione sintetica ha sei categorie di `istruzione`, che
il MaxEnt condiziona su sesso, eta' e zona. Dentro ciascuna, quale titolo
esattamente — «istituto tecnico industriale» invece di «diploma» — non e'
un attributo della popolazione ma una DERIVAZIONE, come il nome: si
calcola quando serve e non finisce in nessun file.

DUE FONTI, COMPLEMENTARI. E' la stessa divisione del lavoro fra margine A
e margine B in opendata_paese:

  cens2011_titolo_studio   quante persone avevano ciascun titolo, per
                           sesso, eta' e regione  ->  i PESI
  claist_2026              quali titoli esistono, come si chiamano oggi,
                           per quale coorte erano ottenibili  ->  il
                           VOCABOLARIO e i vincoli temporali

L'ALBERO E' DICHIARATO DALLA FONTE. Il codebook del censimento ha una
colonna `padre`, e i nodi radice puntano a se' stessi. Non va dedotto dai
codici — cosa che sembrava possibile e non lo e': `01999` (analfabeta) e
`001999` (nessun titolo) differiscono di uno zero iniziale ma sono figlio
e padre, e qualunque normalizzazione della lunghezza li fonderebbe.

SI PESCA SOLO DALLE FOGLIE. Un nodo che ha figli e' un aggregato: usarlo
insieme ai figli conterebbe due volte le stesse persone.
"""

import io
import os
import zipfile

import numpy as np
import pandas as pd
import yaml

from gsp import fonti as F

FONTE_DATI = "cens2011_titolo_studio"
FONTE_VOCAB = "claist_2026"
RACCORDO = os.path.join(F.DIR_FONTI, "istruzione_raccordo.yaml")

DENTRO_ZIP_DATI = ("CSV - DATI SOLO CODICI - DATA ONLY CODES/"
                   "DICA_TITSTUDIO-data.csv")
DENTRO_ZIP_CB = "METADATA/DimTITOLO_STUDIO_CENS-data.csv"

# Il file dati e' UTF-8 senza intestazione; i codebook sono UTF-16 CON
# BOM. Due processi di export diversi nello stesso zip: chi legge il primo
# con successo fallisce sul secondo.
ENC_DATI, ENC_CB = "utf-8", "utf-16"

# eta della popolazione (2024) -> classi del censimento 2011.
#
# DUE REGIMI, e la differenza e' sostanziale.
#
# Sopra i 35 anni oggi si usa la TRASLAZIONE PER COORTE: chi ha 35-49
# anni nel 2024 ne aveva 22-36 nel 2011, quindi si legge la tavola
# spostata di tredici anni e si ottiene la stessa generazione. Funziona
# perche' quelle persone avevano gia' finito di studiare nel 2011.
#
# Sotto i 35 la traslazione NON funziona: leggerebbe bambini. Verificato
# il 4/8/2026 — con la traslazione il bin 15-24 usciva con 53,2% di
# «nessun titolo» e 34,5% di «licenza elementare», perche' si stavano
# leggendo i sei-dieci anni del 2011. Per questi bin si usa la classe
# CORRISPONDENTE, non traslata: riflette la scolarizzazione del 2011
# invece di quella della coorte, il che e' un'approssimazione — ma
# molto migliore che leggere dei bambini.
#
# La conferma che le due letture siano compatibili: 25-34 non traslato
# da' 46,2% diploma e 17,6% magistrale, 35-49 traslato da' 52,0% e
# 13,3%. Due letture diverse della stessa tavola che convergono.
BIN_CENS2011 = {
    "9-14":  None,                              # regola diretta, vedi sotto
    "15-24": ["Y15-19", "Y20-24"],              # NON traslato
    "25-34": ["Y25-29", "Y30-34"],              # NON traslato
    "35-49": ["Y20-24", "Y25-29", "Y30-34"],    # traslato di 13 anni
    "50-64": ["Y35-39", "Y40-44", "Y45-49"],
    "65-74": ["Y50-54", "Y55-59"],
    "75+":   ["Y60-64", "Y65-69", "Y70-74", "Y_GE75"],
}

# I 9-14enni di oggi sono nati DOPO il censimento 2011: non esistono in
# quella tavola. Ma non serve: il MaxEnt garantisce gia' che abbiano solo
# nessun_titolo, elementare o media (esclusioni alpha=0 in cs_build), e in
# ciascuna di quelle categorie il censimento ha UNA SOLA foglia. Il titolo
# e' quindi determinato dalla categoria, senza bisogno di pesi.
BIN_SENZA_CENSIMENTO = {"9-14"}

SESSO_CENS = {"M": "1", "F": "2", None: "9"}

# codici che sono aggregati, non titoli
TOTALI = {"99", "000", "0"}

_cache = {}


# ------------------------------------------------------------- lettura

def _dentro_zip(path, nome, enc):
    with zipfile.ZipFile(path) as z:
        return z.read(nome).decode(enc)


def albero():
    """Il codebook con la gerarchia dichiarata: codice, etichetta, padre,
    e se il nodo sia una foglia."""
    if "albero" in _cache:
        return _cache["albero"]
    p = F.path_grezzo(FONTE_DATI)
    t = _dentro_zip(p, DENTRO_ZIP_CB, ENC_CB)
    d = pd.read_csv(io.StringIO(t), sep="|", header=None, dtype=str,
                    names=["cod", "en", "it", "padre", "ord"])
    d["cod"] = d.cod.str.strip()
    d["padre"] = d.padre.str.strip()
    # `99` e `000` sono il TOTALE generale, non titoli: non hanno
    # categoria e non devono mai essere estratti. Toglierli qui invece
    # che nel raccordo evita di dover trattare una categoria nulla.
    d = d[~d.cod.isin(TOTALI)].reset_index(drop=True)
    # radice: punta a se stessa
    d["radice"] = d.cod == d.padre
    # PADRE solo di qualcun ALTRO: le radici puntano a se stesse, e una
    # radice senza figli — «licenza di scuola elementare» — e' una foglia
    # a tutti gli effetti. Contarla fra i padri la escluderebbe dal
    # repertorio, lasciando la categoria vuota.
    padri = set(d.loc[d.cod != d.padre, "padre"].dropna())
    d["foglia"] = ~d.cod.isin(padri)

    # La RADICE di ogni nodo si trova risalendo la catena dei padri, non
    # guardando il prefisso del codice: la gerarchia ATTRAVERSA i gruppi.
    # `002999` (alfabeta privo di titolo) ha primo gruppo 002 ma e' figlio
    # di `001999` (nessun titolo), che ha 001. Dedurre il ramo dal codice
    # spezzerebbe quell'albero in due.
    su = dict(zip(d.cod, d.padre))
    def _radice_di(c, limite=12):
        visti = set()
        while c in su and su[c] != c and c not in visti and limite:
            visti.add(c)
            c = su[c]
            limite -= 1
        return c
    d["albero"] = d.cod.map(_radice_di)
    _cache["albero"] = d
    return d


def dati(regione="ITD5"):
    """I conteggi del censimento per la regione data."""
    if ("dati", regione) in _cache:
        return _cache[("dati", regione)]
    p = F.path_grezzo(FONTE_DATI)
    t = _dentro_zip(p, DENTRO_ZIP_DATI, ENC_DATI)
    d = pd.read_csv(io.StringIO(t), sep="|", header=None, low_memory=False,
                    names=["terr", "tipo", "sesso", "eta", "cod", "anno",
                           "val", "_x"],
                    dtype={"cod": str, "terr": str, "sesso": str})
    d = d.drop(columns=["_x"])
    d["cod"] = d.cod.str.strip()
    d = d[d.terr == regione]
    if d.empty:
        raise LookupError(
            f"regione '{regione}' assente. Presenti: "
            f"{', '.join(sorted(set(pd.read_csv(io.StringIO(t), sep='|', header=None, usecols=[0], dtype=str)[0])))}")
    _cache[("dati", regione)] = d
    return d


# ------------------------------------------------------------- raccordo

def _raccordo():
    if "rac" not in _cache:
        with open(RACCORDO, encoding="utf-8") as f:
            _cache["rac"] = yaml.safe_load(f) or {}
    return _cache["rac"]


def _gruppi(cod):
    """I gruppi di tre cifre. Il codice ha gli zeri iniziali soppressi:
    sei cifre per la secondaria, nove per il terziario."""
    c = cod.zfill(6) if len(cod) <= 6 else cod.zfill(9)
    return [c[i:i + 3] for i in range(0, len(c), 3)]


def categoria(cod):
    """La categoria di `istruzione` per un codice censuario, secondo il
    raccordo dichiarato. Prima regola che combacia."""
    g = _gruppi(cod)
    g1, g2 = g[0], (g[1] if len(g) > 1 else "")
    for r in _raccordo().get("regole", []):
        se = r.get("se") or {}
        if "g1" in se and g1 not in se["g1"]:
            continue
        if "g2" in se and g2 not in se["g2"]:
            continue
        if "g2_inizia" in se and not any(g2.startswith(x)
                                         for x in se["g2_inizia"]):
            continue
        return r["usa"]
    return None


# ------------------------------------------------------------ verifica

def verifica(regione="ITD5", stampa=True):
    """La partizione regge? Tre controlli, e il terzo e' quello vero.

    1. copertura: ogni codice ha una categoria
    2. foglie: ogni categoria ne ha almeno una
    3. COERENZA: la somma delle foglie di una categoria non deve superare
       il totale del ramo. E' il controllo che scopre se si sta contando
       due volte, ed e' l'unico che guarda i DATI invece del codebook.
    """
    a = albero()
    a = a.assign(cat=a.cod.map(categoria))
    fuori = a[a.cat.isna()]

    d = dati(regione)
    tot = d[(d.sesso == "9") & (d.eta == "Y_GE6")].set_index("cod").val
    foglie = set(a[a.foglia].cod)

    righe = []
    for cat, g in a.groupby("cat"):
        f = [c for c in g.cod if c in foglie and c in tot.index]
        righe.append({"categoria": cat, "codici": len(g), "foglie": len(f),
                      "somma_foglie": int(tot[f].sum()) if f else 0})
    r = pd.DataFrame(righe)

    # Coerenza PER RAMO, non per categoria: una categoria puo' raccogliere
    # foglie da rami diversi — `post_laurea` prende sia la laurea
    # magistrale (072) sia l'AFAM (050) — e sommarle contro il totale di
    # UN solo ramo produce un falso allarme. E' l'errore che questa
    # verifica ha commesso al primo giro sui dati veri.
    rami = []
    for radice, sotto in a.groupby("albero"):
        f = [c for c in sotto.cod if c in foglie and c in tot.index]
        if radice not in tot.index or not f:
            continue
        rami.append({"radice": radice,
                     "titolo": str(a.loc[a.cod == radice, "it"].iloc[0])[:38],
                     "totale": int(tot[radice]),
                     "somma_foglie": int(tot[f].sum()),
                     "foglie": len(f),
                     "categorie": ", ".join(sorted(set(sotto.cat.dropna())))})
    rr = pd.DataFrame(rami)
    if len(rr):
        rr["scarto"] = rr.somma_foglie - rr.totale
        rr["scarto_%"] = (rr.scarto / rr.totale * 100).round(2)

    if stampa:
        print(f"regione {regione} · {len(a)} codici · "
              f"{len(foglie)} foglie · {a.radice.sum()} radici\n")
        print(r.to_string(index=False))
        if len(fuori):
            print(f"\n!! {len(fuori)} codici SENZA categoria:")
            print(fuori[["cod", "it"]].head(10).to_string(index=False))
        else:
            print("\nogni codice ha una categoria: la partizione copre tutto")
        vuote = r[r.foglie == 0]
        if len(vuote):
            print("\n!! categorie SENZA foglie: il repertorio non potrebbe "
                  "estrarre nulla")
            print(vuote[["categoria", "codici"]].to_string(index=False))
        if len(rr):
            print("\ncoerenza per ramo: la somma delle foglie ricostruisce "
                  "il totale?")
            print(rr[["radice", "titolo", "totale", "somma_foglie",
                      "scarto_%", "foglie", "categorie"]].to_string(index=False))
            male = rr[rr["scarto_%"].abs() > 0.5]
            if len(male):
                print("\n!! rami con scarto oltre lo 0,5%: o mancano "
                      "foglie, o se ne contano di troppo")
                print(male[["radice", "titolo", "totale", "somma_foglie",
                            "scarto_%"]].to_string(index=False))
            else:
                print("  ogni ramo torna entro lo 0,5%: nessun doppio "
                      "conteggio, nessuna foglia persa")
    return r, fuori, (rr if len(rr) else None)


# ----------------------------------------------------------- repertorio

def repertorio(cat, sesso=None, eta=None, regione="ITD5", solo_foglie=True):
    """(codice, etichetta, peso) per una categoria, condizionato.

    I pesi sono conteggi censuari sulle FOGLIE: sommare anche i nodi padre
    conterebbe due volte le stesse persone.
    """
    a = albero()
    a = a.assign(cat=a.cod.map(categoria))
    voci = a[a.cat == cat]
    if solo_foglie:
        voci = voci[voci.foglia]
    if voci.empty:
        raise LookupError(f"nessuna foglia per la categoria '{cat}'")

    d = dati(regione)
    d = d[d.sesso == SESSO_CENS.get(sesso, "9")]
    if eta in BIN_SENZA_CENSIMENTO:
        # nessun condizionamento: si usa il totale, e nelle categorie
        # possibili a quell'eta' la foglia e' comunque una sola
        d = d[d.eta == "Y_GE6"]
    elif eta:
        if eta not in BIN_CENS2011:
            raise KeyError(f"bin '{eta}' non mappato; noti: "
                           f"{', '.join(BIN_CENS2011)}")
        classi = BIN_CENS2011[eta]
        d = d[d.eta.isin(classi)]
    else:
        d = d[d.eta == "Y_GE6"]

    peso = d.groupby("cod").val.sum()
    out = voci[["cod", "it"]].copy()
    out["peso"] = out.cod.map(peso).fillna(0.0)
    out = out[out.peso > 0]
    if out.empty:
        raise LookupError(
            f"categoria '{cat}', sesso {sesso}, eta {eta}: nessuna foglia "
            f"con peso positivo nella regione {regione}")
    return (out.rename(columns={"cod": "chiave", "it": "titolo"})
            .sort_values("peso", ascending=False).reset_index(drop=True))


# --------------------------------------------------------------- resa

# Prefissi che segnalano una foglia RESIDUALE: il censimento dettaglia i
# corsi piu' diffusi e raccoglie il resto per gruppo. Non sono una coda:
# nel ramo della laurea triennale valgono il 39% della massa (33 foglie
# su 290, verificato 4/8/2026), quindi in una demo quattro schede su
# dieci direbbero «altre lauree del gruppo...». Si risale al padre, che
# e' il gruppo disciplinare e si puo' dire.
RESIDUALI = ("altre ", "altri ", "altro ")


def _leggibile(t):
    """«gruppo economico-statistico» -> «discipline economico-statistiche».

    I nomi dei gruppi del censimento sono etichette di classificazione,
    non modi di dire un titolo. La sostituzione e' meccanica e imperfetta
    — resta qualche accordo sbagliato — ma e' molto meglio di «gruppo».
    """
    t = t.strip()
    if t.lower().startswith("gruppo "):
        t = "discipline " + t[7:]
    return t


# Il RAMO dice il livello, che l'etichetta della foglia non porta:
# nessuna delle 346 foglie terziarie lo contiene nel nome — sono solo
# discipline, «informatica», «fisica», «matematica» (verificato
# 4/8/2026). Senza il prefisso una magistrale in fisica e una triennale
# in fisica sono indistinguibili.
LIVELLO = {
    "60000000":  "diploma universitario in",
    "71000000":  "laurea triennale in",
    "072000000": "laurea magistrale in",
}


def titolo_leggibile(cod, etichetta=None):
    """L'etichetta da mostrare per un codice.

    Due aggiustamenti, entrambi di sola presentazione — il repertorio e i
    pesi non cambiano:
      1. se la foglia e' RESIDUALE si risale al padre, che e' il gruppo
         disciplinare e si puo' dire;
      2. per il terziario si antepone il LIVELLO, che il nome della
         disciplina non porta.
    """
    a = albero()
    et = dict(zip(a.cod, a.it))
    su = dict(zip(a.cod, a.padre))
    rad = dict(zip(a.cod, a.albero))

    t = etichetta if etichetta is not None else et.get(cod, "")
    if t.lower().startswith(RESIDUALI):
        p = su.get(cod)
        if p and p != cod and p in et:
            t = et[p]
    t = _leggibile(t)

    pref = LIVELLO.get(rad.get(cod))
    if pref and not t.lower().startswith(("laurea", "diploma", "corso")):
        t = f"{pref} {t}"
    return t


# ------------------------------------------------------------ estrazione

def titolo_agente(uid, istruzione, sesso=None, eta=None, regione="ITD5",
                  spiega=False):
    """Il titolo dettagliato di un individuo, deterministico dall'uid.

    Come il nome: si calcola quando serve e non finisce in nessun file.
    Usa `gsp.nomi._rng` con un CANALE separato, cosi' correggendo il
    raccordo dei titoli i nomi non si rimescolano e il diff fra due
    campagne resta leggibile.

    La coerenza con la categoria e' garantita per costruzione: si pesca
    dentro il repertorio di `istruzione`, quindi da `media` esce sempre un
    titolo di livello media.
    """
    from gsp import nomi as N

    if istruzione in (None, "", "non_applicabile"):
        return None
    d = repertorio(istruzione, sesso=sesso, eta=eta, regione=regione)
    rng = N._rng(uid, "titolo")
    p = d.peso.to_numpy(dtype="float64")
    i = int(rng.choice(len(d), p=p / p.sum()))
    grezzo = str(d.titolo.iloc[i])
    reso = titolo_leggibile(str(d.chiave.iloc[i]), grezzo)
    if spiega:
        return reso, {"categoria": istruzione,
                      "codice": str(d.chiave.iloc[i]),
                      "grezzo": grezzo,
                      "foglie": len(d),
                      "quota": round(float(p[i] / p.sum()), 4)}
    return reso


def titoli_popolazione(pop, colonna_id="uid", regione="ITD5"):
    """Titoli per un DataFrame. NON aggiunge colonne: torna una Series che
    il chiamante usa e butta, come i nomi."""
    fuori = []
    for _, r in pop.iterrows():
        try:
            fuori.append(titolo_agente(str(r[colonna_id]), r.get("istruzione"),
                                       sesso=r.get("sesso"), eta=r.get("eta"),
                                       regione=regione))
        except LookupError:
            fuori.append(None)
    return pd.Series(fuori, index=pop.index)
