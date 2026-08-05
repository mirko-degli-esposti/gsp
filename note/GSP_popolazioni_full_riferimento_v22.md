# Popolazioni sintetiche GSP — documento di riferimento

**Versione 2.2 — 2 agosto 2026**
Descrive i file `popolazione_K9C_avq_full.csv` per gli undici comuni
emiliano-romagnoli piu' Brescia: come caricarli, cosa contengono, come sono
stati costruiti, quali limiti dichiarati portano con sé, dove trovare i dati
reali per il confronto e **come aggiungere un comune nuovo** (§12).

Le **fonti esterne** — 37, con universo, licenza, impronta e limiti d'uso
dichiarati — sono censite a parte in `fonti/registro.yaml`; la loro
documentazione è in `note/fonti_e_pacchetto_v8.md` (§9).

> **Alcuni attributi non stanno nel file.** Nome e cognome, titolo di
> studio dettagliato, settore e posizione professionale sono
> **derivazioni**: si calcolano quando servono, deterministicamente
> dall'`uid`, e non finiscono in nessun CSV né nel bundle. Questo
> documento descrive ciò che il file contiene; per le derivazioni vedi
> §2.4 e `note/fonti_e_pacchetto_v8.md`.

*Questa versione sostituisce tutte le precedenti.*

---

## 1. I file

```
~/progetti/gsp/data/comuni/{COMUNE}/constraints_2024/popolazione_K9C_avq_full.csv
```

| comune | codice | individui | attributi | tier paese |
|---|---|---|---|---|
| Brescia | `017029` | 198.259 | 40 | 1 |
| Parma | `034027` | 198.121 | 40 | 3 |
| Bologna | `037006` | 390.098 | 40 | 2 |
| Modena | `036023` | 184.597 | 40 | 0 |

Totale 971.075 individui sintetici, ciascuno con indirizzo civico e
coordinate geografiche.

### Caricamento

Ci sono tre trappole di tipo. Questo snippet le gestisce tutte:

```python
import pandas as pd, os

AVQ = ["AMBIENTE", "FIDUCIA", "SALUTE", "CRONI", "FUMO", "MH",
       "BMI", "BMIMIN", "CPESO",
       "PUNTIFI1", "PUNTIFI2", "PUNTIFI3", "PUNTIFI4", "PUNTIFI5",
       "PUNTIFI6", "PUNTIFI7", "PUNTIFI8", "PUNTIFI10", "PUNTIFI12",
       "PUNTIFI13", "VOTOUSL"]

def carica(comune, anno=2024):
    f = os.path.expanduser(
        f"~/progetti/gsp/data/comuni/{comune}/constraints_{anno}/"
        f"popolazione_K9C_avq_full.csv")
    p = pd.read_csv(f, low_memory=False, dtype={
        "zona": "string",        # 34027001: NON leggere come int
        "sezione": "string",     # 340270000994: 12 cifre
        "civico": "string",      # '19A': numero + esponente
    })
    for c in AVQ:
        p[c + "_num"] = pd.to_numeric(p[c], errors="coerce")
    return p
```

In alternativa, tutti i percorsi e i registri stanno in `gsp.common` (§4).

**Trappole:**

1. `zona` e `sezione` sono codici, non numeri.
2. Le variabili AVQ sono **stringhe** perché mescolano codici numerici e
   `non_applicabile` — tranne `SALUTE`, unica senza missing strutturali.
3. `area` usa `NaN` per gli italiani, non `non_applicabile` (§7).

---

## 2. Gli attributi

### 2.1 Anello 1 — MaxEnt (vincolati)

Dieci attributi le cui marginali e incroci riproducono il constraint set
censuario con MRE ≈ 4·10⁻⁴.

| colonna | modalità | note |
|---|---|---|
| `zona` | codice a 8 cifre | quartiere o zona statistica, §3 |
| `quartiere` | stringa | denominazione della zona |
| `sesso` | `M`, `F` | |
| `eta` | `0-8`, `9-14`, `15-24`, `25-34`, `35-49`, `50-64`, `65-74`, `75+` | bin del constraint set |
| `stato_civile` | `celibe_nubile`, `coniugato_unito`, `divorziato_sciolto`, `vedovo` | unioni civili collassate in `coniugato_unito` |
| `cittadinanza` | `ITL`, `FRG` | giuridica; `FRG` include gli apolidi |
| `istruzione` | `nessun_titolo`, `elementare`, `media`, `diploma`, `laurea_o_its`, `post_laurea` | `laurea_o_its` = triennale + ITS; `post_laurea` = magistrale + ciclo unico + dottorato |
| `condizione` | `occupato`, `in_cerca`, `studente`, `casalinga`, `percettore_pensioni`, `altra_condizione`, `non_applicabile` | `non_applicabile` = under 15 (categoria sostantiva) |
| `background` | `italiano_nativo`, `italiano_rientrato`, `naturalizzato_g2`, `naturalizzato_immigrato`, `straniero_g2`, `straniero_immigrato` | **non** coincide con `cittadinanza` |
| `origine_genitori` | `entrambi_italiani`, `madre_italiana_padre_straniero`, `madre_straniera_padre_italiano`, `entrambi_stranieri`, `non_applicabile` | |

Metà delle 30 combinazioni `background × origine_genitori` è logicamente
impossibile ed è esclusa dal supporto per costruzione.

### 2.2 Anello 2 — AVQ e nazionalità

| colonna | modalità | fonte |
|---|---|---|
| `area` | `UE`, `EXTRA_UE`, `NaN` (italiani) | `ST17/18/20/21` **della sezione** |
| `paese` | 143–151 paesi + `Italia` | censimento comunale **× fonte comunale geografica** (§6) |

**Ventuno variabili AVQ**, tutte assegnate **in blocco dallo stesso
donatore** (hot-deck), quindi con correlazioni interne preservate per
costruzione. Il pool è **regionale**: 8.111 donatori per la Lombardia,
4.629 per l'Emilia-Romagna, con condizionamento su
`sesso × macroetà × istruzione4` e collasso gerarchico progressivo.
Il pool impila **le annate 2023 e 2024** — non il 2022, che `assign_avq.py`
scarta perché vi manca `CRONI` — meno i record con `ISTRMi = 99`. Anatomia
completa, numerosità efficace e limiti: **§13**.

#### Codifiche — risolte sul tracciato ufficiale

| variabile | domanda | codifica |
|---|---|---|
| `AMBIENTE` | **soddisfazione per la situazione ambientale (aria, acqua, ecc.) della zona in cui vive** | 1 = molto … 4 = per niente |
| `FIDUCIA` | *"Lei pensa che ci si possa fidare della maggior parte della gente oppure bisogna stare molto attenti?"* | **1 = ci si può fidare** (24,5%), 2 = stare attenti |
| `SALUTE` | salute percepita | 1 = molto bene … 5 = molto male |
| `CRONI` | malattie croniche o problemi di salute ≥ 6 mesi | 1 = no, 2 = sì |
| `FUMO` | abitudine al fumo | 1 = fumatore, 2 = ex, 3 = mai |
| `MH` | indice SF-12 di salute mentale | continua 0–100, più alto = meglio |
| `BMI` | indice di massa corporea, adulti | 1 = sottopeso … 4 = obeso |
| `BMIMIN` | IOTF 2012, **3–17 anni** | 1 = normo/sotto, 2 = sovrappeso/obeso |
| `CPESO` | **frequenza con cui controlla il proprio peso** | 1 = più spesso … 5 = mai |
| `PUNTIFI*` | *"quanto si fida delle seguenti istituzioni"* | **0–10**, più alto = più fiducia |
| `VOTOUSL` | giudizio complessivo sul servizio ricevuto nell'ASL | 0–10 |

> **`FIDUCIA` è fiducia interpersonale generalizzata**, non istituzionale:
> è l'item classico di Rosenberg (WVS, ESS, GSS). La **polarità invertita**
> (1 = fiducia) è stata dedotta dal segno negativo delle correlazioni con
> `PUNTIFI`.

> **`AMBIENTE` è il costrutto più rilevante per il lavoro Caffaro**: non è
> preoccupazione ambientale generica ma **valutazione della qualità
> ambientale del proprio luogo di residenza**. Vedi §8.

#### La batteria di fiducia istituzionale

| variabile | istituzione | copertura |
|---|---|---|
| `PUNTIFI1` | Parlamento italiano | alta |
| `PUNTIFI2` | sistema giudiziario | alta |
| `PUNTIFI3` | forze dell'ordine | alta |
| `PUNTIFI4` | partiti politici | alta |
| `PUNTIFI5` | Parlamento europeo | alta |
| `PUNTIFI8` | **Governo regionale** | alta |
| `PUNTIFI10` | **Governo comunale** | alta |
| `PUNTIFI12` | vigili del fuoco | alta |
| `PUNTIFI6` | Presidente della Repubblica | ridotta |
| `PUNTIFI7` | Governo italiano | ridotta |
| `PUNTIFI13` | banche | ridotta |
| `VOTOUSL` | ASL (esperienza diretta) | bassa |

Struttura interna, replicata nel sintetico entro ±0,01:

```
PUNTIFI1  - PUNTIFI7   (Parlamento - Governo)      0,863
PUNTIFI8  - PUNTIFI10  (Regione - Comune)          0,812
PUNTIFI1  - PUNTIFI5   (Parlamento IT - UE)        0,792
PUNTIFI3  - PUNTIFI12  (forze ordine - vigili f.)  0,609
```

**Due fattori distinti.** Forze dell'ordine e vigili del fuoco correlano
0,61 fra loro ma solo 0,14–0,27 con le istituzioni politiche: è la
separazione fra fiducia nei *servizi* e fiducia nella *politica*.

**Regione e Comune sono quasi indistinguibili** (0,812). Per Caffaro
significa che chi diffida del Comune diffida anche di ARPA e ATS, che sono
articolazioni regionali: non esiste un canale istituzionale alternativo.

**Medie nazionali AVQ 2024**, ricalcolate il 2/8/2026 con
`scripts/riferimenti/medie_nazionali.py`: media pesata con `COEFIN` su
`ETAMi >= 5` (15 anni e piu'), cioe' **sullo stesso universo della popolazione
sintetica**.

| | media | | media |
|---|---|---|---|
| Vigili del fuoco | **8,06** | Governo comunale | **5,10** |
| Medici del SSN | **6,98** | Sistema giudiziario | 4,87 |
| Infermieri del SSN | **6,88** | Parlamento italiano | 4,68 |
| Forze dell'ordine | **6,68** | Governo regionale | **4,66** |
| Presidente della Repubblica | 6,66 | Parlamento europeo | 4,62 |
| Forze armate | 6,51 | Governo italiano | 4,41 |
| Giudizio sull'ASL | **6,32** | Banche | 4,37 |
| | | Partiti politici | 3,46 |

> **Non sono cifre pubblicate dall'ISTAT, e non lo sono mai state.** Cinque di
> questi valori circolavano nelle note di progetto senza riferimento;
> cercandone la fonte si scopre che **non esiste in quella forma**. L'ISTAT
> diffonde **percentuali** — «il 67,5% assegna punteggi tra 8 e 10 ai Vigili
> del fuoco» — non medie. Le uniche medie pubblicate sono nel **BES**, per
> quattro indicatori compositi, e vi compaiono forze dell'ordine e vigili del
> fuoco **insieme** (7,4 nel 2024). Amministrazione comunale, regionale e ASL
> non ci sono affatto.
>
> Ricalcolate dai microdati, le cinque cablate risultano **corrette entro
> 0,045**. Lo scarto e' sistematicamente negativo su quattro su cinque, ed e'
> la differenza di universo: l'ISTAT pubblica sui 14 anni e piu', noi
> calcoliamo sui 15, e sono i piu' giovani ad avere fiducia piu' bassa.
>
> In una figura la didascalia corretta e' **«elaborazione propria su microdati
> AVQ public use»**, non «fonte ISTAT»: sono due affermazioni diverse e solo
> la prima e' vera.

**Due letture che la tabella completa rende visibili.** Il personale sanitario
— medici 6,98 e infermieri 6,88 — sta subito sotto i vigili del fuoco e
**sopra le forze dell'ordine**, mentre le istituzioni politiche stanno tutte
fra 3,46 e 4,87. **Il divario fra fiducia nei medici e fiducia nel Comune e'
di 1,88 punti**: per un lavoro sulla comunicazione del rischio sanitario
veicolata dall'amministrazione, e' il dato di partenza.

E sei istituzioni politiche sono schiacciate entro mezzo punto (4,37–4,87):
in un grafico quelle righe si sovrappongono, e va tenuto presente disegnandolo.

L'errore standard riportato dallo script usa i pesi ma **non il grappolo
familiare**: la colonna `se_grappolo` lo corregge col fattore 1,66 di §13.3,
ed e' quella da usare.

#### Copertura: tre fasce

Il modulo AVQ **ruota davvero fra le annate**: `PUNTIFI6`, `PUNTIFI7`,
`VOTOUSL` e `FORZE_ARMATE` non esistono nei tracciati 2022 e 2023,
`PUNTIFI13` manca nel 2023. `assign_avq.py` distingue variabili *necessarie*
(se mancano, **l'annata intera si scarta**) da *opzionali* (`--targets-opt`,
prese dove ci sono): così le variabili a rotazione non costringono a
dimezzare il pool.

| fascia | variabili | copertura tipica |
|---|---|---|
| base (2023+2024) | le 9 originali, `PUNTIFI1,2,3,4,5,8,10,12` | 86–88% |
| solo 2024 | `PUNTIFI6,7,13` | 42–43% |
| solo 2024 × utenti ASL | `VOTOUSL` | 15–20% |

Il missing della seconda e terza fascia è **planned missing**: dipende
dall'annata del donatore, non dall'individuo. La *percentuale*, però, dipende
anche da noi: con il pool a due annate il 2024 vale il 52,8%, e la copertura
si prevede a due decimali dalla composizione del pool (§13.1).

**Universi diversi per variabile.** `BMIMIN` copre il 13,6% (minori 3–17),
`SALUTE` il 100%. Un `dropna()` listwise su tutte e 21 restituisce **zero
righe**. Usare `DataFrame.corr(min_periods=...)`, e vedere §11.

### 2.3 Anello 3 — risoluzione fine

| colonna | tipo | descrizione |
|---|---|---|
| `sezione` | codice a 12 cifre | sezione di censimento (`SEZ21_ID`, basi 2021) |
| `eta_anni` | 0–100 | età esatta in anni |
| `via` | stringa | odonimo ANNCSU |
| `civico` | stringa | numero + esponente (`12`, `19A`) |
| `lon`, `lat` | float, EPSG:4258 | coordinate del civico (≈ WGS84) |
| `indirizzo_fonte` | `sezione` / `zona` / `convivenza` | provenienza dell'indirizzo |

| | `sezione` | `zona` | `convivenza` |
|---|---|---|---|
| Brescia | 197.511 (99,62%) | 199 | 549 |
| Parma | 197.601 (99,74%) | 39 | 481 |
| Bologna | 389.432 (99,83%) | 36 | 630 |
| Modena | 184.269 (99,82%) | **278** | **50** |

- `zona`: la sezione è popolata ma priva di civici ANNCSU. Modena ha il
  valore più alto in termini relativi (0,15%), pur avendo **più civici di
  Brescia** (60.488 contro 49.730) a fronte di meno abitanti: non è
  scarsità complessiva ma distribuzione;
- `convivenza`: sezione fittizia `888888x`. **Nessun indirizzo**,
  coordinate = centroide della zona.

---

### 2.4 Attributi derivati — esistono, ma non sono nel file

Quattro attributi si possono ottenere per ogni individuo e **non stanno
in nessuna colonna**: si calcolano al momento, deterministicamente
dall'`uid`, e non finiscono né nel CSV né nel bundle del visualizzatore.

| attributo | modulo | condizionato su | fonte |
|---|---|---|---|
| nome, cognome | `gsp.nomi` | sesso, background, origine dei genitori, paese | anagrafiche comunali, repertori per paese |
| titolo di studio dettagliato | `gsp.istruzione` | istruzione, sesso, coorte | censimento 2011, 458 modalità |
| settore × posizione professionale | `gsp.lavoro` | sesso, comune | censimento 2011, 21 sezioni × 6 profili |

```python
import gsp.individui as I
d = I.campione("034027", {"quartiere": "Cittadella"}, n=20,
               dettaglio="narrativo")
print(I.scheda(d.iloc[0], anagrafica=True))
```

```
Maria Bruni — Via Ugo La Malfa, Cittadella
  45 anni · donna · laurea magistrale in medicina e chirurgia
  dipendente, sanità e assistenza sociale
```

**Perché non sono nel file.** Sono funzioni deterministiche di attributi
già presenti: non aggiungono informazione, ma rendono un record
riconoscibile come *persona* invece che come profilo statistico. Il
determinismo sostituisce la memorizzazione — dallo stesso `uid` esce
sempre lo stesso valore, quindi un campione è riproducibile e citabile
senza che nulla sia scritto su disco.

È anche la ragione per cui il bundle pubblico non li porta: la stessa
proprietà che li rende utili in una presentazione li renderebbe
problematici in un archivio scaricabile. Vedi
`note/piano_trattamento_v2.md` §3.1.

**Perché a valle e non nel MaxEnt.** Non è una scelta di comodità ma il
risultato di una misura: un attributo va nello spazio degli stati solo se
la sua struttura — tipicamente geografica — non è deducibile da ciò che
c'è già. Il criterio è la distanza in variazione totale fra composizione
condizionata e marginale (`gsp.tvd`), e per questi attributi dice
chiaramente «a valle».

Il livello **K10C**, che includeva il settore economico fra le variabili
vincolate, è il controesempio: trentasette milioni di stati contro
69.888, una catena di Gibbs riducibile per gli zeri strutturali del
blocco `MC`, e un vincolo che condiziona sul sesso ignorando
l'istruzione, che è tre volte più informativa. Resta come materiale
sperimentale, escluso dalla produzione.

---

## 3. Livello territoriale — non è uniforme, e i codici si sovrappongono

| comune | livello | zone | abitanti/zona | sezioni | sez./zona |
|---|---|---|---|---|---|
| Brescia | `COM_ASC1` (quartieri) | 33 | 6.008 | 1.822 | 55 |
| Parma | `COM_ASC1` (quartieri) | 13 | 15.240 | 1.357 | 104 |
| Bologna | `COM_ASC2` (zone statistiche) | 18 | 21.672 | 2.224 | 124 |
| Modena | `COM_ASC1` (quartieri) | **4** | **46.149** | 2.186 | **546** |

Bologna usa ASC2 perché i suoi 6 quartieri ASC1 sono troppo pochi; ASC3
(90 aree) è inutilizzabile per la coda di zone minuscole. Parma e Modena
pubblicano **solo** ASC1. Il livello è **fissato nel registro** di
`gsp.common`, non scelto da riga di comando.

**Le quattro zone di Modena sono la partizione più grossolana in
pipeline.** Si usano comunque: servono ai vincoli Z del MaxEnt e danno un
`quartiere` leggibile, mentre il lavoro geografico lo fa l'anello 3 (§10).

### 3.1 I codici ASC si sovrappongono fra livelli

I livelli sono numerati **indipendentemente**. A Bologna `COM_ASC1` va da
`37006011` a `37006016` e `COM_ASC2` da `37006001` a `37006018`.

```
37006011  come ASC1 -> Borgo Panigale-Reno  (quartiere, 61.149 ab.)
37006011  come ASC2 -> Marconi              (zona statistica, 14.687 ab.)
```

**Il codice da solo non identifica la zona.** Un merge sul solo codice
riesce e restituisce il nome sbagliato, senza errori né valori mancanti.
`G.verifica_livello()` intercetta il caso.

### 3.2 Le denominazioni delle zone vanno verificate, sempre

Fino al 29/07/2026 il dizionario `codice → nome` di Bologna era
**permutato**: 16 codici su 18. Nessun controllo strutturale poteva
vederlo — una permutazione resta una biiezione perfetta. I dati numerici
erano corretti, perché calcolati sui codici; sbagliate erano solo le
etichette leggibili, cioè ciò che finisce in mappe e tabelle.

**Metodo di verifica**, in ordine di praticità. Bastano due assi
concordanti; il terzo è disponibile solo in alcuni casi.

**(a) Baricentro e dispersione dei civici.** Dal file
`{prov}_{nome}_civici_sezioni_asc.csv`, media e deviazione standard di
`COORD_X_COMUNE`/`COORD_Y_COMUNE` per `COM_ASC*`, convertite in km. Il
centro storico si riconosce dal raggio minimo; i nomi che contengono
riferimenti cardinali si accoppiano alle direzioni. Nessun download.

**(b) Concentrazione dei toponimi.** Gli odonimi ANNCSU che contengono un
toponimo devono cadere nel quartiere che lo nomina.

**(c) Popolazione per zona da fonte comunale.** Se il portale pubblica la
popolazione per quartiere, il confronto con `P1` aggregato per `COM_ASC*`
identifica la mappa. Lo scarto atteso è ~1–2% (anagrafe contro censimento).

**(d) Struttura della gerarchia**, solo per comuni con due livelli ASC: le
taglie dei gruppi si sovrappongono in un solo modo.

Su Modena i tre assi disponibili hanno dato lo stesso esito:

```
codice     est_km  nord_km  raggio_km  civici   pop.cens.  pop.anagr.
36023001     0,11     0,64       0,68  10.234      24.469      24.038
36023002     2,09     1,36       2,22  14.662      48.018      48.376
36023003     0,85    -2,11       2,34  17.869      59.842      59.675
36023004    -2,65     0,63       3,07  17.723      52.268      52.051

toponimi: SAN FAUSTINO -> 004 (100%) · CROCETTA -> 002 · BUON PASTORE -> 003
          SAN DAMASO -> 003 · EMILIA CENTRO -> 001
```

### Denominazioni

**Parma** (13 quartieri)

```
34027001 Parma Centro    34027006 San Pancrazio        34027011 Cittadella
34027002 Oltretorrente   34027007 San Leonardo         34027012 Montanara
34027003 Molinetto       34027008 Cortile San Martino  34027013 Vigatto
34027004 Pablo           34027009 Lubiana
34027005 Golese          34027010 San Lazzaro
```

**Modena** (4 quartieri, numerazione ufficiale del Comune)

```
36023001 Centro Storico              (portale comunale: CENTRO STORICO-S.CATALDO)
36023002 Crocetta, San Lazzaro, Modena Est
36023003 Buon Pastore, Sant'Agnese, San Damaso
36023004 San Faustino, Madonnina, Quattro Ville
```

Brescia e Bologna sono in `gsp.common`. I codici ASC2 di Bologna
seguono l'ordine **alfabetico** dei nomi, ignorando gli spazi.

---

## 4. `gsp.common` — registro e primitive condivise

Consolida i cinque registri di comuni duplicati negli script. Nel registro
sta **solo ciò che non è derivabile**; i percorsi sono formule sul codice
ISTAT.

```python
import gsp.common as G

G.info("034027")          G.procom("034027")        # 34027
G.cod_prov("034027")      G.cod_avq("034027")       # 80 (REGMf in AVQ)
G.livello_col("037006")   G.zona_nomi("037006")
G.verifica_livello(codici, comune)
G.path_sezioni / path_civici / path_constraints / path_comune / path_shp
G.largest_remainder(n, pesi)      G.spartisci(idx, conta, valori)
G.norm_code(serie, comune)        G.norm_nome("S. Leonardo")
G.paesi_censuari(comune)          G.etichette_paese(comune)
G.risolvi_paese(etichetta, rif)   G.EU27_ISO   G.AGGREGATI_PAESE
```

```bash
python -m gsp.common --check
python -m gsp.common --dump-nomi 037006
```

Il consolidamento è stato eseguito come **refactor puro**, verificato per
identità byte-a-byte dell'output su ogni script migrato.

Dal 2 agosto 2026 il modulo vive in `src/gsp/common.py`, dentro il pacchetto
installato con `pip install -e .`: si importa da qualunque directory,
notebook e Colab compresi. Anche la migrazione a pacchetto è stata verificata
con lo stesso metodo — baseline catturata **prima**, `diff -r` dopo, identità
byte-a-byte su tutti i comandi di controllo. Restano da spostare
`istat_sdmx.py` e `opendata_paese.py`, che sono libreria di fatto
(`fetch_comune.py` importa il primo, `enrich.py` il secondo); il secondo è
ibrido — CLI, sei funzioni lettrici e la logica IPF — e va prima separato.

---

## 5. La pipeline

```
fetch_comune.py         SDMX ISTAT -> 11 tavole censuarie comunali
build_sezioni.py        file regionale -> {comune}_sezioni_2023.csv
join_civici_sezioni.py  ANNCSU + shapefile -> civici agganciati alle sezioni
build_zona_tables.py    sezioni -> Z1..Z4, Z6 al livello ASC scelto
build_constraints.py    tavole -> constraint set (blocchi c1..c10)
cs_build.py             -> supporto |X| + vincoli  (cs_K9C.json)
fit_cs.py               -> MaxEnt esatto -> popolazione_K9C.csv
                                                   |
assign_nationality.py   -> + paese (comunale)      |  anello 2
assign_avq.py           -> + 21 variabili AVQ      |
                                                   |
enrich.py               -> + sezione, area, paese (geografico),
   usa gsp.opendata         eta_anni, indirizzo, lon/lat      anello 3
```

`|X|` = 161.280 × n_zone. MRE(α>0) ≈ 4·10⁻⁴, **indipendente da `|X|`** su
quattro punti che coprono un ordine di grandezza (6,5·10⁵ → 5,3·10⁶).

### Perché l'allocazione esatta conta

MAE della popolazione per sezione: **0,74–1,58** su medie di 84–175
abitanti. Un campionamento multinomiale darebbe ≈ 9,6.

Il MAE **non cresce con la popolazione** e sembra anzi migliorare con zone
più grandi: Modena, con 546 sezioni per zona, ha il MAE più basso (0,74).

---

## 6. Condizionale geografico del paese

| tier | livello | fonte | comune |
|---|---|---|---|
| **0** | comune | solo censimento | **Modena**, e ogni comune nuovo |
| 1 | quartiere | 33 CSV, senza sesso, ~19 paesi + residuale | **Brescia** |
| 2 | zona | parquet con sesso, 155 paesi | **Bologna** |
| 3 | sezione | microdati individuali | **Parma** |

`--no-tier` forza il comportamento comunale su qualunque comune.
**Copertura: 100% dalla geografia su tutte e quattro, zero fallback** — il
peso di sezione per gli stranieri è `P × q` con `q = ST/P`, quindi nessuno
straniero può atterrare dove il censimento non ne conta.

### Formulazione

Le fonti locali sono **anagrafiche** e di data diversa dal censimento. Se
ne usa la **forma**, non i livelli:

```
seed        T0(p,s,g) = struttura locale
margine 1   somma_g  T(p,s,g) = censimento comunale (paese, sesso)
margine 2   somma_ps T(p,s,g) = popolazione straniera censuaria di g
```

Due margini censuari con lo stesso totale: sistema sempre risolubile, IPF
converge in 9–88 iterazioni con scarto ~1e-11. Imporre anche i conteggi
locali renderebbe i margini incompatibili (anagrafe 40.090 stranieri a
Brescia contro 37.478 censuari).

Con la fonte assente il seed è la quota nazionale replicata su ogni zona.

### Il tier 0 è collaudato

Modena è il primo comune senza fonte locale, e il ramo di default — quello
che ogni comune nuovo userà — è stato verificato end-to-end confrontandolo
con `--no-tier`:

```
distanza in variazione totale, complessiva:   0,0023   (66 stranieri su 28.412)
per quartiere, media:                         0,029
per confronto, condizionale geografico:       0,156 - 0,197
```

**Il collaudo ha scoperto due bug latenti**, entrambi della stessa
famiglia — classificare per etichetta invece che per codice:

- le denominazioni ISTAT sono invertite (`Ceca, Repubblica`), quindi il
  confronto con `startswith` classificava la Repubblica Ceca come
  extra-UE;
- la regex sugli aggregati catturava `africa` ovunque nella stringa,
  quindi escludeva `Sud Africa`, che è un paese.

Entrambi ora usano i codici (`G.EU27_ISO`, `G.AGGREGATI_PAESE`). Il filtro
va fatto **per esclusione e non per forma del codice**: i paesi hanno di
norma un ISO alpha-2 ma non sempre (`X95` Kosovo, `XSD_S` Sud Sudan), e
alcuni aggregati hanno forma alpha-2 — `EU` in particolare, somma dei 27
già presenti singolarmente, gonfiava il margine censuario del 21%.

### Riconciliazione delle denominazioni

| | agganciati | residuo |
|---|---|---|
| Brescia | 89,2% | 4.346 = `ALTRE CITTADINANZE`, **tetto strutturale della fonte** |
| Bologna | 100,0% | 7 persone in paesi assenti dal censimento |
| Parma | 100,0% | 13 persone |

### Quanto porta la geografia

Frazione di stranieri che cambia nazionalità passando dal condizionale
comunale a quello geografico, contro la stessa quantità sotto **ipotesi
nulla** (due permutazioni indipendenti).

| | | osservata | nulla | **eccesso** |
|---|---|---|---|---|
| **Brescia** | per quartiere | 0,197 | 0,094 | **2,08** |
| | per sezione | 0,408 | 0,393 | 1,04 |
| **Parma** | per quartiere | 0,156 | 0,074 | **2,10** |
| | per sezione | 0,530 | 0,412 | **1,29** |
| **Bologna** | per quartiere | 0,169 | 0,066 | **2,57** |
| | per sezione | 0,421 | 0,417 | 1,01 |

**A livello di quartiere l'informazione è sostanziale e simile ovunque**:
2,1–2,6 volte quanto si sposterebbe per caso.

**Una fonte povera ma geograficamente risolta vale quanto una ricca.**
Brescia (19 paesi più un residuo del 10,8%, senza sesso) ottiene 2,08
contro il 2,57 di Bologna (155 paesi con sesso). Per i comuni futuri:
basta una tabella `paese × quartiere`, anche troncata alle prime venti
nazionalità.

**Brescia e Bologna a livello di sezione danno 1,04 e 1,01**, cioè nulla —
correttamente, perché il loro condizionale si ferma alla zona. Questo
**valida la metrica per via negativa**. Il 1,29 di Parma è l'unico eccesso
reale sotto il quartiere.

### I microdati di Parma: condizionale o validazione

202.111 righe, una per residente, con `SEZ21`, `Cittad`, `ETA`, `Sesso`,
`Ncomp`, `Relpar`. `SEZ21_ID = "34027" + SEZ21.zfill(7)`, aggancio 99,9%.

| uso | variabili |
|---|---|
| **condizionale** | `Cittad × SEZ21 × Sesso` |
| **validazione esterna, mai usate per generare** | `ETA × SEZ21`; `Ncomp`, `Relpar`; co-occorrenza di nazionalità nella stessa sezione; `Tipores` |

---

## 7. Limiti e assunzioni dichiarate

| n. | assunzione | dove |
|---|---|---|
| (4') | `paese ⊥ tutto \| (area, sesso, geo)` — `geo` secondo il tier; per il tier 0 non vincola | §6 |
| (6) | `target AVQ ⊥ tutto \| (sesso, macroetà, istruzione4, regione)` | AVQ |
| (8) | `sezione ⊥ (istruzione, condizione, background) \| (zona, sesso, età3, cittadinanza)` | anello 3 |
| (9) | entro il quinquennio, l'età segue la distribuzione **comunale** per anno singolo | anello 3 |
| (10) | l'indirizzo è uniforme fra i civici della sezione | anello 3 |
| (11) | **nessuna struttura familiare** | anello 3 |

### Limiti della risoluzione per età

- **L'istruzione ha risoluzione effettiva di 4 classi d'età, non 8.** Il
  vincolo usa `Y9-24`, `Y25-49`, `Y50-64`, `Y_GE65`; dentro ogni classe la
  distribuzione viene da un **IPF con soglie minime di conseguimento**
  (`elementare` 10, `media` 13, `diploma` 18, `laurea_o_its` 20,
  `post_laurea` 22).
- **Resta sovrastimata `media` nel bin `9-14`**.
- **Effetto coorte perso fra `65-74` e `75+`**.
- **Il background migratorio ha risoluzione di zona**, non di sezione.

### Convenzioni per "assente" — non uniformate

| forma | dove |
|---|---|
| `non_applicabile` (stringa) | `condizione`, `origine_genitori`, 20 delle 21 AVQ |
| `NaN` | `area`, `via`, `civico` |
| nessuna | `SALUTE`, `paese` (= `Italia` per gli italiani) |

---

## 8. Punti aperti

### Aggiungere la cittadinanza alla cella di condizionamento AVQ

*Analisi completata il 29/07/2026, patch predisposta e non applicata.*

AVQ pubblica `CITTMi` (3 modalità: `1` italiana, `3` e `9` da
identificare). L'effetto sulla **fiducia istituzionale è sostanziale e
monotono**, ~1 punto su 10, replicato in due regioni indipendenti:

| media pesata | ITA (1) | gr. 3 | gr. 9 |
|---|---|---|---|
| `PUNTIFI10` Comune, Lombardia | 5,16 | 5,81 | 7,00 |
| `PUNTIFI8` Regione, Lombardia | 4,38 | 5,24 | 6,51 |
| `PUNTIFI10` Comune, Emilia | 5,22 | 6,09 | 6,59 |
| `PUNTIFI8` Regione, Emilia | 4,97 | 5,97 | 5,78 |

**I non italiani si fidano delle istituzioni PIÙ degli italiani** —
direzione opposta all'intuizione, ma nota in letteratura. **Nessun effetto
invece su `AMBIENTE` (2,37/2,30/2,14) né su `FIDUCIA` (1,75/1,77/1,84).**

Numerosità: ~430 non italiani nel pool emiliano su due annate. Il livello
di cella pieno non regge (~11 donatori), il secondo sì (~43). Serve il
collasso gerarchico con la cittadinanza in priorità alta:

```python
CELL_COLS = ["sesso", "macroeta", "istr4", "citt"]
CELL_LEVELS = [
    ["sesso", "macroeta", "istr4", "citt"],
    ["sesso", "macroeta", "citt"],
    ["macroeta", "citt"],
    ["sesso", "macroeta", "istr4"],
    ["sesso", "macroeta"],
    ["macroeta"],
]
```

**Prima di applicare**: identificare le modalità `3` e `9` in
`METADATI/Classificazioni/`.

**Limite da dichiarare comunque**: il campione AVQ di stranieri è
autoselezionato sulla competenza linguistica. Descrive gli stranieri più
integrati, quindi la fiducia istituzionale stimata è verosimilmente
**sovrastimata**. Per un lavoro mirato la fonte giusta sarebbe *Condizione
e integrazione sociale dei cittadini stranieri*.

### Modena: due opportunità non sfruttate

*Rilevate il 29/07/2026 esplorando il portale open data comunale.*

**Rioni: una partizione dieci volte più fine dell'ASC1.** Il dataset
*Serie storiche della popolazione residente* espone la popolazione per
**37 rioni**, con cittadinanza binaria, età quinquennali e sesso, dal 2002
al 2024.

| | zone | ab./zona | quota stranieri min → max |
|---|---|---|---|
| ASC1 (in uso) | 4 | 46.149 | 0,124 → 0,255 (fattore 2) |
| rioni | 37 | 4.968 | 0,039 → 0,590 (**fattore 15**) |

Il guadagno **non** sarebbe sulla quota di stranieri — le sezioni sono già
59 volte più fini e `ST1` è dato censuario — ma sull'**assunzione (8)**:
istruzione, condizione professionale e background migratorio hanno
risoluzione di zona, e con quattro zone da 46.000 abitanti sono di fatto
uniformi sulla città. Con 37 zone acquisterebbero struttura geografica
reale, che in una città è forte proprio su quegli attributi.

Serve una **mappatura sezione → rione**, ottenibile dai civici se il
portale pubblica la numerazione civica con il rione (stesso meccanismo del
voto di maggioranza già usato altrove), oppure per join spaziale dalle
geometrie dei rioni. Da verificare che i rioni **partizionino** le sezioni:
una sezione a cavallo introdurrebbe un errore da misurare.

Costo: è una **deviazione dallo standard ISTAT**. Il registro dovrebbe
ammettere livelli non-`COM_ASC*`, e il confronto fra città si
complicherebbe. `|X|` K9C passerebbe da 645.120 a 5.967.360.

**Cittadinanza per paese: non disponibile.** I dataset demografici del
portale (*Popolazione residente dal 1995*, *Serie storiche*, *Emigrati per
sesso cittadinanza ed età*) hanno tutti `CITTADINANZA` **binaria**. Modena
resta quindi **tier 0**, ed è il caso che ha permesso di collaudare il ramo
di default (§6).

**Serie storiche 2002–2024 per rione.** Non serve alla pipeline, che è
statica, ma è materiale per una domanda diversa: come si è formata la
geografia attuale. L'anzianità di insediamento di una comunità in un
quartiere è un predittore di attaccamento al luogo, potenzialmente
rilevante per il lavoro sulla percezione ambientale.

### Altri punti aperti

- **`AMBIENTE` non varia per quartiere.** È il **candidato numero uno per
  il tilt areale**. La cittadinanza non basta: serve un'altra covariata di
  zona e un target areale osservato su cui calibrarla — senza il quale il
  parametro del tilt resterebbe un'assunzione travestita da risultato.
- **`assign_nationality.py` è quasi vestigiale.** `area` e `paese` che
  produce sono **interamente sovrascritti** da `enrich.py`; l'unica
  funzione residua è generare il file che `assign_avq.py` legge, al quale
  servono solo `sesso`, `eta`, `istruzione`.
- **Ramo di remapping ASC2→ASC1 irraggiungibile** in
  `assign_nationality.py`: `G.verifica_livello()` interviene prima.
- **Provenienza del paese non tracciata**: non esiste `paese_fonte`.
- **Struttura familiare.** `Ncomp` e `Relpar` dei microdati di Parma.
- **K10C.** Esiste solo per Brescia e porta l'istruzione pre-correzione.
- **San Vito dei Normanni** (`074017`): `COM_ASC1` ha un solo valore,
  resterà un comune **senza articolazione zonale**.
- **Confronto fra città.** Risoluzioni diverse su partizioni di taglia
  diversa: per un confronto rigoroso conviene rigenerare al **quartiere**.

---

## 9. Dove sono i dati reali, per il confronto

```
{COMUNE}/constraints_2024/
    cs_K9C.json      vincoli con alpha target, categories, domain_sizes, zona_nomi
    targets_K9C.json tabelle target per blocco
    fit_K9C.json     lambdas, MRE, entropia, supporto
    manifest.json    fonte e tipo (hard/soft) di ogni blocco
{COMUNE}/zona_2023/  z1..z4, z6, zona_nomi
data/submun/{slug}_sezioni_2023.csv
    P1, ST1, ST16/ST19, P30-P45 e P67-P82, ST25-ST30
data/opendata/{COMUNE}/   fonti comunali per §6
data/avq/anni/avq{Y}/METADATI/AVQ_Tracciato_{Y}.html   codifiche AVQ
```

### Il registro delle fonti

Dal 2 agosto 2026 le fonti esterne sono censite in `fonti/registro.yaml`:
**24 schede** con universo, licenza, attribuzione, impronta e limiti d'uso
dichiarati per ciascuna — le due di cognomi fiorentini, undici tavole ISTAT
SDMX per dodici comuni, le sezioni di censimento con il loro tracciato, i
microdati AVQ, e tutte e sei le fonti locali per il paese di cittadinanza.

```bash
python -m gsp.fonti --elenco       # inventario
python -m gsp.fonti --verifica     # i grezzi non sono cambiati?
python -m gsp.fonti --copertura    # fonti usate e NON registrate
python -m gsp.fonti --pubblico     # cosa puo' finire in un repo pubblico
```

Il principio è la versione a monte di «ogni statistica richiede una
configurazione di confronto»: **ogni fonte richiede il suo universo
dichiarato**, e un file senza universo è un elenco di numeri, non una
misura. La configurazione operativa delle fonti locali non è riscritta ma
referenziata da `gsp.common` con `parametri_da`, così le due dichiarazioni
non possono divergere.

Documentazione completa, con i dodici normalizzatori e le trappole
incontrate: `note/fonti_e_pacchetto_v3.md`.

Versione senza condizionale geografico, per i confronti:

```bash
python scripts/attributi/enrich.py 037006 --anno 2024 --no-tier \
    --out popolazione_K9C_avq_full_tier0.csv
```

### Geometrie per la visualizzazione

```
data/geodata/{regione}/R{NN}_21/SHP/R{NN}_21_WGS84.shp
    R03 Lombardia    R08 Emilia-Romagna    R16 Puglia    CRS EPSG:32632
```

I poligoni delle zone si ottengono per **dissolve delle sezioni**:

```python
col = G.livello_col("034027")
s = gpd.read_file(G.path_shp("emilia_romagna"))
s = s[s.PRO_COM == G.procom("034027")]
zone = s.dissolve(by=col).reset_index().to_crs("EPSG:4326")
zone["nome"] = zone[col].astype("Int64").astype(str).map(G.zona_nomi("034027"))
```

**Per Bologna `G.livello_col` è `COM_ASC2`**: un dissolve su `COM_ASC1`
darebbe 6 poligoni invece di 18, e i codici — sovrapposti fra livelli
(§3.1) — mapperebbero comunque su dei nomi, sbagliati.

---

## 10. Riepilogo numerico

Esecuzioni del 29 luglio 2026.

| | Brescia | Parma | Bologna | Modena |
|---|---|---|---|---|
| codice ISTAT | `017029` | `034027` | `037006` | `036023` |
| regione (AVQ) | Lombardia (30) | Emilia-R. (80) | Emilia-R. (80) | Emilia-R. (80) |
| popolazione | 198.259 | 198.121 | 390.098 | 184.597 |
| attributi | 40 | 40 | 40 | 40 |
| zone | 33 (ASC1) | 13 (ASC1) | 18 (ASC2) | 4 (ASC1) |
| sezioni | 1.822 | 1.357 | 2.224 | 2.186 |
| sezioni occupate | 1.773 | 1.313 | 2.152 | 2.118 |
| civici ANNCSU | 49.730 | 35.826 | 77.595 | 60.488 |
| stranieri (censimento) | 37.478 | 34.436 | 58.963 | 28.415 |
| stranieri (sintetici) | 37.475 | 34.434 | 59.130 | 28.412 |
| quota stranieri | 18,9% | 17,4% | 15,1% | 15,4% |
| donatori AVQ nel pool | 8.111 | 4.629 | 4.629 | 4.629 |
| donatori distinti usati | 8.108 (100,0%) | 4.618 (99,8%) | 4.625 (99,9%) | 4.617 (99,7%) |
| riuso medio donatore | 24,5× | 42,9× | 84,3× | 40,0× |
| supporto \|X\| K9C | 5.322.240 | 2.096.640 | 2.903.040 | **645.120** |
| tier paese (§6) | 1 | 3 | 2 | **0** |

**Il riuso dei donatori è un tetto strutturale.** Il 99,7–100% del pool
viene usato almeno una volta: la diversità dell'anello 2 è satura. Ma il
numero di donatori usati **non è** la numerosità efficace, che è più bassa di
un fattore 2,8 per il riuso diseguale: vedi §13.3.

### Validazione per sezione

| | sezioni | media/sez | MAE pop. | corr | MAE stranieri | corr | MAE UE | corr |
|---|---|---|---|---|---|---|---|---|
| Brescia | 1.822 | 108,8 | 1,58 | 0,9998 | 0,98 | 0,9989 | 0,13 | 0,9976 |
| Parma | 1.357 | 146,0 | 1,43 | 0,9999 | 1,13 | 0,9985 | 0,16 | 0,9980 |
| Bologna | 2.224 | 175,4 | 1,36 | 0,9999 | 1,08 | 0,9983 | 0,17 | 0,9982 |
| Modena | 2.186 | 84,4 | **0,74** | 0,9999 | 0,63 | 0,9993 | 0,09 | 0,9969 |

I totali comunali coincidono esattamente con il censimento. Gli scarti sui
totali di stranieri (−3, −2, +167, −3) sono entro 0,7 σ del rumore
multinomiale.

### Struttura spaziale: la sezione conta molto più della zona

Decomposizione della varianza della quota UE fra stranieri, al netto della
discretizzazione. **Calcolata dal file sezioni**, cioè dalla verità
censuaria.

| | abitanti/zona | var **tra** zone | var reale **dentro** | sovradisp. | rapporto |
|---|---|---|---|---|---|
| Brescia (33 zone) | 6.008 | 0,00168 | 0,00991 | 2,89× | **5,9×** |
| Parma (13 zone) | 15.240 | 0,00110 | 0,01249 | 3,50× | **11,3×** |
| Bologna (18 zone) | 21.672 | 0,00072 | 0,01124 | 3,04× | **15,7×** |
| Modena (4 zone) | 46.149 | **0,00040** | 0,01756 | 3,17× | **43,5×** |

**Il rapporto cresce monotonamente con la dimensione media delle zone**, su
quattro partizioni da 4 a 33 unità. Condizionare sul quartiere perde
l'85–98% del segnale compositivo.

**Quantità e composizione hanno scale spaziali diverse.** Modena lo rende
evidente: le quattro zone distinguono nettamente il Centro Storico (25,5%
di stranieri) dal resto (12,4–16,9%), ma la composizione *per origine* di
quegli stranieri è quasi identica ovunque. L'accessibilità economica del
patrimonio abitativo opera a scala di quartiere; la segregazione per
nazionalità opera per isolato.

### Validazione esterna puntuale

| | fonte comunale | sintetico (cens. 2023) | rapporto |
|---|---|---|---|
| Primo Maggio (Brescia), quota stranieri | 0,329 | 0,293 | 1,12 |
| Bologna, quota UE fra stranieri | 0,214 | 0,213 | 1,00 |
| Modena, popolazione per quartiere (4 zone) | — | — | 0,982–1,007 |

### Un fatto rilevante per il progetto Caffaro

```
Fiumicello           0,368        Buffalora          0,088
Centro Storico Nord  0,314        Villaggio Violino  0,073
Primo Maggio         0,293
```

**Fiumicello, uno dei due quartieri della `ZonaCaffaro`, ha la più alta
quota di stranieri della città** — il doppio della media comunale. Ma
`AMBIENTE`, `FIDUCIA` e le `PUNTIFI` sono condizionate su sesso, età e
istruzione e **non** su cittadinanza né sulla geografia (§8).

---

## 11. Due principi metodologici ricorrenti

### 11.1 Rapportare sempre all'ipotesi nulla

**Ogni metrica che scala con la numerosità di cella va rapportata alla
propria ipotesi nulla prima di essere confrontata fra configurazioni
diverse.** Quattro occorrenze, stessa forma:

1. **Varianza compositiva della quota UE** (§10) — isolata con un test di
   sovradispersione contro l'assegnazione casuale entro zona.
2. **Distanza compositiva fra tier** (§6) — il 0,569 grezzo di Parma è per
   il 79% discretizzazione; l'eccesso reale è 1,29.
3. **Pavimento MRE del PCD** (`nota_mre_floor_v01.tex`) — la formula
   `1/(2√N)` del paper GibbsPCD confonde errore assoluto e relativo.
4. **Numerosità effettiva di una popolazione hot-deck** (§13.3) — le
   correlazioni AVQ sembrano poggiare su ~200.000 osservazioni ma poggiano su
   un pool di 4.629 donatori, la cui numerosità **efficace** di Kish è
   1.478–2.007 sull'intera popolazione e ~3.200 sull'universo di una singola
   variabile. Il conteggio dei donatori distinti sopravvaluta di un fattore
   2,8; la correzione per grappolo familiare toglie un altro 40%.

In tutti e quattro i casi la metrica grezza ordinava le configurazioni in
modo diverso — e talvolta inverso — rispetto alla metrica corretta.

**Corollario**: quando esiste una configurazione in cui il segnale è *noto
essere assente*, va usata come taratura.

### 11.2 Due percorsi che devono coincidere sono un test permanente

Il confronto fra ramo tier e ramo comunale non serve solo a misurare il
guadagno del condizionale geografico: è una **verifica incrociata**. Su
Modena, dove il tier 0 deve riprodurre esattamente il comportamento
comunale, la discrepanza residua ha rivelato due bug latenti (§6) presenti
da sempre e invisibili a qualunque test su un solo ramo.

---

## 12. Aggiungere un comune nuovo

Procedura ricavata dall'aggiunta di Modena (29/07/2026). Tempo complessivo
circa mezz'ora, di cui tre minuti di download vincolati dal rate limit
ISTAT. Il grosso del lavoro umano sta nella **fase 2**.

### Prerequisiti regionali (una volta per regione)

| serve | dove |
|---|---|
| `Dati_regionali_2023.zip` → `R{NN}_..._sezioni.xlsx` | `data/submun/Dati_regionali_2023/` |
| shapefile basi territoriali `R{NN}_21_WGS84.shp` | `data/geodata/{regione}/R{NN}_21/SHP/` |
| indirizzario ANNCSU regionale | `data/geodata/{regione}/indirizzario*/` |
| voce in `G.REGIONI` | `src/gsp/common.py` |

Poi, una volta sola per regione:

```bash
python scripts/vincoli/join_civici_sezioni.py {regione}
```

Processa **tutte le province** della regione, quindi i civici di ogni
comune di quella regione sono già pronti.

### Fase 0 — verifica preliminare (nessun download)

```bash
python scripts/vincoli/build_sezioni.py {CODICE} --regione {N} --dry-run
```

Funziona anche senza voce di registro. Riporta popolazione, numero di
sezioni e, per ciascun livello `COM_ASC1/2/3`, quante zone e con quale
distribuzione di popolazione.

**Decisione: quale livello usare.** Criteri emersi finora:

| n. zone | ab./zona | giudizio |
|---|---|---|
| 1 | — | nessuna articolazione: comune K6C/K8C senza `zona` |
| 4–6 | 45–65k | grossolano ma usabile (Modena) |
| 13–18 | 15–22k | buono |
| 33+ | ~6k | ottimo |
| zone con < ~500 ab. | — | inutilizzabili: celle vuote nei vincoli Z |

Se esistono più livelli, scegliere quello con la cardinalità migliore
purché non abbia code minuscole (Bologna ASC3 ha 90 aree ma la più piccola
ha 13 abitanti: scartato).

### Fase 1 — bootstrap del registro

Voce **parziale** in `G.COMUNI`, con `nomi: None`:

```python
    "036023": {
        "nome": "Modena", "slug": "modena", "regione": "emilia_romagna",
        "livello": "quartieri",
        "livelli": {
            "quartieri": {"col": "COM_ASC1", "n": 4,
                          "nomi": None, "parent": None},
        },
    },
```

```bash
python scripts/vincoli/build_sezioni.py {CODICE}
```

Scrive `data/submun/{slug}_sezioni_2023.csv`.

### Fase 2 — denominazioni delle zone (il punto critico)

**Dove cercarle**: portale open data comunale, sito istituzionale,
delibere sulle circoscrizioni. Non esistono in nessun file ISTAT.

**Come verificarle**: §3.2, almeno due assi concordanti. Il metodo (a),
baricentri dei civici, richiede solo il file civici già generato:

```python
c = pd.read_csv(G.path_civici(comune), dtype={"CODICE_ISTAT": str},
                low_memory=False)
c = c[c.CODICE_ISTAT == comune]
c = c[pd.to_numeric(c.COM_ASC1, errors="coerce").fillna(0) != 0]
c["z"] = pd.to_numeric(c.COM_ASC1, errors="coerce").astype("Int64").astype(str)
lon0, lat0 = c.COORD_X_COMUNE.mean(), c.COORD_Y_COMUNE.mean()
g = c.groupby("z").agg(civici=("COORD_X_COMUNE","size"),
                       lon=("COORD_X_COMUNE","mean"), lat=("COORD_Y_COMUNE","mean"),
                       dlon=("COORD_X_COMUNE","std"), dlat=("COORD_Y_COMUNE","std"))
g["est_km"]  = (g.lon-lon0)*111*np.cos(np.radians(lat0))
g["nord_km"] = (g.lat-lat0)*111
g["raggio_km"] = np.sqrt((g.dlon*111*np.cos(np.radians(lat0)))**2 + (g.dlat*111)**2)
```

Poi il metodo (b), concentrazione dei toponimi, cercando in `ODONIMO` i
nomi che compaiono nelle denominazioni.

**Non saltare questa verifica**: l'incidente di Bologna (§3.2) è passato
inosservato per settimane e ha prodotto mappe con i nomi scambiati.

Infine si completa il registro e:

```bash
python -m gsp.common --check {CODICE}
```

Tutto verde tranne le directory di lavoro, che non esistono ancora.

### Fase 3 — dati ISTAT via SDMX

```bash
python scripts/acquisizione/fetch_comune.py {CODICE} --explore   # gratis: strutture in cache
python scripts/acquisizione/fetch_comune.py {CODICE}             # 11 tavole, ~3 min
```

L'`--explore` verifica che il comune sia nelle codelist territoriali; non
garantisce che le osservazioni esistano.

**Rate limit ISTAT: 5 query/minuto, violazioni = blocco IP di giorni.** Il
throttle è a 15 s ed è condiviso fra processi; il guard su 429/403/503
ferma tutto invece di martellare.

**Verifica obbligatoria** — il totale SDMX censuario deve coincidere con
`P1` del file sezioni:

```python
d = pd.read_csv(os.path.join(G.path_comune(comune),
                "cens_sesso_eta_cittadinanza_decoded.csv"), low_memory=False)
d["n"] = pd.to_numeric(d.OBS_VALUE, errors="coerce").fillna(0)
print(d[d.TIME_PERIOD.astype(str)=="2023"].n.sum() / 8)   # = P1
```

Il fattore 8 vale perché ogni persona è contata due volte per ciascuna
delle tre dimensioni che variano (sesso, cittadinanza, età), una nella
propria modalità e una nell'aggregato. Su tutti e quattro i comuni finora
il risultato è stato **esatto al singolo abitante**.

### Fase 4 — anello 1 (MaxEnt)

```bash
python scripts/vincoli/build_zona_tables.py {CODICE}
python scripts/vincoli/build_constraints.py {CODICE} --anno 2024
python scripts/vincoli/cs_build.py {CODICE} --anno 2024 --livello K9C
python scripts/fit/fit_cs.py {CODICE} --anno 2024 --livello K9C --eps 1e-8 \
  --min-alpha 2e-4 --sparse --no-gibbs
```

Da controllare, nell'ordine:

- `build_zona_tables`: `attesi {n}` e il `[sanity]` top-5 per quota
  stranieri — deve essere geograficamente plausibile;
- `build_constraints`: **passare sempre `--anno 2024`** (il default è
  2025, che salterebbe i blocchi C7/C8 con un `print` e non un errore); il
  preflight deve dare dieci `ok`;
- `cs_build`: `|X| = 161.280 × n_zone`;
- `fit_cs`: `MRE(α>0)` ≈ 4·10⁻⁴, e `massa su celle escluse: 0.00e+00`.

Le celle escluse post-hoc devono valere `|X|/2 + (esclusioni K7C) × 15`:
metà del supporto è impossibile perché metà delle combinazioni
`background × origine_genitori` è logicamente incoerente.

### Fase 5 — anelli 2 e 3

```bash
OPT=PUNTIFI1,PUNTIFI2,PUNTIFI3,PUNTIFI4,PUNTIFI5,PUNTIFI6,PUNTIFI7,PUNTIFI8,PUNTIFI10,PUNTIFI12,PUNTIFI13,VOTOUSL

python scripts/attributi/assign_nationality.py {CODICE} --anno 2024 \
  --pop-file popolazione_K9C.csv --out popolazione_K9C_naz.csv

python scripts/attributi/assign_avq.py {CODICE} --anno 2024 \
  --pop-file popolazione_K9C_naz.csv --out popolazione_K9C_avq.csv \
  --targets AMBIENTE,FIDUCIA,SALUTE,CRONI,FUMO,MH,BMI,BMIMIN,CPESO \
  --targets-opt $OPT

python scripts/attributi/enrich.py {CODICE} --anno 2024
```

Il `--pop-file` esplicito serve dove esistono più livelli K: l'auto-detect
prende il più ricco.

### Fase 6 — validazione finale

```bash
python -m gsp.common --check {CODICE}          # tutto verde
head -1 .../popolazione_K9C_avq_full.csv | tr ',' '\n' | wc -l   # 40
```

Nel log di `enrich`:

| riga | valore atteso |
|---|---|
| `[3c] paese: tier N` | 100% dalla geografia, 0% riserva comunale |
| `[3e] indirizzo` | ≥ 99,5% dalla sezione |
| `MAE pop.` | 0,7–1,6, correlazione ≥ 0,9998 |
| totali | coincidenti col censimento; stranieri entro ~1 σ |

### Cosa cercare negli open data comunali (tier 1–3)

Il condizionale geografico del paese richiede una tabella
`paese × unità territoriale`, eventualmente con sesso. **La cittadinanza
binaria non basta**: serve il paese di dettaglio.

| cercare | esito |
|---|---|
| «stranieri per cittadinanza e quartiere/zona» | tier 1 o 2 |
| microdati anagrafici con `Cittad` e sezione | tier 3 |
| solo `italiana/straniera` | tier 0 |
| nessun portale | tier 0 |

Il tier 0 è il caso normale e non richiede nulla. Le denominazioni dei
paesi vanno riconciliate con `G.SINONIMI_PAESE`, che è nazionale e già
copre i casi ricorrenti.

### Modi di fallire, osservati

| sintomo | causa |
|---|---|
| nomi di zona plausibili ma sbagliati | mappa `codice → nome` permutata: verificare su due assi (§3.2) |
| merge sui codici zona che «funziona» ma dà nomi assurdi | codici ASC1/ASC2 sovrapposti (§3.1) |
| blocchi C7/C8 «saltati» | `--anno` dimenticato: il default 2025 non ha `cens_migr_backg` |
| `build_zona_tables` esce con `attesi N, trovati M` | il file regionale è cambiato, o il livello nel registro è sbagliato |
| dissolve delle sezioni con troppi pochi poligoni | usato `COM_ASC1` dove il registro dice `COM_ASC2` |

---


---

## 13. Lo strato donatore AVQ — anatomia, numerosità efficace, limiti

*Ricostruita il 30/07/2026 leggendo `assign_avq.py`, i microdati grezzi e la
nota metodologica ISTAT «Aspetti della vita quotidiana — anno 2024, aspetti
metodologici dell'indagine» (2026). È la sezione da cui partire per la parte
su dati e limiti di un paper che usi lo strato AVQ.*

Ogni quantità è marcata con la provenienza: **misurato** da un conteggio sui
file, **dichiarato** dalla nota ISTAT, **aperto** dove non è determinata.

### 13.1 Composizione del pool: quali annate, e perché

Il pool impila **2023 e 2024**, non tutte e tre le annate disponibili. Il
meccanismo è in `load_avq`:

```python
missing = [c for c in base + targets if c not in d.columns]
if missing:
    print(f"[avq] {y}: variabili NECESSARIE mancanti {missing}, annata saltata")
    continue
```
> **La scelta è deliberata.** Il log di generazione riporta: *«il modulo salute
> AVQ ruota tra le annate: es. `CRONI` non è rilevata nel 2022, dove esistono
> solo le singole patologie `DIAB`/`IPAR`/… e `LIMITA`; ricostruirla darebbe
> una definizione non equivalente, quindi l'annata si scarta»*. Il compromesso
> è quindi a **tre** termini, non due: numerosità del pool, copertura delle
> variabili a rotazione, e **omogeneità della definizione di `CRONI`**.
> Ricostruire la cronicità dalle singole patologie darebbe un pool in cui la
> stessa variabile significa cose diverse a seconda dell'annata del donatore.

Un'annata viene **scartata per intero** se le manca una sola variabile fra i
`--targets`. I tracciati differiscono — 741 colonne nel 2022, 708 nel 2023,
736 nel 2024 — e **`CRONI` non esiste nel 2022**. Essendo fra i target
obbligatori, il 2022 è caduto.

Il secondo filtro è silenzioso: `ISTRMI_MAP` mappa quattro codici (1, 7, 9,
10) e **`ISTRMi = 99`, «titolo non indicato», non è mappato**. Quei record
prendono `istr4 = NaN` e spariscono in `dropna(subset=CELL_COLS)` senza
messaggio.

Il conto si chiude esattamente (**misurato**):

| | 2022 | 2023 | 2024 | 2023+2024 | −`ISTRMi` 99 | pool |
|---|---|---|---|---|---|---|
| Emilia-Romagna | 2.380 | 2.210 | 2.471 | 4.681 | −52 | **4.629** ✔ |
| Lombardia | 3.793 | 4.010 | 4.139 | 8.149 | −38 | **8.111** ✔ |

I file completi contengono 128.777 record nazionali (42.022 + 41.750 +
45.005): quello è l'inventario, non il pool.

#### Il costo di `CRONI`, e il compromesso che comporta

Spostare `CRONI` fra le opzionali farebbe rientrare il 2022:

```
pool Emilia-Romagna    4.629 → 7.061      ×1,53
n_eff (PUNTIFI10)      3.220 → ~4.900
banda di confidenza     ×7,0 → ×5,7
```

Ma **non è un miglioramento netto**. Le variabili presenti solo nel 2024
vedrebbero il proprio denominatore crescere, e la loro copertura scenderebbe
dal 42–43% al ~28%. Il compromesso è fra numerosità efficace di tutte le
variabili e copertura delle quattro a rotazione. **Da decidere
consapevolmente**, con il numero accanto: una variabile obbligatoria assente
in un'annata costa un terzo del pool a tutte le altre venti.

#### Perché le coperture sono quelle

La rotazione del modulo AVQ è **reale e dell'ISTAT**: `PUNTIFI6`, `PUNTIFI7`,
`VOTOUSL` e `FORZE_ARMATE` non esistono nei tracciati 2022 e 2023,
`PUNTIFI13` manca nel 2023. Ciò che dipende da noi è il **denominatore**: con
il pool a due annate il 2024 vale il 52,8%, e la copertura osservata si
prevede a due decimali (**misurato**):

```
PUNTIFI6    0,528 × 0,876 (universo 15+) × 0,92 (non risposta) = 0,425
                                                    osservato   0,427
PUNTIFI13   stessa previsione                       osservato   0,424
VOTOUSL     0,528 × 0,876 × 0,38 (filtro esperienza) = 0,176
                                                    osservato   0,202
```

#### Una voce della batteria manca

Nel tracciato la batteria occupa dodici posizioni consecutive (525–536) con
identica scala e formulazione. Undici si chiamano `PUNTIFI{n}`; la
dodicesima si chiama **`FORZE_ARMATE`**, posizione 534. Non essendo elencata
fra i target, **non è nella popolazione**: la batteria sintetica ha undici
voci su dodici.

> **Corollario di metodo.** Sia la lista dei target sia `ISTRMI_MAP` sono
> tabelle scritte a mano che **falliscono in silenzio**: producono assenze,
> non errori, e le assenze non si vedono finché non si cercano. In un
> pomeriggio ne sono emerse tre — `FORZE_ARMATE`, l'annata 2022, i 52
> donatori senza titolo di studio — e nessuna aveva mai prodotto un messaggio.
> Le altre corrispondenze compilate a mano o per prefisso meritano lo stesso
> controllo.

### 13.2 Il condizionamento, definizioni effettive

```
ETAMi → macroeta       1-4 → "0-13"        5-9  → "15-34"
                       10-11 → "35-54"     12-13 → "55-64"
                       14-15 → "65+"

bin censuario →        0-8, 9-14 → "0-13"       15-24, 25-34 → "15-34"
macroeta               35-49 → "35-54"           50-64 → "55-64"
                       65-74, 75+ → "65+"

ISTRMi → istr4         1 → terziario    7 → diploma
                       9 → media        10 → elementare_o_meno
                       minori → "eta_infantile" (chiave dedicata)

collasso               [sesso, macroeta, istr4] → [sesso, macroeta]
                       → [macroeta] → pool regionale
soglia                 min_record = 20 donatori per usare il pool di cella
```

**L'approssimazione dichiarata, quantificata.** Il codice annota *«50-64 →
55-64, approssimazione: 50-54 assimilato a 55-64»*: un cinquantenne sintetico
riceve le AVQ da un donatore di 55–64 anni. La classe quinquennale 50-54 vale
14.724 individui su Modena e 15.899 su Parma, cioè il **35% del bin `50-64` e
l'8% della popolazione** (**misurato**). Per salute percepita, fumo e
benessere psicologico cinque anni a quell'età non sono trascurabili.

**Quanto scatta il collasso gerarchico: misurato**, rigenerando con lo stesso
seed sulle popolazioni in uso.

| | cella piena | `sesso × macroeta` | `macroeta` | regionale |
|---|---|---|---|---|
| Brescia | **98,5%** | 1,5% | 0% | 0% |
| Bologna | 97,6% | 2,4% | 0% | 0% |
| Modena | 97,0% | 3,0% | 0% | 0% |
| Parma | 96,9% | 3,1% | 0% | 0% |

**Il terzo livello non scatta mai e il fallback regionale nemmeno.** Il
condizionamento pieno copre il 97–98,5% degli individui; il resto perde
soltanto l'istruzione.

> La stima indiretta dalle firme — 15,3% confinate alla cella piena su Modena
> — era un limite inferiore molto pessimistico, contaminato dalle collisioni
> fra donatori. Va scartata.
>
> Va scartato anche il **3,7% servito dal pool regionale** che compare nei log
> del 27 luglio: quella generazione precede il collasso gerarchico
> (commit `f383e54`, 28 luglio), mentre le popolazioni in uso sono del 29.

**Il collasso non è casuale: colpisce sempre la bassa istruzione.** Le celle
sotto la soglia di 20 donatori sono **tutte** `elementare_o_meno`, e
`M 15-34 elementare_o_meno` ne ha **quattro** nel pool emiliano.

Quel 3% riceve quindi le AVQ condizionate solo su sesso ed età, e viene tirato
verso la media della popolazione: **più fiducia istituzionale e migliore
salute percepita di quanto il condizionamento pieno darebbe**. La direzione
della distorsione è nota, il che è meglio che ignorarla — ma va dichiarata,
perché ricade su un gruppo già poco rappresentato.

### 13.3 Numerosità efficace

#### La formula

Tutti gli individui sintetici che condividono un donatore hanno **lo stesso
valore** su tutte le variabili AVQ. Per la media su `n` individui provenienti
da `D` donatori con molteplicità `m_d`:

```
x̄ = (1/n) Σ_d m_d x_d          Var(x̄) = σ² Σ_d m_d² / n² = σ² / n_eff
n_eff = n² / Σ_d m_d²
```

che è la formula di Kish. **Il conteggio dei donatori distinti non basta**:
sopravvaluta `n_eff` di un fattore 2,8 quando il riuso è diseguale, perché
Kish è una statistica di secondo momento e vive nella coda della
distribuzione dei riusi.

*Interpretazione*: condizionatamente al pool, i valori AVQ sintetici sono una
funzione deterministica dell'assegnazione. L'incertezza rilevante per
un'inferenza sulla popolazione reale è quella di campionamento **del pool**,
e `n_eff` misura quanti rispondenti indipendenti stanno sotto la statistica.

#### L'universo, non la copertura

`n_eff` va calcolato **per variabile, sul suo universo**. Calcolarlo
sull'intera popolazione lo dimezza, perché le firme dei minori collassano su
quattro valori e producono classi enormi che dominano `Σm²` pur non
partecipando alla variabile (**misurato**, Modena):

```
popolazione intera      n = 184.597   n_eff = 1.520   efficienza 0,36
PUNTIFI10, 15 e più     n = 157.974   n_eff = 3.220   efficienza 0,80
```

Gli universi si riconoscono dalla forma, non dalla percentuale. E sono **tre
cose distinte**, che il solo numero confonde (**misurato**, Modena):

```
MH          161.766 assegnati = 184.597 − 12.812 − 10.019   universo 15+ PURO
PUNTIFI10   157.974 assegnati                                universo 15+
                                                             − 3.792 = 2,3%
                                                             di non risposta d'item
SALUTE      184.597 assegnati                                nessun universo
```

`MH` non ha **alcuna** non risposta: coincide all'unità con la popolazione di
15 anni e più. `PUNTIFI10` ha lo stesso universo più il 2,3% di chi, potendo,
non ha risposto alla batteria — la nota metodologica ISTAT prevede
esplicitamente la facoltà di non rispondere sui quesiti sensibili.

Scrivere «copertura 87,6%» descrive un sintomo e confonde i tre casi;
«universo 15 anni e più, non risposta d'item 2,3%» descrive il dato.

Tre meccanismi distinti, da non confondere:

| | riconoscimento | esempi |
|---|---|---|
| **universo** | 0,00 sotto una soglia d'età, ~0,98 sopra | tutte le `PUNTIFI`, `MH`, `AMBIENTE` |
| **rotazione del modulo** | costante in ogni classe d'età | `PUNTIFI6`, `PUNTIFI7`, `PUNTIFI13`, `VOTOUSL` |
| **filtro per esperienza** | cresce con l'età | `VOTOUSL`: 0,12 a 15-24, 0,30 a 65-74 |

Il terzo **non è ignorabile**: chi giudica l'ASL è chi ci è stato, quindi più
anziano e più malato. La media non è «il giudizio dei modenesi sull'ASL» ma
«il giudizio di chi c'è stato».

#### `n_eff` di Kish è un limite superiore

L'AVQ **campiona famiglie e intervista tutti i componenti** (§3.1 della nota
metodologica): 45.005 individui in 19.775 famiglie, **2,28 per famiglia**
(**dichiarato**). I donatori non sono osservazioni indipendenti, e Kish li
tratta come tali. La correzione è il fattore di grappolo `1 + (k−1)·ρ`.

Le ICC calcolate impilando le annate sono **contaminate**, perché `PROFAM`
riparte da 1 ogni anno e famiglie di anni diversi finiscono nello stesso
grappolo — si riconosce da `k = 5,67` invece di ~2. Le sole stime pulite sono
quelle delle variabili presenti in **una sola annata**, per cui `PROFAM` è di
fatto univoco (**misurato**):

| | ρ | k | fattore |
|---|---|---|---|
| `PUNTIFI6` | 0,652 | 2,01 | 1,66 |
| `PUNTIFI7` | 0,613 | 2,01 | 1,62 |
| `FORZE_ARMATE` | 0,589 | 2,03 | 1,61 |
| `VOTOUSL` | 0,556 | 1,43 | 1,24 |

**ρ ≈ 0,6 per la fiducia istituzionale**, molto più dello 0,2–0,3 che si
assumerebbe per default: le opinioni politiche si condividono in casa.

```
Modena, PUNTIFI10       n = 157.974
  n_eff di Kish             3.220     banda × 7,0
  / fattore 1,66            1.941     banda × 9,0
```

> **aperto**: da rifare con chiave `ANNO|PROFAM` su tutte le variabili.

#### Gli effetti di disegno si compongono

`n_eff / 1,66` corregge solo il grappolo familiare. Restano:

- **stratificazione e calibrazione.** Il campione è calibrato su 24 totali
  noti per regione — sesso × otto classi d'età, sei tipologie comunali,
  stranieri per sesso (**dichiarato**) — che **coincidono con le nostre
  variabili di condizionamento**. Per stime *demografiche* la calibrazione
  riduce la varianza sotto quella di un campione casuale semplice: dal
  modello del prospetto 2 si ricava un deff di **0,72–0,75** per
  l'Emilia-Romagna. Ma quel modello è interpolato sulle stime pubblicate, in
  maggioranza demografiche: per una variabile attitudinale, che età e sesso
  non predicono, la calibrazione non aiuta e il deff è presumibilmente ≥ 1.
  **aperto**;
- **sovrastima dichiarata.** Negli strati NAR si estrae un solo comune e la
  varianza si stima per collassamento degli strati, che sovrastima; anche
  trattare l'estrazione come con reimmissione sovrastima (**dichiarato**,
  §6.2 della nota). Gli errori pubblicati sono quindi conservativi;
- **le firme sottostimano i donatori usati**, e non di una quantità costante.
  Con la firma a 23 variabili e undici comuni lo scarto rispetto alla
  dimensione del pool va da −460 (Bologna) a −885 (Brescia), con Castenaso a
  −739. *Una versione precedente riportava «−418 identico, proprietà del
  pool»: era una **coincidenza di configurazione**, misurata su tre città
  grandi della stessa regione che saturavano il pool allo stesso modo.* Lo
  scarto somma due componenti — **collisioni** fra donatori con firma
  identica, che nessuna variabile in più separerà mai perché hanno quasi tutto
  mancante, e **saturazione incompleta**, donatori mai estratti perché il
  comune non ha abbastanza individui nella cella giusta. Separarle richiede il
  numero di donatori *usati*, che `assign_avq.py` stampa nel log.
  **Scomposte il 2/8/2026** su tre comuni:

  | | pool | estratti | firme | saturaz. incompleta | collisioni |
  |---|---|---|---|---|---|
  | Brescia | 8.111 | 8.111 (**100%**) | 7.226 | **0** | 885 |
  | Modena | 4.629 | 4.617 (99,7%) | 4.161 | 12 | 456 |
  | Castenaso | 4.629 | 4.336 (93,7%) | 3.890 | **293** | 446 |

  La saturazione incompleta è **nulla** a Brescia, trascurabile a Modena e
  non trascurabile solo a Castenaso, dove il riuso medio è 3,8× contro i
  24–40× degli altri. Tutto il resto è collisione, e la sua quota è stabile
  intorno al 10% (9,9% / 10,9% / 10,3%) nonostante pool e riusi molto
  diversi. **chiuso**. L'errore va nella direzione prudente.

Il modello per calcolare gli errori campionari AVQ è disponibile e
verificato: `log(ε²) = a + b·log(Ŷ)`, con per l'Emilia-Romagna, persone,
`a = 8,799059` e `b = −1,134869`. Riproduce il prospetto 4 a tre decimali.

#### La formulazione generale

> **Qualunque popolazione sintetica che imputi attributi da un'indagine
> donatrice eredita la numerosità di quella indagine come tetto,
> indipendentemente da quanti individui contiene** — e la eredita ridotta dal
> riuso diseguale (Kish) e dal disegno dell'indagine (grappoli,
> stratificazione, calibrazione).

**misurato su undici comuni** (firma a 23 variabili, popolazioni del
2/8/2026). Le due misure di `n_eff` si comportano in modo opposto.

| | individui | `n_eff` intera pop. | `n_eff` su `PUNTIFI10` | banda × |
|---|---|---|---|---|
| Bologna | 390.098 | 966 | 2.845 | 10,9 |
| Brescia | 198.259 | 1.093 | **5.655** | 5,5 |
| Parma | 198.121 | 832 | 3.181 | 7,3 |
| Modena | 184.597 | 862 | 3.220 | 7,0 |
| Reggio nell'Emilia | 171.207 | 795 | 3.347 | 6,6 |
| Ravenna | 156.304 | 995 | 3.334 | 6,4 |
| Rimini | 150.046 | 924 | 3.318 | 6,2 |
| Ferrara | 129.391 | 1.153 | 3.082 | 6,1 |
| Forlì | 117.050 | 916 | 3.325 | 5,5 |
| Piacenza | 102.887 | 810 | 3.237 | 5,2 |
| **Castenaso** | **16.357** | 741 | 2.770 | **2,2** |

**La colonna sull'intera popolazione è inutilizzabile.** Sta fra 741 e 1.153
— variazione del 56% — e **non segue nulla**: né la popolazione (Castenaso ha
1/24 degli abitanti di Bologna e `n_eff` più basso solo del 23%), né il riuso,
né il livello (Ferrara ha il massimo e Castenaso il minimo, ed è lo stesso
livello). Non misura il riuso: misura **il collasso delle firme dei minori**,
presente ovunque nella stessa proporzione e dominante in `Σm²`.

**Dove stanno esattamente le collisioni** (pool emiliano-romagnolo, 4.629
donatori, 456 collisioni, firma a 23 variabili, **misurato** il 2/8/2026):

| variabili mancanti su 23 | donatori | firme | collisioni | quota |
|---|---|---|---|---|
| 0–4 | 2.095 | 2.095 | **0** | 0,000 |
| 5 (annata 2023) | 1.697 | 1.693 | 4 | 0,002 |
| 6–18 | 314 | 313 | 1 | 0,003 |
| **19** | 118 | 25 | **93** | **0,788** |
| **20** | 337 | 31 | **306** | **0,908** |
| **21** | 64 | 12 | **52** | **0,812** |
| 22 | 3 | 3 | 0 | 0,000 |

**452 su 456 — il 99% — stanno nelle tre righe 19–21**, cioè i minori: ai
bambini non vengono poste le domande su fiducia, salute percepita, fumo,
benessere psicologico e antropometria, e restano due, tre o quattro valori
su cui distinguersi. Dove le variabili ci sono, le collisioni sono cinque su
4.107 donatori. E **non è l'annata**: il 2023 collide 198 volte su 2.181
donatori, il 2024 229 su 2.448 — stessa misura, nonostante il 2023 manchi
delle cinque opzionali.

Questo conferma per misura ciò che la colonna «intera popolazione» qui sotto
mostra per inferenza, e spiega perché passare da 21 a 23 variabili non abbia
ridotto le collisioni: per quei donatori le variabili in più sono proprio
quelle che mancano.

Se ne era già vista l'instabilità rispetto al set AVQ: togliendo `BMIMIN` —
l'unica variabile che distingue un bambino da un altro — Modena passa da 1.520
a 862, **−43%**, senza che nulla cambi nella popolazione. Una quantità che si
muove del 43% per una variabile al 13% di copertura, e non risponde a una
variazione di 24 volte nella popolazione, non misura niente.

**La colonna sull'universo giusto invece si legge.** Nove comuni su undici
stanno fra 3.082 e 3.347, entro l'8%: è **il pool regionale, e si vede**.
Brescia sta a 5.655 perché attinge a quello lombardo, quasi doppio. Il
rapporto `n_eff / donatori usati` vale 0,74–0,84 dappertutto.

Ed è **stabile rispetto al set AVQ**: sull'universo 15+, passando da 21 a 23
variabili, Modena resta a 3.220 alla cifra, donatori compresi. Stessa
popolazione, set diverso: la misura sull'intera popolazione si muove del 43%,
quella per universo di zero. È un esperimento controllato, e vale più
dell'argomento teorico che lo aveva preceduto.

#### Castenaso: una popolazione piccola è più affidabile di una grande

`n/n_eff` vale 5,0 a Castenaso e 119 a Bologna: **banda ×2,2 contro ×10,9**,
un fattore cinque sulla stessa identica statistica.

Castenaso **non satura il pool**: 13.910 individui su 3.746 donatori fanno
riuso 3,7, quindi ogni donatore porta ancora informazione quasi indipendente.
Bologna ne ha 338.890 sugli stessi 4.000 donatori, e ognuno vale 85 individui
che dicono tutti la stessa cosa.

> **Sulle variabili donate, una popolazione sintetica piccola è più
> affidabile di una grande.** L'informazione è quella del pool: diluirla su
> più individui non la aumenta, e il rapporto `n/n_eff` la fa apparire più
> precisa proprio dove lo è di meno.

### 13.4 Cosa il pool eredita dall'indagine

**dichiarato**, nota metodologica ISTAT 2024:

- **disegno a due stadi**, comuni poi famiglie; nei comuni NAR un solo comune
  campione per strato, con probabilità proporzionale alla dimensione;
- **grappoli familiari**: selezionate le famiglie, si intervistano tutti i
  componenti di fatto;
- **esclusi gli istituti di convivenza**. La popolazione sintetica include
  invece le convivenze (50–630 per comune), che ricevono quindi donatori da
  un universo che non le contiene. **aperto**: entità dell'effetto;
- **proxy sotto i 14 anni**: le informazioni dei minori sono fornite da un
  adulto. Gli universi osservati sono filtri di questionario, non restrizioni
  campionarie;
- **facoltà di non rispondere** su quesiti sensibili, che spiega parte del
  ~2% di non risposta dentro l'universo.

Il file *public use* dà 2.471 record emiliani per il 2024 contro i 2.486 del
prospetto 1. Quindici in meno, lo 0,6%: citando il prospetto e lavorando sul
file, i due numeri non coincidono.

### 13.5 Una verifica che passa

La copertura delle AVQ nella popolazione sintetica **è** quella del pool, non
un artefatto dell'assegnazione (**misurato**):

| | pool ER | popolazione Modena |
|---|---|---|
| `SALUTE` | 1,000 | 1,000 |
| `MH` | 0,892 | 0,876 |
| `AMBIENTE` | 0,883 | 0,864 |
| `PUNTIFI1` | 0,874 | 0,857 |

Scarto costante del 2% su tutte, e `SALUTE` esatta: **l'hot-deck trasmette il
pattern di mancanza del donatore intatto**, come l'assunzione (6) richiede.
È una verifica diretta dell'anello 2 che non era mai stata fatta.

#### Le correlazioni sono preservate — su 253 coppie, non su un esempio

La verifica che giustifica l'hot-deck è che le correlazioni fra target nella
popolazione sintetica coincidano con quelle nei donatori. Con 23 variabili
sono **253 coppie**, e finora si confrontavano due matrici a occhio. Ora è
una misura (**misurato** il 2/8/2026):

| | mediano | massimo | peggiore coppia | n | atteso ~1/√n |
|---|---|---|---|---|---|
| Brescia | 0,005 | 0,031 | `VOTOUSL × BMI` | 1.258 | 0,028 |
| Modena | 0,007 | 0,046 | `FIDMED × FORZE_ARMATE` | 1.130 | 0,030 |
| Castenaso | 0,009 | 0,061 | `CRONI × FORZE_ARMATE` | 1.001 | 0,032 |

Ogni scarto va letto contro la sua precisione attesa: l'errore standard di
una correlazione su `n` osservazioni indipendenti è `~1/√n`, e le
osservazioni indipendenti sono i **donatori estratti** con entrambe le
variabili, non gli individui sintetici. Il rapporto osservato/atteso resta
fra 1 e 2 ovunque — e su 253 coppie il massimo di una normale standard sta
tipicamente sui 2,8σ, quindi siamo sotto. Non è un difetto della procedura:
è la coda della distribuzione degli scarti.

**Il mediano scala con il riuso, non con la popolazione.** Brescia satura il
pool al 100% e ha il mediano più basso; Castenaso lo usa al 93,7% con riuso
3,8× e ha il più alto. Non è la dimensione del comune a determinare la
fedeltà delle correlazioni, è quanto il pool viene esplorato — l'ennesima
conferma che sulle variabili donate le due cose non coincidono.

Le coppie con `FORZE_ARMATE` dominano la classifica perché la variabile è
disponibile in una sola annata (23% degli assegnati), quindi `n ≈ 1.100`
invece di 4.617. L'unica anomalia da tenere d'occhio è
`PUNTIFI5 × PUNTIFI8` a Brescia: 0,029 osservato contro 0,012 atteso con
`n = 7.012`, cioè 2,4 errori standard, il solo caso in cui il rapporto
sfora.

> La frase difendibile: *su 253 coppie, lo scarto fra le correlazioni della
> popolazione sintetica e quelle dei donatori AVQ ha mediana 0,007 e massimo
> 0,046, con le tre peggiori entro 1,5 errori standard della loro numerosità
> effettiva.* Sostituisce l'esempio singolo `SALUTE ↔ CRONI`.

#### La soglia di mascheramento contava la quantità sbagliata

La validazione 2 maschera le correlazioni sotto i 100 donatori, ma li
contava sui **disponibili nel pool** (`src.notna()`), mentre l'informazione
indipendente viene dai donatori **effettivamente estratti**. Una coppia con
400 disponibili e 60 estratti poggiava su 60 osservazioni e passava.

Corretto il 2/8/2026: `n_coppia = ok_u.T @ ok_u` sui soli estratti, con il
conteggio di quante coppie la vecchia soglia lasciasse passare. **Su tutti e
tre i comuni provati quel conteggio è zero**: il difetto era teorico, perché
il pool si satura quasi ovunque. Ma la quantità è ora quella giusta, e su un
comune più piccolo o con più variabili opzionali morderebbe.

C'era anche una collisione di nome che incarnava la confusione: `n_don` era
prima lo scalare dei donatori estratti, poi veniva **sovrascritto** dalla
matrice dei disponibili. Ora si chiamano `n_estratti` e `n_coppia`.

#### I marginali «sintetico vs AVQ pesato» non sono una validazione

Il log di generazione stampa un confronto fra la marginale del **comune** e
quella pesata della **regione**. Non è una validazione: i due termini si
riferiscono a popolazioni diverse, e lo scarto misura **quanto il comune
differisce dalla sua regione attraverso le variabili di condizionamento** —
cioè è compositivo per costruzione.

Lo si vede sulla variabile con lo scarto maggiore, `FIDUCIA` (**misurato**):

| | scarto | istruzione terziaria |
|---|---|---|
| Brescia | +0,017 | la più bassa delle quattro |
| Modena | +0,025 | |
| Parma | +0,028 | |
| Bologna | **+0,042** | la più alta |

L'ordinamento segue il gradiente d'istruzione, che è una delle tre variabili
di cella. Non è errore: è la differenza compositiva comune–regione, la stessa
quantità che il viewer chiama *riga di scomposizione*.

> Il blocco `[val] marginali` del log andrebbe rinominato **«differenza
> compositiva comune–regione»**. Chiamarlo validazione invita a leggere come
> errore ciò che è segnale.

### 13.6 Da rivedere prima di un paper

1. **`CRONI` fra le opzionali?** +53% di pool e +50% di `n_eff` su tutte le
   variabili, al prezzo della copertura delle quattro a rotazione **e**
   dell'omogeneità di definizione di `CRONI` stessa, che è la ragione per cui
   il 2022 fu scartato (§13.1).
2. **`FORZE_ARMATE` nei target**: la batteria è incompleta di una voce su
   dodici. **Quantificato** il 2/8/2026: disponibile in una sola annata,
   copre il 23% degli assegnati (42.636 su 184.597 a Modena), e le sue
   coppie hanno `n ≈ 1.100` contro i 4.617 delle altre — da cui i tre
   scarti peggiori della matrice delle correlazioni, tutti entro 1,5σ
   (§13.5). Non è un difetto: è la precisione che quella numerosità
   consente.
3. **`ISTRMi = 99`**: 52 e 38 donatori scartati in silenzio. Da dichiarare o
   mappare su una classe «non indicato» con cella propria.
4. **ICC corretta** con chiave `ANNO|PROFAM`, su tutte le variabili.
5. **deff per variabili attitudinali**: il modello ISTAT è tarato sulle stime
   demografiche e non si applica.
6. **Convivenze**: ricevono donatori da un universo che le esclude. Aggancio
   empirico trovato il 2/8/2026 nei microdati di Parma: `Ncomp` arriva a
   **319** e sono le convivenze anagrafiche (`Tipores = 2`), non famiglie.
   La variabile mescola due universi e non è utilizzabile per la dimensione
   familiare senza condizionare su `Tipores` (§9).
7. ~~Fonte delle medie nazionali della batteria~~ — **risolto** il 2/8/2026:
   la fonte non esisteva, l'ISTAT non pubblica medie. Ricalcolate dai
   microdati con `medie_nazionali.py`, coincidono entro 0,045 con le cinque
   cablate e ora coprono tutte e ventitre le variabili (§2.2).


---

## 14. L'anello 1 verificato — constraint set e stato del pool

*Misurato il 30/07/2026 con `ispeziona_cs.py` e `verifica_vincoli.py`
(repo `animarium`, cartella `build/`). Ogni quantità è marcata **misurato**
o **aperto**.*

**La sintesi, prima dei dettagli: l'anello 1 è sano.** I totali comunali
coincidono esattamente col censimento, nessuno zero dichiarato impossibile è
popolato, e gli errori per cella sono **interamente al pavimento di rumore**
di un campione finito. Le tre anomalie descritte sotto sono una da 10⁻⁵, una
metodologica e una aperta.

### 14.1 Anatomia del constraint set

**misurato**: sedici blocchi, **identici nelle quattro città** — è una
proprietà del template di `build_constraints.py`, non del comune. Undici
completi (somma α = 1), cinque parziali.

I cinque parziali sono i **complementi fuori universo**:

```
eta × istruzione                  1 cella:  (0-8, nessun_titolo)
eta × condizione                  2 celle:  (0-8, non_applicabile)
                                            (9-14, non_applicabile)
zona × sesso × eta × condizione   i soli occupati fra 15 e 64 anni
```

Le prime due sommano a 1 **a coppie** col blocco completo corrispondente:
`eta × istruzione` 0,0685 più `sesso × eta × istruzione` 0,9315 fa
esattamente 1, e lo stesso per la condizione. Non sono blocchi incompleti:
sono una stessa tavola spezzata in due secondo l'universo, dove il sesso è
disponibile e dove non lo è.

> **Un blocco parziale non è una distribuzione**: le celle non elencate non
> sono vietate, sono **libere**. Non si può normalizzare né usare come
> riferimento.

### 14.2 «Assente» e «zero» sono opposti — materiale da paper GibbsPCD

> Quando l'ISTAT **esclude per universo**, la cella non compare nella tavola.
> Quando il censimento **osserva zero**, la cella compare con valore zero.
> Per MaxEnt le due cose sono **opposte**: una cella assente è *non
> vincolata*, una cella a zero è *vietata*.

La prova che il meccanismo funziona dove il dato c'è: `cittadinanza ×
background` ha **6 zeri espliciti** e `sesso × eta × stato_civile` ne ha 2 —
otto in tutto, identici nelle quattro città — e **nessuno è violato**
(**misurato**).

Ma le **26 coppie logicamente impossibili di età × condizione e
età × istruzione non sono vincolate da nessun blocco**, perché l'ISTAT non
pubblica quegli incroci:

```
bin < 15   × {occupato, in_cerca, studente, casalinga,
              percettore_pensioni, altra_condizione}      2 × 6 = 12
bin ≥ 15   × non_applicabile                              6 × 1 =  6
0-8        × {elementare, media, diploma, laurea, post}   1 × 5 =  5
9-14       × {diploma, laurea_o_its, post_laurea}         1 × 3 =  3
                                                              ----
                                                                26
```

Tre record ci sono finiti dentro (**misurato**): `diploma` a 2 anni e
`post_laurea` a 13 su Parma, `altra_condizione` a 0 anni su Modena. **Tre su
970.000**, cioè 3·10⁻⁶: massa residua del fit, non errore sistematico. Il
verso è coerente con la dimensione del supporto — Modena `|X|`=645.120 ne ha
uno, Parma 2.096.640 ne ha due.

**Riparazione**: aggiungere le 26 coppie all'insieme delle esclusioni α=0,
con lo stesso meccanismo post-hoc sul supporto già in uso per
`background × origine_genitori`. Effetto collaterale: cambia il conteggio
delle celle escluse, quindi la formula di controllo di §12 va aggiornata.

> **Corollario di metodo**: la traduzione da tavole censuarie a vincoli
> MaxEnt deve distinguere esplicitamente fra cella assente e cella a zero,
> perché la fonte le rappresenta con la stessa mancanza di valore ma
> intendono il contrario.

### 14.3 Lo stato del pool: un campione pulito

La popolazione è un **campione** dalla distribuzione fittata, non la sua
media. Per una cella con probabilità target α su N individui la deviazione
standard multinomiale è `√(Nα(1−α))`, quindi la metrica giusta è lo z-score
`(osservato − atteso) / √(Nα(1−α))`, **non l'errore relativo**.

> L'errore relativo su conteggi piccoli è una statistica senza contenuto: la
> classifica delle celle «peggiori» che produce è semplicemente la classifica
> delle celle più piccole. La conferma sta nei dati: **Parma ha MRE per cella
> più alto di Modena** (5,4% contro 4,5%) pur avendo più abitanti — perché ha
> 13 zone invece di 4, quindi celle più piccole. Se fosse errore di fit
> andrebbe nella direzione opposta.

**misurato**:

| | Modena | Parma | atteso |
|---|---|---|---|
| `sd(z)` | **1,018** | 1,031 | 1,000 |
| media(z) | −0,021 | +0,005 | 0 |
| \|z\| medio | 0,829 | 0,810 | 0,798 |
| \|z\| > 2 | 4,45% | 5,49% | 4,55% |
| zeri hard violati | 0 | 0 | 0 |

Il fit è **non distorto** e la dispersione è al 3% sopra il teorico, identica
nelle due città.

**`sd(z)² = 1,04` è il fattore di inflazione della varianza**: il pool di
184.597 individui vale ~177.000 estrazioni indipendenti. Era 1,06 sulle
popolazioni del 29/7; la rigenerazione del 2/8 lo ha marginalmente
migliorato. È la prima
quantificazione del mixing della catena Gibbs, e si legge senza glossario —
*quanto costa in informazione il fatto che PCD non produce estrazioni
indipendenti*.

### 14.4 Un blocco anomalo, replicato — **aperto**

`sesso × background × origine_genitori` è l'unico blocco con `|z|` medio
sopra 1 in entrambe le città — **1,16 su Modena e 1,05 su Parma**, contro
0,80 dei blocchi puramente demografici — e le celle coinvolte hanno una
struttura, non sono sparse (**misurato**):

```
Modena   straniero_g2 × madre_italiana        −3,60 e −3,46
         straniero_g2 × madre_straniera       −3,16
         naturalizzato_g2 × entrambi_italiani +2,89
Parma    straniero_g2 × entrambi_italiani     +4,00
         straniero_g2 × madre_italiana        −3,90
```

**Le celle a genitori misti perdono massa, quelle a genitori omogenei la
guadagnano.** Il danno assoluto è di qualche decina di individui su 184.597 —
irrilevante per qualunque stima — ma è **sistematico e replicato su due
città**, quindi è un fatto sul metodo, non sulla città.

*Ipotesi da verificare*: è l'unico blocco che tocca la coppia su cui sono
dichiarate le esclusioni α=0 post-hoc. L'esclusione sottrae massa dal
supporto e la redistribuzione favorisce le celle grandi a spese delle
piccole, che sono esattamente quelle a genitori misti.

### 14.5 Il MRE del riferimento e quello dello strumento

`verifica_vincoli.py` confronta il MRE osservato con il pavimento di rumore
`mean(√((1−α)/(αN)))`. Ma quella formula è la **deviazione standard**
dell'errore relativo, mentre il MRE è il suo **valore assoluto medio**, che
vale `√(2/π) = 0,798` volte tanto. Corretto il fattore, l'errore osservato
sta il 10–11% sopra il pavimento — coerente con `sd(z) = 1,03`, e con la
sovradispersione concentrata nelle celle piccole.

> **aperto**: verificare quale delle due definizioni usa `fit_cs.py`.
> Strumento e paper devono dire la stessa cosa.

---

## 15. L'anello 3 verificato — allocazione

*Misurato con `diag_quinq.py` e `diag_istruzione_eta.py` su Modena e Parma;
mancano Bologna e Brescia.*

### 15.1 Il seam a nove anni: non è la sorgente d'errore dominante

Sei degli otto bin del constraint set coincidono con gruppi di quinquennali;
i due infantili no, e stanno insieme sotto ipotesi di uniformità:

```
0-8   = <5            + 4/5 di 5-9
9-14  = 1/5 di 5-9    + 10-14
```

Il taglio a nove anni viene dall'universo dell'istruzione (`P83`, «9 anni e
più»), non dalla griglia quinquennale.

**misurato**: riaggregando il sintetico alle sedici classi ISTAT e
confrontandolo con `P{30+k}`/`P{67+k}` per sezione e sesso, il MAE grezzo del
seam è indistinguibile dalle altre classi. Normalizzando per la dimensione di
classe — §11.1 — le due classi del seam finiscono **nei primi tre posti su
sedici in entrambe le città** (per caso vale ~6·10⁻⁴), ma l'eccesso è del
40%, non di un ordine di grandezza.

**Conclusione**: l'ipotesi di uniformità entro il quinquennio 5–9 è elevata
ma **non dominante**. Risultato negativo pulito.

### 15.2 Lo scarto entro bin: dieci prove su dieci

**misurato**, e non era previsto. Dentro ciascuno dei cinque bin veri il
sintetico pende verso il **giovane**: prima classe in positivo, ultima in
negativo, in entrambe le città.

```
            Modena              Parma
15-24   +0,158 / −0,158    +0,186 / −0,186
25-34   +0,110 / −0,110    +0,278 / −0,278
35-49   +0,351 / −0,438    +0,234 / −0,260
50-64   +0,101 / −0,097    +0,201 / −0,131
65-74   +0,199 / −0,199    +0,209 / −0,209
```

Punti percentuali di quota entro bin. Dieci segni concordi hanno p ≈ 0,002.

**Perché conta**: la distribuzione *dentro* il bin non è vincolata da niente.
Il constraint set fissa il totale del bin, il quinquennio viene dalle colonne
`P` di sezione e l'anno esatto dall'anagrafe comunale. L'indiziato è quindi
**l'assunzione (9)**: la forma dell'anagrafe entro il bin non coincide con
quella censuaria di sezione.

Nella regione infantile il verso **si inverte**: `10-14` sovrarappresentata
di +0,37 e +0,35. È l'unico posto dove opera la frazione 4/5–1/5, e ha una
direzione precisa — **il sintetico mette troppo pochi novenni**: la quota
vera dei novenni dentro il quinquennio 5–9 non è un quinto.

> **Ritirato.** Una versione precedente di questa analisi riportava una
> discrepanza «fino a 1,42% fra due prodotti censuari». Era **rumore di
> campionamento**: il target del constraint set e le colonne `P` coincidono,
> e lo scarto della popolazione dal proprio target vale z = 0,24 su Modena e
> 0,64 su Parma.

### 15.3 Incoerenza fra età esatta e istruzione

L'istruzione è assegnata al livello del bin con soglie minime di
conseguimento; `eta_anni` è assegnata dopo, nell'anello 3, e **nulla lega le
due**. Dentro il bin `9-14` può quindi uscire un individuo con
`istruzione = media` ed `eta_anni = 10`.

Non è un bug: è una conseguenza dell'ordine delle assegnazioni. Ma è
misurabile (**misurato**):

| | violazioni | quota |
|---|---|---|
| Modena | 4.867 | 2,64% |
| Parma | 5.434 | 2,74% |

Concentrate nei bin `9-14` (18,8% e 22,2%) e `15-24` (16,5% e 16,1%), zero
altrove. Il vincolo sull'istruzione usa la classe grossa `Y9-24`, l'IPF con
soglie distribuisce i titoli su tutto l'arco, e `eta_anni` arriva dopo in
modo indipendente.

**Riparazione**: permutare `istruzione` fra individui entro
`(zona, sesso, bin)`. È esattamente ciò che è vincolato, e l'assunzione (8)
dichiara `sezione ⊥ istruzione`, quindi non si perde nulla di garantito.
**Post-hoc: non richiede di rigenerare.**

*Nota sulla lettura per quartiere*: la quota grezza varia fra zone (Parma
2,04%–3,19% su 13 quartieri) ma **deve** variare, perché è la quota di
9-24enni moltiplicata per il tasso interno. Il test corretto è il tasso
condizionato sugli individui a rischio, dato bin e titolo.

### 15.4 Cosa resta

1. **Diagnostici su Bologna e Brescia**: chiudono lo scarto entro bin a
   quattro città. Se replica, va da «osservato su due comuni» a proprietà
   della pipeline.
2. **Assunzione (9)**: confrontare la distribuzione per anno singolo
   dell'anagrafe comunale con il profilo quinquennale censuario, direttamente,
   senza passare dalla popolazione. **aperto**.
3. **Le due riparazioni**, entrambe post-hoc: permutazione di `istruzione`, e
   le 26 esclusioni α=0 di §14.2.

## Changelog


**v2.2 — 05/08/2026, ritocchi**
Il file di popolazione **non è cambiato**: le derivazioni non aggiungono
colonne. Aggiunta §2.4 sugli attributi che esistono ma non stanno nel
CSV, e aggiornati i rimandi alle note (`fonti_e_pacchetto_v8`, il registro
a 37 fonti).


**v2.2 — 02/08/2026**
Lo scarto firme-pool **scomposto** nelle sue due componenti, che §13.3
nominava senza separare: la saturazione incompleta è nulla a Brescia
(8.111/8.111), 12 a Modena, 293 a Castenaso; tutto il resto è collisione,
stabile al ~10%. E le collisioni sono **localizzate**: 452 su 456 nei
donatori con 19–21 variabili mancanti su 23, cinque su 4.107 donatori dove
le variabili ci sono. Conferma per misura ciò che §13.3 mostrava per
inferenza, e spiega perché passare da 21 a 23 variabili non le abbia
ridotte. §13.3 e §13.6 punto 2 chiusi.
Aggiunta a §13.5 la verifica delle correlazioni su **253 coppie** invece
che su un esempio, con ogni scarto normalizzato contro `1/√n`: mediana
0,007, massimo 0,046, tutte entro 1,5σ. Il mediano scala con il **riuso**,
non con la popolazione. Corretta la soglia di mascheramento, che contava i
donatori *disponibili* invece degli *estratti* — difetto senza conseguenze
sui comuni attuali (`piu_lasco = 0`), ma la quantità ora è quella giusta.
`gsp_common.py` è diventato `gsp.common` dentro il pacchetto installabile
(§4), e le fonti esterne hanno un registro proprio (§9).
Due previsioni su `assign_avq.py` erano **false** e sono state smentite dal
sorgente: che non stampasse i donatori usati, e che la validazione delle
correlazioni fosse stata rimossa. Entrambe attribuivano allo script meno
diagnostica di quanta ne abbia, ed entrambe erano state dedotte dai log
invece che dal codice.

**v2.1 — 02/08/2026**
Medie nazionali della batteria della fiducia **ricalcolate** dai microdati AVQ
public use con `medie_nazionali.py`, invece che citate. Cercandone la fonte si
scopre che non esiste: l'ISTAT pubblica percentuali, non medie, e le uniche
medie pubblicate stanno nel BES con forze dell'ordine e vigili del fuoco
aggregati. Le cinque cablate risultano corrette entro 0,045, con scarto
sistematico negativo spiegato dalla differenza di universo (14+ contro 15+).
Ora sono ventitre invece di cinque. §13.6 punto 7 chiuso.

**v2.0 — 02/08/2026**
Undici comuni invece di quattro, popolazioni rigenerate col set AVQ a 23
variabili. §13.3 riscritta: `n_eff` sull'intera popolazione varia del 56% fra
comuni **senza seguire nulla**, nemmeno una variazione di 24 volte nella
popolazione, mentre sull'universo della variabile e' costante entro l'8% ed e'
il pool regionale. Aggiunto Castenaso: sulle variabili donate una popolazione
sintetica piccola e' piu' affidabile di una grande. Corretta come coincidenza
di configurazione l'affermazione che lo scarto firme-pool fosse −418 identico.
`sd(z)` da 1,030 a 1,018, inflazione della varianza da 1,06 a 1,04.
**v1.9 — 30/07/2026**
Il collasso gerarchico **misurato** e non più stimato: il condizionamento
pieno copre il 97–98,5%, il terzo livello e il fallback regionale non
scattano mai. Ma il collasso non è casuale — colpisce sempre
`elementare_o_meno` — e la direzione della distorsione è nota. Scartato il
3,7% da pool regionale dei log del 27 luglio: precede il collasso
gerarchico. Distinte le tre coperture che il solo numero confondeva: `MH`
è universo 15+ puro, `PUNTIFI10` ha in più il 2,3% di non risposta d'item.
Il blocco `[val] marginali` del log è una differenza **compositiva**
comune–regione, non una validazione.

**v1.8 — 30/07/2026**
Nuove §14 e §15: l'anello 1 e l'anello 3 verificati. Anatomia del constraint
set (16 blocchi, i 5 parziali sono complementi fuori universo); la
distinzione fra cella **assente** e cella **a zero**, che per MaxEnt sono
opposte, con le 26 coppie impossibili non vincolate da nessun blocco; lo
stato del pool misurato con z-score invece che con errore relativo,
`sd(z)`=1,030 e fattore di inflazione della varianza 1,06; il blocco anomalo
`sesso × background × origine_genitori`, aperto. Per l'anello 3: il seam a
nove anni non è dominante, lo scarto entro bin verso il giovane su dieci
prove su dieci, l'incoerenza età–istruzione al 2,6–2,7%. Ritirata una
discrepanza «fra prodotti censuari» che era rumore di campionamento.

**v1.7 — 30/07/2026**
Nuova §13, lo strato donatore AVQ: composizione effettiva del pool
(2023+2024, per `CRONI` assente nel 2022, meno i record con `ISTRMi`=99),
definizioni vere del condizionamento, numerosità efficace di Kish per
universo di variabile, correzione per grappolo familiare, e cosa il pool
eredita dal disegno campionario ISTAT. Corretti §2.2 e §11.1: il numero di
donatori distinti non è la numerosità efficace. Segnalata l'assenza di
`FORZE_ARMATE` dalla batteria.

**v1.6 — 29/07/2026**
Nuova §12, procedura operativa per aggiungere un comune, ricavata
dall'aggiunta di Modena. Annotate in §8 le due opportunità non sfruttate su
Modena (37 rioni, serie storiche 2002–2024) e la conferma che il portale
comunale non pubblica la cittadinanza per paese. §3.2 riorganizzata come
metodo di verifica in quattro varianti.

**v1.5 — 29/07/2026**
Aggiunta Modena: primo comune **tier 0** collaudato end-to-end. Metodo di
verifica delle denominazioni di zona. Corretti due bug di classificazione
per etichetta anziché per codice. Nuova §11.2.

**v1.4 — 29/07/2026**
Analisi dell'effetto della cittadinanza sulle variabili AVQ (§8).

**v1.3 — 29/07/2026**
Dodici variabili di fiducia istituzionale su scala 0–10. Codifiche AVQ
risolte sul tracciato ufficiale. Attributi da 28 a 40.

**v1.2 — 29/07/2026**
Condizionale geografico del paese collegato e attivo. §11.

**v1.1 — 29/07/2026**
Consolidamento in `gsp_common.py`. Correzione dei nomi delle zone di
Bologna e dell'istruzione nei bin infantili.

**v1.0 — 28/07/2026**
Prima stesura.
