# EU-SILC Public Use Explorer

**Versione 0.3 — 11 agosto 2026**

Esplorazione del **Public Use File (PUF)** italiano di EU-SILC
(European Union Statistics on Income and Living Conditions).

Questo documento registra in modo riproducibile:

- sorgenti utilizzate;
- struttura del dataset;
- risultati dell'esplorazione;
- decisioni progettuali;
- anomalie osservate;
- codice essenziale.

Il Public Use File è utilizzato esclusivamente per:

1. comprendere la struttura dei dati;
2. sviluppare la pipeline software;
3. preparare la richiesta dei Scientific Use Files (SUF);
4. preparare successivamente l'utilizzo dei Microdati per la Ricerca (MFR).

Il PUF **non viene utilizzato per alcuna inferenza statistica**, poiché
Eurostat dichiara esplicitamente che si tratta di dati sintetici.

---

# 0. Esito in breve (v0.3)

La domanda che ha motivato questa esplorazione era se EU-SILC potesse
fornire ciò che nessuna altra fonte disponibile dà: **la struttura
familiare con età esatte**, per calibrare e validare l'anello 4
(`nota_repertorio_avq_v3.md`).

| | esito |
|---|---|
| le variabili di parentela **esistono** nel SUF | ✔ §10 |
| sono **cross-sezionali**, non longitudinali | ✔ §10 |
| sono **assenti dal PUF**, rimosse per riservatezza | ✔ §10 |
| **conseguenza**: il parser non è collaudabile prima del SUF | §10.3 |
| le variabili per l'**uso narrativo** ci sono tutte nel PUF | ✔ §11 |

I due usi di EU-SILC si separano quindi nettamente, e vanno pesati
diversamente:

- **struttura familiare**: bloccata sul PUF, il codice si scrive al buio;
- **variabili di famiglia** (deprivazione, abitazione, reddito): il PUF
  serve esattamente come previsto, e si può procedere.

---

# 1. Sorgenti

## Eurostat

European Union Statistics on Income and Living Conditions (EU-SILC)

Public Use Files

https://ec.europa.eu/eurostat/web/microdata/public-microdata/statistics-on-income-and-living-conditions

La documentazione Eurostat specifica che i Public Use Files

- sono completamente sintetici;
- mantengono struttura, formato e nomi delle variabili dei Scientific Use Files;
- sono destinati allo sviluppo del codice;
- non devono essere utilizzati per analisi statistiche della popolazione.

> **La seconda affermazione è inesatta**, e §10 lo documenta: tre
> variabili del file R presenti nel SUF non compaiono nel PUF.

## Documentazione delle variabili

`SILC065 operation 2013 VERSION MAY 2013.pdf`, linkato dal disclaimer
Eurostat, conservato in `data/eu-silc/`. È il documento che definisce le
variabili target, e la fonte di §10.

## Dataset utilizzato

`IT_PUF_EUSILC.zip`, scompattato in `data/eu-silc/puf/`.

> **Dieci annate, non una.** L'archivio contiene i quattro file per ogni
> anno dal **2004 al 2013**: quaranta CSV, nominati
> `IT_{anno}{lettera}_EUSILC.csv` con la lettera **minuscola**.
> Le cifre di §3 si riferiscono alla sola annata **2013**.
>
> *Trappola da tenere presente prima di impilare le annate*: EU-SILC è
> longitudinale a rotazione, e le stesse famiglie ricompaiono per quattro
> anni consecutivi. Impilare senza deduplicare creerebbe famiglie
> duplicate — la stessa trappola di `PROFAM` che ripartiva da 1 ogni anno
> nell'AVQ (v22 §13.5), su un'altra fonte.

Formato: CSV separato da virgola. **Senza flag**: il disclaimer avverte
che i flag `_F` sono omessi perché non hanno interpretazione su dati
simulati. Sul SUF ci saranno, e diranno se un valore è osservato,
imputato o mancante — inclusi i flag dei puntatori di parentela.

---

# 2. Obiettivo

L'obiettivo dell'esplorazione è identificare

- struttura dei file;
- identificativi;
- relazioni household-person;
- struttura delle famiglie;
- copertura delle variabili;
- anomalie del Public Use File.

L'obiettivo non è produrre statistiche sull'Italia.

---

# 3. Struttura osservata

Annata 2013. Sono presenti quattro file.

| file | livello | record | colonne |
|------|----------|-------:|-------:|
| D | household register | 18.487 | 6 |
| H | household data | 18.487 | ~80 |
| R | personal register | 43.489 | **25** |
| P | personal data | 37.209 | ~90 |

Interpretazione osservata

- D contiene una riga per famiglia.
- H contiene una riga per famiglia.
- R contiene tutti i componenti delle famiglie.
- P contiene soltanto il sottoinsieme degli individui appartenenti
  all'universo del questionario personale.

La differenza

```
R − P = 6.280 individui
```

sarà verificata mediante le variabili di età.

---

# 4. Identificazione delle chiavi

Le chiavi sono state individuate empiricamente tramite

1. ricerca automatica delle variabili 030/040/050;
2. verifica della cardinalità;
3. confronto fra i file.

## Household

| file | variabile |
|------|-----------|
| D | DB030 |
| H | HB030 |
| R | RX030 |
| P | PX030 |

Osservazioni

- DB030 è univoca.
- HB030 è univoca.
- RX030 coincide con la famiglia di appartenenza dei record individuali.
- PX030 coincide con la famiglia di appartenenza dei record individuali del file P.

### Decisione D001

Per tutte le elaborazioni successive

```
household_id = RX030
```

oppure

```
household_id = PX030
```

a seconda del file.

## Persona

| file | variabile |
|------|-----------|
| R | RB030 |
| P | PB030 |

PB030 risulta univoca.

RB030 presenta almeno un duplicato reale.

---

# 5. Prima anomalia osservata

È stato individuato almeno un identificativo personale duplicato nel file R.

| RB030 | RX030 | RB080 | RB090 |
|-------|-------|------:|------:|
| 3564621 | 356462 | 1971 | 1 |
| 3564621 | 356462 | 2010 | 2 |

Le due osservazioni

- appartengono alla stessa famiglia;
- hanno anno di nascita differente;
- hanno sesso differente.

Non rappresentano quindi la stessa persona.

L'anomalia interessa almeno due record su 43.489.

Poiché il Public Use File è sintetico, non è possibile stabilire se
l'anomalia derivi dalla procedura di sintesi oppure da un difetto del
dataset.

L'anomalia viene trattata come proprietà del Public Use File e non di
EU-SILC.

RB030 non è univoco nel PUF. Per il join R–P viene usata una chiave composita costituita da identificativo personale sorgente, anno di nascita e sesso. Una chiave tecnica di riga resta comunque necessaria come identificativo interno univoco.

## 5.1 Una conseguenza sui puntatori — *aggiunta v0.3*

`person_key` (D002) risolve l'identità delle **righe**. Ma le variabili di
parentela del SUF (§10) contengono l'**identificativo sorgente**, cioè
proprio `RB030`: un puntatore verso `3564621` non dice a quale delle due
persone si riferisca.

> Sul SUF la prima misura da fare, prima di costruire qualunque grafo, è
> **quanti puntatori sono ambigui**. Se sono pochi si escludono e si
> documenta; se sono molti il grafo non è ricostruibile e va capito
> perché. Il controllo è già scritto in `eusilc_grafo.py`.

Sul PUF il problema non si pone, perché i puntatori non ci sono.

---

### Decisione D002

RB030 non viene utilizzato come identificativo personale interno.

Per tutte le elaborazioni viene introdotta una chiave tecnica

```
person_key
```

costruita come

```
RB030 + indice di riga
```

RB030 viene comunque conservato come identificativo sorgente.

---

### Decisione D003

Nessuna anomalia del Public Use File viene corretta modificando i dati.

Le anomalie vengono invece

- documentate;
- isolate;
- gestite mediante chiavi tecniche.

---

### Decisione D004 — *v0.3*

**Sul PUF si sviluppa e si collauda il codice; i numeri non si usano
mai**, nemmeno come ordine di grandezza.

Il disclaimer Eurostat è più stretto di quanto la formula «dati
sintetici» suggerisca:

> *With these data it is not possible to make generalised statements
> about individual characteristics **or relationships between different
> personal or household characteristics**.*

Le **relazioni fra caratteristiche** sono escluse esplicitamente. Quindi
un divario d'età calcolato sul PUF non è «una stima imprecisa»: è
precisamente la classe di cose che Eurostat dichiara non inferibili.

*Ne segue una conseguenza sul disegno dei test.* Un test del software che
confronti un valore del PUF con un valore atteso — «il divario
generazionale esce 33 come nell'AVQ, quindi il parser funziona» — è
**ambiguo**: se esce 12, può essere un bug oppure la sintesi che non
preserva quella relazione, e i due casi non si distinguono.

I test devono perciò essere **strutturali e non distribuzionali**:

- quanti puntatori si risolvono verso un membro esistente della stessa
  famiglia (test del parser, indipendente dal realismo dei valori);
- quante famiglie hanno esattamente un riferimento derivabile;
- quante violano invarianti logiche (un figlio più vecchio del genitore).

Un test distribuzionale può accompagnarli, ma etichettato come
secondario.

---

# 6. Codice essenziale

Ricerca automatica delle chiavi

```python
ID_PAT = re.compile(r"(030|040|050)$")
```

Costruzione della chiave tecnica

```python
r["person_key"] = (
    r["RB030"].astype("string")
    + "__row_"
    + r.index.astype(str)
)
```

Individuazione dei file, annata per annata — i nomi sono minuscoli:

```python
m = re.search(r"_(\d{4})([dhrp])_", os.path.basename(f))
```

---

# 7. Esperimenti completati

✓ download automatico

✓ verifica dell'integrità del file

✓ estrazione dell'archivio

✓ inventario dei file — **dieci annate, 2004–2013**

✓ identificazione della struttura D/H/R/P

✓ identificazione delle chiavi household

✓ identificazione delle chiavi persona

✓ individuazione della prima anomalia strutturale

✓ **inventario delle colonne dei quattro file** (v0.3)

✓ **verifica della presenza delle variabili di parentela** (v0.3, §10)

---

# 8. Domande aperte

1. Perché RB030 non è univoco nel Public Use File?

2. La differenza

```
43.489 − 37.209 = 6.280
```

è interamente spiegata dall'universo del questionario individuale?
*Verificabile: `RB080` dà l'anno di nascita e `RB010` l'anno
dell'indagine. Il controllo è in `eusilc_grafo.py`.*

3. Quale variabile identifica la persona di riferimento della famiglia?
**→ nessuna.** Vedi §10.2: EU-SILC non designa un riferimento, a
differenza di `RELPAR` nell'AVQ e nei microdati di Parma. Il riferimento
va **derivato** dal grafo, per convenzione dichiarata.

4. Esiste una variabile che codifica direttamente la relazione di
parentela? **→ RISPOSTA IN §10.** Non una relazione: tre **puntatori**,
presenti nel SUF e assenti dal PUF.

5. Quali variabili household devono essere propagate ai membri della
famiglia durante la costruzione della popolazione sintetica?
*→ §11 elenca cosa c'è; la scelta di quali usare è una decisione
successiva.*

6. *(nuova)* Le dieci annate si possono impilare, o la rotazione
longitudinale le rende dipendenti? §1.

---

# 9. Prossimo passo

Ricostruire la struttura gerarchica

```
Household
    ├── membri
    ├── persona di riferimento
    ├── partner
    ├── figli
    └── altri componenti
```

utilizzando esclusivamente gli identificativi e le relazioni contenute
nei file.

> **Bloccato sul PUF** (§10.3). Il codice è scritto
> (`scripts/diagnostica/eusilc_grafo.py`) ma non collaudabile: le
> variabili da cui la gerarchia si ricostruisce non ci sono.
>
> Resta praticabile una via parziale: §10.4, i partner impliciti.

---

# 10. Le variabili di parentela — *sezione nuova, v0.3*

## 10.1 Esistono, e sono cross-sezionali

Da `SILC065 operation 2013`, file R:

| variabile | contenuto | pagina |
|---|---|---:|
| `RB220` | Father ID | 144 |
| `RB230` | Mother ID | 145 |
| `RB240` | Spouse/partner ID | 146 |

Tutte e tre classificate:

> *BASIC DATA (Demographic data) — **Cross-sectional and longitudinal** —
> Reference period: current — Unit: all*

Quindi **non** sono variabili della sola componente longitudinale:
appartengono anche alla cross-sezionale, che è quella del nostro PUF.

E la nota del documento è esplicita sullo scopo:

> *The variable RB220 as well as variable RB230 have been included in
> EU-SILC **in order to calculate the household composition**.*

Sono lì apposta per ricostruire la struttura familiare — esattamente il
nostro caso d'uso. `RB220` e `RB230` includono padre e madre
adottivi, affidatari e acquisiti.

Le stesse informazioni esistono anche nel file P (`PB160`, `PB170`,
`PB180`), ma **per il nostro uso serve R**: il file P copre solo gli
individui dell'universo del questionario personale (16+), e il divario
generazionale richiede i minori.

## 10.2 EU-SILC non designa una persona di riferimento

Non c'è l'equivalente di `RELPAR` = 1. La codifica è un **grafo di
puntatori**, non una relazione con un riferimento.

*È più ricca*, perché da un grafo si derivano relazioni che `RELPAR` non
distingue — fratelli pieni contro fratellastri, nuclei multipli nella
stessa famiglia — ma richiede una **convenzione** per scegliere il
riferimento, e la convenzione va dichiarata perché influenza i ruoli
derivati. `eusilc_grafo.py` usa: chi non ha genitori in famiglia, con più
legami, il più anziano a parità.

## 10.3 Sono assenti dal PUF

Il file R del PUF 2013 ha **25 colonne**, e non contiene `RB220`,
`RB230`, `RB240`. Il file P non contiene `PB160`, `PB170`, `PB180`.

> Sono state **rimosse per riservatezza**: i puntatori di parentela
> permettono di ricostruire la composizione familiare esatta, che è
> identificante. Coerente con la finalità del PUF, ma rende inesatta
> l'affermazione del disclaimer secondo cui *«the data structure of the
> public microdata is the same as in the microdata for research»*.

**Conseguenza pratica**: il parser dei puntatori si può scrivere ma non
provare. È il contrario di ciò che il PUF dovrebbe permettere, ed è il
motivo per cui `eusilc_grafo.py` resta codice non collaudato finché non
arriva il SUF.

## 10.4 Una via parziale: i partner impliciti

Il file P del PUF contiene `PB190` (stato civile) e `PB200` (situazione
di convivenza, che dice **se** la persona convive con un partner ma non
**chi** sia), più `PX200` fra le derivate.

Nelle famiglie con **esattamente due persone di sesso opposto, entrambe
con partner**, l'accoppiamento è implicito: sono l'unico caso in cui il
divario d'età fra partner si ricava senza puntatori. Corrispondono alla
firma `RP` del repertorio.

Su ~18.500 famiglie ne verranno fuori qualche migliaio. Non tutti i
partner, ma abbastanza per una distribuzione — che però resta **un
numero del PUF**, quindi sintetico (D004). Vale come sviluppo del
codice, non come misura.

---

# 11. Le variabili per l'uso narrativo — *sezione nuova, v0.3*

Questa parte del piano **non è bloccata**: le variabili ci sono tutte nel
PUF, e il codice si può scrivere e collaudare adesso.

## 11.1 Cosa c'è nel file H (famiglia)

| blocco | contenuto |
|---|---|
| `HS011`–`HS190` | **deprivazione materiale**: arretrati su mutuo, affitto e bollette; capacità di sostenere una spesa imprevista; una settimana di vacanza; un pasto adeguato ogni due giorni; riscaldare adeguatamente casa; arrivare a fine mese |
| `HH010`–`HH091` | **abitazione**: tipo, titolo di godimento, stanze, servizi |
| `HD080`–`HD240` | privazioni su beni durevoli e attività sociali |
| `HY010`–`HY170` | redditi, lordi e netti, in dettaglio |
| `HX010`–`HX120` | derivate |

## 11.2 Cosa c'è nel file P (individuo)

`PH010`–`PH070` salute percepita e accesso alle cure; `PE010`–`PE040`
istruzione; `PL` condizione professionale; `PD020`–`PD090` deprivazione
personale.

## 11.3 La geografia c'è, ed è la regione

`DB040` nel file D. Stessa risoluzione dell'AVQ: utile per condizionare
Emilia-Romagna e Lombardia separatamente, inutile sotto la regione.

*Nota sulla numerosità*: ~18.500 famiglie italiane per annata, che su
venti regioni fanno qualche centinaio per regione — **meno dell'AVQ**
per le nostre due. EU-SILC non è migliore dell'AVQ in numerosità; è
migliore in **risoluzione** (età esatte, puntatori di parentela) e in
**copertura tematica** (le variabili di §11, che l'AVQ non ha).

## 11.4 Come si userebbe

Come **hot-deck a livello di nucleo**: si dona il blocco di variabili
familiari al nucleo intero, condizionato su ampiezza, firma, età e
istruzione del riferimento, regione. È la stessa architettura
dell'anello 2, con l'unità cambiata da individuo a nucleo — possibile
solo ora che `id_nucleo` esiste.

Risolverebbe di traverso un limite noto: le AVQ dentro il nucleo sono
scorrelate mentre ρ ≈ 0,6 dice che in famiglia le opinioni si
condividono (v22 §13.5). Variabili donate *per nucleo* sarebbero
correlate per costruzione.

## 11.5 Il reddito: attributo del nucleo, non fatto sulla famiglia

Il reddito è nella lista delle categorie vietate per le biografie
(`nota_biografia_v2`), e il motivo è che non abbiamo dati che lo
sostengano sul singolo caso.

EU-SILC lo darebbe condizionato su regione, ampiezza e istruzione — ma
un reddito familiare così stimato ha un'incertezza enorme sul singolo
nucleo, e messo in una scheda individuo **sembra** un dato quando è una
lotteria condizionata.

> La distinzione utile è fra usarlo come **attributo del nucleo**
> (aggregabile, con incertezza dichiarata) e come **fatto sulla singola
> famiglia** (che non è). La prima cosa è legittima, la seconda no.

**La deprivazione materiale è preferibile al reddito** per l'uso
narrativo, e non come ripiego: è una batteria di sì/no già in forma
qualitativa — «non può permettersi una settimana di vacanza», «ha
difficoltà ad arrivare a fine mese» — e cattura la condizione vissuta
invece del flusso monetario. Entrerebbe al livello **C** della
tassonomia delle biografie, come i tratti caratteriali: plausibile e non
verificabile, mai `misurato`.

> *Un rischio da tenere presente per SimComm e Caffaro.* La condizione
> economica è potenzialmente **causale** sulla risposta a una
> comunicazione di rischio. Se un agente risponde diversamente perché il
> suo prompt dice che fatica ad arrivare a fine mese, quell'effetto è
> generato da un attributo che abbiamo assegnato condizionatamente. Nella
> biografia va bene; in un esperimento che misura effetti, quella
> variabile va trattata come parte dello **strumento**, non del mondo —
> la stessa distinzione che SIVE fa fra controllabilità e validità
> esterna.

---

# 12. Cosa serve dal SUF — *sezione nuova, v0.3*

Argomento per la richiesta, in ordine di forza.

**(1) La validazione dell'anello 4 a livello di nucleo.** Nessuna fonte
disponibile permette di rispondere a «due persone che stanno insieme
nella realtà finiscono insieme nel sintetico?»: i microdati di Parma
hanno la geografia ma nessun identificativo di famiglia, l'AVQ ha i
nuclei ma non la geografia. EU-SILC SUF ha nuclei interi con età esatte.

**(2) Il divario d'età fra partner.** Oggi `PARTNER_MAX_DIFF = 15` è
**convenzionale**: le classi `ETAMi` dell'AVQ sono larghe 5–10 anni e
restituiscono mediana 0, che significa «stessa classe» e non «stessa
età». Parma ha l'età esatta ma nessun identificativo di famiglia.

**(3) I limiti del genitore convivente.** `GENITORE_MIN`/`MAX` sono presi
per analogia dal divario generazionale rovesciato: la misura diretta
sull'AVQ ha n=175 con il 45% nella classe aperta 75+. È il parametro più
debole del repertorio, e `G fuori dai limiti` è il secondo ripiego per
frequenza in tutti gli undici comuni.

**(4) Le variabili di §11**, che il PUF già mostra ma non permette di
stimare.

*Un limite che il SUF non risolve*: il 18–24% di coniugati senza coppia
(`nota_repertorio_avq_v3` §7.4) è una proprietà della popolazione in
ingresso — il constraint set non impone la parità — e nessuna
calibrazione dei parametri lo tocca.

---

# Changelog

## Versione 0.3

- aggiunto §0, esito in breve;
- **§10, le variabili di parentela**: esistono nel SUF, sono
  cross-sezionali, sono assenti dal PUF. La domanda aperta 4 ha risposta;
- **§11, le variabili per l'uso narrativo**: presenti nel PUF, questa
  parte del piano non è bloccata;
- **§12, cosa serve dal SUF**, come argomento per la richiesta;
- aggiunta la decisione **D004** sulla disciplina dei test: strutturali e
  non distribuzionali, perché il disclaimer esclude esplicitamente le
  relazioni fra caratteristiche;
- §5.1: l'anomalia di `RB030` ha una conseguenza sui puntatori del SUF;
- §1: l'archivio contiene **dieci annate** (2004–2013), non una, con la
  trappola della rotazione longitudinale;
- §3: aggiunto il numero di colonne per file;
- domande aperte 3 e 4 risposte, aggiunta la 6.

## Versione 0.2

- aggiunta caratterizzazione quantitativa dei quattro file;
- formalizzata la procedura di identificazione delle chiavi;
- documentata la prima anomalia osservata;
- introdotte le decisioni progettuali D001–D003;
- introdotta la sezione "Domande aperte";
- separati i risultati osservati dagli obiettivi iniziali.
