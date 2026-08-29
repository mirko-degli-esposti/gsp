# Part V — The narrative layer and its use
## Version 1 — §V.1–V.3 (26 August 2026)

> **This part describes work in progress, and is the one part of this
> report expected to change substantially.** The narrative layer is
> built and in use, but its calibration is an open research programme:
> the experiments reported here are evidence that the platform behaves
> controllably, not results about synthetic populations as instruments.
> Findings, and the layer itself, will be updated in later versions of
> this report and in the companion papers; nothing downstream of the
> populations depends on it, and a reader interested only in the
> pipeline (Parts I–III) or the release (Part IV) can stop before this
> point. `registro_esperimento_sive_gsp_v5` is cited here as
> *registro*; the SIVE paper is arXiv:2607.00910.

---

### V.1 From record to persona

The narrative layer exists because a record and a readable individual are
different products, and the difference is exactly where control must not
be ceded. The rule that organises everything fits in one line:

> **The LLM does not generate the person. The person is generated
> statistically; the LLM generates one possible narrative rendering of
> it.**

The temptation is to hand the record to a language model and ask for a
biography. It works, and it is wrong for a precise reason: the model would
fill the gaps with its own idea of plausibility — opaque, unreproducible,
unmeasurable. With twenty-three AVQ attributes, the demographic profile
and a geography down to the section, the gaps are still many: precise
occupation, contract, household detail, transport, income. Whoever fills
them determines what the population appears to say, and that power does
not go to a language model **[n]** biografia §1. Hence three strata:

1. **The constrained profile** — the record as it is, immutable for the
   LLM, *including its declared limits*: the population does not know
   income or precise profession, and its variables have different
   geographic resolutions. A profile that does not carry its own limits
   produces a biography that asserts more than it knows.
2. **The structured expansion** — new variables from conditioned
   distributions, controlled catalogues and compatibility rules (the
   derived layers of §I.6, plus imputation where a narrative needs it);
   still a structured row, still no free text, each variable with a
   declared certainty class (A constrained / B measured / C imputed)
   **[n]** biografia §3.
3. **The narrative rendering** — only here does the LLM enter, realising
   linguistically a profile whose sociological plausibility is already
   fixed.

Two regimes consume this pipeline (§I.7): `persona` renders strata 1–2 as
prompt material for agents — attributes and AVQ vector, no name, no
address; `narrativo` adds the generated name, the address and the prose,
on demand, capped. The distinction is the one §I.6 argued: apparent
diversity must not be mistaken for real diversity, and the persona regime
is the one in which two agents with the same donor signature are still
*visibly* the same evidence.

### V.2 LLM-driven simulation as evidence of use, not as validation

Two studies have run on this platform's outputs. They are reported here
for what they demonstrate about the platform — that its populations
support controlled, replicated, pre-registered experiments on LLM agents —
and not for their findings' own sake, which belong to their papers.

**SIVE** (arXiv:2607.00910) asked whether an LLM-driven synthetic
population is *controllable*: impose a trust level on an agent, and the
agent exhibits it, stably, across the battery. Montelago, its fictional
municipality of 120 personas in three trust strata, predates the GSP
populations; its result — controllability, with compression of the
imposed scale — is the licence for everything that follows, and its
protocol (pre-registered criteria C1–C7, within-subjects design) is the
template the GSP experiments inherit.

**The Brescia conditions** moved the same question onto a real GSP
population and removed SIVE's confound: the SIVE prompt carried both a
direct label («sfiduciato critico») and a story encoding the latent
level; the ablation separates them. 120 employed individuals of synthetic
Brescia, stratified by `PUNTIFI10` (trust in municipal government,
0–10) into LOW/MED/HIGH — Brescia because what matters is how many
*distinct response vectors* exist, and the Lombardy pool (8,111 donors)
gives a replica share of 0.8 % against Parma's 5.8 % **[n]** registro §2.
Three conditions: **B** profile + a story encoding the latent level,
**C** profile alone, **D** profile + a neutral story. The stories
themselves went through a measured correction loop — the first prompt's
examples were taken as instructions and 49 stories of 50 staged the same
municipal counter; a twelve-scene repertoire fixed it, and the monotony
detector born there (count, don't read) became part of the harness
**[n]** registro §3.

What the platform made measurable **[n]** registro §4–5, on
`fiducia_istituzione`, T 0.3:

| condition | Spearman (latent → response) | slope | LOW / MED / HIGH medians |
|---|---|---|---|
| B story with latent | **+0.90** | 0.52 | 2.6 / 4.6 / 6.9 |
| C profile only | +0.06 | 0.00 | 5.0 / 5.1 / 5.1 |
| D neutral story | ~0 | 0.01 | 5.3 / 5.3 / 5.5 |

The narrative transmits the disposition (paired B−C: 40 of 40 negative in
LOW); the profile alone produces clones; and the *presence* of a narrative
does not unlock demographic priors — D's slope is zero — while its
residual positive valence (+0.30 intercept) was independently seen by
three blind human judges and three models: neutral stories describe
services that work, and the absence of friction is itself a signal
**[n]** registro §4, §7.

Replicated across three model families (DeepSeek, Claude Haiku 4.5,
GPT-4o-mini), the result splits into what travels and what does not
**[n]** registro §5: the gain of B is invariant within seven hundredths
(0.52 / 0.55 / 0.59) — the compression is a property of LLMs, not of one
model; the flatness of C is invariant; but the *level* of C spans 1.48
points (3.96 / 5.02 / 5.44). There is no prior on the people; there is a
prior on municipal institutions, and it differs by model. **Differences
and orderings are transportable across models; levels are not** — the one
sentence a practitioner should take from this Part.

Two further platform-enabled findings complete the picture. On
categorical items the profile *is* used, and used along textbook
stereotypes — fourteen times more anger in men, hope to the educated —
established at n = 600 after the n = 120 signal on age was falsified as
thin-cell noise **[n]** registro §9; the numeric-scale abstention is a
refuge the scale offers, not absence of priors. And the ground-state
design (what does the model answer when there is *no one*: 17 cells
instead of a 756-cell factorial) gives every profile effect its reference
point **[n]** registro §10.

The experimental materials are versioned with the pipeline
(`dati/agenti/`, `dati/campagne/`, `dati/giudizio/`; §II of the
repository's `dati/README.md`): agents in the persona regime, campaigns as
`uid` + responses, stories preserved as the actual input of the published
campaigns. The sample regenerates from `(comune, variabile, n, seed)`;
the stories do not, and are stored for that reason **[n]** registro §12.

**SimComm / Caffaro** is the application context these instruments were
calibrated for — institutional risk communication on the SIN
Brescia–Caffaro site — and is deliberately absent from this report beyond
this sentence: it is applied work in progress, with its own protocol and
its own paper.

### V.3 Intended uses, and the two warnings that travel with them

What the released populations support: compositional comparison across
municipalities and zones with honest uncertainty (the viewer's native
use); pre-testing of institutional communication on stratified synthetic
audiences, in the SIVE/Brescia mould — where the platform's contribution
is the *stratification with known ground truth*, which no convenience
panel offers; teaching, where a population that declares its assumptions
is the point.

What they do not support, stated as sharply as the argument allows: any
sub-municipal geography of an attitudinal variable read as information
(assumption 6 — the panel says it, the report repeats it); any claim
about a real address or a real person (§I.7); and any *absolute level*
read off an LLM agent — the 1.48-point model spread is the measured
refutation. Two agents sharing a donor signature are one piece of
evidence, however different their names read (§I.6).

The residual risk is interpretation, and the mitigations are in the
objects themselves: the banner on every card, the caps and on-demand
generation of the narrative regime, the warnings the sampling API emits
when a filter crosses a resolution boundary **[n]** piano §5. The report
adds the one mitigation a document can: this Part's claims are bounded by
its first paragraph — the platform renders and instruments; validation is
someone else's burden of proof, carried elsewhere.

---

### Open items for Part V

1.  Check the SIVE paper's exact terminology for the strata and
   criteria (C1–C7) against `sive_paper_v6` before freezing §V.2's second
   paragraph.
2. Decide whether the three-model table of registro §5 (gain /
   level / D−C per model) is reproduced in full or summarised as in the
   current text; if in full, table V.2a.
3.  The `emo_*` campaigns cite Claude Haiku 4.5 and GPT-4o-mini on
   `emozione` only — confirm which models ran the full BCD before naming
   all three in the stereotype paragraph (currently attributed to
   DeepSeek n=600 only, which is correct per registro §9).
4.  Cross-reference: `dati/README.md` section numbering after the
   repository restructuring.
