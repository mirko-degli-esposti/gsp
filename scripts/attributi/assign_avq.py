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
        del blocco di target; per le celle rade il condizionamento si
        degrada per gradi (istruzione, poi eta') invece di collassare
        sul marginale regionale.

Assunzione dichiarata:
    (6) P(target | sesso, eta, istruzione, regione) costante entro la
        regione: la variazione sub-regionale non e' osservabile nel file
        pubblico e viene assunta nulla.

Uso:
    python assign_avq.py 017029 --anno 2024 \\
        --targets AMBIENTE,FIDUCIA,SALUTE,CRONI,FUMO,MH
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

import gsp.common as G


AVQ_YEARS = ["2022", "2023", "2024"]

AVQ_DIR = G.AVQ_DIR

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
NA_CELL = "__nd__"          # sentinella per chiavi di cella non definite

# Collasso gerarchico del condizionamento quando il pool di cella e' rado.
# L'istruzione si abbandona per prima (corrispondenza piu' incerta fra
# codifica AVQ e codifica censuaria); l'eta' si conserva il piu' a lungo,
# essendo il predittore dominante di salute, fumo e benessere psicologico.
CELL_LEVELS = [
    ["sesso", "macroeta", "istr4"],
    ["sesso", "macroeta"],
    ["macroeta"],
]


def build_pools(a, cols, min_record):
    """Pool di donatori (indici, pesi normalizzati) per una chiave di cella."""
    pools = {}
    for key, g in a.groupby(cols):
        if len(g) < min_record:
            continue
        p = g["w"].to_numpy()
        k = key if isinstance(key, tuple) else (key,)
        pools[k] = (g.index.to_numpy(), p / p.sum())
    return pools

def load_avq(years, targets, opzionali, regione, nome_reg="?"):
    """Impila le annate, normalizza i pesi entro anno, ricodifica le celle.

    'targets' determina quali annate sono utilizzabili: se una manca,
    l'annata si scarta. 'opzionali' vengono prese dove ci sono e restano
    NaN altrove, cosi' il modulo a rotazione di AVQ non costringe a
    dimezzare il pool di donatori per quattro variabili.
    """
    frames = []
    for y in years:
        path = os.path.join(AVQ_DIR, f"avq{y}", "MICRODATI",
                            f"AVQ_Microdati_{y}.txt")
        if not os.path.exists(path):
            # 2022: CRONI non e' presente e non ha equivalenti. Verificato il 1/8/2026
            # contro il tracciato e i dati: l'unica variabile con nome simile e' MALAT,
            # che pero' e' vuota nel 99,99% dei casi (contro il 65/27/8 di CRONI) —
            # altra domanda, non un rinominamento. Il pool resta a due annate.
            print(f"[avq] {y}: file assente, annata saltata")
            continue
        base = ["ETAMi", "SESSO", "ISTRMi", "REGMf", "COEFIN"]
        keep = set(base + targets + opzionali)
        d = pd.read_csv(path, sep="\t", low_memory=False,
                        usecols=lambda c: c in keep)
        # numero di riga DENTRO l'annata: e' l'unica parte dell'identita'
        # del donatore che non cambia fra corse. L'indice di `a` no: dipende
        # da quali annate sono state caricate, e con CRONI fra i target il
        # 2022 salta e slittano tutti.
        d["riga_avq"] = np.arange(len(d), dtype=np.int32)
        
        missing = [c for c in base + targets if c not in d.columns]
        if missing:
            print(f"[avq] {y}: variabili NECESSARIE mancanti {missing}, "
                  f"annata saltata")
            continue
        assenti = [c for c in opzionali if c not in d.columns]
        for c in assenti:
            d[c] = np.nan
        if assenti:
            print(f"[avq] {y}: opzionali assenti -> NaN: {assenti}")
        w = pd.to_numeric(d["COEFIN"], errors="coerce")
        d["w"] = w / w.sum()
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
    a["donor_id"] = (a["anno_avq"].astype(str) + ":"
                     + a["riga_avq"].astype(str))

    a = a[a["REGMf"] == regione].copy()
    n0 = len(a)
    a = a.dropna(subset=CELL_COLS + ["w"])
    print(f"[avq] regione {regione} ({nome_reg}): "
          f"{len(a):,} donatori con cella completa (su {n0:,})")
    return a


def main(comune, anno, pop_file, out_name, targets, opzionali, seed, min_record):
    try:
        nome_reg = G.REGIONI[G.info(comune)["regione"]]["nome"]
    except KeyError as e:
        sys.exit(str(e))
    regione = G.cod_avq(comune)
    cdir = G.path_constraints(comune, anno)

    a = load_avq(AVQ_YEARS, targets, opzionali, regione, nome_reg)
    tutti = targets + opzionali
    pop_file = G.resolve_pop_file(cdir, pop_file)
    pop = pd.read_csv(os.path.join(cdir, pop_file)).reset_index(drop=True)
    if out_name is None:
        out_name = pop_file.replace(".csv", "_avq.csv")
    print(f"[pop] {pop_file}: {len(pop):,} individui")
    for t in tutti + ["donor_id"]:
        if t in pop.columns:
            sys.exit(f"La popolazione ha gia' una colonna '{t}'.")

    pop["macroeta"] = pop["eta"].map(BIN_MACRO)
    pop["istr4"] = pop["istruzione"].map(ISTR6_TO_4)
    pop.loc[pop["macroeta"] == "0-13", "istr4"] = ISTR_MINORI

    # NaN -> sentinella esplicita: nessuna chiave puo' sparire dal groupby,
    # e la sentinella non esiste nei pool -> cade sul fallback per costruzione
    nd = pop[CELL_COLS].isna().any(axis=1)
    if nd.any():
        print(f"[warn] {int(nd.sum()):,} individui senza cella definita "
              f"-> fallback")
        for c in CELL_COLS:
            n_c = int(pop[c].isna().sum())
            if n_c:
                print(f"        {c}: {n_c:,} mancanti")
    pop[CELL_COLS] = pop[CELL_COLS].fillna(NA_CELL)

    # ---- pool gerarchici: cella piena -> collassi progressivi -> regionale ----
    livelli = [(cols, build_pools(a, cols, min_record)) for cols in CELL_LEVELS]
    p_all = a["w"].to_numpy()
    pool_reg = (a.index.to_numpy(), p_all / p_all.sum())

    print(f"\n[donor] pool per livello (soglia {min_record} record):")
    for cols, pl in livelli:
        tot = a.groupby(cols).size()
        print(f"  {' x '.join(cols):<28} {len(pl):>3} pool validi su {len(tot):>3} "
              f"celle | record/cella mediana {int(tot.median())}")
        if len(pl) < len(tot):
            rade = [(k, int(v)) for k, v in tot.items()
                    if (k if isinstance(k, tuple) else (k,)) not in pl]
            print(f"       sotto soglia: {rade}")

    # ---- estrazione dei donatori ----
    rng = np.random.default_rng(seed)
    donor_idx = np.full(len(pop), -1, dtype=np.int64)
    pos_of = {c: i for i, c in enumerate(CELL_COLS)}
    uso = {}

    grp = pop.groupby(CELL_COLS).indices     # chiave -> POSIZIONI (non etichette)
    for key in sorted(grp):                  # ordine deterministico
        pos = grp[key]
        cand = p = None
        for liv, (cols, pl) in enumerate(livelli):
            sub = tuple(key[pos_of[c]] for c in cols)
            if sub in pl:
                cand, p = pl[sub]
                uso[liv] = uso.get(liv, 0) + len(pos)
                break
        if cand is None:
            cand, p = pool_reg
            uso["reg"] = uso.get("reg", 0) + len(pos)
        donor_idx[pos] = rng.choice(cand, size=len(pos), p=p, replace=True)

    if (donor_idx < 0).any():
        sys.exit(f"[bug] {int((donor_idx < 0).sum()):,} individui senza donatore")

    print("\n[donor] individui per livello di condizionamento effettivo:")
    for liv, (cols, _) in enumerate(livelli):
        n = uso.get(liv, 0)
        if n:
            print(f"  {' x '.join(cols):<28} {n:>9,}  ({n/len(pop):5.1%})")
    if uso.get("reg"):
        print(f"  {'regionale (nessun condiz.)':<28} {uso['reg']:>9,}  "
              f"({uso['reg']/len(pop):5.1%})")

    n_estratti = len(np.unique(donor_idx))
    print(f"[donor] donatori distinti usati: {n_estratti:,} su {len(a):,} "
          f"({n_estratti/len(a):.1%}) | riuso medio {len(pop)/n_estratti:.1f}x")

    # l'identita' del donatore scritta a monte, non ricostruita a valle:
    # la firma a 23 valori e' esatta per gli adulti e collide sul 90% dei
    # minori, che hanno 19-21 variabili mancanti (riferimento §13.3).
    pop["donor_id"] = a.loc[donor_idx, "donor_id"].to_numpy()
    print(f"[donor] colonna `donor_id` scritta: "
          f"{pop['donor_id'].nunique():,} valori distinti")

    # ---- copia in blocco del vettore dei target ----
    don = a.loc[donor_idx, tutti].reset_index(drop=True)
    for t in tutti:
        col = don[t]
        # missing del donatore -> non_applicabile. Per le variabili
        # opzionali il missing e' in gran parte STRUTTURALE: dipende
        # dall'annata del donatore, non dall'individuo.
        blank = col.isna() | (col.astype(str).str.strip() == "")
        pop[t] = col.where(~blank, NA_TOKEN).to_numpy()
        n_na = int(blank.sum())
        nota = " [opzionale]" if t in opzionali else ""
        print(f"[{t}] assegnati {len(pop)-n_na:,} | "
              f"{NA_TOKEN}: {n_na:,}{nota}")

    # ---- validazione 1: marginali sintetici vs AVQ pesati ----
    print("\n[val] marginali: sintetico vs AVQ pesato (regione)")
    for t in tutti:
        s = pd.to_numeric(a[t], errors="coerce")
        ok = s.notna()
        if ok.sum() == 0:
            continue
        if s[ok].nunique() > 6:     # 0-10 e MH: confronto su media
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
    # La numerosita' effettiva del sintetico non e' il numero di individui
    # ma il numero di DONATORI distinti: una coppia di variabili a universi
    # quasi disgiunti puo' poggiare su poche decine di donatori replicati
    # migliaia di volte (BMIMIN x VOTOUSL: 266 individui su 198k, ma una
    # manciata di donatori). Si mascherano le coppie sotto i 100 donatori.
    num = pd.DataFrame({t: pd.to_numeric(pop[t], errors="coerce")
                        for t in tutti})
    src = pd.DataFrame({t: pd.to_numeric(a[t], errors="coerce")
                        for t in tutti})
    if num.shape[1] >= 2:
        # La numerosita' effettiva non e' il numero di donatori
        # DISPONIBILI nel pool ma di quelli effettivamente ESTRATTI: una
        # coppia con 400 disponibili e 60 estratti poggia su 60
        # osservazioni indipendenti, non 400, e con la soglia sui
        # disponibili passerebbe il filtro senza doverlo.
        usati = np.unique(donor_idx)
        ok_u = src.loc[usati].notna().astype(int)
        n_coppia = ok_u.T @ ok_u                 # estratti distinti per coppia
        ok_d = src.notna().astype(int)
        n_disp = ok_d.T @ ok_d                   # disponibili, per confronto

        C = num.corr(min_periods=100).where(n_coppia >= 100)
        print(f"\n[val] correlazioni fra target (mascherate se < 100 "
              f"donatori distinti ESTRATTI):")
        print(C.round(3).to_string())

        m = ((n_disp >= 100) & (n_coppia < 100)).to_numpy()
        piu_lasco = int(np.triu(m, k=1).sum())
        if piu_lasco:
            print(f"[val] {piu_lasco} coppie superano la soglia sui "
                  f"DISPONIBILI ma non sugli ESTRATTI: prima passavano.")

        R = src.corr(min_periods=100)
        print("\n[val] stesse correlazioni nei donatori AVQ (riferimento):")
        print(R.round(3).to_string())

        # scarto sintetico-donatori: e' IL controllo che giustifica
        # l'hot-deck, e su 23 variabili sono 253 coppie da guardare a
        # occhio. Ridotto a due numeri piu' le tre peggiori.
        D = (C - R).abs()
        # niente np.fill_diagonal: con pandas 3 il .values e' una vista
        # in sola lettura. Si maschera la diagonale via etichette.
        for t in D.columns:
            D.loc[t, t] = np.nan
        n_cop = int(D.notna().to_numpy().sum() // 2)
        print(f"\n[val] scarto |sintetico - donatori| su {n_cop} coppie: "
              f"max {D.max().max():.3f} | mediano {D.stack().median():.3f}")
        peggiori = D.stack().sort_values(ascending=False)
        viste = set()
        for (i, j), v in peggiori.items():
            if (j, i) in viste:
                continue
            viste.add((i, j))
            nd = int(n_coppia.loc[i, j])
            print(f"       {i} x {j}: {v:.3f}  (n={nd:,}, atteso ~{1/nd**0.5:.3f})")
            if len(viste) == 3:
                break


        # coppie che la vecchia soglia (sui DISPONIBILI) lasciava passare:
        # solo il triangolo superiore, la diagonale non e' una coppia
        m = ((n_disp >= 100) & (n_coppia < 100)).to_numpy()
        piu_lasco = int(np.triu(m, k=1).sum())
        if piu_lasco:
            print(f"[val] {piu_lasco} coppie superano la soglia sui "
                  f"DISPONIBILI ma non sugli ESTRATTI: prima passavano.")

        print("\n[val] stesse correlazioni nei donatori AVQ (riferimento):")
        print(src.corr(min_periods=100).round(3).to_string())

    
    pop = pop.drop(columns=["macroeta", "istr4"])

    out = os.path.join(cdir, out_name)
    pop.to_csv(out, index=False)
    print(f"\n[done] -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Strato AVQ con campionamento per donatore (hot-deck).")
    ap.add_argument("comune", help="codice ISTAT del comune (vedi registro in gsp_common.py)")
    ap.add_argument("--anno", type=int, default=2024)
    ap.add_argument("--pop-file", default=None,
                    help="default: auto-detect popolazione_K10C.csv -> "
                         "K9C -> ... -> K6C in constraints_<anno>/")
    ap.add_argument("--out", default=None,
                    help="default: <file popolazione>_avq.csv")
    ap.add_argument("--targets", default=",".join(G.AVQ_TARGETS),
                    help="variabili AVQ da copiare in blocco dal donatore")
    ap.add_argument("--min-record", type=int, default=20,
                    help="donatori minimi per usare il pool di cella [20]")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--targets-opt", default=",".join(G.AVQ_OPZIONALI),
                    help="variabili prese dove disponibili, NaN altrove "
                         "(il modulo AVQ ruota fra le annate)")
    x = ap.parse_args()
    opz = [t.strip() for t in x.targets_opt.split(",") if t.strip()]
    main(x.comune, x.anno, x.pop_file, x.out,
         [t.strip() for t in x.targets.split(",")], opz, x.seed, x.min_record)
