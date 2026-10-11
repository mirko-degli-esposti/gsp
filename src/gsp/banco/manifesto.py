"""Il manifesto di una corsa: schema, lettura, scrittura atomica, validazione.

Le manopole sono le DIFFERENZE dalla produzione. Cio' che non e' scritto
vale quanto in rigenera.sh (fit) o nei default degli script (anelli 2-4).
`PRODUZIONE` e' la copia dichiarata di quei valori: se cambia rigenera.sh
deve cambiare anche questa tabella, ed e' voluto che siano due posti --
il manifesto deve restare leggibile senza aprire lo script.
"""
from __future__ import annotations

import copy
import datetime as dt
import os
import tempfile

import yaml

import gsp.common as G
from gsp.banco import CORSE

VERSIONE = "0.1"
ANNO = 2024

# Valori di produzione (rigenera.sh e default degli script), per anello.
PRODUZIONE = {
    "vincoli": {"senza": [], "esclusioni": True, "min_age": None, "max_age": None},
    "fit": {"pool": None, "eps": 1e-8, "min_alpha": 2e-4, "outer": 500,
            "tol": 0, "sweeps": 40, "gibbs": False, "no_exact": False,
            "blocks": None, "warm_from": None, "anneal": None,
            "lr": None, "lr_tau": None},
    "avq": {"seed": 42, "targets": None, "targets_opt": None, "min_record": 20},
    "enrich": {"seed": 42, "no_tier": False},
    "nucleo": {"seme": 20260810, "repertorio": None},
}
ANELLO_DI = {"vincoli": 1, "fit": 1, "avq": 2, "enrich": 3, "nucleo": 4}
FASI = ["cs_build", "fit_cs", "assign_avq", "enrich", "assign_nucleo"]
ANELLO_FASE = {"cs_build": 1, "fit_cs": 1, "assign_avq": 2, "enrich": 3,
               "assign_nucleo": 4}


class _Dumper(yaml.SafeDumper):
    """Codici sempre quotati: YAML 1.1 legge 015146 come ottale."""


def _str(dumper, s):
    if "\n" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", s,
                                   style="'" if s.isdigit() else None)


_Dumper.add_representer(str, _str)


def livello_default(cod: str) -> str:
    v = G.info(cod)
    return v.get("fit") or ("K6C" if v.get("livello") is None else "K9C")


def livello_effettivo(m: dict) -> str:
    """Come cs_build: <LIV>_senza_<B1>_<B2> se ci sono blocchi tolti."""
    senza = (m.get("manopole", {}).get("vincoli", {}) or {}).get("senza") or []
    return m["livello"] + ("_senza_" + "_".join(senza) if senza else "")


def manopole_piene(m: dict) -> dict:
    """PRODUZIONE sovrascritta dalle manopole del manifesto; il pool, se
    assente, e' quello del registro."""
    piene = copy.deepcopy(PRODUZIONE)
    for gruppo, kv in (m.get("manopole") or {}).items():
        if gruppo not in piene:
            raise ValueError(f"gruppo di manopole sconosciuto: {gruppo}")
        for k, v in (kv or {}).items():
            if k not in piene[gruppo]:
                raise ValueError(f"manopola sconosciuta: {gruppo}.{k}")
            piene[gruppo][k] = v
    if piene["fit"]["pool"] is None:
        piene["fit"]["pool"] = G.COMUNI[m["comune"]].get("pool")
    return piene


def nuovo_id(cod: str, etichetta: str, oggi: dt.date | None = None) -> str:
    oggi = oggi or dt.date.today()
    base = f"{cod}_{etichetta}_{oggi:%Y%m%d}"
    for lettera in "abcdefghijklmnopqrstuvwxyz":
        if not os.path.exists(os.path.join(CORSE, base + lettera)):
            return base + lettera
    raise RuntimeError(f"piu' di 26 corse oggi per {base}")


def nuovo(cod: str, etichetta: str, anelli=(1, 2, 3, 4), manopole=None,
          base="produzione", note="", livello=None, anno=ANNO) -> dict:
    cod = str(cod)
    G.info(cod)                      # KeyError se non in registro
    m = {
        "versione": VERSIONE,
        "id": nuovo_id(cod, etichetta),
        "tipo": "corsa",
        "comune": cod,
        "anno": int(anno),
        "livello": livello or livello_default(cod),
        "base": base,
        "anelli": sorted(int(a) for a in anelli),
        "manopole": manopole or {},
        "note": note,
        "esito": {"stato": "nuova"},
    }
    valida(m)
    return m


def valida(m: dict) -> None:
    """Solleva ValueError con il motivo. Regole:
    - anelli contigui e terminanti dove si vuole (es. [1,2] o [2,3,4]);
    - se cambia qualcosa dell'anello 1 (vincoli o fit), l'anello 1 e' nella
      lista: non esiste un fit di produzione per quelle manopole;
    - una manopola dell'anello k richiede che k sia rigenerato;
    - il pool c'e' (dal manifesto o dal registro);
    - Z1 e Z2 non si tolgono (Z2 poggia su Z1, Z5 su Z2: cs_build);
    - base = produzione o l'id di una corsa esistente."""
    if m.get("tipo") not in ("corsa", "gemello"):
        raise ValueError(f"tipo sconosciuto: {m.get('tipo')}")
    if m["tipo"] == "gemello":
        raise ValueError("tipo gemello: previsto, non ancora implementato")
    cod = m["comune"]
    if not isinstance(cod, str) or cod not in G.COMUNI:
        raise ValueError(f"comune non in registro o non quotato: {cod!r}")
    a = m["anelli"]
    if not a or a != list(range(a[0], a[-1] + 1)) or a[0] < 1 or a[-1] > 4:
        raise ValueError(f"anelli non contigui o fuori da 1-4: {a}")
    piene = manopole_piene(m)
    for gruppo, kv in (m.get("manopole") or {}).items():
        k = ANELLO_DI[gruppo]
        if kv and k not in a:
            raise ValueError(f"manopole {gruppo} (anello {k}) ma l'anello "
                             f"{k} non viene rigenerato: anelli={a}")
    if piene["fit"]["pool"] is None:
        raise ValueError("pool assente: ne' nel manifesto ne' nel registro")
    for b in piene["vincoli"]["senza"]:
        if b.startswith(("Z1", "Z2")):
            raise ValueError(f"{b} non si puo' togliere (cs_build: Z2 poggia "
                             "su Z1, Z5 su Z2)")
    if G.info(cod).get("livello") is None and piene["vincoli"]["senza"]:
        raise ValueError("comune non articolato: nessun blocco Z da togliere")
    b = m.get("base", "produzione")
    if b != "produzione" and not os.path.exists(percorso(b)):
        raise ValueError(f"base sconosciuta: {b}")


def percorso(id_corsa: str) -> str:
    return os.path.join(CORSE, id_corsa, "esperimento.yaml")


def carica(id_o_percorso: str) -> dict:
    p = id_o_percorso if id_o_percorso.endswith(".yaml") \
        else percorso(id_o_percorso)
    with open(p, encoding="utf-8") as f:
        m = yaml.safe_load(f)
    m["comune"] = str(m["comune"])
    return m


def salva(m: dict, p: str | None = None) -> str:
    """Scrittura atomica dell'intero file (tmp + os.replace)."""
    p = p or percorso(m["id"])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        yaml.dump(m, f, Dumper=_Dumper, allow_unicode=True, sort_keys=False,
                  width=200)
    os.replace(tmp, p)
    return p


def adesso() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()
