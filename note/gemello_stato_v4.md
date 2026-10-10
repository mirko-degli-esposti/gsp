# Gemello identico: stato dopo il passo 4 (livello 0 con R0 e R1)

*v4, 10/10/2026. **Sostituisce `gemello_stato_v3.md`** (ora in `storico/`).
Rispetto alla v3, aggiunge:*
- *le decisioni di Mirko su `fit_cs` e sulle feature g;*
- *l'estensione della batteria Q allo stato civile;*
- *Π per gli anelli 3–4;*
- *il passo 4, cioè il livello 0 con R0 e R1 su 20 semi;*
- *una correzione al criterio d'accettazione del §3.3 di `nota_gemello_v1`;*
- *un'assunzione implicita di `fit_cs` resa esplicita.*

*I contenuti della v3 (passo 3: teoria su X, identità pitagorica, ρ_h)
restano validi e sono in `storico/gemello_stato_v3.md`. Qui sono riassunti
al §1.*

*Etichette: **misurato** = c'è un log; **dichiarato** = viene dal codice o
da una fonte; **aperto** = non deciso o non misurato.*

---

## 0. Commit di riferimento

| repo | commit | contenuto |
|---|---|---|
| gsp | `afe1aba` | `GSP_COMUNI_DIR` |
| gsp | `6224a94` | enrich (3d): età singola ripartita sul comune |
| gsp | `b804aca` | `assign_nucleo` rispetta `GSP_COMUNI_DIR` |
| gsp | `99abb4d` | `fit_cs`: errore se il fit esatto non converge (MRE > 1%) |
| gsp | `dbc06a8` | `GSP_SUBMUN_DIR` (tavole di sezione spostabili) |
| gemello | `532f99a` | Π_blocchi, `teoria.py`, passo 3 |
| gemello | `5870470` | batteria estesa: q14, q15, g4 |
| gemello | `0d6ba7e` | passo 4: domande, metriche, R0/R1, Π anelli 3–4 |

I risultati del passo 4 sono stati prodotti dal codice di `0d6ba7e` con gsp
`dbc06a8` (`risultati/passo4/036023/manifest.json`).

## 1. Riassunto della v3

- **Teoria su X (Modena).** L'identità pitagorica è verificata: con
  Π_blocchi, KL(T‖p\*) = 0,06406 contro H(p\*) − H(T) = 0,0639.
- **Livello 0.** È indistinguibile dal rumore: un campione da p\* ha lo
  stesso KL.
- **ρ_h.** Vale circa 0 per i controlli e per q13; 0,34 per q11 e q23; 0,70
  per q22; mediana 0,75 per q12.
- **Incoerenza di Π_grezzo corretta.** Le coniugate di 15 anni e i totali di
  c1 diversi da quelli di c2 rendevano infeasibile il constraint set; ora
  Π le pubblica come celle extra.

## 2. Decisioni del 10/10/2026 (Mirko)

1. **Controllo di convergenza in `fit_cs`: fatto** (`99abb4d`). Verifica in
   scratchpad:
   - sul cs di produzione di Modena la popolazione è byte-identica a HEAD e
     alla produzione;
   - su un cs reso infeasibile (una cella di Z1 × 1,5), HEAD scriveva una
     popolazione con MRE 7,37 e supporto 1; ora l'esecuzione si ferma con
     codice 1 senza scrivere nulla.

   Nessuno dei 259 fit di produzione supera la soglia (massimo 1,0e-3).
2. **Livello 1a:**
   - **g1** (stranieri laureati in cerca) è la variante principale;
   - **g2** (coniugati laureati) resta come caso «invisibile alla batteria
     lineare»;
   - si aggiunge una variante sullo stato civile, con una domanda adatta.

   Il nome «g3» era già preso dalle seconde generazioni (v3), quindi la
   nuova variante si chiama **g4** = donne coniugate/unite occupate. È la
   penalità occupazionale delle donne sposate: interpretabile e classica.
3. **Nuove domande q14 e q15**, aggiunte il 10/10/2026 **prima di
   qualunque misura d'errore ai livelli 1–2** (§12 della nota, leakage):
   - q14 = donne 25–49 coniugate/unite occupate, per area (conciliazione
     lavoro-famiglia);
   - q15 = vedovi/e 75+, per area (isolamento, complemento di q21).

**Visibilità delle g** (*misurato*, p\* di Π_blocchi;
`risultati/passo3/036023/`):

| g | ‖g_⊥‖ | massima corr. parziale con la batteria | lettura |
|---|---|---|---|
| g1 | 0,034 | 0,24 (q12 post-laurea in cerca, q22) | visibile |
| g2 | 0,178 | 0,013 | invisibile alle domande lineari, anche a q14 e q15 |
| g4 | 0,116 | 0,048 (q14 per zona) | visibile, debole |

**g2 non è invisibile a tutta Q** (*aperto*). La teoria lineare su X non
vede q34 («coppie entrambe laureate»), che è una domanda di nucleo
(anello 4). Un'inclinazione verso coniugati laureati dovrebbe aumentare le
coppie laureate. Il livello 1a dirà se un effetto invisibile al primo
ordine su X compare nei nuclei. Vale anche per g4 con q31 (nuclei con due
genitori occupati).

## 3. Π per gli anelli 3–4

R1 deve vedere solo Π(T) anche negli anelli 3–4. Per questo Π ricalcola da
T le tavole che enrich e assign_nucleo leggono:
- il file sezioni, con lo stesso tracciato: P1, quinquennali per sesso,
  ST1, ST16–ST21, ST25–ST30, PF1, PF3–PF8; le altre colonne di conteggio
  sono messe a NaN, così un uso non previsto fallisce;
- l'anagrafe per età singola.

Servono a gsp tramite `GSP_SUBMUN_DIR` (`dbc06a8`). Verifica: con il file
sezioni reale copiato altrove, enrich produce un output byte-identico alla
verità T.

**Eccezione dichiarata:** la tavola dei paesi di cittadinanza è copiata
dalla fonte reale. Serve solo ad area e paese di enrich, che nessuna
domanda usa.

Confronto con le tavole ISTAT di sezione (*misurato*,
`risultati/passo2/036023/z_sezioni.csv`): |z| medio per colonna da 0,02 a
0,29. Gli anelli 3–4 riproducono le tavole di sezione molto meglio del
rumore multinomiale, per costruzione (largest remainder).

## 4. Ricostruttori (*dichiarato*: `gemello/ricostruttori.py`)

- **R1.** p\* è il fit di produzione sul cs di Π_grezzo. Si estrae un
  campione multinomiale di taglia N con seme s (stessa procedura di
  `fit_cs`: con s = 42 riproduce byte per byte il campione di `fit_cs`),
  poi enrich (seme s) e assign_nucleo (seme s). L'anello 2 (AVQ) è
  saltato, perché nessuna domanda lo usa.
- **R0.** Ha come vincoli i margini 1D di Π (per zona: sesso, età,
  cittadinanza, istruzione, background; comunali: stato civile,
  condizione, origine) più tutte le celle α=0. Si fitta con **IPF su X
  ristretto al supporto ammesso**, non con `fit_cs` (vedi §5). Converge in
  54 iterazioni, con MRE massimo 9e-11. Poi gli stessi anelli 3–4 di R1.
- **Semi:** 1001–1020 per entrambi, diversi da quelli della verità (enrich
  42, nucleo `SEME_BASE`).

## 5. Un'assunzione implicita di `fit_cs` (*dichiarato*)

`fit_cs` (con eps > 0) esclude dal fit esatto i vincoli α=0 e **dopo** il
fit azzera le celle che coprono, poi rinormalizza. Questo dà il MaxEnt con
gli zeri solo se gli altri vincoli assegnano già massa (quasi) nulla a
quelle celle.

In produzione la condizione vale, perché i blocchi C, D e S legano età,
istruzione e condizione: MRE ≤ 1e-3 su tutta la flotta. Con i soli margini
1D (R0) non vale. Le celle escluse, come «0–8 anni occupati», hanno molta
massa; l'azzeramento rompe i margini (MRE 0,24), e il controllo di
convergenza ferma l'esecuzione.

Nessuna azione su gsp, ma l'assunzione va tenuta presente per qualunque
constraint set ridotto (ablazione Π₀ del §6.1 della nota).

## 6. Passo 4: risultati su Modena (K = 20 semi)

*Misurato*: `gemello/risultati/passo4/036023/`, cioè `metriche.csv`,
`decisioni.csv`, `proiezioni.csv`, `bias_varianza.csv`. Comando: `python
script/passo4_livello0.py config/livello0.yaml --paralleli 6`. Tempo: 271
s. Numeri medi sui 20 semi.

**Il pavimento di rumore è |z| ≈ 1,13, non 0,8** (*dichiarato*, e
confermato dai dati). Al livello 0 sia T sia ogni replica di R1 sono
estrazioni indipendenti dallo stesso processo. Lo z di metriche.py usa la
sd binomiale di una sola estrazione, quindi lo scarto fra due estrazioni ha
sd √2 volte più grande e |z| medio atteso √2·√(2/π) ≈ 1,13.

*Correzione 10/10/2026 a `nota_gemello_v1` §3.3, che diceva «|z| medio ≈
√(2/π) ≈ 0,8»:* vale per uno scarto da valori attesi fissi. Fra due
popolazioni campionate il valore atteso è circa 1,13. La nota v1 resta
com'è; vale questa correzione.

**|z| medio per area, R0 contro R1:**

| domanda | ordine | sezione R0 | sezione R1 | zona R0 | zona R1 |
|---|---|---|---|---|---|
| q11 laureati 25–64 | 1 | 1,45 | 1,13 | 25,7 | 1,07 |
| q12 istr. × cond. (celle comunali) | 1 | 76,3 | 1,00 | — | — |
| q13 occupati 25–64 | 1 | 4,12 | 1,14 | 97,2 | **2,18** |
| q14 coniugate occupate | 1 | 1,33 | 1,13 | 19,4 | 1,12 |
| q15 vedovi 75+ | 1 | 2,06 | 1,11 | 47,0 | 1,26 |
| q21 over 75 soli | 2 | 1,19 | 1,17 | 8,19 | 1,37 |
| q22 stranieri ≤ media in cerca | 2 | 0,40 | 0,52 | 9,15 | 1,27 |
| q23 laureate occupate 25–49 | 2 | 1,75 | 1,16 | 36,8 | 1,36 |
| q31 figlio < 3, R e P occupati | 3 | 1,26 | 1,36 | 8,78 | 1,33 |
| q32 monoparentali R in cerca | 3 | 0,28 | 0,18 | 5,86 | 0,88 |
| q33 over 80 senza 18–64 | 3 | 1,51 | 1,47 | 2,52 | 1,34 |
| q34 coppie entrambe laureate | 3 | 0,84 | 0,87 | 3,63 | 1,30 |

**Come si leggono i risultati:**
- **Per zona** (4 aree da circa 46.000 abitanti) R1 sta sul pavimento,
  |z| da 0,9 a 1,4, su tutte le domande di ordine 1–3. R0 è lontano di 1–2
  ordini di grandezza. **H1 è confermata al livello 0, a scala di zona.**
- **L'eccezione è q13 per zona** (|z| 2,18, metà delle zone con |z| > 2).
  q13 è nello span (ρ ≈ 0, v3), quindi non è errore di modello: è l'errore
  di derivazione di `cs_build`, assunzione (3), cioè P(zona | sesso,
  occupato) costante sui bin d'età. Il passo 3 l'aveva previsto: |z_T| di
  q13 0,48 con Π_grezzo contro 0,03 con Π_blocchi.
- **Per sezione** (2.186 sezioni, 84 abitanti in media) le domande di
  ordine 1 danno R1 ≈ 1,13 = pavimento. R0 è peggiore dove la domanda
  dipende dall'età o dalla condizione (q13 4,1, q15 2,1, q23 1,75).
- **Sulle domande rare per sezione** (q22, q31, q32, q34: da 0,05 a 1,3
  unità per sezione) R0 e R1 sono indistinguibili, e R0 ha a volte |z|
  più basso. Su eventi così rari lo z per sezione misura rumore di
  Poisson, non il ricostruttore. Gli errori relativi pesati lo confermano:
  q22 0,94 contro 0,98, q31 0,91 contro 0,98. Qui **H1 non è decidibile
  alla scala di sezione** (vedi §7.1).
- **Domande di nucleo per sezione:** R1 sta sopra il pavimento (q31 1,36,
  q33 1,47), e così R0. È coerente con una sovradispersione dei conteggi
  di nucleo rispetto alla sd binomiale, perché l'anello 4 lavora sezione
  per sezione. Va misurata direttamente (*aperto*).

**Totale comunale** (z_totale, media ± sd sui 20 semi): R1 da −0,98 a
+1,47 con sd ≈ 1 su tutte le domande. È coerente con il rumore: lo scarto
fisso di T, una sola estrazione, sposta la media di una quantità ~N(0,1).
R0 va da −197 (q13) a +12 (q32).

**Scomposizione bias/varianza per zona** (quota del bias su MSE, *misurato*):
- R1: da 0,14 a 0,57. Per il solo rumore ci si attende circa 0,5, perché
  lo scarto fisso di T conta come bias.
- R0: da 0,85 a 1,00, cioè sistematico.

**Decisioni** (top-k sezioni, medie su 20 semi):

| decisione | k | regret R0 | regret R1 | Jaccard R0 | Jaccard R1 | Spearman R0 | Spearman R1 |
|---|---|---|---|---|---|---|---|
| q41 (q21, over 75 soli) | 5 | 0,19 | 0,07 | 0,38 | 0,63 | 0,79 | 0,82 |
| q41 | 10 | 0,17 | 0,07 | 0,32 | 0,50 | | |
| q41 | 20 | 0,13 | 0,08 | 0,38 | 0,41 | | |
| q42 (q31, prima infanzia) | 5 | 0,42 | 0,31 | 0,12 | 0,22 | 0,22 | 0,26 |
| q42 | 10 | 0,47 | 0,35 | 0,15 | 0,24 | | |
| q42 | 20 | 0,50 | 0,38 | 0,15 | 0,21 | | |

Su q41 R1 dimezza il regret. Su q42 entrambi sono poveri, perché per
sezione q31 vale circa 0,4 nuclei: la graduatoria è quasi rumore.

**Proiezioni** (TV fra popolazione ricostruita e T, individui):

| proiezione | R0 | R1 |
|---|---|---|
| età × istruzione × condizione | 0,396 | 0,011 |
| zona × stato civile × condizione | 0,223 | 0,009 |
| cittadinanza × istruzione × condizione | 0,155 | 0,007 |
| istruzione × condizione | 0,113 | 0,005 |
| sesso × età singola | 0,031 | 0,004 |

## 7. Decisioni per Mirko

1. **Scala d'area.** Le sezioni ISTAT di Modena (84 abitanti) sono troppo
   piccole per le domande rare e per le decisioni q42. I quartieri sono 4
   (circa 46.000 abitanti) e il file sezioni non ha livelli intermedi
   (COM_ASC2 e COM_ASC3 hanno un solo valore). Proposta: aggregare le
   sezioni in **aree di circa 2.000 abitanti**, contigue e dentro il
   quartiere, che è la taglia degli IRIS del livello 2. Servono le
   geometrie delle sezioni e una regola deterministica (ad es. crescita
   per contiguità ordinata per codice). Così livelli 0–1 e livello 2 hanno
   la stessa scala, e Fay–Herriot (R3) ha aree con campioni non nulli.
2. **Sovradispersione dei nuclei.** Per le domande di ordine 3, usare
   come scala dello z la varianza fra repliche di R1 (empirica) invece di
   quella binomiale? Proposta: riportarle entrambe.

## 8. Prossimi passi

1. Decidere la scala d'area (§7.1) e rivalutare il passo 4 (basta
   ricalcolare: le popolazioni sono in `lavoro_ric/`).
2. Passo 5: campione S, R2 (IPF a seme) e R3 (Fay–Herriot).
3. Livello 1a con g1, poi g2 e g4; pendenze previste contro misurate.

## 9. Aperto (cumulativo)

- Rigenerare gli anelli 3+4 della flotta con l'età corretta (release).
- Regole `IMPOSSIBILI` per background × origine, con refit.
- Età singola condizionata allo stato civile, e coniugati di 15 anni.
- Causa del disallineamento dei nuclei di produzione di Modena.
- Sovradispersione delle domande di nucleo (§6, §7.2).
- Scala d'area intermedia (§7.1).
