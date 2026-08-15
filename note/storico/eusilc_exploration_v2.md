# EU-SILC Public Use Explorer

**Versione 0.2 — 5 agosto 2026**

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

## Dataset utilizzato

Public Use File italiano.

Download effettuato automaticamente dal notebook Colab.

Il notebook registra SHA256 e dimensione del file scaricato.

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

Sono presenti quattro file.

| file | livello | record |
|------|----------|-------:|
| D | household register | 18.487 |
| H | household data | 18.487 |
| R | personal register | 43.489 |
| P | personal data | 37.209 |

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

---

# 7. Esperimenti completati

✓ download automatico

✓ verifica dell'integrità del file

✓ estrazione dell'archivio

✓ inventario dei file

✓ identificazione della struttura D/H/R/P

✓ identificazione delle chiavi household

✓ identificazione delle chiavi persona

✓ individuazione della prima anomalia strutturale

---

# 8. Domande aperte

1. Perché RB030 non è univoco nel Public Use File?

2. La differenza

```
43.489 − 37.209 = 6.280
```

è interamente spiegata dall'universo del questionario individuale?

3. Quale variabile identifica la persona di riferimento della famiglia?

4. Esiste una variabile che codifica direttamente la relazione di
parentela?

5. Quali variabili household devono essere propagate ai membri della
famiglia durante la costruzione della popolazione sintetica?

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

Successivamente verrà costruito un inventario sistematico delle
variabili individuali e familiari rilevanti per la generazione della
popolazione sintetica.

---

# Changelog

## Versione 0.2

- aggiunta caratterizzazione quantitativa dei quattro file;
- formalizzata la procedura di identificazione delle chiavi;
- documentata la prima anomalia osservata;
- introdotte le decisioni progettuali D001–D003;
- introdotta la sezione "Domande aperte";
- separati i risultati osservati dagli obiettivi iniziali.
