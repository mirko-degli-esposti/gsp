# Il settore economico: dentro il MaxEnt o a valle?

**v4 — 6 settembre 2026, Buttrio** · censimento 2011 `DICA_CARATT_ATTL`
+ `DICA_CARATT_ATTL_COM`, censimento permanente 2021 `DF_DCSS_EMPLP_*_COM`

Sostituisce la v3. Tre cose cambiano, e due sono retrattazioni:

1. **La tavola comunale `DICA_CARATT_ATTL_COM` serve, eccome.** La v3 la
   liquidava in una riga (§7) come ridondante. Era un errore di lettura
   della sua struttura, ed è costato un mese.
2. **I file `c9` e `c10` non sono materiale morto**: sono i vincoli della
   calibrazione. La v3 li dava per mai usati e superflui (§1, §10).
3. **La via aperta della §9 è stata percorsa** e il risultato è negativo.
   Ne apre un'altra, che è stata percorsa e misurata: l'IPF a due
   marginali sul permanente 2021.

Resta invariata la risposta alla domanda del titolo — **a valle** — e
resta invariato tutto il §6, i cui numeri si riproducono esattamente.

---

## 1. Da dove nasce la domanda

Due tavole censuarie erano scaricate e ricostruite a ogni rigenerazione
senza produrre alcun attributo:

| file | contenuto | fonte | uso |
|---|---|---|---|
| `c9_sex_posizione_prof.csv` | sesso × dipendente/indipendente | permanente 2021 | **vincolo di calibrazione** (§11) |
| `c10_sex_settore.csv` | sesso × 6 macro-classi ATECO | permanente 2021 | **vincolo di calibrazione** (§11) |

> **RETRATTAZIONE (6/9/2026).** La v3 scriveva: «Su `c9` la verifica è
> esplicita: l'unico riferimento in tutto il codice è in
> `fetch_comune.py`, che lo scarica. **Nessuno lo legge.**» Vero come
> constatazione, falso come giudizio. L'errore era cercare a quale
> *vincolo* servissero, dentro lo spazio degli stati, quando il loro
> posto è **a valle**, come marginali che calibrano la congiunta.

La ragione strutturale della v3 resta corretta e va tenuta: un vincolo
può agire solo su variabili che stanno nello spazio degli stati, e a K9C
non esistono né `settore` né `posizione`. Quello che era sbagliato è
l'implicito che un file di marginali possa servire *solo* come vincolo.

---

## 2. Perché K10C non è la risposta

*(invariata rispetto alla v3)*

Il livello K10C aggiunge il settore e paga tre prezzi: lo spazio degli
stati passa a **37 milioni** contro i 69.888 di Parma K7C; la catena
diventa **riducibile a λ\*** per gli zeri strutturali del blocco `MC`,
stesso meccanismo del blocco `GC` per cittadinanza × background; su
Brescia produce **3.417 individui impossibili** (1,72%).

Il prezzo peggiore resta il terzo: **il blocco condiziona il settore sul
sesso soltanto**, ignorando l'istruzione.

---

## 3. Le misure di agosto, e quali sopravvivono

Fonte: `DICA_CARATT_ATTL`, occupati (`EMPLP`), tutte le altre dimensioni
al totale. Metrica: distanza in variazione totale.

### Composizione nazionale per sezione ATECO, occupati 15+

| | | | |
|---|---|---|---|
| C manifattura | 18,8% | K finanza | 3,6% |
| O amministrazione pubbl. | 11,0% | S altri servizi | 3,2% |
| G commercio | 9,3% | J informazione | 2,5% |
| Q sanità | 8,7% | T servizi domestici | 1,9% |
| P istruzione | 7,0% | D energia | 1,2% |
| F costruzioni | 6,9% | N servizi imprese | 1,1% |
| I alloggio e ristorazione | 6,7% | E acqua e rifiuti | 1,0% |
| M attività professionali | 5,4% | R arte e sport | 1,0% |
| H trasporti | 4,9% | B estrazione | 0,7% |
| A agricoltura | 4,6% | L immobiliare | 0,4% |
| | | U organismi extraterr. | 0,1% |

### Quanto ciascuna variabile sposta la composizione

| dimensione | TVD | stato |
|---|---|---|
| istruzione, titoli numerosi | 0,105 – 0,390 | `dichiarato`, non riverificato |
| istruzione, titoli rari | 0,31 – 0,49 | `dichiarato`, non riverificato |
| sesso | 0,152 – 0,188 | `dichiarato`, non riverificato |
| età, 12 classi quinquennali | 0,03 – 0,27 (mediana 0,10) | `dichiarato`, non riverificato |
| **comune vs regione** | **RITIRATO** | vedi sotto |

Il dettaglio per titolo — diploma 4-5 anni 0,105 su 5.086.431 occupati,
laurea 4-6 anni 0,390 su 1.877.753, diploma universitario v.o. 0,491 su
243.069 — resta come riportato, con la stessa avvertenza.

### RETRATTAZIONE: il costo del ripiego regionale

La v3 riportava, e con essa il commento in cima a `gsp/lavoro.py` e il
campo `bias` della scheda di registro:

| comune | v3 (5 ago) | **misurato 6/9** |
|---|---|---|
| Bologna | 0,159 | **0,202** |
| Parma | 0,106 | **0,112** |
| Modena | 0,089 | **0,108** |
| Reggio Emilia | 0,042 | **0,048** |
| Ravenna | 0,029 | **0,086** |
| Brescia | — | **0,108** |

**I numeri di agosto non sono riproducibili.** Quattro ipotesi verificate
e scartate:

- **esclusione del profilo `41`** (imprenditore e libero professionista,
  il 10% degli occupati a Parma, aggiunto alla congiunta dopo la
  ricostruzione dell'albero): sposta di 0,001–0,007, e su Ravenna nella
  direzione sbagliata;
- **supporto a 14 sezioni** invece di 21, cioè escludendo le sette non
  incrociate col titolo: Ravenna dà 0,082, non 0,029;
- **il modulo di agosto** (`bfa67bb`) eseguito sui dati di oggi: stampa
  0,202 e 0,086. Il commento alla riga 108 era dunque **già falso nel
  commit che lo conteneva**;
- **dati cambiati sotto**: lo zip è del 5/8 alle 11:40, l'impronta è
  stata scritta una volta sola, `--verifica` dà `ok`.

Origine ignota. Quei numeri non provengono dal modulo in nessuna delle
due versioni: sono con ogni probabilità il residuo di una misura fatta a
parte, su una selezione della tavola che `repertorio()` non costruisce.
**Ritirati, non spiegati.**

*Cosa questo implica per il resto della §3.* Le altre misure della stessa
sessione — istruzione, sesso, età — restano `dichiarato` e non
riverificate. Milita a loro favore il fatto che i numeri del §6 si
riproducano **esattamente** (0,149 / 0,166 / 0,156 / 0,138 / 0,156), il
che esclude un guasto sistematico di quella sessione; ma finché non sono
rimisurate vanno lette come tali.

*Cosa NON cambia.* La conclusione qualitativa regge: **il ripiego costa
poco dove il comune è ordinario e molto dove è particolare**. Cambia
l'esempio — Ravenna non è più il comune ordinario, ed è anzi il caso più
particolare dei sei (§12).

---

## 4. Un errore di lettura, e cosa insegna

*(invariata rispetto alla v3, e più attuale che mai)*

La v1 attribuiva alla composizione settoriale delle TVD calcolate sulla
colonna sbagliata: `OCCUPAZIONE` letta come `ATECO_2007`, perché entrambe
hanno codici alfabetici. Il metodo che scioglie il dubbio è
l'assegnazione **per contenimento** contro le codelist del METADATA.

Il secondo errore, più insidioso: tre titoli di studio davano TVD di
0,954, vicinissima al massimo teorico. Artefatto — quei titoli hanno
**una sola sezione pubblicata**, sempre `A`, contro le quattordici degli
altri.

> **Una metrica calcolata su supporti diversi non è comparabile.**
> Il controllo è sempre lo stesso: contare i supporti prima di
> confrontare le distanze.

**Il conto delle occorrenze sale a cinque** (era tre nella v3): dopo il
`residuo_quota` fra zonizzazioni diverse, l'MRE fra comuni con numero di
zone diverso e i titoli a supporto unico, si sono aggiunti gli aggregati
ATECO mescolati alle sezioni (§10) e le sei macro-classi del taglio
comunale, dove `0010` è il totale e va escluso prima di qualunque
confronto.

---

## 5. La conclusione sulla collocazione

Il vincolo K10C condiziona sul **sesso** e ignora l'**istruzione**, al
prezzo di trentasette milioni di stati e di una catena riducibile. La
derivazione a valle condiziona su sesso, comune e — quando la
riponderazione è accesa — titolo di studio.

La v1 di questa nota traeva da qui la conclusione «l'istruzione conta
più del sesso». Era troppo forte: l'istruzione domina agli estremi della
scala — laurea 0,390, licenza elementare 0,307 — mentre nel mezzo il
diploma quinquennale sta a 0,105, sotto il sesso. La formulazione
corretta è:

> **Contano entrambe, e la derivazione a valle può usarle tutte e due
> insieme al comune, mentre il vincolo K10C ne usa una sola.**

### L'argomento che non dipende da quei numeri

Quelle TVD sono ora marcate `dichiarato, non riverificato` (§3), e
sarebbe fragile appoggiarci sopra la decisione. Non serve: dal 6/9/2026
esiste un secondo argomento, indipendente da esse e misurato.

I file `c9` e `c10` sono gli *stessi* vincoli nei due scenari. Dentro il
MaxEnt costano trentasette milioni di stati, una catena di Gibbs
riducibile a λ\* e 3.417 individui impossibili su Brescia. A valle
costano **un IPF su due marginali**, che converge in una manciata di
iterazioni — quattordici sul collaudo sintetico — e che sul vincolo
coetaneo raggiunge il limite teorico della calibrazione a tre cifre
decimali su sei comuni su sei (§12).

E non producono lo stesso risultato. Dentro, il settore sarebbe
vincolato sul solo sesso, con la struttura di dipendenza fra settore e
posizione lasciata emergere dal solver. Fuori, i due vincoli agiscono su
una congiunta che quella dipendenza la porta già dentro, misurata sulla
fonte censuaria e preservata dall'IPF per costruzione.

> **Non era la strada cara per un risultato equivalente: era la strada
> cara per un risultato peggiore.**

Questa formulazione ha una proprietà che quella basata sulle TVD non ha:
**resta valida anche se la riducibilità venisse risolta**. Non dice che
K10C non funziona, dice che anche funzionando otterrebbe meno.

### Perché la cittadinanza è diversa

Il che non toglie nulla al MaxEnt: dice che *questa* variabile non ha
bisogno di starci. Per la cittadinanza la struttura geografica è forte e
va catturata congiuntamente; qui la geografia arriva già da
`condizione`, che è vincolata su zona — e ora arriva una seconda volta,
dalle marginali comunali della calibrazione.
---

## 6. Come si costruisce

*(invariata; i suoi numeri si riproducono esattamente il 6/9/2026)*

### La tavola non consente il condizionamento pieno

L'incrocio fra settore e titolo di studio a livello comunale esiste
**solo per la sezione A**, agricoltura. Con `titolo` specificato le
sezioni disponibili nei sei comuni sono `['A']`; con `titolo = totale`
sono tutte e ventuno.

### La misura che decide

`ateco` e `profilo` sono fortemente dipendenti:

| territorio | TVD(congiunta, indipendenza) |
|---|---|
| Parma | 0,149 |
| Bologna | 0,166 |
| Emilia-Romagna | 0,156 |
| Lombardia | 0,138 |
| Italia | 0,156 |

Stabile su cinque territori: struttura, non rumore. **Un sesto della
massa si sposta** assumendo l'indipendenza.

### Perché vince la congiunta

> Una TVD di 0,15 sulla congiunta produce individui **palesemente
> assurdi**: dirigenti in agricoltura, coadiuvanti familiari nella
> pubblica amministrazione. Una TVD di 0,20 sul condizionamento produce
> individui plausibili con proporzioni un po' storte.

È la stessa ragione per cui l'hot-deck AVQ copia il vettore intero.

**Questa scelta sopravvive alla calibrazione della §11**, ed è il punto
da non perdere di vista: l'IPF riscala i pesi della tabella
`(ateco, profilo)` *prima* dell'estrazione, che resta una pescata sola.
La dipendenza è preservata per costruzione.

---

## 7. Limiti che restano

**Sette sezioni su ventuno non sono incrociate con il titolo di studio**
— `D`, `E`, `H`, `J`, `L`, `M`, `N` — il **15,9%** degli occupati, e
sono i servizi digitali e professionali dove i laureati si concentrano.
Le TVD per l'istruzione sono quindi un limite inferiore.

**Cittadinanza e settore non sono mai incrociati.**

**Niente età nel condizionamento.** Con TVD fino a 0,27 sulle classi
estreme, i ventenni ricevono la distribuzione dei cinquantenni. La
correzione sarebbe tre bin — giovani, centrali, anziani. **La
calibrazione non allevia questo limite**: il permanente incrocia il
settore solo con il sesso.

**Niente titolo nel condizionamento** (§9).

**Sotto il comune non c'è niente.** Nessuna articolazione sub-comunale in
nessuna delle due fonti.

| attributo derivato | risoluzione |
|---|---|
| titolo di studio | regione |
| **settore economico** | **comune**: congiunta per 6 su 11, calibrazione per tutti |
| attributi AVQ | regione |

---

## 8. Cosa fare di K10C

**Lasciarlo dov'è**, come materiale sperimentale escluso dalla
produzione: conserva la storia della riducibilità, che è un risultato
metodologico.

La motivazione aggiornata è nella §5

---

## 9. La via del titolo: percorsa, esito negativo

La v3 proponeva di recuperare il condizionamento sul titolo riponderando
la congiunta con la marginale `P(ateco | titolo)` nazionale, e fissava il
criterio: «si tiene solo se sposta abbastanza da giustificarsi».

**È stata costruita** (`fattore_titolo`, `sposta`) **ed è spenta di
default.** Tre limiti, nessuno rimediabile con la fonte disponibile:

- il fattore è **nazionale**, applicato a una congiunta comunale: il
  livello del correttore non corrisponde al livello del corretto;
- copre **14 sezioni su 21**, e non arriva al **21,4%** degli occupati
  di Parma — proprio le sezioni dove il titolo conterebbe di più;
- **non è validabile**: non esiste una versione comunale della marginale
  per titolo contro cui misurare l'errore introdotto.

Resta disponibile come opzione dichiarata, non come miglioramento.

---

## 10. Le altre variabili della stessa tavola

`OCCUPAZIONE` (11 grandi gruppi CP) sarebbe la più forte per una
biografia, ma ha solo **1.208 righe** con valore specificato e **nessun
comune**: utilizzabile al più come `P(occup | istruzione, sesso)`
nazionale. `DURATA` ha **zero** righe specificate.

> **RETRATTAZIONE (6/9/2026).** La v3 scriveva: «`PROFILO_PROF` rende
> superfluo `c9`: sette modalità utilizzabili contro le due di `c9`,
> dalla stessa fonte». Due errori in una frase. **Non è la stessa
> fonte**: `PROFILO_PROF` è il censimento 2011, `c9` è il permanente
> 2021 (`DF_DCSS_EMPLP_1_COM`). E il confronto era sull'asse sbagliato —
> il dettaglio — quando gli assi su cui `c9` vince sono l'**annata** e la
> **copertura territoriale**: esiste per tutti i comuni, non per
> venticinque. Non è una versione povera della congiunta: è la marginale
> che la calibra.

---

## 11. La calibrazione sul permanente 2021

### La fonte che la v3 aveva liquidato

> **RETRATTAZIONE (6/9/2026).** La v3, §7: «La tavola comunale
> `DICA_CARATT_ATTL_COM` **non serve**: copre tutti gli 8.230 comuni ma
> con sette sole categorie (totale, industria, servizi, più quattro
> aggregati), senza istruzione.»
>
> Tre errori. **8.230 sono i territori**, di cui 8.092 comuni e 138 fra
> province, regioni, ripartizioni e Italia — e proprio quelle 138 righe
> servono, perché contengono le regionali. Le sei categorie **non sono
> aggregati ma una partizione** esatta delle 21 sezioni. E «senza
> istruzione» è vero ma irrilevante: il suo uso non è condizionare, è
> **vincolare**.

Le sei macro-classi, verificate come partizione il 6/9/2026:

| codice | contenuto | sezioni |
|---|---|---|
| `A` | agricoltura, silvicoltura e pesca | A |
| `0011` | industria | B, C, D, E, F |
| `0026` | commercio, alberghi e ristoranti | G, I |
| `0091` | trasporti, magazzinaggio, informazione | H, J |
| `0092` | finanza, immobiliare, servizi alle imprese | K, L, M, N |
| `0093` | altre attività | O, P, Q, R, S, T, U |

**Non sono intervalli contigui di lettere**: `G` e `I` stanno insieme e
`H` sta altrove, `J` è staccato da `K`-`N`. Chi legge l'etichetta
«(g,i)» come un intervallo mette `H` in commercio e `I` in trasporti —
due sezioni grosse nel posto sbagliato, con i totali che tornano lo
stesso e nessun controllo strutturale che se ne accorga.

### Le due marginali

Il censimento permanente pubblica al **2021**, per **tutti** i comuni:

```
DF_DCSS_EMPLP_2_COM   sesso × sei macro-classi ATECO     -> c10
DF_DCSS_EMPLP_1_COM   sesso × dipendente/indipendente    -> c9
```

Registrate come `istat_cens_settore_prof` e `istat_cens_posizione_prof`,
scaricate e validate su 320 comuni dalla campagna del 28 agosto, mai
usate perché previste per K10C.

### La forma

```
struttura      congiunta 2011 (21 sezioni × 6 profili × sesso),
               comune dove esiste, regione altrimenti
calibrazione   IPF sui due vincoli comunali 2021
estrazione     invariata: la coppia si pesca insieme
```

L'IPF a due vincoli è la distribuzione di **massima entropia relativa**
alla congiunta 2011: conserva i rapporti di odds, non le composizioni
condizionate. La quota di dipendenti dentro le manifatturiere cambia —
deve cambiare, è vincolata — ma il fatto che un coadiuvante familiare sia
raro nell'amministrazione pubblica e frequente in agricoltura resta.

È lo stesso principio del solver, applicato a valle: **forma dalla
congiunta, livelli dal comune**, come l'anello 1.

### Nessuna soglia sulla distanza

Sui comuni già vicini alla propria regione l'IPF non sposta nulla per
costruzione. Una soglia aggiungerebbe un percorso di codice e un numero
da giustificare senza cambiare i risultati. Le guardie riguardano la
**qualità** della marginale: assente, con meno di sei classi (il
pavimento 7 in `ATTESI` dice che esistono comuni con un solo sesso
pubblicato), o troppo piccola.

### Il punto aperto: il parasubordinato

Nell'albero 2011 `99 = 9 + 22 + 42`. Nel 2021 `9 + 22 = 99` esatto
(Bologna: 68.348,04 + 27.270,96 = 95.619), quindi il codice `42` è stato
ripiegato dentro una delle due e **la fonte non dice quale**. Vale il
3,6% degli occupati a Parma. Convenzione ISTAT sulle rilevazioni del
lavoro: fra gli indipendenti. `aperto`, non dedotto.

---

## 12. Le misure che validano la calibrazione

### L'IPF raggiunge il limite teorico

Sul vincolo **coetaneo** (marginali 2011, che il taglio comunale fornisce
per tutti gli 8.092 comuni), il residuo dopo calibrazione coincide a tre
cifre decimali con la media pesata delle distanze *dentro* le
macro-classi — cioè con il limite teorico di ciò che sei classi possono
correggere:

| comune | `prima` | dopo IPF | limite teorico |
|---|---|---|---|
| Brescia | 0,108 | 0,035 | 0,035 |
| Parma | 0,112 | 0,029 | 0,029 |
| Reggio Emilia | 0,048 | 0,029 | 0,029 |
| Modena | 0,108 | 0,032 | 0,032 |
| Bologna | 0,202 | 0,043 | 0,043 |
| Ravenna | 0,086 | 0,077 | 0,077 |

**Il metodo non introduce errore proprio.** Recupero del ripiego
regionale: Bologna 79%, Parma 74%, Modena 70%, Brescia 68%, Reggio 40%,
Ravenna 10%.

> **Una previsione sbagliata, e cosa insegna.** Avevo previsto che il
> residuo scendesse a `prima − tvd_macro`, e dallo scarto ho cercato tre
> difetti inesistenti. **La TVD non si decompone per sottrazione**: il
> termine interno è `Σ_m P(m)·TVD_m`, una media pesata delle distanze
> condizionate, non la differenza fra le TVD aggregate. Le due tavole
> concordano a TVD 0,000 su tutti e sei i comuni.

### La decomposizione

La distanza comune-regione si spacca in due termini con comportamenti
opposti:

| | tra macro-classi | dentro le macro-classi |
|---|---|---|
| natura | recuperabile dalla calibrazione | irriducibile con sei classi |
| escursione | 0,040 → 0,201 | 0,029 → 0,077, quasi costante |
| Bologna | 0,201 | 0,043 |
| Ravenna | 0,043 | **0,077** |

**Bologna è lontana dalla sua regione nel mix settoriale, Ravenna lo è
dentro i settori.** È per questo che la calibrazione recupera il 79% su
una e il 10% sull'altra — e Ravenna, che la v3 dava come il comune più
ordinario dei sei, è il più particolare.

*Cautela:* il termine interno è misurato su sei capoluoghi da 67.000 a
180.000 occupati. Per i comuni piccoli della flotta non esiste congiunta
e non lo sappiamo. `aperto`.

### La deriva decennale

Le stesse sei classi esistono nel 2011 e nel 2021, sugli stessi comuni:
la loro distanza misura quanto è invecchiata la struttura settoriale.

| comune | deriva 2011→2021 | scarto comune-regione |
|---|---|---|
| Ferrara | 0,050 | — |
| Rimini | 0,053 | — |
| Bologna | 0,054 | 0,201 |
| Forlì | 0,058 | — |
| Parma, Modena | 0,062 | 0,107 / 0,103 |
| Castenaso | 0,072 | — |
| Brescia, Reggio | 0,078 | 0,105 / 0,040 |
| Ravenna | 0,079 | 0,043 |
| Piacenza | 0,103 | — |

**Su questa fonte il problema è geografico prima che temporale**: a
Bologna la deriva vale un quarto dello scarto spaziale. Ma sui comuni
ordinari il rapporto si inverte, ed è il motivo per cui il guadagno
misurato contro una verità 2011 risultava negativo per Reggio e Ravenna:
non è la calibrazione che fallisce, è la metrica che punisce l'IPF per
essersi avvicinato al 2021.

Il campo `bias` della scheda passa da `dichiarato` («la fonte ha quindici
anni e la struttura settoriale è cambiata») a `misurato`.

Bologna, il dettaglio della deriva:

| classe | 2011 | 2021 | Δ |
|---|---|---|---|
| agricoltura | 1,65% | 0,60% | −1,05 |
| industria | 17,88% | 16,35% | −1,53 |
| commercio, alberghi | 16,80% | 17,52% | +0,72 |
| trasporti, informazione | 8,34% | 10,96% | **+2,62** |
| finanza, servizi imprese | 19,99% | 22,08% | **+2,09** |
| altre attività | 35,34% | 32,49% | −2,85 |

Nessuna inversione anomala: è dieci anni di terziarizzazione.

*Nota sui livelli:* gli occupati passano da 165.768 a 180.953, +9,2%. **I
due numeri non sono confrontabili come livelli** — 2011 è un conteggio
censuario, 2021 una stima da registro con definizione ILO. La
composizione è confrontabile, il livello no; ed è esattamente il motivo
per cui la calibrazione usa la marginale come **forma** e riscala sul
totale di partenza.

### Quanto lavoro fa sulla flotta

Distanza macro comune-regione sui 240 comuni misurabili del registro,
con la regionale **letta** dalla tavola:

| quantile | valore |
|---|---|
| q05 | 0,038 |
| q25 | 0,069 |
| q50 | **0,101** |
| q75 | 0,131 |
| q95 | 0,199 |
| media pesata sugli occupati | 0,125 |

**Sopra 0,05: 214 comuni su 240 (89%), l'86% degli occupati.** La
calibrazione non è un raffinamento per pochi casi.

I dieci più lontani dalla propria regione sono tutti leggibili, il che è
il controllo che il numero misura struttura e non rumore: **Goro 0,612**
(pesca nel delta), Fiorano Modenese 0,223 e Castellarano 0,205 (distretto
ceramico), Santa Sofia 0,228 e Civitella di Romagna 0,225 (Appennino
romagnolo), Fabbrico 0,218 e Campagnola Emilia 0,209 (pianura reggiana).

**La distanza non scala con la taglia.** Mediana per fascia di occupati:
0,108 (500-2k), 0,100 (2k-8k), 0,092 (8k-30k), 0,104 (>30k). Solo il q90
si allarga scendendo — 0,206 contro 0,186 — ed è la firma giusta: la
mediana è struttura, la coda è rumore multinomiale che scala come
1/√n. **La soglia non va normalizzata sulla taglia**, al contrario di
quanto si è dovuto fare per il C5.

> **Un artefatto, e come si è visto.** Nella prima versione del giro la
> regionale era **aggregata** dai comuni del registro invece che letta
> dalla tavola. Milano risultava a 0,022 dalla propria regione — il
> comune più vicino di tutti — perché pesava 550.946 occupati su tre
> comuni lombardi presenti: un comune vicino a sé stesso. L'errore era
> selettivo sui grandi, e portava la quota di occupati sopra soglia dal
> vero 86% a un apparente 64%.

---

## 13. Come presentarlo

Non è una **stima** del settore del singolo individuo, e non va
presentato come tale. È un'**assegnazione realistica**: un attributo
derivato che rispetta, per costruzione, le marginali comunali osservate
e la struttura di dipendenza nota fra settore e posizione, e che per il
resto distribuisce la massa nel modo meno impegnativo possibile.

Quello che si può dichiarare:

- la coppia `(settore, posizione)` di ogni occupato è coerente con la
  dipendenza misurata sulla fonte censuaria (TVD congiunta-indipendenza
  0,138–0,166);
- le marginali comunali per sesso, macro-classe e posizione riproducono
  quelle del censimento permanente 2021 **esattamente**, dove pubblicate;
- il residuo rispetto alla verità comunale a 21 sezioni, dove misurabile,
  è 0,029–0,077 contro 0,048–0,202 del ripiego regionale.

Quello che **non** si può dichiarare: che il settore del singolo sia
corretto; che la composizione dentro ciascuna macro-classe sia comunale
(viene dalla regione, o dal 2011); che l'attributo sia condizionato su
età o istruzione (non lo è).

---

## 14. Aperto

- il termine interno alle macro-classi sui **comuni piccoli**: misurato
  solo su sei capoluoghi grandi;
- il **parasubordinato** nella dicotomia 2021: convenzione, non dedotto;
- **12 comuni della flotta** assenti dal taglio comunale 2011 (fusioni
  post-2011): calibrabili sul 2021 senza termine di paragone storico;
- le misure della §3 su istruzione, sesso ed età, **non riverificate**
  dopo la retrattazione sul ripiego regionale;
- l'origine dei numeri ritirati: quattro ipotesi scartate, nessuna
  spiegazione.
