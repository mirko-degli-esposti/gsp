# Gemello identico: stato dopo il passo 2

*v2, 10/10/2026. **Sostituisce `gemello_stato_v1.md`** (ora in `storico/`).
Rispetto alla v1:*
- *D1–D4 sono confermate da Mirko;*
- *aggiunge il passo 2 (Π_grezzo e confronto con le tavole ISTAT);*
- *documenta un difetto di produzione trovato nel passo 2, cioè l'età
  singola dell'anello 3, e la sua correzione;*
- *registra la scelta della verità T del livello 0.*

*L'inventario dei blocchi (§1) è quello della v1, senza modifiche di
sostanza.*

*Convenzione delle etichette: **misurato** = c'è un log in `misure/` o in
`~/progetti/gemello/risultati/`; **dichiarato** = viene dal codice o da una
fonte; **aperto** = non deciso o non misurato.*

---

## 0. Commit di riferimento

| repo | commit | contenuto |
|---|---|---|
| gsp | `afe1aba` | `GSP_COMUNI_DIR`; `cs_build` usa `G.path_*` (D2) |
| gsp | `6224a94` | enrich (3d): età singola ripartita sul comune (§3) |
| gsp | `b804aca` | `assign_nucleo.trova_popolazione` rispetta `GSP_COMUNI_DIR` |
| gemello | `d59f577` | scheletro, `pubblica.py` (Π_grezzo), passo 2 |
| gemello | `d34a1c5` | `genera_verita.sh` (T del livello 0), passo 2 su T |

L'env conda `ml` è stato rinominato `gsp` anche su WSL (`257b778` per la
nota sulle fonti; Uniboh `90c465a`).

## 1. Inventario dei vincoli (dalla v1, invariato)

Lo spazio X di K9C ha 9 variabili: zona, sesso, età (8 bin), stato civile
(4), cittadinanza (2), istruzione (6), condizione (7), background (6),
origine dei genitori (5). Quindi |X| = 161.280 × n_zone.

I blocchi sono 16 (A–H, GC, S, Z1–Z5), più 26 celle α=0 da 4 regole
`IMPOSSIBILI`. La tabella completa, con la tavola di provenienza, le classi
grezze e la derivazione di ciascun blocco, sta nella v1 (§2): l'ha confermata
Mirko ed è riprodotta, per Modena, in
`gemello/risultati/passo2/036023/blocchi.csv` (*misurato*).

Punti fermi della v1, ancora validi:
- Le tavole di sezione (`P*`, `ST*`, `PF3–PF8`) **non** sono vincoli del
  MaxEnt. Entrano negli anelli 3 e 4 come condizionali. ρ_h e il gap KL
  coprono solo l'anello 1, alla scala di zona.
- Istruzione × condizione non è mai vincolata: q12 è interamente fuori dallo
  span.
- Il comune per lo sviluppo è Modena 036023: |X| = 645.120, m = 663, fit
  esatto in 16 s (*misurato*, `fit_K9C.json`).

## 2. Decisioni confermate (10/10/2026)

- **D1.** Π_grezzo è il caso principale: Π produce le tavole grezze e
  `cs_build` gira invariato. Π_blocchi (blocchi esatti da T) resta il
  riferimento e **non è ancora implementato** (*aperto*).
- **D2.** Interventi minimi su gsp, ognuno con un commit dettagliato. Fatto:
  `GSP_COMUNI_DIR`, più due percorsi scritti a mano corretti (`cs_build`,
  `assign_nucleo`). Verifica di non regressione: `cs_K9C.json` e
  `targets_K9C.json` di Modena sono byte-identici; i nuclei sono
  byte-identici fra HEAD e versione patchata.
- **D3.** Al livello 2 si usano i bin ISTAT, con i 14enni INSEE ricodificati
  a `non_applicabile`.
- **D4.** Per `DIPL ZZ`, il titolo dei 9–13enni si ricostruisce dall'età
  (≥ 13 media, 10–12 elementare, < 10 nessun titolo).
- **Regola generale (Mirko):** le popolazioni esistenti non si toccano mai.
  Tutto si scrive altrove; `pubblica.scrivi_grezzo` rifiuta qualunque
  destinazione dentro `gsp/data/`.

## 3. Difetto di produzione: l'età singola dell'anello 3 (corretto)

**Il difetto** (*dichiarato*, dal codice). `enrich.assegna_eta` arrotondava
con `largest_remainder` dentro gruppi (sezione, sesso, bin) di 1–5
individui. Il resto andava sempre agli anni più pesanti del quinquennio, in
modo identico in ogni sezione. Di conseguenza l'assunzione (9) di enrich
(«dentro il quinquennio vale la distribuzione comunale dell'anagrafe») non
era rispettata. I marginali per classe (8 bin) e per quinquennio erano
corretti. Era un difetto noto; il passo 2 lo ha fatto riemergere attraverso
c1, c2 e il blocco C.

**L'entità** (*misurato*, `misure/eta_singola_enrich_20261010.txt`, script
`diagnostica/eta_singola_vs_anagrafe.py`). TV su sesso × età singola contro
c1, popolazioni di produzione:

| comune | N | TV | di cui entro blocco |
|---|---|---|---|
| Bologna 037006 | 390.098 | 0,085 | 0,085 |
| Parma 034027 | 198.121 | 0,105 | 0,105 |
| Castenaso 037021 | 16.357 | 0,114 | 0,114 |
| Reggio E. 035033 | 171.207 | 0,144 | 0,143 |
| Piacenza 033032 | 102.887 | 0,147 | 0,147 |
| Modena 036023 | 184.597 | 0,171 | 0,171 |
| Imola 037032 | 69.332 | 0,172 | 0,171 |
| Rimini 099014 | 150.046 | 0,199 | 0,198 |
| Vernasca 033044 | 2.014 | 0,283 | 0,281 |

A Modena alcune età con più di 50 residenti hanno 0 individui, e il rapporto
T/anagrafe arriva a 1,88.

**La correzione** (`6224a94`). Dopo `assegna_eta` si chiama
`riequilibra_anno_singolo`. Il blocco di ciascun individuo resta quello
assegnato; gli anni dentro il blocco si ripartiscono sull'intero comune
(`largest_remainder` con i pesi dell'anagrafe) e si permutano a caso, con un
generatore separato, `default_rng([seed, 3])`. Verifiche su Modena
(*misurato*, stesso log):
- (a) HEAD riproduce byte per byte l'`_avq_full` di produzione;
- (b) cambia solo `eta_anni`, e nessun individuo cambia blocco;
- (c) i marginali sezione × sesso × blocco e sezione × sesso × quinquennio
  sono identici;
- TV scende da 0,1712 a 0,0051, e la parte entro blocco da 0,1706 a 0,0001;
- (d) due corse danno file byte-identici.

**Il residuo** di 0,0051 sta nei totali comunali dei blocchi (*misurato*).
Viene dal passo sezione → quinquennio (quote di sezione 2023 contro
anagrafe 2024) e dalla ripartizione 4/5–1/5 del quinquennio 5–9: l'età 9 è
sotto di 124 (F) e 104 (M). La correzione minima lascia questi totali
invariati, di proposito.

**Cosa resta (*dichiarato*, per costruzione).** Dentro il blocco l'età
singola è indipendente dallo stato civile e dalle altre variabili. Il blocco
75+ va da 75 a 100 anni, quindi T contiene per esempio donne coniugate di
96 anni nella stessa proporzione delle 76enni. Nel passo 2 questo dà c1 con
|z| medio 2,8 (§4). Miglioria possibile, **non fatta**: usare in (3d) i pesi
sesso × età × stato civile di c1 invece di sesso × età.

**Produzione: gli `_avq_full` e i nuclei della flotta hanno ancora l'età
vecchia.** Decidere se e quando rigenerare gli anelli 3 e 4 è una scelta di
release (*aperto*). Gli anelli 1 e 2 non dipendono da questo passo.

## 4. Passo 2: Π_grezzo su T (Modena)

**La verità T del livello 0** (`gemello/script/genera_verita.sh`):
- anelli 1+2 di produzione **copiati** (`popolazione_K9C_avq.csv`, sha256
  `fbd73445…`);
- anelli 3+4 rigenerati con gsp `b804aca` dentro `gemello/verita/`
  (`GSP_COMUNI_DIR` e `--out-dir`);
- un manifest con il commit, i comandi e gli sha256 dell'output
  (`avq_full` `336559d9…`, nuclei `c919a673…`).

Le popolazioni di produzione non sono state toccate: le date dei file sono
invariate, 19/08.

**Π_grezzo** (`gemello/gemello/pubblica.py`) costruisce da T le tavole c1–c8,
z1–z4 e z6 nel formato di `cs_build`, imitando le convenzioni ISTAT
osservate per Modena:
- c1: gli stati civili diversi da celibe sono assenti sotto i 16 anni;
- c2: gli zeri sono omessi;
- c8: solo le combinazioni ammissibili;
- z4: occupati senza limite d'età, residuo calcolato su 15–64;
- tutte le altre tavole: griglia completa.

Classi e costanti si importano da `cs_build`.

**Risultati** (*misurato*: `gemello/risultati/passo2/036023/`, `z_tavole.csv`
e `blocchi.csv`; comando `python script/passo2_pi_su_gsp.py
config/livello0.yaml`).

*Blocchi del constraint set* (`cs_build` su Π(T) contro produzione):
- tutti compatibili con il rumore multinomiale: |z| medio da 0,49 a 0,87,
  quota con |z| > 2 fra 0 e 9,4% (B), |z| massimo 3,1;
- i blocchi strutturali S (1–2 celle) hanno |z| 1,43 e 1,53: sono un solo
  scarto ciascuno, compatibile;
- H fa eccezione: |z| 1,11, per le 6 celle extra (sotto);
- il blocco C passa da |z| 2,03 (massimo 15,2) sulla popolazione con l'età
  difettosa a 0,73 (massimo 3,1) su T.

**Il criterio di accettazione del passo 2 è soddisfatto.**

*Tavole grezze:*
- c3–c7, z1–z3, z6: |z| da 0,6 a 0,9.
- c2 (età singola × cittadinanza): |z| 1,10, contro 6,8 prima della
  correzione.
- c1 (età singola × stato civile): |z| 2,78. È l'indipendenza dentro il
  blocco descritta al §3, non un errore di Π.
- z4: |z| 5,8. Nella tavola originale gli occupati di sezione e quelli
  comunali vengono da fonti diverse, e `cs_build` usa solo le quote
  P(zona | sesso, occupato): il blocco Z4 risultante ha |z| 0,57.

**Altri due difetti di gsp trovati (non corretti):**
1. **c8 / blocco H.** T ha 57 individui (0,03%) su combinazioni background
   × origine impossibili: `naturalizzato_g2` e `straniero_g2` con origine
   `non_applicabile` (55), e 2 immigrati con origine valorizzata. Sono celle
   assenti da c8, quindi non vincolate, e il MaxEnt ci mette massa. Rimedio
   proposto: due regole in `IMPOSSIBILI` (g2 ⇒ origine ≠ non_applicabile;
   immigrato ⇒ origine = non_applicabile). Cambia l'anello 1 e quindi
   richiede un refit: *aperto*.
2. **12 non celibi di 15 anni** in T: il bin 15–24 ammette stato civile ≠
   celibe, mentre c1 ISTAT li pubblica solo da 16 anni. Effetto trascurabile;
   annotato.

**Nuclei di produzione di Modena non allineati al codice** (*misurato*).
`data/nuclei/nuclei_036023.csv` è del 19/08. Il codice attuale, a parità di
input, dà 31.479 ruoli e 58.009 `id_nucleo` diversi. `9b3ac05` (24/08) ha
modificato `assign_nucleo` e `gsp.nucleo`; la causa non è stata accertata
(*aperto*). Non riguarda il gemello, che rigenera i nuclei.

## 5. Prossimi passi

1. Π_blocchi: i blocchi esatti da T, come riferimento di D1.
2. Passo 3 (`teoria.py`): enumerazione di X per Modena, proiezione su
   span(f), ρ_h per le domande lineari, ‖g_⊥‖ per i candidati g del livello
   1a.
3. Passo 4: livello 0 con R0 e R1. R1 è il fit su Π(T) seguito dagli anelli
   3 e 4, tutto sotto `gemello/lavoro/`.

## 6. Aperto

- Rigenerazione degli anelli 3 e 4 della flotta con l'età corretta: è una
  decisione di release.
- Le regole `IMPOSSIBILI` per background × origine, con il refit che
  richiedono.
- I pesi sesso × età × stato civile in (3d).
- La causa del disallineamento dei nuclei di Modena.
