# Part I — Architecture: the four rings
## Draft v0.1 — §I.1–I.7 (20 August 2026)

> Same conventions as the other parts: **[m]** measured at
> `report-v1.0-rc1`, **[n]** from a note (cited), **[v]** to verify before
> freezing. Sources: `GSP_popolazioni_full_riferimento_v24` (cited as
> *riferimento*), `fonti_e_pacchetto_v8`, `piano_trattamento_v2`,
> `nota_nucleo_familiare_v3`, `nota_biografia_v2`. Figure I.0 (pipeline
> diagram) is listed at the end as **[v]** to draw.

---

### I.1 Design principles

Four run through everything and are worth stating before the mechanism.

*Every attribute has a declared place.* An attribute lives either in the
joint model (ring 1), where the solver generates it under simultaneous
constraints, or in a downstream derivation, conditioned on what is already
there. The choice is not a matter of taste: since August 2026 it is a
measurement — the total-variation distance between the attribute's
conditional and marginal distributions, computed for every conditioning
set available downstream (`gsp.tvd`). Large distance on a downstream-
available conditioner → derive; large only on fine geography → joint
model; small everywhere → assign unconditionally. A secondary criterion
breaks ties: at equal distance, preserve the structure that makes an error
*recognisable* — a joint draw that fails produces a manager in agriculture,
which anyone notices; a conditional draw that fails produces plausible
individuals in slightly wrong proportions, which nobody does **[n]** fonti
§8. This criterion moved one decision after it was taken: the
sector × position pair left the constraint set (the abandoned K10C level)
for a downstream joint draw conditioned on sex and municipality (§I.6).

*Every metric is normalised against its null.* A raw error, a raw
distance, a raw correlation scales with cell count, section size, or
support, and comparing it across configurations compares the
configurations' geometry, not their quality. The report's tables therefore
carry the null beside the observation throughout (Part III); the rule has
retired at least four numbers in this project's history (§III.6).

*The population is read-only.* Once generated, a population file is never
modified: derived attributes are computed at consumption time from the
`uid`, ring 4 writes its columns to a separate file joined on `uid`, and
every fix that would touch the file is instead queued for a full
regeneration cycle. The premise makes the regression test trivial — the
file must never change — and makes `diff` the universal instrument.

*Nothing is silently corrected.* Withdrawn claims keep their text and gain
a dated annotation; falsified predictions are registered before the
measure runs; refactorings are accepted only on a byte-identical baseline
(§III.2, §III.6).

### I.2 Ring 1 — the joint model

Ring 1 produces, for each municipality, the joint distribution of up to
ten demographic attributes — zone, sex, age (eight bins), marital status,
citizenship (Italian/foreign), education (six classes), occupational
condition (seven), migratory background (six), parents' origin (five) —
as a maximum-entropy distribution over the discrete support X subject to
the census constraint set, and then samples N individuals from it. The
method — exact solution of the dual where |X| allows, persistent
contrastive divergence where it does not — is the subject of
arXiv:2603.27312 and is not repeated here; what this report documents is
the *configuration*: what the constraints are, where they come from
(Part II), and what the fit achieves on the eleven municipalities
(Part III).

The constraint set is a template, identical across municipalities at the
same level: sixteen blocks at K9C, of which eleven complete (masses
summing to one) and five partial **[n]** riferimento §14.1. The partial
blocks are not incomplete distributions but *complements outside the
universe* — the census publishes education only for ages 9+ and condition
only where it applies, so the table splits in two along the universe
boundary, and the two halves sum to one in pairs. A partial block's
unlisted cells are *free*, not forbidden; the distinction matters because
its opposite also occurs: where the census *observes* zero, the cell is
present with value zero and the support excludes it. Absent and zero are
opposites for maximum entropy — unconstrained versus forbidden — although
the source represents both with the same missing value; translating tables
into constraints without making the distinction explicit is the
characteristic error of the exercise **[n]** riferimento §14.2. Eight
observed zeros (six in citizenship × background, two in
sex × age × marital status) are respected exactly in all municipalities
**[m]** §III.3a; twenty-six logically impossible pairs of age × education
and age × condition, which no census table crosses, are excluded from the
support by construction (α = 0), and the populations contain none of them
**[m]** §III.2.

Two margins have distinct roles: the register table (1 January) is the
hard margin fixing the municipal totals; the census tables (31 December of
the previous year) are soft. The zone dimension enters through tables
built at the municipality's declared articulation — statistical zones,
quartieri, circoscrizioni, aree — which is a property of the municipality,
not of the pipeline (§III.2 table). |X| is 161,280 × n_zones at K9C; the
achieved MRE on α>0 cells is ≈ 4·10⁻⁴ and independent of |X| over the
order of magnitude the fleet spans **[n]** riferimento §5; the per-cell
z-scores against the sampling floor are in §III.3a.

### I.3 Ring 2 — donated attributes and the country of citizenship

The population's attitudinal and health layer — twenty-one AVQ variables:
self-rated health, chronic conditions, smoking, BMI, mental-health index,
environmental satisfaction, interpersonal trust, and the institutional-
trust battery on a 0–10 scale — is not modelled. It is *donated*: each
synthetic individual receives the complete response vector of one
respondent of ISTAT's *Aspetti della vita quotidiana* public-use microdata
(pools: Emilia-Romagna 4,629 donors, Lombardy 8,111; survey years 2023–24
stacked), drawn from the conditioning cell sex × macro-age × education-4
with a declared hierarchical collapse when a cell holds fewer than twenty
donors. Copying the whole vector rather than sampling variable by variable
is the decision that preserves the inter-variable correlations by
construction — and the same recognisability criterion as §I.1: a
mis-sampled joint produces visibly impossible respondents, a mis-sampled
marginal produces invisible bias **[n]** riferimento §2.2.

The price is stated, measured, and carried through every product. The
donated vector holds no geography below the region (assumption 6), so all
sub-municipal AVQ variation is compositional; the honest sample size is
not n but Kish's effective size on the variable's own universe, and the
confidence bands it implies are ×2–×20 wider than the naive ones
(§III.3b); the hierarchical collapse touches 1.5–3.1 % of individuals but
always the low-education cells **[n]** riferimento §13.2. The donor's
identity survives as an equivalence class — the 21-tuple is the signature
— which is what the viewer exposes and what §III.3b counts.

The second half of ring 2 is the country of citizenship. The census gives
the municipal margin (paese × sesso); where a sub-municipal source exists,
its *shape* — never its levels, which are register data of a different
date — seeds an IPF whose two margins are both census: the municipal
country × sex table and the foreign population of each geography. The
result is the tier structure of §II.4: tier 0 (census only) for any new
municipality, tiers 1–2 where an open-data table exists, tier 3 (section
level) in Parma. Coverage is complete by construction — the section weight
for foreigners is P × q with q = ST/P, so no foreigner can land where the
census counts none **[n]** riferimento §6.

### I.4 Ring 3 — sub-municipal placement

Ring 3 turns a zoned population into a placed one: census section,
single-year age, address.

*Section.* Within a zone, individuals are assigned to sections under
assumption (8) — section independent of education, condition and
background given zone, sex, age-3 and citizenship — with an *exact*
allocation (largest remainder) rather than a multinomial draw: the mean
absolute error per section is 0.74–1.58 individuals against ≈ 9.6
multinomial (§III.3, *reported*). The assumption is not decorative: the
compositional analysis that motivated the ring found 80–98 % of the
compositional signal below the zone **[n]** `nota_segnale_compositivo_v3`,
and the M-EM measures bound what remains below the section.

*Single-year age.* Drawn within the bin from the municipal single-year
distribution (assumption 9), reconciled with the sections' five-year
columns; the seam where bins straddle the five-year grid, and the
within-bin young lean, are measured in §III.3–III.4.

*Address.* A civic number drawn uniformly among the section's ANNCSU
entries (assumption 10), with coordinates. The uniformity is the
load-bearing fact of the disclosure argument (§I.7): the address exists,
the assignment carries no information.

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

### I.6 Derived layers — no new information, declared as such

Everything else an individual can carry — the detailed education title
(«diploma di istituto tecnico industriale» rather than «diploma»), the
sector × position pair, first name and surname, the rendered biography —
is a deterministic function of the `uid` and the attributes already
generated, drawn from census-conditioned distributions (2011 structure for
work and titles, ordered by CLAIST) and registered onomastic repertoires.
On the information plane they add nothing; on the readability plane they
change everything, and that is precisely why they demand care: **apparent
diversity grows while real diversity does not**. Two individuals with the
same demographic profile and the same donor signature are identical where
it counts and now merely look different — for a simulation use this is a
worsening, since it hides that two agents are not independent evidence
**[n]** piano §3.1. The operational consequence: derived attributes are
never stored in any file; they exist only in the regimes generated on
demand (§I.7), each on a separate deterministic channel, so that fixing
the title concordance does not reshuffle the names **[n]** piano §5.

### I.7 Publication regimes and the disclosure argument

One function is the single point of enforcement — `gsp.individui`, with
`esporta_pubblico()` for the bundle and `campione(dettaglio=...)` for
samples — and three products carry three declared regimes, on the model of
the statistical institutes' public-use / research / protected distinction
**[n]** piano §4:

- **complete population**: every attribute, exact address, `uid`; never
  leaves the generation machine in any form;
- **pubblico** — the only downloadable product, and the *default*: no
  name, no street or civic number, coordinates randomised within the
  census section with a seed derived from the municipality code, no
  `quartiere` (one-to-one with `zona`), no `uid`, no donor id; the
  permissive export is an explicit act with a warning;
- **persona / narrativo** — prompt material and full narrative records,
  generated on demand, capped at NMAX = 100 individuals per request; a
  sample of dozens is an act of citation, a file of a hundred thousand is
  an archive, and the cap encodes that difference.

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
ISTAT's public-use release, and replicated ~40× across synthetic
individuals so that no combination is unique. The protection is in the
data, not in a clause.

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
