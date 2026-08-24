# Part I — Architecture: the four rings
## Draft v1 — §I.1–I.7 (22 August 2026)

> Same conventions as the other parts: **[m]** measured at
> `report-v1.0-rc1`, **[n]** from a note (cited), **[v]** to verify before
> freezing. Sources: `GSP_popolazioni_full_riferimento_v24` (cited as
> *riferimento*), `fonti_e_pacchetto_v8`, `piano_trattamento_v2`,
> `nota_nucleo_familiare_v3`, `nota_biografia_v2`. Figure I.0 (pipeline
> diagram) is listed at the end as **[v]** to draw.

---

### I.1 Design principles

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
class. ‹Three-year vocational qualifications: state their class
explicitly here.›)





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
(31 December of year N−1) enter as soft constraints. Their mutual
consistency is not assumed but *manufactured upstream*: `cs_build`
rescales each table to its declared universe and to the register total,
and cross-audits every shared margin between blocks, printing the
maximal discrepancy of each — exactly zero on the municipal margins,
10⁻¹⁰–10⁻¹¹ on the zonal sums, machine precision rather than source
conflict **[m]**. What reaches the solver is therefore a consistent
target vector, and the fit's residual is purely numerical: exact-solver
convergence at MRE = 4.9·10⁻⁴ on Parma **[m]**, of the same order across
the fleet and independent of the support size **[n]** riferimento §5.
Two declared floors complete the picture: observed zeros enter at
ε = 10⁻⁸ rather than exactly zero — expected realisations over the whole
fleet ~0.02 individuals, observed none (§III.3) — and cells whose target
falls below min-α = 2·10⁻⁴ are dropped from the constraint vector
altogether, that is, left free rather than constrained to a value
smaller than the sampling noise could ever verify. The zone dimension
enters through tables built at the municipality's declared articulation
— statistical zones, quartieri, circoscrizioni, aree — a property of the
municipality, not of the pipeline (§III.2 table); the support is the
product of the class counts of the table above, 2·8·4·2·6·7·6·5 =
161,280 states per zone, from ~650,000 at four zones to 5.3 million at
Brescia's thirty-three. The fit error above is the distance of the
*distribution* from its targets; the error measured on a sampled
*population* adds the sampling noise, is dominated by it on small cells,
and is the object of §III.3a, where it is read against its floor.

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
spatially filtered panel (§IV.1). The honest sample size behind any AVQ
mean is not n but Kish's effective size on the variable's own universe,
and the confidence bands it implies are 2 to 20 times wider than the
naive ones, the factor growing with the municipality's population and
varying with the variable's universe (§III.3b). The hierarchical
collapse of the conditioning cell touches 1.5–3.1 % of individuals — but
not at random: the cells that fall below the twenty-donor threshold are
all low-education cells, so the collapse concentrates precisely where
educational conditioning would matter **[n]** riferimento §13.2. The
donor's identity survives as an equivalence class — the donated tuple
*is* the signature — which is what the viewer exposes on every
individual card and what §III.3b counts.

The second half of ring 2 is the country of citizenship. The census
gives the municipal margin — country × sex — and, per census section,
the count of foreign residents; where a municipality publishes a
sub-municipal table of residents by country, that table is register
data of a different date, and its *levels* are incompatible with the
census by amounts that matter (Brescia's register counts 40,090
foreigners against 37,478 census). The construction therefore uses the
local source's *shape* only: it seeds an iterative proportional fit
whose two margins are both census — the municipal country × sex table,
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

### I.4 Ring 3 — sub-municipal placement

Ring 3 turns a zoned population into a placed one: census section,
single-year age, address.

*Section.* Within a zone, individuals are assigned to census sections.
The section *totals* are matched almost exactly: the allocation is exact
(largest remainder) rather than multinomial, and the mean absolute error
per section is 0.74–1.58 individuals — against ≈ 9.6 for a multinomial
draw — on sections averaging 84–175 residents, and it does not grow with
population (§III.3, *reported*). The section *composition* is where the
declared assumption sits: (8) — section independent of education,
condition and background, given zone, sex, age-3 and citizenship —
concedes that three attributes are spread within the zone without
section-level structure, because no census table conditions them there.
The concession is not free, and it is measured twice over. The
compositional analysis that motivated this ring found 80–98 % of the
compositional signal living *below* the zone — which is why placement
cannot stop there **[n]** `nota_segnale_compositivo_v3`; and the M-EM
measures, run against the census's own section-level migratory-background
columns, find a real residual on all eleven municipalities (median net
~0.022 for Italians, ~0.018 for foreigners) — assumption (8) discards
section-level structure that exists, the refinement through the census
EM columns is designed, and it is queued with the next regeneration
cycle (§III.5) **[n]** `nota_background_sezione_v1`.

*Single-year age.* The exact age is drawn in two stages:
section → five-year class → single year. The five-year class comes from
the section's own census columns (the sixteen five-year counts per sex),
so the age *structure* of every section is respected at five-year
resolution; where a bin boundary cuts a five-year class — the 0–8 bin
ends inside the 5–9 class — the class is split 4/5–1/5 under uniformity,
the same assumption the method makes throughout. The single year within
the class then follows the municipality's register distribution by
single year of age: this is assumption (9) — below five-year resolution,
every section inherits the municipal shape. The ex-post diagnostic
measures both declared artefacts of the construction: the seam left at
the split classes (mean residual 2.3–5.7 individuals per section,
§III.3), and a systematic within-bin lean — too few nine-year-olds where
the 4/5–1/5 split operates, and a young lean in the adult bins, ten
concordant signs over two cities, p ≈ 0.002 (§III.4). Both measured,
neither repaired in v1.0.

*Address.* A civic number drawn uniformly among the section's ANNCSU
entries (assumption 10), with its coordinates. In production the section
supplies the address directly for ≥ 99.5 % of individuals **[m]** (the
`[3e]` line of every generation log); the residue is sections with
population but no registered civic number — a property of the address
register, not of the pipeline: Modena has the largest share (0.15 %)
while holding *more* civic numbers than Brescia for fewer residents, so
the gap is distributional, not one of coverage — and falls back to the
nearest declared level. One case is handled apart, and declared:
individuals in collective households (the empty `id_nucleo` of ring 4)
sit in a fictitious section and carry *no* address at all, their
coordinates being the zone centroid — an institution is not a home, and
inventing a civic number for it would manufacture exactly the kind of
false precision the regime exists to prevent. The uniformity of the draw
is the load-bearing fact of the disclosure argument (§I.7): every
address exists, and the assignment carries no information about anyone —
which is also why the public regime can randomise the coordinate within
the section at zero analytic cost (§IV.2).

One boundary of that argument was found by adding a municipality
outside the fleet, and is worth stating here rather than discovering.
Address coverage is a property of each municipality's ANNCSU
*georeferencing*, not of the pipeline: the fleet's ≥ 99.5 % reflects
Emilia-Romagna's near-complete coordinate coverage. Mantova — added as
a test case ([n] collaudo_acquisizione_v0.2) — has certified 17,009 accesses in ANNCSU but
georeferenced 240 of them (1.4 %) (**[m]** collaudo, 25/8): the addresses exist as text, not as
coordinates, and the spatial join legitimately finds nothing to
attach. The consequences split exactly along the regime boundary: the
public regime is unaffected, since its coordinates are drawn within
the census section, which every individual has; what degrades is the
textual address of the persona and narrative regimes, which falls back
to the zone level. A municipality's ANNCSU completeness is therefore
part of its declared source profile, on the same footing as its
open-data tier (§I.3).


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
(8,443 nuclei; the size-6+ tail from the Parma microdata, a mixed source,
declared), conditioned demographically **[n]** nota_nucleo §6,
riferimento §16.

`assign_nucleo.py` writes `uid, id_nucleo, ruolo` to a separate file — the
population stays read-only — with individuals in collective households
carried with an empty `id_nucleo` rather than dropped. The friction of
meeting the size constraint is itself reported (which sections required
truncating the open 6+ class, which betray a collective household)
**[n]** riferimento §16.4, and the headline anomaly — 18–25 % of married
individuals not in a married couple — decomposes into three quarters
structurally excluded by their own role (married children living with
their parents: 13.9 % of the married carry role F) and a residue of
unmatched slots; the constraint set never required that people marry in
pairs, so ring 4 reveals an incoherence already present in the ring-1
population rather than creating it (§III.3). Same-sex couples are absent
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
building-level work. And *the assembly still produces rare demographic
oddities at the margins* — a handful of married fifteen-year-olds have
been observed — legal in Italy only with court authorisation at sixteen,
so at fifteen an artefact of the assembly's age conventions, not a
demographic claim; rare enough to survive the current diagnostics,
declared here, on the list for the next repertoire iteration. The
17-to-24 widowed of §I.2 were an observed zero the constraints enforce;
the married fifteen-year-old is the same kind of cell one ring further
out, where no constraint yet reaches.

### I.6 Derived layers — no new information, declared as such

Everything else an individual can carry — the detailed education title
(«diploma di istituto tecnico industriale» rather than «diploma»), the
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
municipal level — so roughly one rendered card in five carries a
sector × title pairing that no conditioning produced, plausible-looking
but unearned; whoever shows a card must know it, and must not mistake
that oddity for a defect of the demographic model, which is verified
**[n]** biografia §3.3. The operational consequence: derived attributes
are never stored in any file; they exist only in the regimes generated on
demand (§I.7), each on a separate deterministic channel, so that fixing
the title concordance does not reshuffle the names **[n]** piano §5.

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
  narrative records, generated on demand, capped at NMAX = 100
  individuals per request **[v]**; a sample of dozens is an act of
  citation, a file of a hundred thousand is an archive, and the cap
  encodes that difference.

The argument for the public release runs in three levels, of which the
first two stand alone **[n]** fonti §10, piano §1–3:

*First, there is no personal datum to protect.* The population is
simulated from published aggregates, not anonymised from individual
records. The two are legally distinct: anonymisation must demonstrate that
a link to a person has been broken; simulation never had one. There is no
re-identification risk for construction, because there is no one to
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

What remains is a risk of *interpretation*, not of data: a record that
reads «Maria Bruni, 45, laurea magistrale in medicina, dipendente nella
sanità, Cittadella» reads like a person, although every component is
either aggregate-derived, donated-and-replicated, or generated-and-
collident. The viewer answers with the banner on every card; the report
answers with the table "what, in a record, is actually real" (reproduced
in Appendix ‹A/F›); the narrative regime answers with the cap and the
on-demand generation.

---

### Open items for Part I

1. **[v]** Figure I.0: one pipeline diagram, `fetch_comune` →
   `assign_nucleo`, rings coloured, assumptions numbered at their entry
   points, regimes as the final box (redraw from riferimento §5 chain).
2. **[v]** The "what is real" table: decide its home (here in §I.7 or in
   the front matter) — it is the single most quotable object of the
   report.
3. **[v]** §I.2: state the exact-vs-PCD split across the eleven
   municipalities (which were solved exactly at the tag) from the fit
   logs.
4. **[v]** §I.5: repertoire size (8,443) and the Parma-tail statement
   against `nota_repertorio_avq_v3` (this draft cites the memory of it).
