# Viewer delle popolazioni sintetiche GSP — documento di design

**v0.2 — 29 luglio 2026 — nessun codice, solo design**
Riferimento dati: `GSP_popolazioni_full_riferimento_v16.md` (§ citati sotto).

*Rispetto alla v0.1: tre decisioni bloccate (stack, destinazione, riferimento).
Semplificati §3.3 e §4.2, riscritti §7 e §10.*

---

## 0. Decisioni prese

| | scelta | conseguenza principale |
|---|---|---|
| **stack** | Observable Framework + DuckDB-WASM, applicazione statica | nessuna riscrittura per la versione in rete; curva di apprendimento JS limitata a Plot e Inputs |
| **destinazione** | solo interna per ora | bundle completo con indirizzi; nessun deploy; interruttore `--pubblico` predisposto e non usato |
| **riferimento** | una sola serie: censimento comunale | pannello dei marginali molto più semplice; il riferimento spaziale resta uno slot vuoto |

**Ancora aperto**: il nome. Cinque candidati in §12, raccomandazione invariata (*Stato delle Anime*, oppure *Microstato* per il pubblico dei fisici).

---

## 1. Scopo, utenti, non-obiettivi

**Tre utenti, in ordine di priorità temporale.**

1. **Tu, adesso.** Ispezione, controllo qualità, ricerca di anomalie prima che finiscano in un paper. È l'unico utente per cui la velocità di iterazione conta più della grafica.
2. **I collaboratori** (Tarantino, Pachet, Zucker, il consorzio PRISM). Devono capire *cosa possono chiedere ai dati* senza leggere 1.000 righe di documentazione. Link permanenti citabili in un paper.
3. **Il pubblico.** Fuori portata per ora, ma le decisioni che lo renderebbero possibile costano zero adesso e molto dopo (§7.3).

**Non-obiettivi dichiarati**, da scrivere nella pagina Metodo:

- non è uno strumento di stima locale: nessun numero di questa app è una misura del quartiere reale;
- non genera popolazioni: consuma i `_full` già prodotti;
- non fa inferenza causale né previsione.

---

## 2. Il principio guida: livello di garanzia

Ogni numero mostrato appartiene a una di **quattro classi di garanzia**, e la classe è visibile sempre, non in una nota a piè di pagina.

| classe | badge | attributi | cosa garantisce |
|---|---|---|---|
| **V — vincolato** | pieno | anello 1: `zona`, `sesso`, `eta`, `stato_civile`, `cittadinanza`, `istruzione`, `condizione`, `background`, `origine_genitori` | marginali e incroci del constraint set riprodotti con MRE ≈ 4·10⁻⁴ |
| **A — allocato** | mezzo pieno | anello 3: `sezione`, `eta_anni`, `via`, `civico`, `lon/lat` | allocazione esatta per sezione (MAE 0,74–1,58 su medie 84–175), sotto le assunzioni (8)–(10) |
| **C — condizionato** | contorno | `paese`, `area` | vincolato ai margini censuari, con struttura geografica secondo il tier (§6 del riferimento). Su Modena, tier 0: nessuna struttura geografica |
| **D — donato** | tratteggiato | le 21 AVQ | **nessuna informazione geografica**. Dipendono solo da `sesso × macroetà × istruzione4 × regione` (assunzione 6) |

**Conseguenza operativa**, imposta dall'interfaccia e non lasciata alla prudenza dell'utente:

> Qualunque variazione spaziale di una variabile di classe **D** è **interamente compositiva per costruzione**. L'app lo dice dove il numero appare, non altrove.

Una mappa per sezione di `PUNTIFI10` non è vietata, ma esce con l'etichetta *«variazione 100% compositiva — nessun segnale areale nei dati»* e con accanto la scomposizione (§4.2). È lo stesso principio di §11.1 del riferimento: la metrica grezza va sempre affiancata alla sua ipotesi nulla.

**Numerosità efficace.** Le statistiche AVQ di una sottopopolazione non poggiano sugli individui ma sui **donatori distinti** che li hanno generati: a Bologna il riuso medio è 84×, quindi 500 individui possono nascere da ~6 donatori. L'app calcola `n_eff` = donatori distinti, e **tutte le bande di incertezza sulle AVQ usano `n_eff`, non `n`**. Richiede una colonna `donor_id` nel bundle (§3.2) — è la dipendenza a monte da verificare per prima.

---

## 3. Modello dei dati

### 3.1 Un bundle, non l'albero di lavoro

Il viewer **non legge mai** `~/progetti/gsp/data/comuni/...`. Legge un *bundle* versionato, prodotto da uno script di export. È ciò che rende l'app pubblicabile in seguito senza modifiche: in locale e in rete girerà sugli stessi byte.

```
bundle/                          # fuori dal repo git, ricostruibile
  manifest.json                  # registro, attributi, etichette, ordini, classi, riferimenti
  qualita.json                   # MRE, MAE, correlazioni, copertura AVQ, riuso donatori
  comuni/
    017029/
      pop.parquet                # 198.259 × ~42, categoriche dizionario-codificate
      agg_sezioni.parquet        # aggregati non filtrati per sezione (vista d'ingresso)
      sezioni.topojson           # 1.822 poligoni semplificati + P1, ST1, ST16/19, P30-45, ST25-30
      zone.topojson              # 33 poligoni (dissolve) + nomi verificati
    034027/ 037006/ 036023/ ...
  regioni/
    emilia_romagna.topojson      # confini comunali, per la futura vista regionale
```

**Perché Parquet**: le 40 colonne sono quasi tutte categoriche a bassa cardinalità; con dictionary encoding un comune sta in 8–20 MB contro i ~90 MB del CSV. Il motore legge **solo le colonne coinvolte nella query**, che è la differenza fra 40 ms e 4 s.

**Un accorgimento che conta**: ordinare le righe per `sezione` prima di scrivere, con row group di ~50k righe. Le statistiche min/max di row group permettono di saltare interi blocchi per qualunque filtro spaziale, che è il filtro più frequente.

**Il bundle sta fuori dal repo.** 60–80 MB per quattro comuni non vanno in git. Il repo contiene codice, schema del manifest e lo script di build; il bundle si ricostruisce in un comando. Quando si pubblicherà, il bundle andrà su un host con CORS e range request (Cloudflare R2, Hugging Face Datasets) o direttamente su Pages se resta sotto il centinaio di MB.

### 3.2 Colonne aggiunte dall'export

| colonna | perché |
|---|---|
| `id` | stabile, per i permalink all'individuo |
| `donor_id` | numerosità efficace delle AVQ (§2). **Se non esiste, va tracciata in `assign_avq.py`** |
| `cella_avq` | la cella di condizionamento usata e il livello di collasso: rende ispezionabile l'assunzione (6) |
| `macroeta`, `istr4` | le variabili su cui *davvero* girano le AVQ, esplicitate |
| `lon_j`, `lat_j` | coordinate con jitter deterministico entro il civico (§4.3) |

`cella_avq` è l'unica colonna che rende visibile *quanto* il collasso gerarchico è intervenuto. Una sottopopolazione in cui il 60% degli individui ha ricevuto le AVQ al terzo livello di collasso è molto meno informativa di una in cui tutti stanno al livello pieno, e oggi la differenza è invisibile.

### 3.3 Il riferimento reale — versione semplice

Una sola serie, dichiarata **per attributo** nel manifest. Nessuna algebra di tavole, nessuna ricerca di incroci osservabili.

```
"riferimento": {
  "sesso":       { "fonte": "censimento_comunale", "tavola": "targets_K9C.c1" },
  "istruzione":  { "fonte": "censimento_comunale", "tavola": "targets_K9C.c5" },
  "paese":       { "fonte": "censimento_comunale", "tavola": "paesi_censuari" },
  "eta_anni":    { "fonte": "istat_eta_singola",   "tavola": "cens_eta_anno" },
  "AMBIENTE":    { "fonte": "avq_regionale_pesata", "n_donatori": 4629, "ic": true },
  ...
}
```

Tre sorgenti, non una:

- **censimento comunale** per tutto l'anello 1, `paese`, `area`. È il caso normale;
- **ISTAT età singola** per `eta_anni` (la stessa distribuzione usata dall'assunzione 9);
- **AVQ regionale pesata** per le 21 variabili di classe D — la stima campionaria pesata sul pool regionale, con intervallo di confidenza. Non esiste un riferimento comunale per queste, e fingere il contrario sarebbe peggio che non averlo.

Il caso AVQ ha una proprietà utile: la marginale sintetica comunale e la stima regionale pesata **differiscono esattamente per composizione demografica**, quindi la riga di scomposizione di §4.2 spiega lo scarto per intero, sempre. È una verifica gratuita che gira su ogni pannello.

**Slot vuoto, predisposto.** Le tavole reali per sezione (`P1`, `ST1`, `ST16/19`, `P30–P45`, `ST25–ST30`) entrano comunque nel bundle: servono alla mappa (§4.3) e alla pagina Metodo. Il giorno in cui volessi il confronto reale su un filtro spaziale, la serie esiste già e va solo collegata al pannello.

---

## 4. Le viste

Cinque pagine: **Città**, **Esplora**, **Individuo**, **Confronta**, **Metodo**.

### 4.1 Esplora — i filtri

Pagina centrale. Colonna sinistra: filtri. Corpo: marginali. Destra o sotto: mappa. Tutto in crossfilter.

**Filtri di v1** (dodici, non quaranta):

- spaziali: `zona` (multiselezione, o selezione dalla mappa), `sezione` (solo via lazo sulla mappa);
- anello 1: `sesso`, `eta`, `stato_civile`, `cittadinanza`, `istruzione`, `condizione`, `background`, `origine_genitori`;
- anello 2–3: `paese` (con ricerca, raggruppabile per continente/UE), `area`, `eta_anni` (slider continuo).

**Le AVQ non sono filtri in v1.** Sono variabili *mostrate*. Il motivo è epistemico prima che tecnico: filtrare su `FIDUCIA` e guardare la mappa produce una figura che sembra dire qualcosa sulla geografia della fiducia e non lo dice.

**Barra di stato**, sempre visibile: `n` selezionati · % della città · `n_eff` donatori · sezioni toccate · badge rosso se `n < 200` o `n_eff < 30`.

Ogni filtro attivo è una pillola rimovibile; lo stato completo sta nell'URL (§5).

### 4.2 Marginali — versione a due serie

Per ogni attributo mostrabile un pannello, in griglia di small multiples, con i primi sei fissabili.

Due serie:

| serie | definizione |
|---|---|
| **sintetico** | `p̂(a \| F)`, barre piene |
| **riferimento** | censimento comunale (o le altre due fonti di §3.3), marcatori a rombo su neutro scuro |

La lettura è diretta: **poiché la popolazione non filtrata riproduce il censimento a 4·10⁻⁴, il riferimento è anche il valore atteso sotto indipendenza fra l'attributo mostrato e il filtro.** Lo scarto *è* l'associazione. Senza filtro, lo stesso pannello diventa un pannello di validazione e le due serie coincidono. Questa doppia funzione è il motivo per cui una serie sola basta, e va scritta nell'interfaccia una volta, in chiaro.

**Modalità Δ.** Un interruttore trasforma le barre in scarti dal riferimento, con banda di campionamento `√(p(1−p)/n)` — e `n_eff` per le variabili di classe D. Serve a non leggere rumore: su 300 individui una differenza di 3 punti percentuali non è niente.

**Riga di scomposizione** (classi C e D):

```
AMBIENTE, Fiumicello vs riferimento:  Δ = −0,07
   spiegato dalla composizione (sesso × macroetà × istr4):  −0,07  (100%)
   residuo areale:                                           0,00
```

Per le classi C e D il residuo è **zero per costruzione**, e mostrarlo ogni volta è il modo più efficace di impedire la lettura sbagliata. Per la classe V il residuo è l'errore del modello, ~10⁻⁴.

**Tipi di grafico**: nominali → barre orizzontali ordinate per frequenza; ordinali (`eta`, `istruzione`, `SALUTE`, `BMI`, `CPESO`) → barre in ordine naturale, mai riordinate; 0–10 (`PUNTIFI*`, `VOTOUSL`) → istogramma + media con IC su `n_eff`; continue (`MH`, `eta_anni`) → densità + quantili.

**Pannello dedicato alla fiducia istituzionale**: dodici medie su un asse comune 0–10, ordinate, con i riferimenti nazionali AVQ 2024 come tacche fisse (vigili del fuoco 8,10 · forze dell'ordine 6,70 · ASL 6,34 · Comune 5,13 · Regione 4,65) e le fasce di copertura (86–88% / 42–43% / 15–20%) come tratteggio sulle variabili interessate. Sotto, opzionale, la matrice di correlazione con `min_periods`, che riproduce la struttura a due fattori (servizi vs politica): è uno dei risultati più belli del dataset e merita una vista propria.

### 4.3 Mappa

Quattro modalità.

| modalità | geometria | quando |
|---|---|---|
| **Individui** | punti ai civici, jitter deterministico | comunicazione, drill-down |
| **Sezioni** | 1.357–2.224 poligoni | **il default analitico**: è dove sta il segnale (§10 del riferimento) |
| **Zone** | 4–33 poligoni | confronto con le fonti comunali, etichette leggibili |
| **Esagoni** | H3 res 9/10 | quando le sezioni sono troppe o si confrontano città |

**La metrica di default non è il conteggio.** Un conteggio filtrato riproduce la densità di popolazione: qualunque filtro «illumina» il centro. In ordine:

1. **quota** — frazione del filtro sul totale locale;
2. **lift** — quota locale / quota comunale, scala divergente centrata su 1;
3. **z** — scarto in unità di deviazione binomiale, l'unico modo di non leggere come struttura una sezione da 20 abitanti al 100%;
4. conteggio, ultimo.

Con quota e lift serve **shrinkage empirico-bayesiano** verso la media comunale, o almeno lo sbiadimento delle sezioni sotto ~30 individui filtrati. Senza, le mappe di sottopopolazioni piccole sono maculate di falsi estremi.

**Qui il riferimento reale c'è, e va usato.** A differenza dei marginali, la mappa ha un dato osservato per sezione: `P1`, `ST1`, `ST16/19`, `P30–P45`. Una modalità **affiancamento sintetico/reale** con scala condivisa, per le quantità dove il reale esiste, è quasi gratis e vale come validazione visiva più di qualunque tabella di MAE.

**Dettagli che vanno gestiti o si vedono subito:**

- le **convivenze** (50–630 per comune) stanno al centroide della zona: senza trattamento producono una torre di punti coincidenti. Escluse dai punti per default, con conteggio dichiarato, simbolo distinto se incluse;
- `indirizzo_fonte = "zona"` (36–278 individui): stesso trattamento;
- più individui per civico: jitter radiale deterministico (funzione dell'`id`, quindi stabile fra sessioni) con raggio ~8 m, così il popup resta cliccabile;
- **base cartografica senza chiavi API**: tiles Protomaps `.pmtiles` self-hosted, oppure CARTO Positron. Le self-hosted rendono l'app archiviabile per intero.

**Doppio strato**: base grigia (campione della popolazione totale) + strato colorato (il filtro), per distinguere «qui non ce ne sono» da «qui non c'è nessuno».

**Selezione spaziale**: lazo e clic su poligono aggiungono un filtro. Da mappa a filtro e ritorno senza passare dai menu — è il gesto che rende utile il crossfilter.

**Campionamento**: tetto a 50k punti con campionamento uniforme e frazione dichiarata in interfaccia; oltre, passaggio automatico a esagoni.

### 4.4 Individuo

La carta d'identità di un individuo sintetico, dal clic su un punto o dal pulsante *estrai un individuo a caso*.

Quaranta campi raggruppati per anello, **ciascuno col proprio badge di garanzia**, e per le AVQ la cella di condizionamento e il livello di collasso. In fondo, la catena di provenienza:

```
Individuo 017029-0084213      [INDIVIDUO SINTETICO — non esiste]
  anello 1   MaxEnt, cella (zona 17029012, F, 35-49, coniugata, ITL, diploma, occupata)
  anello 2   paese: Italia · AVQ dal donatore #3117, cella (F, 35-49, istr4=3), livello pieno
  anello 3   sezione 017029000412 · via ... 19A · 45,54 / 10,21
```

Due ragioni oltre alla bellezza. È lo strumento di debug più efficace che esista, perché rende visibile tutta la pipeline su un caso. Ed **è già il prompt della persona** per il tier 2: una vista «come l'agente LLM vede questo individuo» collega il viewer al lavoro SimComm senza costruire niente di nuovo, e in una presentazione è il momento in cui si capisce cosa sono davvero le due tier.

### 4.5 Confronta

Il §8 del riferimento avverte che il confronto fra città è problematico: risoluzioni diverse su partizioni di taglia diversa. Tre livelli di rigore decrescente e dichiarato.

**Livello A — comune (sicuro).** Marginali comunali affiancati, una colonna per città, più la tabella-carta d'identità di §10 (popolazione, zone, sezioni, civici, quota stranieri, tier, donatori, riuso, `|X|`). Sempre lecito.

**Livello B — distribuzione fra sezioni (il livello giusto).** Non si confrontano le zone ma le **distribuzioni di indicatori a livello di sezione**: quota stranieri, quota laureati, quota over-65. Le sezioni sono unità ISTAT di disegno omogeneo, quindi confrontabili fra città in un modo in cui 4 quartieri di Modena e 33 di Brescia non sono. ECDF sovrapposte o ridgeline. Accanto, la decomposizione della varianza di §10 in forma grafica: il rapporto *tra/dentro* che cresce monotonamente con la taglia media delle zone (5,9× → 43,5×) diventa **l'argomento visivo** per cui la sezione conta più della zona.

**Livello C — zone (con avviso).** Mappe affiancate, scale sincronizzate, avviso non silenziabile: partizioni non confrontabili.

**Avviso obbligatorio sulle AVQ.** Parma, Bologna e Modena condividono lo **stesso pool di 4.629 donatori emiliani**: qualunque differenza AVQ fra le tre è integralmente compositiva — non c'è un solo dato che distingua un bolognese da un modenese oltre alla struttura per sesso, età e istruzione. Brescia attinge a un pool diverso (8.111, Lombardia), quindi un confronto Brescia–Bologna mescola composizione e differenza di pool regionale, che sono cose diverse. Va scritto nella vista.

### 4.6 Metodo e qualità

La pagina che rende l'app difendibile.

- **Validazione**: MRE(α>0) per comune; MAE per sezione e correlazioni (§10) come scatter osservato–sintetico per sezione, più convincente di qualunque numero;
- **Copertura AVQ**: le tre fasce, con la copertura effettiva per variabile e comune, e la nota sul *planned missing*;
- **Riuso dei donatori**: istogramma del riuso, col tetto strutturale (99,7–100% del pool usato) dichiarato;
- **Le sette assunzioni** di §7 in elenco cliccabile: cliccando la (8) si illuminano gli attributi che ne dipendono, ovunque nell'app;
- **Tier del paese** per comune, con i numeri di §6 (2,08–2,57 volte l'ipotesi nulla a livello di quartiere; 1,01–1,04 a livello di sezione, cioè nulla, correttamente);
- **Provenienza dei nomi di zona**: la verifica su due assi (§3.2), con l'incidente di Bologna raccontato. Un'app che documenta un proprio errore passato è un'app di cui ci si fida.

---

## 5. Interazione e stato

**Crossfilter completo**: cliccare una barra aggiunge il filtro corrispondente; disegnare sulla mappa aggiunge un filtro spaziale; entrambi si riflettono nelle pillole e nell'URL.

**Stato nell'URL**, interamente:

```
/esplora/017029?zona=17029012,17029015&sesso=F&istruzione=laurea_o_its
               &mostra=AMBIENTE,PUNTIFI10&mappa=sezioni&metrica=lift
```

Vale da solo lo sforzo: mandare una vista a Tarantino in una riga, citare una figura in un paper con un link riproducibile, ricostruire in un secondo lo stato in cui hai visto qualcosa di strano. Funziona anche in locale, dove i link restano validi fra sessioni.

**Esportazioni** con provenienza incorporata: PNG/SVG del pannello, CSV dei marginali (con riferimento e badge di classe), permalink, GeoJSON degli aggregati per sezione.

---

## 6. Grafica

**Estetica dell'anagrafe.** Il riferimento visivo è il registro amministrativo — tabelle a colonne strette, cifre allineate, timbri — reso in modo contemporaneo, non nostalgico.

- **tipografia**: un serif con carattere per titoli e numeri grandi; un sans neutro per l'interfaccia; **un monospaziato per tutte le cifre**, con cifre tabulari. La coerenza dei numeri è il 70% dell'impressione di rigore;
- **colore**: fondo caldo quasi bianco; **un solo accento** per il sintetico; il riferimento sempre in neutro scuro, mai colorato — la gerarchia dev'essere leggibile in bianco e nero. Divergente sobria per il lift, sequenziale monocroma per le quote. Palette verificata per daltonismo;
- **badge di garanzia** come piccoli timbri, con forma oltre che colore (pieno / mezzo / contorno / tratteggiato), così funzionano anche stampati;
- **densità alta**: small multiples piccoli e numerosi, nello stile delle tavole statistiche. Più bello e più onesto della singola figura grande, che invita a sovra-interpretare;
- **mappa**: base chiara desaturata per le coropleti, base scura solo per i punti;
- **movimento**: transizioni brevi sui cambi di filtro, così si percepisce *cosa* è cambiato. Nient'altro si muove.

Observable Framework ha un tema di default già decente: la personalizzazione passa da un foglio di stile che ridefinisce le variabili CSS del tema. La grafica in senso proprio va fatta in F6, ma tipografia, badge e palette vanno decisi in F2 o si riscrive.

---

## 7. Architettura e strumenti — stack bloccato

### 7.1 I pezzi

| strato | strumento | nota |
|---|---|---|
| costruzione bundle | Python: pandas, geopandas, duckdb, mapshaper | `build_bundle.py {CODICE}` |
| impalcatura | **Observable Framework** | pagine in Markdown con blocchi JS, *data loader* in Python, build statica |
| query | **DuckDB-WASM** | SQL sul Parquet nel browser, via range request HTTP |
| grafici | **Observable Plot** | small multiples e faceting in poche righe |
| mappa | **MapLibre GL** + **deck.gl** | MapLibre per base e coropleti, deck.gl per punti ed esagoni H3 |
| geometrie | TopoJSON + mapshaper | 2.224 poligoni semplificati in ~300 KB |
| hosting | nessuno per ora | `npm run dev` in locale; il repo può stare privato su GitHub da subito |

Il JavaScript che dovrai scrivere è confinato a Plot (grammatica dei grafici, concisa) e agli Inputs. Tutta la preparazione dati resta Python.

### 7.2 I tre punti da verificare con uno smoke test, prima di impegnarsi

Lo stack è la scelta giusta ma ha tre incognite reali. Vanno risolte su un comune prima di costruire qualunque interfaccia — nell'ordine, e ognuna è mezza giornata al massimo.

**(a) Query a runtime, non a build time.** I *data loader* di Observable Framework girano alla build e producono file statici: è il modello opposto a quello che serve, dove le query nascono dai filtri dell'utente. Il pattern corretto è tenere il Parquet come risorsa statica e interrogarlo con DuckDB-WASM a runtime. Funziona, ma è meno documentato del percorso standard del Framework. **Test**: caricare `pop.parquet` di Modena, eseguire un `GROUP BY` filtrato, misurare il tempo al primo risultato e al secondo.

**(b) Range request e potatura delle colonne.** Il guadagno di DuckDB-WASM dipende dal fatto che scarichi solo le colonne e i row group necessari. Va confermato che accada davvero con `read_parquet` su URL, e non che scarichi l'intero file al primo accesso. **Test**: pannello di rete del browser, query su due colonne, verificare che il traffico sia molto minore della dimensione del file.

**(c) Costo del primo caricamento.** Il modulo WASM di DuckDB pesa decine di MB. Sommato al Parquet, il primo ingresso potrebbe essere sgradevole. **Mitigazione già prevista**: `agg_sezioni.parquet` copre la vista d'ingresso senza toccare la popolazione, e DuckDB si carica in modo pigro al primo filtro. **Test**: misurare il tempo alla prima schermata utile.

Se (a) o (b) fallissero, il ripiego non è cambiare stack ma cambiare granularità: precalcolare gli aggregati per un insieme chiuso di filtri, perdendo il filtro arbitrario. Vale la pena saperlo prima, non dopo.

### 7.3 Cosa costa zero adesso e molto dopo

La destinazione è interna, quindi il bundle è completo e nulla è oscurato. Tre accorgimenti costano zero ora e sono un refactor doloroso dopo:

1. **interruttore `--pubblico` in `build_bundle.py`**, che rimuove `via` e `civico` e aggancia i punti al centroide dell'edificio. Va scritto ora anche se non si userà: dopo significherebbe rifare l'export e ricontrollare tutto;
2. **etichettatura**: banner permanente «individuo sintetico», watermark nelle esportazioni PNG, campo di provenienza in ogni CSV esportato. Sono tre righe adesso;
3. **nessuna dipendenza da servizi con chiave API** (mappa inclusa), altrimenti la pubblicazione richiederebbe un account e una chiave da proteggere.

Il motivo per cui insisto sul primo: ogni individuo sintetico sta a un civico ANNCSU esistente, e su Brescia il contesto Caffaro rende la cosa meno teorica che altrove.

---

## 8. Estensibilità

**Principio**: aggiungere una città non deve toccare il codice dell'interfaccia. Tutto ciò che varia sta in `manifest.json`, generato da `G.COMUNI`.

Il manifest dichiara per ogni comune: codice, nome, slug, regione, pool AVQ regionale, livello ASC in uso e sua etichetta leggibile, numero di zone, tier del paese, attributi presenti, riferimenti (§3.3) e numeri di qualità. L'interfaccia si costruisce da lì: se un comune non ha `zona` (San Vito dei Normanni), i controlli spaziali di zona non compaiono.

**Procedura per una città nuova**, dopo la §12 del riferimento:

```
build_bundle.py {CODICE}      # parquet + topojson + voce di manifest
verifica_bundle.py {CODICE}   # controlli
```

I controlli conviene definirli adesso, perché sono il presidio contro l'errore che si ripete: totali coincidenti col censimento; **campo `nomi_verificati: [metodo_a, metodo_b]` obbligatorio** nel manifest, altrimenti il bundle non si costruisce; poligoni in numero pari alle zone attese; nessun individuo fuori dal poligono comunale; copertura AVQ nelle fasce attese; `donor_id` presente e riuso coerente.

**Emilia-Romagna.** Con Parma, Bologna e Modena fatti, i prerequisiti regionali (shapefile R08, indirizzario ANNCSU, `Dati_regionali_2023`, `join_civici_sezioni`) sono già pagati: ogni capoluogo aggiuntivo costa la mezz'ora di §12. Piacenza, Reggio Emilia, Ferrara, Ravenna, Forlì, Cesena, Rimini portano la regione a dieci comuni e ~1,8 milioni di individui — dimensione ancora comoda, un comune alla volta nel browser.

Questo suggerisce una **sesta vista, regionale**: la mappa dell'ER coi comuni coperti, e il confronto di livello B esteso a tutti. Con dieci città la decomposizione tra/dentro su dieci partizioni di taglia diversa diventa una figura che oggi non esiste in nessun paper. Non è un obiettivo di v1, ma la struttura del bundle la prevede già (`regioni/emilia_romagna.topojson`, chiave `regione` nel manifest).

---

## 9. Prestazioni attese

| operazione | atteso |
|---|---|
| prima schermata utile (aggregati precalcolati) | < 1 s |
| primo filtro (carica DuckDB-WASM + colonne) | 2–5 s |
| aggregazione filtrata successiva, 390k righe | 20–80 ms |
| ridisegno dei marginali | < 100 ms |
| coropleta per sezione, 2.224 poligoni | < 100 ms |
| punti, 50k | 60 fps |

Il vincolo non è il calcolo ma il primo trasferimento, ed è esattamente ciò che misurano i test di §7.2.

---

## 10. Fasi

**F1 — smoke test dello stack.** I tre test di §7.2 su Modena (il comune più piccolo: 184.597 individui, `|X|` = 645.120). Nessuna interfaccia, nessun design. Solo: DuckDB-WASM interroga un Parquet remoto in modo efficiente, sì o no. È la fase che decide se il resto del documento è realizzabile come scritto.

**F2 — bundle.** `build_bundle.py` su un comune, con `donor_id` e `cella_avq` aggiunti a monte in `assign_avq.py`. Verifica dei numeri contro il riferimento v1.6. **Rischio principale**: se `donor_id` non è recuperabile senza rilanciare `assign_avq`, va saputo ora.

**F3 — Esplora, senza mappa.** Filtri, marginali a due serie, modalità Δ, scomposizione compositiva. Un comune. È il nucleo: se questa parte funziona ed è leggibile, il resto è lavoro noto. Qui si decidono tipografia, badge e palette.

**F4 — mappa.** Le quattro modalità, le metriche, shrinkage, affiancamento sintetico/reale, selezione spaziale, crossfilter completo.

**F5 — le altre città e il manifest.** L'estensibilità va provata aggiungendo il quarto comune senza toccare l'interfaccia: se serve toccarla, il design del manifest è sbagliato ed è meglio scoprirlo qui.

**F6 — Individuo, Metodo, Confronta**, e la grafica in senso proprio.

---

## 11. Questioni aperte

1. **Il nome** (§12).
2. **`donor_id`**: recuperabile dai file esistenti, o richiede di rilanciare `assign_avq.py` sui quattro comuni? Blocca F2 e metà del design dell'onestà statistica.
3. **AVQ filtrabili**: solo mostrate in v1, o filtrabili dietro interruttore con avviso?
4. **Emilia-Romagna**: quanti capoluoghi nei prossimi mesi, e la vista regionale entra o resta predisposta e vuota?
5. **Modena e i 37 rioni** (§8 del riferimento): se entrassero in pipeline, la vista Zone di Modena passerebbe da inutile a interessante. Non è una decisione del viewer, ma il viewer è l'argomento più forte per prenderla.

---

## 12. Il nome — candidati

| nome | perché | rischio |
|---|---|---|
| **Stato delle Anime** | è il nome storico del censimento parrocchiale italiano: il registro delle anime di una comunità. Qui le anime sono sintetiche. Colto, italiano, memorabile, e regala tutta l'estetica (§6) | «anime» da solo collide con l'animazione giapponese nelle ricerche; va usato per esteso |
| **Microstato** | fisica-nativo: la popolazione è *un* microstato compatibile con i vincoli macroscopici. Coerente col framing MaxEnt del workshop di settembre | opaco per un pubblico non fisico |
| **Sosia** | ogni individuo è il doppio statistico di nessuno in particolare. Breve, italiano, un po' inquietante nel modo giusto | poco descrittivo |
| **Atlante GSP** | sobrio, funziona in inglese (*GSP Atlas*), zero ambiguità | anonimo |
| **Specula** | latino: specchio e torre d'osservazione insieme | criptico |
