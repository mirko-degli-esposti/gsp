#!/usr/bin/env python
"""
estrai_v1.py — tutte le cifre dei dodici comuni di riferimento, da file.

PERCHE'
La tabella di §6 e le macro di numbers.tex sono state composte a mano da
log letti a occhio. Questo script le ricostruisce dai file diagnostici,
cosi' che ogni numero del paper abbia una provenienza meccanica e una
verifica: se il testo dice 7.05 e il file dice altro, si vede qui.

FONTI (una per colonna, mai due per lo stesso numero)
  vincoli_<cod>.txt   celle a target positivo, MRE oss/att, |z| medio,
                      sd(z), quote |z|>2 e >3, media(z), zeri hard,
                      + la tabella per blocco
  celle_<cod>.csv     |z| massimo e l'attesa della cella che lo produce
  quinq_<cod>.txt     MAE del totale per sezione (alloc. MAE), |residuo|
                      medio per sezione (seam), n. sezioni
  istr_eta_<cod>.txt  quota di incoerenza eta x titolo
  donor_<cod>.txt     firme distinte, n_eff e banda per variabile
  <cod>.log           residuo di FIT, esclusioni, H, supporto, donatori
                      usati su pool, riuso, MAE popolazione/stranieri/UE

USO
  python estrai_v1.py /tmp/v1_paper --tabella   # la tabella LaTeX di §6
  python estrai_v1.py /tmp/v1_paper --blocchi 017029
  python estrai_v1.py /tmp/v1_paper --csv fuori.csv
  python estrai_v1.py /tmp/v1_paper --verifica body.tex
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys

NOMI = {
    "037006": "Bologna", "017029": "Brescia", "034027": "Parma",
    "036023": "Modena", "035033": "Reggio nell'Emilia", "039014": "Ravenna",
    "099014": "Rimini", "038008": "Ferrara", "040012": "Forl\\`i",
    "040007": "Cesena", "033032": "Piacenza", "037021": "Castenaso",
}
ORD = list(NOMI)


def _i(s):
    """184.597 -> 184597 ; 4,625 -> 4625. I due separatori convivono nei
    file (italiano nei diagnostici, inglese nei log): si normalizza qui."""
    return int(re.sub(r"[.,\\\s\u00a0]|\\,", "", s))


def _f(s):
    return float(s.replace("%", "").replace(",", ""))


def _cerca(testo, pattern, conv=_f, gruppo=1):
    m = re.search(pattern, testo, re.M)
    return conv(m.group(gruppo)) if m else None


def leggi(d, cod):
    """Tutte le cifre di un comune. Un campo None dice 'non trovato nel
    file', mai 'zero': la differenza conta quando si verifica il paper."""
    r = {"cod": cod, "nome": NOMI.get(cod, cod)}
    p = lambda n: os.path.join(d, n)

    # ---- vincoli: il fit contro il pavimento -------------------------
    with open(p(f"vincoli_{cod}.txt")) as fh:
        t = fh.read()
    r["attributi"] = _cerca(t, r"individui · (\d+) attributi", int)
    r["celle"] = _cerca(t, r"celle con target positivo\s+([\d.]+)", _i)
    r["mre_oss"] = _cerca(t, r"^MRE\s+([\d.]+)%")
    r["mre_att"] = _cerca(t, r"^MRE\s+[\d.]+%\s+([\d.]+)%")
    r["z_med"] = _cerca(t, r"^\|z\| medio\s+([\d.]+)")
    r["z_med_att"] = _cerca(t, r"^\|z\| medio\s+[\d.]+\s+([\d.]+)")
    r["sdz"] = _cerca(t, r"^sd\(z\)\s+([\d.]+)")
    r["media_z"] = _cerca(t, r"^media\(z\)\s+(-?[\d.]+)")
    r["z2"] = _cerca(t, r"^\|z\| > 2\s+([\d.]+)%")
    r["z3"] = _cerca(t, r"^\|z\| > 3\s+([\d.]+)%")
    r["z3_att"] = _cerca(t, r"^\|z\| > 3\s+[\d.]+%\s+([\d.]+)%")
    r["zeri_ok"] = "nessuno: ogni cella dichiarata impossibile" in t
    r["blocchi"] = _blocchi(t)

    # ---- celle: dove vive il |z| estremo -----------------------------
    zmax, att = 0.0, None
    with open(p(f"celle_{cod}.csv")) as fh:
        for riga in csv.DictReader(fh):
            if not riga.get("z"):
                continue
            z = abs(float(riga["z"]))
            if z > zmax:
                zmax, att = z, float(riga["atteso"])
    r["z_max"], r["z_max_atteso"] = zmax, att

    # ---- quinq: allocazione e seam -----------------------------------
    with open(p(f"quinq_{cod}.txt")) as fh:
        t = fh.read()
    r["sezioni"] = _cerca(t, r"^sezioni\s+([\d.]+)", _i)
    r["alloc_mae"] = _cerca(t, r"MAE del totale per sezione\s+([\d.]+)")
    r["corr_sez"] = _cerca(t, r"correlazione oss/sint\s+([\d.]+)")
    r["seam"] = _cerca(t, r"\|residuo\| medio per sezione\s+([\d.]+)")
    r["quinq_mae_cella"] = _cerca(t, r"^MAE\s+([\d.]+)")

    # ---- istruzione x eta --------------------------------------------
    with open(p(f"istr_eta_{cod}.txt")) as fh:
        t = fh.read()
    r["individui"] = _cerca(t, r"^individui\s+([\d.]+)", _i)
    r["istr_quota"] = _cerca(t, r"^quota\s+([\d.]+)%")

    # ---- donatori -----------------------------------------------------
    with open(p(f"donor_{cod}.txt")) as fh:
        t = fh.read()
    r["firme"] = _cerca(t, r"firme distinte\s+([\d.]+)", _i)
    r["riuso_medio"] = _cerca(t, r"riuso medio\s+([\d.]+)")
    r["riuso_max"] = _cerca(t, r"^massimo\s+([\d.]+)", _i)
    for var in ("SALUTE", "PUNTIFI10"):
        m = re.search(rf"^{var}\s+([\d.]+)%\s+([\d.]+)\s+([\d.]+)\s+"
                      rf"([\d.]+)\s+([\d.]+)\s*$", t, re.M)
        if m:
            r[f"neff_{var}"] = _i(m.group(4))
            r[f"banda_{var}"] = _f(m.group(5))

       # ---- log di rigenerazione: il residuo di FIT ----------------------
    # I log non stanno con i diagnostici: undici in rilancio_report_v1.0,
    # Cesena in rilancio_paper_v1.0. Si cercano, non si assume.
    radici = [d, "note/misure/rilancio_report_v1.0",
              "note/misure/rilancio_paper_v1.0"]
    for radice in radici:
        percorso = os.path.join(radice, f"{cod}.log")
        if os.path.exists(percorso):
            break
    else:
        raise FileNotFoundError(f"log di {cod} in nessuna di {radici}")
    with open(percorso) as fh:
        t = fh.read()
    r["fit_mre"] = _cerca(t, r"MRE\(alpha>0\)=([\d.eE+-]+)", float)
    r["n_escl"] = _cerca(t, r"massa su celle escluse: somma=([\d.eE+-]+) \(n=(\d+)\)",
                         int, gruppo=2)
    r["massa_escl"] = _cerca(t, r"massa su celle escluse: somma=([\d.eE+-]+)", float)
    r["H"] = _cerca(t, r"H=([\d.]+) nat")
    m = re.search(r"supporto~([\d,]+)/([\d,]+)", t)
    if m:
        r["supporto"], r["lattice"] = _i(m.group(1)), _i(m.group(2))
    m = re.search(r"donatori distinti usati: ([\d,]+) su ([\d,]+)", t)
    if m:
        r["donatori_usati"], r["pool"] = _i(m.group(1)), _i(m.group(2))
    r["riuso_log"] = _cerca(t, r"riuso medio ([\d.]+)x")
    for chi, key in (("popolazione", "pop"), ("stranieri", "str"), ("UE", "ue")):
        m = re.search(rf"^\s+{chi}\s+MAE\s+([\d.]+) su media\s+([\d.]+) \| "
                      rf"corr ([\d.]+)", t, re.M)
        if m:
            r[f"mae_{key}"], r[f"media_{key}"] = _f(m.group(1)), _f(m.group(2))
            r[f"corr_{key}"] = _f(m.group(3))
    return r


def _blocchi(t):
    """La tabella 'Per blocco': dove l'errore si concentra. E' la sola
    misura che mostra che il fit e' al pavimento BLOCCO PER BLOCCO e non
    solo in media — un aggregato puo' nascondere un blocco fuori posto."""
    out = []
    dentro = False
    for riga in t.splitlines():
        if riga.startswith("blocco "):
            dentro = True
            continue
        if dentro:
            if riga.startswith("---") or not riga.strip():
                if out:
                    break
                continue
            m = re.match(r"^(.+?)\s{2,}(\d+)\s+([\d.]+)\s+([\d.]+)%\s+"
                         r"([\d.]+)%\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s*$", riga)
            if m:
                out.append(dict(blocco=m.group(1).strip(), celle=int(m.group(2)),
                                fuori=float(m.group(3)), mre_oss=float(m.group(4)),
                                mre_att=float(m.group(5)), z_med=float(m.group(6)),
                                z_max=float(m.group(7)), z3=int(m.group(8))))
    return out


# ---------------------------------------------------------------- output

def tabella_sei(righe):
    """La tabella di §6, ricostruita dai file. Rispetto a quella attuale
    aggiunge sd(z) e la coppia (|z| max, attesa della sua cella): sono le
    due colonne che spiegano da sole il caso Forli' e la dispersione,
    senza bisogno del capoverso che oggi le racconta a parole."""
    print(r"\begin{tabular}{lrrrrrrrr}")
    print(r"\toprule")
    print(r"municipality & cells & MRE & floor & mean $|z|$ & sd$(z)$ & "
          r"max $|z|$ & alloc.\ MAE & seam \\")
    print(r" & ($\alpha>0$) & (\%) & (\%) & & & (at $e_c$) & "
          r"(per section) & (per section) \\")
    print(r"\midrule")
    for r in righe:
        floor = (f"{r['mre_att']:,.0f}" if r["mre_att"] >= 1000
                 else f"{r['mre_att']:.2f}")
        print(f"{r['nome']:<20} & {r['celle']:,} & {r['mre_oss']:.2f} & {floor} & "
              f"{r['z_med']:.2f} & {r['sdz']:.3f} & "
              f"{r['z_max']:.1f} ({r['z_max_atteso']:.0f}) & "
              f"{r['alloc_mae']:.2f} & {r['seam']:.2f} \\\\"
              .replace(",", "\\,"))
    print(r"\bottomrule")
    print(r"\end{tabular}")


def tabella_blocchi(r):
    print(f"% blocchi di {r['nome']} ({r['cod']})")
    print(r"\begin{tabular}{lrrrrr}")
    print(r"\toprule")
    print(r"constraint block & cells & MRE & floor & mean $|z|$ & $|z|>3$ \\")
    print(r" & & (\%) & (\%) & & \\")
    print(r"\midrule")
    for b in r["blocchi"]:
        nome = b["blocco"].replace("×", r"$\times$").replace("eta", "age") \
            .replace("sesso", "sex").replace("istruzione", "education") \
            .replace("condizione", "activity").replace("cittadinanza", "citizenship") \
            .replace("stato_civile", "marital status").replace("zona", "zone") \
            .replace("origine_genitori", "parents' origin")
        print(f"{nome:<45} & {b['celle']:>4} & {b['mre_oss']:6.2f} & "
              f"{b['mre_att']:6.2f} & {b['z_med']:.2f} & {b['z3']} \\\\")
    print(r"\bottomrule")
    print(r"\end{tabular}")


def sintesi(righe):
    """I numeri che servono a numbers.tex, con min e max e chi li fa."""
    def banda(k, fmt="{:.2f}"):
        v = [(r[k], r["nome"]) for r in righe if r.get(k) is not None]
        lo, hi = min(v), max(v)
        return (f"{fmt.format(lo[0])} ({lo[1]}) -- {fmt.format(hi[0])} ({hi[1]})")

    print("\n=== bande sui dodici (per numbers.tex) ===")
    for k, lab, fmt in [
        ("fit_mre", "residuo di fit MRE(a>0)", "{:.2e}"),
        ("mre_oss", "MRE campione (%)", "{:.2f}"),
        ("z_med", "|z| medio", "{:.2f}"),
        ("sdz", "sd(z)", "{:.3f}"),
        ("z3", "quota |z|>3 (%)", "{:.2f}"),
        ("alloc_mae", "MAE allocazione", "{:.2f}"),
        ("seam", "seam per sezione", "{:.2f}"),
        ("istr_quota", "eta x titolo (%)", "{:.2f}"),
        ("riuso_log", "riuso donatori", "{:.1f}"),
        ("n_escl", "esclusioni", "{:.0f}"),
        ("H", "entropia (nat)", "{:.3f}"),
    ]:
        print(f"  {lab:<26} {banda(k, fmt)}")
    tot = sum(r["individui"] for r in righe)
    print(f"  {'individui totali':<26} {tot:,}")
    zeri = all(r["zeri_ok"] for r in righe)
    print(f"  {'zeri hard':<26} {'nessuno violato in 12/12' if zeri else 'VIOLATI'}")
    m = max(righe, key=lambda r: r["sdz"])
    print(f"\n  sd(z) massimo: {m['nome']} {m['sdz']:.3f} su {m['celle']:,} celle")
    print("  (la frase attuale di §6, 'unity to three decimals', regge su "
          f"{sum(1 for r in righe if abs(r['sdz'] - 1) < 0.02)}/12)")


def verifica(righe, tex):
    """Ogni riga della tabella in body.tex contro i file. Il paper non ha
    ragione perche' e' scritto: ha ragione se il file lo conferma."""
    with open(tex) as fh:
        t = fh.read()
    print("\n=== verifica della tabella in body.tex ===")
    for r in righe:
        nome = r["nome"]
        m = re.search(rf"^{re.escape(nome)}\s*&([^&]+)&([^&]+)&([^&]+)&([^&]+)&"
                      rf"([^&]+)&([^&]+)&([^\\]+)", t, re.M)
        if not m:
            print(f"  {r['nome']:<20} RIGA NON TROVATA nel .tex")
            continue
        g = [x.strip() for x in m.groups()]
        att = [_i(g[0]), _f(g[1]), _i(g[2]) if "\\," in g[2] else _f(g[2]),
               _f(g[3]), _f(g[4]), _f(g[5]), _f(g[6])]
        oss = [r["celle"], r["mre_oss"], r["mre_att"], r["z_med"],
               r["alloc_mae"], r["seam"], r["istr_quota"]]
        etichette = ["celle", "MRE", "floor", "|z|", "alloc", "seam", "istr"]
        diff = [f"{e}: tex={a} file={o}" for e, a, o in zip(etichette, att, oss)
                if abs(a - o) > max(0.006, abs(o) * 0.002)]
        stato = "ok" if not diff else "DIVERGE"
        print(f"  {r['nome']:<20} {stato}" + ("" if not diff else
                                              "\n      " + "\n      ".join(diff)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", help="cartella con i file diagnostici dei dodici")
    ap.add_argument("--tabella", action="store_true", help="tabella LaTeX di §6")
    ap.add_argument("--blocchi", metavar="COD", help="tabella per blocco di un comune")
    ap.add_argument("--csv", metavar="FILE", help="tutte le cifre in CSV")
    ap.add_argument("--verifica", metavar="BODY.TEX", help="confronta col paper")
    a = ap.parse_args()

    righe = []
    for c in ORD:
        try:
            righe.append(leggi(a.dir, c))
        except FileNotFoundError as e:
            print(f"[manca] {c} {NOMI[c]}: {e.filename}", file=sys.stderr)

    if a.tabella:
        tabella_sei(righe)
    if a.blocchi:
        tabella_blocchi(next(r for r in righe if r["cod"] == a.blocchi))
    if a.verifica:
        verifica(righe, a.verifica)
    if a.csv:
        campi = [k for k in righe[0] if k != "blocchi"]
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=campi, extrasaction="ignore")
            w.writeheader()
            w.writerows(righe)
        print(f"scritto {a.csv}: {len(righe)} comuni, {len(campi)} colonne")
    if not (a.tabella or a.blocchi or a.csv or a.verifica):
        sintesi(righe)
