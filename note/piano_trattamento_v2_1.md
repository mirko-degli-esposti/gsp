# Popolazioni sintetiche GSP — piano di trattamento e regimi di diffusione

**Versione 2.1 — 15 agosto 2026**
Mirko Degli Esposti · Dipartimento di Fisica e Astronomia, Università di
Bologna · mirko.degliesposti@unibo.it

Questo documento descrive che cosa contengono le popolazioni sintetiche
generate dal progetto GSP, da quali fonti derivano, in quali forme
vengono diffuse e con quali limiti. È autosufficiente: non presuppone
conoscenza del progetto.

---

## 1. Che cosa è una popolazione sintetica GSP

È un insieme di **individui simulati** — tipicamente fra 16.000 e 390.000
per comune — ciascuno con un profilo demografico completo, un insieme di
attributi su salute, benessere e fiducia istituzionale, e alcuni attributi
**derivati** che ne rendono leggibile il profilo: titolo di studio
dettagliato, settore e posizione professionale, nome e cognome.

Gli attributi derivati non stanno nei file (§4) e non aggiungono
informazione: sono funzioni deterministiche di ciò che il modello ha già
generato. Ma cambiano il modo in cui un record si legge, ed è per questo
che il documento li tratta a parte (§3.1).

Gli individui **non esistono**. Non sono persone reali rese anonime: sono
generati da un modello a massima entropia calibrato su **marginali
aggregati pubblicati** dall'ISTAT, cioè su tabelle del tipo «in questo
comune ci sono N donne fra i 35 e i 49 anni con laurea».

La distinzione è sostanziale e non terminologica:

| | anonimizzazione | simulazione da aggregati |
|---|---|---|
| punto di partenza | record individuali reali | tabelle di conteggi |
| cosa si deve dimostrare | che il legame con la persona è rotto | — non c'è mai stato un legame |
| rischio residuo | reidentificazione | nessuno per costruzione |

Il metodo è documentato in Degli Esposti, M. (2026), *Scalable Maximum
Entropy Population Synthesis via Persistent Contrastive Divergence*,
arXiv:2603.27312, con il codice pubblico su
`github.com/mirko-degli-esposti/maxent-popsynth-pcd`.

---

## 2. Le fonti, e la loro condizione giuridica

Tutte le fonti sono censite in un registro (`fonti/registro.yaml`) che per
ciascuna dichiara universo, licenza, data di accesso, impronta
crittografica e **limiti d'uso**. Al 5 agosto 2026 sono trentasette.

| famiglia | ente | licenza | condizione |
|---|---|---|---|
| tavole censuarie e anagrafiche (SDMX) | ISTAT | CC-BY-4.0 | aperta, dichiarata |
| basi territoriali, sezioni di censimento | ISTAT | CC-BY-4.0 | aperta (licenza generale del sito) |
| indirizzario ANNCSU | ISTAT e Agenzia delle Entrate | CC-BY-4.0 | **open data ex Reg. (UE) 2023/138** |
| microdati AVQ (mIcro.STAT) | ISTAT | CC-BY-4.0 | file **ad uso pubblico** |
| dati comunali su cittadinanza, nomi, cognomi | sei comuni | CC-BY-4.0 | portali open data comunali |
| censimento 2011 — titoli di studio, attività lavorativa | ISTAT | CC-BY-4.0 | aperta, download massivo |
| classificazione CLAIST dei titoli | ISTAT | CC-BY-4.0 | aperta (licenza generale del sito) |
| repertori onomastici per paese | Wikipedia, Wiktionary, CC0 | CC-BY-SA / CC0 | aperte, provenienza dichiarata |

Tre punti meritano di essere esplicitati.

**L'indirizzario ANNCSU è un *high-value dataset* europeo.** Il
Regolamento di esecuzione (UE) 2023/138, che attua la Direttiva (UE)
2019/1024, classifica gli indirizzi fra le «serie di dati di elevato
valore» nella categoria geospaziale e ne impone il rilascio in formato
aperto. Le Specifiche tecniche vigenti sono state adottate con
Provvedimento interdirigenziale Istat–Agenzia delle Entrate del
**12 dicembre 2024, previo parere positivo del Garante per la protezione
dei dati personali**. L'apertura di questi dati è quindi stata vagliata
dall'autorità competente.

**I microdati AVQ sono file ad uso pubblico, già protetti alla fonte.**
Sono la classe meno restrittiva dei microdati ISTAT: scaricabili senza
contratto né richiesta, a differenza dei file per la ricerca (MFR). ISTAT
dichiara che sono prodotti dal file per la ricerca «attraverso tecniche di
sottocampionamento» e con «un'apposita metodologia statistica che
garantisce la tutela della riservatezza dei rispondenti», e avverte che
«le elaborazioni effettuate sui file ad uso pubblico possono condurre a
risultati in qualche misura difformi rispetto a quelli pubblicati».
**La protezione è incorporata nel dato**, non affidata a una clausola
d'uso.

**Nessuna fonte impone restrizioni sulla ridistribuzione di derivati.**
La CC-BY consente esplicitamente l'adattamento; l'obbligo è l'attribuzione,
che il progetto genera automaticamente in `fonti/ATTRIBUZIONI.md`.

---

## 3. Che cosa, in un record, è davvero reale

Questa è la domanda che conta, e la risposta non è uniforme.

| componente | origine | quanto è reale |
|---|---|---|
| età, sesso, stato civile, istruzione, condizione, cittadinanza | massima entropia da marginali | nessun individuo dietro |
| zona, sezione di censimento | vincoli aggregati | nessuno |
| indirizzo (via, civico, coordinate) | estratto da ANNCSU | **l'indirizzo esiste**, l'assegnazione è arbitraria |
| **vettore di 23 attributi AVQ** | copiato da un rispondente | **risposte di una persona vera, già perturbate** |
| **attributi derivati** — titolo di studio dettagliato, settore, posizione professionale | pescati da distribuzioni censuarie condizionate su ciò che c'è già | nessuna informazione nuova, ma il profilo diventa molto più individuato |
| nome e cognome | generati | plausibili, quindi potenzialmente collidenti |

**Il vettore AVQ è la componente più reale del record**, ed è quella a cui
di solito non si pensa. Il metodo di attribuzione è un *hot-deck* per
donatore: a ogni individuo sintetico si assegna il vettore completo di
risposte di un rispondente AVQ della stessa cella
`(regione, sesso, macro-età, istruzione)`. Copiare il vettore intero
invece di campionare variabile per variabile è ciò che preserva le
correlazioni fra attributi — ma significa che quelle 23 risposte sono
state date da una persona.

La protezione è di due tipi, e va misurata invece che asserita.

**Alla fonte**: i microdati sono già perturbati da ISTAT, come dichiarato
sopra.

**Nella generazione**: ogni vettore è **replicato molte volte** su
individui diversi. Su Modena, 4.617 donatori distinti coprono 184.597
individui sintetici, con riuso medio 40×. Nessuna combinazione di
attributi è unica: ogni profilo AVQ è condiviso da decine di individui
sintetici che differiscono per tutto il resto.

**L'indirizzo non porta informazione.** L'assegnazione di un individuo a
un civico è arbitraria dentro la sezione di censimento: la risoluzione
del dato si ferma alla sezione, e dentro la sezione l'individuo è dove
capita. Questo è il motivo per cui l'indirizzo può essere rimosso o
randomizzato senza perdita analitica (§4).

### 3.1 Gli attributi derivati, e perché meritano attenzione

Dal 5 agosto 2026 un individuo può portare, oltre a nome e cognome, il
**titolo di studio dettagliato** — «diploma di istituto tecnico
industriale» invece di «diploma» — e la coppia **settore × posizione
professionale**, per esempio «dipendente, attività manifatturiere».

Sul piano dell'informazione **non aggiungono nulla**. Sono estratti da
distribuzioni censuarie condizionate su attributi che il modello ha già
generato: il titolo dipende da istruzione, sesso e regione; il mestiere da
sesso e comune. Non c'è un nuovo dato individuale che entra: c'è una
funzione deterministica di ciò che c'era.

Sul piano della **leggibilità** cambiano molto, e va detto perché è
esattamente il punto che interessa a chi valuta il trattamento.

> Un record che dice «F, 45-49, laurea, occupata» è un profilo
> statistico. Uno che dice «Maria Bruni, 45 anni, laurea magistrale in
> medicina e chirurgia, dipendente nella sanità, Cittadella» si legge
> come una persona.

**La diversità apparente cresce mentre quella reale resta la stessa.**
Due individui con lo stesso profilo demografico e lo stesso vettore AVQ
sono identici dove conta — nelle risposte, nelle correlazioni, nel
contributo a una statistica — e ora si assomigliano meno in superficie.
Per un uso simulativo questo è un **peggioramento**, non un
miglioramento: rende più difficile accorgersi che due agenti non sono
evidenza indipendente.

Per un uso divulgativo è il contrario, ed è la ragione per cui gli
attributi derivati esistono.

La conseguenza operativa è nel §4: **stanno solo nei regimi generati al
momento**, mai nei file.

---

## 4. I tre regimi di diffusione

Il progetto distingue tre prodotti con tre regimi dichiarati, sul modello
della distinzione che gli istituti di statistica fanno fra file ad uso
pubblico, file per la ricerca e ambienti protetti. La regola è
**implementata in un solo punto del codice** (`gsp.individui`), non
affidata alla disciplina di chi usa.

### 4.1 Popolazione completa — non diffusa

Vive sulla macchina di lavoro. Contiene tutti gli attributi, l'indirizzo
esatto e la chiave `uid`. Serve alla pipeline, alle verifiche interne e
alla generazione degli altri due prodotti. **Non lascia la macchina in
nessuna forma.**

### 4.2 Regime pubblico — il bundle del visualizzatore

È l'unico prodotto **scaricabile**. Viene generato per *default*, non su
richiesta: la scelta permissiva richiede un'opzione esplicita e produce un
avviso a video.

Contiene: attributi demografici, geografia fino alla sezione di
censimento, i 23 attributi AVQ, e coordinate per la mappa.

Non contiene:

- **nome e cognome** — non sono in nessun file;
- **via e numero civico**;
- **la chiave `uid`**;
- **le coordinate esatte**: `lon` e `lat` sono un **punto casuale
  estratto dentro la sezione** di appartenenza;
- **nessuno degli attributi derivati** — titolo di studio dettagliato,
  settore, posizione professionale. Non perché siano sensibili, ma
  perché sono ciò che rende un record una persona anziché un profilo, e
  il bundle serve a mappe e marginali (§3.1).

La randomizzazione delle coordinate **non comporta perdita analitica**,
perché l'assegnazione al civico era già arbitraria dentro la sezione: la
densità per sezione è identica, la mappa è visivamente indistinguibile, e
l'unica cosa che si perde è l'apparenza di una precisione che il dato non
aveva. Il file diventa così **autoprotettivo**: non dipende da
un'avvertenza che lo accompagni.

#### Attuazione, e una divergenza durata dieci giorni

Il regime è **applicato dal 15 agosto 2026**. Fino a quella data il
generatore del bundle leggeva il file di popolazione direttamente, senza
passare da `gsp.individui`: il bundle conteneva quindi via, civico e
coordinate ANNCSU esatte, e **questo documento descriveva un regime che il
prodotto non applicava**.

La divergenza è durata dal 5 agosto — data della prima versione di questo
piano — al 15. In quel periodo un bundle non conforme è stato pubblicato
su una URL a circolazione ristretta, poi spenta.

Vale la pena registrare **come** è stata sanata, perché la scelta non era
ovvia. La correzione non è stata riscrivere le regole nel generatore, ma
**collegare il percorso**: `to_parquet.py` chiama ora
`gsp.individui.esporta_pubblico`, che applica `REGIMI["pubblico"]` — lo
stesso punto in cui sono definiti `persona` e `narrativo`. Replicare la
logica avrebbe prodotto due copie destinate a divergere di nuovo, e in
silenzio.

> La regola sta in un punto solo non perché sia elegante, ma perché **una
> regola in due punti è una regola che prima o poi vale in uno solo**, e
> nessuno se ne accorge finché qualcuno non confronta il documento col
> file.

**Misure di attuazione** (Modena, 184.597 individui, 2.118 sezioni):

| | |
|---|---|
| punti dentro la propria sezione | **100,00%** |
| spostamento mediano | 87 m |
| spostamento al 95° percentile | 308 m |
| colonne nel file | 41 invece di 45 |
| dimensione | 3,30 MB invece di 3,65 |
| costo della randomizzazione | nullo: `lon` 0,351 MB contro 0,349 |

Lo spostamento è la scala di una sezione di censimento urbana, cioè
esattamente la quantità che il dato non sapeva.

Il seme della randomizzazione è **derivato dal codice del comune**, non
passato come parametro: due bundle dello stesso comune escono identici,
quindi resta possibile distinguere «rigenerato uguale» da «rigenerato
diverso» (§5).

### 4.3 Regimi `persona` e `narrativo` — generati, non archiviati

Non sono file. Sono l'esito di una richiesta, prodotta al momento e non
memorizzata.

**`persona`** serve a costruire i *persona-prompt* di agenti simulati con
modelli linguistici. Include nome, cognome, titolo di studio dettagliato,
settore e posizione professionale — che rendono naturale il prompt — e il
quartiere, ma **nessun indirizzo**: a un agente serve sapere dove vive,
non a quale porta.

**`narrativo`** serve alle biografie mostrate in presentazioni e demo.
Include tutto quanto sopra più la **via**; il numero civico solo su
richiesta esplicita, perché è l'unico elemento che punta a un luogo
abitato preciso.

Una scheda narrativa completa si legge così:

```
Maria Bruni — Via Ugo La Malfa, Cittadella
  45 anni · donna · laurea magistrale in medicina e chirurgia
  dipendente, sanità e assistenza sociale
```

Ed è precisamente per questa leggibilità che quei tre attributi non
stanno nei file: la stessa proprietà che li rende utili in una
presentazione li renderebbe problematici in un archivio scaricabile.

Entrambi sono soggetti a un limite di numerosità (`NMAX = 100` individui
per richiesta). Il limite non è tecnico: **un campione completo di poche
decine di individui è un atto, un file di centomila è un archivio**, e la
differenza fra citare un caso e pubblicare una raccolta sta tutta lì.

---

## 5. Misure tecniche

**Nessun attributo derivato è memorizzato in alcun file.** Nome, titolo
di studio, settore e posizione sono generati al momento da funzioni
deterministiche dell'identificatore individuale, ciascuna su un **canale
separato**: correggere il raccordo dei titoli non rimescola i nomi, e il
diff fra due campagne resta leggibile.

**Il nome non è memorizzato in alcun file.** È generato al momento da una
funzione deterministica dell'identificatore individuale: dallo stesso
`uid` esce sempre lo stesso nome, quindi un campione è riproducibile e
citabile senza che nessun nome sia mai scritto su disco. I repertori
onomastici sono fonti registrate (anagrafiche comunali, CC-BY-4.0), e
sostituirli è una riga di configurazione.

**Il regime è verificabile sul prodotto.** Che il bundle sia conforme non
dipende dalla disciplina di chi lo genera: si controlla leggendo il file,
perché le colonne escluse **non ci sono**, non sono svuotate. Un `--pubblico`
dimenticato non produce un file quasi conforme, produce un file con quattro
colonne in più — visibile a colpo d'occhio.

**Il registro delle fonti** conserva per ciascuna l'impronta SHA-256, i
conteggi misurati e le anomalie riscontrate. Un comando (`--verifica`)
controlla che i dati sul disco siano quelli dichiarati; un altro
(`--pubblico`) segnala che cosa può o non può finire in un repository
pubblico.

**Gli artefatti sono riproducibili**: stessi dati in ingresso producono lo
stesso file byte per byte. Nessun artefatto contiene la propria data di
generazione, perché renderebbe impossibile distinguere «rigenerato
uguale» da «rigenerato diverso».

**Le avvertenze sono automatiche.** Un campione filtrato in modo che il
risultato non sia interpretabile — per esempio incrociando il paese di
cittadinanza con la geografia in un comune dove il paese non è
condizionato geograficamente — produce un avviso esplicito, non un
risultato silenzioso.

**Ogni derivazione ha una verifica di coerenza.** Il raccordo fra le
classificazioni della fonte e le categorie del modello è dichiarato in un
file e controllato come partizione: le foglie devono ricostruire il
totale su ogni territorio. Il controllo ha già impedito due errori — un
insieme di categorie che contava due volte le stesse persone, e uno che
ne perdeva il dieci per cento.

---

## 6. Limiti dichiarati

**La risoluzione geografica non è uniforme fra attributi.** La
cittadinanza è condizionata fino alla sezione di censimento in alcuni
comuni e solo a livello comunale in altri; gli attributi AVQ sono
condizionati **soltanto sulla regione**, perché il file pubblico non
riporta la classe di ampiezza demografica del comune. Una variazione fra
quartieri negli attributi AVQ riflette quindi la composizione demografica
del quartiere, non un'informazione locale.

**Le stime non coincidono con quelle ufficiali per costruzione**, sia
perché i microdati di partenza sono perturbati, sia perché la popolazione
è un campione da una distribuzione.

**La numerosità efficace non è il numero di individui.** Una statistica
calcolata su 184.597 individui sintetici poggia su al più 4.617
rispondenti reali; per variabili a universo ristretto la base scende a
qualche centinaio. Il progetto calcola e riporta la numerosità efficace di
Kish accanto alle statistiche, e maschera le correlazioni che poggiano su
meno di 100 donatori distinti.

**I repertori onomastici sono parziali.** Per gli italiani i cognomi
provengono dall'anagrafe di un comune toscano e non sono rappresentativi
delle regioni trattate; i nomi non sono condizionati sulla coorte di
nascita. Per gli stranieri il 76,5% riceve un cognome del proprio paese o
della propria area linguistica, e il restante 23,5% ripiega su un cognome
italiano — un buco concentrato nel mondo arabo e nell'Africa
subsahariana, che nessuna fonte aperta documenta nella stessa forma.
Tutti i limiti sono dichiarati nel registro e non incidono su alcuna
statistica, perché i nomi non entrano nei dati.

**Gli attributi derivati sono condizionati su ciò che la fonte
consente, non su ciò che servirebbe.** Il titolo di studio è condizionato
sulla regione; il settore su sesso e comune, ma **non sul titolo di
studio**, che sarebbe la variabile più informativa — l'incrocio a livello
comunale non è pubblicato. Un correttivo parziale è disponibile e attivo
solo nei prodotti narrativi: raggiunge quattro individui su cinque, e le
sette sezioni economiche che non copre sono proprio quelle dove il titolo
conterebbe di più.

Queste imprecisioni **non toccano le statistiche** — gli attributi
derivati non stanno nei file — ma producono qualche combinazione
implausibile nelle schede narrative: circa una su cinque. È dichiarato
perché chi mostra una scheda sappia cosa può stonare, e perché una
combinazione strana in una demo non venga scambiata per un difetto del
modello demografico, che invece è verificato.

---

## 7. Che cosa questo documento non copre

Il progetto utilizza esclusivamente **microdati ad uso pubblico**. Se in
futuro si accedesse ai file per la ricerca (MFR), le condizioni
contrattuali relative andrebbero verificate separatamente, in particolare
quanto alla ridistribuibilità di prodotti derivati.

---

## Riferimenti

| | |
|---|---|
| metodo di sintesi | arXiv:2603.27312 · `github.com/mirko-degli-esposti/maxent-popsynth-pcd` |
| registro delle fonti | `fonti/registro.yaml` · `note/fonti_e_pacchetto_v8.md` |
| documento di riferimento sui dati | `note/GSP_popolazioni_full_riferimento_v22.md` |
| visualizzatore | `note/design_animarium_v13.md` |
| licenza ANNCSU | Reg. (UE) 2023/138 · `anncsu.gov.it/it/consultazione-dellarchivio/open-data/` |
| microdati AVQ | `istat.it/microdati/aspetti-della-vita-quotidiana/` |
| criterio di derivazione | `note/nota_settore_economico_v3.md` · `gsp.tvd` |
