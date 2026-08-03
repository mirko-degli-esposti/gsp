# Registro delle fonti, pacchetto `gsp`, questioni aperte — v2

Aggiornata il 2 agosto 2026. Sostituisce la v1: stessa struttura, ma il
registro è passato da 2 a 24 fonti e ha acquisito quattro meccanismi che
in v1 non esistevano.

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

Installato una volta con `pip install -e .` nell'ambiente `ml`.
Dipendenze da dichiarare in `pyproject.toml`: `pandas`, `numpy`,
`pyarrow`, `pyyaml`, `xlrd`, `openpyxl`, `python-calamine`.

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
  `enrich.py` importa il primo, `fetch_comune.py` il secondo. Vanno in
  `src/gsp/`. **Non è la stessa migrazione di `gsp_common`**:
  `opendata_paese.py` è ibrido — CLI (`--check`, `--dump`), sei funzioni
  lettrici, e la logica IPF — quindi va prima separato, e solo la parte
  lettrice va nel pacchetto. `istat_sdmx.py` va spostato prima o insieme,
  perché il primo lo importa.
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
`{istanza}` e `--scansiona` le rileva da sole. Undici schede scritte a
mano invece di centotrentadue.

### `parametri_da`: non riscrivere ciò che esiste già

`common.COMUNI[<cod>]["opendata_paese"]` contiene per ogni comune il
loader, il livello geografico, l'encoding, le mappe di riconciliazione
dei nomi (41→21 unità per Forlì, 22 alias di paese per Ravenna). Il
registro **non lo riscrive: lo referenzia**.

```yaml
parametri_da: common.COMUNI.017029.opendata_paese
```

`--verifica` controlla che il riferimento regga: se il blocco sparisce,
la scheda diventa `DIVERGE`. Riscriverlo darebbe due dichiarazioni della
stessa cosa, destinate a divergere in silenzio — il contrario esatto del
principio dei due rami paralleli.

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

Da Python: `F.carica(id[, istanza])`, `F.info(id)`, `F.parametri(id)`,
`F.istanze(id)`, `F.elenco(usabile_per=...)`.

### Gli esiti di `--verifica`

| esito | significato | esce con |
|---|---|---|
| `ok` | tutto coincide | 0 |
| `IMPRONTA` | grezzo assente ma impronta presente: stato **normale** di un clone senza i file pesanti | 0 |
| `NUOVE` | istanze non ancora in impronta: un comune aggiunto è informazione | 0 |
| `DIVERGE` | hash cambiato, conteggi diversi, campi mancanti, file vuoto, riferimento rotto | 1 |
| `ROTTA` | dichiarata in git ma assente; né grezzo né impronta | 1 |

Uno stato che fallisce sempre è uno stato che si smette di guardare: per
questo `IMPRONTA` e `NUOVE` non sono rossi.

### `--copertura`: la direzione opposta

Tutti gli altri controlli chiedono «la scheda punta a qualcosa che
esiste?». Questo chiede **«esiste una fonte nella pipeline che non è
passata dal registro?»** — elenca i comuni con un blocco
`opendata_paese` in `common.py` e senza scheda. È la stessa asimmetria di
`n_dichiarato` contro `n_misurato`, applicata alla copertura invece che
ai conteggi. Oggi risponde *«ogni comune ha la sua scheda»*.

### I dodici normalizzatori

Funzioni pure `f(path, **opzioni) -> (DataFrame, diagnostica)`. Il
normalizzatore **non corregge mai il grezzo sul disco**: dichiara.

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

CC-BY-4.0, versionate in git, metadato DCAT d'origine, `notPlanned`.

`firenze_cognomi_2013` è la sorgente d'uso: 375.371 residenti anagrafici,
66.353 cognomi distinti, 51% hapax. Chao1 stima ~125.000 cognomi nella
popolazione generatrice: Firenze ne vede metà.

`firenze_cognomi_2012` è solo controllo di stabilità. Correlazione 0,9985,
variazione mediana assoluta 0: **stessa popolazione a un anno di
distanza, non un campione indipendente**. L'unione guadagna 6.103 tipi di
cui 5.523 hapax — l'1,6% della massa: non vale il merge.

Il limite non è la taglia ma la regione. `TOLOMELLI`, il cognome più
frequente di Argelato, non compare in 375.371 fiorentini; `INNOCENTI` è
terzo ed è l'artefatto dell'Ospedale degli Innocenti.

### ISTAT SDMX — 11 tavole × 12 comuni

CC-BY-4.0, `archiviazione: locale`. Limite del servizio: **4 query/minuto**.

| | universo | ruolo |
|---|---|---|
| `istat_anag_sesso_eta_statociv` | anagrafe, 1 gennaio anno **N** | C1, unico **hard** |
| altre dieci | censimento permanente, 31 dicembre anno **N−1** | C2–C10, **soft** |

Le serie coprono 2019–2025 e 2018–2024: sette anni ciascuna, sfalsate di
uno, perché sono gli **stessi sette istanti**. Confermato dal codice:
`build_constraints.py` richiede l'anagrafica all'anno N e le censuarie
all'anno N−1, e `preflight()` verifica la copertura prima di costruire.

`cens_stranieri_paesi` ha cinque consumatori ed è l'unica fonte dei ~150
paesi, pubblicata **solo a livello comunale**: è la ragione
dell'architettura a quattro tier. `cens_migr_backg` genera il blocco GC
(sei zeri strutturali): origine del bug di indipendenza spuria e della
riducibilità di Gibbs a λ*. `cens_posizione_prof` e `cens_settore_prof`
hanno `unita: individuo occupato` ed entrano come C9/C10 **soft e
condizionali**, verificato in `build_constraints.py`.

**`cens_posizione_famiglia` è scaricata e mai letta.** `usabile_per: []`.

`obs_somma` nell'impronta è ~2× (anagrafica) e ~8× (censimento) la
popolazione vera, per via dei codici aggregati: è una **firma per
riconoscere il file, non un conteggio**. Il numero di righe è identico
per Bologna e Castenaso, quindi non discrimina.

### Sezioni di censimento (2)

CC-BY-4.0 per licenza generale ISTAT — la pagina non ne dichiara una
propria, e il registro lo segna in `nota_licenza`: è un'inferenza
corretta ma di natura diversa da un `<dc:license>` letto.

**135.725 sezioni**, 18,35 milioni di residenti. Geometria del censimento
**2021** (`SEZ21_ID`), dati **2023**. `COM_ASC1/2/3` sono le sub-aree
amministrative: è la fonte della gerarchia zona/quartiere.

**10.872 sezioni senza residenti** (4,5%–8,8%): `build_sezioni.py` le
riconosce già come speciali vuote, e verifica `P1 = P2 + P3`.

`istat_sezioni_2023_tracciato`: codebook delle 138 colonne, `unita:
variabile`.

### AVQ (2)

**Licenza `DA_VERIFICARE` di proposito**: i microdati per la ricerca
(mIcro.STAT) non ricadono automaticamente nella CC-BY generale ISTAT.

`unita: individuo campionario`. `n_misurato` registra i **record**,
perché è ciò che la pipeline consuma; `somma_pesi` e `n_eff_kish` stanno
nell'impronta e non vanno confusi con n.

Uso in `assign_avq.py`: annate impilate con `COEFIN` normalizzato **entro
anno** (ogni annata pesa 1/n a prescindere dalla numerosità); cella
`(REGMf, SESSO, ETAMi→macroetà, ISTRMi→istr4)`; donatore estratto con
probabilità proporzionale a w; si copia il **vettore completo** dei
target — è questo che preserva le correlazioni.

**Il pool non ha dimensione fissa: dipende dai target richiesti.**
Un'annata che non ha una variabile fra i target viene scartata per
intero. Con `CRONI` fra i target il 2022 esce e il pool resta a due
annate.

### Le sei fonti locali (7 schede)

Margine B dell'IPF in `opendata_paese.py`, complementare e non
alternativo al censimento (margine A). Tutte anagrafiche, di data diversa
dal censimento, tutte con `parametri_da`. Licenze tutte `DA_VERIFICARE`:
sette portali comunali, nessuna regola generale come quella ISTAT.

| comune | tier | unità | paesi | residuo | sesso | età |
|---|---|---|---|---|---|---|
| Parma | 3 | **1.320 sezioni** | 151 | — | sì | sì |
| Bologna | 2 | 19 zone | 155 | **0%** | sì | no |
| Forlì | 1 | 41 sub-quartieri | 42 | **16,5%** | sì | no |
| Brescia | 1 | 33 quartieri | 8–33 per file | variabile | no | no |
| Ravenna | 1 | 10 aree | ~40 | — | sì | no |
| Reggio E. | 1 | 4 circoscrizioni | 25 | **6,1%** | no | no |

**Brescia** — 33 CSV, uno per quartiere, `Cittadinanze, Num`. Include
`ITALIA`: i totali sono popolazione **completa**, e il filtro è a valle
(`opendata_paese.py:97`). Le modalità vanno da 8 (Caionvico) a 33 (Centro
storico nord): il gruppo residuale è il complemento dei paesi nominati
*in quel quartiere*, quindi cambia da file a file.

**Reggio Emilia** — matrice larga, ISO-8859-1, **2013**. L'uso è
giustificato da una verifica datata 1/8/2026: ranghi delle quote UE per
zona 4-2-1-3 nel 2013 contro 4-1-2-3 nel 2023, unico scambio fra zone che
nel 2023 distano 0,003; quote cresciute uniformemente di 2-4 punti. **È
questa verifica, non la data del file, a rendere la fonte usabile.**

**Ravenna** — XLS binario, foglio formattato per la stampa (creato 2003,
stampato 30/1/2024), doppia intestazione con celle unite. Si usano M e F
e si scarta T. Il file 2024 era a 0 byte: rimosso.

**Forlì** — xlsx **senza `sharedStrings.xml`**: openpyxl solleva
`KeyError`, serve `python-calamine`. Formato lungo, il più semplice.
41 unità mappate + `in corso di definizione` (9 persone) esclusa;
verificato che mappa e file coincidano esattamente. La fonte totalizza
15.021 contro 15.298 del censimento — **1,8% di scarto sui livelli**, che
l'IPF normalizza. Distanza media dalla composizione comunale **0,170**
(0 = nessuna informazione geografica), IPF convergente in 9 iterazioni.

**Bologna** — Parquet, serie storica **1986–2024**, 39 annate in un solo
file: `anno` è una colonna. La pipeline usa l'ultima. Due colonne per la
cittadinanza: `cittadinanza` è l'area (11 modalità), `stato_cittadinanza`
il paese (180 nella serie, 155 nel 2024). `Senza fissa dimora` non è una
zona: 324 persone escluse.

**Parma** — microdati individuali, 202.111 residenti, 36.327 stranieri
(18%), 1.320 sezioni, 13 quartieri. L'unica a microdato e l'unica con la
sezione. Porta `Ncomp` e `Relpar`, cioè **struttura familiare**: non
servono all'IPF ma sono il materiale già disponibile per quando le
famiglie verranno modellate, insieme a `cens_posizione_famiglia`.
Il codebook è a **due livelli** (campo → codice → etichetta), 225 codici
per `Cittad` contro 151 presenti nei dati.

---

## 4. Cosa il registro ha già trovato

Non era l'obiettivo, ma è successo:

- **Due file scaricati vuoti** (0 byte) mai notati: Piacenza e Ravenna
  2024. Da qui il controllo `SHA_VUOTO`.
- **`unita` sparita** da `istat_cens_settore_prof` in un'edit manuale:
  YAML valido, pipeline invariata — l'ha preso il controllo sui campi
  obbligatori.
- **Un record con `ETA = -1`** su 202.111 a Parma, trovato dal controllo
  di plausibilità di `microdati_csv`. Il codebook, registrato come fonte
  a sé, ha stabilito che `ETA` è documentata come «numerico» senza valori
  speciali — quindi è **dato sporco, non convenzione**. Nessuna delle due
  cose da sola bastava.
- **`Ncomp` fino a 319**: sono convivenze anagrafiche (`Tipores = 2`), non
  famiglie. La variabile mescola due universi.
- **`cens_posizione_famiglia` mai usata.**
- **Tre etichette di blocco disallineate** in `build_constraints.py`.
- **Il commit `f7a1e7a`** ha cambiato il default di `--targets-opt` da
  vuoto a 17 variabili: i log di luglio non sono confrontabili con le
  corse attuali.

### `residuo_quota` come criterio comparabile

L'ipotesi «più fine la geografia, più informazione nel residuo» sembrava
reggere passando da Reggio (4 unità, 6,1%) a Forlì (41 unità, 16,5%). **È
falsa**: Bologna ha 19 zone e **zero** residuo. La relazione non è
strutturale ma dipende da come il comune ha costruito la pubblicazione —
Forlì pubblica una graduatoria troncata, Bologna l'estrazione completa.

E a Bologna nel 2024 la fonte nomina **155 paesi contro i 119** che l'IPF
produce dal censimento: qui il margine B è più ricco del margine A, il
contrario del caso generale descritto nella docstring di
`opendata_paese.py`.

---

## 5. Questioni aperte

### 5.1 Donatori AVQ — la più importante

**Stato.** Il numero di donatori **effettivamente estratti** non è mai
stato misurato. `assign_avq.py` **non lo stampa** (verificato 2/8/2026:
la riga del documento di riferimento che diceva il contrario era errata).
Il log stampa la dimensione del **pool disponibile** — `8.111 donatori con
cella completa su 8.149` per la Lombardia — che è un'altra quantità.

**Perché conta, tre ragioni.**

1. **Separare collisioni da saturazione incompleta.** Con 21 variabili le
   collisioni erano 418 (9%) nel pool emiliano-romagnolo; con 23 saranno
   meno, quindi va **rimisurato, non riportato**.

2. **La maschera a 100 donatori è calcolata sulla quantità sbagliata.**
   La validazione 2 costruisce `n_don = ok.T @ ok` sui donatori
   **disponibili** e maschera le correlazioni sotto i 100. Una coppia con
   400 disponibili e 60 estratti oggi passa il filtro e non dovrebbe.

3. **La numerosità efficace.** `n_eff` di Kish è 1.520 per Modena e 1.599
   per Bologna dopo il condizionamento. `avq_microdati` ora calcola il
   Kish nazionale per annata: i due numeri affiancati dicono quanto costa
   il condizionamento.

**Cosa serve.** Tutte e tre discendono dall'avere `idx_don` nel blocco di
validazione:

```python
print(f"[avq] donatori usati: {len(np.unique(idx_don)):,} su {len(pool):,} "
      f"({len(np.unique(idx_don))/len(pool):.1%} del pool) | "
      f"riuso medio {len(idx_don)/len(np.unique(idx_don)):.1f}")
```

Meglio ancora: scrivere `idx_don` come colonna nel CSV. Allora «donatori
usati» diventa una query, e la differenza con i `donor_id` distinti **è**
il conteggio delle collisioni, misurato invece che stimato.

Il ciclo di rigenerazione è già previsto per le 26 esclusioni α=0.

**Da chiarire.** Equipesare le annate implica un pool che rappresenta una
media del triennio e non la popolazione a una data. Per donare attributi
è *probabilmente* irrilevante, ma non è stato verificato.

### 5.2 Etichette di blocco disallineate

| tavola | la tupla dice | il file prodotto è |
|---|---|---|
| `cens_istruzione_cittadinanza` | C3 | `c5_edu_citizenship.csv` |
| `cens_condprof_cittadinanza` | C4 | `c6_condprof_citizenship.csv` |
| `cens_stranieri_paesi` | C6 | `nationality_conditional.csv` |

C6 risulta assegnato due volte. Ipotesi: quando `cens_stranieri_paesi`
uscì dal MaxEnt, C6 si liberò e fu riassegnato senza aggiornare le
stringhe. Non cambia i risultati, ma se `preflight()` le stampa un
messaggio annuncia il blocco sbagliato. Nel registro il campo `blocco`
segue **il nome del file**.

### 5.3 Difetti delle fonti da chiarire

- **`ETA = -1`** a Parma, un record: dato sporco confermato. Se finisse
  in un vincolo o in un pool di donatori produrrebbe un'età negativa. Per
  `opendata_paese` il rischio è nullo (è italiano, viene filtrato).
- **Ravenna 2024** da riscaricare.
- **`Ncomp`** non usabile per la dimensione familiare senza condizionare
  su `Tipores`.

### 5.4 Fonti non ancora registrate

- **`data/istat_structures/`** (120 MB): DSD e codelist SDMX. Non
  osservazioni ma schemi, e sono ciò che permette di costruire le query
  senza interrogare l'API — non banale con 4 query/minuto.
- **`data/geodata/`** (1,7 GB): mai guardato.
- **Licenze dei sette portali comunali**: tutte `DA_VERIFICARE`. Innocue
  finché `archiviazione: locale`, ma vanno chiarite.

---

## 6. Come si aggiunge una fonte

```bash
python -m gsp.fonti --aggiungi ~/scarichi/file.csv --id ente_variabile_anno
```

Copia il grezzo, calcola l'hash, sceglie il livello di archiviazione dalla
dimensione, e stampa uno stub YAML con `DA_COMPILARE` sui campi che
richiedono giudizio: **universo**, **unità**, **usabile_per**,
**non_usabile_per**. Non li indovina di proposito.

**Scaricare sempre i metadati insieme ai dati.** Per Firenze l'XML DCAT
ha risolto la licenza in dieci secondi, dato l'URL vero, il `byteSize` che
conferma l'sha256, e `accrualPeriodicity: notPlanned`. Per Parma il
codebook ha stabilito che `ETA = -1` è sporco e non convenzionale.

**I codebook vanno registrati come fonti**, non lasciati in una cartella:
non sono documentazione accessoria, sono **la fonte che dà significato ai
valori dell'altra**.

**Il campo `non_usabile_per`** è quello che nessuno mette ed è quello che
serve: una fonte che non dichiara i propri limiti d'uso viene riusata a
sproposito sei mesi dopo.

---

## 7. Trappole imparate

**`cat >>` non è idempotente**, ed è capitato **tre volte**. Un controllo
che stampa e basta non serve se il comando pericoloso è nella stessa riga
incollata. La forma giusta lega il controllo all'azione:

```bash
grep -q "id: X" fonti/registro.yaml \
  && echo "GIA' PRESENTE, non appendo" \
  || cat "$SCAR/schede.yaml" >> fonti/registro.yaml
```

**Le chiavi YAML duplicate spariscono in silenzio.** PyYAML tiene
l'**ultima**: sostituire un campo scrivendo la riga nuova sopra quella
vecchia produce un registro che dice una cosa diversa da quella che si
legge. È l'unico errore che nessun altro controllo può vedere, perché
arriva già filtrato dal parser. Ora `_leggi_registro` usa un loader che
li rifiuta, con messaggio su una riga.

**Dopo ogni modifica a mano, stampare il risultato**, non solo validare:
`usabile_per: [a b]` senza virgola è YAML valido e produce **un solo
elemento** con lo spazio dentro. E `[tutto: il file e' vuoto]` è una
mappa, non una stringa.

**I numeri di riga invecchiano.** Un `head -N` calcolato su una copia e
applicato a un'altra taglia nel posto sbagliato. Ancorarsi a un pattern
(`grep -n "^  - id: X"`), non a un numero.

**L'sha256 della stringa vuota è `e3b0c442…852b855`.** Impararlo a
riconoscere: un file da 0 byte in mezzo a gigabyte non lo nota nessuno.

**Un difetto localizzato non deve far perdere le informazioni buone.**
`_impronta_multi` si fermava alla prima istanza illeggibile, perdendo
l'impronta delle altre trentadue. Ora ogni istanza è isolata e l'errore
finisce nell'impronta.

**I file da Windows arrivano `100755`.** `chmod 644` su quello che non è
uno script.

**Il browser rinomina i file omonimi** e l'estrazione appiattita di uno
zip fa collidere i file omonimi *dentro* lo zip. Estrarre sempre in una
sottocartella conservando le cartelle; `smista.sh` riconosce i file dal
contenuto.

**`python-calamine` si importa come `python_calamine`.**
