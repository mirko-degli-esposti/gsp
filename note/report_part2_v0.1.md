# Part II — Sources and their certification
## Draft v0.1 — §II.1, II.2, II.3, II.5 (19 August 2026)

> Same conventions as Part III: **[m]** measured, **[n]** from a note
> (cited), **[v]** to be verified before freezing. Table II.2a is generated
> from the registry by `scripts/diagnostica/tabella_fonti.py` and is not
> reproduced here; §II.4 (source → ring → column) awaits the registry
> corrections in progress. Note names refer to `note/` in the GSP repository.

---

### II.1 The registry as a method

Every external input to the pipeline is an entry in `fonti/registro.yaml`.
There are thirty-nine at the tag `report-v1.0-rc1` **[m]**. An entry records
what the file *is* (issuing body, title, URL, date of access, licence and
attribution string), what it *contains* (universe, unit of observation,
temporal reference), how it is *stored* (in git, on the local disk, or only
as a fingerprint with a remote location), which code *reads* it, and — the
two fields that carry judgement — what it may be used for (`usabile_per`)
and what it must not be used for (`non_usabile_per`). 



Both take values from a controlled vocabulary — sixty-one positive tags,
sixty negative, at the release tag **[m]** — and the near-symmetry is
itself the finding: in this registry the *negative* affordances are
declared as systematically as the positive ones, where common practice
records only what a source is for and lets the misuses be discovered by
whoever commits them. The negative field is where the reasons live.
`confronto_diretto_con_anagrafe_stesso_anno` on every census table says
that the population register at 1 January of year N and the permanent
census at 31 December of year N−1 describe the same instant and must not
be compared as if they were a year apart; `paese_di_dettaglio` on a
municipal table says that it gives the area of citizenship but not the
country; `conteggi_di_popolazione` and `residenti` on the civic-address
register say that a civic number is a place, not a household and not a
count of anyone. These negative affordances are declared at the source,
once, and the normalisers enforce them.

Three rules follow from treating the registry as the authority rather than
as documentation.

*The raw file is immutable; the normaliser is versioned code.* Nothing is
ever edited in a downloaded file. Every transformation — decoding,
reshaping, filtering of aggregate rows — is a function in `gsp.fonti`
with a name recorded in the entry, so that the same raw file and the
same commit produce the same normalised table. Where a file must be
replaced, it is re-fetched and re-fingerprinted, never patched: Ravenna's
citizenship table, flagged stale in the working notes, was re-fetched
during the licence-certification round (access date 2026-08-11) and its
entry updated **[m]**.

*Storage level is declared, and the fingerprint is the invariant.* Small
redistributable files (under a few megabytes: code lists, track records, the
two Florence surname tables) live in git. Large public files (SDMX extracts,
census sections, ANNCSU, AVQ microdata) live on disk and are re-fetched by
the acquisition scripts; the registry holds their SHA-256. Files that may
not be redistributed (the Parma municipal microdata) are also fingerprinted,
so that a reader who obtains them through the same channel can verify they
have the same file. `python -m gsp.fonti --verifica` checks every
fingerprint against the disk; on a fresh clone most entries report *solo
impronta* — the hash is known, the file is not present — and this is the
normal state of a clone, not an error. A state that always fails is a state
nobody looks at; the distinction between *missing* and *different* is what
keeps the check alive **[n]** `fonti_e_pacchetto_v8` §1.
A fresh clone is not merely a degraded state but a diagnostic in its
own right: it verifies the *declarations*, not the files, and during
testing it caught a source whose `archiviazione` field said `git`
while its own licence note declared the opposite — an inconsistency
invisible on a machine where the file happens to be present.

*Artefacts do not contain their generation time.* A derived file that
embedded a timestamp would hash differently at every run even when its
numbers were identical, and the registry would lose the one comparison that
matters — *regenerated equal* against *regenerated different*. This is why
derived sources (`avq_medie_nazionali`, `repertorio_nuclei_v1`) are registered
like any other, with a `derivato_da` pointing to their inputs, and why the
same rule governs populations and bundles (§III.1).

Two commands audit the whole. `--copertura` verifies that every
municipality in the registry has every source it needs, by instance;
`--pubblico` lists what may be redistributed and under which licence, and
what may not, with the reason. At the release tag both pass **[m]**:
no blocking entry; every licence resolved against its portal of origin —
one declared as *presumed* (Forlì, whose portal states no licence of its
own and inherits the site-wide CC-BY-4.0), a presumption recorded as
such in the entry rather than silently upgraded; and two entries whose
terms explicitly forbid redistribution (the EU-SILC public-use files),
registered for exploration only (§II.5).



### II.2 Families of sources and their legal condition

Table II.2a lists the thirty-nine entries with issuing body, universe,
temporal reference, licence, storage level, consuming code and the ring (or
rings) each one feeds. Here we describe them by family, and in particular
the legal ground on which each stands, because this — not the method — is
what a reader deciding whether to reuse the populations needs to know.

**ISTAT dissemination tables via SDMX (eleven tables, twelve
municipalities).** CC-BY-4.0. Ten are from the permanent census at 31
December of year N−1 and one — sex × age × marital status — from the
population register at 1 January of year N; the two series are offset by one
year because they describe the same seven instants. The register table is
the only *hard* constraint of ring 1; the census tables are *soft*. The
service allows about four queries per minute, and violations have led to
multi-day IP blocks; the acquisition scripts respect the rate, and the
catalogue of dataflows and the SDMX structure files are cached locally
(120 MB) but not yet registered — they are an index of what exists, not
data **[n]** `fonti_e_pacchetto_v8` §3, §13.4.

**Census sections (Basi Territoriali).** CC-BY-4.0. Geometry of the 2021
census, counts of the 2023 permanent census: 135,725 sections in the three
regions covered, 18.35 M residents, 10,872 sections with no residents
**[n]**. The 138-column track record is registered as a source in its own
right, because it is the file that gives meaning to the other.

**ANNCSU, the national register of civic addresses.** This is the source
with the strongest legal position in the registry: a *high-value dataset*
under Regulation (EU) 2023/138, whose technical specifications were adopted
after a favourable opinion of the Italian data-protection authority
(12 December 2024). The opening of these data has been examined by the
competent authority; what the pipeline does with them — draw one civic
number uniformly within a section — adds nothing to what the source already
discloses **[n]** `fonti_e_pacchetto_v8` §3.

**AVQ public-use microdata (2022–2024).** The licence is inferred, not read:
the survey page declares none of its own and the site's general CC-BY-4.0
applies. Inside each annual archive the `Leggimi` qualifies the files as
*ad uso pubblico*, the least restrictive class, and neither it nor the four
accompanying PDFs impose conditions of use or clauses on re-identification
**[n]** `fonti_e_pacchetto_v8` §3. What matters for disclosure is that the
only real vector inside a synthetic record — the donated AVQ vector — is
protected at the source, by ISTAT, before it reaches the pipeline; the
hot-deck copies a whole public-use record and nothing more. The weight
`COEFIN` carries four implicit decimals, recorded in the entry as
`scala_peso`.

**Municipal open data (six portals) and one register extract.** Five
municipalities publish residents by citizenship at sub-municipal level
(Bologna by statistical zone; Brescia and Forlì by neighbourhood;
Ravenna by area; Reggio nell'Emilia by circoscrizione), and Modena
publishes the stock of first names by sex; these feed the
country-of-citizenship tiers of ring 2 and, for Bologna, the
zone–neighbourhood hierarchy of ring 3. Their licences were resolved
portal by portal during certification **[m]**: CC-BY-4.0 (Bologna,
Brescia, Modena), CC-BY (Reggio), public domain (Ravenna), and one
declared presumption (Forlì, §II.1). Two vintages are declared as
limits: Forlì's table refers to 2021, and Reggio's to 2013 — thirteen
years older than everything else, the only sub-municipal source
available there; the tiers use these tables for the *composition* of
the foreign population while every total comes from the census margin,
which bounds but does not cancel the staleness (§II.4). One source in
this family is different in kind: **the Parma register extract**, a
full extract of the municipal population register (one row per
resident, 202,111 rows, reference 1 January 2025), published by the
Comune di Parma as open data under CC-BY-4.0 with its codebook. It is
registered, fingerprinted, and *not mirrored here* — a reader obtains
it from the source and verifies the fingerprint; it serves in
production as the IPF margin and the section-level country conditional
(tier 3), and as the external validation source for ring 4 (§I.5,
§III.3). What this repository redistributes are aggregate statistics
and a synthetic population, never the extract.

**ISTAT census 2011 (two tables) and the CLAIST classification.**
CC-BY-4.0. They feed the derived layers only: `cens2011_caratt_attl`
(occupied residents by fourteen dimensions, 94 MB of codes) gives the joint
sector × position distribution behind `gsp.lavoro`; `cens2011_titolo_studio`
gives 458 education titles in a tree declared by the source (399 leaves);
CLAIST 2026 is the current vocabulary and the historicised ordering that
places a title in its cohort. None adds information beyond rings 1–4; they
render it **[n]** `fonti_e_pacchetto_v8` §6, §9.

**Onomastic repertoires (seven).** Surnames of Florence 2012 and 2013
(CC-BY-4.0, DCAT metadata, `notPlanned`; 375,371 residents, 66,353 distinct
surnames, 51 % hapax; the 2012 table is used only as a stability check,
r = 0.9985); first names of Modena (CC-BY-4.0 via the regional portal);
the CC0 `popular_names` lists (2,278 surnames from 75 countries, 2,370
first names from 106, with romanisation and sex); two CC-BY-SA MediaWiki
category lists for Maghrebi and Yoruba surnames (65 and 107 entries —
lists, not distributions). Names are a derived layer: plausible by
construction and therefore collident, as the disclosure argument requires
(§I.7) **[n]** `fonti_e_pacchetto_v8` §3.

**Civil unions 2023 and the household repertoire.** ISTAT's exhaustive
survey of civil unions (CC-BY-4.0) and the derived repertoire of household
configurations (`repertorio_nuclei_v1`, built from AVQ, CC-BY-4.0 by
inheritance) feed ring 4.

**EU-SILC public-use files (two entries).** Registered for exploration
only. Access is public on acceptance of a disclaimer that is *not* an open
licence and does not allow redistribution; the text is kept beside the data.
They feed no ring; they document a decision not yet taken (income and
living conditions, §III.5).

**Derived sources of the project itself.** National means of the AVQ
battery (`avq_medie_nazionali`, used only by the viewer) and the household
repertoire are registered as sources with `derivato_da`, so that the same
verification applies to what the project produces as to what it downloads.

### II.3 Eighteen normalisers, and what running them found

The registry names a normaliser per entry — eighteen distinct ones at
the release tag **[m]**, one per source *form* (SDMX extracts, section
workbooks, microdata, matrices, codebooks, onomastic lists, …) rather
than per source. The value of writing them was less the uniform output
than the anomalies they surfaced, none of which would have been found by
reading the documentation. A selection, one per family where there is
one worth reporting **[n]** `fonti_e_pacchetto_v8` §3–4, §14;
`nota_nucleo_familiare_v3` §2:

- In `DICA_CARATT_ATTL` the code for *total* is not uniform across
  dimensions — `ALL` for occupation and citizenship, `99` for profile and
  education, `0010` for ATECO, `9` for sex and regime, `TOTAL` for duration.
  A reader that assumes one of them filters everything away and gets zero
  rows, which looks like a data problem and is a filter problem.
- The same ISTAT archive (`DICA_TITSTUDIO`) contains codebooks in UTF-16
  with BOM and the data file in UTF-8 without: reading the first
  successfully fails on the second.
- Modena's CKAN catalogue says *names given to newborns, 2012–2022*; the
  data are the *stock* of residents (1,390 Antonios in 2015 are not
  newborns) and run to 2024; the two sex-specific files carry CKAN
  timestamps two and a half years apart, decoded from the `hash` field;
  the WFS adds four service columns, one of which is the centroid of
  Modena repeated 650 times. The catalogue was wrong on what, when, and
  how many columns — and the data were good: the lesson is to certify
  the file, not its description.
- Parma's `Ncomp` showed impossible values — 319, 111, 110, 108, 40 — each
  appearing exactly that many times: the signature of a collective household
  (319 residents of an institution all carry `Ncomp = 319`), not a defect.
  Conditioning on `Tipores = 1` brings the maximum from 319 to 12.
- Parma's codebook, supplied with the data, declares for `Relpar` a
  29-code classification that the data contradict: the file uses eleven
  contiguous codes and nothing above; under the declared labels the code for
  *great-grandchild* has a median age of 80 and the code for *sibling* a
  median age of 13. The codebook describes the current extended
  classification; the extract carries a shorter, inherited one. The mapping
  actually used was inferred from the demographic profile, is marked
  *inferita, non letta* in the note, and is solid for the three codes that
  cover 90 % of the records and conjectural for the rest.
- In the municipal tables, the sum of observations is two to eight times
  the population because aggregate rows are included: the figure is a
  signature for recognising the file, not a count.
- The one-year offset between the population register (1 January N) and
  the census (31 December N−1) is recorded as `riferimento_temporale` and
  `anno_usato` per entry, and is the reason for the `non_usabile_per` tag
  above.

The general lesson, which the project turned into a principle, is that
*the meaning of a quantity belongs to whoever produces it*, and a
generic structure does not guess it: `modalita` on Reggio's matrix (26
nationalities or 104 long rows), `n_misurato` on codebooks (rows or
fields), the sum of weights on national means (82 or 23) — each time the
normaliser's diagnostic wins over the assumption. It is the registry's
face of a rule the reader has already met twice: the declared hierarchy
beats the deduced one, as with the census title tree whose parent column
crosses the code groups (§I.6), and the two-branch cross-check that
caught what no single-branch test could (§I.1, §I.3) **[n]**
`fonti_e_pacchetto_v8` §12.

### II.5 What is registered and not used, and what is used and not registered

Registered and not used: `istat_cens_posizione_famiglia` (position in the
household from the census), present because it was examined for ring 4 and
rejected in favour of the section-level household counts (§I.5); and the two
EU-SILC entries, registered for exploration. Used in production and
registered: everything else. Every licence resolved (§II.2) Deliberately outside the registry:
sources consulted and not used (the project keeps a separate consultation
list in the notes); the experimental K10C constraint set; San Vito dei
Normanni, which has no sub-municipal articulation and is not in production.

---

### Open items for Part II

1. **[v]** Licences of the six municipal open-data sources → registry;
   Parma supply → terms with the Comune.
2. **[v]** Register the SDMX catalogue and structure directories as an index
   source (no fingerprint of 120 MB; a manifest).
3. §II.4 table (source → ring → column): generate from the registry and the
   column schema of Appendix A once the registry round is closed.
4. Confirm counts quoted from `fonti_e_pacchetto_v8` (sections, residents,
   hapax share) against the current normaliser output — they date from the
   37-source version of the note.
