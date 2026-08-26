# Part I — Architecture: the four rings
## Version 1 — §I.0–I.7 (26 August 2026)

> `GSP_popolazioni_full_riferimento_v24` is cited throughout this part
> as *riferimento*.

---

### I.0 The pipeline, as run

Before principles, the machine. This section walks the chain exactly as
it executes for one municipality, with the real commands; everything
after it — the design principles of §I.1, the rings of §I.2–I.5 —
attaches to a step the reader has already seen run. The walkthrough of
every script against two municipalities added from scratch, with real
outputs and the findings it produced, is in
`note/collaudo_acquisizione_v0.2.md` (in Italian, as the project's
working notes are); this section is its distillation.
Terms are used here before they are defined — *ring* for the four
stages that give every attribute its place (§I.2–I.5), *K6C/K9C* for
the two sizes of the joint model, without and with the zone coordinate
(§I.2) — because the reader who sees the chain run once will attach
the definitions to steps already seen, not the other way around. On
first reading, the command names carry enough: fetch, sections, zones,
constraints, fit, then the three enrichment steps.

![The pipeline as run: three doors feeding one chain, ring 1 producing the population and rings 2–4 enriching it, with the publication regimes as the single exit. Source: `note/figure/fig_I0_pipeline.dot`.](figure/fig_I0_pipeline.pdf)

**Three doors.** Every municipality receives data through three doors at
three granularities:

1. **SDMX → the municipality as a whole.** Eleven ISTAT tables —
   register and permanent census — downloaded per municipality. Their
   row counts measure *structure, not size*: Milano (1.4 M residents)
   and Mantova (49 k) produce the same 819 rows of education × age,
   because the grid is fixed and only the counts change. Download time
   is dominated by the API's rate limit (~5 queries/minute, enforced
   globally by `gsp.istat.sdmx`; violations lead to multi-day IP
   blocks), not by bytes.
2. **Territorial bases → census sections.** One workbook *per region*,
   one row per section, 138 columns (population by five-year class and
   sex, citizenship by three macro-classes, education at five levels,
   employment, migratory background, household sizes PF3–PF8). This is
   where a metropolis outweighs a town — Milano has 6,059 sections,
   Mantova 574 — and where the sub-municipal articulation lives, as the
   `COM_ASC*` columns.
3. **Municipal open data → what only the municipality publishes.**
   Citizenship by country at sub-municipal level, chiefly. This door is
   optional by design: the *tier* system of §I.3 degrades gracefully to
   tier 0 (country conditioned on sex and geography from the census
   margin alone) when it is closed, and tier 0 was exercised end-to-end
   on both test municipalities.

**The chain, per municipality.** With the region's one-off files in
place (door 2, plus the ANNCSU address extraction and the regional AVQ
pool), a new municipality is one entry in the `COMUNI` registry of
`gsp.common` — name, slug, region, and the declared zone level or the
declared absence of one — followed by:

```
python scripts/acquisizione/fetch_comune.py 020030          # door 1: 11 tables
python scripts/vincoli/build_sezioni.py     020030          # door 2: sections, ASC check
python scripts/vincoli/build_zona_tables.py 015146          # only if articulated
python scripts/vincoli/build_constraints.py 020030 --anno 2024
python scripts/vincoli/cs_build.py  020030 --anno 2024 --livello K6C
python scripts/fit/fit_cs.py        020030 --anno 2024 --livello K6C --pool 65000
python scripts/attributi/assign_avq.py 020030 --anno 2024 --pop-file popolazione_K6C.csv
python scripts/attributi/enrich.py     020030 --anno 2024 --pop-file popolazione_K6C_avq.csv
python scripts/attributi/assign_nucleo.py 020030 --anno 2024
```

`rigenera.sh` runs this chain for the whole fleet — eleven
municipalities, 44 output files, 33 minutes on one workstation,
byte-identical across runs (§III.2).

Two of these steps deserve a word here because their division of labour
is not guessable from the names. `build_constraints` is the *municipal
preparer*: it reads the eleven decoded tables, verifies year coverage
per table before building anything (a missing mandatory table is a
fatal error; a missing optional one is a declared skip), and writes the
municipal constraint blocks `c1..c10` together with a manifest and a
consistency report. `cs_build` is the *assembler*: it takes those
blocks, adds the zone blocks where the municipality is articulated,
applies the declared zeros and the ε floor, audits the shared margins,
and emits the constraint set the solver reads. The two-stage relay
means the municipal preparation is inspectable on its own — the
`report.md` each run writes is where the register–census identity of
§I.2 was first noticed.

**What the test run established.** Mantova (K6C, no articulation) and
Milano (K9C, nine municipi) were added from scratch as test cases —
they are not part of the released bundle (§III.5). Mantova's constraint
set has m = 263 constraints on |X| = 5,376 states and fits exactly in
0.17 s at MRE 3.4·10⁻⁴; Milano's has m = 1,037 on |X| = 1,451,520 and
fits exactly in 54 s at MRE 4.2·10⁻⁴ — the same error as the fleet,
because for the solver what counts is the number of zones, not of
residents: Milano, with nine municipi, is a *smaller* problem than
Parma with thirteen quartieri. The chain needed nothing beyond the
registry entry; the two limits it surfaced (a solver-repository
dependency resolved by filesystem discovery, and address coverage
depending on each municipality's ANNCSU georeferencing) are declared in
the front matter and §I.4 respectively.



### I.1 Design principles

![The four rings and the derived layer: what each adds, from which source, by which method, and what is real in it. Source: `note figure/fig_I1_anelli.dot`.](figure/fig_I1_anelli.pdf)

*Four principles run through the whole design; they are worth stating before the mechanism they govern.*

*Every attribute has a declared place*: education lives in the joint
model, because its association with age and citizenship must hold under
simultaneous constraints; the sector × position pair is derived
downstream, conditioned on sex and municipality, because that is where
the measurement put it — a total-variation distance between conditional
and marginal compositions, defined below.

An attribute lives either in the joint model (ring 1), where the solver
generates it under simultaneous constraints, or in a downstream
derivation, conditioned on what is already there. The choice is not a
matter of taste, it is a measurement: for a candidate attribute X and
each available conditioning S, the total-variation distance
d(S) = TVD(P(X | S), P(X)) — the share of mass one would have to move,
readable without a scale ("one card in five would be wrong"). Large d on
a conditioning available downstream → derive; large d only on a
conditioning that is not available downstream, typically fine geography →
joint model; small everywhere → assign unconditionally. When two derived
variables are involved, a second measurement decides whether they are
drawn separately or jointly — TVD(P(X, Y | S), P(X | S) · P(Y | S)) — and
here a secondary criterion supplements the number: at equal distance,
preserve the structure that makes an error recognisable. A failed joint
produces a manager in agriculture, which anyone notices; a failed
conditioning produces plausible individuals in slightly wrong
proportions, which nobody does. It is the same reason the AVQ hot-deck
copies whole vectors (§I.3). The criterion is implemented as a
self-contained library (`gsp.tvd`: distance, per-conditioning profiles,
support-partition checks); it knows nothing of municipalities or
populations, and it refuses to measure across mismatched supports — on
real census tables, a distance computed over different supports produced
plausible and meaningless values five times in two days before that
refusal was built in.

The criterion has already reversed one decision. The economic sector
seemed to belong in the joint model, conditioned on sex — the natural
pairing. Measured, the pairing is the wrong one: on the ATECO
composition, education dominates (TVD 0.149–0.512 across municipalities,
median 0.346), sex moves half as much (median 0.153), and age sits below
both. Education, however, is unusable as a conditioner at municipal
level — the census does not publish the sector × title cross outside
agriculture — while putting the sector in the state space would have
cost a much larger support and a conditioning on the least informative
of the three variables. The measurement settled it: the pair
sector × position is drawn downstream, jointly (the joint-vs-product
distance is 0.138–0.166 across five territories — structure, not noise),
conditioned on sex and municipality, with education's absence declared
as a limit rather than silently absorbed (§I.6, and the work module's
own documentation).

*Every metric is normalised against its null*. A raw error, a raw
distance, a raw correlation scales with the geometry of what it
measures — how many cells, how small the sections, how fine the
partition — before it says anything about quality. One example stands
for all: the municipality with the "worst" raw constraint error in this
report (16 %) is a town of sixteen thousand whose sampling floor — the
error a perfect sampler would show, given its cell sizes — is 24 %;
the municipality with the finest zoning has a floor of 3,000 % — its
constraint set contains many cells whose expected count is a fraction
of an individual, and on a cell that expects 0.04 people, finding one
is a relative error of 2,400 % while being off by one person. At that
point the relative scale has stopped measuring the fit and started
measuring the cell sizes. The comparison that still works is the
z-score: each cell's deviation divided by the fluctuation a perfect
sampler would show on that cell — so every cell is judged against its
own floor, and cells of any size become comparable. On that scale the
finest-zoned municipality is unremarkable (§III.3). Comparing raw numbers across configurations compares
their geometry, not their quality. Every table in Part III therefore
carries the null beside the observation, and the rule has retired at
least four published-in-note numbers in this project's history (§III.6).

*The population is read-only.* Once generated, a population file is never
modified: derived attributes are computed at consumption time from the
`uid`, ring 4 writes its columns to a separate file joined on `uid`, and
every fix that would touch the file is instead queued for a full
regeneration cycle. The premise makes the regression test trivial — the
file must never change — and makes `diff` the universal instrument.

*Nothing is silently corrected.* When a claim in a working note turns out
to be wrong, the text is not fixed: the original stays where it was, and
a dated annotation beside it says what the correct number is and why the
first one was wrong. Predictions are written down before the measurement
runs, so that a falsified prediction cannot be quietly rephrased as an
expected result — this report contains two, both falsified, both kept
(§III.6). And code is held to the same standard as prose: a refactoring
is accepted only when the regenerated populations are byte-identical to
the archived ones, so that "nothing changed" is a measurement, not an
assurance (§III.2). The cost is a paper trail of one's own errors; the
return is that every number still standing has survived something.

### I.2 Ring 1 — the joint model

Ring 1 produces, for each municipality, the joint distribution of up to
nine demographic attributes — zone, sex, age (eight bins), marital status,
citizenship (Italian/foreign), education (six classes), occupational
condition (seven), migratory background (six), parents' origin (five) —
as a maximum-entropy distribution over the discrete support X subject to
the census constraint set, and then samples N individuals from it. 

| attribute | classes | values |
|---|---|---|
| `zona` | 4–33 | the municipality's declared articulation (statistical zones, quartieri, circoscrizioni, aree) |
| `sesso` | 2 | M, F |
| `eta` | 8 | 0–8, 9–14, 15–24, 25–34, 35–49, 50–64, 65–74, 75+ |
| `stato_civile` | 4 | never married, married or in civil union, divorced, widowed |
| `cittadinanza` | 2 | Italian, foreign |
| `istruzione` | 6 | no title, primary, lower secondary, upper secondary diploma, tertiary (incl. ITS), postgraduate |
| `condizione` | 7 | employed, seeking work, student, homemaker, pension recipient, other, not applicable (under 15) |
| `background` | 6 | native Italian; returned Italian; naturalised, born in Italy; naturalised immigrant; foreign, born in Italy; foreign immigrant |
| `origine_genitori` | 5 | both Italian; Italian mother, foreign father; foreign mother, Italian father; both foreign; not applicable |

(Class boundaries follow the census: *upper secondary* is the five-year
diploma of any track (liceo, tecnico, professionale); *tertiary/ITS*
pools bachelor's, master's degrees and ITS diplomas without
distinguishing them; *postgraduate* includes doctorates and
specialisation degrees as a class, although the detailed-title rendering
(§I.6) can only produce master's-level titles, its 2011 source having no
doctoral entries — a declared limit of the derived layer, not of the
class. Three- and four-year vocational qualifications are pooled by the census
itself into the *upper secondary* class, together with IFTS — the
source's aggregation, verified on the decoded table's own label
(`USE_IF`: "diploma di istruzione secondaria di II grado o di qualifica
professionale, compresi IFTS").





The
method — exact solution of the dual where |X| allows, persistent
contrastive divergence where it does not — is the subject of
arXiv:2603.27312 and is not repeated here; what this report documents is
the *configuration*: what the constraints are, where they come from
(Part II), and what the fit achieves on the eleven municipalities
(Part III).

The constraint set is a *template*, written once per level and applied
identically to every municipality at that level. Two levels are in
production. **K9C** — nine constrained attributes, the full table above —
applies where the municipality has a declared sub-municipal articulation
and the migratory-background tables to populate it: the nine provincial
capitals and Brescia. **K6C** — six attributes: sex, age, marital status,
citizenship, education, condition — applies where it does not (Ferrara
and Castenaso): no `zona`, and no `background` / `origine_genitori`,
whose census tables have no sub-municipal counterpart there. The level is
a property of the available sources, not of the pipeline, and the viewer
inherits it (a K6C municipality shows six filterable attributes, and its
census-reference coverage has a different denominator — 26 of 96 pairs
against 67 of 333, which is why coverage *counts* are never compared
across levels, only shares; §IV.1).

At K9C the template has sixteen blocks — sub-tables of the census each
constraining a small set of attributes jointly — of which eleven are
complete, their masses summing to one, and five are partial **[n]**
riferimento §14.1.


A partial block's unlisted cells are *free*, not forbidden; the
distinction matters because its opposite also occurs: every constraint
set carries explicit zeros, of three provenances. Twenty-six are
*imposed by construction*, identically in every municipality at both
levels: the logically impossible pairs of age × education (8) and
age × occupational condition (18). Six more appear identically in every K9C municipality in
citizenship × background: combinations the variables' definitions
exclude — an Italian citizen cannot carry a *foreign* background, a
foreign citizen cannot carry an Italian or naturalised one. They are as
structural as the twenty-six, and differ only in provenance: the census
table delivers them as observed zeros, `cs_build` does not need to
impose them. The rest are the only *contingent* zeros — demographically
observed, in sex × age × marital status, varying with the municipality
as data should: none in Bologna, where even widowed 15-to-24-year-olds
exist (two of them costing the fit its largest z-score, §III.3a); two in
most municipalities — the widowed young of both sexes; six in Castenaso,
whose sixteen thousand residents leave more demographic cells empty.
 Mechanically all three kinds are the same
object — a constraint with target zero, whose mass the solver
suppresses — and the generated populations honour them exactly: no zero
cell is realised in any municipality (§III.3), no impossible combination
in 1,814,317 individuals (§III.2). Absent and zero are opposites for maximum entropy — unconstrained versus
forbidden. An unconstrained cell receives the *most* mass compatible
with the remaining constraints, which is the principle itself at work:
where nothing is imposed, the distribution spreads as evenly as it can.
A zero-constrained cell receives none. There is no middle ground, so
misclassifying a cell does not produce a small error but the largest
possible one on that cell — in either direction. Read a missing row as
"no constraint" when it is an observed zero, and the model manufactures
widowed teenagers in quantity; read it as "zero" when the cell is merely
outside the table's universe, and education becomes forbidden for
children under nine — for whom the census publishes nothing, but who
exist and carry `nessun_titolo` — and the population is distorted or
cannot be generated at all. The source offers no help: a downloaded
table shows the same missing value for both, and the difference lives
only in the table's declared universe. Translating tables into
constraints therefore requires knowing, cell by cell, *why* a value is
missing — reading the universe, not just the numbers — and doing it
implicitly is the characteristic error of the exercise **[n]**
riferimento §14.2. The partial blocks encode exactly this reading:
out-of-universe cells stay free, observed zeros enter at α = 0.

Readers from the population-synthesis literature will look here for the
*zero-cell problem* — the impossibility, for seed-based methods like IPF,
of restoring mass to a combination the sample seed happens to miss. The
problem does not arise in this construction, because there is no seed:
the maximum-entropy distribution is determined by the constraints alone,
and an unconstrained cell receives the most even mass compatible with
them rather than inheriting a sampling accident. What the literature
treats as one pathological category is here three deliberate ones —
observed zero (forbidden by a constraint), impossible pair (excluded from
the support, α = 0), and uncovered cell (free) — and the residue of the
classical problem survives only as the sampling floor on small cells
(§III.3).

Two margins have distinct roles, because they describe different
instants: the population-register table (1 January of year N) fixes the
municipal totals *exactly* — the hard margin — while the census tables
(31 December of year N−1) enter as soft constraints. 
A word on what *hard* and *soft* mean here, because the natural reading
is wrong. They do not rank two competing measurements by trust. Since
2018 the official resident population is produced *by* the permanent
census, so the register table and the census tables publish the same
demographic base: on sex × single year of age the two flows agree
exactly — 2,821 cells across fourteen municipalities, zero discrepant,
maximum absolute difference 0 **[m]** (§III.3). The identity extends down one more layer: the census-section tables,
aggregated over a municipality, reproduce the same base — at Brescia,
the thirty-two five-year cells (sixteen classes × two sexes) summed
from 6,000-odd sections match the register with zero discrepancy
**[m]**. Register, municipal census and section tables are one dataset
published at three granularities. The few cells present
in one flow only are empty ones in the tail of the age distribution
(a 99-year-old male in a town of 16,000), not disagreements.

What distinguishes the two families is therefore not accuracy but
*extension*: the register table extends the common base along marital
status — the one axis no census table carries — while the census tables
extend it along citizenship, education, occupational condition and
migratory background. The register block enters as exact counts; the
census blocks enter as conditional distributions applied to those
counts (`share × count`, per group), which is why the demographic
margins remain exact by construction rather than by reconciliation.
Two costs come with the conditional form and are declared: census
quotas defined on wide age classes (9–24, 15–24) are applied to finer
groups under an assumption of homogeneity within the class, and census
values are rounded, with a per-table rounding sigma recorded in the
constraint-set manifest.

The conditional form is not a device for the census tables alone: it is
*the* architectural rule, applied three times. Levels come from the
spine; everything else contributes form. The census blocks contribute
the socio-economic form (`share × count` per demographic group, above);
the zone blocks contribute the geographic form — `P(zone | group) ×
municipal counts`, with IPF closing the double margin — each at the
resolution its section columns carry: five-year classes for age, three
macro-classes for citizenship, five education levels against the
population's six, and the employed side only for occupational condition
(the geography of unemployment is constrained by no observed datum,
§I.4); and the country of citizenship repeats the same pattern
downstream, in ring 3's tier system (§I.3). One principle, three
applications — which is also why the zone-margin audits printed by
`cs_build` (`Z1 vs A: max|diff| = 0.000000`) are algebraic identities
verifying the implementation, not facts about the sources; the fact
about the sources is the register–census identity above.

At the release tag every municipality was solved *exactly*: the eleven
fits converge with MRE between 2.4·10⁻⁴ and 5.0·10⁻⁴, in 0.17 s to
182 s **[m]** (generation logs at the tag). No municipality in the
fleet required PCD, which the solver provides for state spaces this
release does not contain — Brescia at K10C, or the 88-NIL fit of
Milano registered as an experiment (§III.5). Two regularities are
worth noting, because they are counter-intuitive: fitting time follows
|X| = 161,280 × zones and not population — Brescia, 198k residents in
33 quartieri, takes 182 s against Bologna's 79 s for 390k residents in
18 zones — and the fit error does not follow either, staying inside a
narrow band across two orders of magnitude of population, which makes
it a property of the stopping criterion rather than of the problem's
difficulty.

### I.3 Ring 2 — donated attributes and the country of citizenship

The population's attitudinal and health layer — twenty-three AVQ
variables: self-rated health, chronic conditions, smoking, BMI, the
mental-health index, environmental satisfaction, interpersonal trust,
and the institutional-trust battery on a 0–10 scale — is not modelled.
It is *donated*: each synthetic individual receives the complete
response vector of one respondent of ISTAT's *Aspetti della vita
quotidiana* public-use microdata (pools: Emilia-Romagna 4,629 donors,
Lombardy 8,111; survey years 2023–24 stacked, weights renormalised
within year — the 2022 wave is declared in the acquisition list but
excluded, because it lacks the chronic-conditions item with no
equivalent: an absent variable excludes the wave rather than entering as
a silent gap), drawn from the conditioning cell sex × macro-age × education-4
with a declared hierarchical collapse when a cell holds fewer than twenty
donors. 


Copying the whole vector rather than sampling variable by variable
is the decision that preserves the inter-variable correlations by
construction — and the same recognisability criterion as §I.1: a
mis-sampled joint produces visibly impossible respondents, a mis-sampled
marginal produces invisible bias **[n]** riferimento §2.2.

The price is stated, measured, and carried through every product. The
donated vector holds no geography below the region (assumption 6): if a
neighbourhood shows lower institutional trust, it is because people of
the groups that everywhere express lower trust live there in greater
numbers — composition — not because the neighbourhood adds anything of
its own, which the data cannot contain. The viewer says this on every
spatially filtered panel (§IV.1). The honest sample size behind any AVQ mean is 
not n but Kish's
effective size on the variable's own universe. If each donor i is
reused w_i times in the population, the synthetic sample of Σw_i
individuals is worth
n_eff = (Σ w_i)² / Σ w_i² independent respondents —the count the weights would give if they were all equal, and less than
the number of distinct donors whenever they are not — which is why
counting distinct donors, the obvious shortcut, is not enough. Two limits make it readable:
with every donor used the same number of times, n_eff is exactly the
number of donors; with one donor carrying most of the population,
n_eff approaches one. Computed per variable, on the universe that
variable actually has — the trust battery is asked of adults, the
school questions of a narrower group — the confidence bands it implies
are 2 to 20 times wider than the naive ones, the factor growing with
the municipality's population and varying with the universe (§III.3b). The hierarchical
collapse of the conditioning cell touches 1.5–3.1 % of individuals — but
not at random: the cells that fall below the twenty-donor threshold are
all low-education cells, so the collapse concentrates precisely where
educational conditioning would matter **[n]** riferimento §13.2. The
donor's identity survives as an equivalence class — the donated tuple
*is* the signature — which is what the viewer exposes on every
individual card and what §III.3b counts.

Three counts appear in this report and they are not in conflict:
twenty-three variables are donated and all twenty-three form the donor
signature; the viewer's institutional-trust panel displays the fifteen
of them that share a 0–10 trust scale (the two health-service
judgements, the armed forces, eleven institutions of the PUNTIFI
battery and the local-health-authority rating), leaving out health,
chronic conditions, smoking, mental health, environment, BMI and
weight — donated all the same, and present in the record.

The second half of ring 2 is the country of citizenship. The census
gives the municipal margin — country × sex — and, per census section,
the count of foreign residents; where a municipality publishes a
sub-municipal table of residents by country, that table is register
data of a different date, and its *levels* are incompatible with the
census by amounts that matter (Brescia's register counts 40,090
foreigners against 37,478 census). The construction therefore uses the local source's *shape* only — the
third application of the rule stated in §I.2: levels from the base,
form from the source that has it. It seeds an iterative proportional
fit whose two margins are both census — the municipal country × sex table,
and the census count of foreigners of each geography — so the system is
consistent by construction and converges in 9–88 iterations to ~10⁻¹¹
**[n]** riferimento §6. Coverage is complete for the same reason: a
section's weight for foreigners is proportional to its census foreign
count, so no foreigner can land where the census counts none.

The result is a *tier* per municipality — the resolution of the best
available local source, a property of the municipality's open data, not
of the pipeline: tier 0, census only, seed = the national composition
replicated (five municipalities, and every new one); tier 1–2 where a
neighbourhood- or zone-level table exists (Brescia, Forlì, Ravenna,
Reggio; Bologna); tier 3, section level, in Parma, from the municipal
register extract. Tier 0 is the default branch and was commissioned as
such: on Modena it reproduces the no-tier behaviour to a total-variation
distance of 0.0023 — and that cross-check between two branches that must
agree surfaced two latent classification bugs that no single-branch test
had caught (§I.1) **[n]** riferimento §6. Measured against its null (two
independent permutations), the geographic conditional carries 2.1–2.6
times the mass that chance would move at neighbourhood level, in every
municipality that has one — and a poor but resolved source is worth a
rich one: Brescia's nineteen countries without sex achieve 2.08 against
2.57 for Bologna's one hundred fifty-five with sex. For a future
municipality, a truncated country × neighbourhood table is enough
**[n]** riferimento §6.
The default branch is not a theoretical fallback: both municipalities
added during testing ran at tier 0 end to end, including Milano, where
the branch had never been exercised on an *articulated* municipality —
171 countries × 2 sexes × 9 municipi, IPF converging in one iteration
to 5·10⁻¹⁶.

### I.4 Ring 3 — sub-municipal placement

This is the ring where the pipeline goes *below* the level at which its
constraints are defined. Rings 1 and 2 work where tables exist; ring 3
places individuals inside a zone, at a census section, a single year of
age, and an address — none of which the constraint set knows about.
Everything here is therefore allocation, not estimation, and that is
why the assumptions accumulate in this section rather than elsewhere.

*Section.* Within a zone, individuals are allocated to census sections
by *largest remainder* rather than by multinomial draw: each section
receives the integer part of its quota, and the remaining places go to
the sections with the largest fractional remainders. The method is
deterministic and bounded — at most one individual of error per
allocation — and the residue that remains comes from allocating within
each demographic group separately, so that the ±1 of several groups
accumulate on a section. The measured mean absolute error per section
is 0.72–1.57 individuals against ≈ 9.6 for a multinomial draw **[n]**
riferimento §5, on sections averaging 66–175 residents, with section
totals matching the census exactly (§III.3).

The zone blocks of ring 1 already carry geography for age, citizenship,
education and employment, each at the resolution its section columns
have (§I.2). Assumption (8) concerns the step *below* that one — zone
to section — where no table conditions education, occupational
condition or migratory background at all: within a zone, those three
are spread independently of the section, given sex, age-3 and
citizenship. It is a concession of the ring, not a claim about the
world, and its cost is measured twice over. The compositional analysis
that motivated the ring found 80–98 % of the compositional signal
living *below* the zone — which is why placement cannot stop there
**[n]** `nota_segnale_compositivo_v3`; and the M-EM measures, run
against the census's own section-level migratory-background columns,
find a real residual on all eleven municipalities (median net ~0.022
for Italians, ~0.018 for foreigners) — assumption (8) discards
section-level structure that exists. The refinement through the census
EM columns is designed and queued with the next regeneration cycle
(§III.5) **[n]** `nota_background_sezione_v1`.

*Single-year age.* Here, unlike education or condition, the section
*does* have something to say, and the exact age is drawn in two stages:
section → five-year class → single year. The five-year class comes from
the section's own census columns (sixteen five-year counts per sex), so
the age structure of every section is respected at five-year
resolution; where a bin boundary cuts a five-year class, the class is split under
uniformity: the 0–8 bin takes the whole of 0–4 and four fifths of the
5–9 class (ages 5 to 8), the remaining fifth — the nine-year-olds —
going to the 9–14 bin. The single year *within* the class then
follows the municipality's register distribution by single year of age:
this is assumption (9) — below five-year resolution, every section
inherits the municipal shape. The ex-post diagnostic measures both
artefacts of the construction: the seam left at the split classes (mean
residual 2.3–5.7 individuals per section, §III.3), and a systematic
within-bin lean — too few nine-year-olds where the 4/5–1/5 split
operates, and a young lean in the adult bins, ten concordant signs over
two cities, p ≈ 0.002 (§III.4). Both measured, both queued with the
next regeneration cycle (§III.5).

*Address.* A civic number drawn uniformly among the section's ANNCSU
entries (assumption 10), with its coordinates. In production the section
supplies the address directly for ≥ 99.5 % of individuals **[m]** (the
`[3e]` line of every generation log); the residue is sections whose
registered civic numbers cannot be joined — either because the section
has none, or because the ones it has carry no coordinates. In the fleet
it is the first case, and it is distributional, not one of coverage:
Modena has the largest share (0.15 %) while holding *more* civic numbers
than Brescia for fewer residents. Those individuals fall back to the
nearest declared level. One case is handled apart, and declared:
individuals in collective households sit in a fictitious section and
carry *no* address at all, their coordinates being the zone centroid —
an institution is not a home, and inventing a civic number for it would
manufacture exactly the kind of false precision the regime exists to
prevent. The uniformity of the draw is the load-bearing fact of the
disclosure argument (§I.7): every address exists, and the assignment
carries no information about anyone — which is also why the public
regime can randomise the coordinate within the section at zero analytic
cost (§IV.2).

The second case is rare in the fleet and dominant outside it, and was
found by adding a municipality outside it. Address coverage is a
property of each municipality's ANNCSU *georeferencing*: the fleet's
≥ 99.5 % reflects Emilia-Romagna's near-complete coordinate coverage,
while Mantova — added as a test case — has certified 17,009 accesses in
ANNCSU and georeferenced 240 of them (1.4 %) **[m]**,
`collaudo_acquisizione_v0.2`. The addresses exist as text, not as
coordinates, and the spatial join legitimately finds nothing to attach.
The consequences split exactly along the regime boundary: the public
regime is unaffected, since its coordinates are drawn within the census
section, which every individual has; what degrades is the textual
address of the persona and narrative regimes, which falls back to the
zone level. A municipality's ANNCSU completeness is therefore part of
its declared source profile, on the same footing as its open-data tier
(§I.3).


### I.5 Ring 4 — households

Household structure cannot live in the joint model: `|X|` would explode
and the role variable would introduce structural zeros that make the Gibbs
chain reducible. Nor can it be ignored — assumption (11) of the earlier
releases. The resolution, taken with the TVD criterion on the Parma
microdata, is a two-part design whose asymmetry is *measured, not
assumed*: household **size** has geographic structure down to the section
and is therefore constrained by the census size distribution PF3–PF8 per
section (a hard margin: household totals match the census to the unit,
§III.3); internal **composition** has weak structure below the quartiere
and comes from a repertoire of configurations built on the AVQ microdata
(8,443 nuclei, 19,003 components **[m]**; the size-6+ tail from the
Parma microdata, a mixed source, declared), conditioned demographically **[n]** nota_nucleo §6,
riferimento §16.

`assign_nucleo.py` writes `uid, id_nucleo, ruolo` to a separate file — the
population stays read-only — with individuals in collective households
carried with an empty `id_nucleo` rather than dropped. 
These are the same individuals who carry no address in ring 3: the
fictitious sections of §I.4 and the empty `id_nucleo` here identify one
population, those living in collective households — barracks, student
halls, care homes, reception centres — for which neither a civic number
nor a family structure is meaningful. In Milano they are 9,992 people,
0.73 % of the municipality; in Mantova, 34.
The friction of
meeting the size constraint is itself reported (which sections required
truncating the open 6+ class, which betray a collective household)
**[n]** riferimento §16.4, and the headline anomaly — 18–25 % of married individuals not in a
married couple — decomposes cleanly. Three quarters of it is structural:
17.6 % of the married carry a role the repertoire never pairs (13.9 %
are children living with their parents, the rest heads of complex or
non-family arrangements), and these are incoherent by construction. The
pairing itself is accurate: of those in a pairable role, 4.6 % of
partners and 8.8 % of household heads have a spouse who is not married
— together six points of the 23.6 % measured on Modena **[m]**. The
constraint set never required that people marry in pairs, so ring 4
reveals an incoherence already present in the ring-1 population rather
than creating it (§III.3). The rate falls where single-person households are more common, as the
mechanism predicts: 17.7 % in Milano — the lowest measured, below the
fleet's minimum — against 23.0 % in Mantova, whose age structure is
older and whose households are larger. Same-sex couples are absent
because they are absent in the donor data (0 of 4,525 partner pairs), an
inherited limit declared with the civil-union statistics registered for
the next repertoire **[n]** nota_nucleo, assign_nucleo header.

Ring 4 is the youngest ring, and this report freezes it as it stands
rather than as it will be. Three declared immaturities. *Names are still
assigned per individual, not per household* (§I.6): two spouses do not
share a surname, and no onomastic rule links parent to child — the
rendering layer treats each `uid` alone, and household-aware naming is
designed but not built. *The address is per individual* (assumption 11's
residue, §III.4): spouses can carry different civic numbers, and
household-level address assignment is the stated prerequisite of any
building-level work.And *the assembly still produces rare demographic oddities at the
margins* — a handful of married fifteen-year-olds have been observed:
an artefact of the assembly's age conventions, not a demographic claim,
since the register table itself has no married cell below sixteen (§I.2,
the sparsity that encodes legal ages), so the population's own source
excludes what ring 4 produces. Rare enough to survive the current
diagnostics, declared here, on the list for the next repertoire
iteration.
 The
17-to-24 widowed of §I.2 were an observed zero the constraints enforce;
the married fifteen-year-old is the same kind of cell one ring further
out, where no constraint yet reaches.


### I.6 Derived layers — no new information, declared as such

Everything else an individual can carry — the detailed education title
(«diploma di istituto tecnico industriale» rather than «diploma»,
«laurea magistrale in ingegneria civile» rather than «tertiary»), the
sector × position pair, first name and surname, the rendered biography —
is a deterministic function of the `uid` and the attributes already
generated:

| derived | module | conditioned on | source |
|---|---|---|---|
| first name, surname | `gsp.nomi` | sex, background, parents' origin, country | municipal registers, per-country repertoires |
| detailed education title | `gsp.istruzione` | education, sex, cohort | census 2011 title tree, ordered by CLAIST |
| sector × position | `gsp.lavoro` | sex, municipality | census 2011, jointly drawn (§I.1) |

On the information plane they add nothing; on the readability plane they
change everything, and that is precisely why they demand care: **apparent
diversity grows while real diversity does not**. Two individuals with the
same demographic profile and the same donor signature are identical where
it counts and now merely look different — for a simulation use this is a
worsening, since it hides that two agents are not independent evidence
**[n]** piano §3.1. And each derivation carries its declared limits with
the value, because an imputed variable without them is an invention with
the look of a datum: the title tree has no doctoral entries, so
`post_laurea` renders as master's degrees only; the sector is not
conditioned on the title — the census does not publish that cross at
municipal level — so roughly one employed card in five carries a sector × title pairing that no conditioning produced, plausible-looking
but unearned; whoever shows a card must know it, and must not mistake
that oddity for a defect of the demographic model, which is verified
**[n]** biografia §3.3. The operational consequence: derived attributes
are never stored in any file; they exist only in the regimes generated on
demand (§I.7), each on a separate deterministic channel, so that fixing
the title concordance does not reshuffle the names **[n]** piano §5.

The onomastic layer is the clearest case, and in v1.0 the roughest: it
exists to make records readable, not to represent Italian naming.
Italian first names and surnames come from two municipal repertoires
(Florence for surnames, Modena for first names) applied to every
municipality — a Ravenna resident carries a Florentine surname —, and
foreign names come from coarse per-area lists (Arabic, sub-Saharan,
Eastern European) that flatten differences a demographer would care
about and certainly contain errors. This is deliberate for a first
release and declared as such: the names are placeholders that behave
correctly where it matters — they are drawn from repertoires,the coarseness 
has a side effect worth keeping even after the repertoires improve: it guarantees collision (§I.7). 
Improving the repertoires is a v1.1 item; nothing downstream depends on them.

### I.7 Publication regimes and the disclosure argument

One function is the single point of enforcement — `gsp.individui`, with
`esporta_pubblico()` for the bundle and `campione(dettaglio=...)` for
samples — and four regimes in three tiers, on the model of the
statistical institutes' public-use / research / protected distinction
**[n]** piano §4:

- **complete population** (protected): every attribute, exact address,
  `uid`; never leaves the generation machine in any form;
- **pubblico** (public use) — the only downloadable product, and the
  *default*: no name, no street or civic number, coordinates randomised
  within the census section with a seed derived from the municipality
  code, no `quartiere` (one-to-one with `zona`), no `uid`, no donor id;
  the permissive export is an explicit act with a warning;
- **persona / narrativo** (research) — prompt material and full
  narrative records, generated on demand, capped at `NMAX = 100`
  individuals per call **[m]**: beyond that threshold the function
  refuses, with the reason in the error itself — one is producing a
  dataset, not a sample. The bound is not technical, and raising it is
  a decision recorded in the code rather than an argument passed at
  the call site; a sample of dozens is an act of citation, a file of a
  hundred thousand is an archive, and the cap encodes that difference.

The argument for the public release runs in three levels, of which the
first two stand alone **[n]** fonti §10, piano §1–3:

*First, there is no personal datum to protect.* The population is
simulated from published aggregates, not anonymised from individual
records. The two are legally distinct: anonymisation must demonstrate that
a link to a person has been broken; simulation never had one. There is no
re-identification risk by construction, because there is no one to
re-identify.

*Second, the one real thing in a record is the donated AVQ vector* — the
23 responses of an actual respondent, already perturbed at the source by
ISTAT's public-use release, and replicated tens of times — mean donor
reuse 25–84× depending on the municipality (§III.3b) — so that no
combination is unique to a synthetic individual. The protection is in
the data, not in a clause.

*Third, the address carries no information.* The civic assignment is
arbitrary within the section, so removing it, or randomising the
coordinate within the section, loses nothing analytic — which is exactly
what the public regime does, and why the file is self-protecting: "the
point is random within the section" admits no reply (§IV.2). 
The test municipalities gave this level an unintended stress test:
Mantova's addresses are almost entirely non-georeferenced (§I.4), so
its public bundle is built from section geometry alone — and is
indistinguishable in kind from the others, because the public regime
never used the civic number to begin with.

*A fourth level, measured rather than structural: a name identifies no
one.* Names are drawn from repertoires — 301 first names and 638
surnames in the released configuration — so collision is not a residual
risk but the normal case. On Castenaso, the smallest municipality,
16,357 individuals carry 3,024 distinct full names: **94.4 % of the
population shares its full name with at least one other person**, and
the most frequent combinations recur seventeen times each **[m]**. The
5.6 % whose full name is unique are unique only within their
municipality, against repertoires that are the same in all eleven. A
name in these records is a label for reading, not a key for finding.

What remains is a risk of *interpretation*, not of data: a record that
reads «Maria Bruni, 45, laurea magistrale in medicina, dipendente nella
sanità, Cittadella» reads like a person — although the surname comes from a Florentine repertoire (§I.6), which is precisely the point: it individuates no one, although every component is
either aggregate-derived, donated-and-replicated, or generated-and-
collident. The viewer answers with the banner on every card; the report
answers with the table "what, in a record, is actually real" (reproduced
in Appendix ‹A/F›); the narrative regime answers with the cap and the
on-demand generation.

---

### Open items for Part I

1. **[v]** Figure I.0, the pipeline diagram. Drafted as a Graphviz
   source (`note/fig_I0_pipeline.dot`): three doors entering at their
   points, the nine commands of §I.0, rings coloured, regimes as the
   final box. Three things to fix before it goes in: the aspect ratio
   is far too wide for a page (break into two rows, or two figures);
   the ring labels float instead of sitting over their steps (use
   clusters); and the tier arrow points at `build_zona_tables` when it
   belongs to `enrich`.
