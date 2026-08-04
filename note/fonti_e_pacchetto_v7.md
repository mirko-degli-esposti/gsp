# Registro delle fonti, pacchetto `gsp`, attributi derivati — v7

Aggiornata il 4 agosto 2026. Sostituisce la v6. Rispetto a quella:
**trentaquattro fonti**, l'onomastica è completa — il ramo straniero
copre il 59,2% degli stranieri con nome e cognome del loro paese — e il
registro ha valutato per la prima volta una **fonte di terze parti**
invece che istituzionale, accettandola per metà con i limiti misurati.

---

## 1. Il pacchetto e gli script

### Il criterio

**Nel pacchetto va ciò che qualcun altro importa.** Che abbia anche una
CLI è irrilevante: `gsp.common` ce l'ha, e `python -m` la serve.

**In `scripts/` va ciò che si esegue.** Il legame con il pacchetto può
essere un `import` — e allora il modulo sta nel pacchetto — oppure un
**file**: `istat_catalog` scrive `catalog_dataflows.csv` che
`gsp.istat.sdmx` legge, `medie_nazionali` scrive un JSON che Animarium
consuma. Il legame-file non giustifica il pacchetto.

### Struttura

```
~/progetti/gsp/
  pyproject.toml
  src/gsp/
    __init__.py            vuoto: importare `gsp` non deve tirarsi dietro
                           pandas, numba e yaml
    common.py              registro dei 12 comuni e primitive condivise
    opendata.py            fonti locali per il paese di cittadinanza
    istat/sdmx.py          client SDMX (4 query/minuto)
    nomi/__init__.py       repertori onomastici deterministici
    istruzione.py          titoli di studio dettagliati
    individui.py           accesso con i tre regimi di disclosure
    fonti/
      __init__.py          il registro delle fonti
      __main__.py          abilita `python -m gsp.fonti`
      normalizzatori.py    13 funzioni pure grezzo -> canonico

  scripts/
    rigenera.sh · run_avq.sh          orchestrazione
    acquisizione/    istat_catalog · fetch_comune
    vincoli/         build_constraints · build_sezioni ·
                     build_zona_tables · cs_build · join_civici_sezioni
    fit/             fit_cs
    attributi/       assign_nationality · assign_avq · enrich
    diagnostica/     verifica_vincoli · verifica_donor · ispeziona_avq ·
                     ispeziona_cs · diag_quinq · diag_istruzione_eta ·
                     zona_probe · perm_composizione
    gibbs/           gibbs_lab · profile_gibbs · test_invariance ·
                     test_moves · batch_lambda.sh · batch_scaling.sh
    riferimenti/     medie_nazionali

  scripts_archivio/  preflight · run_regression · regress_fit ·
                     check_marginals
  fonti/             registro, grezzi, metadati, impronte, DERIVATI
  data/              4,7 GB, fuori da git
  note/  note/storico/
```

`pip install -e .` nell'ambiente `ml`. Dipendenze: `pandas`, `numpy`,
`pyarrow`, `pyyaml`, `xlrd`, `openpyxl`, `python-calamine`.

### Metà di `animarium/build/` non era Animarium

`build/` aveva quattordici file e 3.377 righe; ne restano sette e 1.718.
Sei diagnostici e `medie_nazionali` sono passati a GSP.

Erano lì per **quando** sono stati scritti, non per **cosa** fanno: le
etichette `F0(a)`, `F0(b)`, `F2`, `F3`, `F4` sono le lacune del design di
Animarium, e quei diagnostici sono nati per rispondere a domande che il
viewer poneva. È la stessa storia di `preflight.sh` in GSP — strumenti di
una fase, sedimentati dove la fase si svolgeva.

Tre di essi si dichiaravano già in bilico nel titolo: «Animarium / GSP».

**`check_marginals` e `verifica_vincoli` erano lo stesso strumento**,
scritti a due giorni di distanza: entrambi normalizzano l'errore contro
il pavimento di campionamento, ed entrambi si aprono spiegando che
l'errore relativo grezzo su celle piccole non significa niente.
`check_marginals` lo dice in forma teorica —
`z = (α_oss − α)/√(α(1−α)/N)`, mediana 0,674, media 0,798 —
`verifica_vincoli` in forma empirica: «la v1 trovava celle sbagliate del
132%, ma quelle celle avevano valore atteso 1,3 individui». La stessa
scoperta raccontata due volte. Resta la v2 (30 luglio), l'altra in
archivio.

### Le dipendenze locali, sciolte

Nessuno script in `scripts/` importa più un altro: era la condizione per
riordinare senza rompere niente.

- `gsp_common` → `gsp.common` (undici importatori)
- `istat_sdmx` → `gsp.istat.sdmx` (`fetch_comune`)
- `opendata_paese` → `gsp.opendata` (`enrich`, **una sola funzione**:
  `tabella_paese(comune, anno-1)`)
- `fast_F` e `test_F`: erano copie **identiche byte per byte** di
  `maxent-popsynth-pcd/src/`. Cancellate; `gibbs_lab` le importa dal repo
  con `importlib`, come già faceva per il solver

### Metodo di verifica

Baseline **prima**, spostamento, confronto. Per il riordino di `scripts/`
la baseline migliore è stata `rigenera.sh --dry-run`, che stampa i
comandi senza eseguirli: il `diff` mostrava esattamente 44 righe — quattro
comandi per undici comuni — cambiate solo nella sottocartella.

Per gli script senza `argparse` il `--help` produce un traceback che
contiene il **percorso del file**: la differenza è attesa, e il confronto
va fatto ignorandolo (`sed 's|/home[^"]*/||'`).

---

## 2. Il registro delle fonti

### Il principio

> **Ogni fonte richiede il suo universo dichiarato.** Un file senza
> universo è un elenco di numeri, non una misura.

### Struttura sul disco

```
fonti/
  registro.yaml        scritto a mano: universo, licenza, uso
  repertori.yaml       configurazione onomastica (§6)
  grezzi/              i file originali sotto i 5 MB, versionati
  derivati/            prodotti da GSP, registrati come fonti
  metadati/            DCAT, note metodologiche, tracciati d'origine
  impronte/            GENERATE: firma di ogni fonte, sempre in git
  norm/                GENERATE: Parquet canonici, ricostruibili
  ATTRIBUZIONI.md      GENERATO: obbligo CC-BY verso chi riceve i dati
```

**Il grezzo è immutabile.** Le correzioni vivono nel normalizzatore, che
è codice versionato; le stranezze restano dichiarate in `anomalie`.

**`derivati/` è nuova** e la distinzione è deliberata: `grezzi/` è ciò che
si è scaricato, `derivati/` ciò che si è calcolato. Un derivato è una
fonte a pieno titolo — ha universo, licenza, impronta — ma dichiara anche
da cosa viene.

### Tre livelli di archiviazione

```
git      grezzo versionato: riproducibile da un clone     (< 5 MB)
locale   grezzo su disco, gitignorato: verificabile qui
remoto   nessun grezzo: resta l'URL, l'impronta è l'unica prova
```

### Due tipi di fonte

**`file`** — una fonte, un file, un hash. Il grezzo sta in `fonti/grezzi/`
oppure, se `percorso` è dichiarato, dove vive già.

**`multi_istanza`** — una scheda per *tavola*, tante istanze uguali per
forma e diverse per chiave. `percorso` contiene un pattern con
`{istanza}` e `--scansiona` le rileva da sole.

### `parametri_da` e `derivato_da`: le due relazioni

**`parametri_da`** referenzia la configurazione operativa invece di
riscriverla:

```yaml
parametri_da: common.COMUNI.017029.opendata_paese
```

`--verifica` controlla che il riferimento regga. Nota che
`opendata_paese` qui è il nome della **chiave di configurazione**, non del
modulo: il modulo è diventato `gsp.opendata`, la chiave resta.

**`derivato_da`** è nuovo, e traccia una **catena** invece di una fonte
singola:

```yaml
derivato_da: [avq_microdati]
prodotto_da: scripts/riferimenti/medie_nazionali.py
```

Tre cose si propagano senza doverle riscrivere: la licenza con la sua
attribuzione, la perturbazione per la riservatezza, e il caveat che le
stime differiscono da quelle pubblicate.

**Da fare**: `--verifica` potrebbe segnalare se un derivato è **più
permissivo della sua origine** — `archiviazione: git` su un derivato di
una fonte con licenza non chiarita. Con un solo derivato non giustifica
il codice, ma è il tipo di errore che si fa una volta e si paga caro.

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

### I sedici normalizzatori

| nome | forma | diagnostica caratteristica |
|---|---|---|
| `distribuzione_csv` | `chiave, peso` | modalità, n_misurato, chiavi fuse |
| `matrice_csv` | largo → `chiave, zona, peso` | zona_nomi, **residuo_quota** |
| `formato_lungo` | melt di colonne affiancate | unità escluse, n per sesso |
| `tabella_parquet` | lungo, con filtro d'anno | anni_n, anno_usato |
| `excel_aree_sesso` | doppia intestazione Excel | zona_nomi, n_M, n_F |
| `microdati_csv` | record individuali | **min/max e negativi per colonna** |
| `codebook_csv` | `campo, codice, etichetta` | codici_per_campo, segnaposto |
| `riferimenti_json` | derivato con metadati in testa | **fonte, metodo, se_grappolo** |
| `onomastico_csv` | repertorio per paese, con romanizzazione | paesi, voci per paese, con/senza peso, sessi |
| `classificazione_xlsx` | classificazione ufficiale multi-foglio | fogli, righe per foglio, colonne di raccordo |
| `archivio_zip` | l'archivio, **senza decomprimerlo** | file dentro, byte non compressi, date |
| `sdmx_csv` | frame intatto | dataflow, ref_area, anni, obs_somma |
| `sezioni_xlsx` | frame intatto | sezioni, comuni, popolazione, vuote |
| `tracciato_xlsx` / `tracciato_csv` | `chiave, definizione` | campi, senza_definizione |
| `avq_microdati` | colonne di struttura | somma_pesi, **n_eff_kish** |

**Trappola ricorrente**: `distribuzione_csv` abbassa i nomi di colonna,
quindi `col_chiave` e `col_peso` vanno in **minuscolo** anche se nel file
sono maiuscoli. L'errore è `KeyError: 'chiave'`, che non aiuta.

---

## 3. Le trentaquattro fonti

### Cognomi — Comune di Firenze (2)

CC-BY-4.0, in git, metadato DCAT, `notPlanned`.
`firenze_cognomi_2013`: 375.371 residenti, 66.353 cognomi distinti, 51%
hapax; Chao1 stima ~125.000 nella popolazione generatrice.
`firenze_cognomi_2012` è solo controllo di stabilità: correlazione 0,9985
— stessa popolazione a un anno di distanza, non un campione indipendente.

Il limite è regionale: `TOLOMELLI`, primo ad Argelato, non compare in
375.371 fiorentini; `INNOCENTI` è l'artefatto dell'Ospedale degli
Innocenti.

### Nomi — Comune di Modena (1)

CC-BY-4.0 con URI del vocabolario controllato AgID, via
dati.emilia-romagna.it, servito da un **WFS di GeoServer**.
Multi-istanza su `sesso`, 650 righe per file, esattamente 50 nomi per
anno.

Sei anomalie registrate, e nessuna si sarebbe ritrovata dopo: il titolo
dice «dal 2012 al 2022» ma i dati arrivano al **2024**; il catalogo dice
«nomi attribuiti ai nati» ma sono lo **stock** dei residenti (1.390
ANTONIO nel 2015 non sono neonati); quattro colonne di servizio WFS con
`SHAPE` che è il centroide di Modena ripetuto 650 volte; i due file hanno
timestamp CKAN di due anni e mezzo di distanza, decodificati dal campo
`hash`; namespace WFS diversi fra maschile e femminile.

A differenza dei cognomi fiorentini la scelta è **regionalmente coerente**
per dieci comuni su dodici.

### ISTAT SDMX — 11 tavole × 12 comuni

CC-BY-4.0, `archiviazione: locale`. **4 query/minuto**.

| | universo | ruolo |
|---|---|---|
| `istat_anag_sesso_eta_statociv` | anagrafe, 1 gennaio anno **N** | C1, unico **hard** |
| altre dieci | censimento permanente, 31 dicembre anno **N−1** | C2–C10, **soft** |

Serie 2019–2025 e 2018–2024: sette anni ciascuna, sfalsate di uno perché
sono gli **stessi sette istanti**.

`obs_somma` è ~2× e ~8× la popolazione per via degli aggregati: **firma
per riconoscere il file, non conteggio**.

### Sezioni di censimento (2)

**135.725 sezioni**, 18,35 milioni di residenti. Geometria del censimento
**2021**, dati **2023**. **10.872 sezioni senza residenti**.

### AVQ (3, di cui uno derivato)

**`avq_microdati`** — licenza **CC-BY-4.0 inferita**, non letta: la pagina
AVQ non ne dichiara una propria e si applica quella generale del sito.
Verificato dentro lo zip di tutte e tre le annate: il `!Leggimi`
qualifica i file come «ad uso pubblico» — la classe meno restrittiva — e
né esso né i quattro PDF pongono condizioni d'uso, divieti di
ridistribuzione o clausole sulla reidentificazione.

`unita: individuo campionario`. **`COEFIN` ha quattro decimali impliciti**
(`scala_peso: 10000`).

| anno | record | somma pesi | n_eff Kish |
|---|---|---|---|
| 2022 | 42.022 | 58.499.237 | 31.015 |
| 2023 | 41.750 | 58.380.189 | 31.386 |
| 2024 | 45.005 | 58.620.700 | 34.154 |

I record del 2022 coincidono con i 42.022 dichiarati nel `!Leggimi`.

**Riservatezza**: i file sono già sottoposti da ISTAT al trattamento per
la tutela della riservatezza — «a causa del trattamento dei dati per la
tutela della riservatezza, le elaborazioni possono condurre a risultati
in qualche misura difformi rispetto a quelli pubblicati». La protezione è
**incorporata nel dato**, non affidata a una clausola d'uso.

**Limite territoriale**: il file pubblico è prodotto dall'MFR per
sottocampionamento e ne eredita struttura e trattamento, ma **non la
classe di ampiezza demografica del comune** (verificato sul tracciato
2024: assente). Il condizionamento si ferma quindi alla **regione**:
Bologna con 390.098 abitanti e Castenaso con 16.357 attingono allo stesso
pool di 4.629 donatori. **La geografia della cittadinanza è condizionata
fino alla sezione, quella degli attributi AVQ si ferma alla regione** —
due risoluzioni molto diverse nello stesso record.

**`avq_medie_nazionali`** — il primo derivato. Medie ponderate nazionali
delle 23 variabili, con `se` e `se_grappolo`. **Non esiste una fonte
ISTAT equivalente**: la batteria di fiducia non è pubblicata in forma
aggregata, e le cinque medie cablate nel viewer venivano da un'origine
mai identificata. Ricalcolate coincidono entro 0,045 e ne coprono
ventitre invece di cinque.

### Titoli di studio (2)

**`claist_2026`** — la Mappa dei percorsi di istruzione ISTAT, che
sostituisce la Classificazione del 2003. Gerarchia su sei livelli, 61
programmi al primo e ~20.000 percorsi al sesto, sedici fogli e 29.282
righe. Il registro normalizza il foglio «Schema sintetico», 104 righe e
**42 titoli**: il livello utile per attribuire un titolo a un individuo.
È un **vocabolario**, non una distribuzione. Il suo valore è il livello 2,
l'**ordinamento**: il decreto di riferimento, che storicizza la mappa. E
il vincolo temporale è dentro i titoli stessi — «DIPLOMA DI MATURITÀ
(ANTE 2010)» contro «DIPLOMA DI SUPERAMENTO DELL'ESAME DI STATO» — quindi
non serve imporre la coorte dall'esterno.

**`cens2011_titolo_studio`** — le frequenze, dal censimento 2011. 458
modalità in un **albero dichiarato dalla fonte**: il codebook ha una
colonna `padre` e le radici puntano a sé stesse. 399 foglie, 9 rami con
dati, universo 6 anni e più.

Il ramo della maturità ha 32 foglie ed è il livello giusto per una
biografia — «istituto tecnico per geometri», «liceo classico». Il
terziario ne ha 345: 180 per la triennale, 112 per il diploma
universitario v.o., 53 per la magistrale.

### Geodata (2)

Registrate come **ZIP**, non come estratti: lo zip è il grezzo
immutabile, l'estratto è cache di lavoro che la pipeline legge tramite i
percorsi dichiarati in `gsp.common.REGIONI`. Il backup delle fonti
geografiche passa da 1,7 GB a 230 MB, e `--verifica` non calcola l'hash
di mezzo giga.

**`istat_sezioni_shp`** — geometrie del censimento 2021, per regione.
**`anncsu_indirizzario`** — i civici georeferenziati, ed è la fonte con
la posizione giuridica più forte del registro: **high-value dataset** ex
Reg. (UE) 2023/138, con le Specifiche tecniche adottate **previo parere
positivo del Garante** (12 dicembre 2024). L'apertura di quei dati è
stata vagliata dall'autorità competente.

Il pattern `percorso` ammette un `*` accanto a `{istanza}`, perché i nomi
non sono uniformi fra regioni: `R03_21.zip`, `R08_21.zip`, `R16_21.zip`
sono i codici regione ISTAT.

### Repertori onomastici (3)

**`firenze_cognomi_2013`** e **`modena_nomi_residenti`** per il ramo
italiano (vedi sopra e §6).

**`popular_names_cognomi`** e **`popular_names_nomi`** — stessa fonte in
due file, CC0, da Wikipedia luglio 2023. 2.278 cognomi da 75 paesi e
2.370 nomi da 106, con romanizzazione e sesso. Universo dichiarato: il
testing del software.

### Le sei fonti locali (7 schede)

| comune | tier | unità | paesi | residuo | sesso | età |
|---|---|---|---|---|---|---|
| Parma | 3 | **1.320 sezioni** | 151 | — | sì | sì |
| Bologna | 2 | 19 zone | 155 | **0%** | sì | no |
| Forlì | 1 | 41 sub-quartieri | 42 | **16,5%** | sì | no |
| Brescia | 1 | 33 quartieri | 8–33 per file | variabile | no | no |
| Ravenna | 1 | 10 aree | ~40 | — | sì | no |
| Reggio E. | 1 | 4 circoscrizioni | 25 | **6,1%** | no | no |

Distanza media dalla composizione comunale: Forlì **0,170**, Parma
**0,569**. Da capire se il salto sia dovuto alla scala (sezione contro
quartiere) o alla ricchezza della fonte (microdati contro tabella
aggregata).

---

## 4. Cosa il registro ha già trovato

- **Due file scaricati vuoti** (0 byte) mai notati: Piacenza e Ravenna
  2024. Da qui il controllo `SHA_VUOTO`.
- **`unita` sparita** da `istat_cens_settore_prof` in un'edit manuale.
- **Un record con `ETA = -1`** su 202.111 a Parma, trovato dal controllo
  di plausibilità di `microdati_csv`. Il codebook ha stabilito che `ETA`
  è «numerico» senza valori speciali: **dato sporco, non convenzione**.
  Nessuna delle due cose da sola bastava.
- **`Ncomp` fino a 319**: convivenze anagrafiche, non famiglie.
- **`cens_posizione_famiglia` mai usata.**
- **Overflow int64 nel Kish**: `n_eff` negativo perché `sum(w)²` con
  somma 5,8e11 sfonda int64.
- **Il titolo di un dataset che mente** sulla copertura temporale.

### `residuo_quota` come criterio comparabile

L'ipotesi «più fine la geografia, più informazione nel residuo» reggeva
da Reggio (4 unità, 6,1%) a Forlì (41 unità, 16,5%). **È falsa**: Bologna
ha 19 zone e zero residuo. La relazione dipende da come il comune
costruisce la pubblicazione. E a Bologna la fonte nomina 155 paesi contro
i 119 che l'IPF produce dal censimento: il margine B è più ricco del
margine A, il contrario del caso generale.

---

## 5. Donatori AVQ — CHIUSA

### Le previsioni falsificate

**«`assign_avq.py` non stampa i donatori usati»** — falso, la riga c'era.
**«La validazione delle correlazioni è stata rimossa»** — falso, il blocco
gira sempre. Entrambe attribuivano allo script **meno** diagnostica di
quanta ne abbia, ed entrambe erano dedotte dai log invece che dal
sorgente.

Una terza: lo scarto di `FIDUCIA` spiegato come effetto della dicotomia,
mentre il §13.5 del riferimento aveva già la spiegazione migliore —
**differenza compositiva comune–regione**, che segue il gradiente
d'istruzione su quattro città.

### Il difetto vero

La soglia mascherava le correlazioni con meno di 100 donatori, ma li
contava sui **disponibili** invece che sugli **estratti**. Corretto;
**zero coppie** lasciate passare su tutti i comuni, quindi il difetto era
teorico — ma la quantità ora è quella giusta.

C'era anche una collisione di nome: `n_don` era prima lo scalare degli
estratti, poi sovrascritto dalla matrice dei disponibili. Ora
`n_estratti` e `n_coppia`.

### Donatori estratti e scarto delle correlazioni

| comune | estratti / pool | riuso | mediano | massimo | n | atteso ~1/√n |
|---|---|---|---|---|---|---|
| Brescia | 8.111/8.111 (**100%**) | 24,4× | 0,005 | 0,031 | 1.258 | 0,028 |
| Modena | 4.617/4.629 (99,7%) | 40,0× | 0,007 | 0,046 | 1.130 | 0,030 |
| Castenaso | 4.336/4.629 (**93,7%**) | 3,8× | 0,009 | 0,061 | 1.001 | 0,032 |

**Il mediano scala con il riuso, non con la popolazione.** Osservato su
atteso resta fra 1 e 2 ovunque.

> *Su 253 coppie, lo scarto fra le correlazioni della popolazione
> sintetica e quelle dei donatori AVQ ha mediana 0,007 e massimo 0,046,
> con le tre peggiori entro 1,5 errori standard della loro numerosità
> effettiva.*

### Le collisioni: spiegate, non risolvibili

| n mancanti su 23 | donatori | firme | collisioni | quota |
|---|---|---|---|---|
| 0–4 | 2.095 | 2.095 | **0** | 0,000 |
| 5 (annata 2023) | 1.697 | 1.693 | 4 | 0,002 |
| 6–18 | 314 | 313 | 1 | 0,003 |
| **19–21** | 519 | 68 | **451** | **0,87** |

**Il 99% sta nei minori**, ai quali le domande su fiducia, salute
percepita, fumo, benessere psicologico e antropometria non vengono poste.
Nessuna variabile aggiuntiva le eliminerà, perché per quei donatori le
variabili aggiuntive sono proprio quelle che mancano.

### `donor_id` scritto a monte — FATTO

Identità **stabile fra corse**: `"2024:12345"`, annata più riga dentro
l'annata — non l'indice del pool, che slitta quando cambia l'insieme
delle annate. In Parquet costa 0,32 MB grazie al dictionary encoding.

| | firma | colonna | fattore |
|---|---|---|---|
| Brescia | 1.093 | **6.618** | 6,1 |
| Modena | 862 | **3.741** | 4,3 |
| Castenaso | 741 | **3.205** | 4,3 |

`n_eff` sull'intera popolazione quadruplica e **smette di essere
erratico**: Brescia sta al doppio degli altri perché attinge al pool
lombardo, rapporto 1,77 contro il 1,75 dei pool.

**Sull'universo della variabile invece non cambia nulla**: 3.220 → 3.227
su Modena, +0,2%. Le collisioni stanno fra i minori, che l'universo 15+
esclude per costruzione. Quindi la raccomandazione del §13.3 — `n_eff`
per variabile — era **immune al difetto dell'identificatore**, e nessuna
banda pubblicata era sbagliata.

### Ancora aperto

Equipesare le annate implica un pool che rappresenta una media del
triennio e non la popolazione a una data. Per donare attributi è
*probabilmente* irrilevante, ma non è stato verificato.

---

## 6. `gsp.nomi` — l'onomastica

### Il principio

**Il nome non è una colonna della popolazione.** È generato al momento
del bisogno da una funzione deterministica dell'`id`, e non finisce mai
in un file. Il determinismo **sostituisce la memorizzazione**: dallo
stesso id esce sempre lo stesso nome, quindi il risultato è riproducibile
e citabile senza essere scritto.

Serve a rendere naturali i persona-prompt degli agenti LLM. Per quell'uso
la fedeltà della coda è irrilevante.

### Tre strati, perché cambiare sorgente non tocchi il codice

**Il repertorio** è una fonte del registro più la dichiarazione di cosa
condiziona (`fonti/repertori.yaml`). `condiziona: []` è una lista unica,
`condiziona: [sesso]` seleziona il sottoinsieme, e se la fonte è
`multi_istanza` sulla stessa chiave si carica l'istanza. `filtro`
seleziona una porzione **fissa** uguale per tutti — tipicamente l'annata.

**Le regole** instradano ogni individuo: il cognome segue il **padre**, il
nome dipende dai genitori. Prima regola che combacia.

**Il generatore** pesca con `blake2b(SEME|canale|id)`. Canali separati per
nome e cognome: correggendo domani il repertorio dei nomi, i cognomi non
si rimescolano.

Cambiare i cognomi italiani da Firenze a una fonte emiliana è **una riga**
in `repertori.yaml`.

### `traduci` — il valore dell'individuo non è quello della fonte

La popolazione dice «Romania», il dataset onomastico dice `RO`. Il campo
`traduci` mappa l'uno sull'altro attraverso un **file dichiarato**
(`fonti/paesi_onomastici.yaml`), non una costante nel codice — perché è
un raccordo con le sue ragioni, non un dettaglio di implementazione.

È il terzo raccordo del progetto dopo `istruzione_raccordo` e
`derivato_da`, e ha la stessa forma: una decisione che nessuna fonte
pubblica, scritta insieme al perché.

### Il ramo straniero

**`popular-names-by-country`**, CC0, con provenienza dichiarata da
Wikipedia. Ed è il primo caso in cui il registro valuta una fonte di
**terze parti** invece che istituzionale — e il risultato è che si è
potuta accettare *per metà*, sapendo esattamente cosa copre.

Tre cose che la valutazione ha stabilito.

**L'universo dichiarato dall'autore è il testing del software**: «I need
a names dataset for doing some software testing», con i criteri
dell'internazionalizzazione — avere esempi CJK e RTL, con romanizzazione.
Non è costruito per rappresentare una popolazione. Per il nostro uso va
bene lo stesso, perché serve un repertorio di **plausibilità** e non una
distribuzione, ma la differenza va dichiarata.

**Nomi e cognomi devono cadere insieme.** La fonte copre 106 paesi per i
nomi e 75 per i cognomi, e l'intersezione è 65. Un nome arabo con cognome
fiorentino — «Mohamed Innocenti» — è **peggio** di due nomi italiani,
perché segnala l'errore invece di nasconderlo. Il raccordo include quindi
solo i paesi coperti da entrambi.

**La copertura è 59,6%**, misurata sulle quote per paese di Parma e
**verificata a 59,2% su 400 individui estratti** — le due misure
coincidono entro il rumore di campionamento.

Il 40,8% ripiega su `cognome_italiano`, e il buco non è casuale: è il
mondo arabo e l'Africa subsahariana — Nigeria 6,7%, Tunisia 6,0%, Marocco
3,7%, Ghana 3,5%, Pakistan 3,0%, Costa d'Avorio 2,9%, Senegal 2,2%,
Camerun 2,2%. Sono paesi per cui **né Wikipedia né gli istituti
statistici nazionali** pubblicano liste onomastiche: la lacuna è della
letteratura aperta, non di questo dataset. Forebears.io li ha, ma non è
open data e i termini vietano l'estrazione sistematica.

La profondità varia di un ordine di grandezza: Filippine 50 cognomi,
Albania 46, Cina 40, ma Romania 12, Moldova 15, India 7, Bangladesh 6. E
la Romania è il 13,8% degli stranieri di Parma: con dodici cognomi, in un
campione da venti la collisione è circa il 10% — accettabile — ma in uno
da centoventi è quasi certa.

### `blake2b` resta

La domanda era se passare a `SHA-256` per la portabilità nel browser.
**Cade**: Animarium non mostra nomi, quindi il browser non deve
calcolarli. Il nome vive solo nel campione narrativo e nei persona-prompt,
entrambi generati da Python.

---

## 7. `gsp.istruzione` — i titoli di studio

### Lo stesso principio dei nomi, con un vincolo in più

Il titolo dettagliato non è un attributo della popolazione ma una
**derivazione**: si calcola quando serve, deterministicamente dall'`uid`,
e non finisce in nessun file.

Ma a differenza del nome ha un vincolo di **coerenza**: se `istruzione =
media`, il titolo deve essere di livello media. È garantito per
costruzione — si pesca dentro il repertorio della categoria — quindi non
esiste modo di produrre un incoerente.

### Il raccordo è una decisione, e sta in un file

`fonti/istruzione_raccordo.yaml` mappa i codici censuari sulle sei
categorie. **Nessuna fonte lo pubblica**: è un giudizio, e il file lo
dichiara insieme alle ragioni.

La decisione principale — dove sta la laurea magistrale — è verificata da
**due fonti indipendenti**. Nella popolazione sintetica `post_laurea` è
al 17,08% e `laurea_o_its` al 5,31%; al censimento 2011 in
Emilia-Romagna la magistrale conta 375.976 persone contro le 103.943 di
diploma universitario più triennale. Rapporti: **0,276 contro 0,311**,
con lo scarto nella direzione giusta perché nel 2024 la riforma del 1999
ha avuto tredici anni in più per produrre triennali. Non è un'ipotesi, è
una misura confermata da due lati.

La scelta più discutibile è dichiarata come tale: l'AFAM del vecchio
ordinamento in `post_laurea` è un'analogia, e vale lo 0,3% della
popolazione.

### `verifica()` — tre controlli, e il terzo è quello vero

Copertura, foglie per categoria, e **coerenza per ramo**: la somma delle
foglie deve ricostruire il totale di ramo. Sui dati veri nove rami su
nove tornano entro lo 0,01%.

Il confronto va fatto **per ramo, non per categoria**: una categoria
raccoglie foglie da rami diversi — `post_laurea` prende sia la magistrale
sia l'AFAM — e sommarle contro il totale di un ramo solo produceva un
falso allarme al primo giro.

### Cosa il collaudo ha stanato

Tre difetti, tutti trovati facendo girare il codice e non ragionando:

**`g2_inizia: ["6"]`** faceva cadere tutto il ramo AFAM nel vecchio
ordinamento. I tre gruppi sono `600`, `610`, `620` e cominciano tutti per
sei: il discriminante è la **seconda** cifra.

**Una radice senza figli è una foglia.** `10000` (licenza elementare)
punta a sé stessa, quindi compariva fra i «padri» e restava fuori dal
repertorio, lasciando la categoria vuota.

**L'albero non si deduce dal codice.** Sembrava di sì — gruppi di tre
cifre con gli zeri iniziali soppressi — ma la gerarchia **attraversa i
gruppi**: `002999` (alfabeta privo di titolo) ha primo gruppo 002 ed è
figlio di `001999` (nessun titolo), che ha 001. E normalizzare la
lunghezza li fonderebbe: `01999` e `001999` sono figlio e padre, non lo
stesso nodo.

### Il condizionamento per coorte ha due regimi

Sopra i 35 anni oggi si **trasla di tredici anni**: chi ha 35-49 anni nel
2024 ne aveva 22-36 nel 2011, e si ottiene la stessa generazione. Funziona
perché quelle persone avevano già finito di studiare.

Sotto, la traslazione **leggerebbe bambini**: con essa il bin 15-24
usciva con 53,2% di «nessun titolo» e 34,5% di «licenza elementare». Per
quei bin si usa la classe corrispondente non traslata, che riflette la
scolarizzazione del 2011 invece di quella della coorte.

Le due letture sono compatibili, ed è la verifica: 25-34 non traslato dà
46,2% diploma e 17,6% magistrale, 35-49 traslato dà 52,0% e 13,3%.

I 9-14enni di oggi sono nati **dopo** il censimento e non esistono nella
tavola. Non serve: il MaxEnt li vincola già a tre categorie.

### La resa, che è presentazione e non repertorio

Due aggiustamenti, entrambi di sola lettura — i pesi non cambiano.

**Le foglie residuali risalgono al padre.** «altre lauree del gruppo
economico-statistico» diventa «discipline economico-statistiche». Non è
una rifinitura: nel ramo della triennale le residuali sono 33 foglie su
290 ma **il 39% della massa**, quindi in una demo quattro schede su dieci
direbbero «altre lauree del gruppo…».

**Il livello viene anteposto**, perché nessuna delle 346 foglie terziarie
lo porta nel nome — sono solo discipline, «informatica», «fisica». Senza
prefisso una magistrale in fisica e una triennale in fisica sono
indistinguibili.

### I limiti, tutti dalla fonte

**Il post-laurea non è rilevato.** Nessuna voce di dottorato, master o
specializzazione fra le 458 modalità. La categoria `post_laurea` produce
quindi solo lauree magistrali: per una biografia è plausibile, ma va
detto.

**Il territorio si ferma alla regione.** Non è grave, perché il MaxEnt ha
già condizionato `istruzione` sul comune: manca la variazione del
**dettaglio** dentro la categoria, che varia molto meno della quota di
diplomati. È la stessa risoluzione degli attributi AVQ.

**I titoli post-2011 sono assenti** per costruzione: ITS Academy
riformati nel 2022-2023, nuove classi di laurea del 2024.

---

## 8. Privacy e disclosure

### L'argomento, in tre livelli

**Primo: non c'è nessun dato personale da proteggere.** La popolazione è
*simulata da aggregati pubblicati*, non anonimizzata da record
individuali. Sono due cose giuridicamente diverse: l'anonimizzazione deve
dimostrare di aver rotto un legame, la simulazione non ne ha mai avuto
uno.

**Secondo: l'unica cosa reale nel record è il vettore AVQ**, e viene da
una fonte già protetta da ISTAT. Il hot-deck aggiunge uno strato: ogni
vettore replicato ~40 volte, nessuna combinazione unica.

**Terzo: l'indirizzo non porta informazione.** L'assegnazione al civico è
arbitraria dentro la sezione, e la risoluzione dei dati si ferma alla
sezione.

I primi due reggono da soli.

### Cosa in un record è davvero reale

| componente | origine | quanto è reale |
|---|---|---|
| età, sesso, istruzione, condizione, cittadinanza | MaxEnt da marginali | nessun individuo dietro |
| zona, sezione | vincoli aggregati | nessuno |
| **civico** | estratto da ANNCSU | **l'indirizzo esiste** |
| **vettore AVQ** | copiato da un donatore | **risposte di una persona vera, perturbate** |
| nome | generato | plausibile, quindi collidente |

Il vettore AVQ è **la cosa più reale del record**, ed è quella a cui non
pensa nessuno.

### Tre prodotti, tre regimi

```
popolazione completa   →  data/, non lascia la macchina
bundle pubblico        →  senza nome, coordinata randomizzata in sezione
campione narrativo     →  completo, generato al momento, decine di individui
```

La differenza fra una scheda letta a schermo e un dataset scaricabile è
quella fra citare un caso e pubblicare un archivio. **Il bundle è
scaricabile per costruzione** — DuckDB-WASM lo prende via HTTP — quindi
il banner del pannello non viaggia con il file.

### `--pubblico` in `to_parquet` — da fare

Toglie `via` e `civico`, e sostituisce `lon`/`lat` con un punto casuale
dentro la sezione. **Non si perde niente**, perché l'assegnazione al
civico è già casuale dentro la sezione: la mappa resta visivamente
identica, la densità è la stessa, e il file diventa autoprotettivo.

Nello stesso passaggio si toglie `quartiere`, che è **uno-a-uno con
`zona`** (verificato: 4 e 4 a Modena, 18 e 18 a Bologna, coppie distinte
pari al numero di zone) e il cui nome arriva già dal manifest.

### La regola di disclosure in un punto solo

```python
gsp.individui.campione(comune, n=20,  dettaglio="narrativo")
gsp.individui.campione(comune, n=120, dettaglio="persona")
gsp.individui.tabella(comune,         dettaglio="pubblico")
```

Un SIVE-like avrà bisogno di caricare, filtrare, campionare e costruire
persona-prompt: esattamente questo. Se quella logica sta in
`animarium/build/`, il terzo consumatore la duplica.

---

## 9. Come si aggiunge una fonte

```bash
python -m gsp.fonti --aggiungi ~/scarichi/file.csv --id ente_variabile_anno
```

Stampa uno stub YAML con `DA_COMPILARE` sui campi che richiedono
giudizio: **universo**, **unità**, **usabile_per**, **non_usabile_per**.

**Scaricare sempre i metadati insieme ai dati.** Per Firenze l'XML DCAT ha
risolto la licenza in dieci secondi. Per Parma il codebook ha stabilito
che `ETA = -1` è sporco. Per Modena il campo `hash` di CKAN conteneva due
timestamp diversi.

**I codebook vanno registrati come fonti**: sono la fonte che dà
significato ai valori dell'altra.

**`non_usabile_per`** è il campo che nessuno mette ed è quello che serve.

---

## 10. Principi

**Il significato di una quantità appartiene a chi la produce.** La
struttura generica non lo indovina. Tre occorrenze in due giorni:
`modalita` sulla matrice di Reggio (26 nazionalità o 104 righe lunghe?),
`n_misurato` sui codebook (righe o campi?), la somma dei pesi sulle medie
nazionali (82 o 23?). Ogni volta la correzione è la stessa: la
diagnostica del normalizzatore vince.

**Un artefatto che contiene la propria data di generazione non è
verificabile.** L'hash cambia a ogni esecuzione anche quando i numeri
sono identici, quindi il registro non distingue «rigenerato uguale» da
«rigenerato diverso», e l'unico controllo che conta si spegne. Vale per
tutto: bundle, impronte, popolazioni. Stessa ragione per cui i nomi usano
un hash con seme fisso e `donor_id` è `"2024:12345"` invece dell'indice
del pool.

**Ogni metrica che scala col numero di celle va normalizzata contro la
sua ipotesi nulla.** Il pavimento di campionamento in `verifica_vincoli`,
`1/√n` sulle correlazioni, `n_eff` di Kish sui donatori, `residuo_quota`
sulle fonti locali.

**La gerarchia dichiarata dalla fonte batte quella dedotta dal codice.**
I codici del censimento sembravano gerarchici — gruppi di tre cifre con
gli zeri iniziali soppressi — e non lo erano: `002999` è figlio di
`001999` pur avendo un primo gruppo diverso, e normalizzare la lunghezza
avrebbe fuso padre e figlio. La colonna `padre` c'era, e risalirla è
l'unica lettura corretta. È lo stesso schema di `residuo_quota` e di
`donor_id`: la struttura generica indovina, la fonte smentisce.

**Mantenere due percorsi che devono produrre lo stesso output è un test
di regressione permanente.** `gibbs_pcd_solver_old.py` nel repo pubblico;
i due rami paralleli sul consolidamento di `gsp_common`.

**Una fonte senza `non_usabile_per` viene riusata a sproposito sei mesi
dopo**, quando si è dimenticato perché la si era scaricata.

---

## 11. Questioni aperte

### 11.1 Da fare, corte

- ~~`--pubblico` in `to_parquet`~~ — **fatto**, ed è il *default*:
  coordinate randomizzate dentro la sezione, via/civico/uid/quartiere
  fuori. `--completo` è l'eccezione esplicita
- ~~`uid` in `fit_cs`~~ — **fatto**, con rigenerazione completa degli
  undici comuni: l'identità sopravvive a `assign_avq` ed `enrich` riga per
  riga, verificata
- ~~`blake2b` → `SHA-256`~~ — **cade**: Animarium non mostra nomi, quindi
  il browser non deve calcolarli e la portabilità dell'hash non serve
- **`medie_nazionali.json` copiato da `build_bundle`** invece che
  generato in Animarium: GSP produce, Animarium consuma
- **la riga 170 del riferimento** dice ancora
  `animarium/build/medie_nazionali.py`

### 11.2 Etichette di blocco disallineate

| tavola | la tupla dice | il file prodotto è |
|---|---|---|
| `cens_istruzione_cittadinanza` | C3 | `c5_edu_citizenship.csv` |
| `cens_condprof_cittadinanza` | C4 | `c6_condprof_citizenship.csv` |
| `cens_stranieri_paesi` | C6 | `nationality_conditional.csv` |

C6 assegnato due volte. Nel registro `blocco` segue il nome del file.

### 11.3 Difetti delle fonti

- **`ETA = -1`** a Parma, un record
- **Ravenna 2024** da riscaricare
- **`Ncomp`** non usabile senza condizionare su `Tipores`

### 11.4 Fonti non registrate

- **`data/istat_catalog/`** — `catalog_dataflows.csv` (641 KB) da
  `catalog_dataflows.xml` (13,6 MB). È un **indice**, non un dato: dice
  cosa esiste, non cosa contiene. Serve un `elenco_csv` senza `peso`.
- **`data/istat_structures/`** (120 MB): DSD e codelist SDMX.
- ~~`data/geodata/`~~ — **registrata**, come due famiglie di zip.
- **Licenze dei sette portali comunali.**

### 11.5 Rifiniture

- `resolve_pop_file` con regole diverse fra script: `assign_avq` ed
  `enrich` preferiscono K10C, `to_parquet` lo esclude. Su Brescia chi
  rigenera a mano senza `--pop-file` produce un file che il viewer
  ignora.
- `_radice()` in `common.py`, quando servirà a un terzo modulo.
- ~~Il **ramo straniero** dei nomi~~ — **fatto** per il 59,2%. Resta il
  buco arabo e subsahariano, che nessuna fonte aperta copre: le strade
  sono una licenza di ricerca da Forebears, una lista curata da fonti
  sparse, o il fallback dichiarato che c'è già.
- **CLAIST non è ancora usato** da `gsp.istruzione`: serve per le
  denominazioni moderne (il censimento ha quelle del 2011) e per il
  vincolo temporale duro, che oggi emerge solo dalle frequenze.
- **I quindici gruppi disciplinari del MUR** sono in CLAIST e darebbero
  nomi più naturali dei «gruppi» del censimento.
- Il condizionamento dei nomi **per coorte**: ISTAT copre solo dal 1999;
  per il 1927–1998 la via pulita è chiedere a un ufficio statistica
  comunale una tavola sesso × classe quinquennale × nome × frequenza con
  soppressione sotto 5.

---

## 12. Trappole imparate

**`cat >>` non è idempotente**, ed è capitato **tre volte**. Un controllo
che stampa e basta non serve se il comando pericoloso è nella stessa riga
incollata. La forma giusta lega il controllo all'azione:

```bash
grep -q "id: X" fonti/registro.yaml \
  && echo "GIA' PRESENTE, non appendo" \
  || cat "$SCAR/schede.yaml" >> fonti/registro.yaml
```

**Le chiavi YAML duplicate spariscono in silenzio.** PyYAML tiene
l'**ultima**. È l'unico errore che nessun altro controllo può vedere,
perché arriva già filtrato dal parser.

**`sed -i 'Nd'` è cieco**: cancella per numero senza guardare il
contenuto, e il numero spesso viene da un messaggio d'errore invece che
dal file.

**Dopo ogni modifica a mano, stampare il risultato**, non solo validare:
`usabile_per: [a b]` senza virgola è YAML valido e produce **un solo
elemento**.

**I numeri di riga invecchiano**, e non vanno mai calcolati su una copia
per applicarli a un'altra.

**L'sha256 della stringa vuota è `e3b0c442…852b855`.**

**Un difetto localizzato non deve far perdere le informazioni buone.**

**Attenzione ai tipi interi in operazioni quadratiche.** `sum(w)²` su
int64 con somma 5,8e11 wrappa a negativo.

**`np.fill_diagonal(D.values, ...)` non funziona con pandas 3**: il
`.values` è una vista in sola lettura.

**`astype(str)` lascia i NaN come float**, e `"|".join` fallisce.

**Confrontare invocazioni diverse dello stesso script non misura nulla.**
Il bundle di Modena è passato da 5,12 a 3,68 MB, e ho cercato la causa in
`donor_id` prima di accorgermi che `build_bundle` passa
`--drop-avq-raw` e la mia invocazione no. Il segnale che avrei dovuto
cogliere: Reggio *saliva* invece di scendere.

**Il prompt dice `(base)` invece di `(ml)`** ed è la causa più frequente
di `ModuleNotFoundError`. `conda config --set auto_activate_base false`
più `conda activate ml` in `.bashrc`.

**I file da Windows arrivano `100755`.** Il browser rinomina gli omonimi.
L'estrazione appiattita di uno zip fa collidere i file omonimi *dentro*
lo zip. **`python-calamine` si importa come `python_calamine`.**

**Un file di configurazione consegnato intero porta lo stato di chi lo
scrive, non di chi lo riceve.** `repertori.yaml` copiato dal container ha
riportato `nome_italiano` a `DA_REGISTRARE`, perche' li' la fonte Modena
non c'era. I file di configurazione vanno consegnati come PATCH — «sostituisci
questo blocco» — non come file interi. Vale per `repertori.yaml`,
`registro.yaml` e qualunque cosa contenga stato locale.

**Il container ha Python 3.13, l'ambiente `ml` ha la 3.11.** Fino alla
3.11 un backslash non può stare dentro l'espressione di una f-string; dalla
3.12 sì (PEP 701). Il difetto esplode come `SyntaxError` all'import, quindi
almeno è rumoroso.

**Due encoding nello stesso zip.** In `DICA_TITSTUDIO` i codebook sono in
UTF-16 con BOM e il file dati in UTF-8 senza: chi legge il primo con
successo fallisce sul secondo. Cinque formati anomali su trentadue fonti
— ISO-8859-1 a Reggio e nel codebook di Parma, xlsx senza `sharedStrings`
a Forlì, XLS binario a Ravenna, WFS a Modena — non è sfortuna: ogni ente
esporta con lo strumento che ha.

**Un dataflow SDMX `ONLY_FILE` non è interrogabile.** `DimId` con zero
modalità e 6 KB di struttura sono il segnale: l'URL del file sta
nell'annotazione `ATTACHED_DATA_FILES`, ed è l'unico modo di trovarlo.
