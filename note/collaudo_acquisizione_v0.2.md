# Collaudo degli script — acquisizione e vincoli, su macchina vergine

**v0.2 — 24 agosto 2026.** Documento di collaudo: per ogni script,
descrizione verificata sul sorgente (le docstring possono essere
datate: le divergenze si annotano), opzioni reali, ed esecuzione su due
comuni nuovi. Macchina: MacBook Pro Intel (x86_64), macOS, conda `gsp`
Python 3.11, clone fresco senza `data/` — il lettore del README. La
replica su WSL popola poi il `data/` ufficiale.

**Comuni di prova:** Mantova (tier 0 puro, il ramo "any new
municipality") e Milano (articolazione da decidere: 9 municipi per il
collaudo; il fit sugli 88 NIL — 14,2 M stati, il caso intermedio fra
Brescia K9C e il limite di mixing — è annotato come esperimento
successivo, non parte del collaudo).

## Findings (aggiornato man mano)

| # | dove | cosa | esito |
|---|---|---|---|
| 1 | `pip install -e .` → primi import | `requests` e `lxml` mancano dalle dipendenze del `pyproject.toml` (lista chiusa con un probe su tutto il pacchetto). Mai emerso su WSL (ambiente preesistente). | **Risolto**: aggiunti al `pyproject`, commit dal Mac. Aperto: dichiarare `numba`/`duckdb` come extra (`fit`, viewer) |
| 2 | `istat_catalog.py` | `OUT_DIR` cablato `~/progetti/gsp/...`: non rispetta `GSP_ROOT` — il pattern bonificato in Animarium sopravviveva qui. | **Risolto**: `from gsp.common import GSP`, commit dal Mac |
| 3 | `build_sezioni.py`, messaggio finale | Per un comune K6C legittimo (ASC tutti a zero, `livello: None`) il messaggio «scegliere un livello e aggiungerlo prima di procedere» è fuorviante: a valle si procede con la zona degenere (Ferrara docet). | Da ritoccare: se ASC vuoti e `livello=None` → «K6C confermato, procedere» |
| 4 | `cs_build.py` / `fit_cs.py` → `import_constraint_set()` | **Dipendenza non dichiarata dal repo del solver**: glob su directory sorella (`~/progetti/maxent-popsynth-pcd`, `/content/` per Colab), fuori dal tag di gsp. Il Mac vergine si ferma con `ImportError`; il version binding del report ha un buco (un file fuori dal tag può cambiare senza rompere git). | v1.0: dichiarare nel README («per il fit serve il clone del solver accanto a gsp») + **riga nella tabella di binding col commit pinnato** + frase di III.1 aggiornata. v1.1: pacchettizzare il solver (`pip install git+…@tag`) |
| 5 | registro, `usato_da` | La sed dei 44 `usato_da` (`build_constraints.py → cs_build.py`) ha cancellato un'informazione vera: `build_constraints.py` è **vivo** — è il preparatore della staffetta a due stadi (vedi scheda). | Da ripristinare come co-lettore: `usato_da: [build_constraints.py, cs_build.py]` sulle tavole SDMX |

---

## scripts/acquisizione/

Tre script: `fetch_comune.py`, `istat_catalog.py`,
`scarica_cognomi_wiki.py`.

### fetch_comune.py

**Cosa fa** (dal sorgente, v2): scarica e profila le tavole ISTAT SDMX
per un comune. Contiene la "rosa dei fondamentali" `CORE` — la mappa
nome-tavola → dataflow SDMX + vincoli espliciti per dimensione
(`spec`), con la dimensione territorio individuata e riempita
automaticamente. Si appoggia a `gsp.istat.sdmx` dal pacchetto
installato.

**Nota di datazione**: la docstring si intitola `fetch_comune_v2.py` ma
il file è `fetch_comune.py` — refuso storico, innocuo. ‹Altre
divergenze docstring/comportamento: da annotare dopo il primo run.›

**Modalità d'uso** (docstring, da verificare con `--help`):

| invocazione | effetto |
|---|---|
| `fetch_comune.py 037006 --explore` | ‹da verificare: esplora i dataflow?› |
| `fetch_comune.py 037006` | scarica la rosa CORE per il comune |
| `… --only cens_istruzione_eta` | una sola tavola della rosa |
| `… --profile cens_condprof_eta [--max-values 40]` | scarica una tavola e ne profila le dimensioni (quali variano, codici presenti con etichette); salva `<tavola>_profile.csv` in `data/comuni/<codice>/` |

**Opzioni reali** (`--help`, verificate): `comune` posizionale a sei
cifre; `--explore` (DSD e codelist, **senza scaricare osservazioni**);
`--only {11 tavole della rosa}`; `--profile TAVOLA`;
`--max-values N` (default 30). Coerente con la docstring.

**Test 1 — Mantova 020030, `--explore --only anag_sesso_eta_statociv`.**
Esito: ok. La struttura del dataflow viene scaricata e cachata (9,9 MB);
lo script *valida* il codice comune contro la codelist territorio e
stampa il nome risolto («REF_AREA = 020030 (Mantova)»). L'explore
mostra il perché della `spec`: DATA_TYPE ha 471 codici (la spec ne
fissa uno, JAN), MARITAL_STATUS 50 (la spec ne elenca sette).

**Test 2 — Mantova, `--profile anag_sesso_eta_statociv`.** Esito: ok.
8.568 righe, sette annate 2019–2025 (la selezione dell'anno avviene a
valle); `data/comuni/020030/` **creata da zero senza errori** — il
clone fresco non deve preparare nulla, punto a favore del README.
Osservazioni a registro:

- *Stato civile, mappa confermata sui codici effettivi*: 1
  nubile/celibe; 2 coniugata/o; 3 divorziata/o; 4 vedova/o; 15 unito/a
  civilmente; **16 già in unione civile per decesso del partner; 17 per
  scioglimento**. L'accorpamento del normalizzatore è quindi 2+15 →
  `coniugato_unito`, 3+**17** → `divorziato_sciolto`, 4+**16** →
  `vedovo` (16 e 17 invertiti rispetto alla congettura iniziale: il 16
  è l'analogo della vedovanza). Ordini di grandezza coerenti: su sette
  annate sommate, 658 uniti contro 291 mila coniugati.
- *La tavola codifica le età legali nella sua stessa sparsità*: per
  Y0–Y15 esistono solo righe con stato 1 (14 righe = 2 sessi × 7
  anni); per Y16–Y17 compaiono gli stati 1–4 (56 = 2×7×4: il
  matrimonio con autorizzazione del tribunale esiste da 16 anni); da
  Y18 tutti e sette (98 = 2×7×7: l'unione civile solo da maggiorenni).
  Doppio valore per il progetto: (a) è il tema «assente vs zero» visto
  dal vivo — le celle impossibili *non ci sono*, non valgono zero; (b)
  risponde alla nota di §I.5 del report: il quindicenne coniugato
  osservato nell'anello 4 è impossibile anche per la fonte (il
  coniugato parte da Y16), quindi va trattato come artefatto da
  correggere, non come rarità legale.
- La somma per periodo (~97–99 mila) è ~2× la popolazione di Mantova
  (~48–49 mila): la wildcard su AGE include il codice TOTAL — la firma
  degli aggregati inclusi, da riconoscere e non sommare (II.3).

**Rate limiting**: non nello script ma nel modulo, che è il posto
giusto — `gsp.istat.sdmx` impone `MIN_INTERVAL = 13` s fra *ogni*
richiesta HTTP (throttle globale, ~4,6 query/min contro il limite ~5)
e si ferma con messaggio esplicito su HTTP 429/403/503 invece di
ritentare. Ogni script che passa dal modulo è protetto senza saperlo.

**Test 3 — Mantova, fetch della rosa completa.** Esito: 10 tavole su
11 al primo giro; `cens_sesso_eta_cittadinanza` fallita con
`IncompleteRead` (troncamento di rete transitorio, non rate limit — il
server ha chiuso a metà risposta). **Situazione tipica, e il
comportamento è quello giusto**: l'errore resta confinato alla tavola
(lo script prosegue con le successive), il riepilogo finale la marca
`ERR 0 righe`, e il recupero è `--only` sulla sola tavola mancante —
riuscito al primo colpo (3.623 righe). Stesso principio di
`build_bundle`: mai fermarsi al primo errore, mai nascondere l'errore
nel riepilogo. Mantova: **11/11 a terra**.

Annotazioni dal riepilogo, utili per `vincoli/`:
- le strutture dei dataflow pesano ~10 MB l'una (cache locale ora
  ~100 MB sul Mac — la «SDMX structure cache» di §II.2, nata qui);
- i millesimi variano per tavola come atteso: censuarie 2018–2024,
  `cens_migr_backg` solo 2021–2023, `posizione_prof` e `settore_prof`
  solo 2021, `posizione_famiglia` 2021 e 2024;
  `cens_condprof_cittadinanza` salta il 2020 — da tenere presente
  quando `cs_build` sceglie l'anno;
- Mantova è piccola: le censuarie stanno in centinaia di righe, i
  tempi sono dominati dal throttle (≈13 s × ~21 richieste ≈ 5 min).

**Test 4 — Milano 015146, fetch della rosa completa.** Esito: 11/11 al
primo giro, nessun errore. Osservazione strutturale: le righe misurano
la *struttura*, non la taglia — Milano (1,4 M abitanti) ha le stesse
819 righe di Mantova su `istruzione_eta`, gli stessi 18 su
`posizione_famiglia`, le stesse 8.568 sull'anagrafica: le tavole
censuarie comunali hanno griglia fissa, cambia solo `OBS_VALUE`.
Crescono solo le tavole il cui supporto dipende dalla città:
`stranieri_paesi` 2.904 righe contro 1.922 (più paesi presenti) e
`sesso_eta_cittadinanza` di poco. Conseguenza per `vincoli/`: costo e
forma dell'acquisizione sono indipendenti dal comune; è l'open data
sub-comunale a distinguere una metropoli da un capoluogo di provincia.

> **Box — le tre porte dei dati, e perché Milano non pesa più di
> Mantova (qui).** Un equivoco naturale a questo punto del collaudo:
> «i dati sono sulle sezioni, Milano dovrebbe essere enorme». No: ogni
> comune riceve dati da **tre porte a tre granularità diverse**, e
> `fetch_comune` è solo la prima.
>
> 1. **SDMX → comune intero.** Le tavole appena scaricate hanno
>    `REF_AREA = <comune>`: un solo territorio (si vede nella chiave
>    della query: `key=.015146.......`). Le righe sono la griglia
>    annate × sesso × classi, identica per ogni comune: Milano e
>    Mantova hanno le stesse 819 righe su `istruzione_eta`, cambia
>    solo `OBS_VALUE` — e un numero grande occupa lo stesso posto di
>    uno piccolo. Il tempo di download è dominato dal throttle
>    (13 s/richiesta), non dai byte.
> 2. **Basi Territoriali → sezioni.** I conteggi per sezione di
>    censimento (`istat_sezioni_2023`) non passano da SDMX: sono file
>    **regionali** (un workbook per regione, una riga per sezione, 138
>    colonne), scaricati una volta per regione. Qui Milano pesa
>    (~6.000 sezioni contro ~500 di Mantova), ma dentro il file
>    `Lombardia` che le contiene entrambe — e che sulla WSL è già a
>    terra da Brescia; sul Mac, senza `data/`, andrà riacquisito o
>    replicato da lì.
> 3. **Open data comunali → l'articolazione intermedia** (zone, NIL,
>    municipi, quartieri): esiste solo dove il comune la pubblica, ed
>    è l'unica porta che distingue davvero una metropoli da un
>    capoluogo — per costo di ricerca, non di download.
>
> Tre porte, tre granularità; il tier del paese (§I.3 del report) è la
> traduzione in codice della terza.

### istat_catalog.py

**Cosa fa**: scarica il catalogo dei ~4.900 dataflow ISTAT (una
richiesta, 13 MB di XML) e lo trasforma in CSV; da lì in poi ogni
ricerca è un grep locale, zero rate limit. È lo strumento con cui la
rosa di `fetch_comune` è stata costruita; per aggiungere un *comune*
non serve, per aggiungere una *tavola* è il punto di partenza.

**Interfaccia**: niente argparse — argomento posizionale = pattern di
ricerca; `--refresh` forza il ri-download; la docstring è
l'interfaccia. La docstring cita ancora «Ambiente: WSL2 / conda env
ml»: datata, gira ovunque (finding cosmetico).

**Test — Mac, prima esecuzione.** Esito: ok. 4.896 dataflow scaricati
in `data/istat_catalog/`; grep «unioni civili» → 11 risultati, con la
famiglia `DCIS_UNIONICIT` e la `_1` («per sesso e tipologia di
coppia») che è la fonte già in registro per l'anello 4 — controllo
incrociato gratuito, passato. Grep «NIL» → 1 risultato, ed è
«occupazione femmi**NIL**e»: il match è substring puro, chi cerca
sigle corte deve saperlo (annotato, non da fixare).

**Risposta strutturale dal test**: in SDMX **non esiste un livello
NIL** (né alcun sub-comunale): ISTAT si ferma al comune.

> **Rettifica (24/8, non silenziosa).** La conclusione tratta qui il
> 23/8 — «i NIL vivranno solo di open data comunali» — era **sbagliata
> a metà**: `build_sezioni` su Milano ha mostrato che le **Basi
> Territoriali codificano entrambe le articolazioni** (COM_ASC1 = 9
> municipi, COM_ASC2 = 88 NIL, tutte le sezioni). La frase corretta:
> non esiste un livello NIL nelle *tavole demografiche SDMX*; la
> *geografia* NIL è già nel file regionale. L'open data comunale resta
> necessario solo per attributi sub-comunali oltre i conteggi di
> sezione (es. paese di cittadinanza per zona).

**Finding 2** (vedi tabella): `OUT_DIR` cablato — risolto con
`gsp.common.GSP`, commit dal Mac.

### scarica_cognomi_wiki.py

**Cosa fa**: scarica i repertori onomastici dalle categorie MediaWiki
via API (non scraping): JSON paginato, `cmnamespace=0` per escludere
pagine di servizio; URL e data finiscono nel file — «la provenienza
risulta riproducibile, mentre un copia-incolla darebbe *l'ho preso da
un sito*, che è precisamente ciò che il registro rifiuta» (la
docstring merita la citazione). I titoli delle voci *sono* i cognomi.

**Interfaccia** (argparse, verificata): posizionali = codici repertorio
(chiavi di `fonti/paesi_onomastici.yaml`, non ISO); `--elenco`;
`--tutti`; `--out`.

**Test**: `--elenco` per vedere i repertori disponibili, poi un
download di verifica idempotenza (i due repertori sono già in
`fonti/grezzi/` dal clone: il riscarico deve dare le stesse impronte a
meno di modifiche wiki — che è il punto interessante: la *fonte è
viva*, e l'impronta certifica quale versione abbiamo usato).
‹esecuzione: opzionale per il collaudo, i file sono già a terra›


---

## scripts/vincoli/

Cinque script: `build_sezioni.py`, `build_zona_tables.py`,
`join_civici_sezioni.py`, `build_constraints.py`, `cs_build.py`.
Il collaudo ha chiarito la **sequenza reale** per un comune nuovo, che
nessun documento scriveva per esteso:

```
fetch_comune → build_sezioni → [build_zona_tables se articolato]
            → build_constraints → cs_build → fit
```

con `join_civici_sezioni` **per regione** (una tantum), fuori dalla
catena per-comune. Il «loop» ricordato a memoria era in realtà una
staffetta a due stadi mai documentata: `build_constraints` prepara i
blocchi comunali (`c1..c10`) dai `_decoded` del fetch; `cs_build` li
assembla con le tavole di zona nel constraint set finale.

### build_sezioni.py

**Cosa fa**: dal file regionale delle Basi Territoriali (cache
parquet) estrae le sezioni del comune, verifica i livelli ASC,
identifica sezioni speciali (convivenze) e non residenziali, valida
P1=(P2+P3), scrive `data/submun/<slug>_sezioni_2023.csv`. Rifiuta i
comuni non in `COMUNI` con messaggio esplicito.

**Test Mantova (WSL, 23/8)**: ASC1/2/3 tutti a zero → **K6C
confermato** come Ferrara/Castenaso; 574 sezioni, P1=49.044, stranieri
16,6%; 1 convivenza (P1=34); validazioni a zero. La voce provvisoria
in `COMUNI` è diventata definitiva con il commento verificato.

**Test Milano (WSL, 23/8)**: 6.059 sezioni, P1=1.371.499; **ASC1 = 9
municipi (tutte le sezioni codificate), ASC2 = 88 NIL** — ma 18 NIL a
cavallo di più municipi: le due articolazioni **non sono annidate**
(niente gerarchia alla Bologna). Convivenza metropolitana: 10.038
persone (0,73%), 62% stranieri — la scelta se escluderle a valle
«deve essere la stessa per tutti i comuni» (nota dello script, da
onorare quando si deciderà). Scelta di produzione: **municipi**
(108–189k l'uno); NIL registrato come esperimento di fit (88×161.280
= 14,2M stati). `ASC_NOMI_MILANO` scritto con denominazione ordinale
(«Municipio N»); l'assunzione suffisso ISTAT = numero municipio è
quasi certa ma resta un'assunzione — il primo open data milanese per
zona sarà il cross-check gratuito (precedente: la permutazione delle
zone di Bologna).

**Finding 3** (vedi tabella): messaggio finale fuorviante per i K6C
legittimi.

### build_zona_tables.py

**Cosa fa**: costruisce le tavole per zona (Z1..Z6) dalle sezioni,
con audit contro i totali comunali SDMX.

**Test Milano (WSL, 23/8)**: passato al primo colpo. 9 municipi, Z1
288 righe … Z6 54; audit **a zero esatto** su popolazione
(1.371.499) e stranieri (269.397) — la coerenza porta 1 ↔ porta 2 che
`cs_build` cross-audita era garantita a monte. Sanity leggibile:
Municipio 2 in testa per quota stranieri (24,7%). **Primo comune con
tavole di zona costruite senza alcun open data comunale: il tier 0
articolato funziona.**

### join_civici_sezioni.py

**Non rieseguito nel collaudo**: i suoi prodotti erano già a terra
per l'intera Lombardia, per provincia
(`data/geodata/lombardia/civici_sezioni_province/020_mantova_…`,
`015_milano_…` ‹verificare nome esatto›) — il giro fatto a suo tempo
per Brescia ha lavorato tutta la regione. Da schedare quando si
aggiungerà una regione nuova.

### build_constraints.py

**Cosa fa** (docstring v2, verificata): dal set di tavole comunali ai
blocchi del constraint set. `preflight()` verifica la copertura
temporale di tutte le tavole *prima* di costruire (obbligatoria
assente = errore fatale; opzionale assente = skip dichiarato);
censimento applicato come **condizionale sui conteggi anagrafici**
(«i marginali demografici restano esatti e lo strato socio-economico
eredita la struttura censuaria») — la filosofia *manufactured
upstream* di §I.2 del report, nel codice. Output: `c1..c10`,
`nationality_conditional.csv`, `manifest.json`, `report.md` in
`constraints_<anno>/`.

**Test Mantova (Mac, 24/8)**: costruito al primo colpo. Annotazioni:

- **Il collasso istruzione chiude un segnaposto del report** (nota
  sotto la tabella di §I.2): `USE_IF` = «diploma di II grado **o
  qualifica professionale (3-4 anni)** compresi IFTS» → `diploma`. Le
  qualifiche triennali stanno nella classe *diploma* per aggregazione
  della fonte stessa (non in `media` come congetturato). Risvolto
  SIVE-GSP: la popolazione non distingue qualifica da quinquennale —
  il `diploma3` degli agenti viene dalla resa dettagliata.
- Codici condprof scartati a vista: `22, 23, 99, ALL` — i «totali
  multiformi» di §II.3, filtrati.
- c9/c10: quote 2021 riscalate sugli occupati 2024 (fattori
  1,031–1,038) — forma-non-livelli applicata al lavoro.
- Sanity paesi: top-5 con **Brasile secondo** — insolito in Emilia,
  giusto a Mantova (distretto tessile): il sanity racconta il
  territorio.

### cs_build.py

**Cosa fa**: assembla i blocchi comunali (+ tavole di zona per i
K9C) nel `cs_<livello>.json`: zeri→ε, min_alpha, audit dei margini
condivisi. Importa `ConstraintSet` dal repo del solver → **finding
4** (dipendenza non dichiarata; sul Mac risolta clonando
`maxent-popsynth-pcd` accanto a gsp).

**Test Mantova K6C (Mac, 24/8)**: `cs_K6C.json` con m=263, |X|=5.376.
L'output è §I.2 dal vivo: blocchi completi a somma 1 esatta (A, B, E,
F); parziali C=0,939 e D=0,888 con i complementi fuori-universo
S_istruzione_under9=0,061 e S_condizione_under15=0,112 che chiudono i
conti a 1 — la coppia «partial block + complement» stampata.

**Da fare (WSL)**: Milano `build_constraints` + `cs_build --livello
K9C` (le tavole di zona sono là); pin del commit del solver per la
tabella di binding (`git -C ~/progetti/maxent-popsynth-pcd rev-parse
--short HEAD`, verificando che sia lo stesso della rigenerazione del
19/8).

---

## Stato della procedura §9 («aggiungere un comune»), come misurata

Per un comune di una **regione già in casa** (il caso
Mantova/Milano): la lista della spesa è **vuota** — tutte le porte
erano aperte o si sono aperte con `fetch_comune` + `build_sezioni` +
una voce in `COMUNI` (più `ASC_NOMI_*` e `livello` se articolato).
Per una **regione nuova**: quattro acquisizioni una tantum — file
regionale Basi Territoriali, shp sezioni, estrazione ANNCSU
provinciale (`join_civici_sezioni`), pool AVQ regionale — poi ogni
comune è gratis. Il tier 0 regge anche sul secondo comune d'Italia.
