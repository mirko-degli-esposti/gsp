# Le code di `PUNTIFI10` — quanti agenti distinti si possono davvero fare

**v2 — 6 agosto 2026**
Sostituisce la v1: il tetto misurato è diverso da quello stimato, e il
campionamento per donatore introduce una distorsione demografica che va
dichiarata.

Serve a decidere se un esperimento di taratura sul modello di SIVE si
possa rifare con individui veri invece che con personas costruite, da
quale comune conviene partire, e fino a quanti agenti.

---

## 1. La domanda

Il disegno di SIVE-Montelago funziona così: si sceglie un valore latente
di fiducia, si genera una storia che lo codifica senza nominarlo,
l'agente riceve solo la storia, e la batteria ricava un valore osservato.
Se l'osservato torna al latente, lo strumento è tarato.

Con una popolazione GSP il latente non si sceglie più: è `PUNTIFI10` del
donatore AVQ, cioè un dato osservato. Meglio per la validità esterna, ma
apre due dubbi pratici:

- **le code esistono?** Senza casi estremi la taratura non si misura;
- **quanti agenti DISTINTI ci sono?** Non quanti individui, ma quanti
  vettori AVQ diversi: due agenti con lo stesso vettore non sono evidenza
  indipendente, sono la stessa risposta con un altro nome.

La seconda è la domanda che conta.

---

## 2. La distribuzione

Parma, 93.173 occupati con `PUNTIFI10` valorizzato:

| valore | individui | quota | |
|---|---|---|---|
| 0 | 8.708 | 9,35% | ███████████ |
| 1 | 3.099 | 3,33% | ███ |
| 2 | 4.366 | 4,69% | █████ |
| 3 | 4.009 | 4,30% | █████ |
| 4 | 6.270 | 6,73% | ████████ |
| 5 | 14.555 | 15,62% | ██████████████████ |
| 6 | 17.111 | 18,36% | ██████████████████████ |
| 7 | 15.460 | 16,59% | ███████████████████ |
| 8 | 11.901 | 12,77% | ███████████████ |
| 9 | 3.776 | 4,05% | ████ |
| 10 | 3.918 | 4,21% | █████ |

**Le code ci sono e sono grosse**: 17,4% sotto 3, 21,0% sopra 7. Il picco
a zero — quasi un decimo del totale — è la firma tipica delle scale di
fiducia istituzionale, dove chi non si fida sceglie l'estremo invece di
graduare.

---

## 3. Undici comuni, e la sorpresa

| comune | occupati | donatori | coda bassa | don. | coda alta | don. |
|---|---|---|---|---|---|---|
| **Brescia** | 88.425 | **6.681** | 18,2% | **1.137** | 19,2% | **1.326** |
| Bologna | 184.827 | 4.005 | 17,3% | 649 | 20,9% | 878 |
| Parma | 93.173 | 3.906 | 17,4% | 640 | 21,0% | 852 |
| Modena | 84.439 | 3.913 | 17,5% | 635 | 20,8% | 856 |
| Reggio Emilia | 80.170 | 3.861 | 17,6% | 634 | 21,0% | 833 |
| Ravenna | 68.487 | 3.830 | 17,3% | 629 | 21,1% | 833 |
| Rimini | 63.531 | 3.885 | 17,2% | 632 | 21,1% | 851 |
| Ferrara | 56.942 | 3.831 | 17,3% | 626 | 21,0% | 823 |
| Forlì | 52.819 | 3.784 | 17,5% | 628 | 21,4% | 820 |
| Piacenza | 46.182 | 3.748 | 17,5% | 623 | 21,1% | 807 |
| Castenaso | 7.706 | 2.670 | 16,8% | 456 | 21,5% | 564 |

### Le quote sono identiche ovunque

17,2–18,2% nella coda bassa, 19,2–21,5% nell'alta, su comuni che vanno da
7.706 a 184.827 occupati.

Non è un fatto sui comuni: **è un fatto sul pool di donatori**. La
distribuzione di `PUNTIFI10` viene dall'hot-deck condizionato sulla
regione, quindi undici comuni la replicano quasi identica. Le differenze
residue vengono dalla composizione demografica, che sposta i pesi delle
celle di condizionamento.

È lo stesso fenomeno del tier 0 per il paese di cittadinanza, su un altro
asse: **la geografia degli attributi AVQ si ferma alla regione**.

### Brescia ha il doppio dei donatori

1.137 e 1.326 contro i ~630 e ~840 degli emiliani. Il rapporto è **1,77**,
esattamente quello fra i due pool: 8.111 donatori lombardi contro 4.629
emiliani.

> **Per un esperimento con agenti il comune migliore è Brescia — non
> Bologna.** Bologna ha il doppio degli occupati e *meno* donatori
> distinti nelle code: 649 contro 1.137. Il numero che conta non è quante
> persone ci sono ma quante risposte diverse esistono, e quella è una
> proprietà del pool regionale.

È un criterio che nessuno cercherebbe guardando la dimensione dei comuni.

---

## 4. Due modi di campionare, e il tetto vero

### 4.1 Per individuo — le collisioni arrivano presto

Il campionamento naturale: si estraggono N individui a caso dalla coda.
Sembrerebbe sicuro fin quasi al numero di donatori disponibili.

**Non è così.** È il paradosso del compleanno: pescando da una coda dove
ogni donatore copre decine di individui, due estrazioni cadono sullo
stesso donatore molto prima che i donatori si esauriscano.

Misurato sui dati veri:

| | Brescia | Parma |
|---|---|---|
| n = 120, replica totale | **0,8%** | **5,8%** |
| n = 120, gruppo LOW | 0,0% | **12,5%** |
| n = 600, replica totale | **10,3%** | — |
| n = 600, gruppo HIGH | 15,0% | — |

A 120 agenti Brescia è quasi pulita e Parma accettabile — ma il LOW di
Parma ha già 35 donatori su 40, e sono proprio gli estremi dove la
taratura si misura.

**Sopra i 300-400 la replica diventa strutturale ovunque.**

### 4.2 Per donatore — replica zero, e il tetto esatto

Si estraggono prima i **donatori** senza reinserimento, poi per ciascuno
un individuo a caso fra quelli che lo portano. Replica **zero per
costruzione**, verificato fino a 3.000 agenti su Brescia e 1.800 su Parma.

E il tetto diventa esatto e dichiarato:

```
LookupError: gruppo LOW (0-2): solo 1137 donatori distinti,
ne servono 1500. E' il tetto vero dell'esperimento.
```

**Brescia regge 3.411 agenti stratificati** (3 × 1.137); gli emiliani
circa 1.900.

### 4.3 Il prezzo: il campione invecchia

Pescando per donatore si **sovrarappresentano i donatori rari**. Un
donatore usato tre volte e uno usato ottanta entrano con la stessa
probabilità, mentre nella popolazione il secondo pesa 27 volte tanto.

E i donatori rari non sono un campione casuale: stanno nelle celle di
condizionamento sottili, che sono gli **anziani e i meno istruiti**. Un
donatore `(Lombardia, M, 65-74, elementare)` copre pochi individui, uno
`(Lombardia, F, 35-49, diploma)` ne copre centinaia.

Misurato su Brescia:

| | età media | donne | laurea o più |
|---|---|---|---|
| popolazione occupati | 45,2 | 44,2% | — |
| per individuo, n=120 | 45,0 | 51,7% | 26,7% |
| per individuo, n=3000 | 45,1 | 44,9% | 29,3% |
| **per donatore, n=120** | **46,9** | 45,8% | **18,3%** |
| **per donatore, n=3000** | **49,1** | 49,6% | **18,7%** |

**Quattro anni più vecchi e un terzo meno laureati**, e la distorsione
cresce con N. Non è rumore: è sistematica.

---

## 5. Tre modi di gestire la distorsione

**A — dichiararla e basta.** L'esperimento a due bracci è **appaiato**:
gli stessi agenti ricevono il profilo con e senza `background_story`, e
la misura è la differenza A−B sullo stesso individuo. La distorsione
demografica agisce ugualmente sui due bracci e **si cancella nella
differenza**.

*È quello che si fa.* Costa nulla, e il disegno appaiato la rende
irrilevante per la domanda che si sta ponendo.

**B — stratificare anche sull'età.** Toglie il problema alla radice ma
complica il campionamento e riduce ulteriormente il tetto, perché ogni
strato attinge a un sottoinsieme dei donatori.

Serve se un giorno si volessero confrontare i **tre gruppi fra loro**
invece dei due bracci: lì la fiducia e l'età si confondono, perché la
fiducia istituzionale correla con l'età e un gruppo più vecchio avrebbe
una fiducia diversa per ragioni che non c'entrano con la taratura.

**C — pesare i donatori per riuso.** Un donatore usato ottanta volte
entra con probabilità ottanta volte maggiore: il campione torna
rappresentativo. Ma è equivalente al campionamento per individuo, e le
collisioni tornano.

> Non esiste un campionamento che sia insieme **senza repliche** e
> **demograficamente rappresentativo**: sono due proprietà in conflitto,
> e quale sacrificare dipende dalla domanda. Per una taratura si
> sacrifica la rappresentatività; per una stima si sacrifica
> l'indipendenza e la si corregge nell'analisi.

È la stessa distinzione che si accetta già stratificando: quaranta agenti
per gruppo non rispettano le proporzioni vere, e non devono.

---

## 6. Cosa questo significa per il disegno

**120 agenti sono largamente sostenibili ovunque**, anche a Castenaso,
dove la coda bassa ha 456 donatori distinti.

**Per il confronto diretto con SIVE conviene Brescia**, dove a 120 la
replica è dello 0,8% invece del 5,8%.

**E la replica va sempre riportata, non assunta.** Un campione di N
agenti va accompagnato dal conteggio dei `donor_id` distinti: se fossero
meno di N, alcuni agenti sono la stessa persona con un altro nome e la
varianza osservata sottostima quella vera.

---

## 7. La cosa che peggiora, non migliora

Gli attributi derivati — nome, titolo di studio dettagliato, settore,
posizione professionale — rendono due agenti con lo stesso vettore AVQ
**molto meno simili in superficie**. Uno è «Maria Bruni, laurea in
medicina, dipendente nella sanità», l'altro «Anna Ferri, diploma tecnico,
lavoratrice in proprio nel commercio».

Dove conta, però, sono identici: stesse ventitré risposte, stesse
correlazioni, stesso contributo a una statistica.

> **La diversità apparente cresce mentre quella reale resta la stessa**,
> e questo rende più difficile accorgersi che due agenti non sono
> evidenza indipendente. È un peggioramento del problema, non un
> miglioramento.

---

## 8. Lo strumento

`scripts/narrativa/campiona_agenti.py` fa il campionamento stratificato,
l'arricchimento con gli attributi derivati e la diagnostica.

```bash
python scripts/narrativa/campiona_agenti.py 017029
python scripts/narrativa/campiona_agenti.py 017029 --per-donatore --n 600
python scripts/narrativa/campiona_agenti.py 034027 --variabile FIDMED
```

Il campione si riproduce da `(comune, variabile, n, seed)`: è il livello
A dell'esperimento e deve essere identico a ogni esecuzione — al
contrario delle biografie, che sono livello C e non devono.

La domanda «quanti agenti distinti posso fare» si ripropone identica per
`FIDMED`, `AMBIENTE` o qualunque altra variabile AVQ: basta cambiare
`--variabile`.

---

## Riferimenti

| | |
|---|---|
| lo strato donatori | `note/GSP_popolazioni_full_riferimento_v22.md` §13 |
| n_eff di Kish per variabile | idem §13.3 |
| gli attributi derivati | idem §2.4 · `note/nota_biografia_v1.md` |
| i tre livelli di certezza | `note/nota_biografia_v1.md` §5 |
| la diversità apparente | `note/design_animarium_v13.md` §14 |
