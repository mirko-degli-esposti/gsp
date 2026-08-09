# Background migratorio per sezione — misura M-EM e anello 3

**Versione 3.0 — 9 agosto 2026**
Mirko Degli Esposti · DIFA, Università di Bologna

I campi `EM1`–`EM6` del censimento permanente 2023 danno il background
migratorio in sei modalità **per sezione di censimento**, con
corrispondenza uno a uno con l'attributo `background` di anello 1. Oggi
quell'attributo ha risoluzione di **zona**, per l'assunzione (8).

Questa nota misura se scendere alla sezione porti informazione reale, e
decide cosa farne in `enrich.py`.

**Risposta: sì.** Netto mediano ~0,022 (italiani) e ~0,018 (stranieri) su
tutte e undici le città, informazione sostanzialmente **ortogonale** a
quella che la pipeline già cattura tramite `area`, e assorbimento
stimato ~5–6% del segnale. Si procede con il raffinamento (§5).

*Changelog v3.0 — sostituisce la v2:*
1. *§7 riscritta. L'assorbimento da parte di `area` è stato misurato tre
   volte con strumenti via via più corretti: 10% → non misurabile →
   **~5–6%**. La decisione non è mai stata in bilico, ma il percorso è
   istruttivo e sta in §7.4.*
2. *I netti di §4 sono **sottostimati di ~8%**: la base includeva la
   sezione stessa e il pavimento era semplificato. Corretti in
   `residuo.py`, misurati su due comuni (§7.2).*
3. *`residuo.py` è ora il modulo condiviso: i tre script di misura vanno
   fatti dipendere da lui (§8.1).*

*La v2 ritirava la «previsione (b)» della v1 e con essa la «regola di
calibrazione» sulle previsioni falsificate: quella ritrattazione resta
valida ed è in §6.2.*

---

## 1. La fonte era già in casa

`istat_sezioni_2023`, registrata il 2 agosto 2026, zip scaricato,
tracciato in git con lo sha. `build_sezioni.py` produce i derivati per
comune **con tutte e 138 le colonne**: `EM1`–`EM6` sono in
`data/submun/{comune}_sezioni_2023.csv` da allora.

Il registro dichiara però `usabile_per: [geografia_subcomunale,
gerarchia_zone, vincoli_zona]`: la fonte è entrata in pipeline per la
sola gerarchia zona/quartiere, ed è la ragione per cui questi campi sono
rimasti invisibili. **Patch al registro**: estendere `usabile_per` con
`background_per_sezione` e ampliare l'`universo`.

Controlli di integrità, su Parma:

| controllo | esito |
|---|---|
| `EM1`+…+`EM6` = `P1` | **esatto** (198.121) |
| `EM5`+`EM6` contro stranieri censuari | 34.436, coincide con il riferimento v22 |
| `EM5`+`EM6` contro `ST17+ST18+ST20+ST21` | **esatto**, scarto +0,00% |
| sezioni con `P1`>0 ed `EM` tutto a zero | **0** |

Il terzo è il controllo che poteva rompere tutto e non si rompe: le due
partizioni della popolazione straniera hanno lo stesso denominatore, il
che rende controllato il confronto di §7.

---

## 2. `EM` raffina la cittadinanza, non la moltiplica

Le sei modalità si spartiscono **deterministicamente** fra le due
cittadinanze di anello 1:

| campo | modalità GSP | cittadinanza |
|---|---|---|
| EM1 Italiani dalla nascita nati in Italia | `italiano_nativo` | ITL |
| EM2 Italiani dalla nascita nati all'estero | `italiano_rientrato` | ITL |
| EM3 Italiani acquisiti nati in Italia | `naturalizzato_g2` | ITL |
| EM4 Italiani acquisiti nati all'estero | `naturalizzato_immigrato` | ITL |
| EM5 Stranieri e apolidi nati in Italia | `straniero_g2` | FRG |
| EM6 Stranieri e apolidi nati all'estero | `straniero_immigrato` | FRG |

È la stessa dipendenza funzionale del blocco GC che rende riducibile la
catena Gibbs a K9C/K10C. Qui lavora a favore: `background` **subsume**
`cittadinanza` nella chiave di cella, e i pesi in `assegna_sezione` non
vanno moltiplicati — `quota_cit × quota_em` conterebbe due volte la
stessa informazione — ma **normalizzati dentro il gruppo**.

Per la stessa ragione la misura si fa **sui due gruppi separatamente**.

---

## 3. Il disegno della misura

    M-EMa   TVD( P(EM | zona),    P(EM | comune) )     comune -> zona
    M-EMb   TVD( P(EM | sezione), P(EM | zona)   )     zona   -> sezione

Script: `scripts/diagnostica/residuo.py` (modulo), `misura_em.py`,
`misura_composizioni.py`, `misura_assorbimento.py`,
`placebo_assorbimento.py`.
Uscite in `note/misure/`, datate 20260809.

**Il pavimento è un bootstrap parametrico dello stimatore.** I dati sono
conteggi per sezione: il nullo è «ogni sezione estrae i suoi *n*
individui dalla composizione del suo gruppo», a *n* fissato. Ogni replica
simula **tutte** le sezioni e riapplica lo stesso stimatore, base
leave-one-out compresa — sotto il nullo anche la base è aleatoria, e
simulare la sola sezione contro una base osservata darebbe un pavimento
sbagliato.

**La base è leave-one-out**: `base(u) = totale del gruppo − conteggi di u`.
Il perché, e cosa costava non farlo, in §7.2.

**Le sezioni sotto `min_n` entrano nella base ma non nella media.** La
composizione di riferimento va stimata su tutta l'informazione
disponibile; il residuo si misura solo dove è misurabile. Stessa regola
nell'osservato e nel simulato.

**La guardia sui supporti è aggirata deliberatamente.** `T.composizione`
scarta le modalità a zero e `T.tvd` rifiuta supporti diversi: giusto
quando le modalità assenti segnalano una classificazione diversa. Qui il
supporto è noto a priori — quattro o due campi censuari fissi — e uno
zero è un conteggio nullo, non una modalità assente.

**Come si legge un netto.** È quota di massa da spostare oltre quella che
sposterebbe il caso: 0,02 significa che conoscere la sezione anziché la
sola zona corregge ~2 individui su 100.

**I terzili sono il test contro la rarefazione.** Il pavimento cresce al
calare di *n*; se il netto fosse rarefazione mal compensata svanirebbe
nelle sezioni grandi. Se sopravvive lì, è reale.

---

## 4. Risultati

Soglie: `MIN_N=30` individui del gruppo per sezione, `MIN_ZONA=200` per
zona, 50 repliche.

### 4.1 Netto M-EMb (zona → sezione), undici comuni

> **I numeri di questa tabella sono conservativi.** Sono stati calcolati
> prima delle due correzioni di §7.2 (base leave-one-out, pavimento
> bootstrap), che sui due comuni rimisurati li alzano di **~8%**:
> Parma da +0,0234 a +0,0252, Bologna da +0,0179 a +0,0193. Il verso è
> sempre lo stesso e nessun ordinamento cambia. Da rifare tutti quando
> gli script dipenderanno da `residuo.py` (§8.1).

| comune | zone | ITL M-EMa | ITL M-EMb | FRG M-EMa | FRG M-EMb |
|---|---:|---:|---:|---:|---:|
| Piacenza | 4 | +0,0227 | **+0,0420** | +0,0153 | +0,0110 |
| Brescia | 33 | +0,0285 | **+0,0363** | +0,0104 | +0,0103 |
| Reggio nell'Emilia | 4 | +0,0105 | +0,0312 | +0,0087 | +0,0170 |
| Modena | 4 | +0,0132 | +0,0255 | +0,0092 | +0,0183 |
| Ravenna | 10 | +0,0145 | +0,0247 | +0,0108 | **+0,0338** |
| Bologna | 18 | +0,0146 | +0,0217 | +0,0205 | +0,0181 |
| Parma | 13 | +0,0119 | +0,0200 | +0,0180 | +0,0232 |
| Forlì | 21 | +0,0186 | +0,0178 | +0,0046 | +0,0102 |
| Rimini | 6 | +0,0085 | +0,0164 | +0,0085 | +0,0226 |
| *Ferrara* | *1* | *n/d* | *+0,0146* | *n/d* | *+0,0222* |
| *Castenaso* | *1* | *n/d* | *+0,0120* | *n/d* | *n.m.* |

**Ventidue netti su ventidue sono positivi.** Non esiste un comune, né un
gruppo, in cui la sezione non aggiunga nulla oltre la zona.

Mediane sui nove comuni articolati: **ITL +0,0247**, **FRG +0,0181**.

Coerente con `nota_segnale_compositivo_v3`, che con uno stimatore
indipendente (informazione mutua corretta per il bias) misura che la
zonizzazione trattiene solo il 2–22% del segnale compositivo disponibile
alla sezione. Vedi §6.2.

### 4.2 Tre avvertenze sulla tabella

**(a) Ferrara e Castenaso non sono confrontabili con gli altri nove.**
Hanno una zona sola, quindi la base di M-EMb è il *comune*: misurano
comune→sezione, cioè ciò che altrove è M-EMa **più** M-EMb. Dovrebbero
perciò essere sistematicamente più alti, e invece stanno in fondo alla
classifica ITL. In corsivo, da leggere a parte.

**(b) Castenaso-FRG non è misurabile.** Sei sezioni, 79,7% di massa
esclusa, e l'osservata (0,0517) sta **sotto il p95 del pavimento**
(0,0687). L'avviso è ora in `residuo.py` e in `misura_composizioni.py`;
`misura_em.py` va allineato.

**(c) Il rapporto M-EMb/M-EMa non è confrontabile fra comuni.** M-EMa
dipende meccanicamente da quanto è grossolana la partizione: Modena ha 4
zone da 46.000 abitanti, Bologna 18, Brescia 33. Si legge solo **dentro**
un comune.

### 4.3 I terzili — la prova che il segnale è reale

Bologna, che è la mediana su entrambi i gruppi:

| gruppo | terzile | osservata | pavimento | netto |
|---|---|---:|---:|---:|
| ITL | grandi (>225) | 0,0387 | 0,0149 | **+0,0238** |
| | medie (106–225) | 0,0416 | 0,0217 | +0,0199 |
| | piccole (≤106) | 0,0492 | 0,0338 | +0,0154 |
| FRG | grandi (>67) | 0,0510 | 0,0277 | **+0,0233** |
| | medie (43–67) | 0,0546 | 0,0379 | +0,0167 |
| | piccole (≤43) | 0,0505 | 0,0450 | +0,0055 |

Su ITL il netto **cresce monotonicamente con l'ampiezza**: profilo
opposto alla rarefazione. Con l'1,7% di massa esclusa e 1.691 sezioni
misurate, il segnale è reale senza ambiguità.

Su FRG il netto globale (+0,0181) **sottostima** il segnale dove c'è:
nelle sezioni grandi vale +0,0233. Il 23,1% di massa esclusa è la
conseguenza della concentrazione: 705 sezioni su 2.223 contengono i tre
quarti della popolazione straniera.

### 4.4 Le due geografie non coincidono

Piacenza è prima su ITL e ottava su FRG; Brescia seconda su ITL e nona su
FRG; Ravenna quinta su ITL e **prima** su FRG. ITL è più alto in sette
comuni su undici.

Il background *generazionale* degli italiani — naturalizzati, rientrati —
e quello degli stranieri sono fenomeni geografici distinti.

Non c'è relazione monotona evidente fra numero di zone e M-EMb: Piacenza
(4) e Brescia (33) entrambe in cima su ITL, Forlì (21) e Rimini (6)
entrambe in fondo. *Osservazione, non misura.* Coerente con §10.4 di
`nota_segnale_compositivo_v3`, dove tre partizioni a quattro zone rendono
in modo radicalmente diverso.

---

## 5. Cosa fare in `enrich.py`

**Decisione: procedere, ma DOPO l'anello 4** (§8.7). Il guadagno lordo è
+0,018–0,025, l'assorbimento da parte di `area` è ~5–6% (§7.3), e per gli
italiani non esiste alcun condizionamento di sezione oggi. La modifica è
quindi giustificata; non è urgente.

La modifica è localizzata: due funzioni, ~15 righe.

**`load_sezioni`** (riga ~153): accanto a `q_{sesso}_{eta3}` si calcolano
le quote `EM` **normalizzate dentro il gruppo**:

```
qem_1..qem_4 = EM_b / (EM1+EM2+EM3+EM4)     italiani
qem_5, qem_6 = EM_b / (EM5+EM6)             stranieri
```

**`assegna_sezione`** (righe 228, 236–239): la chiave del `groupby` passa
da `["zona","sesso","eta","cittadinanza"]` a
`["zona","sesso","eta","background"]`, e il peso diventa

```python
w = base * quota_cit * qem[background]
```

`largest_remainder` e `spartisci` non cambiano: l'allocazione resta
esatta.

### 5.1 Il prezzo, da dichiarare

**`EM` non è incrociato per sesso ed età.** `ST17`–`ST33` danno gli
stranieri per sesso × età3; `EM1`–`EM6` sono sei totali di sezione. Il
raffinamento introduce quindi un'assunzione nuova: *la composizione per
background dentro il gruppo di cittadinanza è indipendente da sesso ed
età, data la sezione*.

**Le celle si moltiplicano**, da 2 cittadinanze a 6 background. Il
contatore `liv_uso` dirà quanto peggiora il fallback «solo demografico»:
è il primo numero da guardare dopo la modifica.

**Il guadagno resta modesto in valore assoluto**: ~2 individui su 100.

### 5.2 Come non perdere l'attuale

Un flag, con il default che riproduce esattamente oggi:

```python
ap.add_argument("--background-sezione", action="store_true",
                help="raffina P(sezione) con EM1-EM6 (anello 3)")
```

Senza il flag l'output è **identico byte a byte**. È lo schema già usato
per `--no-tier`, e dà il test di regressione permanente.

```bash
python scripts/attributi/enrich.py 034027 --anno 2024 --out /tmp/base.csv
# ... modifica ...
python scripts/attributi/enrich.py 034027 --anno 2024 --out /tmp/dopo.csv
cmp /tmp/base.csv /tmp/dopo.csv && echo identico
```

---

## 6. Previsioni: una falsificata, una ritirata

### 6.1 Falsificata — (a)

«Netto sostanziale su FRG, ~zero su ITL», perché con `EM1` al 93% del
gruppo le altre modalità sarebbero troppo rare per emergere sopra il
pavimento. Registrata nel docstring prima della misura.

*Falsificata su tutte e undici*: ITL è più alto in sette comuni su
undici, mediane 0,0247 contro 0,0181.

Lettura post-hoc, **non verificata**: proprio perché `EM1` domina,
naturalizzati e italiani rientrati sono fortemente concentrati dove
stanno i migranti di prima generazione.

### 6.2 Ritirata — (b), e con essa la «regola di calibrazione»

> **Ritrattazione (v2, confermata).** La v1 registrava come previsione:
> «netto piccolo su entrambi, perché `nota_segnale_compositivo_v3` misura
> che sotto il quartiere si perde l'85–98% del segnale compositivo», e la
> dichiarava falsificata.
>
> **La parafrasi era sbagliata, nel verso opposto.** Quella nota misura
> che la zonizzazione *trattiene* il 2–22% del segnale compositivo, e che
> **il 78–98% sta sotto il quartiere** (§1). È la giustificazione
> dell'esistenza dell'anello 3, non un argomento contro la struttura
> fine.
>
> La previsione (b) veniva da un errore di lettura, non da quella nota, e
> non è stata «falsificata»: era mal posta. **Le due note concordano**, e
> M-EM è una conferma con uno stimatore indipendente.

Conteggio corretto: **due previsioni falsificate su due** (M3′ e M4), non
tre su tre. Con due osservazioni è un'indicazione, non una regola: il
riquadro della v1 resta ritirato.

---

## 7. Quanto di questo segnale la pipeline già cattura

`nota_segnale_compositivo_v3` §2 misura la composizione degli stranieri
per **area di cittadinanza**, dalle colonne `ST17`/`ST18` (UE) e
`ST20`/`ST21` (extra-UE). Sono le stesse colonne che `enrich.py` usa in
anello 2 per assegnare `area`, **alla sezione**. L'assunzione (8) esclude
`background`, `istruzione` e `condizione`, ma non `area`.

Da qui la domanda: se `area` è già condizionata per sezione, quanto del
segnale di `EM` è già catturato?

### 7.1 Le due composizioni a confronto

`misura_composizioni.py` mette a confronto le due partizioni binarie
della **stessa** popolazione, sulle **stesse** sezioni, con lo **stesso**
stimatore:

| | Parma | Bologna |
|---|---:|---:|
| **A** stranieri: g2 / immigrati (`EM5`,`EM6`) | +0,0234 | +0,0179 |
| **B** stranieri: UE / extra-UE (`ST`) | **+0,0395** | **+0,0372** |
| **C** italiani: nativi / altri | +0,0212 | +0,0230 |

Il residuo più forte è su una composizione che la pipeline **condiziona
già** per sezione. Non è un buco: è la giustificazione a posteriori di
una scelta di disegno, e una convergenza in più fra metriche indipendenti
su questo tema.

### 7.2 Due difetti dello stimatore, trovati inseguendo l'assorbimento

**(i) La sezione stava dentro la propria base.**
`basi = s.groupby(gruppo).sum()` include la sezione, che con ~29 sezioni
per zona pesa ~1/29 della base verso cui è confrontata. Due conseguenze:
i netti sono **sottostimati**, e — più grave — **stratificare abbassa il
netto anche senza spiegare nulla**, perché dividendo la zona in tre
strati il peso della sezione nella propria base triplica.

Corretto con `base(u) = totale del gruppo − conteggi di u` in
`residuo.py`. Effetto misurato: **+4,1% a Parma, +3,1% a Bologna**.

**(ii) Il pavimento simulava la sola sezione** contro una base osservata,
mentre sotto il nullo anche la base è aleatoria. Corretto con un
bootstrap parametrico dell'intero stimatore. Effetto congiunto con (i):
**~+8%** sui netti (Parma 0,0234 → 0,0252, Bologna 0,0179 → 0,0193).

Entrambi gli errori erano **conservativi**: nessuna conclusione cambia.

### 7.3 L'assorbimento, misurato tre volte

Metodo: stratificare le sezioni per terzile di `q_B` (quota UE) dentro la
zona, e vedere di quanto cala il residuo di A. Il confronto è con un
**placebo**: stessa procedura con strati assegnati a caso, dieci semi.

| | base con la sezione | base leave-one-out |
|---|---|---|
| caduta per `q_B` | 10,7% · 10,2% | **2,5% · 1,8%** |
| caduta per terzile di *n* | 6,0% · 6,0% | 4,5% · 5,2% |
| caduta placebo casuale | 8,4% · 5,7% | **−3,7% · −3,2%** |
| **eccesso `q_B` sul placebo** | +2,3 · +4,5 | **+6,1 · +5,0** |

*(Parma · Bologna)*

**La correzione ha ribaltato il verso.** Con la vecchia base l'eccesso era
maggiore a Bologna, che ha un quarto dell'associazione di Parma
(r di zona +0,118 contro +0,467) — incoerente. Con la base LOO l'eccesso
è maggiore a Parma, **come deve essere se misura assorbimento reale**.

> **Stima: l'assorbimento vale ~5–6% del segnale di A.** Su Parma porta
> il guadagno da +0,0252 a ~+0,0238. **Irrilevante per la decisione**, che
> non è mai stata in bilico: tre versioni dello strumento hanno dato 10%,
> «non misurabile» e 5–6%, e in tutte e tre il raffinamento conserva la
> gran parte del suo valore.

**Il placebo non è centrato su zero**, ed è il limite dichiarato di
questa stima: −3,7% e −3,2%, negativo in tutte e venti le repliche.
Ipotesi non verificata: con la base LOO, stratificando si riduce di un
terzo il numero di sezioni nella base, che diventa più **rumorosa**;
osservata e pavimento crescono entrambi, ma non della stessa quantità,
perché nell'osservata la variabilità della base contiene anche struttura
reale. Sarebbe un artefatto della *dimensione* della base, non della sua
composizione.

Per questo l'**eccesso sul placebo** è l'unica quantità riportata: è per
costruzione robusto a qualunque artefatto che dipenda solo da numero e
dimensione degli strati. Il valore assoluto delle cadute no.

### 7.4 Perché `C` non ha questo problema

Per la scissione generazionale degli **italiani** — nativi contro
naturalizzati e rientrati — non esiste alcun condizionamento di sezione
nella pipeline. Il +0,0212 e +0,0230 misurati sono guadagno pulito,
senza assorbimento da stimare. È anche notevole quanto siano stabili fra
due città diverse, mentre A e B variano molto di più.

### 7.5 E alla scala fine le due composizioni sono indipendenti

Correlazione fra le quote `EM5/(EM5+EM6)` e `UE/(UE+extraUE)`:

| | Parma | Bologna |
|---|---:|---:|
| fra **zone** (Pearson / Spearman) | +0,467 / +0,291 | +0,118 / +0,131 |
| fra **sezioni** (n ≥ 30) | −0,066 / −0,051 | +0,024 / +0,030 |

*Nessuna delle correlazioni di zona è distinguibile da zero*: 13 e 18
unità. A Parma lo scarto fra Pearson e Spearman indica che una o due zone
fanno leva, e il valore robusto è il secondo.

Alla scala della **sezione** le due composizioni sono scorrelate, su 378
e 705 unità. Nascere in Italia e avere cittadinanza UE si accompagnano
fra quartieri — probabilmente perché entrambi correlano con l'anzianità
dell'insediamento — e non si accompagnano più fra isolati.

È l'argomento sostanziale a favore del raffinamento: `EM` porta
informazione **ortogonale** a quella che la pipeline già usa, esattamente
alla scala a cui la pipeline lavora.

---

## 8. Punti aperti

**8.1 Far dipendere i tre script da `residuo.py`.** `misura_em.py`,
`misura_composizioni.py` e `misura_assorbimento.py` contengono tre copie
dello stimatore difettoso. Poi rifare la tabella §4.1 con i valori
corretti (~+8%).

**8.2 Il placebo non centrato** (§7.3). Aperto come questione di metodo,
non come ostacolo: l'eccesso è robusto. Materiale per il paper TVD.

**8.3 La patch al registro** delle fonti: `usabile_per` e `universo` di
`istat_sezioni_2023` (§1).

**8.4 `EM` per sesso ed età non esiste** nel file regionale. Verificare
su IstatData prima di rassegnarsi all'assunzione di §5.1.

**8.5 Ferrara e Castenaso** hanno una zona sola: `enrich.py` fa già
ricadere tutto il condizionamento sulla sezione, e il raffinamento `EM` è
potenzialmente più utile che altrove. Ma la misura non è confrontabile e
su Castenaso-FRG non è calcolabile.

**8.6 La trappola sui confronti 2021↔2023**: ~400.000 famiglie
riallocate per un cambio di procedura di geocodifica. Le differenze per
sezione fra le due annate non sono tutte demografiche.

**8.7 Priorità rispetto all'anello 4.** Il residuo `EM` (+0,022 lordo,
~+0,021 netto) è circa metà di quello sull'ampiezza del nucleo (+0,049).
Ma tocca un attributo **già in produzione** e un limite già dichiarato
nel riferimento v22 e nelle classi di garanzia del viewer, con una
modifica a codice esistente invece che un modulo nuovo.

> **Decisione: la patch a `enrich.py` si fa dopo l'anello 4.**
>
> Il guadagno atteso è ~2 individui su 100 ricollocati, su un attributo
> che non blocca nulla, al costo di un ciclo di rigenerazione su undici
> comuni. L'anello 4 rimuove invece un limite dichiarato — l'assunzione
> (11), «nessuna struttura familiare» — e abilita l'assegnazione a
> edificio, la comunicazione familiare in SimComm e l'uso di EU-SILC.
>
> Nota sul percorso: `EM` è emerso guardando la colonna accanto a
> `PF3`–`PF8` mentre si cercava il vincolo per l'assemblaggio dei nuclei,
> non perché servisse alle famiglie. Il collegamento con l'obiettivo è
> debole e indiretto (coniugi con background simile), e va detto. Il
> guadagno reale di questa deviazione è **metodologico**: `residuo.py`
> corregge un difetto che affligge anche M4 (§8.1 di
> `nota_nucleo_familiare_v3`), e quella misura serve alle famiglie.

---

## 9. Per il paper sul criterio TVD

Questa linea di lavoro ha prodotto tre elementi metodologici
riutilizzabili, tutti sul tema «una TVD non si legge senza il suo nullo»:

**(1) Il pavimento come parte dello stimatore, non come controllo
opzionale.** Con modalità all'1,3% e sezioni da ~150 persone, la TVD
osservata è quasi tutta rarefazione: il pavimento non corregge il numero,
lo *costituisce*.

**(2) La base leave-one-out.** Quando l'unità misurata fa parte del
proprio riferimento, raffinare la partizione abbassa la distanza senza
spiegare nulla. È un artefatto silenzioso che sopravvive al pavimento,
perché il pavimento simula la stessa configurazione. Il segno diagnostico
che l'ha rivelato: una stratificazione **casuale** costava più di una per
dimensione, e con variabilità molto maggiore.

**(3) L'eccesso sul placebo come stimatore robusto.** Quando l'artefatto
dipende solo da numero e dimensione degli strati, la differenza fra
caduta osservata e caduta con strati casuali lo elimina senza doverlo
modellare.

Vale anche come vignetta sul processo: **tre giri di raffinamento dello
strumento** — 10%, «non misurabile», 5–6% — e una decisione che non è mai
cambiata. Il valore dei tre giri non è stato correggere la decisione ma
capire cosa misurava lo strumento.

*§9 è scritta senza aver riletto `paper_criterio_scheletro_v1.md`: da
allineare alle sezioni esistenti.*
