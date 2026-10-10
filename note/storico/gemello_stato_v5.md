# Gemello identico: stato dopo le aree intermedie

*v5, 10/10/2026. **Sostituisce `gemello_stato_v4.md`** (ora in `storico/`).
Rispetto alla v4, aggiunge:*
- *le aree intermedie di circa 2.000 abitanti (decisione di Mirko, pensata
  anche per Fay–Herriot);*
- *le due scale dello z decise da Mirko, più una terza (z sulle quote);*
- *la rivalutazione del passo 4 a scala di area;*
- *una correzione datata a un'affermazione della v4 su q13 (§3).*

*Il resto della v4 resta valido: commit fino a `0d6ba7e`, decisioni su g e
`fit_cs`, Π per gli anelli 3–4, ricostruttori, assunzione implicita di
`fit_cs`, risultati per sezione e zona. È in `storico/gemello_stato_v4.md`.*

*Etichette: **misurato** = c'è un log; **dichiarato** = viene dal codice o
da una fonte; **aperto** = non deciso o non misurato.*

---

## 0. Commit e provenienza

- gemello `0bba750`: aree, z sulle quote, dispersione, livello «area» nel
  passo 4.
- I numeri di questa nota vengono da `gemello/risultati/passo4/036023/`,
  rigenerati su gemello `0bba750` e gsp `2595bba`, entrambi puliti
  (manifest).
- Comando: `python script/passo4_livello0.py config/livello0.yaml
  --paralleli 6`.
- Le popolazioni delle 40 repliche (R0, R1 × 20 semi) sono quelle della v4:
  la valutazione le riusa.

## 1. Aree intermedie (*dichiarato*: `gemello/aree.py`; *misurato*: `lavoro/aree_036023.json`)

**Perché.** Le sezioni ISTAT di Modena hanno 84 abitanti in media: troppo
poche per le domande rare (0,05–1,3 unità per sezione) e per le decisioni
q42. I quartieri sono 4, e il file sezioni non ha livelli intermedi.
Fay–Herriot (R3) serve due cose: abbastanza aree per stimare σ_u² (almeno
qualche decina) e campioni non vuoti nella maggior parte delle aree. La
taglia di 2.000 abitanti è anche quella degli IRIS del livello 2.

**Regola.**
- **Peso:** P1 del file sezioni Π, cioè dati pubblicati e non T.
- **Contiguità:** queen sulle geometrie ISTAT 2021, con una tolleranza di
  0,5 m, e sempre dentro il quartiere (COM_ASC1). Così le covariate di
  zona valgono per ogni area.
- **Sezioni senza popolazione:** le 407 sezioni dello shapefile assenti dal
  file sezioni restano come ponti.
- **Crescita:** si parte dal seme più periferico, cioè la sezione con meno
  vicine libere, e si aggiunge ogni volta la vicina più vicina al seme,
  fino a 2.000 abitanti.
- **Fusione:** le aree sotto 1.000 abitanti si uniscono alla vicina più
  piccola; le componenti senza vicine si fondono per distanza.

Tutto è deterministico: le parità si rompono per codice.

**Esito su Modena.**
- 87 aree, da 1.313 a 3.061 abitanti, mediana 2.063.
- Per quartiere: 11, 22, 29 e 27 aree.
- 2 componenti isolate (31 abitanti in tutto) fuse per distanza; un'area,
  `36023004_062`, quindi non è connessa nel grafo.

**Per Fay–Herriot.** Con 87 aree e φ = 1% (circa 1.850 individui, circa
800 nuclei) ci sono circa 21 individui per area; con φ = 0,1% circa 2, e
molte aree vuote, che ricevono la stima sintetica. Le covariate d'area
vengono da Π aggregato per area (file sezioni) e da Π di zona.

## 2. Scale dello z (decisione di Mirko: riportarle tutte)

| scala | definizione | pavimento sotto solo rumore (T e R campionati) |
|---|---|---|
| conteggi (nota §8.2) | (ĥ − h)/√(N α̃(1−α̃)), N della verità | ≈ 1,13 se il denominatore della stima è fisso; **più alto per quote alte**, perché quando il denominatore è casuale la varianza del conteggio cresce di ~1/(1−α) |
| quote | (ĥ/N̂ − h/N)/√(α̃(1−α̃)(1/N + 1/N̂)) | ≈ 0,8 |
| empirica | (ĥ − h)/sd fra le repliche di R | ≈ 1,13 |

L'indice di **dispersione** è la sd fra le repliche divisa per la sd
binomiale (mediana sulle chiavi).

**Dispersione di R1 per area** (*misurato*):
- domande su individui: 0,93–1,02;
- domande di nucleo: q31 1,15, q33 1,24, cioè sovradispersione moderata
  dell'anello 4;
- q00: 0,22, perché la popolazione per area è quasi fissata dagli anelli
  1 e 3 (largest remainder).

## 3. Correzione alla v4 (q13 per zona)

*v4 §6, testo originale:* «L'eccezione è q13 per zona (|z| 2,18, metà
delle zone con |z| > 2). q13 è nello span (ρ ≈ 0, v3), quindi non è errore
di modello: è l'errore di derivazione di `cs_build`, assunzione (3) […].»

*Correzione 10/10/2026:* il |z| 2,18 viene **soprattutto dalla scala**, non
dalla derivazione. q13 ha quota alta (α ≈ 0,79). Per zona, il denominatore
di R1 (persone 25–64 nella zona) è casuale, e la varianza del conteggio
degli occupati cresce di circa 1/(1−α) ≈ 4,8: sd × 2,2, mentre la
dispersione misurata è 1,94.

Sulle quote, q13 per zona ha |z| 0,99. Contro un pavimento di 0,8 l'eccesso
è piccolo, compatibile con il bias di derivazione di circa 0,5σ previsto
dal passo 3 (|z_T| 0,48 con Π_grezzo). L'errore di derivazione c'è, ma è
molto più piccolo di quanto la v4 lasciasse intendere.

## 4. Passo 4 a scala di area (87 aree, K = 20; *misurato*)

| domanda | ordine | z conteggi R0 | z conteggi R1 | **z quote R0** | **z quote R1** | err. rel. pesato R0 | err. rel. pesato R1 |
|---|---|---|---|---|---|---|---|
| q11 laureati 25–64 | 1 | 5,59 | 1,04 | 3,96 | 0,73 | 0,23 | 0,04 |
| q12 istr. × cond. (celle comunali) | 1 | 76,3 | 0,99 | 54,0 | 0,70 | 0,86 | 0,02 |
| q13 occupati 25–64 | 1 | 21,2 | 1,19 | 15,0 | 0,78 | 0,32 | 0,02 |
| q14 coniugate occupate | 1 | 4,31 | 1,09 | 3,41 | 0,75 | 0,33 | 0,08 |
| q15 vedovi 75+ | 1 | 10,2 | 1,03 | 7,19 | 0,73 | 0,80 | 0,08 |
| q21 over 75 soli | 2 | 2,08 | 1,25 | 1,43 | 0,88 | 0,18 | 0,11 |
| q22 stranieri ≤ media in cerca | 2 | 1,84 | 1,14 | 1,34 | 0,81 | 0,66 | 0,35 |
| q23 laureate occupate 25–49 | 2 | 8,04 | 1,14 | 5,97 | 0,79 | 0,60 | 0,08 |
| q31 figlio < 3, R e P occupati | 3 | 2,04 | 1,29 | 1,44 | 0,74 | 0,47 | 0,29 |
| q32 monoparentali R in cerca | 3 | 1,86 | 1,06 | 1,32 | 0,76 | 1,44 | 0,88 |
| q33 over 80 senza 18–64 | 3 | 1,63 | 1,44 | **0,87** | 0,83 | 0,11 | 0,10 |
| q34 coppie entrambe laureate | 3 | 1,30 | 1,12 | **0,91** | 0,79 | 0,22 | 0,19 |

**Come si leggono i risultati:**
- **R1 sta sul pavimento** in tutte e tre le scale, su tutte le domande:
  quote 0,70–0,88; empirica 1,01–1,21; conteggi 0,99–1,44, con l'eccesso
  sulle domande di nucleo spiegato dalla dispersione. **Al livello 0, R1
  ricostruisce a scala di area quanto il rumore permette** (inverse crime:
  è un controllo, non un risultato).
- **H1 (R1 batte R0 su ordini 1–3) è confermata a scala di area**, ma con
  ampiezze molto diverse. Dove la domanda dipende da interazioni
  dell'anello 1 il vantaggio è grande: q11–q15, q23, q12, con R0 su quote
  3,4–54. Sulle domande di nucleo dominate dalla struttura per età e dalla
  composizione familiare il vantaggio è quasi nullo: q33 0,87 contro 0,83,
  q34 0,91 contro 0,79 sulle quote. **Lettura:** quello che R1 aggiunge a
  R0 sta nell'anello 1. Gli anelli 3–4 sono gli stessi nei due
  ricostruttori, e q33 e q34 dipendono soprattutto da loro e dai margini
  per età e istruzione di zona, che R0 ha.
- **Gli errori relativi pesati** di R1 sono piccoli sulle domande frequenti
  (0,02–0,11) e grandi sulle rare (q22 0,35, q31 0,29, q32 0,88). È rumore
  di conteggi piccoli, coerente con il pavimento.

**Bias/varianza di R1 per area:** la quota del bias va da 0,33 a 0,57. Per
il solo rumore ci si attende circa 0,5, perché lo scarto fisso di T conta
come bias.

**Decisioni per area** (medie su 20 semi):

| decisione | k | regret R0 | regret R1 | Jaccard R0 | Jaccard R1 | Spearman R0 | Spearman R1 |
|---|---|---|---|---|---|---|---|
| q41 (over 75 soli) | 5 | 0,092 | 0,056 | 0,28 | 0,45 | 0,83 | 0,87 |
| q41 | 10 | 0,067 | 0,035 | 0,36 | 0,50 | | |
| q41 | 20 | 0,050 | 0,027 | 0,56 | 0,61 | | |
| q42 (prima infanzia) | 5 | 0,311 | 0,288 | 0,10 | 0,09 | 0,24 | 0,38 |
| q42 | 10 | 0,268 | 0,211 | 0,10 | 0,13 | | |
| q42 | 20 | 0,226 | 0,176 | 0,19 | 0,27 | | |

Rispetto alle sezioni il regret scende per entrambi (q41 R1: da 7% a
3–6%). q42 resta difficile: q31 vale circa 11 nuclei per area, e la
graduatoria è dominata dal rumore anche per R1 (Spearman 0,38).

## 5. Prossimi passi

1. **Passo 5:** campione S di nuclei interi (Bernoulli, φ ∈ {0,1%, 0,5%,
   1%, 2%, 5%}, B ≥ 20 repliche); R2a (IPF a seme per zona, δ in
   sensibilità) e R3 (Fay–Herriot per area con REML, covariate da Π per
   area, fissate prima di guardare gli errori). Criteri del §11.5 della
   nota: al livello 0, R2 con S ⊂ T non batte R1 in modo significativo, e
   R3 con φ = 5% recupera le quote per area entro il suo MSE nominale.
2. **Livello 1a:** g1, poi g2 (invisibile alle domande lineari, da
   verificare su q34) e g4 (q14, q31).

## 6. Aperto (cumulativo)

- Rigenerare gli anelli 3+4 della flotta con l'età corretta (release).
- Regole `IMPOSSIBILI` per background × origine, con refit.
- Età singola condizionata allo stato civile, e coniugati di 15 anni.
- Causa del disallineamento dei nuclei di produzione di Modena.
- Lista delle covariate di R3 (da fissare prima del passo 5).
