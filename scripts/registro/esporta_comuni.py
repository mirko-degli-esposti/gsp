"""scripts/registro/esporta_comuni.py — migrazione una tantum dict -> yaml.
Legge gsp.common.COMUNI com'e' oggi + i pool da rigenera.sh, scrive
flotta/comuni.yaml, e verifica il round-trip: il yaml ricaricato deve
essere UGUALE al dict (a meno dei default che il loader aggiunge)."""
import re, yaml, sys
from pathlib import Path
import gsp.common as G

ROOT = Path(G.__file__).resolve().parents[2]
OUT = ROOT / "flotta" / "comuni.yaml"

# in testa, dopo gli import
class _Dumper(yaml.SafeDumper):
    pass

def _str_quoted_if_numeric(dumper, s):
    # codici comune e codici zona: sempre quotati, o YAML 1.1 li legge
    # come OTTALI quando hanno solo cifre 0-7 (015146 -> 6758)
    style = "'" if s.isdigit() else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", s, style=style)

_Dumper.add_representer(str, _str_quoted_if_numeric)



# pool e stato da rigenera.sh (l'altro posto, per l'ultima volta)
pool, stato = {}, {}
for line in (ROOT / "scripts" / "rigenera.sh").read_text().splitlines():
    m = re.match(r'\s*"(\d{6}):(K\d+C):(\d+)"\s*#\s*(.*)', line)
    if m:
        cod, liv, p, nota = m.groups()
        pool[cod] = int(p)
        stato[cod] = ("collaudo" if "collaudo" in nota else
                      "pilota" if "PILOTA" in nota else "flotta")

voci = {}
for cod, v in G.COMUNI.items():
    e = {"nome": v["nome"], "slug": v["slug"], "regione": v["regione"]}
    if v.get("livello") is not None:
        e["livello"] = v["livello"]
        e["livelli"] = v["livelli"]
    if "opendata_paese" in v:
        e["opendata_paese"] = v["opendata_paese"]
    if cod in pool:
        e["pool"] = pool[cod]
    e["stato"] = stato.get(cod, "collaudo")      # San Vito: non in rigenera
    voci[cod] = e

OUT.parent.mkdir(exist_ok=True)
# e la riga di scrittura diventa:
OUT.write_text(yaml.dump(voci, Dumper=_Dumper, allow_unicode=True, sort_keys=False))
print(f"scritto {OUT}: {len(voci)} voci")

# round-trip: il loader che andra' in common.py, qui in anteprima
def carica(path):
    d = yaml.safe_load(open(path, encoding="utf-8"))
    for e in d.values():
        e.setdefault("livello", None)
        e.setdefault("livelli", {})
    return d

ricaricato = carica(OUT)
for cod, v in G.COMUNI.items():
    r = {k: ricaricato[cod][k] for k in v}     # confronto sui campi del dict
    assert r == v, f"{cod}: round-trip diverso su {[k for k in v if r[k] != v[k]]}"
print("round-trip: identico per tutte le", len(G.COMUNI), "voci")
