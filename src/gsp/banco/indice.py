"""indice.parquet e indice.json: una riga per corsa, dai manifesti e dai
riassunti delle misure. Il JSON e' quello che legge banco.html (M3, con
fetch, senza DuckDB); il Parquet e' per chi interroga da Python o DuckDB.
Si ricostruiscono da zero a ogni chiamata: i manifesti sono la verita',
l'indice una vista.
"""
from __future__ import annotations

import json
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
             "misurato": e.get("misurato"), "note": m.get("note", ""),
             "misure": sorted((e.get("misure") or {}).keys()),
             "bundle": bool(e.get("bundle")),
             "ereditati": len(e.get("ereditati") or [])}
        r.update(MI.riassunto(m))
        out.append(r)
    return out


def scrivi() -> str:
    r = righe()
    df = pd.DataFrame(r)
    if "misure" in df.columns:
        df["misure"] = df["misure"].map(lambda x: ",".join(x) if isinstance(x, list) else x)
    os.makedirs(RADICE, exist_ok=True)
    df.to_parquet(PERCORSO, index=False)
    with open(PERCORSO.replace(".parquet", ".json"), "w", encoding="utf-8") as f:
        json.dump({"generato": M.adesso(), "corse": r}, f, ensure_ascii=False,
                  indent=1, default=lambda x: None if x != x else x)
    return PERCORSO
