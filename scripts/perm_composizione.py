"""
perm_composizione.py — quanto segnale COMPOSITIVO cattura la partizione in
zone, al netto del rumore multinomiale delle sezioni?

Domanda
-------
Sapendo la zona, quanto so in piu' sulla PROVENIENZA di uno straniero, oltre
a cio' che gia' so dal fatto che le zone contengono QUANTITA' diverse di
stranieri? Quantita' e composizione operano a scale spaziali diverse: questo
script misura solo la seconda.

Il nullo
--------
Per ogni sezione si tiene FISSO il numero di stranieri N_s e si riestrae la
loro provenienza da una multinomiale con la composizione cittadina:

    n_s* ~ Multinomial(N_s, p_comune)

Cosi' la struttura di quantita' entra identica nel nullo e nell'osservato, e
cio' che resta e' composizione pura. Il nullo genera automaticamente il
pavimento di rumore: con poche unita' per sezione le zone differiscono anche
sotto indipendenza perfetta, e di quanto lo si MISURA invece di assumerlo.

Per confronto si calcola anche il nullo per permutazione delle etichette di
zona, che distrugge quantita' E composizione insieme: la differenza fra i due
nulli e' essa stessa informativa.

Statistiche
-----------
    I(Z;K)  informazione mutua zona-origine, in nat. E' letteralmente
            "quanto la zona dice sull'origine", cioe' la quantita' operativa
            del conditioner geografico. Attesa sotto indipendenza:
            E[I] ~ (Z-1)(K-1)/(2N), che rende esplicita la dipendenza dal
            numero di celle.
    SSW/SSB rapporto di varianza compositiva within/between, ponderato per
            numerosita'. E' la metrica usata in precedenza: si riporta per
            continuita', normalizzata contro lo stesso nullo.

Ogni statistica va letta come ECCESSO sul nullo, mai in valore assoluto.

Nota sull'IPF
-------------
Questo test va eseguito A MONTE dell'IPF, sui dati di sezione grezzi. L'IPF
preserva esattamente gli odds ratio del seed (Deming-Stephan): non puo'
creare ne' distruggere associazione zona-origine, cambia solo i livelli.
Quindi l'associazione misurata qui e' quella che il pipeline trasporta fino
ai vincoli. Il rapporto di varianza, essendo funzione delle proporzioni e non
degli odds ratio, NON gode della stessa invarianza.

Uso
---
    python perm_composizione.py 039014
    python perm_composizione.py 017029 --level COM_ASC1 -B 2000
    python perm_composizione.py 037006 --level COM_ASC2
    python perm_composizione.py 036023 --gruppi "UE=ST17,ST18;NONUE=ST20,ST21"

ATTENZIONE: le colonne di default (ST17/ST18 = UE, ST20/ST21 = non UE) sono
quelle usate da assign_nationality.py. VERIFICARLE sul tracciato prima di
usare i risultati: se la semantica fosse diversa, il test gira lo stesso ma
misura un'altra cosa.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

import gsp_common as G

GRUPPI_DEFAULT = "UE=ST17,ST18;NONUE=ST20,ST21"


# ----------------------------------------------------------------------
# I/O
# ----------------------------------------------------------------------

def path_sezioni(comune: str) -> str:
    if hasattr(G, "path_sezioni"):
        try:
            p = G.path_sezioni(comune)
            if os.path.exists(p):
                return p
        except Exception:
            pass
    cand = sorted(glob.glob(os.path.join(G.SUBMUN, f"*_sezioni_*.csv")))
    sys.exit(f"CSV sezioni non risolto per {comune}. Indicare --file. "
             f"Presenti in {G.SUBMUN}: {[os.path.basename(x) for x in cand]}")


def parse_gruppi(spec: str) -> dict[str, list[str]]:
    out = {}
    for blocco in spec.split(";"):
        if not blocco.strip():
            continue
        nome, cols = blocco.split("=")
        out[nome.strip()] = [c.strip() for c in cols.split(",") if c.strip()]
    return out


def carica(comune, file_arg, level, gruppi):
    f = file_arg or path_sezioni(comune)
    if not os.path.exists(f):
        sys.exit(f"File sezioni assente: {f}")
    print(f"[load] {os.path.basename(f)}")
    d = pd.read_csv(f, low_memory=False)

    attese = [c for cols in gruppi.values() for c in cols] + [level]
    mancanti = [c for c in attese if c not in d.columns]
    if mancanti:
        sys.exit(f"Colonne assenti: {mancanti}\n"
                 f"  presenti (ST*): "
                 f"{sorted(c for c in d.columns if str(c).startswith('ST'))}")

    z = pd.to_numeric(d[level], errors="coerce").fillna(0).astype("int64")
    N = np.column_stack([
        pd.to_numeric(d[cols].sum(axis=1), errors="coerce").fillna(0).values
        for cols in gruppi.values()
    ]).astype(np.int64)

    tot = N.sum(axis=1)
    tieni = (z != 0) & (tot > 0)
    print(f"[load] {int(tieni.sum()):,} sezioni con stranieri e zona valida "
          f"(su {len(d):,}); {int(tot[tieni].sum()):,} stranieri, "
          f"{len(gruppi)} gruppi di origine")
    return z.values[tieni], N[tieni]


# ----------------------------------------------------------------------
# Statistiche
# ----------------------------------------------------------------------

def tabella_zona(z_codes, z_index, N):
    """Aggrega le sezioni in una tabella (Z x K)."""
    T = np.zeros((len(z_index), N.shape[1]))
    np.add.at(T, z_codes, N)
    return T


def mutual_info(T):
    """I(Z;K) in nat, dalla tabella di contingenza (Z x K)."""
    n = T.sum()
    if n <= 0:
        return 0.0
    p = T / n
    pz = p.sum(axis=1, keepdims=True)
    pk = p.sum(axis=0, keepdims=True)
    den = pz * pk
    m = (p > 0) & (den > 0)
    return float((p[m] * np.log(p[m] / den[m])).sum())


def entropia(N):
    """H(K) in nat: incertezza sull'origine ignorando la geografia.
    E' il denominatore che rende I(Z;K) interpretabile come frazione."""
    p = N.sum(axis=0) / N.sum()
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())


def bias_analitico(n_gruppi, K, n):
    """E[I] sotto indipendenza ~ (G-1)(K-1)/2n. Validata sui cinque casi
    reali: scarto < 10% dalla mediana simulata in ogni citta'."""
    return (n_gruppi - 1) * (K - 1) / (2 * n)


def soffitto_sezioni(N, B, rng):
    """I(S;K) con S = sezione: tetto del segnale spaziale disponibile.

    Il bias qui e' grande — con ~1600 sezioni e ~28k stranieri vale ~0.029
    nat, venti volte l'I(Z;K) osservato — quindi la correzione NON e'
    opzionale: senza, I(S;K) e' quasi tutto rumore multinomiale.
    """
    s = np.arange(len(N))
    oss = mutual_info(tabella_zona(s, s, N))
    tot = N.sum(axis=1)
    p = N.sum(axis=0) / N.sum()
    null = np.array([mutual_info(tabella_zona(s, s, rng.multinomial(tot, p)))
                     for _ in range(B)])
    return oss, float(np.median(null))


def var_ratio(z_codes, z_index, N):
    """SSW/SSB sulle composizioni di sezione, ponderato per numerosita'."""
    tot = N.sum(axis=1, keepdims=True)
    q = N / tot                                   # composizione di sezione
    p = N.sum(axis=0) / N.sum()                   # composizione comunale

    T = tabella_zona(z_codes, z_index, N)
    Wz = T.sum(axis=1, keepdims=True)
    pz = np.divide(T, Wz, out=np.zeros_like(T), where=Wz > 0)

    ssb = float((Wz.ravel() * ((pz - p) ** 2).sum(axis=1)).sum())
    ssw = float((tot.ravel() * ((q - pz[z_codes]) ** 2).sum(axis=1)).sum())
    return (ssw / ssb) if ssb > 0 else np.inf


def statistiche(z_codes, z_index, N):
    return {"I": mutual_info(tabella_zona(z_codes, z_index, N)),
            "ratio": var_ratio(z_codes, z_index, N)}


# ----------------------------------------------------------------------
# Nulli
# ----------------------------------------------------------------------

def nullo_multinomiale(z_codes, z_index, N, B, rng):
    """Tiene fissi gli stranieri per sezione, riestrae solo l'origine."""
    tot = N.sum(axis=1)
    p = N.sum(axis=0) / N.sum()
    out = []
    for _ in range(B):
        Ns = rng.multinomial(tot, p)
        out.append(statistiche(z_codes, z_index, Ns))
    return pd.DataFrame(out)


def nullo_permutazione(z_codes, z_index, N, B, rng):
    """Rimescola le etichette di zona: distrugge quantita' E composizione."""
    out = []
    zc = z_codes.copy()
    for _ in range(B):
        rng.shuffle(zc)
        out.append(statistiche(zc, z_index, N))
    return pd.DataFrame(out)


# ----------------------------------------------------------------------

def riporta(nome, oss, null, verso="alto"):
    """L'eccesso e' centrato sulla MEDIANA del nullo, non sulla media: la
    distribuzione nulla di SSW/SSB e' a coda pesante (SSB puo' finire vicino
    a zero) e la sua media e' dominata dagli outlier. Verificato su dati
    sintetici generati dal nullo: osservato 780.9, media nulla 1764,
    mediana nulla 858. Su I(Z;K) media e mediana distano il 20%."""
    mu, med, sd = null.mean(), null.median(), null.std(ddof=1)
    z = (oss - mu) / sd if sd > 0 else np.nan
    if verso == "alto":
        p = (1 + (null >= oss).sum()) / (1 + len(null))
    else:
        p = (1 + (null <= oss).sum()) / (1 + len(null))
    rap = oss / med if med != 0 else np.nan
    print(f"  {nome:22s} oss {oss:10.4f} | nullo med {med:9.4f} "
          f"(media {mu:9.4f}) | eccesso {rap:6.2f}x | z {z:7.1f} | p {p:.4f}")
    return {"stat": nome, "oss": oss, "null_med": med, "null_mean": mu,
            "null_sd": sd, "eccesso": rap, "z": z, "p": p}


def main(comune, file_arg, level, gruppi_spec, B, seed, out_csv):
    gruppi = parse_gruppi(gruppi_spec)
    z, N = carica(comune, file_arg, level, gruppi)

    z_index = np.unique(z)
    z_codes = np.searchsorted(z_index, z)
    Z, K, n = len(z_index), N.shape[1], int(N.sum())
    print(f"[cfg]  {Z} zone | {K} gruppi | {n:,} stranieri | "
          f"{len(z):,} sezioni | mediana {np.median(N.sum(axis=1)):.0f} "
          f"stranieri/sezione")
    oss = statistiche(z_codes, z_index, N)
    rng = np.random.default_rng(seed)

    H = entropia(N)
    bias_Z = bias_analitico(Z, K, n)
    I_corr = oss["I"] - bias_Z
    print(f"[cfg]  H(K) = {H:.4f} nat | bias analitico = {bias_Z:.6f} nat")
    print(f"[cfg]  I(Z;K) = {oss['I']:.6f} -> corretta {I_corr:.6f} nat "
          f"= {100 * I_corr / H:.2f}% di H(K)")

    B_s = max(B // 4, 50)
    print(f"\n[soffitto] I(S;K) a livello di sezione ({B_s} repliche)")
    I_S, I_S_null = soffitto_sezioni(N, B_s, rng)
    I_S_corr = I_S - I_S_null
    quota = I_corr / I_S_corr if I_S_corr > 0 else np.nan
    print(f"  I(S;K) = {I_S:.6f} | nullo {I_S_null:.6f} -> corretta "
          f"{I_S_corr:.6f} nat = {100 * I_S_corr / H:.2f}% di H(K)")
    if I_S_corr <= 0:
        print("  !! I(S;K) corretta <= 0: nessun segnale compositivo oltre il "
              "rumore nemmeno a livello di sezione. La domanda sulla quota "
              "trattenuta e' mal posta (non si trattiene una frazione di zero).")
    else:
        print(f"  QUOTA TRATTENUTA dalla zonizzazione: "
              f"I(Z;K)/I(S;K) = {100 * quota:.1f}%")

    print(f"\n[nullo A] multinomiale — quantita' FISSA, composizione "
          f"randomizzata ({B} repliche)")
    a = nullo_multinomiale(z_codes, z_index, N, B, rng)
    ra = [riporta("I(Z;K) nat", oss["I"], a["I"], "alto"),
          riporta("SSW/SSB", oss["ratio"], a["ratio"], "basso")]

    print(f"\n[nullo B] permutazione etichette — distrugge anche la "
          f"quantita' ({B} repliche)")
    b = nullo_permutazione(z_codes, z_index, N, B, rng)
    rb = [riporta("I(Z;K) nat", oss["I"], b["I"], "alto"),
          riporta("SSW/SSB", oss["ratio"], b["ratio"], "basso")]

    print("\n[lettura] il nullo A e' quello da citare: isola la composizione.")
    print("          se l'eccesso su A e' ~1 la zona non aggiunge nulla sulla")
    print("          provenienza, anche se separa bene le quantita'.")

    if out_csv:
        df = pd.DataFrame(ra + rb)
        df.insert(0, "nullo", ["A"] * len(ra) + ["B"] * len(rb))
        df.insert(0, "n_stranieri", n)
        df.insert(0, "n_zone", Z)
        df.insert(0, "comune", comune)
        df["H_K"] = H
        df["I_Z_corr"] = I_corr
        df["I_S_corr"] = I_S_corr
        df["quota_trattenuta"] = quota
        df.to_csv(out_csv, index=False)
        print(f"\n[done] -> {out_csv}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Test di permutazione sul segnale compositivo di zona.")
    ap.add_argument("comune")
    ap.add_argument("--file", help="CSV sezioni (override)")
    ap.add_argument("--level", default="COM_ASC1")
    ap.add_argument("--gruppi", default=GRUPPI_DEFAULT,
                    help=f"gruppi di origine [{GRUPPI_DEFAULT}]")
    ap.add_argument("-B", type=int, default=1000, help="repliche [1000]")
    ap.add_argument("--seed", type=int, default=20260731)
    ap.add_argument("--out", help="CSV con i risultati")
    x = ap.parse_args()
    main(x.comune.zfill(6), x.file, x.level, x.gruppi, x.B, x.seed, x.out)
