"""CLI del banco. Vedi gsp/banco/__init__.py."""
from __future__ import annotations

import argparse
import sys

import yaml

from gsp.banco import CORSE
from gsp.banco import corsa as C
from gsp.banco import manifesto as M


def _set(manopole: dict, assegnazioni: list[str]) -> dict:
    """--set fit.pool=200000 --set vincoli.senza=[Z3,Z4] (valori YAML)."""
    for s in assegnazioni or []:
        if "=" not in s or "." not in s.split("=", 1)[0]:
            sys.exit(f"--set vuole gruppo.manopola=valore, non {s!r}")
        chiave, val = s.split("=", 1)
        gruppo, k = chiave.split(".", 1)
        manopole.setdefault(gruppo, {})[k] = yaml.safe_load(val)
    return manopole


def cmd_nuovo(a):
    manopole = {}
    if a.senza:
        manopole["vincoli"] = {"senza": a.senza.split(",")}
    if a.pool:
        manopole.setdefault("fit", {})["pool"] = a.pool
    _set(manopole, a.set)
    anelli = range(int(a.anelli[0]), int(a.anelli[-1]) + 1)
    try:
        m = M.nuovo(a.comune, a.etichetta, anelli, manopole, a.base, a.note,
                    a.livello, a.anno)
    except (ValueError, KeyError) as e:
        sys.exit(f"manifesto non valido: {e}")
    p = M.salva(m)
    print(p)
    if a.lancia:
        C.lancia(m)
        _stampa_esito(m)
    return m


def cmd_lancia(a):
    m = M.carica(a.id)
    try:
        m = C.lancia(m, dry_run=a.dry_run)
    except (ValueError, RuntimeError) as e:
        sys.exit(f"[{a.id}] {e}")
    if not a.dry_run:
        _stampa_esito(m)


def _stampa_esito(m):
    e = m["esito"]
    tot = sum((e.get("tempi_s") or {}).values())
    print(f"[{m['id']}] {e['stato']} · {tot:.0f}s · commit {e.get('commit_gsp')}"
          f"{'' if e.get('git_pulito') else ' (albero NON pulito)'}")
    for rel, h in (e.get("prodotti") or {}).items():
        print(f"   {h[-12:]}  {rel}")


def cmd_elenca(a):
    righe = C.elenca()
    if not righe:
        print(f"nessuna corsa in {CORSE}")
        return
    print(f"{'id':38s} {'liv.':16s} {'anelli':6s} {'stato':9s} {'tempo':>7s}  commit   note")
    for r in righe:
        print(f"{r['id']:38s} {r['livello']:16s} {r['anelli']:6s} "
              f"{r['stato']:9s} {r['tempo_s']:6.0f}s  {r['commit']:8s} {r['note']}")


def cmd_replica(a):
    """Rifa' una corsa finita con lo stesso manifesto e confronta i prodotti."""
    orig = M.carica(a.id)
    if orig["esito"].get("stato") != "finita":
        sys.exit(f"[{a.id}] non e' finita: nulla da replicare")
    etichetta = orig["id"].split("_", 1)[1].rsplit("_", 1)[0]
    m = M.nuovo(orig["comune"], etichetta + "_replica", orig["anelli"],
                orig["manopole"], orig["base"],
                f"replica di {orig['id']}", orig["livello"], orig["anno"])
    M.salva(m)
    m = C.lancia(m)
    _stampa_esito(m)
    if m["esito"]["stato"] == "finita":
        print(f"\nconfronto {orig['id']} / {m['id']}:")
        for rel, v in C.confronta_byte(orig["id"], m["id"]).items():
            print(f"   {v:8s} {rel}")


def cmd_confronta(a):
    for rel, v in C.confronta_byte(a.a, a.b).items():
        print(f"   {v:8s} {rel}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m gsp.banco")
    sp = ap.add_subparsers(dest="cmd", required=True)

    n = sp.add_parser("nuovo", help="scrive un manifesto (e con --lancia lo esegue)")
    n.add_argument("comune")
    n.add_argument("--etichetta", required=True, help="es. senza_Z3, seme7")
    n.add_argument("--anelli", default="1-4", help="es. 1-4, 1, 2-4")
    n.add_argument("--senza", help="blocchi da togliere, es. Z3 o Z3,Z4")
    n.add_argument("--pool", type=int)
    n.add_argument("--set", action="append", metavar="gruppo.manopola=valore")
    n.add_argument("--base", default="produzione")
    n.add_argument("--livello")
    n.add_argument("--anno", type=int, default=M.ANNO)
    n.add_argument("--note", default="")
    n.add_argument("--lancia", action="store_true")
    n.set_defaults(f=cmd_nuovo)

    l = sp.add_parser("lancia", help="esegue un manifesto")
    l.add_argument("id")
    l.add_argument("--dry-run", action="store_true")
    l.set_defaults(f=cmd_lancia)

    e = sp.add_parser("elenca", help="le corse e il loro stato")
    e.set_defaults(f=cmd_elenca)

    r = sp.add_parser("replica", help="rifa' una corsa e confronta byte per byte")
    r.add_argument("id")
    r.set_defaults(f=cmd_replica)

    c = sp.add_parser("confronta", help="prodotti di due corse, byte per byte")
    c.add_argument("a")
    c.add_argument("b")
    c.set_defaults(f=cmd_confronta)

    a = ap.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
