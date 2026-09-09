#!/usr/bin/env python3
"""
holdout_z.py — quanto vale un blocco territoriale: hold-out e tre confronti.

    python scripts/esempio/holdout_z.py 037006 --blocco Z3 --anno 2024
    python scripts/esempio/holdout_z.py --tutti --blocco Z3

Il problema
-----------
Ogni misura del rilascio verifica che il modello riproduca cio' che gli e'
stato imposto. Nessuna dice se le relazioni che la massima entropia
riempie da se' --- quelle su cui nessun vincolo parla --- somiglino alla
popolazione vera. Ed e' su quelle che poggerebbero una simulazione o una
decisione.

L'esperimento
-------------
Si toglie un blocco territoriale dal constraint set, si rifitta, si estrae
una popolazione, e si chiede a quella popolazione di ricostruire il
blocco escluso. Il blocco vale come verita' perche' viene dal censimento
e non e' stato usato.

Il numero da solo non significa nulla, quindi si riporta fra due termini:

  pavimento     l'errore che resta anche VINCOLANDO il blocco: e' il
                rumore di campionamento, e nessun modello puo' fare meglio;
  indipendenza  l'errore assumendo che l'attributo sia indipendente dalla
                zona dato sesso: e' l'ignoranza completa, il limite
                superiore.

Dove cade l'hold-out fra i due dice quanta parte della geografia di
quell'attributo sopravvive attraverso GLI ALTRI blocchi --- Z2 vincola la
cittadinanza per zona, Z5 il background, ed entrambi sono correlati con
l'istruzione, quindi una parte passa per transitivita'. Vicino al
pavimento: il blocco era ridondante. Vicino all'indipendenza: porta
informazione che il modello non puo' inventare, e cio' che non e'
vincolato non e' ricostruito.

Prerequisiti (per comune):
    cs_build.py <c> --livello K9C --esclusioni                  (piena)
    cs_build.py <c> --livello K9C --esclusioni --senza Z3       (hold-out)
    fit_cs.py   <c> --livello K9C          --pool P --no-gibbs
    fit_cs.py   <c> --livello K9C_senza_Z3 --pool P --no-gibbs
Il pool DEVE essere lo stesso: fra le due corse deve cambiare una cosa sola.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("pip install pandas")

GSP = Path(os.environ.get("GSP_ROOT", Path.home() / "progetti" / "gsp"))

# blocco -> (nome nel targets, attributi, colonne del CSV di popolazione)
BLOCCHI = {
    "Z2": ("Z2_zona_sesso_eta_cittad", ["zona", "sesso", "eta", "cittadinanza"]),
    "Z3": ("Z3_zona_sesso_istruz",     ["zona", "sesso", "istruzione"]),
    "Z4": ("Z4_zona_sesso_eta_occ",    ["zona", "sesso", "eta", "condizione"]),
    "Z5": ("Z5_zona_sesso_background", ["zona", "sesso", "background"]),
}


def quote(df: pd.DataFrame, attrs: list[str]) -> pd.Series:
    """Distribuzione congiunta come quote sul totale, indicizzata 'a|b|c'."""
    g = df.groupby(attrs).size()
    g = g / g.sum()
    g.index = ["|".join(str(x) for x in (k if isinstance(k, tuple) else (k,)))
               for k in g.index]
    return g


def indipendenza(df: pd.DataFrame, attrs: list[str]) -> pd.Series:
    """Null: l'attributo di interesse indipendente dalla zona, dato il sesso.

    Si prende P(zona, sesso) dalla popolazione e P(attributo | sesso) dal
    totale comunale, e si moltiplica. E' la ricostruzione che si otterrebbe
    senza NESSUNA informazione territoriale su quell'attributo."""
    resto = [a for a in attrs if a not in ("zona",)]
    attr = [a for a in attrs if a not in ("zona", "sesso")]
    pz = df.groupby(["zona", "sesso"]).size() / len(df)
    pa = (df.groupby(["sesso"] + attr).size()
          / df.groupby("sesso").size().reindex(
              df.groupby(["sesso"] + attr).size().index.get_level_values(0)).values)
    righe = {}
    for (z, s), p1 in pz.items():
        for k, p2 in pa.items():
            k = k if isinstance(k, tuple) else (k,)
            if k[0] != s:
                continue
            chiave = "|".join(str(x) for x in ([z] + list(k)))
            righe[chiave] = p1 * p2
    return pd.Series(righe)


def confronta(vero: pd.Series, stima: pd.Series) -> dict:
    idx = vero.index.union(stima.index)
    v = vero.reindex(idx).fillna(0.0)
    s = stima.reindex(idx).fillna(0.0)
    tvd = float((v - s).abs().sum() / 2)
    mae = float((v - s).abs().mean())
    return {"tvd": round(tvd, 5), "mae_cella": round(mae, 7),
            "celle": int(len(idx))}


def analizza(comune: str, blocco: str, anno: int, livello: str) -> dict | None:
    nome, attrs = BLOCCHI[blocco]
    d = GSP / "data" / "comuni" / comune / f"constraints_{anno}"
    f_tar = d / f"targets_{livello}.json"
    f_pie = d / f"popolazione_{livello}.csv"
    f_out = d / f"popolazione_{livello}_senza_{blocco}.csv"
    for f in (f_tar, f_pie, f_out):
        if not f.exists():
            print(f"  [salto] {comune}: manca {f.name}")
            return None

    blk = json.load(open(f_tar))["blocks"][nome]["target"]
    tar = blk["values"] if "values" in blk else blk[[k for k in blk if k != "attrs"][0]]
    vero = pd.Series(tar, dtype=float)
    
    usecols = list(dict.fromkeys(attrs))
    piena = pd.read_csv(f_pie, usecols=usecols, dtype=str)
    holdo = pd.read_csv(f_out, usecols=usecols, dtype=str)

    q_pie = quote(piena, attrs)
    q_out = quote(holdo, attrs)
    q_ind = indipendenza(piena, attrs)

    pav = confronta(vero, q_pie)
    hol = confronta(vero, q_out)
    ind = confronta(vero, q_ind)

    # dove cade l'hold-out fra pavimento e indipendenza, in scala TVD
    span = ind["tvd"] - pav["tvd"]
    pos = (hol["tvd"] - pav["tvd"]) / span if span > 0 else None

    r = {"comune": comune, "blocco": blocco, "celle": pav["celle"],
         "tvd_pavimento": pav["tvd"], "tvd_holdout": hol["tvd"],
         "tvd_indipendenza": ind["tvd"],
         "posizione": round(pos, 3) if pos is not None else None}
    print(f"  {comune}  pavimento {pav['tvd']:.4f} · hold-out {hol['tvd']:.4f}"
          f" · indipendenza {ind['tvd']:.4f}"
          + (f"  →  {pos:.0%} del divario" if pos is not None else ""))
    return r


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comune", nargs="?")
    ap.add_argument("--tutti", action="store_true",
                    help="tutti i comuni con i file di hold-out presenti")
    ap.add_argument("--blocco", default="Z3", choices=sorted(BLOCCHI))
    ap.add_argument("--anno", type=int, default=2024)
    ap.add_argument("--livello", default="K9C")
    args = ap.parse_args()

    if args.tutti:
        base = GSP / "data" / "comuni"
        bersagli = sorted(
            p.name for p in base.iterdir()
            if (p / f"constraints_{args.anno}" /
                f"popolazione_{args.livello}_senza_{args.blocco}.csv").exists())
        if not bersagli:
            sys.exit("nessun comune con hold-out: eseguire prima cs_build/fit_cs")
    elif args.comune:
        bersagli = [args.comune]
    else:
        ap.error("indicare un comune, oppure --tutti")

    print(f"hold-out del blocco {args.blocco} ({BLOCCHI[args.blocco][0]})")
    print("  TVD contro il blocco escluso, che viene dal censimento\n")
    ris = [r for c in bersagli if (r := analizza(c, args.blocco, args.anno,
                                                 args.livello))]
    if not ris:
        return

    p = [r["posizione"] for r in ris if r["posizione"] is not None]
    if p:
        print(f"\n  l'hold-out copre in media il {sum(p)/len(p):.0%} del divario")
        print("  fra pavimento e indipendenza: e' la parte di geografia che")
        print("  NON sopravvive agli altri blocchi, e che il censimento deve dare.")

    out = GSP / "data" / "esempio" / f"holdout_{args.blocco}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"blocco": args.blocco, "anno": args.anno, "livello": args.livello,
               "nota": ("TVD fra la distribuzione del blocco nel censimento e "
                        "quella della popolazione sintetica. Pavimento: blocco "
                        "vincolato (rumore di campionamento). Hold-out: blocco "
                        "escluso dal fit. Indipendenza: attributo indipendente "
                        "dalla zona dato il sesso."),
               "comuni": ris}, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
