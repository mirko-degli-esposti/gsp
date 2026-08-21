"""tabella_campione.py — la tabella dettagliata del campione giovani. v2.

Legge i CSV per-giovane di campione_diplomati.py e produce quattro
tavole (A struttura, B candidati, C benchmark interno, D celle del
disegno con la colonna `preleva`). Scala a N comuni: in D la spaccatura
per comune usa le sigle, e i nomi vengono dal registro `gsp.common`
quando importabile (fallback: il codice ISTAT).

    python scripts/diagnostica/tabella_campione.py                 # i CSV presenti
    python scripts/diagnostica/tabella_campione.py 034027 017029   # selezione
    python scripts/diagnostica/tabella_campione.py --md t.md --txt t.txt

Formati: markdown (--md) e testo a colonne allineate (--txt), entrambi
stampabili; senza opzioni stampa il testo allineato a video.
Solo lettura.
"""

import argparse
import glob
import os
import re
import sys

import pandas as pd

N_PER_CELLA = 12          # il piano di campionamento: 12 dove disponibili

SIGLE = {"Piacenza": "PC", "Parma": "PR", "Reggio Emilia": "RE",
         "Reggio nell'Emilia": "RE", "Modena": "MO", "Bologna": "BO",
         "Ferrara": "FE", "Ravenna": "RA", "Forli'": "FC", "Forlì": "FC",
         "Rimini": "RN", "Brescia": "BS", "Castenaso": "CS"}

D3 = ["liceo", "tecnico", "professionale"]
G3 = ["bassa", "diploma", "laurea+"]


# ------------------------------------------------------------- registro

def nomi_comuni(codici):
    """codice -> nome, dal registro se importabile."""
    out = {}
    try:
        sys.path.insert(0, "src")
        from gsp import common as G
        for c in codici:
            try:
                out[c] = G.info(c).get("nome", c)
            except Exception:
                out[c] = c
    except Exception:
        out = {c: c for c in codici}
    return out


def sigla(nome):
    return SIGLE.get(nome, nome[:2].upper())


# --------------------------------------------------------------- carica

def carica(comuni, base):
    if not comuni:
        comuni = sorted(
            re.sub(r".*campione_diplomati_(\d+)\.csv", r"\1", p)
            for p in glob.glob(os.path.join(base, "campione_diplomati_*.csv"))
            if "_celle" not in p)
    out = {}
    for c in comuni:
        p = os.path.join(base, f"campione_diplomati_{c}.csv")
        if not os.path.exists(p):
            print(f"[salto] {p} assente — girare prima campione_diplomati.py")
            continue
        g = pd.read_csv(p, dtype=str)
        g["comune"] = c
        out[c] = g
    if not out:
        sys.exit("nessun CSV trovato in " + base)
    return out


def col_background(g):
    for c in ("background", "cittadinanza", "background_migratorio"):
        if c in g.columns:
            return c
    return None


def bkg2(v):
    n = str(v).lower()
    return "ita" if ("ital" in n or n == "ita") else "straniero"


def pi(x):                       # 12.345
    return f"{int(x):,}".replace(",", ".")


# ---------------------------------------------------------------- tavole
# Ogni tavola produce righe astratte; md() e txt() le impaginano.

def prepara(dfs, nomi):
    """Tutti i numeri, una volta sola."""
    A, B, C = [], [], []
    F_tot = []
    for c, g in dfs.items():
        n = len(g)
        r = g["ruolo"].value_counts()
        f = g[g["ruolo"] == "F"].copy()
        fg = (pd.to_numeric(f["n_genitori"], errors="coerce") > 0).mean()
        A.append(dict(comune=nomi[c], giovani=n,
                      F=int(r.get("F", 0)), R=int(r.get("R", 0)),
                      P=int(r.get("P", 0)), Aa=int(r.get("A", 0)),
                      Nn=int(r.get("N", 0)), nc=int(r.get("?", 0)),
                      f_gen=fg))
        cb = col_background(f)
        f["b2"] = f[cb].map(bkg2) if cb else "n/d"
        F_tot.append(f)
        gv, dv = f["gen3"].value_counts(), f["diploma3"].value_counts()
        nf = len(f)
        B.append(dict(comune=nomi[c], n=nf,
                      donne=(f["sesso"] == "F").mean(),
                      stran=(f["b2"] == "straniero").mean(),
                      gb=gv.get("bassa", 0) / nf, gd=gv.get("diploma", 0) / nf,
                      gl=gv.get("laurea+", 0) / nf,
                      li=dv.get("liceo", 0) / nf, te=dv.get("tecnico", 0) / nf,
                      pr=dv.get("professionale", 0) / nf,
                      al=dv.get("altro", 0) / nf))
    F = pd.concat(F_tot)
    nf = len(F)
    gv, dv = F["gen3"].value_counts(), F["diploma3"].value_counts()
    B.append(dict(comune="POOLED", n=nf,
                  donne=(F["sesso"] == "F").mean(),
                  stran=(F["b2"] == "straniero").mean(),
                  gb=gv.get("bassa", 0) / nf, gd=gv.get("diploma", 0) / nf,
                  gl=gv.get("laurea+", 0) / nf,
                  li=dv.get("liceo", 0) / nf, te=dv.get("tecnico", 0) / nf,
                  pr=dv.get("professionale", 0) / nf,
                  al=dv.get("altro", 0) / nf))

    stud = F["condizione"].str.contains("stud", case=False, na=False)
    C.append(("tutti", nf, stud.mean(), ""))
    for l in D3:
        m = F["diploma3"] == l
        C.append((f"diploma3 = {l}", int(m.sum()),
                  (stud & m).sum() / m.sum(), "costr"))
    for l in G3:
        m = F["gen3"] == l
        C.append((f"gen3 = {l}", int(m.sum()),
                  (stud & m).sum() / m.sum(), "costr"))
    for c in dfs:
        m = F["comune"] == c
        C.append((f"comune = {nomi[c]}", int(m.sum()),
                  (stud & m).sum() / m.sum(), "info"))

    Fd = F[(F["diploma3"].isin(D3)) & (F["gen3"].isin(G3))]
    ordine = list(dfs)
    D = (Fd.groupby(["diploma3", "gen3", "sesso", "b2"])
         .agg(n=("uid", "size"),
              **{f"c_{c}": ("comune", lambda s, c=c: int((s == c).sum()))
                 for c in ordine})
         .reset_index())
    D["cella"] = (D.diploma3 + "\u00b7" + D.gen3 + "\u00b7"
                  + D.sesso + "\u00b7" + D.b2)
    D["preleva"] = D.n.clip(upper=N_PER_CELLA)
    return A, B, C, D, ordine, F


# ------------------------------------------------------------------ txt

def formato_txt(A, B, C, D, ordine, nomi, finestra):
    L, p = [], None
    p = L.append
    W = max(74, 60 + 4 * len(ordine))
    sep = "=" * W
    p("CAMPIONE GIOVANI DIPLOMATI - TABELLA DETTAGLIATA"
      + (f" (finestra {finestra})" if finestra else ""))
    p(f"comuni: {len(ordine)} - mappa diploma3 v2 - "
      f"{pd.Timestamp.today():%d/%m/%Y}")
    p(sep)
    p("")
    p("A - STRUTTURA DEL CAMPIONE  (F = ruolo figlio, non sesso)")
    p("")
    p(f"  {'comune':<16}{'giovani':>8}   {'F (figli)':>15}{'R':>14}"
      f"{'P':>14}{'A':>5}{'N':>5}{'n.c.':>6}{'F+gen':>7}")
    p("  " + "-" * (W - 2))
    for r in A:
        p(f"  {r['comune']:<16}{pi(r['giovani']):>8}   "
          f"{pi(r['F']):>7} ({r['F']/r['giovani']:5.1%})"
          f"{pi(r['R']):>6} ({r['R']/r['giovani']:5.1%})"
          f"{pi(r['P']):>6} ({r['P']/r['giovani']:5.1%})"
          f"{r['Aa']:>5}{r['Nn']:>5}{r['nc']:>6}{r['f_gen']:>7.0%}")
    p("")
    p(sep)
    p("")
    p("B - I CANDIDATI (solo ruolo F)")
    p("")
    p(f"  {'comune':<16}{'n':>7}  {'donne':>6}{'stran.':>8} |"
      f"{'g:bassa':>8}{'g:dipl':>7}{'g:laur+':>8} |"
      f"{'liceo':>6}{'tecn':>6}{'prof':>6}{'altro':>6}")
    p("  " + "-" * (W - 2))
    for r in B:
        p(f"  {r['comune']:<16}{pi(r['n']):>7}  {r['donne']:>6.1%}"
          f"{r['stran']:>7.1%} |{r['gb']:>7.1%}{r['gd']:>6.1%}"
          f"{r['gl']:>7.1%} |{r['li']:>5.1%}{r['te']:>5.1%}"
          f"{r['pr']:>5.1%}{r['al']:>5.1%}")
    p("")
    p("  ATTENZIONE - marginali da non leggere come realta':")
    p("   . g:laur+  = artefatto dell'indipendenza fra genitori"
      " (reale ~25-30%)")
    p("   . liceo    = vintage censuario 2011 (reale ~57% degli iscritti)")
    p("")
    p(sep)
    p("")
    p("C - BENCHMARK INTERNO: quota `studente` (pooled, solo F)")
    p("")
    p(f"  {'strato':<30}{'n':>8}{'studente':>10}")
    p("  " + "-" * 50)
    for s, n, q, tipo in C:
        marca = {"costr": "   (piatta per costruzione)",
                 "info": "   <- asse informativo", "": ""}[tipo]
        p(f"  {s:<30}{pi(n):>8}{q:>9.1%}{marca}")
    p("")
    p(sep)
    p("")
    sig = [sigla(nomi[c]) for c in ordine]
    p("D - LE CELLE DEL DISEGNO  (pooled; per comune: " + "/".join(sig) + ")")
    p("")
    hdr = (f"  {'cella':<38}{'n':>5}  "
           + "".join(f"{s:>4}" for s in sig) + "   preleva")
    for d3 in D3:
        p(f"  --- {d3.upper()} " + "-" * max(4, W - 10 - len(d3)))
        p(hdr)
        blocco = D[D.diploma3 == d3].sort_values(["gen3", "sesso", "b2"])
        for _, r in blocco.iterrows():
            star = " *" if r.n < N_PER_CELLA else ""
            p(f"  {r.cella:<38}{r.n:>5}  "
              + "".join(f"{int(r[f'c_{c}']):>4}" for c in ordine)
              + f"{int(r.preleva):>7}{star}")
        p("")
    tot = int(D.preleva.sum())
    p(f"  * cella sotto i {N_PER_CELLA}: entra intera")
    for soglia in (10, N_PER_CELLA, 20):
        ok = int((D.n >= soglia).sum())
        cop = D[D.n >= soglia].n.sum() / D.n.sum()
        p(f"  celle con n>={soglia}: {ok}/{len(D)}  (copertura {cop:.1%})")
    p(f"  minima {int(D.n.min())} . mediana {int(D.n.median())} . "
      f"massima {int(D.n.max())}")
    p(f"  AGENTI DA CAMPIONARE: {tot}  ({N_PER_CELLA} per cella dove"
      " disponibili)")
    p("")
    p(sep)
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------- md

def formato_md(A, B, C, D, ordine, nomi, finestra):
    L, p = [], None
    p = L.append
    p("# Campione giovani diplomati — tabella dettagliata\n")
    p("### A — struttura (F = ruolo figlio, non sesso)\n")
    p("| comune | giovani | F | R | P | A | N | non coll. | F con gen. |")
    p("|---|---|---|---|---|---|---|---|---|")
    for r in A:
        p(f"| {r['comune']} | {r['giovani']} "
          f"| {r['F']} ({r['F']/r['giovani']:.1%}) "
          f"| {r['R']} ({r['R']/r['giovani']:.1%}) "
          f"| {r['P']} ({r['P']/r['giovani']:.1%}) "
          f"| {r['Aa']} | {r['Nn']} | {r['nc']} | {r['f_gen']:.0%} |")
    p("\n### B — i candidati (solo F)\n")
    p("| comune | n | donne | stranieri | g:bassa | g:diploma | g:laurea+ "
      "| liceo | tecnico | prof. | altro |")
    p("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in B:
        p(f"| {r['comune']} | {r['n']} | {r['donne']:.1%} | {r['stran']:.1%} "
          f"| {r['gb']:.1%} | {r['gd']:.1%} | {r['gl']:.1%} "
          f"| {r['li']:.1%} | {r['te']:.1%} | {r['pr']:.1%} "
          f"| {r['al']:.1%} |")
    p("\n### C — benchmark interno (quota studente, pooled F)\n")
    p("| strato | n | studente | lettura |")
    p("|---|---|---|---|")
    for s, n, q, tipo in C:
        m = {"costr": "piatta per costruzione", "info": "asse informativo",
             "": ""}[tipo]
        p(f"| {s} | {n} | {q:.1%} | {m} |")
    sig = [sigla(nomi[c]) for c in ordine]
    p("\n### D — le celle del disegno (per comune: " + "/".join(sig) + ")\n")
    p("| cella | n | " + " | ".join(sig) + " | preleva |")
    p("|---|---|" + "---|" * (len(sig) + 1))
    for _, r in D.sort_values(["diploma3", "gen3", "sesso", "b2"]).iterrows():
        star = " \\*" if r.n < N_PER_CELLA else ""
        p(f"| {r.cella} | {r.n} | "
          + " | ".join(str(int(r[f'c_{c}'])) for c in ordine)
          + f" | {int(r.preleva)}{star} |")
    p(f"\nAgenti da campionare: **{int(D.preleva.sum())}**")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comuni", nargs="*")
    ap.add_argument("--dir", default="data/diagnostica")
    ap.add_argument("--md", help="scrive il markdown qui")
    ap.add_argument("--txt", help="scrive il testo allineato qui")
    ap.add_argument("--finestra", default="19-22",
                    help="etichetta della finestra d'eta' nel titolo")
    a = ap.parse_args()

    dfs = carica(a.comuni, a.dir)
    nomi = nomi_comuni(list(dfs))
    tav = prepara(dfs, nomi)
    txt = formato_txt(*tav[:5], nomi, a.finestra)
    print(txt)
    if a.txt:
        open(a.txt, "w").write(txt)
        print(f"[scritto {a.txt}]")
    if a.md:
        open(a.md, "w").write(formato_md(*tav[:5], nomi, a.finestra))
        print(f"[scritto {a.md}]")


if __name__ == "__main__":
    main()
