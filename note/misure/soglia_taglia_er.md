# Soglia di taglia per la generazione — criterio e misure (ER, 1/9/2026)

Fonte: manifest campagna estensione_er_2026, campo `righe` delle celle
(318 comuni con acquisizione completa; 12 di flotta esclusi dal manifest).

## Il criterio

**pop / |celle| >= 2**: almeno due individui attesi per cella del vincolo
piu' fine (819 celle di istruzione x eta x sesso). Sotto quella soglia il
vincolo censuario degenera in indicatrici (conteggi 0/1/2, dove la
perturbazione ISTAT per la riservatezza e l'arrotondamento pesano quanto
il segnale) e il fit insegue rumore invece di struttura.

Il criterio NON e' la taglia in se': e' il rapporto fra popolazione e
cardinalita' del vincolo. Un comune piccolo puo' rientrare a un livello
piu' basso (meno variabili -> celle piu' piene): scala di configurazioni
per fascia, non esclusione.

## Le misure

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

Atteso per cella (pop / righe di istruzione_eta, mediana per fascia):
E' QUESTO il vincolo. Scala linearmente, attraversa 1 a ~1.000 abitanti.

| fascia | <500 | 0.5-1k | 1-2k | 2-5k | 5-10k | 10-30k | >30k |
|--------|-----:|-------:|-----:|-----:|------:|-------:|-----:|
| ab/cella| 0.3 |    1.0 |  2.1 |  4.1 |   8.7 |   17.6 | 42.6 |

Copertura per soglia (manifest: 320 comuni, 2.854.047 abitanti):

| soglia | comuni       | popolazione       |
|-------:|-------------:|------------------:|
|  1.000 | 299 (93.4%)  | 2.840.074 (99.5%) |
|  2.000 | 269 (84.1%)  | 2.795.459 (97.9%) |
|  3.000 | 237 (74.1%)  | 2.717.679 (95.2%) |
|  5.000 | 185 (57.8%)  | 2.511.509 (88.0%) |
| 10.000 |  92 (28.7%)  | 1.836.445 (64.3%) |
| 15.000 |  47 (14.7%)  | 1.288.111 (45.1%) |

## Scelta e limiti

Soglia efficiente: **2.000 abitanti** (pop/celle ~2.4). Esclude 51 comuni,
il 2.1% della popolazione regionale. Da 2k a 5k si perderebbero altri 84
comuni e 10 punti di popolazione per passare da 2.4 a 6 individui/cella:
guadagno reale ma su un vincolo che a 2.4 gia' funziona.

**Limite da dichiarare (§7):** i comuni esclusi non sono un campione
casuale — sono l'Appennino (Cerignale, Zerba, Corte Brugnatella, Tornolo,
Coli...). Il dataset sopra-rappresenta la pianura.

## Aperto [v]

Due indicatori indipendenti non ancora misurati, potrebbero alzare la
soglia:
1. `n_eff` dei donatori AVQ: il pool e' regionale e fisso; su 2.000
   individui il riuso e' minimo e ogni statistica poggia su pochi
   rispondenti reali. Vincolo dell'anello 3, non dell'anello 1.
2. Fit pilota attorno alla soglia (un comune a 2.000, uno a 800): MRE
   finale contro il pavimento di campionamento. Se a 800 l'MRE e' gia'
   sotto il pavimento, il fit interpola rumore — dimostrazione diretta.
