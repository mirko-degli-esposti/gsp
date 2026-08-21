#!/usr/bin/env python
"""Riepilogo delle diagnostiche per le tabelle III.3 del report.

Legge note/misure/diagnostica_report_v1.0/ e stampa due tabelle Markdown:
anello 1 (vincoli contro il pavimento) e anello 2 (donatori e n_eff).

    python scripts/diagnostica/riepilogo_diagnostica.py
    python scripts/diagnostica/riepilogo_diagnostica.py --dir altra/cartella
"""
import argparse, csv, glob, os, re, sys

NOMI = {"037006": "Bologna", "017029": "Brescia", "034027": "Parma",
        "036023": "Modena", "035033": "Reggio nell'Emilia",
        "039014": "Ravenna", "099014": "Rimini", "038008": "Ferrara",
        "040012": "Forlì", "033032": "Piacenza", "037021": "Castenaso"}
ORD = list(NOMI)

def intero(s):          # migliaia col punto: 184.597 -> 184597
    return int(s.replace(".", ""))

def dec(s):             # decimale col punto: 7.05% -> 7.05, 1.391 -> 1.391
    return float(s.replace("%", ""))

def leggi_vincoli(d, c):
    t = open(os.path.join(d, f"vincoli_{c}.txt")).read()
    r = {}
    m = re.search(r"([\d.]+) individui · (\d+) attributi", t)
    r["attr"] = m.group(2) if m else "?"
    m = re.search(r"celle con target positivo\s+([\d.]+)", t)
    r["celle"] = intero(m.group(1)) if m else None
    for k, pat in [("mre_oss", r"MRE\s+([\d,.]+)%\s+[\d,.]+%"),
                   ("mre_att", r"MRE\s+[\d,.]+%\s+([\d,.]+)%"),
                   ("zmed", r"\|z\| medio\s+([\d,.]+)"),
                   ("sdz", r"sd\(z\)\s+([\d,.]+)\s+[\d,.]+"),
                   ("z3", r"\|z\| > 3\s+([\d,.]+)%\s+[\d,.]+%")]:
        m = re.search(pat, t)
        r[k] = dec(m.group(1)) if m else None
    r["zeri_ok"] = "nessuno: ogni cella dichiarata impossibile" in t
    # |z| max con atteso, dal CSV
    zmax, att = 0.0, None
    with open(os.path.join(d, f"celle_{c}.csv")) as fh:
        for riga in csv.DictReader(fh):
            if not riga.get("z"): continue
            z = abs(float(riga["z"]))
            if z > zmax:
                zmax, att = z, float(riga["atteso"])
    r["zmax"], r["zmax_atteso"] = zmax, att
    return r

def leggi_donor(d, c):
    t = open(os.path.join(d, f"donor_{c}.txt")).read()
    r = {}
    m = re.search(r"firme distinte\s+([\d.]+)", t); r["firme"] = intero(m.group(1)) if m else None
    m = re.search(r"donatori dichiarati usati\s+([\d.]+)\s+\(pool ([\d.]+), ([^)]+)\)", t)
    if m: r["donatori"], r["pool"], r["regione"] = intero(m.group(1)), intero(m.group(2)), m.group(3)
    # righe della tabella per variabile: variabile copertura n distinti n_eff banda
    for var in ("SALUTE", "PUNTIFI10"):
        m = re.search(rf"^{var}\s+([\d,.]+)%\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d,.]+)\s*$",
                      t, re.M)
        if m:
            r[var] = dict(cop=dec(m.group(1)), n=intero(m.group(2)),
                          dist=intero(m.group(3)), neff=intero(m.group(4)),
                          banda=dec(m.group(5)))
    return r

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="note/misure/diagnostica_report_v1.0")
    a = ap.parse_args()
    d = a.dir

    print("### Tabella III.3a — anello 1, vincoli contro il pavimento\n")
    print("| municipality | cells (α>0) | MRE obs. | MRE exp. | mean·z | sd(z) | %·z·>3 | ·z·max (exp. cell) | hard zeros |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in ORD:
        try: v = leggi_vincoli(d, c)
        except FileNotFoundError: continue
        print(f"| {NOMI[c]} | {v['celle']:,} | {v['mre_oss']:.2f} % | {v['mre_att']:.2f} % "
              f"| {v['zmed']:.2f} | {v['sdz']:.3f} | {v['z3']:.2f} % "
              f"| {v['zmax']:.1f} ({v['zmax_atteso']:.1f}) | {'none violated' if v['zeri_ok'] else 'VIOLATED'} |")

    print("\n### Tabella III.3b — anello 2, firme e n_eff\n")
    print("| municipality | n | signatures | donors used (pool) | n_eff SALUTE | band × | n_eff PUNTIFI10 | band × |")
    print("|---|---|---|---|---|---|---|---|")
    for c in ORD:
        try: r = leggi_donor(d, c)
        except FileNotFoundError: continue
        sal, p10 = r.get("SALUTE", {}), r.get("PUNTIFI10", {})
        def f(x, dec=None):
            if x is None: return "n/d"
            return f"{x:,.1f}" if dec else f"{x:,}"
        print(f"| {NOMI[c]} | {f(sal.get('n'))} | {f(r.get('firme'))} | {f(r.get('donatori'))} ({f(r.get('pool'))}) "
              f"| {f(sal.get('neff'))} | {f(sal.get('banda'),1)} "
              f"| {f(p10.get('neff'))} | {f(p10.get('banda'),1)} |"
              .replace(",", "\u2009"))
if __name__ == "__main__":
    main()
