# GSP — Generative Synthetic Populations

Reproducible synthetic populations of Italian municipalities, built from
public ISTAT sources and municipal open data. This repository is the
production pipeline behind [Animarium](https://animarium.pages.dev), a
viewer for the resulting populations, and the code base documented in the
technical report *Animarium: an open, reproducible pipeline for synthetic
populations of Italian cities — from ISTAT sources to open data* (arXiv,
report v1.0, identifier to be added on release).

**Nothing in these populations describes a real person.** Every individual is
sampled from a joint distribution estimated from aggregate statistics; names,
where they appear, are drawn from public name repertoires and are collident by
construction. See *Disclosure* below.

## What the pipeline does

Four rings, applied in sequence to each municipality (`comune`), each with a
declared place for every attribute:

| ring | what | method | main sources |
|---|---|---|---|
| 1 | joint distribution of ten demographic attributes (sex, age, citizenship, education, occupational condition, marital status, zone, …) | maximum entropy, exact where the state space allows, persistent contrastive divergence (GibbsPCD) elsewhere | ISTAT census and register tables (SDMX), municipal open data by zone |
| 2 | attitudes, health, trust battery; country of citizenship | hot-deck donation of whole AVQ vectors, conditioned on a demographic signature; tiered geographic assignment | ISTAT *Aspetti della vita quotidiana* public-use microdata 2022–2024; municipal citizenship tables |
| 3 | sub-municipal placement: census section, single-year age, address | exact allocation within zone; uniform within section | ISTAT permanent census sections 2023; ANNCSU civic address register |
| 4 | households: `id_nucleo` and role | section-level size constraints + composition repertoire from AVQ | census household size distribution (PF3–PF8), AVQ, civil-union statistics |

Downstream layers derive sector, position, detailed education title,
names, and a biography; they add no information beyond rings 1–4 and are
labelled as derived.

Eleven municipalities are in production (Bologna, Brescia, Ferrara, Forlì,
Modena, Parma, Piacenza, Ravenna, Reggio Emilia, Rimini, Castenaso): about
1.9 M individuals and 0.9 M households.

## Repository layout

```
src/gsp/          the package: fonti (source registry), individui (publication regimes),
                  nucleo (households), lavoro, common …
scripts/
  acquisizione/   fetch ISTAT SDMX tables and open data           (ring 1 inputs)
  vincoli/        build constraint sets and zone/section tables    (ring 1, 3)
  fit/            fit the maximum-entropy model                    (ring 1)
  attributi/      AVQ donation, citizenship, enrichment, households (ring 2–4)
  riferimenti/    national reference means for the viewer
  diagnostica/    measurement scripts whose numbers appear in the report
  narrativa/      persona rendering and LLM experiments (see dati/README.md)
fonti/            source registry (registro.yaml), fingerprints, small redistributable raws
dati/             inputs and outputs of the LLM experiments
```

Heavy inputs (`data/`) and generated products (`bundle/`) are not versioned;
see *Reproducing*.

## Sources and their certification

Every external input is an entry in `fonti/registro.yaml`: universe, licence,
access date, SHA-256 fingerprint, and what it may and may not be used for.
Raw files are immutable; normalisers are versioned code. Three commands audit
the registry:

```bash
python -m gsp.fonti --verifica     # every fingerprint against the file on disk
python -m gsp.fonti --copertura    # every municipality has the sources it needs
python -m gsp.fonti --pubblico     # what may be redistributed, and under which licence
```

On a fresh clone most sources report *solo impronta*: the raw file is not in
git, only its fingerprint. This is the normal state, not an error; the raw is
re-downloaded by the acquisition scripts and checked against the fingerprint.

Attribution for all redistributed data is in `fonti/ATTRIBUZIONI.md`.

## Reproducing

```bash
git clone https://github.com/mirko-degli-esposti/gsp && cd gsp
conda create -n gsp python=3.11 && conda activate gsp
pip install -e .
python -m gsp.fonti --verifica
```

The full chain for one municipality (fetch → constraints → fit → AVQ →
citizenship → sections → households → bundle) is listed, with expected
runtimes, in Appendix C of the technical report.
Every random seed is derived from the municipality code; two runs on the same
inputs and commit produce byte-identical outputs. ISTAT's SDMX API is rate
limited (five queries per minute); the acquisition scripts respect a safe rate,
and violations lead to multi-day IP blocks.

Three municipalities are re-run for every tagged report version (Parma,
Castenaso, Bologna); the others carry the results of the run recorded in the
report, with date and commit.

## Publication regimes and disclosure

A generated population is exported in one of three regimes, enforced by a
single function (`gsp.individui.esporta_pubblico` / `campione`):

- **pubblico** — what the viewer and the open dataset expose: no name, no
  street or civic number, coordinates randomised within the census section.
- **persona** — prompt material for LLM agents: attributes and AVQ vector, no
  name or address.
- **narrativo** — full record with generated name and address, produced on
  demand, in dozens, never redistributed.

The argument in one paragraph: simulation from aggregates is not
anonymisation, because there is no microdata to anonymise; the only real
vector inside a synthetic record is the donated AVQ vector, and it is
protected at source by ISTAT's public-use release; the address carries no
information about anyone, because it is assigned uniformly within a section.
The residual risk is one of interpretation, and the viewer states on every
individual card that the person does not exist. The full argument is in the
technical report, Part I.7.

## Related work and citation

- Method for ring 1: *Scalable Maximum Entropy Population Synthesis via Persistent Contrastive Divergence*, arXiv:2603.27312 —
  code at `github.com/mirko-degli-esposti/maxent-popsynth-pcd`.
- *Calibrating the Instrument: Controllability of an LLM-Driven Synthetic Population*, arXiv:2607.00910.

Cite the technical report for the pipeline and the populations; `CITATION.cff`
has the machine-readable form. Software snapshots and the open dataset are
archived on Zenodo with DOIs (links added on release).

## Licence

Code: MIT (see `LICENSE`). Redistributed data and generated populations:
CC-BY-4.0, with the attributions in `fonti/ATTRIBUZIONI.md`. Sources used for
validation only (municipal microdata) are registered but not redistributed.

## Contact

Mirko Degli Esposti — Department of Physics and Astronomy, University of
Bologna — mirko.degliesposti@unibo.it
