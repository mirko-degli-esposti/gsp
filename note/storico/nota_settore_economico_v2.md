# Il settore economico: dentro il MaxEnt o a valle?

**v2 — 5 agosto 2026** · censimento 2011, `DICA_CARATT_ATTL`
Sostituisce la v1, che misurava la variabile sbagliata (§4).

Domanda: il settore di attività va aggiunto come variabile del MaxEnt
(livello K10C) o attribuito a valle come il titolo di studio?

La risposta è **a valle**, e non per comodità: la derivazione condiziona
su istruzione *e* sesso, il vincolo K10C solo sul sesso.

---

## 1. Da dove nasce la domanda

Due tavole censuarie sono scaricate, normalizzate e ricostruite a ogni
rigenerazione, ma **non producono alcun attributo** nella popolazione:

| file | contenuto | usato |
|---|---|---|
| `c9_sex_posizione_prof.csv` | sesso × dipendente/indipendente | **mai** |
| `c10_sex_settore.csv` | sesso × 6 settori | solo a K10C |

La ragione è strutturale: un vincolo può agire solo su variabili che
stanno nello spazio degli stati. A K9C non esiste né `settore` né
`posizione`, quindi quei due file non hanno dove appoggiarsi.

`VAR_ORDER_K10 = VAR_ORDER_K9 + ["settore"]`: il settore è l'unica
differenza fra i due livelli.

Su `c9` la verifica è esplicita: l'unico riferimento in tutto il codice è
in `fetch_comune.py`, che lo scarica. **Nessuno lo legge.**

---

## 2. Perché K10C non è la risposta

Il livello K10C aggiunge il settore e paga tre prezzi.

**Lo spazio degli stati passa a 37 milioni** contro i 69.888 di Parma
K7C. Il solver esatto non arriva, e il Gibbs diventa necessario.

**La catena diventa riducibile.** Il blocco `MC` impone
`condizione × settore` come vincolo diretto — serve a evitare il bug
dell'indipendenza spuria, che senza di esso produrrebbe «pensionati
nell'industria» — e `S_settore_non_occupati` impone il complementare.
Insieme creano zeri strutturali su entrambi i lati che disconnettono il
grafo di compatibilità bipartito, e la catena è irriducibile precisamente
a λ*, cioè nel punto in cui dovrebbe convergere. È lo stesso meccanismo
del blocco `GC` per cittadinanza × background, dichiarato nei commenti di
`cs_build.py` (riga 552).

**Su Brescia produce 3.417 individui impossibili** (1,72%), contro zero
di K9C su undici comuni.

Ma il prezzo peggiore è il terzo, ed è emerso solo con questa misura:
**il blocco condiziona il settore sul SESSO soltanto**, ignorando
l'istruzione.

---

## 3. La misura

Fonte: `DICA_CARATT_ATTL`, censimento 2011, quattordici dimensioni.
Filtri: occupati (`EMPLP`), stato civile / cittadinanza / regime orario /
durata / carattere dell'occupazione tutti al totale.

Metrica: **distanza in variazione totale** fra la composizione di un
sottogruppo e quella complessiva. Va da 0 a 1 ed è la quota di massa da
spostare per trasformare l'una nell'altra.

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

Ventuno sezioni, somma 1,000.

### Quanto ciascuna variabile sposta la composizione

| dimensione | TVD |
|---|---|
| istruzione, **titoli numerosi** | **0,105 – 0,390** |
| istruzione, titoli rari | 0,31 – 0,49 |
| sesso | 0,152 – 0,188 |
| comune vs regione | 0,029 – 0,159 |
| età, 30-55 anni | 0,03 – 0,08 |
| età, 20-24 e 60-64 | 0,12 – 0,20 |

Il dettaglio per titolo, con la numerosità che dice quanto fidarsi:

| titolo | occupati | TVD |
|---|---|---|
| diploma 4-5 anni | 5.086.431 | 0,105 |
| diploma 2-3 anni | 1.220.895 | 0,128 |
| licenza media | 4.550.378 | 0,195 |
| licenza elementare | 652.276 | 0,307 |
| laurea triennale | 354.414 | 0,313 |
| **laurea 4-6 anni** | **1.877.753** | **0,390** |
| diploma universitario v.o. | 243.069 | 0,491 |

### Il territorio: quanto costa il ripiego regionale

| comune | TVD dalla regione |
|---|---|
| Bologna | 0,159 |
| Parma | 0,106 |
| Modena | 0,089 |
| Reggio Emilia | 0,042 |
| Ravenna | 0,029 |

Bologna è capitale amministrativa e ha una composizione terziaria che si
discosta molto; Ravenna è quasi identica alla media regionale. **Il
ripiego costa poco dove il comune è ordinario e molto dove è
particolare**, che è precisamente il caso in cui servirebbe. È
un'asimmetria che vale per qualunque cascata comune→regione, incluse
quelle già in uso.

---

## 4. Un errore di lettura, e cosa insegna

La v1 di questa nota riportava TVD fra 0,17 e 0,50 per l'istruzione,
attribuite alla composizione **settoriale**. Erano calcolate sulla
colonna sbagliata.

Il file dati non ha intestazione, e le quattordici dimensioni vanno
identificate dai valori. Ho assegnato la colonna 8 ad `ATECO_2007`
perché conteneva codici come `EO`, `TW`, `MANAG` — che invece sono di
`OCCUPAZIONE`, il grande gruppo professionale. L'ATECO vero è la
colonna 10.

Il metodo che scioglie il dubbio senza congetture: confrontare l'insieme
dei valori di ogni colonna con ciascuna codelist del pacchetto METADATA,
e assegnare per contenimento. L'assegnazione esce da sola.

**E un secondo errore, più insidioso**, trovato subito dopo: tre titoli
di studio davano TVD di 0,954, vicinissima al massimo teorico. Non era
un segnale ma un artefatto — quei titoli hanno **una sola sezione
pubblicata**, sempre `A` agricoltura, mentre tutti gli altri ne hanno
quattordici. Confrontare una composizione su 1 supporto con una su 21 non
misura nulla.

> **Una metrica calcolata su supporti diversi non è comparabile.**
> È la terza volta che questo schema si presenta, dopo il `residuo_quota`
> fra comuni con zonizzazioni diverse e l'MRE fra comuni con numero di
> zone diverso. Il controllo è sempre lo stesso: contare i supporti prima
> di confrontare le distanze.

---

## 5. La conclusione

Il vincolo K10C condiziona sul **sesso** (TVD 0,152-0,188) e ignora
l'**istruzione**, al prezzo di trentasette milioni di stati e di una
catena di Gibbs riducibile.

Ma il margine è più stretto di quanto la v1 suggerisse: l'istruzione
domina **agli estremi della scala** — laurea 0,390, elementare 0,307 —
mentre nel mezzo il diploma quinquennale sta a 0,105, sotto il sesso.

La conclusione corretta non è «l'istruzione conta più del sesso» ma:

> **contano entrambe, e la derivazione a valle può usarle tutte e due
> insieme al comune, mentre il vincolo K10C ne usa una sola.**

Il che non toglie nulla al MaxEnt: dice che *questa* variabile non ha
bisogno di starci. La differenza con la cittadinanza è che lì la
struttura geografica è forte e va catturata congiuntamente, mentre qui la
geografia arriva già da `condizione`, che è vincolata su zona.

---

## 6. Come si costruirebbe

```
P(ateco | istruzione, sesso, comune)      6 comuni su 11
P(ateco | istruzione, sesso, regione)     i restanti 5
```

Cascata dichiarata, come i tier del paese di cittadinanza. I comuni
presenti nella tavola sono Parma, Modena, Bologna, Brescia, Reggio
Emilia e Ravenna; mancano Rimini, Ferrara, Forlì, Piacenza e Castenaso.

**Non condizionare sull'età** fra i 30 e i 55, dove non porta nulla.
Semmai trattare a parte i due estremi.

**L'universo sono gli occupati**, il 48,0% della popolazione (81% nelle
età centrali). Per tutti gli altri il settore è `non_applicabile` per
costruzione, non mancante — come il missing strutturale delle AVQ.

---

## 7. Limiti

**Sette sezioni su ventuno non sono incrociate con il titolo di studio**:
mancano `D` energia, `E` acqua e rifiuti, `H` trasporti, `J` informazione
e comunicazione, `L` immobiliare, `M` attività professionali, `N` servizi
alle imprese. Sono il **15,9%** degli occupati e includono i servizi
digitali e professionali — proprio dove i laureati si concentrano. La
loro assenza dall'incrocio fa probabilmente **sottostimare** la
dipendenza dall'istruzione, quindi le TVD riportate sono un limite
inferiore.

**Cittadinanza e settore non sono mai incrociati**: `ISO1` è sempre al
totale quando l'ATECO è specificato (verificato 5/8/2026, zero righe con
entrambi). L'assunzione di indipendenza non è verificabile qui.
Una parte dell'effetto passa comunque per via indiretta — gli stranieri
hanno una distribuzione d'istruzione diversa, e il settore è condizionato
sull'istruzione. Si perde l'effetto **residuo**, la concentrazione a
parità di titolo, che esiste ma è di secondo ordine.

**Sotto il comune non c'è niente**: 163 territori, di cui 25 comuni, e
nessuna articolazione sub-comunale.

| attributo derivato | risoluzione territoriale |
|---|---|
| titolo di studio | regione |
| **settore economico** | **comune, per 6 comuni su 11** |
| attributi AVQ | regione |

**La fonte ha quindici anni.** Il trasferimento per coorte è pulito per
chi era già nel mercato del lavoro nel 2011, ma la struttura settoriale
italiana è cambiata dopo: crescita dei servizi digitali, contrazione
della manifattura.

**La tavola comunale `DICA_CARATT_ATTL_COM` non serve**: copre tutti gli
8.230 comuni ma con sette sole categorie (totale, industria, servizi, più
quattro aggregati), senza istruzione.

---

## 8. Cosa fare di K10C

**Lasciarlo dov'è**, come materiale sperimentale escluso dalla
produzione. Conserva la storia della riducibilità, che è un risultato
metodologico e non un difetto da nascondere.

Quello che cambia è la motivazione per non usarlo: non più «produce
combinazioni impossibili», ma **«condiziona su una variabile sola quando
ne servirebbero tre»**. È una ragione più forte, e resta valida anche se
la riducibilità venisse risolta.

---

## 9. E le altre variabili della stessa tavola

`DICA_CARATT_ATTL` non ha solo il settore. Nella stessa tavola, con lo
stesso universo e lo stesso condizionamento:

| dimensione | voci | esempi |
|---|---|---|
| `OCCUPAZIONE` | 11 | «attività operaia qualificata», «lavoro esecutivo d'ufficio», «gestione di un'impresa» |
| `PROFILO_PROF` | 47 | dirigente, quadro, impiegato, operaio, apprendista, imprenditore |
| `CARATT_OCC` | 4 | tempo determinato, indeterminato, stagionale |
| `REGIME_ORARIO` | 8 | tempo pieno, parziale orizzontale/verticale/misto |

**`OCCUPAZIONE` è probabilmente la più forte per una biografia**: dice
*cosa fa* una persona, non *dove* lavora. «Attività operaia qualificata»
comunica più di «manifattura».

**`PROFILO_PROF` rende superfluo `c9`**: quarantasette modalità contro
due, dalla stessa fonte.

Attenzione però: `OCCUPAZIONE` ha solo **1.208 righe** con valore
specificato contro le decine di migliaia dell'ATECO, e i suoi incroci
sono più sparsi. Va verificato caso per caso quali combinazioni esistano
prima di contarci.

Se si deriva il settore, conviene derivare anche queste nello stesso
passo: stessa fonte, stesso universo, stesso condizionamento.
