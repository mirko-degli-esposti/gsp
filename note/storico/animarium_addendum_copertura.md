# Animarium — addendum: classi di garanzia e tabella di copertura

**Da leggere dopo `animarium_passaggio_v20.md`**
1 agosto 2026

Due punti emersi discutendo il documento di passaggio. Il primo lo
semplifica, il secondo corregge una promessa dell'interfaccia.

---

## 1. Il tier non richiede un badge nuovo: `paese` degrada a classe D

Il documento di passaggio proponeva un sistema di badge dedicato al tier.
È sbagliato — o meglio, è più complicato del necessario.

**La classe di garanzia di `paese` non è una proprietà dell'attributo ma
della configurazione del comune.** A tier 0 `paese` non è «classe C
degradata»: è **classe D**, con la stessa semantica identica delle
variabili AVQ — nessuna informazione geografica, ogni variazione spaziale è
compositiva per costruzione.

Quindi non serve un meccanismo nuovo. Serve che la classe di `paese` sia
letta dalla configurazione del comune invece che essere fissa:

```
tier ≥ 1  →  paese in classe C (condizionato sulla geografia)
tier = 0  →  paese in classe D (come le AVQ)
```

Un solo meccanismo, già implementato per le AVQ, applicato a un attributo
in più. Il § 4 del documento di passaggio va riscritto in questi termini e
ne esce più corto.

Quattro comuni su undici sono a tier 0: **Modena, Rimini, Piacenza,
Ferrara**. Per questi, una mappa «quota di rumeni per quartiere» mostra la
composizione comunale replicata, e le differenze fra zone sono rumore di
allocazione.

**Attenzione al perimetro.** Il tier riguarda **solo** il paese di
cittadinanza. Quanti stranieri per zona, età, istruzione, background e la
dicotomia UE/extra-UE sono condizionati sulla geografia in **ogni** comune,
tramite i blocchi Z del MaxEnt e la sezione di censimento. Una mappa «quota
di stranieri per quartiere» è valida ovunque.

---

## 2. La tabella di copertura: 333 regge fra i K9C, si dimezza su K6C

### Cosa abbiamo verificato

Il numero **67 coppie su 333** compare in `Readme.md` e nei design dalla
v06 alla v09, sempre con la formula *«identica nelle quattro città»*. Non
compare in nessun file di codice: è un numero misurato e trascritto.

Lo script che lo produce è `animarium/build/build_riferimenti.py`. La riga
53 definisce:

```python
MOSTRATI = ["zona", "sesso", "eta", "stato_civile", "cittadinanza",
            "istruzione", "condizione", "background", "origine_genitori"]
```

e le righe 158–159 enumerano `itertools.combinations(MOSTRATI, r)` per
`r` in 0..2. Le «coppie» sono quindi combinazioni **(filtro, attributo
mostrato)**, non coppie di categorie. Il conto si riproduce esattamente:

| | |
|---|---|
| filtri di arietà 0, 1, 2 su 9 attributi | 1 + 9 + 36 = 46 |
| per ciascuno, gli attributi mostrabili | 9 meno quelli nel filtro |
| **totale** | **333** ✓ |

Bologna, rieseguito il 1/8/2026, conferma: **67/333, 20%**.

### La buona notizia: il denominatore non dipende dalle zone

`MOSTRATI` è una lista di **nomi di attributo**, non di categorie. Quindi
Piacenza con 4 zone e Forlì con 21 danno lo stesso 333. Confermato anche
dalla struttura dei constraint set: **16 blocchi per tutti i nove K9C**,
indipendentemente dal numero di zone — è il numero di *celle* a variare,
da 663 a 2.983.

**La promessa «identica in tutte le città» era una proprietà, non una
coincidenza** — limitatamente ai comuni K9C.

### La cattiva notizia: K6C perde il 71% delle combinazioni

Ferrara e Castenaso non hanno `zona`, `background`, `origine_genitori`.
Delle 333 combinazioni, quelle che coinvolgono almeno uno dei tre sono
**237**. Ne restano **96**.

```
K9C (nove comuni)      67 / 333
K6C (Ferrara, Castenaso)  N /  96      (N da misurare)
```

### La scelta di progetto

Avevamo considerato un **denominatore fisso a 333**, con le 237 marcate
«non applicabile» invece che assenti — per mantenere la confrontabilità.
Il numero però lo sconsiglia: 237 non applicabili su 333 non aiutano il
confronto, lo sommergono, e comunicano «città con dati scadenti» invece di
«città senza articolazione sub-comunale», che è un fatto amministrativo e
non un difetto del dato.

**Proposta: due denominatori, con la ragione dichiarata accanto.**

> Bologna — 67 su 333 combinazioni
> Ferrara — N su 96 · *comune non articolato: gli incroci che coinvolgono
> zona, background e origine dei genitori non esistono*

I due numeri non sono confrontabili, ma nemmeno le due città lo sono su
quell'asse: una ha diciotto zone, l'altra nessuna. Un denominatore comune
darebbe una confrontabilità apparente.

È anche coerente col principio che regge Animarium — *ogni statistica
richiede la sua configurazione di confronto*. Qui la configurazione **è**
il livello, e va esposta accanto al numero invece che nascosta.

Nota che il pannello distingue **già tre stati** — `✔` coperto, `·`
incrocio non osservato («è modello, e il pannello lo dichiara»), vuoto
(l'attributo è nel filtro). Aggiungere «non applicabile» come quarto stato
è coerente con quello che fa, non un'aggiunta estranea.

### Prima di tutto questo: lo script non parte su K6C

```
errore: constraint set non trovato:
  /home/mirko/progetti/gsp/data/comuni/038008/constraints_2024/cs_K9C.json
```

`build_riferimenti.py` **cabla `cs_K9C.json`** invece di risolvere il
livello. È la stessa classe di difetto che il 1/8/2026 ha fatto pescare a
`assign_avq` il `popolazione_K10C.csv` residuo di Brescia invece del K9C
appena rigenerato: un livello assunto invece che risolto.

La riparazione è un `glob` sul pattern, come già fanno `assign_avq.py` ed
`enrich.py` con `G.resolve_pop_file`. Va fatta **prima** di qualunque
decisione sul denominatore, perché senza non si può misurare N per Ferrara.

**Da verificare se lo stesso difetto sia in altri script di
`animarium/build/`**: `to_parquet.py`, `build_indice.py`, `manifest_min.py`
e `ispeziona_cs.py` sono i candidati, e tutti dovranno gestire due livelli.

---

## 3. Riepilogo delle azioni

| | azione | dove |
|---|---|---|
| 1 | risolvere il livello invece di cablare `cs_K9C.json` | `build_riferimenti.py`, e verificare gli altri script di build |
| 2 | misurare N/96 su Ferrara e Castenaso | esecuzione |
| 3 | riscrivere il § 3.4 con due denominatori e la ragione | `design_animarium_v09.md` |
| 4 | far dipendere la classe di `paese` dal tier (C → D se tier 0) | sistema dei badge |
| 5 | escludere `popolazione_K10C_avq_full.csv` di Brescia | catena del bundle |
| 6 | gestire lo schema a 39 colonne accanto a quello a 42 | `to_parquet.py`, DuckDB |

---

## 4. Una nota di metodo

Il 333 è il **secondo numero in ventiquattr'ore** che, tracciato fino alla
sua origine, si è rivelato legato a una configurazione che non esiste più.
L'altro è il tasso del 2,6% di combinazioni logicamente impossibili,
riportato nelle note di progetto e non riproducibile sui comuni attuali:
si è scoperto essere l'1,72% di Brescia **K10C**, effetto della
riducibilità del blocco MC, contro lo 0,001–0,004% dei K9C
(`note/nota_combinazioni_impossibili_v2.md`).

In entrambi i casi il numero era corretto quando fu misurato, ed è
diventato fuorviante perché la configurazione a cui si riferiva non era
scritta accanto.

La regola che ne discende, ed è la stessa che Animarium applica ai dati che
mostra: **un numero in una nota va accompagnato dalla configurazione su cui
è stato misurato, o non va usato.** Il 333 aveva la formula «identica nelle
quattro città», che era la configurazione — ma quelle quattro città avevano
tutte lo stesso livello, e nessuno l'aveva scritto.
