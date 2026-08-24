# Part III — Reproducibility and quality report
## Draft v0.1 — §III.4–III.6 (20 August 2026)

> Completes Part III (with §III.1–III.2 and §III.3 in their own files).
> Compilative: sources are `GSP_popolazioni_full_riferimento_v24` §7–8,
> §13–15, `nota_nucleo_familiare_v3` §6–8, `fonti_e_pacchetto_v8` §7, and
> the design note §0.1; **[v]** marks the few claims to re-check against
> v24 (this draft was written against v22 sections whose numbering may have
> shifted).

---

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
4. **The per-section allocation MAE script** (§III.3): the measurement is
   *reported*; the script is to be rewritten for v1.1.
5. **Modena's 37 rioni.** A partition ten times finer than the four ASC
   zones exists on the municipal portal (foreigner share spanning a factor
   15 instead of 2); it would attack assumption (8) where it binds most.
   Cost: a deviation from the ISTAT-standard zone levels, a
   section→rione mapping to build, and |X| growing tenfold. Registered as
   an opportunity, not scheduled **[n]** riferimento §8.
6. **EU-SILC** for income and living conditions: explored (two registered
   entries, graph script), decision not taken; the public files' terms do
   not allow redistribution, which any use will have to respect (§II.2).
7. 7. **`donor_anno`** and **`cella_avq`** (collapse level per
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

### Open items for §III.4–III.6

1. **[v]** Re-number section references against riferimento **v24** (this
   draft cites v22 numbering).
2. **[v]** Dates for retractions 1, 2, 12 from the design note.
3. **[v]** Item 7 of §III.5 (MRE floor definition in `fit_cs.py`): one
   grep, then align §III.3a's caption.
