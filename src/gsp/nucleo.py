"""gsp.nucleo — struttura familiare (anello 4).

Produce `id_nucleo` e `ruolo` da aggiungere alla popolazione sintetica.
NON modifica nessun altro attributo: rimosse le due colonne, la
popolazione torna identica byte a byte.

    costruisci_repertorio(anni, regioni)   dai microdati AVQ -> dict JSON
    carica_repertorio(path)                legge e valida
    vincoli_da_sezione(riga, n)            da PF3-PF8 -> nuclei per ampiezza
    assembla(individui, vincoli, rep, rng) -> (DataFrame, diagnostica)

`assembla` e' pura: nessun I/O, `rng` esplicito.


VERSIONE 2 — due modifiche, dopo il collaudo su Parma

(1) `stato_civile` E' UN VINCOLO, non piu' ignorato.

    La v1 usava sesso, eta' e ampiezza. Ma `stato_civile` e' vincolato
    dal MaxEnt in anello 1, e ignorarlo produce contraddizioni logiche
    dentro lo stesso individuo -- non rumore statistico. Misurato su
    Parma (`coerenza_stato_civile.py`):

        21.431 coniugati (26,6%) in un nucleo di 2+ senza nessun altro
        coniugato; solo il 29,6% delle coppie formato da due coniugati;
        rapporto 2*coppie_coniugate/coniugati con mediana 0,301 quando
        dovrebbe stare vicino a 1.

    Cioe' due coniugati su tre risultavano sposati con nessuno. La
    ragione: accoppiando a caso, la probabilita' che il partner sia
    anch'esso coniugato e' quella marginale (~0,4) -- l'assemblaggio
    trattava come indipendente la variabile che DEFINISCE il legame.

    Il 99,3% di «nuclei perfetti» della v1 non vedeva nulla di tutto
    questo: contava solo i ripieghi su eta' e sesso. La metrica misurava
    cio' che l'algoritmo ottimizza, non cio' che conta.

    Ora lo slot `P` richiede lo STESSO stato civile del riferimento, con
    ripiego contato. Nota sostanziale: NON si richiede che la coppia sia
    coniugata. Due `celibe_nubile` insieme sono una convivenza -- che nel
    repertorio e' `RELPAR` 03, distinto da 02 proprio per questo. Ed e'
    aritmeticamente necessario: ~42.000 coppie richiederebbero ~84.000
    coniugati e ce ne sono 80.639, di cui una parte vive sola.

    I `vedovo` sono esclusi dallo slot `P` (un vedovo risposato sarebbe
    `coniugato_unito`) e preferiti come riferimento di firme senza
    partner.

(2) `assembla` RESTITUISCE ANCHE IL RUOLO.

    La v1 dava solo `id_nucleo`, e il ruolo andava ricostruito dalla
    posizione -- approssimazione che sovrastima i partner nei nuclei con
    adulti coabitanti. Il ruolo serve comunque: per la scheda individuo,
    per le biografie, per qualunque validazione.

    ATTENZIONE: la firma cambia. Ora restituisce un DataFrame con
    `id_nucleo` e `ruolo`, non una Series.


COSA IL MODULO DICHIARA DI NON POTER FARE

  · il divario fra partner NON e' calibrato: le classi `ETAMi` sono
    larghe 5-10 anni e il divario reale (~3 anni) sta sotto la
    risoluzione dell'AVQ. `PARTNER_MAX_DIFF` e' CONVENZIONALE.
  · i limiti del genitore sono presi per analogia: n=175 con il 45%
    nella classe aperta. E' il ripiego piu' frequente nel collaudo (385
    casi), quindi il parametro piu' debole.
  · le coppie dello stesso sesso esistono ora, ma SOLO fra
    `coniugato_unito` (unioni civili), con p = 0,004 da ISTAT 2023.
    Le coppie CONVIVENTI dello stesso sesso -- due `celibe_nubile` --
    restano impossibili: la rilevazione ISTAT non le copre e sono
    verosimilmente piu' numerose. Nel repertorio AVQ sono comunque
    0,000 su 4.525 partner, il che e' una proprieta' della fonte e non
    della popolazione.
  · il rapporto M/F delle coppie unite segue quello dei riferimenti in
    coppia (~80% maschi) invece del 56% osservato: il sesso del
    riferimento si sceglie prima di sapere se la coppia sara' dello
    stesso sesso.
  · le AVQ dentro il nucleo restano scorrelate (rho ~0,6 nella realta',
    v22 §13.5), e l'INDIRIZZO e' assegnato per individuo: marito e
    moglie possono risultare a due civici diversi. Entrambe incoerenze
    che l'anello 4 rende visibili e non risolve.
  · la validazione a livello di nucleo NON e' possibile con le fonti
    disponibili. Serve il SUF EU-SILC.
  · repertorio emiliano-lombardo su undici comuni: trasferibilita'
    assunta, gemella della (6).

Riferimenti: `nota_nucleo_familiare_v3.md`, `nota_repertorio_avq_v2.md`.
"""

from __future__ import annotations

import datetime as _dt
import glob
import json
import os
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

__all__ = ["costruisci_repertorio", "carica_repertorio",
           "vincoli_da_sezione", "assembla", "Repertorio"]

# --------------------------------------------------------------- costanti

MAPPA_RELPAR = {1: "R", 2: "P", 3: "P", 4: "G", 5: "G", 6: "F", 7: "F",
                **{k: "A" for k in range(8, 17)}, 17: "N"}
ORDINE = {"R": 0, "P": 1, "F": 2, "G": 3, "A": 4, "N": 5}

BORDI_ETA = [2, 5, 10, 13, 15, 17, 19, 24, 34, 44, 54, 59, 64, 74, 200]
CENTRO_ETA = {1: 1, 2: 4, 3: 8, 4: 12, 5: 14.5, 6: 16.5, 7: 18.5, 8: 22,
              9: 29.5, 10: 39.5, 11: 49.5, 12: 57, 13: 62, 14: 69.5, 15: 82}

AMP_MAX_PF = 6
PAT_AVQ = "data/avq/anni/avq{a}/MICRODATI/AVQ_Microdati_{a}.txt"

# stato civile: usato solo se la colonna e' presente
STATO_COL = "stato_civile"
STATO_NON_PARTNER = {"vedovo"}      # un vedovo risposato sarebbe coniugato

CONVENZIONALI = {
    "PARTNER_MAX_DIFF": 15,
    "GENITORE_MIN": 20,
    "GENITORE_MAX": 40,
    # coppie dello stesso sesso: unioni civili. NON convenzionali --
    # misurate, ma tenute qui perche' esterne al repertorio AVQ.
    # Fonte: ISTAT, Rilevazione sulle unioni civili, 2023.
    #   tav. 2.11 (regione di RESIDENZA, non di costituzione: quella
    #   sovrastima del 12-13%): Emilia-Romagna 273 coppie, Lombardia 621,
    #   cioe' 6,14 e 6,21 per 100.000 residenti -- praticamente identici,
    #   quindi un solo parametro per tutti gli undici comuni.
    #   Cumulato su ~8,5 anni dall'entrata in vigore (giugno 2016):
    #   ~52 coppie per 100.000 residenti. Su Parma ~103 coppie unite su
    #   ~28.000 coppie coniugate.
    #   tav. 1.2: 56,1% delle unioni fra uomini (solo nazionale; Bologna
    #   dalla tav. 1.5 da' 59,7%, coerente).
    "P_STESSO_SESSO_UNITI": 0.004,
    "P_MASCHILE_UNITI": 0.56,
}


def classe_eta(anni) -> int:
    return int(np.searchsorted(BORDI_ETA, anni, side="left")) + 1


# ----------------------------------------------------------- repertorio

def _leggi_avq(anni, regioni, colonne):
    pezzi = []
    for anno in anni:
        p = PAT_AVQ.format(a=anno)
        if not os.path.exists(p):
            g = glob.glob(f"data/avq/**/*Microdati_{anno}*.txt", recursive=True)
            if not g:
                continue
            p = g[0]
        d = pd.read_csv(p, sep="\t", low_memory=False,
                        usecols=lambda c: c in colonne)
        d["ANNO"] = anno
        pezzi.append(d)
    if not pezzi:
        raise FileNotFoundError("microdati AVQ non trovati")
    d = pd.concat(pezzi, ignore_index=True)
    for c in ("REGMf", "RELPAR", "COEFIN", "ETAMi", "SESSO", "CITTMi"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    d["COEFIN"] = d["COEFIN"] / 10000.0
    d = d[d.REGMf.isin(regioni)].copy()
    d["nucleo"] = d.ANNO.astype(str) + "|" + d.PROFAM.astype(str)
    d["ruolo"] = d.RELPAR.map(MAPPA_RELPAR)
    return d


def _quantili(v, w, q):
    v, w = np.asarray(v, float), np.asarray(w, float)
    o = np.argsort(v)
    cum = np.cumsum(w[o]) / w.sum()
    return {str(p): float(v[o][np.searchsorted(cum, p)]) for p in q}


def costruisci_repertorio(anni=(2022, 2023, 2024), regioni=(80, 30),
                          coda_da_parma=True):
    """Repertorio delle configurazioni di nucleo, dai microdati AVQ.

    Il 2022 e' incluso benche' l'anello 2 lo escluda: gli manca `CRONI`,
    variabile TARGET che alla struttura familiare non serve.
    `ISTRMi = 99` NON e' filtrato: scartare un componente mutila il nucleo.
    """
    col = {"PROFAM", "RELPAR", "ETAMi", "SESSO", "CITTMi", "REGMf", "COEFIN"}
    d = _leggi_avq(anni, regioni, col)
    d["eta_c"] = d.ETAMi.map(CENTRO_ETA)

    g = d.groupby("nucleo")
    nuc = pd.DataFrame({
        "amp": g.size(),
        "peso": g["COEFIN"].first(),
        "firma": g.apply(lambda x: "".join(sorted(x.ruolo.dropna(),
                                                  key=lambda r: ORDINE[r]))),
    })
    n_rif = g["ruolo"].apply(lambda s: (s == "R").sum())
    if (n_rif != 1).any():
        raise ValueError(f"{int((n_rif != 1).sum())} nuclei senza esattamente "
                         "un riferimento: verificare RELPAR")

    firme = {}
    for k, s in nuc.groupby("amp"):
        v = s.groupby("firma")["peso"].sum()
        firme[str(int(k))] = {a: float(b) for a, b in (v / v.sum()).items()}

    rif = d[d.ruolo == "R"].merge(nuc[["firma"]], left_on="nucleo",
                                 right_index=True)
    p_masc = {}
    for f, s in rif.groupby("firma"):
        if len(s) >= 20:
            p_masc[f] = {"n": int(len(s)),
                         "p_maschio": float(np.average(
                             (s.SESSO == 1).to_numpy(float),
                             weights=s.COEFIN))}

    base = d[d.ruolo == "R"].set_index("nucleo")[["eta_c", "SESSO", "CITTMi"]]
    fig = d[d.ruolo == "F"].merge(base.add_suffix("_r"), left_on="nucleo",
                                  right_index=True)
    gen = (fig.eta_c_r - fig.eta_c)

    frat = []
    for _, s in fig.groupby("nucleo"):
        if len(s) > 1:
            e = np.sort(s.eta_c.to_numpy())
            frat += [(e[i + 1] - e[i], s.COEFIN.iloc[0])
                     for i in range(len(e) - 1)]

    noto = d[d.CITTMi.isin([1, 3])]
    per_n = noto.groupby("nucleo")["CITTMi"].agg(["nunique", "size"])
    misti = per_n[(per_n["size"] > 1)
                  & per_n.index.isin(noto[noto.CITTMi == 3].nucleo.unique())]
    p_om = float((misti["nunique"] == 1).mean()) if len(misti) else float("nan")

    rep = {
        "meta": {
            "generato": _dt.date.today().isoformat(),
            "anni": list(anni), "regioni": list(regioni),
            "n_nuclei": int(len(nuc)), "n_componenti": int(len(d)),
            "nota": "repertorio AVQ; la coda oltre l'ampiezza 6 viene dai "
                    "microdati di Parma (fonte mista, dichiarata)",
            "avvertenza": "in `convenzionali`, PARTNER_MAX_DIFF, GENITORE_MIN "
                      "e GENITORE_MAX NON sono misurati: sono convenzioni "
                      "o analogie. P_STESSO_SESSO_UNITI e "
                      "P_MASCHILE_UNITI vengono invece da "
                      "istat_unioni_civili_2023, e stanno nello stesso "
                      "blocco solo perche' sono costanti nel codice.",
        },
        "firme": firme,
        "coda": _coda_parma() if coda_da_parma else {},
        "riferimento": p_masc,
        "divari": {
            "generazionale": _quantili(gen, fig.COEFIN,
                                       (0.05, 0.25, 0.5, 0.75, 0.95)),
            "fratelli": (_quantili([x[0] for x in frat], [x[1] for x in frat],
                                   (0.5, 0.95)) if frat else {}),
        },
        "cittadinanza": {"p_omogeneo_misti": p_om, "n_misti": int(len(misti))},
        "convenzionali": dict(CONVENZIONALI),
    }
    return rep


def _coda_parma(path="data/opendata/034027/Popolazione_residente_2025.csv"):
    """Ampiezze oltre 6, dai microdati di Parma.

    L'AVQ ne ha 86 casi contro le migliaia di Parma: per la coda la
    numerosita' conta piu' della copertura regionale. FONTE MISTA,
    dichiarata in `meta`.
    """
    if not os.path.exists(path):
        return {}
    d = pd.read_csv(path, sep=";", dtype=str)
    d["Ncomp"] = pd.to_numeric(d.Ncomp, errors="coerce")
    d = d[(d.Tipores == "1") & d.Ncomp.notna() & (d.Ncomp > AMP_MAX_PF)]
    if not len(d):
        return {}
    n = d.groupby("Ncomp").size()
    n = n / n.index.to_series()          # persone -> nuclei, stesso indice
    return {str(int(k)): float(v) for k, v in (n / n.sum()).items()}


class Repertorio:
    """Vista validata sul JSON del repertorio."""

    def __init__(self, d):
        self.meta = d["meta"]
        self.firme = {int(k): v for k, v in d["firme"].items()}
        self.coda = {int(k): v for k, v in d.get("coda", {}).items()}
        self.riferimento = d.get("riferimento", {})
        self.divari = d["divari"]
        self.conv = d["convenzionali"]

        for k, v in self.firme.items():
            s = sum(v.values())
            if abs(s - 1.0) > 1e-6:
                raise ValueError(f"firme[{k}] somma a {s}, non a 1")

        if self.coda:
            v = np.array(list(self.coda.values()), float)
            if not np.isfinite(v).all():
                raise ValueError(
                    "coda con valori non finiti: probabile disallineamento "
                    "di indici in `_coda_parma` (groupby diviso per una "
                    "colonna invece che per il proprio indice)")
            s = float(v.sum())
            if abs(s - 1.0) > 1e-6:
                raise ValueError(f"coda somma a {s}, non a 1")
            if (v < 0).any():
                raise ValueError("coda con probabilita' negative")
            if min(self.coda) <= AMP_MAX_PF:
                raise ValueError(
                    f"la coda deve contenere solo ampiezze > {AMP_MAX_PF}: "
                    f"trovata {min(self.coda)}")

        for c in CONVENZIONALI:
            if c not in self.conv:
                raise ValueError(f"parametro convenzionale mancante: {c}")
        g = self.divari.get("generazionale", {})
        if not {"0.05", "0.95"} <= set(g):
            raise ValueError("divari.generazionale incompleto")
        self.gen_min = g["0.05"]
        self.gen_max = g["0.95"]
        self.frat_max = self.divari.get("fratelli", {}).get("0.95", 11.0)

    def firma(self, amp, rng):
        k = amp if amp in self.firme else max(
            (x for x in self.firme if x <= amp), default=None)
        if k is None:
            return "R" + "F" * (amp - 1)
        f = self.firme[k]
        scelta = rng.choice(list(f), p=np.array(list(f.values())))
        if len(scelta) == amp:
            return scelta
        return scelta + "F" * (amp - len(scelta)) if amp > len(scelta) \
            else scelta[:amp]

    def p_maschio(self, firma, default=0.5):
        v = self.riferimento.get(firma)
        return v["p_maschio"] if v else default


def carica_repertorio(path):
    with open(path, encoding="utf-8") as f:
        return Repertorio(json.load(f))


# ------------------------------------------------------------- vincoli

def vincoli_da_sezione(riga, n_individui, rep=None, rng=None):
    """Da `P1`, `PF3`..`PF8` ai nuclei per ampiezza, piu' la diagnostica.

      residuo <= 0            i vincoli chiedono piu' persone di quante ce
                              ne siano: riduci le ampiezze maggiori. NON e'
                              un difetto -- l'anello 3 alloca per sezione
                              con MAE 0,74-1,58, e uno scarto di un'unita'
                              basta a invertire il segno. Sul collaudo di
                              Parma capita in 372 sezioni su 1.301.
      0 < residuo <= 6*PF8    la classe aperta `PF8` («6 e oltre») era
                              troncata: allarga i nuclei da 6+ estraendo
                              dalla coda.
      residuo > 6*PF8         il resto e' CONVIVENZA: quegli individui
                              restano senza nucleo.

    Il criterio `6*PF8` e' locale: il residuo attribuibile al troncamento
    e' limitato da quanti nuclei da 6+ ci sono nella sezione.
    """
    pf = {k: int(riga.get(f"PF{k + 2}", 0) or 0)
          for k in range(1, AMP_MAX_PF + 1)}
    richiesti = sum(k * n for k, n in pf.items())
    residuo = int(n_individui) - richiesti
    diag = {"richiesti": richiesti, "residuo": residuo, "caso": "esatto",
            "convivenza": 0, "allargati": 0}

    nuclei = [k for k, n in pf.items() for _ in range(n)]

    if residuo == 0:
        return Counter(nuclei), diag

    if residuo < 0:
        diag["caso"] = "sovrastima"
        manca = -residuo
        nuclei.sort(reverse=True)
        i = 0
        while manca > 0 and i < len(nuclei):
            if nuclei[i] > 1:
                nuclei[i] -= 1
                manca -= 1
            else:
                i += 1
            if i == 0 and all(x == 1 for x in nuclei):
                break
            nuclei.sort(reverse=True)
        diag["ridotti"] = -residuo - manca
        return Counter(nuclei), diag

    capienza = AMP_MAX_PF * pf[AMP_MAX_PF]
    da_allargare = min(residuo, capienza)
    if da_allargare > 0 and rep is not None and rep.coda:
        rng = rng or np.random.default_rng(0)
        idx = [i for i, k in enumerate(nuclei) if k == AMP_MAX_PF]
        rng.shuffle(idx)
        ampiezze = np.array(sorted(rep.coda))
        p = np.array([rep.coda[a] for a in ampiezze])
        for i in idx:
            if da_allargare <= 0:
                break
            a = int(rng.choice(ampiezze, p=p / p.sum()))
            agg = min(a - AMP_MAX_PF, da_allargare)
            if agg > 0:
                nuclei[i] += agg
                da_allargare -= agg
                diag["allargati"] += 1
    diag["caso"] = "troncamento" if residuo <= capienza else "convivenza"
    diag["convivenza"] = int(max(0, residuo - capienza))
    return Counter(nuclei), diag


# ---------------------------------------------------------- assemblaggio

def assembla(individui, vincoli, rep, rng, prefisso=""):
    """Assegna `id_nucleo` e `ruolo` agli individui di una sezione.

    `individui`: DataFrame con `sesso` ('M'/'F') o `maschio` (bool),
    `eta_anni`, e -- se presente -- `stato_civile`, che diventa vincolo
    sullo slot `P`.

    Avido, senza backtracking: sul collaudo di Parma, 99,3% di nuclei
    senza alcun ripiego su 94.484, e divario generazionale fuori dai
    limiti nello 0,03% dei casi.

    Restituisce (DataFrame con `id_nucleo` e `ruolo`, diagnostica). Gli
    individui non collocati -- convivenze e residui -- hanno `pd.NA`.
    """
    ind = individui
    if "maschio" in ind.columns:
        masc = ind["maschio"].astype(bool).to_dict()
    else:
        masc = (ind["sesso"].astype(str).str.upper().str[0] == "M").to_dict()
    eta = pd.to_numeric(ind["eta_anni"], errors="coerce").to_dict()
    usa_sc = STATO_COL in ind.columns
    sc = ind[STATO_COL].astype(str).to_dict() if usa_sc else {}

    lib = set(i for i in ind.index if pd.notna(eta.get(i)))

    # conteggio per (stato civile, sesso): precheck O(1) sulla
    # disponibilita' di un partner compatibile per stato
    disp = Counter((sc[i], masc[i]) for i in lib) if usa_sc else Counter()

    def togli(i):
        lib.discard(i)
        if usa_sc:
            disp[(sc[i], masc[i])] -= 1

    firme = []
    for amp, n in sorted(vincoli.items(), reverse=True):
        firme += [rep.firma(int(amp), rng) for _ in range(int(n))]

    id_n = pd.Series(pd.NA, index=ind.index, dtype="object")
    ruoli = pd.Series(pd.NA, index=ind.index, dtype="object")
    diag = {"nuclei": len(firme), "ripieghi": Counter(),
            "divari": defaultdict(list), "perfetti": 0,
            "coppie": 0, "coppie_omogenee": 0,
            "senza_eta": int(len(ind) - len(lib))}

    pmax = float(rep.conv["PARTNER_MAX_DIFF"])
    p_ss = float(rep.conv.get("P_STESSO_SESSO_UNITI", 0.0))
    p_m_ss = float(rep.conv.get("P_MASCHILE_UNITI", 0.5))
    gmin, gmax = float(rep.conv["GENITORE_MIN"]), float(rep.conv["GENITORE_MAX"])

    # RITIRATA la preassegnazione dei vedovi agli unipersonali (provata
    # il 10/8/2026, misurata, tolta). L'idea era che i vedovi sono la
    # categoria che riempie i nuclei da 1, e che il ciclo -- processando
    # dal piu' grande al piu' piccolo -- li consuma prima come riferimenti
    # di nuclei plurimi. Ma dando loro la prelazione si TOLGONO quei posti
    # ai coniugati che vivono soli, che erano classificati legittimi:
    #
    #     coniugati in nuclei unipersonali   21,6% -> 17,5%
    #     coniugati con ruolo R incoerenti    7,8% -> 15,7%
    #     incoerenza totale                  21,7% -> 25,0%
    #
    # Il problema si sposta, non si risolve. La versione corretta sarebbe
    # una preassegnazione PROPORZIONALE, che riempia gli unipersonali
    # rispettando le quote reali di stato civile fra chi vive solo --
    # quote misurabili sull'AVQ (nuclei con NCOMP=1) e non ancora
    # misurate. Raffinamento, non blocco.
    for n_i, firma in enumerate(sorted(firme, key=len, reverse=True)):
        if not lib:
            diag["ripieghi"]["nucleo senza individui"] += 1
            continue
        nid = f"{prefisso}{n_i:06d}"
        n_f, n_p = firma.count("F"), firma.count("P")
        pulito = True

        # --- riferimento -------------------------------------------------
        cand = list(lib)
        if n_f:
            # Conteggio "figli plausibili" con eta' ordinate + searchsorted:
            # semantica identica al doppio loop (stesso insieme `ok`, stesso
            # ordine, rng non toccato), costo da O(n^2) a O(n log n) per
            # nucleo. Necessario per le sezioni metropolitane (Milano:
            # 15 sezioni >1000, max 4.146 — collaudo 25/8).
            _ee = np.sort(np.fromiter((eta[h] for h in lib),
                                      dtype=np.int64, count=len(lib)))
            _ej = np.fromiter((eta[j] for j in cand),
                              dtype=np.int64, count=len(cand))
            _nf = (np.searchsorted(_ee, _ej - rep.gen_min, side="right")
                   - np.searchsorted(_ee, _ej - rep.gen_max, side="left"))
            ok = [j for j, m in zip(cand, _nf >= n_f) if m]
            if ok:
                cand = ok
            else:
                diag["ripieghi"]["R senza figli plausibili"] += 1
                pulito = False
        if usa_sc:
            if n_p:
                # deve esistere almeno un potenziale partner del suo stato
                ok = [j for j in cand
                      if sc[j] not in STATO_NON_PARTNER
                      and disp[(sc[j], not masc[j])] > 0]
                if ok:
                    cand = ok
                else:
                    diag["ripieghi"]["R senza partner del suo stato"] += 1
                    pulito = False
            else:
                # firme senza partner: preferisci vedovi e non coniugati
                ok = [j for j in cand if sc[j] in STATO_NON_PARTNER]
                if ok and rng.random() < 0.5:
                    cand = ok
        vuole_m = n_p > 0
        pref = [j for j in cand if masc[j] == vuole_m]
        if pref and rng.random() < rep.p_maschio(firma, 0.8 if n_p else 0.5):
            cand = pref
        r = cand[int(rng.integers(len(cand)))]
        togli(r)
        id_n[r], ruoli[r] = nid, "R"

        # --- figli: lo slot piu' vincolato -------------------------------
        figli = []
        for _ in range(n_f):
            c = [j for j in lib
                 if rep.gen_min <= eta[r] - eta[j] <= rep.gen_max
                 and (not figli or
                      min(abs(eta[j] - eta[f]) for f in figli) <= rep.frat_max)]
            if not c:
                c = [j for j in lib if eta[r] - eta[j] >= 15]
                if c:
                    diag["ripieghi"]["F fuori dai limiti"] += 1
                    pulito = False
            if not c:
                diag["ripieghi"]["F senza ripiego"] += 1
                pulito = False
                continue
            j = c[int(rng.integers(len(c)))]
            togli(j)
            figli.append(j)
            id_n[j], ruoli[j] = nid, "F"
            diag["divari"]["generazionale"].append(eta[r] - eta[j])

        # --- partner: stato civile uguale, sesso opposto, eta' entro pmax -
        for _ in range(n_p):
            # `STATO_NON_PARTNER` vale in TUTTI i rami, ripieghi
            # compresi: un `P` mancante e' meno grave di un `P`
            # impossibile. Nella v2 il filtro era applicato al solo
            # riferimento, e il ripiego `c = base` riammetteva i vedovi:
            # ~180 coppie coniugato+vedovo su Parma.
            # Coppie dello stesso sesso: solo fra `coniugato_unito`,
            # perche' e' la modalita' che contiene le unioni civili.
            # Le coppie CONVIVENTI dello stesso sesso (due
            # `celibe_nubile`) restano fuori: la rilevazione ISTAT sulle
            # unioni civili non le copre, e sono verosimilmente piu'
            # numerose. Limite dichiarato.
            stesso = (usa_sc and sc[r] == "coniugato_unito"
                      and rng.random() < p_ss)
            if stesso:
                # il sesso della coppia segue la quota osservata; se il
                # riferimento non e' del sesso estratto, la coppia resta
                # dello stesso sesso comunque -- e' il suo che conta
                amm = [j for j in lib if masc[j] == masc[r]
                       and sc[j] == "coniugato_unito"]
                if not amm:
                    stesso = False
                else:
                    diag["coppie_stesso_sesso"] = (
                        diag.get("coppie_stesso_sesso", 0) + 1)
            if not stesso:
                amm = [j for j in lib if masc[j] != masc[r]
                       and (not usa_sc or sc[j] not in STATO_NON_PARTNER)]
            base = [j for j in amm if abs(eta[j] - eta[r]) <= pmax]
            c = ([j for j in base if sc[j] == sc[r]] if usa_sc else base)
            omogenea = bool(c)
            if not c:
                c = base
                if c and usa_sc:
                    diag["ripieghi"]["P stato civile diverso"] += 1
                    pulito = False
            if not c:
                c = amm
                if c:
                    diag["ripieghi"]["P fuori dai limiti"] += 1
                    pulito = False
            if not c:
                diag["ripieghi"]["P senza ripiego"] += 1
                pulito = False
                continue
            j = c[int(rng.integers(len(c)))]
            togli(j)
            id_n[j], ruoli[j] = nid, "P"
            diag["coppie"] += 1
            diag["coppie_omogenee"] += int(omogenea)
            diag["divari"]["partner"].append(eta[j] - eta[r])

        # --- genitori, altri parenti, non parenti ------------------------
        for ruolo in firma:
            if ruolo in "RPF" or not lib:
                continue
            if ruolo == "G":
                c = [j for j in lib if gmin <= eta[j] - eta[r] <= gmax]
                if not c:
                    c = [j for j in lib if eta[j] > eta[r]]
                    diag["ripieghi"]["G fuori dai limiti"] += 1
                    pulito = False
            else:
                c = list(lib)
            if not c:
                diag["ripieghi"][f"{ruolo} senza ripiego"] += 1
                pulito = False
                continue
            j = c[int(rng.integers(len(c)))]
            togli(j)
            id_n[j], ruoli[j] = nid, ruolo

        diag["perfetti"] += int(pulito)

    diag["non_collocati"] = len(lib)
    diag["ripieghi"] = dict(diag["ripieghi"])
    diag["divari"] = {k: list(map(float, v)) for k, v in diag["divari"].items()}
    return pd.DataFrame({"id_nucleo": id_n, "ruolo": ruoli}), diag
