# Part IV — The Animarium release
## Draft v1 — §IV.1–IV.3 (25 August 2026)

> Same conventions: **[m]** measured (rebuild of 19 August at
> `report-v1.0-rc1`), **[n]** from a note (cited), **[v]** to verify before
> freezing. Main source: `design_animarium_v13`; section references without
> other indication are to that note.

---

### IV.1 What the viewer is

Animarium is a single hand-written HTML page. There is no framework, no
build step, no bundler: the page loads DuckDB-WASM from a CDN, reads the
Parquet bundle over HTTP range requests, and draws bars in HTML/CSS, the map
on a canvas, and the export SVG by hand. The choice is deliberate and
load-bearing. A static page served from a folder is the most reproducible
artefact a viewer can be — anyone can serve it locally with the range-aware
server in `build/serve_range.py` — and the absence of a dependency graph is
what allows the sentence, verified in §III.2, that the site online is a pure
function of the tagged bundle. The one exception is external and *opt-in*: the cartographic base layer,
off by default. The panel draws its maps on an empty background — the
choropleth and the point layers are drawn by the page itself — and a
reader who switches a tile provider on (OpenStreetMap or CARTO,
attributed on the canvas) is told it is an external service. Serving a
static PMTiles extract alongside the bundle — one file, range requests,
the same mechanism the Parquet already uses — is the designed v1.1
replacement that removes the last external dependency **[n]** §7.3,
`nota_pmtiles_v0.1`.

The regional atlas is the case where the empty background costs most —
eleven municipalities on a wide area, with no coastline or provincial
boundary to anchor them — and in v1.0 it inherits whatever the map
panel is set to, with its own selector. The PMTiles extract of v1.1
resolves it properly: a base layer served from the same origin as the
bundle can be on by default, because it introduces no external
dependency.

The panel is organised around one idea: *every number on screen carries its
comparison*. Filters are the bars themselves — clicking a bar filters, the
active filters become removable pills, and the entire state lives in the
URL, so that a view can be sent in one line and cited in a paper. Each
marginal shows up to three markers, with three meanings: the **bar** is the
filtered subpopulation; the **tick** is the whole city, and the gap between
bar and tick measures the *association* between filter and attribute; the
**diamond** is the census count at the filter's level, and the gap between
bar and diamond measures the *model error*. The diamond exists only where a
block of the constraint set contains the filter's attributes together with
the displayed one — 67 of 333 attribute pairs at K9C, 26 of 96 at K6C, a
property of the constraint template, not of the municipality **[n]** §3.4 —
and where it does not exist the panel says so instead of hiding it. The
institutional-trust view draws, for each of the fifteen items, the mean and
two overlaid confidence bands: a thin one computed on `n` and a thick one on
Kish's effective sample size for that variable's universe. The distance
between the two bands is the honest cost of hot-deck donation made visible —
on Modena, unfiltered, the true band is seven times the naive one **[n]**
§4.7, §2.1 — and dotted ticks mark the national means, computed by GSP from
the microdata and registered as a derived source. The individual card shows
the forty-odd fields of a record grouped by ring, each with its guarantee
class, under a banner that reads **SYNTHETIC INDIVIDUAL — DOES NOT EXIST**;
clicking two nearby points on the map and finding the same donor signature
is `n_eff` seen with the naked eye **[n]** §4.4. A regional atlas opens a
card per municipality — individuals, articulation, tier, coverage with its
denominator, and the `n`/`n_eff` band translated into a sentence — before
switching city.

Two things the panel deliberately cannot do. It cannot filter or display
the detailed education title or the sector × position pair: those are
derivations that individuate a *person*, they live in the `persona` and
`narrativo` regimes, and the bundle does not carry them (§IV.2). And it
cannot show any sub-municipal geography of an AVQ variable as if it were
information: the donated vector carries no geography by construction
(assumption 6), so under a spatial filter every AVQ difference is
compositional, and the panel states this in so many words **[n]** §4.7.

### IV.2 The public bundle

The bundle is one folder: an index (`comuni.json`), and per municipality a
`pop.parquet`, a `manifest.json` with labels, declared orderings and
unfiltered counts, and a `riferimenti.json` with the census counts extracted
from the constraint set (`n = α × N`). Eleven municipalities, ≈ 35 MB
**[m]**, rebuilt in one command (`build/build_bundle.py`).

The Parquet layout is designed for the reader, in the literal sense:
DuckDB-WASM fetches contiguous byte ranges, not columns, so the columns are
laid out in three blocks by use — filters and marginals; the AVQ battery
with the donor signature; the heavy map columns — and the rows are sorted by
`zona, sezione` in row groups of 20,000, so that

    cost(query) = footer + Σ weight(block) × (row groups not pruned / total).

Later filters inside a block cost zero bytes and 100–220 ms; the map and the
trust battery are lazy and paid only on request. On Modena the source CSV of
57.8 MB becomes a 3.5 MB Parquet (6 %), and the cost model was verified by
counting bytes with the range-aware server before the design was accepted
**[n]** §3.2, §7.2.
In practice a visitor downloads ≈ 2.5 MB of the 37 MB bundle [m]: the blocks never touched are never read.
**The public regime is enforced in the data, not in a banner.** The panel
always stated that assigning an individual to a civic number carries no
information — the model places people within a section arbitrarily — but a
banner does not travel with a file, and `pop.parquet` is served statically
to anyone with the URL. Since 4 August 2026 the default output of
`to_parquet.py` *is* the public regime, applied by the single enforcement
point `gsp.individui.esporta_pubblico` (§I.7): `lon`/`lat` are a random
point within the census section, drawn with a seed derived from the
municipality code; `via`, `civico` and the address provenance are absent —
the individual card reads "Cittadella, section 034027001042" and loses
nothing analytic; `quartiere` is absent, being one-to-one with `zona` and
already provided as a label by the manifest; `uid` is absent, being the
onomastic key, and the viewer shows no names. The randomisation loses
nothing because the civic assignment was already uniform within the section:
the map is visually identical, the per-section density unchanged, and the
file becomes self-protecting — "the point is random within the section"
admits no reply, where "displaced by thirty metres" invites the question
"and if it were twenty?" **[n]** §15. The permissive export exists
(`--completo`) but is an explicit act with a warning, not a default that can
be forgotten.

What is *not* in the bundle, by the same logic: the AVQ raw codes (dropped
after the donor signature is computed), the detailed education title and the
sector × position pair, and anything from the `narrativo` regime. The
complete population with true civic numbers never leaves the generation
machine (§I.7).

A view is citable. The whole state of the panel — municipality, filters,
open views, map mode — is the URL query string, so a figure in a paper can
carry the exact view that produced it, and the version-binding table (front
matter) ties that URL to a bundle whose Parquet hashes are recorded. The
citation of a view is therefore URL + report version + the SHA-256
prefix of that municipality's `pop.parquet`; the recommended form, with
a worked example, is in the front matter.

### IV.3 Deployment and versioning

What the viewer *requires* of a host is a short list, and it is worth
stating before naming any platform: static file serving over HTTPS, HTTP
**range requests** (the mechanism by which DuckDB-WASM reads parts of a
Parquet instead of downloading it whole, and by which PMTiles will serve
tiles in v1.1), and no ceiling on individual file size. No server-side
runtime, no database, no build step. Any host meeting those three
conditions can serve Animarium, including a laptop: `build/serve_range.py`
in the repository is a range-aware server written for exactly this
purpose. The second of the three fails silently when it is missing, so the
deployed folder carries its own test: `smoke.html` checks that the host
answers range requests. Without them nothing breaks — DuckDB simply
downloads whole files, and the app is merely slow, with nothing on
screen to say why.

The release is served from Cloudflare Pages under the project's own
domain, **animarium.it** — the canonical address, with `www`
redirecting to it.Deployment is one command, `python build/deploy.py --cloudflare`: the
script assembles the `deploy/` folder from the bundle on disk and hands
it to Wrangler, so that assembly and upload cannot drift apart — a
half-regenerated bundle would otherwise go online silently, which is
also why `build_bundle.py` reports per-municipality status instead of
stopping at the first failure **[n]** §8, §15. A second, non-canonical
path (`--gh-pages`) survives from an earlier configuration and is kept
only as a fallback.
The folder-based deploy is kept
because it leaves nothing to clean and can actually be switched off; the
domain is registered independently of the platform, so the citable URLs
of this report survive a change of host. Switching the site off does not
withdraw what has already been downloaded, and the report says so rather
than implying permanence.

Versioning binds three objects: the repository tags (`report-v1.0` on both
GSP and Animarium), the bundle (SHA-256 per `pop.parquet`, listed in the
front matter; the two JSON files per municipality embed a generation
timestamp and are excluded from the binding — compared modulo that field in
§III.2), and the deployed site, which is the `deploy/` folder produced from
that bundle. The build dependency is declared, not assumed: Animarium's
`pyproject.toml` depends on `gsp`, and the build scripts obtain every path
from `gsp.common` (overridable via `GSP_ROOT`); the *runtime* has no
dependency at all — the published site is static, and a reader with only the
Zenodo bundle can serve the viewer without installing GSP (the two entry
points of the repository README). If GSP were ever unavailable, the site
would keep working and the build would stop being reproducible from outside;
this is said rather than solved **[n]** §7.1.

---

### Open items for Part IV

1. **[v]** Re-measure the §7.2 cost figures (init, first query, lazy loads)
   on the rebuilt eleven-city bundle — the quoted numbers date from the
   four-city era of the design note; expected unchanged per municipality,
   but the atlas adds an index fetch.
2. **[v]** Screenshots for the report: three figures (marginals with three
   markers; trust with two bands; map in quota mode) taken from the
   deployed `report-v1.0` site at a fixed URL each, so the captions can
   carry the very URL they show.
3. **[v]** Indexing policy: the page currently carries `noindex,
   noarchive`, adopted while the site was a private draft. With a public
   release under its own domain the decision has to be taken explicitly
   rather than inherited.
4. PMTiles base layer (v1.1): recipe written, one file per region on R2,
   registered as a derived source with its ODbL attribution **[n]**
   `nota_pmtiles_v0.1`.

*Closed for v1.0:* the citation format for a view (front matter, with a
worked example); the cartographic base layer, resolved as off-by-default
with opt-in providers and PMTiles queued for v1.1 (§IV.1).
