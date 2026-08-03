# Popolazioni sintetiche GSP — documento di riferimento

**Versione 1.1 — 29 luglio 2026**
Descrive i file `popolazione_K9C_avq_full.csv` per Brescia, Parma e Bologna:
come caricarli, cosa contengono, come sono stati costruiti, quali limiti
dichiarati portano con sé e dove trovare i dati reali per il confronto.

> **Novità rispetto alla v1.0** (changelog in fondo): modulo condiviso
> `gsp_common.py`; correzione dei nomi delle zone di Bologna (16 su 18
> erano errati); correzione dell'istruzione nei bin infantili; sistema a
> tier per il condizionale geografico del paese di cittadinanza
> (**costruito, non ancora collegato**); riconciliazione delle
> denominazioni di paese fra quattro vocabolari.

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
| `paese` | 143–151 paesi + `Italia` | censimento **comunale** (§6: il condizionale geografico è pronto ma non collegato) |
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
| Brescia | 99,62% | 200 | 545 |
| Parma | 99,74% | 39 | 479 |
| Bologna | 99,83% | 36 | 633 |

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
G.risolvi_paese(etichetta, rif)   # etichetta locale -> codice censuario
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
assign_nationality.py   -> + paese                 |  anello 2
assign_avq.py           -> + 9 variabili AVQ       |
                                                   |
enrich.py               -> + sezione, area, eta_anni, indirizzo, lon/lat
                                                      anello 3
```

**Anello 1 (MaxEnt).** Massima entropia con vincoli censuari, solver esatto
(L-BFGS su matrice sparsa). Il quartiere è il livello più fine a cui il
censimento pubblica gli *incroci* necessari. `|X|` = 161.280 × n_zone.
MRE(α>0) ≈ 4·10⁻⁴, indipendente da `|X|` su tre ordini di grandezza.

**Anello 2 (condizionali).** Attributi non censuari iniettati post-hoc.

**Anello 3 (risoluzione fine).** Sotto il quartiere esistono solo marginali
di sezione, sfruttati come condizionali. Allocazione esatta (largest
remainder) a ogni stadio, mai campionamento multinomiale.

### Perché l'allocazione esatta conta

MAE della popolazione per sezione: **1,4–1,6** su medie di 109–175
abitanti. Un campionamento multinomiale darebbe ≈ 9,6. Il fattore 6,6 viene
dall'allocazione esatta dentro ogni gruppo; il residuo è l'accumulo di
arrotondamenti su una trentina di gruppi per sezione, quindi **non cresce
con la popolazione**.

### Copertura regionale

`join_civici_sezioni.py` è generico per regione:

```bash
python scripts/join_civici_sezioni.py emilia_romagna
python scripts/join_civici_sezioni.py lombardia
python scripts/join_civici_sezioni.py puglia
```

Il bounding box di validità delle coordinate è derivato dallo shapefile, i
codici provincia dai dati, i nomi da `G.PROVINCE_NOMI`. Un contatore
segnala i civici che ANNCSU attribuisce a un comune ma che cadono
geometricamente in sezioni di un altro (42 a Brescia, 14 a Parma, 0 a
Bologna): vengono scartati a valle.

---

## 6. Condizionale geografico del paese — sistema a tier

> **Stato: costruito e validato, NON ancora collegato a `enrich.py`.**
> I file `_full.csv` attuali hanno `paese` condizionato al solo
> `(area, sesso)` comunale, come da assunzione (4).

Diversi comuni pubblicano la cittadinanza a livello sub-comunale, con
risoluzione molto diversa. Il modulo `opendata_paese.py` li normalizza in
un formato unico.

| tier | livello | fonte | comune |
|---|---|---|---|
| 0 | comune | solo censimento | default, ogni comune nuovo |
| 1 | quartiere | 33 CSV, senza sesso, ~19 paesi + residuale | **Brescia** |
| 2 | zona | parquet con sesso, 155 paesi | **Bologna** |
| 3 | sezione | microdati individuali, 147 paesi | **Parma** |

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

Distanza in variazione totale fra la composizione per paese di ciascuna
unità e quella comunale, pesata per popolazione. Il valore grezzo **non è
confrontabile fra tier**: cresce meccanicamente al calare della numerosità
di cella. Va rapportato alla stessa metrica sotto ipotesi nulla
(composizione comunale, stesse numerosità).

| | unità | stranieri/unità | osservata | nulla | **eccesso** |
|---|---|---|---|---|---|
| Bologna | 18 zone | 3.275 | 0,179 | 0,068 | **2,64** |
| Brescia | 33 quartieri | 1.136 | 0,188 | 0,102 | **1,85** |
| Parma | 1.357 sezioni | 30 | 0,569 | 0,447 | **1,27** |

Sulle distanze grezze Parma sembra tre volte più informativa; sull'eccesso
è l'ultima. Il suo 0,569 è per il 79% discretizzazione: 30 stranieri su 146
nazionalità producono composizioni estreme anche in assenza di
segregazione.

**Questo non rende l'assegnazione di Parma peggiore**: la tabella `T`
incorpora la struttura vera a livello di sezione, e l'IPF applica già lo
shrinkage corretto verso la composizione comunale nelle celle rade. La
metrica aggregata non sa distinguere segnale da discretizzazione, ed è un
limite della metrica, non del condizionale.

> **Principio, seconda occorrenza nel progetto**: una metrica che scala con
> la numerosità di cella non è confrontabile fra configurazioni diverse.
> Vale per la distanza compositiva come per il pavimento MRE del PCD
> (vedi `nota_mre_floor_v01.tex`).

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
| (4) | `paese ⊥ geografia | (area, sesso)` | nazionalità — **rimovibile con i tier 1-3, §6** |
| (6) | `target AVQ ⊥ tutto | (sesso, macroetà, istruzione4, regione)` | AVQ |
| (8) | `sezione ⊥ (istruzione, condizione, background) | (zona, sesso, età3, cittadinanza)` | anello 3 |
| (9) | entro il quinquennio, l'età segue la distribuzione **comunale** per anno singolo | anello 3 |
| (10) | l'indirizzo è uniforme fra i civici della sezione | anello 3 |
| (11) | **nessuna struttura familiare** | anello 3 — attaccabile con i microdati di Parma |

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

- **Collegare i tier a `enrich.py`.** `opendata_paese.tabella_paese()`
  restituisce `T(paese, sesso, geo)`; va sostituita a `tab_paesi()`, con il
  paese ristretto ai paesi dell'`area` già assegnata dalla sezione, e le
  tre popolazioni rigenerate.
- **Codebook AVQ.** `AMBIENTE` e `CPESO` non sono note.
- **`FIDUCIA` potrebbe essere il costrutto sbagliato.** Binaria con ~28% di
  positivi: è il profilo della **fiducia interpersonale generalizzata**,
  non della fiducia istituzionale — che è il costrutto centrale per la
  comunicazione del rischio. Da verificare sul codebook; in alternativa
  aggiungere le variabili AVQ di fiducia istituzionale, o passare a ESS.
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

| | Brescia | Parma | Bologna |
|---|---|---|---|
| codice ISTAT | `017029` | `034027` | `037006` |
| regione (AVQ) | Lombardia (30) | Emilia-Romagna (80) | Emilia-Romagna (80) |
| popolazione | 198.259 | 198.121 | 390.098 |
| zone | 33 (ASC1) | 13 (ASC1) | 18 (ASC2) |
| sezioni | 1.822 | 1.357 | 2.224 |
| sezioni occupate | 1.774 | 1.313 | 2.152 |
| civici ANNCSU | 49.730 | 35.826 | 77.595 |
| stranieri (censimento) | 37.478 | 34.436 | 58.963 |
| quota stranieri | 18,9% | 17,4% | 15,1% |
| donatori AVQ | 8.111 | 4.629 | 4.629 |
| riuso medio donatore | 24× | 43× | 84× |
| supporto \|X\| K9C | 5.322.240 | 2.096.640 | 2.903.040 |
| tier paese (§6) | 1 | 3 | 2 |

**Il riuso dei donatori è un tetto strutturale**: nella popolazione di
Bologna esistono al massimo 4.629 vettori psicografici distinti,
indipendentemente dai 390.098 individui. La diversità dell'anello 2 è
limitata dalla taglia del campione AVQ regionale, non dalla popolazione.

### Validazione per sezione

| | sezioni | MAE pop. | corr | MAE stranieri | corr |
|---|---|---|---|---|---|
| Brescia | 1.822 | 1,58 | 0,9998 | 0,98 | 0,9990 |
| Parma | 1.357 | 1,45 | 0,9999 | 1,12 | 0,9985 |
| Bologna | 2.224 | 1,36 | 0,9999 | 1,11 | 0,9982 |

I totali comunali coincidono esattamente con il censimento. Gli scarti sui
totali di stranieri (+53, +74, +54) sono entro 0,5 σ del rumore
multinomiale di estrazione della popolazione, non dell'anello 3.

### Struttura spaziale: la sezione conta molto più della zona

Decomposizione della varianza della quota UE fra stranieri, al netto della
discretizzazione dei piccoli conteggi:

| | var **tra** zone | var reale **dentro** | sovradispersione | rapporto |
|---|---|---|---|---|
| Brescia (33 zone) | 0,00168 | 0,00991 | 2,89× | **5,9×** |
| Parma (13 zone) | 0,00110 | 0,01249 | 3,50× | **11,3×** |
| Bologna (18 zone) | 0,00072 | 0,01124 | 3,04× | **15,7×** |

**Condizionare sul quartiere perde l'85–94% del segnale compositivo.** Il
risultato è monotono nella dimensione media delle zone ed è confermato su
tre partizioni diverse.

### Validazione esterna puntuale

L'unico confronto finora eseguito contro fonti indipendenti:

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

## Changelog

**v1.1 — 29/07/2026**
Consolidamento in `gsp_common.py`, eseguito come refactor puro e verificato
per identità byte-a-byte su ogni script migrato. Correzione dei nomi delle
zone di Bologna (§3.2) e dell'istruzione nei bin infantili (§7). Sistema a
tier per il condizionale geografico del paese, costruito e validato ma non
ancora collegato (§6). `join_civici_sezioni.py` generalizzato a tre
regioni. Nuove sezioni: §3.1 codici ASC sovrapposti, §4 modulo comune,
§6 tier.

**v1.0 — 28/07/2026**
Prima stesura.

---

*Le cifre di validazione dell'anello 3 (MAE, quote di `indirizzo_fonte`,
decomposizione della varianza) provengono dalle esecuzioni del 28 luglio
2026, precedenti la correzione dell'istruzione e dei nomi di Bologna. Le
costanti strutturali non cambiano; i MAE possono differire nell'ultima
cifra. Rileggere i log più recenti per i valori aggiornati.*
