# Part III — Reproducibility and quality report
## Draft v0.1 — §III.1–III.2 (19 August 2026)

> Draft conventions. Numbers marked **[m]** were measured in the run of
> 19 August 2026 at tag `report-v1.0-rc1` (log in
> `note/misure/rilancio_report_v1.0/`); **[n]** are taken from the notes with
> the note cited; **[v]** means to be verified before the draft is frozen.
> Prose is meant to be pasted into the report as is, after review.

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
access once the registered sources are on disk.exact package versions are frozen in 
note/misure/rilancio_report_v1.0/requirements-report.txt, committed with the run logs [m]

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


1. **[v]** Cross-machine regeneration of Parma on Leonardo (or any second
   machine); result goes into §III.2 either way.
2. Decide whether `generato` leaves `manifest.json`/`riferimenti.json` in
   v1.1; for v1.0 the binding hashes Parquet only (decided 19 August).
