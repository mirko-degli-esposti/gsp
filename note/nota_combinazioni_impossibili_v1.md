# Combinazioni impossibili: il 2,6% non è riprodotto

**Nota breve — GSP**
1 agosto 2026

---

## Il fatto

Il documento di riferimento e le note di progetto riportano un tasso di
**combinazioni logicamente impossibili del 2,64–2,74%**, misurato su Modena
e Parma. Misurato oggi sulle popolazioni in pipeline, con le quattro regole
di `G.IMPOSSIBILI`, il tasso è di **tre ordini di grandezza più basso**:

| comune | livello | impossibili | popolazione | tasso |
|---|---|---|---|---|
| Brescia | K9C | 7 | 198.259 | 0,004% |
| Parma | K9C | 3 | 198.121 | 0,002% |
| Modena | K9C | 1 | 184.597 | 0,001% |
| Bologna | K9C | 3 | 390.098 | 0,001% |
| Ravenna | K9C | 1 | 156.304 | 0,001% |
| Forlì | K9C | 1 | 117.050 | 0,001% |

Sedici individui su 1.244.429.

Le regole applicate sono quelle di `gsp_common.IMPOSSIBILI`: età × condizione
professionale (universo 15+), età × istruzione (universo 9+, soglie di
conseguimento 18/20/22 anni).

## Perché è aperto

L'origine del 2,6–2,74% non è stata ricostruita. Tre ipotesi, in ordine di
plausibilità:

**(a) Era una proiezione, non una misura.** Su Parma risultava che il 32,8%
dei 9-14enni avrebbe avuto diploma o laurea. I 9-14enni sono ~5% della
popolazione, quindi il 32,8% di quel bin è ~1,6% del totale — ordine di
grandezza compatibile con un 2,6% che sommi più regole. Se è così, il numero
descriveva cosa sarebbe successo **senza** i blocchi `S_istruzione_under9` e
`S_condizione_under15`, non cosa succedeva con essi.

**(b) Misurava un insieme di combinazioni più ampio**, per esempio
includendo coerenze stato civile × età o condizione × istruzione, che
`G.IMPOSSIBILI` non copre.

**(c) Era su una generazione precedente**, anteriore all'introduzione dei
blocchi `S_*`. In tal caso il problema era già stato risolto a suo tempo.

Se (a) o (c), il meccanismo funzionava già e il numero non descrive lo stato
attuale del pipeline.

## Cosa è stato fatto comunque

`cs_build.py --esclusioni` aggiunge 26 vincoli α=0 sulle coppie
`(eta, condizione)` e `(eta, istruzione)`, dalle regole dichiarative in
`gsp_common.IMPOSSIBILI`. Le stesse regole sono ora lette anche da
`animarium/build/ispeziona_cs.py`, che prima ne aveva una copia locale.

Il vincolo è sulla **coppia**: azzerare il marginale di coppia forza a zero
tutte le celle sottostanti, perché le probabilità sono non negative. Bastano
26 vincoli, non 26 per ogni valore di sesso o di zona.

Collaudo su Castenaso 037021 (K6C, |X| = 5.376):

| | senza | con |
|---|---|---|
| vincoli | 263 | 289 |
| di cui α = 0 | 6 | 32 |
| MRE finale | 3,40·10⁻⁴ | 3,40·10⁻⁴ |
| MRE(α>0) | 4,352·10⁻⁴ | 4,352·10⁻⁴ |
| entropia | 5,314 nat | 5,313 nat |
| supporto | 3.717/5.376 | 3.086/5.376 |
| celle escluse post-hoc | 504 | 2.288 |
| impossibili nella popolazione | — | **0** |

**Il fit non paga nulla per rispettare le esclusioni**: MRE identico alla
quarta cifra, entropia a −0,001 nat, e `massa spontanea su celle escluse =
0,00e+00` — il modello non voleva metterci nessuno neppure prima. Le
esclusioni rendono esplicito ciò che la soluzione MaxEnt già faceva, e
chiudono l'ultimo per mille che veniva dal campionamento.

Il flag è **spento di default**: senza `--esclusioni`, `cs_build` produce un
file identico byte per byte a quello precedente (verificato con `cmp`).

## Implicazione operativa

Le esclusioni non giustificano da sole una rigenerazione: sedici persone su
1,2 milioni non sono visibili in alcuna analisi o visualizzazione. Vanno
attivate perché costano zero e trasformano una garanzia implicita in una
esplicita — utile poter affermare «zero combinazioni impossibili» invece di
«quasi zero».

La ragione vera per rigenerare è un'altra: **l'uniformità del set AVQ**
(Bologna 21 variabili, Ravenna e Forlì 6, Castenaso 23). Quando si rigenera
per quello, le esclusioni entrano gratis perché il constraint set va
comunque ricostruito.

## Da chiudere

Ricostruire l'origine del 2,64–2,74%: dove è stato misurato, con quali
regole, su quale generazione. Finché non è chiarito, **il numero non va
usato in pubblicazioni** — è il tipo di cifra che passa in un paper senza
che nessuno la riverifichi. Nel documento di riferimento va marcato come
non riprodotto.
