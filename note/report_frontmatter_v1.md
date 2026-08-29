# Front matter — version v1 (26 August 2026)


---

# Animarium: an open, reproducible pipeline for synthetic populations of Italian cities — from ISTAT sources to open data

**Technical report v1.0 — Mirko Degli Esposti**
Department of Physics and Astronomy (DIFA), University of Bologna
ORCID 0000-0003-0316-3449 · mirko.degliesposti@unibo.it

Viewer <https://animarium.it> · pipeline
<https://github.com/mirko-degli-esposti/gsp> · viewer code
<https://github.com/mirko-degli-esposti/animarium>

## Abstract

Synthetic populations of eleven Italian municipalities — 1,814,317
individuals in 887,937 households — generated from published aggregates
alone: ISTAT census and register tables, census-section counts, the
national civic-address register, public-use survey microdata, and six
municipal open-data portals, every source certified in a registry with
licence, fingerprint and declared affordances. Four rings give every
attribute a declared place: a maximum-entropy joint model of up to nine
demographic attributes; whole-vector donation of twenty-three
attitudinal and health variables from survey respondents; placement to
census section, single year of age and address; and households
constrained by the census size distribution per section. Every
downstream layer — detailed titles, work, names, biographies — is a
declared derivation adding no information. The pipeline is deterministic
to the byte: regenerating all eleven municipalities from the tagged
commit reproduces every file of every ring bit for bit, in 33 minutes on
one workstation. Populations are released in a public regime enforced in
the data (no names, no addresses, coordinates randomised within census
section), browsable in Animarium — a dependency-free web viewer where
every number carries its comparison and every view is a citable URL —
and downloadable as an open dataset. The report documents the
architecture, the sources and their certification, the reproducibility
and quality measurements at the release tag, the viewer, and the
narrative layer that renders records into personas for LLM-driven
simulation — with the platform's controllability demonstrated in
companion experiments, and validation explicitly out of scope.

## A note on tools

Large language models — principally Anthropic's Claude, with occasional
use of OpenAI's ChatGPT — were used throughout this work: as a writing
partner for these notes and for this report, as a reviewer and
occasional author of code, and as an interlocutor while designing and
debugging the pipeline. Every design decision, every measurement, and
every claim in this document was made, checked and is owned by the
author; where a number appears, it was produced by code in the tagged
repository and verified against its source, not by a model. The errors
that remain are mine.

## Reading conventions

Two markers appear throughout. **[m]** marks a figure measured at the
release tag, with the log or diagnostic that produced it available in
the repository; **[n]** marks a claim taken from a working note, which
is cited by name and travels with the code. Nothing else in this report
is a number: where a quantity appears without a marker, it is a
definition or a design parameter.

Claims marked **[n]** come from the project's working notes, which live
in `note/` of the GSP repository and are versioned with the code: they
are cited by file name, so `nota_nucleo_familiare_v3` is that file at
that version. They are in Italian, as the project's internal record is,
and they are the layer where a decision is argued at length before it
becomes a paragraph here.

## Version binding

Every claim marked **[m]** in this report was measured at the versions
below; the hashes are the verification path.

| artefact | identifier | verify with |
|---|---|---|
| this report |  v1.0 (arXiv:2608.27111v2)— |
| GSP pipeline | tag `report-v1.0`, github.com/mirko-degli-esposti/gsp | `git rev-parse` |
| Animarium viewer | tag `report-v1.0`, github.com/mirko-degli-esposti/Animarium | idem |
| MaxEnt solver (`maxent-popsynth-pcd`) | commit `14f5bab` (2026-08-03), github.com/mirko-degli-esposti/maxent-popsynth-pcd | `git rev-parse --short HEAD` in the clone |
| code snapshots | GSP: [10.5281/zenodo.22127410](https://doi.org/10.5281/zenodo.22127410) · Animarium: [10.5281/zenodo.22127473](https://doi.org/10.5281/zenodo.22127473) | checksum on Zenodo |
| open dataset | [10.5281/zenodo.22127581](https://doi.org/10.5281/zenodo.22127581), CC-BY-4.0 | SHA-256 below |
| public bundle | eleven `pop.parquet`, SHA-256 in `note/misure/rilancio_report_v1.0/hash_parquet_report_v1.0.txt` | `sha256sum` |
| source fingerprints | `fonti/registro.yaml` at the tag | `python -m gsp.fonti --verifica` |
| companion papers | arXiv:2603.27312 (solver) · arXiv:2607.00910 (SIVE) | — |

One entry above deserves its warning. The fitting stage imports
`ConstraintSet` from the solver repository by *filesystem discovery* —
a glob over a sibling directory — and does not verify which commit it
found. Until the solver is a
pinned package dependency (planned for v1.1), reproducing the fit
requires checking out the commit above by hand.

The tag `report-v1.0` names the same commit as `report-v1.0-rc1`, under
which the measurements of Part III were taken: the release candidate was
promoted rather than rebuilt, so every **[m]** in this report refers to
the artefact the tag points at. (Two ring-4 patches were committed after
that commit and are declared in §III.5.)



## What, in a record, is actually real

The single table to read before reading anything else. A released record
looks like a person; its components have exactly three provenances.

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

## How to cite

The report:

> Degli Esposti, M. (2026). *Animarium: an open, reproducible pipeline
> for synthetic populations of Italian cities — from ISTAT sources to
> open data.* Technical report v1.0, arXiv:2608.27111.

The dataset: [10.5281/zenodo.22127581](https://doi.org/10.5281/zenodo.22127581),
CC-BY-4.0, with the attributions in `fonti/ATTRIBUZIONI.md`. The
software: the Zenodo snapshot DOIs in the binding table, or
`CITATION.cff` in either repository.


## Licences

Code MIT (both repositories). Released data and populations CC-BY-4.0,
inheriting the attributions listed in `fonti/ATTRIBUZIONI.md`; sources
used for validation only are registered, fingerprinted and not
redistributed (§II.2). The viewer runs on any static server; no
component requires an account or a key.

## Scope

This report is a release document and a reproducibility record: what
the pipeline does, on which sources it stands, what was measured at the
tag, and in which regimes the results leave the machine. It is not a
methods paper — the maximum-entropy solver is arXiv:2603.27312 — and it
is not a validation of LLM-driven synthetic populations, which it
treats strictly as evidence of use (Part V, first paragraph). Where the
report and the working notes disagree, the report is later and wins.
Every quantitative claim in Part III is measured at the release tag;
where a number comes from a working note instead, it carries the note's
name. Two boundaries are declared rather than hidden: the fit requires
the solver repository at the pinned commit above, and rings 2–4 require
survey microdata obtainable by anyone but through a manual request
(§III.1). Part V describes work in progress and is expected to change.
