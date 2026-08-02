"""
zona_probe.py — caratterizza le zone sub-comunali dai civici ANNCSU, senza
scaricare nulla e senza scrivere nulla.

Formalizza il metodo collaudato su Modena il 29/07/2026, dove era stato
eseguito come heredoc. Due assi indipendenti:

  1. Baricentro e dispersione dei civici per zona. Il centro storico si
     riconosce dal raggio minimo; le zone periferiche dalle direzioni
     cardinali del baricentro. Su Modena: raggio 0,68 km contro 2,2-3,1,
     e le tre direzioni est/sud/ovest coerenti coi nomi ufficiali.
  2. Concentrazione dei toponimi. Un odonimo che contiene un toponimo deve
     cadere nella zona che lo nomina. Su Modena: 5 toponimi su 5 al 100%.

Rispetto alla versione heredoc, i toponimi non vanno piu' forniti a mano:
lo script li estrae dagli odonimi e riporta quelli che si concentrano in
una zona sola. Serve per i comuni di cui NON si conoscono le denominazioni
(il caso Modena era l'opposto: nomi noti, ipotesi da verificare).

Uso:
    python zona_probe.py 039014                  # Ravenna, COM_ASC1
    python zona_probe.py 037006 --level COM_ASC2 # Bologna, 18 zone
    python zona_probe.py 040012 --min-civici 50  # soglia toponimi piu' alta
    python zona_probe.py 039014 --file /percorso/civici.csv

Lettura dell'output:
    raggio_km piccolo + baricentro vicino al centro -> nucleo urbano storico
    raggio_km piccolo + baricentro lontano          -> frazione
    raggio_km grande                                -> settore urbano esteso
    Una partizione di frazioni si riconosce dal fatto che quasi tutte le
    zone sono compatte e lontane.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

import gsp.common as G

# Denominazioni urbanistiche generiche: si tolgono dall'odonimo per isolare
# il toponimo vero e proprio.
DUG = {
    "VIA", "VIALE", "VICOLO", "VICOLETTO", "PIAZZA", "PIAZZALE", "PIAZZETTA",
    "CORSO", "LARGO", "STRADA", "STRADELLO", "STRADELLA", "LUNGOMARE",
    "LUNGOFIUME", "BORGO", "SALITA", "DISCESA", "GALLERIA", "PONTE", "PARCO",
    "ROTONDA", "TRAVERSA", "CIRCONVALLAZIONE", "CAVALCAVIA", "SOTTOPASSO",
    "LOCALITA", "LOCALITA'", "FRAZIONE", "CONTRADA", "CASCINA", "PODERE",
    "DI", "DEL", "DELLA", "DELLE", "DEI", "DEGLI", "DA", "DALLA", "D",
    "SAN", "SANTA", "SANTO", "SANT", "SANT'", "S", "S.",
}

# Toponimi troppo generici per essere informativi sulla zona.
STOPWORDS = {"ROMA", "ITALIA", "GARIBALDI", "MAZZINI", "CAVOUR", "DANTE",
             "VERDI", "MARCONI", "VOLTA", "LEOPARDI", "MANZONI", "GRAMSCI",
             "MATTEOTTI", "KENNEDY", "EUROPA", "LIBERTA", "REPUBBLICA",
             "RESISTENZA", "PARTIGIANI", "MARTIRI", "CADUTI", "VITTORIA"}

# Nomi propri: una strada intitolata a una persona non dice nulla sulla zona.
# EMILIA e' deliberatamente esclusa (Via Emilia e' un toponimo, non un nome).
NOMI_PROPRI = {
    "ANTONIO", "GIOVANNI", "GIUSEPPE", "FRANCESCO", "LUIGI", "CARLO",
    "PIETRO", "PAOLO", "MARIO", "ALDO", "BRUNO", "ACHILLE", "UMBERTO",
    "GAETANO", "ALESSANDRO", "ANDREA", "DOMENICO", "ENRICO", "ERNESTO",
    "FEDERICO", "FILIPPO", "GABRIELE", "GIACOMO", "GIORGIO", "GUGLIELMO",
    "JACOPO", "LORENZO", "LUCIANO", "MARCO", "MATTEO", "MICHELE", "NICOLA",
    "ORESTE", "OTTAVIO", "RICCARDO", "ROBERTO", "SERGIO", "SILVIO",
    "STEFANO", "VINCENZO", "VITTORIO", "ANNA", "MARIA", "TERESA", "ELENA",
}


def path_civici(comune: str) -> str:
    """Percorso del file civici ANNCSU, che e' PROVINCIALE: il prefisso a tre
    cifre basta a identificarlo, quindi funziona anche per comuni non ancora
    registrati in G.COMUNI — che e' il caso d'uso tipico di questo script.
    Nota: lo slug nel nome file e' quello della provincia, non del comune
    (040_forli_cesena per Forli'), percio' non si passa dal registro."""
    if hasattr(G, "path_civici"):
        try:
            p = G.path_civici(comune)
            if os.path.exists(p):
                return p
        except Exception:
            pass
    cand = sorted(glob.glob(os.path.join(
        G.GEODATA, "*", "civici_sezioni_province",
        f"{comune[:3]}_*_civici_sezioni_asc.csv")))
    if not cand:
        sys.exit(f"Nessun file civici per la provincia {comune[:3]} sotto "
                 f"{G.GEODATA}: indicare --file.")
    if len(cand) > 1:
        print(f"[load] {len(cand)} file per la provincia {comune[:3]}, "
              f"uso il primo: {[os.path.basename(x) for x in cand]}")
    return cand[0]


def carica(comune: str, file_arg: str | None, level: str) -> pd.DataFrame:
    f = file_arg or path_civici(comune)
    if not os.path.exists(f):
        sys.exit(f"File civici assente: {f}")

    print(f"[load] {os.path.basename(f)}")
    c = pd.read_csv(f, dtype={"CODICE_ISTAT": str}, low_memory=False)
    c = c[c["CODICE_ISTAT"] == comune].copy()
    if c.empty:
        sys.exit(f"Nessun civico per CODICE_ISTAT == {comune}.")

    for col in (level, "COORD_X_COMUNE", "COORD_Y_COMUNE"):
        if col not in c.columns:
            sys.exit(f"Colonna {col} assente. Presenti: {sorted(c.columns)[:20]}")

    c["zona"] = pd.to_numeric(c[level], errors="coerce") \
                  .astype("Int64").astype("string")
    c["lon"] = pd.to_numeric(c["COORD_X_COMUNE"], errors="coerce")
    c["lat"] = pd.to_numeric(c["COORD_Y_COMUNE"], errors="coerce")

    n0 = len(c)
    c = c[c["zona"].notna() & (c["zona"] != "0")
          & c["lon"].notna() & c["lat"].notna()]
    print(f"[load] {len(c):,} civici usabili su {n0:,} "
          f"({n0 - len(c):,} senza zona o senza coordinate)")
    return c


def geometria(c: pd.DataFrame) -> pd.DataFrame:
    """Baricentro (km dal centro comunale) e raggio di dispersione per zona."""
    lat0, lon0 = c["lat"].mean(), c["lon"].mean()
    kx = 111.320 * np.cos(np.radians(lat0))          # km per grado di lon
    ky = 110.574                                     # km per grado di lat
    c = c.assign(x=(c["lon"] - lon0) * kx, y=(c["lat"] - lat0) * ky)

    out = []
    for z, s in c.groupby("zona", sort=True):
        xb, yb = s["x"].mean(), s["y"].mean()
        raggio = float(np.sqrt(((s["x"] - xb) ** 2 + (s["y"] - yb) ** 2).mean()))
        out.append({"zona": z, "civici": len(s),
                    "est_km": xb, "nord_km": yb,
                    "dist_km": float(np.hypot(xb, yb)),
                    "raggio_km": raggio})
    print(f"[geo]  centro dei civici: {lon0:.4f} E, {lat0:.4f} N")
    if not out:
        sys.exit("[geo] nessuna zona utilizzabile: tutti i civici hanno "
                 "COM_ASC a zero. Il comune non e' articolabile (K6C).")
    return pd.DataFrame(out).set_index("zona")


def nucleo(odonimo: str) -> str:
    """Toglie DUG e parole vuote, lascia il toponimo. '' se non ne resta."""
    parole = [p for p in re.split(r"[^A-Za-zÀ-ÿ']+", str(odonimo).upper()) if p]
    core = [p for p in parole if p not in DUG and len(p) > 2]
    return " ".join(core)


def toponimi(c: pd.DataFrame, min_civici: int, soglia: float) -> pd.DataFrame:
    """Odonimi il cui toponimo si concentra in una zona sola."""
    c = c.assign(core=c["ODONIMO"].map(nucleo))
    c = c[(c["core"] != "") & ~c["core"].isin(STOPWORDS)]
    santo = c["ODONIMO"].astype(str).str.upper().str.contains(
        r"\bSANT?[OA]?\b|\bSANT'", regex=True, na=False)
    primo = c["core"].str.split().str[0]
    n_tok = c["core"].str.split().str.len()
    c = c[~(primo.isin(NOMI_PROPRI) & (n_tok >= 2) & ~santo)]

    tab = c.groupby(["core", "zona"]).size().unstack(fill_value=0)
    tot = tab.sum(axis=1)
    tab = tab[tot >= min_civici]
    if tab.empty:
        return pd.DataFrame()
    tot = tot[tab.index]
    quota = tab.max(axis=1) / tot
    res = pd.DataFrame({"zona": tab.idxmax(axis=1), "civici": tot,
                        "concentr": quota})
    return res[res["concentr"] >= soglia].sort_values(
        ["zona", "civici"], ascending=[True, False])


def main(comune, file_arg, level, min_civici, soglia, top):
    c = carica(comune, file_arg, level)
    g = geometria(c)

    print(f"\n[geo] {len(g)} zone su {level} — baricentri e dispersione")
    print(g.assign(quota=(g["civici"] / g["civici"].sum()))
           .round({"est_km": 2, "nord_km": 2, "dist_km": 2,
                   "raggio_km": 2, "quota": 3})
           .to_string())

    compatte = g[(g["raggio_km"] < 1.0) & (g["dist_km"] > 2.0)]
    if len(compatte) >= max(2, len(g) // 3):
        print(f"\n[lettura] {len(compatte)} zone su {len(g)} sono compatte "
              f"(<1 km) e lontane dal centro (>2 km): la partizione sembra "
              f"per FRAZIONI piu' che per quartieri urbani.")
    elif g["raggio_km"].min() < 0.5 * g["raggio_km"].median():
        z = g["raggio_km"].idxmin()
        print(f"\n[lettura] zona {z} ha raggio {g.loc[z, 'raggio_km']:.2f} km "
              f"contro una mediana di {g['raggio_km'].median():.2f}: "
              f"candidato centro storico.")

    t = toponimi(c, min_civici, soglia)
    if t.empty:
        print(f"\n[topo] nessun toponimo con >= {min_civici} civici e "
              f"concentrazione >= {soglia:.0%}.")
        return
    print(f"\n[topo] toponimi concentrati (>= {min_civici} civici, "
          f">= {soglia:.0%} in una zona) — primi {top} per zona:")
    for z, s in t.groupby("zona"):
        voci = ", ".join(f"{i} ({r.civici}, {r.concentr:.0%})"
                         for i, r in s.head(top).iterrows())
        print(f"  {z}: {voci}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Baricentri e toponimi delle zone sub-comunali "
                    "dai civici ANNCSU. Non scrive nulla.")
    ap.add_argument("comune", help="codice ISTAT a sei cifre")
    ap.add_argument("--level", default="COM_ASC1",
                    help="colonna di zona [COM_ASC1]")
    ap.add_argument("--file", help="CSV civici (override del percorso)")
    ap.add_argument("--min-civici", type=int, default=20,
                    help="civici minimi perche' un toponimo conti [20]")
    ap.add_argument("--soglia", type=float, default=0.90,
                    help="concentrazione minima in una zona [0.90]")
    ap.add_argument("--top", type=int, default=6,
                    help="toponimi da mostrare per zona [6]")
    x = ap.parse_args()
    main(x.comune.zfill(6), x.file, x.level, x.min_civici, x.soglia, x.top)
