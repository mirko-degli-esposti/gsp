"""tabella_campione.py — la tabella dettagliata del campione giovani.

Legge i CSV per-giovane prodotti da campione_diplomati.py e stampa (in
markdown, pronto per una nota) quattro tavole:

  A  struttura del campione: ruoli, F con genitori, non collocati
  B  il campione F: sesso, background, istruzione dei genitori,
     tipo di diploma, condizione
  C  benchmark interno: quota studente per diploma3 e per gen3
  D  le celle del disegno (diploma3 x gen3 x sesso x background),
     pooled sui comuni, con il minimo per cella e la copertura

    python scripts/diagnostica/tabella_campione.py 034027 037006 017029
    python scripts/diagnostica/tabella_campione.py --tutti

Solo lettura; nessun file scritto (--md FILE per salvare il markdown).
"""

import argparse
import os
import sys

import pandas as pd

NOMI = {"034027": "Parma", "037006": "Bologna", "017029": "Brescia",
        "037006_": "Bologna"}

D3 = ["liceo", "tecnico", "professionale", "altro"]
G3 = ["bassa", "diploma", "laurea+", "assenti"]


def nome(c):
    return NOMI.get(c, c)


def carica(comuni, base):
    out = {}
    for c in comuni:
        p = os.path.join(base, f"campione_diplomati_{c}.csv")
        if not os.path.exists(p):
            print(f"[salto] {p} assente")
            continue
        g = pd.read_csv(p, dtype=str)
        g["comune"] = c
        out[c] = g
    if not out:
        sys.exit("nessun CSV trovato: girare prima campione_diplomati.py")
    return out


def col_background(g):
    for c in ("background", "cittadinanza", "background_migratorio"):
        if c in g.columns:
            return c
    return None


def bkg2(v):
    n = str(v).lower()
    return "ita" if ("ital" in n or n == "ita") else "straniero"


def pct(x, tot):
    return f"{100 * x / tot:.1f}%" if tot else "—"


def riga(cols):
    return "| " + " | ".join(str(c) for c in cols) + " |"


def sep(n):
    return "|" + "---|" * n


def tavola_A(dfs, out):
    out.append("### A — struttura del campione (diplomati, finestra d'età della corsa)\n")
    cols = ["comune", "giovani", "F", "R", "P", "A", "N", "non coll.",
            "F con ≥1 genitore"]
    out += [riga(cols), sep(len(cols))]
    for c, g in dfs.items():
        n = len(g)
        r = g["ruolo"].value_counts()
        nc = int(r.get("?", 0))
        f = g[g["ruolo"] == "F"]
        fg = (pd.to_numeric(f["n_genitori"], errors="coerce") > 0).sum()
        out.append(riga([
            nome(c), n,
            f"{int(r.get('F', 0))} ({pct(r.get('F', 0), n)})",
            f"{int(r.get('R', 0))} ({pct(r.get('R', 0), n)})",
            f"{int(r.get('P', 0))} ({pct(r.get('P', 0), n)})",
            int(r.get("A", 0)), int(r.get("N", 0)), nc,
            f"{fg} ({pct(fg, len(f))} degli F)"]))
    out.append("")


def tavola_B(dfs, out):
    out.append("### B — il campione F (i candidati dell'esperimento)\n")
    cols = ["comune", "n", "donne", "stranieri",
            "gen: bassa", "gen: diploma", "gen: laurea+",
            "liceo", "tecnico", "prof.", "altro*"]
    out += [riga(cols), sep(len(cols))]
    tot = []
    for c, g in dfs.items():
        f = g[g["ruolo"] == "F"].copy()
        cb = col_background(f)
        f["b2"] = f[cb].map(bkg2) if cb else "n/d"
        tot.append(f)
        n = len(f)
        gv = f["gen3"].value_counts()
        dv = f["diploma3"].value_counts()
        out.append(riga([
            nome(c), n,
            pct((f["sesso"] == "F").sum(), n),
            pct((f["b2"] == "straniero").sum(), n),
            pct(gv.get("bassa", 0), n), pct(gv.get("diploma", 0), n),
            pct(gv.get("laurea+", 0), n),
            pct(dv.get("liceo", 0), n), pct(dv.get("tecnico", 0), n),
            pct(dv.get("professionale", 0), n), pct(dv.get("altro", 0), n)]))
    f = pd.concat(tot)
    n = len(f)
    gv, dv = f["gen3"].value_counts(), f["diploma3"].value_counts()
    out.append(riga([
        "**pooled**", n, pct((f["sesso"] == "F").sum(), n),
        pct((f["b2"] == "straniero").sum(), n),
        pct(gv.get("bassa", 0), n), pct(gv.get("diploma", 0), n),
        pct(gv.get("laurea+", 0), n),
        pct(dv.get("liceo", 0), n), pct(dv.get("tecnico", 0), n),
        pct(dv.get("professionale", 0), n), pct(dv.get("altro", 0), n)]))
    out.append("\n\\* esclusa dal disegno (filiera artistica e residuali)\n")
    return f


def tavola_C(f, out):
    out.append("### C — benchmark interno: quota `studente` (pooled, solo F)\n")
    stud = f["condizione"].str.contains("stud", case=False, na=False)
    cols = ["strato", "n", "quota studente"]
    out += [riga(cols), sep(len(cols))]
    out.append(riga(["tutti", len(f), pct(stud.sum(), len(f))]))
    for var, livelli in (("diploma3", D3[:3]), ("gen3", G3[:3]),
                         ("comune", sorted(f["comune"].unique()))):
        for l in livelli:
            m = f[var] == l
            et = nome(l) if var == "comune" else l
            out.append(riga([f"{var} = {et}", int(m.sum()),
                             pct((stud & m).sum(), m.sum())]))
    out.append("\nNota: quantita' DI BIN alla risoluzione del dato — non "
               "confrontabile col tasso di passaggio immediato MUR senza "
               "la dichiarazione di finestra. `diploma3` e `gen3` sono "
               "piatte per costruzione: e' il certificato, non un "
               "risultato.\n")


def tavola_D(f, out):
    out.append("### D — le celle del disegno (diploma3 × gen3 × sesso × "
               "background, pooled)\n")
    f = f[(f["diploma3"] != "altro") & (f["gen3"] != "assenti")].copy()
    t = (f.groupby(["diploma3", "gen3", "sesso", "b2"])
         .agg(n=("uid", "size"),
              comuni=("comune", lambda s: "/".join(
                  str((s == c).sum()) for c in sorted(f["comune"].unique()))))
         .reset_index())
    cols = ["diploma3", "gen3", "sesso", "backgr.", "n",
            "per comune (" + "/".join(nome(c) for c in
                                      sorted(f["comune"].unique())) + ")"]
    out += [riga(cols), sep(len(cols))]
    for _, r in t.sort_values(["diploma3", "gen3", "sesso", "b2"]).iterrows():
        out.append(riga([r.diploma3, r.gen3, r.sesso, r.b2, r.n, r.comuni]))
    out.append("")
    for soglia in (10, 12, 20):
        ok = (t.n >= soglia).sum()
        out.append(f"- celle con n ≥ {soglia}: **{ok} / {len(t)}**"
                   f" (copertura {pct(t[t.n >= soglia].n.sum(), t.n.sum())}"
                   " dei candidati)")
    out.append(f"- cella minima: {int(t.n.min())} · mediana: "
               f"{int(t.n.median())} · massima: {int(t.n.max())}")
    out.append("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comuni", nargs="*",
                    default=["034027", "037006", "017029"])
    ap.add_argument("--dir", default="data/diagnostica")
    ap.add_argument("--md", help="scrive il markdown qui oltre a stamparlo")
    a = ap.parse_args()

    dfs = carica(a.comuni, a.dir)
    out = ["# Campione giovani diplomati — tabella dettagliata\n"]
    tavola_A(dfs, out)
    f = tavola_B(dfs, out)
    tavola_C(f, out)
    tavola_D(f, out)
    testo = "\n".join(out)
    print(testo)
    if a.md:
        with open(a.md, "w") as fh:
            fh.write(testo)
        print(f"\n[scritto {a.md}]")


if __name__ == "__main__":
    main()
