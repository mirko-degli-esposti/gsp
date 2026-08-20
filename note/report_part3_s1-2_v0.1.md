# Part III — Reproducibility and quality report
## Draft v0.1 — §III.1–III.2 (19 August 2026)

> Draft conventions. Numbers marked **[m]** were measured in the run of
> 19 August 2026 at tag `report-v1.0-rc1` (log in
> `note/misure/rilancio_report_v1.0/`); **[n]** are taken from the notes with
> the note cited; **[v]** means to be verified before the draft is frozen.
> Prose is meant to be pasted into the report as is, after review.

---

### III.1 Environment, determinism, and what "reproducible" means here

The claim this report makes is narrow and testable: given the source files
registered in `fonti/registro.yaml` and a tagged commit of the GSP
repository, the pipeline regenerates every population, ring by ring, to the
byte. It does not claim that the populations are *right* — that is the
subject of §III.3–III.4 — but that they are *the same*, whoever runs the
code, whenever.

**Reference environment.** All results in this report were produced on a
single workstation running Ubuntu 24.04 under WSL2 (AMD Ryzen AI 9 HX 375,
64 GB RAM; the GPU is not used by the pipeline), Python 3.11 in a conda
environment, with the `gsp` package installed in editable mode from the
repository root (`pip install -e .`). Ring 1 uses Numba for the sparse
constraint kernel; rings 2–4 are pandas and NumPy. No step requires network
access once the registered sources are on disk. **[v]** exact package
versions to be frozen in `requirements-report.txt` at the tag.

**Where randomness enters, and how it is pinned.** Every ring draws random
numbers, and each draw is seeded explicitly:

- Ring 1 (maximum-entropy fit and sampling): the solver is deterministic for
  a given constraint set and parameter vector; the population is sampled with
  a fixed seed per run. **[v]** confirm whether `fit_cs.py` seeds from the
  municipality code or from a constant.
- Ring 2 (AVQ hot-deck): **[v]** seed policy in `assign_avq.py`.
- Ring 3 (`enrich.py`: section, area and country, single-year age, address):
  a single NumPy generator seeded with a declared constant (`--seed 42`
  by default). The constant is global, not derived from the municipality;
  this is recorded as a known inconsistency with the policy adopted later
  (below) and is scheduled for the next cycle in which regeneration is
  already planned for other reasons. It has no effect on reproducibility:
  the same municipality always sees the same seed.
- Ring 4 (`assign_nucleo.py`): seeded as `20260810 + int(municipality code)`,
  so that running two municipalities together or separately gives the same
  result — with a single global seed the generator would advance between
  them. The effective seed is written into the diagnostic JSON.
- Public regime (`gsp.individui.esporta_pubblico`, §I.7): coordinate
  randomisation within the census section is seeded from the municipality
  code, so that the public bundle is itself reproducible.

The policy the project converged on, and that new code follows, is the one
of ring 4 and the public regime: *seeds are derived from the municipality
code, never shared across municipalities, and never taken from the clock*.
Older code (ring 3) uses a fixed declared constant, which is reproducible but
less robust; the difference is documented rather than patched, because
patching it would change the populations without improving them.

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
`diff -r` after, and the refactoring was accepted only on an empty diff. Two
bugs were found this way that no test had caught: a classification error in
the citizenship tiers (Czech Republic and South Africa, whose names contain
the strings of a continent and of a cardinal direction) and a permutation of
zone names in Bologna. **[n]** `GSP_popolazioni_full_riferimento`, §4;
`design_animarium`, §0.1. Maintaining two code paths that must agree is, in
this sense, a permanent regression test; the day they disagree is the day a
bug is found.

---

### Open items carried from this section into the work plan

1. **[v]** Seed policy of `fit_cs.py` and `assign_avq.py` — two `grep`s,
   then one sentence each.
2. **[v]** Freeze package versions at the tag (`pip freeze > requirements-report.txt`,
   committed under `note/misure/rilancio_report_v1.0/`).
3. **[v]** Cross-machine regeneration of Parma on Leonardo (or any second
   machine); result goes into §III.2 either way.
4. Decide whether `generato` leaves `manifest.json`/`riferimenti.json` in
   v1.1; for v1.0 the binding hashes Parquet only (decided 19 August).
