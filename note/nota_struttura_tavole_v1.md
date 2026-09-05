# Nota — struttura delle tavole ISTAT: anagrafe, censimento, dimensioni interne

*Sessione del 5 settembre 2026. Ogni voce marcata **misurato**, **dedotto**
o **aperto**. Le ritrattazioni sono esplicite e conservate.*

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
`gsp.common.COMUNI`. ‹N esatto da riportare: lo script ha girato sulla
flotta, il conteggio non è stato stampato.›

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

**difetto aperto.** `cens_posizione_famiglia` **assente** dai
`_decoded.csv` di Brescia: la riga manca dalla matrice, e con essa le
colonne `HOUSEHOLD_TYPE`, `FAMILY_NUCLEI_TYPE`, `NUM_MEMB`. È la tavola
dell'anello 4. Da riacquisire prima di chiudere la tabella.

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

**aperto.** `AREA_CONTRY_CITIZEN` ha 169 codici che mescolano paesi
elementari e aggregati continentali (`XASI_C_S`, `AFR_N`, `EU28`,
`WORLD`, più `XEUR_NEU28_OTH` etichettato «aggregato che cambia nel
tempo»). Se anche lì i due livelli coesistono nella stessa colonna, il
filtro «ISO-2 = due caratteri alfabetici» è una convenzione nostra, non
una regola dichiarata dalla fonte. Da verificare con lo stesso metodo:
presenza per cella, non somme.

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

### 5.1 L'assunzione non dichiarata

**dedotto, da confermare nel codice.** `c3` è per classe d'età e
distingue `post_laurea` da `laurea_o_its`. Ma quella distinzione — `ML`
contro `RDD` — **nelle classi d'età non esiste**: c'è solo `ML_RDD`
aggregato (§4.1). Quindi `build_constraints` deve star ripartendo
`ML_RDD` dentro ogni classe d'età con la proporzione osservata **solo
sul totale**: 30 399 / 1 203, cioè 96,2 % / 3,8 %, applicata identica ai
25-49enni e agli ultrasessantacinquenni.

> È implausibile — la quota di dottorati non può essere la stessa nelle
> due classi — e ha **la stessa forma dell'assunzione (9)**: una
> ripartizione fine misurata a un livello aggregato e assunta costante
> nei sottogruppi.
>
> `RDD` vale l'1 % scarso della popolazione, quindi l'impatto pratico è
> piccolo. Ma va **dichiarata**: oggi `post_laurea` nella popolazione
> sintetica non porta informazione d'età.
>
> Prossimo passo: leggere `build_constraints` e confermare o smentire.
> Finora è dedotto dai totali.

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

---

## 6. Difetti aperti raccolti

| # | difetto | gravità |
|---|---|---|
| 1 | `cens_posizione_famiglia` assente dai `_decoded` di Brescia | blocca la matrice DSD completa |
| 2 | `REF_AREA_label` vuota: pandas legge `017029` come intero, `decode` fa `astype(str).map()` senza riconciliazione | silenzioso — **sesta comparsa** della trappola degli zeri iniziali |
| 3 | doppio conteggio in `count` di `nationality_conditional.csv` | cosmetico dove è usato, pericoloso se letto come popolazione |
| 4 | scarto di 8 unità fra `count` e 2 × `FJAN` | aperto |
| 5 | ripartizione `ML`/`RDD` costante fra classi d'età | dedotto, da confermare |
| 6 | `sdmx.fetch`: blocco `status_code == 404` duplicato, il secondo è morto | cosmetico |

Per il #2 la patch è di una riga: `dtype=str` in `sdmx.fetch`, oppure
portare `_resolve_codelist_code` dentro `decode`.

---

## 7. Verso la sezione nuova del report

La sessione ha prodotto il materiale per una sezione che oggi manca:
**quali dati censuari e anagrafici usiamo, e come da quelli si
costruiscono i blocchi C**. Le tabelle già misurate:

1. le due fonti e i loro assi (§1), con `MARITAL_STATUS` come
   giustificazione della gerarchia hard/soft;
2. la matrice DSD × modalità effettive (§3) — il disegno 2×2;
3. la struttura interna di `EDU_ATTAIN` (§4) come **caso esemplare**:
   totali di dimensione e alberi interni convivono, e vanno separati
   guardando la presenza per cella e non le somme;
4. le tre mappe dell'istruzione con le frecce di aggregazione (§5.2);
5. dai blocchi grezzi ai sedici del constraint set — undici completi,
   cinque parziali, con i complementi fuori universo.

Manca ancora, per (5), la stessa mappatura quantitativa sui **blocchi
Z**, che non vengono da SDMX ma da `build_zona_tables` — sezioni e open
data comunali. Stessa logica, altra fonte.

---

## 8. Nota di metodo

Il metodo che ha funzionato, e che le due ritrattazioni di §4.2 rendono
esplicito:

> **Le somme aggregate non distinguono le strutture; la presenza per
> cella sì.** Ogni volta che un rapporto sospetto è stato letto su una
> somma (il fattore 2, l'albero, il residuo `−(ML+RDD)`) la lettura era
> sbagliata. La `crosstab` presenza × cella ha risolto in un colpo
> quello che tre giri di somme avevano confuso.

È il parente stretto di un principio già a registro — *ogni metrica che
scala col numero di celle va normalizzata contro la sua ipotesi nulla*.
Qui la variante: **prima di interpretare un rapporto, guardare dove le
celle esistono.**
