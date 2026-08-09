#!/usr/bin/env python3
"""M4 — quale livello geografico serve all'assemblaggio dei nuclei?

Segue `misura_nucleo.py`, stessa fonte (Parma, Popolazione_residente_2025).
Versione 2, 9 agosto 2026: due correzioni al primo giro, entrambe sul
numero centrale.


PERCHE' SERVE

M3 ha misurato il residuo geografico a livello di QUARTIERE, e ha
risposto a una domanda gia' risolta: `Quartiere` e' `zona`, cioe' un
attributo vincolato di anello 1, disponibile a valle per costruzione.
L'architettura e' decisa -- il ruolo si deriva a valle condizionando su
zona x sesso x eta' x cittadinanza, e anello 1 non si tocca.

Resta la domanda che riguarda l'ASSEMBLAGGIO: 13 quartieri da ~15.000
abitanti contro 1.314 sezioni da ~150. Se la composizione dei nuclei e'
omogenea dentro il quartiere, l'assemblaggio usa la distribuzione di
quartiere; se no, servono vincoli per sezione.


LA FORMA DELLA MISURA

Con le celle demografiche le sezioni diventano troppo sottili e la
guardia sui supporti scatta ovunque. M4 rinuncia al controllo per
demografia e misura due passaggi di scala, ciascuno contro il proprio
pavimento di rumore:

    M4a   TVD( P(y | quartiere), P(y) )             comune    -> quartiere
    M4b   TVD( P(y | sezione),   P(y | quartiere) ) quartiere -> sezione

Il numero che interessa e' il RAPPORTO fra i netti. Vicino a zero:
scendere sotto il quartiere non aggiunge. Vicino o sopra uno: la sezione
porta quanto il quartiere, e i vincoli di sezione servono.

Il pavimento di M4b permuta le etichette di sezione DENTRO il quartiere:
distrugge la struttura di sezione conservando la composizione del
quartiere e le ampiezze delle sezioni. Senza, il numero non e'
confrontabile -- una sezione da 150 persone ha TVD elevata anche in
assenza di segnale.


LE DUE CORREZIONI DELLA v2

(1) PESO PER FAMIGLIA. `ncomp5` calcolata sui residenti sovrappesa i
    nuclei grandi -- una famiglia da 5 conta cinque volte. Ma il vincolo
    che serve all'assemblaggio e' la distribuzione SULLE FAMIGLIE. Si
    corregge pesando per 1/Ncomp, che e' lo stesso stimatore gia'
    validato: somma di 1/Ncomp = 96.984 contro 96.985 persone di
    riferimento.
    Entrambe le pesature sono riportate: la conclusione va letta su
    quella per famiglia, quella per persona serve a riprodurre il primo
    giro e a vedere se il verso cambia.
    Su `relpar` la pesatura per famiglia non ha senso -- i ruoli sono
    per persona -- e resta la pesatura naturale.

(2) NETTO PER STRATO DI AMPIEZZA, e RITRATTAZIONE.
    La v1 stampava la correlazione fra TVD e ampiezza della sezione e la
    commentava cosi': «negativa e forte -> quel che resta e' rumore di
    campionamento residuo». IL COMMENTO ERA SBAGLIATO. Sotto l'ipotesi
    nulla quella correlazione e' negativa comunque, perche' le sezioni
    piccole hanno TVD alta per costruzione: il -0,438 misurato al primo
    giro non discriminava nulla.
    Il test corretto e' il netto calcolato per terzile di ampiezza. Se
    sopravvive anche nelle sezioni grandi -- dove il pavimento e' basso
    -- il segnale e' reale. Se svanisce, era rarefazione.
    Le strate si costruiscono sul conteggio di PERSONE, che la
    permutazione dentro il quartiere conserva esattamente, cosi' la
    stratificazione e' la stessa nell'osservato e nel nullo.


ESITI DEL PRIMO GIRO (v1, 9 agosto 2026), da riprodurre

    ncomp5   M4a +0,0459   M4b +0,0638   rapporto 1,39
    relpar   M4a +0,0333   M4b +0,0214   rapporto 0,64

L'attesa registrata prima della misura -- M4b/M4a sotto 0,3 su `ncomp5`,
perche' il gradiente centro-periferia visto in M3 opera alla scala del
quartiere -- E' STATA FALSIFICATA. Il gradiente c'e' (Parma Centro 0,128,
Vigatto 0,087) ma e' piccolo rispetto all'eterogeneita' DENTRO il
quartiere. Seconda previsione falsificata su due, entrambe nella stessa
direzione: struttura fine sottostimata.

    python scripts/diagnostica/misura_nucleo_m4.py \
        2>&1 | tee note/misure/tvd_nucleo_m4_parma_AAAAMMGG.txt
"""

import sys

import numpy as np
import pandas as pd

import gsp.tvd as T

SRC = "data/opendata/034027/Popolazione_residente_2025.csv"
SEP = ";"

# soglie in unita' della pesatura usata: persone senza peso, famiglie con
MIN_QUART_P, MIN_SEZ_P = 500, 60
MIN_QUART_F, MIN_SEZ_F = 250, 30

N_PERM = 50
RNG = np.random.default_rng(20260809)

# codici numerici: senza questo il modulo scarta in silenzio Relpar=9 e
# una eventuale sezione "9" o "99"
KW = dict(auto_totali=False)


def carica():
    try:
        d = pd.read_csv(SRC, sep=SEP, dtype=str)
    except FileNotFoundError:
        sys.exit(f"non trovato: {SRC}\nlanciare dalla radice di ~/progetti/gsp")

    d["ETA"] = pd.to_numeric(d["ETA"], errors="coerce")
    d["Ncomp"] = pd.to_numeric(d["Ncomp"], errors="coerce")
    d = d.dropna(subset=["ETA", "Ncomp", "Relpar", "Sesso", "SEZ21",
                         "Quartiere"])
    d = d[d.Tipores == "1"]
    d = d[~((d.Ncomp == 1) & (d.Relpar != "1"))]

    d["ncomp5"] = "n" + d["Ncomp"].clip(upper=5).astype(int).astype(str)
    d["relpar"] = "r" + d["Relpar"].astype(str)
    d["w_fam"] = 1.0 / d["Ncomp"]          # peso: una unita' per famiglia

    n = d.groupby("SEZ21").size()
    print(f"in analisi {len(d):,}".replace(",", ".")
          + f"  ·  quartieri {d.Quartiere.nunique()}"
          + f"  ·  sezioni {d.SEZ21.nunique()}"
          + f"  ·  famiglie {d.w_fam.sum():,.0f}".replace(",", "."))
    print(f"   persone per sezione: mediana {n.median():.0f}, "
          f"1o quartile {n.quantile(.25):.0f}, max {n.max()}")
    return d, n


def strati(n_sez):
    """Terzili di ampiezza, sul conteggio di persone (invariante sotto
    permutazione dentro il quartiere)."""
    q1, q2 = n_sez.quantile([1 / 3, 2 / 3])
    et = pd.cut(n_sez, [-1, q1, q2, np.inf],
                labels=[f"piccole (<={q1:.0f})",
                        f"medie ({q1:.0f}-{q2:.0f})",
                        f"grandi (>{q2:.0f})"])
    return et.astype(str).to_dict(), (q1, q2)


def _media(p):
    if p.empty:
        return float("nan")
    v = p.dropna(subset=["TVD"])
    return float(np.average(v.TVD, weights=v.n)) if len(v) else float("nan")


def m4a(d, y, peso, min_q, permuta=False):
    g = d.assign(Quartiere=RNG.permutation(d.Quartiere.values)) if permuta else d
    p = T.profilo(g, y, ["Quartiere"], peso, base=T.composizione(g, y, peso),
                  min_unita=min_q, stampa=False, **KW)
    return p, _media(p)


def m4b(d, y, peso, min_q, min_s, permuta=False):
    righe = []
    for q, g in d.groupby("Quartiere", observed=True):
        massa = g[peso].sum() if peso else len(g)
        if massa < min_q:
            continue
        if permuta:
            g = g.assign(SEZ21=RNG.permutation(g.SEZ21.values))
        p = T.profilo(g, y, ["SEZ21"], peso, base=T.composizione(g, y, peso),
                      min_unita=min_s, stampa=False, **KW)
        if not p.empty:
            righe.append(p.assign(quartiere=q))
    if not righe:
        return pd.DataFrame(), float("nan")
    r = pd.concat(righe, ignore_index=True)
    return r, _media(r)


def per_strato(r, mappa):
    """Media pesata della TVD dentro ogni terzile di ampiezza."""
    if r.empty:
        return {}
    v = r.dropna(subset=["TVD"]).copy()
    if not len(v):
        return {}
    v["strato"] = v.modalita.map(mappa)
    return {s: float(np.average(g.TVD, weights=g.n))
            for s, g in v.groupby("strato", observed=True) if len(g)}


def blocco(fun, d, y, peso, args, etichetta, mappa=None):
    r, oss = fun(d, y, peso, *args)
    if not np.isfinite(oss):
        print(f"\n{etichetta}: nessuna unita' misurabile.")
        return None, r
    oss_s = per_strato(r, mappa) if mappa else {}

    tot, strat = [], []
    for _ in range(N_PERM):
        rp, m = fun(d, y, peso, *args, permuta=True)
        if np.isfinite(m):
            tot.append(m)
            if mappa:
                strat.append(per_strato(rp, mappa))
    mu, p95 = float(np.mean(tot)), float(np.percentile(tot, 95))
    nm, ms = int(r.TVD.isna().sum()), int(r.TVD.notna().sum())

    print(f"\n{etichetta}")
    print(f"   osservata {oss:.4f}   pavimento {mu:.4f} (p95 {p95:.4f})"
          f"   NETTO {oss - mu:+.4f}")
    print(f"   unita' misurate {ms}, non misurate {nm}")
    if nm > ms:
        print("   !! la maggioranza non e' misurabile: non e' «la sezione "
              "non conta»,\n      e' «la fonte non incrocia abbastanza».")

    if oss_s and strat:
        print("\n   netto per terzile di ampiezza — il test che sostituisce "
              "la\n   correlazione TVD~ampiezza della v1, che era priva di "
              "potere:")
        for s in sorted(oss_s):
            f = [x[s] for x in strat if s in x]
            if not f:
                continue
            m_s = float(np.mean(f))
            print(f"      {s:22s} oss {oss_s[s]:.4f}  pav {m_s:.4f}  "
                  f"NETTO {oss_s[s] - m_s:+.4f}")
        print("   se il netto sopravvive nelle sezioni GRANDI, dove il "
              "pavimento e'\n   basso, il segnale e' reale; se svanisce, "
              "era rarefazione.")
    return oss - mu, r


def main():
    d, n_sez = carica()
    mappa, (q1, q2) = strati(n_sez)
    print(f"   terzili di ampiezza: <={q1:.0f}, {q1:.0f}-{q2:.0f}, >{q2:.0f}")

    casi = [
        ("ncomp5", "w_fam", "per famiglia  [LA MISURA BUONA]"),
        ("ncomp5", None, "per persona   [riproduce la v1]"),
        ("relpar", None, "per persona"),
    ]
    esiti = {}

    for y, peso, nota in casi:
        mq, ms = (MIN_QUART_F, MIN_SEZ_F) if peso else (MIN_QUART_P, MIN_SEZ_P)
        print("\n" + "=" * 72)
        print(f"M4 — `{y}` ({d[y].nunique()} modalita')   {nota}")
        print("=" * 72)

        na, _ = blocco(m4a, d, y, peso, (mq,), "M4a  comune -> quartiere")
        nb, rb = blocco(m4b, d, y, peso, (mq, ms),
                        "M4b  quartiere -> sezione", mappa)
        esiti[(y, nota)] = (na, nb)

        if na and nb and na > 1e-9:
            rap = nb / na
            print(f"\n   RAPPORTO M4b/M4a = {rap:.2f}")
            if rap < 0.3:
                print("   -> la sezione aggiunge poco: basta la "
                      "distribuzione di quartiere.")
            elif rap > 0.8:
                print("   -> la sezione porta quanto il quartiere: servono "
                      "vincoli per sezione.")
            else:
                print("   -> zona intermedia: guardare i terzili e la "
                      "tabella per quartiere.")

        if not rb.empty and rb.TVD.notna().any():
            v = rb.dropna(subset=["TVD"])
            print("\n   scarto medio per quartiere (pesato):")
            print((v.groupby("quartiere")
                    .apply(lambda g: np.average(g.TVD, weights=g.n))
                    .sort_values(ascending=False).round(3)).to_string())

    print("\n" + "=" * 72)
    print("riepilogo")
    print("=" * 72)
    for (y, nota), (na, nb) in esiti.items():
        a = f"{na:+.4f}" if na is not None else "n/d"
        b = f"{nb:+.4f}" if nb is not None else "n/d"
        r = f"{nb / na:.2f}" if (na and nb and na > 1e-9) else "n/d"
        print(f"   {y:8s} {nota:34s} M4a {a}  M4b {b}  rapporto {r}")
    print("\n   v1 (per persona): ncomp5 1,39 · relpar 0,64.")
    print("   Se la pesatura per famiglia cambia il VERSO della conclusione, "
          "e' la\n   riga per famiglia a valere: il vincolo dell'assemblaggio "
          "e' sulle\n   famiglie, non sulle persone.")


if __name__ == "__main__":
    main()
