# Il repertorio AVQ dei nuclei — firme, configurazioni, `gsp.nucleo`

**Versione 3.0 — 10 agosto 2026**
Mirko Degli Esposti · DIFA, Università di Bologna

Secondo documento sull'anello 4, dopo `nota_nucleo_familiare_v3.md` che
ne fissa l'architettura. Quella nota decide **dove** entra la struttura
familiare; questa stabilisce **con quale materiale** si costruisce,
**quanto costa** costruirla, e documenta il modulo che la costruisce.

*Changelog v3.0 — aggiunta §7: il modulo `gsp.nucleo` e il collaudo sulla
popolazione sintetica di Parma. Il risultato principale è una
**incoerenza trovata e corretta**: la v1 del modulo ignorava
`stato_civile` e produceva due coniugati su tre sposati con nessuno,
senza che nessuna metrica lo segnalasse. §7.2 documenta il difetto, la
correzione e il residuo che resta.*

---

## 1. Cosa fa l'anello 4, e cosa non fa

> **La popolazione sintetica non si tocca.** L'anello 4 aggiunge
> `id_nucleo` e `ruolo`, nient'altro. Gli individui restano quelli
> vincolati dall'anello 1, allocati per sezione dall'anello 3, con le
> loro AVQ. Rimosse le due colonne, la popolazione torna identica byte a
> byte.

Ne segue una decisione che sembrava aperta e non lo è. Si era considerato
di **donare il nucleo AVQ intero**, il che avrebbe anche risolto
un'incoerenza nota (due individui dello stesso nucleo hanno AVQ da
donatori indipendenti, mentre ρ ≈ 0,6 dice che in famiglia le opinioni si
condividono, v22 §13.5). **È impraticabile**: sostituire individui
vincolati dal MaxEnt con componenti campionari distruggerebbe l'anello 1.

Meccanismo, sezione per sezione:

1. la sezione ha N individui dall'anello 3 e i vincoli `PF3`–`PF8`;
2. da lì si sa quanti nuclei di ciascuna ampiezza servono;
3. per ciascuno si estrae una **firma** dal repertorio condizionato
   all'ampiezza;
4. la firma definisce degli **slot**, riempiti con gli individui della
   sezione secondo i criteri di §5;
5. la copertura è totale per costruzione: Σ k × (famiglie da k) = N.

---

## 2. La fonte, e due scelte deliberate

Microdati AVQ 2022–2024. Chiave del nucleo: **`ANNO|PROFAM`**.

| | Emilia-Romagna | Lombardia | unito |
|---|---:|---:|---:|
| componenti | 7.061 | 11.942 | 19.003 |
| nuclei | 3.233 | 5.210 | 8.443 |

**Si usano tutte e tre le annate**: il 2022 è escluso dal pool
dell'anello 2 perché gli manca `CRONI`, variabile *target* che alla
struttura familiare non serve. **Non si filtra `ISTRMi = 99`**: scartare
un componente mutila il nucleo.

### 2.1 I nuclei sono completi — *misurato*

Zero nuclei senza riferimento, zero con due riferimenti, zero con due
partner, zero `RELPAR` non mappate, su 8.443 nuclei. Conferma
indipendente: `NCOMP` dichiarato coincide **esattamente** con l'ampiezza
osservata in ogni classe.

L'invariante è ora un controllo in `costruisci_repertorio`: se cade, il
modulo solleva invece di costruire in silenzio.

### 2.2 La classificazione operativa

| sigla | classe | modalità AVQ |
|---|---|---|
| R | riferimento | 01 |
| P | partner | 02 coniuge · 03 convivente coniugalmente |
| F | figlio | 06 ultima unione · 07 unione precedente |
| G | genitore | 04 di PR · 05 del partner |
| A | altro parente | 08–16 |
| N | non parente | 17 amicizia |

**02 e 03 restano distinti** nella colonna fine. Decisione presa per la
questione del codice 11 di Parma, che si è poi rivelata **necessaria
anche per lo stato civile** (§7.2): due `celibe_nubile` insieme sono una
convivenza, non un errore.

---

## 3. Le firme — quali configurazioni esistono

| | firme distinte | 90% dei nuclei in | 95% in |
|---|---:|---:|---:|
| 17 modalità grezze | 172 | 9 | 17 |
| classificazione operativa | 70 | **6** | 9 |

| ampiezza | nuclei | firme | dominante | quota |
|---|---:|---:|---|---:|
| 1 | 2.793 | 1 | `R` | 1,00 |
| 2 | 2.652 | 5 | `RP` + `RF` | 0,93 |
| 3 | 1.523 | 13 | `RPF` + `RFF` | 0,93 |
| 4 | 1.140 | 15 | `RPFF` | **0,91 da sola** |
| 5 | 249 | 15 | `RPFFF` | 0,74 |
| 6+ | 86 | 13 | `RPFFFF` | 0,53 |

**Il 96% dei nuclei ha ampiezza ≤ 4**, e lì una o due firme coprono il
90%.

TVD fra le due regioni: 0,0681, ma **dominato dalle ampiezze**, che
arriveranno da `PF3`–`PF8`. Condizionando sull'ampiezza sono simili. La
misura giusta — media dei TVD entro ampiezza — non è stata fatta (§9.1).

---

## 4. Le configurazioni interne

`ETAMi` è categorica: quindici classi irregolari, l'ultima aperta. I
divari si calcolano sui centri di classe.

### 4.1 Il divario generazionale è il vincolo forte

| divario | n | p05 | p25 | mediana | p75 | p95 |
|---|---:|---:|---:|---:|---:|---:|
| riferimento − figlio | 5.395 | +21,0 | +27,5 | **+33,0** | +38,5 | +45,0 |
| fra fratelli consecutivi | 1.907 | 0,0 | +2,0 | **+4,0** | +7,0 | +11,0 |

### 4.2 Il divario fra partner NON è determinabile con l'AVQ

Mediana e p75 a zero **non** significano stessa età: significano stessa
**classe**. Il divario reale (~3 anni in Italia) è sotto la risoluzione
dello strumento. **Parma non può supplire**: ha l'età esatta ma nessun
identificativo di famiglia.

### 4.3 Il riferimento è sbilanciato, in due direzioni opposte

`RP` 0,828 maschi · `RPFF` 0,792 · `R` 0,468 · **`RF` monogenitore
0,191**. `RP` è **bimodale** (coppie giovani e nidi vuoti): mediana ~70
contro ~50 di `RPF`.

### 4.4 Coppie dello stesso sesso: esattamente zero

0,000 su 4.525 partner — strutturale, non campionario. **La popolazione
sintetica eredita l'assenza.**

### 4.5 La cittadinanza è una preferenza

Fra i nuclei con almeno uno straniero, **omogenei solo al 45%**: la
maggioranza sono misti. Il 94,4% complessivo è dominato dai nuclei tutti
italiani.

### 4.6 I genitori conviventi non si leggono

n = 175, il **45% tocca la classe aperta**. I limiti sono presi per
analogia e dichiarati. È **il parametro più debole**, e il collaudo lo
conferma: 621 ripieghi `G fuori dai limiti`, il secondo per frequenza.

---

## 5. I criteri di compatibilità

| slot | vincolo | forza |
|---|---|---|
| R in coppia | maschio con p ≈ 0,80 | preferenza |
| R monogenitore | femmina con p ≈ 0,81 | preferenza |
| R senza partner | preferisci `vedovo` | preferenza |
| P | **stesso `stato_civile`** del riferimento | **forte** (§7.2) |
| P | sesso opposto | rigido |
| P | età entro ±15 anni | **convenzionale** |
| F | riferimento − figlio in [21, 45] | forte |
| F secondo | entro 11 anni dal fratello | forte |
| G | riferimento + [20, 40] | **dichiarato**, il più debole |
| cittadinanza | omogenea con p ≈ 0,55 nei misti | preferenza |

---

## 6. Il prototipo — la fattibilità non è un problema

Algoritmo avido, senza backtracking, su Parma anagrafica:

| sezione | individui | nuclei | slot con ripiego |
|---|---:|---:|---:|
| 689 | 38 | 18 | 0 |
| 1055 | 136 | 57 | 2 (1,5%) |
| 1260 | **1.837** | **748** | **0** |

Divario generazionale dentro [21, 45] nel 100% dei casi.

> La domanda era «l'1% o il 15%?». La risposta è **sotto l'1%**. La
> preoccupazione sulla coda dell'assemblaggio era infondata, e la scelta
> fra valvole di sfogo non si pone.

**L'accuratezza del ruolo (59%) non è una metrica valida**: gli errori
R↔P sono lo stesso errore contato due volte. Chi sia la «persona di
riferimento» in una coppia non è una proprietà della famiglia, è chi ha
firmato in anagrafe. La metrica giusta — se due persone insieme nella
realtà finiscano insieme nel sintetico — **non è misurabile con le fonti
disponibili**.

---

## 7. `gsp.nucleo` e il collaudo sulla popolazione sintetica

`src/gsp/nucleo.py`, quattro funzioni; l'I/O in
`scripts/attributi/assign_nucleo.py`. Repertorio precalcolato in
`data/repertorio_nuclei_v1.json`, versionabile e citabile.
Collaudo: `scripts/diagnostica/collaudo_nucleo.py`.

### 7.1 I vincoli di sezione: tre casi, tutti ordinari

```
residuo = N − Σ k·PF_{k+2}          (k = 1..6)
```

| caso | trattamento | Parma |
|---|---|---:|
| `residuo ≤ 0` | riduci le ampiezze maggiori | 372 sezioni |
| `0 < residuo ≤ 6·PF8` | `PF8` («6 e oltre») era troncata: allarga dalla coda | 255 |
| `residuo > 6·PF8` | il resto è **convivenza**, senza nucleo | 297 |
| esatto | — | 389 |

> **`sovrastima` non è un difetto.** Il totale comunale coincide con `P1`
> per costruzione, ma l'anello 3 alloca per sezione con MAE 0,74–1,58: uno
> scarto di un'unità basta a invertire il segno del residuo, e succede in
> circa metà delle sezioni. Il nome è fuorviante e andrebbe cambiato.

La separazione fra troncamento e convivenza usa il criterio locale
`6·PF8`. Su Parma separa 791 persone da 2.770, e le seconde vanno
confrontate con le **3.096 convivenze anagrafiche**: scarto 11%, con due
fonti e due anni diversi.

### 7.2 Il difetto che nessuna metrica segnalava

La v1 del modulo usava sesso, età e ampiezza. **Ignorava
`stato_civile`**, che però è vincolato dal MaxEnt in anello 1.

Il risultato non era rumore statistico ma **contraddizione logica dentro
lo stesso individuo**:

| | v1 |
|---|---:|
| coppie con lo stesso stato civile | **51,0%** |
| coppie con entrambi coniugati | 29,6% |
| coniugati in nucleo di 2+ senza altro coniugato | **26,6%** (21.431) |
| rapporto 2·coppie_coniugate / coniugati, mediana | **0,301** |

Cioè **due coniugati su tre risultavano sposati con nessuno**. Le
combinazioni implausibili erano in cima alla classifica: 7.240 coppie
coniugato+celibe, 2.850 vedovo+coniugato.

> **La v1 riportava «99,3% di nuclei perfetti».** Quella metrica contava
> solo i ripieghi su età e sesso — cioè esattamente ciò che l'algoritmo
> ottimizzava. Misurava il proprio criterio, non la qualità del
> risultato. È il modo tipico in cui un difetto grosso resta invisibile.

**La correzione**: lo slot `P` richiede lo **stesso** stato civile del
riferimento. Non che la coppia sia coniugata — due `celibe_nubile`
insieme sono una convivenza, che nel repertorio è `RELPAR` 03. Ed è
aritmeticamente necessario: ~42.000 coppie richiederebbero ~84.000
coniugati e ce ne sono 80.640, di cui un quinto vive solo. I `vedovo`
sono esclusi dallo slot `P` e preferiti come riferimento di firme senza
partner.

### 7.3 Il risultato, e il residuo che resta

| | v1 | **v2** |
|---|---:|---:|
| coppie con lo stesso stato civile | 51,0% | **96,5%** |
| coppie con entrambi coniugati | 29,6% | **54,0%** |
| coniugati incoerenti | 26,6% | **8,9%** (7.182) |
| rapporto di conteggio, mediana | 0,301 | **0,564** |
| nuclei senza alcun ripiego | 99,3% | 97,8% |
| coppie coniugato+celibe | 7.240 | **480** |

Il costo del vincolo è basso: 1.204 ripieghi `P stato civile diverso` su
42.421 coppie, il **2,8%**.

> **La soglia «vicino a 1» che la v2 di questa nota indicava era
> sbagliata.** Il 21,6% dei coniugati vive in nuclei unipersonali —
> coniugi non conviventi, legittimi. Restano 63.222 coniugati in nuclei
> plurimi, quindi al massimo 31.611 coppie, e il **tetto teorico del
> rapporto è 0,784**, non 1. Con 0,564 siamo al **72% del massimo
> possibile**.

**Il residuo dell'8,9% è strutturale, non un bug.** Le firme si estraggono
dal repertorio *prima* di guardare chi c'è nella sezione: se una sezione
ha 40 coniugati in nuclei plurimi e il repertorio chiede 15 coppie e 25
monogenitori, dieci coniugati restano spaiati comunque. Concorrono anche
il vincolo d'età (293 ripieghi) e il fatto che l'anello 3 non garantisce
un numero pari di coniugati per sezione.

**Correggerlo richiederebbe un passo di aggiustamento** fra
`vincoli_da_sezione` e `assembla`, che scelga le firme guardando la
composizione della sezione. Non c'è, ed è dichiarato (§9.2).

### 7.4 Il resto del collaudo

**Fattibilità**: 198.121 individui, 94.484 nuclei, 97,8% senza alcun
ripiego, 1,85% non collocati di cui 2.884 convivenza dichiarata.

**Divari**: generazionale mediana 30 (target AVQ 33), fuori dai limiti
nello 0,05%. Partner mediana −1, p05 −14, p95 +14 — il limite
convenzionale ±15 morde, e le code si sono strette rispetto ai ±20 del
prototipo.

*`eta_anni` nella popolazione sintetica è pescata **uniforme nel bin**: i
divari ottenuti sono più dispersi di quelli reali, e il rumore sta
nell'età, non nell'assemblaggio.*

**Un peggioramento non previsto**: `G fuori dai limiti` sale da 385 a
621. Ipotesi non verificata: preferendo i vedovi come riferimento di
firme senza partner, gli slot `G` capitano più spesso con riferimenti
giovani, che richiederebbero genitori ancora più anziani. Effetto
collaterale del vincolo nuovo sul parametro già più debole.

---

## 8. EU-SILC: cosa si può fare col PUF, e cosa no

Il PUF è **completamente sintetico** per dichiarazione Eurostat, con
struttura identica al SUF.

**Si può fare ora**: scrivere e collaudare il parser D/H/R/P, la
ricostruzione del grafo di parentela, la funzione che estrae i divari.
Tutto il codice che poi girerà sul SUF.

**Non si può fare**: prendere i numeri. Sono un artefatto della sintesi
Eurostat.

**Un uso legittimo**: verificare che il PUF riproduca le distribuzioni
AVQ dove si sovrappongono. È un test del software, non una stima.

Il motivo per cui il SUF serve davvero non è il partner: è che **nessuna
fonte disponibile permette di validare l'assemblaggio a livello di
nucleo**.

---

## 9. Punti aperti

**9.1 Il TVD fra regioni condizionato sull'ampiezza** (§3). Una riga.

**9.2 Il residuo dell'8,9% sui coniugati** (§7.3). Richiede un passo di
aggiustamento fra vincoli e assemblaggio. **Dichiarato come limite**, non
in programma.

**9.3 L'indirizzo è assegnato per individuo.** Marito e moglie possono
risultare a due civici diversi. Incoerenza che l'anello 4 rende visibile
e non risolve: con i nuclei l'indirizzo va assegnato **per famiglia**, il
che è anche il presupposto dell'assegnazione a edificio.

**9.4 Le AVQ dentro il nucleo restano scorrelate** (ρ ≈ 0,6 nella
realtà). Non risolvibile senza toccare l'anello 2.

**9.5 Il parametro `G`** è il più debole e il collaudo lo conferma (621
ripieghi). Candidato numero uno per il SUF.

**9.6 Il rischio che l'AVQ porta con sé**: nessuna combinazione AVQ
riproduce il 52% di stranieri del codice 11 di Parma. Se le convivenze
migranti sono ciò che l'AVQ cattura peggio, il repertorio è inadeguato
proprio per la tipologia di nucleo più difficile.

**9.7 `assign_nucleo.py`** non è ancora scritto: il collaudo gira su uno
script diagnostico. Serve per portare l'anello 4 in produzione sugli
undici comuni.

**9.8 Trasferibilità**: il collaudo è solo su Parma, da cui viene anche
la coda del repertorio. Va rifatto su Bologna e Brescia prima di
considerarlo generale.

---

## 10. Per il paper

Due elementi metodologici di questa linea meritano di uscire:

**La metrica che misura il proprio criterio.** Il «99,3% di nuclei
perfetti» era vero e inutile: contava i ripieghi sui vincoli che
l'algoritmo imponeva, ed era cieco a una violazione che riguardava un
quarto della popolazione coniugata. Il rimedio non è una metrica
migliore, è **una metrica costruita su un vincolo che l'algoritmo non
usa** — qui `stato_civile`, che veniva da un altro anello.

**Il tetto teorico prima della soglia.** «Il rapporto dovrebbe stare
vicino a 1» era una soglia plausibile e sbagliata: l'aritmetica della
popolazione lo limita a 0,784. Stessa famiglia di errori del pavimento di
rumore — un numero non si legge senza il suo riferimento, e il
riferimento va calcolato, non intuito.
