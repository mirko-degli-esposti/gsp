"""
lista_comuni_er.py — lista dei comuni dell'Emilia-Romagna per popolazione,
dalla tavola POSAS (demo.istat.it, popolazione al 1/1/2026, dichiarata "stima").

Scopo: lista candidati per l'estensione della flotta GSP (soglia 15k).
Fonte di servizio, NON entra negli anelli: base anagrafica, non censuaria
(scarto atteso ~1-2% rispetto ai margini P1 delle sezioni 2023).

Scheda: fonti/registro.yaml -> istat_posas_comuni_2026
Collaudo esterno: 330 comuni ER, ~57 sopra 15k (conteggio indipendente
da liste ISTAT/Wikipedia, 27/8/2026).
"""

import pandas as pd
from pathlib import Path

# Percorso ancorato alla radice del repo, non alla directory di lancio
# (lo script sta in scripts/diagnostica/, due livelli sotto la radice).
GSP_ROOT = Path(__file__).resolve().parents[2]
CSV = GSP_ROOT / "data" / "istat" / "posas_2026_comuni" / "POSAS_2026_it_Comuni.csv"

# Il file ha: BOM (-> utf-8-sig), una riga descrittiva prima dell'intestazione
# (-> skiprows=1), separatore ';', codici comune già a 6 cifre quotate
# (-> dtype=str, altrimenti '033013' diventa 33013 e il filtro provincia salta).
df = pd.read_csv(CSV, sep=";", skiprows=1,
                 encoding="utf-8-sig", dtype={"Codice comune": str})

# Due intrusi noti (misurati, v. anomalie in scheda):
#   - riga di totale per età con codice Età=999, una per comune;
#   - riga di piè di pagina in coda ("Nota: lo stato civile è in corso di
#     validazione."), letta come dato con Età=NaN.
# Il filtro sulle età vere li elimina entrambi con una condizione sola.
df = df[df["Età"].between(0, 100)]

# Collaudo di struttura: 101 età esatte per ciascuno dei 7.896 comuni.
# Se un'annata futura cambia formato, si rompe qui, non nei conteggi.
assert df.groupby("Codice comune").size().eq(101).all(), "righe/comune != 101"
assert df["Codice comune"].nunique() == 7896, "numero comuni inatteso"

# Coerenza interna della fonte: la colonna Totale deve essere M+F.
# Usiamo Totale nei conteggi; se divergesse, è un difetto del file da vedere.
assert (df["Totale maschi"] + df["Totale femmine"]).equals(df["Totale"]), \
    "Totale != maschi+femmine"

# Filtro ER: nel file comunale non esiste una colonna regione, si va di
# prefisso provinciale del codice comune. Province ER: 033-040 più 099 --
# Rimini (provincia del 1992) è fuori sequenza, dimenticarla perde 27 comuni
# in silenzio.
PROV_ER = {"033", "034", "035", "036", "037", "038", "039", "040", "099"}
er = df[df["Codice comune"].str[:3].isin(PROV_ER)]

# Popolazione = somma sulle età (il totale 999 è già stato filtrato).
pop = (er.groupby(["Codice comune", "Comune"])["Totale"]
         .sum().rename("pop").reset_index()
         .sort_values("pop", ascending=False))
pop["pop"] = pop["pop"].astype(int)

# Collaudo finale contro il conteggio indipendente: 330 comuni, ~57 sopra 15k.
print("comuni ER:", len(pop))
print("sopra 15k:", (pop["pop"] > 15_000).sum())
print(pop.head(12).to_string(index=False))

# Candidati: sopra soglia, esclusi i comuni già in flotta.
# Import ancorato: gsp.common è nel repo, non serve installazione.
import sys
sys.path.insert(0, str(GSP_ROOT / "src"))
from gsp.common import COMUNI

fatti = set(COMUNI)                      # codici ISTAT dei comuni in flotta
cand = pop[(pop["pop"] > 15_000) & ~pop["Codice comune"].isin(fatti)]

print(f"\ncandidati >15k non in flotta: {len(cand)}")   # atteso: 47
print(cand.to_string(index=False))