"""Attribuzione onomastica deterministica.

    import gsp.nomi as N

    N.nome_agente("036023-0000042", sesso="F", eta="35-49",
                  background="italiano_nativo", paese=None)
    # ('Giulia', 'Ferrari')

PRINCIPIO: il nome NON e' una colonna della popolazione. E' generato al
momento del bisogno da una funzione deterministica dell'`id`, e non
finisce mai in un file.

Serve a rendere naturali i persona-prompt degli agenti LLM in SimComm.
Per quell'uso la fedelta' della coda e' irrilevante: basta una
distribuzione plausibile per coorte e paese. Scriverlo nel Parquet
creerebbe invece un rischio diverso — nome + cognome + civico reale +
attributi sensibili produce individui sintetici che COLLIDONO con persone
reali, e su un dataset scaricabile la collisione non e' possibile ma
certa. Vedi il design di Animarium, §4.4 e §15.

ARCHITETTURA. Tre strati separati, cosi' cambiare sorgente non tocca il
codice:

  1. il REPERTORIO e' una fonte del registro piu' la dichiarazione di
     cosa condiziona (`fonti/repertori.yaml`). `condiziona: []` e' una
     lista unica; `condiziona: [sesso, coorte]` seleziona il
     sottoinsieme. Il generatore legge le colonne dichiarate e non sa da
     dove vengano;
  2. le REGOLE instradano ogni individuo al repertorio giusto — il
     cognome segue il padre, il nome dipende dai genitori;
  3. il GENERATORE pesca con `blake2b(SEME|canale|id)`.

Cambiare il repertorio dei cognomi italiani da Firenze a una fonte
emiliana significa cambiare una riga in `repertori.yaml`. Aggiungere il
condizionamento per coorte ai nomi significa cambiare `condiziona` e
registrare una fonte con quella colonna.
"""

import hashlib
import os

import numpy as np
import pandas as pd
import yaml

from gsp import fonti as F

# Cambiare il seme rigenera TUTTA l'onomastica. Non farlo a cuor leggero:
# le campagne SimComm gia' eseguite non sarebbero piu' riproducibili.
SEME = "gsp-nomi-2026"

CONFIG = os.path.join(F.DIR_FONTI, "repertori.yaml")

# eta (bin della popolazione) -> coorte di nascita, riferimento 2024.
# Serve solo se un repertorio dichiara `condiziona: [coorte]`.
BIN_COORTE = {
    "0-8": "2016-2024", "9-14": "2010-2015", "15-24": "2000-2009",
    "25-34": "1990-1999", "35-49": "1975-1989", "50-64": "1960-1974",
    "65-74": "1950-1959", "75+": "-1949",
}

_cache = {}


# ------------------------------------------------------------- configurazione

def _config():
    if "cfg" not in _cache:
        with open(CONFIG, encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
        rep = {r["id"]: r for r in doc.get("repertori", [])}
        _cache["cfg"] = (rep, doc.get("regole", {}))
    return _cache["cfg"]


def repertori(tipo=None):
    """Elenco dei repertori, con la fonte e cosa condizionano."""
    rep, _ = _config()
    righe = [{"id": r["id"], "tipo": r["tipo"], "fonte": r.get("fonte"),
              "condiziona": ",".join(r.get("condiziona") or []) or "-",
              "pesato": r.get("pesato", True),
              "pronto": r.get("fonte") not in (None, "DA_REGISTRARE")}
             for r in rep.values() if tipo is None or r["tipo"] == tipo]
    return pd.DataFrame(righe)


# ------------------------------------------------------------------- carica

def _carica(id_rep, attributi=None):
    """(DataFrame, repertorio). Il frame ha `chiave`, le colonne di
    `condiziona`, e `peso` se pesato.

    Se la fonte e' `multi_istanza` e la sua `chiave_istanza` compare fra
    le `condiziona`, si carica l'istanza corrispondente all'individuo:
    e' il caso dei nomi, dove il comune pubblica un file per sesso."""
    rep, _ = _config()
    if id_rep not in rep:
        raise KeyError(f"repertorio '{id_rep}' assente da {CONFIG}")
    r = rep[id_rep]
    fonte = r.get("fonte")
    if fonte in (None, "DA_REGISTRARE"):
        raise LookupError(
            f"repertorio '{id_rep}': fonte non ancora registrata. "
            f"Registrarla e mettere il suo id in `fonte` dentro {CONFIG}.")

    istanza = None
    if F.tipo(fonte) == "multi_istanza":
        chiave = F.info(fonte).get("chiave_istanza")
        if chiave not in (r.get("condiziona") or []):
            raise KeyError(
                f"repertorio '{id_rep}': la fonte '{fonte}' e' multi_istanza "
                f"su '{chiave}', che deve comparire fra le `condiziona`.")
        istanza = str((attributi or {}).get(chiave))
        r = dict(r, _istanza_su=chiave)

    memo = (id_rep, istanza)
    if memo in _cache:
        return _cache[memo]

    try:
        d = F.carica(fonte, istanza) if istanza else F.carica(fonte)
    except KeyError as e:
        raise LookupError(
            f"repertorio '{id_rep}': fonte '{fonte}'"
            + (f", istanza '{istanza}'" if istanza else "")
            + f" non caricabile ({e}). Correggere `fonte` in {CONFIG}."
        ) from None
    mancanti = [c for c in (r.get("condiziona") or [])
                if c not in d.columns and c != r.get("_istanza_su")]
    if mancanti:
        raise KeyError(
            f"repertorio '{id_rep}': la fonte '{fonte}' non ha le colonne "
            f"{mancanti} dichiarate in `condiziona`. O si cambia fonte, o "
            f"si riduce `condiziona`.")
    if r.get("pesato", True) and "peso" not in d.columns:
        raise KeyError(f"repertorio '{id_rep}' e' `pesato` ma la fonte "
                       f"'{fonte}' non ha la colonna `peso`")
    _cache[memo] = (d, r)
    return _cache[memo]


# ------------------------------------------------------------- instradamento

def _instrada(tipo, attributi):
    """Primo repertorio la cui regola combacia. Ritorna (id, motivo)."""
    _, regole = _config()
    for i, regola in enumerate(regole.get(tipo, [])):
        se = regola.get("se") or {}
        if all(attributi.get(k) in v for k, v in se.items()):
            motivo = ", ".join(f"{k}={attributi.get(k)}" for k in se) or "default"
            return regola["usa"], motivo
    raise LookupError(f"nessuna regola per tipo '{tipo}' con {attributi}")


# ---------------------------------------------------------------- estrazione

def _rng(id_individuo, canale):
    """Generatore riproducibile. blake2b e non hash(): l'hash di Python e'
    salato per processo, quindi due esecuzioni darebbero nomi diversi e la
    riproducibilita' salterebbe senza avvisare.

    Canali separati per nome e cognome: correggendo domani il repertorio
    dei nomi, i cognomi non si rimescolano e il diff fra due campagne
    resta leggibile."""
    h = hashlib.blake2b(f"{SEME}|{canale}|{id_individuo}".encode(),
                        digest_size=8).digest()
    return np.random.default_rng(int.from_bytes(h, "little"))


def _pesca(id_rep, id_individuo, attributi, canale):
    d, r = _carica(id_rep, attributi)
    cond = [c for c in (r.get("condiziona") or [])
            if c not in (r.get("_istanza_su") or "")]

    # `filtro` seleziona una porzione FISSA della fonte, uguale per tutti:
    # tipicamente l'annata, quando la fonte e' una serie storica.
    for c, v in (r.get("filtro") or {}).items():
        if c not in d.columns:
            raise KeyError(f"repertorio '{id_rep}': `filtro` su '{c}' ma la "
                           f"fonte non ha quella colonna")
        d = d[d[c].astype(str) == str(v)]
        if d.empty:
            raise LookupError(f"repertorio '{id_rep}': filtro {c}={v} "
                              f"non seleziona nulla")

    if cond:
        m = pd.Series(True, index=d.index)
        for c in cond:
            valore = attributi.get(c)
            if c == "coorte" and valore is None:
                valore = BIN_COORTE.get(attributi.get("eta"))
            m &= d[c].astype(str) == str(valore)
        sub = d[m]
        if sub.empty:
            raise LookupError(
                f"repertorio '{id_rep}': nessuna voce per "
                + ", ".join(f"{c}={attributi.get(c)}" for c in cond))
    else:
        sub = d

    rng = _rng(id_individuo, canale)
    if r.get("pesato", True):
        p = sub["peso"].to_numpy(dtype="float64")
        i = rng.choice(len(sub), p=p / p.sum())
    else:
        i = rng.integers(len(sub))
    return str(sub["chiave"].iloc[i])


# -------------------------------------------------------------------- API

def nome_agente(id_individuo, spiega=False, **attributi):
    """(nome, cognome) per un individuo. Deterministico dall'id.

    `attributi` sono le colonne della popolazione che servono
    all'instradamento e al condizionamento: sesso, eta, background,
    origine_genitori, paese. Quali servano davvero dipende da
    `repertori.yaml`, non da qui.

    Se un repertorio non ha ancora una fonte, si ripiega su `fallback` e
    la cosa e' DICHIARATA: con `spiega=True` si ottiene anche il percorso
    seguito, che e' l'unico modo di accorgersi che i nomi stranieri stanno
    uscendo dal repertorio italiano.
    """
    rep, _ = _config()
    fuori, tracce = {}, {}
    for tipo, canale in (("nome", "nome"), ("cognome", "cognome")):
        scelto, motivo = _instrada(tipo, attributi)
        catena = [scelto]
        while True:
            try:
                fuori[tipo] = _pesca(scelto, id_individuo, attributi, canale)
                break
            except (LookupError, KeyError) as e:
                ripiego = (rep.get(scelto) or {}).get("fallback")
                if not ripiego:
                    raise LookupError(
                        f"{tipo}: {e}  (nessun fallback per '{scelto}')") from None
                catena.append(ripiego)
                scelto = ripiego
        tracce[tipo] = {"regola": motivo, "catena": catena}
    if spiega:
        return fuori["nome"], fuori["cognome"], tracce
    return fuori["nome"], fuori["cognome"]


def nomi_popolazione(pop, colonna_id="id", spiega=False):
    """Nomi per un DataFrame di popolazione. NON aggiunge colonne: torna
    una Series di tuple, che il chiamante usa e butta."""
    servono = [c for c in ("sesso", "eta", "background", "origine_genitori",
                           "paese") if c in pop.columns]
    fuori = []
    for _, riga in pop.iterrows():
        attributi = {c: riga[c] for c in servono}
        fuori.append(nome_agente(str(riga[colonna_id]), **attributi))
    return pd.Series(fuori, index=pop.index)
