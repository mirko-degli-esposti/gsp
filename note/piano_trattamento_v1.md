# Popolazioni sintetiche GSP — piano di trattamento e regimi di diffusione

**Versione 1.0 — 4 agosto 2026**
Mirko Degli Esposti · Dipartimento di Fisica e Astronomia, Università di
Bologna · mirko.degliesposti@unibo.it

Questo documento descrive che cosa contengono le popolazioni sintetiche
generate dal progetto GSP, da quali fonti derivano, in quali forme
vengono diffuse e con quali limiti. È autosufficiente: non presuppone
conoscenza del progetto.

---

## 1. Che cosa è una popolazione sintetica GSP

È un insieme di **individui simulati** — tipicamente fra 16.000 e 390.000
per comune — ciascuno con un profilo demografico completo e un insieme di
attributi su salute, benessere e fiducia istituzionale.

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
crittografica e **limiti d'uso**. Al 4 agosto 2026 sono ventinove.

| famiglia | ente | licenza | condizione |
|---|---|---|---|
| tavole censuarie e anagrafiche (SDMX) | ISTAT | CC-BY-4.0 | aperta, dichiarata |
| basi territoriali, sezioni di censimento | ISTAT | CC-BY-4.0 | aperta (licenza generale del sito) |
| indirizzario ANNCSU | ISTAT e Agenzia delle Entrate | CC-BY-4.0 | **open data ex Reg. (UE) 2023/138** |
| microdati AVQ (mIcro.STAT) | ISTAT | CC-BY-4.0 | file **ad uso pubblico** |
| dati comunali su cittadinanza, nomi, cognomi | sei comuni | CC-BY-4.0 | portali open data comunali |

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
  estratto dentro la sezione** di appartenenza.

La randomizzazione delle coordinate **non comporta perdita analitica**,
perché l'assegnazione al civico era già arbitraria dentro la sezione: la
densità per sezione è identica, la mappa è visivamente indistinguibile, e
l'unica cosa che si perde è l'apparenza di una precisione che il dato non
aveva. Il file diventa così **autoprotettivo**: non dipende da
un'avvertenza che lo accompagni.

### 4.3 Regimi `persona` e `narrativo` — generati, non archiviati

Non sono file. Sono l'esito di una richiesta, prodotta al momento e non
memorizzata.

**`persona`** serve a costruire i *persona-prompt* di agenti simulati con
modelli linguistici. Include nome e cognome — che rendono naturale il
prompt — e il quartiere, ma **nessun indirizzo**: a un agente serve sapere
dove vive, non a quale porta.

**`narrativo`** serve alle biografie mostrate in presentazioni e demo.
Include nome, cognome e la **via**; il numero civico solo su richiesta
esplicita, perché è l'unico elemento che punta a un luogo abitato preciso.

Entrambi sono soggetti a un limite di numerosità (`NMAX = 100` individui
per richiesta). Il limite non è tecnico: **un campione completo di poche
decine di individui è un atto, un file di centomila è un archivio**, e la
differenza fra citare un caso e pubblicare una raccolta sta tutta lì.

---

## 5. Misure tecniche

**Il nome non è memorizzato in alcun file.** È generato al momento da una
funzione deterministica dell'identificatore individuale: dallo stesso
`uid` esce sempre lo stesso nome, quindi un campione è riproducibile e
citabile senza che nessun nome sia mai scritto su disco. I repertori
onomastici sono fonti registrate (anagrafiche comunali, CC-BY-4.0), e
sostituirli è una riga di configurazione.

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

**I repertori onomastici sono provvisori.** I cognomi provengono
dall'anagrafe di un comune toscano e non sono rappresentativi delle
regioni trattate; i nomi non sono condizionati sulla coorte di nascita.
Entrambi i limiti sono dichiarati nel registro e non incidono su alcuna
statistica, perché i nomi non entrano nei dati.

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
| registro delle fonti | `fonti/registro.yaml` · `note/fonti_e_pacchetto_v5.md` |
| documento di riferimento sui dati | `note/GSP_popolazioni_full_riferimento_v22.md` |
| visualizzatore | `note/design_animarium_v13.md` |
| licenza ANNCSU | Reg. (UE) 2023/138 · `anncsu.gov.it/it/consultazione-dellarchivio/open-data/` |
| microdati AVQ | `istat.it/microdati/aspetti-della-vita-quotidiana/` |
