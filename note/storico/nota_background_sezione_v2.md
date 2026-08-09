# Background migratorio per sezione — misura M-EM e anello 3

**Versione 2.0 — 9 agosto 2026**
Mirko Degli Esposti · DIFA, Università di Bologna

I campi `EM1`–`EM6` del censimento permanente 2023 danno il background
migratorio in sei modalità **per sezione di censimento**, con
corrispondenza uno a uno con l'attributo `background` di anello 1. Oggi
quell'attributo ha risoluzione di **zona**, per l'assunzione (8).

Questa nota misura se scendere alla sezione porti informazione reale, e
decide cosa farne in `enrich.py`.

Risposta breve: **sì**, su tutte e undici le città e su entrambi i gruppi
di cittadinanza, con netto mediano ~0,022 (italiani) e ~0,018
(stranieri). Ma il guadagno **netto** rispetto a quanto la pipeline già
cattura resta da misurare (§7.1).

*Changelog v2.0 — sostituisce la v1, tre correzioni di sostanza:*
1. *La «previsione (b) falsificata» della v1 era basata su una **lettura
   errata** di `nota_segnale_compositivo_v3`. Ritirata: le due note
   concordano (§6.2).*
2. *Il conteggio «tre previsioni falsificate su tre» scende a **due**, e
   il riquadro che ne faceva una regola di calibrazione è ridimensionato.*
3. *Aggiunta §7: la composizione UE/extra-UE che la pipeline **già**
   condiziona per sezione mostra un residuo maggiore di quella misurata
   qui, il che ridimensiona il guadagno atteso del raffinamento.*

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

Script: `scripts/diagnostica/misura_em.py`,
`scripts/diagnostica/misura_composizioni.py`.
Uscite: `note/misure/tvd_em_undici_20260809.txt`,
`note/misure/tvd_composizioni_20260809.txt`.

**Il pavimento è multinomiale, non permutazionale.** M3 e M4 lavoravano
su microdati e il nullo giusto era la permutazione delle etichette. Qui i
dati sono conteggi per sezione: il nullo è «ogni sezione estrae i suoi
*n* individui dalla composizione della sua zona», a *n* fissato. Con
modalità all'1,3% e sezioni da ~150 persone la TVD osservata è quasi
tutta rarefazione.

È lo stesso problema che `nota_segnale_compositivo_v3` §3–§4 risolve con
un nullo costruito ad hoc per l'informazione mutua. Stimatori diversi,
stessa necessità.

**La guardia sui supporti è aggirata deliberatamente.** `T.composizione`
scarta le modalità a zero e `T.tvd` rifiuta supporti diversi: giusto
quando le modalità assenti segnalano una classificazione diversa. Qui il
supporto è noto a priori — quattro o due campi censuari fissi — e uno
zero è un conteggio nullo, non una modalità assente.

**Come si legge un netto.** È quota di massa da spostare oltre quella che
sposterebbe il caso: 0,02 significa che conoscere la sezione anziché la
sola zona corregge ~2 individui su 100.

**I terzili sono il test decisivo.** Il pavimento cresce al calare di
*n*; se il netto fosse rarefazione mal compensata svanirebbe nelle
sezioni grandi. Se sopravvive lì, è reale.

---

## 4. Risultati

Soglie: `MIN_N=30` individui del gruppo per sezione, `MIN_ZONA=200` per
zona, 50 permutazioni.

### 4.1 Netto M-EMb (zona → sezione), undici comuni

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

Il risultato è **coerente con** `nota_segnale_compositivo_v3`, che con
uno stimatore indipendente (informazione mutua corretta per il bias)
misura che la zonizzazione trattiene solo il 2–22% del segnale
compositivo disponibile alla sezione. Vedi §6.2.

### 4.2 Tre avvertenze sulla tabella

**(a) Ferrara e Castenaso non sono confrontabili con gli altri nove.**
Hanno una zona sola, quindi la base di M-EMb è il *comune*: misurano
comune→sezione, cioè ciò che altrove è M-EMa **più** M-EMb. Dovrebbero
perciò essere sistematicamente più alti, e invece stanno in fondo alla
classifica ITL. In corsivo, da leggere a parte.

**(b) Castenaso-FRG non è misurabile.** Sei sezioni, 79,7% di massa
esclusa, e l'osservata (0,0517) sta **sotto il p95 del pavimento**
(0,0687). *Corretto* in `misura_composizioni.py`, che stampa un avviso;
`misura_em.py` va allineato.

**(c) Il rapporto M-EMb/M-EMa non è confrontabile fra comuni.** M-EMa
dipende meccanicamente da quanto è grossolana la partizione: Modena ha 4
zone da 46.000 abitanti, Bologna 18, Brescia 33. Il rapporto si legge
solo **dentro** un comune.

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
entrambe in fondo. *Osservazione, non misura.* È coerente con §10.4 di
`nota_segnale_compositivo_v3`, dove tre partizioni a quattro zone rendono
in modo radicalmente diverso.

---

## 5. Cosa fare in `enrich.py`

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
contatore `liv_uso` dirà quanto peggiora il fallback «solo demografico».

**Il guadagno lordo è modesto**: ~2 individui su 100. Quello **netto**
è probabilmente inferiore — vedi §7.

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

> **Ritrattazione.** La v1 registrava come previsione: «netto piccolo su
> entrambi, perché `nota_segnale_compositivo_v3` misura che sotto il
> quartiere si perde l'85–98% del segnale compositivo», e la dichiarava
> falsificata.
>
> **La parafrasi era sbagliata, e nel verso opposto.** Quella nota
> misura che la zonizzazione *trattiene* il 2–22% del segnale
> compositivo disponibile alla sezione, e che **il 78–98% sta sotto il
> quartiere** (§1). È la giustificazione dell'esistenza dell'anello 3,
> non un argomento contro la struttura fine.
>
> La previsione (b) non veniva quindi da quella nota ma da un errore di
> lettura, e non è stata «falsificata»: era mal posta. **Le due note
> concordano**, e M-EM è una conferma con uno stimatore indipendente —
> TVD con pavimento multinomiale contro informazione mutua corretta per
> il bias — di un risultato già stabilito.

Di conseguenza il conteggio corretto è **due previsioni falsificate su
due** (M3′ e M4), non tre su tre. Resta un pattern nella stessa
direzione — struttura fine sottostimata — ma con due sole osservazioni è
un'indicazione, non una regola. La v1 ne faceva un riquadro: ritirato.

---

## 7. Quanto di questo segnale la pipeline già cattura

*Sezione nuova nella v2, ed è quella che ridimensiona la conclusione.*

`nota_segnale_compositivo_v3` §2 misura la composizione degli stranieri
per **area di cittadinanza**, dalle colonne `ST17`/`ST18` (UE) e
`ST20`/`ST21` (extra-UE). Sono le stesse colonne che `enrich.py` usa in
anello 2 per assegnare `area`, **alla sezione**. L'assunzione (8) esclude
`background`, `istruzione` e `condizione`, ma non `area`.

`misura_composizioni.py` mette a confronto le due partizioni binarie
della **stessa** popolazione, sulle **stesse** sezioni, con lo **stesso**
stimatore:

| | Parma | Bologna |
|---|---:|---:|
| **A** stranieri: g2 / immigrati (`EM5`,`EM6`) | +0,0234 | +0,0179 |
| **B** stranieri: UE / extra-UE (`ST`) | **+0,0395** | **+0,0372** |
| **C** italiani: nativi / altri | +0,0212 | +0,0230 |
| A/B | 0,59 | 0,48 |

Due conseguenze.

**(1) B è già catturata.** Il residuo più forte è su una composizione che
la pipeline condiziona già per sezione. Non è un buco: è la
giustificazione a posteriori di una scelta di disegno, e la sesta
convergenza fra metriche indipendenti su questo tema.

**(2) Il guadagno netto di A è incerto.** Se le due partizioni sono
correlate fra sezioni — plausibile, perché essere UE correla con essere
immigrato di prima generazione — parte del segnale di A è già assorbita
da `area`. Il guadagno reale del raffinamento `EM` sarebbe allora
sensibilmente sotto +0,018.

La domanda giusta non è quella misurata in §4 (`EM` contro la marginale
di zona) ma **`EM` condizionato su `area`, alla stessa sezione**.
L'incrocio `EM × area` per sezione non esiste nel file regionale; il
surrogato praticabile è la correlazione fra le quote
`EM5/(EM5+EM6)` e `UE/(UE+extraUE)` per sezione. **Da misurare prima di
toccare `enrich.py`** (§8.1).

`C` — gli italiani, +0,0212 e +0,0230 — **non ha questo problema**: non
esiste alcun condizionamento di sezione per la scissione generazionale
degli italiani. È la parte del risultato che regge senza riserve, ed è
notevole quanto sia stabile fra due città diverse.

---

## 8. Punti aperti

**8.1 La correlazione fra le quote A e B per sezione.** Decide se il
raffinamento `EM` valga la modifica. Dieci righe. **Prima di tutto il
resto.**

**8.2 L'avviso mancante in `misura_em.py`**: quando l'osservata sta sotto
il p95 del pavimento, stampare «non misurabile» invece del netto. Già
implementato in `misura_composizioni.py`.

**8.3 La patch al registro** delle fonti: `usabile_per` e `universo` di
`istat_sezioni_2023` (§1).

**8.4 `EM` per sesso ed età non esiste** nel file regionale. Verificare
su IstatData prima di rassegnarsi all'assunzione di §5.1.

**8.5 Ferrara e Castenaso** hanno una zona sola: `enrich.py` fa già
ricadere tutto il condizionamento sulla sezione, e il raffinamento `EM` è
potenzialmente più utile che altrove. Ma la misura non è confrontabile e
su Castenaso-FRG non è calcolabile.

**8.6 La trappola sui confronti 2021↔2023**: la nota metodologica ISTAT
avverte che ~400.000 famiglie sono state riallocate per un cambio di
procedura di geocodifica. Le differenze per sezione fra le due annate non
sono tutte demografiche.

**8.7 Priorità rispetto all'anello 4.** Il residuo `EM` (+0,022 lordo,
netto ignoto) è al più metà di quello sull'ampiezza del nucleo (+0,049,
netto). Ma tocca un attributo **già in produzione** e un limite già
dichiarato nel riferimento v22 e nelle classi di garanzia del viewer, con
una modifica a codice esistente. Resta una decisione, non una
conseguenza — e §7 la sposta verso l'anello 4.
