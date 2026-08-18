# scripts/ — what runs, what measures, what explores

Every script in this folder is kept, including the ones the current pipeline no
longer needs: an exploratory script that produced a number quoted in a note is
part of the record. To tell them apart, each script belongs to one of four
groups.

## 1. Rebuild chain

The scripts that produce a population from a clean clone, in this order. The
full command sequence with expected runtimes is in the technical report,
Appendix C.

| step | script | ring |
|---|---|---|
| fetch ISTAT SDMX tables and municipal open data | `acquisizione/fetch_comune.py`, `acquisizione/istat_catalog.py`, `acquisizione/scarica_cognomi_wiki.py` | inputs |
| build constraint sets and zone / section tables | `vincoli/build_constraints.py`, `vincoli/cs_build.py`, `vincoli/build_zona_tables.py`, `vincoli/build_sezioni.py`, `vincoli/join_civici_sezioni.py` | 1, 3 |
| fit the maximum-entropy model | `fit/fit_cs.py` | 1 |
| donate AVQ vectors, assign citizenship, enrich, build households | `attributi/assign_avq.py`, `attributi/assign_nationality.py`, `attributi/enrich.py`, `attributi/assign_nucleo.py` | 2–4 |
| national reference means for the viewer | `riferimenti/medie_nazionali.py` | — |
| registry maintenance | `riempi_sha.py` | — |

## 2. Measurements cited in the report

Diagnostics whose output appears as a number, table or figure in the notes and
in the technical report. Reproducing a table means re-running one of these.

| script | measures |
|---|---|
| `diagnostica/verifica_vincoli.py` | MRE by constraint block, sampling floor, z-scores (ring 1) |
| `diagnostica/verifica_donor.py`, `diagnostica/avq_firme.py` | effective sample size by variable universe, donor signatures (ring 2) |
| `diagnostica/misura_composizioni.py`, `diagnostica/perm_composizione.py` | compositional signal by zone partition and its permutation null (ring 3) |
| `diagnostica/misura_em.py` | total-variation distance of migratory-background variables at section level |
| `diagnostica/misura_nucleo.py`, `diagnostica/misura_nucleo_m4.py`, `diagnostica/collaudo_nucleo.py`, `diagnostica/avq_nuclei.py`, `diagnostica/parma_codice11.py` | ring 4: household size and composition, validation on Parma, codebook check |
| `diagnostica/diag_istruzione_eta.py` | impossible age × education combinations (the α = 0 exclusions) |
| `diagnostica/diag_quinq.py` | the five-year age seam |
| `narrativa/*` | persona rendering and LLM experiments; see `../dati/README.md` |

## 3. Exploratory

Kept for the record; not part of the rebuild chain and not cited in the
report. Some are superseded by package modules (e.g. `proto_assembla.py` by
`gsp.nucleo`).

`diagnostica/ispeziona_avq.py`, `diagnostica/ispeziona_cs.py`,
`diagnostica/zona_probe.py`, `diagnostica/residuo.py`,
`diagnostica/misura_assorbimento.py`, `diagnostica/placebo_assorbimento.py`,
`diagnostica/proto_assembla.py`, `diagnostica/avq_configurazioni.py`,
`diagnostica/eusilc_grafo.py`, `riordina_note.py`.

## Solver laboratory

`gibbs/` — `gibbs_lab.py`, `profile_gibbs.py`, `test_invariance.py`,
`test_moves.py`: experiments on the GibbsPCD solver run on the municipal
constraint sets (mixing, invariance of the fit, move sets, profiling). They
depend on `gsp` and on the municipalities' `cs_*.json`, which is why they live
here rather than in the method repository
(`github.com/mirko-degli-esposti/maxent-popsynth-pcd`). Where one of them
produced a number quoted in the report (e.g. the Ravenna intermediate case),
it is cited as such.
