# Il repertorio AVQ dei nuclei — firme e configurazioni interne

**Versione 1.0 — 9 agosto 2026**
Mirko Degli Esposti · DIFA, Università di Bologna

Secondo documento sull'anello 4, dopo `nota_nucleo_familiare_v3.md` che
ne fissa l'architettura. Quella nota decide **dove** entra la struttura
familiare; questa stabilisce **con quale materiale** si costruisce.

L'AVQ campiona famiglie e intervista tutti i componenti. `PROFAM` le
ricostruisce intere, e con `RELPAR` fornisce anche il ruolo. Diventa
quindi il **repertorio** dell'assemblaggio: dice quali configurazioni
esistono e chi ci sta dentro.

---

## 1. Cosa fa l'anello 4, e cosa non fa

> **La popolazione sintetica non si tocca.** L'anello 4 aggiunge una
> colonna `id_nucleo` e nient'altro. Gli individui restano quelli
> vincolati dall'anello 1, allocati esattamente per sezione dall'anello
> 3, con le loro AVQ. Togliendo la colonna la popolazione torna identica
> byte a byte.

Ne segue una decisione che sembrava aperta e non lo è. Si era considerato
di **donare il nucleo AVQ intero** — prendendo i suoi componenti come
individui sintetici, il che avrebbe anche risolto un'incoerenza nota
(oggi due individui dello stesso futuro nucleo hanno AVQ da donatori
indipendenti, mentre ρ ≈ 0,6 dice che in famiglia le opinioni si
condividono, v22 §13.5).

**È impraticabile**: sostituire individui vincolati dal MaxEnt con
componenti campionari distruggerebbe l'anello 1, i cui totali coincidono
col censimento e la cui allocazione per sezione ha MAE 0,74–1,58. Il
repertorio serve quindi a dire **quali configurazioni sono plausibili**,
non a fornire persone.

Meccanismo, sezione per sezione:

1. la sezione ha N individui dall'anello 3 e i vincoli `PF3`–`PF8`;
2. da lì si sa quanti nuclei di ciascuna ampiezza servono;
3. per ciascuno si estrae una **firma** dal repertorio condizionato
   all'ampiezza;
4. la firma definisce degli **slot**, che si riempiono con gli individui
   della sezione secondo i criteri di compatibilità di §4;
5. la copertura è totale per costruzione, perché Σ k × (famiglie da k) = N
   — verificato esatto a Parma, 96.984 contro 96.985.

---

## 2. La fonte, e due scelte deliberate

Microdati AVQ 2022, 2023, 2024. Chiave del nucleo: **`ANNO|PROFAM`** —
`PROFAM` riparte da 1 ogni anno.

| | Emilia-Romagna | Lombardia | unito |
|---|---:|---:|---:|
| componenti | 7.061 | 11.942 | 19.003 |
| nuclei | 3.233 | 5.210 | 8.443 |
| ampiezza media | 2,18 | 2,29 | 2,25 |

Due differenze deliberate rispetto ad `assign_avq.py`:

**Si usano tutte e tre le annate.** Il 2022 è escluso dal pool
dell'anello 2 perché gli manca `CRONI`, che è una variabile *target*: la
struttura familiare non ne ha bisogno. Il pool emiliano passa da ~2.000 a
3.233 nuclei, +50% su una risorsa scarsa.

**Non si filtra `ISTRMi = 99`.** Per l'anello 2 è un donatore in meno;
qui scartare un componente **mutila il nucleo**, e una famiglia da quattro
diventa una terna falsa.

### 2.1 I nuclei sono completi — *misurato*

| controllo | esito |
|---|---|
| nuclei senza riferimento | **0** |
| nuclei con 2+ riferimenti | **0** |
| nuclei con 2+ partner | **0** |
| individui con `RELPAR` non mappata | **0** |

Su 8.443 nuclei e tre annate. Conferma indipendente: `NCOMP` dichiarato
coincide **esattamente** con l'ampiezza osservata in ogni classe (1.136
nuclei da uno ↔ 1.136 individui con `NCOMP=1`; 381 da quattro ↔ 1.524; e
così via). Se anche un solo componente mancasse la colonna si
sfalserebbe.

`RELPAR = 1` compare 3.233 volte in Emilia, cioè una per nucleo.

### 2.2 La classificazione operativa

Da `METADATI/Classificazioni/AVQ_Classificazione_2024_var5.html`. Le 17
modalità AVQ collassano in sei classi, con mappa in dizionario esplicito
(`avq_firme.py`):

| sigla | classe | modalità AVQ |
|---|---|---|
| R | riferimento | 01 |
| P | partner | 02 coniuge · 03 convivente coniugalmente |
| F | figlio | 06 ultima unione · 07 unione precedente |
| G | genitore | 04 di PR · 05 del partner |
| A | altro parente | 08–16 |
| N | non parente | 17 amicizia |

Due decisioni prese esplicitamente:

**02 e 03 restano distinti** nella colonna fine. La fusione costerebbe
l'unica distinzione utile alla questione del codice 11 di Parma, e coppie
di fatto e coniugate hanno profili diversi.

**`altro_parente` accorpa nove modalità** in una classe da ~250 nuclei:
grossolano, ma separare i nipoti darebbe classi da 56 e da poche decine.
La mappa è un dizionario, cambiarla è una riga.

---

## 3. Le firme — quali configurazioni esistono

Una firma è la stringa dei ruoli ordinati: `RPFF` = riferimento, partner,
due figli.

| | firme distinte | 90% dei nuclei in | 95% in |
|---|---:|---:|---:|
| 17 modalità grezze | 172 | 9 | 17 |
| classificazione operativa | 70 | **6** | 9 |

La classificazione dimezza le firme senza perdere copertura.

### 3.1 Il risultato che semplifica l'assemblaggio

Dentro ogni classe di ampiezza la struttura è **quasi determinata**:

| ampiezza | nuclei | firme | firma dominante | quota |
|---|---:|---:|---|---:|
| 1 | 2.793 | 1 | `R` | 1,00 |
| 2 | 2.652 | 5 | `RP` 0,72 + `RF` 0,21 | 0,93 |
| 3 | 1.523 | 13 | `RPF` 0,79 + `RFF` 0,14 | 0,93 |
| 4 | 1.140 | 15 | `RPFF` | **0,91 da sola** |
| 5 | 249 | 15 | `RPFFF` | 0,74 |
| 6+ | 86 | 13 | `RPFFFF` | 0,53 |

**Il 96% dei nuclei ha ampiezza ≤ 4**, e lì una o due firme coprono il
90%. La preoccupazione sulla coda dell'assemblaggio — fino a 748 famiglie
in una sezione — si ridimensiona: sono molti problemi quasi tutti banali.

### 3.2 I due pool si possono unire, ma il test va rifatto

TVD fra le distribuzioni di firme delle due regioni: **0,0681**. Sembra
grande, ma è dominato dalle **ampiezze** — la Lombardia ha più `RPFF`
(0,1345 contro 0,1033) e meno `R` (0,318 contro 0,351) — e l'ampiezza
arriverà da `PF3`–`PF8`, non dal repertorio.

Condizionando sull'ampiezza le due regioni sono molto simili: `RP` 0,72
in entrambe, `RPF` 0,75 contro 0,81, `RPFF` 0,88 contro 0,92. **La misura
giusta è la media dei TVD entro ampiezza**, pesata, e non è stata fatta:
è una riga in `avq_firme.py` (§7.1).

Unire i pool è comunque un'assunzione **in più** rispetto all'anello 2,
dove le regioni restano separate perché le AVQ sono attitudinali. Qui
l'ipotesi è che la struttura interna di un nucleo da quattro sia la
stessa a Brescia e a Parma.

---

## 4. Le configurazioni interne — chi sta dentro le firme

Misurate su `ETAMi`, che è **categorica** — quindici classi irregolari da
3 a 10 anni, l'ultima aperta. I divari si calcolano sui **centri di
classe**, non sui codici: dalla 003 alla 004 sono cinque anni, dalla 009
alla 010 sono dieci. Dove la classe aperta 75+ pesa più del 2% dei casi
il centro è una convenzione e il numero va letto con riserva.

### 4.1 Il divario generazionale è il vincolo forte, ed è ben determinato

| divario | n | p05 | p25 | mediana | p75 | p95 |
|---|---:|---:|---:|---:|---:|---:|
| riferimento − figlio | 5.395 | +21,0 | +27,5 | **+33,0** | +38,5 | +45,0 |
| fra fratelli consecutivi | 1.907 | 0,0 | +2,0 | **+4,0** | +7,0 | +11,0 |

Distribuzione stretta e plausibile. È il criterio operativo: dato un
riferimento di 45 anni, uno slot «figlio» va riempito con qualcuno fra 0
e 24, con il grosso fra 6 e 18.

### 4.2 Il divario fra partner NON è determinabile con l'AVQ

| | n | p05 | p25 | mediana | p75 | p95 |
|---|---:|---:|---:|---:|---:|---:|
| tutti i partner | 4.525 | −12,5 | −7,5 | **0,0** | **0,0** | +10,0 |
| 02 coniuge | 3.855 | −12,5 | −7,5 | 0,0 | 0,0 | +7,5 |
| 03 convivente | 670 | −10,0 | −7,5 | 0,0 | 0,0 | +10,0 |

> Mediana e p75 a **zero non significano che i partner abbiano la stessa
> età**: significano che cadono nella **stessa classe**. Con classi larghe
> 5–10 anni, metà delle coppie finisce nello stesso bin, e il divario
> reale — in Italia mediana ~3 anni, uomo più vecchio — è **sotto la
> risoluzione dello strumento**.

Si legge solo l'asimmetria: p25 −7,5 contro p95 +10, partner più giovane
del riferimento, coerente con l'80% di riferimenti maschi (§4.3).

**Parma non può supplire.** Ha l'età esatta in anni ma **nessun
identificativo di famiglia**: solo `Ncomp` e `Relpar` per individuo. Dà
le marginali ruolo × età, non i divari dentro il nucleo.

È l'argomento più forte per il **SUF di EU-SILC**, che ha età esatte e
nuclei interi. Nel frattempo il vincolo sarà «stessa classe o una
adiacente»: grossolano, non assurdo.

### 4.3 Il riferimento è fortemente sbilanciato, in due direzioni opposte

| firma | n | quota maschi | età mediana |
|---|---:|---:|---:|
| `RP` | 1.912 | **0,828** | ~70 |
| `RPFF` | 1.035 | 0,792 | ~50 |
| `RPF` | 1.205 | 0,784 | ~50 |
| `R` unipersonale | 2.793 | 0,468 | ~62 |
| `RF` monogenitore | 570 | **0,191** | ~57 |

Nelle coppie il riferimento è maschio in quattro casi su cinque; nei
monogenitori è **donna** in quattro su cinque. Entrambe vanno riprodotte:
il capofamiglia sintetico uscirebbe altrimenti sbagliato di genere in
modo visibile in una scheda individuo.

**Avvertenza su `RP`**: mediana ~70 anni contro ~50 di `RPF`. La firma
unisce coppie giovani senza figli e nidi vuoti, quindi è **bimodale** e
la mediana non la descrive. Per l'assemblaggio serve la distribuzione.

### 4.4 Le coppie dello stesso sesso sono esattamente zero

**0,000 su 4.525 partner.** Con una prevalenza anche minima se ne
aspetterebbero alcune decine: è **strutturale**, non campionario — o il
questionario non lo prevede, o un controllo di coerenza le esclude.

Va dichiarato come proprietà della fonte, perché **la popolazione
sintetica erediterà quell'assenza**.

### 4.5 La cittadinanza è una preferenza, non un vincolo

| | nuclei | omogenei |
|---|---:|---:|
| con 2+ componenti a cittadinanza nota | 5.601 | 0,944 |
| **con almeno uno straniero** | **567** | **0,450** |

Il 94,4% complessivo è ingannevole: è dominato dai nuclei tutti italiani,
omogenei per definizione. Il numero informativo è il secondo — **la
maggioranza dei nuclei che contengono uno straniero sono misti**.

Si aggancia all'anomalia del codice 11 di Parma
(`nota_nucleo_familiare_v3` §2.4): se le convivenze miste sono la norma,
un codice residuo con il 52% di stranieri è meno strano di quanto
sembrasse.

*Cautele*: `CITTMi` è ricostruita, il campione straniero è
autoselezionato sulla competenza linguistica (v22 §8), e 567 nuclei sono
pochi. Il 45% è indicativo.

### 4.6 I genitori conviventi non si leggono

n = 175 e il **45% tocca la classe aperta 75+**, dove il centro è
convenzione. La mediana +27,5 è inutilizzabile. Per gli slot `G` il
vincolo andrà preso per analogia dal divario generazionale rovesciato,
dichiarandolo.

---

## 5. I criteri di compatibilità che ne discendono

Bozza operativa per il prototipo. Ogni riga è un vincolo su chi può
riempire uno slot, dato il riferimento già scelto.

| slot | vincolo | forza | fonte |
|---|---|---|---|
| R in coppia | maschio con p ≈ 0,80 | preferenza | §4.3 |
| R monogenitore | femmina con p ≈ 0,81 | preferenza | §4.3 |
| P | stessa classe d'età o adiacente; sesso opposto | debole per l'età, **rigido** per il sesso | §4.2, §4.4 |
| F | riferimento − figlio in [21, 45], centro 33 | **forte** | §4.1 |
| F secondo | entro 11 anni dal fratello | forte | §4.1 |
| G | riferimento + [20, 40], per analogia | dichiarato | §4.6 |
| cittadinanza | omogenea con p ≈ 0,55 nei nuclei misti | preferenza | §4.5 |

---

## 6. Un rischio che l'AVQ porta con sé

`nota_nucleo_familiare_v3` §2.4 registra che **nessuna combinazione AVQ
riproduce il 52% di stranieri del codice 11 di Parma**: il massimo è il
37% del solo codice 17, la miscela larga sta al 20%.

Ipotesi non verificata: le convivenze migranti sono ciò che l'AVQ cattura
peggio — autoselezione linguistica, e un'indagine su famiglie anagrafiche
fatica a intercettare coabitazioni instabili.

> **Se fosse così, l'AVQ sarebbe un repertorio inadeguato proprio per la
> tipologia di nucleo più difficile da assemblare.** Da verificare prima
> di considerare chiuso il repertorio.

---

## 7. Punti aperti

**7.1 Il TVD fra regioni condizionato sull'ampiezza** (§3.2). Una riga, e
decide se unire i pool.

**7.2 La distribuzione del riferimento in `RP`**, che è bimodale (§4.3):
serve la distribuzione, non la mediana.

**7.3 Il SUF di EU-SILC** per i divari d'età esatti (§4.2). Ora è
l'argomento più forte per richiederlo: nessun'altra fonte disponibile ha
insieme nuclei interi ed età in anni.

**7.4 Il prototipo su una sezione di Parma.** Quanti slot restano senza
candidato plausibile con i criteri di §5. Se è l'1% si rilassa la
compatibilità; se è il 15% serve un algoritmo che ottimizzi invece di
riempire avidamente. È il prossimo passo.

**7.5 La scelta fra le due valvole di sfogo**, quando uno slot non si
riempie: rilassare la compatibilità d'età (nuclei tenuti insieme male,
vincoli rispettati) o rilassare `PF3`–`PF8` (nuclei plausibili, vincoli
violati). Il precedente dell'anello 3 è il vincolo esatto, ma lì l'unità è
indivisibile e qui va composta. Decisione da prendere col numero di §7.4.

**7.6 Le AVQ dentro il nucleo restano scorrelate.** ρ ≈ 0,6 per la
fiducia istituzionale dice che in famiglia le opinioni si condividono; la
popolazione sintetica non lo riprodurrà, perché l'anello 2 dona per
individuo. È un limite noto e **non risolvibile** senza toccare l'anello
2 — ma ora è visibile, e va dichiarato fra le assunzioni.
