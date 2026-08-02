"""Registro delle fonti esterne della pipeline GSP.

    import gsp.fonti as F

    F.elenco()                          # tutte le fonti, in tabella
    F.elenco(usabile_per="cognome_italiano")
    F.info("firenze_cognomi_2013")      # la scheda, dict
    F.carica("firenze_cognomi_2013")    # DataFrame canonico (chiave, peso)
    F.verifica()                        # hash + n_misurato di tutte le fonti

Da riga di comando:

    python -m gsp.fonti --elenco
    python -m gsp.fonti --verifica
    python -m gsp.fonti --aggiungi ~/scarichi/x.csv --id comune_var_anno
    python -m gsp.fonti --normalizza firenze_cognomi_2013

Principio: nel registro sta l'universo, non solo la provenienza. Un file
senza universo dichiarato e' un elenco di numeri, non una misura.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sys

import pandas as pd
import yaml

from . import normalizzatori

# ------------------------------------------------------------------ percorsi

def _radice():
    """Radice del repo, in ordine: variabile d'ambiente, posizione del
    pacchetto (installazione editable), percorso storico."""
    env = os.environ.get("GSP_RADICE")
    if env:
        return os.path.expanduser(env)
    qui = os.path.dirname(os.path.abspath(__file__))        # src/gsp/fonti
    repo = os.path.dirname(os.path.dirname(os.path.dirname(qui)))
    if os.path.exists(os.path.join(repo, "fonti", "registro.yaml")):
        return repo
    return os.path.expanduser("~/progetti/gsp")


RADICE = _radice()
DIR_FONTI = os.path.join(RADICE, "fonti")
REGISTRO = os.path.join(DIR_FONTI, "registro.yaml")
DIR_GREZZI = os.path.join(DIR_FONTI, "grezzi")
DIR_NORM = os.path.join(DIR_FONTI, "norm")
DIR_IMPRONTE = os.path.join(DIR_FONTI, "impronte")

SOGLIA_GIT_MB = 5           # oltre, il grezzo non entra in git

# git     grezzo versionato: riproducibile da un clone
# locale  grezzo su disco, ignorato da git: verificabile solo qui
# remoto  nessun grezzo: resta l'URL, e l'impronta e' l'unica prova
ARCHIVIAZIONI = ("git", "locale", "remoto")

CAMPI_OBBLIGATORI = [
    "id", "ente", "titolo", "url", "data_accesso", "licenza",
    "file", "sha256", "archiviazione", "universo", "unita", "copertura",
    "normalizzatore", "usabile_per", "non_usabile_per",
]

CAMPI_MULTI = [
    "id", "ente", "titolo", "licenza", "archiviazione", "percorso",
    "chiave_istanza", "universo", "unita", "normalizzatore",
    "usabile_per", "non_usabile_per",
]

N_IMPRONTA = 20             # quante modalita' di testa entrano nell'impronta

# ------------------------------------------------------------------ registro

_cache = {}


def _leggi_registro():
    if "reg" not in _cache:
        with open(REGISTRO, encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
        fonti = doc.get("fonti") or []
        ids = [f["id"] for f in fonti]
        dupl = {i for i in ids if ids.count(i) > 1}
        if dupl:
            raise ValueError(f"id duplicati nel registro: {sorted(dupl)}")
        _cache["reg"] = {f["id"]: f for f in fonti}
    return _cache["reg"]


def info(id_fonte):
    reg = _leggi_registro()
    if id_fonte not in reg:
        raise KeyError(
            f"fonte '{id_fonte}' assente. Presenti: " + ", ".join(sorted(reg))
        )
    return reg[id_fonte]


def elenco(usabile_per=None, ente=None, come_tabella=True):
    reg = _leggi_registro()
    righe = []
    for f in reg.values():
        if usabile_per and usabile_per not in (f.get("usabile_per") or []):
            continue
        if ente and ente.lower() not in f["ente"].lower():
            continue
        cop = f.get("copertura") or {}
        multi = f.get("tipo") == "multi_istanza"
        if multi:
            try:
                n_ist = len(istanze(f["id"]))
            except Exception:                       # noqa: BLE001
                n_ist = None
            geo = f"{n_ist} {f.get('chiave_istanza', 'istanze')}"
            tempo = f.get("riferimento_temporale")
            n = None
        else:
            geo = cop.get("geo")
            tempo = cop.get("tempo")
            n = f.get("n_misurato")
        righe.append({
            "id": f["id"],
            "tipo": "multi" if multi else "file",
            "ente": (f["ente"] or "").split(" - ")[0],
            "geo": geo,
            "tempo": tempo,
            "unita": f.get("unita"),
            "n": n,
            "licenza": f.get("licenza"),
            "arch": f.get("archiviazione"),
        })
    d = pd.DataFrame(righe).sort_values("id").reset_index(drop=True)
    return d if come_tabella else righe


def tipo(id_fonte):
    """'file' (una fonte, un file) oppure 'multi_istanza' (una tavola,
    tanti file uguali per forma e diversi per chiave: un comune, un anno)."""
    return info(id_fonte).get("tipo", "file")


def istanze(id_fonte):
    """Mappa {chiave_istanza: percorso assoluto}, dal pattern `percorso`.

    Il pattern e' relativo alla radice del repo e contiene {istanza}:
        data/comuni/{istanza}/cens_istruzione_eta_raw.csv
    I grezzi multi-istanza vivono in data/, fuori da fonti/grezzi/, perche'
    sono troppi e troppo grossi per essere versionati.
    """
    f = info(id_fonte)
    pat = f.get("percorso")
    if not pat:
        raise KeyError(f"'{id_fonte}' e' multi_istanza ma non ha `percorso`")
    intero = os.path.join(RADICE, pat)
    rx = re.compile("^" + re.escape(intero).replace(
        re.escape("{istanza}"), "([^/]+)") + "$")
    out = {}
    for p in sorted(glob.glob(intero.replace("{istanza}", "*"))):
        m = rx.match(p)
        if m:
            out[m.group(1)] = p
    return out


def path_grezzo(id_fonte, istanza=None):
    if tipo(id_fonte) == "multi_istanza":
        mappa = istanze(id_fonte)
        if istanza is None:
            raise ValueError(f"'{id_fonte}' e' multi_istanza: serve `istanza`"
                             f" fra {sorted(mappa)}")
        return mappa[istanza]
    return os.path.join(DIR_GREZZI, info(id_fonte)["file"])


def path_norm(id_fonte):
    return os.path.join(DIR_NORM, f"{id_fonte}.parquet")


def path_impronta(id_fonte):
    return os.path.join(DIR_IMPRONTE, f"{id_fonte}.json")


# ------------------------------------------------------------------ impronta


def _impronta(id_fonte, d, diag):
    """Riassunto di pochi KB, sempre versionato.

    E' cio' che sopravvive quando il grezzo non entra in git: permette di
    riconoscere se un file riscaricato e' lo stesso che e' stato usato.
    """
    f = info(id_fonte)
    g = path_grezzo(id_fonte)
    imp = {
        "id": id_fonte,
        "sha256": sha256(g) if os.path.exists(g) else f.get("sha256"),
        "byte": os.path.getsize(g) if os.path.exists(g) else None,
        "modalita": int(len(d)),
        "diagnostica": {k: (float(v) if isinstance(v, float) else v)
                        for k, v in diag.items()},
    }
    if "peso" not in d.columns:
        # normalizzatori che non producono una distribuzione (codebook,
        # tavole di definizioni): l'impronta e' la testa piu' i conteggi.
        prima = d.columns[0]
        imp["n_misurato"] = float(len(d))
        imp["testa"] = [str(x) for x in d[prima].head(N_IMPRONTA)]
        return imp

    pesi = d["peso"].to_numpy()
    imp.update({
        "n_misurato": float(pesi.sum()),
        "peso_max": float(pesi.max()) if len(d) else None,
        "peso_min": float(pesi.min()) if len(d) else None,
        "hapax": int((pesi == 1).sum()),
        "decili": [float(x) for x in
                   pd.Series(pesi).quantile([i / 10 for i in range(1, 10)])],
        "testa": [{"chiave": k, "peso": float(p)} for k, p in
                  zip(d["chiave"].head(N_IMPRONTA), pesi[:N_IMPRONTA])],
    })
    return imp


def _impronta_multi(id_fonte):
    """Impronta di una fonte multi-istanza: una riga per istanza.

    E' l'unica cosa che finisce in git per queste fonti: i grezzi stanno in
    data/, che pesa gigabyte ed e' escluso. Serve a riconoscere se un file
    riscaricato o rigenerato e' lo stesso che e' stato usato.
    """
    mappa = istanze(id_fonte)
    out = {}
    for k, p in mappa.items():
        _, diag = normalizza(id_fonte, k, salva=False)
        out[k] = {
            "sha256": sha256(p),
            "byte": os.path.getsize(p),
            # tutta la diagnostica scalare, qualunque sia il
            # normalizzatore: SDMX porta anni e obs_somma, le sezioni
            # comuni e popolazione, un normalizzatore futuro altro ancora.
            **{k: v for k, v in diag.items()
               if isinstance(v, (int, float, str))
               or (isinstance(v, list) and len(v) <= 40)},
        }
    return {"id": id_fonte, "tipo": "multi_istanza",
            "n_istanze": len(out), "istanze": out}


def impronta(id_fonte, scrivi=False):
    if tipo(id_fonte) == "multi_istanza":
        imp = _impronta_multi(id_fonte)
    else:
        d, diag = normalizza(id_fonte, salva=False)
        imp = _impronta(id_fonte, d, diag)
    if scrivi:
        os.makedirs(DIR_IMPRONTE, exist_ok=True)
        with open(path_impronta(id_fonte), "w", encoding="utf-8") as fh:
            json.dump(imp, fh, ensure_ascii=False, indent=2, sort_keys=True)
    return imp


def _impronta_salvata(id_fonte):
    p = path_impronta(id_fonte)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ hash


def sha256(path, blocco=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for pezzo in iter(lambda: f.read(blocco), b""):
            h.update(pezzo)
    return h.hexdigest()


# ------------------------------------------------------------------ carica


def normalizza(id_fonte, istanza=None, salva=True):
    """Applica il normalizzatore al grezzo. Ritorna (DataFrame, diagnostica)."""
    f = info(id_fonte)
    d, diag = normalizzatori.applica(
        f["normalizzatore"], path_grezzo(id_fonte, istanza),
        f.get("opzioni"), f.get("dimensioni"),
    )
    if salva and tipo(id_fonte) == "file":
        os.makedirs(DIR_NORM, exist_ok=True)
        d.to_parquet(path_norm(id_fonte), index=False, compression="zstd")
        os.makedirs(DIR_IMPRONTE, exist_ok=True)
        with open(path_impronta(id_fonte), "w", encoding="utf-8") as fh:
            json.dump(_impronta(id_fonte, d, diag), fh,
                      ensure_ascii=False, indent=2, sort_keys=True)
    return d, diag


def carica(id_fonte, istanza=None, rinormalizza=False):
    """Frame della fonte. Per le multi-istanza serve `istanza`; il Parquet
    non viene usato (i grezzi vivono in data/ e sono gia' compatti)."""
    if tipo(id_fonte) == "multi_istanza":
        return normalizza(id_fonte, istanza, salva=False)[0]
    p, g = path_norm(id_fonte), path_grezzo(id_fonte)
    if rinormalizza or not os.path.exists(p) or os.path.getmtime(p) < os.path.getmtime(g):
        return normalizza(id_fonte)[0]
    return pd.read_parquet(p)


# ------------------------------------------------------------------ verifica


def _verifica_multi(i, f, riga):
    """Confronta le istanze sul disco con quelle nell'impronta.

    Tre esiti distinti, e la distinzione conta: un'istanza NUOVA e' un
    comune aggiunto (informazione, non guasto), una CAMBIATA e' un file
    rigenerato o riscaricato (da guardare), una MANCANTE e' un dato che non
    c'e' piu'.
    """
    imp = _impronta_salvata(i)
    trovate = istanze(i)
    riga["arch"] = f.get("archiviazione")
    riga["n"] = len(trovate)

    if imp is None:
        riga.update(esito="DIVERGE",
                    nota=f"{len(trovate)} istanze sul disco, impronta "
                         f"assente: generarla con --scansiona")
        return riga

    note = []
    vecchie = imp.get("istanze", {})
    nuove = sorted(set(trovate) - set(vecchie))
    perse = sorted(set(vecchie) - set(trovate))
    cambiate = [k for k in sorted(set(trovate) & set(vecchie))
                if sha256(trovate[k]) != vecchie[k].get("sha256")]

    if perse:
        note.append(f"{len(perse)} mancanti: {', '.join(perse[:4])}")
    if cambiate:
        note.append(f"{len(cambiate)} cambiate: {', '.join(cambiate[:4])}")

    if note:
        riga.update(esito="DIVERGE", nota=" · ".join(note))
    elif nuove:
        riga.update(esito="NUOVE",
                    nota=f"{len(nuove)} istanze non in impronta: "
                         f"{', '.join(nuove[:6])} — rilanciare --scansiona")
    return riga


def verifica(id_fonte=None, silenzioso=False):
    """Ricalcola hash e n_misurato. Ritorna la tabella degli esiti."""
    reg = _leggi_registro()
    ids = [id_fonte] if id_fonte else sorted(reg)
    righe = []
    for i in ids:
        f = reg[i]
        riga = {"id": i, "esito": "ok", "nota": ""}
        note = []

        obbl = CAMPI_OBBLIGATORI if f.get("tipo") != "multi_istanza" \
            else CAMPI_MULTI
        mancanti = [c for c in obbl if c not in f]
        if mancanti:
            note.append("campi mancanti: " + ",".join(mancanti))

        arch = f.get("archiviazione")
        if arch not in ARCHIVIAZIONI:
            note.append(f"archiviazione '{arch}' non valida")
        riga["arch"] = arch

        if f.get("tipo") == "multi_istanza":
            riga = _verifica_multi(i, f, riga)
            if note:
                riga["esito"] = "DIVERGE"
                riga["nota"] = " · ".join(note + [riga.get("nota", "")]).strip(" ·")
            righe.append(riga)
            continue

        g = path_grezzo(i)
        if not os.path.exists(g):
            imp = _impronta_salvata(i)
            if arch == "git":
                riga.update(esito="ROTTA", arch=arch,
                            nota="dichiarata in git ma il grezzo non c'e': " + g)
            elif imp is None:
                riga.update(esito="ROTTA", arch=arch,
                            nota="ne' grezzo ne' impronta: la fonte non e' "
                                 "piu' verificabile, riscaricare da url")
            else:
                riga.update(esito="IMPRONTA", arch=arch,
                            n=imp["n_misurato"], modalita=imp["modalita"],
                            nota=f"grezzo assente, impronta del "
                                 f"{f.get('data_accesso')} presente")
            righe.append(riga)
            continue

        h = sha256(g)
        if h != f.get("sha256"):
            note.append(f"sha256 diverso (disco {h[:12]}, registro "
                        f"{str(f.get('sha256'))[:12]})")

        try:
            d_norm, diag = normalizza(i, salva=False)
            # solo distribuzione_csv produce n_misurato/modalita; gli altri
            # normalizzatori riassumono altro, e il confronto si fa su cio'
            # che c'e'.
            n_oss = diag.get("n_misurato", float(len(d_norm)))
            m_oss = diag.get("modalita", len(d_norm))
            n_att = f.get("n_misurato")
            if n_att is not None and abs(n_oss - n_att) > 0.5:
                note.append(f"n_misurato {n_oss:.0f} contro {n_att:.0f} "
                            "nel registro")
            m_att = f.get("modalita")
            if m_att is not None and m_oss != m_att:
                note.append(f"modalita' {m_oss} contro {m_att}")
            riga["n"] = n_oss
            riga["modalita"] = m_oss

            imp = _impronta_salvata(i)
            if imp is None:
                note.append("impronta assente, generarla con --impronta")
            else:
                if abs(imp.get("n_misurato", n_oss) - n_oss) > 0.5:
                    note.append(f"impronta: n {imp['n_misurato']:.0f} "
                                f"contro {n_oss:.0f}")
                if imp.get("modalita", m_oss) != m_oss:
                    note.append(f"impronta: modalita' {imp['modalita']} "
                                f"contro {m_oss}")
        except Exception as e:              # noqa: BLE001
            note.append(f"normalizzatore fallito: {type(e).__name__}: {e}")

        nd, nm = f.get("n_dichiarato"), f.get("n_misurato")
        if nd is not None and nm is not None and abs(nd - nm) > 0.5:
            note.append(f"dichiarato {nd:.0f} != misurato {nm:.0f} "
                        "(atteso se documentato in anomalie)")

        if note:
            riga["esito"] = "DIVERGE"
            riga["nota"] = " · ".join(note)
        righe.append(riga)

    d = pd.DataFrame(righe)
    # IMPRONTA non e' un guasto: e' lo stato normale di una fonte `locale`
    # o `remoto` vista da un clone che non ha i grezzi.
    d["ok"] = d.esito.isin(["ok", "IMPRONTA", "NUOVE"])
    if not silenzioso:
        segni = {"ok": "  ", "IMPRONTA": " ·", "NUOVE": " +"}
        for _, r in d.iterrows():
            print(f"{segni.get(r.esito, '!!')} {r.id:34s} "
                  f"{r.esito:8s} {r.nota}")
        n_imp = (d.esito == "IMPRONTA").sum()
        n_ko = (~d.ok).sum()
        coda = f" · {n_imp} solo impronta" if n_imp else ""
        print(f"\n{len(d)} fonti · {n_ko} da guardare{coda}")
    return d


def pubblicabile(silenzioso=False):
    """Cosa finirebbe in un repo pubblico, e cosa non puo' finirci.

    Un grezzo con `archiviazione: git` viene pubblicato insieme al codice.
    Se la sua licenza non e' verificata, quel push e' una violazione fatta
    senza accorgersene. Le impronte e il registro sono sempre pubblicabili:
    sono misure nostre, non ridistribuzione della fonte.
    """
    reg = _leggi_registro()
    righe = []
    for i in sorted(reg):
        f = reg[i]
        lic = (f.get("licenza") or "").strip()
        pubblica = f.get("archiviazione") == "git"
        if not pubblica:
            esito, nota = "solo impronta", "il grezzo non e' versionato"
        elif lic in ("", "DA_VERIFICARE", "NON_NOTA"):
            esito, nota = "BLOCCANTE", "grezzo in git con licenza non verificata"
        elif lic.startswith("NON_REDISTRIBUIBILE"):
            esito, nota = "BLOCCANTE", "grezzo in git ma non ridistribuibile"
        else:
            esito, nota = "ok", f"ridistribuibile con attribuzione ({lic})"
        righe.append({"id": i, "licenza": lic or "-", "esito": esito,
                      "nota": nota})
    d = pd.DataFrame(righe)
    if not silenzioso:
        for _, r in d.iterrows():
            segno = "!!" if r.esito == "BLOCCANTE" else "  "
            print(f"{segno} {r.id:34s} {r.esito:13s} {r.nota}")
        n = (d.esito == "BLOCCANTE").sum()
        print(f"\n{len(d)} fonti · {n} bloccanti per il repo pubblico")
        if n:
            print("Per ognuna: verificare la licenza, oppure passare a "
                  "`archiviazione: locale`\ne aggiungere il file a "
                  "fonti/grezzi/.gitignore.")
    return d


def attribuzioni(scrivi=True):
    """Genera fonti/ATTRIBUZIONI.md dal registro.

    Le licenze CC-BY obbligano ad attribuire in modo visibile a chi riceve
    i dati: un campo dentro un YAML non basta. Il file e' generato, mai
    scritto a mano, cosi' non puo' divergere dal registro.
    """
    reg = _leggi_registro()
    righe = ["# Attribuzioni delle fonti",
             "",
             "Generato da `python -m gsp.fonti --attribuzioni`. Non "
             "modificare a mano:",
             "le informazioni vivono in `fonti/registro.yaml`.",
             ""]
    for i in sorted(reg):
        f = reg[i]
        cop = f.get("copertura") or {}
        righe += [
            f"## {f.get('titolo', i)}",
            "",
            f"- **Fonte:** {' '.join((f.get('ente') or '').split())}",
            f"- **Licenza:** {f.get('licenza')}",
            f"- **URL:** {f.get('url')}",
            f"- **Scaricato il:** {f.get('data_accesso')}",
            f"- **Copertura:** {cop.get('geo')}, {cop.get('tempo')}",
            f"- **Universo:** {' '.join((f.get('universo') or '').split())}",
        ]
        attr = f.get("attribuzione")
        if attr:
            righe += ["", "> " + " ".join(attr.split())]
        righe.append("")
    testo = "\n".join(righe)
    if scrivi:
        p = os.path.join(DIR_FONTI, "ATTRIBUZIONI.md")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(testo)
        print(f"fonti/ATTRIBUZIONI.md scritto · {len(reg)} fonti")
    return testo


# ------------------------------------------------------------------ aggiungi


def aggiungi(path, id_fonte, copia=True):
    """Copia il grezzo, calcola l'hash, stampa lo stub YAML da incollare.

    I campi che richiedono giudizio - universo, unita', usabile_per,
    non_usabile_per - restano da compilare a mano. E' voluto: sono la
    ragione per cui il registro esiste.
    """
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    mb = os.path.getsize(path) / 1e6
    ext = os.path.splitext(path)[1]
    nome = f"{id_fonte}{ext}"
    dest = os.path.join(DIR_GREZZI, nome)

    if copia:
        os.makedirs(DIR_GREZZI, exist_ok=True)
        if os.path.exists(dest) and sha256(dest) != sha256(path):
            raise FileExistsError(f"{dest} esiste con contenuto diverso")
        shutil.copy2(path, dest)

    h = sha256(dest if copia else path)
    arch = "git" if mb <= SOGLIA_GIT_MB else "locale"

    print(f"# {mb:.2f} MB · copiato in fonti/grezzi/{nome} · "
          f"archiviazione: {arch}")
    if arch == "locale":
        print(f"#\n# oltre la soglia di {SOGLIA_GIT_MB} MB: il grezzo resta "
              f"su disco, fuori da git.\n"
              f"# aggiungi a fonti/grezzi/.gitignore la riga:\n"
              f"#     {nome}\n"
              f"# poi `python -m gsp.fonti --impronta {id_fonte}`: e' "
              f"l'unica cosa\n# che un clone vedra' di questa fonte.")
    print(f"""
  - id: {id_fonte}
    ente: DA_COMPILARE
    titolo: DA_COMPILARE
    url: DA_COMPILARE
    data_accesso: {pd.Timestamp.today().date()}
    licenza: DA_VERIFICARE
    file: {nome}
    sha256: {h}
    archiviazione: {arch}         # git | locale | remoto
    universo: DA_COMPILARE        # chi conta, a che data, con quale filtro
    unita: DA_COMPILARE           # individuo | famiglia | intestazione | ...
    copertura: {{geo: DA_COMPILARE, tempo: DA_COMPILARE}}
    normalizzatore: distribuzione_csv
    opzioni: {{sep: ","}}
    dimensioni: []
    n_dichiarato: null            # quello che dice la fonte, se lo dice
    n_misurato: null              # lo riempie --normalizza
    modalita: null
    anomalie: []
    bias: DA_COMPILARE
    usabile_per: []
    non_usabile_per: []
""")
    return h


# ------------------------------------------------------------------ cli


def _main():
    ap = argparse.ArgumentParser(description="registro delle fonti GSP")
    ap.add_argument("--elenco", action="store_true")
    ap.add_argument("--verifica", nargs="?", const=True)
    ap.add_argument("--pubblico", action="store_true",
                    help="cosa puo' finire in un repo pubblico")
    ap.add_argument("--attribuzioni", action="store_true",
                    help="rigenera fonti/ATTRIBUZIONI.md")
    ap.add_argument("--normalizza", metavar="ID")
    ap.add_argument("--impronta", metavar="ID")
    ap.add_argument("--scansiona", metavar="ID",
                    help="rileva le istanze di una fonte multi_istanza")
    ap.add_argument("--aggiungi", metavar="PATH")
    ap.add_argument("--id", metavar="ID")
    a = ap.parse_args()

    if a.scansiona:
        imp = impronta(a.scansiona, scrivi=True)
        print(f"fonti/impronte/{a.scansiona}.json · "
              f"{imp['n_istanze']} istanze")
        salta = {"sha256", "byte", "righe", "colonne"}
        for k, v in sorted(imp["istanze"].items()):
            pezzi = [f"{v['righe']:,} righe"]
            anni = v.get("anni")
            if anni:
                pezzi.append(f"anni {anni[0]}-{anni[-1]}")
            for c, et in (("comuni", "comuni"), ("sezioni", "sezioni"),
                          ("popolazione", "pop"), ("obs_somma", "obs")):
                if c in v:
                    pezzi.append(f"{et} {v[c]:,.0f}"
                                 if isinstance(v[c], (int, float))
                                 else f"{et} {v[c]}")
            extra = [f"{c}={v[c]}" for c in sorted(v)
                     if c not in salta and c not in
                     ("anni", "comuni", "sezioni", "popolazione", "obs_somma")
                     and not c.startswith("var_") and not c.startswith("obs_per")]
            print(f"  {k:22s} " + " · ".join(pezzi)
                  + ("   " + " ".join(extra) if extra else ""))
        return
    if a.impronta:
        imp = impronta(a.impronta, scrivi=True)
        t = imp.get("testa") or [None]
        t0 = t[0]["chiave"] if isinstance(t[0], dict) else t[0]
        print(f"fonti/impronte/{a.impronta}.json scritta · "
              f"n {imp['n_misurato']:.0f} · modalita' {imp['modalita']} · "
              f"testa {t0}")
        return

    if a.elenco:
        print(elenco().to_string(index=False))
    elif a.attribuzioni:
        attribuzioni()
    elif a.pubblico:
        d = pubblicabile()
        sys.exit(0 if (d.esito != "BLOCCANTE").all() else 1)
    elif a.verifica:
        d = verifica(None if a.verifica is True else a.verifica)
        sys.exit(0 if d.ok.all() else 1)
    elif a.normalizza:
        d, diag = normalizza(a.normalizza)
        print(f"{a.normalizza}: {len(d)} modalita', peso {d.peso.sum():.0f}")
        for k, v in diag.items():
            print(f"  {k}: {v}")
        print(f"\nda incollare nel registro:\n  n_misurato: "
              f"{diag['n_misurato']:.0f}\n  modalita: {diag['modalita']}")
    elif a.aggiungi:
        if not a.id:
            ap.error("--aggiungi richiede --id")
        aggiungi(a.aggiungi, a.id)
    else:
        ap.print_help()
