# Animarium — cosa è cambiato e cosa va aggiornato

**Documento di passaggio**
1 agosto 2026

Riassume la rigenerazione completa del 1/8/2026 e quello che comporta per
Animarium. Chi legge questo documento non ha bisogno di aver seguito la
sessione: tutto il necessario è qui.

---

## 1. In sintesi

Animarium era progettata su **quattro città** (Brescia, Parma, Bologna,
Modena) con file a 40 attributi. Ora ce ne sono **undici**, con due schemi
di colonne diversi, un set di variabili AVQ ampliato e una nuova
informazione che deve entrare nel sistema di garanzie: il **tier del
condizionale geografico**, che determina se una mappa per nazionalità sia
informativa o ingannevole.

| | prima | ora |
|---|---|---|
| comuni | 4 | **11** |
| individui | 971.075 | **2.012.576** |
| attributi | 40 (ma solo Bologna) | **42** (K9C) / **39** (K6C) |
| variabili AVQ | 21 su Bologna, 6 sugli altri | **23 ovunque** |
| combinazioni impossibili | non misurate | **zero** |

---

## 2. I file

```
~/progetti/gsp/data/comuni/{COMUNE}/constraints_2024/popolazione_{LIV}_avq_full.csv
```

**Il nome del file non è più uniforme.** Nove comuni sono K9C, due sono
K6C perché non hanno articolazione sub-comunale. Il caricatore deve
risolvere il livello, non assumerlo:

```python
import glob, os
f = glob.glob(os.path.join(dir_comune, "popolazione_K*_avq_full.csv"))
```

**Escludere `popolazione_K10C_avq_full.csv` di Brescia** (43 colonne). È un
residuo conservato di proposito come materiale sperimentale: contiene
3.417 individui con combinazioni logicamente impossibili (1,72%), effetto
della riducibilità del blocco MC. Non va in Animarium. Un `glob` su
`K*_avq_full` lo prende: filtrare esplicitamente.

### Due schemi di colonne

| | K9C (9 comuni) | K6C (Ferrara, Castenaso) |
|---|---|---|
| colonne totali | 42 | 39 |
| `zona` | codice a 8 cifre | **sempre `"0"`** |
| `background` | presente | assente |
| `origine_genitori` | presente | assente |

I tre attributi in meno sono `zona`, `background`, `origine_genitori`.
Qualunque vista che li usi deve degradare, non fallire.

---

## 3. Le undici città

| comune | codice | livello | individui | zone | denominazione zone | tier | quota trattenuta |
|---|---|---|---|---|---|---|---|
| Bologna | `037006` | K9C | 390.098 | 18 | zone statistiche | 2 | 6,0% |
| Brescia | `017029` | K9C | 198.259 | 33 | quartieri | 1 | 14,5% |
| Parma | `034027` | K9C | 198.121 | 13 | quartieri | 3 | 8,1% |
| Modena | `036023` | K9C | 184.597 | 4 | quartieri | **0** | 2,2% |
| Reggio Emilia | `035033` | K9C | 171.207 | 4 | circoscrizioni | 1 | 6,8% |
| Ravenna | `039014` | K9C | 156.304 | 10 | aree territoriali | 1 | 16,9% |
| Rimini | `099014` | K9C | 150.046 | 6 | ex quartieri | **0** | 7,8% |
| Ferrara | `038008` | **K6C** | 129.391 | — | — | **0** | — |
| Forlì | `040012` | K9C | 117.050 | 21 | quartieri | 1 | 22,2% |
| Piacenza | `033032` | K9C | 102.887 | 4 | ex circoscrizioni | **0** | 5,9% |
| Castenaso | `037021` | **K6C** | 16.357 | — | — | **0** | — |

Nove sono capoluoghi dell'Emilia-Romagna; Brescia è in Lombardia;
Castenaso è un comune della città metropolitana di Bologna, incluso come
test del limite inferiore di scala.

**Nel registro c'è anche San Vito dei Normanni (`074017`, Puglia)**, con un
`popolazione_K8C_avq.csv` ma senza `_full` e senza file sezioni. È
incompleto: o si completa o si esclude da Animarium.

---

## 4. Il tier — la cosa più importante per la visualizzazione

Il **tier** dice a quale granularità geografica il paese di cittadinanza è
stato condizionato:

| tier | significato |
|---|---|
| 0 | il paese **non** è condizionato sulla geografia. La composizione per nazionalità è quella comunale, replicata identica in ogni zona |
| 1 | condizionato sul quartiere / area / circoscrizione |
| 2 | condizionato sulla zona statistica |
| 3 | condizionato sulla sezione di censimento |

### La conseguenza operativa

**Una mappa «nazionalità per quartiere» per un comune a tier 0 non mostra
un dato: mostra un artefatto.** Le differenze fra zone sarebbero solo
rumore di allocazione attorno alla composizione comunale.

Quattro comuni su undici sono a tier 0: Modena, Rimini, Piacenza, e
Ferrara (che per giunta non ha zone).

Questo va gestito nel sistema di badge di garanzia già previsto nel design.
Tre livelli possibili:

- **tier ≥ 1** — la mappa per nazionalità è informativa, badge verde
- **tier 0 con zone** — la mappa è disponibile ma va marcata: *«composizione
  comunale replicata: le differenze fra zone non sono informative»*
- **K6C** — la vista per zona non esiste, si scende direttamente alla sezione

**Attenzione: il tier riguarda solo il paese.** Tutto il resto —
quanti stranieri per zona, età, istruzione, background, la dicotomia
UE/extra-UE — è condizionato sulla geografia in **ogni** comune, tramite i
blocchi Z del MaxEnt (anello 1) e la sezione di censimento (anello 3).
Quindi una mappa «quota di stranieri per quartiere» è valida ovunque; una
mappa «quota di rumeni per quartiere» è valida solo da tier 1 in su.

### Un secondo asse di garanzia: la quota trattenuta

La colonna «quota trattenuta» dice **quanta parte della struttura spaziale
della composizione sopravvive all'aggregazione in zone**. Va dal 2,2% di
Modena al 22,2% di Forlì: anche nel caso migliore, quattro quinti della
struttura stanno *sotto* il quartiere.

Per Animarium significa che **la vista per sezione è più informativa della
vista per zona**, in ogni comune. Se il design prevede entrambe, la
gerarchia va comunicata.

Dettagli in `note/nota_segnale_compositivo_v3.md`.

---

## 5. Le variabili AVQ — da 6/21 a 23

Il set è ora **una costante di progetto** (`AVQ_TARGETS` e `AVQ_OPZIONALI`
in `gsp_common.py`), identico per tutti i comuni.

### Sei target, copertura piena

`AMBIENTE` (soddisfazione ambientale della zona) · `FIDUCIA` (fiducia
interpersonale generalizzata, **polarità invertita**) · `SALUTE` · `CRONI`
(malattie croniche) · `FUMO` · `MH` (indice di salute mentale, continua)

### Diciassette opzionali, copertura variabile

La fiducia **istituzionale** sta qui, tutta su scala 0–10 (0 = per niente,
10 = completamente). Da non confondere con `FIDUCIA`, che è interpersonale.

| variabile | oggetto | copertura |
|---|---|---|
| `PUNTIFI1` | Parlamento italiano | 85% |
| `PUNTIFI2` | sistema giudiziario | 85% |
| `PUNTIFI3` | forze dell'ordine | 85% |
| `PUNTIFI4` | partiti politici | 85% |
| `PUNTIFI5` | Parlamento europeo | 85% |
| `PUNTIFI8` | **Governo regionale** | 85% |
| `PUNTIFI10` | **Governo comunale** | 85% |
| `PUNTIFI12` | vigili del fuoco | 85% |
| `FIDMED` | **medici del SSN** | 85% |
| `FIDINF` | **infermieri del SSN** | 85% |
| `PUNTIFI6` | Presidente della Repubblica | 42% |
| `PUNTIFI7` | Governo italiano | 42% |
| `PUNTIFI13` | banche | 42% |
| `FORZE_ARMATE` | Forze Armate | 22% |
| `VOTOUSL` | giudizio sul servizio ASL ricevuto | 20% |
| `BMI` | indice di massa corporea (18+) | 84% |
| `CPESO` | frequenza di controllo del peso | 97% |

### Il missing è strutturale, non mancante

**Questo va comunicato in interfaccia.** Il `non_applicabile` delle
opzionali non è un dato assente per errore: dipende dall'**annata del
donatore** (il modulo AVQ ruota fra le annate) o dall'**universo della
domanda** (`VOTOUSL` riguarda solo chi ha usato l'ASL).

Il sottocampione che ha il valore è **casuale**, quindi statisticamente
utilizzabile. Ma una barra che mostri «42% dei dati mancanti» darebbe
l'impressione sbagliata: la formulazione corretta è «rilevata su una
sola annata AVQ su due».

### La numerosità efficace non è il numero di individui

Le correlazioni fra variabili AVQ *sembrano* poggiare su centinaia di
migliaia di osservazioni ma poggiano su al più **4.629 donatori distinti**
(8.111 per Brescia, che è in Lombardia). Il riuso medio va da 3,8× a 84,3×.

Per coppie a universi quasi disgiunti la base scende a poche decine.
`assign_avq.py` maschera già le coppie con meno di 100 donatori distinti.
Animarium deve fare lo stesso, o riportare la banda di confidenza corretta
— altrimenti mostrerebbe correlazioni prive di significato con
l'apparenza della precisione.

---

## 6. Altri cambiamenti da sapere

**Combinazioni impossibili: zero.** `cs_build.py --esclusioni` aggiunge 26
vincoli α=0 su combinazioni logicamente impossibili (età sotto i 15 con
condizione professionale, età sotto i 9 con titolo di studio, 9-14enni con
diploma o laurea). Verificato su tutti gli undici comuni. Animarium può
affermare «zero combinazioni impossibili» invece di «quasi zero».

**Zona degenere.** Per Ferrara e Castenaso `zona = "0"` per tutti gli
individui. Non è un valore mancante: è una zona sola che copre il comune.

**Le denominazioni delle zone sono verificate**, ciascuna per almeno due
vie indipendenti (baricentri dei civici ANNCSU, concentrazione dei
toponimi, ordine dei documenti ufficiali). Due casi in cui l'ipotesi
«i codici seguono l'ordine 001, 002, …» era **falsa**: Bologna e Ravenna,
che ha un salto sui codici 004–006.

**Rimini: attenzione ai 12 nuovi quartieri.** Nel 2025 il Comune ha
istituito 12 nuovi quartieri. I dati comunali dal 2025 non sono agganciabili
a `COM_ASC1`, che resta sui 6 del censimento 2023. Se in futuro arrivassero
dati comunali per Rimini, verificare l'anno prima di usarli.

---

## 7. La mappa dell'Emilia-Romagna — proposta

L'idea: **affiancare al menu una mappa regionale cliccabile**, tenendo
Brescia accessibile dal menu perché è fuori regione.

Perché ha senso, oltre all'estetica: nove degli undici comuni sono
capoluoghi ER, e la mappa rende immediato ciò che una lista non mostra —
che il progetto ha ora una **copertura regionale completa**, non un
campione sparso. È un argomento di credibilità del dato, non solo di
navigazione.

Alcune considerazioni di progetto.

**Le scale sono molto diverse.** Da Bologna con 390.098 abitanti a
Castenaso con 16.357, un fattore 24. Se i cerchi fossero proporzionali alla
popolazione, Castenaso sarebbe invisibile. Meglio marcatori di dimensione
fissa, con la popolazione nell'etichetta.

**Castenaso non è un capoluogo** e sta a pochi chilometri da Bologna: sulla
mappa i due marcatori si sovrappongono. Va gestito — offset, oppure un
trattamento visivo che lo distingua come «comune non capoluogo».

**Il tier andrebbe codificato sulla mappa.** È l'informazione che decide
cosa si può guardare in quella città, e vederla prima di entrare evita
l'aspettativa sbagliata. Quattro livelli, ma attenzione a non usare il
colore come unico canale.

**Brescia fuori regione.** Tenerla nel menu è la soluzione più semplice.
Alternativa: una mappa che includa anche la Lombardia con Brescia
evidenziata, che però sposta il baricentro visivo e rende l'ER meno
leggibile. Propenderei per la prima.

**Le geometrie** sono già sul disco: i confini comunali ISTAT sono
registrati per regione in `gsp_common` (`shp ok` per lombardia,
emilia_romagna, puglia). Per una mappa regionale servono i soli confini
comunali, non le sezioni.

---

## 8. Cosa verificare, e cosa serve caricare

Non ho gli script di Animarium sotto mano. Le domande a cui non so
rispondere:

1. **Come il bundle Parquet risolve i file.** Era ottimizzato su una
   configurazione a quattro città con nome fisso `popolazione_K9C_avq_full.csv`.
   Con due livelli diversi e undici comuni va rivisto, e con esso il
   modello di costo delle query (il tre-blocchi di colonne, l'ordinamento
   per zona e sezione, i row group da 20.000).
2. **Se lo schema è per-comune o unificato.** Con 42 e 39 colonne servono
   o due schemi o un'unione con `null` sui tre attributi mancanti.
   La seconda è più semplice per DuckDB-WASM ma va decisa.
3. **Dove vive il sistema dei badge di garanzia**, per aggiungerci il tier.
4. **Se `ispeziona_cs.py`** — che sta in `animarium/build/` — è usato dalla
   build o è solo diagnostico.

Utile caricare, nell'ordine: lo script che costruisce il bundle Parquet, il
file di configurazione delle città (se esiste), e il documento di design
`design_animarium_v09.md` per allinearsi sulla terminologia dei badge.

---

## 9. Documenti di riferimento

| file | contenuto |
|---|---|
| `note/GSP_popolazioni_full_riferimento_v20.md` | documento di riferimento sui file di popolazione: attributi, codifiche, limiti, procedura per aggiungere un comune |
| `note/nota_segnale_compositivo_v3.md` | quanto segnale compositivo trattiene la zonizzazione, undici comuni; giustificazione dell'anello 3 |
| `note/nota_combinazioni_impossibili_v2.md` | perché K10C produce l'1,7% di individui impossibili e K9C no |
| `scripts/rigenera.sh` | pipeline completa, undici comuni, riproducibile |
