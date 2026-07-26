"""
assign_avq.py — strato condizionale AVQ (anello 2) sulla popolazione sintetica.

Aggiunge attributi psicografici/comportamentali stimati dai microdati AVQ
(Multiscopo ISTAT, file ad uso pubblico) alla popolazione generata dal MaxEnt.

Metodo:
    (1) impila piu' annate AVQ, normalizzando COEFIN entro anno (cosi' ogni
        annata contribuisce con lo stesso monte di peso);
    (2) costruisce la cella di condizionamento comune ai due dataset:
        sesso x macro-eta x istruzione4 x regione;
    (3) stima P(target | cella) pesata con COEFIN (stima puntuale corretta
        per il disegno campionario complesso dell'indagine);
    (4) campiona un valore per ciascun individuo sintetico adulto
        (multinomiale: a differenza della nazionalita', qui NON esistono
        totali comunali noti da rispettare esattamente).

Universo: individui con eta' >= 15 (bin 15-24 e superiori). Sotto quella
soglia l'AVQ non somministra le domande di opinione: gli attributi restano
'non_applicabile', coerentemente con istruzione/condizione nel CS.

Assunzione dichiarata:
    (6) P(target | sesso, eta, istruzione, regione) e' costante entro la
        regione: la variazione sub-regionale (comune, quartiere) non e'
        osservabile nel file pubblico e viene assunta nulla. La struttura
        territoriale fine resta quella del MaxEnt (zona), su cui l'AVQ non
        aggiunge informazione.

Uso:
    python assign_avq.py 017029 --anno 2024 --pop-file popolazione_K9C_naz.csv \\
        --out popolazione_K9C_avq.csv --targets AMBIENTE,FIDUCIA
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

AVQ_DIR = os.path.expanduser("~/progetti/gsp/data/avq/anni")
AVQ_YEARS = ["2022", "2023", "2024"]

# comune -> codice regione AVQ (REGMf)
COMUNE_REGIONE = {
    "017029": 30,    # Brescia -> Lombardia
    "037006": 80,    # Bologna -> Emilia-Romagna
    "074017": 160,   # San Vito dei Normanni -> Puglia
}
REGIONE_NOMI = {30: "Lombardia", 80: "Emilia-Romagna", 160: "Puglia"}

# ETAMi (classi AVQ) -> macro-classe di condizionamento
ETAMI_MACRO = {
    5: "15-34", 6: "15-34", 7: "15-34", 8: "15-34", 9: "15-34",   # 14-34
    10: "35-54", 11: "35-54",                                      # 35-54
    12: "55-64", 13: "55-64",                                      # 55-64
    14: "65+", 15: "65+",                                          # 65+
}
# bin della popolazione sintetica -> stessa macro-classe
BIN_MACRO = {
    "15-24": "15-34", "25-34": "15-34",
    "35-49": "35-54",          # 35-49 cade dentro 35-54
    "50-64": "55-64",          # approssimazione: 50-54 assimilato a 55-64
    "65-74": "65+", "75+": "65+",
}
BIN_MINORI = {"0-8", "9-14"}   # esclusi dallo strato AVQ

# ISTRMi (AVQ) -> istruzione4; la popolazione sintetica ha 6 livelli
ISTRMI_MAP = {1: "terziario", 7: "diploma", 9: "media", 10: "elementare_o_meno"}
ISTR6_TO_4 = {
    "laurea_o_its": "terziario", "post_laurea": "terziario",
    "diploma": "diploma", "media": "media",
    "elementare": "elementare_o_meno", "nessun_titolo": "elementare_o_meno",
}

CELL_COLS = ["sesso", "macroeta", "istr4", "regione"]


def load_avq(years, targets, regione):
    """Impila le annate AVQ, normalizza i pesi entro anno, filtra e ricodifica."""
    frames = []
    for y in years:
        path = os.path.join(AVQ_DIR, f"avq{y}", "MICRODATI", f"AVQ_Microdati_{y}.txt")
        if not os.path.exists(path):
            print(f"[avq] {y}: file assente ({path}), annata saltata")
            continue
        keep = ["ETAMi", "SESSO", "ISTRMi", "REGMf", "COEFIN"] + targets
        d = pd.read_csv(path, sep="\t", low_memory=False, usecols=lambda c: c in keep)
        missing = [c for c in keep if c not in d.columns]
        if missing:
            print(f"[avq] {y}: variabili mancanti {missing}, annata saltata")
            continue
        d["anno_avq"] = y
        # pesi normalizzati entro anno: ogni annata pesa uguale nel pool
        w = pd.to_numeric(d["COEFIN"], errors="coerce")
        d["w"] = w / w.sum()
        frames.append(d)
        print(f"[avq] {y}: {len(d):,} record caricati")
    if not frames:
        sys.exit("Nessuna annata AVQ disponibile.")
    a = pd.concat(frames, ignore_index=True)

    # ricodifica delle chiavi di cella
    a["ETAMi"] = pd.to_numeric(a["ETAMi"], errors="coerce")
    a["ISTRMi"] = pd.to_numeric(a["ISTRMi"], errors="coerce")
    a["REGMf"] = pd.to_numeric(a["REGMf"], errors="coerce")
    a["macroeta"] = a["ETAMi"].map(ETAMI_MACRO)
    a["istr4"] = a["ISTRMi"].map(ISTRMI_MAP)
    a["sesso"] = a["SESSO"].map({1: "M", 2: "F"})
    a["regione"] = a["REGMf"]

    n0 = len(a)
    a = a.dropna(subset=CELL_COLS + ["w"])
    print(f"[avq] record con cella completa: {len(a):,} / {n0:,} "
          f"(esclusi minori <14 e non-disponibili)")
    return a


def conditional_table(a, target, regione):
    """P(target | cella) pesata con COEFIN, ristretta alla regione richiesta."""
    d = a[a["regione"] == regione].copy()
    d[target] = pd.to_numeric(d[target], errors="coerce")
    d = d.dropna(subset=[target])
    if d.empty:
        sys.exit(f"[{target}] nessun record per regione {regione}")
    num = d.groupby(CELL_COLS + [target])["w"].sum().rename("num").reset_index()
    den = d.groupby(CELL_COLS)["w"].sum().rename("den").reset_index()
    t = num.merge(den, on=CELL_COLS)
    t["p"] = t["num"] / t["den"]
    # diagnostica numerosita': record grezzi per cella (non pesati)
    cnt = d.groupby(CELL_COLS).size().rename("n_record").reset_index()
    t = t.merge(cnt, on=CELL_COLS)
    ncell = t[CELL_COLS].drop_duplicates().shape[0]
    print(f"[{target}] regione {regione} ({REGIONE_NOMI.get(regione, '?')}): "
          f"{ncell} celle, {len(d):,} record | "
          f"record/cella: min={cnt['n_record'].min()}, "
          f"mediana={int(cnt['n_record'].median())}, max={cnt['n_record'].max()}")
    thin = cnt[cnt["n_record"] < 20]
    if len(thin):
        print(f"[{target}] ATTENZIONE: {len(thin)} celle con <20 record "
              f"(stime instabili); fallback su marginale regionale")
    # fallback: marginale regionale, per celle assenti o troppo rade
    marg = d.groupby(target)["w"].sum()
    marg = (marg / marg.sum()).to_dict()
    return t, marg, cnt


def main(comune, anno, pop_file, out_name, targets, seed, min_record):
    if comune not in COMUNE_REGIONE:
        sys.exit(f"Comune {comune} non nel registro COMUNE_REGIONE: "
                 f"aggiungere il codice regione AVQ (REGMf).")
    regione = COMUNE_REGIONE[comune]
    cdir = os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}")

    a = load_avq(AVQ_YEARS, targets, regione)

    pop = pd.read_csv(os.path.join(cdir, pop_file))
    print(f"[pop] {pop_file}: {len(pop):,} individui")
    for t in targets:
        if t in pop.columns:
            sys.exit(f"La popolazione ha gia' una colonna '{t}'.")

    # cella della popolazione sintetica
    pop["macroeta"] = pop["eta"].map(BIN_MACRO)
    pop["istr4"] = pop["istruzione"].map(ISTR6_TO_4)
    pop["regione"] = regione
    adulti = pop["macroeta"].notna() & pop["istr4"].notna()
    print(f"[pop] adulti (>=15 anni) da assegnare: {adulti.sum():,} "
          f"({(~adulti).sum():,} minori -> non_applicabile)")

    rng = np.random.default_rng(seed)

    for target in targets:
        t, marg, cnt = conditional_table(a, target, regione)
        pop[target] = pd.NA
        # tabella cella -> (valori, probabilita')
        lut = {}
        for key, g in t.groupby(CELL_COLS):
            n_rec = int(g["n_record"].iloc[0])
            if n_rec < min_record:
                continue    # cella troppo rada: usera' il marginale
            lut[key] = (g[target].to_numpy(), g["p"].to_numpy())
        vals_marg = np.array(list(marg.keys()))
        p_marg = np.array(list(marg.values()))

        n_fallback = 0
        for key, idx in pop[adulti].groupby(CELL_COLS).groups.items():
            idx = np.asarray(idx)
            if key in lut:
                vals, p = lut[key]
            else:
                vals, p = vals_marg, p_marg
                n_fallback += len(idx)
            p = p / p.sum()
            pop.loc[idx, target] = rng.choice(vals, size=len(idx), p=p)
        pop.loc[~adulti, target] = "non_applicabile"
        if n_fallback:
            print(f"[{target}] {n_fallback:,} individui in celle rade "
                  f"(<{min_record} record): marginale regionale")

        # ---- validazione: marginale sintetico vs marginale AVQ regionale ----
        syn = pop.loc[adulti, target].value_counts(normalize=True).sort_index()
        print(f"[{target}] marginale: sintetico vs AVQ (pesato, regione)")
        for k in sorted(marg):
            s = syn.get(k, 0.0)
            print(f"    {k}: sintetico {s:.3f} | avq {marg[k]:.3f} "
                  f"(scarto {s-marg[k]:+.3f})")

    pop = pop.drop(columns=["macroeta", "istr4", "regione"])
    out = os.path.join(cdir, out_name)
    pop.to_csv(out, index=False)
    print(f"\n[done] -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Strato condizionale AVQ sulla popolazione sintetica.")
    ap.add_argument("comune", help="codice ISTAT (017029, 037006, 074017)")
    ap.add_argument("--anno", type=int, default=2024)
    ap.add_argument("--pop-file", default="popolazione_K9C_naz.csv")
    ap.add_argument("--out", default="popolazione_K9C_avq.csv")
    ap.add_argument("--targets", default="AMBIENTE,FIDUCIA",
                    help="variabili AVQ da assegnare, separate da virgola")
    ap.add_argument("--min-record", type=int, default=20,
                    help="record minimi per usare la condizionale di cella "
                         "invece del marginale regionale [default: 20]")
    ap.add_argument("--seed", type=int, default=42)
    x = ap.parse_args()
    main(x.comune, x.anno, x.pop_file, x.out,
         [t.strip() for t in x.targets.split(",")], x.seed, x.min_record)
