# Dal record alla biografia — i tre strati e i tre livelli di certezza

**v1 — 5 agosto 2026**

Come si passa da un individuo sintetico a un testo che lo racconti, senza
che il testo prometta più di quanto il dato contenga.

La formulazione che tiene insieme tutto sta in una riga:

> **L'LLM non genera la persona. La persona viene generata
> statisticamente; l'LLM ne genera una possibile rappresentazione
> narrativa.**

---

## 1. Perché serve una pipeline invece di un prompt

La tentazione è passare il record a un modello linguistico e chiedergli
una biografia. Funziona, ed è sbagliato per una ragione precisa: il
modello riempirebbe i vuoti con la propria idea di plausibilità, che è
opaca, non riproducibile e non misurabile.

Con ventitré attributi AVQ, otto demografici e una geografia fino alla
sezione, i vuoti sono comunque tanti — professione precisa, contratto,
famiglia, mezzo di trasporto, tempo libero, reddito. Riempirli è
necessario perché una biografia senza di essi non è una biografia. Ma
**chi li riempie determina cosa la popolazione sembra dire**, e quel
potere non va a un modello linguistico.

Da cui i tre strati.

```
record sintetico  ──►  profilo strutturato      strato 1, vincolato
profilo           ──►  variabili imputate       strato 2, misurato
profilo completo  ──►  testo narrativo          strato 3, generato
```

L'LLM entra solo al terzo. La plausibilità sociologica resta sotto
controllo; al modello resta la realizzazione linguistica e la coerenza
del racconto.

---

## 2. Strato 1 — il profilo vincolato

È il record com'è, e i suoi attributi sono **immutabili**: l'LLM non può
modificarli né reinterpretarli.

| | |
|---|---|
| demografia | sesso, età esatta, stato civile, cittadinanza, paese, background migratorio, origine dei genitori |
| istruzione | classe a sei modalità |
| lavoro | condizione professionale |
| geografia | zona, sezione, indirizzo |
| salute | percepita, croniche, fumo, BMI, indice di salute mentale |
| fiducia | interpersonale e istituzionale, dodici voci |
| ambiente | soddisfazione per la zona |

E i **limiti dichiarati** valgono quanto gli attributi: la popolazione
non conosce famiglia, reddito, professione specifica, e le sue variabili
hanno risoluzioni geografiche diverse — la cittadinanza scende alla
sezione in alcuni comuni, gli attributi AVQ si fermano alla regione.

Un profilo che non porti con sé i propri limiti produce una biografia che
afferma più di quanto sappia.

---

## 3. Strato 2 — l'espansione strutturata

Qui non scrive nulla l'LLM. Si generano variabili nuove da distribuzioni
condizionate, cataloghi controllati o regole di compatibilità, e il
risultato è ancora una riga strutturata.

### 3.1 Cosa esiste già

Tre derivazioni sono implementate, e ciascuna ha fonte registrata,
raccordo dichiarato e verifica di coerenza.

| variabile | modulo | condizionata su | fonte |
|---|---|---|---|
| nome, cognome | `gsp.nomi` | sesso, background, origine genitori, paese | anagrafiche comunali, repertori per paese |
| titolo di studio dettagliato | `gsp.istruzione` | istruzione, sesso, coorte | censimento 2011 |
| settore × posizione professionale | `gsp.lavoro` | sesso, comune | censimento 2011 |

Il risultato è quello che le note preliminari immaginavano:

```json
{
  "istruzione": "diploma",
  "titolo_dettaglio": "diploma di istituto tecnico industriale",
  "condizione": "occupato",
  "settore": "attività manifatturiere",
  "posizione": "dipendente"
}
```

### 3.2 Il criterio, che le note preliminari non avevano

«Ogni nuova variabile deve avere una provenienza precisa» è necessario ma
non basta. Serve anche sapere **su cosa condizionarla**, e la risposta
non è ovvia: il settore economico sembrava andasse condizionato sul
sesso, e invece l'istruzione lo sposta tre volte di più.

Il criterio è la distanza in variazione totale fra composizione
condizionata e marginale (`gsp.tvd`), calcolata prima di costruire. Senza
di esso si sarebbe condizionato sulla variabile sbagliata — che è
esattamente quello che il livello K10C del MaxEnt faceva.

> **Una variabile imputata senza criterio è un'invenzione con l'aspetto
> di un dato.** La provenienza dice da dove viene il numero; il criterio
> dice se quel numero significa qualcosa per *questo* individuo.

### 3.3 I limiti viaggiano con il valore

Ogni imputazione ha una precisione, e va portata avanti insieme al dato.

Il settore è condizionato su sesso e comune ma **non sul titolo di
studio**, perché la fonte non pubblica quell'incrocio a livello comunale.
Una riponderazione parziale lo corregge nei prodotti narrativi, ma non
raggiunge il 21,4% degli occupati — le sette sezioni economiche escluse
dall'incrocio, che sono proprio quelle dove il titolo conterebbe di più.

Conseguenza concreta: **circa una scheda su cinque ha una combinazione
implausibile**. Un diplomato alberghiero in uno studio professionale non
è impossibile, ma non è nemmeno il risultato di un condizionamento.

Chi mostra una scheda deve saperlo, e chi la guarda non deve scambiare
quella stranezza per un difetto del modello demografico — che invece è
verificato.

### 3.4 Cosa manca

**Hobby e tempo libero.** Le note preliminari li mettevano qui con base
AVQ, ma le ventitré variabili assegnate non li contengono: servirebbe
un'altra sezione dell'indagine, o un catalogo pesato su età, sesso e
istruzione con la sua provenienza dichiarata.

**Contratto e orario di lavoro.** `CARATT_OCC` (determinato,
indeterminato, stagionale) e `REGIME_ORARIO` esistono nella tavola
censuaria ma **non sono incrociati con nulla**: zero righe con valore
specificato. Vicolo cieco con quella fonte, e sarebbero variabili
interessanti per il lavoro sulla fiducia istituzionale.

**Famiglia, reddito, mezzo di trasporto.** Non esistono nella
popolazione e non hanno una fonte ovvia. Da lasciare al livello C, o non
inventarli affatto.

---

## 4. Strato 3 — la realizzazione narrativa

L'LLM riceve un profilo già completo e fa quattro cose: prosa, coerenza,
nessuna contraddizione, dettagli ambientali innocui.

Non sceglie il mestiere, non sceglie il titolo, non sceglie il quartiere.
Sceglie come raccontarli.

### La regola che rende difendibile il prodotto

> Una biografia è **una realizzazione plausibile fra molte compatibili**
> con lo stesso individuo sintetico, non la sua storia.

Il modo per rendere questa affermazione visibile invece che dichiarata è
**generare tre biografie dallo stesso profilo e mostrarle insieme**.
Quello che resta uguale è il livello A; quello che cambia è il livello C.
Nessuna spiegazione lo comunica altrettanto bene.

Provato il 5/8/2026: non funziona come previsto. Tre generazioni indipendenti a temperatura 1,0 dallo stesso profilo producono testi diversi ma molto simili — il profilo vincola troppo perché lo spazio narrativo residuo sia visibile. La regola resta vera e va dichiarata invece che mostrata. Il risultato negativo è però informativo in altra direzione: se tre generazioni convergono, un persona-prompt non lascia al modello lo spazio di inventare la persona, che per un uso simulativo conta più della varietà.

---

## 5. I tre livelli di certezza

| livello | significato | esempio |
|---|---|---|
| **A — vincolato** | è nella popolazione | 52 anni, diploma, occupato, Cittadella |
| **B — imputato** | campionato da una distribuzione con fonte e criterio | istituto tecnico industriale; manifattura; dipendente |
| **C — narrativo** | dettaglio espositivo, senza pretesa di verità | «nel fine settimana sistema piccoli oggetti in casa» |

La biografia li mostra insieme; il sistema conserva la provenienza di
ciascuno.

Questo permette **due prodotti dallo stesso individuo**:

**Una scheda scientifica** — attributi, condizionamenti, fonti, limiti.
È quella che accompagna un articolo o una richiesta formale.

**Una biografia dimostrativa** — vivace quanto serve, purché presentata
per quello che è.

La seconda non compromette la prima **finché la provenienza resta
tracciata**. È il motivo per cui i tre livelli non sono una raffinatezza
espositiva ma una struttura del dato.

---

## 6. Il persona-prompt è un prodotto diverso

Le note preliminari non lo distinguevano, e vale la pena farlo: la
biografia e il persona-prompt hanno scopi opposti.

| | biografia | persona-prompt |
|---|---|---|
| destinatario | una persona che legge | un modello che agisce |
| forma | prosa | istruzione di sistema |
| conta | che sia bella e memorabile | che sia coerente e non suggestiva |
| il livello C | arricchisce | **contamina** |

Un persona-prompt che dicesse «guarda con diffidenza alle istituzioni
locali» starebbe **dicendo all'agente cosa rispondere** su una variabile
che l'esperimento vuole misurare. Il livello C, che in una biografia è
colore, in un prompt è una fuga di informazione dall'ipotesi al soggetto.

La regola operativa che ne segue:

> Nel persona-prompt entra il livello A, entra il livello B con
> parsimonia, **non entra il livello C**. E gli attributi che
> l'esperimento misura non si dichiarano mai in prosa: si lasciano
> emergere.

Questo si lega a una questione già aperta per SimComm: la diversità
psicologica effettiva di una popolazione di agenti è quella di alcune
migliaia di donatori, non dei suoi individui. Gli attributi derivati la
fanno sembrare maggiore — due agenti con lo stesso vettore AVQ ora si
assomigliano meno in superficie — il che **peggiora il problema invece di
risolverlo**: rende più difficile accorgersi che non sono evidenza
indipendente.

---

## 7. Cosa fare, in ordine

1. **Tre biografie dallo stesso profilo**, per vedere se la regola del
   §4 si mostri da sé. È mezz'ora e dice molto.
2. **Un catalogo di hobby** con provenienza dichiarata, oppure la
   decisione di non averne.
3. **Il persona-prompt come formato**, distinto dalla biografia, con la
   regola del §6 applicata.
4. **La scheda scientifica** come secondo prodotto, che oggi esiste solo
   come `scheda(anagrafica=True)`.

---

## Riferimenti

| | |
|---|---|
| gli attributi del record | `note/GSP_popolazioni_full_riferimento_v22.md` §2 |
| gli attributi derivati | idem §2.4 · `note/fonti_e_pacchetto_v8.md` §6, §7, §9 |
| il criterio | `note/fonti_e_pacchetto_v8.md` §8 · `gsp.tvd` |
| i limiti del settore | `note/nota_settore_economico_v3.md` |
| cosa esce e in quale forma | `note/piano_trattamento_v2.md` |
