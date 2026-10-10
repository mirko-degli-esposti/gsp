# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

GSP builds synthetic populations of Italian municipalities (comuni) from public ISTAT aggregates and municipal open data. It is the production pipeline behind the Animarium viewer (a separate repo, `~/progetti/animarium`, which holds `bundle/`). Code, comments, CLI flags and notes are in **Italian**; keep new code and comments in Italian to match. The README and `scripts/README.md` are in English and are the best short overview.

## Setup and environment

```bash
conda activate gsp && pip install -e .     # Python >=3.11, package in src/gsp
```

- Project root comes from `GSP_ROOT` (default `~/progetti/gsp`). All paths are derived in `gsp.common` (`DATA`, `COMUNI_DIR`, `SUBMUN`, …). `GSP_COMUNI_DIR` relocates only the per-comune products (`COMUNI_DIR`: constraints, populations) and `GSP_SUBMUN_DIR` the section tables (`SUBMUN`), for external experiments that must never write into `data/`. Exception: `src/gsp/istat/sdmx.py` hardcodes `~/progetti/gsp/data/...` for its cache.
- `scripts/fit/fit_cs.py` imports the solver from a sibling clone `~/progetti/maxent-popsynth-pcd` via `sys.path`. It does not check the version, so the pinned commit has to be checked out by hand.
- `data/`, `bundle/`, `log/`, `regress/` and `*.csv` are git-ignored. Heavy inputs and every generated population live under `data/` and are not versioned. The one exception is `fonti/grezzi/*.csv`, which is re-included on purpose.

## Commands

There is no test suite or linter. Correctness is checked with registry audits, determinism checks and the diagnostic scripts.

```bash
python -m gsp.fonti --verifica        # SHA-256 of every registered source vs disk ("solo impronta" = raw not on disk, normal)
python -m gsp.fonti --copertura       # every comune has the sources it needs
python -m gsp.fonti --pubblico        # what may be redistributed, under which licence
python -m gsp.common --check [COD]    # sanity-check the comune registry / paths
python -m gsp.common --righe-rigenera # codice:livello:pool rows consumed by rigenera.sh

scripts/rigenera.sh [COD ...]         # full chain rings 1–4, per comune (6-digit ISTAT code, e.g. 037006)
scripts/rigenera.sh --dry-run         # print commands only
scripts/rigenera.sh --from avq|enrich|nucleo   # restart from a later stage
scripts/rigenera.sh --confronta <archive>      # byte-compare outputs with an archive (determinism test)
bash scripts/diagnostica_report.sh [COD ...]   # report measurements -> note/misure/diagnostica_report_v1.0/
scripts/todo.sh "testo" [tag]         # append an item to note/TODO.md
```

`rigenera.sh` overwrites products in `data/comuni/<COD>/` and never deletes anything. Back up `data/comuni/` before a full run (see `--help`). A run counts as citable only if `git status` is clean, and it records HEAD in `log/rigenera_<stamp>/commit.txt`. Always run `fit_cs.py` with the production flags from `rigenera.sh` (`--eps 1e-8 --min-alpha 2e-4 --outer 500 --numba --sparse --tol 0 --sweeps 40 --no-gibbs --pool N`). Its bare defaults take a much slower path.

## Architecture

**Four rings per comune**, run in order by `rigenera.sh`:

1. **Ring 1: joint demographics (MaxEnt).** `acquisizione/fetch_comune.py` (ISTAT SDMX) → `vincoli/build_sezioni.py` → `vincoli/build_constraints.py` (c1–c10 tables) → `vincoli/build_zona_tables.py` (z1–z6, articulated comuni only) → `vincoli/cs_build.py --livello K?C --esclusioni` (`cs_<LIV>.json`) → `fit/fit_cs.py`, which writes `data/comuni/<COD>/constraints_2024/popolazione_<LIV>.csv`. `rigenera.sh` runs the three preparatory steps only when their product is missing.
2. **Ring 2: AVQ donation.** `attributi/assign_avq.py` hot-decks whole ISTAT AVQ microdata vectors onto individuals (`popolazione_<LIV>_avq.csv`). `assign_nationality.py` assigns the country of citizenship.
3. **Ring 3: sub-municipal placement.** `attributi/enrich.py` assigns the census section, single-year age and address, and writes `..._avq_full.csv`.
4. **Ring 4: households.** `attributi/assign_nucleo.py` (logic in `gsp.nucleo`) writes `data/nuclei/nuclei_<COD>.csv`.

`livello` (K6C = not articulated into zones; K9C and others = articulated) chooses the constraint set and appears in every file name. K10C is an abandoned experiment. Skip it.

**Registries: data, not code.**
- `flotta/comuni.yaml` is the single registry of comuni (name, slug, region, pool, level, zone names, status `flotta|collaudo|pilota|…`). It is loaded by `gsp.common` (`G.info(cod)`, `G.COMUNI`), and `rigenera.sh` derives its list from it. **Codes must always be quoted strings**: YAML 1.1 reads an unquoted `015146` as octal. Adding a comune means adding one entry here (plus a zone-name map if articulated). The README describes the procedure, and `note/collaudo_acquisizione_v0.2.md` records how it was tested.
- `fonti/registro.yaml` has one entry per external source (licence, SHA-256, allowed uses). Fingerprints go in `fonti/impronte/`, and normalisers in `gsp/fonti/normalizzatori.py`. Raw files are immutable. `scripts/riempi_sha.py` fills in the hashes.
- `campagne/manifest_er_2026.yaml` is managed by `gsp.campagna` and `gsp.campagna_fetch`. It tracks the per-table acquisition state (`mancante → scaricata|shadow → validata`, or `DIVERGE`) while the fleet is extended. The gate is derived from those states, never set by hand. Files are written atomically, cells are updated rather than replaced, and the emitter prints fragments instead of writing them.
- `gsp.common.IMPOSSIBILI` lists the impossible attribute combinations (α=0 exclusions). `rigenera.sh` checks for them at the end of every run.

**Publication regimes.** Every export goes through `gsp.individui` (`esporta_pubblico`, `campione`), which applies one of three regimes: `pubblico`, `persona` or `narrativo`. Do not let consumers read population CSVs and decide for themselves what to expose. Names and addresses must never enter public outputs or the files under `dati/agenti/`.

**ISTAT SDMX rate limit.** All SDMX access goes through `gsp.istat.sdmx`, which enforces `MIN_INTERVAL = 13`s between requests. Never bypass or lower it: violations lead to IP blocks lasting several days.

**Determinism.** Every seed is declared, either as a constant or derived from the comune code. Two runs on the same inputs and commit must give byte-identical outputs, and `--confronta` checks this. Keep new randomness seeded the same way.

## scripts/ groups

`scripts/README.md` sorts scripts into four groups: the rebuild chain, measurements cited in the technical report (`diagnostica/`, `narrativa/`), exploratory scripts, and the solver lab (`gibbs/`, whose `test_*.py` files are experiments, not unit tests). Scripts are never deleted, because an exploratory script that produced a quoted number is part of the record. `scripts_archivio/` holds retired scripts, such as the old regression harness.

## note/ conventions

`note/` holds versioned working notes that the technical report cites by name and version (see `note/README.md`).
- A note that evolves is named `nome_vNN.md`, and only the highest version is current. Superseded versions go to `note/storico/` (`scripts/riordina_note.py`). Raw diagnostic output goes to `note/misure/`.
- A change of substance gets a new version that says at the top what it replaces and why. Fixing a path or a typo is a patch with no version bump.
- Mark every quantitative claim as *misurato* (with a log in `misure/`), *dichiarato* or *aperto*. Take numbers from a measurement, never from memory, and state which data and which command produced them.
- Never silently remove a falsified or withdrawn claim. Keep the original text and add a dated correction beside it. The same rule applies to code and data: corrections stay explicit.
- Where the report and a note disagree, the report wins.

## Git

Work happens on `dev-mirko`, and PRs target `master`. Local settings deny `git push origin` and remote edits.
