#!/usr/bin/env python3
"""L'AVQ come repertorio di nuclei familiari — verifica di fattibilita'.

La nota metodologica ISTAT dichiara che l'AVQ CAMPIONA FAMIGLIE E
INTERVISTA TUTTI I COMPONENTI (45.005 individui in 19.775 famiglie, 2,28
per famiglia). Se e' vero nei file, `PROFAM` ricostruisce nuclei interi e
l'AVQ puo' fornire all'anello 4 il REPERTORIO delle configurazioni
interne -- chi convive con chi, con quali eta' -- che e' cio' che si
sarebbe altrimenti dovuto cercare in EU-SILC.

Sarebbe una sorgente migliore dei microdati di Parma per tre ragioni:
copre DUE regioni (quindi anche Brescia), ha l'ISTRUZIONE (che a Parma
manca e che M1/M2 non hanno potuto testare come condizionante), e
contiene le configurazioni interne. Parma tornerebbe a fare solo
validazione.


DUE DIFFERENZE DELIBERATE RISPETTO A `assign_avq.py`

(1) SI USANO TUTTE E TRE LE ANNATE, 2022 compreso. Il 2022 e' escluso dal
    pool dell'anello 2 perche' gli manca `CRONI`, che e' una variabile
    TARGET. La struttura familiare non ne ha bisogno: per il repertorio
    le tre annate valgono tutte, e il pool emiliano passa da ~2.000 a
    ~3.000 nuclei. Su una risorsa scarsa e' un guadagno del 50%.

(2) NON SI FILTRA `ISTRMi = 99`. `assign_avq` scarta quei record (52 in
    Emilia) perche' senza titolo mappabile non hanno cella. Per l'anello 2
    e' un donatore in meno; per il repertorio scartare un componente
    MUTILA IL NUCLEO, e una famiglia da quattro diventa una terna falsa.


LA TRAPPOLA DA CUI DIPENDE TUTTO

`PROFAM` RIPARTE DA 1 OGNI ANNO. E' gia' documentato nel riferimento
v22 §13.5, dove aveva contaminato le ICC: impilando le annate, famiglie
di anni diversi finiscono nello stesso grappolo e `k` sale a 5,67 invece
di ~2. Li' era un errore di stima; qui sarebbe peggio, perche' si
assemblerebbero NUCLEI FANTASMA che mescolano persone di annate diverse.

La chiave e' `ANNO|PROFAM`. Lo script misura entrambe le versioni proprio
per rendere visibile la differenza.


COSA DECIDE

  · numero di nuclei per regione -> se il repertorio ha numerosita'
    sufficiente per condizionare su demografia. ~2.000-3.000 nuclei in
    Emilia significa che i nuclei da cinque saranno qualche decina: e' il
    limite da conoscere PRIMA di progettare l'assemblaggio.
  · distribuzione delle ampiezze, pesata con COEFIN, contro `PF3`-`PF8`
    aggregati sui comuni -> se il repertorio e' rappresentativo o va
    ripesato.
  · quali variabili di RUOLO esistono accanto a PROFAM -> se l'AVQ dice
    solo chi sta con chi, o anche in che relazione.

    python scripts/diagnostica/avq_nuclei.py
    python scripts/diagnostica/avq_nuclei.py --regione 30    # Lombardia
"""

import argparse
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

import gsp.common as G

ANNI = (2022, 2023, 2024)
PAT = "data/avq/anni/avq{a}/MICRODATI/AVQ_Microdati_{a}.txt"

# candidati per le variabili di struttura familiare: il tracciato non e'
# stato letto, quindi si cercano per pattern e si riporta cosa esiste
PATTERN_FAM = re.compile(
    r"PROFAM|RELPAR|PARENT|NCOMP|TIPFAM|NUMCOMP|COMPFAM|RELAZ|POSFAM|"
    r"CAPOFAM|INTESTA|NUCLEO", re.I)


def percorso(anno):
    p = PAT.format(a=anno)
    if os.path.exists(p):
        return p
    g = glob.glob(f"data/avq/**/*Microdati_{anno}*.txt", recursive=True)
    return g[0] if g else None


def intestazione(anno):
    p = percorso(anno)
    if not p:
        return None, None
    cols = pd.read_csv(p, sep="\t", nrows=0).columns.tolist()
    return p, cols


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regione", type=int, default=80,
                    help="REGMf: 80 Emilia-Romagna, 30 Lombardia")
    a = ap.parse_args()

    # ---------------------------------------------------- quali colonne
    print("=" * 72)
    print("1. variabili di struttura familiare presenti nei tracciati")
    print("=" * 72)
    trovate = {}
    for anno in ANNI:
        p, cols = intestazione(anno)
        if cols is None:
            print(f"   {anno}: file non trovato")
            continue
        fam = [c for c in cols if PATTERN_FAM.search(c)]
        trovate[anno] = (p, cols, fam)
        print(f"   {anno}: {len(cols)} colonne · struttura familiare: "
              f"{fam if fam else 'NESSUNA'}")

    if not trovate:
        sys.exit("nessun file AVQ trovato: controllare i percorsi")

    comuni_fam = set.intersection(*(set(v[2]) for v in trovate.values()))
    print(f"\n   presenti in TUTTE le annate: {sorted(comuni_fam)}")
    if "PROFAM" not in comuni_fam:
        sys.exit("PROFAM non e' in tutte le annate: verificare il tracciato")

    # ---------------------------------------------------- carica e impila
    base = ["PROFAM", "ETAMi", "SESSO", "ISTRMi", "REGMf", "COEFIN"]
    extra = sorted(comuni_fam - {"PROFAM"})
    pezzi = []
    for anno, (p, cols, _) in trovate.items():
        keep = [c for c in base + extra if c in cols]
        d = pd.read_csv(p, sep="\t", low_memory=False,
                        usecols=lambda c: c in keep)
        d["ANNO"] = anno
        pezzi.append(d)
        print(f"   {anno}: {len(d):,} record letti".replace(",", "."))
    d = pd.concat(pezzi, ignore_index=True)

    d["REGMf"] = pd.to_numeric(d["REGMf"], errors="coerce")
    d["COEFIN"] = pd.to_numeric(d["COEFIN"], errors="coerce") / 10000.0
    r = d[d.REGMf == a.regione].copy()
    nome_reg = {80: "Emilia-Romagna", 30: "Lombardia"}.get(a.regione,
                                                           str(a.regione))

    # ------------------------------------------------- la chiave composita
    print("\n" + "=" * 72)
    print(f"2. PROFAM riparte da 1 ogni anno? — {nome_reg}, {len(r):,} record"
          .replace(",", "."))
    print("=" * 72)
    r["k_ingenua"] = r["PROFAM"].astype(str)
    r["k_giusta"] = r["ANNO"].astype(str) + "|" + r["PROFAM"].astype(str)
    n_i, n_g = r.k_ingenua.nunique(), r.k_giusta.nunique()
    print(f"   nuclei con chiave PROFAM       {n_i:,}"
          .replace(",", ".") + f"   ampiezza media {len(r)/n_i:.2f}")
    print(f"   nuclei con chiave ANNO|PROFAM  {n_g:,}"
          .replace(",", ".") + f"   ampiezza media {len(r)/n_g:.2f}")
    print("   atteso ~2,28 (nota metodologica ISTAT). Se la prima riga da'"
          "\n   un'ampiezza molto piu' alta, la chiave composita e' "
          "obbligatoria.")

    # sovrapposizione fra annate sullo stesso PROFAM
    per_anno = r.groupby("PROFAM")["ANNO"].nunique()
    print(f"   PROFAM presenti in piu' di un'annata: "
          f"{int((per_anno > 1).sum()):,} su {len(per_anno):,}"
          .replace(",", "."))

    # ------------------------------------------------- ampiezza dei nuclei
    print("\n" + "=" * 72)
    print("3. ampiezza dei nuclei, e confronto con il censimento")
    print("=" * 72)
    g = r.groupby("k_giusta")
    amp = g.size()
    peso = g["COEFIN"].first()          # il peso e' della famiglia
    print(f"   nuclei: {len(amp):,}".replace(",", ".")
          + f" · individui: {len(r):,}".replace(",", ".")
          + f" · max ampiezza: {amp.max()}")

    dist = (pd.DataFrame({"amp": amp.clip(upper=6), "w": peso})
            .groupby("amp")["w"].sum())
    dist = dist / dist.sum()
    grezza = amp.clip(upper=6).value_counts(normalize=True).sort_index()

    # censimento: PF3..PF8 aggregati sui comuni della regione in pipeline
    cens = None
    try:
        tot = np.zeros(6)
        n_com = 0
        for c in (getattr(G, "COMUNI", None) or {}):
            try:
                s = pd.read_csv(G.path_sezioni(c))
            except Exception:
                continue
            if "PF3" not in s.columns or G.cod_avq(c) != a.regione:
                continue
            tot += np.array([pd.to_numeric(s[f"PF{i}"], errors="coerce")
                             .fillna(0).sum() for i in range(3, 9)])
            n_com += 1
        if n_com:
            cens = pd.Series(tot / tot.sum(), index=range(1, 7))
            print(f"   censimento: {n_com} comuni della regione in pipeline")
    except Exception as e:
        print(f"   censimento non disponibile: {e}")

    t = pd.DataFrame({"AVQ pesata": dist, "AVQ grezza": grezza})
    if cens is not None:
        t["censimento"] = cens
        t["scarto"] = t["AVQ pesata"] - t["censimento"]
    print("\n" + t.round(4).to_string())
    if cens is not None:
        tvd = 0.5 * float((t["AVQ pesata"] - t["censimento"]).abs().sum())
        print(f"\n   TVD fra ampiezze AVQ pesate e censuarie: {tvd:.4f}")
        print("   piccola -> il repertorio e' rappresentativo;"
              " grande -> va ripesato")

    # ------------------------------------- numerosita' per ampiezza: il limite
    print("\n" + "=" * 72)
    print("4. quanti nuclei per ampiezza — il limite del repertorio")
    print("=" * 72)
    cnt = amp.clip(upper=6).value_counts().sort_index()
    for k, v in cnt.items():
        eti = "6+" if k == 6 else str(k)
        print(f"   ampiezza {eti:2s}  {v:5d} nuclei"
              + ("   <-- sottile" if v < 100 else ""))
    print("\n   Condizionando su sesso x eta x istruzione questi numeri si"
          "\n   frammentano: e' il vincolo che decide quanto puo' essere"
          "\n   fine la tabella di derivazione.")

    # ------------------------------------------- che ruolo dice l'AVQ?
    if extra:
        print("\n" + "=" * 72)
        print("5. variabili di ruolo accanto a PROFAM")
        print("=" * 72)
        for c in extra:
            vc = r[c].value_counts().head(12)
            print(f"\n   {c}: {r[c].nunique()} modalita'")
            print("      " + ", ".join(f"{k}={v}" for k, v in vc.items()))
        print("\n   Se una di queste codifica la relazione col capofamiglia,"
              "\n   l'AVQ da' anche il RUOLO e non solo l'appartenenza.")
    else:
        print("\n   Nessuna variabile di ruolo oltre PROFAM: l'AVQ direbbe"
              "\n   CHI STA CON CHI ma non IN CHE RELAZIONE. Le relazioni si"
              "\n   dovrebbero inferire da eta' e sesso, o prendere da Parma.")


if __name__ == "__main__":
    main()
