"""
confronta_prov.py — il canale provinciale dice il vero?

Confronta i decoded della SHADOW (fetch_prov) con quelli UFFICIALI
(data/comuni/, canale singolo collaudato) per gli stessi comuni/tavole.
Confronto SEMANTICO, mai cmp di byte: i due canali possono divergere
legittimamente in dtype, ordine righe, ordine colonne (lezione
REF_AREA int). Ciò che deve coincidere è il CONTENUTO:
  - stesse colonne (come insieme)
  - stesso numero di righe
  - stessi OBS_VALUE cella per cella, allineati sulle dimensioni

Uso:
  python scripts/acquisizione/confronta_prov.py --tavola cens_istruzione_eta \
      --comuni 040007 040012
"""
import argparse
import os
import sys

import pandas as pd

SHADOW = os.path.expanduser("~/progetti/gsp/data/prov_shadow")
UFFICIALE = os.path.expanduser("~/progetti/gsp/data/comuni")


def normalizza(df):
    """Porta un decoded in forma canonica per il confronto: colonne
    ordinate, tutto stringa (dtype fuori gioco), righe ordinate su
    tutte le dimensioni."""
    d = df.copy()
    d = d[sorted(d.columns)]
    for c in d.columns:
        # i numerici passano da float per uniformare 33021 vs 33021.0
        num = pd.to_numeric(d[c], errors="coerce")
        d[c] = num.astype("Float64").astype(str).where(num.notna(),
                                                       d[c].astype(str).str.strip())
    dims = [c for c in d.columns if c != "OBS_VALUE"]
    return d.sort_values(dims).reset_index(drop=True)


def confronta(cod, tavola):
    fs = os.path.join(SHADOW, cod, f"{tavola}_decoded.csv")
    fu = os.path.join(UFFICIALE, cod, f"{tavola}_decoded.csv")
    for f, tag in [(fs, "shadow"), (fu, "ufficiale")]:
        if not os.path.exists(f):
            return f"MANCA il file {tag}"

    s, u = normalizza(pd.read_csv(fs)), normalizza(pd.read_csv(fu))

    if set(s.columns) != set(u.columns):
        solo_s = set(s.columns) - set(u.columns)
        solo_u = set(u.columns) - set(s.columns)
        return f"COLONNE diverse: solo shadow {solo_s or '-'}, solo ufficiale {solo_u or '-'}"
    if len(s) != len(u):
        return f"RIGHE diverse: shadow {len(s)} vs ufficiale {len(u)}"
    if s.equals(u):
        return None
    diff = (s != u).any(axis=1)
    return f"CONTENUTO diverso su {int(diff.sum())} righe (prima: idx {diff.idxmax()})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tavola", required=True)
    ap.add_argument("--comuni", nargs="+", required=True)
    a = ap.parse_args()

    esito = 0
    for cod in a.comuni:
        m = confronta(cod, a.tavola)
        if m is None:
            print(f"  {cod}  {a.tavola}: IDENTICI (semanticamente)")
        else:
            print(f"  {cod}  {a.tavola}: {m}")
            esito = 1
    sys.exit(esito)


if __name__ == "__main__":
    main()