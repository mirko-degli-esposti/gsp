# Priors LLM sulla scelta post-diploma — risultati. v2

**nota_risultati_scelta_v2 — 21 agosto 2026 · sostituisce la v1 (che
resta agli atti: registrava P1-P3 prima dei dati; qui ci sono i
verdetti)**

Campagne: tre modelli (DeepSeek-chat, GPT-4o-mini, Claude Haiku 4.5) ·
campione `agenti_scelta_n432_s0` (livello A, versionato: 432 agenti,
36 celle diploma3 × gen3 × sesso × background, 10 comuni, 19-22) ·
fase 1: 3 repliche × 2 item indipendenti, T 0,3 (3.888 batterie) ·
fase 2: SOLI TECNICI (144), T 1,0, 4 repliche = ciclo completo di
rotazioni (1.728 batterie). Parsing ≥93% pulito ovunque, None ≤0,3%.
Ipotesi H1-H5 e predizioni P1-P3 registrate prima dei rispettivi dati
(nota campione §6; nota risultati v1 §8; file di campagna). Benchmark:
`nota_benchmark_scelta_v1`.

---

## 1. La sintesi

**I tre modelli condividono la conoscenza ordinale e divergono nella
regola di risposta — e la regola e' una link function misurabile.**
Le rho di Spearman sulla prob per agente sono 0,70-0,83: ordinano quasi
gli stessi individui. Tutti i gradienti sociali hanno il segno giusto
dove non nulli. Cio' che distingue i modelli e' come la credenza
diventa scelta, e la fase 2 lo ha ridotto a due parametri (§5):

    quota = sigma( a + b · logit(credenza) )

| modello | a (bias) | b (ripidita') | R² | carattere |
|---|---:|---:|---:|---|
| Haiku 4.5 | −1,28 | 3,04 | 0,88 | pessimista tranchant, coerente |
| DeepSeek | +0,68 | 1,67 | 0,61 | ottimista morbido |
| GPT-4o-mini | n.i. | n.i. | 0,38 | non identificabile: continuo morto |

(b=1, a=0 sarebbe il campionamento dalla propria credenza; l'argmax
puro e' b→∞. Stima su 12 celle dei tecnici, quota T=1,0 contro
credenza T=0,3; figura `scatter_quota_credenza.png`.)

E' la conclusione SIVE — la distorsione vive nel response behavior, non
nella conoscenza — con un passo in piu': il response behavior non e'
solo diverso dalla conoscenza, e' *parametrizzabile* per modello, come
la' il gain <1 sulla trasmissione. Resa possibile dai DUE ITEM
INDIPENDENTI e dalle DUE TEMPERATURE.

## 2. Credenza e regola: misura sì, meccanismo no — *aggiornato in v2*

L'item categoriale chiede «la situazione PIU' PROBABILE»: chiede una
funzione della credenza, non un'estrazione. La v1 ipotizzava che la
funzione fosse l'argmax e che T=1,0 la sciogliesse in campionamento
(P1). **P1 e' falsificata** (§4): la temperatura ammorbidisce la soglia
ma non recupera la credenza. La distinzione di MISURA sopravvive
intatta — la calibrazione si legge sul continuo, il categoriale misura
la regola — il MECCANISMO ipotizzato (argmax termico) e' ritrattato e
sostituito dalla link function di §1.

Le credenze, dove il confronto e' legittimo (prob media, tecnici e
licei = maturita'):

| | reale 73,6 / 34,5 | liceo / tecnico |
|---|---|---|
| DeepSeek | | **72 / 49** — la piu' vicina |
| Haiku | | 70 / 40 — seconda |
| GPT-mini | | 75 / 70 — satura sull'ancora 70 |

## 3. I tre ritratti (fase 1, invariati nella sostanza; coordinate da §1)

**DeepSeek — soglia mediana, credenze quasi calibrate.** 99,3 / 56,2 /
3,7 sul categoriale; delibera solo nei tecnici, dove i gradienti si
dispiegano interi (genitori bassa→laurea+: M 17→71%, F 38→83%): i
gradienti sociali non solo amplificati sul categoriale — CONCENTRATI
nella classe intermedia. Ancore 30/70.

**GPT-4o-mini — l'ottimista col primacy.** Su rotazioni pulite: 97,9 /
82,3 / 34,0; continuo inchiodato a ~70 (76% delle risposte), contrasti
miti, livelli gonfiati. **Primacy strutturale ~2/3** (v. §4, P2).

**Haiku 4.5 — il pessimista a soglie dure.** 94,7 / 7,6 / 0,0; genitori
binarizzati (laurea+ +4,3, diploma +0,4), sesso nullo, ancore
pseudo-precise. Professionale 0/432: quasi-separazione dichiarata.

## 4. I verdetti — H (fase 1) e P (fase 2)

**H1** (beta diploma > reale +1,67): confermata sul canale categoriale
(DeepSeek +5,8; Haiku oltre soglia; GPT +2,2), ridimensionata dalla
scomposizione: l'eccesso sta nella regola (b>1, §1), le credenze sono
vicine al reale. La gamba professionale e' in H5 (la classe e'
qualifiche, riferimento ~0).

**H2** (beta genitori < reale +1,49): **falsificata** — DeepSeek +2,7 e
Haiku +4,3 sovrappesano; GPT +1,4 ~. Il meccanismo «regolarita' poco
narrata» era sbagliato.

**H3** (eta' negativa ~−0,85): confermata (−0,75 / −0,75 / −0,34).

**H4** (mutismo categoriale): falsificata per tutti; con SIVE accanto,
**il mutismo e' proprieta' dell'item, non del modello**.

**H5** (qualifica trattata come diploma debole, non come non-accesso):
confermata a tre voci in forma raffinata — gradiente presente in
almeno un canale per tutti, regola assente per tutti; il canale che
vede dipende dal modello. A una qualifica triennale i tre dichiarano
prob 28 / 35 / 70. Mai lo zero normativo.

**P1** (a T=1,0 la quota migra verso la credenza): **falsificata come
formulata**, con diagnosi per modello — Haiku migra un decimo del
tragitto (7,6→11,5 contro credenza 40: la soglia si ammorbidisce, non
si scioglie); DeepSeek si ALLONTANA (56→63 contro 49), e la link
function localizza il perche': non rigidita' ma BIAS (a=+0,68 —
a T=1,0 e' ottimista rispetto alla propria credenza); GPT «migra» ma il
suo verdetto e' non interpretabile (credenza piatta + primacy).
La dispersione sale e la stabilita' scende come atteso dal
campionamento: il campionamento c'e', ma attorno alla soglia, non
dalla credenza.

**P2** (primacy GPT strutturale): **confermata a ciclo completo** —
curva di posizione 50,5 / 21,5 / 21,3 / 6,6% (attesa 25% ciascuna);
ITS 84,0% quando primo, 0,2% altrove, a T=1,0. Primacy in testa E
recency negativo in coda. DeepSeek e Haiku quasi piatti (19-30%).
Per GPT-mini come rispondente a scelte multiple, l'ordine delle
opzioni E' il trattamento.

**P3** (quote T=1,0 ~ credenze entro le ancore): falsificata come
soglia fissa (scarti medi 12-29 punti), RIASSORBITA dalla link
function: gli scarti non sono rumore oltre soglia, sono la sigmoide
(a,b) — vicino al 50% i canali concordano (bassa·M·straniero di
DeepSeek: 46% vs 46%), lontano si apre la forbice (diploma·M·ita:
88% vs 52%).

## 5. La link function — *il risultato della fase 2*

Su doppia scala logit, per cella: logit(quota_T10) = a + b·logit(
credenza_T03). Stime in §1. Letture:

- **Haiku (−1,28; 3,04; R² 0,88)**: il categoriale e' funzione quasi
  deterministica della credenza — canali ACCOPPIATI da una link
  distorta ma stabile. Pessimismo (a) e affilamento (b) separati e
  misurati.
- **DeepSeek (+0,68; 1,67; R² 0,61)**: affilamento mite, bias
  ottimista a T alta; un terzo di varianza fuori — accoppiati con
  gioco.
- **GPT (R² 0,38, b=12,7 non credibile)**: il regressore (la sua
  credenza) vive in 0,66-0,75 — escursione ~0,4 logit, pendenza non
  identificata. Il test e' cieco su di lui PER il suo continuo morto:
  che e' una conferma del ritratto, non un buco del test.

Limite dichiarato: 12 celle di UNA classe. La verifica fuori-campione
— le celle di liceo e professionale, dove credenza e quota T=0,3 gia'
esistono — costa zero chiamate e decide se (a,b) e' del modello o dei
tecnici: **primo aperto della fase 3** (con l'avvertenza che la' la
quota e' a T=0,3, quindi la b attesa e' piu' alta: il confronto pulito
e' sull'ordinamento a fra modelli, non sui valori).

---

## §5-bis — Verifica fuori-campione della link function *(addendum 21/8/2026, sera)*

Programmata come primo aperto della fase 3 (§5, §9.1); eseguita con
`scripts/narrativa/verifica_link.py` sulle 36 celle a T=0,3 (liceo e
professionale MAI usati nella stima di fase 2; GPT su r0+r2; stima a
due epsilon per il clipping — 10-24 celle sature per modello; gli
ordinamenti non dipendono dall'epsilon, i valori di b sì e vanno sempre
citati con l'epsilon accanto).

**Verdetti**: L2 regge (a_Haiku −0,63 < a_DeepSeek +0,28: il
pessimista resta pessimista su celle mai viste); L3 regge e sale
(R² 0,87-0,96 — DeepSeek a 0,96 su 36 celle: la sua quota e' funzione
quasi deterministica della sua credenza su tutto il dominio);
**L1 regge solo per DeepSeek** (b 3,5→1,7 dal freddo al caldo) e
**cade per Haiku** (3,6→3,0, entro il rumore del clipping).

**Revisione della link function — due regimi di soglia:**

| modello | b a T=0,3 (eps 0,02/0,05) | b a T=1,0 | regime |
|---|---|---|---|
| DeepSeek | 3,52 / 2,81 | 1,67 | **termico**: b = b(T), il calore ammorbidisce |
| Haiku 4.5 | 3,64 / 2,84 | 3,04 | **costituzionale**: b invariante a T |
| GPT-4o-mini | 8,24 / 6,72 | n.i. | caso estremo (v. sotto) |

Coerente con P1 di fase 2: la migrazione minima di Haiku (7,6→11,5%
contro credenza 40) non era un'anomalia — la sua soglia sta PRIMA del
campionamento. Il bias a si accentua a T alta per entrambi (Haiku
−0,6→−1,3; DeepSeek +0,3→+0,7), ma le due stime non sono a parita' di
dominio (36 celle vs 12): agli atti senza sovrainterpretare.

**GPT identificato**: le 36 celle danno al suo regressore l'escursione
che i tecnici non avevano (credenza 66-75) e la stima diventa leggibile
— b ~7-8, R² 0,67-0,73. Il ritratto si completa: **la sigmoide piu'
ripida dei tre montata sul continuo piu' piatto dei tre** — quasi tutto
il lavoro lo fa la soglia, quasi niente la credenza. La tabella di §1
va letta con questa riga al posto di «non identificabile».

**Conseguenza per la fase 3.2 (iniezione delle regole)**: lo strumento
appena validato misura anche l'intervento — se le regole correggono H5,
il COME e' osservabile sulla link (spostamento di a, o deformazione
locale sulle celle qualifica). Il world model iniettato diventa un
intervento sulla link function, non solo sulle quote.

Provenienza: `note/verifica_link.md` (output macchina),
`figure/scatter_quota_credenza.png` (fase 2). Predizioni L1-L3
registrate nel docstring dello script prima dell'esecuzione.

## 6. Altri esiti (invariati dalla v1)

- **ITS invisibili a tutti** (0,1 / 0,9 pulito / 0%; l'84% di GPT a
  r1 e' primacy): il canale che l'orientamento pubblico vorrebbe
  potenziare non esiste nei priors di nessuno.
- **I comuni non sono letti**: rho col benchmark interno +0,33 / +0,32
  / +0,18 (n=10, n.s.); Rimini controesempio. Covariata di disturbo.
- **Ancore**: tre griglie (30/70; ~70 fisso; pseudo-precisi);
  risoluzione effettiva ~4-5 gradini.

## 7. Strumento: difetti e correzioni

- Rotazione `replica % 4` con 3 repliche (fase 1): ciclo incompleto —
  primacy GPT ~2/3 della risposta, aggregati contaminati, letture GPT
  su r0+r2. CORRETTO in fase 2 (4 repliche); per il futuro: 4 repliche
  o ordine casuale registrato.
- A T=1,0 il parsing regge (pulito ≥93,8%, None ≤0,3%): l'item chiuso
  sopravvive alla temperatura.

## 8. Registro delle ritrattazioni (cumulativo)

1. «I LLM amplificano i gradienti sociali 2-3x» → canale categoriale
   di un modello, senza scomposizione.
2. «GPT-mini quasi calibrato» → aggregati contaminati dal primacy.
3. La riga `professionale` nei contrasti → qualifiche, benchmark ~0,
   spostata in H5.
4. Il meccanismo di H2 (narrato vs statistico) → falsificato.
5. Il controllo di posizione «a costo zero» → sottodimensionato di una
   replica.
6. **(v2)** Il meccanismo argmax-termico della scomposizione (v1 §2)
   → falsificato da P1; sostituito dalla link function (a,b), che
   spiega anche P3. La scomposizione resta come distinzione di misura.

## 9. Fase 3 — *proposta*

1. **Verifica fuori-campione della link function** (zero chiamate,
   §5).
2. **Iniezione delle REGOLE** — qualifica = non-accesso; esistono gli
   ITS — mai dei tassi: verifica se H5 si corregge e se gli ITS
   compaiono. E' la taratura legittima dello strumento (world model
   si', statistiche-bersaglio no), il ponte al mestiere-simulatore e a
   Caffaro/SimComm a settembre.
3. In coda, dal §5 della v1: il campionamento esternalizzato
   (Bernoulli sulla credenza, canale rng per uid) come architettura
   del simulatore — ora con la giustificazione empirica che i modelli
   NON campionano da soli dalla propria credenza (P1), quindi
   esternalizzare non e' un vezzo: e' l'unico modo di averla.

## Provenienza

Fase 1: `campagna_agenti_scelta_n432_s0_{modello}_r3_t03.json` ·
fase 2: `campagna_agenti_scelta_n432_s0_tecnico_{modello}_r4_t10.json`
(tutte fuori repo, Zenodo a fine giro) · analisi macchina:
`note/analisi_scelta_tre_modelli.md` (aggregati GPT contaminati dal
primacy — avviso in testa alla v1), `note/analisi_t10.md` · figure:
`figure/prob_ancore.png`, `figure/quota_diploma_gen.png`,
`figure/scatter_quota_credenza.png` · campione versionato nel repo ·
verifiche inline (posizione, comuni, scatter) riproducibili dai JSON.
