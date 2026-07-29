# Popolazioni sintetiche GSP — documento di riferimento

**Versione 1.5 — 29 luglio 2026**
Descrive i file `popolazione_K9C_avq_full.csv` per Brescia, Parma, Bologna e
Modena: come caricarli, cosa contengono, come sono stati costruiti, quali
limiti dichiarati portano con sé e dove trovare i dati reali per il
confronto.

*Questa versione sostituisce tutte le precedenti.*

---

## 1. I file

```
~/progetti/gsp/data/comuni/{COMUNE}/constraints_2024/popolazione_K9C_avq_full.csv
```

| comune | codice | individui | attributi | tier paese |
|---|---|---|---|---|
| Brescia | `017029` | 198.259 | 40 | 1 |
| Parma | `034027` | 198.121 | 40 | 3 |
| Bologna | `037006` | 390.098 | 40 | 2 |
| Modena | `036023` | 184.597 | 40 | 0 |

Totale 971.075 individui sintetici, ciascuno con indirizzo civico e
coordinate geografiche.

### Caricamento

Ci sono tre trappole di tipo. Questo snippet le gestisce tutte:

```python
import pandas as pd, os

AVQ = ["AMBIENTE", "FIDUCIA", "SALUTE", "CRONI", "FUMO", "MH",
       "BMI", "BMIMIN", "CPESO",
       "PUNTIFI1", "PUNTIFI2", "PUNTIFI3", "PUNTIFI4", "PUNTIFI5",
       "PUNTIFI6", "PUNTIFI7", "PUNTIFI8", "PUNTIFI10", "PUNTIFI12",
       "PUNTIFI13", "VOTOUSL"]

def carica(comune, anno=2024):
    f = os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}/"
        f"popolazione_K9C_avq_full.csv")
    p = pd.read_csv(f, low_memory=False, dtype={
        "zona": "string",        # 34027001: NON leggere come int
        "sezione": "string",     # 340270000994: 12 cifre
        "civico": "string",      # '19A': numero + esponente
    })
    for c in AVQ:
        p[c + "_num"] = pd.to_numeric(p[c], errors="coerce")
    return p
```

In alternativa, tutti i percorsi e i registri stanno in `gsp_common.py` (§4).

**Trappole:**

1. `zona` e `sezione` sono codici, non numeri.
2. Le variabili AVQ sono **stringhe** perché mescolano codici numerici e
   `non_applicabile` — tranne `SALUTE`, unica senza missing strutturali.
3. `area` usa `NaN` per gli italiani, non `non_applicabile` (§7).

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
| `cittadinanza` | `ITL`, `FRG` | giuridica; `FRG` include gli apolidi |
| `istruzione` | `nessun_titolo`, `elementare`, `media`, `diploma`, `laurea_o_its`, `post_laurea` | `laurea_o_its` = triennale + ITS; `post_laurea` = magistrale + ciclo unico + dottorato |
| `condizione` | `occupato`, `in_cerca`, `studente`, `casalinga`, `percettore_pensioni`, `altra_condizione`, `non_applicabile` | `non_applicabile` = under 15 (categoria sostantiva) |
| `background` | `italiano_nativo`, `italiano_rientrato`, `naturalizzato_g2`, `naturalizzato_immigrato`, `straniero_g2`, `straniero_immigrato` | **non** coincide con `cittadinanza` |
| `origine_genitori` | `entrambi_italiani`, `madre_italiana_padre_straniero`, `madre_straniera_padre_italiano`, `entrambi_stranieri`, `non_applicabile` | |

Metà delle 30 combinazioni `background × origine_genitori` è logicamente
impossibile ed è esclusa dal supporto per costruzione.

### 2.2 Anello 2 — AVQ e nazionalità

| colonna | modalità | fonte |
|---|---|---|
| `area` | `UE`, `EXTRA_UE`, `NaN` (italiani) | `ST17/18/20/21` **della sezione** |
| `paese` | 143–151 paesi + `Italia` | censimento comunale **× fonte comunale geografica** (§6) |

**Ventuno variabili AVQ**, tutte assegnate **in blocco dallo stesso
donatore** (hot-deck), quindi con correlazioni interne preservate per
costruzione. Il pool è **regionale**: 8.111 donatori per la Lombardia,
4.629 per l'Emilia-Romagna, con condizionamento su
`sesso × macroetà × istruzione4` e collasso gerarchico progressivo.

#### Codifiche — risolte sul tracciato ufficiale

| variabile | domanda | codifica |
|---|---|---|
| `AMBIENTE` | **soddisfazione per la situazione ambientale (aria, acqua, ecc.) della zona in cui vive** | 1 = molto … 4 = per niente |
| `FIDUCIA` | *"Lei pensa che ci si possa fidare della maggior parte della gente oppure bisogna stare molto attenti?"* | **1 = ci si può fidare** (24,5%), 2 = stare attenti |
| `SALUTE` | salute percepita | 1 = molto bene … 5 = molto male |
| `CRONI` | malattie croniche o problemi di salute ≥ 6 mesi | 1 = no, 2 = sì |
| `FUMO` | abitudine al fumo | 1 = fumatore, 2 = ex, 3 = mai |
| `MH` | indice SF-12 di salute mentale | continua 0–100, più alto = meglio |
| `BMI` | indice di massa corporea, adulti | 1 = sottopeso … 4 = obeso |
| `BMIMIN` | IOTF 2012, **3–17 anni** | 1 = normo/sotto, 2 = sovrappeso/obeso |
| `CPESO` | **frequenza con cui controlla il proprio peso** | 1 = più spesso … 5 = mai |
| `PUNTIFI*` | *"quanto si fida delle seguenti istituzioni"* | **0–10**, più alto = più fiducia |
| `VOTOUSL` | giudizio complessivo sul servizio ricevuto nell'ASL | 0–10 |

> **`FIDUCIA` è fiducia interpersonale generalizzata**, non istituzionale:
> è l'item classico di Rosenberg (WVS, ESS, GSS). La **polarità invertita**
> (1 = fiducia) è stata dedotta dal segno negativo delle correlazioni con
> `PUNTIFI`.

> **`AMBIENTE` è il costrutto più rilevante per il lavoro Caffaro**: non è
> preoccupazione ambientale generica ma **valutazione della qualità
> ambientale del proprio luogo di residenza**. Vedi §8.

#### La batteria di fiducia istituzionale

| variabile | istituzione | copertura |
|---|---|---|
| `PUNTIFI1` | Parlamento italiano | alta |
| `PUNTIFI2` | sistema giudiziario | alta |
| `PUNTIFI3` | forze dell'ordine | alta |
| `PUNTIFI4` | partiti politici | alta |
| `PUNTIFI5` | Parlamento europeo | alta |
| `PUNTIFI8` | **Governo regionale** | alta |
| `PUNTIFI10` | **Governo comunale** | alta |
| `PUNTIFI12` | vigili del fuoco | alta |
| `PUNTIFI6` | Presidente della Repubblica | ridotta |
| `PUNTIFI7` | Governo italiano | ridotta |
| `PUNTIFI13` | banche | ridotta |
| `VOTOUSL` | ASL (esperienza diretta) | bassa |

Struttura interna, replicata nel sintetico entro ±0,01:

```
PUNTIFI1  - PUNTIFI7   (Parlamento - Governo)      0,863
PUNTIFI8  - PUNTIFI10  (Regione - Comune)          0,812
PUNTIFI1  - PUNTIFI5   (Parlamento IT - UE)        0,792
PUNTIFI3  - PUNTIFI12  (forze ordine - vigili f.)  0,609
```

**Due fattori distinti.** Forze dell'ordine e vigili del fuoco correlano
0,61 fra loro ma solo 0,14–0,27 con le istituzioni politiche: è la
separazione fra fiducia nei *servizi* e fiducia nella *politica*.

**Regione e Comune sono quasi indistinguibili** (0,812). Per Caffaro
significa che chi diffida del Comune diffida anche di ARPA e ATS, che sono
articolazioni regionali: non esiste un canale istituzionale alternativo.

Medie AVQ 2024, nazionali: vigili del fuoco 8,10 · forze dell'ordine 6,70 ·
ASL 6,34 · **Governo comunale 5,13** · **Governo regionale 4,65**.

#### Copertura: tre fasce

Il modulo AVQ **ruota fra le annate**. `assign_avq.py` distingue variabili
*necessarie* (se mancano, l'annata si scarta) da *opzionali*
(`--targets-opt`, prese dove ci sono): così le dodici nuove non
costringono a dimezzare il pool di donatori.

| fascia | variabili | copertura tipica |
|---|---|---|
| base (2023+2024) | le 9 originali, `PUNTIFI1,2,3,4,5,8,10,12` | 86–88% |
| solo 2024 | `PUNTIFI6,7,13` | 42–43% |
| solo 2024 × utenti ASL | `VOTOUSL` | 15–20% |

Il missing della seconda e terza fascia è **planned missing**: dipende
dall'annata del donatore, non dall'individuo.

**Universi diversi per variabile.** `BMIMIN` copre il 13,6% (minori 3–17),
`SALUTE` il 100%. Un `dropna()` listwise su tutte e 21 restituisce **zero
righe**. Usare `DataFrame.corr(min_periods=...)`, e vedere §11.

### 2.3 Anello 3 — risoluzione fine

| colonna | tipo | descrizione |
|---|---|---|
| `sezione` | codice a 12 cifre | sezione di censimento (`SEZ21_ID`, basi 2021) |
| `eta_anni` | 0–100 | età esatta in anni |
| `via` | stringa | odonimo ANNCSU |
| `civico` | stringa | numero + esponente (`12`, `19A`) |
| `lon`, `lat` | float, EPSG:4258 | coordinate del civico (≈ WGS84) |
| `indirizzo_fonte` | `sezione` / `zona` / `convivenza` | provenienza dell'indirizzo |

| | `sezione` | `zona` | `convivenza` |
|---|---|---|---|
| Brescia | 197.511 (99,62%) | 199 | 549 |
| Parma | 197.601 (99,74%) | 39 | 481 |
| Bologna | 389.432 (99,83%) | 36 | 630 |
| Modena | 184.269 (99,82%) | **278** | **50** |

- `zona`: la sezione è popolata ma priva di civici ANNCSU. Modena ha il
  valore più alto in termini relativi (0,15%), pur avendo **più civici di
  Brescia** (60.488 contro 49.730) a fronte di meno abitanti: non è
  scarsità complessiva ma distribuzione;
- `convivenza`: sezione fittizia `888888x`. **Nessun indirizzo**,
  coordinate = centroide della zona. Modena ne ha un ordine di grandezza
  meno delle altre (50 contro 481–630).

---

## 3. Livello territoriale — non è uniforme, e i codici si sovrappongono

| comune | livello | zone | abitanti/zona | sezioni | sez./zona |
|---|---|---|---|---|---|
| Brescia | `COM_ASC1` (quartieri) | 33 | 6.008 | 1.822 | 55 |
| Parma | `COM_ASC1` (quartieri) | 13 | 15.240 | 1.357 | 104 |
| Bologna | `COM_ASC2` (zone statistiche) | 18 | 21.672 | 2.224 | 124 |
| Modena | `COM_ASC1` (quartieri) | **4** | **46.149** | 2.186 | **546** |

Bologna usa ASC2 perché i suoi 6 quartieri ASC1 sono troppo pochi; ASC3
(90 aree) è inutilizzabile per la coda di zone minuscole. Parma e Modena
pubblicano **solo** ASC1. Il livello è **fissato nel registro** di
`gsp_common.py`, non scelto da riga di comando.

**Le quattro zone di Modena sono la partizione più grossolana in
pipeline**, meno informativa dei 6 quartieri ASC1 di Bologna che avevamo
scartato. Si usano comunque: servono ai vincoli Z del MaxEnt e danno un
`quartiere` leggibile, mentre il lavoro geografico lo fa l'anello 3 (§10).

### 3.1 I codici ASC si sovrappongono fra livelli

I livelli sono numerati **indipendentemente**. A Bologna `COM_ASC1` va da
`37006011` a `37006016` e `COM_ASC2` da `37006001` a `37006018`.

```
37006011  come ASC1 -> Borgo Panigale-Reno  (quartiere, 61.149 ab.)
37006011  come ASC2 -> Marconi              (zona statistica, 14.687 ab.)
```

**Il codice da solo non identifica la zona.** Un merge sul solo codice
riesce e restituisce il nome sbagliato, senza errori né valori mancanti.
`G.verifica_livello()` intercetta il caso.

### 3.2 Le denominazioni delle zone vanno verificate, sempre

Fino al 29/07/2026 il dizionario `codice → nome` di Bologna era
**permutato**: 16 codici su 18. Nessun controllo strutturale poteva
vederlo — una permutazione resta una biiezione perfetta — e la gerarchia
zona→quartiere costruita a mano sopra quei nomi era coerente con sé stessa.
I dati numerici erano corretti, perché calcolati sui codici; sbagliate
erano solo le etichette leggibili, cioè ciò che finisce in mappe e tabelle.

**Metodo di verifica** (collaudato su Modena, applicabile ovunque, senza
alcun download):

1. **Baricentro e dispersione dei civici per zona.** Dal file
   `{prov}_{nome}_civici_sezioni_asc.csv`, media e deviazione standard di
   `COORD_X_COMUNE`/`COORD_Y_COMUNE` per `COM_ASC*`, convertite in km. Il
   centro storico si riconosce dal raggio minimo; i nomi che contengono
   riferimenti cardinali o toponimi si accoppiano alle direzioni.
2. **Concentrazione dei toponimi.** Gli odonimi ANNCSU che contengono un
   toponimo devono cadere nel quartiere che lo nomina.

Su Modena i due assi hanno dato lo stesso esito, ciascuno inequivocabile:

```
codice     est_km  nord_km  raggio_km  civici     lettura
36023001     0,11     0,64       0,68  10.234     Centro Storico
36023002     2,09     1,36       2,22  14.662     ...Modena Est
36023003     0,85    -2,11       2,34  17.869     Buon Pastore, S.Agnese, S.Damaso
36023004    -2,65     0,63       3,07  17.723     San Faustino, Madonnina, 4 Ville

toponimi: SAN FAUSTINO -> 004 (100%) · CROCETTA -> 002 · BUON PASTORE -> 003
          SAN DAMASO -> 003 · EMILIA CENTRO -> 001
```

Per Bologna, che ha una gerarchia a due livelli, era stato usato un terzo
metodo: struttura della gerarchia (gruppi di taglia 3, 3, 4, 2, 4, 2, che
si sovrappongono in un solo modo) più conteggi di stranieri per zona da
open data comunali.

### Denominazioni

**Parma** (13 quartieri)

```
34027001 Parma Centro    34027006 San Pancrazio        34027011 Cittadella
34027002 Oltretorrente   34027007 San Leonardo         34027012 Montanara
34027003 Molinetto       34027008 Cortile San Martino  34027013 Vigatto
34027004 Pablo           34027009 Lubiana
34027005 Golese          34027010 San Lazzaro
```

**Modena** (4 quartieri, numerazione ufficiale del Comune)

```
36023001 Centro Storico
36023002 Crocetta, San Lazzaro, Modena Est
36023003 Buon Pastore, Sant'Agnese, San Damaso
36023004 San Faustino, Madonnina, Quattro Ville
```

Brescia e Bologna sono in `gsp_common.py` (`ASC_NOMI_BRESCIA`,
`ASC1_NOMI_BOLOGNA`, `ASC2_NOMI_BOLOGNA`). I codici ASC2 di Bologna
seguono l'ordine **alfabetico** dei nomi, ignorando gli spazi.

---

## 4. `gsp_common.py` — registro e primitive condivise

Consolida i cinque registri di comuni duplicati negli script. Nel registro
sta **solo ciò che non è derivabile**; i percorsi sono formule sul codice
ISTAT.

```python
import gsp_common as G

G.info("034027")          G.procom("034027")        # 34027
G.cod_prov("034027")      G.cod_avq("034027")       # 80 (REGMf in AVQ)
G.livello_col("037006")   G.zona_nomi("037006")
G.verifica_livello(codici, comune)
G.path_sezioni / path_civici / path_constraints / path_comune / path_shp
G.largest_remainder(n, pesi)      G.spartisci(idx, conta, valori)
G.norm_code(serie, comune)        G.norm_nome("S. Leonardo")
G.paesi_censuari(comune)          G.etichette_paese(comune)
G.risolvi_paese(etichetta, rif)   G.EU27_ISO   G.AGGREGATI_PAESE
```

```bash
python scripts/gsp_common.py --check
python scripts/gsp_common.py --dump-nomi 037006
```

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
assign_avq.py           -> + 21 variabili AVQ      |
                                                   |
enrich.py               -> + sezione, area, paese (geografico),
   usa opendata_paese.py    eta_anni, indirizzo, lon/lat      anello 3
```

`|X|` = 161.280 × n_zone. MRE(α>0) ≈ 4·10⁻⁴, **indipendente da `|X|`** su
quattro punti che coprono un ordine di grandezza (6,5·10⁵ → 5,3·10⁶).

### Perché l'allocazione esatta conta

MAE della popolazione per sezione: **0,74–1,58** su medie di 84–175
abitanti. Un campionamento multinomiale darebbe ≈ 9,6.

Il MAE **non cresce con la popolazione** e sembra anzi migliorare con
zone più grandi: Modena, con 546 sezioni per zona, ha il MAE più basso
(0,74). Il meccanismo plausibile è che l'errore di arrotondamento
dell'allocazione esatta si distribuisca su più sezioni quando i gruppi
sono grandi — ma le sezioni di Modena sono anche le più piccole, e i due
effetti si sovrappongono.

### Copertura regionale

```bash
python scripts/join_civici_sezioni.py emilia_romagna | lombardia | puglia
```

Bounding box derivato dallo shapefile, codici provincia dai dati. Un
contatore segnala i civici che ANNCSU attribuisce a un comune ma che
cadono in sezioni di un altro (42 Brescia, 25 Modena, 14 Parma, 0 Bologna).

---

## 6. Condizionale geografico del paese

| tier | livello | fonte | comune |
|---|---|---|---|
| **0** | comune | solo censimento | **Modena**, e ogni comune nuovo |
| 1 | quartiere | 33 CSV, senza sesso, ~19 paesi + residuale | **Brescia** |
| 2 | zona | parquet con sesso, 155 paesi | **Bologna** |
| 3 | sezione | microdati individuali | **Parma** |

`--no-tier` forza il comportamento comunale su qualunque comune.
**Copertura: 100% dalla geografia su tutte e quattro, zero fallback** — il
peso di sezione per gli stranieri è `P × q` con `q = ST/P`, quindi nessuno
straniero può atterrare dove il censimento non ne conta.

### Formulazione

Le fonti locali sono **anagrafiche** e di data diversa dal censimento. Se
ne usa la **forma**, non i livelli:

```
seed        T0(p,s,g) = struttura locale
margine 1   somma_g  T(p,s,g) = censimento comunale (paese, sesso)
margine 2   somma_ps T(p,s,g) = popolazione straniera censuaria di g
```

Due margini censuari con lo stesso totale: sistema sempre risolubile, IPF
converge in 9–88 iterazioni con scarto ~1e-11. Imporre anche i conteggi
locali renderebbe i margini incompatibili (anagrafe 40.090 stranieri a
Brescia contro 37.478 censuari).

Con la fonte assente il seed è la quota nazionale replicata su ogni zona.

### Il tier 0 è collaudato

Modena è il primo comune senza fonte locale, e il ramo di default — quello
che ogni comune nuovo userà — è stato verificato end-to-end confrontandolo
con `--no-tier`:

```
distanza in variazione totale, complessiva:   0,0023   (66 stranieri su 28.412)
per quartiere, media:                         0,029
per confronto, condizionale geografico:       0,156 - 0,197
```

Il seed uniforme riproduce la composizione comunale entro il rumore di
allocazione, cioè cinque-sette volte meno di quanto sposti un condizionale
geografico vero.

**Il collaudo ha scoperto due bug latenti**, entrambi della stessa
famiglia — classificare per etichetta invece che per codice:

- le denominazioni ISTAT sono invertite (`Ceca, Repubblica`), quindi il
  confronto con `startswith` classificava la Repubblica Ceca come
  extra-UE;
- la regex sugli aggregati catturava `africa` ovunque nella stringa,
  quindi escludeva `Sud Africa`, che è un paese.

Entrambi ora usano i codici (`G.EU27_ISO`, `G.AGGREGATI_PAESE`). Il filtro
va fatto **per esclusione e non per forma del codice**: i paesi hanno di
norma un ISO alpha-2 ma non sempre (`X95` Kosovo, `XSD_S` Sud Sudan), e
alcuni aggregati hanno forma alpha-2 — `EU` in particolare, somma dei 27
già presenti singolarmente, gonfiava il margine censuario del 21%.

### Riconciliazione delle denominazioni

| | agganciati | residuo |
|---|---|---|
| Brescia | 89,2% | 4.346 = `ALTRE CITTADINANZE`, **tetto strutturale della fonte** |
| Bologna | 100,0% | 7 persone in paesi assenti dal censimento |
| Parma | 100,0% | 13 persone |

### Quanto porta la geografia

Frazione di stranieri che cambia nazionalità passando dal condizionale
comunale a quello geografico, contro la stessa quantità sotto **ipotesi
nulla** (due permutazioni indipendenti: nessuna struttura, stesse
numerosità).

| | | osservata | nulla | **eccesso** |
|---|---|---|---|---|
| **Brescia** | per quartiere | 0,197 | 0,094 | **2,08** |
| | per sezione | 0,408 | 0,393 | 1,04 |
| **Parma** | per quartiere | 0,156 | 0,074 | **2,10** |
| | per sezione | 0,530 | 0,412 | **1,29** |
| **Bologna** | per quartiere | 0,169 | 0,066 | **2,57** |
| | per sezione | 0,421 | 0,417 | 1,01 |

**A livello di quartiere l'informazione è sostanziale e simile ovunque**:
2,1–2,6 volte quanto si sposterebbe per caso.

**Una fonte povera ma geograficamente risolta vale quanto una ricca.**
Brescia (19 paesi più un residuo del 10,8%, senza sesso) ottiene 2,08
contro il 2,57 di Bologna (155 paesi con sesso). Per i comuni futuri:
basta una tabella `paese × quartiere`, anche troncata alle prime venti
nazionalità.

**Brescia e Bologna a livello di sezione danno 1,04 e 1,01**, cioè nulla —
correttamente, perché il loro condizionale si ferma alla zona. Questo
**valida la metrica per via negativa**. Il 1,29 di Parma è l'unico eccesso
reale sotto il quartiere.

### I microdati di Parma: condizionale o validazione

202.111 righe, una per residente, con `SEZ21`, `Cittad`, `ETA`, `Sesso`,
`Ncomp`, `Relpar`. `SEZ21_ID = "34027" + SEZ21.zfill(7)`, aggancio 99,9%.

| uso | variabili |
|---|---|
| **condizionale** | `Cittad × SEZ21 × Sesso` |
| **validazione esterna, mai usate per generare** | `ETA × SEZ21`; `Ncomp`, `Relpar`; co-occorrenza di nazionalità nella stessa sezione; `Tipores` |

È l'unica occasione di **validazione esterna vera** che il progetto abbia.

---

## 7. Limiti e assunzioni dichiarate

| n. | assunzione | dove |
|---|---|---|
| (4') | `paese ⊥ tutto \| (area, sesso, geo)` — `geo` = quartiere, zona o sezione secondo il tier; per il tier 0 `geo` non vincola | §6 |
| (6) | `target AVQ ⊥ tutto \| (sesso, macroetà, istruzione4, regione)` | AVQ |
| (8) | `sezione ⊥ (istruzione, condizione, background) \| (zona, sesso, età3, cittadinanza)` | anello 3 |
| (9) | entro il quinquennio, l'età segue la distribuzione **comunale** per anno singolo | anello 3 |
| (10) | l'indirizzo è uniforme fra i civici della sezione | anello 3 |
| (11) | **nessuna struttura familiare** | anello 3 |

### Limiti della risoluzione per età

- **L'istruzione ha risoluzione effettiva di 4 classi d'età, non 8.** Il
  vincolo usa `Y9-24`, `Y25-49`, `Y50-64`, `Y_GE65`; dentro ogni classe la
  distribuzione viene da un **IPF con soglie minime di conseguimento**
  (`elementare` 10, `media` 13, `diploma` 18, `laurea_o_its` 20,
  `post_laurea` 22).
  *Prima della correzione del 29/07/2026 il 32,8% dei 9-14enni risultava
  diplomato o laureato.*
- **Resta sovrastimata `media` nel bin `9-14`**.
- **Effetto coorte perso fra `65-74` e `75+`**: `Y_GE65` li rende
  indistinguibili.
- **Il background migratorio ha risoluzione di zona**, non di sezione.

### Convenzioni per "assente" — non uniformate

| forma | dove |
|---|---|
| `non_applicabile` (stringa) | `condizione`, `origine_genitori`, 20 delle 21 AVQ |
| `NaN` | `area`, `via`, `civico` |
| nessuna | `SALUTE`, `paese` (= `Italia` per gli italiani) |

`non_applicabile` è a volte una **categoria sostantiva** (la condizione
professionale degli under-15), a volte un **missing individuale**
(`BMIMIN` per gli adulti), a volte un **planned missing** legato
all'annata del donatore (`PUNTIFI6,7,13`, `VOTOUSL`).

---

## 8. Punti aperti

### Aggiungere la cittadinanza alla cella di condizionamento AVQ

*Analisi completata il 29/07/2026, patch predisposta e non applicata.*

AVQ pubblica `CITTMi` (variabile derivata, 3 modalità: `1` italiana, `3` e
`9` da identificare — proporzioni nazionali 93,8% / 4,1% / 2,1%).
L'effetto sulla **fiducia istituzionale è sostanziale e monotono**, ~1
punto su 10, replicato in due regioni indipendenti:

| media pesata | ITA (1) | gr. 3 | gr. 9 |
|---|---|---|---|
| `PUNTIFI10` Comune, Lombardia | 5,16 | 5,81 | 7,00 |
| `PUNTIFI8` Regione, Lombardia | 4,38 | 5,24 | 6,51 |
| `PUNTIFI10` Comune, Emilia | 5,22 | 6,09 | 6,59 |
| `PUNTIFI8` Regione, Emilia | 4,97 | 5,97 | 5,78 |

**I non italiani si fidano delle istituzioni PIÙ degli italiani** —
direzione opposta all'intuizione, ma nota in letteratura: il metro di
paragone è il paese d'origine. Per Caffaro ribalta la narrazione attesa.

**Nessun effetto invece su `AMBIENTE` (2,37/2,30/2,14) né su `FIDUCIA`
(1,75/1,77/1,84).** La cittadinanza migliora le `PUNTIFI` e non tocca il
costrutto più rilevante per Caffaro.

Numerosità: ~430 non italiani nel pool emiliano su due annate. Il livello
di cella pieno non regge (~11 donatori per cella), il secondo sì (~43).
Serve il collasso gerarchico con la cittadinanza in priorità alta:

```python
CELL_COLS = ["sesso", "macroeta", "istr4", "citt"]
CELL_LEVELS = [
    ["sesso", "macroeta", "istr4", "citt"],
    ["sesso", "macroeta", "citt"],
    ["macroeta", "citt"],
    ["sesso", "macroeta", "istr4"],
    ["sesso", "macroeta"],
    ["macroeta"],
]
```

**Prima di applicare**: identificare le modalità `3` e `9` in
`METADATI/Classificazioni/`. Con n = 19 e 31 la differenza fra i due gruppi
non è distinguibile dal rumore, quindi il merge è difendibile — ma va
deciso sapendo cosa si unisce.

**Limite da dichiarare comunque**: il campione AVQ di stranieri è
autoselezionato sulla competenza linguistica (indagine familiare condotta
in italiano). Descrive gli stranieri più integrati, quindi la fiducia
istituzionale stimata è verosimilmente **sovrastimata**. Per un lavoro
mirato la fonte giusta sarebbe *Condizione e integrazione sociale dei
cittadini stranieri*.

### Altri punti aperti

- **`AMBIENTE` non varia per quartiere.** È soddisfazione per l'ambiente
  *della zona in cui si vive*, ma è condizionata solo su sesso, età e
  istruzione. È il **candidato numero uno per il tilt areale**. La
  cittadinanza non basta: serve un'altra covariata di zona e un target
  areale osservato su cui calibrarla — senza il quale il parametro del
  tilt resterebbe un'assunzione travestita da risultato.
- **`assign_nationality.py` è quasi vestigiale.** `area` e `paese` che
  produce sono **interamente sovrascritti** da `enrich.py`; l'unica
  funzione residua è generare il file che `assign_avq.py` legge, al quale
  servono solo `sesso`, `eta`, `istruzione`. La semplificazione naturale è
  far leggere ad `assign_avq` direttamente `popolazione_K9C.csv` e
  ritirare lo script. Chi legge la pipeline oggi vede due passi che
  assegnano il paese e non capisce perché.
- **Ramo di remapping ASC2→ASC1 irraggiungibile** in
  `assign_nationality.py`: `G.verifica_livello()` interviene prima.
- **Provenienza del paese non tracciata**: non esiste `paese_fonte`
  analoga a `indirizzo_fonte`.
- **Struttura familiare.** `Ncomp` e `Relpar` dei microdati di Parma, più
  `cens_posizione_famiglia` (scaricata e mai usata) per gli altri comuni.
- **K10C.** Esiste solo per Brescia e porta ancora l'istruzione
  **pre-correzione**: va rigenerato se usato.
- **San Vito dei Normanni** (`074017`): registrato, civici presenti, file
  sezioni non generato. `COM_ASC1` ha un solo valore: resterà un comune
  **senza articolazione zonale**.
- **Confronto fra città.** Le popolazioni usano condizionali di
  risoluzione diversa su partizioni di taglia diversa. Per un confronto
  rigoroso conviene rigenerarle al **quartiere**.

---

## 9. Dove sono i dati reali, per il confronto

```
{COMUNE}/constraints_2024/
    cs_K9C.json      vincoli con alpha target, categories, domain_sizes, zona_nomi
    targets_K9C.json tabelle target per blocco
    fit_K9C.json     lambdas, MRE, entropia, supporto
    manifest.json    fonte e tipo (hard/soft) di ogni blocco
{COMUNE}/zona_2023/  z1..z4, z6, zona_nomi
data/submun/{slug}_sezioni_2023.csv
    P1, ST1, ST16/ST19, P30-P45 e P67-P82, ST25-ST30
data/opendata/{COMUNE}/   fonti comunali per §6
data/avq/anni/avq{Y}/METADATI/AVQ_Tracciato_{Y}.html   codifiche AVQ
```

Versione senza condizionale geografico, per i confronti:

```bash
python scripts/enrich.py 037006 --anno 2024 --no-tier \
    --out popolazione_K9C_avq_full_tier0.csv
```

### Geometrie per la visualizzazione

```
data/geodata/{regione}/R{NN}_21/SHP/R{NN}_21_WGS84.shp
    R03 Lombardia    R08 Emilia-Romagna    R16 Puglia    CRS EPSG:32632
```

I poligoni delle zone si ottengono per **dissolve delle sezioni**:

```python
col = G.livello_col("034027")
s = gpd.read_file(G.path_shp("emilia_romagna"))
s = s[s.PRO_COM == G.procom("034027")]
zone = s.dissolve(by=col).reset_index().to_crs("EPSG:4326")
zone["nome"] = zone[col].astype("Int64").astype(str).map(G.zona_nomi("034027"))
```

**Per Bologna `G.livello_col` è `COM_ASC2`**: un dissolve su `COM_ASC1`
darebbe 6 poligoni invece di 18, e i codici — sovrapposti fra livelli
(§3.1) — mapperebbero comunque su dei nomi, sbagliati.

---

## 10. Riepilogo numerico

Esecuzioni del 29 luglio 2026.

| | Brescia | Parma | Bologna | Modena |
|---|---|---|---|---|
| codice ISTAT | `017029` | `034027` | `037006` | `036023` |
| regione (AVQ) | Lombardia (30) | Emilia-R. (80) | Emilia-R. (80) | Emilia-R. (80) |
| popolazione | 198.259 | 198.121 | 390.098 | 184.597 |
| attributi | 40 | 40 | 40 | 40 |
| zone | 33 (ASC1) | 13 (ASC1) | 18 (ASC2) | 4 (ASC1) |
| sezioni | 1.822 | 1.357 | 2.224 | 2.186 |
| sezioni occupate | 1.773 | 1.313 | 2.152 | 2.118 |
| civici ANNCSU | 49.730 | 35.826 | 77.595 | 60.488 |
| stranieri (censimento) | 37.478 | 34.436 | 58.963 | 28.415 |
| stranieri (sintetici) | 37.475 | 34.434 | 59.130 | 28.412 |
| quota stranieri | 18,9% | 17,4% | 15,1% | 15,4% |
| donatori AVQ nel pool | 8.111 | 4.629 | 4.629 | 4.629 |
| donatori distinti usati | 8.108 (100,0%) | 4.618 (99,8%) | 4.625 (99,9%) | 4.617 (99,7%) |
| riuso medio donatore | 24,5× | 42,9× | 84,3× | 40,0× |
| supporto \|X\| K9C | 5.322.240 | 2.096.640 | 2.903.040 | **645.120** |
| MRE(α>0) esatto | 4,6e-04 | 3,6e-04 | — | 4,3e-04 |
| tier paese (§6) | 1 | 3 | 2 | **0** |

**Il riuso dei donatori è un tetto strutturale.** Il 99,7–100% del pool
viene usato almeno una volta: la diversità dell'anello 2 è satura, e nella
popolazione di Bologna esistono al massimo 4.629 vettori psicografici
distinti indipendentemente dai 390.098 individui.

### Validazione per sezione

| | sezioni | media/sez | MAE pop. | corr | MAE stranieri | corr | MAE UE | corr |
|---|---|---|---|---|---|---|---|---|
| Brescia | 1.822 | 108,8 | 1,58 | 0,9998 | 0,98 | 0,9989 | 0,13 | 0,9976 |
| Parma | 1.357 | 146,0 | 1,43 | 0,9999 | 1,13 | 0,9985 | 0,16 | 0,9980 |
| Bologna | 2.224 | 175,4 | 1,36 | 0,9999 | 1,08 | 0,9983 | 0,17 | 0,9982 |
| Modena | 2.186 | 84,4 | **0,74** | 0,9999 | 0,63 | 0,9993 | 0,09 | 0,9969 |

I totali comunali coincidono esattamente con il censimento. Gli scarti sui
totali di stranieri (−3, −2, +167, −3) sono entro 0,7 σ del rumore
multinomiale di estrazione.

### Struttura spaziale: la sezione conta molto più della zona

Decomposizione della varianza della quota UE fra stranieri, al netto della
discretizzazione. **Calcolata dal file sezioni**, cioè dalla verità
censuaria: non dipende dalla popolazione sintetica.

| | abitanti/zona | var **tra** zone | var reale **dentro** | sovradisp. | rapporto |
|---|---|---|---|---|---|
| Brescia (33 zone) | 6.008 | 0,00168 | 0,00991 | 2,89× | **5,9×** |
| Parma (13 zone) | 15.240 | 0,00110 | 0,01249 | 3,50× | **11,3×** |
| Bologna (18 zone) | 21.672 | 0,00072 | 0,01124 | 3,04× | **15,7×** |
| Modena (4 zone) | 46.149 | **0,00040** | 0,01756 | 3,17× | **43,5×** |

**Il rapporto cresce monotonamente con la dimensione media delle zone**, su
quattro partizioni che vanno da 4 a 33 unità. Condizionare sul quartiere
perde l'85–98% del segnale compositivo.

**Quantità e composizione hanno scale spaziali diverse.** Modena lo rende
evidente: le quattro zone distinguono nettamente il Centro Storico (25,5%
di stranieri) dal resto (12,4–16,9%), ma la composizione *per origine* di
quegli stranieri è quasi identica ovunque. L'accessibilità economica del
patrimonio abitativo opera a scala di quartiere; la segregazione per
nazionalità opera per isolato.

### Validazione esterna puntuale

| | fonte comunale | sintetico (cens. 2023) | rapporto |
|---|---|---|---|
| Primo Maggio (Brescia), quota stranieri | 0,329 | 0,293 | 1,12 |
| Bologna, quota UE fra stranieri | 0,214 | 0,213 | 1,00 |

### Un fatto rilevante per il progetto Caffaro

```
Fiumicello           0,368        Buffalora          0,088
Centro Storico Nord  0,314        Villaggio Violino  0,073
Primo Maggio         0,293
```

**Fiumicello, uno dei due quartieri della `ZonaCaffaro`, ha la più alta
quota di stranieri della città** — il doppio della media comunale. Ma
`AMBIENTE`, `FIDUCIA` e le `PUNTIFI` sono condizionate su sesso, età e
istruzione e **non** su cittadinanza né sulla geografia (§8).

---

## 11. Due principi metodologici ricorrenti

### 11.1 Rapportare sempre all'ipotesi nulla

**Ogni metrica che scala con la numerosità di cella va rapportata alla
propria ipotesi nulla prima di essere confrontata fra configurazioni
diverse.** Quattro occorrenze, stessa forma:

1. **Varianza compositiva della quota UE** (§10). Con 30 stranieri per
   sezione la varianza fra sezioni è alta per pura combinatoria. Isolata
   con un test di sovradispersione contro l'assegnazione casuale entro zona.
2. **Distanza compositiva fra tier** (§6). Il 0,569 grezzo di Parma è per
   il 79% discretizzazione; l'eccesso reale è 1,29.
3. **Pavimento MRE del PCD** (`nota_mre_floor_v01.tex`). La formula
   `1/(2√N)` del paper GibbsPCD confonde errore assoluto e relativo.
4. **Numerosità effettiva di una popolazione hot-deck** (§2.2). Le
   correlazioni fra variabili AVQ sembrano poggiare su ~200.000
   osservazioni ma poggiano su al più 4.629 donatori distinti. `BMIMIN` ×
   `VOTOUSL` ha 266 individui ma una manciata di donatori, e produceva una
   correlazione di −0,61 priva di significato. `assign_avq.py` maschera
   ora le coppie con meno di 100 **donatori** distinti.

In tutti e quattro i casi la metrica grezza ordinava le configurazioni in
modo diverso — e talvolta inverso — rispetto alla metrica corretta.

**Corollario**: quando esiste una configurazione in cui il segnale è *noto
essere assente*, va usata come taratura. In §6, Brescia e Bologna a livello
di sezione danno eccesso 1,04 e 1,01: la metrica è tarata correttamente
proprio perché lì non trova nulla.

### 11.2 Due percorsi che devono coincidere sono un test permanente

Il confronto fra ramo tier e ramo comunale non serve solo a misurare il
guadagno del condizionale geografico: è una **verifica incrociata**. Su
Modena, dove il tier 0 deve riprodurre esattamente il comportamento
comunale, la discrepanza residua ha rivelato due bug latenti (§6) presenti
da sempre e invisibili a qualunque test su un solo ramo.

Vale la pena mantenere entrambi i percorsi anche quando uno diventa il
default, e usare il confronto come controllo di regressione.

---

## Changelog

**v1.5 — 29/07/2026**
Aggiunta Modena (`036023`): primo comune **tier 0** collaudato end-to-end,
partizione più grossolana in pipeline (4 zone da 46.000 abitanti,
rapporto sezione/zona 43,5×). Metodo di verifica delle denominazioni di
zona (§3.2), applicabile ovunque e senza download. Corretti due bug di
classificazione per etichetta anziché per codice (§6). Nuova §11.2.

**v1.4 — 29/07/2026**
Analisi dell'effetto della cittadinanza sulle variabili AVQ (§8), patch
predisposta e non applicata.

**v1.3 — 29/07/2026**
Dodici variabili di fiducia istituzionale su scala 0–10. Codifiche AVQ
risolte sul tracciato ufficiale. Attributi da 28 a 40.

**v1.2 — 29/07/2026**
Condizionale geografico del paese collegato e attivo. §11 sul principio
dell'ipotesi nulla.

**v1.1 — 29/07/2026**
Consolidamento in `gsp_common.py`. Correzione dei nomi delle zone di
Bologna e dell'istruzione nei bin infantili.

**v1.0 — 28/07/2026**
Prima stesura.
