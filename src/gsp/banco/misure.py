"""Le misure di una corsa: i diagnostici di scripts/diagnostica lanciati
sulla corsa, con uscita strutturata in corse/<id>/misure/.

    anello 1  verifica_vincoli.py --json     vincoli.json, celle.csv
              holdout_z.py --out             holdout_<B>.json  (per blocco tolto)
    anello 2  verifica_donor.py --json       donor.json
    anello 3  MAE per sezione dal log di enrich   sezioni.json
              diag_quinq.py, diag_istruzione_eta.py   quinq.csv, istr_eta.csv
    anello 4  nuclei_<COD>_diagnostica.json  nuclei.json (copia)

Ogni diagnostico lascia anche il suo testo in <nome>.txt. Il manifesto
registra in esito.misure quali file esistono; `riassunto()` ne estrae i
numeri di testa per l'indice.

Il pavimento e l'indipendenza del hold-out vengono dalla corsa PIENA, che
e' la base (produzione): deve avere popolazione_<LIV>.csv e
targets_<LIV>.json dello stesso livello e pool.

Non sono misure di una corsa, e qui non si lanciano: misura_em.py misura
la tavola delle sezioni (la fonte), misura_nucleo.py i microdati di Parma.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import gsp.common as G
from gsp.banco import corsa as C
from gsp.banco import manifesto as M

DIAG = "scripts/diagnostica"


def _esegui(argv, log, env):
    with open(log, "w") as f:
        f.write(f"--- {' '.join(argv)} ---\n")
        f.flush()
        return subprocess.run(argv, cwd=G.GSP, env=env, stdout=f,
                              stderr=subprocess.STDOUT).returncode


def _mae_da_log(log_enrich: str) -> dict | None:
    """Le tre righe '[val]' di enrich.py:
       '  popolazione  MAE   1.06 su media    75.3 | corr 0.9998 | totale 96,066 vs 96,066'
    enrich non ha un --json: si leggono queste righe, e solo queste."""
    if not os.path.exists(log_enrich):
        return None
    out = {}
    for riga in open(log_enrich, encoding="utf-8", errors="replace"):
        s = riga.strip()
        if " MAE " not in s or " su media " not in s:
            continue
        try:
            nome, resto = s.split(" MAE ", 1)
            mae, resto = resto.split(" su media ", 1)
            media, resto = resto.split("|", 1)
            corr = resto.split("corr", 1)[1].split("|", 1)[0]
            tot = resto.split("totale", 1)[1]
            a, b = tot.split("vs")
            out[nome.strip()] = {
                "mae": float(mae), "media_censimento": float(media),
                "corr": float(corr),
                "totale_sintetico": int(a.strip().replace(",", "")),
                "totale_censimento": int(b.strip().replace(",", ""))}
        except (ValueError, IndexError):
            continue
    return out or None


def misura(m: dict, verboso=True) -> dict:
    if m["esito"].get("stato") != "finita":
        raise RuntimeError(f"corsa {m['id']} non finita: niente da misurare")
    d = C.cartella(m["id"])
    cod, anno = m["comune"], str(m["anno"])
    liv, liv_eff = m["livello"], M.livello_effettivo(m)
    cdir = os.path.join(C.dir_comuni(m["id"]), cod, f"constraints_{anno}")
    out = os.path.join(d, "misure")
    os.makedirs(out, exist_ok=True)
    env = dict(os.environ, GSP_COMUNI_DIR=C.dir_comuni(m["id"]))
    env.pop("GSP_SUBMUN_DIR", None)
    py = sys.executable
    fatte, errori = {}, {}

    def passo(nome, argv, prodotti):
        if verboso:
            print(f"[{m['id']}] misura {nome} ...", flush=True)
        rc = _esegui(argv, os.path.join(out, f"{nome}.txt"), env)
        if rc != 0:
            errori[nome] = rc
            if verboso:
                print(f"[{m['id']}] misura {nome} FALLITA (rc={rc})")
            return
        for p in prodotti:
            if os.path.exists(os.path.join(out, p)):
                fatte[p.split(".")[0]] = f"misure/{p}"
        fatte.setdefault(nome, f"misure/{nome}.txt")

    # --- anello 1 ------------------------------------------------------
    f_cs = os.path.join(cdir, f"cs_{liv_eff}.json")
    f_pop = os.path.join(cdir, f"popolazione_{liv_eff}.csv")
    if os.path.exists(f_cs) and os.path.exists(f_pop):
        passo("vincoli", [py, f"{DIAG}/verifica_vincoli.py", cod, "--anno", anno,
                          "--cs", f_cs, "--pop-file", f_pop,
                          "--out", os.path.join(out, "celle.csv"),
                          "--json", os.path.join(out, "vincoli.json")],
              ["vincoli.json", "celle.csv"])
    senza = M.manopole_piene(m)["vincoli"]["senza"]
    if senza:
        base_com, _ = C._base_dirs(m)
        d_piena = os.path.join(base_com, cod, f"constraints_{anno}")
        for b in senza:
            passo(f"holdout_{b}",
                  [py, "scripts/esempio/holdout_z.py", cod, "--blocco", b,
                   "--anno", anno, "--livello", liv, "--dir", cdir,
                   "--piena-dir", d_piena,
                   "--out", os.path.join(out, f"holdout_{b}.json")],
                  [f"holdout_{b}.json"])

    # --- anello 2 ------------------------------------------------------
    f_full = os.path.join(cdir, f"popolazione_{liv_eff}_avq_full.csv")
    if os.path.exists(f_full):
        passo("donor", [py, f"{DIAG}/verifica_donor.py", cod, "--anno", anno,
                        "--pop-file", f_full,
                        "--json", os.path.join(out, "donor.json")],
              ["donor.json"])
        # --- anello 3 --------------------------------------------------
        mae = _mae_da_log(os.path.join(d, "log", "enrich.log"))
        if mae:
            with open(os.path.join(out, "sezioni.json"), "w") as f:
                json.dump({"comune": cod, "fonte": "log/enrich.log [val]",
                           "per_sezione": mae}, f, indent=1)
            fatte["sezioni"] = "misure/sezioni.json"
        passo("quinq", [py, f"{DIAG}/diag_quinq.py", cod, "--anno", anno,
                        "--pop-file", f_full,
                        "--out", os.path.join(out, "quinq.csv")], ["quinq.csv"])
        passo("istr_eta", [py, f"{DIAG}/diag_istruzione_eta.py", cod,
                           "--anno", anno, "--pop-file", f_full,
                           "--out", os.path.join(out, "istr_eta.csv")],
              ["istr_eta.csv"])

    # --- anello 4 ------------------------------------------------------
    f_nuc = os.path.join(d, "nuclei", f"nuclei_{cod}_diagnostica.json")
    if os.path.exists(f_nuc):
        shutil.copy2(f_nuc, os.path.join(out, "nuclei.json"))
        fatte["nuclei"] = "misure/nuclei.json"

    m["esito"]["misure"] = fatte
    m["esito"]["misure_errori"] = errori or None
    m["esito"]["misurato"] = M.adesso()
    M.salva(m)
    return m


def riassunto(m: dict) -> dict:
    """I numeri di testa di una corsa, dai JSON in misure/ (None se mancano)."""
    d = C.cartella(m["id"])
    mis = m["esito"].get("misure") or {}
    r = {}

    def leggi(k):
        p = mis.get(k)
        if not p or not p.endswith(".json"):
            return None
        with open(os.path.join(d, p)) as f:
            return json.load(f)

    v = leggi("vincoli")
    if v:
        g = v["globale"]
        r.update(celle=g["celle"], mre_oss=g["mre_oss"], mre_att=g["mre_att"],
                 z_abs_medio=g["z_abs_medio"], sd_z=g["sd_z"],
                 quota_z3=g["quota_z3"], zeri_violati=g["zeri_violati"])
    for k, p in mis.items():
        if k.startswith("holdout_") and p.endswith(".json"):
            h = leggi(k)
            if h and h.get("comuni"):
                c = h["comuni"][0]
                b = k.split("_", 1)[1]
                r[f"tvd_pav_{b}"] = c["tvd_pavimento"]
                r[f"tvd_hold_{b}"] = c["tvd_holdout"]
                r[f"tvd_ind_{b}"] = c["tvd_indipendenza"]
                r[f"posizione_{b}"] = c["posizione"]
    dn = leggi("donor")
    if dn:
        r["firme"] = dn["firme"]
        for x in dn["variabili"]:
            if x["variabile"] == "SALUTE":
                r["n_eff_salute"] = x["n_eff"]
                r["banda_salute"] = x["banda"]
    s = leggi("sezioni")
    if s:
        r["mae_sezione_pop"] = s["per_sezione"].get("popolazione", {}).get("mae")
    n = leggi("nuclei")
    if n:
        sc = n.get("stato_civile") or {}
        r.update(nuclei=n["nuclei"],
                 ampiezza_media=n["individui"] / max(n["nuclei"], 1),
                 coniugati_incoerenti=sc.get("incoerenti"))
    return r
