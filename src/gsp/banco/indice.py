"""indice.parquet: una riga per corsa, dai manifesti e dai riassunti delle
misure. E' il file che la dashboard legge (DuckDB-WASM, M3). Si ricostruisce
da zero a ogni chiamata: i manifesti sono la verita', l'indice una vista.
"""
from __future__ import annotations

import os

import pandas as pd

import gsp.common as G
from gsp.banco import CORSE, RADICE
from gsp.banco import corsa as C
from gsp.banco import manifesto as M
from gsp.banco import misure as MI

PERCORSO = os.path.join(RADICE, "indice.parquet")


def righe() -> list[dict]:
    out = []
    if not os.path.isdir(CORSE):
        return out
    for nome in sorted(os.listdir(CORSE)):
        p = M.percorso(nome)
        if not os.path.exists(p):
            continue
        m = M.carica(p)
        e = m.get("esito", {})
        piene = M.manopole_piene(m)
        r = {"id": m["id"], "tipo": m["tipo"], "comune": m["comune"],
             "nome": G.info(m["comune"])["nome"], "anno": m["anno"],
             "livello": m["livello"], "livello_eff": M.livello_effettivo(m),
             "anelli": "".join(str(k) for k in m["anelli"]),
             "base": m["base"], "senza": ",".join(piene["vincoli"]["senza"]),
             "pool": piene["fit"]["pool"],
             "manopole": ";".join(f"{g}.{k}={v}" for g, kv in (m.get("manopole") or {}).items()
                                  for k, v in (kv or {}).items()),
             "stato": e.get("stato"), "inizio": e.get("inizio"), "fine": e.get("fine"),
             "tempo_s": float(sum((e.get("tempi_s") or {}).values())),
             "commit": e.get("commit_gsp"), "git_pulito": e.get("git_pulito"),
             "misurato": e.get("misurato"), "note": m.get("note", "")}
        r.update(MI.riassunto(m))
        out.append(r)
    return out


def scrivi() -> str:
    df = pd.DataFrame(righe())
    os.makedirs(RADICE, exist_ok=True)
    df.to_parquet(PERCORSO, index=False)
    return PERCORSO
