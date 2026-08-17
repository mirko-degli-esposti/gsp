"""Accesso agli individui sintetici, con il dettaglio DICHIARATO.

    import gsp.individui as I

    I.campione("036023", {"zona": "Cittadella", "eta": "35-49"},
               n=20, dettaglio="narrativo")
    print(I.scheda(riga))

PERCHE' ESISTE. Senza un punto d'accesso unico, ogni consumatore legge il
CSV e decide da se' cosa esporre: il viewer, il campione per le demo, un
SIVE-like per i persona-prompt. Tre consumatori, tre regole di
disclosure, e la piu' permissiva vince senza che nessuno l'abbia decisa.
Qui la regola sta in un punto solo ed e' scritta.

I TRE REGIMI. E' la stessa distinzione che gli istituti di statistica
fanno fra file ad uso pubblico, per la ricerca e ambienti protetti — e
per la stessa ragione: il rischio non sta nel dato ma in cosa se ne fa.

  pubblico    cio' che puo' finire in un file scaricabile. Niente nome,
              niente via ne' civico, coordinate randomizzate dentro la
              sezione. La `sezione` resta: e' la risoluzione vera del
              dato, e dichiararla e' piu' onesto che nasconderla.

  persona     per i persona-prompt degli agenti LLM. Nome e cognome ci
              sono, perche' rendono naturale il prompt; l'indirizzo no,
              perche' a un prompt serve il quartiere, non la porta.

  narrativo   per le biografie da mostrare. Nome, cognome e via; il
              CIVICO solo su richiesta esplicita (`civico=True`), perche'
              e' l'unico elemento che punta a un luogo abitato preciso.

CIO' CHE E' DAVVERO REALE nel record e' il vettore AVQ: sono le risposte
di un rispondente vero, gia' perturbato da ISTAT, replicato ~40 volte su
individui sintetici diversi. Tutto il resto — eta', sesso, istruzione,
zona — viene da marginali aggregati e non ha nessun individuo dietro. Il
civico esiste come indirizzo, ma l'assegnazione e' arbitraria dentro la
sezione e non porta informazione.

NUMEROSITA'. `NMAX` limita quanto si puo' materializzare in un colpo. Non
e' un vincolo tecnico: un campione completo di poche decine di individui
e' un ATTO, un file di centomila e' un dataset — e la differenza fra
citare un caso e pubblicare un archivio sta tutta li'.
"""

import os

import numpy as np
import pandas as pd

import gsp.common as G
import gsp.nomi as N

# Oltre questo si sta producendo un dataset, non un campione. Alzarlo e'
# una decisione, non un parametro.
NMAX = 100

DEMOGRAFICI = ["sesso", "eta", "eta_anni", "stato_civile", "cittadinanza",
               "istruzione", "condizione", "background", "origine_genitori",
               "area", "paese"]
GEOGRAFICI = ["zona", "quartiere", "sezione"]
INDIRIZZO = ["via", "civico", "lon", "lat", "indirizzo_fonte"]

REGIMI = {
    "pubblico":  {"nome": False, "uid": False, "via": False,
                  "civico": False, "coord": "randomizzate",
                  "sezione": True, "donor_id": True},
    "persona":   {"nome": True,  "uid": True,  "via": False,
                  "civico": False, "coord": None,
                  "sezione": False, "donor_id": False},
    "narrativo": {"nome": True,  "uid": True,  "via": True,
                  "civico": False, "coord": None,
                  "sezione": False, "donor_id": False},
}

_cache = {}


# ------------------------------------------------------------- caricamento

def carica(comune, anno=2024):
    """La popolazione completa. Resta in memoria: non la si riscrive mai."""
    chiave = (comune, anno)
    if chiave in _cache:
        return _cache[chiave]
    cdir = G.path_constraints(comune, anno)
    nome = G.resolve_pop_file(cdir, suffisso="_avq_full", escludi=["K10C"])
    d = pd.read_csv(os.path.join(cdir, nome), low_memory=False)
    if "uid" not in d.columns:
        raise KeyError(
            f"{nome} non ha la colonna `uid`: e' una popolazione generata "
            f"prima del 4/8/2026. Rigenerare con rigenera.sh — senza uid "
            f"l'onomastica non e' riproducibile.")
    _cache[chiave] = d
    return d


def _avq():
    return list(G.AVQ_TARGETS) + list(G.AVQ_OPZIONALI)


# ---------------------------------------------------------------- filtro

def filtra(d, filtro=None):
    """Sottoinsieme che soddisfa ESATTAMENTE gli attributi dati.

    Un valore singolo o una lista: {"zona": "Cittadella"} oppure
    {"eta": ["35-49", "50-64"]}.
    """
    if not filtro:
        return d
    m = pd.Series(True, index=d.index)
    for c, v in filtro.items():
        if c not in d.columns:
            raise KeyError(f"'{c}' non e' una colonna: "
                           f"{', '.join(sorted(d.columns)[:12])}...")
        vals = [str(x) for x in
                (v if isinstance(v, (list, tuple, set)) else [v])]
        presenti = set(d[c].astype(str))
        ignoti = [x for x in vals if x not in presenti]
        if ignoti:
            # Il caso tipico e' zona/quartiere: `zona` porta il CODICE
            # (34027001), `quartiere` il NOME (Cittadella), e chi filtra
            # scrive naturalmente il nome. Dire soltanto "nessun individuo
            # soddisfa" darebbe la colpa all'utente, che ha ragione.
            altrove = [k for k in d.columns
                       if k != c and set(ignoti) <= set(d[k].astype(str))]
            if altrove:
                # niente backslash dentro l'espressione di una f-string:
                # Python 3.11 lo rifiuta, 3.12+ lo accetta
                verbo = "e' " if len(ignoti) == 1 else "sono "
                agg = (f"Ma {verbo}in `{altrove[0]}`: prova "
                       f"{{'{altrove[0]}': {ignoti[0]!r}}}.")
            else:
                v_ok = sorted(presenti)[:8]
                agg = (f"Valori di `{c}`: {', '.join(v_ok)}"
                       + (" ..." if len(presenti) > 8 else ""))
            raise LookupError(f"`{c}` non ha {ignoti}. {agg}")
        m &= d[c].astype(str).isin(vals)
    return d[m]


def conta(comune, filtro=None, anno=2024):
    """Quanti individui soddisfano il filtro. Sempre lecito, a qualunque
    numerosita': e' un conteggio, non un'estrazione."""
    return int(len(filtra(carica(comune, anno), filtro)))


# ------------------------------------------------------------- avvertenze

def avvertenze(comune, filtro=None):
    """Cosa il filtro NON puo' dire. Non e' cortesia: un filtro che
    incrocia il paese con la geografia su un comune a tier 0 legge un
    artefatto, e chi mostra il risultato deve saperlo."""
    fuori = []
    f = filtro or {}
    geo = [c for c in ("zona", "quartiere", "sezione") if c in f]
    if geo and any(c in f for c in ("paese", "area")):
        try:
            tier = (G.info(comune).get("opendata_paese") or {}).get("tier")
        except Exception:                                    # noqa: BLE001
            tier = None
        if tier in (0, None):
            fuori.append(
                "il paese NON e' condizionato sulla geografia in questo "
                "comune (tier 0): la composizione per nazionalita' e' "
                "quella comunale replicata in ogni zona, quindi incrociarlo "
                "con " + "/".join(geo) + " non porta informazione.")
    if geo and any(c in f for c in _avq()):
        fuori.append(
            "gli attributi AVQ sono condizionati solo sulla REGIONE: la "
            "variazione fra zone viene dalla composizione demografica "
            "della zona, non da un'informazione locale.")
    if "sezione" in f:
        fuori.append(
            "la sezione e' la risoluzione vera del dato, ma l'assegnazione "
            "dell'individuo a un CIVICO dentro la sezione e' arbitraria.")
    return fuori


# -------------------------------------------------------------- campione

def campione(comune, filtro=None, n=20, dettaglio="persona", anno=2024,
             seed=0, civico=False, spiega=True):
    """`n` individui che soddisfano il filtro, al dettaglio dichiarato.

    L'estrazione e' RIPRODUCIBILE: stesso filtro, stesso seme, stessi
    individui — quindi una demo si puo' provare prima e una biografia
    mostrata in un articolo si puo' citare.
    """
    if dettaglio not in REGIMI:
        raise ValueError(f"dettaglio '{dettaglio}': attesi "
                         f"{', '.join(REGIMI)}")
    r = dict(REGIMI[dettaglio])
    if civico:
        if dettaglio != "narrativo":
            raise ValueError("`civico=True` ha senso solo con "
                             "dettaglio='narrativo'")
        r["civico"] = True

    d = filtra(carica(comune, anno), filtro)
    disponibili = len(d)
    if disponibili == 0:
        raise LookupError(f"nessun individuo soddisfa {filtro}")
    if n > NMAX:
        raise ValueError(
            f"n={n} oltre NMAX={NMAX}. Oltre questa soglia si sta "
            f"producendo un dataset, non un campione: se serve davvero, "
            f"alzare NMAX e' una decisione da prendere, non un parametro "
            f"da passare.")
    m = min(n, disponibili)

    rng = np.random.default_rng(seed)
    scelti = d.iloc[np.sort(rng.choice(disponibili, size=m, replace=False))]
    fuori = _proietta(scelti.copy(), comune, r, rng)

    if spiega:
        print(f"[campione] {m} su {disponibili:,} che soddisfano il filtro "
              f"· dettaglio '{dettaglio}'".replace(",", "."))
        for a in avvertenze(comune, filtro):
            print(f"  ! {a}")
    return fuori


# agosto 17 2026
def esporta_pubblico(comune, anno=2024, seme=None, con_nuclei=False):
    """La popolazione INTERA in regime pubblico, per il bundle scaricabile.

    Non passa da `campione` di proposito. `NMAX` esiste per i regimi
    narrativi, dove il limite e' la sostanza — cento biografie sono un atto,
    centomila un archivio. Il regime `pubblico` e' invece l'unico pensato
    per essere completo (§4.2 del piano di trattamento).

    Il seme e' derivato dal comune, non passato: le coordinate randomizzate
    devono uscire IDENTICHE a ogni rigenerazione, o due bundle dello stesso
    comune differirebbero senza che nulla sia cambiato (§5).

    Con `con_nuclei=True` aggiunge l'anello 4:

        nucleo   int16   progressivo del nucleo DENTRO la sezione, -1 se
                         l'individuo e' in convivenza anagrafica
        ruolo    str     R, P, F, G, A, N

    L'`id_nucleo` per esteso — `360230002112-000003` — NON viene esportato:
    contiene la sezione, che nella riga c'e' gia', quindi la stringa e' una
    ridondanza da 4 MB dove basta un intero da 0,2. Si ricostruisce a valle
    concatenando `sezione` e il progressivo.

    Il merge avviene QUI perche' e' l'unico punto che vede `uid` prima di
    toglierlo. Non e' un accoppiamento fra anelli: questo modulo compone
    gia' cio' che gli anelli producono — nel regime `narrativo` chiama
    `gsp.nomi`, `gsp.istruzione` e `gsp.lavoro`. Compone, non calcola.
    """
    r = dict(REGIMI["pubblico"])
    d = carica(comune, anno).copy()

    if con_nuclei:
        f = os.path.join(G.DATA, "nuclei", f"nuclei_{comune}.csv")
        if not os.path.exists(f):
            # Avviso e non errore: un comune senza nuclei non deve bloccare
            # la build degli altri dieci. La pagina dei nuclei si accorgera'
            # da se' che le colonne non ci sono e lo dichiarera'.
            print(f"[avviso] nuclei assenti per {comune}: il bundle non "
                  f"avra' l'anello 4\n         {f}\n"
                  f"         eseguire assign_nucleo.py per averlo")
        else:
            n = pd.read_csv(f, dtype={"uid": "string", "id_nucleo": "string",
                                      "ruolo": "string"})
            d = d.merge(n, on="uid", how="left")

            # La sezione dentro `id_nucleo` coincide sempre con quella
            # dell'individuo — verificato: nessun nucleo a cavallo di due
            # sezioni. Quindi il progressivo basta a identificarlo, e la
            # stringa per esteso sarebbe 4 MB dove ne bastano 0,2.
            prog = pd.to_numeric(d["id_nucleo"].str.slice(13), errors="coerce")
            d["nucleo"] = prog.fillna(-1).astype("int16")
            d["ruolo"] = d["ruolo"].fillna("")
            d = d.drop(columns=["id_nucleo"])

            # Il nucleo e' identificato dalla COPPIA (sezione, nucleo): il
            # progressivo riparte in ogni sezione. Contare i valori distinti
            # del solo progressivo dava 367 invece di 85.249.
            n_nuclei = int(d.loc[d["nucleo"] >= 0, ["sezione", "nucleo"]]
                           .drop_duplicates().shape[0])
            senza = int((d["nucleo"] < 0).sum())
            print(f"[nuclei] {n_nuclei:,} nuclei · "
                  f"{senza:,} individui in convivenza ({senza / len(d):.2%})"
                  .replace(",", "."))

    seme = int(comune) if seme is None else seme
    return _proietta(d, comune, r, np.random.default_rng(seme))


def _proietta(d, comune, r, rng):
    """Applica il regime: toglie colonne, aggiunge nomi, randomizza."""
    if r["nome"]:
        nomi = [N.nome_agente(x.uid, sesso=x.get("sesso"),
                              eta=x.get("eta"),
                              background=x.get("background"),
                              origine_genitori=x.get("origine_genitori"),
                              paese=x.get("paese"))
                for _, x in d.iterrows()]
        d.insert(1, "nome", [a for a, _ in nomi])
        d.insert(2, "cognome", [b for _, b in nomi])

        # Il titolo DETTAGLIATO — «diploma di perito industriale» invece
        # di «diploma» — sta nei regimi che hanno il nome, per la stessa
        # ragione: e' cio' che rende una scheda una persona invece di un
        # profilo. Deterministico dall'uid come il nome, e non finisce in
        # nessun file.
        try:
            from gsp import istruzione as _IS
            d["titolo_studio"] = [
                _IS.titolo_agente(x.uid, x.get("istruzione"),
                                  sesso=x.get("sesso"), eta=x.get("eta"))
                for _, x in d.iterrows()]
        except Exception as e:                              # noqa: BLE001
            # il repertorio dei titoli e' opzionale: se la fonte non e'
            # registrata la scheda resta valida, solo meno ricca
            print(f"[avviso] titoli non disponibili ({e})")

        # Settore e posizione dal censimento 2011, coppia congiunta: si
        # estraggono INSIEME perche' sono fortemente dipendenti (TVD 0,15
        # fra congiunta e indipendenza), e separarli produrrebbe dirigenti
        # in agricoltura.
        #
        # La riponderazione per titolo e' attiva SOLO qui, nei prodotti
        # narrativi: la plausibilita' individuale conta piu' della
        # correttezza aggregata, perche' una laureata in agricoltura si
        # nota mentre uno scostamento del 5% su una marginale no. Nel
        # bundle pubblico e nelle statistiche resta spenta.
        try:
            from gsp import lavoro as _L
            lav = [_L.lavoro_agente(x.uid, condizione=x.get("condizione"),
                                    sesso=x.get("sesso"), comune=comune,
                                    istruzione=x.get("istruzione"))
                   for _, x in d.iterrows()]
            d["settore"] = [a for a, _ in lav]
            d["posizione"] = [b for _, b in lav]
        except Exception as e:                              # noqa: BLE001
            print(f"[avviso] settore e posizione non disponibili ({e})")

    if r["coord"] == "randomizzate" and {"lon", "lat", "sezione"} <= set(d.columns):
        # Punto casuale nel rettangolo dei civici della sezione. NON si
        # perde niente: l'assegnazione al civico e' gia' arbitraria dentro
        # la sezione, quindi la coordinata non porta informazione oltre a
        # «abita in questa sezione». La densita' per sezione resta
        # identica, e il dato diventa autoprotettivo — «il punto e'
        # casuale dentro la sezione» e' una frase che non ammette repliche,
        # mentre «spostato di trenta metri» invita la domanda «e se
        # fossero venti?».
        for _, g in d.groupby("sezione"):
            for c in ("lon", "lat"):
                v = pd.to_numeric(g[c], errors="coerce")
                lo, hi = float(v.min()), float(v.max())
                if np.isfinite(lo) and np.isfinite(hi) and hi > lo:
                    d.loc[g.index, c] = rng.uniform(lo, hi, len(g))

    togli = []
    if not r["uid"]:
        togli.append("uid")
    if not r["via"]:
        togli.append("via")
    if not r["civico"]:
        togli.append("civico")
    if not r["sezione"]:
        togli.append("sezione")
    if not r["donor_id"]:
        togli.append("donor_id")
    if r["coord"] is None:
        togli += ["lon", "lat"]
    togli.append("indirizzo_fonte")
    return d.drop(columns=[c for c in togli if c in d.columns])


# ---------------------------------------------------------------- scheda

_ETICHETTE = {
    "AMBIENTE": "soddisfazione per l'ambiente della zona",
    "FIDUCIA": "fiducia interpersonale",
    "SALUTE": "salute percepita",
    "CRONI": "malattie croniche",
    "FUMO": "abitudine al fumo",
    "MH": "indice di salute mentale (0-100)",
    "FIDMED": "fiducia nei medici del SSN",
    "FIDINF": "fiducia negli infermieri del SSN",
    "PUNTIFI10": "fiducia nel governo comunale",
    "PUNTIFI8": "fiducia nel governo regionale",
    "PUNTIFI3": "fiducia nelle forze dell'ordine",
    "PUNTIFI12": "fiducia nei vigili del fuoco",
    "VOTOUSL": "giudizio sul servizio ASL ricevuto",
}


def _capitalizza(x):
    """ANNCSU scrive gli odonimi in maiuscolo e la fonte dei cognomi pure.
    In una scheda da leggere il maiuscolo grida."""
    if not isinstance(x, str) or not x.isupper():
        return x
    return x.title()


def _numero(x):
    """I valori AVQ arrivano come stringhe dal CSV, con lo zero iniziale:
    `06` invece di 6, `072` invece di 72."""
    try:
        f = float(x)
        return int(f) if f == int(f) else f
    except (TypeError, ValueError):
        return x


def _tronca(t, n=76):
    """Taglia a parola intera: «scientifiche e t» e' peggio di una riga
    lunga."""
    t = str(t).strip()
    if len(t) <= n:
        return t
    corto = t[:n].rsplit(" ", 1)[0]
    return (corto or t[:n]).rstrip(" ,;") + "…"


def scheda(riga, variabili=("PUNTIFI10", "PUNTIFI8", "FIDMED", "VOTOUSL",
                            "AMBIENTE", "SALUTE", "MH"),
           anagrafica=False):
    """Una scheda leggibile. Deterministica, senza LLM: e' il punto di
    partenza per una biografia, non la biografia.

    `anagrafica=True` si ferma a chi e' la persona e non stampa gli
    attributi AVQ. Serve quando si guarda un campione per verificarne la
    plausibilita': i valori di fiducia e salute riempiono lo schermo e
    non aiutano a vedere se il mestiere stia col titolo di studio.
    """
    p = []
    testa = " ".join(_capitalizza(riga[c]) for c in ("nome", "cognome")
                     if c in riga and pd.notna(riga.get(c)))
    dove = riga.get("quartiere") or riga.get("zona")
    via = _capitalizza(riga.get("via"))
    civ = riga.get("civico")
    luogo = ", ".join(x for x in (
        (f"{via} {civ}" if via and pd.notna(civ) else via), dove) if x)
    p.append(f"{testa or riga.get('uid', '?')}" + (f" — {luogo}" if luogo else ""))

    eta = riga.get("eta_anni")
    # il titolo dettagliato SOSTITUISCE la categoria quando c'e': «diploma
    # di perito industriale» dice qualcosa, «diploma» no
    tit = riga.get("titolo_studio")
    if not isinstance(tit, str) or not tit.strip():
        tit = str(riga.get("istruzione", "")).replace("_", " ")
    elif tit.isupper():
        tit = tit.capitalize()
    

    # `condizione` solo se NON c'e' il mestiere: per un occupato
    # «dipendenti, attività manifatturiere» dice gia' tutto e «occupato»
    # e' rumore; per un pensionato o uno studente e' l'unica informazione
    # su quel fronte.
    riga_2 = [f"{int(eta)} anni" if pd.notna(eta) else riga.get("eta"),
              {"M": "uomo", "F": "donna"}.get(riga.get("sesso")),
              tit]
   
    sett = riga.get("settore")
    if not (isinstance(sett, str) and sett.strip()):
        riga_2.append(str(riga.get("condizione", "")).replace("_", " "))
    p.append("  " + " · ".join(x for x in riga_2 if x))

    if riga.get("cittadinanza") and str(riga["cittadinanza"]) != "ITL":
        prov = riga.get("paese") or riga.get("area")
        p.append(f"  cittadinanza {riga['cittadinanza']}"
                 + (f", {prov}" if prov else ""))

    # settore e posizione: solo per gli occupati, e per costruzione — per
    # tutti gli altri sono `non_applicabile`, non mancanti
    pos = riga.get("posizione")
    if isinstance(sett, str) and sett.strip():
        pezzi = [x for x in ((pos if isinstance(pos, str) and pos.strip()
                              else None), sett) if x]
        p.append("  " + _tronca(", ".join(pezzi)))

    if anagrafica:
        return "\n".join(p)

    dette, assenti = [], []
    for v in variabili:
        if v not in riga:
            continue
        x = riga[v]
        if pd.isna(x) or str(x) == "non_applicabile":
            assenti.append(v)
        else:
            dette.append((v, _numero(x)))
    if dette:
        p.append("")
        for v, x in dette:
            p.append(f"  {_ETICHETTE.get(v, v):<42} {x}")
    # Il missing e' STRUTTURALE, non mancante: dipende dall'annata del
    # donatore o dall'universo della domanda (VOTOUSL riguarda solo chi ha
    # usato l'ASL). Ometterlo in silenzio farebbe pensare a un dato perso;
    # dirlo comunica che la variabile ha un universo.
    for v in assenti:
        p.append(f"  {_ETICHETTE.get(v, v):<42} non rilevata")
    return "\n".join(p)
