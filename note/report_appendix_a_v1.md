# Appendix A — Reference tables
## Version 1 — §A.1–A.4 (26 August 2026)

> Everything here is generated from the release artefacts rather than
> written: each section names the command that produces it, so a reader
> can regenerate it against a different tag. This draft populates every
> section from the working notes (`riferimento`, `fonti`) and from the
> prose of Parts I–IV, which is as far as a reader can go without the
> tagged repository itself; where the literal command has not yet been
> re-run against `report-v1.0`, the section says so and the gap is
> carried into the open items at the end, in the same form as every
> other Part.

---

### A.1 What, in a record, is actually real



| component | provenance | what is real |
|---|---|---|
| demographic attributes (sex, age, marital status, citizenship, education, condition, background, parents' origin, zone) | drawn from a maximum-entropy distribution under census constraints | the *aggregates* are real; the individual is a sample of a distribution, and no record corresponds to anyone |
| attitudes and health (23 AVQ variables) | the complete response vector of one real survey respondent, copied whole | the vector is real — already protected at source by ISTAT's public-use release, and reused across tens of synthetic individuals, so no combination is unique to one record |
| section, exact age, address | allocated within the census section; the address uniformly among its registered civic numbers | the *counts* per section are real; the assignment carries no information about anyone (and the public regime randomises the coordinate within the section) |
| household id and role | assembled under the census size distribution per section, composition from a survey-based repertoire | the size distribution is real per section; the household is a model |
| names, detailed titles, sector, biography | deterministic rendering from registered repertoires and census-conditioned structure | nothing: plausible by construction, and therefore collident — a name individuates no one |

**No component is personal data.** The population is simulated from
published aggregates, not anonymised from individual records; there is
no one to re-identify (§I.7).

---

### A.2 The released schema

The columns of `pop.parquet` in the public regime, with type and
meaning, and the columns that exist only in the `persona` and
`narrativo` regimes (marked °). 

**Ring 1 — the joint model (public).**

| column | type | classes | meaning |
|---|---|---|---|
| `zona` | string (8-digit code) | 4–33, per municipality | statistical zone / quartiere / circoscrizione / area |
| `sesso` | categorical | 2 | `M`, `F` |
| `eta` | categorical | 8 | age bin: `0-8`, `9-14`, `15-24`, `25-34`, `35-49`, `50-64`, `65-74`, `75+` |
| `stato_civile` | categorical | 4 | `celibe_nubile`, `coniugato_unito`, `divorziato_sciolto`, `vedovo` |
| `cittadinanza` | categorical | 2 | `ITL`, `FRG` (legal; `FRG` includes stateless persons) |
| `istruzione` | categorical | 6 | `nessun_titolo` … `post_laurea` |
| `condizione` | categorical | 7 | `occupato` … `non_applicabile` (under 15) |
| `background` | categorical | 6 | `italiano_nativo` … `straniero_immigrato` |
| `origine_genitori` | categorical | 5 | `entrambi_italiani` … `non_applicabile` |
| `quartiere`° | string | — | zone display name; **absent from the public regime**, one-to-one with `zona` and supplied by the manifest instead |

**Ring 2 — donated attributes and nationality (public, except `donor_id`).**

| column | type | classes | meaning |
|---|---|---|---|
| `area` | categorical | 3 | `UE`, `EXTRA_UE`, `NaN` for Italian citizens |
| `paese` | string | 143–151 + `Italia` | country of citizenship (municipal census × municipal geographic source, §I.3) |
| `AMBIENTE`, `FIDUCIA`, `SALUTE`, `CRONI`, `FUMO`, `MH`, `BMI`, `BMIMIN`, `CPESO`, `PUNTIFI1`, `PUNTIFI2`, `PUNTIFI3`, `PUNTIFI4`, `PUNTIFI5`, `PUNTIFI6`, `PUNTIFI7`, `PUNTIFI8`, `PUNTIFI10`, `PUNTIFI12`, `PUNTIFI13`, `VOTOUSL` | string (mixed numeric codes + `non_applicabile`), except `SALUTE` (no structural missing) | — | the 21 AVQ variables, assigned in one block from a single hot-deck donor (§I.3) |
| `donor_id`° | string, dictionary-encoded | — | donor identity stable across runs (`annata:riga`); **absent from the public regime** |

**Ring 3 — fine allocation (public, except `via`/`civico`; coordinates randomised).**

| column | type | classes | meaning |
|---|---|---|---|
| `sezione` | string (12-digit code) | — | census section (`SEZ21_ID`, 2021 bases) |
| `eta_anni` | int | 0–100 | exact age in years |
| `lon`, `lat` | float, EPSG:4258 | — | address coordinates; **in the public regime, a random point within the census section**, seeded on the municipality code |
| `via`° | string | — | ANNCSU odonym; `persona`/`narrativo` only |
| `civico`° | string | — | civic number + suffix (`12`, `19A`); `narrativo` only, and only on explicit request (§V.1) |
| `indirizzo_fonte` | categorical | 3 | `sezione` / `zona` / `convivenza`, address provenance; |
| `uid`° | string | — | individual key; **absent from the public regime**, present in the complete population and joined on by ring 4 and the `persona`/`narrativo` regimes |

**Ring 4 — household (separate file, not in `pop.parquet`).**

| column | type | meaning |
|---|---|---|
| `id_nucleo` | string | household identifier, `nuclei_{comune}.csv` |
| `ruolo` | categorical | role within the household |

Joined to the population on `uid`; never written into the population
file itself (§II.4).

**Derived layer (° — `persona`/`narrativo` only, never stored).**

| column | type | conditioned on | source |
|---|---|---|---|
| `nome`°, `cognome`° | string | sex, background, parents' origin, country | municipal registers, per-country repertoires |
| `titolo_studio`° (detailed) | string | education, sex, cohort | census 2011 title tree, ordered by CLAIST |
| `settore`°, `posizione`° | categorical | sex, municipality | census 2011, drawn jointly |

These four are deterministic functions of `uid` and the attributes
already generated; they are computed on demand and never written to
`pop.parquet` or the bundle (§I.6, §I.7).

---

### A.3 The source register


`fonti/registro.yaml`

**ISTAT SDMX (11 tables, CC-BY-4.0, `archiviazione: locale`, ~4 queries/min).**

| id | universe | temporal reference | feeds |
|---|---|---|---|
| `istat_anag_sesso_eta_statociv` | population register, sex × age × marital status | 1 January year N | ring 1, hard margin (block `c1`) |
| `istat_cens_sesso_eta_cittadinanza` | permanent census, sex × age × citizenship | 31 December year N−1 | ring 1, soft block; zone-table audit (Z1/Z2) |
| `istat_cens_stranieri_paesi` | permanent census, foreign residents by country, municipal margin | 31 December year N−1 | ring 2 (`paese`, `area`), tier 0 |
| *(8 further permanent-census tables — istruzione, condizione, background, origine_genitori, cittadinanza × background, and others of `c2`–`c10`)* | permanent census | 31 December year N−1 | ring 1, soft blocks — |

**Census sections / Basi Territoriali (CC-BY-4.0).**

| id | universe | temporal reference | feeds |
|---|---|---|---|
| `istat_sezioni_2023` | census-section counts, 138 columns, 135,725 sections | 2023 (geometry 2021) | ring 3 (`sezione`, `eta_anni`), ring 1 zone tables |
| `istat_sezioni_shp` | census-section geometry, per region | 2021 | ring 3 (coordinates pre-randomisation), viewer |
| `istat_sezioni_2023_tracciato` | section-file record layout / decode table | 2023 | decoding of `istat_sezioni_2023` |—

**ANNCSU.**

| id | universe | temporal reference | licence | feeds |
|---|---|---|---|---|
| `anncsu_indirizzario` | georeferenced civic addresses, national register | current | high-value dataset, Reg. (EU) 2023/138 | ring 3 (`via`°, `civico`°, coordinates pre-randomisation) |

**AVQ (3, one derived; licence CC-BY-4.0 inferred from the portal).**

| id | universe | temporal reference | feeds |
|---|---|---|---|
| `avq_microdati` | individual respondents, *Aspetti della vita quotidiana*, public-use; pools Emilia-Romagna 4,629 / Lombardia 8,111 | 2023–2024 (2022 acquired, excluded for lacking `CRONI`) | ring 2, the 21 AVQ variables and `donor_id` |
| `avq_tracciato_2024` | AVQ record layout / decode table | 2024 | decoding of `avq_microdati` |
| `avq_medie_nazionali` (derived, `derivato_da: avq_microdati`) | national weighted means of the AVQ battery | 2024 | viewer only, not a population column |

**Municipal open data (6 portals) and 1 register extract.**

| id | issuing body | universe | temporal reference | licence | feeds |
|---|---|---|---|---|---|
| `bologna_cittadinanza_zone` | Comune di Bologna | residents by citizenship, statistical zone | — | CC-BY-4.0 | ring 2/3, tier 2, zone–quartiere hierarchy |
| `brescia_cittadinanza_quartieri` | Comune di Brescia | residents by citizenship, quartiere | — | CC-BY-4.0 | ring 2, tier 1 |
| `forli_cittadinanza_quartieri` | Comune di Forlì | residents by citizenship, sub-quartiere | 2021 | CC-BY-4.0 (presumed, §II.1) | ring 2, tier 1 |
| `ravenna_cittadinanza_aree` | Comune di Ravenna | residents by citizenship, area | re-fetched 2026-08-11 | public domain | ring 2, tier 1 |
| `reggio_cittadinanza_circoscrizioni` | Comune di Reggio nell'Emilia | residents by citizenship, circoscrizione | 2013 | CC-BY | ring 2, tier 1 |
| `modena_nomi_residenti` | Comune di Modena (regional portal, WFS) | stock of first names by sex | 2012–2024 | CC-BY-4.0 | ring D (`nome`°) |
| `parma_microdati_residenti` | Comune di Parma | full population-register extract, one row per resident, 202,111 rows | 1 January 2025 | CC-BY-4.0 (registered, fingerprinted, not mirrored) | ring 2 (`paese`/`area`, tier 3); external validation, ring III |

**ISTAT census 2011 and CLAIST (CC-BY-4.0).**

| id | universe | temporal reference | feeds |
|---|---|---|---|
| `cens2011_caratt_attl` | occupied residents, 14 dimensions | 2011 | ring D (`settore`°, `posizione`°) |
| `cens2011_titolo_studio` | education-title frequencies, 458 modalities, 399 leaves | 2011 | ring D (`titolo_studio`°) |
| `claist_2026` | education-pathway classification and historicised ordering | 2026 | ring D (`titolo_studio`° ordering) |

**Onomastic repertoires (7; `modena_nomi_residenti` above is one of them).**

| id | issuing body | universe | licence | feeds |
|---|---|---|---|---|
| `firenze_cognomi_2013` | Comune di Firenze | resident surnames, 375,371 residents, 66,353 distinct | CC-BY-4.0 | ring D (`cognome`°) |
| `firenze_cognomi_2012` | Comune di Firenze | resident surnames (stability check only, r = 0.9985) | CC-BY-4.0 | ring D, verification only |
| `popular_names_nomi` | Wikipedia aggregation | first names, 2,370 from 106 countries | CC0 | ring D (`nome`°, foreign) |
| `popular_names_cognomi` | Wikipedia aggregation | surnames, 2,278 from 75 countries | CC0 | ring D (`cognome`°, foreign) |
| `cognomi_wiki_MA_ARAB` | Wikipedia (MediaWiki category) | Maghrebi/Arabic surname list, 65 entries | CC-BY-SA | ring D, specific communities |
| `cognomi_wiki_NG_YORUBA` | Wikipedia (MediaWiki category) | Yoruba surname list, 107 entries | CC-BY-SA | ring D, specific communities |

**Civil unions and the household repertoire.**

| id | issuing body | universe | temporal reference | licence | feeds |
|---|---|---|---|---|---|
| `istat_unioni_civili_2023` | ISTAT | exhaustive survey of civil unions | 2023 | CC-BY-4.0 | ring 4 |
| `repertorio_nuclei_v1` (derived, `derivato_da: avq_microdati`) | GSP | household-configuration repertoire | — | CC-BY-4.0 (inherited) | ring 4 |

**EU-SILC (2, registered for exploration only, not used).**

| id | licence | feeds |
|---|---|---|
| *EU-SILC public-use file 1* | non-open, no redistribution | none — documents an undecided item, §III.5 |
| *EU-SILC public-use file 2* | non-open, no redistribution | none | 

**Registered and not used.**

| id | universe | reason |
|---|---|---|
| `istat_cens_posizione_famiglia` | position in the household, from the census | examined for ring 4, rejected in favour of section-level household counts (§I.5) |

Deliberately outside the registry: sources consulted and not used.

---

### A.4 The constraint set

The blocks of a K9C and a K6C constraint set, with arity, cell count
and universe — the template that §I.2 describes in prose. Generated
from `cs_<livello>.json`. 
**The joint attribute set (K9C).**

| attribute | classes | values |
|---|---|---|
| `zona` | 4–33 | the municipality's declared articulation |
| `sesso` | 2 | M, F |
| `eta` | 8 | 0–8, 9–14, 15–24, 25–34, 35–49, 50–64, 65–74, 75+ |
| `stato_civile` | 4 | never married, married/civil union, divorced, widowed |
| `cittadinanza` | 2 | Italian, foreign |
| `istruzione` | 6 | no title … postgraduate |
| `condizione` | 7 | employed … not applicable (under 15) |
| `background` | 6 | native Italian … foreign immigrant |
| `origine_genitori` | 5 | both Italian … not applicable |

State-space size: |X| = 161,280 × n_zone (161,280 = 2 × 8 × 4 × 2 × 6 ×
7 × 6 × 5, the product of the eight non-zone attributes). K6C drops
`zona`, `background` and `origine_genitori`, leaving |X| = 5,376
(2 × 8 × 4 × 2 × 6 × 7), municipality-independent since K6C carries no
zone dimension — confirmed on the Mantova test fit (m = 263
constraints, MRE 3.4·10⁻⁴, 0.17 s).

**Block census.**

| level | blocks | complete (α sums to 1) | partial | municipalities |
|---|---|---|---|---|
| K9C | 16 | 11 | 5 | the nine provincial capitals + Brescia |
| K6C | 6 (named `A`–`F` in the `cs_build` audit) | 4 (`A`, `B`, `E`, `F`) | 2 (`C`, `D`) | Ferrara, Castenaso |

K9C's sixteen blocks are ten municipal blocks `c1`–`c10` (from
`build_constraints.py`: `c1` the register hard margin, `c2`–`c10` the
soft census blocks) plus the zone blocks from `build_zona_tables.py` —
five documented in production (Z1 age×sex by zone, Z2 macro-age×sex×
citizenship by zone, Z3 education by zone at 5 levels, Z4 employed
condition by zone, Z6 migratory background by zone; no Z5 appears in
the working notes).

The five K9C partial blocks are the out-of-universe complements:

| block | free cells | complement (closes to α = 1 with) |
|---|---|---|
| `eta × istruzione` | 1 cell: (0–8, `nessun_titolo`) | `sesso × eta × istruzione` (0.0685 + 0.9315 = 1) |
| `eta × condizione` | 2 cells: (0–8, `non_applicabile`), (9–14, `non_applicabile`) | the corresponding complete condition block (`S_condizione_under15`) |
| `zona × sesso × eta × condizione` | employed 15–64 only | not closed within the template — the geography of non-employment is unconstrained by any observed datum (§I.4) |

K6C's `C` (istruzione) and `D` (condizione) are the same reading at
municipal level, without the zone axis: on the Mantova test, `C` =
0.939 with complement `S_istruzione_under9` = 0.061, `D` = 0.888 with
complement `S_condizione_under15` = 0.112.

**Zero-cell accounting (both levels).**

| provenance | count | where |
|---|---|---|
| impossible age × education pairs | 8 | identical in every municipality, both levels |
| impossible age × condition pairs | 18 | identical in every municipality, both levels |
| citizenship × background, structurally excluded | 6 | identical in every K9C municipality |
| contingent (observed) zeros, sex × age × marital status | 0–6, municipality-dependent | none in Bologna; two in most municipalities (young widowed of both sexes); six in Castenaso |

The first two rows (26 pairs total) are not currently enforced by any
block — ISTAT does not publish that cross — and three of 970,000
individuals fall into them in the released populations (3·10⁻⁶); adding
them as α = 0 exclusions is a queued repair (§II of the pipeline
backlog, `riferimento` §14.2).

---
