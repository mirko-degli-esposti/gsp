# I nuclei familiari — riassunto per Animarium

**11 agosto 2026** · documento di passaggio, non una nota di progetto

Serve a portare nella chat di Animarium lo stato dell'anello 4: cosa
esiste, con quali variabili, con quali limiti, e qualche idea per una
pagina di visualizzazione.

Riferimenti completi: `nota_nucleo_familiare_v3.md` (architettura e
misure), `nota_repertorio_avq_v3.md` (repertorio, modulo, collaudo).

---

## 1. Cosa esiste, in due righe

Ogni individuo delle undici popolazioni sintetiche ha ora un
`id_nucleo` e un `ruolo`. **1,91 milioni di individui in 888.000
nuclei.** La popolazione non è stata toccata: le due colonne stanno in
file separati e si uniscono con un join su `uid`.

```
data/nuclei/nuclei_{comune}.csv                uid, id_nucleo, ruolo
data/nuclei/nuclei_{comune}_diagnostica.json   tutte le metriche
```

`id_nucleo` ha la forma `340270000993-000041`: **contiene la sezione**,
quindi un nucleo a cavallo di due sezioni si vedrebbe a occhio. Non
esistono: ogni nucleo sta interamente in una sezione.

L'1,1–2,3% degli individui ha `id_nucleo` **vuoto**. Non è un errore: è
popolazione in convivenza anagrafica — case di riposo, studentati,
caserme — dedotta dal residuo dei vincoli censuari. Va mostrata come
categoria, non nascosta.

---

## 2. Le variabili

### 2.1 Del nucleo (derivabili per aggregazione)

| | come si ottiene |
|---|---|
| **ampiezza** | conteggio dei membri |
| **firma** | stringa dei ruoli ordinati: `RPFF` |
| **tipologia** | dalla firma: coppia con figli, monogenitore, unipersonale, … |
| sezione, zona, quartiere | dai membri (tutti la stessa) |
| età del riferimento | dal membro con `ruolo = R` |
| presenza di minori, di anziani | dalle età dei membri |
| cittadinanza | omogenea o mista |

### 2.2 Dell'individuo, già esistenti

`sesso`, `eta_anni`, `stato_civile`, `cittadinanza`, `istruzione`,
`condizione`, `background`, `origine_genitori`, `area`, `paese`, più
tutto il blocco AVQ (fiducia istituzionale, salute, ambiente, fumo…) e
l'indirizzo.

### 2.3 I ruoli

| sigla | significato | quota indicativa |
|---|---|---|
| `R` | persona di riferimento | uno per nucleo |
| `P` | partner (coniuge o convivente) | ~45% dei nuclei |
| `F` | figlio | |
| `G` | genitore convivente | raro |
| `A` | altro parente | raro |
| `N` | non parente | molto raro |

---

## 3. Le firme — la struttura dei nuclei

Una firma è la stringa dei ruoli. Il **96% dei nuclei ha ampiezza ≤ 4**, e
lì una o due firme coprono il 90%:

| ampiezza | firma dominante | quota |
|---|---|---:|
| 1 | `R` | 1,00 |
| 2 | `RP` coppia · `RF` monogenitore | 0,72 + 0,21 |
| 3 | `RPF` · `RFF` | 0,79 + 0,14 |
| 4 | `RPFF` | **0,91 da sola** |
| 5 | `RPFFF` | 0,74 |
| 6+ | `RPFFFF` | 0,53 |

*Sono le quote del repertorio AVQ da cui si estrae; quelle realizzate
nelle popolazioni sono vicine ma non identiche, perché le ampiezze
vengono dai vincoli censuari del comune.*

---

## 4. I numeri per comune

Da `assign_nucleo.py --tutti`, 10 agosto:

| comune | individui | nuclei | omogenee | incoerenti | senza nucleo |
|---|---:|---:|---:|---:|---:|
| Bologna | 390.098 | 210.737 | 98,1% | 18,2% | 1,43% |
| Brescia | 198.259 | 96.608 | 95,1% | 22,7% | 1,82% |
| Parma | 198.121 | 94.484 | 96,5% | 21,7% | 1,86% |
| Modena | 184.597 | 85.249 | 93,8% | 23,6% | 2,28% |
| 035033 | 171.207 | 80.829 | 94,8% | 22,7% | 1,13% |
| 039014 | 156.304 | 75.616 | 91,6% | 23,4% | 1,60% |
| 099014 | 150.046 | 68.903 | 93,0% | 24,0% | 1,78% |
| 038008 | 129.391 | 65.281 | 92,9% | 21,4% | 2,06% |
| 040012 | 117.050 | 54.000 | 91,4% | 24,7% | 1,79% |
| 033032 | 102.887 | 48.737 | 93,9% | 24,5% | 1,42% |
| Castenaso | 16.357 | 7.493 | 94,6% | 23,5% | 1,15% |

**«omogenee»** = coppie in cui i due partner hanno lo stesso stato
civile. **«incoerenti»** = coniugati che non stanno in una coppia di
coniugati (§5).

---

## 5. I limiti, e come mostrarli

La regola del progetto è che i limiti si dichiarano, non si nascondono.
Per una pagina pubblica questi sono quelli che un lettore attento
noterebbe da solo.

**Il 18–24% dei coniugati non è in una coppia di coniugati.** Ma
scomposto per ruolo dice l'opposto di quel che sembra: chi ha ruolo `P`
è appaiato correttamente nel 97–98% dei casi, chi ha `R` nel 92–94%.
L'incoerenza sta in **chi non è finito in una coppia** — figli sposati
che vivono coi genitori, soprattutto. La causa è a monte: il constraint
set non impone che ci si sposi a due a due, quindi in molte sezioni i
coniugati sono un numero dispari. **L'anello 4 rivela un'incoerenza già
presente, non la crea.**

**Nessuna coppia convivente dello stesso sesso.** Le unioni civili
esistono (0,4% delle coppie coniugate, da ISTAT), ma due `celibe_nubile`
dello stesso sesso non si accoppiano mai: manca la fonte.

**Il divario d'età fra partner è convenzionale** (±15 anni): l'AVQ ha
classi larghe 5–10 anni e non lo risolve.

**L'indirizzo è ancora per individuo.** Marito e moglie possono
risultare a due civici diversi. È il limite più visibile se la pagina
mostrasse i nuclei sulla mappa, e va sistemato prima.

**Il repertorio è emiliano-lombardo** e la coda (nuclei oltre 6
componenti) viene dai soli microdati di Parma.

---

## 6. Idee per la pagina

### 6.1 Statistiche, in stile anagrafe

Il modello è la pagina di statistiche demografiche di un comune. Quattro
blocchi:

- **famiglie per ampiezza**, con il confronto contro il dato censuario
  `PF3`–`PF8`. Qui il riferimento c'è ed è forte: è il vincolo stesso,
  quindi la barra e il rombo coincidono per costruzione — il che è
  un'informazione onesta da mostrare, non un trucco;
- **tipologia familiare** (coppia con figli, coppia senza, monogenitore,
  unipersonale, altro), che **non** ha riferimento censuario: è modello;
- **ampiezza media, numero di figli per famiglia con figli, età media
  del riferimento**;
- **famiglie con almeno un minore / un ultra75enne / uno straniero**.

Vale la distinzione già in uso nel pannello dei marginali: dove c'è un
riferimento censuario si mostra, dove non c'è si dichiara che è modello.

### 6.2 Distribuzione spaziale

Le famiglie **per ampiezza media per sezione**, o la quota di
unipersonali, dovrebbero mostrare il gradiente centro-periferia che
abbiamo misurato: nuclei piccoli in centro, grandi fuori. È il tipo di
struttura che si vede bene su mappa e che valida visivamente il
risultato.

### 6.3 Schede di nucleo — il ponte verso la narrativa

Questa è la parte nuova rispetto alla scheda individuo. Un nucleo
mostrato come **gruppo**, con i membri in ordine di ruolo:

```
Nucleo 340270000993-000041 · ampiezza 4 · RPFF
Sezione 993 · quartiere Oltretorrente

  R  F  51a  coniugata   ITL  laurea      occupata
  P  M  59a  coniugato   ITL  diploma     occupato
  F  M  24a  celibe      ITL  diploma     studente
  F  F  18a  nubile      ITL  licenza     studente
```

Tre cose che secondo me rendono la scheda utile:

- **la firma in chiaro**, perché è l'oggetto che il modello genera;
- **i divari d'età** calcolati e mostrati (padre-figlio 27 e 33), così si
  vede il vincolo all'opera;
- un **pulsante per pescarne un altro a caso**, che è il modo più
  efficace per farsi un'idea della qualità — è quello che abbiamo usato
  noi per trovare il bug delle coppie coniugato+vedovo.

Filtri utili: per ampiezza, per firma, per presenza di minori, per
sezione. E una modalità «mostrami un nucleo con caratteristica X», che
serve sia per l'ispezione sia per scegliere i casi da narrare.

### 6.4 Il ponte narrativo

Se la scheda di nucleo diventa la base per la narrativa, due
raccomandazioni dal lato dati:

**La provenienza va portata dentro.** Un nucleo ha attributi `misurato`
(sesso, età, cittadinanza — vincolati dal MaxEnt), `dichiarato` (il
ruolo, la firma — derivati dal modello) e presto `aperto` (le variabili
narrative). La scheda dovrebbe distinguerli visivamente, altrimenti la
biografia eredita un'apparenza di fattualità che i dati non hanno.

**I nuclei con incoerenze non vanno nascosti ma marcati.** Un nucleo con
un figlio coniugato senza coniuge è un caso reale del modello: mostrarlo
con una nota è più onesto che filtrarlo, e per la narrativa è
un'informazione (quel personaggio ha un coniuge che vive altrove — cosa
che nella realtà succede).

---

## 7. Cosa serve prima, dal lato dati

**L'indirizzo per famiglia** (§5) è l'unico prerequisito vero se la
pagina mostra i nuclei su mappa. Oggi i membri di un nucleo possono
avere civici diversi, e su mappa si vedrebbe subito.

Il resto è pronto: i CSV ci sono per tutti e undici i comuni, e la
diagnostica JSON contiene già le metriche per una pagina «metodo».

---

## 8. Numeri utili da avere sottomano

- **888.000 nuclei**, 1,91 M individui, undici comuni
- ampiezza media **~2,15**
- **96%** dei nuclei ha ≤ 4 componenti
- **97,2–98,8%** dei nuclei senza alcun ripiego nell'assemblaggio
- divario generazionale mediana **29–30 anni** (target AVQ 33)
- divario fra partner: mediana **−1**, p05 **−14**, p95 **+14**
- l'**1,1–2,3%** degli individui è in convivenza, senza nucleo
