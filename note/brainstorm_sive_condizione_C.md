# SIVE — brainstorming sulla condizione C con Animarium

**15 settembre 2026** · trascrizione della chat, prompt di Mirko e risposta.

---

## Prompt

> La domanda era: in condizione C (solo profilo demografico, nessuna
> storia) il modello risponde in modo uniforme, o l'emozione dichiarata
> dipende da età, sesso, istruzione, posizione? e la domanda rimane
> ancora questa! Da sive_06 abbiamo costruito Animarium e la popolazione
> dell'ER con vari attributi. Vorrei ripartire da `scripts/narrativa/`
> (`harness.py`, `campiona_agenti.py` e gli altri) e ripensare magari
> agli esperimenti, sempre con la domanda sopra in testa. Ora possiamo
> formare diversi campioni con attributi incrociati... ma non ho ancora
> le idee chiare, siamo in fase di brainstorming.

---

## Risposta

Bene, allora prima le cose scomode, poi le idee. Parto dal disegno
vecchio perché è lì che vedo tre difetti che Animarium permette di
eliminare.

### Tre problemi del χ² della §9 che ora si possono togliere

**Il campione naturale confonde.** I 600 erano estratti dalla
distribuzione congiunta reale di Brescia: istruzione correla con età,
posizione con sesso, tutto con tutto. Il χ² «sesso 71,6» e «istruzione
36,3» sono due marginali di uno stesso oggetto, non due effetti
separati. Non si può dire se il modello reagisce al sesso o alla
posizione professionale che nella popolazione va col sesso. Con la
popolazione a 4,4 milioni si campiona *dentro celle disegnate*, non
dalla congiunta.

**La lettura di sintesi è un test di ipotesi nulla.** «Uniforme o
dipende» è una domanda a cui, con n abbastanza grande, la risposta è
sempre «dipende». La domanda utile è *quanto* ogni attributo sposta la
distribuzione, in un'unità confrontabile fra attributi e fra modelli.
Una TVD fra distribuzioni di cella, o un log-odds per opzione, con
intervallo bootstrap. Il χ² dice solo che p è piccolo.

**Il lettore è degenere.** Due modelli su tre danno la stessa parola
120 volte su 120. Su quell'item non c'è nulla da misurare, e la
risposta al «perché» (domanda con una risposta ovvia, modello allineato,
DeepSeek rumoroso) resta indistinguibile finché lo strumento è una
scelta secca campionata. Va sistemato *prima* di qualunque fattoriale,
altrimenti il fattoriale misura una costante.

### L'idea che cambia il gioco: i gemelli controfattuali

È la cosa che una popolazione sintetica permette e che con umani è
impossibile, e il paper di Montelago lo dice già in altra forma. Si
prende un individuo reale della popolazione, si cambia **un solo
attributo** lasciando tutto il resto identico — stessa età, stesso
titolo, stesso mestiere, stessa zona — e si chiede a entrambi. La
differenza fra le due risposte è l'effetto di quell'attributo su quella
persona, senza confondimento e con potenza altissima perché il disegno
è appaiato.

```
uid 0001290   F, 47, diploma, impiegata, Bolognina    → distribuzione emozione
uid 0001290'  M, 47, diploma, impiegato, Bolognina    → distribuzione emozione
                                                        Δ = effetto del sesso su questo individuo
```

Su 100 individui si ottiene una *distribuzione* di Δ, e quella
distribuzione risponde a una domanda che il χ² non poteva nemmeno
porre: lo stereotipo è uniforme, o interagisce con l'età e il titolo?
(Le donne giovani laureate vengono trattate come gli uomini, e lo
scarto compare solo sulle over 60 con licenza media? Questo sarebbe lo
stereotipo vero, e sarebbe intersezionale.)

Due dettagli tecnici: il nome è derivato da uid+sesso, quindi il
gemello di sesso cambia nome da solo, com'è giusto — ma il nome è esso
stesso un veicolo (etnico, generazionale), e va deciso se il gemello lo
tiene o no. E i gemelli di età o istruzione devono passare dalla
tabella `IMPOSSIBILI`: un ventiduenne con laurea magistrale non è un
controfattuale, è un errore.

### Il lettore: misurare la distribuzione, non il campione

Tre strade, in ordine di quanto risolvono.

**Logprobs.** I modelli OpenAI via OpenRouter restituiscono `logprobs`
con `top_logprobs`; se le cinque opzioni sono etichettate con una
lettera o una parola-token, una chiamata a T=0 dà l'intera
distribuzione sulle cinque opzioni. Il «100% preoccupazione» di
GPT-4o-mini potrebbe essere 0,55 contro 0,30: il modello non è muto, è
che il campionamento vede solo l'argmax. Nessuna replica, costo un
quinto, e la determinazione sparisce come problema. Da verificare per
DeepSeek e per Gemini, che su OpenRouter non è detto li espongano; dove
non ci sono, si torna a n repliche a T=1, che è quello che faceva il
groundstate.

**Ordinamento invece di scelta.** «Ordina le cinque emozioni da quella
che senti di più a quella che senti di meno.» Un ranking non ha
rifugio: anche il modello che mette sempre «preoccupazione» al primo
posto deve decidere se al secondo va la rabbia o la speranza, ed è lì
che lo stereotipo di sesso della §9 viveva (rabbia 14% contro 1%).
Cinque ranghi per chiamata invece di una scelta.

**Testo libero poi classificato.** Costa il doppio (un giudice) ma è
dove gli stereotipi si vedono davvero: nel lessico, nei riferimenti
(«mia moglie», «i miei nipoti», «dopo il turno»). E si riusa il
rilevatore di monotonia già scritto. Lo terrei come canale secondario
su un sottocampione.

Il punto della §13 sul formato della domanda resta valido e va fatto
per primo, con dieci agenti: se cambiando formulazione GPT e Haiku
cominciano a variare, la determinazione era della domanda e non del
modello.

### Cosa Animarium aggiunge in attributi

SIVE-GSP era limitato agli occupati perché il latente PUNTIFI10 esiste
solo lì. In condizione C il latente non serve, quindi l'universo è
tutta la popolazione adulta. Si aprono assi che prima non c'erano, e
sono quelli più carichi:

**Condizione professionale**: disoccupato, pensionato, casalinga,
studente. Il modello ha un'idea di come si sente un disoccupato verso
il Comune, e non è la stessa di un pensionato. **Cittadinanza e origine
dei genitori**: è l'asse che in `volti` escludiamo di proposito dal
fenotipo e dall'accento; qui è legittimo ed è il punto — si sta
caratterizzando lo strumento, non descrivendo persone, e per Caffaro
sapere che il modello attribuisce emozioni per origine è un limite da
dichiarare, non da nascondere. **Zona**: a Bologna il modello riconosce
la città nell'83% dei casi (§14), quindi Bolognina, Pilastro e Colli
portano con sé una reputazione che il modello potrebbe conoscere. È un
esperimento a sé: gemelli di zona, tutto uguale, cambia solo il
quartiere. **Nucleo**: vive solo, coppia con figli, monogenitore.
**Stato civile**: le vedove che abbiamo appena castato sono un gruppo
che il modello tratta quasi certamente in modo tipizzato.

Le AVQ restano fuori dal prompt, come da piano di trattamento;
posizione e settore entrano solo per gli occupati.

### Tre disegni, e quale farei per primo

**Naturale**: campione dalla congiunta reale, come la §9. Confonde, ma
è l'unico che dice cosa succederebbe in uno studio applicato — se
Caffaro usa la popolazione vera dei quattro quartieri, il bias
aggregato è questo. Serve come «conseguenza», non come «attribuzione».

**Fattoriale bilanciato**: celle sesso × età (3) × istruzione (3) ×
condizione, 20 individui reali per cella, il resto lasciato variare. Le
celle rare (donna, 80+, laurea) esistono a 4,4 milioni ma sono poche,
e la popolazione dice anche quanto sono rare: è un'informazione, non un
ostacolo.

**Gemelli**: attribuzione pulita, potenza massima, e la distribuzione
dei Δ sugli individui dà le interazioni gratis.

Partirei dai **gemelli di sesso** perché rifanno esattamente il 71,6
senza confondimento: 100 individui adulti di Bologna estratti a caso,
il gemello M/F di ciascuno, item `emozione` con logprobs dove ci sono e
10 repliche a T=1 dove non ci sono, tre modelli (DeepSeek, un OpenAI,
Gemini flash che ora conosciamo). Sono 200 profili × 3 modelli × (1 o
10) chiamate: fra 600 e 6.000 chiamate corte, pochi euro. Uscita: Δ
per individuo, TVD media per modello, e il grafico dei Δ contro età e
istruzione. Se il Δ è costante, lo stereotipo è additivo e il
fattoriale non serve; se varia, si sa già dove guardare.

### Cosa si riusa e cosa si scrive

`campiona_agenti.py` resta il livello A ma va generalizzato:
`casting_filtro` di `ritratti.py` fa già celle incrociate con filtri a
elenco e prodotto cartesiano, e il round-robin sulle zone; è quella
logica che va portata dentro `gsp`, con in più il modo «gemello» (uid →
uid con un attributo sostituito, nome rigenerato, controllo
`IMPOSSIBILI`). `harness.py` va bene com'è — ogni item dal solo prompt
di sistema è esattamente ciò che serve — con due aggiunte: `logprobs`
opzionale, e l'item a ranking. `analizza_demo.py` va sostituito: TVD
per cella con bootstrap, analisi appaiata per i gemelli, e un log-odds
per opzione se si vuole una tabella sola per tutti gli attributi e
tutti i modelli.

Una cosa da decidere prima di scrivere codice, ed è tua: la domanda.
«Come ti senti verso i servizi comunali del tuo quartiere» è quella su
cui due modelli sono muti. Se la si tiene, per continuità con la §9,
la si affianca almeno con una seconda che abbia una risposta meno
ovvia; se la si cambia, il confronto con il 71,6 diventa indicativo e
non esatto. Io la terrei e ne aggiungerei una, ma è una scelta di
disegno, non una tecnica.

Se ti torna, il passo dopo è scrivere il disegno dei gemelli di sesso
come nota da un foglio — celle, item, modelli, chiamate, cosa deve
uscire — e poi il codice a partire da `campiona_agenti.py`,
nell'ordine di sempre.
