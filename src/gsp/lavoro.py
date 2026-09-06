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

# 6 settembre 2026 buttrio.....

PROV_REG = {**{p: "ITD5" for p in ("033","034","035","036","037","038","039","040","099")},
            **{p: "ITC4" for p in ("012","013","014","015","016","017","018","019","020","097","098","108")}}

def _regione_di(c):
    """Sigla regionale per un codice comunale ISTAT, o None.

    Il codice porta gia' la provincia nelle prime tre cifre, quindi la
    regione si deduce senza tabella per comune: `REGIONE_DI` resta per
    gli undici che la dichiarano a mano, `PROV_REG` copre tutta la flotta.
    """
    c = str(c).strip()
    if not c.isdigit():
        return None
    c = c.zfill(6)
    r = REGIONE_DI.get(c) or PROV_REG.get(c[:3])
    if r is None:
        print(f"   [regione] {c}: provincia {c[:3]} non mappata, "
              f"la congiunta ripiega su IT")
    return r


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
               istruzione=None, calibrare=True):
    """(ateco, profilo, peso) per una cella, dalla congiunta.

    La cascata e' comune -> regione -> Italia, e viene dichiarata nella
    colonna `livello` del risultato: chi legge sa a quale risoluzione sta
    guardando invece di doverlo dedurre.
    """
    d = _leggi()
    liv = "comune"
    if territorio is None:
        territorio = comune
    if territorio and str(territorio).isdigit():
        territorio = str(territorio).zfill(6)      # ottava occorrenza

    if territorio and territorio not in set(d.terr):
        reg = _regione_di(territorio)
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

    # Riponderazione OPZIONALE per titolo di studio: spenta se
    # `istruzione` non e' passata. Vedi il blocco in fondo al modulo per
    # i tre limiti che la rendono una scelta e non un miglioramento.
    if istruzione:
        f = fattore_titolo(istruzione)
        if f:
            g["peso"] = g.peso * g.ateco.map(lambda a: f.get(a, 1.0))
            g = g[g.peso > 0].reset_index(drop=True)
            liv += "+titolo"

    # Calibrazione sulle marginali comunali del censimento permanente
    # 2021 (6/9/2026, Buttrio). Va DOPO il titolo, non prima: il fattore
    # per titolo moltiplica i pesi per sezione e sposterebbe la marginale
    # appena colpita. Con l'IPF in coda, il titolo diventa la misura di
    # riferimento e le marginali 2021 il vincolo — che e' anche l'ordine
    # sensato concettualmente.
    #
    # NESSUNA SOGLIA SULLA DISTANZA, per scelta misurata: sui comuni gia'
    # vicini alla propria regione l'IPF non sposta nulla per costruzione,
    # quindi una soglia aggiungerebbe un percorso di codice e un numero
    # da giustificare senza cambiare i risultati. Le guardie in
    # `_marginale_usabile` riguardano la QUALITA' della marginale.
    if calibrare and liv.startswith(("regione", "nazionale")) and comune:
        t_macro, t_pos = _margini_2021(str(comune).zfill(6), sesso)
        if _marginale_usabile(t_macro):
            g = calibra(g, t_macro, t_pos)
            liv += "+cal2021" if t_pos else "+cal2021m"

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
        r = repertorio(comune=c, calibrare=False)
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
        base = repertorio(sesso=sesso, comune=comune,calibrare=False)
        rip = repertorio(sesso=sesso, comune=comune, istruzione=istr,calibrare=False)
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


    # 6 settembere 2026 buttrio.....
    # =====================================================================
# CALIBRAZIONE SUL PERMANENTE 2021
#
# Da incollare in gsp/lavoro.py dopo il blocco della riponderazione per
# titolo. Richiede una sola modifica a repertorio(), in fondo al file.
#
# PERCHE'. La congiunta viene dal 2011 e per cinque comuni su undici —
# e per tutta la flotta dei 245 — non e' nemmeno comunale: e' ITD5
# tale e quale. Il censimento permanente pubblica al 2021, per TUTTI i
# comuni, due marginali che quella congiunta puo' colpire:
#
#     DF_DCSS_EMPLP_2_COM   occupati per sesso e sei macro-classi ATECO
#     DF_DCSS_EMPLP_1_COM   occupati per sesso e dipendente/indipendente
#
# Non sostituiscono la congiunta: due marginali separate non
# ricostruiscono una dipendenza che vale 0,138-0,166 in TVD. La
# sostituiscono nei LIVELLI e la lasciano nella FORMA — la stessa
# architettura dell'anello 1, applicata a un terzo asse.
#
# COSA CONSERVA. L'IPF a due vincoli e' la distribuzione di massima
# entropia relativa alla congiunta 2011 sotto quelle due marginali:
# conserva i RAPPORTI DI ODDS, non le composizioni condizionate. La
# quota di dipendenti dentro le manifatturiere cambia — deve cambiare,
# e' vincolata — ma il fatto che un coadiuvante familiare sia raro
# nell'amministrazione pubblica e frequente in agricoltura resta.
#
# COSA NON RISOLVE. Ne' il titolo di studio ne' l'eta': il permanente
# incrocia solo sesso. I due limiti dichiarati piu' grossi restano.
# =====================================================================

FLOW_MACRO = "DF_DCSS_EMPLP_2_COM"
FLOW_POSIZ = "DF_DCSS_EMPLP_1_COM"
ANNO_DCSS = "2021"

# Le sei macro-classi partizionano le 21 sezioni, ma NON per intervalli
# contigui di lettere: G e I stanno insieme, H sta con J. Leggere
# «(g,i)» come un intervallo mette H in commercio e I in trasporti, i
# totali tornano lo stesso e nessun controllo se ne accorge.
MACRO = {
    "A": "A",                                             # agricoltura
    "B": "0011", "C": "0011", "D": "0011", "E": "0011",    # industria b-f
    "F": "0011",
    "G": "0026", "I": "0026",                              # commercio, alberghi
    "H": "0091", "J": "0091",                              # trasporti, informazione
    "K": "0092", "L": "0092", "M": "0092", "N": "0092",    # finanza, servizi imprese
    "O": "0093", "P": "0093", "Q": "0093", "R": "0093",    # altre attivita' o-u
    "S": "0093", "T": "0093", "U": "0093",
}
MACRO_TOT = "0010"

# Il 2021 pubblica la sola dicotomia: `9` dipendenti, `22` indipendenti,
# `99` totale. Sono i primi due livelli dell'albero ricostruito su Parma.
POSIZ_DIP, POSIZ_IND, POSIZ_TOT = "9", "22", "99"
PROFILI_DIP = {"9"}
PROFILI_IND = {"41", "15", "18", "19"}

# IL PARASUBORDINATO E' IL PUNTO APERTO. Nell'albero 2011 il codice 42 e'
# fratello di 9 e 22, non figlio: 99 = 9 + 22 + 42. Nel 2021 la somma
# fa 9 + 22 = 99 esatta (Bologna: 68.348,04 + 27.270,96 = 95.619), quindi
# i parasubordinati sono stati ripiegati dentro una delle due e la fonte
# non dice quale. Convenzione ISTAT sulle rilevazioni sul lavoro: il
# collaboratore sta fra gli indipendenti. Vale il 3,6% degli occupati a
# Parma, quindi la scelta si misura con `deriva(sensibilita=True)` invece
# di essere data per buona.
PARASUB = "42"
PARASUB_IN = POSIZ_IND

SESSO_DCSS = {"M": "M", "F": "F", None: "T"}

# I valori del permanente sono STIME, non conteggi: arrivano con i
# decimali. Sotto questa soglia l'errore di campionamento sulle sei
# classi non giustifica la calibrazione, e si ripiega sulla congiunta
# non calibrata dichiarandolo nel livello.
MIN_OCCUPATI_2021 = 300.0


def _margini_2021(comune, sesso=None):
    """Le due marginali comunali del permanente, o None se non ci sono.

    Torna (macro, posizione) come due dict {codice: valore}, gia'
    ristretti al sesso richiesto.
    """
    from gsp.istat import sdmx as X

    g = SESSO_DCSS.get(sesso, "T")
    chiave = ("dcss", comune, g)
    if chiave in _cache:
        return _cache[chiave]

    def _tira(flow, dim):
        d = X.fetch(flow, {"REF_AREA": comune})
        if d is None or not len(d):
            return None
        d = d[(d.GENDER.astype(str) == g) &
              (d.TIME_PERIOD.astype(str) == ANNO_DCSS)]
        if not len(d):
            return None
        v = pd.to_numeric(d.OBS_VALUE, errors="coerce")
        return dict(zip(d[dim].astype(str).str.strip(), v))

    try:
        mac = _tira(FLOW_MACRO, "BRANCH_ECON_ACT")
        pos = _tira(FLOW_POSIZ, "EMPLOYMENT_STATUS")
    except Exception as e:                      # servizio giu', chiave rifiutata
        print(f"   [permanente] {comune}: {type(e).__name__} {e}")
        mac = pos = None

    if mac:
        mac = {k: v for k, v in mac.items() if k in set(MACRO.values())}
    if pos:
        # `10` e' il totale ATECO in _1_COM, `0010` in _2_COM: terza
        # convenzione diversa nella stessa famiglia.
        pos = {k: v for k, v in pos.items() if k in (POSIZ_DIP, POSIZ_IND)}

    r = (mac or None, pos or None)
    _cache[chiave] = r
    return r


def _classe_posizione(profilo):
    if profilo in PROFILI_DIP:
        return POSIZ_DIP
    if profilo == PARASUB:
        return PARASUB_IN
    return POSIZ_IND


def calibra(g, t_macro=None, t_pos=None, iterazioni=100, tol=1e-10):
    """IPF della congiunta sulle marginali 2021. Modifica `g` in copia.

    Vincoli assenti = vincoli non applicati: passare un solo target
    calibra un asse solo, ed e' il caso di un comune dove una delle due
    tavole non ha righe.
    """
    g = g.copy()
    w = g.peso.to_numpy(dtype="float64")
    if w.sum() <= 0:
        return g
    w = w / w.sum()

    m = g.ateco.map(MACRO).to_numpy()
    q = np.array([_classe_posizione(p) for p in g.profilo])

    vincoli = []
    for chiavi, target in ((m, t_macro), (q, t_pos)):
        if not target:
            continue
        s = sum(target.values())
        if s <= 0:
            continue
        vincoli.append((chiavi, {k: v / s for k, v in target.items()}))
    if not vincoli:
        return g

    n = 0
    for n in range(1, iterazioni + 1):
        prima = w.copy()
        for chiavi, target in vincoli:
            for k, t in target.items():
                sel = chiavi == k
                s = w[sel].sum()
                if s > 0:
                    w[sel] *= t / s
                # s == 0 con t > 0: la congiunta non ha righe in quella
                # classe. Non si puo' creare massa dal nulla; il vincolo
                # resta mancato e `scarto_calibrazione` lo segnala.
        if np.abs(w - prima).sum() < tol:
            break

    g["peso"] = w * g.peso.sum() / w.sum() if w.sum() > 0 else g.peso
    g.attrs["iterazioni_ipf"] = n
    return g


def _marginale_usabile(t, minimo=MIN_OCCUPATI_2021, classi=6):
    """Vero se la marginale copre l'universo e non e' troppo rumorosa.

    Tre modi in cui la marginale del permanente non e' utilizzabile, e
    nessuno dei tre e' la distanza dalla regione:
      - manca del tutto (comune non nella tavola);
      - non ha tutte e sei le macro-classi. ATTESI da' pavimento 7 a
        `settore_prof`, cioe' 7 righe = un solo sesso: esistono comuni
        con pubblicazione ridotta. Una classe mancante non e' zero, ed
        e' massa che l'IPF ricollocherebbe sulle altre cinque;
      - e' troppo piccola perche' la stima campionaria regga sei classi.
    """
    if not t:
        return False
    if len(t) < classi:
        return False
    return sum(t.values()) >= minimo


def scarto_calibrazione(g, t_macro=None, t_pos=None):
    """Quanto la calibrazione ha mancato i target. Zero = colpiti."""
    w = g.peso.to_numpy(dtype="float64")
    w = w / w.sum()
    fuori = {}
    for nome, chiavi, target in (("macro", g.ateco.map(MACRO).to_numpy(), t_macro),
                                 ("posiz", np.array([_classe_posizione(p)
                                                     for p in g.profilo]), t_pos)):
        if not target:
            continue
        s = sum(target.values())
        d = 0.0
        for k, t in target.items():
            d += abs(w[chiavi == k].sum() - t / s)
        fuori[nome] = round(0.5 * d, 6)
    return fuori


# ---------------------------------------------------------- la deriva
#
# Le SEI STESSE CLASSI esistono nel 2011 (DICA_CARATT_ATTL_COM) e nel
# 2021 (DF_DCSS_EMPLP_2_COM), sugli stessi comuni. La TVD fra le due
# composizioni misura quanto e' invecchiata la struttura settoriale, ed
# e' confrontabile con la distanza comune-regione: se le due sono dello
# stesso ordine, la correzione temporale vale quanto quella spaziale.

FONTE_COM_2011 = "cens2011_caratt_attl_com"      # da registrare in fonti.yaml
DENTRO_ZIP_COM = ("CSV - DATI SOLO CODICI - DATA ONLY CODES/"
                  "DICA_CARATT_ATTL_COM-data.csv")
COLONNE_COM = ["terr", "tipo", "sesso", "ateco", "anno", "val", "_x"]


def _macro_2011(comune, sesso=None):
    """P(macro | sesso) comunale al 2011, dal taglio comunale."""
    if "com2011" not in _cache:
        p = F.path_grezzo(FONTE_COM_2011)
        with zipfile.ZipFile(p) as z:
            t = z.read(DENTRO_ZIP_COM).decode("utf-8")
        d = pd.read_csv(io.StringIO(t), sep="|", header=None,
                        names=COLONNE_COM, dtype=str)
        d = d[(d.tipo == "EMPLP") & (d.ateco != MACRO_TOT)]
        # zero iniziale: sesta occorrenza della trappola, e qui i codici
        # territoriali di provincia (3 cifre) vanno tenuti fuori.
        d = d[(d.tipo == "EMPLP") & (d.ateco != MACRO_TOT)]
        d["val"] = pd.to_numeric(d.val, errors="coerce").fillna(0.0)
        _cache["com2011"] = d
    d = _cache["com2011"]
    chiave = str(comune).zfill(6) if str(comune).strip().isdigit() else str(comune).strip()
    s = d[d.terr == chiave]
    if sesso:
        s = s[s.sesso == SESSO_CENS.get(sesso, "9")]
    else:
        s = s[s.sesso == "9"]
    v = s.groupby("ateco").val.sum()
    return dict(v[v > 0]) if v.sum() > 0 else None


def deriva(comuni=None, sesso=None, sensibilita=False, stampa=True):
    """2011 contro 2021 sulle stesse sei classi, piu' il costo del ripiego.

    Le tre colonne da leggere insieme:
      tvd_tempo    quanto la struttura settoriale e' cambiata in dieci anni
      tvd_spazio   quanto il comune dista dalla sua regione (2011)
      guadagno     quanto la calibrazione recupera sui comuni che hanno
                   la congiunta, cioe' dove esiste la verita' a 21 sezioni
    """
    comuni = comuni or sorted(REGIONE_DI)
    d = _leggi()
    righe = []
    for c in comuni:
        m11 = _macro_2011(c, sesso)
        m21, p21 = _margini_2021(c, sesso)
        r = {"comune": c, "nome": G.info(c).get("nome", "?"),
             "occupati_2021": round(sum(m21.values()), 0) if m21 else None}

        if m11 and m21:
            i = set(m11) | set(m21)
            a = np.array([m11.get(k, 0.0) for k in i]); a = a / a.sum()
            b = np.array([m21.get(k, 0.0) for k in i]); b = b / b.sum()
            r["tvd_tempo"] = round(0.5 * float(np.abs(a - b).sum()), 3)

        if c in set(d.terr):
            base = repertorio(sesso=sesso, comune=c,calibrare=False)
            reg = repertorio(sesso=sesso, territorio=REGIONE_DI[c],calibrare=False)

            def macro_comp(x):
                v = x.groupby(x.ateco.map(MACRO)).peso.sum()
                return v / v.sum()

            a, b = macro_comp(base), macro_comp(reg)
            i = a.index.union(b.index)
            r["tvd_spazio"] = round(0.5 * float(np.abs(
                a.reindex(i, fill_value=0) - b.reindex(i, fill_value=0)).sum()), 3)

            # il test che conta: la regione calibrata sul comune quanto
            # si avvicina alla verita' comunale a 21 sezioni?
            if m21:
                cal = calibra(reg, m21, p21)
                def sez(x):
                    v = x.groupby("ateco").peso.sum()
                    return v / v.sum()
                v0, v1, vv = sez(reg), sez(cal), sez(base)
                i = v0.index.union(v1.index).union(vv.index)
                f = lambda u, w: 0.5 * float(np.abs(
                    u.reindex(i, fill_value=0) - w.reindex(i, fill_value=0)).sum())
                d0, d1 = f(v0, vv), f(v1, vv)
                r["prima"] = round(d0, 3)
                r["dopo"] = round(d1, 3)
                r["guadagno_pc"] = round(100 * (d0 - d1) / d0, 1) if d0 > 0 else None

        righe.append(r)

    t = pd.DataFrame(righe)

    if sensibilita:
        global PARASUB_IN
        vecchio = PARASUB_IN
        alt = []
        for scelta in (POSIZ_IND, POSIZ_DIP):
            PARASUB_IN = scelta
            _cache.pop("sens", None)
            g = deriva(comuni=[c for c in comuni if c in set(d.terr)][:3],
                       sesso=sesso, stampa=False)
            alt.append({"parasubordinato_in": scelta,
                        "dopo_medio": round(g["dopo"].mean(), 4)
                        if "dopo" in g else None})
        PARASUB_IN = vecchio
        t.attrs["sensibilita"] = pd.DataFrame(alt)

    if stampa:
        print(t.to_string(index=False))
        print("\ntvd_tempo  = struttura settoriale 2011 vs 2021, sei classi")
        print("tvd_spazio = comune vs regione, 2011, stesse sei classi")
        print("guadagno   = quanto la calibrazione recupera del ripiego "
              "regionale,\n             misurato a 21 sezioni sui comuni "
              "che hanno la congiunta")
        if "sensibilita" in t.attrs:
            print("\ndove mettere il parasubordinato:")
            print(t.attrs["sensibilita"].to_string(index=False))
    return t


# =====================================================================
# LA PATCH A repertorio(): sostituire il blocco della riponderazione
# per titolo con questo, che aggiunge la calibrazione PRIMA.
#
#     # calibrazione sulle marginali comunali del permanente 2021.
#     # Attiva quando la congiunta NON e' comunale: dove lo e' gia',
#     # calibrarla sulle proprie marginali di dieci anni dopo e' una
#     # scelta diversa, che va misurata prima (vedi `deriva`).
#     if calibrare and liv != "comune" and comune:
#         t_macro, t_pos = _margini_2021(comune, sesso)
#         if t_macro and sum(t_macro.values()) >= MIN_OCCUPATI_2021:
#             g = calibra(g, t_macro, t_pos)
#             liv += "+cal2021"
#
#     if istruzione:
#         ...
#
# e aggiungere `calibrare=True` alla firma.
# =====================================================================
