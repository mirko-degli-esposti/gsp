# Esperimento SIVE-GSP — registro di lavoro

**v4 — 6 agosto 2026** · nota di lavoro, non permanente
Sostituisce la v3: aggiunta la §8 sugli **altri quattro item**, finora
raccolti e mai analizzati. Contiene il risultato che cambia di piu' la
lettura di tutto il resto — in condizione C il modello **non e' neutro**,
si astiene soltanto sulle scale numeriche.

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

## 9. I parametri, e quali sono scelte

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

## 10. I file

```
dati/agenti/
  agenti_017029_PUNTIFI10_n120_s0.json           il campione
  ..._storie.json                                 B · 120 storie
  ..._storie_v1sportelli.json                     primo giro, per confronto
  ..._neutre.json                                 D · 60 storie
  ..._neutre_n18.json                             le 18 viste dai giudici

dati/campagne/
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
  harness.py · analizza.py · leggi_storie.py · prepara_giudizio.py
  tre_biografie.py                                (esperimento chiuso)
```

Il campione si riproduce da `(comune, variabile, n, seed)`: è il **livello
A** e deve essere identico a ogni esecuzione. Le storie no — sono
generate — e per questo si salvano invece di rigenerarle.

---

## 11. Cosa resta

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

## 12. Questioni aperte minori

**I toni pinyin nei nomi cinesi** — «Zǐhán Chiu», «Yīnuò Sūn» — non sono
normalizzati come per lo yoruba. Non tocca l'esperimento.

**La struttura narrativa può essere monotona anche con scene diverse.**
Il rilevatore cerca parole, non forme: «ho chiamato, hanno detto che
avrebbero, non è successo» può ripetersi con oggetti diversi.

**Le variabili AVQ non entrano nel profilo passato al generatore** — solo
anagrafica, titolo, mestiere, quartiere. Se la storia sapesse della
salute percepita finirebbe per toccare la sanità, che la batteria misura.
È una scelta discutibile: una persona vera è un tutto.
