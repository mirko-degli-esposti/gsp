# Il campione dei giovani diplomati — diagnostica per l'esperimento sui priors

**nota_campione_diplomati_v1 — 20 agosto 2026**

Diagnostica pre-disegno per l'esperimento sulla calibrazione dei priors
LLM nella scelta post-diploma. Strumenti:
`scripts/diagnostica/campione_diplomati.py` (estrazione e misure),
`scripts/diagnostica/tabella_campione.py` (tavole A-D). Comuni: Parma,
Bologna, Brescia; finestra d'eta' 19-22; popolazioni `report-v1.0-rc1`
con anello 4.

La domanda a cui la diagnostica doveva rispondere: **il campione che
serve al disegno esiste, e con quali proprieta'?** Risposta: esiste —
5.137 candidati F, 36 celle, 35 con n≥10 — e ogni sua proprieta' anomala
e' stata o spiegata meccanicamente o ricondotta a un difetto ora
identificato. Due ritrattazioni, tre certificati, due meccanismi capiti,
un artefatto di mappa corretto.

---

## 1. Le due ritrattazioni

### 1.1 La regione dei titoli dettagliati — *misurato, corretto*

`titolo_agente` aveva `regione="ITD5"` come default e **nessun chiamante
la passava**: tutti i titoli dettagliati mai generati per Brescia
(schede, biografie, `indovina_citta`) pescavano dai pesi
dell'Emilia-Romagna. Perimetro verificato con grep su `src/`, `scripts/`
e sul notebook SIVE: quattro chiamanti, tutti col difetto;
**`sive_harness.ipynb` non consuma la derivazione — l'esperimento JASSS
e' fuori perimetro per costruzione.** Nessun file e' contaminato: il
titolo non e' mai stato archiviato, per costruzione (piano di
trattamento §5). Le demo passate non sono riproducibili col codice
corretto.

L'effetto, misurato (bin 15-24):

| livello | M | F |
|---|---|---|
| TVD alle foglie (32) | 0,063 | 0,096 |
| TVD alle classi di disegno (diploma3, mappa v1) | 0,037 | 0,026 |
| null campionario fra comuni a pesi identici (n≈2.500) | 0,033 | 0,029 |

La formulazione corretta — che sostituisce una prima versione
sovrageneralizzata («sovrarappresentava i licei») — e':
**distorsione di composizione fino a ~2-3 punti per classe, con verso
diverso per sesso** (licei depressi negli uomini: 0,317 ITC4 contro
0,297 ITD5; professionali depressi nelle donne: 0,242 contro 0,216),
piu' un artefatto di etichettatura sulla filiera artistica (§4) che
mascherava parte dell'effetto femminile. Alle classi di disegno
l'effetto e' della stessa grandezza del rumore campionario: la
correzione e' reale, doverosa, e invisibile a valle — visibile solo
nella colonna `altro`.

Correzione (`patch_titolo_regione`, applicata 20/8): firma
`titolo_agente(..., comune=None, regione=None)` con risoluzione dal
raccordo `NUTS_CENS2011` (attenzione permanente: il censimento 2011 usa
i codici NUTS **pre-2010** — l'Emilia-Romagna e' ITD5, non ITH5);
`regione` senza default; `eta=None` solleva invece di scivolare su
`Y_GE6` (la piramide intera si chiede con `eta="tutte"`); repertorio
ordinato per `chiave` prima dell'estrazione (decisione [D]: le revisioni
future dei pesi rimescolano localmente, non globalmente — costo: un
rimescolamento una tantum dei titoli, nessun file toccato, nomi immuni
per canale separato).

### 1.2 «`eta_anni` presa in maniera uniforme» — *refutato, in meglio e in peggio*

La dichiarazione a memoria era «uniforme nel bin». Il codice
(`enrich.assegna_eta`) fa di meglio: **sezione → quinquennio (pesi
censuari per sezione) → anno singolo (anagrafe SDMX comunale per
sesso)**. Ma il secondo stadio e' rotto.

- **Primo stadio validato**: la massa per quinquennio del sintetico
  combacia con l'anagrafe (15-19: 0,490 contro 0,486).
- **Secondo stadio**: l'anagrafe e' liscia (scarti del 3-4% fra anni
  contigui; M 15-24: 0,104 · 0,095 · 0,093 · 0,093 · 0,097 · 0,093 ·
  0,096 · 0,107 · 0,106 · 0,118), il sintetico e' seghettato con salti
  del 65-100% (16: 0,121 contro 17: 0,073; 23-24: 0,137 contro 21:
  0,070). Il caricatore e' pulito (niente totali: 196.924 al netto dei
  filtri, stati civili tutti reali).

**Meccanismo identificato**: `largest_remainder` con pesi *identici in
ogni blocco* (`eta_w` comunale) su blocchi da 2-6 individui. I resti
frazionari sono gli stessi numeri in migliaia di blocchi, `argsort`
produce la stessa permutazione, e le eta' vincitrici a ogni valore di
`c` sono sempre le stesse: gli errori di arrotondamento non si
compensano, si accumulano. Con pesi quasi uguali chi vince non lo decide
il peso ma lo spareggio — **la forma sintetica riproduce la regola di
spareggio, non la fonte** (il pattern non segue l'ordinamento dei pesi:
verificato).

> **Principio.** Il largest remainder con quote costanti fra blocchi
> piccoli non riproduce la distribuzione: riproduce la propria regola di
> spareggio. E' il duale del principio del pavimento — l'allocatore va
> confrontato col proprio comportamento a quote piatte. La preferenza
> per il largest remainder (enumerazione, non campionamento; fattore ~6
> sul MAE) resta giusta dove le sue condizioni valgono: quote variabili
> fra blocchi, n decente. Al secondo stadio cadono entrambe.

**Correzione definita, non applicata**: al secondo stadio,
`rng.choice(anni, size=c, p=pw/pw.sum())` al posto del blocco largest
remainder (l'`rng` e' gia' in firma). Si perde la riproduzione esatta
per blocco — che a n=3 non esisteva — e la media su ~1.300 sezioni
ricostruisce la fonte. **Nel prossimo ciclo di rigenerazione, insieme
alle 26 esclusioni α=0.** Verifica post-correzione gia' pronta: il
marginale della diagnostica contro le righe M/F dell'anagrafe.

Previsione falsificabile, se serve conferma: la seghettatura deve
variare fra comuni ma essere **identica rigenerando Parma con altro
seme** — l'rng in quel punto non decide nulla.

Effetto sull'esperimento: cosmetico. L'eta' nel prompt e' quella del
record, coerente col resto della scheda; la distorsione e' di
composizione fine dentro i quinquenni, ortogonale agli assi di disegno.

---

## 2. I tre certificati — *misurato*

**(a) `diploma3` e' piatta rispetto a `condizione`, per costruzione e
per misura.** TVD(P(diploma3|studente), P(diploma3)) su Parma 19-20:
osservata 0,012, pavimento 0,011, **netto 0,0009**. Il titolo
dettagliato e' condizionato su istruzione × sesso × coorte, non sulla
condizione: chi legge la tavola C deve sapere che la piattezza e' il
certificato della costruzione, non un risultato sulla popolazione.

**(b) Scambiabilita' di `eta_anni` nel bin** (v2: contro il marginale
empirico, pavimento a permutazione; la v1 confrontava col piatto e
misurava la forma, non la selezione). Netti massimi su Parma:
istruzione **+0,016**, condizione **+0,031**, ruolo **+0,085**.
L'ordinamento riproduce i meccanismi: `assembla` legge `eta_anni`
direttamente (ruolo), gli altri due la vedono solo attraverso la
composizione quinquennale delle sezioni. Lezione a margine: «scambiabile
per costruzione» vale solo **condizionatamente alle variabili che la
costruzione condiziona** — la condizione e' assegnata per zona, l'eta'
per sezione, e il canale sezione passa.

**(c) Neutralita' della selezione-F, sui tre comuni, finestra 19-22.**
TVD(P(var|F), P(var)): condizione 0,004-0,011, diploma3 0,004-0,014,
eta_anni 0,037-0,054. Le prime due sotto il pavimento pratico; la terza
e' spiegata e innocua — gli F sono la coda giovane del bin (i figli),
R e P quella vecchia; l'eta' nel prompt resta quella vera per record.
**Campionare solo F non seleziona nulla di misurabile sugli assi di
disegno.**

---

## 3. La struttura dei ruoli a 19-22 anni — *capita, strutturale*

A 19-20 anni: F 54,7%, R 24,2%, P 17,3% (Parma). Nella realta' ~90% dei
19-20enni vive coi genitori. **Non e' un difetto dell'assemblaggio**: i
P sono celibi/nubili al 99,6% (263/264) — non e' la coda dei coniugati —
e gli slot di convivente e intestatario, definiti alla risoluzione del
bin 15-24, sono riempiti indifferentemente da 19enni e 24enni.
E' la stessa famiglia dei *coniugati incoerenti*: **proprieta'
strutturale della risoluzione a bin, non dell'algoritmo**, che lavora
bene alla risoluzione che il dato possiede.

Composizione spiegata per intero: F e' il ritratto del marginale
(52,5% donne a Parma, contro marginale ~50%); P e' femmina al **95,1%**
(la firma dell'accoppiamento: partner donna di intestatario piu'
vecchio, ereditata dall'AVQ) — e l'eccesso di liceali fra i P (45,6%) e'
interamente mediato dal sesso; R e' maschio al 69,1% (coerente con
M1/M2: il sesso pesa sul ruolo, non sull'ampiezza). Il residuo d'eta'
dei P (72,6% a 19) passa dal divario convenzionale ±15 che `assembla`
applica leggendo `eta_anni`.

Dichiarazione per l'esperimento: *il 45-56% di non-F e' la struttura
media del bin, esclusa per costruzione dal campione; la selezione e'
certificata neutra (§2c).*

---

## 4. La mappa `diploma3` — *convenzione dichiarata*

Collasso delle 32 foglie della maturita' su
liceo / tecnico / professionale / altro, per parola chiave
sull'etichetta **censuaria** (stabile rispetto alla resa di
`titolo_leggibile`), priorita' professionale > tecnico > liceo.

**Correzione v2 (20/8)**: la filiera artistica va tutta in `altro`.
L'Emilia etichetta «istruzione di II grado artistica» (→ altro nella
v1), la Lombardia «liceo artistico» (→ liceo nella v1): stessa filiera,
due ordinamenti, due classi — un artefatto da ~1-1,5 punti nei confronti
fra comuni, che tra l'altro mascherava parte dell'effetto regionale
femminile (§1.1). Post-correzione la colonna `altro` si allinea
(3,3-4,0%) e lo scarto sul liceo Parma-Brescia si allarga a 2 punti nel
verso dei pesi ITC4.

**`altro` (3,8% pooled) e' escluso dal disegno**: filiera artistica
pre-riforma e residuali non mappano sulle classi MUR.

**Vintage 2011, permanente**: i pesi sono censuari 2011, bin 15-24 non
traslato. La licealizzazione 2011→2023 (44%→~57% degli iscritti) rende
la marginale sintetica (37,6% licei) **mai confrontabile col reale**.
Innocuo per il disegno (le celle condizionano su diploma3; i confronti
MUR sono *dentro* ciascun tipo), letale se dimenticato.

---

## 5. Il campione — *misurato* (tavole complete: `tabella_campione.py`)

| | Parma | Bologna | Brescia | pooled |
|---|---:|---:|---:|---:|
| diplomati 19-22 | 2.781 | 5.678 | 2.542 | 11.001 |
| F (candidati) | 1.384 | 2.493 | 1.260 | **5.137** |
| F con ≥1 genitore | 100% | 100% | 100% | 100% |
| donne | 52,5% | 47,7% | 46,7% | 48,7% |
| stranieri | 17,8% | 17,4% | 21,0% | 18,4% |
| gen3 laurea+ | 48,8% | 58,4% | 44,4% | 52,4% |
| quota studente | 69,2% | 66,5% | 64,6% | 66,8% |

Bologna ha F al 43,9% (citta' universitaria: piu' R e P giovani) contro
~50% degli altri — previsto e innocuo, vista §2c. La quota studente
**varia fra citta'** (69,2 / 66,5 / 64,6): il benchmark interno non e'
piatto, e il comune entra nel disegno come covariata con un dato di
confronto reale. Divari genitore-figlio: mediana 33, q10-q90 [22,42] —
plausibili.

> **Avvertenza costitutiva su `gen3`, ora quantificata.** L'assemblaggio
> non vede l'istruzione: i titoli dei due genitori sono indipendenti fra
> loro e dal figlio. Il massimo di due estrazioni indipendenti gonfia
> `laurea+` al 52,4% — l'accoppiamento assortativo reale comprimerebbe
> quel massimo verso il ~25-30% osservato nelle indagini. **La cella
> gen3 esiste e si campiona; la sua marginale non e' quella della
> popolazione e non va mai letta come tale.** Per la calibrazione dei
> priors e' irrilevante: al modello serve vedere la cella, non la sua
> frequenza.

**Le celle del disegno**: diploma3(3) × gen3(3, `assenti` esclusa) ×
sesso(2) × background ita/straniero(2) = **36 celle**; 35 con n≥10,
31 con n≥20; minima 7 (tecnico × bassa × F × straniera — rara anche nel
reale), mediana 77, massima 498.

---

## 6. Il disegno che ne esce — *proposto, da fissare*

- **Campione**: 12 agenti per cella dove disponibili, tutte le unita'
  sotto; campionamento dentro-cella proporzionale ai comuni → **~430
  agenti**.
- **Item**: scelta a quattro (universita' / ITS / lavoro-ricerca /
  altro) + probabilita' 0-100 di iscriversi. Il continuo copre il
  rischio di mutismo categoriale gia' visto (GPT e Haiku al 98-100% su
  una modalita' in SIVE-Brescia) e da' la calibrazione.
- **Repliche**: 3 semi per agente (pavimento di rumore, come a
  Brescia).
- **Modelli**: DeepSeek + GPT-4o-mini + Haiku — aggancio diretto al
  risultato SIVE sui priors categoriali (presenti solo in DeepSeek).
  ≈ 430 × 3 × 3 ≈ 3.900 chiamate.
- **Benchmark**: interno — quota studente per cella/comune (quantita'
  DI BIN: dichiarare la finestra 19-22, mai confrontare col tasso di
  passaggio immediato); esterno — MUR/ANS per tipo di diploma, sesso,
  cittadinanza; AlmaDiploma per l'istruzione dei genitori.
- **Misura**: logit sulle risposte LLM e stesso logit sul dato reale,
  confronto dei coefficienti — la mappa di *dove* i priors sono
  calibrati (ipotesi da registrare prima dei dati: tipo di diploma
  sovrappesato, genitori sottopesati).

---

## 7. Aperto

- **(a)** Correzioni nel prossimo ciclo di rigenerazione: largest
  remainder di secondo stadio in `assegna_eta` (§1.2) + 26 esclusioni
  α=0. Con verifica marginale-contro-anagrafe.
- **(b)** Il prompt: cosa dell'F entra nel profilo (titolo dei genitori
  si'; condizione dei genitori? fratelli?), formulazione dell'item che
  non suggerisca la risposta, data «luglio, maturita' appena fatta».
  Prossima decisione.
- **(c)** Coerenza del titolo del genitore donatore AVQ con
  l'`istruzione` di anello 1: mai testata (sollevata 20/8, non
  bloccante per il disegno — gen3 usa l'istruzione di anello 1, non
  quella del donatore).
- **(d)** La verifica per rigenerazione con altro seme della
  seghettatura (§1.2): conferma definitiva del meccanismo, se mai
  servisse.
- **(e)** Estensione ad altri comuni della finestra: il pooled regge
  gia'; Modena/Reggio aggiungerebbero celle straniere.
