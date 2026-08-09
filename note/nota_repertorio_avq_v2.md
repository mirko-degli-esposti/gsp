# Il repertorio AVQ dei nuclei — firme, configurazioni, e il prototipo

**Versione 2.0 — 9 agosto 2026**
Mirko Degli Esposti · DIFA, Università di Bologna

Secondo documento sull'anello 4, dopo `nota_nucleo_familiare_v3.md` che
ne fissa l'architettura. Quella nota decide **dove** entra la struttura
familiare; questa stabilisce **con quale materiale** si costruisce e
**quanto costa** costruirla.

*Changelog v2.0 — aggiunta §6, il prototipo di assemblaggio. Due esiti
opposti: la fattibilità è un non-problema (sotto l'1% di slot falliti
anche su 748 nuclei in una sezione), l'accuratezza del ruolo è al 59% e
per una ragione che non è un difetto. Aggiunta §7 sulla distinzione fra
PUF e SUF di EU-SILC.*

---

## 1. Cosa fa l'anello 4, e cosa non fa

> **La popolazione sintetica non si tocca.** L'anello 4 aggiunge una
> colonna `id_nucleo` e nient'altro. Gli individui restano quelli
> vincolati dall'anello 1, allocati esattamente per sezione dall'anello
> 3, con le loro AVQ. Togliendo la colonna la popolazione torna identica
> byte a byte.

Ne segue una decisione che sembrava aperta e non lo è. Si era considerato
di **donare il nucleo AVQ intero** — prendendo i suoi componenti come
individui sintetici, il che avrebbe anche risolto un'incoerenza nota
(oggi due individui dello stesso futuro nucleo hanno AVQ da donatori
indipendenti, mentre ρ ≈ 0,6 dice che in famiglia le opinioni si
condividono, v22 §13.5).

**È impraticabile**: sostituire individui vincolati dal MaxEnt con
componenti campionari distruggerebbe l'anello 1, i cui totali coincidono
col censimento e la cui allocazione per sezione ha MAE 0,74–1,58. Il
repertorio serve quindi a dire **quali configurazioni sono plausibili**,
non a fornire persone.

Meccanismo, sezione per sezione:

1. la sezione ha N individui dall'anello 3 e i vincoli `PF3`–`PF8`;
2. da lì si sa quanti nuclei di ciascuna ampiezza servono;
3. per ciascuno si estrae una **firma** dal repertorio condizionato
   all'ampiezza;
4. la firma definisce degli **slot**, che si riempiono con gli individui
   della sezione secondo i criteri di §5;
5. la copertura è totale per costruzione, perché Σ k × (famiglie da k) = N
   — verificato esatto a Parma, 96.984 contro 96.985.

---

## 2. La fonte, e due scelte deliberate

Microdati AVQ 2022, 2023, 2024. Chiave del nucleo: **`ANNO|PROFAM`** —
`PROFAM` riparte da 1 ogni anno.

| | Emilia-Romagna | Lombardia | unito |
|---|---:|---:|---:|
| componenti | 7.061 | 11.942 | 19.003 |
| nuclei | 3.233 | 5.210 | 8.443 |
| ampiezza media | 2,18 | 2,29 | 2,25 |

**Si usano tutte e tre le annate.** Il 2022 è escluso dal pool
dell'anello 2 perché gli manca `CRONI`, che è una variabile *target*: la
struttura familiare non ne ha bisogno. Il pool emiliano passa da ~2.000 a
3.233 nuclei, +50% su una risorsa scarsa.

**Non si filtra `ISTRMi = 99`.** Per l'anello 2 è un donatore in meno;
qui scartare un componente **mutila il nucleo**.

### 2.1 I nuclei sono completi — *misurato*

| controllo | esito |
|---|---|
| nuclei senza riferimento | **0** |
| nuclei con 2+ riferimenti | **0** |
| nuclei con 2+ partner | **0** |
| individui con `RELPAR` non mappata | **0** |

Su 8.443 nuclei e tre annate. Conferma indipendente: `NCOMP` dichiarato
coincide **esattamente** con l'ampiezza osservata in ogni classe (381
nuclei da quattro ↔ 1.524 individui con `NCOMP=4`, e così via). Se anche
un solo componente mancasse la colonna si sfalserebbe.

### 2.2 La classificazione operativa

Da `METADATI/Classificazioni/AVQ_Classificazione_2024_var5.html`. Mappa
in dizionario esplicito (`avq_firme.py`):

| sigla | classe | modalità AVQ |
|---|---|---|
| R | riferimento | 01 |
| P | partner | 02 coniuge · 03 convivente coniugalmente |
| F | figlio | 06 ultima unione · 07 unione precedente |
| G | genitore | 04 di PR · 05 del partner |
| A | altro parente | 08–16 |
| N | non parente | 17 amicizia |

**02 e 03 restano distinti** nella colonna fine: la fusione costerebbe
l'unica distinzione utile alla questione del codice 11 di Parma.
**`altro_parente` accorpa nove modalità** in ~250 nuclei: grossolano, ma
separare i nipoti darebbe classi da poche decine.

---

## 3. Le firme — quali configurazioni esistono

| | firme distinte | 90% dei nuclei in | 95% in |
|---|---:|---:|---:|
| 17 modalità grezze | 172 | 9 | 17 |
| classificazione operativa | 70 | **6** | 9 |

### 3.1 Il risultato che semplifica l'assemblaggio

| ampiezza | nuclei | firme | firma dominante | quota |
|---|---:|---:|---|---:|
| 1 | 2.793 | 1 | `R` | 1,00 |
| 2 | 2.652 | 5 | `RP` 0,72 + `RF` 0,21 | 0,93 |
| 3 | 1.523 | 13 | `RPF` 0,79 + `RFF` 0,14 | 0,93 |
| 4 | 1.140 | 15 | `RPFF` | **0,91 da sola** |
| 5 | 249 | 15 | `RPFFF` | 0,74 |
| 6+ | 86 | 13 | `RPFFFF` | 0,53 |

**Il 96% dei nuclei ha ampiezza ≤ 4**, e lì una o due firme coprono il
90%.

### 3.2 I due pool si possono unire, ma il test va rifatto

TVD fra le distribuzioni di firme delle due regioni: **0,0681**, ma è
dominato dalle **ampiezze** — la Lombardia ha più `RPFF` e meno `R` — e
l'ampiezza arriverà da `PF3`–`PF8`. Condizionando sull'ampiezza le due
regioni sono simili: `RP` 0,72 in entrambe, `RPFF` 0,88 contro 0,92.
**La misura giusta è la media dei TVD entro ampiezza**, e non è stata
fatta (§8.1).

---

## 4. Le configurazioni interne — chi sta dentro le firme

`ETAMi` è **categorica**: quindici classi irregolari da 3 a 10 anni,
l'ultima aperta. I divari si calcolano sui **centri di classe**.

### 4.1 Il divario generazionale è il vincolo forte, ed è ben determinato

| divario | n | p05 | p25 | mediana | p75 | p95 |
|---|---:|---:|---:|---:|---:|---:|
| riferimento − figlio | 5.395 | +21,0 | +27,5 | **+33,0** | +38,5 | +45,0 |
| fra fratelli consecutivi | 1.907 | 0,0 | +2,0 | **+4,0** | +7,0 | +11,0 |

### 4.2 Il divario fra partner NON è determinabile con l'AVQ

| | n | p05 | p25 | mediana | p75 | p95 |
|---|---:|---:|---:|---:|---:|---:|
| tutti i partner | 4.525 | −12,5 | −7,5 | **0,0** | **0,0** | +10,0 |

> Mediana e p75 a zero **non** significano che i partner abbiano la
> stessa età: significano che cadono nella **stessa classe**. Il divario
> reale — in Italia mediana ~3 anni — è **sotto la risoluzione dello
> strumento**.

**Parma non può supplire**: ha l'età esatta ma **nessun identificativo di
famiglia**. Dà le marginali ruolo × età, non i divari dentro il nucleo.

Il costo si vede nel prototipo (§6.3).

### 4.3 Il riferimento è sbilanciato, in due direzioni opposte

| firma | n | quota maschi | età mediana |
|---|---:|---:|---:|
| `RP` | 1.912 | **0,828** | ~70 |
| `RPFF` | 1.035 | 0,792 | ~50 |
| `R` unipersonale | 2.793 | 0,468 | ~62 |
| `RF` monogenitore | 570 | **0,191** | ~57 |

**Avvertenza su `RP`**: mediana ~70 contro ~50 di `RPF`. La firma unisce
coppie giovani senza figli e nidi vuoti: è **bimodale**.

### 4.4 Le coppie dello stesso sesso sono esattamente zero

**0,000 su 4.525 partner** — strutturale, non campionario. Va dichiarato
come proprietà della fonte: **la popolazione sintetica erediterà
quell'assenza**.

### 4.5 La cittadinanza è una preferenza, non un vincolo

| | nuclei | omogenei |
|---|---:|---:|
| con 2+ componenti a cittadinanza nota | 5.601 | 0,944 |
| **con almeno uno straniero** | **567** | **0,450** |

Il 94,4% è dominato dai nuclei tutti italiani. Il numero informativo è il
secondo: **la maggioranza dei nuclei che contengono uno straniero sono
misti**. *Cautele*: `CITTMi` è ricostruita, il campione straniero è
autoselezionato sulla lingua, 567 nuclei sono pochi.

### 4.6 I genitori conviventi non si leggono

n = 175 e il **45% tocca la classe aperta 75+**. La mediana +27,5 è
inutilizzabile: per gli slot `G` il vincolo va preso per analogia dal
divario generazionale rovesciato, dichiarandolo.

---

## 5. I criteri di compatibilità

| slot | vincolo | forza | fonte |
|---|---|---|---|
| R in coppia | maschio con p ≈ 0,80 | preferenza | §4.3 |
| R monogenitore | femmina con p ≈ 0,81 | preferenza | §4.3 |
| P | stessa classe d'età o adiacente; sesso opposto | **debole** per l'età, rigido per il sesso | §4.2, §4.4 |
| F | riferimento − figlio in [21, 45] | **forte** | §4.1 |
| F secondo | entro 11 anni dal fratello | forte | §4.1 |
| G | riferimento + [20, 40], per analogia | **dichiarato** | §4.6 |
| cittadinanza | omogenea con p ≈ 0,55 nei nuclei misti | preferenza | §4.5 |

---

## 6. Il prototipo — quanto costa comporre i nuclei

`scripts/diagnostica/proto_assembla.py`, uscita in `note/misure/`.
Deliberatamente **avido**: nuclei dal più grande al più piccolo, slot più
vincolati per primi, nessuna ottimizzazione né backtracking. I tassi di
fallimento sono quindi un **limite superiore**.

Gira sui microdati di Parma e non sulla popolazione sintetica perché
Parma ha `Relpar`, cioè il ruolo vero. L'assemblaggio usa solo gli
attributi dell'anello 1 (sesso, età, cittadinanza); `Ncomp` serve solo a
costruire il vincolo di ampiezza, `Relpar` solo a valutare a posteriori.

### 6.1 La fattibilità è un non-problema

| sezione | individui | nuclei | slot con ripiego | non collocati |
|---|---:|---:|---:|---:|
| 689 | 38 | 18 | 0 | 0 |
| 1055 | 136 | 57 | 2 (1,5%) | 0 |
| 1260 | **1.837** | **748** | **0** | 4 |

E il divario generazionale sta **dentro [21, 45] nel 100% dei casi** in
tutte e tre le sezioni, con mediana 25–31 contro il target AVQ di 33.

> La domanda del prototipo era «l'1% o il 15%?». La risposta è **sotto
> l'1%**, anche sulla sezione più grande di Parma. Comporre nuclei
> plausibili è facile con un algoritmo avido: **la preoccupazione sulla
> coda dell'assemblaggio era infondata**, e §7.5 della v1 — quale valvola
> di sfogo scegliere quando uno slot non si riempie — è una questione che
> non si pone.

I 4 individui non collocati su 1.837 vengono dall'arrotondamento del
vincolo di ampiezza, non da incompatibilità.

### 6.2 L'accuratezza del ruolo è al 59%, e non è un difetto

Stabile nelle tre sezioni. Ma gli errori sono simmetrici:

| errore | sezione 1260 |
|---|---:|
| vero R → assegnato P | 198 |
| vero P → assegnato R | 151 |

> **Sono lo stesso errore contato due volte.** Dentro una coppia il
> prototipo ha scelto come riferimento quello che nell'anagrafe era il
> partner. Ma il **nucleo è corretto**: le due persone stanno insieme,
> di sesso opposto, di età compatibile. È scambiata solo l'etichetta.

E qui c'è un punto sostanziale: **chi sia la «persona di riferimento» in
una coppia non è una proprietà misurabile della famiglia**, è chi ha
firmato la dichiarazione anagrafica. Nell'AVQ è maschio nell'83% dei
casi: una convenzione sociale, non un fatto strutturale. Un modello non
può indovinarlo meglio di così, e non deve. Lo stesso vale per R↔F, dove
figlio adulto e genitore si scambiano l'intestazione.

> **La metrica giusta non è l'accuratezza del ruolo**, che misura una
> convenzione, ma se due persone che stanno nello stesso nucleo vero
> finiscano nello stesso nucleo sintetico. **Non è misurabile con le
> fonti che abbiamo**: i microdati di Parma non hanno un identificativo
> di famiglia, l'AVQ ha i nuclei ma non la geografia. Vedi §7.

### 6.3 Il difetto reale: il vincolo sul partner è troppo largo

Divario fra partner ottenuto: p05 −20 e p95 +13 nella sezione grande,
−20/+6 nella piccola. Code troppo larghe.

È la conseguenza diretta di §4.2. Il vincolo «stessa classe o adiacente»
è debole dove le classi `ETAMi` sono larghe dieci anni (25-34, 35-44):
due partner possono distare vent'anni restando «adiacenti».

Si può stringere a mano — diciamo ±10 anni sull'età esatta — ma sarebbe
un vincolo **inventato, non misurato**. La scelta pulita è tenerlo come
parametro esplicito e dichiarato, da sostituire quando arriva il SUF
(§7).

---

## 7. EU-SILC: cosa si può fare col PUF, e cosa no

Il Public Use File è **completamente sintetico** per dichiarazione
Eurostat, con struttura e nomi di variabile identici al SUF
(`eusilc_exploration_v2.md`).

**Si può fare ora**: scrivere e collaudare il parser D/H/R/P, la
ricostruzione del grafo di parentela dai puntatori padre/madre/partner
(domanda aperta 4 di quel documento), e la funzione che estrae i divari
d'età. Tutto il codice che poi girerà sul SUF senza modifiche.

**Non si può fare**: prendere i numeri. I divari d'età del PUF sono un
artefatto della procedura di sintesi. Metterli nei criteri di
compatibilità significherebbe calibrare la popolazione sintetica italiana
su dati finti.

**Un uso legittimo e utile**: verificare che il PUF riproduca le
distribuzioni AVQ dove le due si sovrappongono. Se il divario
generazionale del PUF ha mediana ~33 come l'AVQ, il parser legge bene; se
dà 12, c'è un bug. È un test del software, non una stima.

> **L'implementazione vera può partire senza aspettare il SUF.** I
> vincoli forti sono misurati sull'AVQ; l'unico debole è il partner, e la
> scelta pulita è una costante `PARTNER_MAX_DIFF` esplicita, con scritto
> accanto che è convenzionale. Meglio che aspettare, e molto meglio che
> nasconderla dentro un criterio che sembra misurato.

Il motivo per cui il SUF servirà davvero non è il partner: è che
**nessuna fonte disponibile permette di validare l'assemblaggio a livello
di nucleo** (§6.2). EU-SILC SUF ha nuclei interi con età esatte, ed è
l'unica via per rispondere a «due persone che stanno insieme nella realtà
finiscono insieme nel sintetico?».

---

## 8. Punti aperti

**8.1 Il TVD fra regioni condizionato sull'ampiezza** (§3.2). Una riga, e
decide se unire i pool.

**8.2 La distribuzione del riferimento in `RP`**, bimodale (§4.3): serve
la distribuzione, non la mediana.

**8.3 Il parser EU-SILC sul PUF** (§7), che è lavoro utile da subito e
indipendente dal resto.

**8.4 Il SUF di EU-SILC**, per i divari esatti e — soprattutto — per la
validazione a livello di nucleo. È ora l'argomento più forte per
richiederlo.

**8.5 Il rischio che l'AVQ porta con sé.**
`nota_nucleo_familiare_v3` §2.4 registra che nessuna combinazione AVQ
riproduce il 52% di stranieri del codice 11 di Parma (massimo 37%).
Ipotesi non verificata: le convivenze migranti sono ciò che l'AVQ cattura
peggio — autoselezione linguistica, e un'indagine su famiglie anagrafiche
fatica a intercettare coabitazioni instabili. **Se fosse così, l'AVQ
sarebbe un repertorio inadeguato proprio per la tipologia di nucleo più
difficile da assemblare.**

**8.6 Le AVQ dentro il nucleo restano scorrelate.** ρ ≈ 0,6 per la
fiducia istituzionale dice che in famiglia le opinioni si condividono; la
popolazione sintetica non lo riprodurrà, perché l'anello 2 dona per
individuo. Limite noto e **non risolvibile** senza toccare l'anello 2, ma
ora visibile e da dichiarare fra le assunzioni.

**8.7 Il prototipo non ottimizza**, e non ce n'è stato bisogno (§6.1).
L'implementazione vera può restare avida: se un giorno servisse
ottimizzare, i numeri di §6.1 sono la baseline da battere.
