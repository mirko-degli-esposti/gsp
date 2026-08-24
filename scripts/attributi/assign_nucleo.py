#!/usr/bin/env python3
"""assign_nucleo.py — anello 4: struttura familiare, in produzione.

Assegna `id_nucleo` e `ruolo` a ogni individuo della popolazione
sintetica, usando `gsp.nucleo`. Sul modello di `assign_avq.py`.

    python scripts/attributi/assign_nucleo.py 034027
    python scripts/attributi/assign_nucleo.py 034027 037006 017029
    python scripts/attributi/assign_nucleo.py --tutti


COSA SCRIVE, E COSA NON TOCCA

  · `nuclei_{comune}.csv`            uid, id_nucleo, ruolo
  · `nuclei_{comune}_diagnostica.json`

**Il file di popolazione NON viene modificato.** E' la promessa in testa
a `nota_repertorio_avq_v3.md` §1, e qui e' garantita nel modo piu'
semplice: lo script apre la popolazione in sola lettura e scrive altrove.
Il test di regressione e' banale -- il file di popolazione non cambia mai
-- e chi consuma fa il join su `uid`.

`stato_civile` entra in `assembla` in sola lettura: serve a decidere chi
mettere con chi, non a essere riscritto. I vincoli MaxEnt restano
soddisfatti.

Gli individui NON COLLOCATI -- convivenze anagrafiche e residui, l'1,4-1,9%
-- compaiono nel CSV con `id_nucleo` VUOTO, non omessi. Omettendoli, chi
fa il join non distinguerebbe «convivenza» da «riga persa nel join».


IL SEME

Deterministico e derivato dal comune: `seme_base + int(comune)`. Con un
seme globale, girare due comuni insieme o separatamente darebbe risultati
diversi -- l'`rng` avanzerebbe. Il seme effettivo e' scritto nella
diagnostica.


LIMITI, tutti misurati e documentati in `nota_repertorio_avq_v3.md`

  · 18-23% dei coniugati non sta in una coppia di coniugati. NON e' un
    difetto dell'accoppiamento: chi ha ruolo `P` e' corretto nel 97-98%
    dei casi, chi ha ruolo `R` nel 92-94%. Mancano gli SLOT, perche' il
    repertorio chiede coppie in base alle ampiezze censuarie e non a
    quanti coniugati ci sono. Il constraint set non impone che ci si
    sposi a due a due: l'anello 4 rivela un'incoerenza gia' presente
    nella popolazione, non la crea (§7.4).
  · il divario fra partner e' CONVENZIONALE (±15 anni): le classi
    `ETAMi` non risolvono sotto i 10 anni. Serve il SUF EU-SILC.
  · i limiti del genitore sono per analogia (n=175, 45% nella classe
    aperta): e' il parametro piu' debole, e il ripiego `G fuori dai
    limiti` e' il secondo per frequenza.
  · nessuna coppia dello stesso sesso: 0,000 su 4.525 partner nell'AVQ,
    strutturale. La popolazione eredita l'assenza.
  · l'INDIRIZZO resta assegnato per individuo: marito e moglie possono
    risultare a due civici diversi. Va assegnato per famiglia, ed e' il
    presupposto dell'assegnazione a edificio (§9.3).
"""

import argparse
import glob
import json
import os
import sys
import time
from collections import Counter

import numpy as np
import pandas as pd

import gsp.common as G
import gsp.nucleo as N

REP_DEFAULT = "data/repertorio_nuclei_v1.json"
SEME_BASE = 20260810
CONIUGATO = "coniugato_unito"


def trova_popolazione(comune, anno=None):
    pat = (f"data/comuni/{comune}/constraints_{anno}/popolazione_K*_avq_full.csv"
           if anno else
           f"data/comuni/{comune}/constraints_*/popolazione_K*_avq_full.csv")
    c = [p for p in sorted(glob.glob(pat)) if "backup" not in p]
    return c[-1] if c else None


def elenco_comuni():
    for attr in ("COMUNI", "REGISTRO", "REGISTRO_COMUNI", "INFO"):
        v = getattr(G, attr, None)
        if isinstance(v, dict) and v:
            return sorted(v)
    return None


def incoerenza_per_ruolo(r, usa_sc):
    """Metrica PER COPPIA (nota §7.3): un coniugato e' coerente solo se
    sta in una coppia (R,P) in cui anche l'altro e' coniugato, o se vive
    solo. La metrica per NUCLEO -- «c'e' un altro coniugato» -- e' troppo
    debole: un `RPF` con tre coniugati la soddisfa e contiene un figlio
    sposato con nessuno."""
    if not usa_sc:
        return {}
    d = r[r.id_nucleo.notna()].copy()
    g = d.groupby("id_nucleo")
    d["amp"] = g["uid"].transform("size")
    rp = d[d.ruolo.isin(["R", "P"])]
    pv = rp.pivot_table(index="id_nucleo", columns="ruolo",
                        values=N.STATO_COL, aggfunc="first")
    for c in ("R", "P"):
        if c not in pv.columns:
            pv[c] = np.nan
    coppia = (pv.R == CONIUGATO) & (pv.P == CONIUGATO)
    d["in_coppia"] = d.id_nucleo.map(coppia).fillna(False)
    con = d[d[N.STATO_COL] == CONIUGATO].copy()
    con["coerente"] = ((con.ruolo.isin(["R", "P"]) & con.in_coppia)
                       | (con.amp == 1))
    per_ruolo = con.groupby("ruolo").agg(n=("coerente", "size"),
                                         coerenti=("coerente", "sum"))
    return {
        "coniugati": int(len(con)),
        "unipersonali": float((con.amp == 1).mean()),
        "incoerenti": float(1 - con.coerente.mean()),
        "per_ruolo": {k: {"n": int(v.n), "incoerenti": float(1 - v.coerenti / v.n)}
                      for k, v in per_ruolo.iterrows()},
    }


def lavora(comune, rep_path, out_dir, anno, seme_base, verboso=True):
    pop_path = trova_popolazione(comune, anno)
    if not pop_path:
        print(f"[{comune}] popolazione non trovata")
        return None
    t0 = time.time()
    rep = N.carica_repertorio(rep_path)
    sez = pd.read_csv(G.path_sezioni(comune))
    sez["k"] = sez.SEZ21_ID.astype("Int64").astype(str)
    per_sez = sez.set_index("k").to_dict("index")

    pop = pd.read_csv(pop_path, low_memory=False)
    if "uid" not in pop.columns or "sezione" not in pop.columns:
        print(f"[{comune}] colonne `uid`/`sezione` assenti")
        return None
    pop["k"] = pop["sezione"].astype(str)
    usa_sc = N.STATO_COL in pop.columns

    seme = seme_base + int(comune)
    rng = np.random.default_rng(seme)
    tieni = ["uid"] + ([N.STATO_COL] if usa_sc else [])

    tot, casi, rip = Counter(), Counter(), Counter()
    div_g, div_p, pezzi = [], [], []
    for s, ind in pop.groupby("k", sort=False):
        riga = per_sez.get(s)
        if riga is None:
            tot["sezioni_non_agganciate"] += 1
            tot["individui_senza_sezione"] += len(ind)
            pezzi.append(ind[tieni].assign(id_nucleo=pd.NA, ruolo=pd.NA))
            continue
        if s.endswith("8888888"):
            # Sezione fittizia delle convivenze (enrich): istituti, non
            # famiglie. Niente assemblaggio: id_nucleo vuoto per design.
            # Senza questo salto, il matching O(|sez|^2) sulla convivenza
            # di Milano (10.038 individui) costava ore per un risultato
            # scartato per definizione (collaudo 25/8). Nota: il salto
            # non consuma rng, quindi cambia la sequenza per le sezioni
            # successive rispetto alle corse precedenti la patch.
            tot["individui"] += len(ind)
            tot["non_collocati"] += len(ind)
            tot["convivenze_saltate"] += len(ind)
            pezzi.append(ind[tieni].assign(id_nucleo=pd.NA, ruolo=pd.NA))
            continue
        v, d = N.vincoli_da_sezione(riga, len(ind), rep, rng)
        res, dd = N.assembla(ind, v, rep, rng, prefisso=f"{s}-")
        pezzi.append(ind[tieni].join(res))
        tot["individui"] += len(ind)
        for k in ("nuclei", "perfetti", "non_collocati", "coppie",
                  "coppie_omogenee"):
            tot[k] += dd[k]
        tot["convivenza_dichiarata"] += d["convivenza"]
        casi[d["caso"]] += 1
        rip.update(dd["ripieghi"])
        div_g += dd["divari"].get("generazionale", [])
        div_p += dd["divari"].get("partner", [])

    r = pd.concat(pezzi)
    if len(r) != len(pop):
        sys.exit(f"[{comune}] righe in uscita {len(r)} != {len(pop)}: "
                 "il join a valle sarebbe rotto")

    os.makedirs(out_dir, exist_ok=True)
    fcsv = os.path.join(out_dir, f"nuclei_{comune}.csv")
    r[["uid", "id_nucleo", "ruolo"]].to_csv(fcsv, index=False)

    diag = {
        "comune": comune,
        "generato": time.strftime("%Y-%m-%d %H:%M"),
        "popolazione": os.path.basename(pop_path),
        "repertorio": os.path.basename(rep_path),
        "repertorio_meta": rep.meta,
        "seme": seme,
        "individui": int(tot["individui"]),
        "nuclei": int(tot["nuclei"]),
        "senza_ripiego": float(tot["perfetti"] / max(tot["nuclei"], 1)),
        "non_collocati": int(tot["non_collocati"]),
        "quota_non_collocati": float(tot["non_collocati"]
                                     / max(tot["individui"], 1)),
        "convivenza_dichiarata": int(tot["convivenza_dichiarata"]),
        "sezioni_non_agganciate": int(tot["sezioni_non_agganciate"]),
        "coppie": int(tot["coppie"]),
        "coppie_omogenee": float(tot["coppie_omogenee"]
                                 / max(tot["coppie"], 1)),
        "casi_vincoli": dict(casi),
        "ripieghi": dict(rip),
        "divari": {
            "generazionale_mediana": (float(np.median(div_g)) if div_g else None),
            "generazionale_fuori_limiti": (
                float(np.mean((np.array(div_g) < rep.gen_min)
                              | (np.array(div_g) > rep.gen_max)))
                if div_g else None),
            "partner_p05": (float(np.percentile(div_p, 5)) if div_p else None),
            "partner_p95": (float(np.percentile(div_p, 95)) if div_p else None),
        },
        "stato_civile": incoerenza_per_ruolo(r, usa_sc),
        "convenzionali": rep.conv,
    }
    fjson = os.path.join(out_dir, f"nuclei_{comune}_diagnostica.json")
    with open(fjson, "w", encoding="utf-8") as f:
        json.dump(diag, f, indent=1, ensure_ascii=False)

    if verboso:
        sc = diag["stato_civile"]
        print(f"[{comune}] {tot['individui']:,} individui · "
              f"{tot['nuclei']:,} nuclei · senza ripiego "
              f"{diag['senza_ripiego']:.1%} · non collocati "
              f"{diag['quota_non_collocati']:.2%}".replace(",", "."))
        print(f"          coppie omogenee {diag['coppie_omogenee']:.1%}"
              + (f" · coniugati incoerenti {sc['incoerenti']:.1%}"
                 if sc else " · stato_civile assente")
              + f" · {time.time() - t0:.0f}s")
        print(f"          -> {fcsv}")
    return diag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comuni", nargs="*")
    ap.add_argument("--tutti", action="store_true")
    ap.add_argument("--anno", type=int)
    ap.add_argument("--repertorio", default=REP_DEFAULT)
    ap.add_argument("--out-dir", default="data/nuclei")
    ap.add_argument("--seme", type=int, default=SEME_BASE)
    a = ap.parse_args()

    comuni = a.comuni or (elenco_comuni() if a.tutti else None)
    if not comuni:
        sys.exit("passare i codici ISTAT, oppure --tutti")
    if not os.path.exists(a.repertorio):
        sys.exit(f"repertorio non trovato: {a.repertorio}\n"
                 "generarlo con gsp.nucleo.costruisci_repertorio")

    esiti = [d for c in comuni
             if (d := lavora(c, a.repertorio, a.out_dir, a.anno, a.seme))]
    if len(esiti) > 1:
        print("\n" + "=" * 66)
        print(f"   {'comune':10s} {'individui':>10s} {'nuclei':>9s} "
              f"{'omogenee':>9s} {'incoer.':>8s} {'non coll.':>10s}")
        for d in esiti:
            sc = d["stato_civile"]
            inc = f"{sc['incoerenti']:7.1%}" if sc else "    n/d"
            print(f"   {d['comune']:10s} {d['individui']:10,} "
                  .replace(",", ".")
                  + f"{d['nuclei']:9,} ".replace(",", ".")
                  + f"{d['coppie_omogenee']:8.1%} {inc} "
                    f"{d['quota_non_collocati']:9.2%}")


if __name__ == "__main__":
    main()
