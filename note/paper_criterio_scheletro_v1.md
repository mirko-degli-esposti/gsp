# Which variables belong in the joint model?

**Scheletro per un articolo breve** — 5 agosto 2026
Mirko Degli Esposti, Università di Bologna

Titolo di lavoro: *Which variables belong in the joint model? A
total-variation criterion for attribute selection in population
synthesis.*

Formato: methods paper corto, 6-8 pagine. Sede naturale JASSS, che
conosce già il filone; alternative in §7.

---

## 1. Il problema

La letteratura sulla sintesi di popolazioni si concentra quasi
interamente su **come** riprodurre una distribuzione congiunta:
iterative proportional fitting, reti bayesiane, MCMC e campionamento di
Gibbs, modelli a classi latenti, e più di recente GAN e autoencoder
variazionali. Il problema è formulato in modo esplicito: la congiunta
non è accessibile direttamente, e riprodurla è il compito primario.

La domanda **quali** variabili debbano stare in quel modello congiunto
non è trattata come una decisione da prendere.

Nella pratica viene risolta in due modi, entrambi impliciti.

**Per disponibilità dei dati**: si mettono nel modello le variabili per
cui esistono marginali territoriali, e si lascia fuori il resto. Lavori
recenti distinguono esplicitamente *conditioned attributes* da
*unconditional variables*, ma il confine coincide con quello dei dati
disponibili.

**Per convenienza a valle**: nella pratica dei modelli di trasporto le
categorie marginali si scelgono per far combaciare gli attributi che
alimentano i modelli di scelta successivi.

Nessuno dei due criteri riguarda una proprietà del fenomeno. E il costo
di sbagliare non è simmetrico: aggiungere una variabile al modello
congiunto moltiplica lo spazio degli stati, può introdurre zeri
strutturali che rendono riducibile la catena di campionamento, e vincola
il solver — mentre lasciarla fuori costa solo l'informazione che quella
variabile porta, se ne porta.

**Tesi dell'articolo**: la decisione si può prendere con una misura, la
misura è semplice, e prenderla senza misurare porta a modelli peggiori.

---

## 2. Il criterio

### 2.1 Formulazione

Sia `X` la variabile candidata e `C` l'insieme degli attributi già nel
modello congiunto. Per ogni sottoinsieme `S ⊆ C` di condizionamento
possibile a valle, si misura

    d(S) = TVD( P(X | S) , P(X) )

cioè la distanza in variazione totale fra la composizione di `X`
condizionata su `S` e quella marginale.

La regola:

- se `d` è grande per un `S` **disponibile a valle**, la variabile può
  essere derivata: il condizionamento cattura ciò che serve;
- se `d` è grande solo per un `S` **non disponibile a valle** — tipico
  della geografia fine — la variabile deve stare nel modello congiunto;
- se `d` è piccolo per ogni `S`, la variabile è quasi indipendente e la
  si può assegnare senza condizionamento.

### 2.2 Perché la TVD

È la quota di massa da spostare per trasformare una composizione
nell'altra: interpretabile senza riferimento a una scala, limitata fra
0 e 1, e confrontabile fra variabili con numero di modalità diverso —
purché **definite sullo stesso supporto** (§2.4).

Alternative da discutere: Hellinger, Jensen-Shannon, chi quadro. La TVD
si presta meglio perché la sua interpretazione — «una scheda su cinque
sarà sbagliata» — è direttamente la quantità che interessa a chi guarda
il risultato.

### 2.3 Il caso della coppia

Se due variabili candidate `X` e `Y` sono entrambe derivabili, resta da
decidere se derivarle separatamente o congiuntamente. La misura è la
stessa applicata a un altro confronto:

    TVD( P(X, Y | S) , P(X | S) · P(Y | S) )

Se è piccola, si possono derivare separatamente e ciascuna col suo
condizionamento migliore. Se è grande, vanno estratte insieme, anche a
costo di un condizionamento peggiore per entrambe.

### 2.4 Il controllo che il criterio richiede

> **Una TVD calcolata su supporti diversi non è una misura.**

Nelle applicazioni di §3 e §4 questo errore si è presentato **quattro
volte** su fonti censuarie reali, e ogni volta ha prodotto valori
plausibili ma privi di significato: distanze di 0,95 su categorie con un
solo supporto pubblicato, composizioni che sommavano a più di uno perché
mescolavano aggregati e foglie di una gerarchia non dichiarata.

Il criterio va quindi accompagnato da un controllo di partizione:
contare i supporti prima di confrontare le distanze, e verificare che le
foglie ricostruiscano il totale. È metodologicamente banale e
praticamente indispensabile.

---

## 3. Applicazione 1 — il titolo di studio

**Contesto.** Una popolazione sintetica di dodici comuni italiani,
generata con un modello a massima entropia su otto variabili
demografiche fra cui `istruzione` a sei modalità, condizionata su sesso,
età e zona sub-comunale.

**Domanda.** Il titolo di studio dettagliato — 458 modalità del
censimento 2011, dalla licenza elementare alle classi di laurea — va
aggiunto al modello congiunto?

**Misura.** [DA COMPLETARE con la tabella delle TVD]

**Esito.** A valle. Il condizionamento su sesso, età e regione cattura
quasi tutta la variazione; la geografia fine, che sarebbe l'argomento per
il modello congiunto, arriva gratis dalla variabile `istruzione` già
presente. Aggiungere 458 modalità allo spazio degli stati non
comprerebbe nulla.

**Nota metodologica.** La derivazione ha richiesto un raccordo dichiarato
fra le 458 modalità della fonte e le sei categorie del modello,
verificato come partizione su nove rami dell'albero censuario, con scarti
inferiori allo 0,01%.

---

## 4. Applicazione 2 — il settore economico

**Domanda.** Il settore di attività va nel modello congiunto? Un livello
del sistema — K10C — lo prevedeva già.

**Misure.**

| dimensione | TVD |
|---|---|
| istruzione | 0,105 – 0,390 |
| sesso | 0,152 – 0,188 |
| comune vs regione | 0,029 – 0,202 |
| età, 30-55 anni | 0,03 – 0,08 |

**Esito.** A valle, e la coppia settore × posizione professionale va
estratta **insieme**: la distanza fra la congiunta e il prodotto delle
marginali è 0,138–0,166 su cinque territori, stabile quindi strutturale.
Estrarle separatamente produce combinazioni palesemente assurde —
dirigenti in agricoltura, coadiuvanti familiari nella pubblica
amministrazione.

**Il punto interessante.** Le due perdite sono numericamente
confrontabili — 0,15 per l'indipendenza, 0,105–0,390 per il
condizionamento sul titolo — ma non lo sono per **visibilità**. Una
distanza di 0,15 sulla congiunta produce individui che chiunque
riconosce come impossibili; una di 0,20 sul condizionamento produce
individui plausibili con proporzioni un po' storte.

> Un dirigente agricoltore lo nota chiunque. Che i laureati siano il 12%
> invece del 18% in un settore, no.

È un criterio secondario che il numero da solo non dà, e vale la pena
enunciarlo: **a parità di distanza, si preserva la struttura che rende
riconoscibile un errore**.

---

## 5. Il controesempio

Il livello K10C del sistema aggiungeva il settore economico al modello
congiunto. La decisione era stata presa senza misurare, ed è istruttiva
perché tutti e tre i costi sono documentati.

**Lo spazio degli stati** passa da 6,99·10⁴ a 3,7·10⁷.

**La catena di campionamento diventa riducibile.** Il vincolo che lega
condizione professionale e settore — necessario, perché senza di esso il
modello a massima entropia tratta le due variabili come indipendenti e
produce «pensionati nell'industria» — introduce zeri strutturali che
disconnettono il grafo di compatibilità bipartito. La catena è
irriducibile precisamente in corrispondenza del punto di convergenza.
Su un comune il livello produce 3.417 individui con combinazioni
logicamente impossibili (1,72%), contro zero del livello inferiore su
undici comuni.

**E il vincolo condiziona sulla variabile sbagliata**: sul sesso (TVD
0,152–0,188) ignorando l'istruzione (0,105–0,390).

Il terzo costo è quello che il criterio avrebbe evitato, ed è anche
quello che resta valido se i primi due venissero risolti.

---

## 6. Discussione

**Cosa il criterio non dice.** Nulla su come stimare la congiunta una
volta scelte le variabili; nulla sulla scelta del numero di modalità;
nulla su variabili continue, dove la TVD richiede una discretizzazione
che è essa stessa una scelta.

**Il limite delle fonti.** Il criterio si calcola su tavole aggregate
pubblicate, che non incrociano tutto con tutto. In §4 sette sezioni su
ventuno non erano incrociate con il titolo di studio, e sono il 21,4%
degli occupati: le TVD misurate sono quindi limiti inferiori. Il
criterio dice cosa fare **dato ciò che si può misurare**, e la copertura
della misura va dichiarata insieme al risultato.

**Generalizzabilità.** Il criterio non dipende dal metodo di sintesi: si
applica a IPF, reti bayesiane, modelli generativi profondi. Dipende solo
dall'esistere di una distinzione fra variabili del modello congiunto e
attributi assegnati a valle — distinzione che tutti i metodi hanno, e
che quasi nessuno esplicita.

---

## 7. Sedi possibili

| | |
|---|---|
| **JASSS** | conosce il filone, open access, tempi medi |
| Transportation Research Part C | dove sta gran parte della letteratura di population synthesis |
| Journal of Transport Geography | se si enfatizza l'aspetto territoriale |
| Computational Urban Science | recente, aperta a metodi |

---

## 8. Nota bibliografica — cosa cercare

### 8.1 Verificare che il gap sia reale

**Questa è la ricerca più importante**: l'affermazione «nessuno propone
un criterio per la selezione delle variabili» è quella che un revisore
verifica per prima. Termini da provare, in inglese:

```
attribute selection population synthesis
variable selection synthetic population
which variables joint distribution synthetic population
control variables selection population synthesis
marginal selection IPF population synthesis
```

E la formulazione più vicina, che potrebbe esistere in altra forma:

```
conditional independence assumption population synthesis
attribute dependency population synthesis
```

Se qualcuno l'ha già fatto, quasi certamente **non** con questa
formulazione ma come parte di un lavoro applicativo — e allora
l'articolo diventa «esplicitiamo e misuriamo ciò che si fa
implicitamente», che è un contributo minore ma ancora valido.

### 8.2 I lavori che vanno citati comunque

**Sulla formulazione del problema come stima della congiunta**: la
rassegna in Sun & Erath sulla rete bayesiana (Transportation Research C,
2015) contiene la formulazione standard e la critica al *sequential
modeling framework*, che è esattamente il condizionamento a valle fatto
senza criterio.

**Sul Gibbs sampling in population synthesis**: Farooq et al. 2013 è il
riferimento canonico, citato da tutti i lavori successivi.

**Sulla distinzione conditioned/unconditional**: il lavoro su CT-GAN
(arXiv 2510.00871, ottobre 2025) la usa esplicitamente — età e sesso
condizionati per zona, WORK non condizionato — ed è **la citazione più
utile** perché mostra la distinzione senza il criterio. Da verificare se
sia pubblicato o solo preprint.

**Sulla pratica applicata**: TF Resource (`tfresource.org`) documenta
che le categorie marginali si scelgono in funzione dei modelli di scelta
a valle. È grigia ma citabile come evidenza di prassi.

**Su IPF e i suoi limiti**: la letteratura è vasta; per il punto sulla
crescita dello spazio degli stati basta il lavoro su JDI (JASSS 20/4/16,
2017), che quantifica 1,4·10⁸ combinazioni come limite pratico.

**Sui modelli generativi profondi**: Borysov et al. sulla predizione di
combinazioni rare (arXiv 1909.07689) per mostrare che il problema del
supporto è noto in altra forma.

### 8.3 Da cercare fuori dal campo

Il criterio somiglia a cose che esistono altrove e che varrebbe la pena
citare per collocarlo:

- **selezione di variabili nei modelli grafici** — structure learning,
  criteri di indipendenza condizionale (PC algorithm, score-based);
- **collapsibility** nei modelli log-lineari: quando una tabella si può
  marginalizzare senza perdere informazione sull'associazione. È
  probabilmente il concetto statistico più vicino, e vale la pena
  guardarlo bene — se il criterio fosse un caso particolare di
  collapsibility, va detto e citato;
- **feature selection** basata su mutua informazione, dove il rapporto
  fra TVD e informazione mutua è noto.

La **collapsibility** è quella su cui cercherei per prima: se c'è un
teorema che dice quando una variabile si può togliere da un modello
log-lineare senza distorcere le associazioni residue, il criterio
diventa la sua versione operativa e misurata — il che lo rafforza invece
di indebolirlo.

### 8.4 Termini italiani, se si volesse una versione per statistici ufficiali

```
sintesi di popolazioni sintetiche
selezione delle variabili di controllo
riproporzionamento iterativo
```

Ma il pubblico sarebbe diverso e l'articolo pure: più sulle fonti e
sulla riproducibilità che sul criterio.

---

## 9. Materiale disponibile

| | |
|---|---|
| misure | `note/nota_settore_economico_v3.md` |
| implementazione | `gsp.istruzione`, `gsp.lavoro` |
| controesempio | `cs_build.py`, livelli K9C e K10C |
| dati | dodici comuni, fonti ISTAT aperte, tutto riproducibile |

Il codice e le fonti sono pubblici o pubblicabili: l'articolo può
dichiarare la riproducibilità completa, che in questo campo non è
scontata.
