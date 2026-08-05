"""Distanza in variazione totale, e il criterio di selezione delle
variabili che ne discende.

    import gsp.tvd as T

    T.tvd(a, b)                          # due composizioni
    T.profilo(d, "ateco", ["titolo", "sesso"], peso="val")
    T.indipendenza(d, "ateco", "profilo", peso="val")
    T.partizione(d, "profilo", foglie={...}, totale="99", peso="val")

MODULO INDIPENDENTE. Non importa nulla di GSP: non conosce i comuni, non
sa cosa sia una popolazione sintetica, non legge il registro delle
fonti. Sta in `src/gsp/` per comodita' di import, ma il giorno che serve
allegarlo a un articolo si stacca copiando un file.


LA DISTANZA IN VARIAZIONE TOTALE

Per due distribuzioni P e Q sullo stesso supporto,

    TVD(P, Q) = (1/2) * somma_x |P(x) - Q(x)|

cioe' la meta' della distanza in norma L1. Il fattore un mezzo la porta
nell'intervallo [0, 1], e l'interpretazione e' quella che serve: la
QUOTA DI MASSA da spostare per trasformare una distribuzione nell'altra.

Si preferisce a Hellinger, Jensen-Shannon o chi quadro per una ragione
pratica: «una scheda su cinque sara' sbagliata» e' direttamente la
quantita' che interessa a chi guarda il risultato, senza passare per una
scala che va interpretata.


IL CRITERIO

Data una variabile candidata X e un insieme C di attributi gia' presenti
in un modello congiunto, per ogni sottoinsieme S ⊆ C si misura

    d(S) = TVD( P(X | S), P(X) )

  - d grande per un S DISPONIBILE a valle -> la variabile si puo'
    derivare: il condizionamento cattura cio' che serve;
  - d grande solo per un S NON disponibile a valle (tipicamente la
    geografia fine) -> deve stare nel modello congiunto;
  - d piccolo per ogni S -> quasi indipendente, si assegna senza
    condizionamento.

Il costo dell'errore non e' simmetrico: aggiungere una variabile al
modello congiunto moltiplica lo spazio degli stati e puo' introdurre
zeri strutturali che rendono riducibile la catena di campionamento,
mentre lasciarla fuori costa solo l'informazione che porta.


IL CONTROLLO CHE IL CRITERIO RICHIEDE

    Una TVD calcolata su supporti diversi non e' una misura.

Su fonti censuarie reali questo errore si e' presentato QUATTRO VOLTE in
due giorni, e ogni volta ha prodotto valori plausibili e privi di
significato:

  1. titoli di studio con UNA sola sezione pubblicata confrontati con
     composizioni su ventuno: TVD 0,954, vicinissima al massimo teorico,
     che sembrava un segnale fortissimo ed era il nulla;
  2. classificazione ATECO che mescola sezioni (A-U) e aggregati
     (`0011` totale industria, `0012` totale servizi): la composizione
     sommava a piu' di uno;
  3. profili professionali con una gerarchia NON dichiarata dal
     codebook — la colonna che sembra il padre e' l'ordinamento — dove
     la somma dei codici presenti faceva il 140% del totale;
  4. due livelli di dettaglio che non coincidono fra la tavola dei
     totali e quella degli incroci: escludere un aggregato perdeva il
     10% delle unita'.

Per questo `tvd()` RIFIUTA di misurare quando i supporti divergono
troppo, invece di restituire un numero. E `partizione()` esiste apposta
per il controllo da fare PRIMA.
"""

from itertools import combinations

import numpy as np
import pandas as pd

# Sotto questa quota di supporto comune la distanza non si calcola. La
# soglia e' arbitraria ma la scelta di averne una non lo e': i quattro
# casi sopra avevano tutti supporto comune sotto la meta'.
SUPPORTO_MINIMO = 0.5


# ------------------------------------------------------------- distanza

def tvd(a, b, supporto_minimo=SUPPORTO_MINIMO, normalizza=True):
    """Distanza in variazione totale fra due composizioni.

    `a` e `b` sono Series indicizzate sulle modalita'. Con
    `normalizza=True` vengono riscalate a somma uno: passare conteggi
    grezzi e' quindi lecito.

    Solleva `ValueError` se i supporti condividono meno di
    `supporto_minimo` delle modalita' complessive. Non e' pedanteria:
    confrontare una composizione definita su una modalita' con una
    definita su ventuno produce sempre un valore vicino a 1, che sembra
    un segnale ed e' un artefatto.
    """
    a, b = pd.Series(a).astype(float), pd.Series(b).astype(float)
    a, b = a[a.notna()], b[b.notna()]
    if normalizza:
        if a.sum() <= 0 or b.sum() <= 0:
            raise ValueError("una delle due composizioni ha massa nulla")
        a, b = a / a.sum(), b / b.sum()

    unione = a.index.union(b.index)
    comune = a.index.intersection(b.index)
    if len(unione) == 0:
        raise ValueError("supporti vuoti")
    if len(comune) < supporto_minimo * len(unione):
        raise ValueError(
            f"supporti troppo diversi: {len(a)} e {len(b)} modalita', "
            f"{len(comune)} in comune su {len(unione)}. Una distanza fra "
            f"composizioni definite su insiemi diversi non e' una misura. "
            f"Contare i supporti prima di confrontare.")
    return 0.5 * float(np.abs(a.reindex(unione, fill_value=0.0)
                              - b.reindex(unione, fill_value=0.0)).sum())


def composizione(d, variabile, peso=None, filtro=None):
    """La distribuzione di `variabile`, eventualmente su un sottoinsieme.

    `peso` e' la colonna dei conteggi; senza, si contano le righe.
    """
    s = d
    if filtro:
        for c, v in filtro.items():
            vals = v if isinstance(v, (list, tuple, set)) else [v]
            s = s[s[c].isin(list(vals))]
    if s.empty:
        return pd.Series(dtype=float)
    if peso:
        x = s.groupby(variabile)[peso].sum()
    else:
        x = s.groupby(variabile).size().astype(float)
    return x[x > 0]


# -------------------------------------------------------------- criterio

# Codici che nelle classificazioni ufficiali indicano il TOTALE. Non
# sono uniformi nemmeno dentro la stessa tavola — `ALL` per una
# dimensione, `99` per un'altra, `0010` per una terza — e confrontare la
# composizione del totale con se' stessa da' zero: non significa nulla ma
# abbassa il minimo e la mediana, facendo sembrare debole un
# condizionante forte.
TOTALI = {"ALL", "TOTAL", "TOT", "99", "9", "999", "0", "totale", "total"}

# ATTENZIONE alle classificazioni che NON sono partizioni. `TOTALI`
# esclude il totale esplicito, ma non i livelli intermedi: la dimensione
# dell'eta' in DICA_CARATT_ATTL ha 82 modalita' che si sovrappongono —
# anni singoli (`Y15`), quinquennali (`Y15-19`), decennali (`Y20-29`) e
# aperti (`Y30-54`) tutti insieme. Misurare su tutte e 82 mescola cose
# incomparabili e produce una mediana che non significa niente.
#
# Non e' automatizzabile: quali modalita' formino una partizione dipende
# dalla classificazione, e va deciso da chi conosce la fonte. Ma va
# DECISO, non subito: passare `ignora` o filtrare a monte.


def profilo(d, variabile, condizionanti, peso=None, base=None,
            min_unita=0, ignora=None, auto_totali=True, stampa=True,
            supporto_minimo=SUPPORTO_MINIMO):
    """d(S) per ogni modalita' di ogni condizionante, separatamente.

    Restituisce una riga per (condizionante, modalita') con la distanza
    dalla composizione marginale e la numerosita', che serve a
    distinguere il segnale dal rumore: una TVD di 0,4 su cinquanta unita'
    non dice nulla.

    `min_unita` esclude le celle troppo sottili invece di lasciarle
    inquinare la lettura.

    `ignora` e' {colonna: [modalita']} da escludere. Con
    `auto_totali=True` i codici di TOTALI vengono esclusi da soli:
    confrontare il totale con se' stesso da' zero, che sporca il minimo e
    la mediana senza dire niente. Metterlo a False se una modalita'
    legittima si chiamasse `9` o `99`.
    """
    ign = {c: {str(x) for x in v} for c, v in (ignora or {}).items()}
    marg = base if base is not None else composizione(d, variabile, peso)
    righe = []
    for c in condizionanti:
        for v in sorted(d[c].dropna().unique()):
            if str(v) in ign.get(c, set()):
                continue
            if auto_totali and str(v) in TOTALI:
                continue
            s = composizione(d, variabile, peso, {c: v})
            n = float(s.sum())
            if s.empty or n < min_unita:
                continue
            try:
                x = tvd(s, marg, supporto_minimo=supporto_minimo)
                nota = ""
            except ValueError as e:                          # noqa: PERF203
                x, nota = np.nan, str(e).split(".")[0]
            righe.append({"condizionante": c, "modalita": str(v),
                          "n": int(n), "supporto": int(len(s)),
                          "TVD": None if np.isnan(x) else round(x, 3),
                          "nota": nota})
    r = pd.DataFrame(righe)
    if stampa and len(r):
        print(f"d(S) = TVD( P({variabile} | S), P({variabile}) )  ·  "
              f"marginale su {len(marg)} modalita'\n")
        print(r.to_string(index=False))
        v = r.TVD.dropna()
        if len(v):
            print(f"\n   intervallo {v.min():.3f} – {v.max():.3f}")
        saltate = r.nota.astype(bool).sum()
        if saltate:
            print(f"   !! {saltate} celle non misurate: supporti diversi. "
                  f"Guardare la colonna `supporto`.")
    return r


def riassunto(d, variabile, condizionanti, peso=None, min_unita=0,
              ignora=None, auto_totali=True, stampa=True):
    """Una riga per condizionante: l'intervallo delle distanze.

    E' la tabella che serve a DECIDERE, mentre `profilo` serve a capire
    da dove viene il numero. Ordinata per distanza massima decrescente:
    in cima la variabile su cui condizionare, in fondo quella che si puo'
    ignorare.
    """
    p = profilo(d, variabile, condizionanti, peso, min_unita=min_unita,
                ignora=ignora, auto_totali=auto_totali, stampa=False)
    if p.empty:
        # nessuna cella misurabile: o il filtro a monte ha svuotato tutto,
        # o `min_unita` e' troppo alto. Restituire un frame vuoto con le
        # colonne giuste e' meglio di un KeyError su `condizionante` —
        # l'errore va detto, non fatto esplodere altrove.
        if stampa:
            print(f"nessuna cella misurabile per `{variabile}`: "
                  f"controllare il filtro a monte e `min_unita`")
        return pd.DataFrame(columns=["condizionante", "modalita", "TVD_min",
                                     "TVD_mediana", "TVD_max",
                                     "non_misurate"])
    righe = []
    for c, g in p.groupby("condizionante"):
        v = g.TVD.dropna()
        if not len(v):
            continue
        righe.append({"condizionante": c, "modalita": len(g),
                      "TVD_min": round(float(v.min()), 3),
                      "TVD_mediana": round(float(v.median()), 3),
                      "TVD_max": round(float(v.max()), 3),
                      "non_misurate": int(g.TVD.isna().sum())})
    r = (pd.DataFrame(righe).sort_values("TVD_max", ascending=False)
         .reset_index(drop=True))
    if stampa and len(r):
        print(f"quanto ciascuna variabile sposta la composizione di "
              f"`{variabile}`\n")
        print(r.to_string(index=False))
        print("\n   in cima la variabile su cui condizionare, in fondo "
              "quella\n   che si puo' ignorare. Il confronto e' fra le "
              "colonne, non\n   con una soglia assoluta.")
        # la maggioranza delle celle non misurabile: il numero che
        # resta e' su una cella o due, e non e' un profilo
        pochi = r[r.non_misurate > r.modalita / 2]
        if len(pochi):
            for _, x in pochi.iterrows():
                print(f"\n   !! {x.condizionante}: {x.non_misurate} celle "
                      f"su {x.modalita} non misurabili.\n      Il valore "
                      f"riportato viene da {x.modalita - x.non_misurate} "
                      f"cella/e. Non e' «questa variabile\n      non "
                      f"conta», e' «la fonte non la incrocia»: due cose "
                      f"diverse,\n      e la seconda va dichiarata invece "
                      f"che confusa con la prima.")
    return r


def indipendenza(d, x, y, peso=None, filtro=None, stampa=True):
    """TVD( P(x,y), P(x)·P(y) ): le due variabili si possono derivare
    separatamente?

    Se la distanza e' piccola, si', e ciascuna col suo condizionamento
    migliore. Se e' grande vanno estratte INSIEME, anche a costo di un
    condizionamento peggiore per entrambe — perche' le combinazioni
    impossibili si vedono, mentre una marginale un po' storta no.
    """
    s = d
    if filtro:
        for c, v in filtro.items():
            vals = v if isinstance(v, (list, tuple, set)) else [v]
            s = s[s[c].isin(list(vals))]
    if s.empty:
        raise LookupError("nessuna riga dopo il filtro")
    P = (s.pivot_table(index=x, columns=y, values=peso, aggfunc="sum")
         if peso else pd.crosstab(s[x], s[y]).astype(float))
    P = P.fillna(0.0)
    tot = float(P.values.sum())
    if tot <= 0:
        raise ValueError("massa nulla")
    P = P / tot
    ind = np.outer(P.sum(axis=1), P.sum(axis=0))
    v = 0.5 * float(np.abs(P.values - ind).sum())
    if stampa:
        print(f"TVD( P({x},{y}), P({x})·P({y}) ) = {v:.3f}   "
              f"({P.shape[0]}×{P.shape[1]}, {tot:,.0f} unita')"
              .replace(",", "."))
        print("   grande -> estrarre la coppia INSIEME; "
              "piccola -> separatamente")
    return v


# ------------------------------------------------------------ partizione

def partizione(d, colonna, foglie, totale, peso, gruppi=None,
               tolleranza=0.5, stampa=True):
    """Le foglie ricostruiscono il totale?

    Il controllo da fare PRIMA di qualunque distanza. Le classificazioni
    ufficiali contengono aggregati insieme alle foglie — «totale
    industria» accanto alle sezioni, «indipendenti» accanto a
    «lavoratore in proprio» — e la gerarchia spesso NON e' dichiarata nel
    codebook. Sommarli conta due volte le stesse unita'.

    `gruppi` ripete il controllo per ogni valore di quelle colonne: una
    partizione che torna a livello nazionale puo' non tornare su un
    territorio, e scoprirlo dopo costa molto piu' che scoprirlo qui.
    """
    def _una(s, et):
        tot = float(s.loc[s[colonna] == totale, peso].sum())
        fog = float(s.loc[s[colonna].isin(list(foglie)), peso].sum())
        if tot <= 0:
            return None
        return {"gruppo": et, "totale": int(tot), "somma_foglie": int(fog),
                "scarto_pc": round((fog - tot) / tot * 100, 2)}

    righe = []
    if gruppi:
        for chiave, g in d.groupby(list(gruppi)):
            r = _una(g, str(chiave))
            if r:
                righe.append(r)
    else:
        r = _una(d, "tutto")
        if r:
            righe.append(r)
    t = pd.DataFrame(righe)
    if stampa and len(t):
        print(f"le foglie di `{colonna}` ricostruiscono `{totale}`?\n")
        print(t.to_string(index=False))
        male = t[t.scarto_pc.abs() > tolleranza]
        if len(male):
            print(f"\n   !! {len(male)} gruppi oltre {tolleranza}%: "
                  f"l'insieme delle foglie\n      non e' lo stesso "
                  f"ovunque, o la gerarchia e' diversa da\n      come la "
                  f"si e' ricostruita")
        else:
            print(f"\n   ogni gruppo torna entro {tolleranza}%")
    return t


def foglie_candidate(d, colonna, totale, peso, max_combinazioni=2000):
    """Cerca quali sottoinsiemi ricostruiscono il totale.

    Quando la gerarchia non e' dichiarata — e capita spesso — si puo'
    ricostruirla dai conteggi: si prova ogni sottoinsieme dei codici e si
    tengono quelli che sommano al totale entro lo 0,5%.

    Puo' restituirne PIU' DI UNO: sono i livelli diversi dello stesso
    albero. Su un caso reale ne sono usciti tre, e disegnavano la
    gerarchia completa:
        99 = 9 + 22 + 42 · 22 = 41 + 15 + 18 + 19 · 41 = 11 + 12
    Sceglierne uno e' una decisione di dettaglio, non una deduzione.
    """
    s = d.groupby(colonna)[peso].sum()
    tot = float(s.get(totale, 0.0))
    if tot <= 0:
        raise LookupError(f"nessun totale `{totale}` in `{colonna}`")
    cod = [c for c in s.index if c != totale]
    if 2 ** len(cod) > max_combinazioni:
        # troppi codici per la forza bruta: si prova solo con quelli che
        # da soli non superano il totale, che e' quasi sempre abbastanza
        cod = [c for c in cod if s[c] <= tot * 1.001]
    fuori = []
    for k in range(1, len(cod) + 1):
        for comb in combinations(cod, k):
            v = float(sum(s[c] for c in comb))
            if abs(v - tot) < tot * 0.005:
                fuori.append({"foglie": sorted(comb), "somma": int(v),
                              "n": k})
        if len(fuori) > 20:
            break
    return sorted(fuori, key=lambda x: -x["n"])
