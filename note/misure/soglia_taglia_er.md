# Soglia di taglia per la generazione — criterio e misure (ER, 1-2/9/2026)

Fonte: manifest campagna estensione_er_2026, campo `righe` delle celle
(318 comuni con acquisizione completa; 12 di flotta esclusi dal manifest);
pilota di generazione su tre comuni (2/9, log `rigenera_20260902_0905` e
`_0908`, corse di collaudo ad albero sporco — i numeri sono deterministici,
il verbale citabile va rifatto a commit pulito se entra nel paper).

Stato del criterio: **v2** (2/9). La v1 (1/9, `pop/|celle| >= 2`) e'
conservata in fondo come rettifica: era un proxy sui dati grezzi, il
pilota ha dato il criterio sul modello.

## Il criterio (v2)

**pop / |supporto| >= 1**: almeno un individuo atteso per stato del modello
fittato. Il supporto e' l'insieme degli stati del lattice K6C (5.376) su
cui il fit assegna massa non trascurabile — `supporto~N/5376` nel log di
`fit_cs`. Sotto quella soglia la popolazione sintetica e' un campione piu'
piccolo del proprio modello: la maggioranza degli stati con massa positiva
riceve zero individui, e la popolazione generata non puo' riprodurre la
distribuzione che l'ha generata.

E' una proprieta' del MODELLO, non dei dati grezzi: il supporto cresce
lentamente con la popolazione (2.484 -> 3.016 stati su un fattore 10 di
abitanti), quindi il rapporto e' dominato dalla popolazione e attraversa 1
attorno ai **2.500-3.000 abitanti** a K6C. Un comune piccolo puo' rientrare
a un livello con meno variabili (supporto piu' piccolo): scala di
configurazioni per fascia, non esclusione — resta un'estensione possibile,
non misurata.

Sotto soglia la popolazione sintetica e' **descrittivamente corretta e
inferenzialmente vuota**: le marginali univariate e le medie delle
continue restano giuste (Maiolo: tutte entro 0,04 e pochi decimi), ma le
distribuzioni congiunte non sono piu' stimabili (riuso donatori -> 1,
correlazioni al rumore, coppie mascherate). E' la distinzione che il paper
deve fare: il metodo non fallisce sui piccoli, produce un oggetto diverso.

## Il pilota (2/9): tre comuni, tre indicatori indipendenti

Comuni scelti dal manifest per popolazione, gate chiuso, articolazione
ASSENTE (K6C), tre province diverse:

| comune            | codice | provincia | pop (anag 2024) | regime atteso |
|-------------------|--------|-----------|----------------:|---------------|
| Sissa Trecasali   | 034049 | Parma     |           7.901 | sopra         |
| Vernasca          | 033044 | Piacenza  |           2.014 | al bordo      |
| Maiolo            | 099022 | Rimini    |             799 | sotto         |

Catena completa (`build_constraints` -> `build_sezioni` -> `rigenera.sh`:
cs_build, fit_cs, assign_avq, enrich, nucleo). Tutti e tre completano
senza errori e con zero combinazioni impossibili: **la pipeline non si
rompe sui piccoli**. La giustificazione del taglio non puo' essere
"non funziona" — e' piu' sottile, e sta nei tre indicatori sotto.

### Indicatore 1 — anello 1, costruzione dei vincoli

`[c2]` (sesso x eta x cittadinanza, soft condizionato sulla spine
anagrafica): "gruppi anagrafici senza dato censuario" = celle che
l'anagrafe ha (spine hard piena: 712 celle ovunque) ma su cui il
censimento tace, e il condizionale ripiega sul default.

| comune   | celle c2 | gruppi senza dato censuario | frazione | celle c3 (su 48) |
|----------|---------:|----------------------------:|---------:|-----------------:|
| Sissa    |      363 |                           1 |     0,3% |               48 |
| Vernasca |      268 |                           9 |     3,4% |               46 |
| Maiolo   |      220 |                          19 |     8,6% |               40 |

A 800 abitanti quasi il 9% dei gruppi viaggia senza informazione
censuaria; la griglia istruzione (c3) si sbriciola per prima.

### Indicatore 2 — anello 1, fit e supporto

| comune   | MRE finale | supporto (stati con massa) | **individui per stato** |
|----------|-----------:|---------------------------:|------------------------:|
| Sissa    |    4,82e-4 |                3.016/5.376 |                     2,6 |
| Vernasca |    4,93e-4 |                2.795/5.376 |                    0,72 |
| Maiolo   |    2,93e-4 |                2.484/5.376 |                    0,32 |

Maiolo ha l'MRE **migliore**: non fitta meglio, ha meno da fittare —
la firma del regime patologico e' un MRE "troppo bello". Il numero che
decide e' l'ultima colonna: sotto 1 il campione e' piu' piccolo del
supporto. Il rapporto attraversa 1 tra Vernasca e Sissa.

### Indicatore 3 — anello 2, donatori AVQ e correlazioni

Pool regionale fisso: 4.629 donatori con cella completa.

| comune   | donatori distinti | riuso medio | scarto max corr. (253 coppie) | mediano | vs rumore 1/sqrt(n) |
|----------|------------------:|------------:|------------------------------:|--------:|--------------------:|
| Sissa    |      3.570 (77%)  |        2,2x |                         0,069 |   0,010 | al rumore (~3σ)     |
| Vernasca |      1.584 (34%)  |        1,3x |                         0,098 |   0,016 | 4,4σ                |
| Maiolo   |        720 (16%)  |        1,1x |                         0,181 |   0,030 | 5,2σ; 1 coppia mascherata (<100 donatori) |

Rumore atteso di una correlazione campionaria: ~1/sqrt(n) (Sissa 0,011,
Vernasca 0,022, Maiolo 0,035); il massimo su 253 coppie sotto ipotesi
nulla si aspetta attorno a 3σ. Sissa sta al rumore; Vernasca sopra;
Maiolo ha la mediana degli scarti pari al rumore (0,030 vs 0,035) —
cioe' TUTTO lo scarto e' campionamento, nessun segnale residuo — e la
pipeline maschera gia' una coppia per donatori insufficienti. A riuso
1,1x la popolazione sintetica e' un sottocampione di AVQ, non un
ricampionamento.

### Sintesi

| indicatore                                | anello | Sissa 7,9k | Vernasca 2,0k | Maiolo 0,8k |
|-------------------------------------------|:------:|-----------:|--------------:|------------:|
| gruppi senza condizionale censuario       |   1    |       0,3% |          3,4% |        8,6% |
| individui per stato del supporto          |   1    |        2,6 |          0,72 |        0,32 |
| riuso donatori                            |   2    |       2,2x |          1,3x |        1,1x |
| scarto max correlazioni vs rumore         |   2    |  al rumore |          4,4σ |        5,2σ |

**Sissa dentro, Maiolo fuori, Vernasca marginale su tutti e quattro.**
Tre indicatori indipendenti (costruzione vincoli, fit, donatori)
concordano: la soglia sta fra 2.000 e 8.000, e il criterio
`pop/supporto >= 1` la colloca attorno ai 2.500-3.000.

## Misure di contorno (1/9, dal manifest)

Saturazione censuaria (frazione di celle presenti sul tetto, mediana):
NON e' il vincolo. Regge sopra il 94% fino a 500 abitanti.

| fascia  | n  | istruzione_eta | condprof_eta | istr_citt | condprof_citt | settore |
|---------|----|---------------:|-------------:|----------:|--------------:|--------:|
| <500    |  4 |           81.7 |         98.5 |      86.2 |          97.3 |    92.9 |
| 0.5-1k  | 17 |           94.3 |        100.0 |      97.5 |         100.0 |   100.0 |
| 1-2k    | 30 |           97.7 |        100.0 |      99.5 |         100.0 |   100.0 |
| 2-5k    | 84 |           99.1 |        100.0 |     100.0 |         100.0 |   100.0 |
| 5-10k   | 93 |           99.9 |        100.0 |     100.0 |         100.0 |   100.0 |
| 10-30k  | 78 |          100.0 |        100.0 |     100.0 |         100.0 |   100.0 |
| >30k    | 12 |          100.0 |        100.0 |     100.0 |         100.0 |   100.0 |

Atteso per cella del vincolo piu' fine (pop / righe di istruzione_eta,
mediana per fascia) — il proxy della v1, scala linearmente:

| fascia  | <500 | 0.5-1k | 1-2k | 2-5k | 5-10k | 10-30k | >30k |
|---------|-----:|-------:|-----:|-----:|------:|-------:|-----:|
| ab/cella|  0.3 |    1.0 |  2.1 |  4.1 |   8.7 |   17.6 | 42.6 |

Copertura per soglia (manifest: 320 comuni, 2.854.047 abitanti):

| soglia | comuni       | popolazione       |
|-------:|-------------:|------------------:|
|  1.000 | 299 (93.4%)  | 2.840.074 (99.5%) |
|  2.000 | 269 (84.1%)  | 2.795.459 (97.9%) |
|  2.500 |          [v] |               [v] |
|  3.000 | 237 (74.1%)  | 2.717.679 (95.2%) |
|  5.000 | 185 (57.8%)  | 2.511.509 (88.0%) |
| 10.000 |  92 (28.7%)  | 1.836.445 (64.3%) |
| 15.000 |  47 (14.7%)  | 1.288.111 (45.1%) |

## Scelta e limiti

Soglia: **fra 2.500 e 3.000 abitanti** — la decisione esatta e' una
convenzione dichiarata sul criterio `pop/supporto >= 1`, ed entrambe
sono difendibili. 3.000 e' la piu' prudente (Vernasca a 2.014 e' sotto
su tutti gli indicatori; 3.000 lascia margine) e vale ancora il **95,2%
della popolazione regionale** (237 comuni). Rispetto al taglio a 5.000
inizialmente ipotizzato, si recuperano 52 comuni e 7 punti di
popolazione.

Formulazione per §7: *un comune entra nel dataset se la sua popolazione
supera il supporto del modello fittato (almeno un individuo atteso per
stato), il che in Emilia-Romagna corrisponde a ~3.000 abitanti e copre
il 95% dei residenti; sotto quella soglia le marginali restano corrette
ma le distribuzioni congiunte non sono stimabili — il riuso dei
donatori tende a 1 e le correlazioni scendono al livello del rumore
campionario.*

### Il caso al bordo: Sarmato (033042)

La soglia si applica su POSAS 2026, il dato di selezione disponibile
prima della generazione; il criterio si verifica su P1 censuario 2023,
il dato che la generazione usa davvero. Un comune su 234 cade fra i
due: Sarmato, POSAS 3.108 (dentro) e P1 2.931 (ind_per_stato 0,949,
fuori). E' escluso a posteriori.

Non e' un caso qualunque: e' lo stesso comune che il controllo C5 aveva
segnalato come DIVERGE per lo scarto anagrafe/proiezione piu' grande
della regione (-4,5%), accettato con la nota "da guardare se rientra
nella v2". Due criteri indipendenti — coerenza fra fonti e capienza del
modello — indicano lo stesso comune. La v2 e' quindi 233 comuni piu' i
12 della flotta storica: 245.

**Limiti da dichiarare (§7):**
1. I comuni esclusi non sono un campione casuale — sono l'Appennino
   (Cerignale, Zerba, Corte Brugnatella, Tornolo, Coli, Maiolo...). Il
   dataset sopra-rappresenta la pianura e sotto-rappresenta la montagna.
2. I tre indicatori sono stati misurati su tre comuni: la soglia e'
   stimata per interpolazione fra 2.014 e 7.901. Un quarto punto a
   ~3.000-4.000 la fisserebbe meglio (costo: un comune in piu' nel
   pilota, minuti di macchina).
3. La soglia e' specifica del livello K6C (5.376 stati). A K9C il
   supporto e' molto piu' grande e la soglia molto piu' alta — coerente
   col fatto che K9C esiste solo per i capoluoghi.

## Rettifica: il criterio v1 (1/9)

La v1 dichiarava `pop/|celle| >= 2` (819 celle del vincolo piu' fine),
con soglia efficiente a 2.000. Era un proxy corretto nella direzione ma
sbagliato nell'oggetto: misurava i dati grezzi (quante persone per cella
del vincolo) invece del modello (quante persone per stato del supporto).
Il pilota ha mostrato che il supporto e' ~3x le celle del vincolo e
cresce con la popolazione, quindi la soglia v1 sottostimava: Vernasca
(2.014) passava la v1 (2,1 ab/cella) ed e' marginale su tutti gli
indicatori del pilota. La v1 e' conservata qui per tracciabilita', non
si usa piu'.

## Chiusi

- ~~`n_eff` dei donatori~~: misurato (indicatore 3). Morde da 2.000 in
  giu': riuso 1,3x a Vernasca, 1,1x a Maiolo.
- ~~Fit pilota attorno alla soglia~~: fatto (indicatore 2). L'MRE non
  discrimina da solo (tutti convergono a ~3-5e-4); discrimina il
  rapporto popolazione/supporto.

## Aperto [v]

- Copertura a 2.500 (una riga del heredoc di copertura).
- Un quarto comune del pilota a ~3.500 per fissare l'interpolazione.
- Il corollario sui livelli ridotti (K5C/K4C sotto soglia): possibile,
  non misurato. Da valutare solo se la v2 vorra' includere i piccoli.
