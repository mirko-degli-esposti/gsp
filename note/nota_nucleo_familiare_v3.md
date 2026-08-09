# Struttura familiare e anello 4 — dove entra, e a quale scala

**Versione 3.0 — 9 agosto 2026**
Mirko Degli Esposti · DIFA, Università di Bologna

Questa nota registra le misure sui microdati comunali di Parma e le
decisioni architetturali che ne discendono. Risponde a una domanda sola:
**dove inserire la struttura familiare nella pipeline GSP senza rifittare
nulla di quanto esiste.**

Contiene due previsioni registrate prima della misura ed entrambe
falsificate (§7), una ritrattazione di metodo (§6.3), la refutazione del
codebook della fornitura (§2.3) e la refutazione di una lettura data per
acquisita nella versione precedente (§2.4).

*Changelog v3.0 — sostituisce la v2, due cambiamenti di sostanza:*
1. *Il punto aperto (1), «rischio principale» in v2, è **risolto in
   positivo**: i campi `PF3`–`PF8` danno la distribuzione delle famiglie
   per numero di componenti a livello di sezione, per tutti e undici i
   comuni, e sono già su disco dal 2 agosto (§8.1).*
2. *L'interpretazione del codice 11 come «coabitazione», che la v2
   dichiarava confermata dal profilo demografico, è **contraddetta** dal
   confronto con `PF9` del censimento (§2.4). Torna aperta.*

---

## 1. Il problema, e perché non ha una risposta ovvia

L'assunzione (11) del documento di riferimento — «nessuna struttura
familiare» — è il limite dichiarato più vistoso della pipeline. Toglierlo
sembra a prima vista un problema di aggiungere una variabile. Non lo è,
perché gli oggetti in gioco sono due e hanno natura diversa:

| | cos'è | dove può stare |
|---|---|---|
| **ruolo** (Ncomp, Relpar) | attributo individuale | anello 1, anello 2, o derivazione a valle |
| **appartenenza** (chi con chi) | **relazione fra individui** | solo un passo di assemblaggio |

Il MaxEnt sugli stati individuali non può esprimere la seconda. Vincolare
`Ncomp` nel joint darebbe una popolazione in cui il numero di persone che
dichiarano «vivo in tre» è corretto e in cui non esiste **nessuna terna**.
È un errore che supera tutti i controlli marginali.

L'anello 2 è escluso per una ragione diversa: il pool AVQ è regionale e
per assunzione (6) le variabili donate non hanno alcuna informazione
geografica. La composizione familiare in una città è fortemente
geografica; donarla darebbe una struttura uniforme sulla dimensione che
conta. `PROFAM` resta utile come sorgente di distribuzioni condizionate,
non come attributo donato.

Resta da decidere, e da **misurare**, se il ruolo si possa derivare a
valle condizionando sugli attributi di anello 1, e a quale scala
geografica debba essere vincolato l'assemblaggio.

---

## 2. Le fonti

### 2.0 Microdati comunali di Parma

`data/opendata/034027/Popolazione_residente_2025.csv`, fornitura del
Comune di Parma. 202.111 righe, una per residente, separatore `;`.
Codebook allegato: `Descrizione_codifica_campi_2025.csv` (ma vedi §2.3).

| campo | contenuto |
|---|---|
| `Tipores` | 1 = famiglia (199.015) · 2 = convivenza anagrafica (3.096) |
| `Sesso` | 1 = maschio · 2 = femmina |
| `ETA` | anni compiuti |
| `Cittad` | codice paese ISTAT, **151 modalità** nel dato, 100 = Italia (82,03%) |
| `Ncomp` | componenti del nucleo |
| `Relpar` | relazione con l'intestatario — **codifica non risolta, §2.3** |
| `Quartiere` | 13 modalità **in chiaro** = `COM_ASC1`, la `zona` di anello 1 |
| `SEZ21` | sezione 2021, progressiva da 1 a 1667, **non** zero-paddata |

**Non contiene lo stato civile.** È la variabile che spiegherebbe gran
parte di `Relpar`, ed è in anello 1. La sua assenza rende la lettura di
M3 asimmetrica (§6.2).

Il file è del **2025**; la popolazione sintetica è calibrata su dati
**2023**. Due istanti diversi: da dichiarare ovunque i numeri finiscano
in un articolo.

### 2.1 Le anomalie di `Ncomp` sono le convivenze — *misurato*

`Ncomp` presentava valori impossibili: 319, 111, 110, 108, 40. Ciascuno
compariva **esattamente quel numero di volte**. È la firma di una
convivenza — 319 residenti di un istituto portano tutti `Ncomp=319` — non
un difetto del file. Con `Tipores=1` il massimo scende **da 319 a 12**.

Un solo record incoerente su 199.015 (`Ncomp=1` con `Relpar≠1`). Escluso
e contato, non corretto.

Conferma laterale che i due universi vanno tenuti separati: le 3.096
righe di convivenza portano `Relpar` 2 (3.086) e 1 (10). Dentro la
convivenza il codice 2 non può significare «coniuge»: **lo stesso codice
ha due significati nei due universi**, che è la firma di una codifica
corta e riutilizzata.

### 2.2 I nuclei chiudono — *misurato*

| stimatore del numero di famiglie | valore |
|---|---|
| somma di 1/`Ncomp` | 96.984 |
| conteggio di `Relpar=1` | 96.985 |
| scarto | **−0,00%** |

Residuo frazionario massimo per sezione: **1/3 su 1.314 sezioni**. Un solo
nucleo in tutta Parma sta a cavallo di due sezioni.

> **Conseguenza.** Il numero di famiglie per sezione è un vincolo
> **esatto**, non stimato, e vale al livello dove serve all'assemblaggio.

> **Ritrattazione.** Una lettura precedente attribuiva uno scarto di ~30
> famiglie per classe di ampiezza a nuclei a cavallo di sezione. Era
> l'effetto delle convivenze mescolate al conteggio. L'ipotesi cade.

### 2.3 Il codebook della fornitura è refutato dai dati — *misurato*

`Descrizione_codifica_campi_2025.csv` è allegato alla stessa fornitura,
stesso anno, stessa cartella. Risolve senza ambiguità `Tipores`, `Sesso`,
`Cittad`, `SEZ21` e `Quartiere`. **Per `Relpar` dichiara una
classificazione che i dati contraddicono.**

Il codebook elenca 29 codici (1–28, più 80, 81, 99) della classificazione
anagrafica per esteso. Il dato ne usa **undici, contigui, 1–11, e nulla
sopra**.

La refutazione non si appoggia alle numerosità — che si potrebbero
spiegare con la direzionalità della relazione rispetto all'intestatario —
ma al **profilo per età**, che sotto le etichette dichiarate fa previsioni
assolute:

| codice | etichetta dichiarata | età attesa | età mediana osservata | n |
|---|---|---|---:|---:|
| 4 | Nipote (discendente) | giovane | **74** | 1.192 |
| 5 | Pronipote (discendente) | bambino | **80** | 229 |
| 9 | Fratello / Sorella | ~ intestatario (55) | **13** | 1.280 |
| 8 | Bisnonno / Bisnonna | 90+ | **48** | 354 |

Pronipoti ottantenni e fratelli tredicenni non esistono. A conferma, i
codici 12–28 sono **tutti a zero**, e comprendono relazioni che in
qualunque anagrafe reale sono presenti: Genero/Nuora, Suocero/Suocera,
Cognato, Altro parente, Convivente, Unito civilmente.

La spiegazione più probabile non è un file allegato per errore, ma che il
codebook riporti la classificazione **corrente ed estesa** mentre
l'estrazione porti una codifica **più corta, ereditata**.

**Mappatura inferita dal profilo demografico** — *inferita, non letta*:

| codice | n | età mediana | stranieri | lettura |
|---|---:|---:|---:|---|
| 1 | 96.985 | 55 | 0,15 | intestatario |
| 3 | 49.963 | 16 | 0,14 | figlio |
| 2 | 33.262 | 57 | 0,13 | coniuge |
| 11 | 14.725 | 38 | **0,52** | **non parente — natura non risolta, §2.4** |
| 9 | 1.280 | 13 | 0,08 | discendente di 2ª generazione |
| 4 | 1.192 | 74 | 0,30 | ascendente diretto |
| 6 | 926 | 47 | 0,10 | collaterale di generazione |
| 8 | 354 | 48 | 0,21 | affine di generazione |
| 5 | 229 | 80 | 0,41 | ascendente di 2ª generazione o affine |
| 7 | 80 | 61 | 0,11 | ignoto |
| 10 | 19 | 81 | 0,16 | ignoto |

Le prime tre righe — **il 90% delle unità** — sono solide: 1, 2 e 3 sono
forzate dall'aritmetica (uno per famiglia; ≤1 per famiglia; mai con
`Ncomp=1`) e confermate dall'età. I codici 4–10 valgono 4.080 persone, il
2%, e le etichette sono congetture ordinate per generazione: da 80 e 19
casi non si deduce quale sia esattamente il codice 7 o il 10.

Del codice 11 — 14.725 persone, il 7,4% — è determinato solo ciò che
**non** è: non ascendente né zio, perché l'età mediana (38) è molto sotto
quella dell'intestatario (55). Vedi §2.4.

### 2.4 Il censimento per sezione: validazione incrociata, e una refutazione

Fonte: `istat_sezioni_2023`, già nel registro dal 2 agosto 2026, file
regionale `R08_Emilia-Romagna_2023_sezioni.xlsx`, 138 colonne, derivato
per comune in `data/submun/`. Censimento permanente al 31.12.2023 su Basi
Territoriali 2021.

Confronto con i microdati comunali 2025, **due fonti indipendenti**:

| | censimento 2023 | microdati 2025 | scarto |
|---|---:|---:|---:|
| popolazione (`P1`) | 198.121 | 199.014 | +0,5% |
| famiglie (`PF1`) | 94.484 | 96.984 | +2,6% |
| famiglie coabitanti (`PF9`) | 2.542 | ? | — |

Gli scarti vanno nella stessa direzione e sono compatibili con due anni di
crescita anagrafica più differenze definitorie. È la validazione esterna
che nessuno può fare senza avere entrambe le fonti.

**`PF3`–`PF8` partizionano `PF1` esattamente**: somma 94.484 contro
94.484, scarto 0,000%. `PF9` è **fuori dalla partizione**, non un settimo
bin. Controllo eseguito con la stessa logica di `T.partizione()`.

Analogamente `EM1`+…+`EM6` = 198.121 = `P1`, esattamente.

> **Refutazione — il codice 11 non è «coabitazione» nel senso ISTAT.**
>
> La v2 dichiarava l'interpretazione «confermata dal profilo
> demografico». Il confronto con `PF9` la contraddice: 2.542 famiglie
> coabitanti al censimento contro 14.725 persone col codice 11. Anche
> tenendo conto che le unità sono diverse — famiglie contro persone — non
> torna: la crosstab mostra 4.552 persone col codice 11 in nuclei da due,
> il che implica da solo almeno 4.552 famiglie interessate, quasi il
> doppio di `PF9`.
>
> Le due nozioni sono diverse. `PF9` conta famiglie **coabitanti in una
> stessa abitazione**, cioè nuclei anagrafici distinti sotto lo stesso
> tetto; il codice 11 è una relazione **dentro** un nucleo. Conferma
> indipendente: `PF1` − `A2` = 94.484 − 92.521 = **1.963**, cioè
> l'eccesso di famiglie sulle abitazioni occupate, che sta nell'ordine di
> `PF9` = 2.542.

Restano due letture candidate per il codice 11, e i dati disponibili non
le separano:

| lettura | a favore | contro |
|---|---|---|
| convivente *more uxorio* | rapporto con `Relpar=2` fra 0,34 e 0,43 per `Ncomp` 2, 3 e 4 — la firma di una categoria che segue i coniugi; età mediana 38 contro 57 dei coniugi, coerente con coppie non sposate più giovani | stranieri al 52% è alto per i conviventi italiani |
| altro non parente / coabitante | stranieri al 52% contro 15% degli intestatari | il rapporto costante con `Relpar=2` sarebbe una coincidenza |

**Evidenza indipendente dall'AVQ, 9/8/2026.** L'AVQ distingue
esplicitamente `RELPAR` 02 «coniuge di PR» da 03 «convivente
(coniugalmente) di PR», e ha anche 17 «persona legata da amicizia»: separa
cioè le due letture che a Parma restano confuse. Nel pool emiliano i
conviventi coniugali sono **252 contro 1.396 coniugi, il 18%**. A Parma il
codice 11 vale 14.725 contro 33.262 coniugi, il **44%**: due volte e mezzo
la quota regionale. Non impossibile in una città universitaria, ma è un
argomento **contro** la lettura «convivente *more uxorio*» e a favore di
«altro non parente». Evidenza debole — due fonti, due anni, due universi —
e nel verso opposto a quella del profilo demografico.

> **Conseguenza sostanziale, indipendente da quale delle due sia vera.**
> Il 7,4% dei residenti in famiglia sta in una relazione che non è
> coniugio né filiazione, e ha un profilo demografico nettamente diverso
> dal resto. Un nucleo con questa componente e una famiglia coniugale
> hanno regole di composizione diverse. L'assemblaggio richiede una
> **tipologia del nucleo** a monte, e `PF9` fornisce un vincolo per
> sezione per *una* delle tipologie.

---

## 3. Cosa NON è stato deciso dai dati

Per evitare che la nota si legga come più conclusiva di quanto sia:

- **la natura del codice 11** (7,4% delle unità): determinato che non è
  ascendente e che non coincide con `PF9`; non determinato se sia
  convivente *more uxorio* o altro non parente (§2.4);
- l'etichetta esatta dei codici 4–10 (2% delle unità);
- se il residuo geografico di M3 sia struttura familiare o stato civile
  travestito (§6.2).

---

## 4. Le misure

Tutte con `gsp.tvd`. `auto_totali=False` ovunque: le modalità di `Relpar`,
`Ncomp` e delle sezioni sono codici numerici, e `T.TOTALI` contiene `"0"`,
`"9"`, `"99"` — col default il modulo scarterebbe `Relpar=9` in silenzio.

| | domanda | forma |
|---|---|---|
| **M0** | la coppia si estrae insieme? | `indipendenza(Relpar, Ncomp)` |
| **M1/M2** | quali condizionanti servono | `d(S) = TVD(P(y\|S), P(y))` |
| **M3** | serve la geografia oltre la demografia? | TVD(P(y\|C4,quartiere), P(y\|C4)) |
| **M3′** | è il codice 11 a guidarla? | M3 senza `Relpar=11` |
| **M4a/M4b** | quale scala geografica? | comune→quartiere e quartiere→sezione |

Script: `scripts/diagnostica/misura_nucleo.py`,
`scripts/diagnostica/misura_nucleo_m4.py`.
Uscite: `note/misure/tvd_nucleo_parma_20260809.txt`,
`note/misure/tvd_nucleo_m4_parma_20260809_v2.txt`.

**Ogni netto è la TVD osservata meno un pavimento di rumore** ottenuto per
permutazione delle etichette del condizionante dentro il gruppo di
riferimento. Senza pavimento questi numeri non sono confrontabili fra
configurazioni: la TVD cresce con la rarefazione delle celle. È lo stesso
principio già applicato al MRE floor e alla distanza compositiva fra tier.

Le misure trattano `relpar` come **etichette categoriali**: né la
refutazione del codebook (§2.3) né quella sul codice 11 (§2.4) ne
alterano un solo numero, solo la lettura sostantiva delle celle in cima.

---

## 5. Risultati

### 5.1 M0 — la coppia va estratta insieme

```
TVD( P(relpar, ncomp5), P(relpar)·P(ncomp5) ) = 0,263   (11×5, 199.014 unità)
```

Il 26% della massa va spostato. Insieme all'incompatibilità logica
figlio ↔ `Ncomp=1`, chiude la questione: `(Relpar, Ncomp)` si estraggono
come coppia.

### 5.2 M1/M2 — ordine dei condizionanti

| variabile | condizionante | TVD min | mediana | max |
|---|---|---:|---:|---:|
| `ncomp5` | età (8 bin) | 0,061 | 0,293 | **0,410** |
| | cittadinanza | 0,032 | 0,091 | 0,151 |
| | sesso | 0,018 | 0,018 | 0,019 |
| `relpar` | età (8 bin) | 0,103 | 0,282 | **0,702** |
| | cittadinanza | 0,032 | 0,092 | 0,152 |
| | sesso | 0,080 | 0,083 | **0,086** |

L'età domina largamente entrambe. Il sesso è trascurabile sull'ampiezza
(0,018) ma **non** sul ruolo (0,08–0,086), e a posteriori è ovvio:
l'intestatario è più spesso maschio, il coniuge più spesso femmina.

Ordine per il collasso gerarchico: **zona → età → cittadinanza → sesso**,
con il sesso escludibile per l'ampiezza e da tenere per il ruolo.

Una cella non misurata su `relpar × età`: è il bin `0-8`, dove il supporto
è due modalità su undici. La guardia ha funzionato.

### 5.3 M3 — residuo geografico a demografia fissata

Condizionanti C4 = `sesso × età4 × cittadinanza`. Geografia = quartiere.

| | osservata | pavimento | **netto** | misurate / non |
|---|---:|---:|---:|---|
| `ncomp5` | 0,0586 | 0,0196 | **+0,0390** | 186 / 0 |
| `relpar` (tutti) | 0,0399 | 0,0151 | **+0,0247** | 177 / 9 |
| `relpar` (senza codice 11) | 0,0382 | 0,0127 | **+0,0255** | 172 / 8 |

Lo scarto è **strutturato, non sparso**: in cima Parma Centro e
Oltretorrente, cioè il centro storico, con n fino a 2.353. Nuclei piccoli
al centro, grandi in periferia — gradiente urbano classico, e la sua
nitidezza è una validazione della misura.

### 5.4 M4 — quale scala geografica

Senza condizionamento demografico (le celle demografiche rendono le
sezioni troppo sottili). Terzili di ampiezza: ≤54, 54–156, >156 persone.

| variabile | pesatura | M4a comune→quartiere | M4b quartiere→sezione | rapporto |
|---|---|---:|---:|---:|
| `ncomp5` | **per famiglia** | +0,0564 | +0,0492 | **0,87** |
| `ncomp5` | per persona | +0,0458 | +0,0639 | 1,40 |
| `relpar` | per persona | +0,0332 | +0,0212 | 0,64 |

La riga che vale è la prima: il vincolo dell'assemblaggio è sulle
**famiglie**, non sulle persone, e `ncomp5` calcolata sui residenti
sovrappesa i nuclei grandi. La pesatura per famiglia usa `1/Ncomp`, lo
stimatore già validato in §2.2.

La riga per persona riproduce la v1 dello script (1,39 → 1,40, M4a e M4b
identici alla quarta cifra): il codice della v2 non ha alterato
nient'altro.

**Netto per terzile di ampiezza** (`ncomp5`, per famiglia):

| terzile | osservata | pavimento | netto |
|---|---:|---:|---:|
| grandi (>156) | 0,0854 | 0,0370 | **+0,0484** |
| medie (54–156) | 0,1183 | 0,0669 | **+0,0514** |
| piccole (≤54) | 0,1483 | 0,0897 | +0,0586 |

Il netto è **quasi piatto** e sopravvive nelle sezioni grandi, dove il
pavimento è basso. Non è rarefazione.

*Due censure da dichiarare*: nelle corse per persona `MIN_SEZ_P=60` è
sopra il primo terzile e ne esclude l'intero contenuto; nella corsa per
famiglia il terzile «piccole» sopravvive solo per le sezioni piccole
ricche di famiglie, cioè quelle con molti unipersonali. **Il confronto
pulito è grandi contro medie.**

---

## 6. Cosa se ne conclude

### 6.1 Il ruolo si deriva a valle — anello 1 non si tocca

`Quartiere` **è** `zona`, cioè un attributo già vincolato di anello 1.
Quindi un residuo alla scala del quartiere non forza nulla nel modello
congiunto: dice solo che la tabella di derivazione deve condizionare anche
su `zona`, che a valle è disponibile per costruzione.

> **Decisione.** Il ruolo familiare si deriva a valle, con
> `(Relpar, Ncomp)` estratti come coppia, condizionati su
> `zona × età × cittadinanza × sesso`. Stesso pattern di `gsp.lavoro`.
> `|X|` invariato, nessun rifit, nessun nuovo zero strutturale.

### 6.2 L'asimmetria ampiezza / ruolo è il risultato di disegno

Su entrambe le misure, e con margine crescente scendendo di scala:

| | M3 (netto) | M4b/M4a |
|---|---:|---:|
| ampiezza del nucleo | +0,0390 | 0,87 |
| ruolo nel nucleo | +0,0247 | 0,64 |

> **Decisione.** L'anello 4 si separa in due parti con requisiti diversi:
>
> | | struttura geografica | vincolo necessario |
> |---|---|---|
> | ampiezza del nucleo | forte fino alla sezione | **marginali di sezione** (`PF3`–`PF8`) |
> | composizione interna | debole sotto il quartiere | condizionamento demografico + zona |

È la forma ipotizzata per l'uso di EU-SILC — vincoli geografici
sull'ampiezza, repertorio di configurazioni interne condiviso — ora
misurata invece che assunta.

**Limite sulla lettura di M3**, dovuto all'assenza dello stato civile: con
un condizionamento demografico più debole di quello disponibile in anello
1, parte di ciò che lo stato civile spiegherebbe finisce nel residuo. Un
M3 piccolo sarebbe stato una conclusione solida; un M3 **grande resta
ambiguo**, perché lo stato civile può travestirsi da geografia — i
quartieri differiscono per quota di coniugati. Servirebbe un controllo su
una fonte che contenga entrambi.

### 6.3 Ritrattazione — la correlazione TVD ~ ampiezza

La v1 di `misura_nucleo_m4.py` stampava la correlazione di Spearman fra
TVD e ampiezza della sezione (−0,438 su `ncomp5`) e la commentava:
«negativa e forte → quel che resta è rumore di campionamento residuo».

**Il commento era privo di potere diagnostico.** Sotto l'ipotesi nulla
quella correlazione è negativa comunque, perché le sezioni piccole hanno
TVD alta per costruzione. Il numero non discriminava fra segnale e rumore.

Sostituito dal netto per terzile di ampiezza (§5.4), che è il test
corretto e che ha dato risposta opposta a quella suggerita dal commento
ritirato: il segnale **c'è** anche dove il pavimento è basso.

---

## 7. Le due previsioni falsificate

Registrate nel docstring degli script **prima** di far girare la misura.

**(a) M3′ — il codice 11 guida il residuo geografico.** Attesa: il netto
crolla escludendolo, perché la popolazione col codice 11 è
geograficamente concentrata mentre la struttura coniugale lo è molto meno.
Misurato: **+0,0247 → +0,0255**, cioè sale di un soffio. *Falsificata.*

Spiegazione post-hoc, non verificata: la concentrazione geografica del
codice 11 è quasi interamente mediata dalla cittadinanza, che è già in C4.
Verificabile rifacendo M3 su `relpar` senza `citt` fra i condizionanti.

**(b) M4 — la sezione aggiunge poco.** Attesa: rapporto M4b/M4a sotto 0,3
su `ncomp5`, perché il gradiente centro-periferia visto in M3 opera alla
scala del quartiere. Misurato: **0,87** per famiglia, **1,40** per
persona. *Falsificata.* Il gradiente esiste (per persona: Parma Centro
0,128, Vigatto 0,087) ma è piccolo rispetto all'eterogeneità **dentro** il
quartiere.

Due previsioni su due falsificate, **entrambe nella stessa direzione**:
struttura fine sistematicamente sottostimata. Vale la pena tenerne conto
sulle prossime.

Un effetto non previsto emerso dalla pesatura per famiglia: la tabella
dello scarto per quartiere si riordina e si appiattisce — Parma Centro dal
primo posto (0,128) al quarto (0,095), escursione da 0,087–0,128 a
0,079–0,112. L'eterogeneità interna del centro storico era in buona parte
un effetto della pesatura per persona.

---

## 8. Punti aperti

### 8.1 Risolto — il vincolo di ampiezza esiste, ed è già in casa

*Era il «rischio principale» della v2.* Il rilascio del **Censimento
permanente al 31.12.2023 su Basi Territoriali 2021** contiene, per ogni
sezione:

| campi | contenuto |
|---|---|
| `PF1` | famiglie residenti, totale |
| `PF3`–`PF8` | famiglie con 1, 2, 3, 4, 5, 6+ componenti — **la distribuzione che serve** |
| `PF9` | famiglie coabitanti (fuori dalla partizione, §2.4) |
| `A2`, `A3`, `A5`, `A8` | abitazioni occupate da residenti, vuote, altri alloggi, totali |
| `EM1`–`EM6` | background migratorio in sei modalità |
| `NA1` | automobili di proprietà |

**Il metodo è trasferibile a tutti e undici i comuni.** La fonte è
registrata come `istat_sezioni_2023` dal 2 agosto 2026, lo zip è
scaricato, e `build_sezioni.py` produce i derivati per comune **con tutte
e 138 le colonne**: `data/submun/{comune}_sezioni_2023.csv` le contiene
già. Non c'è nulla da acquisire.

Il registro però dichiara `usabile_per: [geografia_subcomunale,
gerarchia_zone, vincoli_zona]`: la fonte è entrata in pipeline per la sola
gerarchia zona/quartiere, ed è la ragione per cui questi campi sono
rimasti invisibili. **Patch necessaria al registro**: estendere
`usabile_per` con `struttura_familiare`, `abitazioni_per_sezione`,
`background_per_sezione`, e ampliare l'`universo` per dire cosa
contengono le ~130 colonne.

*Da annotare fra le trappole*: la nota metodologica ISTAT avverte che fra
2021 e 2023 circa **400.000 famiglie** sono state riallocate per un
cambio di procedura di geocodifica (nuova cartografia catastale WFS,
catasto 2023 invece di 2020). Le differenze per sezione fra le due annate
**non sono tutte demografiche**.

### 8.2 Aperto — e più grande dell'anello 4

**`EM1`–`EM6` è il `background` di anello 1, a livello di sezione.**
Corrispondenza uno a uno con le sei modalità in uso:

| campo | modalità GSP |
|---|---|
| EM1 Italiani dalla nascita nati in Italia | `italiano_nativo` |
| EM2 Italiani dalla nascita nati all'estero | `italiano_rientrato` |
| EM3 Italiani acquisiti nati in Italia | `naturalizzato_g2` |
| EM4 Italiani acquisiti nati all'estero | `naturalizzato_immigrato` |
| EM5 Stranieri e apolidi nati in Italia | `straniero_g2` |
| EM6 Stranieri e apolidi nati all'estero | `straniero_immigrato` |

Oggi il background migratorio ha **risoluzione di zona**, non di sezione —
è fra i limiti dichiarati del riferimento v22 e parte dell'assunzione (8).
Con `EM1`–`EM6` diventa vincolabile per sezione su tutti gli undici
comuni. Tocca un attributo **già in produzione**, non uno da costruire, e
merita una misura propria prima di qualunque decisione.

### 8.3 Gli altri

**(a) La codifica di `Relpar` presso l'ufficio statistica del Comune.**
Domanda precisa: *`Descrizione_codifica_campi_2025.csv` dichiara per
`Relpar` una classificazione che i dati contraddicono su almeno quattro
codici (4, 5, 8, 9) per profilo d'età. Quale codifica usa effettivamente
il file, e esiste un tracciato della versione in uso? In particolare il
codice 11 (14.725 persone, età mediana 38, 52% stranieri) non è
compatibile né con «Zio/Zia» né con le famiglie coabitanti del
censimento (`PF9` = 2.542).* Le tabelle §2.3 e §2.4 vanno allegate.

**(b) Il costo della validazione.** `Ncomp` e `Relpar` erano nella lista
«validazione esterna, mai usate per generare». Usandoli per generare,
Parma smette di essere il comune dove validare la struttura familiare. Due
uscite: tenere per la validazione ciò che resta (`Tipores`, co-occorrenza
di nazionalità) più `PF3`–`PF8`; oppure split delle sezioni — generare su
metà, validare sull'altra. La seconda è più costosa e più difendibile.

**(c) EU-SILC** come repertorio di configurazioni interne al nucleo e come
controllo esterno di realismo (divari d'età genitore-figlio, differenza
d'età fra partner). Il PUF è sintetico per dichiarazione Eurostat: serve
solo a scrivere il parser. Il SUF va richiesto.

**(d) Coda dell'assemblaggio.** Mediana 47 famiglie per sezione, ma
massimo 748 e primo quartile 18. Metà delle sezioni sono banali; la coda
richiede un algoritmo che regga qualche centinaio di nuclei.

**(e) La tipologia del nucleo** come variabile a monte dell'assemblaggio,
resa necessaria da §2.4. `PF9` dà un vincolo di sezione per una delle
tipologie; per le altre serve una fonte.

**(g) I netti di M3 e M4 sono sottostimati.** La base contro cui si
misura ogni unità include l'unità stessa: con ~29 sezioni per zona pesa
~1/29 della propria base, che ne risulta tirata verso di lei. Corretto in
`scripts/diagnostica/residuo.py` (base leave-one-out + pavimento
bootstrap parametrico), che su una misura analoga alza i netti di ~8%.
L'errore è **conservativo** — nessuna conclusione di questa nota cambia —
ma M4 va rifatto con `residuo.py` prima che i numeri finiscano in un
articolo. Diagnosi completa in `nota_background_sezione_v3` §7.2.

**(f) Il conteggio degli edifici residenziali** non è nel file regionale
(nessun blocco `E`), benché la pagina ISTAT lo annunci. Da cercare negli
attributi degli shapefile delle Basi Territoriali o in `Comuni_2023.zip`.

---

## 9. Per il paper sul criterio TVD

Questo è un terzo caso applicativo, con una struttura **diversa** dagli
altri due. Su istruzione e settore economico il criterio decideva «dentro
o fuori dal modello congiunto». Qui decide **quale livello geografico
serve**, che è un uso non ancora coperto dallo scheletro.

Gli elementi riutilizzabili: il pavimento per permutazione come parte
integrante della misura; il rapporto fra netti a due scale come modo di
rendere leggibile una TVD che altrimenti non ha riferimento; il netto per
strato come test contro la rarefazione; e due previsioni registrate e
falsificate, che sono la parte più difendibile del capitolo.

Da citare come stato dell'arte, non da ignorare: **l'ISTAT esegue già
internamente l'assegnazione famiglia→edificio**. Il Registro Statistico di
Base dei Luoghi include un registro degli edifici e delle unità
immobiliari con coordinate, e il linkage RBI–RSBL associa ogni famiglia
alla sua abitazione. Non è ridistribuibile a livello individuale, ed è
esattamente il caso d'uso della sintesi da aggregati.

*§9 è scritta senza aver riletto `paper_criterio_scheletro_v1.md`: da
allineare alle sezioni esistenti.*
