#!/usr/bin/env python3
"""campiona_diplomati.py — il campione dell'esperimento sui priors. Livello A.

    python scripts/narrativa/campiona_diplomati.py
    python scripts/narrativa/campiona_diplomati.py --comuni 034027 017029
    python scripts/narrativa/campiona_diplomati.py --n-cella 12 --seed 0

COSA FA. Dai CSV di `campione_diplomati.py` (la diagnostica) estrae
`n_cella` agenti per ciascuna delle 36 celle diploma3 × gen3 × sesso ×
background, pooled sui comuni con allocazione proporzionale, e
materializza cio' che serve al prompt e che il CSV non porta:

  · nome e cognome              `gsp.nomi.nome_agente` (canale nome)
  · titolo alla foglia          gia' nel CSV (titolo_dettaglio, da
                                titolo_agente con comune= — post patch)
  · titolo e sesso dei GENITORI rijoin su nuclei + popolazione: serve
                                «tua madre ha X, tuo padre ha Y», non il
                                massimo collassato della diagnostica
  · numero di FRATELLI          gli altri F dello stesso nucleo

IL CAMPIONE E' IL LIVELLO A (registro SIVE §12): si riproduce
esattamente da `(comuni, n_cella, seed)` e deve essere identico a ogni
esecuzione. Percio': candidati ordinati per uid PRIMA dell'estrazione,
rng seminato una volta, allocazione per comune col resto maggiore.
Lo script rifiuta di sovrascrivere senza --forza.

COSA NON ENTRA nel record dell'agente, di proposito:
  · `condizione` propria — e' l'ESITO che l'esperimento chiede;
  · settore e posizione — ramo debole della riponderazione;
  · le variabili AVQ — nessun asse dell'esperimento le usa.
"""

import argparse
import glob
import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from gsp import common as G          # noqa: E402
from gsp import nomi as N            # noqa: E402

D3 = ["liceo", "tecnico", "professionale"]      # `altro` escluso, dichiarato
G3 = ["bassa", "diploma", "laurea+"]            # `assenti` esclusa (vuota)

DIR_DIAG = "data/diagnostica"
DIR_NUCLEI = "data/nuclei"


def trova_popolazione(comune, anno=None):
    pat = (f"data/comuni/{comune}/constraints_{anno}/popolazione_K*_avq_full.csv"
           if anno else
           f"data/comuni/{comune}/constraints_*/popolazione_K*_avq_full.csv")
    c = [p for p in sorted(glob.glob(pat)) if "backup" not in p]
    return c[-1] if c else None


def col_background(df):
    for c in ("background", "cittadinanza", "background_migratorio"):
        if c in df.columns:
            return c
    return None


def bkg2(v):
    n = str(v).lower()
    return "ita" if ("ital" in n or n == "ita") else "straniero"


# le colonne della popolazione che servono all'identita' dell'agente:
# le STESSE che _proietta passa a nome_agente, piu' zona e cittadinanza
# per il prompt. Prese dalla popolazione e non dalla diagnostica, cosi'
# il nome coincide con la scheda per costruzione.
COL_IDENTITA = ["sesso", "eta", "eta_anni", "background",
                "origine_genitori", "paese", "cittadinanza", "zona"]


def carica_comune(comune, anno):
    """Diagnostica + popolazione + nuclei. Ritorna anche la vista della
    popolazione indicizzata per uid (solo le colonne d'identita': Bologna
    ha 400k righe e la memoria non e' gratis) e la mappa codice->nome
    delle zone dal registro."""
    p_diag = os.path.join(DIR_DIAG, f"campione_diplomati_{comune}.csv")
    p_nuc = os.path.join(DIR_NUCLEI, f"nuclei_{comune}.csv")
    p_pop = trova_popolazione(comune, anno)
    for p, che in ((p_diag, "diagnostica"), (p_nuc, "nuclei"),
                   (p_pop, "popolazione")):
        if not p or not os.path.exists(p):
            sys.exit(f"{comune}: {che} non trovata ({p})")

    diag = pd.read_csv(p_diag, dtype=str)
    nuc = pd.read_csv(p_nuc, dtype=str).fillna({"id_nucleo": ""})
    pop = pd.read_csv(p_pop, dtype={"uid": str}, low_memory=False)
    pop["uid"] = pop["uid"].astype(str)

    memb = nuc[nuc["id_nucleo"] != ""].merge(
        pop[["uid", "sesso", "istruzione"]
            + (["eta_anni"] if "eta_anni" in pop.columns else [])],
        on="uid", how="left")
    per_nucleo = {k: v for k, v in memb.groupby("id_nucleo")}

    presenti = [c for c in COL_IDENTITA if c in pop.columns]
    pop_uid = pop.set_index("uid")[presenti]

    try:
        zona_nomi = dict(G.zona_nomi(comune))
    except Exception:                                    # noqa: BLE001
        zona_nomi = {}
    return diag, per_nucleo, pop_uid, zona_nomi


def genitori_e_fratelli(riga, per_nucleo):
    """(genitori, n_fratelli). Genitori = membri R/P del nucleo di un F.
    L'assemblaggio non produce coppie dello stesso sesso, quindi
    madre/padre si distinguono dal sesso; con un genitore solo si rende
    quello che c'e'."""
    nid = riga.get("id_nucleo") or ""
    if not nid or nid not in per_nucleo:
        return [], 0
    m = per_nucleo[nid]
    gen = m[m["ruolo"].isin(["R", "P"])]
    frat = m[(m["ruolo"] == "F") & (m["uid"] != riga["uid"])]
    out = [{"sesso": r["sesso"], "istruzione": r["istruzione"]}
           for _, r in gen.iterrows()]
    return out, int(len(frat))

def _json_default(o):
    """Gli scalari numpy che pandas semina nei record."""
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(f"non serializzabile: {type(o).__name__}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--comuni", nargs="*", default=None,
                    help="default: tutti i CSV presenti in data/diagnostica")
    ap.add_argument("--anno", type=int)
    ap.add_argument("--n-cella", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None,
                    help="default: dati/agenti/agenti_scelta_n{N}_s{seed}.json")
    ap.add_argument("--forza", action="store_true")
    a = ap.parse_args()

    import re
    comuni = a.comuni or sorted(
        re.sub(r".*campione_diplomati_(\d+)\.csv", r"\1", p)
        for p in glob.glob(os.path.join(DIR_DIAG, "campione_diplomati_*.csv"))
        if "_celle" not in p)
    if not comuni:
        sys.exit("nessuna diagnostica trovata: girare campione_diplomati.py")

    print(f"comuni: {', '.join(comuni)} · n/cella {a.n_cella} · seed {a.seed}")
    rng = np.random.default_rng(a.seed)

    # ------- candidati: solo F, celle di disegno, ordinati per uid
    pezzi, contesti = [], {}
    for c in comuni:
        diag, per_nucleo, pop_uid, zn = carica_comune(c, a.anno)
        f = diag[diag["ruolo"] == "F"].copy()
        cb = col_background(f)
        f["b2"] = f[cb].map(bkg2) if cb else "n/d"
        f = f[f["diploma3"].isin(D3) & f["gen3"].isin(G3)]
        f["comune"] = c
        pezzi.append(f)
        contesti[c] = {"nuclei": per_nucleo, "pop": pop_uid, "zone": zn}
        print(f"  {c}: {len(f)} candidati")
    cand = (pd.concat(pezzi)
            .sort_values("uid")            # ordine stabile: livello A
            .reset_index(drop=True))
    cand["cella"] = (cand.diploma3 + "\u00b7" + cand.gen3 + "\u00b7"
                     + cand.sesso + "\u00b7" + cand.b2)

    # ------- estrazione: per cella, proporzionale ai comuni (resto
    # maggiore — qui le sue condizioni valgono: quote diverse per cella,
    # e l'eventuale distorsione di spareggio agisce UNA volta, non su
    # migliaia di blocchi)
    agenti = []
    for cella, gruppo in cand.groupby("cella"):
        n_tot = min(a.n_cella, len(gruppo))
        per_com = gruppo.groupby("comune").size().reindex(comuni,
                                                          fill_value=0)
        conta = G.largest_remainder(n_tot, per_com.to_numpy())
        # se un comune ha meno candidati dell'allocato, il resto va agli
        # altri: si rialloca il mancante sul residuo disponibile
        conta = np.minimum(conta, per_com.to_numpy())
        while conta.sum() < n_tot:
            resto = per_com.to_numpy() - conta
            i = int(np.argmax(resto))
            if resto[i] <= 0:
                break
            conta[i] += 1
        for com, k in zip(comuni, conta):
            if k == 0:
                continue
            g = gruppo[gruppo.comune == com]
            scelti = g.iloc[rng.choice(len(g), size=int(k), replace=False)]
            agenti.append(scelti)
    camp = pd.concat(agenti).sort_values("uid").reset_index(drop=True)
    print(f"\nestratti {len(camp)} agenti su "
          f"{cand['cella'].nunique()} celle")

        # ------- materializzazione: identita' dalla POPOLAZIONE, non dalla
    # diagnostica — il collaudo dei profili ha mostrato nomi incoerenti
    # con cittadinanza e origine quando gli input venivano dal CSV
    # ridotto (v. nota, correzione del 20/8)
    fuori = []
    for _, r in camp.iterrows():
        ctx = contesti[r["comune"]]
        try:
            pr = ctx["pop"].loc[r["uid"]]
        except KeyError:
            sys.exit(f"uid {r['uid']} non nella popolazione di "
                     f"{r['comune']}: diagnostica e popolazione non "
                     "vengono dalla stessa corsa?")
        gen, n_frat = genitori_e_fratelli(r, ctx["nuclei"])
        nome, cognome = N.nome_agente(
            r["uid"], sesso=pr.get("sesso"), eta=pr.get("eta"),
            background=pr.get("background"),
            origine_genitori=pr.get("origine_genitori"),
            paese=pr.get("paese"))
        zona = pr.get("zona") or r.get("zona")
        grezzo = str(r.get("titolo_grezzo", "")).lower()
        fuori.append({
            "uid": r["uid"], "comune": r["comune"], "cella": r["cella"],
            "diploma3": r["diploma3"], "gen3": r["gen3"],
            "nome": nome, "cognome": cognome,
            "sesso": pr.get("sesso") or r["sesso"],
            "eta_anni": int(float(pr.get("eta_anni") or r["eta_anni"])),
            "zona_cod": zona,
            "quartiere": ctx["zone"].get(str(zona), zona),
            "cittadinanza": pr.get("cittadinanza"),
            "background": pr.get("background"),
            "origine_genitori": pr.get("origine_genitori"),
            "paese": pr.get("paese"),
            "titolo_dettaglio": r["titolo_dettaglio"],
            # la categoria censuaria `diploma` include le QUALIFICHE
            # triennali, che non danno accesso all'universita'. Il flag
            # permette l'analisi con e senza; il confronto MUR (solo
            # maturita') lo richiede. Scoperto al collaudo dei profili.
            "qualifica": ("qualifica" in grezzo or "idoneita" in grezzo
                          or "idoneità" in grezzo),
            "genitori": gen, "fratelli": n_frat,
        })

    out = a.out or f"dati/agenti/agenti_scelta_n{len(fuori)}_s{a.seed}.json"
    if os.path.exists(out) and not a.forza:
        sys.exit(f"{out} esiste gia'. Il campione e' il livello A: "
                 "sovrascriverlo invalida i confronti. --forza per farlo "
                 "comunque.")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    testo = json.dumps({"comuni": comuni, "n_cella": a.n_cella,
                        "seed": a.seed,
                        "generato": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "n": len(fuori),
                        "esclusioni": "diploma3=altro, gen3=assenti, "
                                      "ruoli!=F",
                        "agenti": fuori},
                       ensure_ascii=False, indent=1, default=_json_default)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(testo)
    print(f"[salvato] {out}")

    # riepilogo: le celle sotto quota, i genitori mancanti
    per_cella = pd.Series([x["cella"] for x in fuori]).value_counts()
    sotto = per_cella[per_cella < a.n_cella]
    if len(sotto):
        print(f"\ncelle sotto quota ({len(sotto)}):")
        for k, v in sotto.items():
            print(f"   {k:<40} {v}")
    senza_gen = [x["uid"] for x in fuori if not x["genitori"]]
    if senza_gen:
        print(f"\n!! {len(senza_gen)} agenti senza genitori nel rijoin — "
              "non doveva accadere (F al 100% con genitori): da guardare")


if __name__ == "__main__":
    main()
