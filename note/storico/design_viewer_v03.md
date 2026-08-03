# Viewer delle popolazioni sintetiche GSP — documento di design

**v0.3 — 29 luglio 2026 — nessun codice, solo design**
Riferimento dati: `GSP_popolazioni_full_riferimento_v16.md` (§ citati sotto).

*Rispetto alla v0.2: riscritte §3.3 e §4.2 — il riferimento è unico ma valutato
al livello spaziale del filtro, con tre stati e due marcatori. Corretta §4.3, dove
il confronto sulla mappa era presentato come validazione ed è verifica. Aggiunti
due diagnostici in §4.6. Chiusa la questione `P30–P45`/`P67–P82`.*

---

## 0. Decisioni prese

| | scelta | conseguenza principale |
|---|---|---|
| **stack** | Observable Framework + DuckDB-WASM, applicazione statica | nessuna riscrittura per la versione in rete; il JavaScript si limita a Plot e Inputs |
| **destinazione** | solo interna per ora | bundle completo con indirizzi; nessun deploy; interruttore `--pubblico` predisposto e non usato |
| **riferimento** | una sola serie, valutata al livello spaziale del filtro | §3.3 — niente algebra generale delle tavole, tre livelli e una regola di ricaduta |

**Ancora aperto**: il nome (§12).

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
| **C — condizionato** | contorno | `paese`, `area` | vincolato ai margini censuari, con struttura geografica secondo il tier; su Modena, tier 0: nessuna struttura geografica |
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
      rif_comune.parquet         # riferimento livello 0  (§3.3)
      rif_zona.parquet           # riferimento livello 1
      rif_sezione.parquet        # riferimento livello 2
      sezioni.topojson           # 1.822 poligoni semplificati
      zone.topojson              # 33 poligoni (dissolve) + nomi verificati
    034027/ 037006/ 036023/ ...
  regioni/
    emilia_romagna.topojson      # confini comunali, per la futura vista regionale
```

**Perché Parquet**: le 40 colonne sono quasi tutte categoriche a bassa cardinalità; con dictionary encoding un comune sta in 8–20 MB contro i ~90 MB del CSV. Il motore legge **solo le colonne coinvolte nella query**, che è la differenza fra 40 ms e 4 s.

**Un accorgimento che conta**: ordinare le righe per `sezione` prima di scrivere, con row group di ~50k righe. Le statistiche min/max di row group permettono di saltare interi blocchi per qualunque filtro spaziale, che è il filtro più frequente.

**Il bundle sta fuori dal repo.** 60–80 MB per quattro comuni non vanno in git. Il repo contiene codice, schema del manifest e lo script di build; il bundle si ricostruisce in un comando.

### 3.2 Colonne aggiunte dall'export

| colonna | perché |
|---|---|
| `id` | stabile, per i permalink all'individuo |
| `donor_id` | numerosità efficace delle AVQ (§2). **Se non esiste, va tracciata in `assign_avq.py`** |
| `cella_avq` | la cella di condizionamento usata e il livello di collasso: rende ispezionabile l'assunzione (6) |
| `macroeta`, `istr4` | le variabili su cui *davvero* girano le AVQ, esplicitate |
| `quinq` | classe quinquennale derivata da `eta_anni`, per il confronto di §4.6 |
| `lon_j`, `lat_j` | coordinate con jitter deterministico entro il civico (§4.3) |

`cella_avq` è l'unica colonna che rende visibile *quanto* il collasso gerarchico è intervenuto. Una sottopopolazione in cui il 60% degli individui ha ricevuto le AVQ al terzo livello di collasso è molto meno informativa di una in cui tutti stanno al livello pieno, e oggi la differenza è invisibile.

### 3.3 Il riferimento — una serie, tre livelli, tre stati

**Regola del livello.** Una sola serie di riferimento, valutata al livello spaziale più fine compatibile col filtro attivo. Nessuna algebra generale delle tavole: tre livelli e una ricaduta.

| filtro attivo | riferimento |
|---|---|
| nessuno, o solo attributi non spaziali | `rif_comune` — censimento comunale |
| un quartiere o un insieme di zone | `rif_zona` — tavole di zona (`zona_2023/`: z1..z4, z6) + fonti comunali dove esistono |
| una selezione di sezioni | `rif_sezione` — `P1`, `ST1`, `ST16/19`, `ST25–ST30`, `P30–P45`/`P67–P82` |
| zona ∧ attributi assenti dalla tavola di zona | ricaduta a `rif_comune`, **dichiarata nel pannello** |

**Regola dello stato.** Ogni coppia (attributo × livello) sta in uno di tre stati, e il pannello lo mostra come badge:

| stato | significato | come si legge lo scarto |
|---|---|---|
| **verifica** | il valore reale a quel livello **è entrato nella pipeline** (constraint set, o peso di allocazione) | accordo garantito a ~4·10⁻⁴. Uno scarto non è un risultato: è un bug |
| **validazione esterna** | il valore reale esiste a quel livello e **non è stato usato** | lo scarto è informativo, con la propria linea di base |
| **assente** | nessun dato osservato a quel livello | il pannello lo dichiara e ricade al livello superiore |

Lo stato **non si mantiene a mano**: `constraints_2024/manifest.json` dichiara già fonte e tipo (hard/soft) di ogni blocco, e `enrich.py` dichiara le colonne usate come pesi di allocazione. `build_bundle.py` deriva la classificazione da lì e la scrive nel manifest. Una fonte sola, nessuna divergenza possibile.

**Dov'è la validazione esterna, in concreto.** Solo in un posto, ma è quello che serviva:

- **fonti comunali anagrafiche di zona.** Non sono mai state usate come *livelli*: il condizionale tier ne prende la **forma** come seed, con i margini presi dal censimento (§6 del riferimento). Confrontare i loro livelli col sintetico è quindi un test genuino. Sono i numeri di §10: Modena 0,982–1,007 sulla popolazione per quartiere; Primo Maggio (Brescia) 0,329 contro 0,293, rapporto 1,12; Bologna 0,214 contro 0,213 sulla quota UE fra stranieri. **Linea di base dichiarata: 1–2% di scarto atteso fra anagrafe e censimento**, date diverse. Uno scarto del 12% è sopra la linea di base e vuol dire qualcosa;
- disponibilità: popolazione per zona ovunque il portale la pubblichi (Modena sì, ed è tier 0); `paese × zona` su Brescia (tier 1) e Bologna (tier 2); `Cittad × SEZ21` su Parma (tier 3).

**Dove la validazione esterna *non* c'è, e va detto.** A livello di sezione **tutto l'osservato è usato**. `P30–P45` (maschi) e `P67–P82` (femmine) sono i conteggi per sesso e classe quinquennale, e non sono un dato accessorio: sono **il peso stesso** con cui l'anello 3 assegna la sezione,

```
w(σ) = ( Σ_{k∈e} P_{s,k}(σ) ) × [ q_{s,e3}(σ) se straniero, 1−q_{s,e3}(σ) se italiano ]
```

e poi, scelta la sezione, determinano il quinquennio dentro il bin. Insieme a `P1`, `ST1` e le `ST` di area, esauriscono l'osservato di sezione. **Non esiste quindi alcun test out-of-sample dell'assunzione (8)**: il dato per farlo non c'è, che è esattamente il motivo per cui l'assunzione è dichiarata. Il pannello a livello di sezione sta sempre in stato *verifica*.

Un caso torbido da non spacciare per pulito: su Parma `ETA × SEZ21` dai microdati è marcato «mai usato per generare», ma la stessa quantità rientra dall'altra porta come `P30–P45`/`P67–P82` censuari. Il confronto misura in buona parte lo scarto anagrafe–censimento, non l'errore del modello. Si tiene, con l'ipotesi nulla dichiarata sporca.

**Le tre sorgenti non spaziali**, invariate dalla v0.2:

- **censimento comunale** per tutto l'anello 1, `paese`, `area`;
- **ISTAT età singola** per `eta_anni` (la stessa distribuzione dell'assunzione 9);
- **AVQ regionale pesata** per le 21 variabili di classe D, con intervallo di confidenza. Non esiste un riferimento comunale per queste, e fingere il contrario sarebbe peggio che non averlo. La marginale sintetica comunale e la stima regionale differiscono **esattamente per composizione demografica**, quindi la riga di scomposizione di §4.2 spiega lo scarto per intero, sempre: una verifica gratuita che gira su ogni pannello.

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

**Barra di stato**, sempre visibile: `n` selezionati · % della città · `n_eff` donatori · sezioni toccate · **livello del riferimento attivo** · badge rosso se `n < 200` o `n_eff < 30`.

Ogni filtro attivo è una pillola rimovibile; lo stato completo sta nell'URL (§5).

### 4.2 Marginali

Per ogni attributo mostrabile un pannello, in griglia di small multiples, con i primi sei fissabili.

**Una serie sintetica, fino a due marcatori di riferimento:**

| elemento | resa |
|---|---|
| **sintetico** | `p̂(a \| F)`, barre piene, colore d'accento |
| **riferimento censuario** | rombo **pieno**, neutro scuro — stato *verifica* |
| **riferimento comunale** | rombo **vuoto**, neutro scuro — stato *validazione esterna*, dove esiste |

I due marcatori non vanno letti allo stesso modo, ed è questo il punto: sul rombo pieno lo scarto atteso è zero e ogni deviazione è un guasto; sul rombo vuoto lo scarto atteso è l'1–2% dello sfasamento anagrafe–censimento, e ciò che eccede è segnale. Il badge di stato accanto al titolo del pannello dice quale dei due si sta guardando; passandoci sopra, la provenienza per esteso.

**Senza filtro spaziale la lettura resta quella della v0.2**: poiché la popolazione non filtrata riproduce il censimento a 4·10⁻⁴, il riferimento comunale è anche il valore atteso sotto indipendenza fra attributo mostrato e filtro, quindi lo scarto *è* l'associazione. Con filtro spaziale il riferimento si sposta al livello della zona e la lettura diventa un confronto quartiere-per-quartiere. Sono due usi dello stesso pannello e vanno etichettati, o si confondono.

**Modalità Δ.** Un interruttore trasforma le barre in scarti dal riferimento, con banda di campionamento `√(p(1−p)/n)` — e `n_eff` per le variabili di classe D. Su 300 individui una differenza di 3 punti percentuali non è niente.

**Riga di scomposizione** (classi C e D):

```
AMBIENTE, Fiumicello vs riferimento:  Δ = −0,07
   spiegato dalla composizione (sesso × macroetà × istr4):  −0,07  (100%)
   residuo areale:                                           0,00
```

Per le classi C e D il residuo è **zero per costruzione**. Per la classe V è l'errore del modello, ~10⁻⁴.

**Tipi di grafico**: nominali → barre orizzontali ordinate per frequenza; ordinali (`eta`, `istruzione`, `SALUTE`, `BMI`, `CPESO`) → barre in ordine naturale, mai riordinate; 0–10 (`PUNTIFI*`, `VOTOUSL`) → istogramma + media con IC su `n_eff`; continue (`MH`, `eta_anni`) → densità + quantili.

**Pannello dedicato alla fiducia istituzionale**: dodici medie su un asse comune 0–10, ordinate, con i riferimenti nazionali AVQ 2024 come tacche fisse (vigili del fuoco 8,10 · forze dell'ordine 6,70 · ASL 6,34 · Comune 5,13 · Regione 4,65) e le fasce di copertura (86–88% / 42–43% / 15–20%) come tratteggio sulle variabili interessate. Sotto, opzionale, la matrice di correlazione con `min_periods`, che riproduce la struttura a due fattori (servizi vs politica).

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

Con quota e lift serve **shrinkage empirico-bayesiano** verso la media comunale, o almeno lo sbiadimento delle sezioni sotto ~30 individui filtrati.

**Affiancamento sintetico/reale, e cos'è davvero.** Per `P1`, `ST1`, le `ST` di area e le quinquennali il dato di sezione c'è, e l'affiancamento a scala condivisa è quasi gratis. Ma — correzione rispetto alla v0.2 — **è verifica, non validazione**: quelle colonne sono i pesi dell'allocazione, quindi l'accordo è costruito. Resta la resa visiva del MAE di §10, che vale più della tabella, e il modo più rapido di individuare una sezione che si è rotta. Va etichettato come tale, con il badge *verifica*, o suggerisce una convalida che non c'è.

Sulle **zone** invece l'affiancamento con la fonte comunale è validazione vera, ed è lì che la mappa dice qualcosa di nuovo: dove il sintetico si discosta dall'anagrafe più della linea di base dell'1–2%.

**Dettagli che vanno gestiti o si vedono subito:**

- le **convivenze** (50–630 per comune) stanno al centroide della zona: senza trattamento producono una torre di punti coincidenti. Escluse dai punti per default, con conteggio dichiarato;
- `indirizzo_fonte = "zona"` (36–278 individui): stesso trattamento;
- più individui per civico: jitter radiale deterministico (funzione dell'`id`, stabile fra sessioni) con raggio ~8 m;
- **base cartografica senza chiavi API**: tiles Protomaps `.pmtiles` self-hosted, oppure CARTO Positron.

**Doppio strato**: base grigia (campione della popolazione totale) + strato colorato (il filtro), per distinguere «qui non ce ne sono» da «qui non c'è nessuno».

**Selezione spaziale**: lazo e clic su poligono aggiungono un filtro. Da mappa a filtro e ritorno senza passare dai menu.

**Campionamento**: tetto a 50k punti con frazione dichiarata in interfaccia; oltre, passaggio automatico a esagoni.

### 4.4 Individuo

La carta d'identità di un individuo sintetico, dal clic su un punto o dal pulsante *estrai un individuo a caso*.

Quaranta campi raggruppati per anello, **ciascuno col proprio badge di garanzia**, e per le AVQ la cella di condizionamento e il livello di collasso. In fondo, la catena di provenienza:

```
Individuo 017029-0084213      [INDIVIDUO SINTETICO — non esiste]
  anello 1   MaxEnt, cella (zona 17029012, F, 35-49, coniugata, ITL, diploma, occupata)
  anello 2   paese: Italia · AVQ dal donatore #3117, cella (F, 35-49, istr4=3), livello pieno
  anello 3   sezione 017029000412 (peso P38+P39) · quinquennio 35-39 · via ... 19A
```

Due ragioni oltre alla bellezza. È lo strumento di debug più efficace che esista, perché rende visibile tutta la pipeline su un caso — inclusa, ora, la colonna `P` che ha determinato la sezione. Ed **è già il prompt della persona** per il tier 2: una vista «come l'agente LLM vede questo individuo» collega il viewer al lavoro SimComm senza costruire niente di nuovo.

### 4.5 Confronta

Tre livelli di rigore decrescente e dichiarato.

**Livello A — comune (sicuro).** Marginali comunali affiancati, una colonna per città, più la tabella-carta d'identità di §10.

**Livello B — distribuzione fra sezioni (il livello giusto).** Non si confrontano le zone ma le **distribuzioni di indicatori a livello di sezione**: quota stranieri, quota laureati, quota over-65. Le sezioni sono unità ISTAT di disegno omogeneo, confrontabili fra città in un modo in cui 4 quartieri di Modena e 33 di Brescia non sono. ECDF sovrapposte o ridgeline. Accanto, la decomposizione della varianza di §10 in forma grafica: il rapporto *tra/dentro* che cresce monotonamente con la taglia media delle zone (5,9× → 43,5×) è **l'argomento visivo** per cui la sezione conta più della zona.

**Livello C — zone (con avviso).** Mappe affiancate, scale sincronizzate, avviso non silenziabile: partizioni non confrontabili.

**Avviso obbligatorio sulle AVQ.** Parma, Bologna e Modena condividono lo **stesso pool di 4.629 donatori emiliani**: qualunque differenza AVQ fra le tre è integralmente compositiva. Brescia attinge a un pool diverso (8.111, Lombardia), quindi un confronto Brescia–Bologna mescola composizione e differenza di pool regionale, che sono cose diverse.

### 4.6 Metodo e qualità

La pagina che rende l'app difendibile.

- **Validazione**: MRE(α>0) per comune; MAE per sezione e correlazioni (§10) come scatter osservato–sintetico, più convincente di qualunque numero;
- **Copertura AVQ**: le tre fasce, copertura effettiva per variabile e comune, nota sul *planned missing*;
- **Riuso dei donatori**: istogramma, col tetto strutturale (99,7–100% del pool usato) dichiarato;
- **Le sette assunzioni** di §7 in elenco cliccabile: cliccando la (8) si illuminano gli attributi che ne dipendono, ovunque nell'app;
- **Tier del paese** per comune, coi numeri di §6 (2,08–2,57 volte l'ipotesi nulla a livello di quartiere; 1,01–1,04 a livello di sezione, cioè nulla, correttamente);
- **Provenienza dei nomi di zona**: la verifica su due assi (§3.2), con l'incidente di Bologna raccontato.

**Due diagnostici nuovi**, entrambi una query sola sul `_full`, entrambi sullo stesso punto di cucitura — il taglio a nove anni, che viene dall'universo dell'istruzione ISTAT (`P83` = «9 anni e più») e non dalla griglia quinquennale.

**(a) Il seam quinquennale.** Sei bin su otto del constraint set coincidono con gruppi di quinquennali; i due infantili no, e stanno insieme per

```
0-8   = <5      +  4/5 di 5-9
9-14  = 1/5 di 5-9  +  10-14
```

sotto uniformità entro il quinquennio. Poiché `eta_anni` è esatta, si riaggrega il sintetico ai sedici quinquennali e lo si confronta con `P{30+k}` / `P{67+k}` per sezione. Dà un MAE molto più fine di quello sui totali (0,74–1,58), e soprattutto **localizzato**: se l'errore si concentra su `P31` / `P68` — la classe 5–9 — l'assunzione di uniformità sta cedendo, presumibilmente dove ci sono molte famiglie giovani. Resa: mappa del residuo per sezione, più un profilo per classe quinquennale. Resta uno stato *verifica* (le colonne sono usate), ma è la verifica alla risoluzione massima che i dati permettono, e l'unica che può isolare un'assunzione con nome e cognome.

**(b) Coerenza fra età esatta e istruzione.** L'istruzione è assegnata al livello del bin con soglie minime di conseguimento (`elementare` 10, `media` 13, `diploma` 18, `laurea_o_its` 20, `post_laurea` 22); `eta_anni` è assegnata dopo, nell'anello 3, e nulla le lega. Dentro il bin `9-14` può quindi uscire un individuo con `istruzione = media` ed `eta_anni = 10`, che è impossibile. Non è un bug: è una conseguenza dell'ordine delle assegnazioni. Ma è misurabile — quanti individui portano un titolo irraggiungibile alla loro età esatta, e dove — e sospetto sia lo stesso fenomeno di «resta sovrastimata `media` nel bin `9-14`» visto dall'altro lato. Resa: conteggio e quota per comune, tabella `istruzione × eta_anni` con le celle impossibili evidenziate, e la stessa quota come metrica di mappa.

Se (b) dà un numero non trascurabile è materiale per §7 del documento di riferimento, e forse per una riga nel paper.

---

## 5. Interazione e stato

**Crossfilter completo**: cliccare una barra aggiunge il filtro corrispondente; disegnare sulla mappa aggiunge un filtro spaziale; entrambi si riflettono nelle pillole e nell'URL.

**Stato nell'URL**, interamente:

```
/esplora/017029?zona=17029012,17029015&sesso=F&istruzione=laurea_o_its
               &mostra=AMBIENTE,PUNTIFI10&mappa=sezioni&metrica=lift
```

Vale da solo lo sforzo: mandare una vista a Tarantino in una riga, citare una figura in un paper con un link riproducibile, ricostruire in un secondo lo stato in cui hai visto qualcosa di strano. Funziona anche in locale.

**Esportazioni** con provenienza incorporata: PNG/SVG del pannello, CSV dei marginali (con riferimento, stato e badge di classe), permalink, GeoJSON degli aggregati per sezione.

---

## 6. Grafica

**Estetica dell'anagrafe.** Il riferimento visivo è il registro amministrativo — tabelle a colonne strette, cifre allineate, timbri — reso in modo contemporaneo, non nostalgico.

- **tipografia**: un serif con carattere per titoli e numeri grandi; un sans neutro per l'interfaccia; **un monospaziato per tutte le cifre**, con cifre tabulari. La coerenza dei numeri è il 70% dell'impressione di rigore;
- **colore**: fondo caldo quasi bianco; **un solo accento** per il sintetico; i riferimenti sempre in neutro scuro, mai colorati, distinti per *forma* (rombo pieno vs vuoto) e non per tinta — così la distinzione verifica/validazione sopravvive alla stampa in bianco e nero. Divergente sobria per il lift, sequenziale monocroma per le quote. Palette verificata per daltonismo;
- **badge di garanzia** come piccoli timbri, con forma oltre che colore (pieno / mezzo / contorno / tratteggiato);
- **densità alta**: small multiples piccoli e numerosi, nello stile delle tavole statistiche;
- **mappa**: base chiara desaturata per le coropleti, base scura solo per i punti;
- **movimento**: transizioni brevi sui cambi di filtro, così si percepisce *cosa* è cambiato. Nient'altro si muove.

Observable Framework ha un tema di default decente: la personalizzazione passa da un foglio di stile che ridefinisce le variabili CSS del tema. La grafica in senso proprio va fatta in F6, ma tipografia, badge e palette vanno decisi in F3 o si riscrive.

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

### 7.2 I tre punti da verificare con uno smoke test, prima di impegnarsi

**(a) Query a runtime, non a build time.** I *data loader* di Observable Framework girano alla build e producono file statici: è il modello opposto a quello che serve. Il pattern corretto è tenere il Parquet come risorsa statica e interrogarlo con DuckDB-WASM a runtime — funziona, ma è meno documentato del percorso standard. **Test**: caricare `pop.parquet` di Modena, eseguire un `GROUP BY` filtrato, misurare il tempo al primo e al secondo risultato.

**(b) Range request e potatura delle colonne.** Il guadagno dipende dal fatto che scarichi solo le colonne e i row group necessari. **Test**: pannello di rete, query su due colonne, verificare che il traffico sia molto minore del file.

**(c) Costo del primo caricamento.** Il modulo WASM di DuckDB pesa decine di MB. **Mitigazione già prevista**: `agg_sezioni.parquet` copre la vista d'ingresso senza toccare la popolazione, e DuckDB si carica pigramente al primo filtro. **Test**: tempo alla prima schermata utile.

Se (a) o (b) fallissero, il ripiego non è cambiare stack ma cambiare granularità: precalcolare gli aggregati per un insieme chiuso di filtri, perdendo il filtro arbitrario.

### 7.3 Cosa costa zero adesso e molto dopo

1. **interruttore `--pubblico` in `build_bundle.py`**, che rimuove `via` e `civico` e aggancia i punti al centroide dell'edificio. Va scritto ora anche se non si userà;
2. **etichettatura**: banner permanente «individuo sintetico», watermark nelle esportazioni PNG, campo di provenienza in ogni CSV;
3. **nessuna dipendenza da servizi con chiave API**, mappa inclusa.

Ogni individuo sintetico sta a un civico ANNCSU esistente, e su Brescia il contesto Caffaro rende la prima cosa meno teorica che altrove.

---

## 8. Estensibilità

**Principio**: aggiungere una città non deve toccare il codice dell'interfaccia. Tutto ciò che varia sta in `manifest.json`, generato da `G.COMUNI`.

Il manifest dichiara per ogni comune: codice, nome, slug, regione, pool AVQ regionale, livello ASC in uso e sua etichetta, numero di zone, tier del paese, attributi presenti, **riferimenti per livello con il rispettivo stato** (§3.3) e numeri di qualità. L'interfaccia si costruisce da lì: se un comune non ha `zona` (San Vito dei Normanni), i controlli spaziali di zona non compaiono; se non ha fonte comunale di zona (Modena, tier 0), il rombo vuoto non compare per il paese ma compare per la popolazione.

**Procedura per una città nuova**, dopo la §12 del riferimento:

```
build_bundle.py {CODICE}      # parquet + topojson + riferimenti + voce di manifest
verifica_bundle.py {CODICE}   # controlli
```

Controlli: totali coincidenti col censimento; **campo `nomi_verificati: [metodo_a, metodo_b]` obbligatorio**, altrimenti il bundle non si costruisce; poligoni in numero pari alle zone attese; nessun individuo fuori dal poligono comunale; copertura AVQ nelle fasce attese; `donor_id` presente e riuso coerente; stato di ogni riferimento derivato e non scritto a mano.

**Emilia-Romagna.** Con Parma, Bologna e Modena fatti, i prerequisiti regionali sono già pagati: ogni capoluogo aggiuntivo costa la mezz'ora di §12. Piacenza, Reggio Emilia, Ferrara, Ravenna, Forlì, Cesena, Rimini portano la regione a dieci comuni e ~1,8 milioni di individui.

Questo suggerisce una **sesta vista, regionale**: la mappa dell'ER coi comuni coperti e il confronto di livello B esteso a tutti. Con dieci città la decomposizione tra/dentro su dieci partizioni di taglia diversa diventa una figura che oggi non esiste in nessun paper. Non è un obiettivo di v1, ma la struttura del bundle la prevede già.

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

Il vincolo non è il calcolo ma il primo trasferimento, ed è ciò che misurano i test di §7.2.

---

## 10. Fasi

**F0 — i due diagnostici** (§4.6). Sono query sul `_full` che non richiedono né bundle né interfaccia, e il loro esito cambia cosa va messo nella pagina Metodo. Mezza giornata, e si può fare subito.

**F1 — smoke test dello stack.** I tre test di §7.2 su Modena (184.597 individui, `|X|` = 645.120). Decide se il resto del documento è realizzabile come scritto.

**F2 — bundle.** `build_bundle.py` su un comune, con `donor_id`, `cella_avq` e `quinq`, e i tre file di riferimento con lo stato derivato. Verifica contro il riferimento v1.6. **Rischio principale**: se `donor_id` non è recuperabile senza rilanciare `assign_avq`, va saputo ora.

**F3 — Esplora, senza mappa.** Filtri, marginali, regola del livello, tre stati, modalità Δ, scomposizione compositiva. Un comune. Qui si decidono tipografia, badge e palette.

**F4 — mappa.** Le quattro modalità, le metriche, shrinkage, affiancamento (verifica su sezione, validazione su zona), selezione spaziale, crossfilter completo.

**F5 — le altre città e il manifest.** L'estensibilità va provata aggiungendo il quarto comune senza toccare l'interfaccia.

**F6 — Individuo, Metodo, Confronta**, e la grafica in senso proprio.

---

## 11. Questioni aperte

1. **Il nome** (§12).
2. **`donor_id`**: recuperabile dai file esistenti, o richiede di rilanciare `assign_avq.py` sui quattro comuni? Blocca F2. Se va rilanciato, conviene aggiungere nello stesso passaggio anche `cella_avq` e il livello di collasso.
3. **AVQ filtrabili**: solo mostrate in v1, o filtrabili dietro interruttore con avviso?
4. **Fonti comunali di zona**: quali sono effettivamente disponibili come *livelli* per i quattro comuni, oltre a quelle già usate come seed? Determina quanti rombi vuoti compaiono, cioè quanta validazione esterna l'app può offrire.
5. **Emilia-Romagna**: quanti capoluoghi nei prossimi mesi, e la vista regionale entra o resta predisposta e vuota?
6. **Modena e i 37 rioni** (§8 del riferimento): se entrassero in pipeline, la vista Zone di Modena passerebbe da inutile a interessante.

---

## 12. Il nome — candidati

| nome | perché | rischio |
|---|---|---|
| **Stato delle Anime** | è il nome storico del censimento parrocchiale italiano: il registro delle anime di una comunità. Qui le anime sono sintetiche. Colto, italiano, memorabile, e regala tutta l'estetica di §6 | «anime» da solo collide con l'animazione giapponese nelle ricerche; va usato per esteso |
| **Microstato** | fisica-nativo: la popolazione è *un* microstato compatibile con i vincoli macroscopici. Coerente col framing MaxEnt del workshop di settembre | opaco per un pubblico non fisico |
| **Sosia** | ogni individuo è il doppio statistico di nessuno in particolare | poco descrittivo |
| **Atlante GSP** | sobrio, funziona in inglese (*GSP Atlas*), zero ambiguità | anonimo |
| **Specula** | latino: specchio e torre d'osservazione insieme | criptico |
| ~~Albo Pretorio~~ | bella parola, ma nomina l'oggetto sbagliato: l'albo pretorio pubblica *atti*, non registra persone. Su un progetto che vuole collaborare con le amministrazioni, l'errore di categoria si nota | **riservato**: è il nome giusto per il corpus di comunicazioni istituzionali di SimComm/Caffaro — ordinanze comunali, materiali ATS/ARPA — dove sarebbe esatto invece che suggestivo |
