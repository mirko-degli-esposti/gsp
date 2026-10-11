# Il laboratorio: lavorare con le popolazioni — nota di design

*v0.1 — 11/10/2026. Prima versione: non sostituisce nulla. Nasce dalla slide
«Animarium as a laboratory» (generate · replicate · control · measure ·
intervene) e dal brainstorming dell'11/10 con Claude Code. È una nota di
design: dice che cosa si costruisce, in che ordine e con quali regole.
Si aggiorna a ogni tappa; le decisioni prese stanno in §0 e non si cambiano
senza una nuova versione.*

---

## 0. Scopo e decisioni prese

**In una frase.** Una dashboard per *lavorare* con le popolazioni della flotta:
lanciare una corsa con manopole diverse dalla produzione, misurarla contro il
censimento e contro il pavimento di campionamento, confrontarla con un'altra
corsa dello stesso comune. Prima sulla macchina locale, con l'architettura già
pronta per andare pubblica un giorno.

**Che cosa non è.** Non è un dataset e non è il viewer: Animarium mostra la
release, il laboratorio produce corse sperimentali. Non genera comuni nuovi e
non scarica fonti (D1).

**Decisioni dell'11/10/2026 (Mirko).**

| | decisione |
|---|---|
| D1 | Niente comuni nuovi, niente fetch SDMX: si lavora con i dati su disco. Per ora la flotta Emilia-Romagna. |
| D2 | Tutti e quattro gli anelli sono rigenerabili dal laboratorio, non solo il fit. |
| D3 | Quante più manopole possibile (censimento in §3). |
| D4 | Il confronto è fra corse dello **stesso comune**. Metriche canoniche: MRE con pavimento, z, TVD, n_eff. |
| D5 | Frontend sullo stack Animarium (pagine statiche + DuckDB-WASM su Parquet), non Streamlit. |
| D6 | Modulo dentro `gsp`; le corse scrivono fuori da `data/`, in `~/progetti/laboratorio/corse/<id>/`. |
| D7 | Il pubblico non si progetta ora ma si tiene in prospettiva: nessuna scelta che lo precluda (§7). |
| D8 | Il gemello entra dopo, ma il manifesto lo prevede da subito (§8). |
| D9 | Questa nota si tiene aggiornata. Il nome è aperto (§1). |

Tempi *dichiarati* (Mirko): il fit K9C di Bologna dura «pochi minuti». Da
misurare alla prima corsa dal laboratorio e registrare in `misure/`.

---

## 1. Il nome (aperto)

«Laboratorio» è la parola generica e resta nel testo. Per il modulo serve un
nome corto, italiano come il resto del codice, che regga accanto ad
*Animarium*. Proposte, in ordine di preferenza di chi scrive:

- **banco** — il banco ottico, il banco di prova: si accendono e spengono gli
  ingressi e si legge lo strumento. È esattamente la metafora della slide
  («come in un esperimento si spengono e accendono gli ingressi»). Modulo
  `gsp.banco`, comando `python -m gsp.banco`.
- **vivarium** — il luogo dove gli animali dell'Animarium si tengono vivi e si
  studiano; bello il parallelo, ma è un nome già usato da altri software.
- **officina** — dove si costruisce e si aggiusta; più «fabbrica» che
  «esperimento».

Nel resto della nota il modulo si chiama `gsp.banco` per avere un nome
concreto. Se si sceglie altro, è un patch.

---

## 2. L'oggetto: l'esperimento

L'unità del laboratorio è **l'esperimento**, un file YAML che dichiara tutto
ciò che cambia rispetto alla produzione e che, a fine corsa, registra tutto ciò
che serve a ripeterla byte per byte. Un esperimento esiste prima e
indipendentemente dalla dashboard: si lancia da riga di comando come ogni altro
pezzo del progetto, e la dashboard è un modo di scriverlo, lanciarlo e
leggerlo.

```yaml
versione: '0.1'
id: 037006_senza_Z3_2026-10-11a        # <comune>_<etichetta>_<data><lettera>
tipo: corsa                            # corsa | gemello (§8)
comune: '037006'                       # sempre stringa (YAML 1.1 e gli zeri)
anno: 2024
livello: K9C
base: produzione                       # o l'id di un'altra corsa (warm start, confronto)
anelli: [1, 2, 3, 4]                   # quali rigenerare; gli altri si copiano da `base`
manopole:                              # solo le differenze dalla produzione (§3)
  vincoli:
    senza: [Z3]
    esclusioni: true
  fit:
    pool: 500000                       # obbligatorio: = alla corsa piena se si confronta
    min_alpha: 2.0e-4
  avq: {seed: 42}
  enrich: {seed: 42}
  nucleo: {seme: 20260810}
note: "hold-out del blocco Z3; stesso pool della produzione"
# --- scritto dal runner, mai a mano ---
esito:
  stato: finita                        # in_coda | in_corso | finita | fallita
  inizio: '2026-10-11T15:02:11'
  fine:   '2026-10-11T15:09:40'
  commit_gsp: 9ebf594
  git_pulito: true
  impronte_fonti: ok                   # esito di python -m gsp.fonti --verifica
  prodotti:                            # SHA-256 di ogni file scritto
    constraints_2024/cs_K9C_senza_Z3.json: "…"
    constraints_2024/popolazione_K9C_senza_Z3.csv: "…"
  tempi_s: {cs_build: 4, fit: 388, avq: 51, enrich: 120, nucleo: 73}
```

Regole, nello stile di `gsp.campagna`: il file si scrive atomicamente, il
blocco `esito` lo aggiorna solo il runner, una corsa finita non si
sovrascrive mai (si fa una corsa nuova con lettera successiva). Il manifesto
è anche la citazione: `id` + `commit_gsp` + impronte identificano la corsa.

**La cartella di una corsa** riproduce il layout di `data/comuni/<COD>/` e
`data/submun/`, così gli script esistenti ci scrivono senza modifiche,
puntati dalle due variabili d'ambiente già previste in `gsp.common`
(`GSP_COMUNI_DIR`, `GSP_SUBMUN_DIR`):

```
~/progetti/laboratorio/
  corse/<id>/
    esperimento.yaml
    comuni/<COD>/constraints_<anno>/…      ← GSP_COMUNI_DIR
    submun/…                               ← GSP_SUBMUN_DIR (solo se cambia)
    nuclei/nuclei_<COD>.csv
    misure/*.json                          ← §4, output strutturato
    bundle/                                ← Parquet per il frontend (§6)
    log/*.log
  indice.parquet                           ← una riga per corsa, per la dashboard
```

Gli anelli non rigenerati si prendono da `base` per **copia** nella cartella
della corsa (non per link), così la corsa è autosufficiente e l'hash dei
prodotti ha senso. Le popolazioni di produzione in `data/comuni/` non vengono
mai scritte: è la regola del progetto e il laboratorio la rende strutturale.

---

## 3. Le manopole

Censimento dell'11/10/2026 sugli script della catena. «oggi» = il flag esiste
già; «da costruire» = richiede codice nuovo (in `gsp.banco` o, con intervento
chirurgico, nello script). Le manopole sono divise per quello che toccano:
**l'informazione** che il modello vede, **l'estrazione**, **il solver**, e
gli anelli a valle.

### 3.1 Informazione (anello 1, `cs_build.py`)

| manopola | oggi | note |
|---|---|---|
| togliere blocchi (`--senza Z3,Z4`) | sì | è il hold-out; i nomi dei blocchi sono quelli di `cs_<LIV>.json` |
| esclusioni α=0 on/off (`--esclusioni`) | sì | spegnerle è un esperimento sulle combinazioni impossibili |
| finestra di età (`--min-age`, `--max-age`) | sì | |
| livello (K6C/K9C; K7C storico) | sì | per i comuni articolati, K6C = «senza zone», già un'ablazione |
| **accorpare** le categorie di un blocco (età 5→10 anni, istruzione 8→4) | da costruire | il «coarsen» della slide; si fa sul JSON prima del fit, sommando i target delle celle unite; serve una mappa per variabile |
| sostituire un blocco con una tabella data (es. anno diverso delle fonti) | da costruire | D1 esclude il fetch; ma le tabelle già su disco per altri anni si possono scegliere |
| rumore sui target (perturbazione, arrotondamento a 3 come ISTAT) | da costruire | è l'operatore Π del gemello (§8); qui nasce come manopola |

### 3.2 Solver ed estrazione (anello 1, `fit_cs.py`)

| manopola | oggi | note |
|---|---|---|
| `--pool N` | sì | **obbligatorio**; per confrontare due corse deve essere uguale |
| `--blocks a,b` (sottoinsieme di blocchi da imporre) | sì | alternativa a `--senza` che agisce al fit invece che al cs; da capire quale usare come canonica |
| `--min-alpha`, `--eps`, `--outer`, `--tol` | sì | la produzione fissa 2e-4, 1e-8, 500, 0 |
| `--gibbs` / `--no-exact`, `--sweeps`, `--anneal`, `--lr`, `--lr-tau`, `--warm-from` | sì | il laboratorio del solver; esporli ma marcarli «avanzate» |
| seed dell'estrazione | da costruire | in `fit_cs.py` il seme è la costante 42 (riga 395; warm start 123): non c'è flag, per le repliche serve `--seed` |

### 3.3 Anelli 2–4

| anello | manopola | oggi |
|---|---|---|
| 2 `assign_avq.py` | `--seed`, `--targets`, `--targets-opt`, `--min-record` (donatori minimi per cella, default 20) | sì |
| 2 | cella di condizionamento (oggi `sesso × macroetà × istruzione4`), aggiungere la cittadinanza | da costruire (patch già preparata, III.5 del report) |
| 2 `assign_nationality.py` | `--seed` | sì |
| 3 `enrich.py` | `--seed`, `--no-tier`, `--keep-naz` | sì |
| 3 | allocazione esatta vs multinomiale alle sezioni | da costruire (esiste nel codice come confronto, non come flag) |
| 4 `assign_nucleo.py` | `--seme`, `--repertorio` | sì |

Il seme è la manopola più importante per il laboratorio: con lo stesso
esperimento e semi diversi si misura la varianza fra repliche, che è il
pavimento di ogni confronto. Vale la regola del progetto: ogni seme è
dichiarato nel manifesto e, se assente, è quello di produzione.

---

## 4. Le misure

Ogni corsa produce in `misure/` file **strutturati** (JSON o Parquet), non
testo da rileggere con regex come fa oggi `riepilogo_diagnostica.py`. Gli
script di `scripts/diagnostica/` restano la fonte dei numeri: il laboratorio
li chiama e, dove stampano solo testo, aggiunge loro un `--json` (intervento
chirurgico, un commit per script).

| misura | anello | script | per corsa / per confronto |
|---|---|---|---|
| MRE per blocco con pavimento di campionamento, z per cella, quota \|z\|>3 | 1 | `verifica_vincoli.py` | corsa |
| ricostruzione di un blocco escluso: pavimento · hold-out · indipendenza | 1 | `holdout_z.py` | confronto (piena vs senza) |
| n_eff di Kish per universo di variabile | 2 | `verifica_donor.py` | corsa |
| TVD per sezione e per zona degli attributi di background | 3 | `misura_em.py` | corsa |
| MAE per sezione dell'allocazione | 3 | (in `enrich.py`) | corsa |
| dimensione dei nuclei vs PF3–PF8, coniugati incoerenti | 4 | `misura_nucleo.py` | corsa |
| TVD fra due corse su ogni marginale e su ogni incrocio a due | tutti | da costruire | confronto |

Il principio del report vale anche qui: **nessun numero senza il suo nullo**.
La TVD fra due corse si riporta sempre accanto alla TVD fra due repliche
della stessa corsa con seme diverso (§3, ultimo capoverso).

---

## 5. Il confronto

Due corse A e B dello stesso comune, stesso anno. Tre viste:

1. **Marginali e incroci**: i pannelli di Animarium con tre marcatori
   (barra / tacca / rombo) diventano A / B / censimento, con la banda del
   pavimento. È lo stesso codice del viewer, puntato a due bundle.
2. **Blocco escluso**: per un hold-out, la ricostruzione del blocco tolto fra
   pavimento e indipendenza, per zona, come in `holdout_z.py`.
3. **Tabella delle misure**: le righe di §4 affiancate, con la differenza e il
   suo nullo.

Un confronto si cita come coppia di `id` e si salva nell'URL, come ogni vista
di Animarium.

---

## 6. Architettura

Tre strati. Ognuno funziona senza quello sopra.

**Strato 1 — `gsp.banco` (Python, nessuna interfaccia).**
- `manifesto.py`: schema, lettura/scrittura atomica, validazione (comune in
  flotta, pool presente, blocchi esistenti nel cs).
- `corsa.py`: crea la cartella, copia gli anelli da `base`, esporta
  `GSP_COMUNI_DIR`/`GSP_SUBMUN_DIR`, chiama gli script **nell'ordine di
  `rigenera.sh`** con i flag di produzione più le manopole, registra tempi,
  hash e commit. Lo stesso comando che oggi lancia `rigenera.sh`, ma su una
  cartella isolata.
- `misure.py`: lancia i diagnostici di §4 e raccoglie i JSON.
- `confronto.py`: TVD fra corse, con il nullo fra repliche.
- `indice.py`: ricostruisce `indice.parquet` dai manifesti.
- `bundle.py`: chiama `to_parquet.py` di Animarium sulla corsa.
- `__main__.py`: `lancia`, `misura`, `confronta`, `elenca`, `replica`
  (riesegue un manifesto e confronta byte per byte, come `--confronta`).

**Strato 2 — servizio e coda.** FastAPI minimo: `GET /corse`,
`GET /corse/{id}`, `POST /corse` (accoda un manifesto), `GET /corse/{id}/log`.
Una tabella SQLite dei job; in locale il worker è un processo che consuma la
coda e lancia `gsp.banco.corsa`. Niente di più finché non serve.

**Strato 3 — frontend.** Pagine statiche nel repo Animarium (cartella
`banco/`), DuckDB-WASM che legge `indice.parquet`, i bundle delle corse e le
misure. Tre pagine: *esperimenti* (indice e modulo per scriverne uno),
*corsa* (misure di §4 più i pannelli del viewer), *confronto* (§5). Lo stato
nell'URL. Il frontend parla con lo strato 2 solo per accodare e per i log;
tutto il resto è lettura di file statici, com'è oggi il viewer.

**Perché in `gsp` e non in Animarium.** Lo strato 1 lancia la catena e deve
conoscere flag, registri e regole del progetto; Animarium consuma e basta.
Il frontend sta in Animarium perché ne riusa i pannelli. La dipendenza resta
una sola e nella direzione di oggi: Animarium importa `gsp`.

---

## 7. Regole e prospettiva pubblica

- **Mai in `data/`.** Il runner rifiuta di partire se `GSP_COMUNI_DIR` punta
  dentro il repo. Le popolazioni di produzione restano quelle citate dal
  report.
- **Replicabilità.** Una corsa è citabile solo con `git_pulito: true`; il
  comando `replica` è il test di determinismo del laboratorio.
- **Regimi di pubblicazione.** Tutto ciò che esce dal laboratorio verso un
  bundle passa da `gsp.individui.esporta_pubblico`, comprese le corse di
  hold-out. Nessun nome e nessun indirizzo nei bundle delle corse.
- **Verso il pubblico (D7).** Lo strato 2 è già una coda: in pubblico cambiano
  solo il worker (su un server), le quote (corse per utente e per giorno) e
  l'autenticazione. Lo strato 3 è già statico. Le corse pubbliche saranno un
  catalogo precalcolato più una coda con quote; la generazione da fonti resta
  esclusa (D1 vale anche lì, per il rate limit SDMX).

---

## 8. Il posto del gemello (dopo, ma previsto)

L'esperimento a gemello (`nota_gemello_v1`, stato in `gemello_stato_v8`) è un
«intervene» di tipo diverso dal hold-out: non toglie una tabella, ma
sostituisce la verità (T nota, eventualmente con struttura piantata), la
pubblica attraverso Π e misura la trasmissione su una batteria di domande.
Oggi vive in `~/progetti/gemello`.

Che cosa il manifesto prevede da subito perché il gemello entri senza
rifare nulla:

- `tipo: gemello` accanto a `tipo: corsa`;
- `base` che può essere una **verità** (una cartella con il layout di una
  corsa) e non solo la produzione;
- la manopola «rumore sui target» di §3.1, che è Π_grezzo;
- le misure di confronto per **domanda** (q1…q34) come file strutturati
  accanto a quelle di §4.

Che cosa resta fuori finché non si decide: la griglia θ, i ricostruttori
alternativi (IPF, Fay–Herriot), le aree intermedie. Da discutere con Mirko
quando lo strato 1 funziona sul hold-out.

---

## 9. Piano a tappe

| tappa | consegna | criterio di accettazione |
|---|---|---|
| M0 | `gsp.banco` con manifesto e `lancia` su hold-out Z3 di un comune piccolo e di Bologna, cartella isolata | i prodotti coincidono byte per byte con `holdout_run.sh` sullo stesso pool; tempi *misurati* in `misure/` |
| M1 | `misura` con `--json` nei diagnostici di §4; `indice.parquet` | `riepilogo_diagnostica.py` riprodotto dai JSON senza regex |
| M2 | `confronta` con TVD e nullo fra repliche; `replica` | due repliche con lo stesso seme: TVD = 0; semi diversi: nullo misurato |
| M3 | frontend: pagina *corsa* e *confronto* in Animarium su bundle di corsa | la vista hold-out Z3 di Bologna leggibile nel browser dall'URL |
| M4 | strato 2 (API + coda) e pagina *esperimenti* | si accoda e si segue una corsa dal browser |
| M5 | manopole da costruire: accorpamento, rumore sui target, seed del fit | ciascuna con un confronto contro il suo nullo |

M0 è il punto in cui la nota passa a v0.2 con i primi numeri misurati.

---

## 10. Questioni aperte

- `--senza` (al cs) oppure `--blocks` (al fit) come via canonica per togliere
  un blocco: producono lo stesso fit? Da verificare con un confronto byte per
  byte prima di M0.
- Il seme dell'estrazione in `fit_cs.py` è una costante (42) senza flag:
  serve `--seed` per le repliche (§3.2), intervento chirurgico con commit.
- Dove sta `holdout_z.py`: oggi in `scripts/esempio/`, ma è la misura di
  confronto principale; va promosso in `diagnostica/` o chiamato da lì.
- ~~`to_parquet.py` deve accettare una radice diversa da `data/`~~ — verificato
  l'11/10: risolve il file con `G.path_constraints`, che legge `GSP_COMUNI_DIR`;
  basta esportare la variabile. Nessuna modifica in Animarium.
- Il nome (§1).
