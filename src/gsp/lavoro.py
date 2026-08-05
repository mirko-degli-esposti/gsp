"""Settore di attività e posizione professionale, dal censimento 2011.

    import gsp.lavoro as L

    L.verifica()
    L.repertorio(sesso="M", comune="034027")
    L.lavoro_agente(uid, condizione="occupato", sesso="M", comune="034027")

PERCHE' A VALLE E NON NEL MaxEnt. Il livello K10C aggiunge `settore` allo
spazio degli stati, lo condiziona sul SESSO e paga tre prezzi: 37 milioni
di stati, una catena di Gibbs riducibile a lambda* per gli zeri
strutturali del blocco MC, e 3.417 individui impossibili su Brescia.
La derivazione a valle condiziona su sesso E comune, non tocca il solver,
e tiene la coppia congiunta. Misure e ragionamento in
note/nota_settore_economico_v3.md.

LA COPPIA SI ESTRAE INSIEME. `ateco` e `profilo` sono fortemente
dipendenti: la distanza fra la distribuzione congiunta osservata e il
prodotto delle sue marginali e' 0,149 a Parma, 0,166 a Bologna, 0,156 in
Emilia-Romagna, 0,138 in Lombardia, 0,156 in Italia. Stabile su cinque
territori, quindi struttura e non rumore. Estrarli separatamente
produrrebbe dirigenti in agricoltura e coadiuvanti familiari nella
pubblica amministrazione. E' la stessa ragione per cui l'hot-deck AVQ
copia il vettore intero invece di campionare variabile per variabile.

NIENTE TITOLO DI STUDIO, e non per scelta. La tavola pubblica l'incrocio
settore x titolo a livello comunale SOLO per la sezione A, agricoltura
(verificato 5/8/2026). Sarebbe stato il condizionamento piu' informativo
— TVD 0,105-0,390 — ed e' la perdita che fa piu' male. La §9 della nota
registra la via per recuperarlo con una riponderazione.

NIENTE ETA'. Fra i 30 e i 55 anni non porta nulla (TVD 0,03-0,08); conta
solo agli estremi, dove i ventenni si concentrano in commercio e
ristorazione. Il «non serve nel mezzo» e' esso stesso un risultato.
"""

import io
import os
import zipfile

import numpy as np
import pandas as pd

import gsp.common as G
from gsp import fonti as F

FONTE = "cens2011_caratt_attl"
DENTRO_ZIP = ("CSV - DATI SOLO CODICI - DATA ONLY CODES/"
              "DICA_CARATT_ATTL-data.csv")

# Il file dati e' UTF-8 senza intestazione, come DICA_TITSTUDIO. Le
# quattordici dimensioni vanno identificate dai VALORI, confrontandoli con
# le codelist del pacchetto METADATA: assegnarle a occhio ha gia' prodotto
# un errore, `OCCUPAZIONE` letta come `ATECO_2007` (§4 della nota).
COLONNE = ["terr", "tipo", "sesso", "eta", "statciv", "iso", "titolo",
           "profilo", "occup", "regime", "ateco", "caratt", "durata",
           "anno", "val", "_x"]

# I codici «totale» di ciascuna dimensione. Non sono uniformi — chi lo
# desse per scontato filtrerebbe via tutto: `ALL` per occupazione e
# cittadinanza, `99` per profilo e titolo, `0010` per ateco, `9` per
# sesso e regime, `TOTAL` per durata.
TOT = {"statciv": "99", "iso": "ALL", "occup": "ALL", "regime": "9",
       "caratt": "9", "durata": "TOTAL", "titolo": "99", "eta": "Y_GE15"}

TOT_ATECO, TOT_PROFILO = "0010", "99"

# I PROFILI FORMANO UN ALBERO CHE IL CODEBOOK NON DICHIARA: la quarta
# colonna sembra un padre ma e' l'ordinamento (10, 20, 30... 430), come
# nel caso dei titoli di studio. La gerarchia va ricostruita dai
# conteggi, e a Parma (5/8/2026) e' questa:
#
#     99 totale                          81.165
#     ├── 9  dipendenti                  60.806
#     ├── 22 indipendenti                17.407
#     │   ├── 41 imprend. e libero prof.  8.265
#     │   │   ├── 11 imprenditore         2.621
#     │   │   └── 12 libero profess.      5.644
#     │   ├── 15 lavoratore in proprio    7.103
#     │   ├── 18 coadiuvante familiare    1.175
#     │   └── 19 socio di cooperativa       864
#     └── 42 parasubordinato              2.952
#
# Tenere aggregati e componenti insieme conta DUE VOLTE le stesse
# persone: la somma dei nove codici presenti fa il 140% del totale, e
# l'estrazione pescherebbe prevalentemente dagli aggregati perche' sono i
# piu' grossi. Stesso errore dei codici `0010`-`0091` per l'ateco, che il
# filtro `len(codice) == 1` gia' esclude.
#
# DUE INSIEMI DI FOGLIE, e non coincidono.
#
# `11 imprenditore` e `12 libero professionista` esistono SOLO nelle
# righe di totale, non incrociate con l'ateco: nella congiunta compare
# soltanto il loro aggregato `41`. Escluderlo perderebbe 8.265 occupati a
# Parma, il 10% — e infatti il primo tentativo dava 72.896 invece di
# 81.165.
#
# Il livello di dettaglio disponibile non e' quindi lo stesso nei due
# posti: fine nel totale, medio nella congiunta. Distinguerli e' meno
# elegante che avere un insieme solo, ma e' quello che la fonte offre, e
# tenerli uguali significherebbe o perdere il 10% degli occupati o
# contare due volte gli imprenditori.
FOGLIE_CONGIUNTA = {"9", "41", "15", "18", "19", "42"}
FOGLIE_TOTALE = {"9", "11", "12", "15", "18", "19", "42"}

# I sei comuni presenti nella tavola con l'incrocio completo. Gli altri
# cinque ripiegano sulla regione, e il costo NON e' uniforme: Bologna
# dista 0,159 dalla sua regione, Ravenna 0,029. Il ripiego costa poco dove
# il comune e' ordinario e molto dove e' particolare — cioe' proprio dove
# servirebbe.
REGIONE_DI = {
    "034027": "ITD5", "036023": "ITD5", "037006": "ITD5",
    "035033": "ITD5", "039014": "ITD5", "033032": "ITD5",
    "038008": "ITD5", "040012": "ITD5", "099014": "ITD5",
    "037021": "ITD5", "017029": "ITC4",
}

SESSO_CENS = {"M": "1", "F": "2", None: "9"}

# Universo: solo gli occupati. Per tutti gli altri settore e posizione
# sono `non_applicabile` per COSTRUZIONE, non mancanti — come il missing
# strutturale delle AVQ.
CONDIZIONE_OCCUPATO = {"occupato"}

# Il censimento etichetta le CATEGORIE, non le persone: «dipendenti» è il
# gruppo, ma in una scheda individuale serve il singolare. E alcune voci
# vanno accordate al sesso.
PROFILO_LEGGIBILE = {
    "9":  {"M": "dipendente", "F": "dipendente"},
    "41": {"M": "imprenditore o libero professionista",
           "F": "imprenditrice o libera professionista"},
    "15": {"M": "lavoratore in proprio", "F": "lavoratrice in proprio"},
    "18": {"M": "coadiuvante familiare", "F": "coadiuvante familiare"},
    "19": {"M": "socio di cooperativa", "F": "socia di cooperativa"},
    "42": {"M": "parasubordinato", "F": "parasubordinata"},
}

_cache = {}


# ------------------------------------------------------------- lettura

def _leggi(nome_dim=None):
    """Il file dati, o una codelist del pacchetto METADATA."""
    p = F.path_grezzo(FONTE)
    if nome_dim:
        chiave = ("cb", nome_dim)
        if chiave in _cache:
            return _cache[chiave]
        with zipfile.ZipFile(p) as z:
            t = z.read(f"METADATA/Dim{nome_dim}-data.csv").decode("utf-16")
        d = pd.read_csv(io.StringIO(t), sep="|", header=None, dtype=str,
                        names=["cod", "en", "it", "padre", "ord"])
        _cache[chiave] = d
        return d
    if "dati" in _cache:
        return _cache["dati"]
    with zipfile.ZipFile(p) as z:
        t = z.read(DENTRO_ZIP).decode("utf-8")
    pezzi = []
    for ch in pd.read_csv(io.StringIO(t), sep="|", header=None,
                          names=COLONNE, dtype=str, chunksize=500_000):
        m = (ch.tipo == "EMPLP")
        for c, v in TOT.items():
            m &= (ch[c] == v)
        ch = ch[m & (ch.sesso.isin(["1", "2"])) &
                (ch.ateco.str.len() == 1) &
                (ch.profilo.isin(FOGLIE_CONGIUNTA))]
        if len(ch):
            pezzi.append(ch[["terr", "sesso", "ateco", "profilo", "val"]])
    d = pd.concat(pezzi, ignore_index=True)
    d["val"] = pd.to_numeric(d.val, errors="coerce").fillna(0.0)
    _cache["dati"] = d
    return d


def etichette(dim):
    """{codice: etichetta italiana} per una dimensione."""
    chiave = ("et", dim)
    if chiave not in _cache:
        d = _leggi(dim)
        _cache[chiave] = dict(zip(d.cod.astype(str).str.strip(),
                                  d.it.astype(str).str.strip()))
    return _cache[chiave]


# ------------------------------------------------------------ repertorio

def repertorio(sesso=None, comune=None, territorio=None,
               istruzione=None):
    """(ateco, profilo, peso) per una cella, dalla congiunta.

    La cascata e' comune -> regione -> Italia, e viene dichiarata nella
    colonna `livello` del risultato: chi legge sa a quale risoluzione sta
    guardando invece di doverlo dedurre.
    """
    d = _leggi()
    liv = "comune"
    if territorio is None:
        territorio = comune
    if territorio and territorio not in set(d.terr):
        reg = REGIONE_DI.get(territorio)
        if reg and reg in set(d.terr):
            territorio, liv = reg, "regione"
        else:
            territorio, liv = "IT", "nazionale"
    elif territorio is None:
        territorio, liv = "IT", "nazionale"

    s = d[d.terr == territorio]
    if sesso:
        s = s[s.sesso == SESSO_CENS.get(sesso, "9")]
    if s.empty:
        raise LookupError(f"nessun dato per territorio={territorio}, "
                          f"sesso={sesso}")
    g = (s.groupby(["ateco", "profilo"], as_index=False).val.sum()
         .rename(columns={"val": "peso"}))
    g = g[g.peso > 0].reset_index(drop=True)

    # riponderazione OPZIONALE per titolo di studio: spenta se
    # `istruzione` non e' passata. Vedi il blocco in fondo al modulo per
    # i tre limiti che la rendono una scelta e non un miglioramento.
    if istruzione:
        f = fattore_titolo(istruzione)
        if f:
            g["peso"] = g.peso * g.ateco.map(lambda a: f.get(a, 1.0))
            g = g[g.peso > 0].reset_index(drop=True)
            liv += "+titolo"

    g["livello"] = liv
    g["territorio"] = territorio
    return g


# -------------------------------------------------------------- verifica

def _coerenza():
    """La somma delle foglie ricostruisce il totale, su OGNI territorio?

    L'albero dei profili e' stato ricostruito dai conteggi di Parma. Se
    un altro comune avesse una struttura diversa — o se ISTAT
    ripubblicasse la tavola con codici diversi — la somma non tornerebbe,
    e questo controllo se ne accorgerebbe invece di produrre in silenzio
    una popolazione con i mestieri contati due volte.
    """
    p = F.path_grezzo(FONTE)
    with zipfile.ZipFile(p) as z:
        t = z.read(DENTRO_ZIP).decode("utf-8")
    pezzi = []
    for ch in pd.read_csv(io.StringIO(t), sep="|", header=None,
                          names=COLONNE, dtype=str, chunksize=500_000):
        m = (ch.tipo == "EMPLP") & (ch.sesso == "9") & (ch.ateco == TOT_ATECO)
        for c, v in TOT.items():
            m &= (ch[c] == v)
        ch = ch[m]
        if len(ch):
            pezzi.append(ch[["terr", "profilo", "val"]])
    d = pd.concat(pezzi, ignore_index=True)
    d["val"] = pd.to_numeric(d.val, errors="coerce").fillna(0.0)

    righe = []
    for terr, g in d.groupby("terr"):
        if terr not in set(REGIONE_DI) | set(REGIONE_DI.values()) | {"IT"}:
            continue
        s = g.groupby("profilo").val.sum()
        tot = float(s.get(TOT_PROFILO, 0.0))
        fog = float(sum(s.get(c, 0.0) for c in FOGLIE_TOTALE))
        if tot <= 0:
            continue
        righe.append({"territorio": terr, "totale": int(tot),
                      "somma_foglie": int(fog),
                      "scarto_pc": round((fog - tot) / tot * 100, 2)})
    r = pd.DataFrame(righe).sort_values("territorio")

    # Secondo controllo, su un asse diverso: quanto la CONGIUNTA ricompone
    # del totale. E' quello che ha scoperto la perdita del 10% — il primo
    # controllo tornava a zero perche' guardava le righe di totale, dove
    # `11` e `12` ci sono, mentre la congiunta ne era priva.
    cong = _leggi().groupby("terr").val.sum()
    r["congiunta"] = r.territorio.map(cong).fillna(0).astype(int)
    r["copertura_pc"] = (r.congiunta / r.totale * 100).round(1)
    return r


def verifica(stampa=True):
    """Cosa la tavola sostiene, e quanto costa il ripiego regionale.

    Il controllo che conta e' l'ultimo: la distanza fra la congiunta e il
    prodotto delle marginali. Se fosse piccola si potrebbero derivare
    `ateco` e `profilo` separatamente, con condizionamenti diversi e
    migliori. Non lo e'.
    """
    d = _leggi()
    ea, ep = etichette("ATECO_2007"), etichette("PROFILO_PROF")
    righe = []
    for c, reg in sorted(REGIONE_DI.items()):
        pres = c in set(d.terr)
        r = repertorio(comune=c)
        righe.append({"comune": c, "nome": G.info(c).get("nome", "?"),
                      "nella_tavola": pres, "livello": r.livello.iloc[0],
                      "celle": len(r), "occupati": float(r.peso.sum())})
    t = pd.DataFrame(righe)

    def tvd_indip(terr):
        s = d[d.terr == terr]
        if s.empty:
            return None
        P = s.pivot_table(index="ateco", columns="profilo", values="val",
                          aggfunc="sum").fillna(0.0)
        if P.values.sum() <= 0:
            return None
        P = P / P.values.sum()
        ind = np.outer(P.sum(axis=1), P.sum(axis=0))
        return 0.5 * float(np.abs(P.values - ind).sum())

    def tvd(a, b):
        i = a.index.union(b.index)
        return 0.5 * float(np.abs(a.reindex(i, fill_value=0)
                                  - b.reindex(i, fill_value=0)).sum())

    def comp(terr, col="ateco"):
        s = d[d.terr == terr]
        v = s.groupby(col).val.sum()
        return v / v.sum() if v.sum() else v

    coer = _coerenza()

    if stampa:
        print(f"{len(d):,} righe · {d.ateco.nunique()} sezioni × "
              f"{d.profilo.nunique()} profili × 2 sessi\n"
              .replace(",", "."))
        print(t.to_string(index=False))

        print("\nle FOGLIE ricostruiscono il totale? l'albero dei profili "
              "non e'\ndichiarato dal codebook ed e' stato ricostruito su "
              "Parma:")
        print(coer.to_string(index=False))
        scarsa = coer[coer.copertura_pc < 97]
        if len(scarsa):
            print("\n!! la CONGIUNTA copre meno del 97% del totale: "
                  "mancano profili\n   o sezioni dall'incrocio, e gli "
                  "occupati persi non sono pochi")
            print(scarsa[["territorio", "totale", "congiunta",
                          "copertura_pc"]].to_string(index=False))
        male = coer[coer.scarto_pc.abs() > 0.5]
        if len(male):
            print("\n!! su questi territori la partizione NON torna: "
                  "l'albero dei\n   profili non e' lo stesso ovunque, e "
                  "PROFILO_FOGLIE va rivisto")
            print(male.to_string(index=False))
        else:
            print("   ogni territorio torna entro lo 0,5%")

        print("\ndipendenza fra ateco e profilo — se fosse piccola si "
              "potrebbero\nderivare separatamente. TVD(congiunta, "
              "indipendenza):")
        for terr in ("IT", "ITD5", "ITC4", "034027", "037006"):
            v = tvd_indip(terr)
            if v is not None:
                print(f"   {terr:<8} {v:.3f}")

        print("\ncosto del ripiego regionale — TVD del comune dalla sua "
              "regione:")
        for c, reg in sorted(REGIONE_DI.items()):
            if c not in set(d.terr):
                continue
            v = tvd(comp(c), comp(reg))
            print(f"   {G.info(c).get('nome','?'):<16} {v:.3f}")

        print("\nprofili:")
        for p in sorted(d.profilo.unique()):
            print(f"   {p:<4} {ep.get(p, '?')[:60]}")
    return t


# ------------------------------------------------------------ estrazione

def lavoro_agente(uid, condizione=None, sesso=None, comune=None,
                  istruzione=None, spiega=False):
    """(settore, posizione) per un individuo, deterministico dall'uid.

    La COPPIA si estrae insieme, in un'unica pescata dalla congiunta: e'
    l'unico modo di non produrre dirigenti in agricoltura.

    Canale `lavoro` separato da quelli di `gsp.nomi` e `gsp.istruzione`,
    cosi' correggendo questo raccordo il resto non si rimescola.
    """
    from gsp import nomi as N

    if condizione not in CONDIZIONE_OCCUPATO:
        return (None, None) if not spiega else (None, None, {
            "motivo": "non occupato: settore e posizione sono "
                      "`non_applicabile` per costruzione"})
    d = repertorio(sesso=sesso, comune=comune, istruzione=istruzione)
    rng = N._rng(uid, "lavoro")
    p = d.peso.to_numpy(dtype="float64")
    i = int(rng.choice(len(d), p=p / p.sum()))
    ea, ep = etichette("ATECO_2007"), etichette("PROFILO_PROF")
    sett = ea.get(str(d.ateco.iloc[i]), str(d.ateco.iloc[i]))
    cod_p = str(d.profilo.iloc[i])
    pos = (PROFILO_LEGGIBILE.get(cod_p, {}).get(sesso)
           or ep.get(cod_p, cod_p))
    if spiega:
        return sett, pos, {"livello": d.livello.iloc[0],
                           "territorio": d.territorio.iloc[0],
                           "celle": len(d),
                           "codici": (d.ateco.iloc[i], d.profilo.iloc[i]),
                           "quota": round(float(p[i] / p.sum()), 4)}
    return sett, pos

# --------------------------------------------- riponderazione per titolo
#
# OPZIONALE E SPENTA DI DEFAULT, per tre ragioni misurate.
#
# Il problema che vorrebbe risolvere e' reale: la congiunta e'
# condizionata su sesso e comune, non sul titolo di studio, quindi una
# laureata finisce in agricoltura con la stessa probabilita' di chi ha la
# licenza elementare. Verificato su 600 individui di Parma: le quote per
# settore sono indistinguibili fra i titoli, e le differenze visibili
# sono rumore di campionamento.
#
# La correzione: riscalare la congiunta per il rapporto
# P(ateco|titolo)/P(ateco), che sposta le marginali senza spezzare la
# dipendenza fra settore e profilo.
#
# Ma i tre limiti sono seri e non aggirabili con questa fonte:
#
#   1. la marginale per titolo esiste SOLO A LIVELLO NAZIONALE. A livello
#      regionale e comunale l'incrocio settore x titolo copre la sola
#      sezione A, agricoltura. Si applicherebbe quindi un rapporto
#      nazionale a una congiunta comunale;
#   2. copre 14 sezioni su 21, e le sette mancanti — energia, acqua,
#      trasporti, informazione, immobiliare, attivita' professionali,
#      servizi alle imprese — sono PROPRIO quelle dove i laureati si
#      concentrano. Il fattore resta 1 dove servirebbe di piu';
#   3. NON E' VALIDABILE: il controllo naturale sarebbe confrontare la
#      marginale nazionale con quella regionale, che non esiste.
#
# Corregge quindi una parte dell'errore introducendone uno nuovo di
# entita' ignota. Resta qui, spenta, con `sposta()` per misurare quanto
# cambierebbe: si decide sui numeri, non per principio.

TOT_TITOLO = "99"

# titolo della popolazione -> codice TITOLO_STUDIO della tavola.
# Le sei categorie di `istruzione` non hanno corrispondenza uno-a-uno:
# `laurea_o_its` copre sia il diploma universitario del vecchio
# ordinamento (42) sia la triennale (45), e si sceglie la piu' numerosa.
TITOLO_CENS = {
    "nessun_titolo": "1",
    "elementare":    "2",
    "media":         "29",
    "diploma":       "31",
    "laurea_o_its":  "45",
    "post_laurea":   "47",
}


def _marginale_titolo():
    """P(ateco | titolo) nazionale, dalle righe con profilo al totale."""
    if "marg" in _cache:
        return _cache["marg"]
    p = F.path_grezzo(FONTE)
    with zipfile.ZipFile(p) as z:
        t = z.read(DENTRO_ZIP).decode("utf-8")
    pezzi = []
    for ch in pd.read_csv(io.StringIO(t), sep="|", header=None,
                          names=COLONNE, dtype=str, chunksize=500_000):
        m = (ch.tipo == "EMPLP") & (ch.terr == "IT") & (ch.sesso == "9")
        for c, v in TOT.items():
            if c != "titolo":
                m &= (ch[c] == v)
        ch = ch[m & (ch.profilo == TOT_PROFILO) &
                (ch.ateco.str.len() == 1)]
        if len(ch):
            pezzi.append(ch[["titolo", "ateco", "val"]])
    d = pd.concat(pezzi, ignore_index=True)
    d["val"] = pd.to_numeric(d.val, errors="coerce").fillna(0.0)
    _cache["marg"] = d
    return d


def fattore_titolo(istruzione):
    """{ateco: P(ateco|titolo)/P(ateco)}, o None se non disponibile.

    Dove il titolo non ha quella sezione il fattore resta 1: e' il caso
    delle sette sezioni escluse dall'incrocio, e va saputo perche' e'
    dove la correzione servirebbe di piu'.
    """
    t = TITOLO_CENS.get(istruzione)
    if not t:
        return None
    d = _marginale_titolo()
    num = d[d.titolo == t].groupby("ateco").val.sum()
    den = d[d.titolo == TOT_TITOLO].groupby("ateco").val.sum()
    if num.sum() <= 0 or den.sum() <= 0:
        return None
    num, den = num / num.sum(), den / den.sum()
    f = {}
    for a in den.index:
        if a in num.index and den[a] > 0:
            f[a] = float(num[a] / den[a])
        else:
            f[a] = 1.0
    return f


def sposta(comune="034027", sesso="M", stampa=True):
    """Quanto la riponderazione cambierebbe la distribuzione.

    Il criterio per adottarla: se sposta meno di 0,05 la complessita' non
    vale, e il limite si dichiara invece di correggerlo male.
    """
    fuori = []
    for istr in TITOLO_CENS:
        base = repertorio(sesso=sesso, comune=comune)
        rip = repertorio(sesso=sesso, comune=comune, istruzione=istr)
        a = base.groupby("ateco").peso.sum(); a = a / a.sum()
        b = rip.groupby("ateco").peso.sum(); b = b / b.sum()
        i = a.index.union(b.index)
        v = 0.5 * float(np.abs(a.reindex(i, fill_value=0)
                               - b.reindex(i, fill_value=0)).sum())
        f = fattore_titolo(istr) or {}
        uno = sum(1 for x in f.values() if x == 1.0)
        fuori.append({"istruzione": istr, "TVD": round(v, 3),
                      "sezioni_non_corrette": uno})
    r = pd.DataFrame(fuori)
    if stampa:
        print(f"quanto la riponderazione sposta la composizione "
              f"({comune}, sesso {sesso}):\n")
        print(r.to_string(index=False))
        print("\nsotto 0,05 la complessita' non vale: si dichiara il "
              "limite invece\ndi correggerlo con un fattore nazionale non "
              "validabile.")
    return r
