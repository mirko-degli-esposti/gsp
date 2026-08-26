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
| 3 | `build_sezioni.py`, messaggio finale | Per un comune K6C legittimo (ASC tutti a zero, `livello: None`) il messaggio «scegliere un livello e aggiungerlo prima di procedere» è fuorviante: a valle si procede con la zona degenere (Ferrara docet). | Risolto — patch dal Mac, verificata su WSL (020030 e 038008 "K6C confermato", 015146 invariato). |
| 4 | `cs_build.py` / `fit_cs.py` → `import_constraint_set()` | **Dipendenza non dichiarata dal repo del solver**: glob su directory sorella (`~/progetti/maxent-popsynth-pcd`, `/content/` per Colab), fuori dal tag di gsp. Il Mac vergine si ferma con `ImportError`; il version binding del report ha un buco (un file fuori dal tag può cambiare senza rompere git). | v1.0: dichiarare nel README («per il fit serve il clone del solver accanto a gsp») + **riga nella tabella di binding col commit pinnato** + frase di III.1 aggiornata. v1.1: pacchettizzare il solver (`pip install git+…@tag`) |v1.0 **fatto**: dichiarato nel README, riga nella tabella di binding col commit pinnato `14f5bab` (2026-08-03), claim di III.1 aggiornata. Aperto per v1.1: pacchettizzare il solver (`pip install git+…@tag`). Nota dal campo: i due cloni (Mac 0a7bc0f, WSL 14f5bab) hanno divergiuto senza che nessuno se ne accorgesse — differenza innocua (typo nei ringraziamenti), ma è la dimostrazione del rischio
| 5 | registro, `usato_da` | La sed dei 44 `usato_da` (`build_constraints.py → cs_build.py`) ha cancellato un'informazione vera: `build_constraints.py` è **vivo** — è il preparatore della staffetta a due stadi (vedi scheda). |**Risolto** (commit dal Mac): `build_constraints.py` ripristinato come lettore-catena delle tavole SDMX, `cs_build.py` rimosso dagli `usato_da` (legge solo derivati non registrati); completati i due `usato_da` mancanti (`anag_sesso_eta_statociv` → build_constraints + enrich, `istat_cens_istruzione_eta` → build_constraints); note C3/C5 e tavola non consumata riscritte
| 6 | `fit_cs.py`, default | **I default non sono la riga di produzione**: lanciato nudo su Milano prende un percorso denso — 111 minuti senza convergere (ucciso); con la riga di `rigenera.sh` (`--eps 1e-8 --min-alpha 2e-4 --pool … --outer 500 --numba --sparse --tol 0 --sweeps 40 --no-gibbs`): **54 s**. Specifico del fit: per `assign_avq`, `enrich` e `assign_nucleo` i default *sono* la produzione. |**Risolto**: default allineati alla riga di produzione (commit dal Mac: eps 1e-8, min-alpha 2e-4, tol 0, sweeps 40, anno 2024, numba+sparse attivi, gibbs opt-in via `--gibbs`, `--pool` obbligatorio con messaggio; `--no-gibbs`/`--numba`/`--sparse` accettati come no-op per non toccare `rigenera.sh`). **Verificato su WSL**: `fit_cs` nudo riproduce l'archivio del tag byte-identico su entrambi i livelli — Castenaso K6C e Piacenza K9C, `cmp` IDENTICO. Docstring aggiornata a K6C–K9C
| 7 | `gsp/nucleo.py` 502–504, via `assign_nucleo` su Milano | Matching «figli plausibili» O(n²) per nucleo (~n³ per sezione): invisibile sulla flotta (sezioni ≤ ~700), ore sulla metropoli — Milano ha 15 sezioni >1.000 (max 4.146) più la convivenza fittizia da 10k, attraversata per un risultato scartato per design. Diagnosi con py-spy (99% del tempo su una riga). | **Risolto in due patch**: (a) skip della sezione `8888888` in `lavora` (id_nucleo vuoto per design, rng non consumato — cambia la sequenza per le sezioni successive, dichiarato);… (b) conteggio via `searchsorted` in `nucleo.py`, **semantica identica verificata**: A/B sullo stesso comune con la sola 7b commutata, output byte-identico (`cmp` su `nuclei_020030.csv`); Milano 65 s. Bonus misurato: le sezioni grandi *migliorano* l'assemblaggio (Milano: omogenee 98,6%, ripieghi 0,9% — i migliori della flotta)
verificata**: A/B sullo stesso comune con la sola 7b commutata, output.
**Conseguenza sul tag, dichiarata.** Le due patch sono *post-tag*: da
oggi `master` non riproduce più i `nuclei_*.csv` del tag per nessun
comune — la 7b è semantica-identica (verificata), ma la 7a non consuma
rng e sposta la sequenza per tutte le sezioni successive alla
convivenza, che ogni comune ha. La flotta non si rigenera per questo
(§III.5: la rigenerazione invalida `donor_id` e ogni misura, non si fa
per un fix); le due patch viaggiano col prossimo ciclo. La claim del
binding resta vera com'è scritta — vale per il commit taggato.
Registrato anche in III.5 del report.
byte-identico (`cmp` su `nuclei_020030.csv`); Milano 65 s.ok procediamo in ordine
. Bonus misurato: le sezioni grandi *migliorano* l'assemblaggio (Milano: omogenee 98,6%, ripieghi 0,9% — i migliori della flotta) |
| 8 | `fonti/registro.yaml`, scheda `avq_tracciato_2024` | `python -m gsp.fonti --verifica` **dal clone fresco** (Mac, senza `data/`) segnala `ROTTA: dichiarata in git ma il grezzo non c'è`. Non era un file smarrito: il campo `archiviazione: git` contraddiceva la `nota_licenza` della scheda stessa, che dichiara la scelta opposta — «finché la licenza non è chiarita sulla pagina di rilascio il grezzo resta *locale*: verificabile qui, non ridistribuito». Il tipo di incoerenza che solo una macchina **senza** `data/` può vedere: sulla macchina completa il file c'è e la verifica passa. | **Risolto**: `archiviazione: locale`, percorso invariato; il clone fresco ora riporta *solo impronta*, che è la verità |

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

### build_zona_tables.py + la parte-zona di cs_build.py

**Il principio, in una riga** (docstring di `cs_build`, righe 8-9, e
convenzione finale di `build_zona_tables`): *ogni tabella di zona entra
come `P(zona | gruppo) × conteggi comunali del gruppo`, con IPF a
chiudere il doppio margine*. È **la stessa architettura dei vincoli
censuari applicata all'asse geografico**: la spina anagrafica dà i
livelli, tutto il resto — socio-economico *e* geografia — entra come
forma condizionata. Un solo principio, tre applicazioni (blocchi C-F,
blocchi Z, tier del paese in `enrich`).

Conseguenza da tenere a mente leggendo gli audit: `[audit] margine Z1
vs A = 0.000000` e `Z2 vs B = 0.000000` **non sono fatti sulle fonti**
ma identità algebriche — sommare `P(zona|gruppo) × count` sulle zone
restituisce `count` per costruzione. Verificano che l'implementazione
sia corretta, nient'altro. (Diverso il caso del raccordo
anagrafe↔censimento, dove lo zero *è* un fatto misurato: §sopra.)

**Cosa alimenta i blocchi.** `build_zona_tables` aggrega le colonne
delle sezioni (tracciato 2023) alla zona dichiarata nel registro
(`COM_ASC*`), producendo cinque tavole in `zona_2023/`. Ogni blocco ha
la sua risoluzione, ed è la risoluzione della *fonte*, non una scelta:

| blocco | tavola | risoluzione della fonte | assunzione dichiarata |
|---|---|---|---|
| Z1 | `z1_zona_sesso_eta5` | classi quinquennali (16) | quota di zona costante entro il quinquennio |
| Z2 | `z2_zona_sesso_macroeta_citt` | 3 macro-classi (0-14, 15-64, 65+) × ITL/FRG | quota di zona costante entro la macro-classe |
| Z3 | `z3_zona_sesso_istruzione` | **5 livelli** (la popolazione ne ha 6) | laurea e post-laurea hanno la stessa forma spaziale |
| Z4 | `z4_zona_sesso_occup` | occupati, senza dettaglio d'età | `P(zona\|sesso, occupato)` costante sui bin 15-64 |
| Z6 | `z6_zona_background` | EM1-6, dove presenti | — |

**Tre annotazioni che il collaudo ha chiarito.**

*Z3, istruzione a cinque livelli.* `EDU6TO5 = {"laurea_o_its":
"terziario", "post_laurea": "terziario"}` (cs_build): le quote di zona
si calcolano sull'aggregazione a cinque e si applicano ai conteggi
comunali a sei. La zona conosce la geografia del terziario, non la sua
composizione interna. Gli under-9 entrano a mano come `nessun_titolo`
(la tavola di sezione parte dall'età scolare), con il complemento
comunale `S_istruzione_under9` a chiudere l'universo.

*Z4 vincola solo il lato occupato* — ed è una scelta, non una
dimenticanza: la sezione dà gli occupati, ma la popolazione ha quattro
condizioni non-occupate (in cerca, studente, pensionato, altro) che la
sezione non separa; vincolarle in blocco imporrebbe a studenti e
pensionati la stessa geografia. Da qui la somma di blocco `Z4 = 0,47`
vista su Milano: è l'universo del blocco (occupati 15-64), non un
difetto — stessa lettura di C = 0,93 e D = 0,88. **Limite da
dichiarare nel report: la geografia della disoccupazione non è
vincolata da alcun dato osservato.**

*Le sezioni fittizie 888888x/999999x sono tenute* nell'unità assegnata
da ISTAT (convenzione dichiarata in `build_zona_tables`), per coerenza
contabile con i totali ufficiali — la stessa scelta che a valle,
nell'anello 4, richiede invece lo skip (finding 7a).

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

### fit_cs.py — la catena arriva alla popolazione (WSL, 24/8)

**Milano K9C, riga di produzione**: esatto, **MRE = 4,24·10⁻⁴ in
54 s**; massa sulle celle escluse = 0 esatto (737.100 celle post-hoc,
supporto effettivo ~346k/1,45M); popolazione campionata n=1.371.499.
Stesso ordine di Parma (4,9·10⁻⁴): il fit error è indipendente dalla
taglia, e per il solver contano le zone, non gli abitanti — il secondo
comune d'Italia è più leggero di Parma.

**Mantova K6C, riga di produzione**: esatto, **0,17 s, MRE = 3,43·10⁻⁴**
(|X| = 5.376, ~270× più piccolo di Milano).

**Finding 6 — i default di `fit_cs` non sono la produzione.** Lanciato
nudo su Milano: percorso denso, 111 minuti senza convergere (ucciso);
con la riga di `rigenera.sh` (`--eps 1e-8 --min-alpha 2e-4 --pool …
--outer 500 --numba --sparse --tol 0 --sweeps 40 --no-gibbs`): 54 s.
Rimedio: allineare i default alla produzione, o dichiarare nel README
che la via è `rigenera.sh`. Nota collaterale: la docstring dice «K6C o
K7C» — datata, il K9C è il livello di produzione.

**Mini-finding — la lista dei comuni vive in due posti**:
`gsp.common.COMUNI` (registro) e l'array `COMUNI` di `rigenera.sh`
(`COD:LIV:POOL`, con POOL ≈ 1,3×N di sovracampionamento). Per rendere
Mantova e Milano rigenerabili in blocco vanno aggiunte due righe
all'array; candidato a consolidamento (POOL derivabile da N).

---

---

## Anelli 2–4 sui due comuni nuovi (WSL, 25/8)

Gli anelli 2–4 dipendono da fonti che non si auto-acquisiscono (AVQ
mIcro.STAT su richiesta; repertorio nuclei derivato da AVQ): il **Mac
collauda il lettore pubblico** — che arriva legittimamente fino alla
popolazione dell'anello 1 — la **WSL è la macchina completa**. Da
dichiarare in README e §III.1: *riproducibile da fonti auto-acquisibili
fino all'anello 1; oltre, servono i microdati (ottenibili da chiunque,
con richiesta manuale).*

### assign_avq.py (anello 2)

Riga di produzione = default (nessun flag in `rigenera.sh`): il
finding 6 è specifico di `fit_cs`. Entrambi i comuni al primo colpo;
la matrice di correlazione stampata in coda è **identica** sui due —
com'è giusto: è una proprietà del pool lombardo, non del comune, e
vederla uguale due volte è la conferma involontaria.

**La scoperta FORZE_ARMATE** (vedi Rettifica in coda): Mantova
mostrava una variabile che il report dichiarava assente; il controllo
sulla flotta al tag ha mostrato che c'è ovunque — il fix era entrato
prima del tag, le note no. Le variabili donate sono **23** (conteggio
sulle colonne: 8 + 11 PUNTIFI + FORZE_ARMATE + VOTOUSL + BMI + CPESO);
resta da chiudere il conto 23/21/20 (donate / firma / pannello) con
una nota a piè unica nel report.

### enrich.py (anello 3)

**Milano**: il ramo mai esercitato — **tier 0 articolato** — gira
perfetto: «tier 0 su municipi, 171 paesi × 2 sessi × 9 unità, IPF 1
iter, scarto 5·10⁻¹⁶»; indirizzo 99,10% dalla sezione; età media 45,2;
diagnostica UE: struttura di sezione/di zona = 9,9× (la geografia fine
domina — coerente con il segnale compositivo). MAE per sezione: pop
1,28, stranieri 1,17, UE 0,08 su correlazioni ≥0,998.

**Mantova**: MAE pop 0,90 — ma **indirizzo 15,31% dalla sezione,
84,62% fallback di zona** (che con zona unica = coordinate sparse sul
comune). Indagine: il derivato civici ha 240 accessi per il capoluogo;
il grezzo ANNCSU regionale ne ha **17.009**; dei 17.009, solo 240
hanno METODO di georeferenziazione valorizzato. **Non è un bug di
`join_civici_sezioni`: Mantova ha certificato gli accessi senza
coordinate**, e lo spatial join legittimamente li scarta. Terzo caso
mai visto dalla flotta (l'Emilia è georeferenziata quasi al 100%).
Conseguenze: (a) il **regime pubblico non ne soffre** — lon/lat
pubblici sono un punto casuale nella sezione, che tutti hanno; il
buco tocca solo l'indirizzo testuale dei regimi persona/narrativo;
(b) §I.4 del report guadagna la frase onesta: *la copertura
dell'indirizzo è una proprietà della georeferenziazione ANNCSU del
comune, non della pipeline*.

**Seconda rettifica, la migliore**: il blocco `[val]` di `enrich`
stampa **a ogni corsa** il MAE per sezione contro il censimento — il
«numero *reported*, script non conservato» di §III.3 sta quindi nei
log della rigenerazione del 19/8 ‹verificare: grep "\[val\]" sul log
di Parma›. Se c'è, l'unico numero non rimisurato della Part III
diventa **[m]** e la Part III è misurata al 100%.

### assign_nucleo.py (anello 4)

Firma diversa dagli altri anelli (niente `--pop-file`: risolve da
solo il `_full`; comuni posizionali multipli; seme derivato
`20260810+int(comune)`). Il repertorio è **unico**
(`repertorio_nuclei_v1.json`, base AVQ emiliana + coda Parma): i
comuni lombardi ricevono configurazioni di nucleo emiliane —
assunzione ereditata, dichiarata qui; le configurazioni sono meno
regionali delle risposte, ma è un'assunzione, non un fatto.

**Mantova**: 49.044 individui, 24.298 nuclei (ampiezza 2,02 — città
anziana), senza ripiego 96,7%, omogenee 94,2%, incoerenti 23,0%,
divario generazionale mediano 30 anni, seme 20280840 ✓. **Non
collocati 2,16%**: dentro la banda di flotta (1,1–2,3%) ma al bordo
alto, e sopra la forchetta della docstring («1,4–1,9%» — datata, da
aggiornare alla banda misurata). Con la convivenza a 34 persone, i
non collocati sono quasi tutti residui d'assemblaggio.

**Milano** (post patch 7a+7b, **65 s** — era >1h ucciso due volte):

| comune | individui | nuclei | ampiezza | omogenee | incoerenti | non collocati |
|---|---|---|---|---|---|---|
| Mantova | 49.044 | 24.275 | 2,02 | 94,2 % | 23,0 % | 2,21 % (incl. 34 convivenza) |
| Milano | 1.371.499 | 736.131 | 1,86 | 98,6 % | 17,7 % | 1,88 % (incl. 9.992 convivenza, 0,73 %) |

Tre letture. *Milano è il nuovo estremo della flotta su tre colonne,
tutte nella direzione che la sua demografia comanda*: ampiezza 1,86
(sotto Bologna, 1,85 — le due metropoli si riconoscono); incoerenti
17,7 %, sotto il minimo di flotta (Bologna 18,2 %) — terza conferma
della regola «più single, meno slot per l'incoerenza». *Le sezioni
grandi migliorano l'assemblaggio*: omogenee 98,6 % e senza-ripiego
99,1 %, i migliori mai misurati — più candidati per ruolo, meno
ripieghi; il costo quadratico del finding 7 era il prezzo
computazionale di un beneficio statistico. *Mantova riassemblata post
patch*: 24.275 nuclei (era 24.298), non collocati 2,21 % (era 2,16 %,
ora includono la convivenza), il resto invariato al decimale — il
salto ha cambiato solo ciò che doveva.

## Misure d'occasione (26/8): il margine di zona nel campione

Nate da una domanda posta rileggendo la Part I: *sommando le zone di un
quartiere ritrovo esattamente i suoi abitanti sintetici?* No — e vale la
pena avere il numero, perché è il tipo di scarto che un consumatore dei
dati incontra senza spiegazione.

### 1. Quanto il campione si scosta dal censo, per zona

L'anello 1 vincola la *distribuzione* di zona e poi estrae N individui:
ogni zona porta quindi l'errore di un'estrazione multinomiale. Solo il
totale comunale è esatto per costruzione. Milano, K9C, nove municipi:

| zona | censo | sintetico | diff | rel% |
|---|---|---|---|---|
| 15146001 | 107.629 | 106.989 | −640 | −0,595 |
| 15146002 | 151.112 | 151.460 | +348 | +0,230 |
| 15146003 | 142.501 | 142.472 | −29 | −0,020 |
| 15146004 | 159.311 | 159.591 | +280 | +0,176 |
| 15146005 | 123.239 | 123.772 | +533 | +0,432 |
| 15146006 | 150.078 | 149.934 | −144 | −0,096 |
| 15146007 | 169.031 | 168.941 | −90 | −0,053 |
| 15146008 | 188.850 | 188.838 | −12 | −0,006 |
| 15146009 | 179.748 | 179.502 | −246 | −0,137 |

**Scarto assoluto medio 258 individui**, contro ≈ 293 attesi per
un'estrazione di questa taglia (per una normale, E|X| = 0,8 σ con
σ = √(N p (1−p)), p ≈ 0,11, N = 1.371.499). Segni alternati, nessuna
deriva sistematica: è rumore di campionamento, non errore di modello.

```bash
python3 - <<'EOF'
import pandas as pd
com, liv = "015146", "K9C"
pop = pd.read_csv(f"data/comuni/{com}/constraints_2024/popolazione_{liv}.csv",
                  usecols=["zona"], dtype=str)
sin = pop.zona.value_counts().sort_index()
z = pd.read_csv(f"data/comuni/{com}/zona_2023/z1_zona_sesso_eta5.csv",
                dtype={"zona": str})
cen = z.groupby("zona")["count"].sum().sort_index()
d = (sin - cen).dropna()
print(pd.DataFrame({"censo": cen, "sintetico": sin, "diff": d,
                    "rel%": (100*d/cen).round(3)}).to_string())
print("\nscarto assoluto medio:", round(d.abs().mean(), 1),
      "| atteso ~sqrt(N_zona):", round((cen**0.5).mean(), 1))
EOF
```

(nota: `popolazione_<LIV>.csv` è l'uscita del *fit*, prima di `enrich` —
così la misura isola il campionamento puro.)

### 2. L'ipotesi che ne è seguita, e la sua falsificazione

**Congettura**: se ogni zona sbaglia di ~250–650 individui e `enrich`
li distribuisce nelle sue sezioni proporzionalmente ai conteggi
censuari, l'errore si spalma a ~1 individuo per sezione — cioè
*l'ordine del MAE osservato* (1,28 su Milano). In tal caso il MAE per
sezione non misurerebbe la qualità dell'allocazione ma il rumore a
monte, e la nota geometrica sotto la tabella III.3 andrebbe riscritta.

**Falsificata dalla decomposizione**, su Milano:

| componente | MAE |
|---|---|
| totale osservato | 1,280 |
| propagato dalla zona (errore di zona × quota della sezione) | 0,383 |
| residuo netto (allocazione) | 1,236 |
| corr(osservato, propagato) | 0,37 |

**La ragione è strutturale**: l'errore di zona è *un numero solo*,
spalmato in modo coerente su centinaia di sezioni; l'arrotondamento
largest-remainder agisce invece dentro *ogni cella demografica*
separatamente (sesso × età-3 × cittadinanza), e decine di ±1
incoerenti si accumulano più in fretta in valore assoluto. La nota
geometrica di III.3 resta valida; la voce entra in III.6 come
previsione falsificata.

```bash
python3 - <<'EOF'
import pandas as pd
com = "015146"
pop = pd.read_csv(f"data/comuni/{com}/constraints_2024/popolazione_K9C_avq_full.csv",
                  usecols=["sezione", "zona"], dtype=str)
sin = pop.groupby("sezione").size().rename("sint")
sez = pd.read_csv("data/submun/milano_sezioni_2023.csv", dtype={"SEZ21_ID": str})
cen = sez.set_index("SEZ21_ID")["P1"].rename("cen")
zon = sez.set_index("SEZ21_ID")["COM_ASC1"].astype(str).rename("zona")
t = pd.concat([cen, sin, zon], axis=1).fillna(0)
t["res"] = t.sint - t.cen
gz = t.groupby("zona")
t["err_zona"] = t.zona.map(gz.res.sum())
t["quota"] = t.cen / t.zona.map(gz.cen.sum())
t["atteso_propagato"] = t.err_zona * t.quota
t["residuo_netto"] = t.res - t.atteso_propagato
print("MAE totale        :", round(t.res.abs().mean(), 3))
print("MAE propagato     :", round(t.atteso_propagato.abs().mean(), 3))
print("MAE netto (alloc.):", round(t.residuo_netto.abs().mean(), 3))
print("corr(res, propagato):", round(t.res.corr(t.atteso_propagato), 3))
EOF
```

### 3. Coda

Entrambi gli script sono usa-e-getta ma meritano di diventare una
diagnostica sola (`scripts/diagnostica/verifica_zona_campione.py`,
argomenti comune e livello): chiuderebbe anche l'open item di Part III
sulle diagnostiche riusabili. Da fare quando serve su un secondo
comune — Bologna con le sue diciotto zone è il controllo naturale, e
direbbe se il rapporto fra le due componenti dipende dal numero di
zone.

## Stato della procedura §9 («aggiungere un comune»), come misurata

Per un comune di una **regione già in casa** (il caso
Mantova/Milano): la lista della spesa è **vuota** — tutte le porte
erano aperte o si sono aperte con `fetch_comune` + `build_sezioni` +
una voce in `COMUNI` (più `ASC_NOMI_*` e `livello` se articolato).
Per una **regione nuova**: quattro acquisizioni una tantum — file
regionale Basi Territoriali, shp sezioni, estrazione ANNCSU
provinciale (`join_civici_sezioni`), pool AVQ regionale — poi ogni
comune è gratis. Il tier 0 regge anche sul secondo comune d'Italia.

> **Rettifica (25/8).** §III.4 dichiarava la batteria a undici item su
> dodici per l'assenza di `FORZE_ARMATE` (selezione per prefisso), e
> §III.5.6 ne programmava il rientro. **Misurato sui file al tag** (la
> rigenerazione del 19/8 è bit-identica, quindi i file sono lo stato
> del tag): `FORZE_ARMATE` è presente in `_avq.csv` e `_full.csv` di
> tutta la flotta — il fix era entrato prima del tag e le note non
> erano state aggiornate. La batteria è a dodici item; §III.4 va
> corretto e §III.5.6 ridotto a `donor_anno` e `cella_avq`. Il
> collaudo l'ha scoperto perché Mantova mostrava una variabile che il
> report dichiarava assente.
**Verificato al tag**: `grep "popolazione  MAE"` sui log del 19/8 dà
gli undici valori — banda 0,72 (Ferrara) – 1,57 (Brescia), totali
esatti ovunque. Il numero «*reported*» di §III.3 diventa **[m]** con
fonte `log/rigenera_20260819_0940/*.log`, e la Part III è misurata al
100%.
