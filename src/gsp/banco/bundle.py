"""Il bundle di una corsa: lo stesso layout del bundle di Animarium, in
corse/<id>/bundle/, cosi' il pannello della release lo legge con
`?bundle=<url>` senza modifiche.

    bundle/
      comuni.json                 (build_indice.py --bundle)
      medie_nazionali.json        (copia dal bundle di Animarium)
      geo/                        (copia, se c'e': serve all'atlante)
      comuni/<COD>/pop.parquet    (to_parquet.py --pop-file --nuclei-dir, regime PUBBLICO)
      comuni/<COD>/manifest.json  (manifest_min.py)
      comuni/<COD>/riferimenti.json (build_riferimenti.py --cs)
      comuni/<COD>/rif_nuclei.json  (build_rif_nuclei.py)

Il riferimento censuario viene dal constraint set PIENO della base (la
produzione), non da quello della corsa: in un hold-out il blocco tolto e'
proprio quello che si vuole vedere contro il censimento. Il manifesto
registra quale cs e' stato usato.

Gli script sono quelli di Animarium (ANIMARIUM_ROOT, default
~/progetti/animarium): il banco non ne duplica nessuno. Il Parquet esce
dal regime pubblico di gsp.individui.esporta_pubblico, come la release.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

import gsp.common as G
from gsp.banco import corsa as C
from gsp.banco import manifesto as M

ANIMARIUM = os.path.expanduser(os.environ.get("ANIMARIUM_ROOT",
                                              "~/progetti/animarium"))


def _esegui(script, argomenti, log):
    cmd = [sys.executable, os.path.join(ANIMARIUM, "build", script)] + argomenti
    env = dict(os.environ)
    with open(log, "a") as f:
        f.write(f"--- {' '.join(cmd)} ---\n")
        f.flush()
        rc = subprocess.run(cmd, cwd=ANIMARIUM, env=env, stdout=f,
                            stderr=subprocess.STDOUT).returncode
    if rc != 0:
        raise RuntimeError(f"{script} fallito (rc={rc}), log: {log}")


def costruisci(m: dict, verboso=True) -> str:
    if m["esito"].get("stato") != "finita":
        raise RuntimeError(f"corsa {m['id']} non finita")
    if not os.path.isdir(os.path.join(ANIMARIUM, "build")):
        raise RuntimeError(f"Animarium non trovato in {ANIMARIUM} (ANIMARIUM_ROOT)")
    d = C.cartella(m["id"])
    cod, anno = m["comune"], str(m["anno"])
    liv_eff = M.livello_effettivo(m)
    cdir = os.path.join(C.dir_comuni(m["id"]), cod, f"constraints_{anno}")
    f_full = os.path.join(cdir, f"popolazione_{liv_eff}_avq_full.csv")
    if not os.path.exists(f_full):
        raise RuntimeError(f"manca {f_full}: il bundle vuole l'anello 3")
    b = os.path.join(d, "bundle")
    bc = os.path.join(b, "comuni", cod)
    os.makedirs(bc, exist_ok=True)
    log = os.path.join(d, "log", "bundle.log")
    open(log, "w").close()

    base_com, _ = C._base_dirs(m)
    cs_pieno = os.path.join(base_com, cod, f"constraints_{anno}",
                            f"cs_{m['livello']}.json")
    if not os.path.exists(cs_pieno):
        cs_pieno = os.path.join(cdir, f"cs_{liv_eff}.json")

    passi = [
        ("to_parquet.py", [cod, "--anno", anno, "--pop-file", f_full,
                           "--nuclei-dir", os.path.join(d, "nuclei"),
                           "--out", os.path.join(bc, "pop.parquet"),
                           "--drop-avq-raw"]),
        ("manifest_min.py", [cod, "--parquet", os.path.join(bc, "pop.parquet"),
                             "--out", os.path.join(bc, "manifest.json")]),
        ("build_riferimenti.py", [cod, "--anno", anno, "--cs", cs_pieno,
                                  "--out", os.path.join(bc, "riferimenti.json")]),
        ("build_rif_nuclei.py", [cod, "--out", os.path.join(bc, "rif_nuclei.json")]),
        ("build_indice.py", ["--bundle", b]),
    ]
    for script, argv in passi:
        if verboso:
            print(f"[{m['id']}] bundle: {script} ...", flush=True)
        _esegui(script, argv, log)
    for nome in ("medie_nazionali.json",):
        s = os.path.join(ANIMARIUM, "bundle", nome)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(b, nome))
    geo = os.path.join(ANIMARIUM, "bundle", "geo")
    if os.path.isdir(geo):
        shutil.copytree(geo, os.path.join(b, "geo"), dirs_exist_ok=True)
    m["esito"]["bundle"] = {"cartella": "bundle", "cs_riferimenti": cs_pieno,
                            "parquet_mb": round(os.path.getsize(
                                os.path.join(bc, "pop.parquet")) / 1024 / 1024, 2),
                            "quando": M.adesso()}
    M.salva(m)
    return b
