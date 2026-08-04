# Registro delle fonti, pacchetto `gsp`, donatori AVQ — v4

Aggiornata il 3 agosto 2026. Sostituisce la v3. Rispetto a quella: la
struttura è **finita** — `scripts/` riordinato in sei gruppi, tutte le
dipendenze interne sciolte, tre repo allineati — e il §5 sui donatori è
chiuso con `donor_id` scritto a monte.

---

## 1. Il pacchetto e gli script

### Perché

`scripts/` conteneva trenta file che erano due cose diverse: una libreria
importata da tutti e una ventina di passi eseguibili che nessuno importa.
Il vincolo pratico era che Python non importa dalle cartelle sorelle:
raggruppare gli script avrebbe rotto gli import, e le uniche uscite erano
un `sys.path.append` in cima a ogni file — fragile, si rompe da Colab —
oppure il pacchetto installato.

### Struttura finale

```
~/progetti/gsp/
  pyproject.toml
  src/gsp/
    __init__.py            vuoto di proposito: importare `gsp` non deve
                           tirarsi dietro pandas, numba e yaml
    common.py              registro dei 12 comuni e primitive condivise
    opendata.py            fonti locali per il paese di cittadinanza
    istat/
      sdmx.py              client SDMX (4 query/minuto)
    fonti/
      __init__.py          il registro delle fonti
      __main__.py          abilita `python -m gsp.fonti`
      normalizzatori.py    12 funzioni pure grezzo -> canonico

  scripts/
    rigenera.sh            orchestrazione dell'intera pipeline
    run_avq.sh
    acquisizione/          istat_catalog · fetch_comune
    vincoli/               build_constraints · build_sezioni ·
                           build_zona_tables · cs_build · join_civici_sezioni
    fit/                   fit_cs
    attributi/             assign_nationality · assign_avq · enrich
    diagnostica/           check_marginals · zona_probe · perm_composizione
    gibbs/                 gibbs_lab · profile_gibbs · test_invariance ·
                           test_moves · batch_lambda.sh · batch_scaling.sh

  scripts_archivio/        preflight · run_regression · regress_fit
  fonti/                   DATI del registro (non codice)
  data/                    4,7 GB, fuori da git
  note/  note/storico/
```

`pip install -e .` nell'ambiente `ml`. Dipendenze in `pyproject.toml`:
`pandas`, `numpy`, `pyarrow`, `pyyaml`, `xlrd`, `openpyxl`,
`python-calamine`.

### Il criterio

**Nel pacchetto va ciò che qualcun altro importa.** Che abbia anche una
CLI è irrilevante: `gsp.common` ce l'ha, e `python -m` la serve.

- `gsp_common` → `gsp.common` — importato da undici script
- `istat_sdmx` → `gsp.istat.sdmx` — importato da `fetch_comune`
- `opendata_paese` → `gsp.opendata` — importato da `enrich`, una sola
  funzione: `tabella_paese(comune, anno-1)`
- `istat_catalog` **resta in `scripts/`**: nessuno lo importa. Scrive
  `data/istat_catalog/catalog_dataflows.csv`, che `gsp.istat.sdmx` legge
  come cache — il legame è un file, non un `import`

### Le copie eliminate

`scripts/fast_F.py` e `scripts/test_F.py` erano **identici byte per byte**
ai file in `maxent-popsynth-pcd/src/`. Cancellati; `gibbs_lab` li importa
dal repo con `importlib`, come già faceva per il solver.

`preflight.sh`, `run_regression.sh` e `regress_fit.py` sono in archivio:
erano il pre-volo di un esperimento concluso — misurare quanto valesse
`fast_F` confrontando il fit prima e dopo. Le patch sono state adottate e
stanno nel repo pubblico, quindi quei controlli oggi verificano uno stato
che non esiste più, e in direzione **invertita**.

### Metodo di verifica

Baseline catturata **prima** di toccare qualsiasi cosa, spostamento,
confronto. Per il riordino di `scripts/` la baseline migliore è stata
`rigenera.sh --dry-run`, che **stampa i comandi senza eseguirli**: dopo lo
spostamento il `diff` mostrava esattamente 44 righe — quattro comandi per
undici comuni — cambiate solo nella sottocartella, più il timestamp del
log. Niente altro.

Per gli script senza `argparse` il `--help` produce un traceback che
contiene il **percorso del file**: la differenza è attesa, e il confronto
va fatto ignorandolo (`sed 's|/home[^"]*/||'`).

`git mv` e non `cp` + `rm`, così `git log --follow` continua a raccontare
la storia di ogni file.

### Cosa non è stato fatto, di proposito

- **`_radice()` non è stata spostata** in `common.py`. Serve a `gsp.fonti`
  e servirebbe a `gsp.istat.sdmx`, che oggi cabla
  `~/progetti/gsp/data/istat_catalog/...` e **funziona**. Il momento di
  generalizzarla è quando servirà a un terzo modulo: allora la
  duplicazione diventa reale invece che ipotetica.
- **`fit/` ha un file solo.** Una cartella per un file è discutibile, ma
  la fase è concettualmente distinta e ci andranno le varianti per
  Leonardo.

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

`--verifica` controlla che il riferimento regga. Nota che
`opendata_paese` qui è il nome della **chiave di configurazione**, non
del modulo: il modulo è diventato `gsp.opendata`, la chiave resta.

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
distanza, non un campione indipendente**.

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
meno restrittiva, ma il `!Leggimi` **non dichiara una licenza**. Il
tracciato è passato a `archiviazione: locale` per questo: era l'unico
grezzo in git con licenza non verificata.

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
valle. Modalità da 8 a 33 per quartiere.

**Reggio Emilia** — matrice larga, ISO-8859-1, **2013**. L'uso è
giustificato da una verifica del 1/8/2026 sui ranghi delle quote UE per
zona: 4-2-1-3 nel 2013 contro 4-1-2-3 nel 2023, unico scambio fra zone
che nel 2023 distano 0,003. **È questa verifica, non la data, a rendere
la fonte usabile.**

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
cioè **struttura familiare**. Distanza media dalla composizione comunale
**0,569**, il triplo di Forlì: da capire se il salto sia dovuto alla
scala (sezione contro quartiere) o alla ricchezza della fonte (microdati
contro tabella aggregata).

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
  e `sum(w)²` con somma 5,8e11 sfonda int64.

### `residuo_quota` come criterio comparabile

L'ipotesi «più fine la geografia, più informazione nel residuo» reggeva
passando da Reggio (4 unità, 6,1%) a Forlì (41 unità, 16,5%). **È
falsa**: Bologna ha 19 zone e zero residuo. La relazione dipende da come
il comune costruisce la pubblicazione. E a Bologna la fonte nomina 155
paesi contro i 119 che l'IPF produce dal censimento: il margine B è più
ricco del margine A, il contrario del caso generale.

---

## 5. Donatori AVQ — questione CHIUSA

### 5.1 Le due previsioni falsificate

**«`assign_avq.py` non stampa i donatori usati»** — falso, la riga c'era.
**«La validazione delle correlazioni è stata rimossa»** — falso, il blocco
gira sempre. Entrambe attribuivano allo script **meno** diagnostica di
quanta ne abbia, ed entrambe erano state dedotte dai log invece che dal
sorgente.

Una terza, sulla stessa giornata: lo scarto di `FIDUCIA` nei marginali
spiegato come effetto della dicotomia, mentre il §13.5 del riferimento
aveva già la spiegazione migliore — è **differenza compositiva
comune–regione**, e segue il gradiente d'istruzione su quattro città.

### 5.2 Il difetto vero: la maschera contava la quantità sbagliata

La soglia mascherava le correlazioni con meno di 100 donatori, ma li
contava sui **disponibili nel pool**, mentre l'informazione indipendente
viene dai donatori **estratti**. Corretto con
`n_coppia = ok_u.T @ ok_u` sui soli estratti, più il conteggio di quante
coppie la vecchia soglia lasciasse passare: **zero su tutti i comuni**.
Il difetto era teorico, ma la quantità ora è quella giusta.

C'era anche una collisione di nome: `n_don` era prima lo scalare degli
estratti, poi **sovrascritto** dalla matrice dei disponibili. Ora si
chiamano `n_estratti` e `n_coppia`.

### 5.3 Donatori estratti: misurati

| comune | estratti / pool | riuso medio |
|---|---|---|
| Brescia | 8.111 / 8.111 — **100%** | 24,4× |
| Modena | 4.617 / 4.629 — 99,7% | 40,0× |
| Castenaso | 4.336 / 4.629 — **93,7%** | 3,8× |

### 5.4 Il confronto sintetico/donatori, ridotto a tre numeri

| comune | mediano | massimo | peggiore coppia | n | atteso ~1/√n |
|---|---|---|---|---|---|
| Brescia | 0,005 | 0,031 | `VOTOUSL × BMI` | 1.258 | 0,028 |
| Modena | 0,007 | 0,046 | `FIDMED × FORZE_ARMATE` | 1.130 | 0,030 |
| Castenaso | 0,009 | 0,061 | `CRONI × FORZE_ARMATE` | 1.001 | 0,032 |

**Il mediano scala con il riuso, non con la popolazione.** Osservato su
atteso resta fra 1 e 2 ovunque: su 253 coppie, con 253 estrazioni il
massimo di una normale standard sta tipicamente sui 2,8σ. Non è un
difetto della procedura, è la coda della distribuzione degli scarti.

**La frase difendibile:** *su 253 coppie, lo scarto fra le correlazioni
della popolazione sintetica e quelle dei donatori AVQ ha mediana 0,007 e
massimo 0,046, con le tre peggiori entro 1,5 errori standard della loro
numerosità effettiva.*

### 5.5 Le collisioni: spiegate, non risolvibili

Scomposizione sul pool emiliano-romagnolo (4.629 donatori, 456
collisioni), per numero di variabili mancanti su 23:

| n mancanti | donatori | firme | collisioni | quota |
|---|---|---|---|---|
| 0–4 | 2.095 | 2.095 | **0** | 0,000 |
| 5 (annata 2023) | 1.697 | 1.693 | 4 | 0,002 |
| 6–18 | 314 | 313 | 1 | 0,003 |
| **19** | 118 | 25 | **93** | **0,788** |
| **20** | 337 | 31 | **306** | **0,908** |
| **21** | 64 | 12 | **52** | **0,812** |

**452 su 456 — il 99% — stanno nelle righe 19–21**, cioè i minori.
Nessuna variabile aggiuntiva le eliminerà, perché per quei donatori le
variabili aggiuntive sono proprio quelle che mancano. Questo spiega
perché passare da 21 a 23 variabili non le abbia ridotte.

### 5.6 `donor_id` scritto a monte — FATTO

`assign_avq.py` scrive la colonna `donor_id` dal 2/8/2026. L'identità è
**stabile fra corse**: `"2024:12345"`, annata più riga dentro l'annata —
non l'indice del pool, che slitta quando cambia l'insieme delle annate.
In Parquet costa 0,32 MB grazie al dictionary encoding, quanto un intero.

`to_parquet.py` di Animarium la usa se c'è e ripiega sulla firma se
manca, dichiarando la fonte nel log.

**L'effetto misurato**, ed è quello che chiude il §13.3 del riferimento:

| | firma | colonna | fattore |
|---|---|---|---|
| Brescia | 1.093 | **6.618** | 6,1 |
| Modena | 862 | **3.741** | 4,3 |
| Castenaso | 741 | **3.205** | 4,3 |

`n_eff` sull'intera popolazione quadruplica e **smette di essere
erratico**: Brescia sta al doppio degli altri perché attinge al pool
lombardo (8.111 contro 4.629), rapporto 1,77 contro il 1,75 dei pool.
Segue il pool regionale, come già faceva la colonna sull'universo della
variabile.

**Sull'universo della variabile invece non cambia nulla**: 3.220 → 3.227
su Modena, +0,2%, e i donatori distinti su `PUNTIFI10` sono 4.010 con la
colonna contro 4.012 con la firma. Le collisioni stanno interamente fra i
minori, che l'universo 15+ esclude per costruzione.

Quindi la raccomandazione del §13.3 — `n_eff` per variabile, sul suo
universo — non era solo più corretta statisticamente: era **immune al
difetto dell'identificatore**. Nessuna banda pubblicata era sbagliata, e
la colonna `banda` dell'indice Animarium è invariata a tutte le cifre.

### 5.7 Ancora aperto

Equipesare le annate (`w = COEFIN / somma dell'anno`) implica un pool che
rappresenta una media del triennio e non la popolazione a una data. Per
donare attributi è *probabilmente* irrilevante, ma non è stato
verificato.

---

## 6. I tre repo

| repo | remoto | stato |
|---|---|---|
| `gsp` | `github.com/mirko-degli-esposti/gsp` | pipeline e registro |
| `animarium` | `github.com/mirko-degli-esposti/Animarium` | viewer, dipendenza da `gsp` dichiarata in `pyproject.toml` |
| `maxent-popsynth-pcd` | pubblico | solver, tag `submission-tkdd` |

**Animarium** è uscito da `~/progetti/gsp/` e vive in
`~/progetti/animarium`. Prima era annidato **e ignorato** dal
`.gitignore` di GSP: lo stato peggiore, perché `git status` non lo vedeva
e chi apriva la cartella non capiva se fosse tracciato. Nove script di
`build/` importano `gsp.common`; è una dipendenza di **sola build**, il
sito servito staticamente non dipende da GSP.

**`maxent-popsynth-pcd`** non contiene copie divergenti: `fit_cs.py` e
`gibbs_lab.py` importano il solver da lì con `importlib`. Il tag
`submission-tkdd` marca `ecf35f3` (31 marzo 2026), l'ultimo commit prima
di tre mesi di silenzio; i tre commit di luglio — warm start, blocchi
mixed-radix ~145×, `lr_tau` — sono ottimizzazioni successive.
`gibbs_pcd_solver_old.py` è tenuto **deliberatamente** come riferimento
di regressione, non è un residuo.

Leggendo il README per aggiornarlo sono saltati fuori quattro errori:
**arXiv sbagliato nel BibTeX** (`2503.XXXXX` invece di `2603.27312`),
flag `--use_numba` inesistente (è `--no_numba`), numba dichiarato
«optional» e «required» nella stessa pagina, e la cartella delle figure
sbagliata. Nessuno rompe il codice, tutti rompono l'esperienza di chi
prova a riprodurre. È lo stesso scarto che il registro trova fra ciò che
una scheda dichiara e ciò che il file contiene — qui il registro era il
README e nessuno aveva mai fatto il confronto.

---

## 7. Questioni aperte

### 7.1 Etichette di blocco disallineate

| tavola | la tupla dice | il file prodotto è |
|---|---|---|
| `cens_istruzione_cittadinanza` | C3 | `c5_edu_citizenship.csv` |
| `cens_condprof_cittadinanza` | C4 | `c6_condprof_citizenship.csv` |
| `cens_stranieri_paesi` | C6 | `nationality_conditional.csv` |

C6 assegnato due volte. Nel registro il campo `blocco` segue **il nome
del file**.

### 7.2 Difetti delle fonti

- **`ETA = -1`** a Parma, un record: dato sporco confermato.
- **Ravenna 2024** da riscaricare.
- **`Ncomp`** non usabile senza condizionare su `Tipores`.

### 7.3 Fonti non registrate

- **`data/istat_catalog/`** — `catalog_dataflows.csv` (641 KB) derivato
  da `catalog_dataflows.xml` (13,6 MB). È un **indice**, non un dato:
  dice cosa esiste, non cosa contiene. `gsp.istat.sdmx` lo legge come
  cache. Serve un normalizzatore `elenco_csv` senza `peso`.
- **`data/istat_structures/`** (120 MB): DSD e codelist SDMX.
- **`data/geodata/`** (1,7 GB): mai guardato.
- **Licenze dei sette portali comunali** e di AVQ.

### 7.4 Rifiniture rimandate

- `resolve_pop_file` con regole diverse fra script: `assign_avq` ed
  `enrich` preferiscono K10C, `to_parquet` lo esclude. Su undici comuni
  su dodici coincidono, su Brescia no — e chi rigenera a mano senza
  `--pop-file` produce un file che il viewer ignora.
- `_radice()` in `common.py`, quando servirà a un terzo modulo.

---

## 8. Come si aggiunge una fonte

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

## 9. Trappole imparate

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

**`sed -i 'Nd'` è cieco**: cancella una riga per numero senza guardarne
il contenuto, e il numero spesso viene da un messaggio d'errore invece
che dal file. Meglio uno script che stampa cosa sta per fare.

**Dopo ogni modifica a mano, stampare il risultato**, non solo validare:
`usabile_per: [a b]` senza virgola è YAML valido e produce **un solo
elemento**. E `[tutto: il file e' vuoto]` è una mappa, non una stringa.

**I numeri di riga invecchiano.** Ancorarsi a un pattern, non a un
numero — e mai calcolarli su una copia del file per applicarli a
un'altra.

**L'sha256 della stringa vuota è `e3b0c442…852b855`.**

**Un difetto localizzato non deve far perdere le informazioni buone.**
`_impronta_multi` si fermava alla prima istanza illeggibile.

**Attenzione ai tipi interi in operazioni quadratiche.** `sum(w)²` su
int64 con somma 5,8e11 wrappa a negativo: convertire a float **prima**.

**`np.fill_diagonal(D.values, ...)` non funziona con pandas 3**: il
`.values` è una vista in sola lettura — meglio della variante silenziosa
che scriveva su una copia. Si maschera per etichette.

**`astype(str)` lascia i NaN come float**, e `"|".join` fallisce.

**I file da Windows arrivano `100755`.** `chmod 644`.

**Il browser rinomina i file omonimi** e l'estrazione appiattita di uno
zip fa collidere i file omonimi *dentro* lo zip.

**`python-calamine` si importa come `python_calamine`.**

**Confrontare invocazioni diverse dello stesso script non misura nulla.**
Il bundle di Modena è passato da 5,12 a 3,68 MB, e ho cercato la causa
in `donor_id` prima di accorgermi che `build_bundle` passa
`--drop-avq-raw` e la mia invocazione no. Il segnale che avrei dovuto
cogliere: Reggio *saliva* invece di scendere.
