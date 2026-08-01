# Quanto si perde fermandosi al quartiere?

**Nota metodologica — giustificazione quantitativa dell'anello 3**
GSP · v2, 1 agosto 2026

*v1 (31 luglio): quattro configurazioni su quattro comuni. v2 aggiunge
Ravenna e Forlì, che rompono il legame fra numero di zone e resa e
spostano la conclusione operativa dalla granularità all'allineamento
della partizione.*

---

## 1. La domanda

L'anello 1 (MaxEnt) assegna il **quartiere**, che è il livello più fine a cui
il censimento pubblica gli incroci necessari al solver. Sotto il quartiere
esistono solo marginali di sezione, che l'anello 3 (`enrich.py`) sfrutta
come condizionali post-hoc.

Questa nota misura ciò che giustifica quella scelta architetturale:

> Quanta parte della struttura spaziale della **provenienza** degli stranieri
> sopravvive all'aggregazione in quartieri, e quanta resta sotto?

La distinzione che regge tutto è fra **quantità** e **composizione**. Le due
proprietà operano a scale spaziali diverse: una partizione grossolana può
separare bene *quanti* stranieri vivono in ciascuna zona e per nulla *da
dove vengono*. Solo la seconda è in questione qui.

La risposta breve: la zonizzazione trattiene fra il 2% e il 20% del segnale
compositivo disponibile a livello di sezione. **Fra l'80% e il 98% sta sotto
il quartiere**, e la partizione migliore non è la più fine. È la ragione per
cui l'anello 3 esiste.

## 2. Dati e definizioni

Unità elementare: la sezione di censimento 2023, con la sua zona di
appartenenza (`COM_ASC1` o `COM_ASC2`). Per ogni sezione si osservano i
conteggi di stranieri per gruppo di origine, dalle colonne del tracciato
ISTAT `ST17`/`ST18` (UE, M/F) e `ST20`/`ST21` (extra-UE, M/F).

Sono escluse le sezioni senza stranieri o senza codice di zona: non portano
informazione compositiva.

Notazione: *Z* = zona, *S* = sezione, *K* = gruppo di origine (qui K = 2),
*n* = numero di stranieri, *H(K)* = entropia dell'origine.

I conteggi censuari sono **enumerazione completa, non stime**. La variabilità
fra sezioni non è quindi errore campionario d'indagine, ma la somma di
struttura spaziale reale e di rumore multinomiale di allocazione su celle
piccole. Separare le due è il problema centrale della misura.

## 3. Perché la metrica precedente non bastava

La misura usata in precedenza era il rapporto fra varianza compositiva
*within* e *between* zone, sulle composizioni di sezione ponderate per
numerosità. Presentava quattro difficoltà, tutte di **inferenza** e non di
stima — distinzione che il § 9 rende necessaria.

**(a) Non monotòna.** Bologna con 18 zone risultava spiegare meno di Parma
con 13.

**(b) Denominatore contaminato.** La varianza *within* è calcolata fra
sezioni della stessa zona, ma una sezione di Modena contiene mediamente 7
stranieri: la quota UE stimata su 7 unità ha deviazione standard binomiale
dell'ordine di 0,14. Il pavimento di rumore dipende da quanti stranieri ci
sono per sezione, cioè dalla quota di stranieri della città — quindi
l'ordinamento fra città poteva essere prodotto da quel confondimento. La
correzione applicata a mano nell'anello 3 (sottrazione della componente di
discretizzazione: su Parma 0,00499 su 0,01748) affrontava esattamente
questo, ma caso per caso.

**(c) Pochi gradi di libertà.** Con 4 zone la varianza *between* è stimata
da quattro numeri.

**(d) Distribuzione nulla a coda pesante.** Verificato su dati sintetici
generati dal nullo: rapporto osservato 780,9, media nulla 1.764, mediana
858, massimo su 600 repliche 30.964. La media è dominata dagli outlier in
cui SSB si avvicina a zero.

Conferma sui dati reali: nelle cinque configurazioni il rapporto ha z fra
−0,1 e −3,0 con p al pavimento di 0,001. Una statistica il cui p-value è
massimamente significativo e la cui z è indistinguibile da zero non ha
distribuzione nulla approssimabile alla normale.

## 4. Il nullo corretto

Il nullo deve preservare la struttura di **quantità** e distruggere solo
quella di **composizione**. Per ogni sezione si tiene fisso il numero di
stranieri N_s e si riestrae la provenienza dalla composizione cittadina:

    n_s* ~ Multinomial(N_s, p_comune)

La struttura di quantità entra identica nel nullo e nell'osservato; ciò che
resta è composizione pura. Il nullo genera automaticamente il pavimento di
rumore — la stessa quantità che l'anello 3 sottraeva a mano — ma per ogni
configurazione e senza taratura.

Un secondo nullo, per confronto, permuta le etichette di zona: distrugge
quantità e composizione insieme. Sotto il nullo B gli eccessi sono da 3 a 7
volte, sotto il nullo A da 16 a 36, perché il nullo B lascia nel "segnale"
anche la struttura di quantità. **Solo il nullo A risponde alla domanda del
§ 1.**

## 5. La statistica

Informazione mutua *I(Z;K)*, in nat, sulla tabella di contingenza zona ×
origine. Tre ragioni: è letteralmente "quanto la zona dice sull'origine";
ha attesa nulla analitica nota, `E[I] ≈ (Z−1)(K−1)/2n`, che rende esplicita
la dipendenza dal numero di celle; non soffre della coda pesante del
rapporto di varianza (media e mediana del nullo distano il 20%, contro un
fattore 2).

Tre quantità derivate:

- **I(Z;K) corretta** = I osservata − mediana del nullo. Segnale assoluto.
- **I / H(K)** — frazione dell'incertezza sull'origine rimossa dalla zona.
- **I(Z;K) / I(S;K)** — la **quota trattenuta**: quanta parte del segnale
  compositivo spaziale sopravvive all'aggregazione in zone. Adimensionale,
  confrontabile fra città, risponde direttamente al § 1.

L'**eccesso sul nullo** misura il rapporto segnale-rumore, non l'effetto: il
denominatore cresce con Z, quindi è confuso dal numero di zone esattamente
come il rapporto di varianza. Non va usato per confronti fra partizioni
diverse.

## 6. Validazione

**Su dati sintetici con verità nota** (1.627 sezioni, 4 zone, quantità per
zona in rapporto 5:1):

| costruzione | eccesso su nullo A |
|---|---|
| composizione identica, quantità molto diverse per zona | 0,90× |
| segnale compositivo debole | 7,8× |
| segnale compositivo forte | 1.495× |

Il primo caso è decisivo: la metrica non si lascia ingannare dalla quantità.

**Della formula analitica**, contro la mediana simulata a livello di zona:

| città | Z | mediana simulata | (Z−1)(K−1)/2n |
|---|---|---|---|
| Modena | 4 | 4,43·10⁻⁵ | 5,3·10⁻⁵ |
| Bologna | 6 | 3,65·10⁻⁵ | 4,2·10⁻⁵ |
| Parma | 13 | 1,65·10⁻⁴ | 1,74·10⁻⁴ |
| Bologna | 18 | 1,37·10⁻⁴ | 1,44·10⁻⁴ |
| Brescia | 33 | 4,18·10⁻⁴ | 4,27·10⁻⁴ |

Accordo entro il 20%, formula sistematicamente più alta: atteso, perché
approssima la **media** e la distribuzione nulla di I è asimmetrica a destra.

**Avvertenza.** A livello di sezione la formula non è utilizzabile: con
~1.900 celle e mediana di 7–19 unità ciascuna il regime asintotico non vale
e la formula **sottostima** il bias del 6–8%. Per il soffitto I(S;K) la
correzione va fatta per simulazione.

## 7. Dove entra l'IPF

Le tabelle di zona non entrano come conteggi ma come struttura: i margini
comunali dei blocchi Z sono imposti in `cs_build` via
`P(zona | margine) × conteggi comunali`, riconciliati con IPF.

L'IPF preserva **esattamente** i rapporti di prodotti incrociati del seed
(Deming & Stephan 1940; Bishop, Fienberg & Holland 1975, cap. 3): converge
alla tabella che minimizza la divergenza di Kullback-Leibler dal seed fra
quelle compatibili con i margini, e tutti i termini di interazione
sopravvivono immutati. Cambiano i livelli, non l'associazione.

Due conseguenze. **La misura va fatta a monte dell'IPF**, sulle sezioni
grezze, e il risultato vale per tutta la catena. E **spiega perché due
metriche precedenti divergevano**: l'eccesso del condizionale geografico
risultava piatto (2,08 · 2,10 · 2,57) su partizioni da 13 a 33 zone, mentre
il rapporto di varianza oscillava fra 5,9 e 15,7. Il primo è definito sulla
decisione di assegnazione, che dipende dall'associazione: invariante per
IPF. Il secondo è funzione delle proporzioni: non invariante.

**Assunzione dichiarata.** L'IPF trasferisce l'interazione zona × origine
delle sezioni 2023 sui margini comunali dell'anno di ancoraggio: stabilità
strutturale dell'associazione fra il 2023 e l'anno corrente. Stessa classe
dell'ipotesi (7) usata per i blocchi C9/C10.

## 8. Risultati

Sette configurazioni su sei comuni. B = 1.000 repliche per il nullo di zona,
250 per il soffitto di sezione. Seed 20260731. Ordinate per quota trattenuta.

| città | Z | sezioni | stranieri | mediana/sez | H(K) | I(Z;K) corr | % di H | I(S;K) corr | % di H | **quota trattenuta** | z |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Modena | 4 | 1.627 | 28.415 | 7 | 0,4486 | 0,001424 | 0,32% | 0,059712 | 13,31% | **2,4%** | 30,7 |
| Bologna | 6 | 1.925 | 58.963 | 19 | 0,5177 | 0,001274 | 0,25% | 0,036594 | 7,07% | **3,5%** | 50,0 |
| Bologna | 18 | 1.925 | 58.963 | 19 | 0,5177 | 0,002009 | 0,39% | 0,036594 | 7,07% | **5,5%** | 39,8 |
| Parma | 13 | 1.139 | 34.436 | 17 | 0,4780 | 0,003594 | 0,75% | 0,044798 | 9,37% | **8,0%** | 49,5 |
| Ravenna | 10 | 1.715 | 17.777 | 5 | 0,6179 | 0,016059 | 2,60% | 0,109904 | 17,79% | **14,6%** | 141,7 |
| Brescia | 33 | 1.464 | 37.478 | 11 | 0,4253 | 0,006373 | 1,50% | 0,041902 | 9,85% | **15,2%** | 57,5 |
| Forlì | 21 | 1.175 | 15.298 | 7 | 0,5369 | 0,019747 | 3,68% | 0,097270 | 18,12% | **20,3%** | 95,0 |

## 9. Convergenza fra tre misure indipendenti

Il risultato non dipende dal funzionale scelto. Tre metodi che non
condividono né la statistica né il modello di rumore danno la stessa
risposta:

| città | varianza *non* corretta | varianza corretta per discretizzazione | informazione mutua, nullo multinomiale |
|---|---|---|---|
| Modena | 1,55% | 2,25% | **2,4%** |
| Bologna 18 | 4,11% | 5,99% | **5,5%** |
| Parma | 5,94% | 8,13% | **8,0%** |
| Brescia | 9,99% | 14,49% | **15,2%** |

La colonna centrale è la misura originale; la prima è la stessa senza
correzione del rumore; la terza è questa nota.

**La lettura importante è nel confronto fra le prime due colonne.** La
varianza non corretta sottostima sistematicamente di un fattore ~1,45,
perché il rumore multinomiale gonfia la componente *within*. La correzione
di discretizzazione applicata a mano nell'anello 3 rimuoveva proprio quel
fattore. Il nullo multinomiale del § 4 fa la stessa cosa
**automaticamente, per ogni configurazione e senza taratura**, e arriva
allo stesso numero.

Riscontro puntuale su Parma, dove esistono entrambe le versioni: il
rapporto non corretto vale 15,82 con questo script e 15,9 nel docstring di
`enrich.py`; corretto, 11,3 nella misura originale e 11,4 in `enrich.py`.
Quattro numeri, due implementazioni indipendenti.

Riscontro analogo su Forlì, dove la diagnostica interna di `enrich.py` dà un
rapporto struttura-di-sezione / struttura-di-zona pari a 3,5, cioè una quota
trattenuta del 22,2%, contro il 20,3% di questa nota. Quinta coincidenza fra
metriche indipendenti, scarto del 9%.

## 10. Cinque risultati

**(1) La perdita va dall'80% al 98%.** La quota trattenuta va dal 2,4% di
Modena al 20,3% di Forlì. Anche nella configurazione migliore, quattro
quinti della struttura spaziale della composizione restano sotto il
quartiere. È la giustificazione quantitativa dell'anello 3.

**(2) Il segnale è statisticamente schiacciante e sostanzialmente
minuscolo.** Le z vanno da 31 a 142; le frazioni di H(K) rimosse dalla zona
dallo 0,25% al 3,68%. Su 28.000–59.000 individui la significatività è
garantita e non informa: va riportato l'effetto, non il test. Stesso
pattern del pavimento MRE nel lavoro su GibbsPCD.

**(3) Modena ha il segnale spaziale più alto e la partizione peggiore.**
I(S;K) corretta vale il 13,31% di H(K), la più alta delle quattro città; la
quota trattenuta è il 2,4%, la più bassa. Modena non è meno segregata per
origine: è peggio partizionata. I suoi quattro quartieri da ~46.000
abitanti attraversano i confini di insediamento invece di rispettarli.

**(4) Conta l'allineamento della partizione, non il numero di zone.**
Ravenna con 10 aree trattiene il 14,6%, quasi quanto Brescia con 33 (15,2%)
e quasi il triplo di Bologna con 18 (5,5%). Forlì con 21 quartieri arriva al
20,3%, il massimo osservato. La correlazione di rango fra numero di zone e
quota trattenuta, sui sei comuni distinti, è 0,714 (p = 0,111): presente ma
non significativa, e ben lontana dal determinare l'esito.

La regolarità che spiega meglio i dati è la **natura** della partizione.
Ravenna e Forlì hanno zone costruite attorno a frazioni identificabili —
dieci aree territoriali su 652 km², ventun quartieri di cui dieci rurali,
ciascuno corrispondente a nuclei nominati. Modena e Bologna hanno
suddivisioni amministrative di un tessuto urbano continuo. Quando i confini
seguono l'insediamento, dieci pezzi bastano; quando lo tagliano
trasversalmente, diciotto non servono.

**(5) Il raffinamento Bologna 6 → 18 guadagna il 57%.** Unico esperimento
controllato: stessa città, stessi dati, stesso n. Da riportare con cautela —
ASC2 è un raffinamento di ASC1, e per la disuguaglianza sull'elaborazione
dei dati un raffinamento non può ridurre l'informazione mutua. Che 18 batta
6 è garantito a priori; l'unica quantità empirica è di quanto. Il +57%
misura quindi il guadagno reale del triplicare le zone *dentro la stessa
partizione amministrativa*: modesto, e inferiore al divario fra Bologna e
qualunque comune a partizione allineata.

**(6) Anche il soffitto varia per città.** I(S;K) corretta va dal 7,07% di
Bologna al 18,12% di Forlì: la quantità di struttura spaziale *disponibile*
non è una costante contro cui misurare le partizioni, ma essa stessa una
proprietà del comune. I due comuni a insediamento più disperso hanno i
soffitti più alti — con il confondimento discusso al § 12.

## 11. Cosa fa il pipeline

L'anello 3 non si ferma al quartiere, ed è coerente con questi risultati.

**(3b) area UE/extra-UE** — condizionata alla **sezione**, non alla zona:
`P(area | sezione, sesso)` dalle colonne `ST17/18/20/21`. Ricade sulla zona
solo se la sezione non ha stranieri di quel sesso. Nelle tre città
generate: 100% dalla sezione, zero fallback.

**(3c) paese** — condizionato alla geografia tramite `opendata_paese`, che
fornisce un tensore paese × sesso × geografia da **open data comunale**. I
tier sono i livelli di granularità della fonte:

| tier | fonte geografica | comune | esito |
|---|---|---|---|
| 0 | nessuna: `P(paese \| area, sesso)` comunale | Modena (4 quartieri) | — |
| 1 | quartieri | Brescia (33) | 100% dalla geografia |
| 1 | aree territoriali | Ravenna (10) | 100% dalla geografia |
| 1 | quartieri | Forlì (21) | 100% dalla geografia |
| 2 | zone | Bologna (18) | 100% dalla geografia |
| 3 | sezione di censimento | Parma (1.357) | 100% dalla geografia |

Ravenna e Forlì mostrano che «assente dal catalogo open data» non significa
«assente»: per entrambe la fonte stava in una pubblicazione statistica del
sito comunale, fuori dal catalogo. Ravenna espone paese × sesso × area in un
`.xls` annuale (139 nazionalità, 17.870 persone, scarto +0,5% sulle sezioni
ISTAT); Forlì paese × sesso × unità in formato lungo, con granularità più
fine del livello di destinazione — 41 unità fra frazioni e rioni storici,
aggregate nei 21 quartieri — e un gruppo residuale dichiarato che copre il
16,5% dei casi, gestito dall'IPF come complemento specifico dell'unità.

**Conseguenza.** L'assunzione (4) di `assign_nationality.py` — *paese ⊥ zona
| (area, sesso)* — vale solo per quello script, che l'anello 3 sovrascrive
riassegnando `area` e `paese` da zero. Nel percorso corrente
(`fit_cs → assign_avq → enrich`) `assign_nationality.py` non viene eseguito.
Resta utile come ramo di confronto (`--keep-naz`, `--no-tier`) e per comuni
privi di sezioni o di open data.

Se i rumeni si concentrano in una zona e il portale comunale lo pubblica, la
popolazione sintetica lo rispecchia. Questa nota riguarda il canale
UE/extra-UE, cioè lo stadio (3b) e il margine di area entro cui (3c) opera.

## 12. Limiti

**K = 2 nelle sezioni ISTAT.** Il tracciato fornisce l'origine solo come
dicotomia: `ST16` = 4.702 coincide esattamente con l'aggregato comunale `EU`
2023, e `ST1` = 28.415 con `ALL`. Marocco e Ghana stanno nello stesso
gruppo, Romania e Germania nell'altro. Le quote qui riportate misurano
quindi il segnale della **dicotomia**, non quello della provenienza per
paese, che è verosimilmente maggiore. Il pipeline aggira il limite con gli
open data comunali (§ 11), ma la misura resta ancorata a K = 2.

Restano non identificate due partizioni a tre gruppi presenti nel tracciato
e non usate (`ST3`/`ST4`/`ST5` e `ST22`/`ST23`/`ST24`, entrambe chiudono
esattamente su `ST1`). Nessuna si decompone negli aggregati continentali
comunali. Il tracciato ISTAT le chiarirebbe; se una fosse l'origine a tre
gruppi, la misura andrebbe rifatta con K = 3.

**Il soffitto non è tutto raggiungibile.** Parte di I(S;K) è struttura a
scala di edificio, che nessuna partizione zonale può catturare. Il 2,4% di
Modena non significa che con la partizione giusta si arriverebbe al 100%.
Il massimo realmente raggiungibile richiederebbe un livello intermedio fra
sezione e quartiere — misurabile aggregando le sezioni in cluster spaziali
di taglia crescente e cercando dove la curva si appiattisce.

**Il sesso non è considerato.** Il pipeline condiziona su `(zona, sesso)`;
qui i due sessi sono aggregati, perché il sesso non è una variabile
territoriale. La verifica costa due esecuzioni con
`--gruppi "UE=ST17;NONUE=ST20"` e `"UE=ST18;NONUE=ST21"`.

**Confondimento fra dispersione insediativa e taglia delle celle.** Il
soffitto I(S;K) correla inversamente con la mediana di stranieri per sezione:
la correlazione di rango sulle sette configurazioni è −0,936 (p = 0,002).
Ravenna (5 stranieri per sezione) e Forlì (7) hanno i soffitti più alti,
Bologna (19) e Parma (17) i più bassi. Insediamento disperso significa
insieme sezioni piccole ed eterogeneità spaziale genuina, e le due
spiegazioni non sono separabili con questi dati. La correzione di bias non è
in discussione — il nullo per simulazione usa gli stessi conteggi di cella
dell'osservato, quindi è non distorta per costruzione — ma l'interpretazione
sostantiva del soffitto sì. Servirebbe un confronto a densità insediativa
costante.

**Dipendenza dalla fonte open data.** L'esposizione reale del pipeline non è
la granularità della zonizzazione ma la disponibilità di `opendata_paese`
per il comune: senza, si ricade al tier 0, che non ha alcun
condizionamento geografico sul paese — peggio del condizionamento di zona.

## 13. Implicazioni operative

Per la scelta dei comuni da aggiungere, il criterio non è il numero di zone
ma **se la partizione segue la geografia dell'insediamento**. La differenza è
sostanziale: Ravenna con 10 aree rende quasi il triplo di Bologna con 18.

`zona_probe.py` lo anticipa senza generare la popolazione, dai soli civici
ANNCSU: baricentri compatti e distanti dal centro indicano frazioni, cioè
partizioni allineate all'insediamento; raggi ampi e sovrapposti indicano
settori amministrativi ritagliati su tessuto continuo. Su Ravenna e Forlì la
diagnosi era corretta prima di qualunque generazione.

La variabile più critica resta però la fonte che determina il tier, e la
ricerca va estesa **oltre il catalogo open data**, alla sezione statistica
del sito comunale: è lì che stavano sia Ravenna sia Forlì.

Modena è il caso con il ritorno potenziale maggiore: soffitto al 13,31%, il
secondo più alto, e quota trattenuta al 2,4%, la più bassa. Non è meno
segregata per origine — è la sola delle sei a combinare molta struttura
disponibile, una partizione che non la intercetta, e nessuna fonte locale
per il tier.

## 14. Riproducibilità

Script: `scripts/perm_composizione.py`. Seed 20260731. Input:
`<comune>_sezioni_2023.csv` da `build_sezioni.py`. Nessuna dipendenza dal
ramo comunale del pipeline.

    for c in 036023 034027 037006 017029 039014 040012; do
      python perm_composizione.py $c -B 1000 --out /tmp/perm2_$c.csv
    done
    python perm_composizione.py 037006 --level COM_ASC1 -B 1000 \
        --out /tmp/perm2_bo6.csv

Nota: 037006 senza --level usa il default del registro, che per Bologna e'
COM_ASC2 (18 zone). La configurazione a 6 quartieri richiede --level
COM_ASC1 esplicito.

---

### Riferimenti

Deming, W.E. & Stephan, F.F. (1940). On a least squares adjustment of a
sampled frequency table when the expected marginal totals are known.
*Annals of Mathematical Statistics*, 11(4), 427–444.

Bishop, Y.M.M., Fienberg, S.E. & Holland, P.W. (1975). *Discrete
Multivariate Analysis: Theory and Practice*, cap. 3.

Miller, G.A. (1955). Note on the bias of information estimates. In H. Quastler
(a cura di), *Information Theory in Psychology*, 95–100.
