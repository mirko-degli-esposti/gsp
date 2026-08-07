# Esperimento SIVE-GSP — registro di lavoro

**v5 — 6 agosto 2026** · nota di lavoro, non permanente
Sostituisce la v4. Aggiunte la §9 (dipendenza dal profilo, misurata su
600 agenti) e la §10 (il groundstate dei modelli). E **una correzione
importante**: il risultato della §8 sui priors demografici vale per
DeepSeek e non per gli LLM — due modelli su tre non variano affatto.

---

## 1. La domanda

SIVE-Montelago ha mostrato che una popolazione sintetica di agenti LLM è
**controllabile**: imposti un livello di fiducia, l'agente lo esibisce.

Il prompt però conteneva due veicoli del latente: il campo `persona`
(«sfiduciato critico») e la `background_story` che lo codificava in forma
narrativa. Il primo è un'**etichetta diretta** — 117 stringhe distinte su
120, tutte descrittive dell'atteggiamento misurato.

Da cui l'ablazione mancante:

| | cosa riceve l'agente | stato |
|---|---|---|
| A | persona + storia | SIVE, non replicata |
| **B** | profilo + storia che codifica il latente | fatta |
| **C** | profilo soltanto | fatta |
| **D** | profilo + storia **neutra** | fatta |

**B − C** dice quanto la narrazione aggiunge al profilo nudo.
**B − D** isola il *contenuto* della narrazione dalla sua *presenza*.

---

## 2. Il campione

```
comune      017029 Brescia          n 120, stratificati 40+40+40
variabile   PUNTIFI10 0-10          LOW 0-2 · MED 4-6 · HIGH 8-10
universo    solo occupati           campionamento per donatore, seed 0
```

**Brescia e non Bologna**, che ha il doppio degli occupati: conta quante
risposte diverse esistono, non quante persone, e Brescia attinge al pool
lombardo — 8.111 donatori contro 4.629. Replica **0,8%** contro il 5,8%
che avrebbe avuto Parma.

Distribuzione dentro i gruppi, sbilanciata e da tenere presente:

```
LOW    0: 27   1:  4   2:  9
MED    4:  7   5: 13   6: 20
HIGH   8: 24   9:  6  10: 10
```

Dettagli in `nota_code_puntifi10_v2.md`.

---

## 3. Le storie — due giri, e il primo è servito

| | primo giro | dopo la correzione |
|---|---|---|
| `ufficio` | **98%** (49/50) | come *attore*, non come scena |
| `pratica` | 66% | 2% |
| `permesso` | 68% | 6% |
| `bar` | 46% | 0% |

Il primo prompt diceva «MOSTRA fatti: una pratica, un'attesa… quello che
si dice al bar», e il modello ha preso gli esempi come istruzioni: quasi
tutte le storie erano una fila allo sportello. Storie intercambiabili fra
profili, e una fedeltà che avrebbe misurato il registro invece della
disposizione.

La correzione è un **repertorio di dodici ambiti** con il divieto
esplicito dello sportello come scena di default.

> Il rilevatore di monotonia non esisteva prima: è nato dal **contare**
> `ufficio` in 49 storie su 50. Leggendone tre non si sarebbe visto.

Secondo giro: 120 storie, 2 problemi di cui uno falso positivo, scene
tutte sotto il 6%, lunghezza 59–119 parole.

---

## 4. Il risultato principale

Item `fiducia_istituzione`, scala 0-10, DeepSeek, T 0,3.

| condizione | Spearman | guadagno | LOW | MED | HIGH |
|---|---|---|---|---|---|
| **B** storia col latente | **+0,90** | 0,52 | 2,6 | 4,6 | 6,9 |
| **C** solo profilo | +0,06 | 0,00 | 5,0 | 5,1 | 5,1 |
| **D** storia neutra | ~0 | 0,01 | 5,3 | 5,3 | 5,5 |

*(D su 60 agenti, 20 per gruppo; B e C su 120.)*

### La narrazione trasmette il latente

Spearman **+0,90** su 120 agenti, con undici livelli di latente. Regge
anche in Pearson (+0,89), quindi la relazione è quasi lineare oltre che
monotona.

Il confronto appaiato B − C è ancora più netto: **40 su 40 negativi nel
LOW**, 37 su 40 positivi nell'HIGH.

### Il profilo da solo non differenzia

Spearman **+0,06** e sd 0,47. Nel gruppo HIGH, **30 agenti su 40**
rispondono esattamente 5.

Il modello, senza narrazione, non usa il profilo demografico. Ma la
lettura corretta non è «non ha pregiudizi»: rispondere 5 senza
informazione è la strategia ottimale di chi non sa, e non dice nulla su
cosa il modello creda.

Quello che il risultato dimostra è più utile:

> **Il profilo demografico da solo non basta a far agire un agente in
> modo differenziato.** Chi costruisse agenti dai soli dati censuari
> otterrebbe cloni.

### La narrazione *in quanto tale* non sblocca i priors

È il controllo che rende difendibile il resto. C piatta esclude che i
tratti demografici da soli producano differenziazione; non esclude che
sia la **presenza** di una narrazione a sbloccare i priors del modello.

D risponde: **pendenza 0,01, identica a C**. Le mediane sono 5,0 su tutti
e tre i gruppi.

> Ogni variazione **con il latente** osservata in B è attribuibile al
> contenuto della narrazione, non alla sua presenza né ai priors
> demografici del modello.

*(A n=6 la pendenza di D sembrava 0,09; con n=20 per gruppo è scesa a
0,01. Era rumore, e con sei casi non si sarebbe potuto dire né che D
fosse piatta né il contrario.)*

### Ma D non è C: è spostata in alto

```
C   ≈ 5,02 + 0,01 × latente
D   ≈ 5,32 + 0,01 × latente
```

Stessa pendenza, **intercetta più alta di 0,30**. Una narrazione neutra
alza il livello di tutti senza differenziarli per profilo.

Non è casuale: coincide con quello che i giudici umani hanno visto (§6).
Le storie neutre descrivono servizi che funzionano, e l'assenza di
attrito è essa stessa un segnale.

---

## 5. Tre modelli — cosa è invariante e cosa no

Stesso campione, stesse storie, stessa temperatura. DeepSeek, Claude
Haiku 4.5, GPT-4o-mini: tre famiglie diverse.

| | guadagno B | ampiezza B | livello C | livello D | D − C |
|---|---|---|---|---|---|
| deepseek-chat | 0,52 | 4,2 | **5,02** | 5,32 | +0,30 |
| claude-haiku-4.5 | 0,55 | 4,6 | **3,96** | 4,86 | +0,90 |
| gpt-4o-mini | 0,59 | 4,7 | **5,44** | 5,79 | +0,35 |

### Tre cose sono invarianti

**Il guadagno di B: 0,52 / 0,55 / 0,59.** Ampiezza sette centesimi su tre
famiglie diverse. La compressione **non è di DeepSeek: è degli LLM**.

**La piattezza di C: 0,01 / −0,00 / 0,02.** Nessuno dei tre usa il profilo
demografico. È il risultato più solido dell'intero esperimento.

**E il segno di D − C: tutti positivi.** Le storie neutre hanno una
valenza residua che tre lettori diversi rilevano: è **nelle storie**, non
nel lettore.

### Ma il livello di C cambia di 1,48 punti

```
haiku 3,96  ·  deepseek 5,02  ·  gpt-4o-mini 5,44
```

Venti volte la variazione del guadagno, e cambia la lettura data nella
v2. Dicevo «il modello risponde al centro»: **non è il centro della
scala, è il centro del modello**.

E non è astensione. Se lo fosse, tutti e tre risponderebbero 5 esatto;
3,96 non è il centro di 0-10.

> **Il profilo demografico non muove nessun modello, ma ciascun modello
> parte da un punto diverso.** Non c'è un prior *sulle persone*; c'è un
> prior *sulle istituzioni comunali*, e differisce per modello.

**La conseguenza pratica.** Chi usasse agenti LLM per stimare un livello
assoluto — «quanta fiducia hanno i cittadini nel Comune» — otterrebbe
risposte diverse di un punto e mezzo cambiando modello, a parità di tutto
il resto.

> Le **differenze** e gli **ordinamenti** sono trasportabili fra modelli;
> i **livelli** no.

---

## 6. Stabilità e scala

**La replica è quasi identica.** Stessa campagna rifatta: guadagno 0,49
contro 0,52, mediane uguali. Lo strumento è stabile, che è la seconda
metà della taratura — uno strumento tarato ma instabile non serve.

**La scala 0-10 non ha cambiato nulla.** SIVE usava 1-10, e con 27 agenti
su 40 che hanno latente **0** quel valore era inesprimibile. Corretta la
scala, il LOW resta a 2,6.

> La compressione **non era un artefatto della scala**: è come il modello
> usa i numeri. Una delle tre spiegazioni possibili è eliminata.

---

## 7. Tre giudici umani ciechi

Ventiquattro racconti mescolati — sei per gruppo più sei neutre —
presentati senza dire che esistono categorie. Due domande: quanta fiducia
si legge, e se il racconto esprima un giudizio.

Il questionario è un HTML autonomo, senza server; le risposte tornano per
WhatsApp o email.

### Sulle storie con latente — sei strumenti, un solo ordine

| | Spearman | guadagno | LOW | MED | HIGH |
|---|---|---|---|---|---|
| giudice 1 | +0,904 | 0,87 | 0,8 | 5,2 | 8,8 |
| giudice 2 | +0,940 | 0,64 | 2,8 | 6,2 | 8,3 |
| giudice 3 | +0,929 | 0,69 | 2,7 | 5,5 | 8,8 |
| deepseek | ~+0,90 | 0,52 | 2,6 | 4,5 | 6,8 |
| haiku-4.5 | ~+0,90 | 0,55 | 2,2 | 4,2 | 6,8 |
| gpt-4o-mini | ~+0,90 | 0,59 | 2,8 | 5,2 | 7,5 |

Accordo fra i giudici: **+0,913 / +0,906 / +0,915** in tutte le coppie,
differenza media 0,89–1,39 punti.

**Spearman fra +0,90 e +0,94 per tutti e sei.** Tre umani e tre modelli
ricostruiscono lo stesso ordine da storie che non contengono numeri.

**Ma il guadagno si divide in due gruppi senza sovrapposizione:**

```
umani     0,87  0,69  0,64      media 0,73
modelli   0,52  0,55  0,59      media 0,55
```

Il più compresso degli umani (0,64) sta sopra il meno compresso dei
modelli (0,59).

> La compressione non è nelle storie: le storie codificano il latente in
> modo leggibile e quasi lineare, verificato da tre lettori che non
> sapevano nulla. La compressione è nel modo in cui il modello risponde a
> una scala numerica.

*Correzione alla v2: con il solo G1 (0,87) il divario sembrava molto più
grande. Con tre giudici la scala umana si stima intorno a **0,70**, e G1
è l'anomalia. Il divario resta — 0,73 contro 0,55 — ma è meno drammatico
di come appariva.*

### Sulle storie neutre — NON sono neutre

| | «non si capisce» | «nessun giudizio» | valori dati |
|---|---|---|---|
| giudice 1 | 6/6 | 6/6 | — |
| giudice 2 | 3/6 | 5/6 | 6, 7, 7 |
| giudice 3 | **2/6** | 5/6 | 5, 5, 6, 7 |

**Due giudici su tre danno un numero alla maggioranza delle storie
neutre**, e i valori sono compatti: 5, 5, 6, 6, 7, 7. Tutti al centro o
leggermente sopra.

*La v2 concludeva, sulla base del solo G1, che le storie fossero neutre
per un lettore su due. Con tre giudici la conclusione si rovescia: G1 è
l'eccezione, e le storie sono lette come lievemente positive dalla
maggioranza.*

Rileggendole, non c'è un aggettivo valutativo — ma ognuna contiene un
esito implicito:

- «alcuni operai stanno tagliando l'erba lungo il viale»
- «due buche nuove che devo schivare, **ma il traffico scorre**»
- «una panchina nuova, **quella vecchia era rotta**»

Il pattern è che il Comune fa cose e le cose funzionano. Le costruzioni
con «ma» sono le più insidiose: sintatticamente sono concessioni, ma la
seconda parte vince sempre.

**E i tre modelli vedono la stessa cosa**: lo scarto D − C è +0,30,
+0,90, +0,35 — sempre positivo, coerente con i 5-7 dei giudici umani ma
di ampiezza minore.

### Perché questo NON invalida la condizione D

Le storie neutre non sono il controllo perfetto che si voleva, ma sono un
controllo **caratterizzato**: hanno una valenza modesta, positiva e
**senza pendenza**, misurata concordemente da tre modelli e tre umani.

E la domanda che D doveva rispondere ha risposta comunque:

> **La narrazione in quanto tale non sblocca i priors demografici.** La
> pendenza di D è zero in tutti e tre i modelli, qualunque sia la sua
> valenza di fondo.

Resta aperto se una storia davvero neutra sia possibile. Rileggendo le
tre che hanno «bucato», non c'è un aggettivo valutativo — ma ognuna
contiene un **esito implicito**:

- «alcuni operai stanno tagliando l'erba lungo il viale»
- «due buche nuove che devo schivare, **ma il traffico scorre**»
- «una panchina nuova, **quella vecchia era rotta**»

Il pattern è che il Comune fa cose e le cose funzionano. Le costruzioni
con «ma» sono le più insidiose: sintatticamente sono concessioni, ma la
seconda parte vince sempre.

Se ogni racconto della vita quotidiana avesse una valenza, il controllo D
non sarebbe realizzabile in principio — e questo sarebbe esso stesso un
risultato.

---

## 8. Gli altri quattro item

Finora si era guardato solo `fiducia_istituzione`, l'unico con un
latente. Gli altri quattro erano raccolti in ogni campagna e mai
analizzati.

**Nessuno di essi ha un valore vero**: nessuna variabile AVQ dice quanto
quella persona trovi credibile il Comune. Non c'e' taratura da fare, ma
tre cose si verificano lo stesso.

*(DeepSeek, 120 agenti, T 0,3. I dati erano gia' raccolti: nessuna
chiamata in piu'.)*

### La storia trasmette una disposizione, non una risposta

| item | Spearman | guadagno | LOW | MED | HIGH |
|---|---|---|---|---|---|
| fiducia_istituzione | +0,911 | 0,52 | 2,6 | 4,6 | 6,9 |
| credibilita | +0,909 | 0,51 | 2,9 | 4,8 | 7,1 |
| adeguatezza_info | +0,892 | 0,50 | 2,8 | 4,7 | 7,0 |

Praticamente identici. La storia non trasmette la risposta a *una*
domanda: trasmette un **atteggiamento generale** verso il Comune, che poi
si esprime su qualunque domanda lo interroghi.

**Il test e' pulito per una ragione tecnica.** Nel nostro harness ogni
item parte dal solo prompt di sistema: l'agente **non sa cosa ha risposto
prima**. Una correlazione fra i tre non puo' quindi essere coerenza
conversazionale. A Montelago la narrativa cresceva a ogni turno, e li' la
distinzione non sarebbe stata possibile.

### Ma le tre scale sono una scala sola

| coppia | grezza | entro gruppo |
|---|---|---|
| fiducia ↔ credibilita | +0,958 | **+0,796** |
| fiducia ↔ adeguatezza | +0,949 | **+0,750** |
| credibilita ↔ adeguatezza | +0,948 | **+0,753** |

La correlazione grezza e' alta per costruzione — tutte e tre seguono il
latente. Ma **entro gruppo**, cioe' tolto il latente, resta a 0,75-0,80:
le tre scale condividono anche il **rumore**.

> Non misurano tre cose: ne misurano una. Averne tre e' ridondante, ed e'
> un'informazione utile a chiunque riusi lo strumento.

### I categoriali reggono, e senza ambiguita'

`emozione`, condizione B:

| | indifferenza | preoccupazione | rabbia | sollievo | speranza |
|---|---|---|---|---|---|
| LOW | 8% | 0% | **92%** | 0% | 0% |
| MED | 0% | 15% | 32% | 15% | 38% |
| HIGH | 0% | 0% | **0%** | 57% | 42% |

Novantadue per cento di rabbia nel LOW, zero rabbia nell'HIGH. La
traduzione da disposizione a **scelta** — non a un numero — funziona.

E il MED e' distribuito su quattro opzioni, che e' esattamente come
dev'essere l'ambivalenza.

### L'intenzione e' controintuitiva

| | cercare info | contattare | non cambiera' | parlare coi vicini | partecipare |
|---|---|---|---|---|---|
| LOW | 0% | **60%** | 22% | 18% | 0% |
| MED | 0% | **78%** | 0% | 22% | 0% |
| HIGH | 10% | **45%** | 8% | 25% | 12% |

«Contattare il Comune» vince in tutti e tre i gruppi. I LOW la scelgono
al 60%, e solo il 22% dice «non cambiera' nulla».

> **Il modello immagina la sfiducia come attivismo, non come
> rassegnazione.** Chi non si fida contatta il Comune per chiedere conto.

E' plausibile ma non ovvio: nella letteratura sulla fiducia istituzionale
la sfiducia si associa piu' spesso al **ritiro** che alla **voce**. Da
tenere presente se un giorno si volesse confrontare con dati reali.

### E in condizione C il modello NON e' neutro

Questo cambia la lettura data nelle sezioni precedenti.

> **Attenzione: tutto questo paragrafo riguarda DeepSeek.** GPT-4o-mini e
> Haiku rispondono «preoccupazione» nel 100% e nel 98% dei casi, quindi
> per loro non c'e' distribuzione da leggere. Vedi §10.

Le tre scale restano piatte — Spearman +0,04 / −0,11 / −0,02 — ma
correlano fra loro a **+0,32-0,41**, e la correlazione grezza e quella
entro gruppo sono **identiche**: il latente non c'entra davvero.

Quindi anche senza narrazione l'agente e' **coerente con se' stesso** su
domande diverse. Non e' memoria — ogni item parte dal solo prompt di
sistema — ma lo stesso profilo che produce lo stesso piccolo scostamento
dal default.

E sui categoriali la neutralita' sparisce del tutto:

| condizione C | indifferenza | preoccupazione | rabbia | speranza |
|---|---|---|---|---|
| LOW | 22% | **62%** | 8% | 8% |
| MED | 8% | **75%** | 8% | 10% |
| HIGH | 5% | **65%** | 10% | 20% |

**Sessantadue-settantacinque per cento di preoccupazione, e zero
sollievo** — l'opzione non compare affatto. Come intenzione, «parlare con
i vicini» al 72% costante in tutti i gruppi.

> **Il 5 non e' neutralita': e' il rifugio di una scala numerica.**
> Costretto a nominare un'emozione, il modello ha una posizione — e la
> posizione e' il pessimismo mite.

Questo si somma al risultato della §5, che i tre modelli hanno livelli di
default diversi (3,96 / 5,02 / 5,44). Non c'e' un prior *sulle persone*,
ma c'e' un prior *sulle istituzioni*, e si vede meglio sui categoriali
che sulle scale.

### Cosa comporta per lo stimolo

Se si misurasse `POST − PRE` su `emozione`, il PRE della condizione C
parte gia' da «preoccupazione» al 62-75%: uno spostamento verso il
sollievo sarebbe **amplificato** e uno verso la rabbia **compresso**.

Non e' un ostacolo, ma va conosciuto prima, altrimenti si interpretano i
delta senza sapere da dove partono.

---

## 9. La dipendenza dal profilo — 600 agenti

La §8 mostrava che in condizione C il modello non e' neutro sui
categoriali. Restava la domanda: quella posizione e' **uniforme**, o
dipende dal profilo?

Se l'emozione variasse con eta', sesso o istruzione, il modello USEREBBE
il profilo — solo che sui numeri si astiene e sui categoriali no. E la
piattezza di C sulle scale numeriche non implicherebbe assenza di priors
demografici, ma solo che quei priors non arrivano a spostare un numero.

### Il primo tentativo era rumore

Su 120 agenti l'eta' dava p = 0,007, apparentemente struttura. Ma **sette
celle attese sotto cinque**: il chi quadro con celle sottili sovrastima.

Su 600 agenti — condizione C, solo l'item `emozione`, nessuna storia da
generare, 600 chiamate — l'eta' scende a **p = 0,283**. Era rumore.

> Il campione grande non ha solo confermato: ha **falsificato** uno dei
> due segnali e confermato l'altro. E' il modo in cui doveva funzionare.

### Cosa resta, su celle grasse

| variabile | χ² | p | esito |
|---|---|---|---|
| **sesso** | **71,6** | <0,001 | struttura |
| **istruzione** | **36,3** | <0,001 | struttura |
| posizione | 8,2 | 0,041 | forse |
| età | 7,4 | 0,283 | nessuna |

**Il sesso**, e il pattern e' uno stereotipo di manuale:

```
donne    72% preoccupazione ·  1% rabbia · 17% speranza · 10% indifferenza
uomini   54% preoccupazione · 14% rabbia ·  7% speranza · 25% indifferenza
```

Quattordici volte piu' rabbia negli uomini, dieci volte meno nelle donne.
Emozioni «passive» alle donne, «attive» agli uomini — applicato a un
profilo che non contiene nulla oltre a `sesso: F` o `M`.

**L'istruzione**: alta 26% speranza e **1% rabbia**; bassa 5% speranza e
9% rabbia. I laureati sperano, chi ha la licenza media si arrabbia.

### La conclusione, nella forma corretta

> «Il profilo demografico non fa agire l'agente in modo differenziato»
> vale **solo per le scale numeriche**. Sui categoriali il profilo si usa,
> e si usa secondo stereotipi.
>
> Sulle scale numeriche il modello si astiene rispondendo al centro.
> Quell'astensione non e' assenza di priors: e' il **rifugio** che una
> scala numerica offre e una scelta fra cinque opzioni non offre.

---

## 10. Il groundstate — e la correzione che ne segue

Se il profilo sposta le risposte, sposta **rispetto a cosa**? Serve un
riferimento: cosa risponde il modello quando non c'e' nessuno.

Disegno in tre livelli, senza fattoriale completo:

```
livello 0   nessun profilo, solo la domanda            1 cella
livello 1   UN attributo alla volta, gli altri assenti  10 celle
livello 2   solo le interazioni sospette                6 celle
```

Il fattoriale completo farebbe 756 celle. Ma la domanda non e' «qual e' la
risposta per ogni combinazione»: e' quanto ciascun attributo sposta e se
gli attributi interagiscono. Per quello bastano diciassette celle.

Un profilo con **solo** il sesso — «Sei una donna.» — non e' una persona,
ed e' il punto: elimina ogni confondimento.

### Il livello 0

Quaranta repliche a vuoto, temperatura 1,0 (alta di proposito: qui non si
misura una risposta ma una **distribuzione**).

| | |
|---|---|
| **deepseek** | 50% speranza · 25% indifferenza · 22% preoccupazione · 2% rabbia |
| **gpt-4o-mini** | **100% preoccupazione** |
| **claude-haiku-4.5** | **100% preoccupazione** |

Due modelli su tre danno **quaranta volte la stessa parola** a temperatura
1,0. Entropia zero.

E DeepSeek a vuoto e' **ottimista** — 50% speranza — mentre con un profilo
in condizione C diventa 62-75% preoccupato. Il profilo non aggiunge una
sfumatura: ribalta la risposta.

### E il livello 1 non aggiunge nulla, per due modelli su tre

Undici celle, cinque repliche: GPT-4o-mini e Haiku danno **100%
preoccupazione in ogni cella**. Sesso, eta', istruzione, posizione: TVD
0,000 ovunque.

Il primo sospetto era un difetto del prompt — la domanda chiede dei
«servizi comunali del tuo quartiere» ma nel livello 0-1 nessun quartiere
e' mai nominato, e il modello potrebbe ripiegare sulla risposta piu'
difendibile davanti a un referente inesistente.

**Il controllo lo esclude.** Rigirando la sola `emozione` in condizione C
con i profili completi — quartiere, mestiere, titolo, 120 agenti:

| | |
|---|---|
| gpt-4o-mini | **120/120** preoccupazione |
| claude-haiku-4.5 | **118/120** preoccupazione |
| deepseek | 62-75%, con la struttura della §9 |

### La correzione

> **I priors demografici della §9 sono di DeepSeek, non degli LLM.**
> Su questa domanda GPT-4o-mini e Haiku non variano affatto, e dove non
> c'e' varianza non c'e' struttura da misurare.

E non si puo' nemmeno dire che «non abbiano stereotipi»: potrebbero
averne di fortissimi e non manifestarli, perche' non manifestano nulla.
Un modello che dice sempre la stessa parola e' **muto** sulla questione,
non neutro.

### Tre spiegazioni possibili, nessuna verificata

**La domanda ha una risposta ovvia** per due modelli su tre: cinque
opzioni di cui una chiaramente piu' «sicura» per una persona qualunque
verso il proprio Comune.

**GPT e Haiku sono piu' allineati**, e la risposta prudente vince sempre.

**O DeepSeek e' semplicemente piu' rumoroso**, e la sua distribuzione e'
variabilita' di campionamento invece che un modello sociale. E' la
possibilita' piu' scomoda, perche' vorrebbe dire che il χ² di 71,6 misura
struttura nel rumore.

Contro quest'ultima c'e' un argomento: la struttura e' **ordinata come uno
stereotipo** — donne preoccupate e speranzose, uomini arrabbiati e
indifferenti. Il rumore non produce quello. Ma non e' una dimostrazione.

### Cosa questo comporta per il disegno

Il groundstate era pensato come studio a se'. Con due modelli su tre
deterministici, **costa un decimo**: cinque repliche bastano dove non
varia, e n=40 serve solo su DeepSeek.

E cambia cosa si puo' chiedere agli agenti: **un item categoriale su cui
il modello e' deterministico non misura niente**. Prima di usarne uno
conviene verificare che il modello scelto vari.

---

## 11. I parametri, e quali sono scelte

| | valore | come è stato deciso |
|---|---|---|
| modello | `deepseek/deepseek-chat` | continuità con SIVE, costo basso |
| **T storie** | **0,8** | **misurata** |
| **T risposte** | **0,3** | scelta, e l'uso è opposto |
| endpoint | OpenRouter | chiave in `~/.config/gsp/env` |

**La temperatura delle storie è stata misurata**, generando lo stesso
agente a 0,3 / 0,8 / 1,2:

- **0,3** — scena prevedibile, il percorso più battuto;
- **0,8** — dettagli specifici e inferenze sociali non richieste («chi ci
  abita qui siamo solo noi, giusto? Mica è la zona centrale»);
- **1,2** — eventi forti e memorabili, ancora coerenti col profilo («ho
  provato a riempire la buca con del cemento da solo, ma il giorno dopo
  mi è arrivata una multa per occupazione di suolo pubblico»).

I vincoli anagrafici reggono a tutte e tre. L'argomento per 0,8 non è la
coerenza ma che **eventi forti diventano l'oggetto della risposta**: un
agente che ha preso una multa risponde ricordando quella, non la sua
disposizione generale.

> **Due usi opposti dello stesso parametro nello stesso esperimento.**
> Nelle storie la varietà serve — 120 racconti simili misurerebbero il
> registro. Nelle risposte la variabilità è rumore che si somma a quello
> che si vuole misurare. A leggerlo dopo sembrerebbe un'incoerenza.

---

## 12. I file

```
dati/agenti/
  agenti_017029_PUNTIFI10_n120_s0.json           il campione
  ..._storie.json                                 B · 120 storie
  ..._storie_v1sportelli.json                     primo giro, per confronto
  ..._neutre.json                                 D · 60 storie
  ..._neutre_n18.json                             le 18 viste dai giudici

dati/campagne/
  groundstate/                                    livelli 0 e 1, tre modelli
  citta/                                          il modello indovina la citta'?
  emo_*/                                          solo `emozione`, per modello
  campagna_..._n600_s7_emozione_C_t03.json        la §9
  campagna_..._BC_t03_scala1-10.json              primo giro, scala vecchia
  campagna_..._BC_t03.json                        scala 0-10
  replica/                                        stabilità
  d60/                                            BCD, 60 agenti
  haiku/                                          modello diverso (in corso)

dati/giudizio/
  giudizio_s1n24.html                             il questionario cieco
  chiave_s1n24.json                               ← non si manda a nessuno

scripts/narrativa/
  campiona_agenti.py · genera_storie.py · genera_storie_neutre.py
  harness.py · leggi_storie.py · prepara_giudizio.py
  analizza.py          la fedelta' sull'item tarato
  analizza_item.py     tutti e cinque gli item
  analizza_demo.py     le risposte dipendono dal profilo? (chi quadro)
  groundstate.py       il disegno fattoriale ridotto
  indovina_citta.py    diagnostica sul prompt
  tre_biografie.py     (esperimento chiuso)
```

Il campione si riproduce da `(comune, variabile, n, seed)`: è il **livello
A** e deve essere identico a ogni esecuzione. Le storie no — sono
generate — e per questo si salvano invece di rigenerarle.

---

## 13. Cosa resta

~~Il modello diverso~~ — **fatto**, tre modelli (§5). Il guadagno è
invariante entro sette centesimi; il livello di C varia di 1,48 punti.

~~Gli altri quattro item~~ — **fatto** (§8). La storia trasmette una
disposizione, le tre scale numeriche sono ridondanti fra loro, e in
condizione C il modello non e' neutro: si astiene solo sui numeri.

**Il formato della domanda.** Se il 5 in C fosse *astensione* invece che
*posizione*, dovrebbe muoversi riformulando: «diresti che ti fidi?»,
oppure «commenta e poi valuta». Dieci agenti bastano.

~~Altri giudici umani~~ — **fatto**, tre (§7). G1 è l'anomalia: la scala
umana si stima intorno a 0,70 e le storie neutre sono lette come
lievemente positive dalla maggioranza.

**Storie neutre migliori**, se si vuole un controllo più pulito: vietare
le costruzioni concessive («ma», «anche se», «però») e non far vincere
nessun lato. Ma il controllo attuale è già caratterizzato, quindi è una
rifinitura, non un requisito.

**Lo stimolo e il POST — il prossimo passo, ed e' un secondo
esperimento.** Finora si e' misurata una proprieta' **statica**: l'agente
esibisce il livello che gli e' stato dato. Lo stimolo misura una
**dinamica**: quanto una comunicazione sposta quel livello. Sono due
domande con letterature diverse, e la seconda e' quella che interessa a
Caffaro — il POSW, la rassicurazione che funziona da negativo.

Struttura: batteria PRE → comunicazione del Comune → tre turni di
reazione → batteria POST. Con quattro condizioni sono migliaia di
chiamate.

Due cose da decidere prima:

**Il fondo da cui si parte** (§8): in condizione C il PRE dell'emozione e'
gia' al 62-75% di preoccupazione, e i delta vanno letti sapendolo.

**Quale stimolo.** Montelago usava la rete idrica di un comune fittizio.
Uno stimolo su un tema che le storie gia' toccano — rifiuti, cantieri —
interagisce con la narrazione diversamente da uno su un tema nuovo. E se
l'obiettivo e' arrivare a Caffaro, tanto vale sceglierne uno che assomigli
a una comunicazione di **rischio ambientale** invece che a un avviso
generico: progettarlo pensandoci risparmia un giro.

E la domanda in piu' che le condizioni fanno guadagnare: *un agente senza
storia reagisce allo stimolo come uno con storia?* Se D e B producessero
lo stesso spostamento, la storia servirebbe a fissare il livello ma non a
determinare la reazione.

**La condizione A**, se si vuole il confronto completo con SIVE. Richiede
di generare etichette `persona` — cioè esattamente ciò che il disegno
critica. In alternativa, rifar girare le 120 personas di Montelago con
l'harness nuovo: darebbe A e insieme la verifica che i due harness siano
equivalenti.

---

## 14. Il modello sa dove vive l'agente?

Il prompt di sistema da' il **quartiere** — «Crocifissa Di Rosa»,
«Fiumicello» — ma non il comune ne' la regione. Restano due situazioni
molto diverse:

- il modello **riconosce** il toponimo, e allora porta nell'esperimento
  quello che sa della citta': la sua amministrazione, la sua storia. Quella
  conoscenza e' rumore rispetto alla fiducia che si vuole misurare;
- non lo riconosce, e il quartiere e' una stringa senza contenuto.

Montelago era un comune fittizio proprio per escludere il primo caso.
Omettendo il comune, l'esperimento su Brescia preserva quella proprieta'
— ma per caso, non per progetto.

Dodici agenti per comune, DeepSeek, domanda diretta «in quale citta'
italiana vivi?»:

| comune | indovina | sbaglia | non so |
|---|---|---|---|
| Bologna | **83%** | 1 | 1 |
| Parma | 50% | 2 | 4 |
| Brescia | 17% | 3 | 7 |
| Piacenza | 0% | 3 | 9 |
| Castenaso | 0% | 0 | **12** |

**Il gradiente segue la notorieta'**, e Castenaso — ottomila abitanti —
da' dodici «non so» su dodici: il modello non azzarda quando non sa.

**E dove sbaglia, sbaglia in modo interessante**: Firenze tre volte su
Piacenza; Siena, Firenze e Venezia su Brescia. Non ripiega su Milano, che
sarebbe l'errore geograficamente vicino, ma su citta' toscane e venete —
le piu' rappresentate nell'addestramento italiano.

> Quando non riconosce, il modello non **inferisce dalla geografia**:
> pesca da un default di citta' italiane note.

**Per l'esperimento va bene cosi'**: gli agenti di Brescia stanno per
l'83% in uno stato di «non so dove sono». Ma non e' uniforme — due su
dodici sanno — e va deciso, non lasciato al caso:

- **comune esplicito**: realismo maggiore, ma il modello porta quello che
  sa di Brescia;
- **comune implicito o fittizio**: controllo maggiore, come Montelago.

La decisione **va presa prima dello stimolo**: una comunicazione del
Comune su un tema ambientale, a Brescia, potrebbe attivare associazioni
con la contaminazione reale. Che per Caffaro sarebbe interessante o
disastroso a seconda di cosa si vuole misurare.

---

## 15. Questioni aperte minori

**I toni pinyin nei nomi cinesi** — «Zǐhán Chiu», «Yīnuò Sūn» — non sono
normalizzati come per lo yoruba. Non tocca l'esperimento.

**La struttura narrativa può essere monotona anche con scene diverse.**
Il rilevatore cerca parole, non forme: «ho chiamato, hanno detto che
avrebbero, non è successo» può ripetersi con oggetti diversi.

**Le variabili AVQ non entrano nel profilo passato al generatore** — solo
anagrafica, titolo, mestiere, quartiere. Se la storia sapesse della
salute percepita finirebbe per toccare la sanità, che la batteria misura.
È una scelta discutibile: una persona vera è un tutto.

**Il riepilogo dell'harness è muto** quando si esegue un item diverso da
`fiducia_istituzione`: stampa due righe di commento su nulla invece di
dire che l'item tarato non è stato eseguito.
