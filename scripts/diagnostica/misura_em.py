#!/usr/bin/env python3
"""M-EM — il background migratorio ha struttura geografica sotto la zona?

Analogo di M4 (`misura_nucleo_m4.py`) applicato a `EM1`-`EM6` del
censimento permanente 2023 per sezione. Decide se valga la pena
raffinare `assegna_sezione` in `enrich.py` (anello 3), o se
l'assunzione (8) -- background indipendente dalla sezione data la zona --
sia gia' adeguata.

    M-EMa   TVD( P(EM | zona),    P(EM | comune) )   comune -> zona
    M-EMb   TVD( P(EM | sezione), P(EM | zona)   )   zona   -> sezione

Versione 2, 9 agosto 2026. Due correzioni al primo giro, entrambe sul
modo di leggere il risultato -- vedi CORREZIONI in fondo.


PERCHE' I DUE GRUPPI SI MISURANO SEPARATI

Le sei modalita' si spartiscono DETERMINISTICAMENTE fra le due
cittadinanze di anello 1 -- e' la stessa dipendenza funzionale del
blocco GC che rende riducibile la catena Gibbs a K9C/K10C:

    EM1 italiano_nativo           EM5 straniero_g2
    EM2 italiano_rientrato        EM6 straniero_immigrato
    EM3 naturalizzato_g2                    -> FRG
    EM4 naturalizzato_immigrato
              -> ITL

Quindi `EM` non moltiplica la quota di cittadinanza gia' calcolata da
`load_sezioni` (`q_{sesso}_{eta3}` dai campi ST): la RAFFINA dentro il
gruppo. Misurare sulle sei modalita' insieme confonderebbe il segnale
del raffinamento con quello della cittadinanza, che la pipeline gia'
cattura per sezione. La composizione va quindi normalizzata DENTRO il
gruppo, ed e' cosi' che verrebbe usata in `enrich.py`.


IL PAVIMENTO E' MULTINOMIALE, NON PERMUTAZIONALE

M3 e M4 lavoravano su microdati e il nullo giusto era la permutazione
delle etichette. Qui i dati sono CONTEGGI PER SEZIONE: il nullo e'
«ogni sezione estrae i suoi n individui dalla composizione della sua
zona». Si simula con una multinomiale per sezione, a n fissato.
Senza pavimento il numero non si legge: con modalita' all'1,3% e
sezioni da ~150 persone, la TVD osservata e' quasi tutta rarefazione.


LA GUARDIA SUI SUPPORTI, E PERCHE' QUI NON DEVE SCATTARE

`T.composizione` scarta le modalita' a zero, e con supporti diversi
`T.tvd` rifiuta di misurare. E' giusto quando le modalita' assenti
segnalano una classificazione diversa -- il caso per cui la guardia e'
stata scritta. QUI NO: il supporto e' noto a priori (quattro o due campi
censuari fissi) e uno zero e' un conteggio nullo, non una modalita'
assente. Le composizioni si costruiscono quindi sul supporto pieno,
zeri inclusi, e la guardia passa legittimamente.


ESITO DEL PRIMO GIRO (Parma, v1), da riprodurre

    gruppo   M-EMa      M-EMb      rapporto
    ITL      +0,0120    +0,0200    1,67
    FRG      +0,0181    +0,0232    1,29

ENTRAMBE LE PREVISIONI REGISTRATE SONO STATE FALSIFICATE.

(a) «netto sostanziale su FRG, ~zero su ITL, perche' con EM1 al 93% del
    gruppo le altre modalita' sono troppo rare per emergere sopra il
    pavimento». Falsificata: ITL ha netto PIU' ALTO di FRG. Lettura
    post-hoc, non verificata: proprio perche' EM1 domina, naturalizzati
    e italiani rientrati sono fortemente concentrati dove stanno i
    migranti di prima generazione.

(b) «netto piccolo su entrambi, perche' nota_segnale_compositivo_v3
    misura che sotto il quartiere si perde l'85-98% del segnale
    compositivo». Falsificata: entrambi i rapporti sopra uno.
    Riconciliazione possibile, da verificare: quella nota misurava la
    composizione per NAZIONALITA' fra paesi, questa il background
    GENERAZIONALE. La seconda generazione si concentra dove c'e'
    edilizia popolare e scuole, non dove si concentra una nazionalita'.

TERZA PREVISIONE FALSIFICATA SU TRE in questa linea di lavoro (M3', M4,
M-EM), sempre nella stessa direzione: la struttura fine sotto la zona
viene sistematicamente sottostimata. E' una regola di calibrazione, non
un aneddoto.


LE DUE CORREZIONI DELLA v2

(1) PAVIMENTO PER TERZILE. La v1 stampava la sola TVD osservata per
    terzile di ampiezza, e su Parma ITL scendeva monotonicamente da
    0,0564 a 0,0367: e' il profilo del PAVIMENTO, non del segnale, e non
    permetteva di dire se il netto sopravviva dove il pavimento e'
    basso. E' lo stesso difetto gia' corretto in `misura_nucleo_m4.py`
    e qui ripetuto. Ora il pavimento si calcola per strato, sugli stessi
    strati, e si stampa il netto.

(2) IL RAPPORTO NON E' CONFRONTABILE FRA COMUNI. M-EMa dipende
    meccanicamente da quanto e' grossolana la partizione in zone: Modena
    ha 4 zone da 46.000 abitanti, Bologna 18, Brescia 33. Con poche zone
    il denominatore e' piccolo e il rapporto si gonfia, il che e' un
    fatto sulla partizione e non sul background. Per il confronto fra
    citta' vale il solo netto M-EMb, definito allo stesso modo ovunque;
    il rapporto si legge DENTRO un comune. Il riepilogo ora stampa il
    numero di zone accanto ai numeri e ordina per M-EMb.

    python scripts/diagnostica/misura_em.py 034027
    python scripts/diagnostica/misura_em.py            # tutti i comuni

Fonte: `istat_sezioni_2023`, derivati in `data/submun/`.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

import gsp.common as G
import gsp.tvd as T

GRUPPI = {"ITL": ["EM1", "EM2", "EM3", "EM4"],
          "FRG": ["EM5", "EM6"]}
ETICHETTE = {"EM1": "italiano_nativo", "EM2": "italiano_rientrato",
             "EM3": "naturalizzato_g2", "EM4": "naturalizzato_immigrato",
             "EM5": "straniero_g2", "EM6": "straniero_immigrato"}

SPECIALI = ("888888", "999999")
MIN_N = 30          # individui del gruppo perche' la sezione entri in M-EMb
MIN_ZONA = 200      # individui del gruppo perche' la zona entri in M-EMa
N_PERM = 50
RNG = np.random.default_rng(20260809)


def elenco_comuni():
    """Il registro di gsp.common, se espone un dizionario di comuni."""
    for attr in ("COMUNI", "REGISTRO", "REGISTRO_COMUNI", "INFO"):
        v = getattr(G, attr, None)
        if isinstance(v, dict) and v:
            return sorted(v)
    return None


def carica(comune):
    path = G.path_sezioni(comune)
    if not os.path.exists(path):
        return None, f"file sezioni assente: {path}"
    s = pd.read_csv(path)
    manca = [c for c in ETICHETTE if c not in s.columns]
    if manca:
        return None, f"campi assenti: {manca} (rigenerare con build_sezioni.py)"

    sez = s["SEZ21_ID"].astype("Int64").astype(str)
    s = s[~sez.str.contains("|".join(SPECIALI), regex=True)].copy()

    liv = G.livello_col(comune) if G.info(comune)["livello"] else None
    if liv is not None and liv not in s.columns:
        return None, f"colonna zona {liv} assente"
    s["zona"] = (s[liv].astype("Int64").astype(str) if liv is not None
                 else "0")
    for c in ETICHETTE:
        s[c] = pd.to_numeric(s[c], errors="coerce").fillna(0.0)
    return s, None


def _tvd(a, b, campi):
    """TVD su supporto PIENO: gli zeri sono conteggi nulli, non modalita'
    assenti. Vedi il docstring."""
    sa = pd.Series(np.asarray(a, float), index=campi)
    sb = pd.Series(np.asarray(b, float), index=campi)
    if sa.sum() <= 0 or sb.sum() <= 0:
        return np.nan
    return T.tvd(sa, sb)


def _basi(s, campi, base_livello):
    if base_livello == "zona":
        return s.groupby("zona")[campi].sum()
    return pd.DataFrame([s[campi].sum()], index=["_"])


def _chiave(s, campi, livello, base_livello):
    agg = s.groupby(livello)[campi].sum()
    key = (s.groupby(livello)["zona"].first() if base_livello == "zona"
           else pd.Series("_", index=agg.index))
    return agg, key


def misura(s, campi, livello, base_livello, min_n):
    """TVD di ogni unita' contro la propria base, con la numerosita'."""
    agg, key = _chiave(s, campi, livello, base_livello)
    basi = _basi(s, campi, base_livello)
    righe = []
    for u, riga in agg.iterrows():
        n = float(riga.sum())
        if n < min_n:
            continue
        b = basi.loc[key.loc[u]]
        righe.append({"unita": u, "n": n,
                      "TVD": _tvd(riga.to_numpy(), b.to_numpy(), campi)})
    r = pd.DataFrame(righe)
    if r.empty:
        return r, np.nan
    v = r.dropna(subset=["TVD"])
    return r, (float(np.average(v.TVD, weights=v.n)) if len(v) else np.nan)


def pavimento(s, campi, livello, base_livello, min_n, strati=None,
              n_perm=N_PERM):
    """Nullo multinomiale: ogni unita' estrae i suoi n individui dalla
    composizione della propria base, a n fissato.

    `strati` e' una mappa unita' -> etichetta di strato. Se presente, il
    pavimento si calcola ANCHE per strato: e' il test che dice se il
    netto sopravvive dove il pavimento e' basso (correzione (1)).
    """
    agg, key = _chiave(s, campi, livello, base_livello)
    p = _basi(s, campi, base_livello)
    p = p.div(p.sum(axis=1), axis=0)

    n_u = agg.sum(axis=1)
    tenute = [u for u in n_u.index if n_u.loc[u] >= min_n]
    if not tenute:
        return np.nan, np.nan, {}

    glob, per_str = [], {}
    for _ in range(n_perm):
        t, w, acc = [], [], {}
        for u in tenute:
            pu = p.loc[key.loc[u]].to_numpy(float)
            if not np.isfinite(pu).all() or pu.sum() <= 0:
                continue
            n = int(round(n_u.loc[u]))
            d = _tvd(RNG.multinomial(n, pu / pu.sum()), pu, campi)
            if not np.isfinite(d):
                continue
            t.append(d)
            w.append(n)
            if strati is not None:
                acc.setdefault(strati.get(u), []).append((d, n))
        if t:
            glob.append(float(np.average(t, weights=w)))
        for st, vals in acc.items():
            dd = np.array([x[0] for x in vals])
            ww = np.array([x[1] for x in vals], float)
            per_str.setdefault(st, []).append(float(np.average(dd, weights=ww)))

    if not glob:
        return np.nan, np.nan, {}
    return (float(np.mean(glob)), float(np.percentile(glob, 95)),
            {k: float(np.mean(v)) for k, v in per_str.items()})


def blocco(s, campi, gruppo, comune, nome):
    n_tot = float(s[campi].sum().sum())
    n_zone = s["zona"].nunique()
    una_zona = n_zone <= 1
    base_b = "comune" if una_zona else "zona"

    print(f"\n--- {nome} · gruppo {gruppo}: {n_tot:,.0f} individui, "
          f"{n_zone} zone, {len(s)} sezioni ---".replace(",", "."))
    print("   composizione comunale: "
          + ", ".join(f"{ETICHETTE[c]} {v:.3f}"
                      for c, v in (s[campi].sum() / n_tot).items()))

    na = None
    if una_zona:
        print("   comune non articolato: M-EMa non definita")
    else:
        _, oa = misura(s, campi, "zona", "comune", MIN_ZONA)
        ma, p95a, _ = pavimento(s, campi, "zona", "comune", MIN_ZONA)
        if np.isfinite(oa) and np.isfinite(ma):
            na = oa - ma
            print(f"   M-EMa comune->zona     oss {oa:.4f}  pav {ma:.4f} "
                  f"(p95 {p95a:.4f})  NETTO {na:+.4f}")

    rb, ob = misura(s, campi, "SEZ21_ID", base_b, MIN_N)
    if rb.empty or not np.isfinite(ob):
        print("   M-EMb: non misurabile")
        return na, None, n_zone

    # strati sulla numerosita' del GRUPPO nella sezione
    strati = None
    if len(rb) > 30:
        q1, q2 = rb.n.quantile([1 / 3, 2 / 3])
        rb = rb.assign(strato=pd.cut(
            rb.n, [-1, q1, q2, np.inf],
            labels=[f"piccole (<={q1:.0f})", f"medie ({q1:.0f}-{q2:.0f})",
                    f"grandi (>{q2:.0f})"]).astype(str))
        strati = dict(zip(rb.unita, rb.strato))

    mb, p95b, mb_str = pavimento(s, campi, "SEZ21_ID", base_b, MIN_N, strati)
    if not np.isfinite(mb):
        print("   M-EMb: pavimento non calcolabile")
        return na, None, n_zone

    nb = ob - mb
    esclusa = 1.0 - rb.n.sum() / n_tot
    print(f"   M-EMb zona->sezione    oss {ob:.4f}  pav {mb:.4f} "
          f"(p95 {p95b:.4f})  NETTO {nb:+.4f}")
    print(f"      sezioni misurate {len(rb)} · massa esclusa da "
          f"MIN_N={MIN_N}: {esclusa:.1%}")

    if strati is not None and mb_str:
        print("      netto per terzile di ampiezza del gruppo:")
        for st in sorted(rb.strato.unique()):
            g = rb[rb.strato == st].dropna(subset=["TVD"])
            if not len(g) or st not in mb_str:
                continue
            o = float(np.average(g.TVD, weights=g.n))
            print(f"         {st:22s} oss {o:.4f}  pav {mb_str[st]:.4f}  "
                  f"NETTO {o - mb_str[st]:+.4f}")
        print("      se il netto sopravvive nelle GRANDI, dove il pavimento "
              "e' basso,\n      il segnale e' reale; se svanisce, era "
              "rarefazione.")

    if na is not None and na > 1e-9:
        print(f"   RAPPORTO M-EMb/M-EMa = {nb / na:.2f}   "
              f"(leggibile solo DENTRO il comune: dipende da n_zone)")
    return na, nb, n_zone


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comuni", nargs="*", help="codici ISTAT")
    a = ap.parse_args()

    comuni = a.comuni or elenco_comuni()
    if not comuni:
        sys.exit("nessun comune: passarli come argomenti\n"
                 "  (gsp.common non espone un dizionario riconoscibile)")

    esiti = []
    for c in comuni:
        s, err = carica(c)
        if s is None:
            print(f"\n[{c}] saltato: {err}")
            continue
        nome = G.info(c).get("nome", c)
        print("\n" + "=" * 72)
        print(f"{nome} ({c})")
        print("=" * 72)
        for gruppo, campi in GRUPPI.items():
            na, nb, nz = blocco(s, campi, gruppo, c, nome)
            esiti.append({"comune": nome, "gruppo": gruppo, "zone": nz,
                          "M_EMa": na, "M_EMb": nb})

    e = pd.DataFrame(esiti)
    print("\n" + "=" * 72)
    print("riepilogo — ordinato per M-EMb, che e' l'unico confrontabile")
    print("=" * 72)
    for gruppo in GRUPPI:
        g = e[e.gruppo == gruppo].sort_values("M_EMb", ascending=False)
        if g.empty:
            continue
        print(f"\ngruppo {gruppo}")
        print(f"   {'comune':18s} {'zone':>5s} {'M-EMa':>9s} {'M-EMb':>9s} "
              f"{'rapp':>7s}")
        for _, r in g.iterrows():
            sa = f"{r.M_EMa:+.4f}" if pd.notna(r.M_EMa) else "    n/d"
            sb = f"{r.M_EMb:+.4f}" if pd.notna(r.M_EMb) else "    n/d"
            sr = (f"{r.M_EMb / r.M_EMa:.2f}"
                  if pd.notna(r.M_EMa) and pd.notna(r.M_EMb)
                  and r.M_EMa > 1e-9 else "n/d")
            print(f"   {r.comune:18s} {r.zone:5d} {sa:>9s} {sb:>9s} {sr:>7s}")

    print("\n   M-EMb e' definito allo stesso modo ovunque: e' la colonna da")
    print("   confrontare fra citta'. Il RAPPORTO no -- dipende da quanto e'")
    print("   grossolana la partizione in zone (Modena 4, Bologna 18,")
    print("   Brescia 33), quindi si legge solo dentro un comune.")
    print("\n   Il numero che decide se toccare enrich.py e' il netto per")
    print("   terzile nelle sezioni GRANDI, non la media globale.")


if __name__ == "__main__":
    main()
