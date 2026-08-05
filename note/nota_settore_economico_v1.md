# Il settore economico: dentro il MaxEnt o a valle?

**Misura del 5 agosto 2026** · censimento 2011, `DICA_CARATT_ATTL`

Domanda: il settore di attività va aggiunto come variabile del MaxEnt
(livello K10C) o attribuito a valle come il titolo di studio?

La risposta è **a valle**, e non per comodità: la derivazione condiziona
sulla variabile che conta, il vincolo K10C su quella che non conta.

---

## 1. Da dove nasce la domanda

Due tavole censuarie sono scaricate, normalizzate e ricostruite a ogni
rigenerazione, ma **non producono alcun attributo** nella popolazione:

| file | contenuto | usato |
|---|---|---|
| `c9_sex_posizione_prof.csv` | sesso × dipendente/indipendente | **mai** |
| `c10_sex_settore.csv` | sesso × 6 settori | solo a K10C |

La ragione è strutturale: un vincolo può agire solo su variabili che
stanno nello spazio degli stati. A K9C non esiste né `settore` né
`posizione`, quindi quei due file non hanno dove appoggiarsi.

`VAR_ORDER_K10 = VAR_ORDER_K9 + ["settore"]`: il settore è l'unica
differenza fra i due livelli.

---

## 2. Perché K10C non è la risposta

Il livello K10C aggiunge il settore e paga tre prezzi.

**Lo spazio degli stati passa a 37 milioni** contro i 69.888 di Parma
K7C. Il solver esatto non arriva, e il Gibbs diventa necessario.

**La catena diventa riducibile.** Il blocco `MC` impone
`condizione × settore` come vincolo diretto — serve a evitare il bug
dell'indipendenza spuria, che senza di esso produrrebbe «pensionati
nell'industria» — e `S_settore_non_occupati` impone il complementare.
Insieme creano zeri strutturali su entrambi i lati che disconnettono il
grafo di compatibilità bipartito, e la catena di Gibbs è irriducibile
precisamente a λ*, cioè nel punto in cui dovrebbe convergere. È lo stesso
meccanismo del blocco `GC` per cittadinanza × background, dichiarato nei
commenti di `cs_build.py` (riga 552).

**Su Brescia produce 3.417 individui impossibili** (1,72%), contro zero
di K9C su undici comuni.

Ma il prezzo peggiore è il terzo, ed è emerso solo con questa misura:
**il blocco condiziona il settore sul SESSO**, che è la dimensione meno
informativa delle tre disponibili.

---

## 3. La misura

Fonte: `DICA_CARATT_ATTL` del censimento 2011, quattordici dimensioni fra
cui `ATECO_2007`, `ETA1`, `TITOLO_STUDIO`, `SEXISTAT1`, `ITTER107`.
Filtri: occupati (`EMPLP`), tutte le altre dimensioni al totale.

Metrica: **distanza in variazione totale** fra la composizione settoriale
di un sottogruppo e quella complessiva. Va da 0 a 1 ed è la quota di
massa da spostare per trasformare l'una nell'altra.

### Composizione nazionale, occupati 15+

| sezione | quota |
|---|---|
| SSW | 17,2% |
| EO | 16,2% |
| TW | 13,6% |
| PIS | 13,3% |
| TAP | 13,2% |
| CSW | 12,3% |
| PMO | 5,8% |
| MANAG | 5,2% |
| AGRFORW | 1,6% |
| AFO | 1,4% |

### Quanto ciascuna variabile sposta la composizione

| dimensione | TVD | |
|---|---|---|
| **istruzione** | **0,17 – 0,50** | dominante |
| sesso | 0,13 – 0,18 | |
| comune vs regione | 0,03 – 0,16 | molto variabile |
| età, 30-55 anni | 0,03 – 0,08 | trascurabile |
| età, 20-24 e 60-64 | 0,12 – 0,20 | conta agli estremi |

**L'istruzione domina.** Chi non ha titolo di studio ha una composizione
settoriale che differisce dalla media per il **49,6% della massa**: quasi
metà. Il titolo più alto sta a 0,45. Nessun'altra dimensione si avvicina.

**L'età è quasi irrilevante** nella fascia centrale — sotto 0,05 fra i 30
e i 55 — e conta solo agli estremi, dove i ventenni si concentrano in
commercio e ristorazione e i sessantenni nei settori in uscita.

### Il territorio, e quanto costa il ripiego regionale

| comune | TVD dalla regione |
|---|---|
| Bologna | 0,159 |
| Parma | 0,106 |
| Modena | 0,089 |
| Reggio Emilia | 0,042 |
| Ravenna | 0,029 |

Bologna è capitale amministrativa e ha una composizione terziaria che si
discosta molto; Ravenna è quasi identica alla media regionale. **Il
ripiego costa poco dove il comune è ordinario e molto dove è
particolare**, che è precisamente il caso in cui servirebbe.

---

## 4. La conclusione

Il vincolo K10C condiziona su **sesso** (TVD 0,13-0,18) e ignora
l'**istruzione** (0,17-0,50), al prezzo di trentasette milioni di stati e
di una catena di Gibbs riducibile.

La derivazione a valle condiziona su istruzione, sesso e comune, non
tocca il solver, e ha il comune dove la tavola lo dà.

> **È migliore su tutti e tre gli assi: informazione, costo
> computazionale, correttezza.**

Il che non toglie nulla al MaxEnt: dice che *questa* variabile non ha
bisogno di starci. La differenza con la cittadinanza è che lì la
struttura geografica è forte e va catturata congiuntamente, mentre qui la
geografia arriva già da `condizione`, che è vincolata su zona.

---

## 5. Come si costruirebbe

```
P(ateco | istruzione, sesso, comune)      6 comuni su 11
P(ateco | istruzione, sesso, regione)     i restanti 5
```

Cascata dichiarata, come i tier del paese di cittadinanza. I sei comuni
presenti nella tavola sono Parma, Modena, Bologna, Brescia, Reggio
Emilia, Ravenna; mancano Rimini, Ferrara, Forlì, Piacenza e Castenaso.

**Non condizionare sull'età** fra i 30 e i 55, dove non porta nulla.
Semmai trattare a parte i due estremi.

**L'universo sono gli occupati**, il 48,0% della popolazione (81% nelle
età centrali). Per tutti gli altri il settore è `non_applicabile` per
costruzione, non mancante — come il missing strutturale delle AVQ.

---

## 6. Limiti

**Cittadinanza e settore non sono mai incrociati** in questa tavola:
`ISO1` è sempre al totale quando `ATECO_2007` è specificato (verificato
5/8/2026, zero righe con entrambi). L'assunzione di indipendenza fra
settore e cittadinanza non è quindi verificabile qui.

Una parte dell'effetto passa comunque per via indiretta: gli stranieri
hanno una distribuzione d'istruzione diversa dagli italiani, e il settore
è condizionato sull'istruzione. Quello che si perde è l'effetto
**residuo** — la concentrazione settoriale a parità di titolo, che esiste
ma è di secondo ordine.

**Sotto il comune non c'è niente**: la tavola ha 163 territori, di cui 25
comuni, e nessuna articolazione sub-comunale. La variazione fra zone di
uno stesso comune resta non catturata.

Ne esce una gerarchia fra gli attributi derivati che vale la pena
ricordare:

| attributo | risoluzione territoriale |
|---|---|
| titolo di studio | regione |
| **settore economico** | **comune, per 6 comuni su 11** |
| attributi AVQ | regione |

**La fonte ha quindici anni.** Vale quanto detto per i titoli di studio:
il trasferimento per coorte è pulito per chi era già nel mercato del
lavoro nel 2011, e la struttura settoriale italiana è cambiata dopo —
crescita dei servizi digitali, contrazione della manifattura.

**La tavola comunale `DICA_CARATT_ATTL_COM` non serve**: copre tutti gli
8.230 comuni ma con sette sole categorie settoriali (totale, industria,
servizi, più quattro aggregati), senza istruzione. Utile eventualmente
come vincolo, non per il dettaglio.

---

## 7. Cosa fare di K10C

**Lasciarlo dov'è**, come materiale sperimentale escluso dalla
produzione. Conserva la storia della riducibilità, che è un risultato
metodologico e non un difetto da nascondere.

Quello che cambia è la motivazione per non usarlo: non più «produce
combinazioni impossibili», ma **«condiziona sulla variabile sbagliata»**.
È una ragione più forte, e resta valida anche se un giorno la
riducibilità venisse risolta.

## 8. E `c9_sex_posizione_prof`

Resta il caso aperto: due modalità, `dipendente` / `indipendente`,
condizionate sul sesso, costruite a ogni rigenerazione e **mai lette da
nessuno**. `DICA_CARATT_ATTL` ha `PROFILO_PROF` con 47 modalità e
`OCCUPAZIONE` con 11 grandi gruppi — «attività operaia qualificata»,
«addetto a impianti fissi di produzione» — che sono più informative e
disponibili nella stessa tavola.

Se si deriva il settore, conviene derivare anche quelle nello stesso
passo: sono la stessa fonte, lo stesso universo e lo stesso
condizionamento.
