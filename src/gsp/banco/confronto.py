"""Confronto fra due corse dello stesso comune: TVD su ogni marginale e su
ogni incrocio a due delle variabili scelte, accanto al suo NULLO.

    python -m gsp.banco tvd A B                    # TVD(A, B)
    python -m gsp.banco tvd A B --nullo C D        # e TVD(C, D) come pavimento

Il nullo è la TVD fra due repliche della stessa corsa con seme diverso
(manopola fit.seed, o avq.seed, enrich.seed, nucleo.seme): è la parte di
differenza che il campionamento produce da solo. Un confronto senza nullo
non si legge (nota, §4: nessun numero senza il suo nullo).

Si legge il file più ricco disponibile in entrambe le corse, nell'ordine
_avq_full, _avq, popolazione: le variabili assenti da uno dei due file si
saltano e vengono elencate. Le TVD sono fra composizioni (quote), su
supporto = unione delle categorie viste nei due file.
"""
from __future__ import annotations

import itertools
import json
import os

import pandas as pd

import gsp.common as G
from gsp.banco import RADICE
from gsp.banco import corsa as C
from gsp.banco import manifesto as M

CONFRONTI = os.path.join(RADICE, "confronti")
# variabili di default: quelle dell'anello 1 (dal cs) + i target AVQ
VARS_ANELLO1 = ["zona", "sesso", "eta", "stato_civile", "cittadinanza",
                "istruzione", "condizione", "background", "origine_genitori"]


def _file(m: dict) -> str | None:
    cdir = os.path.join(C.dir_comuni(m["id"]), m["comune"],
                        f"constraints_{m['anno']}")
    liv = M.livello_effettivo(m)
    for suf in ("_avq_full", "_avq", ""):
        p = os.path.join(cdir, f"popolazione_{liv}{suf}.csv")
        if os.path.exists(p):
            return p
    return None


def _carica(m: dict, variabili: list[str]) -> tuple[pd.DataFrame, str]:
    p = _file(m)
    if p is None:
        raise RuntimeError(f"{m['id']}: nessuna popolazione")
    cols = set(pd.read_csv(p, nrows=0).columns)
    use = [v for v in variabili if v in cols]
    return pd.read_csv(p, usecols=use, dtype=str, low_memory=False), p


def _quote(d: pd.DataFrame, cols: list[str]) -> pd.Series:
    g = d.groupby(cols, dropna=False).size()
    return g / g.sum()


def tvd(a: pd.Series, b: pd.Series) -> float:
    idx = a.index.union(b.index)
    return float((a.reindex(idx).fillna(0.0) - b.reindex(idx).fillna(0.0)).abs().sum() / 2)


def confronta(id_a: str, id_b: str, variabili: list[str] | None = None,
              ordine: int = 2) -> dict:
    a, b = M.carica(id_a), M.carica(id_b)
    if a["comune"] != b["comune"]:
        raise RuntimeError(f"comuni diversi: {a['comune']} / {b['comune']}")
    variabili = variabili or VARS_ANELLO1 + list(G.AVQ_TARGETS)
    da, fa = _carica(a, variabili)
    db, fb = _carica(b, variabili)
    comuni_ = [v for v in variabili if v in da.columns and v in db.columns]
    saltate = [v for v in variabili if v not in comuni_]
    ris = {}
    for k in range(1, ordine + 1):
        for cols in itertools.combinations(comuni_, k):
            ris["×".join(cols)] = tvd(_quote(da, list(cols)), _quote(db, list(cols)))
    return {"a": id_a, "b": id_b, "comune": a["comune"],
            "file_a": fa, "file_b": fb, "n_a": int(len(da)), "n_b": int(len(db)),
            "variabili": comuni_, "saltate": saltate, "ordine": ordine,
            "tvd": ris}


def con_nullo(id_a, id_b, id_c=None, id_d=None, variabili=None, ordine=2) -> dict:
    r = confronta(id_a, id_b, variabili, ordine)
    if id_c and id_d:
        n = confronta(id_c, id_d, variabili, ordine)
        r["nullo"] = {"c": id_c, "d": id_d, "tvd": n["tvd"]}
        r["rapporto"] = {k: (r["tvd"][k] / n["tvd"][k] if n["tvd"].get(k) else None)
                         for k in r["tvd"]}
    return r


def salva(r: dict) -> str:
    os.makedirs(CONFRONTI, exist_ok=True)
    p = os.path.join(CONFRONTI, f"{r['a']}__{r['b']}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(r, f, indent=1, ensure_ascii=False)
    return p


def tabella(r: dict, top: int = 25) -> str:
    righe = sorted(r["tvd"].items(), key=lambda kv: -kv[1])
    nullo = (r.get("nullo") or {}).get("tvd", {})
    out = [f"TVD {r['a']} / {r['b']}  (n {r['n_a']:,} / {r['n_b']:,})"
           + (f"   nullo: {r['nullo']['c']} / {r['nullo']['d']}" if nullo else "")]
    out.append(f"{'variabili':42s} {'TVD':>8s}" + (f" {'nullo':>8s} {'x':>6s}" if nullo else ""))
    for k, v in righe[:top]:
        s = f"{k[:42]:42s} {v:8.4f}"
        if nullo:
            n = nullo.get(k)
            s += f" {n:8.4f} {(v / n if n else float('nan')):6.1f}"
        out.append(s)
    if len(righe) > top:
        out.append(f"... {len(righe) - top} altre (nel JSON)")
    if r["saltate"]:
        out.append(f"saltate (assenti in uno dei file): {r['saltate']}")
    return "\n".join(out)
