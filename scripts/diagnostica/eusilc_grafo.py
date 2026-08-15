#!/usr/bin/env python3
"""EU-SILC: ricostruzione del grafo di parentela dal Public Use File.

Continua `eusilc_exploration_v2.md` §9. Risponde alle domande aperte 2, 3
e 4, e produce i ruoli familiari nella stessa classificazione operativa
usata per il repertorio AVQ (`nota_repertorio_avq_v3.md` §2.2), cosi' che
le due fonti siano confrontabili.


LA DISCIPLINA PUF/SUF

Il PUF e' **completamente sintetico** per dichiarazione Eurostat. Quindi:

  · IL CODICE e' quello definitivo: girera' sul SUF senza modifiche.
  · I NUMERI NO. Nessuna cifra prodotta da questo script e' una stima
    sulla popolazione italiana. Sono TEST DEL SOFTWARE.

Il test piu' utile e' il divario generazionale: sull'AVQ la mediana e'
33 anni (n=5.395). Se il PUF ne da' uno simile, il parser legge bene i
puntatori; se ne da' 12, c'e' un bug. Questo e' un uso legittimo di dati
sintetici -- verificare che il software funzioni -- e non diventa una
stima solo perche' il numero e' plausibile.


PERCHE' EU-SILC E' PIU' RICCO DEL CENSIMENTO E DELL'AVQ

L'AVQ e i microdati di Parma codificano la RELAZIONE CON UN
RIFERIMENTO (`RELPAR`): «figlio della persona di riferimento». EU-SILC
codifica invece dei PUNTATORI: ogni persona porta l'identificativo del
padre, della madre e del partner dentro la stessa famiglia. Non e' una
codifica equivalente ma un grafo, da cui i ruoli si DERIVANO invece di
essere letti -- e da cui si ricavano relazioni che `RELPAR` non
distingue (fratelli veri contro fratellastri, nuclei multipli nella
stessa famiglia).

Le variabili attese sono `RB220` (padre), `RB230` (madre), `RB240`
(partner). Lo script NON le assume: le cerca, e se non le trova cerca
qualunque colonna che si comporti da puntatore interno alla famiglia.


L'ANOMALIA DI §5 HA UNA CONSEGUENZA SUI PUNTATORI

`RB030` non e' univoco: nella famiglia 356462 due persone condividono
l'identificativo 3564621. La chiave tecnica `person_key` (decisione
D002) risolve l'identita' delle RIGHE, ma i puntatori contengono l'ID
SORGENTE: un puntatore verso 3564621 non si sa a quale delle due si
riferisca.

Lo script misura quanti puntatori sono ambigui prima di costruire il
grafo. Se sono pochi, si documentano e si escludono; se sono molti, il
grafo non e' ricostruibile e va capito perche'.

    python scripts/diagnostica/eusilc_grafo.py --dir data/eusilc/puf
"""

import argparse
import glob
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

# candidati per i puntatori, in ordine di priorita'
PUNTATORI = {"padre": ["RB220"], "madre": ["RB230"], "partner": ["RB240"]}
ORDINE = {"R": 0, "P": 1, "F": 2, "G": 3, "A": 4, "N": 5}

# riferimenti dall'AVQ, per il test del software (nota_repertorio §4.1)
AVQ_GEN_MEDIANA = 33
AVQ_FIRME = {"R": 0.331, "RP": 0.227, "RPF": 0.143, "RPFF": 0.123,
             "RF": 0.068, "RFF": 0.026}


def trova_file(d, anno=None):
    """I file D/H/R/P. I nomi sono `IT_2013r_EUSILC.csv`: la lettera del
    file e' l'ultimo carattere del secondo campo, minuscola."""
    out = defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(d, "**", "*.csv"), recursive=True)):
        m = re.search(r"_(\d{4})([dhrp])_", os.path.basename(f))
        if m:
            out[int(m.group(1))][m.group(2).upper()] = f
    if anno:
        return out.get(anno, {})
    return out[max(out)] if out else {}          # l'ultima annata


def leggi(path):
    for sep in (",", ";", "\t"):
        try:
            d = pd.read_csv(path, sep=sep, low_memory=False)
            if d.shape[1] > 3:
                return d
        except Exception:
            continue
    sys.exit(f"non riesco a leggere {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/eusilc/puf")
    ap.add_argument("--anno", type=int, default=None,
                    help="anno dell'indagine, per il calcolo dell'eta'")
    a = ap.parse_args()

    f = trova_file(a.dir)
    if "R" not in f:
        sys.exit(f"file R non trovato in {a.dir}\ntrovati: {f}")
    print("file trovati:", {k: os.path.basename(v) for k, v in f.items()})

    r = leggi(f["R"])
    p = leggi(f["P"]) if "P" in f else None
    print(f"R: {r.shape} · P: {p.shape if p is not None else '—'}")

    hh = "RX030" if "RX030" in r.columns else (
        "RB040" if "RB040" in r.columns else None)
    if hh is None:
        cand = [c for c in r.columns if c.endswith("030") or c.endswith("040")]
        sys.exit(f"chiave famiglia non trovata; candidati: {cand}")
    pid = "RB030"
    print(f"chiavi: famiglia={hh} persona={pid}")

    # ------------------------------------------------ domanda aperta 2
    print("\n" + "=" * 70)
    print("2. la differenza R − P e' l'universo del questionario personale?")
    print("=" * 70)
    if p is not None and "RB080" in r.columns:
        anno = a.anno or (int(r["RB010"].mode()[0])
                          if "RB010" in r.columns else None)
        if anno:
            r["eta"] = anno - pd.to_numeric(r["RB080"], errors="coerce")
            ppid = "PB030" if "PB030" in p.columns else pid
            in_p = set(p[ppid].dropna())
            fuori = r[~r[pid].isin(in_p)]
            print(f"   anno indagine: {anno} · in R ma non in P: {len(fuori):,}"
                  .replace(",", "."))
            if "eta" in fuori and fuori.eta.notna().any():
                print(f"   eta': max {fuori.eta.max():.0f} · "
                      f"quota under 16 {(fuori.eta < 16).mean():.3f}")
                print(f"   in R con eta' < 16: {int((r.eta < 16).sum()):,}"
                      .replace(",", "."))
                print("   se i due numeri coincidono, la differenza e'"
                      " interamente l'universo 16+")
    else:
        print("   file P o RB080 assenti: non verificabile")

    # ------------------------------------------- domande aperte 3 e 4
    print("\n" + "=" * 70)
    print("3-4. i puntatori di parentela")
    print("=" * 70)
    col = {}
    for ruolo, cands in PUNTATORI.items():
        c = next((x for x in cands if x in r.columns), None)
        col[ruolo] = c
        if c:
            v = pd.to_numeric(r[c], errors="coerce")
            print(f"   {ruolo:8s} {c}: valorizzato {v.notna().mean():.3f} "
                  f"({int(v.notna().sum()):,} record)".replace(",", "."))
        else:
            print(f"   {ruolo:8s} NON TROVATO fra {cands}")

    if not any(col.values()):
        print("\n   Nessun puntatore trovato. Cerco colonne che si comportino")
        print("   da puntatore interno alla famiglia (valori che coincidono")
        print("   con identificativi di altri membri):")
        chiavi = set(zip(r[hh], r[pid]))
        for c in r.columns:
            if c in (pid, hh) or r[c].dtype == object:
                continue
            v = pd.to_numeric(r[c], errors="coerce")
            if v.notna().sum() < 100:
                continue
            q = np.mean([(h, x) in chiavi for h, x in
                         zip(r[hh][v.notna()][:2000], v.dropna()[:2000])])
            if q > 0.5:
                print(f"      {c}: {q:.2f} dei valori punta a un membro")
        sys.exit("\n   verificare il tracciato prima di procedere")

    # ---------------------------------- l'ambiguita' ereditata da §5
    print("\n" + "=" * 70)
    print("l'anomalia di §5: quanti puntatori sono ambigui?")
    print("=" * 70)
    dup = r.groupby([hh, pid]).size()
    amb = set(dup[dup > 1].index)
    print(f"   coppie (famiglia, id_persona) duplicate: {len(amb)}")
    n_amb = 0
    for c in filter(None, col.values()):
        v = pd.to_numeric(r[c], errors="coerce")
        n_amb += sum((h, x) in amb for h, x in zip(r[hh][v.notna()],
                                                   v.dropna()))
    tot_punt = sum(pd.to_numeric(r[c], errors="coerce").notna().sum()
                   for c in filter(None, col.values()))
    print(f"   puntatori totali {tot_punt:,}".replace(",", ".")
          + f" · verso un id ambiguo {n_amb}")
    print("   `person_key` (D002) risolve l'identita' delle RIGHE, ma i")
    print("   puntatori contengono l'ID SORGENTE: se pochi, si escludono e")
    print("   si documenta; se molti, il grafo non e' ricostruibile.")

    # ------------------------------------------------------- il grafo
    print("\n" + "=" * 70)
    print("il grafo: ruoli derivati, nella classificazione del repertorio")
    print("=" * 70)
    r = r.reset_index(drop=True)
    r["riga"] = r.index
    idx = {}
    for i, h, x in zip(r.riga, r[hh], r[pid]):
        idx.setdefault((h, x), i)     # in caso di ambiguita': la prima

    def punta(i, quale):
        c = col.get(quale)
        if not c:
            return None
        v = r.at[i, c]
        if pd.isna(v):
            return None
        return idx.get((r.at[i, hh], int(v)))

    eta = (pd.to_numeric(r["RB080"], errors="coerce")
           if "RB080" in r.columns else pd.Series(np.nan, index=r.index))
    ruolo = pd.Series(pd.NA, index=r.index, dtype="object")
    firme, gen, part, diag = [], [], [], Counter()

    for h, g in r.groupby(hh):
        m = list(g.riga)
        genitori = {i: [x for x in (punta(i, "padre"), punta(i, "madre"))
                        if x is not None] for i in m}
        partner = {i: punta(i, "partner") for i in m}
        figli = defaultdict(list)
        for i in m:
            for gg in genitori[i]:
                figli[gg].append(i)

        # riferimento: senza genitori in famiglia, con piu' legami, il piu'
        # anziano a parita'. E' una CONVENZIONE: EU-SILC non designa una
        # persona di riferimento, a differenza di RELPAR.
        cand = [i for i in m if not genitori[i]] or m
        rif = max(cand, key=lambda i: (len(figli[i]) + (partner[i] is not None),
                                       -(eta.get(i) or 9999)))
        ruolo[rif] = "R"
        pa = partner[rif]
        if pa is not None and pa in m:
            ruolo[pa] = "P"
            if pd.notna(eta[pa]) and pd.notna(eta[rif]):
                part.append(int(eta[rif] - eta[pa]))
        for i in set(figli[rif]) | (set(figli[pa]) if pa is not None else set()):
            if pd.isna(ruolo[i]):
                ruolo[i] = "F"
                if pd.notna(eta[i]) and pd.notna(eta[rif]):
                    gen.append(int(eta[i] - eta[rif]))
        for gg in genitori[rif]:
            if pd.isna(ruolo[gg]):
                ruolo[gg] = "G"
        for i in m:
            if pd.isna(ruolo[i]):
                ruolo[i] = "A"
        firme.append("".join(sorted((ruolo[i] for i in m),
                                    key=lambda x: ORDINE[x])))
        diag["famiglie"] += 1
        diag["senza_legami"] += int(all(not genitori[i] and partner[i] is None
                                        for i in m) and len(m) > 1)

    fs = pd.Series(firme).value_counts(normalize=True)
    print(f"   famiglie {diag['famiglie']:,}".replace(",", ".")
          + f" · firme distinte {fs.size}"
          + f" · famiglie plurime senza alcun legame {diag['senza_legami']}")
    print("\n   firma      PUF     AVQ    (l'AVQ e' il dato vero, il PUF"
          " e' sintetico)")
    for k in sorted(set(fs.index[:10]) | set(AVQ_FIRME),
                    key=lambda x: -fs.get(x, 0)):
        av = AVQ_FIRME.get(k)
        print(f"   {k:8s} {fs.get(k, 0):6.3f}  "
              + (f"{av:6.3f}" if av else "     —"))

    # ------------------------------------------- il test del software
    print("\n" + "=" * 70)
    print("TEST DEL SOFTWARE — non sono stime")
    print("=" * 70)
    if gen:
        g = np.array(gen)
        print(f"   divario generazionale: n={len(g):,}".replace(",", ".")
              + f" · mediana {np.median(g):.0f}"
              + f" · p05 {np.percentile(g, 5):.0f}"
              + f" · p95 {np.percentile(g, 95):.0f}")
        print(f"   AVQ: mediana {AVQ_GEN_MEDIANA}, p05 21, p95 45")
        ok = abs(np.median(g) - AVQ_GEN_MEDIANA) < 8
        print("   -> " + ("il parser legge bene i puntatori"
                          if ok else
                          "SCARTO GRANDE: probabile bug nella risoluzione"))
    if part:
        q = np.array(part)
        print(f"\n   divario fra partner: n={len(q):,}".replace(",", ".")
              + f" · mediana {np.median(q):+.0f}"
              + f" · p05 {np.percentile(q, 5):+.0f}"
              + f" · p95 {np.percentile(q, 95):+.0f}")
        print("   E' LA MISURA CHE SERVE, e che l'AVQ non puo' dare: le sue")
        print("   classi d'eta' sono larghe 5-10 anni e restituiscono")
        print("   mediana 0, che significa «stessa classe» e non «stessa")
        print("   eta'». Qui il valore e' sintetico; sul SUF sara' quello")
        print("   con cui sostituire `PARTNER_MAX_DIFF`, oggi convenzionale.")

    print("\n   Sul SUF questo script gira senza modifiche. I numeri di")
    print("   sopra vanno riportati come test, mai come stime.")


if __name__ == "__main__":
    main()
