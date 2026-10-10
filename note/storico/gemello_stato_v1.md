# Gemello identico — stato dopo il passo 1 (inventario dei vincoli)

*v1 — 10/10/2026. Risponde ai punti **[VERIFICA NEL REPO]** di
`nota_gemello_v1.md` (§3.1, §4.2, §5.4, §5.5, §6). Fonti: lettura di
`scripts/vincoli/cs_build.py`, `scripts/attributi/enrich.py`,
`src/gsp/nucleo.py`, `gsp.common.IMPOSSIBILI`, e dei file prodotti per
Bologna (037006) in `data/comuni/037006/{constraints_2024,zona_2023}/`.
Tutti i numeri sono **misurati** leggendo `cs_K9C.json`, `targets_K9C.json`
e `fit_K9C.json` dei comuni citati (nessun ricalcolo: sono i prodotti della
corsa che ha generato i file su disco).*

Ambiente: `gsp` è installato nell'env conda **`ml`**, non in `gsp` come dice
CLAUDE.md (l'env `gsp` non esiste su questa macchina).

---

## 1. Spazio X (K9C)

| var | classi | n |
|---|---|---|
| zona | quartieri/zone del comune | 4 (Modena) … 18 (Bologna) |
| sesso | M, F | 2 |
| eta | 0-8, 9-14, 15-24, 25-34, 35-49, 50-64, 65-74, 75+ | 8 |
| stato_civile | celibe_nubile, coniugato_unito, divorziato_sciolto, vedovo | 4 |
| cittadinanza | ITL, FRG | 2 |
| istruzione | nessun_titolo, elementare, media, diploma, laurea_o_its, post_laurea | 6 |
| condizione | altra_condizione, casalinga, in_cerca, non_applicabile, occupato, percettore_pensioni, studente | 7 |
| background | italiano_nativo, italiano_rientrato, naturalizzato_g2, naturalizzato_immigrato, straniero_g2, straniero_immigrato | 6 |
| origine_genitori | entrambi_italiani, entrambi_stranieri, madre_straniera_padre_italiano, madre_italiana_padre_straniero, non_applicabile | 5 |

|X| = 161.280 × n_zone (prodotto pieno, prima delle esclusioni).

## 2. Inventario dei blocchi (Bologna 037006, K9C, m = 1.783 celle)

Il formato su disco è `cs_<LIV>.json`: lista di celle `{attrs, vals, alpha}`
con indici in `vars`/`categories`, alpha = quota sulla popolazione totale.
`targets_<LIV>.json` dà gli stessi blocchi con nome e fonte.

| blocco | variabili | scala | classi (tavola grezza → blocco) | celle | somma | fonte / derivazione |
|---|---|---|---|---|---|---|
| A | sesso × eta × stato_civile | comune | età singola → 8 bin | 52 | 1,000 | anagrafe 1/1/2024, esatto (`c1`) |
| B | sesso × eta × cittadinanza | comune | età singola → 8 bin | 32 | 1,000 | censimento 2023, esatto (`c2`) |
| C | sesso × eta × istruzione | comune | **4 classi** (9-24, 25-49, 50-64, 65+) × 6 titoli → 8 bin | 78 | 0,935 (univ. 9+) | `c3`, allocazione classe→bin sui pesi anagrafici con IPF ed età minima per titolo |
| D | sesso × eta × condizione | comune | **4 classi** (15-24, 25-49, 50-64, 65+) × 6 condizioni → bin | 72 | 0,888 (univ. 15+) | `c4`, allocazione classe→bin proporzionale |
| E | cittadinanza × istruzione | comune | 2 × 6 | 12 | 1,000 | `c5`, riscalato a univ. 9+, + under-9 strutturali |
| F | cittadinanza × condizione | comune | 2 × 7 | 14 | 1,000 | `c6`, riscalato a univ. 15+, + under-15 strutturali |
| S_istr | eta × istruzione | comune | 0-8 → nessun_titolo | 1 | 0,065 | strutturale |
| S_cond | eta × condizione | comune | 0-8, 9-14 → non_applicabile | 2 | 0,112 | strutturale |
| G | sesso × background | comune | 2 × 6 | 12 | 1,000 | `c7` (migr backg, armonizzato su B) |
| H | sesso × background × origine_genitori | comune | 2 × 6 × 5 | 30 | 1,000 | `c8` |
| GC | cittadinanza × background | comune | 2 × 6, con zeri | 12 | 1,000 | deterministico (background ⇒ cittadinanza) |
| Z1 | zona × sesso × eta | zona | quinquennali di sezione → bin | 288 | 1,000 | `z1`: P(zona \| sesso, quinq.) × anagrafe |
| Z2 | zona × sesso × eta × cittadinanza | zona | **macroetà 3 classi** (0-14, 15-64, 65+) | 576 | 1,000 | `z2`: quote × B, poi IPF righe=Z1, colonne=B |
| Z3 | zona × sesso × istruzione | zona | **5 titoli** (laurea+post fusi in «terziario») | 216 | 1,000 | `z3`: quote × totali C, under-9 da Z1, IPF |
| Z4 | zona × sesso × eta × condizione | zona | **solo `occupato`**, bin 15-64; la tavola non ha età | 144 | 0,459 | `z4`: P(zona \| sesso, occupato) costante sui bin, cap su Z1 |
| Z5 | zona × sesso × background | zona | 6 background | 216 | 1,000 | `z6` (EM1-6): IPF entro gruppo di cittadinanza, righe=Z2, colonne=G |
| X_* | eta × condizione, eta × istruzione | — | 26 celle α=0 | 26 | 0 | `gsp.common.IMPOSSIBILI` (sotto) |

Esclusioni α=0 (`IMPOSSIBILI`, 4 regole, tutte su coppie con `eta`):
1. eta ∈ {0-8, 9-14} ⇒ condizione = non_applicabile (universo 15+);
2. eta ≥ 15-24 ⇒ condizione ≠ non_applicabile;
3. eta 0-8 ⇒ istruzione = nessun_titolo (universo 9+);
4. eta 9-14 ⇒ istruzione ∉ {diploma, laurea_o_its, post_laurea}.

A queste si aggiungono gli zeri deterministici di GC (background ⇒
cittadinanza) e gli zeri impliciti dell'allocazione C (`ETA_MIN_TITOLO`:
elementare ≥ 10, media ≥ 13 anni).

### 2.1 Fuori dal constraint set (anelli 3 e 4)

Le tavole di sezione **non** sono vincoli del MaxEnt. Entrano dopo, come
condizionali:
- **anello 3** (`enrich.py`): sezione ~ P(σ | zona, sesso, eta3,
  cittadinanza) da `P1`, quinquennali per sesso (`P30…P104`), `ST25–ST30`
  (sesso × eta3), `ST1` (stranieri), `ST16–ST21` (UE/extra-UE). Assunzione
  (8): sezione ⊥ (istruzione, condizione, background, origine) | (zona,
  sesso, eta3, cittadinanza);
- **anello 4** (`gsp.nucleo`): `P1`, `PF3–PF8` (famiglie per ampiezza
  1…6+) per sezione.

**Conseguenza per la nota (§2, §6.1):** ρ_h e il gap KL calcolati su X
riguardano solo l'anello 1 e la scala di zona. Π₂ e Π₃ non cambiano p*:
cambiano gli anelli 3 e 4, che non sono MaxEnt. Per le domande per sezione
o per nucleo la teoria del §2 non dà una previsione diretta. Va detto nel
paper, oppure si estende la teoria all'anello 3 (che è un prodotto di
condizionali, quindi la previsione si scrive lo stesso, ma è un'altra
formula).

## 3. Interazioni vincolate e non vincolate (per scegliere g, §4.2)

Vincolate, almeno a qualche scala: sesso×eta×{stato_civile, cittadinanza,
istruzione, condizione}; cittadinanza×{istruzione, condizione, background};
sesso×background×origine; zona×sesso×eta×cittadinanza; zona×sesso×istruzione;
zona×sesso×background; zona×sesso×eta×occupato.

**Mai vincolate**, quindi candidate per g (‖g_⊥‖ ancora da calcolare):
- istruzione × condizione, a qualunque scala. **q12 è interamente fuori
  dallo span.**
- stato_civile × tutto, eccetto sesso × eta.
- cittadinanza × istruzione × eta, e cittadinanza × istruzione × condizione.
- background × {istruzione, condizione, eta}.
- zona × {stato_civile, condizione ≠ occupato}, zona × eta × istruzione.

I tre candidati della nota (cittadinanza×istruzione×condizione,
stato_civile×istruzione, background×condizione per età) sono tutti fuori dal
constraint set. Il terzo è parzialmente implicato dai blocchi
cittadinanza×condizione e GC, quindi il suo ‖g_⊥‖ sarà probabilmente il più
piccolo.

## 4. Comune per i livelli 0–1 (§3.1)

| comune | N | zone | \|X\| | m | celle tenute | t solver esatto |
|---|---|---|---|---|---|---|
| Modena 036023 | 184.597 | 4 | 645.120 | 663 | 596 | 16 s |
| Reggio E. 035033 | 171.207 | 4 | 645.120 | 663 | 597 | 23 s |
| Piacenza 033032 | 102.887 | 4 | 645.120 | 663 | 598 | 20 s |
| Rimini 099014 | 150.046 | 6 | 967.680 | 823 | 757 | 29 s |
| Parma 034027 | 198.121 | 13 | 2.096.640 | 1.383 | 1.279 | 79 s |
| Bologna 037006 | 390.098 | 18 | 2.903.040 | 1.783 | 1.614 | 79 s |

(`t_exact_s` da `fit_K9C.json`; «celle tenute» = `kept_sig_exact`, dopo il
filtro `--min-alpha 2e-4`.)

Proposta: **Modena** per sviluppare (16 s per fit, così le griglie θ × semi
costano poco) e **Parma** come secondo comune. Parma ha N simile ma 13 zone,
il che serve per la scala di zona e per R3 a livello di zona. Lo scaling con
N si fa con Piacenza (103 k) → Modena (185 k) → Bologna (390 k), tutti
enumerabili.

## 5. Implicazioni per il disegno (decisioni da prendere)

**D1 — dove taglia Π.** Il constraint set non è una pubblicazione: è una
*derivazione* da tavole grezze, con le assunzioni (1)–(3) di `cs_build`
(allocazione classe→bin, quote di zona costanti entro classe, Z4 senza età).
Ci sono due opzioni:
- **Π_grezzo**: Π produce le tavole grezze nel formato ISTAT (`c1…c8`,
  `z1…z6`, file sezioni), e poi `cs_build.py` gira invariato. È fedele alla
  geometria ISTAT e include nella misura l'errore di derivazione.
- **Π_blocchi**: Π produce direttamente i blocchi A…Z5 esatti da T. È più
  pulito per la teoria, perché E_T[f] = b esattamente e vale l'identità
  pitagorica.

Proposta: Π_grezzo come caso principale (è ciò che Animarium fa davvero) e
Π_blocchi come riferimento. Π_grezzo − Π_blocchi isola l'errore di
derivazione, che altrimenti finisce nel «gap di modello». Al livello 0 con
Π_grezzo, E_T[f] ≠ b anche senza rumore: il §3.3 va letto così.

**D2 — l'adattatore (§5.5) diventa semplice con Π_grezzo.** Basta scrivere
`c*.csv` e `zona_2023/z*.csv` in una directory comune fittizia e chiamare
`cs_build.main`. Ostacolo: `cs_build.main` e `fit_cs.py` hardcodano
`~/progetti/gsp/data/comuni/<COD>/`. Servono un codice comune fittizio (es.
`FR31555`) in quella directory, oppure una modifica chirurgica per accettare
la directory come parametro. Proposta: la modifica chirurgica, perché il
gemello non deve scrivere in `data/comuni/`.

**D3 — soglia 14/15 al livello 2.** I bin `9-14 | 15-24` coincidono con la
soglia ISTAT. La soglia INSEE a 14 anni taglia il bin 9-14. Si può scegliere
fra (a) bin `9-13 | 14-24` al livello 2, che è coerente ma cambia la griglia
rispetto all'Italia, oppure (b) bin ISTAT con i 14enni INSEE ricodificati a
`non_applicabile`, che perde un'informazione minima e mantiene la geometria.
Proposta: (b), in linea con «imitare la geometria ISTAT» (§6).

**D4 — `DIPL ZZ`.** In `gsp` i minori di 9 anni sono `nessun_titolo` per
costruzione. Fra 9 e 14 anni il titolo viene da C, con `ETA_MIN_TITOLO`
(elementare ≥ 10, media ≥ 13). Se ZZ copre tutti i minori di 14 anni, il
titolo dei 9–13enni non c'è nella verità. Si può imputarlo per età con la
stessa regola deterministica (≥ 13 → media, 10–12 → elementare,
< 10 → nessun_titolo) e dichiararlo, oppure escludere l'istruzione degli
under-14 dalle domande. Proposta: imputare, perché nessuna domanda della
batteria tocca l'istruzione degli under-14.

**D5 — §6 della nota da correggere.** «Età (4 classi) × istruzione» è in
realtà **sesso** × età(4 classi) × istruzione, allocata sugli 8 bin. Esiste
anche età(4 classi) × condizione per sesso (D). I margini per sezione e i
`PF3–PF8` non stanno in Π₁ (constraint set), stanno negli anelli 3 e 4 (§2.1).

## 6. Aperto

- Dove stanno le popolazioni prodotte da `release-v2.0`: il tag esiste, ma
  `data/` non è versionata. Va confermato che i file attuali di Modena siano
  quelli della release, o va indicato l'archivio da usare in sola lettura.
- ‖g_⊥‖ per i candidati del §3: si misura al passo 3 (`teoria.py`).
- Conferma della tabella del §2 da parte di Mirko (criterio di accettazione
  del passo 1).
