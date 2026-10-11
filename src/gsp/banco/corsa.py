"""Una corsa: cartella isolata, copia degli ingressi, comandi per fase,
esecuzione con GSP_COMUNI_DIR, esito con hash e commit.

Layout di corse/<id>/:
    esperimento.yaml
    comuni/<COD>/...          <- GSP_COMUNI_DIR per gli script
    nuclei/                   <- --out-dir di assign_nucleo
    log/<fase>.log
    misure/                   (M1)
    bundle/                   (M3)

Gli anelli non rigenerati vengono COPIATI dalla base (produzione o un'altra
corsa), mai linkati: la corsa e' autosufficiente e l'hash dei prodotti ha
senso. Gli ingressi (tavole grezze e decodificate, c1-c10, zona_2023)
vengono copiati sempre: cs_build li legge dalla stessa cartella in cui
scrive.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import time

import gsp.common as G
from gsp.banco import CORSE, RADICE
from gsp.banco import manifesto as M

SCRIPT = {
    "cs_build": "scripts/vincoli/cs_build.py",
    "fit_cs": "scripts/fit/fit_cs.py",
    "assign_avq": "scripts/attributi/assign_avq.py",
    "enrich": "scripts/attributi/enrich.py",
    "assign_nucleo": "scripts/attributi/assign_nucleo.py",
}
# Nomi che cs_build/fit_cs/avq/enrich scrivono e che NON sono ingressi.
_PRODOTTI_PREFISSI = ("cs_", "fit_", "targets_", "popolazione_", "pool_")


def cartella(id_corsa: str) -> str:
    return os.path.join(CORSE, id_corsa)


def dir_comuni(id_corsa: str) -> str:
    return os.path.join(cartella(id_corsa), "comuni")


def _controlla_isolamento(d: str) -> None:
    d = os.path.realpath(d)
    for proibita in (G.GSP, G.DATA):
        if d == os.path.realpath(proibita) or \
                d.startswith(os.path.realpath(proibita) + os.sep):
            raise RuntimeError(f"la corsa scriverebbe dentro {proibita}: "
                               f"rifiuto ({d})")


def _base_dirs(m: dict) -> tuple[str, str]:
    """(cartella comuni, cartella nuclei) della base."""
    if m["base"] == "produzione":
        return G.COMUNI_DIR, os.path.join(G.DATA, "nuclei")
    return dir_comuni(m["base"]), os.path.join(cartella(m["base"]), "nuclei")


def prodotti_anello(m: dict, k: int, livello: str | None = None) -> list[str]:
    """Percorsi RELATIVI alla cartella della corsa dei prodotti dell'anello k
    per il livello dato (default: quello effettivo del manifesto)."""
    cod, anno = m["comune"], m["anno"]
    liv = livello or M.livello_effettivo(m)
    c = f"comuni/{cod}/constraints_{anno}"
    if k == 1:
        return [f"{c}/cs_{liv}.json", f"{c}/targets_{liv}.json",
                f"{c}/fit_{liv}.json", f"{c}/popolazione_{liv}.csv",
                f"{c}/pool_{liv}.csv"]
    if k == 2:
        return [f"{c}/popolazione_{liv}_avq.csv"]
    if k == 3:
        return [f"{c}/popolazione_{liv}_avq_full.csv"]
    return [f"nuclei/nuclei_{cod}.csv", f"nuclei/nuclei_{cod}_diagnostica.json"]


def prepara(m: dict) -> str:
    """Crea la cartella, copia ingressi e anelli ereditati. Idempotente
    solo su una corsa `nuova`."""
    if m["esito"].get("stato") not in ("nuova", None):
        raise RuntimeError(f"corsa {m['id']} gia' {m['esito']['stato']}: "
                           "non si rilancia, si crea una corsa nuova")
    d = cartella(m["id"])
    _controlla_isolamento(d)
    cod, anno = m["comune"], m["anno"]
    for sub in ("comuni", "nuclei", "log", "misure"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    base_com, base_nuc = _base_dirs(m)
    src = os.path.join(base_com, cod)
    dst = os.path.join(d, "comuni", cod)
    if not os.path.isdir(src):
        raise RuntimeError(f"base senza il comune {cod}: {src}")
    # ingressi: tutto tranne i prodotti della catena
    for radice, dirs, files in os.walk(src):
        rel = os.path.relpath(radice, src)
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in files:
            if f.startswith(_PRODOTTI_PREFISSI):
                continue
            shutil.copy2(os.path.join(radice, f), os.path.join(dst, rel, f))
    # anelli ereditati: quelli prima del primo rigenerato
    ereditati = []
    primo = m["anelli"][0]
    liv_base = m["livello"] if m["base"] == "produzione" else None
    for k in range(1, primo):
        for rel in prodotti_anello(m, k, liv_base):
            s = os.path.join(base_com if not rel.startswith("nuclei/")
                             else os.path.dirname(base_nuc),
                             rel[len("comuni/"):] if rel.startswith("comuni/")
                             else rel)
            if os.path.exists(s):
                t = os.path.join(d, rel)
                os.makedirs(os.path.dirname(t), exist_ok=True)
                shutil.copy2(s, t)
                ereditati.append(rel)
            elif not rel.endswith("pool_" + M.livello_effettivo(m) + ".csv"):
                raise RuntimeError(f"anello {k} ereditato ma manca {s}")
    m["esito"]["ereditati"] = ereditati
    return d


def comandi(m: dict) -> list[tuple[str, list[str]]]:
    """[(fase, argv)] nell'ordine di rigenera.sh, per gli anelli richiesti.
    I flag di produzione sono scritti per esteso, come in rigenera.sh,
    cosi' il comando registrato nell'esito e' quello eseguito."""
    p = M.manopole_piene(m)
    cod, anno = m["comune"], str(m["anno"])
    liv, liv_eff = m["livello"], M.livello_effettivo(m)
    py = sys.executable
    out = []
    v, f = p["vincoli"], p["fit"]
    if 1 in m["anelli"]:
        a = [py, SCRIPT["cs_build"], cod, "--anno", anno, "--livello", liv]
        if v["esclusioni"]:
            a.append("--esclusioni")
        if v["senza"]:
            a += ["--senza", ",".join(v["senza"])]
        for k in ("min_age", "max_age"):
            if v[k] is not None:
                a += ["--" + k.replace("_", "-"), str(v[k])]
        out.append(("cs_build", a))
        a = [py, SCRIPT["fit_cs"], cod, "--anno", anno, "--livello", liv_eff,
             "--eps", _s(f["eps"]), "--min-alpha", _s(f["min_alpha"]),
             "--pool", str(f["pool"]), "--outer", str(f["outer"]),
             "--numba", "--sparse", "--tol", _s(f["tol"]),
             "--sweeps", str(f["sweeps"])]
        a.append("--gibbs" if f["gibbs"] else "--no-gibbs")
        if f["no_exact"]:
            a.append("--no-exact")
        if f["blocks"]:
            a += ["--blocks", ",".join(f["blocks"])]
        for k in ("warm_from", "anneal", "lr", "lr_tau"):
            if f[k] is not None:
                a += ["--" + k.replace("_", "-"), _s(f[k])]
        out.append(("fit_cs", a))
    if 2 in m["anelli"]:
        q = p["avq"]
        a = [py, SCRIPT["assign_avq"], cod, "--anno", anno,
             "--pop-file", f"popolazione_{liv_eff}.csv"]
        if q["seed"] != M.PRODUZIONE["avq"]["seed"]:
            a += ["--seed", str(q["seed"])]
        if q["targets"]:
            a += ["--targets", ",".join(q["targets"])]
        if q["targets_opt"]:
            a += ["--targets-opt", ",".join(q["targets_opt"])]
        if q["min_record"] != M.PRODUZIONE["avq"]["min_record"]:
            a += ["--min-record", str(q["min_record"])]
        out.append(("assign_avq", a))
    if 3 in m["anelli"]:
        e = p["enrich"]
        a = [py, SCRIPT["enrich"], cod, "--anno", anno,
             "--pop-file", f"popolazione_{liv_eff}_avq.csv"]
        if e["seed"] != M.PRODUZIONE["enrich"]["seed"]:
            a += ["--seed", str(e["seed"])]
        if e["no_tier"]:
            a.append("--no-tier")
        out.append(("enrich", a))
    if 4 in m["anelli"]:
        n = p["nucleo"]
        a = [py, SCRIPT["assign_nucleo"], cod, "--anno", anno,
             "--out-dir", os.path.join(cartella(m["id"]), "nuclei")]
        if n["seme"] != M.PRODUZIONE["nucleo"]["seme"]:
            a += ["--seme", str(n["seme"])]
        if n["repertorio"]:
            a += ["--repertorio", n["repertorio"]]
        out.append(("assign_nucleo", a))
    return out


def _s(x) -> str:
    """Numeri come li scrive rigenera.sh: 1e-8, 2e-4, 0, 0.01."""
    if isinstance(x, float):
        if x == int(x) and abs(x) < 1e6:
            return str(int(x))
        mant, esp = f"{x:e}".split("e")
        esp = int(esp)
        if esp <= -3:
            return f"{mant.rstrip('0').rstrip('.')}e{esp}"
        return f"{x:g}"
    return str(x)


def _git() -> tuple[str, bool]:
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=G.GSP,
                           capture_output=True, text=True, check=True).stdout.strip()
        st = subprocess.run(["git", "status", "--short"], cwd=G.GSP,
                            capture_output=True, text=True, check=True).stdout
        return h, st.strip() == ""
    except Exception:
        return "?", False


def sha256(p: str, blocco=1 << 20) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(blocco), b""):
            h.update(b)
    return h.hexdigest()


# Due prodotti portano dentro l'orologio: fit_<LIV>.json i tempi di calcolo
# (t_exact_s, t_gibbs_s) e nuclei_<COD>_diagnostica.json l'ora di
# generazione (`generato`). Due corse identiche differiscono SOLO li'
# (misurato su Cesena l'11/10/2026, replica del banco). rigenera.sh
# --confronta non li confronta affatto; qui si confronta tutto il resto.
# Che un artefatto porti la data e' contro la regola del report (III.1):
# segnato in TODO, qui si tollera.
_CHIAVI_OROLOGIO = {"fit_": ("t_exact_s", "t_gibbs_s"),
                    "_diagnostica": ("generato",)}


def impronta(p: str) -> str:
    """SHA-256 del file; per i JSON con l'orologio dentro, del JSON senza
    quelle chiavi (prefisso `senza-orologio:`)."""
    nome = os.path.basename(p)
    if nome.endswith(".json"):
        for pat, chiavi in _CHIAVI_OROLOGIO.items():
            if pat in nome:
                import json
                with open(p) as f:
                    j = json.load(f)
                for k in chiavi:
                    j.pop(k, None)
                s = json.dumps(j, sort_keys=True, separators=(",", ":"))
                return "senza-orologio:" + hashlib.sha256(s.encode()).hexdigest()
    return sha256(p)


def lancia(m: dict, dry_run=False, verboso=True) -> dict:
    """Prepara ed esegue. Scrive il manifesto a ogni passo (in_corso con la
    fase corrente, poi finita/fallita), cosi' un Ctrl+C lascia uno stato
    leggibile. Restituisce il manifesto aggiornato."""
    M.valida(m)
    cmds = comandi(m)
    if dry_run:
        for fase, a in cmds:
            print(f"[dry] {fase}: {' '.join(a)}")
        return m
    d = prepara(m)
    env = dict(os.environ, GSP_COMUNI_DIR=dir_comuni(m["id"]))
    env.pop("GSP_SUBMUN_DIR", None)      # le sezioni restano quelle di produzione
    e = m["esito"]
    e.update(stato="in_corso", inizio=M.adesso(), tempi_s={}, comandi={},
             fase=None)
    e["commit_gsp"], e["git_pulito"] = _git()
    e["python"] = sys.version.split()[0]
    M.salva(m)
    for fase, a in cmds:
        e["fase"] = fase
        e["comandi"][fase] = " ".join(a)
        M.salva(m)
        log = os.path.join(d, "log", f"{fase}.log")
        if verboso:
            print(f"[{m['id']}] {fase} ...", flush=True)
        t0 = time.time()
        with open(log, "w") as f:
            f.write(f"--- {' '.join(a)} ---\n")
            f.flush()
            rc = subprocess.run(a, cwd=G.GSP, env=env, stdout=f,
                                stderr=subprocess.STDOUT).returncode
        e["tempi_s"][fase] = round(time.time() - t0, 1)
        if rc != 0:
            e.update(stato="fallita", fine=M.adesso(), fase=fase, rc=rc)
            M.salva(m)
            if verboso:
                print(f"[{m['id']}] {fase} FALLITA (rc={rc}), log: {log}")
            return m
        if verboso:
            print(f"[{m['id']}] {fase} ok in {e['tempi_s'][fase]}s")
    e["prodotti"] = impronte(m)
    e.update(stato="finita", fine=M.adesso(), fase=None)
    M.salva(m)
    return m


def impronte(m: dict) -> dict:
    """SHA-256 dei prodotti degli anelli rigenerati, per percorso relativo."""
    d = cartella(m["id"])
    out = {}
    for k in m["anelli"]:
        for rel in prodotti_anello(m, k):
            p = os.path.join(d, rel)
            if os.path.exists(p):
                out[rel] = impronta(p)
    return out


def confronta_byte(id_a: str, id_b: str) -> dict:
    """Prodotti di A contro B, per percorso relativo: uguale / DIVERSO /
    manca. Il test di determinismo del banco."""
    a, b = M.carica(id_a), M.carica(id_b)
    pa, pb = impronte(a), impronte(b)      # ricalcolate dai file, non dal manifesto
    esito = {}
    for rel in sorted(set(pa) | set(pb)):
        if rel not in pa or rel not in pb:
            esito[rel] = "manca in " + ("A" if rel not in pa else "B")
        else:
            esito[rel] = "uguale" if pa[rel] == pb[rel] else "DIVERSO"
    return esito


def elenca() -> list[dict]:
    righe = []
    if not os.path.isdir(CORSE):
        return righe
    for nome in sorted(os.listdir(CORSE)):
        p = M.percorso(nome)
        if not os.path.exists(p):
            continue
        m = M.carica(p)
        e = m.get("esito", {})
        righe.append({"id": m["id"], "comune": m["comune"],
                      "livello": M.livello_effettivo(m),
                      "anelli": "".join(str(k) for k in m["anelli"]),
                      "stato": e.get("stato", "?"),
                      "tempo_s": round(sum((e.get("tempi_s") or {}).values()), 0),
                      "commit": e.get("commit_gsp", ""),
                      "note": m.get("note", "")})
    return righe
