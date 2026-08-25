# Part III — Reproducibility and quality report
## Draft v0.1 — §III.3 (19 August 2026)

> Continues `report_part3_s1-2_v0.1.md`; same conventions. All numbers in
> this section are **[m]** — measured on 19 August 2026 at
> `report-v1.0-rc1`, outputs in `note/misure/diagnostica_report_v1.0/` —
> unless marked otherwise. All tables are filled; the one figure not
> re-measured at the tag (the per-section allocation MAE) is declared
> *reported* in the ring-3 subsection.

---

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

---

### Open items for §III.3

1. The MAE per section is *reported*; if a re-measurement is wanted for
   v1.1, the script is to be rewritten (the original was not retained) —
   noted in §III.5.
3. `residuo.py` (leave-one-out compositional residual) is a shared module
   correcting M-EM and related measures: move it from the exploratory group
   to group 2 in `scripts/README.md`.
