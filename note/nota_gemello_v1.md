# Esperimento a gemello identico — nota operativa per Claude Code

*v1 — 10/10/2026. Nota di progetto per il paper B («cosa la massima entropia
ricostruisce e cosa no»). Scritta per essere eseguita da Claude Code: dice
cosa costruire, in che ordine, con quali criteri di accettazione e quali
trappole evitare. Dove la nota non conosce il codice di `gsp` lo dichiara
con **[VERIFICA NEL REPO]**: in quei punti si legge il codice, non si
indovina.*

---

## 0. Scopo, in una frase

Prendere una popolazione **vera nota** T, pubblicarne solo le tabelle che
pubblicherebbe l'ISTAT, ricostruirla con Animarium e con i metodi standard
(IPF a seme, modello di piccola area Fay–Herriot), e misurare chi risponde
meglio a domande di difficoltà crescente — **prevedendo a priori** l'errore
di Animarium con la teoria della massima entropia.

La tesi da mettere alla prova **non** è «Animarium è più accurato». È:

> Animarium è l'unico metodo che risponde a **tutte** le domande, in modo
> coerente, **partendo solo da tabelle pubbliche**, con un errore che si
> **prevede** dal contenuto d'informazione fuori vincolo. I metodi a
> campione lo battono quando hanno un'indagine abbastanza grande; l'esperimento
> misura **quanto grande**, domanda per domanda.

---

## 1. Notazione

| simbolo | significato |
|---|---|
| X | spazio degli stati individuali dell'anello 1 (zona, sesso, età, stato civile, cittadinanza, istruzione, condizione, background, origine genitori), con le esclusioni α=0 |
| f : X → ℝᵐ | feature dei vincoli (indicatori delle celle dei blocchi del constraint set) |
| T | popolazione verità: individui + nuclei + collocazione (zona, sezione/IRIS) |
| Π | operatore di pubblicazione: T ↦ tabelle nella forma del constraint set ISTAT |
| b = Π(T) | i vincoli pubblicati |
| p* | MaxEnt su X con E_p[f] = b (ciò che `gsp` fitta) |
| S | campione d'indagine estratto da T (nuclei interi), frazione φ |
| h : popolazione → ℝ^{aree} | una domanda della batteria Q, valutata per area |
| R | ricostruttore: (Π(T), S) ↦ popolazione sintetica P̂ |

Errore di un ricostruttore R sulla domanda h: `err_h(R) = h(P̂_R) − h(T)`,
per area e in totale.

---

## 2. La teoria che rende l'esperimento predittivo

### 2.1 Identità pitagorica

Se T (come distribuzione empirica su X) soddisfa gli stessi vincoli di p*,
cioè E_T[f] = b, e il supporto di T è contenuto in quello di p* (nessuna
massa su celle escluse con α=0), allora

```
KL(T ‖ p*) = H(p*) − H(T)
```

con le entropie calcolate sulla stessa misura di base (conteggio sul
supporto ammesso). L'errore di Animarium sulla congiunta è esattamente il
**gap di entropia**: l'informazione che T contiene oltre ai vincoli.

> Se T mette massa su una cella che p* esclude (α=0), KL è infinito.
> Prima di ogni calcolo: **contare la massa di T sulle celle escluse** e
> riportarla. Sui dati INSEE può succedere (le esclusioni sono pensate per
> le categorie ISTAT).

### 2.2 Errore previsto per domanda

Per una domanda lineare h (media di una funzione individuale):

```
E_T[h] − E_p*[h] = E_T[h_⊥] − E_p*[h_⊥]
```

dove h_⊥ è il residuo di h dopo la proiezione L²(p*) sullo span di
{1, f}. **Se h sta nello span dei vincoli, l'errore è zero** (a meno del
rumore di campionamento). Diagnostico da calcolare per ogni domanda:

```
ρ_h = ‖h_⊥‖_{p*} / ‖h − E_p* h‖_{p*}      ∈ [0, 1]
```

ρ_h è il **contenuto fuori vincolo** della domanda. Ipotesi H2 (§9):
l'errore di Animarium cresce con ρ_h.

### 2.3 Livello 1: previsione al primo ordine

Nel livello 1 (§4) la verità è una famiglia esponenziale inclinata
p_θ ∝ exp(λ(θ)·f + θ g), con λ(θ) rifittato in modo che E[f] = b per ogni
θ. Allora p_0 = p* e:

```
d/dθ E_θ[h] |_{θ=0} = Cov_p*(h_⊥, g_⊥)        (covarianza parziale)
KL(p_θ ‖ p*) = H(p*) − H(p_θ) ≈ ½ θ² Var_p*(g_⊥)
```

Quindi l'errore di Animarium sulla domanda h, al primo ordine, è
`θ · Cov_p*(h_⊥, g_⊥)`: **calcolabile prima di generare qualsiasi cosa**.
Il confronto previsione/misura è una figura del paper.

Nota per l'implementazione: Cov(h_⊥, g_⊥) = Cov(h,g) − Cov(h,f) Cov(f,f)⁺
Cov(f,g), con la pseudo-inversa perché le feature dei blocchi sono
collineari (i blocchi condividono i margini). Calcolo esatto su X
enumerato.

### 2.4 Perché MaxEnt e IPF sono parenti stretti

IPF con seme q calcola la I-proiezione `argmin KL(p ‖ q)` sotto E_p[f] = b.
**MaxEnt è IPF con seme uniforme.** Quindi la differenza fra Animarium e
IPF a seme sta tutta nella *prior*: il confronto R1 vs R2 misura quanto
vale l'informazione d'interazione contenuta nel seme. Va detto così nel
paper.

---

## 3. Livello 0 — verità = popolazione GSP (pavimento di rumore)

### 3.1 Disegno

1. Scegliere un comune ER dove il solver esatto gira comodamente
   **[VERIFICA NEL REPO: dimensione di |X| e tempi del solver esatto;
   candidati Modena, Parma]**.
2. T = popolazione `gsp` di quel comune al seme s₀ (si può usare quella di
   `release-v2.0`, **in sola lettura**).
3. b = Π(T): ricalcolare i vincoli **dalla popolazione T**, non usare i
   vincoli ISTAT originali (differiscono per il rumore di campionamento di
   T: z ≈ 0,2–0,6 misurato su Modena e Parma).
4. Ricostruire con R1 (Animarium, semi s₁…s_K), R0 (nullo), R2 (IPF con
   seme S ⊂ T), R3 (Fay–Herriot con S).

### 3.2 Cosa misura, e cosa NON misura

Misura:
- che il solver ritrovi i propri parametri (correttezza);
- lo **scaling dell'errore con N** (ripetere su comuni di taglia diversa);
- il **pavimento di rumore**: l'errore che Animarium ha anche quando la
  realtà è esattamente MaxEnt. Ai livelli 1 e 2, errore − pavimento =
  errore di modello.

NON misura quanto la realtà si discosta da MaxEnt: per costruzione
KL(T ‖ p*) ≈ 0. È un *inverse crime* (dati generati con lo stesso modello
che li inverte). Va dichiarato nel paper; il livello 0 è un controllo, non
un risultato.

### 3.3 Criteri di accettazione

- vincoli di T riprodotti da R1 con z per cella compatibili con N(0,1);
- errore di R1 sulle domande di ordine ≥1 compatibile con il solo rumore
  multinomiale (|z| medio ≈ √(2/π) ≈ 0,8);
- R2 con seme S ⊂ T **non** deve battere R1 in modo significativo
  (entrambi stimano la stessa distribuzione): se lo batte, c'è un errore.

---

## 4. Livello 1 — verità GSP con struttura piantata (θ controllato)

### 4.1 Idea

Si inclina la popolazione MaxEnt lungo una feature g **fuori dal constraint
set**, con intensità θ regolabile, **tenendo fissi i vincoli**. Così
Π(T_θ) = b per ogni θ (a meno del rumore), la ricostruzione di Animarium è
la stessa per ogni θ, e si muove solo la verità. Si ottengono curve di
errore in funzione di θ, e quindi del gap KL.

### 4.2 Tre varianti, una per anello

**1a — inclinazione degli attributi (anello 1).**
Fit MaxEnt con feature {f, g}, vincoli E[f] = b e E[g] = τ, con τ che varia
da E_p*[g] (θ = 0) verso valori più alti/bassi. Equivale a variare θ. Su X
enumerato non serve MCMC: si calcolano i pesi esatti
`w(x) ∝ exp(λ·f(x) + θ g(x))` e si campiona multinomialmente. Gibbs/PCD
solo se |X| non è enumerabile.

Candidati per g (scegliere quelli con ‖g_⊥‖ grande e interpretabili —
**calcolarlo, non presumerlo**; se ‖g_⊥‖ ≈ 0, g è già implicato dai
vincoli e va scartata):
- interazione a tre vie `cittadinanza × istruzione × condizione`
  (es. stranieri laureati in cerca di occupazione);
- `stato_civile × istruzione` (le persone più istruite si sposano più tardi);
- `background × condizione` per età fine.

**[VERIFICA NEL REPO]**: l'elenco esatto dei blocchi del constraint set,
per stabilire quali interazioni sono già vincolate.

**1b — inclinazione dei nuclei (anello 4).**
Nell'appaiamento dei partner si aggiunge un peso `exp(θ · 1[istruzione_R
== istruzione_P])` (omogamia educativa), a parità di vincoli di ampiezza
per sezione. Animarium (anello 4 standard, θ = 0) non la vede. È il test
naturale delle domande di nucleo (ordine 3).

**1c — inclinazione spaziale (anello 3).**
Nella collocazione degli individui nelle sezioni, probabilità
`∝ exp(θ · s_sez · 1[istruzione ∈ {laurea_o_its, post_laurea}])`, con s_sez
un punteggio di sezione fisso (es. distanza dal centro standardizzata),
**a parità di totali per sezione e dei vincoli di zona**. Simula la
segregazione residenziale sotto la scala di zona, che l'assunzione (8)
(`sezione ⊥ istruzione | zona, …`) ignora. È il test della parte spaziale e
delle decisioni (ordine 4).

### 4.3 Griglia

θ su ~8 valori, da 0 al valore per cui KL(T_θ ‖ p*) per individuo
raggiunge l'ordine di grandezza stimato sui dati INSEE (livello 2). Il
livello 2 dice dove cade la realtà sulla curva del livello 1: conviene
quindi fare il livello 2 almeno fino alla stima del gap prima di fissare la
griglia finale.

### 4.4 Criteri di accettazione

- per θ = 0 i risultati coincidono con il livello 0;
- `KL(T_θ ‖ p*)` misurato = `H(p*) − H(T_θ)` entro l'errore numerico
  (controllo dell'identità pitagorica);
- errore di R1 su ogni domanda lineare ≈ `θ · Cov(h_⊥, g_⊥)` per θ piccolo
  (pendenza della retta entro gli errori);
- la variante 1b non deve alterare la distribuzione dell'ampiezza dei
  nuclei per sezione; la 1c non deve alterare i totali per sezione.

---

## 5. Livello 2 — verità reale: censimento francese INSEE

### 5.1 La fonte

INSEE, *Recensement de la population 2021 — fichier détail INDCVI*
(individus localisés au canton-ou-ville), aggiornato il 16/12/2025.
92 variabili, 17.427.687 record. Pagina:
https://www.insee.fr/fr/statistiques/8268848

- zona D (Nouvelle-Aquitaine, Occitanie): `RP2021_indcvizd.zip`;
- dizionario delle modalità: `varmod_indcvi_2021.csv`;
- elenco variabili: `contenu_RP2021_indcvi.pdf`.

Il download da insee.fr va fatto **sulla macchina di Mirko** (dal workspace
cloud il dominio è bloccato). Il ritaglio si fa con lo script
`estrai_insee_comune.py`, già scritto: legge lo zip senza scompattarlo e
tiene un comune (default Tolosa, 31555) o un dipartimento, e circa 50
colonne:

```
python estrai_insee_comune.py RP2021_indcvizd.zip                  # Tolosa
python estrai_insee_comune.py RP2021_indcvizd.zip --comune 33063   # Bordeaux
python estrai_insee_comune.py RP2021_indcvizd.zip --dept 31        # Haute-Garonne
```

Città: **Tolosa = verità**, **Bordeaux = città donatrice** del seme per la
variante «indagine da un'altra città» (§7.3).

### 5.2 Natura del dato — tre fatti da non dimenticare

1. **Non è un censimento completo.** Deriva dall'exploitation
   complémentaire del censimento rotativo: ogni record ha un peso `IPONDI`
   (fino a 15 decimali; tenerli tutti).
2. **IRIS mascherato** (codice tipo `ZZZZZZZZZ`) per gli IRIS sotto i 200
   abitanti. A Tolosa non dovrebbe succedere; nei comuni rurali sì.
3. `NUMMI` identifica il ménage **solo dentro `CANTVILLE`**: la chiave del
   nucleo è `CANTVILLE + "_" + NUMMI`.

### 5.3 Costruzione della pseudo-popolazione T

Per definizione, **la verità del gemello è la pseudo-popolazione**, non la
Francia.

1. Verificare che `IPONDI` sia costante dentro il ménage (lo script lo
   stampa). Se non lo è, usare il peso della persona di riferimento
   (`LPRM == "1"`) per tutto il nucleo e riportare quanti nuclei sono
   interessati.
2. Arrotondamento controllato a livello di nucleo: ogni ménage con peso w
   è replicato `floor(w) + Bernoulli(w − floor(w))` volte, con seme fisso.
   Si replicano **nuclei interi**, mai individui.
3. Nuovi identificativi: `uid` individuale, `id_nucleo` univoco per replica.
4. Individui fuori ménage ordinario (`LPRM == "Z"`, convivenze): stessa
   regola, `id_nucleo` vuoto — coerente con la convenzione di `gsp`
   (individui in convivenza senza nucleo).
5. Controllo: totale di T vs somma di `IPONDI` (scarto atteso ≈ √N).

**Rischio da dichiarare.** Con pesi tipici ~4–5, T contiene gruppi di
nuclei identici. Non tocca i conteggi aggregati, ma rende le congiunzioni
più «grumose» di una popolazione vera e gonfia leggermente le stime di
ρ_h. Va riportato nel paper; come sensibilità, ripetere con 2–3 semi di
arrotondamento.

### 5.4 Mappatura delle variabili su Animarium

**Geografia.** `zona` ← `TRIRIS` (raggruppamenti di IRIS; **[VERIFICA SUI
DATI]** che sia valorizzato per Tolosa, altrimenti raggruppare gli IRIS per
codice o usare i grands quartiers); `sezione` ← `IRIS` (~2.000 abitanti,
più grande della sezione ISTAT: ok, è la scala fine disponibile).

| Animarium | INSEE | regola | stato |
|---|---|---|---|
| `sesso` | `SEXE` | 1→M, 2→F | 1:1 |
| `eta` | `AGEREV` (anno singolo) | bin `0-8, 9-14, 15-24, 25-34, 35-49, 50-64, 65-74, 75+`; tenere anche l'anno singolo | 1:1 |
| `stato_civile` | `STAT_CONJ` (+ `COUPLE`) | **[VERIFICA in varmod]** le modalità; PACS → `coniugato_unito` | da decidere |
| `cittadinanza` | `INATC` | 1→ITL (francese), 2→FRG | 1:1 |
| `background` | `IMMI` × `INATC` | non immigrato + francese → `italiano_nativo`; immigrato + francese → `naturalizzato_immigrato`; immigrato + straniero → `straniero_immigrato`; non immigrato + straniero → `straniero_g2` | **parziale**: `italiano_rientrato` e `naturalizzato_g2` non identificabili |
| `origine_genitori` | — | assente | **escludere** dallo spazio X al livello 2 |
| `istruzione` | `DIPL` | 01→nessun_titolo; 02, 11→elementare; 03, 12→media; 13, 14, 15→diploma; 16, 17→laurea_o_its; 18, 19→post_laurea; ZZ→vedi sotto | decisioni marcate sotto |
| `condizione` | `TACT` | 11→occupato; 12→in_cerca; 21→percettore_pensioni; 22→studente; 24→casalinga; 25→altra_condizione; 23→non_applicabile | **soglia 14 anni (INSEE) vs 15 (ISTAT)** |
| ruolo nel nucleo | `LPRM` | 1→R; 2→P; 3→F; 5→G; 4, 6→A; 7, 8, 9→N; Z→convivenza | 1:1 |
| ampiezza nucleo | `NPERR` | come `PF3–PF8` (6+ classe aperta) | 1:1 |
| occupazione (strato futuro) | `CS1`, `NA5`/`NA17`, `EMPL`, `STATR`, `TP` | verità per l'anello settore × posizione | extra |
| variabili di esito | `VOIT`, `TRANS`, `ILT`, `STOCD`, `HLML`, `SURF`, `NBPI` | **mai** usate nei vincoli | extra |

Decisioni da registrare (Mirko le conferma prima del livello 2):
- `DIPL 03` («nessun diploma, scolarità fino alla fine del collège»):
  proposto `media`, per analogia con chi ha frequentato la scuola media;
  alternativa `elementare`.
- `DIPL 13` (CAP/BEP): proposto `diploma`, perché l'ISTAT accorpa la
  qualifica professionale al diploma nelle tavole censuarie.
- `DIPL ZZ` (sotto i 14 anni): mapparlo come `gsp` tratta gli under 9/14
  **[VERIFICA NEL REPO]**.
- Soglia 14/15 anni: al livello 2 usare **la soglia INSEE ovunque**
  (vincoli, esclusioni α=0, domande). Non mescolare.

Le esclusioni α=0 vanno **riscritte** per il livello 2 sulle categorie
mappate. Prima di fittare, contare la massa di T sulle celle escluse
(§2.1): deve essere zero, o le esclusioni sono sbagliate.

### 5.5 Adattatore verso `gsp`

`gsp` è costruito sulle fonti ISTAT (acquisizione SDMX, staffetta
`build_sezioni` + `build_constraints`). Per il livello 2 serve un
adattatore che **scriva i vincoli nello stesso formato** prodotto da
`build_constraints`, saltando l'acquisizione.

**[VERIFICA NEL REPO]**: formato e percorso dei file che `build_constraints`
produce e che il solver legge; come sono codificate le esclusioni α=0;
come l'anello 3 legge sezioni e indirizzi (per il livello 2 non ci sono
indirizzi: collocazione solo a livello IRIS, nessun civico).

Le popolazioni di `release-v2.0` **non si toccano**: tutto l'esperimento
scrive in una directory propria.

---

## 6. L'operatore di pubblicazione Π

Π deve imitare la **geometria** del constraint set ISTAT, non la sua
semantica francese: stessi blocchi, stesse scale geografiche, stessa
granularità delle classi. È ciò che rende il risultato trasferibile
all'Italia.

**Primo compito di Claude Code**: inventariare i blocchi del constraint set
di un comune reale della flotta (es. Bologna 037006) leggendo
`build_constraints` e i file prodotti **[VERIFICA NEL REPO]**, e scrivere
una tabella `blocco | variabili | scala geografica | classi`. Poi, per ogni
blocco, una funzione `pubblica_<blocco>(T) -> DataFrame` con lo stesso
schema. Dalla documentazione di progetto, i blocchi includono almeno:
- crosstab comunali o di zona: sesso × età × stato civile; età (4 classi) ×
  istruzione; età × condizione; cittadinanza × background;
- margini per sezione: popolazione, stranieri, struttura per età;
- ampiezza dei nuclei per sezione (`PF3`–`PF8`).

Distinguere «cella assente» (non vincolata) da «cella a zero» (vietata):
Π produce zeri espliciti solo dove la tavola ISTAT corrispondente li
produrrebbe.

### 6.1 Ablazione di Π

Livelli di informazione crescente:

| Π_k | contenuto |
|---|---|
| Π₀ | solo margini 1D comunali |
| Π₁ | + crosstab comunali/di zona |
| Π₂ | + margini 1D e 2D per sezione/IRIS |
| Π₃ | + ampiezza nuclei per sezione (abilita l'anello 4) |
| Π₄ | Π₃ + un blocco «ipotetico» che l'ISTAT non pubblica (es. istruzione × condizione per zona) |

Per ogni k: gap KL (stimato, §8.3) ed errore sulle domande. La **curva
errore–informazione** dice quale tabella vale di più; Π₄ quantifica il
valore di una tabella che l'ISTAT potrebbe pubblicare.

---

## 7. I ricostruttori e il budget d'informazione comune

### 7.1 Budget comune

Tutti i metodi ricevono **lo stesso budget**: Π(T) + un campione S di
nuclei interi estratto da T con frazione φ.

```
φ ∈ {0, 0,1%, 0,5%, 1%, 2%, 5%}
```

Disegno di S: campionamento di Bernoulli dei nuclei con probabilità φ,
peso di disegno 1/φ. (Variante più realistica, opzionale: stratificato per
IRIS con allocazione proporzionale.) Per ogni φ, B ≥ 20 repliche di S.

Con φ = 0 funziona solo Animarium: IPF non ha seme, Fay–Herriot non ha
stime dirette. Al crescere di φ i metodi a campione migliorano. La figura
centrale è il **punto d'incrocio φ\***, per domanda e per ordine.

### 7.2 I quattro ricostruttori

**R0 — nullo (indipendenza).** Per ogni area, prodotto dei margini 1D di
Π. Fissa la scala; non usa S.

**R1 — Animarium.** Pipeline `gsp` (solver esatto, anelli 1, 3, 4) su Π(T).
Ignora S. Variante **R1+hd**: usa S come pool di donatori hot-deck per le
variabili fuori vincolo (`VOIT`, `TRANS`, `HLML`…), condizionando su
`sesso × macroetà × istruzione4` con collasso gerarchico, **esattamente
come per l'AVQ**. È il confronto equo sulle variabili di esito.

**R2 — IPF a seme (microsimulazione spaziale classica).**
- *R2a, individui*: per ogni zona, IPF della tabella di contingenza sullo
  spazio X con prior = conteggi pesati di S (+ δ per le celle a zero del
  seme, δ ∈ {10⁻⁶, 10⁻³, 0,5} come analisi di sensibilità; le celle α=0
  restano a zero per tutti). Poi integerizzazione (TRS, *truncate,
  replicate, sample*) e collocazione nelle sezioni/IRIS con i margini di
  sezione.
- *R2b, nuclei*: per le domande di nucleo, riponderazione dei nuclei di S
  per area con calibrazione/raking a livello nucleo (vincoli individuali e
  di nucleo insieme: IPU di Ye et al. 2009, o raking di Deville–Särndal),
  poi integerizzazione. Questo dà a IPF una struttura familiare vera.

**R3 — Fay–Herriot (piccola area, livello di area).** Un modello **per ogni
domanda** h. Per area i:

```
stima diretta    y_i = Σ_{j∈S_i} d_j h_j / Σ_{j∈S_i} d_j       (Hájek)
modello          y_i = θ_i + e_i,   e_i ~ N(0, ψ_i)
                 θ_i = x_iᵀβ + u_i,  u_i ~ N(0, σ_u²)
EBLUP            θ̂_i = γ_i y_i + (1 − γ_i) x_iᵀβ̂,   γ_i = σ_u² / (σ_u² + ψ_i)
```

- x_i: covariate di area da Π(T) a livello IRIS (quote per età, stranieri,
  ampiezza media dei nuclei, quote di zona dei crosstab). Stessa lista per
  tutte le domande, fissata prima di guardare i risultati.
- ψ_i: con campioni minuscoli la varianza diretta è instabile o nulla. Usare
  l'approssimazione binomiale con proporzione pooled,
  `ψ_i = θ̄(1 − θ̄)/n_i^eff` (n_i^eff in nuclei, perché il campione è a
  grappoli), o una funzione di varianza generalizzata.
- Stima di σ_u² per **REML** (da implementare, ~60 righe con
  `scipy.optimize`): con V = diag(σ_u² + ψ_i),
  `ℓ_R = −½[log|V| + log|XᵀV⁻¹X| + yᵀ P y]`,
  `P = V⁻¹ − V⁻¹X(XᵀV⁻¹X)⁻¹XᵀV⁻¹`, `β̂ = (XᵀV⁻¹X)⁻¹XᵀV⁻¹y`; σ_u² ≥ 0.
- Aree con n_i = 0: stima sintetica x_iᵀβ̂. Troncare θ̂_i in [0, 1].
  Conteggi stimati: `N_i θ̂_i` con N_i noto da Π.
- Opzionale: trasformazione arcoseno per le proporzioni; MSE di
  Prasad–Rao come incertezza.

**Cosa R3 non può fare, e va detto**: risponde solo alle domande per cui è
stato stimato, non produce una popolazione e non garantisce coerenza fra
domande (le stime di h₁ e h₂ possono essere tra loro incompatibili). Per
misurarlo: verificare su una coppia di domande annidate (es. «over 75
soli» ⊂ «over 75») quante aree violano h₁ ≤ h₂.

### 7.3 Variante «indagine da un'altra città»

S estratto da una città diversa: Bordeaux al livello 2; un altro comune ER
ai livelli 0 e 1. È il caso italiano tipico, in cui l'indagine non copre il
comune d'interesse. R2 usa S come seme, R3 stima β su Bordeaux, dove la
verità è nota, e lo applica a Tolosa (solo parte sintetica, γ_i = 0).

---

## 8. La batteria di domande Q e le metriche

### 8.1 Domande

Ogni domanda è una funzione `h(pop) -> Series` indicizzata per area
(IRIS/sezione), più il totale comunale. Tutte definite sulle categorie
Animarium mappate (§5.4), in un unico modulo `domande.py`.

| ordine | id | definizione | note |
|---|---|---|---|
| 0 | q00 | margini vincolati di Π | controllo: errore ≈ 0 |
| 1 | q11 | quota `istruzione ∈ {laurea_o_its, post_laurea}` per area, 25–64 anni | interazione area × istruzione |
| 1 | q12 | `istruzione × condizione` per bin d'età (tabella comunale) | non vincolata |
| 1 | q13 | quota occupati per area, 25–64 | |
| 2 | q21 | over 75 che vivono soli | età × ampiezza nucleo |
| 2 | q22 | stranieri, istruzione ≤ media, in cerca di occupazione | congiunzione a 3 |
| 2 | q23 | donne 25–49 laureate occupate | congiunzione a 4 |
| 3 | q31 | nuclei con figlio < 3 anni e due genitori occupati | funzionale di nucleo |
| 3 | q32 | monoparentali con capofamiglia in cerca di occupazione | |
| 3 | q33 | nuclei con almeno un over 80 e nessun membro 18–64 | rischio isolamento |
| 3 | q34 | coppie entrambe laureate (omogamia) | test diretto di 1b |
| 4 | q41 | scegliere k aree che massimizzano i membri del gruppo q21 | decisione |
| 4 | q42 | idem per q31 (servizi per la prima infanzia) | decisione |
| fuori | q51 | over 75 soli **senza auto** (`VOIT = 0`) | solo livello 2 |
| fuori | q52 | occupati che vanno al lavoro in auto, per area | solo livello 2 |
| fuori | q53 | nuclei in HLM con almeno un disoccupato | solo livello 2 |

Le domande «fuori» si valutano solo per R1+hd, R2 e R3 (R1 puro non ha
quelle variabili e lo dichiara).

### 8.2 Metriche

- **Per conteggi per area**: errore relativo pesato per popolazione, bias
  medio e soprattutto
  `z_i = (ĥ_i − h_i) / √(N_i α_i (1 − α_i))`, con α_i la quota vera. Riportare
  |z| medio e la quota di aree con |z| > 2. **Mai** classificare le aree
  per errore relativo grezzo (premia le celle piccole).
- **Per le decisioni** (k ∈ {5, 10, 20}):
  - regret: `[h(top_k^vero) − h(top_k^stimato)] / h(top_k^vero)`, dove h è
    sempre valutato **sulla verità**;
  - Jaccard fra i top-k;
  - Spearman della graduatoria completa delle aree.
- **Sulla congiunta**: distanza di Hellinger e variazione totale sulle
  proiezioni a 2 e 3 vie.
- **Coerenza** (R3): quota di aree che violano i vincoli d'ordine fra
  domande annidate.
- **Incertezza**: per R1 e R2, K ≥ 20 semi di generazione; per R2 e R3, B ≥
  20 repliche di S. Riportare media ± deviazione standard; separare bias e
  varianza.

### 8.3 Stima del gap di entropia

- Livelli 0 e 1: esatto su X enumerato (per il livello 1, H(T_θ) è
  calcolabile dalla distribuzione esatta prima del campionamento; sul
  campione, plug-in con correzione).
- Livello 2: la stima plug-in di H(T) sulla congiunta completa è
  **distorta** (supporto 10⁵–10⁶ celle contro ~5·10⁵ individui). Usare la
  decomposizione per proiezioni di ordine basso (informazione mutua
  condizionata dei termini non vincolati) o uno stimatore con correzione
  del bias (Miller–Madow, NSB). Riportare la stima con intervallo
  bootstrap sui nuclei.
- Per ogni domanda: ρ_h (§2.2), calcolato su p*.

---

## 9. Ipotesi, scritte prima di vedere i risultati

| id | ipotesi | come si falsifica |
|---|---|---|
| H1 | R1 batte nettamente R0 su tutte le domande di ordine 1–3 | R1 non migliore di R0 su ≥ 1 ordine |
| H2 | l'errore di R1 cresce con ρ_h; al livello 1 segue θ·Cov(h_⊥, g_⊥) | correlazione di rango errore/ρ_h non significativa; pendenza fuori dagli errori |
| H3 | con S dalla stessa città, R2 batte R1 sulle interazioni non vincolate da un certo φ in poi; il prezzo dell'essere sample-free a φ = 0 è misurabile | R1 ≥ R2 per ogni φ (improbabile), oppure R2 ≫ R1 già con φ = 0,1% |
| H4 | R3 è competitivo o migliore su conteggi per area lisci (ordine 1), peggiore sui funzionali di nucleo e sulle decisioni; il φ\* d'incrocio cresce con l'ordine | φ\* indipendente dall'ordine |
| H5 | R1 sottostima la concentrazione spaziale (1c e livello 2): graduatoria delle aree buona (Spearman alto), magnitudini compresse | Spearman basso, oppure magnitudini corrette |
| H6 | con S da un'altra città (§7.3) il vantaggio di R2/R3 si riduce o si inverte | vantaggio invariato |

Il risultato atteso **non** è che Animarium vinca ovunque: è la mappa di
dove vince, dove perde e di quanto, con l'errore previsto da ρ_h.

---

## 10. Struttura del codice

Progetto separato, sul modello di `~/progetti/osrm` e `~/progetti/r5`:
**`~/progetti/gemello`**, con `gsp` installato in modalità editabile come
dipendenza. Niente dati binari nel repo `gsp`; nessuna scrittura nelle
popolazioni di `release-v2.0`.

```
gemello/
  config/
    livello0.yaml  livello1.yaml  livello2.yaml   # comune, semi, griglie θ e φ, K, B
    mappa_insee.yaml                              # §5.4 come dati, non come codice
  gemello/
    insee.py          # lettura del CSV ritagliato, dtype=str, controlli §5.2
    pseudo_pop.py     # §5.3, replica dei nuclei, semi
    pubblica.py       # Π e i livelli d'ablazione Π_k (§6)
    adattatore_gsp.py # scrive i vincoli nel formato di build_constraints (§5.5)
    inclina.py        # livello 1: 1a, 1b, 1c (§4)
    campione.py       # S: Bernoulli/stratificato, altra città (§7)
    ricostruttori/
      nullo.py  animarium.py  ipf.py  fay_herriot.py
    domande.py        # la batteria Q (§8.1)
    metriche.py       # z, regret, Jaccard, Spearman, Hellinger, coerenza
    teoria.py         # h_⊥, ρ_h, Cov parziali, KL, stime di entropia (§2, §8.3)
  script/
    estrai_insee_comune.py
    run_livello0.py  run_livello1.py  run_livello2.py
  risultati/          # parquet per corsa + manifest JSON (config, semi, hash git di gsp)
  figure/
```

Ogni corsa scrive un manifest con: config completa, semi, hash git di
`gsp` e `gemello`, versione dei dati, tempi. Determinismo: stessa config →
stessi numeri.

---

## 11. Ordine di lavoro, con criteri di accettazione

1. **Inventario dei vincoli.** Leggere `build_constraints` e i file di un
   comune della flotta; produrre la tabella dei blocchi (§6).
   *Accettazione*: Mirko conferma la tabella.
2. **Π su popolazione GSP.** Implementare `pubblica.py` e applicarlo a una
   popolazione `release-v2.0`. *Accettazione*: Π(T) ≈ vincoli ISTAT
   originali con z per cella compatibili con il rumore.
3. **Teoria su X.** `teoria.py`: enumerazione di X, proiezione su span(f),
   ρ_h per le domande lineari. *Accettazione*: ρ_h ≈ 0 per le domande
   nello span (controllo positivo) e > 0 per le altre.
4. **Livello 0** con R0 e R1. *Accettazione*: §3.3.
5. **Campione S, R2 e R3.** *Accettazione*: al livello 0, R2 con S ⊂ T non
   batte R1 in modo significativo; R3 con φ = 5% recupera le quote per area
   entro il suo MSE nominale.
6. **Livello 1**, prima 1a, poi 1b e 1c. *Accettazione*: §4.4.
7. **Dati INSEE**: ritaglio (sulla macchina di Mirko), pseudo-popolazione,
   mappatura. *Accettazione*: controlli §5.3 e massa nulla su α=0.
8. **Adattatore e livello 2.** *Accettazione*: `gsp` gira su Π(T_Tolosa) e
   riproduce i vincoli come sui comuni italiani.
9. **Ablazione Π₀…Π₄ e figure.**

Dopo ogni passo: breve nota di stato (`note/gemello_stato_vN.md`) con
numeri, decisioni e cosa resta aperto. Modifiche chirurgiche, nessun
refactoring di `gsp` non richiesto.

---

## 12. Trappole note

- **Codici come stringhe.** `IRIS`, `TRIRIS`, `CANTVILLE`, `DEPT`, `NUMMI`
  vanno letti con `dtype=str`: zeri iniziali, e la Corsica usa `2A`/`2B`.
  È lo stesso errore di `REF_AREA` in `gsp.istat.sdmx`.
- **Chiave del nucleo** = `CANTVILLE + NUMMI`, non `NUMMI` da solo.
- **Pesi**: `IPONDI` a piena precisione; arrotondamento solo nella replica
  controllata dei nuclei.
- **Soglia d'età** 14 (INSEE) vs 15 (ISTAT): una sola per livello, ovunque.
- **Esclusioni α=0**: identiche per tutti i ricostruttori; al livello 2
  riscritte sulle categorie mappate; massa di T su celle escluse = 0
  verificata.
- **Cella assente ≠ cella a zero** in Π (§6).
- **Celle a zero nel seme IPF**: un seme piccolo azzera combinazioni reali;
  sensibilità su δ obbligatoria (§7.2).
- **Inverse crime** al livello 0: non presentarlo come risultato.
- **Rumore di T al livello 0**: i vincoli si ricalcolano da T, non si
  prendono dall'ISTAT.
- **Grumi della pseudo-popolazione** (§5.3): dichiararli, sensibilità sui
  semi di replica.
- **Errore relativo** su celle piccole: usare z (§8.2).
- **Fay–Herriot con ψ_i instabili**: varianza lisciata, non quella diretta.
- **Leakage**: le covariate di R3 e la lista delle domande si fissano
  **prima** di guardare gli errori; le variabili di esito non entrano mai
  in Π.

---

## 13. Decisioni aperte per Mirko

1. Comune ER per i livelli 0–1 (dimensione di |X| compatibile con
   l'enumerazione esatta).
2. Mappature `DIPL 03`, `DIPL 13`, `DIPL ZZ`, `STAT_CONJ` (§5.4).
3. Mappatura della zona al livello 2: `TRIRIS` o grands quartiers.
4. Feature g del livello 1a (dopo aver visto i ‖g_⊥‖).
5. Se includere la variante stratificata di S e la variante unit-level di
   R3 (Battese–Harter–Fuller) o tenerle come lavoro futuro.

---

## Riferimenti

- INSEE, *Individus localisés au canton-ou-ville en 2021 — fichiers
  détail*: https://www.insee.fr/fr/statistiques/8268848
- INSEE, documentazione INDCVI: https://www.insee.fr/fr/information/2383284
- Fay, R. E., Herriot, R. A. (1979). Estimates of income for small places:
  an application of James–Stein procedures to census data. *JASA* 74.
- Battese, G. E., Harter, R. M., Fuller, W. A. (1988). An error-components
  model for prediction of county crop areas using survey and satellite
  data. *JASA* 83.
- Rao, J. N. K., Molina, I. (2015). *Small Area Estimation*, 2ª ed., Wiley.
- Prasad, N. G. N., Rao, J. N. K. (1990). The estimation of the mean
  squared error of small-area estimators. *JASA* 85.
- Deville, J.-C., Särndal, C.-E. (1992). Calibration estimators in survey
  sampling. *JASA* 87.
- Ye, X., Konduri, K., Pendyala, R. M., Sana, B., Waddell, P. (2009). A
  methodology to match distributions of both household and person
  attributes in the generation of synthetic populations. TRB Annual
  Meeting.
- Lovelace, R., Dumont, M. (2016). *Spatial Microsimulation with R*. CRC
  (IPF, TRS).
- Csiszár, I. (1975). I-divergence geometry of probability distributions
  and minimization problems. *Annals of Probability* 3 (identità
  pitagorica, I-proiezione).
