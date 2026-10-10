# Gemello identico: stato dopo il passo 3

*v3, 10/10/2026. **Sostituisce `gemello_stato_v2.md`** (ora in `storico/`).
Rispetto alla v2, aggiunge:*
- *Π_blocchi;*
- *il passo 3 (teoria su X: p\*, bilancio d'informazione, ρ_h, pendenze
  previste);*
- *un'incoerenza di Π_grezzo che rendeva infeasibile il constraint set, e la
  sua correzione;*
- *una correzione datata a un giudizio della v2 (§4);*
- *due decisioni per il livello 1a.*

*I contenuti della v2 (inventario dei vincoli, D1–D4, difetto dell'età
singola e sua correzione, passo 2) restano validi. Qui sono riassunti al §1;
il dettaglio è in `storico/gemello_stato_v2.md`.*

*Etichette: **misurato** = c'è un log; **dichiarato** = viene dal codice o
da una fonte; **aperto** = non deciso o non misurato.*

---

## 0. Commit di riferimento

| repo | commit | contenuto |
|---|---|---|
| gsp | `afe1aba` | `GSP_COMUNI_DIR`; `cs_build` usa `G.path_*` |
| gsp | `6224a94` | enrich (3d): età singola ripartita sul comune |
| gsp | `b804aca` | `assign_nucleo` rispetta `GSP_COMUNI_DIR` |
| gemello | `d34a1c5` | verità T del livello 0, passo 2 |
| gemello | `532f99a` | Π_blocchi, `teoria.py`, passo 3; c1 di Π reso coerente |

## 1. Riassunto della v2

- **Spazio e comune.** X di K9C ha 9 variabili; il comune di sviluppo è
  Modena 036023 (|X| = 645.120, fit esatto in circa 16–20 s).
- **Decisioni.** D1–D4 sono confermate. Le popolazioni esistenti non si
  toccano mai.
- **Verità T del livello 0.** Anelli 1+2 di produzione copiati, anelli 3+4
  rigenerati con l'enrich corretto, in `gemello/verita/`.
- **Passo 2.** Tutti i blocchi del constraint set derivati da Π_grezzo(T)
  sono compatibili con il rumore.
- **Difetto dell'età singola.** In enrich (3d) l'età singola era distorta
  (TV da 0,085 a 0,283 sulla flotta). È corretto in `6224a94`; la produzione
  ha ancora l'età vecchia.

## 2. Passo 3: la teoria su X (Modena)

**Implementazione** (*dichiarato*): `gemello/gemello/teoria.py`,
`script/passo3_teoria.py`.
- p\* si ricostruisce come in `fit_cs.main`, importandone le funzioni. I λ
  si riferiscono ai vincoli con α ≥ `min_alpha` = 2e-4, **senza** gli zeri.
  Le celle coperte da un vincolo α ≤ eps si azzerano dopo il fit.
- Le feature f della teoria sono quindi i vincoli effettivamente tenuti: 596
  su 669 celle del cs. Gli altri 73 sono zeri oppure stanno sotto
  `min_alpha`.
- La proiezione su span{1, f} si fa in L²(p\*) con la pseudo-inversa della
  Gram. Il rango effettivo è 400 su 597, perché i blocchi condividono i
  margini.

**Π_blocchi** (*misurato*): stessa geometria del cs di Π_grezzo, con α
esatti da T. La massa di T sulle 34 celle α=0 è **0**, quindi KL(T‖p\*) è
finito (§2.1 della nota).

**Bilancio d'informazione** (*misurato*:
`gemello/risultati/passo3/036023/bilancio.csv`; comando `python
script/passo3_teoria.py config/livello0.yaml`; gsp `b804aca`, gemello
`532f99a`). In nat; N = 184.597.

| Π | distribuzione | KL(·‖p\*) | H(p\*) − H(·) | scarto pitagorico | MRE momenti |
|---|---|---|---|---|---|
| blocchi | T | 0,06406 | 0,06390 | 1,6e-4 | 0,04% |
| blocchi | campione da p\* | 0,06526 | 0,06676 | −1,5e-3 | 2,4% |
| grezzo | T | 0,06459 | 0,06433 | 2,6e-4 | 1,1% |
| grezzo | campione da p\* | 0,06614 | 0,06858 | −2,4e-3 | 2,5% |

Come si legge la tabella:
- **Identità pitagorica** (*misurato*). Con Π_blocchi, E_T[f] = b per
  costruzione e KL = H(p\*) − H(T) a meno di 1,6e-4 nat. Lo scarto residuo
  è coerente con la tolleranza del solver (MRE dei momenti di p\*
  dell'ordine di 4e-4).
- **Livello 0 = rumore** (*misurato*). Un campione di taglia N tratto da
  p\* stesso (la `popolazione_K9C.csv` scritta dal fit) ha lo stesso KL di
  T, circa 0,065 nat. Questo valore è il pavimento plug-in a questa N, non
  struttura. È il comportamento atteso dall'*inverse crime* (§3.2 della
  nota): T è a sua volta un campione multinomiale del p\* di produzione.
- **Errore di derivazione di `cs_build`** (*misurato*). Passare da
  Π_blocchi a Π_grezzo costa 0,0005 nat di KL. I momenti di T rispetto ai b
  derivati si scostano dell'1,1% (MRE). Esempio: q13, che è nello span, ha
  |z_T| mediano 0,48 con Π_grezzo e 0,03 con Π_blocchi. La causa è
  l'assunzione (3) di `cs_build`: P(zona | sesso, occupato) costante sui bin
  d'età.

**ρ_h** (*misurato*: `rho.csv`, p\* di Π_blocchi; i valori con Π_grezzo
coincidono alla terza cifra):

| funzione | ρ_h | nota |
|---|---|---|
| controlli positivi (1 cella vincolata per blocco, 16) | ≤ 8e-10 | nello span, come deve |
| q13 occupati 25–64 per zona (4) | ≤ 2e-10 | nello span: Z4 la vincola |
| q11 laureati 25–64 per zona (4) | 0,33–0,35 | |
| q23 donne 25–49 laureate occupate | 0,35 | |
| q22 stranieri, istruzione ≤ media, in cerca | 0,70 | |
| q12 istruzione × condizione (36 celle) | mediana 0,75; da 0,42 (post-laurea occupati) a 0,95 (nessun titolo in cerca) | non vincolata a nessuna scala |

Le celle rare (in cerca, altra condizione) hanno ρ vicino a 1: sono quasi
interamente informazione fuori vincolo.

**Livello 0** (*misurato*). Su 50 funzioni non di controllo, lo scarto di T
da p\* è |z| medio 0,44, e nessuna ha |z| > 2. È compatibile con il solo
rumore; il criterio del §3.3 della nota è soddisfatto per le domande
lineari su X. R0, R1 completo e le domande di ordine ≥ 2 sono il passo 4.

**Candidati g del livello 1a** (*misurato*):

| g | ρ_g | ‖g_⊥‖ (sd) | effetto al primo ordine sulla batteria |
|---|---|---|---|
| g1 stranieri laureati in cerca | 0,87 | 0,034 | corr. ±0,22–0,24 con q12 post-laurea in cerca e con q22 |
| g2 coniugati laureati | 0,58 | **0,178** | **nullo** (Cov ≈ 1e-17 con tutte le h) |
| g2b celibi laureati 25–34 | 0,33 | 0,063 | **nullo** (Cov ≈ 1e-18) |
| g3 seconde generazioni 15–24 in cerca | 0,95 | 0,018 | trascurabile (corr. ≤ 0,025) |

La previsione della v1 su g3 («‖g_⊥‖ probabilmente il più piccolo») è giusta
in valore assoluto (0,018), ma g3 è il candidato con ρ più alto (0,95): è
raro, ma quasi del tutto fuori vincolo.

**Perché g2 è invisibile** (*dichiarato*, dalla struttura). In p\* lo stato
civile è legato al resto solo attraverso il blocco A (sesso × età), e
nessuna domanda della batteria Q lo coinvolge. Quindi Cov(h_⊥, g_⊥) = 0 per
ogni h della batteria. Un'inclinazione lungo g2 cambierebbe la verità in un
modo che Q non vede: l'errore di R1 sulla batteria sarebbe nullo per ogni
θ, anche con un KL grande.

## 3. Incoerenza di Π_grezzo (corretta in `532f99a`)

Π_grezzo ometteva da c1 le celle non celibi sotto i 16 anni, come fa ISTAT.
Ma T contiene **12 coniugate di 15 anni**. Il bin 15–24 ammette lo stato
civile ≠ celibe, ed enrich assegna l'età singola dentro il bin senza
guardare lo stato civile.

Effetti (*misurato*, `risultati/passo2/036023/cs_build.log` prima e dopo):
- il totale di c1 era 184.585, quello di c2 184.597;
- Z2, che `cs_build` armonizza con IPF fra Z1 (da c1) e B (da c2), non
  poteva rispettare entrambi: audit «Z2 somma citt vs Z1» = 3,84;
- il constraint set era quindi infeasibile e il solver esatto divergeva
  (λ fino a 1e19, MRE 2,13, p\* su una sola cella).

**`fit_cs` è terminato senza errore e ha scritto la popolazione.**

Correzione in Π (non in gsp): quando T ha massa sulle celle che ISTAT non
pubblica, Π le pubblica comunque, con un avviso, come già faceva per c8.
Dopo la correzione l'audit dà 8,8e-11 e il fit converge.

**Produzione** (*misurato*): ho controllato i 259 fit di produzione
(`fit_K?C.json`, K10C escluso). Il peggiore ha MRE 0,10%, e nessuno supera
l'1%. Nessun fit divergente è in produzione. Il rischio però esiste:
`fit_cs` non controlla la convergenza, e l'unico segnale sarebbe l'audit di
`cs_build`, che stampa e non si ferma.

## 4. Correzione datata alla v2

*v2 §4, testo originale:* «12 non celibi di 15 anni in T […]. Effetto
trascurabile; annotato.»

*Correzione 10/10/2026:* per la produzione resta vero, perché ISTAT
pubblica c1 senza quelle celle e il cs di produzione è coerente. Per il
gemello **non era trascurabile**: attraverso la convenzione di c1 in Π
rendeva infeasibile il constraint set (§3). Resta da notare che una
popolazione gsp contiene coniugati di 15 anni, cosa che c1 ISTAT esclude.

## 5. Decisioni per Mirko

1. **Controllo di convergenza in `fit_cs`** (proposta, non applicata).
   `fit_cs` dovrebbe uscire con errore, senza scrivere la popolazione, se
   l'MRE dei vincoli positivi del fit esatto supera una soglia (ad es.
   1%). Sulla flotta attuale non cambierebbe nulla: il massimo è 0,10%.
2. **Feature g del livello 1a** (decisione 4 della nota §13). Proposta:
   **g1** (stranieri laureati in cerca) come variante principale, perché è
   l'unico candidato con effetto previsto non nullo sulla batteria. Per g2
   ci sono due strade: aggiungere a Q una domanda che coinvolga lo stato
   civile (ad es. «coniugati laureati per zona»), oppure dichiararlo come
   caso «invisibile a Q». Sarebbe un risultato utile per il paper: il gap KL
   non basta a prevedere l'errore, conta l'allineamento fra g_⊥ e le
   domande.
3. **Coniugati di 15 anni in T e in produzione.** Si possono escludere con
   una regola su età singola × stato civile in enrich (3d), oppure si
   lasciano. Collegato al TODO «età condizionata allo stato civile».

## 6. Prossimi passi

1. Passo 4: livello 0 con R0 (indipendenza) e R1 (anelli 1, 3 e 4 su Π(T),
   sotto `gemello/lavoro/`). Serve `domande.py` sulle popolazioni, con le
   domande di ordine 2 e 3 sui nuclei, e `metriche.py`.
2. Pendenze previste contro misurate: a θ piccolo, dopo la scelta di g.

## 7. Aperto (cumulativo)

- Rigenerare gli anelli 3+4 della flotta con l'età corretta (release).
- Regole `IMPOSSIBILI` per background × origine, con refit.
- Età singola condizionata allo stato civile, e coniugati di 15 anni.
- Causa del disallineamento dei nuclei di produzione di Modena.
- Controllo di convergenza in `fit_cs` (§5.1).
- Scelta di g e completamento della batteria Q (§5.2).
