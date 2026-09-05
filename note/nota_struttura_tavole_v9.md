# Nota — struttura delle tavole ISTAT: anagrafe, censimento, dimensioni interne

**v9** — 5 settembre 2026. Ogni voce marcata **misurato**, **dedotto**
o **aperto**. Le ritrattazioni sono esplicite e conservate.

> **Modifiche v8 → v9.** §14 nuova: **l'anello 3** (`enrich.py`), dove
> vive l'assunzione (9), qui localizzata con precisione e delimitata.
> §14.3: la decomposizione della varianza su Parma — **11,4×** di
> struttura di sezione contro struttura di zona — che ribalta
> l'aspettativa sulla tabella sezioni/zona. §14.5: tabella
> sezioni-per-zona sui 12 comuni ER. Difetto #10 **declassato**: era
> già stato trovato e corretto in `assign_nationality.py`;
> `build_constraints` è l'unico posto rimasto con la versione vecchia.
> §8.2 nuova: *la correzione applicata a un ramo e non all'altro* —
> tre occorrenze, è un pattern.

> **Modifiche v7 → v8.** §12 nuova: **la convergenza dei due rami** in
> `cs_build`, con la catena di ancoraggio completa e la misura dello
> spostamento IPF — **esattamente l'identità** quando i rami sono
> allineati nell'anno (11 comuni), 0,10–0,18 % quando sono sfasati di
> uno. §10.2 **ritrattata** in parte: la pipeline *non* assume
> uniformità entro bin, usa la forma di C1 ad anno singolo; il
> meccanismo che avevo proposto per lo scarto 10/10 è sbagliato.
> §13 nuova: le zone dell'Emilia-Romagna, 12 comuni articolati su 330.

> **Modifiche v6 → v7.** §2.5 nuova: **l'exact match è esteso a tutta
> la flotta** — 102 212 celle su 253 comuni e due annate, zero
> discrepanti, differenza massima 0. §11.5 chiusa, con una ritrattazione
> di metodo: i `report.md` stampano il MAE arrotondato a un decimale,
> quindi «0.0» significava «< 0,05», non zero; il risultato regge solo
> perché ricalcolato dalle celle.

> **Modifiche v5 → v6.** §11 nuova: **la costruzione del constraint
> set**, letta dal sorgente. `apply_conditional` è l'architettura
> forma-non-livelli in tre righe; i regimi di ancoraggio sono **cinque**
> e il report ne descrive uno; `elementary_classes` implementa già per
> l'età il controllo generalizzabile invocato in §8; l'assunzione (9)
> **non entra** in `build_constraints` e la domanda si sposta a
> `build_sezioni`. Aperto nuovo, a costo quasi nullo: i 254 `report.md`
> contengono già il raccordo spina anagrafe ↔ censimento, mai aggregato.

> **Modifiche v4 → v5.** §2.4 nuova: exact match C1 ↔ C2 verificato
> **cella per cella** su Mantova (202 celle, zero discrepanti). §3ter
> nuova: struttura di C2, con tre totali annidati e copertura temporale
> non uniforme. §9 nuova: **il precursore dell'assunzione (9) è stato
> eseguito** — la forma entro bin quinquennale è *nazionale, non
> locale* (sd fra 253 comuni = 0,075 anni), ma l'ipotesi di uniformità
> entro bin sbaglia sistematicamente sopra i 75 anni. §10 nuova: le
> tre risoluzioni dell'età e il trade-off età/territorio.

> **Modifiche v3 → v4.** §4.4 nuova: `AREA_CONTRY_CITIZEN` è un albero
> a tre livelli, con i due livelli intermedi che **non** partizionano.
> Difetto #4 **chiuso e identificato**: `ZA` + `CF` = 4 individui a
> Brescia (× 2 per `GENDER` = gli 8 osservati). Difetto #10 nuovo e
> **reale**: il filtro degli aggregati in `build_constraints` fa
> substring matching sulle etichette ed elimina «Sud **Africa**» e
> «Centr**africa**na» — 700 individui sulla flotta.
>
> **Modifiche v2 → v3.** §5.3 chiusa con misura su tre comuni
> (Bologna, Brescia, Mantova): il collasso 7 → 4 interessa lo
> **0,13–0,26 %** della popolazione. §6 difetto #2 **declassato** da
> «silenzioso» a noto e innocuo: `REF_AREA` non è letto a valle, e il
> costo era già documentato in `fetch_prov.py`. §3bis nuova: struttura
> di C1 letta dal profilo di Mantova (sparsità, `AGE=TOTAL`).
>
> **Modifiche v1 → v2.** §5.1 **ritratta**: `edu_collapse` è una
> mappatura per etichetta, non una ripartizione — nessuna assunzione
> non dichiarata. §5.3 nuova: collasso dello stato civile 7 → 4.
> §6 aggiornato: difetto #1 chiuso (non applicabile), #5 rimosso,
> aggiunto C9/C10 marcati hard per residuo. §8 riscritta attorno a
> `istruzione.verifica()`, che implementava già il controllo giusto.
> Conteggio flotta fissato a **254**.

---

## 1. Anagrafe e censimento: cosa entra davvero nella pipeline

**dichiarato.** La distinzione va tenuta su due piani che nella sessione
sono stati confusi più volte:

- l'**anagrafe come registro** (APR comunale) contiene cittadinanza,
  famiglia anagrafica, indirizzo, luogo di nascita;
- l'**anagrafe come fonte GSP** entra con **una sola tavola**,
  `istat_anag_sesso_eta_statociv` (`22_289_DF_DCIS_POPRES1_26`):
  sesso × età per anno singolo × stato civile a sette modalità. È C1,
  l'unico blocco hard. **Cittadinanza e famiglia non ci sono.**

Le altre dieci tavole della rosa `CORE` sono censuarie.

**misurato.** `MARITAL_STATUS` è **dichiarato nel DSD censuario** ma
sempre collassato a una modalità in tutte e nove le tavole censuarie
profilate. Il censimento *potrebbe* portare lo stato civile e non lo
articola mai.

> **Conseguenza per il paper.** C1 non è la tavola anagrafica per
> convenzione: è l'**unica fonte esistente** per l'asse stato civile.
> La gerarchia hard/soft ha qui una giustificazione misurata, dove
> finora aveva un argomento.

---

## 2. L'identità registro–censimento si estende alla cittadinanza

### 2.1 `FJAN` non è un conteggio anagrafico

**misurato.** Nel dataflow `29_316` (bilancio stranieri) il codice
`DATA_TYPE = FJAN` è etichettato «popolazione **censita** straniera al
1° gennaio». Su Brescia (`017029`), `SEX = 9` (totale, verificato
additivo: 9 = 1 + 2 in tutte e sette le annate):

| anno | FJAN | FSTAT_ADJUST |
|---|---|---|
| 2019 | 36 067 | −807 |
| 2020 | 36 184 | +1 378 |
| 2021 | 37 720 | −1 829 |
| 2022 | 36 885 | +159 |
| 2023 | 36 613 | −367 |
| 2024 | **37 478** | −29 |
| 2025 | 38 228 | — |

`FJAN` 2024 = **37 478**, identico al valore censuario estratto da
`cens_sesso_eta_cittadinanza` (2023). L'allineamento temporale è quello
noto: censimento al 31 dicembre N−1 = anagrafe al 1° gennaio N.

**misurato.** Scarto **zero su tutti i comuni** iterati da
`gsp.common.COMUNI`.

*Nota sui conteggi*, per evitare l'ambiguità che la v1 aveva lasciato
aperta: **254** è il numero di comuni con `cens_istruzione_eta_decoded.csv`
a terra; **245** è la flotta Animarium v2. I nove in più sono comuni
acquisiti e non pubblicati. Tutte le verifiche di questa nota girano
sui 254.

### 2.2 Ritrattazione

> **Ritratto**: «la correzione di copertura ISTAT sugli stranieri è
> nulla». Era una lettura sbagliata. Zero differenze non è una
> correzione nulla: è un'**identità di costruzione**. Le due grandezze
> che credevo di confrontare sono lo stesso numero ripubblicato in due
> famiglie di dataflow.
>
> **Formulazione corretta**: l'ISTAT non pubblica un conteggio
> anagrafico grezzo degli stranieri. Lo stock al 1° gennaio è ancorato
> al censimento; `FSTAT_ADJUST` è la posta che fa quadrare i flussi
> amministrativi *contro* quello stock — oscilla di segno, media
> ~−250/anno, e non è una stima di sovracopertura.
>
> Il ~7 % di Brescia (40 090 APR comunale contro 37 478) resta
> attribuito interamente all'APR comunale, ma **per assenza di
> alternative**, non perché l'altra componente sia stata misurata e
> trovata nulla. Conclusione più debole di quella annunciata in seduta.

### 2.3 `29_317` è lo stesso dato di `cens_stranieri_paesi`

**misurato.** Chiavi ISO-2 identiche, ordinamento dei paesi identico,
totale `WORLD` = `FJAN`. Confronto con `nationality_conditional.csv`
(Brescia): somma `count` = 74 948 contro 2 × 37 478 = 74 956.

- `share_frg` somma a 1 (0,999999999999995);
- `count/share` costante a 74 948 su tutte e 143 le righe.

**aperto.** Lo scarto di **8 unità** (1 su 10 000) non è arrotondamento.
Due spiegazioni plausibili: individui con paese non allocabile che le
143 righe non raccolgono, oppure `SEX = 3` («non indicato») che entra da
un lato e non dall'altro. Non verificato.

**dichiarato.** `29_317` non aggiunge né contenuto né copertura:
`cens_stranieri_paesi` è già nella rosa `CORE` e scaricata per tutta la
flotta. Il ramo si chiude senza modifiche al pipeline. Le fonti locali
restano necessarie solo per il **sub-comunale**, che era già la
conclusione di agosto.

---

### 2.4 Exact match C1 ↔ C2, cella per cella

**misurato** (Mantova `020030`, anagrafe 1 gen 2025 contro censimento
31 dic 2024 — stesso istante).

C1 sommata sullo stato civile, C2 con `CITIZENSHIP = TOTAL`, entrambe
su sesso × età per anno singolo:

```
celle confrontate      : 202
presenti in entrambe   : 202
discrepanti            : 0
|differenza| massima   : 0
somma C1 = somma C2    : 49 607
```

Non è un confronto di totali: è **cella per cella**. Mantova si
aggiunge ai quattordici comuni dove l'identità era già misurata.

**La geometria che ne esce.** C1 e C2 non sono fonti concorrenti da
riconciliare: sono **due estensioni ortogonali della stessa spina**.

| | C1 (anagrafe) | C2 (censimento) |
|---|---|---|
| spina | sesso × 101 età singole | sesso × 101 età singole |
| terzo asse | **stato civile** (7) | **cittadinanza** (2) |
| data | 1 gen 2025 | 31 dic 2024 |

> **Perché conta per il paper.** Il MaxEnt non deve mediare fra misure
> discordi: deve ricomporre **proiezioni diverse di un oggetto solo**.
> E dà la ragione *strutturale* — non convenzionale — per cui C1 è
> l'unico hard: porta la spina a piena risoluzione **e** l'unico asse
> che nessun'altra tavola ha (§1). Vincolarla esattamente non toglie
> nulla alle altre, perché sulla spina le altre dicono la stessa cosa.

### 2.5 L'identità sulla spina, su tutta la flotta

**misurato**, per ricalcolo diretto dai `_decoded.csv` (non dai
`report.md` — vedi §11.5). C1 sommata sullo stato civile contro C2 con
`CITIZENSHIP ∈ {ITL, FRGAPO}`, su sesso × età per anno singolo,
ancoraggi 2024 e 2025:

```
confronti (comune x anno)  :     506
comuni                     :     253
celle confrontate          : 102 212
celle discrepanti          :       0
|differenza| massima       :       0
run con valori non interi  :       0
```

**Zero non è un arrotondamento**: la differenza massima su centomila
celle è esattamente nulla, e nessun valore censuario ha parte
decimale — la nota v1 di `build_constraints` su «stime SDMX non
arrotondate, internamente additive» **non si applica a queste due
tavole**.

> **Formulazione per il paper.** *L'identità fra spina anagrafica e
> spina censuaria è verificata su 102 212 celle in 253 comuni e due
> ancoraggi, con differenza esattamente nulla in ogni cella.* Sostituisce
> la formulazione precedente, limitata a quattordici comuni.
>
> Non è una coincidenza da spiegare, è una **conseguenza di
> costruzione**: entrambe le fonti derivano dal Registro Base degli
> Individui. Il valore della misura non è la scoperta, è la
> **verificabilità sistematica** su tutta la flotta.

---

## 3. Il disegno delle tavole censuarie

**misurato** (matrice B, `/tmp/mappa_dsd_B.csv`, Brescia): modalità
effettive per dimensione. `–` = dimensione assente dal DSD;
`1` = presente ma collassata.

| tavola | AGE_NOCL | AGE_CL | CITIZ | AREA_CC | EDU | CUR_ACT | EMPL_ST | BRANCH | INDIC | PL_BIRTH |
|---|---|---|---|---|---|---|---|---|---|---|
| sesso_eta_cittadinanza | **102** | – | 3 | 1 | – | – | – | – | 1 | – |
| istruzione_eta | 5 | – | 1 | – | **11** | 1 | – | – | 1 | – |
| istruzione_cittadinanza | 1 | – | **3** | – | **7** | 1 | – | – | 1 | – |
| condprof_eta | 5 | – | 1 | – | 1 | **9** | – | – | 1 | – |
| condprof_cittadinanza | 1 | – | **3** | – | 1 | **9** | – | – | 1 | – |
| stranieri_paesi | – | 1 | 1 | **169** | – | – | – | – | 1 | – |
| migr_backg | – | 1 | 1 | – | 1 | – | – | – | **11** | 5 |
| posizione_prof | – | 1 | – | – | – | – | **3** | 1 | 1 | – |
| settore_prof | – | 1 | – | – | – | – | 1 | **7** | 1 | – |

`GENDER = 3` ovunque (F, M, T).

**Le dieci tavole sono una tavola parametrizzata.** Le quattro
`DF_DCSS_ISTR_LAV_PEN_2_TV_*` condividono il DSD e realizzano un **2×2
esatto**: {istruzione, condizione} × {età, cittadinanza}. Una variabile
di contenuto e una di incrocio accese, le altre due collassate. Stessa
struttura per la coppia lavoro: `posizione_prof` accende
`EMPLOYMENT_STATUS` e spegne `BRANCH`, `settore_prof` fa l'opposto.

**Due dimensioni d'età convivono e non si incontrano mai.**
`AGE_NOCLASS` in cinque tavole, `AGE_CLASS` nelle altre quattro. Unire
tavole di famiglie diverse richiede di riconciliare due codelist.

**chiuso, non è un difetto.** `cens_posizione_famiglia` è presente in
**11 comuni su 254** — il gruppo originario — e assente altrove. Non è
una lacuna di acquisizione: **l'anello 4 ricostruisce i nuclei per
altra via** e la tavola non entra nel constraint set. La riga manca
dalla matrice, e con essa le colonne `HOUSEHOLD_TYPE`,
`FAMILY_NUCLEI_TYPE`, `NUM_MEMB`; la matrice DSD va quindi letta come
riferita alle **nove** tavole censuarie effettivamente consumate.

---

## 3bis. La struttura di C1, letta dal profilo

**misurato** (`anag_sesso_eta_statociv_profile.csv`, Mantova `020030`,
8 568 righe di dati).

| dimensione | status | modalità |
|---|---|---|
| `FREQ`, `REF_AREA`, `DATA_TYPE` | FISSA | 1 |
| `SEX` | VARIA | 2 — vincolata in `spec` a `["1","2"]` |
| `AGE` | VARIA | **102** — 101 anni singoli (`Y0`…`Y99`, `Y_GE100`) **+ `TOTAL`** |
| `MARITAL_STATUS` | VARIA | 7 — vincolata in `spec` alle elementari |
| `TIME_PERIOD` | VARIA | 7 (2019–2025) |

**`TOTAL` sta dentro `AGE`.** Mantova 2024: `AGE=TOTAL` → 49 044;
somma degli anni singoli → 49 044; somma di tutto → **98 088**. È lo
stesso fattore 2 di `GENDER` in §4, su un'altra dimensione. Qui `SEX` e
`MARITAL_STATUS` non lo portano perché la `spec` in `CORE` li vincola
esplicitamente alle modalità elementari: **un asse blindato nella
query, uno lasciato in wildcard**.

**La sparsità è strutturale**, non dato mancante (Mantova 2024, maschi):

| stato civile | età presenti | età minima |
|---|---|---|
| nubile/celibe | 101 | 0 |
| coniugato, divorziato, vedovo | 85 | 16 |
| unione civile (15, 16, 17) | 83 | 18 |

L'ISTAT non pubblica celle impossibili: nessun coniugato sotto i 16
anni, nessuna unione civile sotto i 18. Sono **zeri strutturali della
fonte** — parenti diretti delle esclusioni α = 0 previste per
eta × istruzione e eta × condizione.

**Sui tre file prodotti da `fetch_comune`**, per il lettore del report:

- `_raw.csv` — la risposta SDMX-CSV. Sette colonne utili
  (`REF_AREA, DATA_TYPE, SEX, AGE, MARITAL_STATUS, TIME_PERIOD,
  OBS_VALUE`); le altre dodici (`NOTE_*`, `OBS_STATUS`, `BASE_PER`,
  `UNIT_MEAS`, `UNIT_MULT`) sono vuote o costanti.
  `NOTE_REF_AREA = FILTER__ITC4` è la traccia del filtro lato server.
- `_decoded.csv` — le stesse righe più sei colonne `_label` da
  `sdmx.decode`. Nessun dato nuovo, solo leggibilità.
- `_profile.csv` — 122 righe di metadati, una per (dimensione, codice),
  con `status`, `n_distinct` e conteggio righe. **È l'unico dei tre che
  si legge per capire la tavola** invece che per usarla.

---

## 3ter. La struttura di C2

**misurato** (`cens_sesso_eta_cittadinanza`, Mantova, 3 623 righe).

**Tre totali annidati, tutti additivi** — `AGE_NOCLASS = TOTAL`,
`GENDER = T`, `CITIZENSHIP = TOTAL`. Mantova 2024, anni singoli:

| | F | M | T |
|---|---|---|---|
| ITL | 21 601 | 19 584 | 41 185 |
| FRGAPO | 4 275 | 4 147 | 8 422 |
| TOTAL | 25 876 | 23 731 | **49 607** |

Sommare in wildcard dà **8×**, non 2×. È la tavola con più totali
sovrapposti incontrata finora, e **nessuno dei tre è vincolato dalla
`spec`**: in `CORE` tutte le censuarie hanno `"spec": {}`. Se
`build_constraints` non seleziona esplicitamente, moltiplica per otto.

**La copertura temporale non è uniforme:**

| anni | righe | contenuto |
|---|---|---|
| 2018–2020 | 15 | solo `AGE=TOTAL` più `Y_GE100` |
| 2021–2024 | ~890 | età per anno singolo |

**Il dettaglio per anno singolo esiste solo dal 2021.** Le prime tre
annate portano il totale e — curiosamente — i soli centenari.

> **aperto, e non banale.** Il `preflight` di `build_constraints` v2
> verifica la **presenza** della tavola per l'anno richiesto, non la
> **profondità** della sua articolazione. Una tavola può passare il
> preflight ed essere inutilizzabile per quell'anno. Da verificare se
> il buco 2018–2020 sia uniforme sulla flotta o dipenda dalla taglia.

**Sparsità di natura diversa da C1.** In C2 la sparsità colpisce solo
gli stranieri: 101 età per gli italiani, **94/90** per gli stranieri.
Sono **zeri empirici** (nessun residente straniero a quelle età), non
strutturali come le età minime di C1 (§3bis) — spariranno su un comune
più grande.

---

## 4. `EDU_ATTAIN`: due strutture sovrapposte

Il punto su cui la sessione ha sbagliato due volte prima di arrivarci.

### 4.1 Il fatto

**misurato** (`cens_istruzione_eta`, Brescia 2023, presenza per cella):

| EDU_ATTAIN | Y9-24 | Y25-49 | Y50-64 | Y_GE65 | Y_GE9 |
|---|---|---|---|---|---|
| ALL, BL, LSE, ML_RDD, NED, PSE, USE_IF | 3 | 3 | 3 | 3 | 3 |
| **IL, LBNA, ML, RDD** | 0 | 0 | 0 | 0 | **3** |

Le quattro modalità fini **esistono solo sul totale d'età** `Y_GE9`.

**misurato**, chiusure su `GENDER = T`, `AGE = Y_GE9`:

```
somma sei foglie (USE_IF, LSE, ML_RDD, PSE, BL, NED) = 184 715 = ALL
ML + RDD  = 31 602 = ML_RDD
IL + LBNA =  6 872 = NED
```

Sei foglie partizionano; quattro figli stanno sotto due di esse; padri e
figli **coesistono nella stessa cella** di `Y_GE9`.

**misurato**, chiusura `somma sei − ALL = 0` su **254 comuni su 254**,
con lo stesso insieme di undici codici ovunque: nessuna soppressione per
riservatezza.

**misurato**, `GENDER`: `T = F + M` esattamente, su tutte le classi
d'età testate, su una foglia pura (`USE_IF`).

### 4.2 Ritrattazione

> **Ritratto**: «il fattore 2 non era `GENDER`, era l'albero interno
> alla dimensione». **Sbagliato.** Il fattore 2 *è* `GENDER`, come
> ipotizzato in origine.
>
> L'errore diagnostico: avevo cercato l'albero sommando tutte le classi
> d'età insieme. In quell'aggregato i due livelli si mescolano, e il
> residuo `−(ML+RDD)` che leggevo veniva dal confronto fra popolazioni
> di celle diverse — non da un padre che contiene i figli.
>
> **Le due strutture sono compatibili, su assi diversi**: `GENDER` ha un
> totale additivo; `EDU_ATTAIN` ha un albero a due livelli, ma solo su
> `Y_GE9`. Sommando in wildcard su entrambi il fattore non è né 2 né 4:
> dipende dalla cella.
>
> **Secondo errore, nello stesso passaggio**: avevo attribuito
> `AGE_NOCLASS = 102` a `cens_istruzione_eta`. Il 102 (anno singolo) è
> di `cens_sesso_eta_cittadinanza`; `cens_istruzione_eta` ha **cinque**
> modalità, quattro classi larghe più il totale. Riga sbagliata della
> matrice.
>
> **Terzo, minore**: «sette foglie che partizionano» → sono **sei**.
> `ALL` è il totale, non una foglia.

### 4.3 Il ritorno su `nationality_conditional`

Con la chiave corretta, la diagnosi di §2.3 **regge**: 74 948 ≈ 2 ×
37 478 è il totale `GENDER`, `share_frg` è corretta e non ne risente,
la colonna `count` porta un doppio conteggio cosmetico.

### 4.4 `AREA_CONTRY_CITIZEN`: albero a tre livelli, e i livelli intermedi non partizionano

**misurato** (`cens_stranieri_paesi`, Brescia, 2023, `GENDER = T`,
163 codici presenti su 169 in codelist).

Il totale qui si chiama **`ALL`**, non `WORLD`: `WORLD` è il codice di
`29_317`. *Nomi diversi per lo stesso ruolo fra dataflow* — da tenere
presente in qualunque codice che tocchi più di una tavola.

**Livello 1 — continenti, partiziona esatto:**

```
EUR 13 693 + ASI 13 975 + AFR 8 313 + AME 1 490 + OCE 5 + 999 (apolidi) 2
= 37 478 = ALL
```

**Livello 2 — sotto-continenti, NON partiziona il proprio padre:**
`EUR_C_E` 7 939 + `EUR_OTH` 77 = 8 016, contro `EUR` = 13 693. Mancano
~5 677 — l'UE, che in questa tavola non compare come figlio di `EUR`.

> **Differenza rispetto a `EDU_ATTAIN`.** Lì l'albero era a due livelli
> e il livello fine viveva solo su una cella (`Y_GE9`). Qui i livelli
> sono tre, **tutti sempre presenti**, e quello intermedio è
> incompleto. Non esiste una regola unica: ogni dimensione va profilata
> per conto suo.

**Codici fuori standard che sono paesi veri**: `X95` (Kosovo, 64) e
`999` (apolidi, 2). Il Kosovo non ha ISO-2 assegnato e l'ISTAT lo
codifica fuori standard. **La convenzione «due lettere maiuscole =
paese» è nostra, non della fonte, ed è sbagliata in entrambe le
direzioni** — vedi il difetto #10.

### 4.5 Difetto #4 chiuso: erano `ZA` e `CF`

**misurato.** Scarto fra `ALL` e la somma dei 143 codici selezionati da
`nationality_conditional.csv`, Brescia: **5 / 4 / 4** nelle annate
2022 / 2023 / 2024. In conteggio singolo vale 4; raddoppiato dal totale
`GENDER` dà gli **8** osservati in §2.3.

I quattro individui sono identificati: `ZA` (Sud Africa, 2) e `CF`
(Repubblica Centrafricana, 2). Che lo scarto vari fra annate conferma
che sono persone, non un artefatto di costruzione.

**Impatto nullo.** `nationality_conditional` è dichiarata alla riga 33
di `build_constraints` come *«P(paese | straniero), two-stage, fuori
dal MaxEnt»*: non è un vincolo. `share_frg` è rinormalizzata sui codici
presenti, quindi quelle persone ricevono un altro paese invece di
sparire. Su 37 478 stranieri l'effetto è sotto il rumore.

**Ma la causa non è innocua** — vedi #10.

---

## 5. I blocchi C sull'asse istruzione

**misurato** (Brescia, `constraints_*`): `c3_sex_ageclass_edu.csv` e
`c5_edu_citizenship.csv` portano le **stesse sei categorie** —
`nessun_titolo, elementare, media, diploma, laurea_o_its, post_laurea` —
e la **stessa somma** (184 715 in un'annata, 186 538 nell'altra).

Due conseguenze:

1. **Nessuna riconciliazione da costruire.** `build_constraints`
   normalizza a monte; i due blocchi sono componibili così come sono.
2. Il totale 184 715 = `ALL` su `Y_GE9` conferma che il doppio conteggio
   dell'albero **non sopravvive** al passaggio.

### 5.1 RITRATTATA — non c'è nessuna assunzione non dichiarata

> **Ritratto** l'intera §5.1 della v1, che ipotizzava che
> `build_constraints` ripartisse `ML_RDD` fra `laurea_o_its` e
> `post_laurea` dentro ogni classe d'età con la quota 96,2 / 3,8
> osservata su `Y_GE9`, e che questo fosse un parente dell'assunzione
> (9). **Non accade nulla del genere.**

**misurato** (lettura di `edu_collapse`, `scripts/vincoli/build_constraints.py`).
Il collasso 10 → 6 è una **mappatura per etichetta**, con l'ordine dei
check che porta l'informazione:

| check (in ordine) | esito |
|---|---|
| `"totale" in s` | `None` — scartato |
| `"its"` o `"primo livello"` | `laurea_o_its` |
| `"secondo livello"` o `"dottorato"` | `post_laurea` |
| `"nessun"`, `"analfabeta"`, `"alfabeta privo"` | `nessun_titolo` |
| `"elementare"` | `elementare` |
| `"media inferiore"`, `"avviamento"` | `media` |
| `"diploma"`, `"maturit"`, `"secondaria superiore"`, `"qualifica"` | `diploma` |
| altrimenti | `?<label>` — emerge nel print di verifica |

Applicato ai codici delle classi d'età:

- `BL` «ITS o terziario di **primo livello**» → `laurea_o_its`
- `ML_RDD` «terziario di **secondo livello** e dottorato» → `post_laurea`

Quindi nelle classi d'età `post_laurea` **è** `ML_RDD` per intero, e
`laurea_o_its` **è** `BL`. Nessuna quota, nessuna ripartizione.

**Origine dell'errore.** Avevo letto `post_laurea` come «dottorato»,
mentre significa «magistrale + dottorato». La partizione GSP è
*triennale/ITS* contro *magistrale/dottorato* — semanticamente sensata,
col nome che inganna.

**Conferma aritmetica indipendente**: `c3` ha n = 48 = 2 sessi × **4**
classi d'età × 6 categorie. `Y_GE9` non entra, quindi i quattro codici
fini (`ML`, `RDD`, `IL`, `LBNA`) non sono mai letti e il doppio
conteggio è impossibile **per costruzione**.

**Secondo errore, sulla provenienza del commento.** «Foglie da rami
diversi — `post_laurea` prende sia la laurea magistrale (072) sia
l'AFAM (050)» sta in `src/gsp/istruzione.py`, che lavora sull'albero
dei titoli del **codebook regionale** (codici a tre cifre) per il
repertorio narrativo — non sui codici SDMX. Due strutture diverse con
gli stessi nomi di categoria, agganciate a torto.

### 5.2 Tre mappe dell'istruzione, il report ne documenta due

Sullo stesso asse convivono nel progetto:

| livello | modalità | dove |
|---|---|---|
| ISTAT, livello alto | 6 + `ALL` | `cens_istruzione_cittadinanza`, e classi d'età di `cens_istruzione_eta` |
| ISTAT, livello fine | 10 + `ALL` | `cens_istruzione_eta`, solo `Y_GE9` |
| GSP | 6 | `c3`, `c5` |
| condizionamento AVQ | 4 (`istr4`) | `assign_avq` |

Da scrivere come tabella unica con le frecce di aggregazione. È il primo
pezzo della sezione nuova (§7).

### 5.3 Lo stato civile collassa 7 → 4

**misurato** (stesso file, mappa `MARITAL_STATUS` sopra `edu_collapse`).
Le sette modalità di C1 diventano quattro, **fondendo le unioni civili
con i corrispondenti stati matrimoniali**:

| codice ISTAT | → categoria GSP |
|---|---|
| 1 nubile/celibe | `celibe_nubile` |
| 2 coniugato · **15 unito civilmente** | `coniugato_unito` |
| 3 divorziato · **17 scioglimento unione** | `divorziato_sciolto` |
| 4 vedovo · **16 vedovanza civile** | `vedovo` |

È una scelta ragionevole — i tre codici civili sono numericamente
minuscoli — ma **non è documentata nel report**, e vale la stessa
osservazione fatta per l'istruzione: la popolazione sintetica non
distingue matrimonio e unione civile, e chi legge `coniugato_unito`
deve sapere che le comprende entrambe.

**misurato** (anni singoli, `AGE ≠ TOTAL`, 1° gennaio 2025):

| comune | totale | cod. 15 | cod. 16 | cod. 17 | civili | quota |
|---|---|---|---|---|---|---|
| Bologna `037006` | 390 151 | 936 | 16 | 42 | 994 | **0,255 %** |
| Brescia `017029` | 199 853 | 389 | 4 | 16 | 409 | **0,205 %** |
| Mantova `020030` | 49 607 | 61 | 3 | 1 | 65 | **0,131 %** |

Il collasso interessa lo **0,13–0,26 %** della popolazione, con un
gradiente ordinato per taglia e carattere urbano: Bologna quasi il
doppio di Mantova. Essendo Bologna il comune più grande della flotta,
0,26 % è un buon candidato al limite superiore.

**La composizione interna conta più del totale.** Il codice 15 è il
~94 % del blocco; 16 e 17 sono residui veri (16 e 42 individui su
390 mila a Bologna). L'unica fusione che sposta qualcosa è
`15 → coniugato_unito`.

**Formulazione per il report**: *il collasso interessa lo 0,13–0,26 %
della popolazione (Mantova, Brescia, Bologna al 1° gennaio 2025),
concentrato per il ~94 % nel codice 15; la popolazione sintetica non
distingue matrimonio e unione civile, e `coniugato_unito` comprende
entrambi.* Resta una scelta da dichiarare, ma con una misura invece
che con un aggettivo.

**Osservazione di passaggio, non sulle unioni civili.** I tre comuni
hanno profili di stato civile nettamente diversi — celibi/nubili dal
44,8 % (Mantova) al 51,4 % (Bologna), sei punti e mezzo. È la forma che
C1 impone come vincolo hard, e la variabilità fra comuni è quella che
il MaxEnt deve riprodurre.

---

## 6. Difetti aperti raccolti

| # | difetto | gravità |
|---|---|---|
| 1 | ~~`cens_posizione_famiglia` assente~~ | **chiuso**: non consumata, l'anello 4 ricostruisce i nuclei altrimenti |
| 2 | ~~`REF_AREA_label` vuota~~ | **declassato**: noto e innocuo — vedi sotto |
| 3 | doppio conteggio in `count` di `nationality_conditional.csv` (fattore `GENDER`) | cosmetico dove è usato, pericoloso se letto come popolazione |
| 4 | ~~scarto di 8 unità fra `count` e 2 × `FJAN`~~ | **chiuso e identificato**: `ZA` + `CF` = 4, × 2 per `GENDER`. §4.5 |
| 5 | ~~ripartizione `ML`/`RDD` costante fra classi d'età~~ | **ritirato**, §5.1 |
| 6 | `sdmx.fetch`: blocco `status_code == 404` duplicato, il secondo è morto | cosmetico |
| 7 | **C9/C10 marcati `hard` nel manifest** | dichiarato nel sorgente stesso: «è un residuo, l'universo è derivato per riscalatura e andrebbe riclassificato `soft`» |
| 8 | collasso stato civile 7 → 4 non documentato nel report | §5.3 |
| 9 | peso di `MARITAL_STATUS` 15/16/17 mai misurato | **chiuso**, §5.3 |
| 10 | filtro aggregati per substring sulle etichette in `build_constraints` | **reale ma già noto**: corretto in `assign_nationality.py`, `build_constraints` è l'ultimo rimasto — vedi sotto |
| 11 | `report.md` stampa MAE con `{:.1f}` e scarto con `{:+,.0f}` | l'output arrotondato **non è utilizzabile come evidenza** (§11.5); patch: `{:.6g}` |
| 12 | `preflight` verifica la presenza della tavola, non la **profondità** della sua articolazione | §3ter: C2 ha solo i totali dal 2018 al 2020 |

### Il difetto #10

**misurato.** `build_constraints`, riga ~413:

```python
aggregates = lab.str.contains("tutte le voci|unione europea|countries|"
    "europ|africa|america|asia|oceania|total|apolidi|aggregat|eea|efta")
```

`lab` è l'etichetta in minuscolo. Quindi:

- «Sud **africa**» → escluso come se fosse un aggregato
- «centr**africa**na, Repubblica» → escluso

**Non cadono per soglia né per elenco chiuso: cadono perché il loro
nome contiene il nome di un continente.** È la trappola di «NIL» →
*femmiNILe*, **settima comparsa**, stavolta sui nomi di paese.

**Impatto misurato sulla flotta** (254 comuni, codici a due lettere
catturati dal pattern):

| codice | individui | etichetta |
|---|---|---|
| `ZA` | 594 | Sud Africa |
| `CF` | 106 | Centrafricana, Repubblica |

**700 individui**, sistematici e silenziosi. Effetto sul MaxEnt nullo
(§4.5), ma quelle due nazionalità **non esistono** nella popolazione
sintetica di nessun comune.

**Errore di segno opposto nello stesso punto**: il filtro cerca
`apolidi` ma l'etichetta ISTAT è «Apolide». Non matcha, quindi `999`
entra nel file — **contro l'intenzione dichiarata dal filtro stesso**.
Due individui a Brescia.

> **Ritratto** un allarme lanciato in seduta: «Mala*ysia* contiene
> *asia*». **Falso.** `malaysia` contiene `ysia`, non `asia`. Dedotto a
> occhio senza verificare, e l'output sulla flotta lo smentisce.

**Sulla patch, e su una trappola nella patch.** L'istinto è filtrare
sui **codici** invece che sulle etichette — il codice è stabile,
l'etichetta è prosa. Ma il conteggio sulla flotta ha rivelato che
**`EU` è un codice a due lettere e vale 1 086 900**: un'euristica
«due lettere = paese» farebbe entrare l'Unione europea come se fosse
un paese, con un errore trenta volte peggiore di quello che corregge.

La patch corretta è una **lista esplicita dei codici aggregato**, non
un'euristica di forma. Su nessuno dei due lati — codice o etichetta —
esiste una regola di forma che funzioni.

### La patch esiste già (aggiornamento v9)

**misurato.** `src/gsp/common.py:496` definisce `AGGREGATI_PAESE`, con
il commento *«Codici della codelist AREA_CONTRY_CITIZEN che NON sono
paesi: continenti…»*. È usata in `opendata.py`, `enrich.py` e
`assign_nationality.py`. Quest'ultimo porta il commento che chiude la
questione:

> *Filtrare gli aggregati per CODICE e non per etichetta: la regex su
> 'africa' catturava anche 'Sud Africa', che è un paese. I codici
> aggregati sono una ventina e fissi (`G.AGGREGATI_PAESE`); i paesi
> sono duecento e in crescita.*

La vecchia `AGGREG_RE` è conservata commentata sopra, in due file.

> **Il difetto #10 non è quindi un bug nuovo**: è un bug **già trovato,
> già diagnosticato con lo stesso esempio (`Sud Africa`) e già
> corretto** — in tre script su quattro. `build_constraints.py:415` è
> l'unico rimasto con la versione vecchia. La patch è una riga:
> `~isin(G.AGGREGATI_PAESE)` al posto di `str.contains(...)`.

**Sul #2, declassato.** `_resolve_codelist_code` esiste ed è usata da
`profile`, **mai da `decode`** — toppa applicata a un ramo e non
all'altro. Ma **misurato**: `grep -rn "REF_AREA" --include=*.py src/
scripts/` non trova alcuna lettura a valle (due occorrenze in
`normalizzatori.py` sono diagnostica, tre sono commenti nel modulo di
acquisizione). L'identità del comune viaggia nel **percorso**
`data/comuni/<codice>/`, non nella colonna, e `build_constraints`
riceve il codice da riga di comando.

Il costo era già noto e documentato: `fetch_prov.py:18` — *«REF_AREA
int nei decoded — già pagato in C3»*. Non è un difetto aperto, è un
costo pagato nel posto giusto.

Resta un punto di igiene: lo zero si perde in `sdmx.fetch`, alla
`pd.read_csv`, **prima** che il file venga scritto. Quindi
`_raw.csv` contiene già `20030`: il nome promette il dato originale e
non lo mantiene. Qui l'informazione è recuperabile con uno
zero-padding a sei cifre, ma su un'altra colonna potrebbe non esserlo.
`dtype=str` in `sdmx.fetch` risolve alla sorgente — preferibile a
portare la riconciliazione in `decode`, che agirebbe a valle.

Il #7 merita attenzione perché **incrina la giustificazione di §1**: se
la gerarchia hard/soft è motivata dalla natura della fonte, due blocchi
marcati hard per residuo sono un'eccezione da dichiarare, non da
lasciare implicita. L'assunzione (7) di stabilità strutturale 2021, per
contro, è dichiarata correttamente in docstring — ed è il modello di
come vanno trattate le altre.

---

## 7. Verso la sezione nuova del report

La sessione ha prodotto il materiale per una sezione che oggi manca:
**quali dati censuari e anagrafici usiamo, e come da quelli si
costruiscono i blocchi C**. Le tabelle già misurate:

1. le due fonti e i loro assi (§1), con `MARITAL_STATUS` come
   giustificazione della gerarchia hard/soft — e l'eccezione C9/C10
   (difetto #7) dichiarata invece che taciuta;
2. la matrice DSD × modalità effettive (§3) — il disegno 2×2;
3. la struttura interna di `EDU_ATTAIN` (§4) come **caso esemplare**:
   totali di dimensione e alberi interni convivono, e vanno separati
   guardando la presenza per cella e non le somme;
4. le mappature di collasso, tutte con le frecce di aggregazione: le
   tre risoluzioni dell'istruzione (§5.2) e lo stato civile 7 → 4
   (§5.3), con le regole per etichetta di `edu_collapse` (§5.1) come
   documentazione del *come*, non solo del *cosa*;
5. dai blocchi grezzi ai sedici del constraint set — undici completi,
   cinque parziali, con i complementi fuori universo.

**Perché la sezione vale.** Il pezzo che nessuno scrive non è
l'inventario delle fonti ma §4: *una tavola ISTAT non è una matrice*.
È una matrice con totali di dimensione e alberi interni che convivono
nella stessa colonna, e il livello fine può esistere solo su certe
celle. Chi costruisce un constraint set da fonti pubbliche ci sbatte
contro. Che questa sessione ci sia arrivata dopo **due letture
sbagliate**, e che l'errore fosse **già documentato** in un altro
modulo dello stesso progetto (§8), è la prova che serve.

Manca ancora, per (5), la stessa mappatura quantitativa sui **blocchi
Z**, che non vengono da SDMX ma da `build_zona_tables` — sezioni e open
data comunali. Stessa logica, altra fonte.

---

## 8. Nota di metodo — l'errore era già documentato altrove

Il principio che le ritrattazioni di §4.2 e §5.1 rendono esplicito:

> **Le somme aggregate non distinguono le strutture; la presenza per
> cella sì.** Ogni volta che un rapporto sospetto è stato letto su una
> somma (il fattore 2, l'albero, il residuo `−(ML+RDD)`) la lettura era
> sbagliata. La `crosstab` presenza × cella ha risolto in un colpo
> quello che tre giri di somme avevano confuso.

**E il progetto lo sapeva già.** `src/gsp/istruzione.py`, funzione
`verifica()`, terzo controllo — con un commento che descrive
esattamente l'errore commesso oggi:

> *Coerenza **per ramo**, non per categoria: una categoria può
> raccogliere foglie da rami diversi — `post_laurea` prende sia la
> laurea magistrale (072) sia l'AFAM (050) — e sommarle contro il
> totale di UN solo ramo produce un falso allarme. È l'errore che
> questa verifica ha commesso al primo giro sui dati veri.*

La docstring della stessa funzione è ancora più esplicita sul perché
quel controllo esista: *«è il controllo che scopre se si sta contando
due volte, ed è l'unico che guarda i DATI invece del codebook»*.

**La stessa classe di errore è ricomparsa a un livello diverso** — dal
codebook regionale ai codici SDMX, da `istruzione.py` a
`cens_istruzione_eta` — e non è stata riconosciuta. Che sia riemersa
su un altro oggetto è l'informazione utile: non è un incidente locale,
è una proprietà delle classificazioni statistiche gerarchiche.

**Conseguenza operativa.** Il controllo giusto esiste già, con la sua
soglia (`scarto_%` oltre 0,5 % → allarme), e va **generalizzato alle
tavole SDMX**: per ogni dimensione, verificare che la somma delle
foglie ricostruisca il totale *del proprio ramo*, e non del ramo
sbagliato né dell'intera dimensione. Un `preflight` strutturale
accanto a quello temporale già presente in `build_constraints` v2.

È il parente stretto di un principio già a registro — *ogni metrica che
scala col numero di celle va normalizzata contro la sua ipotesi nulla*.
Qui la variante: **prima di interpretare un rapporto, guardare dove le
celle esistono, e contro quale totale.**

### 8.1 Corollario: nessuna euristica di forma sui codici

Il difetto #10 e la trappola nella sua patch (§6) danno un secondo
principio, indipendente dal primo:

> **Le classificazioni statistiche non hanno una forma che distingua
> gli elementi dagli aggregati.** Non l'etichetta — «Sud Africa»
> contiene «africa». Non il codice — `EU` ha la stessa forma di `IT`.
> L'unica selezione affidabile è una **lista esplicita**, derivata
> dalla struttura gerarchica dichiarata, non da una regola di pattern.

Le comparse a registro della stessa famiglia di errore sono ora sette:
la trappola degli zeri iniziali (cinque), «NIL» → *femmiNILe*, e i nomi
di paese che contengono nomi di continente.

**Controllo generalizzabile.** Per ogni dimensione con struttura
gerarchica, verificare che la somma dei codici selezionati come
elementari ricostruisca il totale **del proprio ramo**. Su
`AREA_CONTRY_CITIZEN` a Brescia lo scarto è 4 su 37 478 e ha portato
diritto a `ZA` e `CF`. È il controllo di `istruzione.verifica()`,
applicato all'altra fonte.

---

## 9. Le tre risoluzioni dell'età, e il trade-off età / territorio

**misurato** (matrice B, §3, più la copertura di `REF_AREA`).

**Tutte e undici le tavole `CORE` hanno `REF_AREA` = comune.** Nessuna
scende sotto. Il sub-comunale arriva da altre due fonti: le sezioni di
censimento (workbook regionali, `data/submun/`) e gli open data
comunali per quartiere / zona.

Le classi d'età entrano al **secondo livello**, quando l'incrocio si
arricchisce. Tre risoluzioni che non si sovrappongono mai:

| risoluzione | dove | attributi | territorio |
|---|---|---|---|
| **anno singolo** (101) | C1, C2 | stato civile, cittadinanza | comune |
| **4 classi larghe** `Y9-24, Y25-49, Y50-64, Y_GE65` | C3, C4 | istruzione, condizione prof. | comune |
| **quinquennali** (16 per sesso) | sezioni ISTAT | solo sesso | **sezione** |

Più un quarto caso: `cens_stranieri_paesi`, `migr_backg`,
`posizione_prof`, `settore_prof` hanno `AGE_CLASS` collassato a una
modalità — **nessuna informazione d'età**. Paese di cittadinanza,
background migratorio, posizione e settore vivono senza età.

**La regola implicita è un compromesso di significatività**: più
attributi si incrociano, più l'età si degrada. Anno singolo con un
attributo binario; quattro classi con l'istruzione; niente età con il
paese. Conferma aritmetica: `c3_sex_ageclass_edu.csv` ha n = 48 =
2 sessi × **4** classi × 6 titoli.

> **Ed è qui che la geometria dell'assunzione (9) diventa visibile.**
> La risoluzione fine dell'età esiste solo dove il territorio è grosso;
> il territorio fine esiste solo dove l'età è grossa:
>
> - comune → età per anno singolo
> - sezione → età quinquennale, e nient'altro che il sesso
>
> L'assunzione (9) è **il ponte che attraversa un buco che la fonte non
> copre**. Non è una scelta discutibile fra alternative: è l'unico modo
> di arrivare dall'altra parte. Il che non la rende vera, ma spiega
> perché non esiste un test diretto.

---

## 10. Assunzione (9): il precursore, eseguito

**Enunciato.** La distribuzione dell'età *dentro* ogni bin quinquennale
è la stessa in tutte le sezioni di censimento del comune. La pipeline
misura la forma entro bin sul comune (da C1, anno singolo) e la
applica dentro ogni sezione (che ha solo il quinquennale).

**Perché l'exact match non aiuta.** L'identità verificata riguarda gli
**aggregati**: sommando le sezioni, i totali quinquennali coincidono
con l'anagrafe a zero. L'assunzione (9) vive *sotto* quella
risoluzione. È come conoscere esattamente la massa in ogni cella e
assumere che il profilo di densità dentro la cella sia lo stesso
ovunque: si può verificare la massa mille volte senza sapere nulla
della densità interna.

### 10.1 Il disegno

Non essendo osservabile l'anno singolo per sezione, il test è
**indiretto e fra comuni**: se la forma entro bin varia molto fra i
253 comuni, esiste un gradiente locale e trasportarla introduce errore;
se è costante, la quantità trasportata è nazionale e il trasporto è
innocuo.

Metrica: **scostamento del baricentro** — per ogni bin, età media entro
il bin meno il punto medio (`lo + 2.0`, perché le età sono interi: un
bin 0–4 uniforme ha baricentro esattamente 2). Segno negativo = skew
giovane. Somma su sesso e stato civile; bin con n < 50 esclusi, perché
su un comune piccolo il baricentro di sei individui è rumore e
gonfierebbe la dispersione con un artefatto di taglia.

### 10.2 Il risultato

**misurato** (253 comuni, 4 762 osservazioni, anagrafe 1 gen 2025):

| bin | media | sd | p05 | p95 |
|---|---|---|---|---|
| 0-4 | +0,058 | 0,088 | −0,086 | +0,185 |
| 5-9 | +0,077 | 0,081 | −0,045 | +0,211 |
| 10-14 | +0,051 | 0,075 | −0,082 | +0,160 |
| 15-19 | −0,006 | 0,069 | −0,110 | +0,119 |
| 20-24 | +0,005 | 0,080 | −0,128 | +0,141 |
| 25-29 | −0,008 | 0,077 | −0,149 | +0,113 |
| 30-34 | +0,048 | 0,077 | −0,079 | +0,184 |
| 35-39 | +0,026 | 0,076 | −0,090 | +0,159 |
| 40-44 | +0,044 | 0,075 | −0,065 | +0,157 |
| 45-49 | +0,097 | 0,061 | −0,009 | +0,192 |
| 50-54 | −0,001 | 0,060 | −0,097 | +0,100 |
| 55-59 | −0,013 | 0,067 | −0,113 | +0,114 |
| 60-64 | −0,074 | 0,068 | −0,175 | +0,028 |
| 65-69 | −0,056 | 0,068 | −0,166 | +0,066 |
| 70-74 | −0,039 | 0,072 | −0,182 | +0,067 |
| **75-79** | **−0,156** | 0,073 | −0,275 | −0,043 |
| 80-84 | −0,048 | 0,089 | −0,202 | +0,096 |
| **85-89** | **−0,272** | 0,095 | −0,422 | −0,110 |
| **90-94** | **−0,399** | 0,144 | −0,634 | −0,143 |

```
sd mediana fra bin : 0,075 anni  (27 giorni)
|media| mediana    : 0,048 anni
```

**Primo risultato — l'ipotesi del gradiente locale è smentita, non
non-verificata.** La dispersione fra comuni è di 27 giorni; sedici bin
su diciannove sotto 0,09. La forma entro bin è **praticamente identica
in tutti i 253 comuni**.

La spiegazione teorica regge: l'inclinazione entro bin è dominata dalla
dimensione delle **coorti di nascita**, che è un fenomeno *nazionale*.
Un comune è giovane per migrazione e fecondità, ma la forma della
piramide dentro un quinquennio la detta la storia demografica italiana,
uguale ovunque.

> **Conseguenza per l'assunzione (9).** Trasportare la forma entro bin
> dal comune alla sezione **non introduce eterogeneità fra sezioni**:
> la quantità trasportata è nazionale, non locale. È una
> giustificazione misurata, più debole di una verifica diretta —
> che resta impossibile — ma non più nuda.

**Secondo risultato — l'ipotesi di uniformità sbaglia sopra i 75
anni.** L'inclinazione *comune a tutti* è trascurabile fino ai 74 anni
(|media| mediana 0,048), ma diventa sostanziale nella coda vecchia:
−0,156 a 75-79, −0,272 a 85-89, −0,399 a 90-94. È l'effetto della
mortalità: dentro un bin di ultraottantenni i più giovani sono
sistematicamente di più.

> **RITRATTATO** (v8). Avevo proposto: *se la pipeline assumesse
> uniformità entro bin, sui bin anziani sbaglierebbe di 0,3–0,4 anni
> con segno negativo — direzione giusta per lo scarto 10/10.*
>
> **La pipeline non assume uniformità.** `expand_z1` in `cs_build` fa
> `count = P(zona | sesso, quinquennio) × anag(sesso, età singola)`:
> il peso anagrafico è ad **anno singolo** ed esatto. Sommando sulle
> zone, il marginale d'età torna esattamente quello di C1, **per
> costruzione**. Il meccanismo proposto non può produrre alcuno scarto.
>
> Ciò che è assunto costante entro il bin è la **quota di zona**, non
> la forma dell'età — è l'assunzione (2) dichiarata in `cs_build`.
> Le due formulazioni sono **equivalenti**: se ogni età dentro il bin
> ha la stessa distribuzione spaziale, allora ogni zona ha la stessa
> forma entro bin. Il precursore di §10.2 le sostiene entrambe.
>
> Lo scarto verso il giovane 10/10 **resta senza meccanismo
> identificato**.

**Note minori.** Un comune manca (253 su 254): probabilmente un comune
minuscolo senza bin sopra soglia. I bin 0-4 e 5-9 hanno media positiva
(+0,06 / +0,08): skew *vecchio*, coerente con la denatalità recente.

### 10.3 Formulazione per il report

> *La forma entro bin quinquennale è nazionale, non locale (sd fra 253
> comuni = 0,075 anni); l'assunzione (9) non introduce eterogeneità fra
> sezioni, ma l'ipotesi di uniformità entro bin sbaglia
> sistematicamente sopra i 75 anni.*

**Il test lungo — regressione della forma entro bin contro il profilo
grosso — non serve più**: si sarebbe cercato un gradiente che il
precursore mostra non esserci.

---

## 11. La costruzione del constraint set

**misurato** (lettura di `scripts/vincoli/build_constraints.py`, v2, 596 righe).

### 11.1 La spina, e il meccanismo unico

Tutto pende da un solo oggetto, costruito alla riga 277:

```python
anag_sex_age = c1.groupby(["sex","age"])["count"].sum()   # -> anag_total
```

È C1 sommata sullo stato civile: **sesso × età per anno singolo, conteggi
anagrafici esatti**. Ogni blocco censuario vi si aggancia tramite una sola
funzione:

```python
def apply_conditional(anag_groups, cens, group_cols, attr_col):
    share = cens[attr] / cens[group_total]      # dal CENSIMENTO: la forma
    count = share * anag_groups["anag_total"]   # dall'ANAGRAFE: i livelli
```

> **Questa funzione *è* l'architettura forma-non-livelli.** Non è una
> scelta descritta a parole nel report e implementata altrove: sono tre
> righe, e ogni blocco condizionale ci passa attraverso. Per il paper è
> la citazione più efficace possibile.

**E l'exact match la rende quasi un'identità.** Se anagrafe e censimento
coincidono sulla spina (§2.4), il fattore `anag_total / cens_total` vale
1 e `apply_conditional` non sposta nulla. Conferma empirica: `c3`
(riscalato) e `c5` (non riscalato, §11.2) danno la **stessa somma**,
184 715. L'architettura è progettata per essere robusta a una divergenza
che oggi non esiste — e resterebbe corretta se l'ISTAT cambiasse
metodologia.

### 11.2 I cinque regimi di ancoraggio

| blocco | contenuto | fonte | gruppo di condizionamento | ancoraggio |
|---|---|---|---|---|
| **C1** | sesso × età × stato civile (4) | anagrafe *N* | — | **HARD**, conteggi esatti |
| **C2** | sesso × età × cittadinanza (2) | cens. *N−1* | sesso × età **anno singolo** | `apply_conditional` |
| **C3** | sesso × classe × istruzione (6) | cens. *N−1* | sesso × **classe d'età** (4) | `apply_conditional` |
| **C4** | sesso × classe × condizione prof. | cens. *N−1* | sesso × **classe d'età** (4) | `apply_conditional` |
| **C5** | istruzione × cittadinanza | cens. *N−1* | — | **nessuno**: livelli censuari grezzi |
| **C6** | condizione prof. × cittadinanza | cens. *N−1* | — | **nessuno**: idem |
| **C7** | sesso × background migratorio (6) | cens. *N−1* | margini ITL/FRG di C2 | armonizzazione **1D** |
| **C8** | background × origine genitori | cens. *N−1* | — (condizionale su C7) | — |
| **C9** | sesso × posizione prof. (2) | cens. **2021** | totale occupati per sesso da **C4** | quote riscalate |
| **C10** | sesso × settore (6) | cens. **2021** | idem | quote riscalate |
| *naz.* | P(paese \| straniero), 143 codici | cens. *N−1* | — | **fuori dal MaxEnt**, two-stage |

**Cinque regimi distinti**: conteggi esatti (C1); riscalatura su gruppo
fine (C2); riscalatura su gruppo grosso (C3, C4); nessuna riscalatura
(C5, C6); riscalatura su un blocco già costruito (C7–C10). Il report
oggi ne descrive uno.

**Su C5/C6 il manifest è esplicito**: `"note": "quote su universo
tavola; riscalare in fase solver"`. La riscalatura non è omessa, è
**delegata a valle**. Va detto, perché un lettore che confronti i conteggi
di C3 e C5 li trova uguali e potrebbe dedurne che siano prodotti allo
stesso modo — non lo sono.

**C9/C10 hanno una dipendenza sequenziale**: leggono
`c4_sex_ageclass_condprof.csv` **dal disco**, appena scritto, per
ricavare gli occupati per sesso. Se C4 non è leggibile escono senza
riscalatura, con un `print` a video. È l'unico punto in cui l'ordine
di costruzione dei blocchi è vincolante.

### 11.3 Il rilevamento automatico degli aggregati d'età

`elementary_classes()` risolve per l'età lo stesso problema che §4 ha
risolto a mano per `EDU_ATTAIN`:

```python
contains_other = any(o != c and lo <= plo and phi <= hi ...)
```

Scarta ogni codice classe che **contiene interamente** un'altra classe.
Su `cens_istruzione_eta` elimina `Y_GE9` e tiene le quattro classi —
esattamente il risultato di §4.1, ottenuto per costruzione invece che
per ispezione.

> **Il controllo generalizzabile invocato in §8 esiste già, per una
> dimensione sola.** `elementary_classes` funziona sull'età perché i
> codici `Y*` hanno estremi numerici confrontabili. Su `EDU_ATTAIN` e
> `AREA_CONTRY_CITIZEN` la gerarchia non è deducibile dal codice (§8.1)
> e servirebbe leggerla dal DSD. Ma il **principio** è già implementato
> e collaudato: la generalizzazione ha un modello interno da seguire.

### 11.4 Le altre normalizzazioni, tutte per etichetta

| dimensione | meccanismo | rischio |
|---|---|---|
| stato civile | dizionario **sui codici** (7 → 4) | nessuno |
| background, origine | dizionario **sui codici** | nessuno |
| posizione, settore | dizionario **sui codici** | nessuno |
| **istruzione** | `edu_collapse`, catene di `in` **sull'etichetta** | ordine dei check rilevante (§5.1) |
| **condizione prof.** | etichetta passata **grezza** come `attr` | nessuna normalizzazione |
| **paesi** | `str.contains` **sull'etichetta** | **difetto #10** |

Le mappature su **codice** sono robuste; quelle su **etichetta** sono
dove stanno i due problemi noti. La condizione professionale è un terzo
caso: l'etichetta ISTAT diventa direttamente il valore dell'attributo,
senza collasso — quindi la stabilità dello schema dipende dalla
stabilità della prosa ISTAT.

### 11.5 Diagnostica già prodotta, e mai raccolta

`build_constraints` scrive per ogni comune un `report.md` che contiene
il **raccordo anagrafe ↔ censimento sulla spina**: MAE per cella, scarto
totale, top-5 scarti. È la stessa misura di §2.4, calcolata a ogni run
su tutti i 254 comuni — e mai aggregata.

**chiuso, ma non per la via prevista.** L'aggregazione dei 255
`report.md` disponibili (253 comuni, ancoraggi 2024 e 2025) dà MAE 0,0
e scarto totale +0 in **tutti** i run. Risultato sospetto per
perfezione, e infatti insufficiente:

> **Ritrattazione di metodo.** `report.md` formatta il MAE con
> `{mae:.1f}` e lo scarto con `{:+,.0f}`. Quindi «0.0» significa
> **MAE < 0,05**, non MAE nullo, e «+0» significa |scarto| < 0,5.
> Avevo aggregato 255 numeri **già arrotondati** leggendoli come
> esatti — leggere una quantità derivata invece della cella, per la
> terza volta nella stessa sessione (§4.2, §5.1, qui).

Il risultato regge solo perché **ricalcolato dalle celle** a piena
precisione: §2.5. Il ricalcolo copre anche di più — 506 confronti
contro 255 run, perché non dipende da quali comuni siano stati
processati da `build_constraints`.

**Resta utile aggregare i `report.md`** per il monitoraggio corrente
(sono già scritti a ogni run), ma **non come evidenza**: per quella
serve la precisione piena. Se si vuole usarli, la patch è cambiare i
formati in `{:.6g}`.

### 11.6 Dove *non* sta l'assunzione (9)

**misurato.** In `build_constraints` l'età resta ad **anno singolo** in
C1 (hard) e C2. C3/C4 aggregano la spina anagrafica in classi con
`to_class()`, ma **non ridistribuiscono mai** dentro la classe: la
distribuzione per età del comune resta quella anagrafica esatta.

Nessuna ipotesi di uniformità entro bin entra qui. La domanda aperta di
§10.2 — *la pipeline usa la forma di C1 o assume uniforme?* — si sposta
quindi interamente a **`build_sezioni`**, dove il quinquennale di
sezione incontra l'anno singolo comunale. È lì che va letta.

---

## 12. La convergenza dei due rami

**misurato** (lettura di `cs_build.py` v2, 812 righe, più misura diretta).

### 12.1 Il meccanismo, dichiarato in testa al file

> *ogni tabella di zona entra come `P(zona | gruppo) × conteggi comunali
> del gruppo` → i margini sommati sulle zone coincidono **esattamente**
> coi blocchi comunali, per costruzione*

È `apply_conditional` (§11.1) per la **terza** volta, a una terza scala,
qui con l'IPF a chiudere **entrambi** i margini invece di uno solo.

**Z1 è la spina spaziale, come C1 è quella demografica.** Costruita per
prima, diventa il target di riga per tutto il resto.

### 12.2 La catena di ancoraggio completa

| blocco | forma da | livelli da | meccanismo |
|---|---|---|---|
| A (C1) | — | **anagrafe** | conteggi esatti (HARD) |
| B, E, F | censimento comunale | anagrafe (`anag_sex_age`) | `apply_conditional` |
| C, D | censimento per classe | anagrafe **anno singolo** | `block_from_class` + IPF con zeri strutturali |
| **Z1** | sezioni (quinquennale) | anagrafe **anno singolo** | `P(zona\|sesso,quinq) × anag` |
| **Z2** | sezioni (macroetà) | **blocco B** | IPF 2D: righe Z1, colonne B |
| **Z3** | sezioni (edu5) | **blocco C** | IPF 2D per sesso |
| **Z4** | sezioni (occupati) | **blocco D** | quote + cap su Z1, ridistribuzione |

> **La frase che riassume l'architettura**: *nessuna fonte contribuisce
> mai i propri livelli, tranne l'anagrafe.* Tre applicazioni dello
> stesso principio a tre scale — anagrafe ↔ censimento, comune ↔
> classe d'età, comune ↔ zona.

**Z4 è l'eccezione strutturale.** Non usa IPF: cappa su Z1 e
ridistribuisce l'eccesso in un loop da 60 iterazioni. Il margine
comunale resta esatto, il cap è una **disuguaglianza** — garanzia più
debole degli altri blocchi. E vincola solo il lato «occupato»: la
docstring dichiara che lo split di zona dei non-occupati non è
esprimibile senza assunzioni extra.

### 12.3 Quanto lavoro fa davvero l'armonizzazione

**misurato.** Ricostruzione indipendente dell'inizializzazione di Z2
(`P(zona|sesso,macro,citt) × C2`) e confronto con il risultato dell'IPF,
importando `zona_shares`, `ipf_2d` e `macro_of` **da `cs_build`** per
non misurare la propria interpretazione.

| comune | anno | massa | spostata | quota | max cella |
|---|---|---|---|---|---|
| Milano `015146` | 2024 | 1 371 499 | 0 | 0 % | **0** |
| Brescia `017029` | 2024 | 198 259 | 0 | 0 % | **1,6·10⁻⁹** |
| Brescia | **2025** | 199 853 | 352,2 | 0,18 % | **14,92** |
| Piacenza, Parma, Reggio, Modena, Ravenna, Cesena, Forlì, Rimini | 2024 | — | 0 | 0 % | **0** |
| Bologna `037006` | 2024 | 390 098 | 0 | 0 % | **1,6·10⁻⁹** |
| Bologna | **2025** | 390 151 | 371,6 | 0,10 % | **14,18** |

**Prova positiva, non assenza di evidenza.** Gli `assert` sui margini
(`A.sum(axis=1) == row_t`, `A.sum(axis=0) == col_t`, tolleranza 10⁻⁶)
**passano su tutti i gruppi**, in entrambi gli anni. Quindi lo zero del
2024 non significa «l'IPF non ha fatto niente»: significa che
**l'inizializzazione soddisfaceva già entrambi i margini**, e il
residuo di 1,6·10⁻⁹ è la tolleranza del solver.

Controlli di integrità superati: zero `share` NaN (6 666 e 3 636 celle
Z1; 12 936 e 7 182 celle Z2), nessuna classe quinquennale non
matchata, celle non nulle **396** per Brescia (33 zone × 2 sessi × 3
macro × 2 cittadinanze) e **216** per Bologna (18 × 2 × 3 × 2) —
esattamente il conteggio atteso dalla geometria.

**Perché il 2024 è esatto.** Le sezioni sono 2023; con `--anno 2024`
l'ancoraggio censuario è anch'esso 2023. **Stessa fonte, stesso
istante**: l'identità del RBI (§2.5) si propaga dal ramo comunale a
quello territoriale. Sezioni e SDMX non sono due misure da riconciliare,
sono la stessa base a due granularità — verificato qui sull'intero
prodotto zona × sesso × macroetà × cittadinanza.

**Perché il 2025 no.** Solo Brescia e Bologna hanno il constraint set
2025; lì le sezioni restano 2023 mentre il censimento passa al 2024.
Lo 0,10–0,18 % è quindi **il costo misurato dello sfasamento temporale
fra i due rami**, non un'incompatibilità fra fonti. Lo spostamento
massimo per cella è ~15 individui su entrambi i comuni, nonostante una
differenza di taglia di 2× — suggerisce un effetto in valore assoluto
per cella, non proporzionale alla popolazione.

> **Formulazione per il paper.** *Quando ramo comunale e ramo
> territoriale sono allineati nell'anno, l'armonizzazione IPF è
> esattamente l'identità (undici comuni, spostamento nullo a precisione
> macchina). Il disallineamento di un anno costa lo 0,10–0,18 % della
> massa, con spostamento massimo di ~15 individui per cella.*
>
> Dice due cose insieme: che l'architettura è internamente coerente, e
> che l'assunzione di stabilità della struttura spaziale fra 2023 e
> 2024 ha un prezzo **quantificato** invece che dichiarato.

### 12.4 `ETA_MIN_TITOLO`: la cicatrice più istruttiva

La classe censuaria dell'istruzione (`Y9-24`) attraversa i bin 9-14 e
15-24. Senza vincolo, la quota di diplomati viene applicata identica a
ogni età: il commento nel sorgente riporta che **su Parma il 32,8 % dei
9-14enni risultava diplomato o laureato**.

La soluzione è zeri strutturali più IPF su (età singola × titolo), con
`_ipf_eta_attr` che vincola **simultaneamente** riga (anagrafe per età)
e colonna (conteggi censuari per titolo) — *«imporre solo i secondi
romperebbe la coerenza con il blocco A»*. Con un fallback dichiarato:
se un titolo non ha nessuna età ammissibile nella classe, il vincolo
viene rilassato per quella colonna, con `[warn]` se l'IPF non converge
sotto 10⁻³.

È lo stesso pattern delle esclusioni α = 0, già implementato per un
caso — e il flag `--esclusioni` in `main()` conferma che il meccanismo
generale esiste: le 26 combinazioni in lista sono un'**estensione del
set**, non l'implementazione.

---

## 13. Le zone dell'Emilia-Romagna

**misurato** (file regionale `R08`, 43 729 sezioni, 330 comuni,
4 451 938 abitanti).

| livelli ASC | comuni | popolazione |
|---|---|---|
| 0 | **318** | 2 721 971 (61,1 %) |
| 1 | 11 | 1 339 869 |
| 3 | 1 (Bologna) | 390 098 |

**12 comuni su 330 sono articolati: il 3,6 % dei comuni, il 38,9 %
della popolazione regionale.** Il 61 % della popolazione ER non ha
alcuna partizione sub-comunale ISTAT.

| comune | pop | sez | ASC1 | ASC2 | ASC3 |
|---|---|---|---|---|---|
| Bologna | 390 098 | 2 224 | 6 | 18 | **90** |
| Parma | 198 121 | 1 357 | 13 | — | — |
| Modena | 184 597 | 2 186 | 4 | — | — |
| Reggio nell'Emilia | 171 207 | 1 813 | 4 | — | — |
| Ravenna | 156 304 | 2 376 | 10 | — | — |
| Rimini | 150 046 | 1 888 | 6 | — | — |
| Forlì | 117 050 | 1 519 | 21 | — | — |
| Piacenza | 102 887 | 1 009 | 4 | — | — |
| Cesena | 96 066 | 1 275 | 12 | — | — |
| **Carpi** | 72 523 | 914 | **33** | — | — |
| **Faenza** | 58 843 | 674 | **5** | — | — |
| **Lugo** | 32 225 | 219 | **14** | — | — |

### 13.1 I tre non articolati, e perché

Carpi, Faenza e Lugo **offrono un livello ASC1 e sono stati generati
senza articolazione**. `build_sezioni` lo segnala già a video: *«K6C
dichiarato nel registro, ma il file regionale offre livelli ASC —
scelta legittima, verificare che sia intenzionale»*.

**misurato**, squilibrio di taglia (pop max / pop min per zona):

| comune | zone | pop/zona | max/min |
|---|---|---|---|
| Carpi | 33 | 14 – 7 741 | **553×** |
| Lugo | 14 | 442 – 6 633 | 15× |
| Faenza | 5 | 2 742 – 20 509 | 7,5× |
| *in flotta, peggiore* (Ravenna) | 10 | 3 605 – 39 580 | 11× |

**Carpi ha una zona da 14 abitanti.** Incrociata con sesso × 16 classi
quinquennali dà 32 celle da ~0,4 persone: non è una zona piccola, è
vuota rispetto alla granularità che il blocco Z richiede.

**E non sono quartieri.** Il pattern è *capoluogo più frazioni* —
Faenza 20 509 nel centro e quattro rurali, Lugo 6 633 e tredici
frazioni. Partizione di natura diversa da quelle urbane della flotta
(Brescia 33 quartieri, Parma 13), che hanno zone comparabili fra loro.

> **Formulazione per il report**: *le tre partizioni disponibili e non
> usate sono di tipo centro-frazioni, con squilibrio di taglia fino a
> 553×, non comparabili con le partizioni urbane della flotta.*

**Bologna ha un terzo livello, ASC3 = 90 unità, non nel registro.**
~4 300 abitanti l'una: sarebbe il livello più fine della flotta, su un
comune già misurato a 6 e 18 zone — quindi controllato per città. Punto
naturale della serie varianza interna/esterna (Modena 4 → 43,5×;
Bologna 18 → 15,7×; Parma 13 → 11,3×; Brescia 33 → 5,9×). **aperto.**

### 13.2 Il costo delle sezioni fittizie

La convenzione è tenerle («coerenza contabile con i totali ufficiali»).
**misurato**, peso della sezione fittizia sulla zona che la ospita:

| comune | zone | P1 fittizia | % della zona | stranieri |
|---|---|---|---|---|
| **Reggio nell'Emilia** | 4 | 1 416 | **5,4 %** | 958 (68 %) |
| Parma | 13 | 502 | 2,5 % | 365 (73 %) |
| Bologna | 18 | 620 | 2,3 % | 228 (37 %) |
| Cesena | 12 | 192 | 1,6 % | 85 (44 %) |
| Rimini | 6 | 256 | 1,2 % | 44 (17 %) |
| Ravenna | 10 | 300 | 0,8 % | 135 (45 %) |
| Piacenza | 4 | 56 | 0,2 % | 14 (25 %) |
| Modena | 4 | 50 | 0,2 % | 0 |
| Forlì | 21 | **1** | 0,0 % | 1 |

**Reggio Emilia è il caso da dichiarare.** 958 stranieri in una singola
sezione dentro una zona da 26 198 abitanti spostano la quota di
stranieri della zona di ~3,5 punti percentuali — lo stesso ordine di
grandezza del segnale che il blocco Z2 dovrebbe misurare. Con **sole 4
zone** l'effetto si concentra invece di diluirsi.

> **Principio, e la tensione che apre**: *il peso di una convivenza
> sulla composizione di una zona è funzione della **partizione**, non
> del comune* — stesso comune con più zone, effetto minore. È un
> argomento a favore delle partizioni fini, in tensione diretta con
> l'argomento sulla taglia minima che ha escluso Carpi (§13.1).

---

## 14. L'anello 3: dalla zona alla sezione

**misurato** (lettura di `scripts/attributi/enrich.py`, 609 righe, e
`assign_nationality.py`).

### 14.1 Perché esiste

> *Il MaxEnt (anello 1) assegna il quartiere, che è il livello più fine
> a cui il censimento pubblica gli **incroci** necessari al solver.
> Sotto il quartiere esistono solo **marginali** di sezione, che si
> sfruttano meglio come condizionali post-hoc.*

È la stessa logica forma-non-livelli, applicata al confine
incroci/marginali invece che a quello forma/livelli. Cinque passi:

| passo | cosa aggiunge | condizionamento |
|---|---|---|
| **3a** | sezione di censimento | `P(σ \| zona, sesso, età3, cittadinanza)` |
| **3b** | area UE / EXTRA_UE | `P(area \| SEZIONE, sesso)` — **ri-assegnata** |
| **3c** | paese | `P(paese \| area, sesso)` — **ri-assegnato** |
| **3d** | età esatta in anni | sezione → quinquennio → anno singolo |
| **3e** | indirizzo e coordinate | civico ANNCSU dentro la sezione |

**3b e 3c sovrascrivono `assign_nationality`**, che condiziona l'area
sulla *zona*. Il motivo è §14.3.

### 14.2 L'assunzione (9), localizzata e delimitata

Dichiarata alla lettera nel docstring:

> *(9) entro il quinquennio, la distribuzione per anno singolo è quella
> comunale (anagrafe 1/1/anno), non quella di sezione.*

**misurato**, `assegna_eta`, le due righe che la realizzano:

```python
w  = [f * r[f"w_{s}_{k}"] for k, f, _, _ in blocchi]   # SEZIONE
pw = [eta_w[s].get(a, 0.0) for a in anni]              # COMUNE
```

> **La sezione decide quale quinquennio; il comune decide la forma
> dentro il quinquennio.** L'assunzione è scoped esattamente lì: la
> distribuzione *fra* quinquenni viene dalla sezione ed è un dato; solo
> la forma *entro* il quinquennio è trasportata dal comune.

Il precursore di §10.2 misura proprio quella quantità: la forma entro
bin varia fra 253 comuni di **0,075 anni** (sd). L'assunzione resta
indimostrabile in diretta — l'anno singolo per sezione non esiste — ma
la quantità trasportata è nazionale, non locale.

**Una seconda uniformità, minore e dichiarata.** `BIN_QUINQ` spezza il
quinquennio 5-9 fra il bin `0-8` e il bin `9-14` con pesi **0,8 / 0,2**:

```python
"0-8":  [(0, 1.0, 0, 4), (1, 0.8, 5, 8)],
"9-14": [(1, 0.2, 9, 9), (2, 1.0, 10, 14)],
```

Il commento la dichiara: *«si spezza 4/5 – 1/5 assumendo uniformità
entro il quinquennio»*. Il taglio a 9 anni viene dall'universo
istruzione ISTAT («9 anni e più»), non dalla griglia quinquennale.

> **congettura, non misurata.** §10.2 mostra che il bin 5-9 ha
> inclinazione **positiva** (+0,077 anni): i 9enni sono più di 1/5 del
> quinquennio. Il 4/5–1/5 uniforme sarebbe quindi leggermente
> sbilanciato, e in direzione *giovane* sul bin `0-8`. Effetto piccolo
> e confinato a due bin, ma è l'unico candidato residuo identificato
> per lo scarto 10/10 (§10.2). Da verificare, non da assumere.

### 14.3 Dove sta davvero il segnale spaziale

**misurato**, riportato nel docstring di `enrich` (Parma, quota UE):

```
tra zone          0,00110   (sd 0,033)
dentro le zone    0,01748   (sd 0,132)   di cui 0,00499 da discretizzazione
struttura REALE di sezione / struttura di zona  =  11,4×
sovradispersione contro assegnazione casuale entro zona  =  3,50
```

Con la precisazione che rende il numero interpretabile: *i conteggi
censuari sono **enumerazione completa, non stime**; la sovradispersione
misura struttura reale, non rumore campionario.*

> **Quasi tutta la struttura spaziale sta sotto il quartiere.** E
> `load_sezioni` lo generalizza in un commento: la zona trattiene fra
> il **2 % e il 20 %** del segnale compositivo.
>
> Conseguenza operativa: per un comune non articolato la zona degenere
> non è una perdita grave, perché *«il condizionamento si sposta
> interamente sulla sezione, che è il livello più fine disponibile e
> anche il più informativo»*.

### 14.4 Le altre assunzioni dell'anello 3

| # | enunciato | natura |
|---|---|---|
| **(8)** | sezione ⊥ (istruzione, condizione, background, origine) \| (zona, sesso, età3, cittadinanza) | **strutturale**: sotto il quartiere il censimento non pubblica quegli incroci |
| **(9)** | forma entro quinquennio = comunale | §14.2, sostenuta da §10.2 |
| **(10)** | indirizzo uniforme fra i civici della sezione | ANNCSU non dà residenti per civico |
| **(11)** | nessuna struttura familiare in `enrich` | i nuclei arrivano nell'anello 4 |

L'assunzione (8) è la più forte del passo, ed è **strutturale**: non è
una scelta fra alternative, è il confine oltre il quale il dato non
esiste. Stessa forma di §9 sul trade-off età/territorio.

**Cosa vincola davvero la sezione**: `assegna_sezione` usa i pesi
demografici quinquennali della sezione (`w_{sesso}_{k}`) moltiplicati
per la quota straniera per classe d'età a 3 livelli (`q_{sesso}_{età3}`,
da `ST25`–`ST30`). Con fallback dichiarato e **contato**: se la cella
(zona, sesso, bin, cittadinanza) è vuota si scende al solo peso
demografico, e il `print` riporta quante assegnazioni hanno usato l'uno
o l'altro livello.

### 14.5 Sezioni per zona nei 12 comuni articolati (ER)

**misurato** (file regionale R08; «abitate» esclude le sezioni con
P1 = 0, che non sono contenitori disponibili).

| comune | liv | zone | sez tot | vuote | sez/zona | **abitate/zona** | min–max | pop/zona | pop/sez |
|---|---|---|---|---|---|---|---|---|---|
| Bologna | ASC1 | 6 | 2 224 | 72 | 370,7 | **358,7** | 311–413 | 65 016 | 181,3 |
| Bologna | ASC2 | 18 | 2 224 | 72 | 123,6 | **119,6** | 48–208 | 21 672 | 181,3 |
| Bologna | ASC3 | **90** | 2 224 | 72 | 24,7 | **23,9** | 2–83 | 4 334 | 181,3 |
| Modena | ASC1 | 4 | 2 186 | 68 | 546,5 | **529,5** | 261–753 | 46 149 | 87,2 |
| Reggio E. | ASC1 | 4 | 1 813 | 98 | 453,2 | **428,8** | 316–665 | 42 802 | 99,8 |
| Rimini | ASC1 | 6 | 1 888 | 49 | 314,7 | **306,5** | 231–434 | 25 008 | 81,6 |
| Piacenza | ASC1 | 4 | 1 009 | 52 | 252,2 | **239,2** | 208–305 | 25 722 | 107,5 |
| Ravenna | ASC1 | 10 | 2 376 | 67 | 237,6 | **230,9** | 97–475 | 15 630 | 67,7 |
| Faenza | ASC1 | 5 | 674 | 29 | 134,8 | **129,0** | 36–244 | 11 769 | 91,2 |
| Cesena | ASC1 | 12 | 1 275 | 28 | 106,2 | **103,9** | 48–180 | 8 006 | 77,0 |
| Parma | ASC1 | 13 | 1 357 | 44 | 104,4 | **101,0** | 61–177 | 15 240 | 150,9 |
| Forlì | ASC1 | 21 | 1 519 | 41 | 72,3 | **70,4** | 28–167 | 5 574 | 79,2 |
| Carpi | ASC1 | 33 | 914 | 25 | 27,7 | **26,9** | 4–73 | 2 198 | 81,6 |
| Lugo | ASC1 | 14 | 219 | 8 | 15,6 | **15,1** | 4–47 | 2 302 | 152,7 |

**Come NON leggerla.** L'aspettativa naturale è che molte sezioni per
zona significhino molta libertà residua nell'assegnazione — cioè che
il segnale di sezione sia in gran parte artefatto del modello. §14.3
dice il contrario: la sezione porta marginali reali (`P1`, `ST1`,
`ST16`–`ST21`, quinquennali per sesso), e lì sta l'88-98 % del segnale
compositivo. Le 101 sezioni per zona di Parma **non** sono libertà: sono
dove il dato vive.

**Cosa la tabella misura davvero**: quanto il vincolo zonale del MaxEnt
stringa, prima che l'anello 3 intervenga. A Modena, 4 zone su 529
sezioni ciascuna: il blocco Z fissa un totale e l'assegnazione fine è
governata quasi interamente dai marginali di sezione. A Lugo, 15
sezioni per zona, il vincolo zonale è molto più stretto.

**Bologna è il controllo interno**: stesso comune, stesse 2 224
sezioni, tre risoluzioni — **358,7 → 119,6 → 23,9**, un fattore 15.

**E un secondo numero, non richiesto ma più insidioso.** `pop/sez`
varia di **2,7×** fra comuni: Bologna 181,3 contro Ravenna 67,7. *La
sezione di censimento non è un'unità di taglia comparabile fra comuni.*
Qualunque metrica per sezione confrontata fra comuni eredita questa
disomogeneità — è il principio già a registro (*normalizzare contro
l'ipotesi nulla*) applicato alla geometria invece che ai conteggi.

### 14.6 Correzione a v8 su `area`

> **Ritratto** parzialmente: avevo scritto che `area` è *«una colonna
> decorativa nel prodotto finale»*. Non è un vincolo — quello resta
> vero, non compare in nessun `VAR_ORDERS` — ma **non è decorativa**:
> `enrich.py:502` la confronta con `ST16`, il conteggio di stranieri UE
> **a livello di sezione**, in un audit. E in 3b viene ri-assegnata
> condizionando sulla sezione, non sulla zona.
>
> Rimuoverla dal viewer Animarium resta sicuro (è calcolata a monte, e
> `paese` la determina). Rimuoverla dalla **pipeline** romperebbe
> l'audit di sezione.

**misurato** (Brescia, `bundle/comuni/017029/pop.parquet`, 198 259
righe): `area` è NaN in 160 778 righe = **81,1 %**, coincidente con la
quota ITL; il viewer rende il NaN come «non applicabile». 100 paesi
distinti, **zero** con più di un'area: la dipendenza paese → area è
funzionale, quindi nessun bug residuo nella mappa.

---

## 15. Il pattern che la sessione ha reso visibile

Aggiunta v9 a §8, come sezione autonoma perché ricorre tre volte in un
giorno solo su tre oggetti diversi.

> **La correzione esiste, applicata a un ramo e non all'altro.**

| # | correzione | dove è applicata | dove manca |
|---|---|---|---|
| 1 | `_resolve_codelist_code` — riconcilia gli zeri iniziali | `fetch_comune.profile` | `sdmx.decode` (§6, #2) |
| 2 | `elementary_classes` — scarta i codici che ne contengono altri | `build_constraints`, **solo per l'età** | `EDU_ATTAIN`, `AREA_CONTRY_CITIZEN` (§11.3) |
| 3 | `AGGREGATI_PAESE` — lista esplicita invece di regex | `opendata`, `enrich`, `assign_nationality` | `build_constraints` (§6, #10) |

Non sono tre incidenti: è una **proprietà di come il progetto impara**.
Un problema viene incontrato in un punto, diagnosticato bene,
documentato in un commento, e corretto **lì**. Il ramo gemello resta
com'era, perché in quel momento non stava sbagliando in modo visibile.

**Conseguenza operativa.** Ogni volta che si scrive un commento del
tipo *«questo era un bug, ora filtriamo per codice»*, la domanda
successiva è: **quali altri punti fanno la stessa cosa nel modo
vecchio?** Un `grep` sul meccanismo — non sul sintomo — costa poco e
chiude la classe invece del caso.

Vale anche per la generalizzazione mancata: `elementary_classes` non è
un bug, è una soluzione corretta con **dominio più stretto del
problema**. Riconoscere che il dominio è più stretto è la stessa
operazione.

> Da mettere in §8 del report accanto al principio *«le somme aggregate
> non distinguono le strutture; la presenza per cella sì»*. Il primo
> riguarda come si legge un dato, il secondo come si propaga una
> correzione.
