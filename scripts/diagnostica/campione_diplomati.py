"""campione_diplomati.py — diagnostica per l'esperimento sui priors universitari.

Estrae dai comuni i diplomati giovani, li incrocia con l'anello 4 e
misura tutto cio' che serve a decidere il disegno sperimentale PRIMA di
scrivere un prompt:

  1. quota di giovani con ruolo F in un nucleo con almeno un genitore
     (regola sicura: SOLO F conta come «vive coi genitori»; A include
     nipoti e cognati, errore per difetto ~1%)
  2. plausibilita' dei divari d'eta' genitore-figlio (fuori 18-50 = bug)
  3. distribuzione del tipo di diploma (liceo/tecnico/professionale)
     via gsp.istruzione, estrazione deterministica per uid
  4. quota `studente` per tipo di diploma + TVD contro il marginale con
     pavimento a permutazione (attesa: piatta per costruzione)
  5. crosstab delle celle diploma3 x istruzione-genitori x sesso x
     background, con i conteggi per il campionamento stratificato

    python scripts/diagnostica/campione_diplomati.py 034027
    python scripts/diagnostica/campione_diplomati.py 034027 037006 017029
    python scripts/diagnostica/campione_diplomati.py --tutti

COSA SCRIVE (in --out-dir, default data/diagnostica):
  campione_diplomati_{comune}.csv    una riga per giovane, variabili
                                     derivate incluse: pronto per
                                     l'estrazione stratificata
  campione_diplomati_{comune}.json   i numeri di sanita'
La popolazione e i file dei nuclei sono aperti in sola lettura.

AVVERTENZE COSTITUTIVE (da ripetere ovunque i numeri finiscano):
  · titolo_dettaglio e' condizionato su istruzione x sesso x coorte, NON
    su condizione: P(diploma3 | studente) DEVE uscire piatta. La TVD del
    punto 4 lo certifica invece di affermarlo.
  · l'istruzione dei genitori e' indipendente da quella del figlio per
    costruzione dell'assemblaggio: la cella esiste e si campiona, ma non
    rappresenta una regolarita' della popolazione.
"""

import argparse
import glob
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from gsp import common as G          # noqa: E402
import gsp.istruzione as I           # noqa: E402

SEME_TITOLO = 20260820

# ---------------------------------------------------------------- percorsi

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

# ------------------------------------------------------- colonne difensive

def _prima_colonna(df, candidate, obbligatoria=None):
    for c in candidate:
        if c in df.columns:
            return c
    if obbligatoria:
        sys.exit(f"colonna {obbligatoria} non trovata; presenti: "
                 f"{list(df.columns)}")
    return None


def colonna_eta_esatta(df):
    """Cerca un'eta' in anni. Ritorna (nome, e' esatta?)."""
    for c in ("eta_anni", "eta_esatta", "anni", "age"):
        if c in df.columns and pd.api.types.is_numeric_dtype(df[c]):
            return c, True
    if "eta" in df.columns and pd.api.types.is_numeric_dtype(df["eta"]):
        return "eta", True
    return _prima_colonna(df, ["eta", "eta_bin"], "eta"), False

# --------------------------------------------------- titolo di studio

def _normalizza_repertorio(rep):
    """dict {nome: peso} | iterabile di coppie | DataFrame -> (nomi, pesi)."""
    if isinstance(rep, dict):
        coppie = list(rep.items())
    elif isinstance(rep, pd.DataFrame):
        col_p = [c for c in rep.columns
                 if pd.api.types.is_numeric_dtype(rep[c])][-1]
        col_n = [c for c in rep.columns if c != col_p][0]
        coppie = list(zip(rep[col_n], rep[col_p]))
    else:
        coppie = [tuple(x)[:2] for x in rep]
    nomi = [str(n) for n, _ in coppie]
    pesi = np.array([float(p) for _, p in coppie], dtype=float)
    s = pesi.sum()
    if not (s > 0):
        return None, None
    return nomi, pesi / s


def estrai_titolo(uid, nomi, cum, seme):
    """Deterministico da uid, schema gsp.nomi: blake2b(SEME|canale|id)."""
    h = hashlib.blake2b(f"{seme}|titolo|{uid}".encode(),
                        digest_size=8).digest()
    u = int.from_bytes(h, "big") / 2**64
    return nomi[int(np.searchsorted(cum, u, side="right"))]


# priorita': professionale > tecnico > liceo. Le foglie della maturita'
# sono 32; cio' che non combacia finisce in `altro` ED e' STAMPATO.
def collassa_diploma(nome):
    n = nome.lower()
        # filiera artistica: l'Emilia etichetta «istruzione di II grado
    # artistica», la Lombardia «liceo artistico» — stessa filiera sotto
    # due ordinamenti, che la mappa v1 spediva in due classi diverse
    # creando un artefatto di ~1-1,5 punti nei confronti fra comuni
    # (misurato 21/8/2026, colonna `altro` della V2). Tutta in `altro`,
    # per simmetria con istituto e maestro d'arte, ed esclusa dal
    # disegno come il resto della classe.
    if "artist" in n or "d'arte" in n:
        return "altro"
    if "professionale" in n or "alberghier" in n:
        return "professionale"
    if ("tecnico" in n or "geometri" in n or "ragion" in n
            or "perit" in n or "agrari" in n or "nautic" in n
            or "aeronautic" in n or "commercial" in n):
        return "tecnico"
    if ("liceo" in n or "classic" in n or "scientific" in n
            or "linguistic" in n or "magistral" in n
            or "scienze umane" in n):
        return "liceo"
    return "altro"          # istituti d'arte, conservatori, residuali


def collassa_istruzione_genitore(v):
    n = str(v).lower()
    if "laurea" in n or "post" in n or "dottor" in n or "terziar" in n:
        return "laurea+"
    if "diploma" in n or "matur" in n or "second" in n:
        return "diploma"
    return "bassa"          # nessun_titolo, elementare, media

# ------------------------------------------------------------------- TVD

def tvd(p, q):
    return 0.5 * np.abs(p - q).sum()


def tvd_con_pavimento(df, col_gruppo, valore, col_var, rng, n_perm=200):
    """TVD(P(var|gruppo=valore), P(var)) e pavimento per permutazione
    delle etichette del gruppo. Stesso principio del MRE floor."""
    mask = (df[col_gruppo] == valore).to_numpy()
    if mask.sum() < 30:
        return None
    livelli = sorted(df[col_var].unique())
    marg = df[col_var].value_counts(normalize=True).reindex(
        livelli, fill_value=0).to_numpy()

    def _cond(m):
        return (df.loc[m, col_var].value_counts(normalize=True)
                .reindex(livelli, fill_value=0).to_numpy())

    oss = tvd(_cond(mask), marg)
    pav = float(np.median([tvd(_cond(rng.permutation(mask)), marg)
                           for _ in range(n_perm)]))
    return {"osservata": round(oss, 4), "pavimento": round(pav, 4),
            "netto": round(oss - pav, 4), "n": int(mask.sum())}

# ------------------------------------------------------------------ core

def lavora(comune, anno, eta_min, eta_max, out_dir, seme, verboso=True):
    pop_path = trova_popolazione(comune, anno)
    if not pop_path:
        print(f"-- {comune}: popolazione non trovata, salto")
        return None
    nuc_path = os.path.join("data/nuclei", f"nuclei_{comune}.csv")
    if not os.path.exists(nuc_path):
        print(f"-- {comune}: {nuc_path} assente (assign_nucleo non "
              "girato?), salto")
        return None

    pop = pd.read_csv(pop_path, dtype={"uid": str}, low_memory=False)
    nuc = pd.read_csv(nuc_path, dtype=str).fillna({"id_nucleo": ""})

    c_uid = _prima_colonna(pop, ["uid", "id"], "uid")
    pop = pop.rename(columns={c_uid: "uid"})
    pop["uid"] = pop["uid"].astype(str)

    c_eta, eta_esatta = colonna_eta_esatta(pop)
    c_bkg = _prima_colonna(pop, ["background", "cittadinanza",
                                 "background_migratorio"])
    c_cond = _prima_colonna(pop, ["condizione", "condizione_prof"],
                            "condizione")
    c_istr = _prima_colonna(pop, ["istruzione"], "istruzione")
    c_sesso = _prima_colonna(pop, ["sesso"], "sesso")

    df = pop.merge(nuc[["uid", "id_nucleo", "ruolo"]], on="uid", how="left")
    perse = df["ruolo"].isna().sum()
    df["ruolo"] = df["ruolo"].fillna("?")
    df["id_nucleo"] = df["id_nucleo"].fillna("")

      # ------- scambiabilita' di eta_anni nel bin — v2: contro il
    # marginale EMPIRICO con pavimento a permutazione. La v1 confrontava
    # col piatto: misurava la forma della marginale, non la selezione.
    b24 = df[df["eta"].astype(str) == "15-24"]
    b24 = b24[b24["eta_anni"].notna()]
    val = b24["eta_anni"].astype(float).to_numpy()
    livelli = np.unique(val)
    marg = np.array([(val == l).mean() for l in livelli])
    rng_u = np.random.default_rng(seme + 1)

    def _tvd_da_marg(m):
        q = np.array([(val[m] == l).mean() for l in livelli])
        return 0.5 * np.abs(q - marg).sum()

    unif = {"marginale": {int(l): round(float((val == l).mean()), 4)
                          for l in livelli}}
    for nome, col in [("istruzione", c_istr), ("condizione", c_cond),
                      ("ruolo", "ruolo")]:
        gr = b24[col].astype(str).to_numpy()
        netti = {}
        for gv in np.unique(gr):
            m = gr == gv
            if m.sum() < 200:
                continue
            oss = _tvd_da_marg(m)
            pav = float(np.median([_tvd_da_marg(rng_u.permutation(m))
                                   for _ in range(100)]))
            netti[gv] = round(oss - pav, 4)
        unif[nome] = netti

    # ------- filtro: diplomati nella finestra d'eta'
    dipl = df[c_istr].astype(str).str.contains("diploma", case=False)
    if eta_esatta:
        giov = df[dipl & df[c_eta].between(eta_min, eta_max)].copy()
        nota_eta = f"eta' esatta [{eta_min},{eta_max}] da `{c_eta}`"
    else:
        giov = df[dipl & (df[c_eta].astype(str) == "15-24")].copy()
        nota_eta = "SOLO BIN 15-24: eta' esatta assente, finestra larga"

    if len(giov) == 0:
        print(f"-- {comune}: nessun diplomato nella finestra ({nota_eta})")
        return None

    # ------- genitori: F -> {R,P}; R -> {G}; P -> {G} (ambiguo, flag)
    fam = df[df["id_nucleo"] != ""]
    per_nucleo = fam.groupby("id_nucleo")
    ruoli_n = per_nucleo["ruolo"].agg(lambda s: "".join(sorted(s)))
    istr_rp = (fam[fam["ruolo"].isin(["R", "P"])]
               .groupby("id_nucleo")[c_istr].agg(list))
    istr_g = (fam[fam["ruolo"] == "G"]
              .groupby("id_nucleo")[c_istr].agg(list))
    if eta_esatta:
        eta_rp = (fam[fam["ruolo"].isin(["R", "P"])]
                  .groupby("id_nucleo")[c_eta].agg(list))
        eta_g = (fam[fam["ruolo"] == "G"]
                 .groupby("id_nucleo")[c_eta].agg(list))

    def _genitori(r):
        if not r["id_nucleo"]:
            return [], None
        if r["ruolo"] == "F":
            return istr_rp.get(r["id_nucleo"], []), \
                   (eta_rp.get(r["id_nucleo"], []) if eta_esatta else None)
        if r["ruolo"] in ("R", "P"):
            return istr_g.get(r["id_nucleo"], []), \
                   (eta_g.get(r["id_nucleo"], []) if eta_esatta else None)
        return [], None

    gen = giov.apply(_genitori, axis=1)
    giov["n_genitori"] = [len(g[0]) for g in gen]
    giov["gen3"] = [
        (max((collassa_istruzione_genitore(x) for x in g[0]),
             key=["bassa", "diploma", "laurea+"].index)
         if g[0] else "assenti")
        for g in gen]

    divari, fuori = [], 0
    if eta_esatta:
        for (_, r), g in zip(giov.iterrows(), gen):
            if g[1]:
                for e in g[1]:
                    d = float(e) - float(r[c_eta])
                    divari.append(d)
                    fuori += not (18 <= d <= 50)

    # ------- tipo di diploma via gsp.istruzione
       # STESSA derivazione della produzione: titolo_agente, canale
    # "titolo", regione dal comune. L'eta' esatta seleziona CHI (filtro
    # 19-20), il bin condiziona COSA: e' l'unica risoluzione che il dato
    # possiede, dato eta_anni uniforme nel bin.
    non_mappati = {}

    def _titolo(r):
        reso, sp = I.titolo_agente(str(r["uid"]), "diploma",
                                   sesso=r[c_sesso], eta="15-24",
                                   comune=comune, spiega=True)
        return sp["codice"], sp["grezzo"], reso

    tre = giov.apply(_titolo, axis=1, result_type="expand")
    giov["titolo_cod"] = tre[0]
    giov["titolo_grezzo"] = tre[1]
    giov["titolo_dettaglio"] = tre[2]
    # il collasso aggancia l'etichetta CENSUARIA, stabile rispetto a
    # ogni futura cosmesi di titolo_leggibile
    giov["diploma3"] = giov["titolo_grezzo"].map(collassa_diploma)
    
    for t in giov.loc[giov["diploma3"] == "altro", "titolo_dettaglio"]:
        non_mappati[t] = non_mappati.get(t, 0) + 1

    # ------- misure
    rng = np.random.default_rng(seme + int(comune))
    q_ruoli = giov["ruolo"].value_counts(normalize=True).to_dict()
    f_con_gen = giov[(giov["ruolo"] == "F") & (giov["n_genitori"] > 0)]
    studente = giov[c_cond].astype(str).str.contains("stud", case=False)
    giov["_studente"] = np.where(studente, "studente", "altro")
    q_stud_dipl = (giov.groupby("diploma3")["_studente"]
                   .apply(lambda s: (s == "studente").mean()).to_dict())
    tvd_stud = tvd_con_pavimento(giov, "_studente", "studente",
                                 "diploma3", rng)

    celle = (giov.groupby(["diploma3", "gen3", c_sesso] +
                          ([c_bkg] if c_bkg else []))
             .size().rename("n").reset_index())

    # ------- uscite
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"campione_diplomati_{comune}")
    giov.drop(columns=["_studente"]).to_csv(base + ".csv", index=False)
    celle.to_csv(base + "_celle.csv", index=False)

    d = {
        "comune": comune, "popolazione": pop_path, "nota_eta": nota_eta,
        "scambiabilita_eta_anni": unif,
        "seme_titolo": seme, "n_giovani": int(len(giov)),
        "righe_senza_nucleo_nel_join": int(perse),
        "quota_ruoli": {k: round(v, 4) for k, v in q_ruoli.items()},
        "quota_F_con_genitore": round(len(f_con_gen) / len(giov), 4),
        "gen3": giov["gen3"].value_counts(normalize=True)
                .round(4).to_dict(),
        "divari_eta": ({
            "n": len(divari),
            "mediana": float(np.median(divari)),
            "q10": float(np.quantile(divari, .1)),
            "q90": float(np.quantile(divari, .9)),
            "fuori_18_50": int(fuori),
        } if divari else "eta' esatta assente"),
        "diploma3": giov["diploma3"].value_counts(normalize=True)
                    .round(4).to_dict(),
        "foglie_non_mappate": non_mappati,
        "quota_studente_per_diploma3":
            {k: round(v, 4) for k, v in q_stud_dipl.items()},
        "tvd_diploma3_studente_vs_marginale": tvd_stud,
        "n_celle": int(len(celle)),
        "celle_con_n_ge_10": int((celle["n"] >= 10).sum()),
    }
    with open(base + ".json", "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    if verboso:
        print(f"\n== {comune}  ({nota_eta})")
        print("   scambiabilita' eta_anni (netto max per condizionante): " +
              "  ".join(f"{k}={max(v.values()):+.4f}" if v else f"{k}=n/d"
                        for k, v in unif.items() if k != "marginale"))
        print(f"   marginale eta_anni nel bin: {unif['marginale']}")
        print(f"   giovani diplomati: {len(giov):,}".replace(",", "."))
        print(f"   ruoli: " + "  ".join(
            f"{k}={v:.1%}" for k, v in sorted(q_ruoli.items())))
        print(f"   F con >=1 genitore: {d['quota_F_con_genitore']:.1%}")
        if divari:
            dv = d["divari_eta"]
            print(f"   divario gen-figlio: mediana {dv['mediana']:.0f}, "
                  f"q10-q90 [{dv['q10']:.0f},{dv['q90']:.0f}], "
                  f"fuori 18-50: {dv['fuori_18_50']}")
        print(f"   diploma3: " + "  ".join(
            f"{k}={v:.1%}" for k, v in d["diploma3"].items()))
        if non_mappati:
            print(f"   !! foglie in `altro`: {non_mappati}")
        print(f"   quota studente per diploma3: " + "  ".join(
            f"{k}={v:.1%}" for k, v in q_stud_dipl.items()))
        if tvd_stud:
            print(f"   TVD(diploma3|studente vs marg): "
                  f"oss {tvd_stud['osservata']}, pav "
                  f"{tvd_stud['pavimento']}, netto {tvd_stud['netto']}"
                  "   <- atteso ~0 per costruzione")
        print(f"   celle: {d['n_celle']} totali, "
              f"{d['celle_con_n_ge_10']} con n>=10")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comuni", nargs="*")
    ap.add_argument("--tutti", action="store_true")
    ap.add_argument("--anno", type=int)
    ap.add_argument("--eta", nargs=2, type=int, default=[19, 20],
                    metavar=("MIN", "MAX"))
    ap.add_argument("--out-dir", default="data/diagnostica")
    ap.add_argument("--seme", type=int, default=SEME_TITOLO)
    a = ap.parse_args()

    comuni = a.comuni or (elenco_comuni() if a.tutti else None)
    if not comuni:
        sys.exit("passare i codici ISTAT, oppure --tutti")

    esiti = [d for c in comuni
             if (d := lavora(c, a.anno, a.eta[0], a.eta[1],
                             a.out_dir, a.seme))]
    if len(esiti) > 1:
        print("\n" + "=" * 72)
        print(f"   {'comune':10s} {'giovani':>8s} {'F+gen':>7s} "
              f"{'liceo':>7s} {'tecnico':>8s} {'prof.':>7s} "
              f"{'stud.tot':>9s} {'celle>=10':>9s}")
        for d in esiti:
            dp = d["diploma3"]
            st = sum(v * dp.get(k, 0) for k, v in
                     d["quota_studente_per_diploma3"].items())
            print(f"   {d['comune']:10s} {d['n_giovani']:8,}"
                  .replace(",", ".")
                  + f" {d['quota_F_con_genitore']:6.1%}"
                  f" {dp.get('liceo', 0):6.1%} {dp.get('tecnico', 0):7.1%}"
                  f" {dp.get('professionale', 0):6.1%}"
                  f" {st:8.1%} {d['celle_con_n_ge_10']:9d}")


if __name__ == "__main__":
    main()
