# Il laboratorio: lavorare con le popolazioni — nota di design

*v0.5 — 11/10/2026. Sostituisce la v0.4 (stesso giorno, in `storico/`)
perché la tappa M3 è fatta: una corsa ha un bundle in regime pubblico, il
pannello di Animarium lo apre con `?bundle=`, e `banco.html` mostra elenco,
corsa e confronto (§14). La v0.4 chiudeva M2: `fit_cs.py` ha `--seed`, `tvd` confronta due
corse con il nullo fra repliche, e il primo confronto piena/hold-out
mostra sopra il nullo solo il blocco tolto (§13). La v0.3 chiudeva M1: i diagnostici scrivono JSON, `misura` li lancia
su una corsa, `indice.parquet` esiste, e la tabella III.3 del report si
riproduce dai JSON senza regex (§12). Corregge §4: due misure elencate come
«per corsa» non lo sono. La v0.2 chiudeva M0 (§11); la v0.1 nasceva dalla
slide «Animarium as a laboratory» e dal brainstorming dell'11/10. La v0.1 nasceva dalla slide «Animarium as a laboratory» (generate ·
replicate · control · measure · intervene) e dal brainstorming dell'11/10
con Claude Code. È una nota di design: dice che cosa si costruisce, in che
ordine e con quali regole. Si aggiorna a ogni tappa; le decisioni prese
stanno in §0 e non si cambiano senza una nuova versione.*

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

Tempi: nella v0.1 *dichiarati* (Mirko: «pochi minuti» per il fit K9C di
Bologna); dalla v0.2 *misurati* (§11): la catena completa di Bologna con
hold-out Z3 dura 133 s, di cui 87 s di fit.

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

Il modulo si chiama `gsp.banco` (M0, 11/10/2026): un nome concreto serviva
per scrivere il codice. Se Mirko sceglie altro, rinominare la cartella e
questa nota è un patch.

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
| `--blocks a,b` (sottoinsieme di blocchi da imporre) | sì | agisce al fit invece che al cs. *Misurato* (§11): stessa popolazione di `--senza`, byte per byte. La via canonica è `--senza`: lascia traccia nel nome del file e nel campo `hold_out` del cs, e i nomi dei blocchi sono quelli di cs_build |
| `--min-alpha`, `--eps`, `--outer`, `--tol` | sì | la produzione fissa 2e-4, 1e-8, 500, 0 |
| `--gibbs` / `--no-exact`, `--sweeps`, `--anneal`, `--lr`, `--lr-tau`, `--warm-from` | sì | il laboratorio del solver; esporli ma marcarli «avanzate» |
| seed dell'estrazione (`--seed`, manopola `fit.seed`) | sì (M2, 11/10) | default 42, com'era cablato; registrato in `fit_<LIV>.json`. Il seme del warm start (123) resta fisso |

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
| ~~TVD per sezione e per zona degli attributi di background~~ | 3 | `misura_em.py` | **non è una misura della corsa** (corretto in v0.3): misura la tavola delle sezioni, cioè la fonte |
| MAE per sezione dell'allocazione | 3 | (in `enrich.py`, righe `[val]` del log) | corsa; enrich non ha `--json`, `misure.py` legge quelle tre righe del log e solo quelle |
| dimensione dei nuclei vs PF3–PF8, coniugati incoerenti | 4 | `nuclei_<COD>_diagnostica.json` scritto da `assign_nucleo.py` (`misura_nucleo.py` misura i microdati di Parma, non la corsa: corretto in v0.3) | corsa |
| seam quinquennale, età × istruzione impossibili | 3 | `diag_quinq.py`, `diag_istruzione_eta.py` (CSV) | corsa |
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

**Strato 1 — `gsp.banco` (Python, nessuna interfaccia).** Fatto in M0
(`src/gsp/banco/`, 11/10/2026) per le parti segnate ✓.
- ✓ `manifesto.py`: schema (§2), `PRODUZIONE` (la copia dichiarata dei
  valori di rigenera.sh e dei default degli script), lettura, scrittura
  atomica con i codici quotati, validazione (comune in registro, anelli
  contigui, manopola di un anello ⇒ quell'anello si rigenera, pool presente,
  Z1/Z2 non escludibili, base esistente).
- ✓ `corsa.py`: crea la cartella, copia gli ingressi e gli anelli ereditati
  da `base`, esporta `GSP_COMUNI_DIR` (le sezioni restano quelle di
  produzione), chiama gli script **nell'ordine di `rigenera.sh`** con i
  flag di produzione scritti per esteso più le manopole, registra tempi,
  comandi, commit, hash. Rifiuta di scrivere dentro il repo.
- ✓ `__main__.py`: `nuovo` (anche con `--set gruppo.manopola=valore`),
  `lancia`, `elenca`, `replica` (rifà una corsa finita e confronta byte per
  byte), `confronta`.
- ✓ `misure.py` (M1): lancia i diagnostici di §4 sulla corsa, con
  `--json`, in `corse/<id>/misure/`; `riassunto()` estrae i numeri di testa.
  Il hold-out prende pavimento e indipendenza dalla corsa piena della base.
- ✓ `confronto.py` (M2): `tvd A B [--nullo C D]`, TVD su ogni marginale e
  incrocio a due delle variabili dell'anello 1 e dei target AVQ (120
  combinazioni) dal file più ricco presente in entrambe le corse, con la
  stessa TVD fra due repliche a seme diverso e il rapporto. Uscita in
  `~/progetti/laboratorio/confronti/<A>__<B>.json`.
- ✓ `indice.py` (M1): `~/progetti/laboratorio/indice.parquet`, una riga per
  corsa (manifesto + riassunto), ricostruito da zero a ogni `lancia`,
  `misura` o `indice`: i manifesti sono la verità, l'indice una vista.
- ✓ `bundle.py` (M3): `bundle <id>` chiama i quattro script di Animarium
  (`to_parquet.py --pop-file --nuclei-dir`, `manifest_min.py`,
  `build_riferimenti.py --cs`, `build_rif_nuclei.py`, poi `build_indice.py`)
  e scrive `corse/<id>/bundle/` con lo stesso layout del bundle di release,
  in regime pubblico. Il riferimento censuario viene dal cs **pieno** della
  base: in un hold-out il blocco tolto è quello che si vuole vedere contro
  il censimento. `indice.py` scrive anche `indice.json`.

Due prodotti portano l'orologio dentro: `fit_<LIV>.json` (`t_exact_s`,
`t_gibbs_s`) e `nuclei_<COD>_diagnostica.json` (`generato`). Il banco ne
calcola l'impronta senza quelle chiavi (prefisso `senza-orologio:`), come
`rigenera.sh --confronta` che non li confronta affatto. È contro la regola
III.1 del report ed è segnato in `TODO.md` con il tag `[banco]`.

**Strato 2 — servizio e coda.** FastAPI minimo: `GET /corse`,
`GET /corse/{id}`, `POST /corse` (accoda un manifesto), `GET /corse/{id}/log`.
Una tabella SQLite dei job; in locale il worker è un processo che consuma la
coda e lancia `gsp.banco.corsa`. Niente di più finché non serve.

**Strato 3 — frontend.** Fatto in M3 nella forma minima, diversa da
quella prevista in v0.1 e più semplice: nessuna pagina nuova con DuckDB.
- `build/pannello_marginali.html` accetta `?bundle=<url>`: lo stesso
  pannello della release apre il bundle di una corsa (marginali con i tre
  marcatori, mappa, scheda, fiducia, nuclei), e l'URL resta la citazione
  della vista. Il parametro sopravvive al cambio di comune e a `scriviURL`.
- `build/banco.html` (nuova, ~250 righe, solo `fetch` di JSON): *elenco*
  delle corse da `indice.json` con i numeri di testa e il link al pannello;
  *corsa* (`?corsa=<id>`) con manifesto, tempi, commit e le misure di §4
  rese come tabelle e una barra pavimento–hold-out–indipendenza; *confronto*
  (`?a=<id>&b=<id>`) con i numeri di testa affiancati e la tabella TVD con
  nullo e rapporto da `confronti/<A>__<B>.json`, in grassetto sopra 2.
- Si serve dalla cartella che contiene i due repo:
  `cd ~/progetti && python animarium/build/serve_range.py`, poi
  `http://localhost:8000/animarium/build/banco.html`.
La pagina *esperimenti* con il modulo per scrivere un manifesto e accodarlo
resta per M4, perché ha bisogno dello strato 2.

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
| M0 ✓ 11/10/2026 | `gsp.banco` con manifesto e `lancia` su hold-out Z3 di Cesena e di Bologna, cartella isolata | **soddisfatto** (§11): cs, targets e popolazione dell'anello 1 byte-identici alla catena di `holdout_run.sh` sullo stesso pool; replica byte-identica su tutti e quattro gli anelli; tempi in `misure/banco_M0/` |
| M1 ✓ 11/10/2026 | `misura` con `--json` nei diagnostici di §4; `indice.parquet` | **soddisfatto** (§12): `riepilogo_diagnostica.py --json` dà le stesse righe della via regex su Castenaso e Piacenza; misure della replica uguali all'originale |
| M2 ✓ 11/10/2026 | `tvd` con nullo fra repliche; `--seed` in `fit_cs.py` | **soddisfatto** (§13): stesso seme TVD = 0 su 120 combinazioni; seme 7 contro 42 misurato come nullo; piena contro senza Z3 sopra il nullo solo in zona×istruzione |
| M3 ✓ 11/10/2026 | frontend: pagina *corsa* e *confronto* in Animarium su bundle di corsa | **soddisfatto sul lato dati e HTTP** (§14): bundle di Bologna senza Z3 in regime pubblico, ogni URL che le pagine chiedono risponde 200/206 con il content-type giusto, JS senza errori di sintassi. **La verifica visiva nel browser resta da fare** (nessun browser headless sulla macchina) |
| M4 | strato 2 (API + coda) e pagina *esperimenti* | si accoda e si segue una corsa dal browser |
| M5 | manopole da costruire: accorpamento, rumore sui target, seed del fit | ciascuna con un confronto contro il suo nullo |

Prossima tappa: da decidere con Mirko fra M4 (API e coda, pagina
*esperimenti*) e M5 (manopole nuove: accorpamento, rumore sui target),
dopo la verifica visiva di M3.

---

## 10. Questioni aperte

- ~~`--senza` (al cs) oppure `--blocks` (al fit) come via canonica~~ —
  *misurato* l'11/10 su Cesena (`misure/banco_M0/senza_vs_blocks_040007.txt`):
  stesso insieme di vincoli (1.158), stesse categorie e dominio, popolazioni
  byte-identiche. Canonica: `--senza`.
- ~~Il seme dell'estrazione in `fit_cs.py` è una costante (42) senza flag~~
  — fatto in M2 (gsp `e2cb8d3`), default invariato e verificato byte per byte.
- Il nullo di `tvd` cambia solo il seme dell'anello 1: gli anelli 2–4
  girano con i loro semi di default su una popolazione diversa, quindi il
  nullo include la propagazione a valle. È voluto (è la variabilità di una
  corsa intera), ma per isolare un anello servono manopole di seme per
  anello: ci sono (`avq.seed`, `enrich.seed`, `nucleo.seme`), non ancora
  esercitate.
- Gli anelli 3–4 della produzione di Cesena non coincidono con il codice
  attuale (§13): è il TODO `[gemello]` «rigenerare gli anelli 3+4 della
  flotta», decisione di release, non del banco.
- ~~`holdout_z.py`, `verifica_vincoli.py` e gli altri diagnostici leggono da
  `data/comuni` con percorso fisso~~ — fatto in M1: `--dir/--piena-dir/--out`
  in `holdout_z.py`, `--pop-file` e radice da `gsp.common` in
  `verifica_vincoli.py`; gli altri avevano già `--pop-file`.
- I JSON di `misure/` registrano i percorsi assoluti dei file letti
  (`cs`, `popolazione`): è l'unica differenza fra le misure di una corsa e
  della sua replica. Provenienza utile, ma impedisce il `cmp`; da decidere
  se renderli relativi.
- Quando la base è un'altra corsa e l'anello 1 non si rigenera, i prodotti
  ereditati si cercano con il livello effettivo della base; non ancora
  esercitato (M0 ha usato solo `base: produzione`).
- Dove sta `holdout_z.py`: oggi in `scripts/esempio/`, ma è la misura di
  confronto principale; va promosso in `diagnostica/` o chiamato da lì.
- ~~`to_parquet.py` deve accettare una radice diversa da `data/`~~ — in
  v0.2 risultava bastare `GSP_COMUNI_DIR`; **corretto in v0.5**: non
  bastava, perché il regime pubblico passa da `gsp.individui.carica`, che
  risolve la popolazione con i nomi di produzione (`POP_CANDIDATES`) e i
  nuclei da `data/nuclei`. Servivano `pop_file` e `nuclei_dir` in
  `esporta_pubblico` e `--pop-file`/`--nuclei-dir` in `to_parquet.py`
  (M3); con i default il Parquet di Castenaso resta byte-identico al bundle.
- Il nome (§1).

---

## 11. Misure di M0 (11/10/2026)

Tutto *misurato*; log in `misure/banco_M0/`. Commit di gsp `9ebf594` con
albero non pulito (il codice di `gsp.banco` non era ancora committato: le
corse di M0 non sono citabili per commit, e servono solo a collaudare il
banco). Pool uguale a quello di produzione (Cesena 125.000, Bologna
500.000), flag di produzione, `--senza Z3`, anelli 1–4, base produzione.

**Tempi per fase (s)**

| corsa | cs_build | fit_cs | assign_avq | enrich | assign_nucleo | totale |
|---|---|---|---|---|---|---|
| Cesena 040007 | 0,5 | 69,4 | 3,2 | 8,0 | 4,2 | 85 |
| Cesena, replica | 0,5 | 70,7 | 6,3 | 8,1 | 4,3 | 90 |
| Bologna 037006 | 0,6 | 87,2 | 7,6 | 17,8 | 19,9 | 133 |

Il fit di Bologna, esatto, dura 87 s: non «pochi minuti». La catena intera
sta sotto i tre minuti anche per il comune più grande della flotta ER, il
che per la dashboard significa «clic e aspetta» in locale.

**Esiti**

- MRE(α>0) del fit senza Z3: Cesena 6,903·10⁻⁴, Bologna 5,518·10⁻⁴
  (`log/fit_cs.log` delle corse).
- Combinazioni impossibili nelle `_avq_full`: 0 su 96.066 (Cesena), 0 su
  390.098 (Bologna).
- `--senza` contro `--blocks` (Cesena, scratch, tre cartelle isolate): 1.158
  vincoli in entrambi, nessuno solo da una parte; `vars`, `domain_sizes`,
  `categories` uguali; popolazioni byte-identiche; MRE identica.
- Anello 1 del banco contro la catena di `holdout_run.sh` (stesso pool):
  `cs`, `targets`, `popolazione` uguali; `fit_<LIV>.json` diverso nella sola
  chiave `t_exact_s` (64,6 s contro 67,6 s).
- `replica` di Cesena: otto prodotti su otto uguali, una volta tolte le
  chiavi dell'orologio (`t_exact_s`; `generato` nella diagnostica dei
  nuclei, 15:00 contro 15:04).

---

## 12. Misure di M1 (11/10/2026)

Tutto *misurato*; log in `misure/banco_M1/`. Patch chirurgiche, un commit:
`verifica_vincoli.py` v2.1 (`--pop-file` CSV, `--json`, radice da
`gsp.common`), `verifica_donor.py` v1.1 (`--json`), `holdout_z.py` v1.1
(`--dir`, `--piena-dir`, `--out`), `riepilogo_diagnostica.py` v1.1
(`--json`, `--comuni`).

**Il criterio di M1.** `riepilogo_diagnostica.py` sulla produzione, via
regex sui `.txt` del report (`diagnostica_report_v1.0`) e via `--json` sui
sommari scritti oggi: righe identiche per Castenaso (K6C) e Piacenza (K9C),
tabelle III.3a e III.3b. Inoltre, per Castenaso, `verifica_vincoli.py` dà
lo stesso blocco `globale` dal Parquet del bundle e dal CSV
`popolazione_K6C.csv`, e lo stesso testo del report a meno delle righe
`[info]` (`riepilogo_json_vs_regex.txt`).

**Le corse di M0 misurate** (`misura`, numeri di testa dall'indice):

| | Cesena senza Z3 | Bologna senza Z3 |
|---|---|---|
| celle α>0 | 1.123 | 1.535 |
| MRE oss / att | 9,16 % / 10,76 % | 6,91 % / 5,61 % |
| \|z\| medio · sd(z) | 0,795 · 0,996 | 0,833 · 1,283 |
| quota \|z\|>3 | 0,36 % | 0,65 % |
| zeri violati | 0 | 0 |
| hold-out Z3: TVD pavimento · hold-out · indipendenza | 0,0137 · 0,0533 · 0,0528 | 0,0086 · 0,0713 · 0,0818 |
| posizione nel divario | 101 % | 86 % |
| firme AVQ · n_eff SALUTE · banda | 4.143 · 980 · 9,9 | 4.169 · 966 · 20,1 |
| MAE per sezione (popolazione) | 1,06 | 1,36 |
| nuclei · ampiezza media · coniugati incoerenti | 43.239 · 2,22 · 25,7 % | 210.140 · 1,86 · 18,8 % |

Lettura, senza trarne ancora conclusioni (è un collaudo del banco, non un
risultato): a Cesena il hold-out di Z3 cade sull'indipendenza (101 %), cioè
nulla della geografia dell'istruzione passa per gli altri blocchi; a Bologna
all'86 %. Il MRE osservato di Bologna sopra l'atteso e sd(z) = 1,28 sono
coerenti con il fit esatto su un dominio grande; da confrontare con la
corsa piena in M2.

**Replica.** Le misure della replica di Cesena coincidono con l'originale:
`holdout_Z3.json`, `sezioni.json`, `celle.csv`, `quinq.csv`, `istr_eta.csv`
byte-identici; `vincoli.json` e `donor.json` differiscono solo nei percorsi
registrati (`cs`, `popolazione`), che contengono l'id della corsa (§10).

**indice.parquet**: 3 corse, colonne del manifesto più i numeri di testa
(`mre_oss`, `mre_att`, `z_abs_medio`, `sd_z`, `quota_z3`, `zeri_violati`,
`tvd_*_Z3`, `posizione_Z3`, `firme`, `n_eff_salute`, `banda_salute`,
`mae_sezione_pop`, `nuclei`, `ampiezza_media`, `coniugati_incoerenti`).

---

## 13. Misure di M2 (11/10/2026)

Tutto *misurato*; log in `misure/banco_M2/`. Cesena, pool 125.000, flag di
produzione, anelli 1–4. Tre corse nuove: replica dell'hold-out Z3 con il
nuovo `fit_cs.py` e seme di default, hold-out Z3 con `fit.seed=7`, corsa
piena senza manopole.

**Il `--seed` non cambia la produzione.** Replica con seme di default: cs,
targets, popolazione, `_avq`, `_avq_full`, nuclei e diagnostica
byte-identici all'originale; `fit_<LIV>.json` diverso solo per la chiave
nuova `seed` e il tempo.

**La corsa piena contro la produzione in `data/comuni/040007`** (sola
lettura): cs, targets, `popolazione_K9C.csv` e `_avq` byte-identici;
`_avq_full` e `nuclei_040007.csv` diversi. Gli anelli 1–2 di produzione si
riproducono oggi; gli anelli 3–4 no, perché `enrich.py` è stato corretto
dopo (età singola, gsp `6224a94`). Noto e in TODO (§10).

**TVD piena contro senza Z3, con il nullo** (seme 42 contro seme 7, stessa
corsa senza Z3; 120 combinazioni, le prime per TVD):

| variabili | TVD | nullo | rapporto |
|---|---|---|---|
| zona × istruzione | 0,0519 | 0,0161 | 3,2 |
| zona × MH | 0,0240 | 0,0285 | 0,8 |
| condizione × MH | 0,0117 | 0,0126 | 0,9 |
| zona × FIDUCIA | 0,0113 | 0,0098 | 1,2 |
| zona × SALUTE | 0,0110 | 0,0120 | 0,9 |
| zona × condizione | 0,0070 | 0,0144 | 0,5 |
| zona × background | 0,0058 | 0,0117 | 0,5 |

Sopra il nullo c'è un solo incrocio, ed è il blocco tolto. Tutto il resto
sta fra 0,5 e 1,2 volte il nullo: togliere Z3 non sposta nessun'altra
relazione oltre quanto fa il campionamento. È la lettura che la nota
chiedeva in §4 («nessun numero senza il suo nullo») e la prima misura del
banco che dice qualcosa sulla popolazione e non sul banco.

**Il seme muove anche le misure di hold-out.** La posizione nel divario di
Z3 passa da 101 % (seme 42) a 110 % (seme 7): la metrica di `holdout_z.py`
ha una variabilità di campionamento di circa dieci punti su Cesena, che
va dichiarata quando la si cita. `n_eff` SALUTE: 980 contro 1.006.
MRE osservato: 9,16 % contro 9,13 %, atteso 10,76 % in entrambe.

**indice.parquet**: 6 corse.

---

## 14. Misure di M3 (11/10/2026)

Tutto *misurato* dove possibile; log in `misure/banco_M3/`.

**Patch.** gsp: `individui.carica(pop_file=)` e
`esporta_pubblico(pop_file=, nuclei_dir=)`, default invariati. Animarium:
`to_parquet.py` v2.1 (`--pop-file` anche in regime pubblico, `--nuclei-dir`,
livello dal nome del file), `pannello_marginali.html` con `?bundle=`,
`build/banco.html` nuova, README.

**Regressione.** `to_parquet.py` patchato, senza flag nuovi, su Castenaso
di produzione: Parquet byte-identico a `bundle/comuni/037021/pop.parquet`
della release.

**Bundle di `037006_senza_Z3_20261011a`**: 390.098 righe, 43 colonne,
nessuna colonna proibita (`uid`, `via`, `civico`, `indirizzo_fonte`),
`nucleo` e `ruolo` presenti, 7,42 MB; riferimenti dal cs pieno di
produzione (copertura 67/333 come nella release). Bundle anche per le due
corse di Cesena (1,8 MB ciascuno).

**HTTP.** `serve_range.py --dir ~/progetti`: `banco.html`, il pannello con
`?bundle=…&comune=037006`, `indice.json`, `misure/vincoli.json`,
`bundle/comuni.json`, `manifest.json`, `confronti/*.json` rispondono 200
con `text/html` o `application/json`; `pop.parquet` con `Range` risponde
206. `node --check` sugli script delle due pagine: nessun errore.

**Non misurato.** Il rendering nel browser e le query DuckDB-WASM sul
bundle di corsa: sulla macchina non c'è un browser headless. Da fare a mano
aprendo `http://localhost:8000/animarium/build/banco.html`, poi
«pannello» sulla riga di Bologna.
