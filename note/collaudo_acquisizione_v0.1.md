# Collaudo degli script — acquisizione, su macchina vergine

**v0.1 — 23 agosto 2026.** Documento di collaudo: per ogni script,
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
| 1 | `pip install -e .` → primo import | `requests` non è nelle dipendenze del `pyproject.toml`: `ModuleNotFoundError` al primo script che tocca la rete. Mai emerso su WSL (ambiente preesistente). | `pip install requests` sul posto; **da aggiungere a `pyproject.toml`** insieme a un controllo su `numba` e `duckdb` |

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

**Test 4 — Milano 015146 (municipi):** ‹da eseguire.›

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
NIL** (né alcun sub-comunale): ISTAT si ferma al comune, sotto ci sono
solo le Basi Territoriali. Milano si disegna quindi come ogni comune
articolato: tavole comunali via `fetch_comune`, articolazione dagli
open data del Comune (NIL o municipi) + corrispondenza
sezione→articolazione.

**Mini-finding 3**: `OUT_DIR` cablato `~/progetti/gsp/...` con
`expanduser` — non rispetta `GSP_ROOT`; il pattern bonificato in
Animarium sopravvive qui. Da allineare (`gsp.common.GSP`), commit dal
Mac.

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
