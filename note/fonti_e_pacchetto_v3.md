# Registro delle fonti, pacchetto `gsp`, donatori AVQ — v3

Aggiornata il 2 agosto 2026. Sostituisce la v2. Rispetto a quella, la
novità sostanziale è la **chiusura della questione sui donatori AVQ**
(§5), aperta da mesi: i tre punti sono ora misurati, e due delle
convinzioni che li circondavano erano false.

---

## 1. Migrazione a pacchetto

### Perché

`scripts/` conteneva trenta file che erano due cose diverse: una libreria
importata da tutti (`gsp_common.py`) e una ventina di passi eseguibili che
nessuno importa. Il vincolo pratico era che Python non importa dalle
cartelle sorelle: raggruppare gli script avrebbe rotto `import
gsp_common`, e le uniche uscite erano un `sys.path.append` in cima a ogni
file — fragile, si rompe da Colab — oppure il pacchetto installato.

### Struttura

```
~/progetti/gsp/
  pyproject.toml
  src/gsp/
    __init__.py            vuoto di proposito: importare `gsp` non deve
                           tirarsi dietro pandas, numba e yaml
    common.py              ex gsp_common.py (registro dei 12 comuni)
    fonti/
      __init__.py          il modulo del registro
      __main__.py          abilita `python -m gsp.fonti`
      normalizzatori.py    12 funzioni pure grezzo -> canonico
  scripts/                 i passi della pipeline, invariati
  fonti/                   DATI del registro (non codice)
  data/                    4,7 GB, fuori da git
  note/
```

`pip install -e .` nell'ambiente `ml`. Dipendenze da dichiarare in
`pyproject.toml`: `pandas`, `numpy`, `pyarrow`, `pyyaml`, `xlrd`,
`openpyxl`, `python-calamine`.

### Uso quotidiano

| prima | dopo |
|---|---|
| `python scripts/gsp_common.py --check` | `python -m gsp.common --check` |
| `python scripts/fit_cs.py` | invariato |
| `import gsp_common as G` (solo da `scripts/`) | `import gsp.common as G` (da ovunque) |
| — | `python -m gsp.fonti --verifica` |

### Metodo di verifica

Baseline catturata **prima** di toccare qualsiasi cosa, migrazione,
confronto `diff -r`: `IDENTICO` su tutti i file. È il metodo dei due rami
paralleli applicato a una rifattorizzazione. `git mv` e non `cp` + `rm`,
così `git log --follow src/gsp/common.py` racconta ancora tutta la storia
di `gsp_common.py`.

### Da fare

- **`opendata_paese.py` e `istat_sdmx.py` sono libreria di fatto**:
  `enrich.py` importa il primo, `fetch_comune.py` il secondo. **Non è la
  stessa migrazione di `gsp_common`**: `opendata_paese.py` è ibrido — CLI
  (`--check`, `--dump`), sei funzioni lettrici, e la logica IPF — quindi
  va prima separato, e solo la parte lettrice va nel pacchetto.
  `istat_sdmx.py` va spostato prima o insieme, perché il primo lo importa.
- Raggruppare i trenta script in sottocartelle: ora indolore, commit a sé.
- Verificare se i dieci file del banco Gibbs appartengano a
  `maxent-popsynth-pcd`.

---

## 2. Il registro delle fonti

### Il principio

> **Ogni fonte richiede il suo universo dichiarato.** Un file senza
> universo è un elenco di numeri, non una misura.

È la versione a monte di «ogni statistica richiede una configurazione di
confronto». La riga che conta non è l'URL: è *«residenti anagrafici al
31/12/2013, tutte le età, italiani e stranieri, un record per persona»*.

### Struttura sul disco

```
fonti/
  registro.yaml        scritto a mano: universo, licenza, uso
  grezzi/              i file originali sotto i 5 MB, versionati
  metadati/            DCAT, note metodologiche, tracciati d'origine
  impronte/            GENERATE: firma di ogni fonte, sempre in git
  norm/                GENERATE: Parquet canonici, ricostruibili
  ATTRIBUZIONI.md      GENERATO: obbligo CC-BY verso chi riceve i dati
```

**Il grezzo è immutabile**: non si tocca mai, nemmeno per correggere un
separatore. Le correzioni vivono nel normalizzatore, che è codice
versionato; le stranezze restano dichiarate in `anomalie`.

### Tre livelli di archiviazione

```
git      grezzo versionato: riproducibile da un clone     (< 5 MB)
locale   grezzo su disco, gitignorato: verificabile qui
remoto   nessun grezzo: resta l'URL, l'impronta è l'unica prova
```

### Due tipi di fonte

**`file`** — una fonte, un file, un hash. Il grezzo sta in `fonti/grezzi/`
oppure, se `percorso` è dichiarato, dove vive già (tipicamente `data/`).

**`multi_istanza`** — una scheda per *tavola*, tante istanze uguali per
forma e diverse per chiave. `percorso` contiene un pattern con
`{istanza}` e `--scansiona` le rileva da sole.

### `parametri_da`: non riscrivere ciò che esiste già

`common.COMUNI[<cod>]["opendata_paese"]` contiene loader, livello
geografico, encoding, mappe di riconciliazione (41→21 unità per Forlì,
22 alias di paese per Ravenna). Il registro **lo referenzia**:

```yaml
parametri_da: common.COMUNI.017029.opendata_paese
```

`--verifica` controlla che il riferimento regga. Riscriverlo darebbe due
dichiarazioni della stessa cosa, destinate a divergere in silenzio.

### I comandi

```bash
python -m gsp.fonti --verifica          # hash, conteggi, campi obbligatori
python -m gsp.fonti --elenco            # inventario
python -m gsp.fonti --scansiona ID      # rileva le istanze, scrive l'impronta
python -m gsp.fonti --impronta ID       # (fonti a file singolo)
python -m gsp.fonti --attribuzioni      # rigenera ATTRIBUZIONI.md
python -m gsp.fonti --pubblico          # cosa può finire in un repo pubblico
python -m gsp.fonti --copertura         # fonti usate e NON registrate
python -m gsp.fonti --aggiungi PATH --id ID
```

### Gli esiti di `--verifica`

| esito | significato | esce con |
|---|---|---|
| `ok` | tutto coincide | 0 |
| `IMPRONTA` | grezzo assente ma impronta presente: stato **normale** di un clone senza i file pesanti | 0 |
| `NUOVE` | istanze non ancora in impronta: un comune aggiunto è informazione | 0 |
| `DIVERGE` | hash cambiato, conteggi diversi, campi mancanti, file vuoto, riferimento rotto | 1 |
| `ROTTA` | dichiarata in git ma assente; né grezzo né impronta | 1 |

Uno stato che fallisce sempre è uno stato che si smette di guardare.

### `--copertura`: la direzione opposta

Tutti gli altri controlli chiedono «la scheda punta a qualcosa che
esiste?». Questo chiede **«esiste una fonte nella pipeline che non è
passata dal registro?»**. Stessa asimmetria di `n_dichiarato` contro
`n_misurato`, applicata alla copertura.

### I dodici normalizzatori

| nome | forma | diagnostica caratteristica |
|---|---|---|
| `distribuzione_csv` | `chiave, peso` | modalità, n_misurato, chiavi fuse |
| `matrice_csv` | largo → `chiave, zona, peso` | zona_nomi, **residuo_quota** |
| `formato_lungo` | melt di colonne affiancate | unità escluse, n per sesso |
| `tabella_parquet` | lungo, con filtro d'anno | anni_n, anno_usato |
| `excel_aree_sesso` | doppia intestazione Excel | zona_nomi, n_M, n_F |
| `microdati_csv` | record individuali | **min/max e negativi per colonna** |
| `codebook_csv` | `campo, codice, etichetta` | codici_per_campo, segnaposto |
| `sdmx_csv` | frame intatto | dataflow, ref_area, anni, obs_somma |
| `sezioni_xlsx` | frame intatto | sezioni, comuni, popolazione, vuote |
| `tracciato_xlsx` / `tracciato_csv` | `chiave, definizione` | campi, senza_definizione |
| `avq_microdati` | colonne di struttura | somma_pesi, **n_eff_kish** |

Solo il primo produce `peso`: impronta e verifica sono tolleranti perché
un codebook non è una distribuzione, e un microdato nemmeno.

---

## 3. Le ventiquattro fonti

### Cognomi — Comune di Firenze (2)

CC-BY-4.0, in git, metadato DCAT, `notPlanned`.

`firenze_cognomi_2013`: 375.371 residenti, 66.353 cognomi distinti, 51%
hapax. Chao1 stima ~125.000 cognomi nella popolazione generatrice.

`firenze_cognomi_2012` è solo controllo di stabilità: correlazione
0,9985, variazione mediana assoluta 0 — **stessa popolazione a un anno di
distanza, non un campione indipendente**. L'unione guadagna 6.103 tipi di
cui 5.523 hapax, l'1,6% della massa: non vale il merge.

Il limite è regionale, non dimensionale: `TOLOMELLI`, il cognome più
frequente di Argelato, non compare in 375.371 fiorentini.

### ISTAT SDMX — 11 tavole × 12 comuni

CC-BY-4.0, `archiviazione: locale`. **4 query/minuto**.

| | universo | ruolo |
|---|---|---|
| `istat_anag_sesso_eta_statociv` | anagrafe, 1 gennaio anno **N** | C1, unico **hard** |
| altre dieci | censimento permanente, 31 dicembre anno **N−1** | C2–C10, **soft** |

Serie 2019–2025 e 2018–2024: sette anni ciascuna, sfalsate di uno perché
sono gli **stessi sette istanti**.

`cens_stranieri_paesi` ha cinque consumatori ed è l'unica fonte dei ~150
paesi, pubblicata solo a livello comunale: è la ragione dei quattro tier.
`cens_migr_backg` genera il blocco GC (sei zeri strutturali).
`cens_posizione_prof` e `cens_settore_prof` hanno `unita: individuo
occupato` ed entrano come C9/C10 soft e condizionali.
**`cens_posizione_famiglia` è scaricata e mai letta.**

`obs_somma` è ~2× (anagrafica) e ~8× (censimento) la popolazione, per via
degli aggregati: **firma per riconoscere il file, non conteggio**.

### Sezioni di censimento (2)

**135.725 sezioni**, 18,35 milioni di residenti. Geometria del censimento
**2021**, dati **2023**. `COM_ASC1/2/3` è la gerarchia zona/quartiere.
**10.872 sezioni senza residenti**, già riconosciute da
`build_sezioni.py`. Il tracciato delle 138 colonne è registrato a parte.

### AVQ (2)

Licenza `DA_VERIFICARE`: mIcro.STAT è «file ad uso pubblico», la classe
meno restrittiva, ma il `!Leggimi` **non dichiara una licenza**.

`unita: individuo campionario`. `n_misurato` = **record**; `somma_pesi` e
`n_eff_kish` stanno nell'impronta.

**`COEFIN` ha quattro decimali impliciti** (`scala_peso: 10000`): senza,
la somma dei pesi è 5,8e11 invece di 5,8e7. Con la scala corretta:

| anno | record | somma pesi | n_eff Kish |
|---|---|---|---|
| 2022 | 42.022 | 58.499.237 | 31.015 |
| 2023 | 41.750 | 58.380.189 | 31.386 |
| 2024 | 45.005 | 58.620.700 | 34.154 |

I record del 2022 coincidono esattamente con i 42.022 dichiarati nel
`!Leggimi`: prima verifica `n_dichiarato` = `n_misurato` su AVQ.

**I microdati sono perturbati** per la tutela della riservatezza: il
`!Leggimi` avverte che le elaborazioni possono dare risultati difformi da
quelli pubblicati. Limitazione strutturale dell'universo, non licenza.

### Le sei fonti locali (7 schede)

Margine B dell'IPF, complementare al censimento (margine A). Tutte
anagrafiche, di data diversa dal censimento, tutte con `parametri_da`.
Licenze tutte `DA_VERIFICARE`.

| comune | tier | unità | paesi | residuo | sesso | età |
|---|---|---|---|---|---|---|
| Parma | 3 | **1.320 sezioni** | 151 | — | sì | sì |
| Bologna | 2 | 19 zone | 155 | **0%** | sì | no |
| Forlì | 1 | 41 sub-quartieri | 42 | **16,5%** | sì | no |
| Brescia | 1 | 33 quartieri | 8–33 per file | variabile | no | no |
| Ravenna | 1 | 10 aree | ~40 | — | sì | no |
| Reggio E. | 1 | 4 circoscrizioni | 25 | **6,1%** | no | no |

**Brescia** include `ITALIA`: i totali sono popolazione completa, filtro a
valle (`opendata_paese.py:97`). Modalità da 8 a 33 per quartiere.

**Reggio Emilia** — matrice larga, ISO-8859-1, **2013**. L'uso è
giustificato da una verifica del 1/8/2026: ranghi delle quote UE per zona
4-2-1-3 nel 2013 contro 4-1-2-3 nel 2023, unico scambio fra zone che nel
2023 distano 0,003. **È questa verifica, non la data, a rendere la fonte
usabile.**

**Ravenna** — XLS binario formattato per la stampa (creato 2003, stampato
30/1/2024), doppia intestazione con celle unite. Si usano M e F, si
scarta T. Il 2024 era a 0 byte: rimosso.

**Forlì** — xlsx **senza `sharedStrings.xml`**: serve `python-calamine`.
41 unità mappate + `in corso di definizione` (9 persone) esclusa. La
fonte totalizza 15.021 contro 15.298 del censimento — **1,8% di scarto
sui livelli**, che l'IPF normalizza. Distanza media dalla composizione
comunale **0,170**, IPF convergente in 9 iterazioni.

**Bologna** — Parquet, serie **1986–2024**, 39 annate: `anno` è una
colonna. `Senza fissa dimora` esclusa (324 persone).

**Parma** — 202.111 residenti, 36.327 stranieri (18%), 1.320 sezioni.
L'unica a microdato e l'unica con la sezione. Porta `Ncomp` e `Relpar`,
cioè **struttura familiare**. Codebook a due livelli, 225 codici per
`Cittad` contro 151 presenti.

---

## 4. Cosa il registro ha già trovato

- **Due file scaricati vuoti** (0 byte) mai notati: Piacenza e Ravenna
  2024. Da qui il controllo `SHA_VUOTO`.
- **`unita` sparita** da `istat_cens_settore_prof` in un'edit manuale.
- **Un record con `ETA = -1`** su 202.111 a Parma, trovato dal controllo
  di plausibilità di `microdati_csv`. Il codebook ha stabilito che `ETA`
  è «numerico» senza valori speciali: **dato sporco, non convenzione**.
  Nessuna delle due cose da sola bastava.
- **`Ncomp` fino a 319**: convivenze anagrafiche (`Tipores = 2`), non
  famiglie.
- **`cens_posizione_famiglia` mai usata.**
- **Overflow int64 nel Kish**: `n_eff` negativo perché `COEFIN` è intero
  e `sum(w)²` con somma 5,8e11 sfonda int64. Un `n_eff` negativo sembra
  un peso negativo e non lo è.

### `residuo_quota` come criterio comparabile

L'ipotesi «più fine la geografia, più informazione nel residuo» reggeva
passando da Reggio (4 unità, 6,1%) a Forlì (41 unità, 16,5%). **È
falsa**: Bologna ha 19 zone e zero residuo. La relazione dipende da come
il comune costruisce la pubblicazione — Forlì pubblica una graduatoria
troncata, Bologna l'estrazione completa. E a Bologna la fonte nomina 155
paesi contro i 119 che l'IPF produce dal censimento: il margine B è più
ricco del margine A, il contrario del caso generale.

---

## 5. Donatori AVQ — questione CHIUSA

Era il punto aperto da mesi. Tutti e tre i sotto-problemi sono ora
misurati, e **due delle convinzioni che li circondavano erano false**.

### 5.1 Le due previsioni falsificate

**«`assign_avq.py` non stampa i donatori usati».** Falso: la riga esiste
già nel sorgente. La deduzione veniva dall'assenza nei log del 27 luglio,
che sono precedenti a quella versione. Era stata registrata come
verificata senza guardare il codice.

**«La validazione delle correlazioni è stata rimossa».** Falso: il blocco
`[val]` gira sempre, con l'unica condizione `num.shape[1] >= 2`. Le due
corse del 27 luglio differivano per gli argomenti passati a mano, non per
il codice.

Entrambe attribuivano allo script **meno** diagnostica di quanta ne
abbia, ed entrambe sono state smentite guardando il sorgente invece del
comportamento. È il pattern da ricordare.

### 5.2 Il difetto vero: la maschera contava la quantità sbagliata

Nella validazione 2 la soglia mascherava le correlazioni con meno di 100
donatori, ma li contava sui **disponibili nel pool** (`src.notna()`),
mentre l'informazione indipendente nel sintetico viene dai donatori
**effettivamente estratti**. Una coppia con 400 disponibili e 60 estratti
poggia su 60 osservazioni e passava il filtro.

C'era anche una collisione di nome che incarnava la confusione: `n_don`
era prima lo scalare degli estratti, poi veniva **sovrascritto** dalla
matrice dei disponibili. Ora si chiamano `n_estratti` e `n_coppia`.

**Correzione applicata:**

```python
usati = np.unique(donor_idx)
ok_u = src.loc[usati].notna().astype(int)
n_coppia = ok_u.T @ ok_u          # estratti distinti, non disponibili
```

più il conteggio di quanto la vecchia soglia fosse permissiva:

```python
m = ((n_disp >= 100) & (n_coppia < 100)).to_numpy()
piu_lasco = int(np.triu(m, k=1).sum())   # solo il triangolo: la
                                         # diagonale non e' una coppia
```

**Esito: `piu_lasco = 0` su tutti e tre i comuni provati.** Il difetto era
teorico — ma ora è la quantità giusta, e su un comune più piccolo o con
più variabili opzionali potrebbe mordere.

Nota tecnica: `src.loc[usati]` e non `.iloc` — `a` ha indice non contiguo
dopo `concat` + filtro regione + `dropna`, e `donor_idx` contiene
etichette, non posizioni.

### 5.3 Donatori estratti: misurati

| comune | estratti / pool | riuso medio |
|---|---|---|
| Brescia (017029) | 8.111 / 8.111 — **100%** | 24,4× |
| Modena (036023) | 4.617 / 4.629 — 99,7% | 40,0× |
| Castenaso (037021) | 4.336 / 4.629 — **93,7%** | 3,8× |

Il pool si satura quasi completamente ovunque: è per questo che
`piu_lasco` è zero.

### 5.4 Il confronto sintetico/donatori, ridotto a tre numeri

Le due matrici sono 23×23, cioè **253 coppie da guardare a occhio**. Ora
c'è la misura:

```python
D = (C - R).abs()
for t in D.columns:           # niente np.fill_diagonal: con pandas 3
    D.loc[t, t] = np.nan      # il .values e' una vista in SOLA LETTURA
```

| comune | mediano | massimo | peggiore coppia | n | atteso ~1/√n |
|---|---|---|---|---|---|
| Brescia | 0,005 | 0,031 | `VOTOUSL × BMI` | 1.258 | 0,028 |
| Modena | 0,007 | 0,046 | `FIDMED × FORZE_ARMATE` | 1.130 | 0,030 |
| Castenaso | 0,009 | 0,061 | `CRONI × FORZE_ARMATE` | 1.001 | 0,032 |

**Il mediano scala con il riuso, non con la popolazione.** Brescia satura
il pool e ha il mediano più basso; Castenaso lo usa al 93,7% con riuso
3,8× e ha il più alto. Non è la dimensione del comune a determinare la
fedeltà, è quanto il pool viene esplorato.

**Ogni scarto è affiancato alla sua precisione attesa.** L'errore
standard di una correlazione su n osservazioni indipendenti è ~1/√n, e le
osservazioni indipendenti sono i donatori estratti con entrambe le
variabili. Osservato/atteso resta fra 1 e 2 ovunque: su 253 coppie, con
253 estrazioni il massimo di una normale standard sta tipicamente sui
2,8σ, quindi siamo perfino sotto. **Non è un difetto della procedura, è
la coda della distribuzione degli scarti.**

Le coppie con `FORZE_ARMATE` dominano la classifica perché quella
variabile è disponibile in una sola annata (23% degli assegnati), quindi
n ≈ 1.100 invece di 4.617. Unica anomalia da tenere d'occhio:
`PUNTIFI5 × PUNTIFI8` a Brescia, 0,029 osservato contro 0,012 atteso con
n = 7.012 — 2,4 errori standard, il solo caso in cui il rapporto sfora.

**La frase difendibile davanti a un revisore:** *su 253 coppie, lo scarto
fra le correlazioni della popolazione sintetica e quelle dei donatori AVQ
ha mediana 0,007 e massimo 0,046, con le tre peggiori entro 1,5 errori
standard della loro numerosità effettiva.* È molto più forte del singolo
`SALUTE ↔ CRONI` che c'era prima.

### 5.5 Le collisioni: spiegate, non risolvibili

Con 21 variabili erano 418 (9%). Con 23:

| comune | firme | estratti | collisioni |
|---|---|---|---|
| Modena | 4.161 | 4.617 | 456 (9,9%) |
| Brescia | 7.226 | 8.111 | 885 (10,9%) |
| Castenaso | 3.890 | 4.336 | 446 (10,3%) |

**Aggiungere due variabili non ha risolto niente**, ed è la chiave: le
collisioni non sono un problema di potere discriminante — con 23
variabili quasi tutte politomiche, due donatori identici per caso
sarebbero un evento di probabilità infinitesima.

Scomposizione sul pool emiliano-romagnolo (4.629 donatori, 456
collisioni), per numero di variabili mancanti su 23:

| n mancanti | donatori | firme | collisioni | quota |
|---|---|---|---|---|
| 0–4 | 2.095 | 2.095 | **0** | 0,000 |
| 5 | 1.697 | 1.693 | 4 | 0,002 |
| 6–18 | 314 | 313 | 1 | 0,003 |
| **19** | 118 | 25 | **93** | **0,788** |
| **20** | 337 | 31 | **306** | **0,908** |
| **21** | 64 | 12 | **52** | **0,812** |
| 22 | 3 | 3 | 0 | 0,000 |

**452 collisioni su 456 (il 99%) stanno nelle tre righe 19–21.** Sono i
minori: ai bambini non vengono poste le domande su fiducia, salute
percepita, fumo, benessere psicologico e antropometria, quindi si
distinguono su due, tre o quattro valori soltanto — e lì la collisione
non è un caso raro ma il comportamento atteso.

**Dove le variabili ci sono, le collisioni sono zero**: da 0 a 18
mancanti, su 4.107 donatori, ce ne sono cinque in tutto.

**Non è l'annata**: 2023 collide 198 volte su 2.181 donatori, 2024 229 su
2.448 — stessa misura, nonostante il 2023 manchi delle cinque opzionali.
Il picco a `n_na = 5` è proprio l'annata 2023, e lì le collisioni sono
quattro.

**Conclusione.** Il 10% non è un difetto della firma: è il riflesso del
**pattern di mancanza strutturale dei minori**. Nessuna variabile
aggiuntiva le eliminerà, perché per quei donatori le variabili aggiuntive
sono proprio quelle che mancano. Questo sistema anche il conto vecchio:
le 418 collisioni con 21 variabili non erano un limite della codifica, e
passare a 23 non doveva risolverle — infatti non le ha risolte.

### 5.6 Conseguenze operative

- Per il **numero** di donatori distinti si usa `n_estratti`, che
  `assign_avq.py` stampa.
- Per **identificare** il donatore di un individuo, la firma è esatta per
  gli adulti e inutilizzabile per i minori. L'unica strada è scrivere
  `idx_don` come colonna al momento dell'assegnazione: `idx_don` esiste
  già in memoria, e una colonna in più chiude definitivamente qualcosa
  che dalla firma non è ricostruibile.
- **Ancora aperto**: equipesare le annate (`w = COEFIN / somma dell'anno`)
  implica un pool che rappresenta una media del triennio e non la
  popolazione a una data. Per donare attributi è *probabilmente*
  irrilevante, ma non è stato verificato.

### 5.7 Il pool a due annate, verificato girando

`2022: variabili NECESSARIE mancanti ['CRONI'], annata saltata`. Con
`CRONI` fra i target il pool resta a **due** annate — 41.750 + 45.005
record nazionali che diventano 4.629 donatori emiliano-romagnoli con
cella completa. Il `nota_pool` della scheda AVQ lo descriveva, e questa è
la prima volta che lo si vede girare.

### 5.8 Nota su `FIDUCIA`, per Caffaro

`FIDUCIA` è l'unica variabile della validazione 1 con uno scarto
marginale sopra lo 0,01: **±0,025** contro ≤0,009 di tutte le altre. Non
è un pool ridotto — ha 25.060 `non_applicabile` su 184.597 (13,6%, i
minori), esattamente come `AMBIENTE`. È che è **dicotomica**: due sole
modalità, nessuna compensazione fra celle, tutto lo scarto concentrato in
una coppia di numeri.

Dentro il rumore, ma è il numero da tenere presente: **la prevalenza
della fiducia nella popolazione sintetica ha un'incertezza di circa 2,5
punti percentuali**, e un effetto più piccolo di così non è misurabile.
È la stessa cosa che il framework SIVE dice sul rumore di fondo — un
effetto sotto la soglia di rilevabilità dello strumento non è un effetto.

La polarità invertita è confermata dai segni: `FIDUCIA` correla
**negativamente** con `FIDMED` (−0,155) e `FIDINF` (−0,150), che sono
anch'esse misure di fiducia. Stesso pattern per `AMBIENTE` con tutti i
`PUNTIFI`. Il segno è un controllo di polarità gratuito.

---

## 6. Altre questioni aperte

### 6.1 Etichette di blocco disallineate

| tavola | la tupla dice | il file prodotto è |
|---|---|---|
| `cens_istruzione_cittadinanza` | C3 | `c5_edu_citizenship.csv` |
| `cens_condprof_cittadinanza` | C4 | `c6_condprof_citizenship.csv` |
| `cens_stranieri_paesi` | C6 | `nationality_conditional.csv` |

C6 assegnato due volte. Non cambia i risultati, ma se `preflight()` le
stampa un messaggio annuncia il blocco sbagliato. Nel registro il campo
`blocco` segue **il nome del file**.

### 6.2 Difetti delle fonti

- **`ETA = -1`** a Parma, un record: dato sporco confermato.
- **Ravenna 2024** da riscaricare.
- **`Ncomp`** non usabile senza condizionare su `Tipores`.

### 6.3 Fonti non registrate

- **`data/istat_structures/`** (120 MB): DSD e codelist SDMX. Non
  osservazioni ma schemi, e sono ciò che permette di costruire le query
  senza interrogare l'API — non banale con 4 query/minuto.
- **`data/geodata/`** (1,7 GB): mai guardato.
- **Licenze dei sette portali comunali** e di AVQ.

### 6.4 Il ciclo di rigenerazione

 Aggiungere lì la colonna `idx_don`
costa nulla e chiude §5.6 su dodici comuni in un colpo.

---

## 7. Come si aggiunge una fonte

```bash
python -m gsp.fonti --aggiungi ~/scarichi/file.csv --id ente_variabile_anno
```

Copia il grezzo, calcola l'hash, sceglie il livello di archiviazione, e
stampa uno stub YAML con `DA_COMPILARE` sui campi che richiedono
giudizio: **universo**, **unità**, **usabile_per**, **non_usabile_per**.

**Scaricare sempre i metadati insieme ai dati.** Per Firenze l'XML DCAT
ha risolto la licenza in dieci secondi e dato il `byteSize` che conferma
l'sha256. Per Parma il codebook ha stabilito che `ETA = -1` è sporco.

**I codebook vanno registrati come fonti**: sono **la fonte che dà
significato ai valori dell'altra**.

**`non_usabile_per`** è il campo che nessuno mette ed è quello che serve.

---

## 8. Trappole imparate

**`cat >>` non è idempotente**, ed è capitato **tre volte**. Un controllo
che stampa e basta non serve se il comando pericoloso è nella stessa riga
incollata:

```bash
grep -q "id: X" fonti/registro.yaml \
  && echo "GIA' PRESENTE, non appendo" \
  || cat "$SCAR/schede.yaml" >> fonti/registro.yaml
```

**Le chiavi YAML duplicate spariscono in silenzio.** PyYAML tiene
l'**ultima**. È l'unico errore che nessun altro controllo può vedere,
perché arriva già filtrato dal parser. Ora un loader le rifiuta.

**Dopo ogni modifica a mano, stampare il risultato**, non solo validare:
`usabile_per: [a b]` senza virgola è YAML valido e produce **un solo
elemento**. E `[tutto: il file e' vuoto]` è una mappa, non una stringa.

**I numeri di riga invecchiano.** Ancorarsi a un pattern, non a un numero.

**L'sha256 della stringa vuota è `e3b0c442…852b855`.**

**Un difetto localizzato non deve far perdere le informazioni buone.**
`_impronta_multi` si fermava alla prima istanza illeggibile.

**Attenzione ai tipi interi in operazioni quadratiche.** `sum(w)²` su
int64 con somma 5,8e11 wrappa a negativo: convertire a float **prima** di
elevare.

**`np.fill_diagonal(D.values, ...)` non funziona con pandas 3**: il
`.values` è una vista in sola lettura, e l'errore è esplicito — meglio
della variante silenziosa che scriveva su una copia. Si maschera per
etichette: `for t in D.columns: D.loc[t, t] = np.nan`.

**`astype(str)` lascia i NaN come float**, e `"|".join` fallisce.
Usare `.map(lambda x: "NA" if pd.isna(x) else str(x))`.

**I file da Windows arrivano `100755`.** `chmod 644`.

**Il browser rinomina i file omonimi** e l'estrazione appiattita di uno
zip fa collidere i file omonimi *dentro* lo zip.

**`python-calamine` si importa come `python_calamine`.**
