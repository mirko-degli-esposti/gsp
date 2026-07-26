"""
assign_avq.py — v2 — strato condizionale AVQ (anello 2) con campionamento
per DONATORE (hot-deck): assegna in blocco piu' attributi psicografici,
comportamentali e di salute preservandone le correlazioni interne.

Differenza chiave rispetto alla v1 (campionamento indipendente per
variabile): per ogni individuo sintetico si estrae UN rispondente AVQ
della stessa cella (con probabilita' proporzionale a COEFIN) e se ne copia
il VETTORE COMPLETO dei target. Cosi' le correlazioni fra target sono
preservate per costruzione — e non si producono individui incoerenti
(es. "salute molto male" + "nessuna cronicita'" + MH=95), che sarebbero
l'analogo, nell'anello 2, del bug di indipendenza spuria gia' corretto nel
MaxEnt con il vincolo GC.

Vantaggi collaterali:
  - le variabili continue (MH, indice di salute mentale SF-12 0-100) non
    vanno discretizzate: si copia il valore reale del donatore;
  - i missing strutturali si propagano coerentemente: un donatore bambino
    ha CRONI/FUMO/MH mancanti, e il sintetico corrispondente li eredita
    come 'non_applicabile' (opzione (c) del disegno).

Metodo:
    (1) impila piu' annate AVQ, normalizzando COEFIN entro anno;
    (2) cella di condizionamento: sesso x macro-eta x istruzione4 x regione
        (le classi infantili sono incluse: hanno cella propria, con
        istruzione non definita -> chiave dedicata);
    (3) per ogni cella, pool di donatori con pesi COEFIN normalizzati;
    (4) per ogni individuo sintetico, estrazione di un donatore e copia
        del blocco di target; fallback su pool regionale per celle rade.

Assunzione dichiarata:
    (6) P(target | sesso, eta, istruzione, regione) costante entro la
        regione: la variazione sub-regionale non e' osservabile nel file
        pubblico e viene assunta nulla.

Uso:
    python assign_avq.py 017029 --anno 2024 \\
        --pop-file popolazione_K9C_naz.csv --out popolazione_K9C_avq.csv \\
        --targets AMBIENTE,FIDUCIA,SALUTE,CRONI,FUMO,MH
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

AVQ_DIR = os.path.expanduser("~/progetti/gsp/data/avq/anni")
AVQ_YEARS = ["2022", "2023", "2024"]

COMUNE_REGIONE = {
    "017029": 30,    # Brescia -> Lombardia
    "037006": 80,    # Bologna -> Emilia-Romagna
    "074017": 160,   # San Vito dei Normanni -> Puglia
}
REGIONE_NOMI = {30: "Lombardia", 80: "Emilia-Romagna", 160: "Puglia"}

# ETAMi (classi AVQ) -> macro-classe di condizionamento (incluse le infantili)
ETAMI_MACRO = {
    1: "0-13", 2: "0-13", 3: "0-13", 4: "0-13",                  # 0-13
    5: "15-34", 6: "15-34", 7: "15-34", 8: "15-34", 9: "15-34",  # 14-34
    10: "35-54", 11: "35-54",
    12: "55-64", 13: "55-64",
    14: "65+", 15: "65+",
}
BIN_MACRO = {
    "0-8": "0-13", "9-14": "0-13",
    "15-24": "15-34", "25-34": "15-34",
    "35-49": "35-54",
    "50-64": "55-64",      # approssimazione: 50-54 assimilato a 55-64
    "65-74": "65+", "75+": "65+",
}

ISTRMI_MAP = {1: "terziario", 7: "diploma", 9: "media", 10: "elementare_o_meno"}
ISTR6_TO_4 = {
    "laurea_o_its": "terziario", "post_laurea": "terziario",
    "diploma": "diploma", "media": "media",
    "elementare": "elementare_o_meno", "nessun_titolo": "elementare_o_meno",
}
ISTR_MINORI = "eta_infantile"   # chiave dedicata per le classi 0-13

CELL_COLS = ["sesso", "macroeta", "istr4"]
NA_TOKEN = "non_applicabile"


def load_avq(years, targets, regione):
    """Impila le annate, normalizza i pesi entro anno, ricodifica le celle."""
    frames = []
    for y in years:
        path = os.path.join(AVQ_DIR, f"avq{y}", "MICRODATI", f"AVQ_Microdati_{y}.txt")
        if not os.path.exists(path):
            print(f"[avq] {y}: file assente, annata saltata")
            continue
        keep = set(["ETAMi", "SESSO", "ISTRMi", "REGMf", "COEFIN"] + targets)
        d = pd.read_csv(path, sep="\t", low_memory=False,
                        usecols=lambda c: c in keep)
        missing = [c for c in keep if c not in d.columns]
        if missing:
            print(f"[avq] {y}: variabili mancanti {missing}, annata saltata "
                  f"(il modulo salute AVQ ruota tra le annate: es. CRONI non "
                  f"e' rilevata nel 2022, dove esistono solo le singole "
                  f"patologie DIAB/IPAR/... e LIMITA; ricostruirla darebbe "
                  f"una definizione non equivalente, quindi l'annata si scarta)")
            continue
        w = pd.to_numeric(d["COEFIN"], errors="coerce")
        d["w"] = w / w.sum()          # ogni annata pesa uguale nel pool
        d["anno_avq"] = y
        frames.append(d)
        print(f"[avq] {y}: {len(d):,} record")
    if not frames:
        sys.exit("Nessuna annata AVQ disponibile.")
    a = pd.concat(frames, ignore_index=True)

    a["ETAMi"] = pd.to_numeric(a["ETAMi"], errors="coerce")
    a["ISTRMi"] = pd.to_numeric(a["ISTRMi"], errors="coerce")
    a["REGMf"] = pd.to_numeric(a["REGMf"], errors="coerce")
    a["macroeta"] = a["ETAMi"].map(ETAMI_MACRO)
    a["istr4"] = a["ISTRMi"].map(ISTRMI_MAP)
    # i minori non hanno istruzione rilevata: chiave dedicata
    a.loc[a["macroeta"] == "0-13", "istr4"] = ISTR_MINORI
    a["sesso"] = a["SESSO"].map({1: "M", 2: "F"})

    a = a[a["REGMf"] == regione].copy()
    n0 = len(a)
    a = a.dropna(subset=CELL_COLS + ["w"])
    print(f"[avq] regione {regione} ({REGIONE_NOMI.get(regione, '?')}): "
          f"{len(a):,} donatori con cella completa (su {n0:,})")
    return a


def main(comune, anno, pop_file, out_name, targets, seed, min_record):
    if comune not in COMUNE_REGIONE:
        sys.exit(f"Comune {comune} non nel registro COMUNE_REGIONE.")
    regione = COMUNE_REGIONE[comune]
    cdir = os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")

    a = load_avq(AVQ_YEARS, targets, regione)

    pop = pd.read_csv(os.path.join(cdir, pop_file))
    print(f"[pop] {pop_file}: {len(pop):,} individui")
    for t in targets:
        if t in pop.columns:
            sys.exit(f"La popolazione ha gia' una colonna '{t}'.")

    pop["macroeta"] = pop["eta"].map(BIN_MACRO)
    pop["istr4"] = pop["istruzione"].map(ISTR6_TO_4)
    pop.loc[pop["macroeta"] == "0-13", "istr4"] = ISTR_MINORI
    if pop["macroeta"].isna().any() or pop["istr4"].isna().any():
        n = int(pop["macroeta"].isna().sum() + pop["istr4"].isna().sum())
        print(f"[warn] {n} individui senza cella definita: fallback regionale")

    # ---- pool di donatori per cella ----
    pools, thin = {}, []
    for key, g in a.groupby(CELL_COLS):
        if len(g) < min_record:
            thin.append((key, len(g)))
            continue
        p = g["w"].to_numpy()
        pools[key] = (g.index.to_numpy(), p / p.sum())
    p_all = a["w"].to_numpy()
    pool_reg = (a.index.to_numpy(), p_all / p_all.sum())
    sizes = a.groupby(CELL_COLS).size()
    print(f"[donor] {len(pools)} celle con pool valido "
          f"(record/cella: min={sizes.min()}, mediana={int(sizes.median())}, "
          f"max={sizes.max()})")
    if thin:
        print(f"[donor] {len(thin)} celle sotto {min_record} record "
              f"-> pool regionale: {thin[:5]}")

    # ---- estrazione dei donatori ----
    rng = np.random.default_rng(seed)
    donor_idx = np.empty(len(pop), dtype=np.int64)
    n_fallback = 0
    for key, idx in pop.groupby(CELL_COLS, dropna=False).groups.items():
        idx = np.asarray(idx)
        if key in pools:
            cand, p = pools[key]
        else:
            cand, p = pool_reg
            n_fallback += len(idx)
        donor_idx[idx] = rng.choice(cand, size=len(idx), p=p, replace=True)
    if n_fallback:
        print(f"[donor] {n_fallback:,} individui serviti dal pool regionale")

    # ---- copia in blocco del vettore dei target ----
    don = a.loc[donor_idx, targets].reset_index(drop=True)
    for t in targets:
        col = don[t]
        # missing del donatore -> non_applicabile (propagazione coerente)
        blank = col.isna() | (col.astype(str).str.strip() == "")
        pop[t] = col.where(~blank, NA_TOKEN).to_numpy()
        n_na = int(blank.sum())
        print(f"[{t}] assegnati {len(pop)-n_na:,} | "
              f"{NA_TOKEN} (missing strutturale nel donatore): {n_na:,}")

    # ---- validazione 1: marginali sintetici vs AVQ pesati ----
    print("\n[val] marginali: sintetico vs AVQ pesato (regione)")
    for t in targets:
        s = pd.to_numeric(a[t], errors="coerce")
        ok = s.notna()
        if ok.sum() == 0:
            continue
        if s[ok].nunique() > 12:      # continua: confronto su media
            m_avq = float((s[ok] * a.loc[ok, "w"]).sum() / a.loc[ok, "w"].sum())
            syn = pd.to_numeric(pop[t], errors="coerce")
            m_syn = float(syn.mean())
            print(f"  {t} (continua): media sintetico {m_syn:.2f} | "
                  f"avq {m_avq:.2f} (scarto {m_syn-m_avq:+.2f})")
        else:
            w_avq = a.loc[ok].groupby(s[ok])["w"].sum()
            w_avq = w_avq / w_avq.sum()
            syn = pop.loc[pop[t] != NA_TOKEN, t]
            syn = pd.to_numeric(syn, errors="coerce").value_counts(normalize=True)
            print(f"  {t}:")
            for k in sorted(w_avq.index):
                print(f"    {k:g}: sintetico {syn.get(k, 0):.3f} | "
                      f"avq {w_avq[k]:.3f} (scarto {syn.get(k, 0)-w_avq[k]:+.3f})")

    # ---- validazione 2: coerenza interna (correlazioni preservate) ----
    num = {t: pd.to_numeric(pop[t], errors="coerce") for t in targets}
    num = pd.DataFrame(num).dropna()
    if len(num.columns) >= 2 and len(num) > 100:
        print("\n[val] correlazioni fra target nella popolazione sintetica:")
        print(num.corr().round(3).to_string())
        src = pd.DataFrame({t: pd.to_numeric(a[t], errors="coerce")
                            for t in targets}).dropna()
        if len(src) > 100:
            print("\n[val] stesse correlazioni nei donatori AVQ (riferimento):")
            print(src.corr().round(3).to_string())

    pop = pop.drop(columns=["macroeta", "istr4"])
    out = os.path.join(cdir, out_name)
    pop.to_csv(out, index=False)
    print(f"\n[done] -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Strato AVQ con campionamento per donatore (hot-deck).")
    ap.add_argument("comune", help="codice ISTAT (017029, 037006, 074017)")
    ap.add_argument("--anno", type=int, default=2024)
    ap.add_argument("--pop-file", default="popolazione_K9C_naz.csv")
    ap.add_argument("--out", default="popolazione_K9C_avq.csv")
    ap.add_argument("--targets", default="AMBIENTE,FIDUCIA,SALUTE,CRONI,FUMO,MH",
                    help="variabili AVQ da copiare in blocco dal donatore")
    ap.add_argument("--min-record", type=int, default=20,
                    help="donatori minimi per usare il pool di cella [20]")
    ap.add_argument("--seed", type=int, default=42)
    x = ap.parse_args()
    main(x.comune, x.anno, x.pop_file, x.out,
         [t.strip() for t in x.targets.split(",")], x.seed, x.min_record)
