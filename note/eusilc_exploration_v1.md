# EU-SILC Public Use Explorer

**Versione 0.1 — 5 agosto 2026**

Esplorazione del **Public Use File (PUF)** italiano di EU-SILC
(European Union Statistics on Income and Living Conditions).

Questo documento registra in modo riproducibile:

- sorgenti utilizzate;
- struttura del dataset;
- esperimenti svolti;
- decisioni progettuali;
- anomalie osservate;
- codice essenziale.

L'obiettivo **non** è analizzare la popolazione italiana.

Il Public Use File è infatti **interamente sintetico** e viene utilizzato
esclusivamente per:

1. comprendere la struttura dei dati;
2. sviluppare la pipeline software;
3. preparare la futura richiesta dei **Scientific Use Files (SUF)** e,
   successivamente, dei **Microdati per la Ricerca (MFR)**.

---

# 1. Sorgenti

## Eurostat

Public microdata

European Union Statistics on Income and Living Conditions (EU-SILC)

https://ec.europa.eu/eurostat/web/microdata/public-microdata/statistics-on-income-and-living-conditions

La documentazione Eurostat specifica che i Public Use Files:

- sono completamente sintetici;
- mantengono struttura, nomi delle variabili e formato dei Scientific Use Files;
- sono destinati allo sviluppo del codice e all'esplorazione della survey;
- non devono essere utilizzati per inferenza statistica.

## Dataset utilizzato

Public Use File italiano

(download effettuato automaticamente dal notebook Colab)

SHA256 registrato durante il download.

---

# 2. Obiettivo dell'esplorazione

Prima della richiesta dei SUF vogliamo verificare:

- struttura D/H/R/P;
- identificativi;
- relazioni household-person;
- possibilità di join;
- struttura delle famiglie;
- copertura delle variabili.

L'intera pipeline dovrà funzionare sul PUF senza modifiche sostanziali
quando verrà sostituito con il SUF.

---

# 3. Struttura individuata

Sono presenti quattro file principali.

| file | livello |
|------|----------|
| D | household register |
| H | household data |
| R | personal register |
| P | personal data |

Cardinalità osservate

| file | record |
|------|--------|
| D | 18 487 |
| H | 18 487 |
| R | 43 489 |
| P | 37 209 |

Interpretazione

- D e H contengono una riga per famiglia.
- R contiene tutti i componenti delle famiglie.
- P contiene solo il sottoinsieme delle persone appartenenti
  all'universo del questionario individuale.

---

# 4. Identificazione delle chiavi

## Household

Identificativi osservati

| file | variabile |
|------|-----------|
| D | DB030 |
| H | HB030 |
| R | RX030 |
| P | PX030 |

Le cardinalità risultano coerenti.

DB030 e HB030 sono biiettivi.

RX030 e PX030 identificano la famiglia di appartenenza
dell'individuo.

### Decisione D001

Per tutte le elaborazioni successive

```
household_id = RX030
```

per i file individuali.

---

## Persona

Variabili candidate

| file | variabile |
|------|-----------|
| R | RB030 |
| P | PB030 |

PB030 risulta univoco.

RB030 presenta invece una anomalia.

---

# 5. Anomalia osservata

È stato individuato almeno un identificativo personale duplicato.

Esempio

| RB030 | RX030 | RB080 | RB090 |
|-------|-------|-------|-------|
| 3564621 | 356462 | 1971 | 1 |
| 3564621 | 356462 | 2010 | 2 |

Le due righe rappresentano chiaramente due individui differenti:

- stesso household;
- anno di nascita diverso;
- sesso diverso.

L'identificativo RB030 non è quindi sufficiente per distinguere
univocamente le persone nel Public Use File.

Poiché il dataset è sintetico non è possibile stabilire se si tratti
di una scelta della procedura di sintesi oppure di un difetto del
dataset.

L'anomalia interessa almeno due record su 43 489.

---

### Decisione D002

RB030 **non** viene utilizzato come identificativo personale interno.

Viene invece introdotta una chiave tecnica

```
person_key
```

costruita come

```
RB030 + indice di riga
```

RB030 viene conservato esclusivamente come identificativo sorgente.

---

# 6. Codice essenziale

Ricerca automatica delle possibili chiavi

```python
ID_PAT = re.compile(r'(030|040|050)$')

...
```

Profiling delle colonne candidate

```python
...
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

# 7. Stato corrente

Completato

- download
- estrazione
- inventario
- identificazione D/H/R/P
- identificazione household key
- identificazione person key
- individuazione prima anomalia

Da fare

- verifica completa dei join D-H
- verifica completa dei join R-P
- ricostruzione della struttura familiare
- classificazione dei nuclei familiari
- inventario sistematico delle variabili

---

# 8. Prossimo passo

Ricostruire l'intera gerarchia

```
Household

    Household
        ├── adulti
        ├── minori
        ├── persona di riferimento
        ├── partner
        └── altri componenti
```

senza utilizzare ancora alcuna informazione sostantiva, ma
soltanto gli identificativi e le relazioni presenti nei file.
