# Combinazioni impossibili: è un effetto del blocco MC in K10C

**Nota breve — GSP**
1 agosto 2026 · v2

*La v1 di questa nota, scritta la mattina dello stesso giorno, dava il tasso
del 2,6% come «non riprodotto» e ne elencava tre possibili origini. La
misura del pomeriggio lo ha riprodotto e ne ha individuato la causa. Questa
versione sostituisce la precedente.*

---

## Il fatto

Il tasso di **combinazioni logicamente impossibili** — età sotto i 15 anni
con una condizione professionale, età sotto i 9 con un titolo di studio,
9-14enni con diploma o laurea — differisce di tre ordini di grandezza fra
due livelli del constraint set:

| comune | livello | impossibili | popolazione | tasso |
|---|---|---|---|---|
| **Brescia** | **K10C** | **3.417** | 198.259 | **1,724%** |
| Brescia | K9C | 7 | 198.259 | 0,004% |
| Parma | K9C | 3 | 198.121 | 0,002% |
| Modena | K9C | 1 | 184.597 | 0,001% |
| Bologna | K9C | 3 | 390.098 | 0,001% |
| Ravenna | K9C | 1 | 156.304 | 0,001% |
| Forlì | K9C | 1 | 117.050 | 0,001% |

Le regole applicate sono quelle di `gsp_common.IMPOSSIBILI`.

Il 2,64–2,74% riportato nelle note di progetto è quindi **valido e riferito
a K10C**. Su K9C il fenomeno non esiste.

## La causa: il blocco MC

Il tasso è identico in `popolazione_K10C.csv` e in
`popolazione_K10C_avq_full.csv` (3.417 in entrambi): il problema **nasce nel
fit**, gli anelli 2 e 3 trasportano fedelmente ciò che ricevono.

K10C differisce da K9C per il blocco **MC**, `condizione × settore`, che
codifica una relazione deterministica:

    occupato  ⟺  settore ≠ non_applicabile

Imporla come vincolo MaxEnt significa mettere zeri esatti su celle del
prodotto cartesiano. A λ* quegli zeri diventano barriere infinite e
**disconnettono il grafo di compatibilità bipartito**: la catena di Gibbs
diventa riducibile precisamente nel punto in cui dovrebbe convergere.

La diagnostica del fit lo conferma: su Brescia K10C la **massa spontanea
sulle celle escluse è 6,95·10⁻²** — il 7% della massa vuole finire dove i
vincoli la azzerano — e il PCD risulta *mixing-limited* con |X| ≈ 3,7·10⁷.

Le combinazioni impossibili sono quindi un **sintomo della mancata
convergenza**, non una patologia indipendente. È lo stesso oggetto
matematico del blocco GC (`background × cittadinanza`, 6 zeri strutturali),
in un'altra coordinata.

## Cosa NON è la cura

Le esclusioni α=0 introdotte oggi in `cs_build.py --esclusioni` **non
risolvono questo**. Chiudono l'ultimo per mille residuo su K9C, dove il
problema è già sostanzialmente assente, e non toccano la riducibilità.

La cura è **ridurre le coordinate invece di aggiungere vincoli**:
sostituire `condizione × settore` con una singola variabile a categorie
legali

    {non_applicabile_u15, disoccupato, pensionato, studente, ...}
    ∪ {occupato_agricoltura, occupato_industria, ...}

Il prodotto cartesiano non contiene più zeri strutturali, il grafo torna
connesso, e MC diventa un margine ordinario su questa variabile composita.
Idem per la cittadinanza, che è funzione deterministica del background e
non una coordinata indipendente.

## Il meccanismo delle esclusioni α=0

Introdotte comunque, perché costano zero e trasformano una garanzia
implicita in una esplicita.

`cs_build.py --esclusioni` aggiunge 26 vincoli α=0 sulle coppie
`(eta, condizione)` e `(eta, istruzione)`, dalle regole dichiarative in
`gsp_common.IMPOSSIBILI` — lette ora anche da
`animarium/build/ispeziona_cs.py`, che prima ne aveva una copia locale.

Il vincolo è sulla **coppia**: azzerare il marginale di coppia forza a zero
tutte le celle sottostanti, perché le probabilità sono non negative.
Bastano 26 vincoli, non 26 per ogni valore di sesso o di zona.

Collaudato a due livelli con spazi che differiscono di un fattore 300:

| | Castenaso K6C senza | con | Ravenna K9C senza | con |
|---|---|---|---|---|
| \|X\| | 5.376 | 5.376 | 1.612.800 | 1.612.800 |
| vincoli α=0 | 6 | 32 | 9 | 35 |
| MRE finale | 3,40·10⁻⁴ | 3,40·10⁻⁴ | 5,00·10⁻⁴ | 5,00·10⁻⁴ |
| MRE(α>0) | 4,352·10⁻⁴ | 4,352·10⁻⁴ | 5,277·10⁻⁴ | 5,317·10⁻⁴ |
| entropia | 5,314 nat | 5,313 nat | 8,172 nat | 8,171 nat |
| supporto | 3.717 | 3.086 | 362.127 | 341.351 |
| massa su escluse | 0 | 0 | 0 | 0 |
| tempo | 0,23 s | 0,30 s | 61,9 s | 55,5 s |

**Il fit non paga nulla**: MRE invariato alla quarta cifra, entropia a
−0,001 nat, massa spontanea sulle celle escluse zero anche prima
dell'azzeramento. Le esclusioni rendono esplicito ciò che la soluzione
MaxEnt già faceva.

Il flag è **spento di default**: senza `--esclusioni`, `cs_build` produce un
file identico byte per byte al precedente (verificato con `cmp`).

## Conseguenze

**Per la rigenerazione.** Fatta il 1/8/2026 su sette comuni con
`scripts/rigenera.sh`: tutti a K9C tranne Castenaso (K6C), esclusioni
attive, set AVQ uniforme a 23 variabili. Impossibili: **zero ovunque**.

**Per il K10C di Brescia.** Da conservare, non cancellare: è l'unica
popolazione con la patologia in forma misurabile, e serve come termine di
paragone quando si affronterà la riducibilità. Attenzione però
all'auto-detect di `assign_avq` ed `enrich`, che cerca
`K10C → K9C → … → K6C` e prenderebbe il K10C: nella pipeline di
rigenerazione il livello va passato esplicitamente con `--pop-file`.

**Per il paper (ACM TKDD).** La nota a piè di pagina sulla riducibilità in
virgola mobile si arricchisce di una conseguenza osservabile: la
reducibilità non degrada solo la convergenza del solver, produce **l'1,7%
di individui logicamente impossibili** nella popolazione generata. È il
tipo di effetto che rende concreta una patologia altrimenti astratta.

## Cronologia

La v1 di questa nota elencava tre ipotesi sull'origine del 2,6%: (a) era
una proiezione e non una misura, (b) misurava un insieme di combinazioni
più ampio, (c) era su una generazione precedente. **La (c) era corretta**,
con la precisazione che «precedente» significa *a un livello diverso*, non
*prima di una correzione*.

Il numero è emerso di nuovo per caso: durante la rigenerazione del
1/8/2026 l'auto-detect di `assign_avq` ha scelto il `popolazione_K10C.csv`
residuo invece del K9C appena rigenerato, e la verifica finale ha mostrato
3.417 impossibili accanto agli zeri degli altri sei comuni. Un difetto
dello script di rigenerazione ha chiuso una questione aperta da giorni.
