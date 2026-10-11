# Gemello identico: stato dopo il livello 1a con g1, e impianto del preprint

*v7, 10/10/2026. **Sostituisce `gemello_stato_v6.md`** (ora in `storico/`).
Rispetto alla v6 aggiunge:*
- *il livello 1a con la feature g1: costruzione, risultati, verifica della
  previsione;*
- *l'impianto del preprint (`~/progetti/paper-gemello`), con numeri,
  tabelle e figure generati dai risultati.*

*Livello 0, passi 1–5, aree e scale dello z restano come nella v6
(`storico/gemello_stato_v6.md`).*

*Etichette: **misurato** = c'è un log; **dichiarato** = viene dal codice o
da una fonte; **aperto** = non deciso o non misurato.*

---

## 0. Commit e provenienza

| repo | commit | contenuto |
|---|---|---|
| gemello | `62417df` | livello 1a: `livello1.py`, `script/livello1a.py`, config |
| gemello | `f414a5c` | `analisi_livello1a.py`, `numeri_preprint.py` |
| gemello | `67697b7` | φ\* significativo nell'analisi |
| gemello | `3eb65d8` | macro e figure del livello 1a per il preprint |
| paper-gemello | `31af807` … `f421fd3` | impianto, bozza, sezione del livello 1 |

**Corsa del livello 1a:** `python script/livello1a.py config/livello1a.yaml`.
- θ = 0 è stato eseguito a parte, con gemello `62417df` (470 s).
- Gli altri 7 θ sono stati eseguiti con `--theta -2 -1 0.5 1 1.5 2 3`.
  Il manifest dice gemello `f414a5c` e gsp `ec6be37`, ma il codice usato
  dalla corsa è quello di `62417df`: i commit successivi aggiungono solo
  script di analisi.
- θ = 0,5 ha impiegato 4.210 s invece di circa 550. Il ritardo è tutto
  nella fase R2a, compatibile con una sospensione durante la ripartenza
  della sessione; i θ successivi sono tornati a 550–620 s.

**Analisi:** `python script/analisi_livello1a.py config/livello1a.yaml`
(`risultati/livello1a/g1/analisi.txt`, `analisi_*.csv`, `figure/`).

## 1. Costruzione (*dichiarato*: `gemello/livello1.py`)

- **p₀** è il p\* di produzione di Modena (letto in sola lettura): lo stesso
  che ha generato la verità del livello 0.
- **p_θ** è la I-proiezione di p₀·e^{θg} sui vincoli tenuti di p₀, con
  target **i momenti esatti di p₀**, E_{p₀}[f], e non i b del cs. p₀
  rispetta i b solo a MRE 4,3e-4, mentre i suoi momenti sono coerenti per
  costruzione. Quindi p_θ ∝ e^{λ(θ)·f + θg} con E[f] fisso: è la famiglia
  della nota §4.
  - Si calcola con IPF a blocchi, tolleranza 1e-6 (1.500–17.300
    iterazioni secondo θ).
  - Prima prova con i b del cs come target: l'identità pitagorica non
    tornava (KL 7,7e-4 contro H(p₀) − H(p_θ) 4,0e-4 a θ = 1). Con i momenti
    esatti torna (§2).
- **T_θ** si genera come la verità del livello 0: anello 1 dal campione di
  p_θ con seme 42 (procedura di `fit_cs`), anelli 3–4 sulle tavole reali con
  i semi della verità (enrich 42, nucleo `SEME_BASE`).
  - **Controllo θ = 0** (*misurato*): T₀ coincide con la verità del livello 0
    su tutte le 20 colonne comuni, e i nuclei sono byte-identici. Il campione
    dell'anello 1 col seme 42 da p₀ è byte-identico a `popolazione_K9C.csv`
    di produzione.
- **Per ogni θ:** Π(T_θ) completo, R1 (fit di produzione), R0 (IPF), K = 10
  repliche di R0 e R1, R2a a φ ∈ {1%, 5%} con B = 10, R3 su tutti i φ con
  B = 20.
- **Aree:** fisse, quelle del livello 0.
- **g1** = stranieri laureati in cerca di occupazione (cittadinanza ×
  istruzione × condizione), ρ = 0,87.
- **Griglia** θ ∈ {−2, −1, 0, 0,5, 1, 1,5, 2, 3}, fissata prima dei
  risultati.

## 2. Risultati (*misurato*, Modena, g1)

**Bilancio d'informazione:**
- E[g1] va da 0,26 a 6,57 per mille (p₀: 1,50).
- KL(p_θ‖p₀) arriva a 0,0080 nat per individuo a θ = 3.
- **Identità pitagorica:** KL / (H(p₀) − H(p_θ)) − 1 vale al massimo 1,6e-3
  in valore assoluto su tutti i θ (criterio §4.4 soddisfatto).
- **Approssimazione quadratica:** KL / (½θ²Var(g_⊥)) va da 0,41 (θ = −2) a
  1,56 (θ = 3). È asimmetrica, perché g1 è rara e il tilt agisce sulle
  quote relative: per θ grandi l'approssimazione è solo indicativa.

**Previsione dell'errore di R1** (413 coppie h × θ ≠ 0, h = funzioni lineari
su X della batteria del passo 3):

| confronto | correlazione | pendenza |
|---|---|---|
| primo ordine −θ·Cov(h_⊥, g_⊥) contro esatto E_{p₀}[h] − E_{p_θ}[h] | 0,96 | |
| R1 atteso (p\* fittato su Π(T_θ)) contro esatto | 0,92 | 0,99 |
| R1 misurato (media di 10 repliche) contro esatto | 0,89 | 0,99 |

Il residuo dell'atteso rispetto all'esatto è in media 0,55 errori standard
del rumore campionario di T. **H2 è confermata al livello 1:** l'errore di
MaxEnt sulle domande lineari si prevede dal modello e dalla feature
piantata, prima di generare qualsiasi cosa. Per |θ| ≤ 1 la pendenza di g1
stessa è prevista −1,14e-3 e misurata −1,06e-3 (`analisi_pendenze.csv`).

**Errore sulle quote per area (R1):**
- Solo le domande allineate con g1 peggiorano: **q22** passa da 0,364 a
  1,784 lungo la griglia, q12 da 0,022 a 0,035. Tutte le altre domande sono
  piatte in θ.
- Su q22, a θ = 3, perfino R0 (0,573) fa meglio di R1. Le tavole a due vie
  pubblicate (cittadinanza × istruzione, cittadinanza × condizione),
  combinate dal MaxEnt, implicano un'interazione a tre vie che la verità
  piantata contraddice. Questa lettura è *dichiarata* (dalla struttura) e
  coerente con i numeri, ma non è misurata separatamente.

**φ\* significativo** (differenza delle medie < −2 errori standard;
`analisi_phi_star.csv`):

| q22 | θ = 1,5 | θ = 2 | θ = 3 |
|---|---|---|---|
| R2a | 5% | 5% | 1% |
| R3 | 5% | 5% | 0,5% |

- Per θ ≤ 1 e su tutte le altre domande non c'è nessun attraversamento.
- Fuori da q22 ci sono 2 attraversamenti su 176 confronti (q31 a θ = 2,
  q33 a θ = 0,5), quanti ne attende la soglia per caso.
- **H3 è confermata qualitativamente:** φ\* esiste solo dove la domanda
  dipende dall'informazione fuori dalle tavole, e cala al crescere di quella
  informazione.

**Correzione metodologica** (*dichiarato*): la prima definizione di φ\*,
«media del metodo ≤ media di R1», dava attraversamenti spuri su q13, q21 e
q31–q34, dove i metodi sono pari entro il rumore. È stata sostituita dalla
versione con significatività (`67697b7`). La tabella con la prima definizione
resta in `analisi.txt` come documentazione.

**Decisioni** (k = 10): q41 piatta in θ (R1 0,031–0,040); q42 dominata dal
rumore per tutti, come al livello 0.

## 3. Preprint (`~/progetti/paper-gemello`)

- **Convenzioni:** quelle del paper A (elsarticle, file separati, inglese).
- **Numeri e figure non si scrivono a mano.** `numbers.tex` (100 macro),
  `tabelle/` e `figure/` sono generati da `gemello/script/numeri_preprint.py`
  a partire dai CSV di `risultati/` e dal log di misura dell'età in gsp.
  Ogni macro porta in commento la provenienza. `./compila.sh` rigenera e
  compila (9 pagine).
- **Bozza:** introduzione, setting, teoria, disegno, livello 0 (due
  tabelle), livello 1 con g1 (due figure), appendice sulle correzioni della
  pipeline.
- **Segnaposto (`\todo`):** contributi, tabella dei blocchi, R2b, g2/g4,
  livello 2, discussione, conclusioni, riproducibilità.
- **Bibliografia:** stub dai riferimenti di `nota_gemello_v1`, marcati
  `TODO-VERIFICA`. **Non sono verificati sulle fonti** (*aperto*).
- Titolo di lavoro da rivedere con Mirko.

## 4. Prossimi passi

1. Livello 1a con **g2**: invisibile alle domande lineari, va verificato su
   q34 all'anello 4. Poi con **g4** (q14, q31). Basta una config per g: lo
   script è generico.
2. Varianti 1b (omogamia nei nuclei) e 1c (segregazione spaziale), nota §4.2.
3. Livello 2 (INSEE): serve il download sulla macchina di Mirko.
4. Preprint: discussione e conclusioni dopo g2/g4; verifica della
   bibliografia.

## 5. Aperto (cumulativo)

- Rigenerare gli anelli 3+4 della flotta con l'età corretta (release).
- Regole `IMPOSSIBILI` per background × origine, con refit.
- Età singola condizionata allo stato civile, e coniugati di 15 anni.
- Causa del disallineamento dei nuclei di produzione di Modena.
- R2b non implementato.
- MSE di R3 senza g3; degenerazione sulle domande rare a φ basso.
- Riferimenti del preprint da verificare.

## 6. Ripresa nella prossima chat (aggiunta 11/10/2026, patch: nessun contenuto cambiato)

**Da leggere per primo:** questa nota. Poi, se serve il disegno completo,
`note/nota_gemello_v1.md`. Le note precedenti sono in `note/storico/`.

**Dove sta cosa:**
- `~/progetti/gsp` (dev-mirko): pipeline. Gli interventi fatti per il
  gemello sono `GSP_COMUNI_DIR`, `GSP_SUBMUN_DIR`, la correzione dell'età
  singola in enrich e il controllo di convergenza in `fit_cs`.
- `~/progetti/gemello` (dev-mirko, remote `origin` = GitHub privato `mirko-degli-esposti/gemello`): codice
  in `gemello/`, script numerati in `script/`, config in `config/`
  (`livello0.yaml`, `livello1a.yaml`). Non versionati: `verita/`,
  `lavoro*/`, `livello1a/`, `risultati/`.
- `~/progetti/paper-gemello` (main, remote `origin` = GitHub privato `mirko-degli-esposti/paper-gemello`):
  preprint. `./compila.sh` rigenera numeri, tabelle e figure da
  `gemello/script/numeri_preprint.py` e compila.

**Ambiente:**
- `conda activate gsp`, oppure l'interprete
  `~/miniconda3/envs/gsp/bin/python`.
- I terminali aperti prima del rename possono avere `GDAL_DATA`/`PROJ_DATA`
  che puntano a `envs/ml`. `aree.py` li corregge da solo; altrimenti basta
  riaprire il terminale.

**Regole che valgono sempre:**
- Mai scrivere in `gsp/data/`: tutto passa per `GSP_COMUNI_DIR` /
  `GSP_SUBMUN_DIR`, e le funzioni `scrivi_*` lo rifiutano.
- Un commit dettagliato per ogni cambio di codice.
- I numeri si prendono da una misura, mai dalla memoria.
- I numeri del preprint si generano, non si scrivono a mano.

**Comandi per riprendere** (dalla radice di gemello):
- livello 0: `script/passo2_pi_su_gsp.py`, `passo3_teoria.py`,
  `costruisci_aree.py`, `passo4_livello0.py`, `passo5_campione.py`,
  `analisi_passo5.py`, tutti con `config/livello0.yaml`;
- livello 1a: `script/livello1a.py config/livello1a.yaml [--theta …]`, poi
  `script/analisi_livello1a.py`. Ogni θ richiede circa 9 minuti con 7
  processi paralleli. Le corse lunghe vanno lanciate con `nohup … &`.
  Una sospensione della macchina le rallenta, ma non le rompe; i passi già
  fatti si riusano.
- **Per g2 e g4** si copia `config/livello1a.yaml` in
  `config/livello1a_g2.yaml` (e `_g4`), cambiando `g.id`, `g.descrizione`
  e `g.cond`:
  - g2 = `{stato_civile: [coniugato_unito], istruzione: [laurea_o_its, post_laurea]}`
  - g4 = `{sesso: [F], stato_civile: [coniugato_unito], condizione: [occupato]}`

  Le uscite vanno in `risultati/livello1a/<g>/`. `analisi_livello1a.py`
  legge `cfg["g"]["id"]`. **Attenzione:** `numeri_preprint.py` per ora
  legge solo `livello1a/g1`, e va esteso.

**Decisioni in sospeso per Mirko:**
- procedere con g2/g4, poi 1b/1c;
- download INSEE per il livello 2 (dalla sua macchina, script
  `estrai_insee_comune.py` della nota v1);
- titolo del preprint;
- ~~dove ospitare `gemello` e `paper-gemello` (oggi senza remote)~~ deciso l'11/10/2026: due repo GitHub privati separati, non dentro gsp;
- rigenerazione degli anelli 3+4 della flotta (release).
