# Part III — Reproducibility and quality report
## Draft v1 — §III.1–III.6 (25 August 2026)

> Conventions. Numbers marked **[m]** were measured in the run of
> 19 August 2026 at tag `report-v1.0-rc1` (logs in
> `note/misure/rilancio_report_v1.0/`, diagnostics in
> `note/misure/diagnostica_report_v1.0/`); **[n]** are taken from the
> notes, with the note cited; **[v]** means to be verified before the
> draft is frozen. Every figure in §III.3 is measured at the tag.
> This draft merges the former `report_part3_s1-2_v0.1.md`,
> `report_part3_s3_v0.1.md` and `report_part3_s456_v0.1.md`, written
> separately; all three are in `note/storico/`.

---

### III.1 Environment, determinism, and what "reproducible" means here

The claim this report makes is narrow and testable: given the source
files registered in `fonti/registro.yaml`, a tagged commit of the GSP
repository, and the solver repository at the pinned commit of the
binding table (front matter), the pipeline regenerates every
population, ring by ring, to the byte. It does not claim that the
populations are *right* — that is the subject of §III.3–III.4 — but
that they are *the same*, whoever runs the code, whenever. Two
boundaries of the claim are declared at the start. The solver
dependency is resolved by filesystem discovery, not by version pin:
the reproducer must check out the stated commit by hand (front
matter). And the chain is reproducible from self-acquirable public
sources only up to ring 1: rings 2–4 require the AVQ public-use
microdata and their derivatives, obtainable by anyone from ISTAT's
mIcro.STAT channel, but through a manual request that no script can
perform.

**Reference environment.** All results in this report were produced on a
single workstation running Ubuntu 24.04 under WSL2 (AMD Ryzen AI 9 HX 375,
64 GB RAM; the GPU is not used by the pipeline), Python 3.11 in a conda
environment, with the `gsp` package installed in editable mode from the
repository root (`pip install -e .`). Ring 1 uses Numba for the sparse
constraint kernel; rings 2–4 are pandas and NumPy. No step requires network
access once the registered sources are on disk. Exact package versions are
frozen in `note/misure/rilancio_report_v1.0/requirements-report.txt`,
committed with the run logs **[m]**.

**Where randomness enters, and how it is pinned.** Every ring draws random
numbers, and each draw is seeded explicitly:

- Ring 1 (`fit_cs.py`): the exact solver is deterministic by
  construction — no randomness enters the fit. Where PCD is used, its
  warm start has its own fixed seed (123). The final *sampling* of N
  individuals from the fitted distribution uses a fixed seed (42).
- Ring 2 (`assign_avq.py`): one generator per run, `--seed` with a
  declared default of 42, drawing the donor within each conditioning
  cell.
- Ring 3 (`enrich.py`): a single generator seeded with a declared
  constant (`--seed 42` by default) for section, country, single-year
  age and address.
- Ring 4 (`assign_nucleo.py`): seeded as `20260810 + int(municipality
  code)`, so that running municipalities together or separately gives
  the same result; the effective seed is written into the diagnostic
  JSON.
- Public regime (`gsp.individui.esporta_pubblico`, §I.7): coordinate
  randomisation seeded from the municipality code.

Two seed policies therefore coexist, and their history is visible in the
code: the early rings use a fixed declared constant, the later ones
derive the seed from the municipality code. The constant is reproducible
in practice because each municipality runs in its own process — the
regeneration test of §III.2, forty-four bit-identical files, is the
certificate — but it is the weaker convention: it would silently couple
municipalities if the chain were ever run in one process, and it is
scheduled for alignment in the next cycle in which regeneration is
already required for other reasons. The policy new code follows is ring
4's: *seeds derived from the municipality code, never shared, never from
the clock*.

**Artefacts do not embed their generation time.** A population file that
contained a timestamp would never hash the same twice. The CSV products of
rings 1–4 contain none. Two derived JSON files written by the Animarium
bundle chain (`manifest.json`, `riferimenti.json`) do carry a `generato`
field; for this reason the version binding in the front matter hashes the
Parquet files only, which are timestamp-free, and the two JSON files are
compared modulo that field. **[n]** `design_animarium_v13`, §15.

### III.2 The regeneration test at `report-v1.0-rc1`

On 19 August 2026, with the repository at tag `report-v1.0-rc1` and a clean
working tree, all eleven municipalities were regenerated from their
constraint sets through the full chain
`cs_build → fit_cs → assign_avq → enrich → assign_nucleo`
(`scripts/rigenera.sh`, one log per municipality), and every product of
every ring was compared byte for byte (`cmp`) with the population archived
immediately before the run. The outcome:

| municipality | code | level | ring 1 | ring 2 | ring 3 | ring 4 | time |
|---|---|---|---|---|---|---|---|
| Bologna | 037006 | K9C | = | = | = | = | 395 s |
| Brescia | 017029 | K9C | = | = | = | = | 333 s |
| Parma | 034027 | K9C | = | = | = | = | 339 s |
| Modena | 036023 | K9C | = | = | = | = | 105 s |
| Reggio nell'Emilia | 035033 | K9C | = | = | = | = | 220 s |
| Ravenna | 039014 | K9C | = | = | = | = | 130 s |
| Rimini | 099014 | K9C | = | = | = | = | 138 s |
| Ferrara | 038008 | K6C | = | = | = | = | 51 s |
| Forlì | 040012 | K9C | = | = | = | = | 147 s |
| Piacenza | 033032 | K9C | = | = | = | = | 72 s |
| Castenaso | 037021 | K6C | = | = | = | = | 16 s |

**[m]** Forty-four comparisons, forty-four identical files; 1,814,317
individuals in 33 minutes of wall-clock time on the reference machine. The
same run verified that none of the 26 impossible age × education and
age × occupational-condition combinations (§I.2) occurs in any population:
0 of 1,814,317.

One qualification belongs here rather than only in §III.5: since the tag,
two patches to ring 4 have been committed, one of which shifts the random
sequence for every municipality. The claim above is about the tagged
commit — which is what the binding table states — and a reader running
`master` today reproduces rings 1–3 identically and ring 4 differently
(§III.5, *post-tag divergence*).

The Animarium bundle was then rebuilt from the regenerated populations
(`build/build_bundle.py --forza`) and compared with the archived bundle: the
eleven `pop.parquet` files are byte-identical **[m]**; `manifest.json` and
`riferimenti.json` differ only in the `generato` timestamp. The SHA-256 of
each `pop.parquet` is recorded in the version-binding table of the front
matter and is the hash against which the public dataset on Zenodo can be
checked.

Two remarks on what this test does and does not show.

It shows that the pipeline is deterministic end to end, including the
Numba-accelerated sparse solver on the largest state spaces (Bologna,
390,098 individuals, eighteen zones), and that nothing in the chain depends
on the order in which municipalities are run or on the state of the machine.
It also shows that the populations currently displayed online are exactly
those produced by the tagged code: the archive against which the regeneration
was compared is the one the viewer was serving.

It does not show that a different machine would produce the same bytes.
Floating-point reductions in Numba are deterministic on a given build but
not across compilers or CPU vector widths; and the sampling in ring 1 depends
on NumPy's generator implementation, which is stable across versions by
policy but not guaranteed. A reader who regenerates on other hardware should
expect identical populations in most cases and, where they differ, should
find differences confined to ring 1 and invisible at the level of §III.3's
quality metrics. **[v]** this is the experiment to run on CINECA Leonardo
before the report is frozen: one municipality (Parma) regenerated there,
compared with the archive. If it is byte-identical the sentence becomes a
measurement; if not, the size of the discrepancy is itself the number to
report.

Finally, the method used here — archive, regenerate, compare byte for byte,
read the diff only where it is non-empty — is the same one that governed
every refactoring of the pipeline (§I.1): the migration to the `src/gsp/`
package layout, the consolidation of five duplicated municipality registries
into `gsp.common`, the removal of `sys.path` manipulation from the Animarium
build scripts. In each case a baseline was written before the change and
`diff -r` after, and the refactoring was accepted only on an empty diff.
Three bugs were found this way that no test had caught: a classification error in
the citizenship tiers (Czech Republic and South Africa, whose names contain
the strings of a continent and of a cardinal direction), a permutation of
zone names in Bologna, and — during the testing campaign of August — a
bulk edit of the registry that silently replaced a live script name with
its successor, caught because the two-stage relay of §I.0 made the
substitution visibly wrong **[n]** `collaudo_acquisizione_v0.2`,
finding 5; `GSP_popolazioni_full_riferimento`, §4;
`design_animarium`, §0.1. Maintaining two code paths that must agree is, in
this sense, a permanent regression test; the day they disagree is the day a
bug is found.

### III.3 Ring-by-ring quality

The regeneration test of §III.2 established that the populations are the
ones the tagged code produces. This section asks whether they are any good,
one ring at a time, and with each metric normalised against its null
(§I.1): raw error against the sampling floor, effective sample size on the
variable's own universe, household counts against the census partition.

#### Ring 1 — constraints, against the sampling floor

`verifica_vincoli.py` checks every cell of the constraint set against the
generated population, expressed as a z-score against the sampling floor
√(α(1−α)/N) rather than as relative error — because relative error on small
cells is a statistic without content: a cell with expectation 1.3
individuals that is off by two is not a five-per-cent municipality problem,
and the v1 of the tool, which ranked by relative error, produced nothing but
the ranking of the smallest cells **[n]** header of `verifica_vincoli.py`.
The comparison runs against the *published* Parquet, not the working CSV:
what is verified is what anyone can download.

Two anchor municipalities, the extremes of the state space:

- **Bologna** (K9C, 18 zones, 1,783 cells): no hard zero violated — every
  cell declared impossible is empty. The largest deviations sit exactly
  where the floor predicts them: |z| = 13.4 on a cell with expectation 2.0
  (widowed men aged 15–24), |z| = 10.2 on expectation 6.0; among cells with
  expectation above ~100, |z| stays below ~4.1 and the bulk is under 3.
- **Castenaso** (K6C, one zone, 289 cells): no hard zero violated;
  |z|max = 2.8, on a cell with expectation 12.2.

The full table:

| municipality | cells (α>0) | MRE obs. | MRE floor | mean |z| | sd(z) | % |z|>3 | |z|max (exp. of cell) | hard zeros |
|---|---|---|---|---|---|---|---|---|
| Bologna | 1,751 | 7.05 % | 5.29 % | 0.84 | 1.391 | 0.63 % | 36.0 (1.0) | none violated |
| Brescia | 2,949 | 7.82 % | 9.52 % | 0.80 | 1.012 | 0.47 % | 7.1 (2.0) | none violated |
| Parma | 1,349 | 4.99 % | 6.10 % | 0.80 | 1.014 | 0.44 % | 3.7 (9.0) | none violated |
| Modena | 629 | 3.95 % | 5.07 % | 0.82 | 1.018 | 0.16 % | 3.1 (5,577) | none violated |
| Reggio nell'Emilia | 629 | 4.74 % | 5.32 % | 0.78 | 0.979 | 0.32 % | 3.8 (27.0) | none violated |
| Ravenna | 1,108 | 7.99 % | 7.50 % | 0.85 | 1.164 | 0.63 % | 17.0 (1.0) | none violated |
| Rimini | 789 | 4.55 % | 5.41 % | 0.82 | 1.014 | 0.51 % | 3.3 (13.0) | none violated |
| Ferrara | 261 | 9.33 % | 7.95 % | 0.80 | 1.098 | 1.15 % | 7.1 (2.0) | none violated |
| Forlì | 1,989 | 11.04 % | 3,189 % | 0.85 | 1.092 | 0.80 % | 10.0 (1.0) | none violated |
| Piacenza | 629 | 5.48 % | 6.70 % | 0.91 | 1.118 | 0.48 % | 4.1 (165.7) | none violated |
| Castenaso | 257 | 15.81 % | 23.68 % | 0.80 | 1.000 | 0.00 % | 2.9 (169.9) | none violated |

Reading the table is an exercise in the project's own rule: never compare a
raw error across configurations. Observed MRE ranges from 4 to 16 % and is
everywhere of the order of its floor — the mean relative error a perfect
sampler would show given the cell sizes — and the municipalities with the
"worst" raw MRE are precisely those whose floor is highest (Castenaso:
16 % observed against a 24 % floor). Forlì is the reductio: 21 zones over
117,050 inhabitants make it the finest partition relative to population, its
constraint set contains many α>0 cells whose expectation is a fraction of an
individual, and its floor evaluates to 3,189 % — three hundred times the
observed error. On such a partition the relative scale carries no content at
all and only the z-scores speak; the observed |z| distribution of Forlì
(mean 0.85, sd 1.09) is unremarkable.

The z-scores are not independent draws — the sampler is a Gibbs chain, and
sd(z) above 1 measures the variance inflation due to its autocorrelation.
Nine municipalities sit between 0.98 and 1.16. Bologna stands out at 1.391,
with |z|max = 36 on a cell of expectation 1.0 (widowed men aged 15–24 in
one zone): the largest state space of the fleet (18 zones, K9C) mixes least,
and the inflation concentrates on near-empty cells while cells with
expectation above ~100 stay within |z| ≲ 4. It is a documented property of
the fit, not a defect of the population: no hard zero is violated and the
aggregate error is at its floor.

The same run re-verified the 26 impossible-combination exclusions at the
population level: zero occurrences in 1,814,317 individuals (§III.2).

*Register–census agreement on the demographic base.* Measured twice,
by two independent routes. From the decoded source tables, before any
processing: sex × single year of age, register at 1 January 2024
against census at 31 December 2023, 2,821 cells over fourteen
municipalities (the eleven released plus Mantova, Milano and one test
municipality), **zero discrepant cells, maximum absolute difference 0**;
cells present in one source only (5 across two small municipalities)
are empty in the tail of the age distribution. From inside the
pipeline: the raccordo section of every `constraints_*/report.md`
reports MAE 0.0 per cell and total discrepancy +0. The agreement is a
property of the sources — the official resident population being
census-derived since 2018 — not an artefact of the pipeline, which
performs no reconciliation on this margin.

#### Ring 2 — donors, and the honest width of every AVQ band

`verifica_donor.py` reconstructs the donor identity from the 21-tuple of
donated values (the hot-deck copies the whole vector from one donor, so the
tuple is the signature), and computes Kish's effective sample size. Three
findings, anchored on Modena and Castenaso:

*The signature is the donor, up to declared equivalence.* On Modena, 4,161
distinct signatures against 4,617 donors used (pool 4,629, Emilia-Romagna):
456 fewer, because some pairs of donors carry identical 21-tuples. They are
informationally equivalent, so `n_eff` computed on signatures is the correct
count — the donor label would overstate it.

*The conditioning cell leaves a visible trace.* 99.2 % of Modena's
signatures serve a single sex, 70.1 % a single macro-age, 45.3 % a single
education class; 15.4 % are confined to their full conditioning cell,
serving 9.4 % of individuals. The rest of the population received its AVQ
vector through the declared hierarchical collapse — the price of small
pools, stated as a measurement.

*The band width is a property of the variable's universe, not of the
municipality.* The naive confidence band on an AVQ mean, computed on `n`,
understates the honest one by √(n/n_eff), and this factor differs by
variable because each is defined on its own universe:

| variable (Modena) | coverage | n | signatures | n_eff | band × |
|---|---|---|---|---|---|
| SALUTE | 100.0 % | 184,597 | 4,161 | 862 | 14.6 |
| CRONI | 93.8 % | 173,208 | 3,889 | 774 | 15.0 |
| PUNTIFI10 (trust: local govt.) | 85.6 % | 157,973 | 4,006 | 3,220 | 7.0 |
| FIDUCIA (interpersonal) | 86.4 % | 159,537 | 4,053 | 3,260 | 7.0 |
| AMBIENTE | 86.4 % | 159,404 | 4,052 | 3,258 | 7.0 |
| BMI | 84.4 % | 155,843 | 3,942 | 3,156 | 7.0 |
| PUNTIFI13 | 42.4 % | 78,349 | 2,095 | 1,683 | 6.8 |

The whole-population variables (SALUTE, CRONI) carry the widest inflation
(×14–15); the battery items, whose universe excludes children, sit at ×7 —
the figure the viewer's trust panel draws as the thick band (§IV.1). A
whole-population `n_eff`, averaged across universes, would land between the
two and describe neither; this is why the project computes it per variable
and treats the whole-population figure as meaningless **[n]**
`GSP_popolazioni_full_riferimento`, §13.

*The band factor grows with population, not with any quality defect.* The
full table (SALUTE = whole-population universe; PUNTIFI10 = the trust
battery, universe 14+):

| municipality | n | signatures | donors used (pool) | n_eff SALUTE | band × | n_eff PUNTIFI10 | band × |
|---|---|---|---|---|---|---|---|
| Bologna | 390,098 | 4,169 | 4,625 (4,629) | 966 | 20.1 | 2,845 | 10.9 |
| Brescia | 198,259 | 7,225 | 8,108 (8,111) | 1,093 | 13.5 | 5,655 | 5.5 |
| Parma | 198,121 | 4,162 | 4,618 (4,629) | 832 | 15.4 | 3,181 | 7.3 |
| Modena | 184,597 | 4,161 | 4,617 (4,629) | 862 | 14.6 | 3,220 | 7.0 |
| Reggio nell'Emilia | 171,207 | 4,167 | — | 795 | 14.7 | 3,347 | 6.6 |
| Ravenna | 156,304 | 4,151 | — | 995 | 12.5 | 3,334 | 6.4 |
| Rimini | 150,046 | 4,155 | — | 924 | 12.7 | 3,318 | 6.2 |
| Ferrara | 129,391 | 4,150 | — | 1,153 | 10.6 | 3,082 | 6.1 |
| Forlì | 117,050 | 4,152 | — | 916 | 11.3 | 3,325 | 5.5 |
| Piacenza | 102,887 | 4,160 | — | 810 | 11.3 | 3,237 | 5.2 |
| Castenaso | 16,357 | 3,890 | — | 741 | 4.7 | 2,770 | 2.2 |

(The donors-used column exists where the generation log declares the donors
drawn; the signature count, which is what n_eff needs, is computed for all.)
The battery band factor falls monotonically with population, from ×10.9 in
Bologna to ×2.2 in Castenaso: a small municipality does not saturate the
donor pool, so each donor still contributes nearly independent information,
and the factor measures reuse, not quality. Brescia is the natural control:
the only municipality on the Lombardy pool (8,111 donors instead of 4,629)
carries almost twice the signatures (7,225) and the highest battery n_eff of
the fleet (5,655) at a population equal to Parma's — the pool size passes
through exactly as the design predicts.

#### Ring 3 — placement

Two diagnostics were re-run at the tag on all eleven municipalities
(`diag_quinq`, `diag_istruzione_eta`); all three diagnostics are measured at the tag — two re-run, the allocation MAE read from the generation logs

| municipality | allocation MAE per section | five-year seam: mean ·res· per section | impossible age×title share | conditional rate |
|---|---|---|---|---|
| Bologna | 1.36 | 5.11 | 2.39 % | 30.8 % |
| Brescia | 1.57 | 5.34 | 2.91 % | 33.6 % |
| Parma | 1.44 | 5.74 | 2.73 % | 31.7 % |
| Modena | 0.74 | 2.61 | 2.67 % | 30.3 % |
| Reggio nell'Emilia | 0.90 | 3.32 | 2.96 % | 32.4 % |
| Ravenna | 0.74 | 2.27 | 2.92 % | 34.3 % |
| Rimini | 0.89 | 2.57 | 2.88 % | 32.9 % |
| Ferrara | 0.72 | 2.41 | 2.43 % | 31.8 % |
| Forlì | 1.18 | 4.08 | 3.39 % | 38.5 % |
| Piacenza | 1.07 | 3.93 | 2.80 % | 33.1 % |
| Castenaso | 0.87 | 3.21 | 3.04 % | 37.3 % |

Two of the columns move together, and the reason is geometric, not
diagnostic: allocation MAE and seam residual are absolute counts per
section, and both scale with mean section size — Bologna, Brescia,
Parma and Forlì sit high on both because their sections average
109–175 residents, Ferrara and Ravenna sit low at 66–74. Comparing
these columns *across* municipalities compares their section
geometry; the quality reading is within each row, against the
denominators the text provides (a seam of 5 individuals on sections
of 175 is the same resolution limit as a seam of 2.4 on sections of
74). The two percentage columns, being ratios, carry their own
denominator and compare directly.

*Section counts.* The allocation of individuals to census sections is
exact (largest remainder) rather than multinomial; the mean absolute
error per section, printed by the generation chain at every run and
read here from the tag logs **[m]**, is 0.72–1.57 individuals across
the eleven municipalities (against ≈ 9.6 for a multinomial baseline
**[n]** riferimento §5) on sections averaging 66–175 residents, with
section totals matching the census exactly everywhere.

*The five-year seam.* Single-year ages are drawn within bins whose
boundaries do not coincide with ISTAT's five-year classes; re-aggregating
the synthetic population to those sixteen classes per section and sex leaves
a mean absolute residual of 2.3–5.7 individuals per section, concentrated on
the classes that straddle the 0–8 / 9-14 bin boundary (the fifteen worst
sections of Bologna carry seam residuals of 4–6 individuals on sections of
several hundred). It is a declared resolution limit (assumption 9, §III.4),
visible and small.

*Age×title coherence.* Education is constrained at the age-bin level; the
exact age is assigned afterwards in ring 3, and nothing ties the two below
the bin. The share of individuals whose exact age is below the minimum
attainment age for their title is 2.4–3.4 % everywhere. The diagnostic's
own control shows the incoherence is arithmetic, not spatial: the rate
*conditional on the ages at risk* is flat across zones within each
municipality (30–37 %), so the raw share varies between zones only through
age composition. Forlì's and Castenaso's highest conditional rates (38.5 % and 37.3 %) tracks its
age structure, not a defect. The fix — drawing the age jointly with the
title's threshold — is defined and scheduled for the next regeneration
cycle (§III.5).

#### Ring 4 — households, eleven municipalities

`assign_nucleo.py` writes a diagnostic per municipality at generation time;
the table below is their collection at the tag (`nuclei_riepilogo.md`):

| municipality | individuals | nuclei | mean size | no fallback | not placed | homog. couples | "incoherent married" |
|---|---|---|---|---|---|---|---|
| Bologna | 390,098 | 210,737 | 1.85 | 98.8 % | 1.4 % | 98.1 % | 18.2 % |
| Brescia | 198,259 | 96,608 | 2.05 | 97.2 % | 1.8 % | 95.1 % | 22.7 % |
| Parma | 198,121 | 94,484 | 2.10 | 97.7 % | 1.9 % | 96.5 % | 21.7 % |
| Modena | 184,597 | 85,249 | 2.17 | 96.0 % | 2.3 % | 93.8 % | 23.7 % |
| Reggio nell'Emilia | 171,207 | 80,829 | 2.12 | 96.8 % | 1.1 % | 94.8 % | 22.7 % |
| Ravenna | 156,304 | 75,616 | 2.07 | 95.0 % | 1.6 % | 91.6 % | 23.4 % |
| Rimini | 150,046 | 68,903 | 2.18 | 95.6 % | 1.8 % | 93.0 % | 24.0 % |
| Ferrara | 129,391 | 65,281 | 1.98 | 95.8 % | 2.1 % | 92.9 % | 21.4 % |
| Forlì | 117,050 | 54,000 | 2.17 | 94.7 % | 1.8 % | 91.4 % | 24.7 % |
| Piacenza | 102,887 | 48,737 | 2.11 | 96.4 % | 1.4 % | 93.9 % | 24.5 % |
| Castenaso | 16,357 | 7,493 | 2.18 | 96.5 % | 1.2 % | 94.6 % | 23.5 % |

Three readings. *The size constraint is exact where it can be checked
externally:* Parma's 94,484 nuclei equal the census `PF1` for Parma to the
unit — the section-level size distribution (PF3–PF8) is a hard constraint,
and this is its visible consequence. *Individuals not placed (1.1–2.3 %)
are declared, not dropped:* they appear in the output with an empty
`id_nucleo`, so a join cannot confuse "collective household" with "row lost"
**[n]** `assign_nucleo.py` header. *The "incoherent married" share
(18–25 %) is a property of the population, not of the assembly:* the
constraint set does not require that people marry in pairs, so the ring-1
population contains married individuals without a matching spouse slot in
their section's size profile; ring 4 reveals the incoherence, it does not
create it. Decomposed on Parma, individuals with role R are correctly
paired in 92–94 % of cases and role P in 97–98 %; what is missing are
slots, not pairings **[n]** `nota_repertorio_avq_v3` §7.4. Bologna's low
18.2 % tracks its low mean household size (1.85): more one-person
households, fewer chances for the incoherence to bind.

Same-sex couples are structurally absent (0 of 4,525 partner pairs in the
donor data carry one), and the population inherits the absence — declared
as a limit of the source, not a demographic claim **[n]**
`assign_nucleo.py` header; civil-union statistics are registered for the
next iteration of the repertoire (§III.5).

### III.4 Assumptions and resolution limits, in one place

Every attribute outside the constraint set enters through a declared
conditional-independence assumption. The report states them once, numbered
as in the reference document, each with its ring and its measured cost
where one exists.

| n. | assumption | ring |
|---|---|---|
| (4′) | country ⊥ everything given (area, sex, geography) — geography per tier; at tier 0 it does not bind | 2 |
| (6) | AVQ targets ⊥ everything given (sex, macro-age, education-4, region) | 2 |
| (8) | section ⊥ (education, condition, background) given (zone, sex, age-3, citizenship) | 3 |
| (9) | within a five-year class, single-year age follows the municipal distribution | 3 |
| (10) | the address is uniform over the civic numbers of the section | 3 |
| (11) | ~~no household structure~~ — lifted by ring 4; what remains is that the *address* is assigned per individual, so spouses can carry different civic numbers: household-level address assignment is the stated prerequisite for any building-level work | 3→4 |

Their measured costs, where the diagnostics put a number on them:

- **(6)** is the assumption the viewer prints on every spatially filtered
  AVQ panel: the donated vector carries no geography, so all sub-municipal
  AVQ variation is compositional. Its price is the band inflation of
  §III.3b (×2.2–×20.1 by variable universe and municipality). Two further
  declared costs inside the conditioning cell: the 50–54 class is served by
  55–64 donors — 35 % of the 50–64 bin, 8 % of the population **[n]** §13.2
  — and the hierarchical collapse, measured by regeneration, touches only
  1.5–3.1 % of individuals (full cell 96.9–98.5 %, third level and regional
  fallback never reached), but is not random: the cells under the 20-donor
  threshold are all `elementare_o_meno` **[n]** §13.2. An earlier
  signature-based estimate of the collapse (15.3 % on Modena) was
  contaminated by donor collisions and is withdrawn (§III.6).
- **(8)** is bounded by the compositional analysis: 80–98 % of the
  compositional signal lives below the zone, which is why ring 3 exists;
  and its residual is the subject of the M-EM measures, whose leave-one-out
  correction is in `residuo.py` **[n]** `nota_background_sezione_v1`.
- **(9)** produces the five-year seam of §III.3 (mean residual 2.3–5.7 per
  section) — elevated in rank but only ~40 % above the other classes once
  normalised, not an order of magnitude **[n]** §15.1. A subtler measured
  fact stands beside it: within every true bin the synthetic age
  distribution leans *young* — first class positive, last negative, ten
  signs concordant over two cities (p ≈ 0.002) **[n]** §15.2. Nothing
  constrains the within-bin shape; declared, on the list for the next
  cycle.
- **(10)** is what makes the public regime lossless: randomising the
  coordinate within the section discards an assignment that was already
  uniform (§IV.2).

**Zone-block resolutions, and what each one costs.** The zone blocks
carry every variable at the resolution its section columns have, which
is coarser than the population's in three places; each gap is an
assumption, and each assumption has a cost that no diagnostic in this
report measures — they are stated here so that a user of the data
knows where not to look for structure.

*Education, five levels against six.* The section tables distinguish
none, primary, lower secondary, upper secondary and tertiary; the
population splits tertiary into first-cycle and postgraduate. Zone
shares are computed on the five-level aggregation and applied to the
six-level municipal counts (`EDU6TO5` in `cs_build`), so within a zone
a degree and a postgraduate title share the same spatial form. Cost:
the geography of postgraduate education is that of tertiary education
as a whole — a municipality where doctorates concentrate in one
neighbourhood would not show it.

 *Occupational condition, the employed side only.* The section tables
count the employed; the population distinguishes four non-employed
categories (seeking work, student, retired, other), which the section
does not separate. Constraining them as one block would impose a single
geography on students and pensioners, which is false and unmeasurable,
so the zone block constrains the employed side alone — hence its mass
of ≈ 0.47, the universe of the block and not a defect (§I.2, partial
blocks). Cost, and it is the most consequential of the three: **the
spatial distribution of unemployment is constrained by no observed
datum**. Where the unemployed live follows from the maximum-entropy
solution given everything else — their sex, age, education, citizenship
and the zone shares of those — not from a measurement. Any use of these
populations that reads unemployment geographically must know this.

 *Citizenship, three macro-classes.* The zone block conditions on
0–14 / 15–64 / 65+ rather than on the population's eight bins, so
within a macro-class the zone shares of foreigners are constant: a
foreign twenty-year-old and a foreign sixty-year-old are distributed
across zones identically. Cost: the age profile of foreign residents
does not vary by zone beyond the three-class structure — a
neighbourhood of young foreign workers and one of settled foreign
families differ in the model only through the macro-class composition.

None of the three is a bug, and none can be removed without a source
that does not exist: they are the resolution of the census section
tables, inherited.

**Resolution limits by construction.** Education has an effective age
resolution of 4 classes, not 8: the census constraint uses Y9-24 / Y25-49 /
Y50-64 / Y≥65, and within each class the distribution comes from an IPF
with minimum attainment thresholds — `media` remains overstated in the 9–14
bin (the age×title incoherence of §III.3 is its single-year shadow), and
the cohort effect between 65–74 and 75+ is lost. The migratory background
has zone resolution, not section (assumption 8). The AVQ battery is complete at twelve items. An earlier release lacked
`FORZE_ARMATE` — the target list selected by prefix, one of three
silent hand-written-table failures found in one afternoon, all
producing absences rather than errors **[n]** riferimento §13 — and
the working notes still described that state; the fix entered before
the release tag, and the discrepancy was caught during testing when a
new municipality showed a variable the notes declared absent (§III.6,
register).

**Conventions for "absent", not unified** — declared as a trap for
consumers: `non_applicabile` as a string in `condizione`,
`origine_genitori` and 20 of 21 AVQ variables; `NaN` in `area`, `via`,
`civico`; nothing in `SALUTE` and `paese` (Italians read `Italia`) **[n]**
riferimento §1.

### III.5 Open points carried into v1.0

Declared, analysed, and deliberately not applied in this release — each
with the reason and, where it exists, the prepared change.

1. **Citizenship in the AVQ conditioning cell.** Analysis complete, patch
   drafted, not applied. AVQ's `CITTMi` shows a substantial, monotone
   effect on institutional trust (~1 point of 10, replicated in two
   regions; non-Italians trust institutions *more*, a direction opposite to
   intuition but known in the literature), and no effect on `AMBIENTE` or
   interpersonal `FIDUCIA`. The full cell does not hold (~11 donors); the
   collapse hierarchy with citizenship in high priority is written and
   waiting. Two reasons to wait: the modalities `3`/`9` must be identified
   in the codebooks first, and the foreign AVQ sample is self-selected on
   language competence, so the estimated trust is likely *overstated* — a
   limit to declare regardless **[n]** riferimento §8.
2. **The within-bin age lean** (§III.4, assumption 9) and **the
   age-at-threshold draw** for education (§III.3): both defined, both
   waiting for a cycle in which regeneration is already required, because
   regeneration invalidates `donor_id` and every measure, and is not done
   for one fix **[n]** old Animarium README.
3. **Section-level migratory background (EM1–EM6).** The census's own
   section columns give the six background modalities per section, in
   one-to-one correspondence with ring 1's `background`; the M-EM
   measures find a real net residual on all eleven municipalities
   (median ~0.022 Italians, ~0.018 foreigners), so assumption (8)
   discards structure that exists. The modification to `enrich.py` is
   designed — background subsumes citizenship in the cell key, weights
   normalised within the group, not multiplied — and the registry patch
   extending the source's `usabile_per` is written. Queued with the same
   regeneration cycle as (2) **[n]** `nota_background_sezione_v1`.
4. **A standalone diagnostic for the per-section allocation MAE**
   (§III.3): the measurement itself is not missing — the generation
   chain prints it at every run and this report reads it from the tag
   logs — but recomputing it today requires a full regeneration. A
   small script that recomputes it from an existing population is a
   v1.1 convenience.
5. **Modena's 37 rioni.** A partition ten times finer than the four ASC
   zones exists on the municipal portal (foreigner share spanning a factor
   15 instead of 2); it would attack assumption (8) where it binds most.
   Cost: a deviation from the ISTAT-standard zone levels, a
   section→rione mapping to build, and |X| growing tenfold. Registered as
   an opportunity, not scheduled **[n]** riferimento §8.
6. **EU-SILC** for income and living conditions: explored (two registered
   entries, graph script), decision not taken; the public files' terms do
   not allow redistribution, which any use will have to respect (§II.2).
7. **`donor_anno`** and **`cella_avq`** (collapse level per
   individual): queued for the same next regeneration cycle as (2).
   (`FORZE_ARMATE`, previously listed here, was already in at the tag —
   see §III.4.)
8. **MRE floor definition**: the floor formula in `verifica_vincoli.py` is
   the standard deviation of the relative error, while MRE is its mean
   absolute value (factor √(2/π) = 0.798); corrected, the observed error
   sits 10–11 % above the floor, consistent with sd(z) ≈ 1.03. Open:
   verify which definition `fit_cs.py` uses — instrument and paper must
   say the same thing **[n]** riferimento §14.5. **[v]** resolve before
   freezing §III.3's table caption.
9. **Household-level address** (the residue of assumption 11) as the
   prerequisite of any building-level assignment **[n]** nota_nucleo §9.

**Post-tag divergence in ring 4, declared.** The code in `master` no
longer reproduces the tagged ring-4 files, and the reason is worth
stating precisely rather than discovering. Two patches were applied to
`gsp/nucleo.py` and `assign_nucleo.py` *after* the release tag, both
from the same finding — a per-nucleus O(n²) matching invisible on the
fleet (sections up to ~700 residents) and costing hours on a metropolis
(Milano has fifteen sections above 1,000, one of 4,146, plus the
fictitious convivenza section of 10,038).

- **(a) Skip of the fictitious convivenza section.** Those individuals
  carry an empty `id_nucleo` by design, so assembling them was work
  thrown away; the section is now skipped before assembly. Because the
  skip does not consume the generator, **the rng sequence shifts for
  every section that follows it**: ring-4 outputs change for any
  municipality that has a convivenza section — that is, all of them.
  The aggregate diagnostics move within the noise of reassembly
  (Mantova: 24,298 → 24,275 nuclei, non-placed 2.16 % → 2.21 %, the
  rest unchanged to the decimal), and the non-placed now correctly
  include the institutional population.
- **(b) Children-plausibility count via `searchsorted`.** Semantics
  identical — same candidate set, same order, same rng draws —
  **verified** by an A/B run with only this patch switched, giving a
  byte-identical `nuclei_020030.csv`. Milano's ring 4 went from over an
  hour to 65 s.

Consequences, declared: the binding table's byte-identity claim holds
for the **tagged commit**, which is what it states; a reader running
`master` reproduces rings 1–3 identically and ring 4 with the shifted
sequence described above. The fleet is not regenerated for this alone
(point 2 above: regeneration invalidates `donor_id` and every
measurement, and is not done for one fix); both patches travel with the
next cycle **[n]** `collaudo_acquisizione_v0.2`, finding 7.

**What the next regeneration cycle carries.** Regeneration is expensive
in the only currency that matters here — it invalidates `donor_id` and every measured number in this report — so
the queued changes travel together. At the time of writing the cycle
carries: the two ring-4 patches above (a, b); the section-level
migratory-background refinement through the census EM columns
(§III.5.3); `donor_anno` and `cella_avq` written per individual
(§III.5.7); the within-bin age lean and the age-at-threshold draw for
education (§III.5.2); seed policy aligned to the municipality-derived
convention everywhere (§III.1); and the two test municipalities
(Mantova K6C, Milano K9C) promoted from test cases to fleet, taking the
released bundle from eleven to thirteen. The α = 0 exclusions for
impossible age × education and age × condition combinations are
**already in the tagged constraint sets** — twenty-six imposed cells,
verified at the tag (§I.2) — and are listed here only to record that
they were checked, not deferred.

### III.6 Register of retractions and falsified predictions

Nothing in this project is silently corrected: a withdrawn claim keeps its
original text and gains a dated annotation, in the note and where relevant
in the code. This register collects them, because a reader auditing the
populations deserves to know not only what is claimed but what was claimed
and withdrawn — and because the pattern of one's own errors is itself a
finding. Dates are those of the annotations.

1. **The −418 gap** between two population totals, initially read as a
   data defect, was a configuration coincidence; withdrawn and documented
   in the design note §0.1 **[v]** exact date from the note.
2. **`quartiere` = `zona`.** The viewer briefly treated the two as
   distinct levels; they are one-to-one, and the column was dropped from
   the bundle as redundant **[n]** design note.
3. **Whole-population `n_eff`** is unstable and was withdrawn; `n_eff` per
   variable universe is the correct object (§III.3b) **[n]** riferimento
   §13.
4. **The signature-based collapse estimate** (15.3 % of individuals
   confined to the full cell on Modena) was a very pessimistic lower bound
   contaminated by donor collisions; superseded by the regeneration
   measurement (1.5–3.1 %) **[n]** riferimento §13.2.
5. **The 3.7 % regional-fallback figure** in the 27 July logs described a
   generation predating the hierarchical collapse (commit `f383e54`); it
   does not apply to the populations in use **[n]** riferimento §13.2.
6. **Ring-4 prediction (a)**: excluding relationship code 11 would
   collapse the geographic residual of household structure. Measured:
   +0.0247 → +0.0255. *Falsified* — the code-11 concentration is almost
   entirely mediated by citizenship, already conditioned on **[n]**
   nota_nucleo §7.
7. **Ring-4 prediction (b)**: the section adds little over the quartiere
   (expected ratio < 0.3). Measured: 0.87 per family, 1.40 per person.
   *Falsified* — the centre–periphery gradient exists but is small against
   within-quartiere heterogeneity. Both falsified predictions err in the
   same direction — fine structure systematically underestimated — which
   is itself recorded as a prior for the next ones **[n]** nota_nucleo §7.
8. **The TVD ~ size correlation** (−0.438, read as "residual sampling
   noise"): under the null that correlation is negative anyway, because
   small sections have high TVD by construction; the comment had no
   diagnostic power and was replaced by the net-by-size-tercile test,
   which answered in the *opposite* direction **[n]** nota_nucleo §6.3.
9. **The Parma codebook reading of code 11** ("coabitazione") was
   contradicted by the data (PF9 cross-check); the mapping in use is
   inferred from demographic profiles and marked *inferita, non letta*
   (§II.3) **[n]** nota_nucleo §2.
10. **Aggregate MRE as a quality claim**: an aggregate MRE of a fraction
    of a per cent can hide per-cell errors of 1 %; per-cell z-scores
    against the floor replaced it (§III.3a) **[n]** design note /
    riferimento §11.
11. **Raking's MRE = 0 on training constraints** is algebraically
    guaranteed and is not an accuracy metric; held-out evaluation and
    diversity metrics are the comparison framework (this is the framing
    the solver paper adopts) **[n]** memory / arXiv:2603.27312.
12. **The Q-series and unit corrections** of the viewer's cost and error
    measures (a factor-2.1 estimate corrected; two results withdrawn by
    comparing against known-answer configurations) **[n]** design note
    §12–13, *working rule* of §IV.1. **[v]** compress or itemise from the
    note when assembling.
13.

The register's lesson is the project's method in miniature: every
withdrawal above was produced by a comparison against a null or a
known-answer configuration, never by re-reading the code — and the two
falsified predictions were falsifiable only because they were registered
before the measure ran.

---

### Open items for Part III

1. **[v]** Cross-machine regeneration of Parma on Leonardo (or any second
   machine); the result goes into §III.2 either way — byte-identity turns
   the sentence into a measurement, a discrepancy becomes the number to
   report.
2. **[v]** Re-number section references against riferimento **v24** (this
   draft cites v22 numbering).
3. **[v]** Dates for retractions 1, 2, 12 from the design note.
4. **[v]** MRE floor definition (§III.5, point 8): verify which definition
   `fit_cs.py` uses, then align §III.3a's caption.
5. `residuo.py` (leave-one-out compositional residual) is a shared module
   correcting M-EM and related measures: move it from the exploratory
   group to group 2 in `scripts/README.md`.
6. Decide whether `generato` leaves `manifest.json` / `riferimenti.json`
   in v1.1; for v1.0 the binding hashes Parquet only (decided 19 August).
