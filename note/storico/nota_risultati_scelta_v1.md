# Priors LLM sulla scelta post-diploma — risultati a tre modelli

**nota_risultati_scelta_v1 — 21 agosto 2026**

Campagne: DeepSeek-chat, GPT-4o-mini, Claude Haiku 4.5 · campione
`agenti_scelta_n432_s0` (livello A, versionato: 432 agenti, 36 celle
diploma3 × gen3 × sesso × background, 10 comuni, finestra 19-22) ·
3 repliche × 2 item indipendenti × T 0,3 · 3.888 batterie, parsing
100/100/93% pulito, nessun None. Ipotesi H1-H5 registrate prima dei
dati in `nota_campione_diplomati_v1` §6 e nei file di campagna; i
benchmark in `nota_benchmark_scelta_v1`. I verdetti stanno QUI: le due
note a monte non si toccano.

---

## 1. La sintesi

**I tre modelli condividono la conoscenza ordinale e divergono
nell'idioma di risposta.** Le rho di Spearman sulla prob per agente
sono 0,70-0,83: ordinano quasi gli stessi individui nello stesso modo,
e tutti i gradienti sociali hanno il segno giusto dove non nulli
(diploma, genitori, eta'; sesso e origine in due su tre). Cio' che
diverge — e di molto — e' come la credenza diventa risposta: soglie in
posizioni diverse, ancore diverse, sensibilita' alla posizione diverse.
La frase «i LLM amplificano i gradienti sociali», scritta a caldo dopo
la prima campagna, e' RITRATTATA in questa forma: l'amplificazione sul
canale categoriale e' reale ma e' in gran parte un artefatto della
regola di decisione, non della credenza (§2), e la sua entita' e'
idiosincratica per modello.

E' la conclusione SIVE — la distorsione vive nel response behavior, non
nella conoscenza — riapparsa sul lato dei priors. Resa visibile da una
scelta di disegno: i DUE ITEM INDIPENDENTI. Per GPT il categoriale
informa e il continuo mente; per Haiku quasi l'opposto; per DeepSeek
concordano. Un item solo, o un JSON unico coerentizzato, avrebbe
mostrato un modello solo.

## 2. La scomposizione credenza / regola di decisione — *metodologico, centrale*

L'item categoriale chiede «la situazione PIU' PROBABILE»: chiede
l'argmax. Un agente con credenza P(universita')=0,72 DEVE rispondere
universita' il 100% delle volte: la saturazione del categoriale non e'
(tutta) distorsione — e' matematica della domanda. Il tasso reale
(73,6% dei liceali) e' invece una quota di popolazione che ingloba
l'eterogeneita' dentro la cella, che il profilo non porta.

Conseguenze: **la calibrazione si legge sul continuo** (le credenze);
il categoriale misura la regola di decisione; i beta del logit
categoriale confondono le due cose. Riletti cosi':

| credenza (prob media): liceo / tecnico | reale 73,6 / 34,5 |
|---|---|
| DeepSeek | **72 / 49** — la piu' vicina |
| Haiku | 70 / 40 — seconda |
| GPT-mini | 75 / 70 — saturata in alto |

Test diretto della scomposizione: l'esperimento T=1,0 (§8).

## 3. I tre ritratti

**DeepSeek — soglia mediana, credenze quasi calibrate.** Categoriale:
99,3 / 56,2 / 3,7. Satura gli estremi (l'unico liceale dissidente e' la
cella piu' svantaggiata: donna, straniera, genitori bassa, 21 anni) e
delibera SOLO nei tecnici, dove i gradienti si dispiegano interi
(genitori bassa→laurea+: M 17→71%, F 38→83%). I gradienti sociali non
sono solo amplificati sul categoriale: sono CONCENTRATI nella classe
intermedia, dove nel reale operano ovunque. Ancore 30/70 (93% multipli
di 10), stabilita' 85,6%.

**GPT-4o-mini — l'ottimista col primacy.** Su rotazioni pulite (r0+r2):
97,9 / **82,3** / 34,0 — manda all'universita' quasi tutti tranne le
qualifiche; contrasto liceo-tecnico il piu' mite (+2,3 log-odds) ma
livelli gonfiati ovunque, coerenti col continuo inchiodato a ~70 (76%
delle prob = 70; per classe: 75/70/66, otto punti dove DeepSeek ne ha
45). Il continuo di GPT e' quasi muto; il categoriale e' vivo e stabile
nel contenuto (80,6% fra r0 e r2). **Primacy bias ~2/3**: quando ITS e'
presentato per primo (r1), lo sceglie il 67,4% contro lo 0,9% delle
altre rotazioni — la lode «quasi calibrato» della prima lettura e'
RITRATTATA (era fondata su aggregati contaminati).

**Haiku 4.5 — il pessimista a soglie dure.** 94,7 / **7,6** / 0,0: la
zona di deliberazione che DeepSeek ha nei tecnici in Haiku e' morta —
stessa architettura, soglia piu' alta (credenze 70/40/28: il tecnico a
40 muore nell'argmax). Genitori BINARIZZATI (laurea+ +4,3, diploma
+0,4: conta la laurea, non il gradiente), sesso nullo, ancore
pseudo-precise (0% multipli di 10: 35, 72, 25...). Professionale 0/432:
quasi-separazione, beta «oltre soglia», se degenerato — segnalato, non
nascosto.

## 4. I verdetti sulle ipotesi registrate

**H1 (beta diploma LLM > reale +1,67)** — confermata sul canale
categoriale per DeepSeek (+5,8) e Haiku (oltre soglia), mite per GPT
(+2,2); ma la scomposizione §2 la ridimensiona: sulle credenze DeepSeek
e Haiku sono vicini al reale. Verdetto onesto: *l'eccesso sta nella
regola di decisione piu' che nella credenza*. La gamba professionale e'
USCITA dal test (la classe contiene solo qualifiche, riferimento ~0:
v. nota campione §4-5) ed e' entrata in H5.

**H2 (beta genitori LLM < reale +1,49)** — **falsificata** per DeepSeek
(+2,7) e Haiku (+4,3 su laurea+), circa rispettata da GPT (+1,4). Il
meccanismo ipotizzato («regolarita' statistica poco narrata») e'
sbagliato: due modelli su tre pesano i genitori PIU' del marginale
reale — che gia' ingloba il canale scelta-scuola, qui tagliato per
costruzione. La registrazione pre-dati esisteva per questo momento.

**H3 (eta' negativa ~−0,85)** — confermata: −0,75 DeepSeek e Haiku
(quasi esatta), −0,34 GPT (attenuata, coerente col suo ottimismo
uniforme). L'unico asse quasi-calibrato ovunque: ipotesi a margine, da
non promuovere oltre — l'eta' nel prompt e' un numero, gli altri assi
sono categorie sociali.

**H4 (mutismo categoriale possibile)** — falsificata per tutti e tre.
Con SIVE accanto (GPT e Haiku muti sulle emozioni a n=600): **il
mutismo e' una proprieta' dell'item, non del modello**. Comportamentale
-fattuale: vivo; emotivo-categoriale: muto.

**H5 (la qualifica trattata come diploma debole, non come non-accesso)**
— confermata a tre voci, in forma raffinata: *tutti possiedono il
gradiente in almeno un canale, nessuno possiede la regola, e quale
canale veda il gradiente dipende dal modello*. Tecnici, qualifica vs
maturita': DeepSeek prob 35 vs 51 e univ 21 vs 60%; Haiku schiacciata
nel pavimento (0 vs 8,4%); GPT continuo CIECO (69,5 vs 70,5) ma
categoriale vivo (46 vs 86%, r0+r2). Il numero applicativo: a un
giovane con qualifica triennale — titolo che NON accede — i tre modelli
dichiarano prob 28, 35 e 70. Mai lo zero normativo.

## 5. Altri esiti

- **ITS invisibili a tutti** (0,1 / 0,9 pulito / 0%): il canale che le
  politiche di orientamento vorrebbero potenziare non esiste nei priors
  di nessuno dei tre. (Il 23,1% di GPT nell'aggregato era interamente
  il primacy di r1.)
- **I comuni non sono letti**: rho col benchmark interno (quota
  studente per comune, n=10) +0,33 / +0,32 / +0,18 — indistinguibili da
  zero; Rimini e' seconda nel dato e ultima per DeepSeek. Gli
  effetti-comune del logit si archiviano come priors urbani non
  validati o rumore; il comune resta covariata di disturbo.
- **Ancore**: tre griglie diverse (30/70 tondi; 70 quasi fisso;
  pseudo-precisi non tondi). La risoluzione effettiva del continuo e'
  ~4-5 gradini per tutti.

## 6. Il difetto di strumento — *ritrattazione di disegno*

La rotazione delle opzioni era `replica % 4` con **3 repliche su 4
rotazioni**: ciclo incompleto, nessuna media bilanciata per posizione.
Per DeepSeek e Haiku l'effetto rotazione e' 5-8 punti (da dichiarare);
per GPT e' ~2/3 della risposta e contamina ogni aggregato sulle tre
repliche — le letture pulite di GPT in questa nota sono su r0+r2.
Correzione per ogni corsa futura: **4 repliche = ciclo completo**,
oppure ordine casuale per chiamata con ordine registrato nel log.
Il primacy stesso e' pero' un finding: per GPT-mini l'ordine delle
opzioni E' il trattamento — rilevante per chiunque lo usi come
rispondente a scelta multipla.

## 7. Registro delle ritrattazioni di questa fase

1. «I LLM amplificano i gradienti sociali 2-3x» → era il canale
   categoriale di un modello, riletto senza la scomposizione §2.
2. «GPT-mini quasi calibrato» → aggregati contaminati dal primacy.
3. La riga `professionale` nella prima tabella dei contrasti → la
   classe e' qualifiche (vintage 2011), benchmark ~0, spostata in H5.
4. Il meccanismo di H2 (narrato vs statistico) → falsificato.
5. Il controllo di posizione «a costo zero» → sottodimensionato di una
   replica (§6).

## 8. Il prossimo esperimento — *proposto*

**T=1,0, 4 repliche, sottocampione tecnici** (144 agenti — la classe
viva; ~2.300 chiamate/modello). Predizioni registrate ORA:

- **P1**: a T=1,0 la quota categoriale migra dalle soglie verso le
  credenze dichiarate (DeepSeek tecnici: dal 56% verso ~49). Se accade,
  la scomposizione credenza/argmax e' dimostrata empiricamente.
- **P2**: il primacy di GPT persiste a T alta (e' strutturale, non da
  campionamento); misurato a ciclo completo di rotazioni.
- **P3** (se P1 regge): le quote a T=1,0 per cella coincidono con le
  prob medie a T=0,3 entro la risoluzione delle ancore.

In coda, il ponte applicativo: **iniezione delle regole** (qualifica =
non-accesso; esistono gli ITS) — mai dei tassi — per verificare se H5
si corregge: la dimostrazione che la taratura legittima dello strumento
funziona, e il confine misurato fra world model e barare.

## Provenienza

Campagne: `dati/campagne/scelta/campagna_agenti_scelta_n432_s0_{deepseek-chat,gpt-4o-mini,claude-haiku-4.5}_r3_t03.json`
(fuori repo, Zenodo a fine giro) · analisi: `note/analisi_scelta_tre_modelli.md`
(output macchina, con i §2-§5 di GPT contaminati dal primacy — le
letture corrette sono in questa nota) · verifiche posizione e comuni:
script inline del 21/8, riprodicibili dai JSON · campione: versionato
nel repo.
