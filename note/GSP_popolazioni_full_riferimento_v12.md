# Popolazioni sintetiche GSP — documento di riferimento

**Versione 1.2 — 29 luglio 2026**
Descrive i file `popolazione_K9C_avq_full.csv` per Brescia, Parma e Bologna:
come caricarli, cosa contengono, come sono stati costruiti, quali limiti
dichiarati portano con sé e dove trovare i dati reali per il confronto.

> **Novità rispetto alla v1.1**: il condizionale geografico del paese di
> cittadinanza è **collegato e attivo** su tutte e tre le città (§6); §10
> riporta i numeri delle esecuzioni correnti; aggiunta la §11 sul principio
> dell'ipotesi nulla.

---

## 1. I file

```
~/progetti/gsp/data/comuni/{COMUNE}/constraints_2024/popolazione_K9C_avq_full.csv
```

| comune | codice | individui | attributi |
|---|---|---|---|
| Brescia | `017029` | 198.259 | 28 |
| Parma | `034027` | 198.121 | 28 |
| Bologna | `037006` | 390.098 | 28 |

Totale 786.478 individui sintetici, ciascuno con indirizzo civico e
coordinate geografiche.

### Caricamento

Ci sono tre trappole di tipo. Questo snippet le gestisce tutte:

```python
import pandas as pd, os

def carica(comune, anno=2024):
    f = os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}/"
        f"popolazione_K9C_avq_full.csv")
    p = pd.read_csv(f, low_memory=False, dtype={
        "zona": "string",        # 34027001: NON leggere come int
        "sezione": "string",     # 340270000994: 12 cifre
        "civico": "string",      # '19A': numero + esponente
    })
    for c in ["AMBIENTE", "FIDUCIA", "SALUTE", "CRONI", "FUMO",
              "MH", "BMI", "BMIMIN", "CPESO"]:
        p[c + "_num"] = pd.to_numeric(p[c], errors="coerce")
    return p
```

In alternativa, tutti i percorsi e i registri stanno in `gsp_common.py` (§4):

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/progetti/gsp/scripts"))
import gsp_common as G
f = os.path.join(G.path_constraints("034027", 2024),
                 "popolazione_K9C_avq_full.csv")
```

**Trappole:**

1. `zona` e `sezione` sono codici, non numeri. Letti come `int64` funzionano
   ma perdono la natura di chiave; letti come `float` diventano notazione
   scientifica.
2. Le nove variabili AVQ sono **stringhe** perché mescolano codici numerici
   e `non_applicabile` — tranne `SALUTE`, che è `int64` perché è l'unica
   senza missing strutturali.
3. `area` usa `NaN` per gli italiani, non `non_applicabile`. Le convenzioni
   per "assente" sono tre e non sono state uniformate (§7).

---

## 2. Gli attributi

### 2.1 Anello 1 — MaxEnt (vincolati)

Dieci attributi le cui marginali e incroci riproducono il constraint set
censuario con MRE ≈ 4·10⁻⁴.

| colonna | modalità | note |
|---|---|---|
| `zona` | codice a 8 cifre | quartiere o zona statistica, §3 |
| `quartiere` | stringa | denominazione della zona |
| `sesso` | `M`, `F` | |
| `eta` | `0-8`, `9-14`, `15-24`, `25-34`, `35-49`, `50-64`, `65-74`, `75+` | bin del constraint set |
| `stato_civile` | `celibe_nubile`, `coniugato_unito`, `divorziato_sciolto`, `vedovo` | unioni civili collassate in `coniugato_unito` |
| `cittadinanza` | `ITL`, `FRG` | giuridica; `FRG` include gli apolidi (= `FRGAPO` SDMX = `ST1` sezioni) |
| `istruzione` | `nessun_titolo`, `elementare`, `media`, `diploma`, `laurea_o_its`, `post_laurea` | `laurea_o_its` = triennale + ITS; `post_laurea` = magistrale + ciclo unico + dottorato |
| `condizione` | `occupato`, `in_cerca`, `studente`, `casalinga`, `percettore_pensioni`, `altra_condizione`, `non_applicabile` | `non_applicabile` = under 15 (categoria sostantiva) |
| `background` | `italiano_nativo`, `italiano_rientrato`, `naturalizzato_g2`, `naturalizzato_immigrato`, `straniero_g2`, `straniero_immigrato` | background migratorio: **non** coincide con `cittadinanza` |
| `origine_genitori` | `entrambi_italiani`, `madre_italiana_padre_straniero`, `madre_straniera_padre_italiano`, `entrambi_stranieri`, `non_applicabile` | |

Metà delle 30 combinazioni `background × origine_genitori` è logicamente
impossibile ed è esclusa dal supporto per costruzione.

### 2.2 Anello 2 — condizionali post-hoc

| colonna | modalità | fonte |
|---|---|---|
| `area` | `UE`, `EXTRA_UE`, `NaN` (italiani) | `ST17/18/20/21` **della sezione** |
| `paese` | 143–151 paesi + `Italia` | censimento comunale **× fonte comunale geografica** (§6) |
| `AMBIENTE` | 1–4 + `non_applicabile` | AVQ regionale |
| `FIDUCIA` | 1–2 + `non_applicabile` | AVQ |
| `SALUTE` | 1–5 | AVQ, nessun missing |
| `CRONI` | 1–2 + `non_applicabile` | AVQ |
| `FUMO` | 1–3 + `non_applicabile` | AVQ |
| `MH` | continua 0–100 + `non_applicabile` | AVQ, indice SF-12 salute mentale |
| `BMI` | 1–4 + `non_applicabile` | AVQ, adulti |
| `BMIMIN` | 1–2 + `non_applicabile` | AVQ, **solo minori (~13,6%)** |
| `CPESO` | 1–5 + `non_applicabile` | AVQ, percezione del peso |

**Le nove variabili AVQ arrivano in blocco dallo stesso donatore**
(hot-deck), quindi le correlazioni interne sono preservate per costruzione.

Il pool di donatori è **regionale**: 8.111 per la Lombardia, 4.629 per
l'Emilia-Romagna. Il condizionamento è su `sesso × macroetà × istruzione4`,
con collasso gerarchico progressivo (prima l'istruzione, poi l'età) quando
la cella è rada. Su Parma il 94,8% resta al livello pieno, il 5,2% scende a
`sesso × macroetà`, nessuno arriva al marginale regionale.

**Universi diversi per variabile.** `BMIMIN` copre il 13,6% della
popolazione, `CRONI` il 93,8%, `SALUTE` il 100%. Non esiste un
sottoinsieme di righe completo su tutte. Per le correlazioni usare
`DataFrame.corr(min_periods=...)`, che fa cancellazione pairwise — un
`dropna()` listwise su tutte e nove restituisce **zero righe** (`BMIMIN` e
`FIDUCIA` hanno universi complementari).

**Codifiche AVQ — stato di conoscenza.** Inferite dai marginali, non lette
dal codebook:

| | inferenza | confidenza |
|---|---|---|
| `SALUTE` | 1 = molto bene … 5 = molto male | alta |
| `FUMO` | 1 = fumatore, 2 = ex, 3 = mai | alta |
| `BMI` | 1 = sottopeso … 4 = obeso | alta |
| `MH` | SF-12, più alto = meglio | alta |
| `CRONI` | 1 = nessuna, 2 = almeno una | media |
| `BMIMIN` | 1 = normo/sotto, 2 = sovrappeso/obeso | media |
| `AMBIENTE` | scala a 4 punti, direzione ignota | **bassa** |
| `CPESO` | scala a 5 punti, costrutto ignoto | **bassa** |
| `FIDUCIA` | binaria, ~28% positivi | **da verificare, §8** |

### 2.3 Anello 3 — risoluzione fine

| colonna | tipo | descrizione |
|---|---|---|
| `sezione` | codice a 12 cifre | sezione di censimento (`SEZ21_ID`, basi territoriali 2021) |
| `eta_anni` | 0–100 | età esatta in anni |
| `via` | stringa | odonimo ANNCSU |
| `civico` | stringa | numero + esponente (`12`, `19A`) |
| `lon`, `lat` | float, EPSG:4258 | coordinate del civico (≈ WGS84) |
| `indirizzo_fonte` | `sezione` / `zona` / `convivenza` | provenienza dell'indirizzo |

`indirizzo_fonte` è la colonna di qualità:

| | `sezione` | `zona` | `convivenza` |
|---|---|---|---|
| Brescia | 197.511 (99,62%) | 199 | 549 |
| Parma | 197.601 (99,74%) | 39 | 481 |
| Bologna | 389.432 (99,83%) | 36 | 630 |

- `sezione`: civico estratto dentro la sezione assegnata (caso normale);
- `zona`: la sezione è popolata ma priva di civici ANNCSU → civico preso
  altrove nel quartiere;
- `convivenza`: sezione fittizia `888888x` (senza tetto, convivenze
  anagrafiche). **Nessun indirizzo**, coordinate = centroide della zona.
  Profilo demografico anomalo: a Parma 80% maschi, 73% stranieri.

---

## 3. Livello territoriale — non è uniforme, e i codici si sovrappongono

ISTAT pubblica fino a tre livelli di sub-aree amministrative
(`COM_ASC1/2/3`), ma disponibilità e cardinalità variano per comune. Il
livello è **fissato nel registro** di `gsp_common.py`, non scelto da riga
di comando.

| comune | livello | zone | abitanti/zona | sezioni |
|---|---|---|---|---|
| Brescia | `COM_ASC1` (quartieri) | 33 | 6.008 | 1.822 |
| Parma | `COM_ASC1` (quartieri) | 13 | 15.240 | 1.357 |
| Bologna | `COM_ASC2` (zone statistiche) | 18 | 21.672 | 2.224 |

Bologna usa ASC2 perché i suoi 6 quartieri ASC1 sono troppo pochi; ASC3
(90 aree) è inutilizzabile per la coda di zone minuscole (la più piccola ha
13 abitanti). Parma pubblica **solo** ASC1.

**Conseguenza per il confronto**: la granularità zonale non è comparabile
fra le tre città (fattore 3,6 fra Brescia e Bologna).

### 3.1 I codici ASC si sovrappongono fra livelli

I livelli sono numerati **indipendentemente**. A Bologna `COM_ASC1` va da
`37006011` a `37006016` e `COM_ASC2` da `37006001` a `37006018`: sei codici
esistono a entrambi i livelli con significati diversi.

```
37006011  come ASC1 -> Borgo Panigale-Reno  (quartiere, 61.149 ab.)
37006011  come ASC2 -> Marconi              (zona statistica, 14.687 ab.)
```

**Il codice da solo non identifica la zona**: l'informazione sta nella
colonna da cui proviene. Un merge sul solo codice riesce e restituisce il
nome sbagliato, senza errori né valori mancanti. La guardia
`G.verifica_livello()` intercetta il caso in cui i codici di una
popolazione non appartengano al livello atteso.

### 3.2 Incidente: i nomi delle zone di Bologna erano errati

Fino al 29/07/2026 il dizionario `codice → nome` di Bologna era
**permutato**: 16 codici su 18 portavano il nome di un'altra zona. Nessun
controllo strutturale poteva vederlo — una permutazione resta una biiezione
perfetta — e la gerarchia zona→quartiere, costruita a mano sopra quei nomi,
era coerente con sé stessa.

L'errore è emerso quando il consolidamento ha sostituito la mappa cablata
con una **derivata dalle sezioni**, e le due hanno divergato.
L'identificazione ha usato due vincoli indipendenti che concordano: la
struttura della gerarchia (gruppi di taglia 3, 3, 4, 2, 4, 2, che si
sovrappongono in un solo modo) e i conteggi di stranieri per zona degli
open data comunali (rapporto anagrafe/censimento ~1,05 costante).

I codici ASC2 di Bologna seguono l'**ordine alfabetico** dei nomi,
ignorando gli spazi (per questo `San Ruffillo`, `Santa Viola`, `San Vitale`
finiscono in quell'ordine).

> **Lezione operativa**: le denominazioni delle zone vanno verificate
> contro una fonte esterna prima di fidarsene. I dati numerici erano tutti
> corretti — popolazione, stranieri, varianze, MAE — perché calcolati sui
> codici; sbagliate erano solo le etichette leggibili, cioè esattamente
> ciò che finisce in mappe e tabelle.

### Quartieri di Parma

```
34027001 Parma Centro    34027006 San Pancrazio        34027011 Cittadella
34027002 Oltretorrente   34027007 San Leonardo         34027012 Montanara
34027003 Molinetto       34027008 Cortile San Martino  34027013 Vigatto
34027004 Pablo           34027009 Lubiana
34027005 Golese          34027010 San Lazzaro
```

Le denominazioni di Brescia e Bologna stanno in `gsp_common.py`
(`ASC_NOMI_BRESCIA`, `ASC1_NOMI_BOLOGNA`, `ASC2_NOMI_BOLOGNA`).

---

## 4. `gsp_common.py` — registro e primitive condivise

Consolida i cinque registri di comuni che erano duplicati in altrettanti
script. Principio: nel registro sta **solo ciò che non è derivabile**; il
codice ISTAT contiene già provincia e comune, e i percorsi sono formule.

```python
import gsp_common as G

G.info("034027")          # voce di registro
G.procom("034027")        # 34027
G.cod_prov("034027")      # "034"
G.cod_avq("034027")       # 80   (codice REGMf nei microdati AVQ)
G.livello_col("037006")   # "COM_ASC2"
G.zona_nomi("037006")     # {codice: nome} del livello in uso
G.path_sezioni("034027")  # .../submun/parma_sezioni_2023.csv
G.path_civici("034027")   # .../034_parma_civici_sezioni_asc.csv
G.path_constraints("034027", 2024)
G.largest_remainder(n, pesi)      # allocazione esatta
G.norm_code(serie, comune)        # codice zona -> chiave normalizzata
G.norm_nome("S. Leonardo")        # "sleonardo"
G.paesi_censuari("034027")        # {nome normalizzato: codice ISO}
G.etichette_paese("034027")       # {codice ISO: etichetta ISTAT}
G.risolvi_paese(etichetta, rif)   # etichetta locale -> codice censuario
G.EU27_ISO                        # 27 codici ISO alpha-2 dell'Unione
```

Self-test contro i file su disco:

```bash
python scripts/gsp_common.py --check
python scripts/gsp_common.py --dump-nomi 037006   # nomi zona da zona_2023/
```

Verifica per ogni comune: file sezioni presente, numero di zone al livello
dichiarato uguale a quello atteso, corrispondenza biunivoca codici↔nomi,
presenza dei civici e delle directory di lavoro.

Il consolidamento è stato eseguito come **refactor puro**, verificato per
identità byte-a-byte dell'output su ogni script migrato.

---

## 5. La pipeline

```
fetch_comune.py         SDMX ISTAT -> 11 tavole censuarie comunali
build_sezioni.py        file regionale -> {comune}_sezioni_2023.csv
join_civici_sezioni.py  ANNCSU + shapefile -> civici agganciati alle sezioni
build_zona_tables.py    sezioni -> Z1..Z4, Z6 al livello ASC scelto
build_constraints.py    tavole -> constraint set (blocchi c1..c10)
cs_build.py             -> supporto |X| + vincoli  (cs_K9C.json)
fit_cs.py               -> MaxEnt esatto -> popolazione_K9C.csv
                                                   |
assign_nationality.py   -> + paese (comunale)      |  anello 2
assign_avq.py           -> + 9 variabili AVQ       |
                                                   |
enrich.py               -> + sezione, area, paese (geografico),
   usa opendata_paese.py    eta_anni, indirizzo, lon/lat      anello 3
```

**Anello 1 (MaxEnt).** Massima entropia con vincoli censuari, solver esatto
(L-BFGS su matrice sparsa). Il quartiere è il livello più fine a cui il
censimento pubblica gli *incroci* necessari. `|X|` = 161.280 × n_zone.
MRE(α>0) ≈ 4·10⁻⁴, indipendente da `|X|` su tre ordini di grandezza.

**Anello 2 (condizionali).** Attributi non censuari iniettati post-hoc.
`assign_nationality.py` assegna un `paese` provvisorio a livello comunale;
`enrich.py` lo **ri-assegna** con il condizionale geografico (§6).

**Anello 3 (risoluzione fine).** Sotto il quartiere esistono solo marginali
di sezione, sfruttati come condizionali. Allocazione esatta (largest
remainder) a ogni stadio, mai campionamento multinomiale.

### Perché l'allocazione esatta conta

MAE della popolazione per sezione: **1,36–1,58** su medie di 109–175
abitanti. Un campionamento multinomiale darebbe ≈ 9,6. Il fattore ~6,5
viene dall'allocazione esatta dentro ogni gruppo; il residuo è l'accumulo
di arrotondamenti su una trentina di gruppi per sezione, quindi **non
cresce con la popolazione**.

### Copertura regionale

`join_civici_sezioni.py` è generico per regione:

```bash
python scripts/join_civici_sezioni.py emilia_romagna
python scripts/join_civici_sezioni.py lombardia
python scripts/join_civici_sezioni.py puglia
```

Bounding box derivato dallo shapefile, codici provincia ricavati dai dati,
nomi da `G.PROVINCE_NOMI`. Un contatore segnala i civici che ANNCSU
attribuisce a un comune ma che cadono geometricamente in sezioni di un
altro (42 a Brescia, 14 a Parma, 0 a Bologna): scartati a valle.

---

## 6. Condizionale geografico del paese — attivo

Il censimento pubblica la cittadinanza di dettaglio solo a livello
comunale. Diverse amministrazioni la pubblicano a livello sub-comunale, con
risoluzione molto diversa; `opendata_paese.py` le normalizza e `enrich.py`
le usa per assegnare `paese`.

| tier | livello | fonte | comune |
|---|---|---|---|
| 0 | comune | solo censimento | default, ogni comune nuovo |
| 1 | quartiere | 33 CSV, senza sesso, ~19 paesi + residuale | **Brescia** |
| 2 | zona | parquet con sesso, 155 paesi | **Bologna** |
| 3 | sezione | microdati individuali | **Parma** |

Il flag `--no-tier` di `enrich.py` ripristina il comportamento comunale, ed
è quello con cui è stato prodotto il confronto qui sotto.

**Copertura: 100% dalla geografia su tutte e tre le città, zero fallback.**
Non è fortuna: il peso di sezione per gli stranieri è `P × q` con
`q = ST/P`, quindi nessuno straniero può atterrare dove il censimento non
ne conta, e le celle della tabella sono sempre popolate.

### Formulazione

Le fonti locali sono **anagrafiche** e di data diversa dal censimento
(Bologna 1/1/2024, Parma 1/1/2025, Brescia non dichiarata). Se ne usa la
**forma**, non i livelli:

```
seed        T0(p,s,g) = struttura locale
margine 1   somma_g  T(p,s,g) = censimento comunale (paese, sesso)
margine 2   somma_ps T(p,s,g) = popolazione straniera censuaria di g
```

Due margini censuari con lo stesso totale: sistema sempre risolubile, IPF
converge in 9–88 iterazioni con scarto ~1e-11. Imporre anche i conteggi
locali renderebbe i margini incompatibili (l'anagrafe conta 40.090
stranieri a Brescia, il censimento 37.478) e l'IPF non convergerebbe.

Il gruppo residuale entra nel seed: la sua massa si distribuisce sui paesi
non nominati *in quel geo* proporzionalmente alla quota nazionale. Per
Brescia il residuale cambia contenuto da quartiere a quartiere — è il
complemento della top-19 locale — e l'IPF lo gestisce senza inventare
informazione.

Con la fonte assente il seed è la sola quota nazionale replicata ovunque, e
il risultato coincide **esattamente** con il tier 0.

In assegnazione, `area` viene prima ed è già a risoluzione di sezione;
`paese` è poi estratto dai soli paesi di quell'area (`G.EU27_ISO` per
codice ISO, non per etichetta), con allocazione esatta.

### Riconciliazione delle denominazioni

Quattro vocabolari diversi, riconciliati da `G.SINONIMI_PAESE` (tabella
nazionale, unica per tutte le città) e `G.NON_PAESI`:

| | agganciati | residuo |
|---|---|---|
| Brescia | 89,2% | 4.346 = `ALTRE CITTADINANZE`, **tetto strutturale della fonte** |
| Bologna | 100,0% | 7 persone in paesi assenti dal censimento |
| Parma | 100,0% | 13 persone |

`G.AGGREGATI_PAESE` elenca i codici che **non** sono paesi. Il filtro va
fatto per esclusione e non per forma del codice: i paesi hanno di norma un
ISO alpha-2, ma non sempre (`X95` Kosovo, `XSD_S` Sud Sudan), e alcuni
aggregati **hanno** forma alpha-2 — in particolare `EU` (Unione europea),
che è la somma dei 27 già presenti singolarmente e gonfiava il margine
censuario del 21%.

### Quanto porta la geografia

Frazione di stranieri sintetici che cambia nazionalità passando dal
condizionale comunale a quello geografico, in distanza di variazione
totale. Confrontata con la stessa quantità sotto **ipotesi nulla** (due
permutazioni indipendenti della stessa popolazione: nessuna struttura
geografica, stesse numerosità di cella).

| | \_\_ | osservata | nulla | **eccesso** |
|---|---|---|---|---|
| **Brescia** | per quartiere | 0,197 | 0,094 | **2,08** |
| | per sezione | 0,408 | 0,393 | 1,04 |
| **Parma** | per quartiere | 0,156 | 0,074 | **2,10** |
| | per sezione | 0,530 | 0,412 | **1,29** |
| **Bologna** | per quartiere | 0,169 | 0,066 | **2,57** |
| | per sezione | 0,421 | 0,417 | 1,01 |

Tre letture.

**A livello di quartiere l'informazione è sostanziale e simile ovunque**:
tutte e tre spostano circa 2,1–2,6 volte quanto si sposterebbe per caso.
In termini concreti, ~7.400 stranieri sintetici di Brescia, ~5.400 di Parma
e ~10.000 di Bologna hanno una nazionalità diversa da prima, e il
cambiamento è informativo.

**Una fonte povera ma geograficamente risolta vale quanto una ricca.**
Brescia (19 paesi nominati più un residuo del 10,8%, senza sesso) ottiene
2,08 contro il 2,57 di Bologna (155 paesi con sesso). Per i comuni futuri è
la conclusione operativa: basta una tabella `paese × quartiere`, anche
troncata alle prime venti nazionalità.

**Brescia e Bologna a livello di sezione danno 1,04 e 1,01**, cioè nulla —
correttamente, perché il loro condizionale si ferma alla zona. Questo
**valida la metrica per via negativa**: l'ipotesi nulla predice entro
l'1–4% il comportamento di due sistemi che sappiamo privi di quel segnale.
Il 1,29 di Parma è quindi l'unico eccesso reale sotto il quartiere, ed è la
misura di ciò che i microdati individuali aggiungono.

**Il tier 3 non ripaga la complessità in aggregato**: quasi tutto il
guadagno di Parma è già catturato al livello di quartiere. Resta però
migliore per il singolo individuo, ed è la risoluzione necessaria per
qualunque analisi che incroci nazionalità e posizione fine (per esempio la
distanza da un perimetro di contaminazione).

### I microdati di Parma: condizionale o validazione

I microdati anagrafici di Parma (202.111 righe, una per residente)
contengono `SEZ21`, `Cittad`, `ETA`, `Sesso`, `Ncomp` (ampiezza del nucleo)
e `Relpar` (relazione di parentela). `SEZ21_ID = "34027" + SEZ21.zfill(7)`,
con aggancio al 99,9% degli individui.

Vanno separati **per variabile**, altrimenti si valida il modello contro i
dati che lo hanno generato:

| uso | variabili |
|---|---|
| **condizionale** | `Cittad × SEZ21 × Sesso` |
| **validazione esterna, mai usate per generare** | `ETA × SEZ21`; `Ncomp`, `Relpar`; co-occorrenza di nazionalità nella stessa sezione; `Tipores` |

È l'unica occasione di **validazione esterna vera** che il progetto abbia:
finora si è verificata solo la coerenza interna, cioè che la popolazione
riproduca i vincoli imposti.

---

## 7. Limiti e assunzioni dichiarate

### Assunzioni di indipendenza condizionale

| n. | assunzione | dove |
|---|---|---|
| (4') | `paese ⊥ tutto \| (area, sesso, geo)` — con `geo` = quartiere, zona o sezione secondo il tier | nazionalità, §6 |
| (6) | `target AVQ ⊥ tutto \| (sesso, macroetà, istruzione4, regione)` | AVQ |
| (8) | `sezione ⊥ (istruzione, condizione, background) \| (zona, sesso, età3, cittadinanza)` | anello 3 |
| (9) | entro il quinquennio, l'età segue la distribuzione **comunale** per anno singolo | anello 3 |
| (10) | l'indirizzo è uniforme fra i civici della sezione | anello 3 |
| (11) | **nessuna struttura familiare** | anello 3 — attaccabile con i microdati di Parma |

La (4') sostituisce la vecchia (4) `paese ⊥ geografia | (area, sesso)`. Per
Brescia resta parzialmente in vigore sul 10,8% di stranieri che ricadono
nella categoria `ALTRE CITTADINANZE`: per loro il paese è estratto dalla
quota nazionale entro il gruppo residuale del proprio quartiere.

### Limiti della risoluzione per età

- **L'istruzione ha risoluzione effettiva di 4 classi d'età, non 8.** Il
  vincolo censuario usa `Y9-24`, `Y25-49`, `Y50-64`, `Y_GE65`. Dentro ogni
  classe la distribuzione è ottenuta per **IPF con soglie minime di
  conseguimento** (`elementare` 10, `media` 13, `diploma` 18,
  `laurea_o_its` 20, `post_laurea` 22): i margini censuari sono preservati e
  le combinazioni impossibili azzerate.
  *Prima della correzione del 29/07/2026 il 32,8% dei 9-14enni risultava
  diplomato o laureato: il MaxEnt applicava alla classe `Y9-24` una
  distribuzione uniforme per età.*
- **Resta sovrastimata `media` nel bin `9-14`**: la licenza media si
  consegue a 14 anni, quindi riguarda circa un sesto del bin.
- **Effetto coorte perso fra `65-74` e `75+`**: `Y_GE65` li rende
  indistinguibili.
- **Il background migratorio ha risoluzione di zona**, non di sezione.

### Convenzioni per "assente" — non uniformate

| forma | dove |
|---|---|
| `non_applicabile` (stringa) | `condizione`, `origine_genitori`, 8 delle 9 AVQ |
| `NaN` | `area`, `via`, `civico` |
| nessuna | `SALUTE`, `paese` (= `Italia` per gli italiani) |

`non_applicabile` è a volte una **categoria sostantiva** (la condizione
professionale degli under-15) e a volte un **missing** (il `BMIMIN` degli
adulti).

---

## 8. Punti aperti

- **Codebook AVQ.** `AMBIENTE` e `CPESO` non sono note.
- **`FIDUCIA` potrebbe essere il costrutto sbagliato.** Binaria con ~28% di
  positivi: è il profilo della **fiducia interpersonale generalizzata**,
  non della fiducia istituzionale — che è il costrutto centrale per la
  comunicazione del rischio. Da verificare sul codebook; in alternativa
  aggiungere le variabili AVQ di fiducia istituzionale, o passare a ESS.
- **Provenienza del paese non tracciata.** Non esiste una colonna
  `paese_fonte` analoga a `indirizzo_fonte`: oggi il tier è uniforme per
  comune (100% dalla geografia), ma se in futuro comparissero fallback
  andrebbe registrata.
- **Struttura familiare.** `Ncomp` e `Relpar` dei microdati di Parma, più
  `cens_posizione_famiglia` (scaricata e mai usata) per gli altri comuni.
- **Convivenze.** Riprodotte con scarto ±2–5%, il peggiore fra tutte le
  celle: un tilt moltiplicativo su classi larghe fatica su un profilo così
  estremo.
- **K10C.** Esiste solo per Brescia, con `settore` come decimo attributo, e
  porta ancora l'istruzione **pre-correzione**: va rigenerato se usato.
- **San Vito dei Normanni** (`074017`): registrato, civici presenti, file
  sezioni non ancora generato. `COM_ASC1` ha un solo valore, quindi resterà
  un comune **senza articolazione zonale** (`"livello": None`).
- **Confronto fra città.** Le tre popolazioni usano condizionali di
  risoluzione diversa (tier 1, 2, 3) su partizioni di taglia diversa. Per
  un confronto rigoroso conviene rigenerarle a una risoluzione comune —
  il quartiere — dato che a quel livello gli eccessi sono simili (2,1–2,6).

---

## 9. Dove sono i dati reali, per il confronto

```
{COMUNE}/constraints_2024/
    cs_K9C.json          vincoli con alpha target, categories, domain_sizes,
                         zona_nomi. E' la verita' di riferimento dell'anello 1.
    targets_K9C.json     tabelle target per blocco (A, B, C, D, E, F, S...)
    fit_K9C.json         lambdas, MRE, entropia, supporto
    manifest.json        fonte e tipo (hard/soft) di ogni blocco

{COMUNE}/zona_2023/
    z1..z4, z6, zona_nomi   marginali censuarie per zona

data/submun/{slug}_sezioni_2023.csv
    verita' per sezione: P1 (popolazione), ST1 (stranieri), ST16/ST19
    (UE/extra-UE), P30-P45 e P67-P82 (sesso x quinquennio),
    ST25-ST30 (stranieri per sesso x eta3)

data/opendata/{COMUNE}/
    fonti comunali per il condizionale geografico del paese (§6)
```

Per rigenerare la versione senza condizionale geografico, utile ai
confronti:

```bash
python scripts/enrich.py 037006 --anno 2024 --no-tier \
    --out popolazione_K9C_avq_full_tier0.csv
```

Estrazione degli α target:

```python
import json, os, sys
sys.path.insert(0, os.path.expanduser("~/progetti/gsp/scripts"))
import gsp_common as G
cs = json.load(open(os.path.join(G.path_constraints("034027", 2024),
                                 "cs_K9C.json")))
vars_, cats = cs["vars"], cs["categories"]
# ogni vincolo: {'attrs': [indici di vars_], 'vals': [indici di cats], 'alpha': ...}
```

### Geometrie per la visualizzazione

```
data/geodata/{regione}/R{NN}_21/SHP/R{NN}_21_WGS84.shp
    R03 Lombardia    R08 Emilia-Romagna    R16 Puglia
    CRS: EPSG:32632 — riproiettare a EPSG:4326 per il web
```

Lo shapefile contiene le colonne `COM_ASC1/2/3`, quindi **i poligoni delle
zone si ottengono per dissolve delle sezioni**, senza uno shapefile ASC
separato:

```python
import geopandas as gpd, sys, os
sys.path.insert(0, os.path.expanduser("~/progetti/gsp/scripts"))
import gsp_common as G

col = G.livello_col("034027")
s = gpd.read_file(G.path_shp("emilia_romagna"))
s = s[s.PRO_COM == G.procom("034027")]
zone = s.dissolve(by=col).reset_index().to_crs("EPSG:4326")
zone["nome"] = zone[col].astype("Int64").astype(str).map(G.zona_nomi("034027"))
```

**Per Bologna `G.livello_col("037006")` è `COM_ASC2`**: un dissolve su
`COM_ASC1` darebbe 6 poligoni invece di 18, e i codici — che si
sovrappongono fra livelli (§3.1) — mapperebbero comunque su dei nomi,
sbagliati.

Attenzione: lo shapefile regionale contiene **più sezioni** del file dati
2023 (quelle senza popolazione residente pubblicata). Il collegamento su
`SEZ21_ID` è però completo: tutte le sezioni dei dati 2023 hanno geometria.

---

## 10. Riepilogo numerico

Esecuzioni del 29 luglio 2026, successive alla correzione dell'istruzione,
dei nomi di Bologna e all'attivazione dei tier.

| | Brescia | Parma | Bologna |
|---|---|---|---|
| codice ISTAT | `017029` | `034027` | `037006` |
| regione (AVQ) | Lombardia (30) | Emilia-Romagna (80) | Emilia-Romagna (80) |
| popolazione | 198.259 | 198.121 | 390.098 |
| zone | 33 (ASC1) | 13 (ASC1) | 18 (ASC2) |
| sezioni | 1.822 | 1.357 | 2.224 |
| sezioni occupate | 1.773 | 1.313 | 2.152 |
| civici ANNCSU | 49.730 | 35.826 | 77.595 |
| di cui su base provinciale | 415.456 | 128.366 | 315.505 |
| stranieri (censimento) | 37.478 | 34.436 | 58.963 |
| stranieri (sintetici) | 37.475 | 34.434 | 59.130 |
| quota stranieri | 18,9% | 17,4% | 15,1% |
| donatori AVQ | 8.111 | 4.629 | 4.629 |
| riuso medio donatore | 24× | 43× | 84× |
| supporto \|X\| K9C | 5.322.240 | 2.096.640 | 2.903.040 |
| tier paese (§6) | 1 (quartieri) | 3 (sezione) | 2 (zone) |

**Il riuso dei donatori è un tetto strutturale**: nella popolazione di
Bologna esistono al massimo 4.629 vettori psicografici distinti,
indipendentemente dai 390.098 individui. La diversità dell'anello 2 è
limitata dalla taglia del campione AVQ regionale, non dalla popolazione.

### Validazione per sezione

| | sezioni | media/sez | MAE pop. | corr | MAE stranieri | corr | MAE UE | corr |
|---|---|---|---|---|---|---|---|---|
| Brescia | 1.822 | 108,8 | 1,58 | 0,9998 | 0,98 | 0,9989 | 0,13 | 0,9976 |
| Parma | 1.357 | 146,0 | 1,43 | 0,9999 | 1,13 | 0,9985 | 0,16 | 0,9980 |
| Bologna | 2.224 | 175,4 | 1,36 | 0,9999 | 1,08 | 0,9983 | 0,17 | 0,9982 |

I totali comunali coincidono esattamente con il censimento. Gli scarti sui
totali di stranieri (−3, −2, +167) sono entro 0,7 σ del rumore multinomiale
di estrazione della popolazione, non dell'anello 3.

### Struttura spaziale: la sezione conta molto più della zona

Decomposizione della varianza della quota UE fra stranieri, al netto della
discretizzazione dei piccoli conteggi. **Calcolata dal file sezioni**, cioè
dalla verità censuaria: non dipende dalla popolazione sintetica ed è
invariata dalla v1.0.

| | var **tra** zone | var reale **dentro** | sovradispersione | rapporto |
|---|---|---|---|---|
| Brescia (33 zone) | 0,00168 | 0,00991 | 2,89× | **5,9×** |
| Parma (13 zone) | 0,00110 | 0,01249 | 3,50× | **11,3×** |
| Bologna (18 zone) | 0,00072 | 0,01124 | 3,04× | **15,7×** |

**Condizionare sul quartiere perde l'85–94% del segnale compositivo.** Il
risultato è monotono nella dimensione media delle zone ed è confermato su
tre partizioni diverse.

### Validazione esterna puntuale

| | fonte comunale | sintetico (cens. 2023) | rapporto |
|---|---|---|---|
| Primo Maggio (Brescia), quota stranieri | 0,329 | 0,293 | 1,12 |
| Bologna, quota UE fra stranieri | 0,214 | 0,213 | 1,00 |

### Un fatto rilevante per il progetto Caffaro

Classifica di Brescia per quota di stranieri:

```
Fiumicello           0,368        Buffalora          0,088
Centro Storico Nord  0,314        Villaggio Violino  0,073
Primo Maggio         0,293
```

**Fiumicello, uno dei due quartieri della `ZonaCaffaro`, è quello con la
più alta quota di stranieri della città** — il doppio della media comunale.
Lingua, canali informativi e fiducia nelle istituzioni sono fortemente
differenziati su quell'asse, ma l'anello 2 condiziona `FIDUCIA` e
`AMBIENTE` su sesso, età e istruzione e **non** su cittadinanza: oggi la
popolazione sintetica di Fiumicello ha attitudini indistinguibili da quelle
di Mompiano a parità di profilo demografico.

---

## 11. Un principio metodologico ricorrente

**Ogni metrica che scala con la numerosità di cella va rapportata alla
propria ipotesi nulla prima di essere confrontata fra configurazioni
diverse.**

Il problema si è presentato tre volte con la stessa forma:

1. **Varianza compositiva della quota UE** (§10). Con 30 stranieri per
   sezione la varianza fra sezioni è alta per pura combinatoria. Isolata
   con un test di sovradispersione: osservato / atteso sotto assegnazione
   casuale entro zona.
2. **Distanza compositiva fra tier** (§6). Il 0,569 grezzo di Parma è per
   il 79% discretizzazione; l'eccesso reale è 1,29.
3. **Pavimento MRE del PCD** (`nota_mre_floor_v01.tex`). La formula
   `1/(2√N)` del paper GibbsPCD confonde errore assoluto e relativo; il
   pavimento corretto dipende dalla rarità dei vincoli.

In tutti e tre i casi la metrica grezza ordinava le configurazioni in modo
diverso — e talvolta inverso — rispetto alla metrica corretta.

Corollario operativo: quando è disponibile una configurazione in cui il
segnale è **noto essere assente**, va usata come controllo. In §6, Brescia
e Bologna a livello di sezione danno eccesso 1,04 e 1,01: la metrica è
tarata correttamente proprio perché lì non trova nulla.

---

## Changelog

**v1.2 — 29/07/2026**
Condizionale geografico del paese collegato e attivo su tutte e tre le
città (§6), con misura dell'eccesso rispetto all'ipotesi nulla. §10 con i
numeri delle esecuzioni correnti. Nuova §11 sul principio dell'ipotesi
nulla. Assunzione (4) sostituita dalla (4').

**v1.1 — 29/07/2026**
Consolidamento in `gsp_common.py`. Correzione dei nomi delle zone di
Bologna e dell'istruzione nei bin infantili. Sistema a tier costruito.
`join_civici_sezioni.py` generalizzato a tre regioni.

**v1.0 — 28/07/2026**
Prima stesura.
