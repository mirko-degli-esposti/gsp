#!/usr/bin/env bash
# verifica_registro.sh — il registro dopo la sessione dell'11 agosto.
#
#   bash scripts/verifica_registro.sh
#
# Non modifica nulla: guarda e riporta. Serve a rispondere a una domanda
# sola — il registro e' completo? — con una misura invece che a memoria.

cd ~/progetti/gsp || exit 1

echo "═══ 1. YAML e impronte"
python -c "import yaml; yaml.safe_load(open('fonti/registro.yaml')); print('  YAML valido')"
python -m gsp.fonti --verifica | tail -2

echo
echo "═══ 2. Le sette fonti locali: URL e licenza"
python - << 'PY'
import yaml
d = yaml.safe_load(open("fonti/registro.yaml"))
sette = ["brescia_cittadinanza_quartieri", "reggio_cittadinanza_circoscrizioni",
         "ravenna_cittadinanza_aree", "forli_cittadinanza_quartieri",
         "bologna_cittadinanza_zone", "parma_microdati_residenti",
         "parma_codifica_campi"]
for x in d["fonti"]:
    if x["id"] not in sette:
        continue
    u = str(x.get("url", ""))
    lic = str(x.get("licenza", ""))
    seg = "!!" if "DA_VERIFICARE" in u + lic else "ok"
    print(f"  {seg} {x['id']:<36} {lic:<22} "
          f"{'url mancante' if 'DA_VERIFICARE' in u else ''}")
PY

echo
echo "═══ 3. Campi obbligatori mancanti, per scheda"
python - << 'PY'
import yaml
d = yaml.safe_load(open("fonti/registro.yaml"))
obbl = ["ente", "url", "data_accesso", "licenza", "archiviazione",
        "universo", "unita", "normalizzatore", "usabile_per",
        "non_usabile_per", "copertura"]
buchi = 0
for x in d["fonti"]:
    m = [k for k in obbl if k not in x]
    if m:
        buchi += 1
        print(f"  {x['id']:<36} manca: {','.join(m)}")
if not buchi:
    print("  nessuno")
PY

echo
echo "═══ 4. Riferimento temporale — quanto sono vecchie le fonti locali"
python - << 'PY'
import yaml
d = yaml.safe_load(open("fonti/registro.yaml"))
for x in d["fonti"]:
    if "cittadinanza" in x["id"] or "parma_microdati" in x["id"]:
        r = x.get("riferimento_temporale", "NON DICHIARATO")
        print(f"  {x['id']:<36} {r}")
PY

echo
echo "═══ 5. usato_da che puntano a file inesistenti"
python - << 'PY'
import yaml, os
d = yaml.safe_load(open("fonti/registro.yaml"))
visti = set()
for x in d["fonti"]:
    for u in (x.get("usato_da") or []):
        if not isinstance(u, str) or not u.endswith(".py") or u in visti:
            continue
        visti.add(u)
        trovato = any(os.path.exists(os.path.join(r, u))
                      for r, _, f in os.walk("scripts")) or \
                  any(u in f for _, _, f in os.walk("src"))
        if not trovato:
            print(f"  !! {u}  (citato da {x['id']})")
if not visti:
    print("  nessun usato_da con nome di file")
PY

echo
echo "═══ 6. ATTRIBUZIONI.md — le voci senza licenza accertata"
python -m gsp.fonti --attribuzioni > /dev/null 2>&1
grep -c "DA_VERIFICARE" fonti/ATTRIBUZIONI.md 2>/dev/null \
  | xargs -I{} echo "  {} occorrenze di DA_VERIFICARE nel file pubblico"

echo
echo "───────────────────────────────────────────────────────────────"
echo "  Il file che conta e' ATTRIBUZIONI.md: e' quello che accompagna"
echo "  il bundle pubblico, e finche' contiene DA_VERIFICARE dichiara"
echo "  di non sapere sotto quale licenza stiano le sue fonti."
