# Il repertorio AVQ dei nuclei — firme, configurazioni, `gsp.nucleo`

**Versione 3.1 — 10 agosto 2026**
Mirko Degli Esposti · DIFA, Università di Bologna

Secondo documento sull'anello 4, dopo `nota_nucleo_familiare_v3.md` che
ne fissa l'architettura. Quella nota decide **dove** entra la struttura
familiare; questa stabilisce **con quale materiale** si costruisce,
**quanto costa**, e documenta il modulo che la costruisce.

*Changelog v3.1 — la metrica sullo stato civile della v3.0 era troppo
debole e va sostituita (§7.3). Il numero corretto è 18–23%, non 8,9%, ma
scomposto racconta l'opposto: l'algoritmo accoppia bene, e l'incoerenza
sta dove il repertorio non prevede coppie. Aggiunto il collaudo su tre
comuni: **il repertorio è trasferibile** (§7.5).*

---

## 1. Cosa fa l'anello 4, e cosa non fa

> **La popolazione sintetica non si tocca.** L'anello 4 aggiunge
> `id_nucleo` e `ruolo`, nient'altro. Rimosse le due colonne, la
> popolazione torna identica byte a byte.

> **`stato_civile` non viene mai modificato.** Entra in `assembla` in
> sola lettura: serve a decidere *chi mettere con chi*, non a essere
> riscritto. I vincoli MaxEnt restano soddisfatti. La direzione della
> freccia è «lo stato civile vincola il nucleo», non «il nucleo
> determina lo stato civile».

Si era considerato di **donare il nucleo AVQ intero**, il che avrebbe
anche risolto un'incoerenza nota (ρ ≈ 0,6 sulla fiducia, v22 §13.5).
**È impraticabile**: sostituire individui vincolati dal MaxEnt con
componenti campionari distruggerebbe l'anello 1.

Meccanismo, sezione per sezione:

1. la sezione ha N individui dall'anello 3 e i vincoli `PF3`–`PF8`;
2. da lì si sa quanti nuclei di ciascuna ampiezza servono;
3. per ciascuno si estrae una **firma** dal repertorio condizionato
   all'ampiezza;
4. la firma definisce degli **slot**, riempiti con gli individui della
   sezione secondo i criteri di §5;
5. copertura totale per costruzione: Σ k × (famiglie da k) = N.

Il passo (3) è cieco alla composizione della sezione, e §7.4 mostra che
è lì che nasce il limite principale.

---

## 2. La fonte, e due scelte deliberate

Microdati AVQ 2022–2024. Chiave del nucleo: **`ANNO|PROFAM`**.

| | Emilia-Romagna | Lombardia | unito |
|---|---:|---:|---:|
| componenti | 7.061 | 11.942 | 19.003 |
| nuclei | 3.233 | 5.210 | 8.443 |

**Tutte e tre le annate**: il 2022 è escluso dall'anello 2 perché gli
manca `CRONI`, variabile *target* che qui non serve. **Non si filtra
`ISTRMi = 99`**: scartare un componente mutila il nucleo.

### 2.1 I nuclei sono completi — *misurato*

Zero nuclei senza riferimento, zero con due riferimenti, zero con due
partner, zero `RELPAR` non mappate, su 8.443 nuclei. `NCOMP` dichiarato
coincide esattamente con l'ampiezza osservata in ogni classe.
L'invariante è un controllo in `costruisci_repertorio`.

### 2.2 La classificazione operativa

| sigla | classe | modalità AVQ |
|---|---|---|
| R | riferimento | 01 |
| P | partner | 02 coniuge · 03 convivente coniugalmente |
| F | figlio | 06 ultima unione · 07 unione precedente |
| G | genitore | 04 di PR · 05 del partner |
| A | altro parente | 08–16 |
| N | non parente | 17 amicizia |

**02 e 03 restano distinti.** Decisione presa per la questione del codice
11 di Parma, rivelatasi **necessaria anche per lo stato civile**: due
`celibe_nubile` insieme sono una convivenza, non un errore.

---

## 3. Le firme

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

Il 96% dei nuclei ha ampiezza ≤ 4, e lì una o due firme coprono il 90%.

TVD fra le due regioni 0,0681, ma **dominato dalle ampiezze**, che
arriveranno da `PF3`–`PF8`. La misura giusta — media dei TVD entro
ampiezza — non è stata fatta (§9.1).

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
**classe**. Il divario reale (~3 anni) è sotto la risoluzione dello
strumento. **Parma non può supplire**: età esatta ma nessun
identificativo di famiglia.

### 4.3 Il riferimento è sbilanciato, in due direzioni opposte

`RP` 0,828 maschi · `RPFF` 0,792 · `R` 0,468 · **`RF` monogenitore
0,191**. `RP` è **bimodale** (coppie giovani e nidi vuoti).

### 4.4 Coppie dello stesso sesso: esattamente zero

0,000 su 4.525 partner — strutturale. **La popolazione sintetica eredita
l'assenza.**

### 4.5 La cittadinanza è una preferenza

Fra i nuclei con almeno uno straniero, **omogenei solo al 45%**.

### 4.6 I genitori conviventi non si leggono

n = 175, il 45% nella classe aperta. Limiti presi per analogia. **Il
parametro più debole**, e il collaudo lo conferma: 621–1.139 ripieghi
`G fuori dai limiti`, il secondo per frequenza in tutti e tre i comuni.

---

## 5. I criteri di compatibilità

| slot | vincolo | forza |
|---|---|---|
| R in coppia | maschio con p ≈ 0,80 | preferenza |
| R monogenitore | femmina con p ≈ 0,81 | preferenza |
| R senza partner | preferisci `vedovo` | preferenza |
| P | **stesso `stato_civile`** del riferimento | **forte** |
| P | sesso opposto | rigido |
| P | età entro ±15 anni | **convenzionale** |
| F | riferimento − figlio in [21, 45] | forte |
| F secondo | entro 11 anni dal fratello | forte |
| G | riferimento + [20, 40] | **dichiarato**, il più debole |
| cittadinanza | omogenea con p ≈ 0,55 nei misti | preferenza |

---

## 6. Il prototipo — la fattibilità non è un problema

Algoritmo avido, senza backtracking, su Parma anagrafica: slot con
ripiego 0%, 1,5%, 0% su sezioni da 38, 136 e **1.837 individui (748
nuclei)**. Divario generazionale dentro [21, 45] nel 100% dei casi.

> La domanda era «l'1% o il 15%?». La risposta è **sotto l'1%**. La
> preoccupazione sulla coda dell'assemblaggio era infondata.

**L'accuratezza del ruolo (59%) non è una metrica valida**: gli errori
R↔P sono lo stesso errore contato due volte. Chi sia la «persona di
riferimento» in una coppia non è una proprietà della famiglia, è chi ha
firmato in anagrafe.

---

## 7. `gsp.nucleo` e il collaudo

`src/gsp/nucleo.py`, quattro funzioni. Repertorio precalcolato in
`data/repertorio_nuclei_v1.json`. Collaudo:
`scripts/diagnostica/collaudo_nucleo.py`.

### 7.1 I vincoli di sezione: tre casi, tutti ordinari

```
residuo = N − Σ k·PF_{k+2}          (k = 1..6)
```

| caso | trattamento | Parma |
|---|---|---:|
| `residuo ≤ 0` | riduci le ampiezze maggiori | 372 |
| `0 < residuo ≤ 6·PF8` | `PF8` troncata: allarga dalla coda | 255 |
| `residuo > 6·PF8` | il resto è **convivenza**, senza nucleo | 297 |
| esatto | — | 389 |

> **`sovrastima` non è un difetto**: l'anello 3 alloca per sezione con
> MAE 0,74–1,58, e uno scarto di un'unità basta a invertire il segno del
> residuo. Il nome è fuorviante e andrebbe cambiato.

Il criterio locale `6·PF8` separa su Parma 791 persone da 2.770, e le
seconde vanno confrontate con le **3.096 convivenze anagrafiche**:
scarto 11%, due fonti e due anni diversi.

### 7.2 Il difetto che nessuna metrica segnalava

La prima versione del modulo **ignorava `stato_civile`**, che però è
vincolato dal MaxEnt in anello 1. Il risultato non era rumore ma
**contraddizione logica dentro lo stesso individuo**: coppie
coniugato+celibe, vedovi accoppiati con viventi.

> **La v1 riportava «99,3% di nuclei perfetti».** Quella metrica contava
> solo i ripieghi su età e sesso — cioè esattamente ciò che l'algoritmo
> ottimizzava. **Misurava il proprio criterio.** È il modo tipico in cui
> un difetto grosso resta invisibile.

**La correzione**: lo slot `P` richiede lo **stesso** stato civile del
riferimento. Non che la coppia sia coniugata — due `celibe_nubile`
insieme sono una convivenza (`RELPAR` 03), ed è aritmeticamente
necessario: ~42.000 coppie richiederebbero ~84.000 coniugati e ce ne sono
80.640, di cui un quinto vive solo. I `vedovo` sono esclusi da `P`.

Effetto su Parma:

| | prima | dopo |
|---|---:|---:|
| coppie con lo stesso stato civile | 51,0% | **96,5%** |
| coppie con entrambi coniugati | 29,6% | 54,0% |
| coppie coniugato+celibe | 7.240 | **480** |
| nuclei senza alcun ripiego | 99,3% | 97,8% |

Costo: 1.204 ripieghi `P stato civile diverso` su 42.421 coppie, il
**2,8%**.

### 7.3 La metrica giusta, e perché la precedente era troppo debole

> **Ritrattazione.** La v3.0 dichiarava un'incoerenza dell'**8,9%**,
> contando i «coniugati in un nucleo di 2+ senza nessun altro
> coniugato». Quella condizione **non verifica che i coniugati siano
> accoppiati fra loro**: un nucleo `RPF` con padre, madre e figlio tutti
> coniugati la soddisfa, e contiene un figlio sposato con nessuno.
>
> La condizione corretta è **per coppia**: un `coniugato_unito` è
> coerente solo se sta in una coppia (R,P) in cui anche l'altro è
> coniugato, oppure se vive solo. Il numero vero è **18–23%**.

Ma il numero unico nasconde il risultato. Scomposto per ruolo:

| ruolo del coniugato | Parma | Bologna | Brescia |
|---|---:|---:|---:|
| **P** | 0,025 | **0,015** | 0,034 |
| **R** | 0,078 | **0,060** | 0,076 |
| A, F, G, N | 1,000 | 1,000 | 1,000 |

> **Chi sta in coppia è quasi sempre coerente**: il 97–98% dei coniugati
> con ruolo `P` è appaiato con un altro coniugato, e il 92–94% di quelli
> con ruolo `R`. **L'algoritmo, quando forma coppie, le forma bene.**

*La metrica è comunque severa in eccesso*: un coniugato con ruolo `A` —
un fratello sposato che vive col fratello — è marcato incoerente, ma il
suo coniuge potrebbe semplicemente vivere altrove. Idem per `G`. Sono
casi rari; il caso `F` è invece **quantitativamente dominante**: 10.498
su 17.463 a Parma, il 60% dell'incoerenza.

### 7.4 La causa non è l'algoritmo: mancano gli slot `P`

Il conto su Parma: 80.640 coniugati, di cui 17.418 vivono soli. Restano
63.222 in nuclei plurimi, cioè al massimo 31.611 coppie. Le coppie
coniugate formate sono 22.898, cioè 45.796 persone. **Mancano 17.426
coniugati**, ed è esattamente il numero di quelli finiti in ruoli
non-partner.

> Il repertorio chiede un certo numero di firme con `P`, e quel numero è
> determinato dalle **ampiezze** censuarie, non da quanti coniugati ci
> sono nella sezione. **La popolazione ha più coniugati di quante coppie
> il repertorio preveda.**

Non serve quindi un algoritmo migliore per riempire gli slot: servirebbe
**scegliere firme diverse** — più `P` e meno `F` dove la sezione ha molti
coniugati. È un intervento sul passo (3) del meccanismo, non sul (4), e
non c'è (§9.2).

E resta il fatto sostanziale: **il constraint set non impone che ci si
sposi a due a due.** L'anello 4 rivela un'incoerenza già presente nella
popolazione, non la crea. Il posto dove il problema nasce è anello 1 —
cioè quello che abbiamo deciso di non toccare.

### 7.5 Il repertorio è trasferibile

| comune | omogenee | incoerenti | senza ripiego | non collocati | div. gen. |
|---|---:|---:|---:|---:|---:|
| Parma | 96,5% | 21,7% | 97,8% | 1,85% | 30 |
| **Bologna** | **98,1%** | **18,4%** | **98,8%** | **1,42%** | 29 |
| Brescia | 95,0% | 22,6% | 97,2% | 1,80% | 30 |

> La **coda** del repertorio (ampiezze oltre 6) viene dai microdati di
> **Parma**, e il repertorio delle firme è emiliano-lombardo. Il timore
> che fossero locali non si materializza: Bologna è **migliore** di Parma
> su ogni indicatore, e Brescia — Lombardia, fuori regione — perde meno
> di due punti.

Brescia è leggermente peggiore in modo coerente: `P stato civile diverso`
sale a 1.620 e `R senza partner del suo stato` a 279. Lì i coniugati sono
più difficili da appaiare. Differenza di grado, non di natura.

### 7.6 Il resto del collaudo

**Fattibilità**: 97,2–98,8% di nuclei senza alcun ripiego; non collocati
1,4–1,9%, di cui la parte dichiarata come convivenza dai vincoli
censuari.

**Divari**: generazionale mediana 29–30 (target AVQ 33), fuori dai limiti
0,04–0,12%. Partner mediana −1, p05 −14, p95 +14 in tutti e tre i comuni
— il limite convenzionale ±15 morde.

*`eta_anni` è pescata **uniforme nel bin**: i divari sono più dispersi di
quelli reali, e il rumore sta nell'età, non nell'assemblaggio.*

---

## 8. EU-SILC: cosa si può fare col PUF, e cosa no

Il PUF è **completamente sintetico** per dichiarazione Eurostat, con
struttura identica al SUF.

**Si può fare ora**: parser D/H/R/P, ricostruzione del grafo di
parentela, estrazione dei divari. Tutto il codice che poi girerà sul SUF.

**Non si può fare**: prendere i numeri, che sono artefatto della sintesi.

**Un uso legittimo**: verificare che il PUF riproduca le distribuzioni
AVQ dove si sovrappongono — test del software, non stima.

Il motivo per cui il SUF serve davvero: **nessuna fonte disponibile
permette di validare l'assemblaggio a livello di nucleo**.

---

## 9. Punti aperti

**9.1 Il TVD fra regioni condizionato sull'ampiezza** (§3). Una riga.

**9.2 Gli slot `P` mancanti** (§7.4). Richiederebbe di scegliere le firme
guardando la composizione della sezione. **Dichiarato come limite**, non
in programma. Il posto giusto sarebbe un vincolo di parità sui coniugati
per sezione nel constraint set — cioè anello 1.

**9.3 L'indirizzo è assegnato per individuo.** Marito e moglie possono
risultare a due civici diversi. Con i nuclei va assegnato **per
famiglia**, il che è anche il presupposto dell'assegnazione a edificio
attesa per settembre.

**9.4 Le AVQ dentro il nucleo restano scorrelate** (ρ ≈ 0,6 nella
realtà). Non risolvibile senza toccare l'anello 2.

**9.5 Il parametro `G`** è il più debole e il collaudo lo conferma.
Candidato numero uno per il SUF.

**9.6 Il rischio che l'AVQ porta con sé**: nessuna combinazione AVQ
riproduce il 52% di stranieri del codice 11 di Parma.

**9.7 `assign_nucleo.py`** non è ancora scritto: il collaudo gira su uno
script diagnostico.

**9.8 La metrica per coppia è severa in eccesso** sui ruoli `A` e `G`
(§7.3): un coniugato che vive col fratello mentre il coniuge sta altrove
è marcato incoerente. Quantificabile separando `F` dal resto.

---

## 10. Per il paper

Tre elementi metodologici di questa linea meritano di uscire.

**La metrica che misura il proprio criterio.** Il «99,3% di nuclei
perfetti» era vero e inutile: contava i ripieghi sui vincoli che
l'algoritmo imponeva, ed era cieco a una violazione che riguardava un
quarto dei coniugati. Il rimedio non è una metrica migliore ma **una
metrica costruita su un vincolo che l'algoritmo non usa** — qui
`stato_civile`, che viene da un altro anello.

**Il tetto teorico prima della soglia.** «Il rapporto dovrebbe stare
vicino a 1» era plausibile e sbagliato: l'aritmetica della popolazione lo
limita. Stessa famiglia del pavimento di rumore — un numero non si legge
senza il suo riferimento, e il riferimento va calcolato, non intuito.

**Il numero unico che nasconde il risultato.** L'incoerenza del 18–23%
scomposta per ruolo dice l'opposto di quel che sembra: l'algoritmo
accoppia bene, e il limite sta a monte, nella scelta delle firme. Una
metrica aggregata può essere corretta e insieme fuorviante.
