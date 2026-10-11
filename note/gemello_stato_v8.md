# Gemello identico: stato dopo il livello 1a con g2 e g4

*v8, 11/10/2026. **Sostituisce `gemello_stato_v7.md`** (ora in `storico/`).
Rispetto alla v7 aggiunge:*
- *il livello 1a con le feature g2 e g4: griglia, risultati, limiti;*
- *una lettura delle tre feature (g1, g2, g4) insieme, che ridimensiona il
  modo in cui la v7 riportava la previsione dell'errore (§4);*
- *repo GitHub privati, nuovo script di misura, estensione del generatore
  del preprint.*

*Livello 0 e passi 1–5 restano come nella v6, il livello 1a con g1 come
nella v7 (`storico/`).*

*Etichette: **misurato** = c'è un log; **dichiarato** = viene dal codice o
da una fonte; **aperto** = non deciso o non misurato.*

*Log di misura di questa nota:
`note/misure/gemello_livello1a_g2_g4_20261011.txt`. Contiene `analisi.txt` e
`bersaglio_theta` di g2 e g4, le sintesi, la griglia a priori e il
controllo di determinismo. Le sorgenti sono in
`gemello/risultati/livello1a/{g2,g4}/`, che non è versionato.*

---

## 0. Commit e provenienza

| repo | commit | contenuto |
|---|---|---|
| gemello | `5910f76` | config `livello1a_g2.yaml`, `livello1a_g4.yaml` (griglia) |
| gemello | `36ef29f` | chiave `g.bersaglio`; `numeri_preprint` per più g |
| gemello | `e17faae` | `script/misura_bersaglio_theta.py` |
| gemello | `32444d4` | `numeri_preprint`: primo attraversamento solo per θ > 0 |
| paper-gemello | `a187265` | numeri e figure rigenerati con g2 e g4 |
| gsp | `fe611fe` | patch della v7 (remote) |

**Corse:**
- `script/livello1a.py config/livello1a_g2.yaml`: 4.853 s;
- `script/livello1a.py config/livello1a_g4.yaml`: 6.032 s.

Le due corse sono state eseguite in sequenza con il codice di `5910f76`. La
chiave `bersaglio` è stata aggiunta a corsa di g2 già avviata: serve solo
all'analisi, non alla corsa.

**Analisi:** `script/analisi_livello1a.py <config>` e
`script/misura_bersaglio_theta.py <config>`.

**Determinismo** (*misurato*): a θ = 0, g2 e g4 riproducono g1, perché
usano la stessa verità e gli stessi semi.
- Decisioni: identiche.
- Quote: identiche nelle colonne non numeriche; nelle colonne numeriche
  differiscono al massimo di 3,6e-15, cioè per l'ordine delle somme in
  virgola mobile.

## 1. Disegno di g2 e g4 (*dichiarato*: config)

- **g2** = coniugati laureati (stato civile × istruzione), ρ = 0,58.
  È il caso «invisibile» alle domande lineari. Bersaglio dichiarato prima
  dei risultati: **q34** (coppie entrambe laureate, anello 4).
- **g4** = donne coniugate occupate (sesso × stato civile × condizione),
  ρ = 0,38. Bersagli: **q14** (donne 25–49 coniugate occupate per zona) e
  **q31** (nuclei con figlio < 3 anni e due genitori occupati).
- **Griglia** (*misurato*, a priori). Var(g_⊥) su p₀ vale:
  - 0,00114 per g1;
  - 0,0316 per g2;
  - 0,0136 per g4.

  Con la griglia di g1, a θ = 3 la KL arriverebbe a 0,086 per g2 e 0,042
  per g4, cioè 5–10 volte il massimo di g1. Si è quindi tarato θ in unità
  di sd(g_⊥): θ = f × {−2, −1, 0, 0,5, 1, 1,5, 2, 3}, con f = 0,19 per g2 e
  0,29 per g4, più due punti estesi a 4,5× e 6×. Decisione di Mirko,
  11/10/2026, presa prima dei risultati.
- Tutto il resto è come per g1: K = 10, R2a a φ ∈ {1%, 5%} con B = 10, R3
  con B = 20, aree fisse.

## 2. g2 (*misurato*)

**Bilancio:**
- E[g2] va da 0,0949 a 0,1405 (p₀: 0,1070); la KL da 1,4e-4 a 0,0185.
- Identità pitagorica: scarto massimo 7,4e-4.
- Approssimazione quadratica: rapporto da 0,90 a 1,006. g2 è comune, e
  l'approssimazione regge molto meglio che per g1 (0,41–1,56).
- IPF convergente a 1e-6 su tutti i θ.

**Il tilt è invisibile a Π.** A livello comunale:

| | θ = −0,38 | θ = 0 | θ = 1,14 |
|---|---|---|---|
| quota di g2 nella verità | 0,0952 | 0,1075 | 0,1401 |
| quota di g2 in R1 (media di 10) | | 0,1064–0,1070 su tutti i θ, sd 0,0009 | |

A θ = 1,14 R1 sottostima g2 del 24%, ed è l'errore previsto.

**Domanda bersaglio q34:**
- *Per area* (errore relativo pesato, R1): da 0,190 a θ = 0 a 0,203 a
  θ = 1,14, entro il rumore delle repliche lungo la griglia. Per R0 da 0,227
  a 0,260.
- *φ\* significativo*: un solo attraversamento, R2a all'1% a θ = 1,14;
  nessuno per R3.
- *Comunale*: nella verità q34 passa da 0,0705 (θ = −0,38) a 0,0712 (θ = 0)
  e a 0,0791 (θ = 1,14), cioè +11% fra θ = 0 e θ massimo. R1 resta fra
  0,0701 e 0,0725 (sd delle repliche 0,0008–0,0020). A θ = 1,14 lo scarto
  vale circa 7 sd delle repliche. Il segnale c'è, ma è debole rispetto al
  +30% di g2 sullo stesso intervallo.

**Perché la trasmissione a q34 è debole** (meccanismo *dichiarato*, numeri
*misurati*):
- **L'anello 4 non forma coppie solo fra coniugati.** In `gsp.nucleo` v2 lo
  slot P chiede lo stesso stato civile di R, ma ammette coppie di non
  coniugati (convivenze). È una scelta voluta, dichiarata nella docstring.
  - Nella verità i coniugati sono il 55,1–55,9% dei membri di coppia, su
    tutti i θ.
  - La diagnostica dei nuclei a θ = 0 dà il 93,0% di coppie omogenee per
    stato civile e il 24,6% di coniugati «incoerenti».
- **Il tilt sposta laureati, non li aggiunge.** A momenti fissi (istruzione
  e stato civile marginali invariati), il tilt sposta laureati dai non
  coniugati ai coniugati. Fra i membri di coppia i due gruppi si mescolano:
  la quota di g2 fra loro sale da 0,120 a 0,177, ma l'effetto su «entrambi
  laureati» in gran parte si compensa.
- **Conseguenza.** Quanto g2 arriva a q34 dipende dall'anello 4 della
  pipeline, che il gemello eredita, non solo da MaxEnt. Il test di q34 con
  g2 è quindi debole per costruzione. Il test diretto è la variante 1b
  (omogamia piantata nei nuclei).

**Altre domande:** tutte piatte in θ. Fuori da q34 ci sono 0
attraversamenti significativi su 220 confronti.

## 3. g4 (*misurato*)

**Bilancio:**
- E[g4] va da 0,0980 a 0,1274 (p₀: 0,1057); la KL da 1,4e-4 a 0,0181.
- Identità pitagorica: scarto massimo 2,9e-3. Approssimazione quadratica:
  da 0,88 a 1,002.
- **Limite:** ai tre θ più grandi (0,87, 1,305, 1,74) l'IPF di `inclina`
  si ferma al tetto di 20.000 iterazioni, con MRE residuo 1,04e-6, 1,47e-6
  e 1,81e-6 contro la tolleranza 1e-6. Lo scarto è piccolo e l'identità
  regge, ma va dichiarato. Per le corse future si potrebbe alzare il tetto.

**Domanda bersaglio q14:**
- *Comunale*: nella verità q14 passa da 0,3221 (θ = −0,58) a 0,3445 (θ = 0)
  e a 0,4032 (θ = 1,74). R1 resta fra 0,3415 e 0,3430 (sd 0,003).
- *Per area* (R1): da 0,083 a θ = 0 a 0,154 a θ = 1,74, e 0,102 a
  θ = −0,58. R0 cresce da 0,366 a 0,457. R2a al 5% resta fra 0,080 e 0,095.
- *φ\* significativo*:
  - R2a: 5% a θ = 0,87, 1% a θ = 1,305 e 1,74, e anche 5% a θ = −0,58;
  - R3: 5% a θ = 1,305, 2% a θ = 1,74.
- **Limite:** q14 è quasi g4 ristretta alle donne 25–49, e la versione per
  zona sta nella batteria lineare. Che R1 sbagli q14 come sbaglia g4 è
  quindi atteso: non è un test di trasmissione oltre le tavole. Il dato
  utile è la scala: con KL ≈ 0,005–0,01 il campione al 5% batte già il
  MaxEnt sulle quote per area.

**Domanda bersaglio q31:** nessun segnale.
- Nella verità q31 oscilla fra 0,397 e 0,429 senza tendenza in θ.
- R1 sta fra 0,409 e 0,420, con sd delle repliche fra 0,006 e 0,015.
- Nessun attraversamento.

Il denominatore (nuclei con figlio < 3 anni) è piccolo e il rumore copre
qualunque effetto della grandezza attesa. È plausibile che pesi anche la
diluizione dell'anello 4 vista per g2: fra i membri di coppia la quota di g4
sale solo da 0,118 a 0,157. Questa lettura è *aperta*: l'effetto atteso su
q31 non è stato calcolato.

**Altre domande:** fuori da q14 e q31 c'è 1 attraversamento significativo
su 200 confronti (q33 a θ = 0,58, R2a 5%), quanti ne attende la soglia per
caso.

## 4. Lettura delle tre feature insieme (*misurato*)

**Correzione di lettura rispetto alla v7.** La v7 riportava la previsione
dell'errore di R1 con la correlazione su tutte le coppie (h, θ): 0,92/0,89
per g1. Per g2 e g4 la stessa statistica dà 0,995/0,993 e 0,989/0,985, ma è
trascinata da poche h. Quasi tutte le h della batteria hanno un effetto
previsto molto sotto il rumore di T: la mediana di |effetto|/rumore vale
0,08 per g1 e meno di 0,01 per g2 e g4. Il testo della v7 resta valido nei
numeri; cambia come vanno letti.

| | tutte le h | senza g stessa | h con effetto > 2 volte il rumore |
|---|---|---|---|
| g1 | 413: 0,92 / 0,89 | 406: 0,89 / 0,84 | 49: 0,995 / 0,994, pendenza 0,98–0,99 |
| g2 | 531: 0,995 / 0,993 | 522: 0,82 / 0,77 | 15 (solo g2, g2b): 1,000 / 1,000 |
| g4 | 531: 0,989 / 0,985 | 522: 0,83 / 0,79 | 32 (g4, q14 per zona): 1,000 / 0,999 |

*Nelle celle: numero di coppie, poi correlazione con l'errore esatto di R1
atteso / R1 misurato.*

Per g4, tolte anche le q14 restano 486 coppie, con correlazione
0,34 / 0,33 e pendenza instabile (1,7 e 1,9): sono effetti trascurabili
dominati dal rumore.

**Come leggerlo.**
- **H2 regge dove c'è qualcosa da prevedere.** Dove l'effetto supera il
  rumore, l'errore di MaxEnt è previsto quasi esattamente da modello e
  feature, prima di generare.
- **La batteria vede g1, non vede g2 né g4.** g1 tocca molte domande:
  q12, q22, q23. Per g2 e g4 le uniche h sopra il rumore sono g stessa,
  la sua quasi gemella g2b, e q14, che è quasi g4. È la definizione
  operativa di «invisibile a Q», e g2 la soddisfa come progettato. Vale
  anche per g4, salvo q14.
- **Al θ massimo (KL circa 0,018) R1 sbaglia il margine di g del 24%
  (g2) e del 17% (g4)**, ma le domande della batteria non se ne accorgono,
  a parte quelle costruite sulla stessa congiunzione.
- **H3** (*misurato*, qualitativo): φ\* esiste solo sulle domande
  allineate con g. Quando esiste cala al crescere di θ (q22 con g1, q14
  con g4). Fuori dai bersagli ci sono 3 attraversamenti su 596 confronti,
  sommando le tre g. Nota: con g2 l'unico attraversamento è su q34 al θ
  massimo, ed è debole.

## 5. Limiti di queste misure

1. **Una sola realizzazione di T per θ.** La verità ha rumore proprio:
   lungo θ, q31 nella verità oscilla di circa ±0,015. Le tendenze
   comunali vanno lette sull'intera griglia, non su un singolo θ.
2. **Errori per area dominati dal rumore delle aree** (87 aree, circa
   2.000 abitanti ciascuna). Gli effetti comunali di qualche punto
   percentuale, come q34 con g2, non emergono per area. `misura_bersaglio_theta.py`
   esiste per questo.
3. **La trasmissione alle domande di nucleo passa dall'anello 4 di gsp**
   (coppie non necessariamente coniugate, 24,6% di coniugati incoerenti).
   Per q31 e q34 il livello 1a misura MaxEnt + anello 4 insieme, non
   MaxEnt da solo.
4. **q14 coincide quasi con g4** (§3): non è un test indipendente.
5. **IPF di g4 non del tutto convergente** ai tre θ più grandi (§3).
6. **φ\* con B = 10 (R2a) e B = 20 (R3)** e una soglia di −2 errori
   standard: su circa 600 confronti fuori bersaglio sono attesi alcuni
   falsi positivi, e se ne osservano 3.
7. **Un solo comune** (Modena). La generalità è *aperta* fino al
   livello 2.

## 6. Preprint (`~/progetti/paper-gemello`)

- `numeri_preprint.py` produce ora una sezione per ogni
  `config/livello1a*.yaml` con risultati: 167 macro, con le figure
  `_g2`/`_g4` per bilancio, previsione e domande bersaglio.
  - Le macro di g1 hanno gli stessi valori di prima. Si aggiungono
    `loneEgMin` e `loneCrossNegN`.
  - `ThetaFirst` considera solo θ > 0. Per g4 il primo attraversamento in
    ordine era θ = −0,58.
- Il testo non usa ancora le macro di g2 e g4. La sezione del livello 1
  va riscritta con la lettura del §4, cioè con la previsione per effetto
  sopra il rumore e non solo sulla correlazione globale, e con i limiti del
  §5 (*aperto*, da discutere con Mirko).
- Restano i segnaposto della v7 e la bibliografia da verificare.

## 7. Prossimi passi

1. **Discussione con Mirko** di questi risultati e della lettura del §4,
   prima di toccare il testo del preprint.
2. **Download INSEE per il livello 2:** subito dopo questa fase (decisione
   di Mirko, 11/10/2026).
3. **Titolo del preprint:** dopo il livello 2.
4. **Varianti 1b (omogamia nei nuclei) e 1c (segregazione spaziale).** Il
   §2 mostra che q34 si testa solo con 1b.
5. **Rigenerazione degli anelli 3+4 della flotta per l'età singola.**
   Confermata da Mirko. Va preparata come release, con piano scritto e
   backup: `data/comuni` non si tocca prima dell'approvazione.

## 8. Aperto (cumulativo)

- Rigenerare gli anelli 3+4 della flotta con l'età corretta (release, §7).
- Regole `IMPOSSIBILI` per background × origine, con refit.
- Età singola condizionata allo stato civile, e coniugati di 15 anni.
- Causa del disallineamento dei nuclei di produzione di Modena.
- R2b non implementato.
- MSE di R3 senza g3; degenerazione sulle domande rare a φ basso.
- Riferimenti del preprint da verificare.
- Effetto atteso di g4 su q31 non calcolato (§3).
- Tetto di iterazioni dell'IPF di `inclina` per tilt forti (§3).
- *Nuovo, sulla pipeline:* la quota di coniugati fra i membri di coppia
  (circa 55%) e il 24,6% di coniugati incoerenti nell'anello 4 sono
  plausibili per Modena? Serve un confronto con il censimento (coppie
  coniugate contro unioni libere), senza il quale resta *aperto*.

## 9. Ripresa nella prossima chat

**Da leggere per primo:** questa nota. Il disegno completo è in
`note/nota_gemello_v1.md`; le note precedenti in `note/storico/`.

**Dove sta cosa:**
- `~/progetti/gsp` (`dev-mirko`, push su `privato`): la pipeline. Gli
  interventi per il gemello sono `GSP_COMUNI_DIR`, `GSP_SUBMUN_DIR`,
  l'età singola in enrich e il controllo di convergenza in `fit_cs`.
- `~/progetti/gemello` (`dev-mirko`, `origin` = GitHub privato
  `mirko-degli-esposti/gemello`):
  - codice in `gemello/`, script in `script/`;
  - config `livello0.yaml`, `livello1a.yaml` (g1), `livello1a_g2.yaml`,
    `livello1a_g4.yaml`;
  - non versionati: `verita/`, `lavoro*/`, `livello1a/`, `risultati/`.
- `~/progetti/paper-gemello` (`main`, `origin` = GitHub privato
  `mirko-degli-esposti/paper-gemello`): `./compila.sh` rigenera e compila.

**Ambiente:** `conda activate gsp`, oppure
`~/miniconda3/envs/gsp/bin/python`.

**Regole che valgono sempre:** mai scrivere in `gsp/data/`; un commit
dettagliato per ogni cambio di codice; i numeri si prendono da una misura;
i numeri del preprint si generano.

**Livello 1a, per una nuova g:**
1. Copiare una config `livello1a_*.yaml`, cambiando `g.id`,
   `g.descrizione`, `g.cond`, `g.bersaglio` e `theta`.
2. Tarare θ in unità di sd(g_⊥) (`TH.Modello.rho(g)["sd_perp"]`) e
   misurare la KL agli estremi con `livello1.inclina` prima di lanciare.
3. Lanciare con
   `nohup python script/livello1a.py <config> > risultati/livello1a/corsa_<g>.log 2>&1 &`.
   Ogni θ richiede 450–690 s.
4. Poi `script/analisi_livello1a.py <config>`,
   `script/misura_bersaglio_theta.py <config>` e
   `paper-gemello/compila.sh`.
