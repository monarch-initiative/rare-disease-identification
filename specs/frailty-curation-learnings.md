# Frailty curation — what we are learning

A running log, amended after every batch. It records what the curation is *teaching us about
the method*, not what it produced — the numbers are in `just frailty-stats`, and the claims are
in the list itself.

**Status:** 900 of 3,079 diseases curated (29.2%), through batch 7.

| Batch | Diseases | Literature line | Orphanet rows | Graded | Disputing |
|---|---|---|---|---|---|
| 1 (rank 1–50) | 50 | 24% | 7 | 16 | 4 |
| 2 (51–150) | 100 | 10% | 6 | 16 | 5 |
| 3 (151–300) | 150 | 3% | 18 | 22 | 3 |
| 4 (301–450) | 150 | 3% | 19 | 22 | **10** |
| 5 (451–600) | 150 | 2% | 13 | 15 | **6** |
| 6 (601–750) | 150 | 3% | 17 | 21 | **8** |
| 7 (751–900) | 150 | 3% | 14 | 17 | **9** |

Cumulative: **99 diseases** with an actionable level (`TOTAL`/`SUBSTANTIAL`), **41** carrying a
literature line, **50** carrying a line that argues *against* the score.

---

## 1. The literature lane does not scale. Orphanet does.

This was the pilot's open question and it is now settled. Quotable functional-outcome literature
fell from 24% to 2% as we worked down the ranking, while Orphanet coverage roughly held.

**Name recognition does not predict functional literature.** Batch 2 contained Krabbe, Sandhoff,
Zellweger, Batten, Alexander and Pitt-Hopkins — all well known, all returning plenty of papers,
almost none reporting what patients can *do*. They are characterised genetically and
biochemically. We predicted batch 2 would beat batch 1; it halved.

The two sources are close to complementary rather than overlapping. Orphanet covers recognisable
named syndromes; the literature covers whichever ultra-rare gene happened to get a natural-history
study. Neither substitutes for the other.

**Implication:** curating in score order spends most of the effort where nothing can be concluded
— 1,027 of 1,200 assessments are `UNKNOWN`. Roughly 1,000 diseases have a cached Orphanet record;
working that pool would convert far faster.

## 2. The score's dominant failure is reading untreated natural history

Every batch has produced diseases that rank high because the phenotype profile describes a course
almost nobody now follows. The pattern is consistent enough to be predictive:

- **Treated metabolic disease.** Classic galactosemia (newborn-screened, rated *moderate*),
  systemic primary carnitine deficiency (L-carnitine, *occasional/low*), adult Refsum (dietary,
  *occasional/transient*), cblB methylmalonic aciduria (B12-responsive), Wilson disease (chelation;
  90% recover to pre-morbid function).
- **Enzyme replacement and gene therapy.** Fabry, Gaucher III, infantile Pompe (56% mortality
  untreated vs *no mortality* under newborn screening with treatment from birth),
  adrenoleukodystrophy (81% of 32 boys with no major functional disability 6 years after gene
  therapy), TK2 deficiency (58% of 69 untreated died; 0 of 38 treated).
- **Subtype confusion.** SMA type III rated `None | None | None` by Orphanet for work *and*
  self-care — the score reads "SMA" without separating the ambulatory form from types I and II.

`care_context` is doing exactly the job the spec predicted, and it is the single most valuable
field in the schema.

**Batch 7 produced the extreme case.** Untreated SMA type 1 means death or permanent ventilation
by age 2 — historical survival 8%. After single-dose gene replacement, all 15 infants were alive
and event-free at 20 months, and 11 of 12 at the high dose sat unassisted, fed orally and spoke,
with 2 walking independently. Whether a child with SMA1 is totally dependent or acquiring
milestones now depends on **newborn screening and access to therapy, not on the disease**. The
same batch produced molybdenum cofactor deficiency type A, where fosdenopterin leaves 44%
ambulatory at 12 months — while **type B**, curated in batch 3, has no such therapy and a median
age at death of 2.2 years.

That is the sharpest statement of the problem: for a growing set of diseases, the honest answer to
"how impaired is someone with this condition" is *it depends on what care they received*, and a
disease-level dataset can only record that as `VARIABLE` and say why.

## 3. Orphanet increasingly argues levels *down*, not up

Early batches used Orphanet to establish high impairment. From batch 4 onward it more often
*lowers* a level: 10 disputing diseases in batch 4, 6 in batch 5. `MILD` now appears 29 times.

Two mechanisms, worth distinguishing:

**Frequency below the bar.** Orphanet's *Occasional* band sits under the schema's ≥30% threshold,
so a *severe but occasional* limitation argues the level **down**, however alarming the severity
reads. Encoding this rule in the skeleton generator was the single highest-value correctness fix
of the project — before it, severity alone would have driven the level.

**Episodic temporality.** MELAS is rated severe and frequent but **transient** — stroke-like
episodes with recovery between. CADASIL likewise. Severity and frequency alone would have made
both `TOTAL`.

**Relapsing-remitting temporality** *(new in batch 6)*. Dermatomyositis, polymyositis and
Landau-Kleffner are all rated **Complete but Transient** — total during a flare, resolving
between. This is a third distinct mechanism, and clinically the most important one for these
diseases: immunosuppression induces remission in most patients, so the limitation recurs rather
than persists. All three came out `SUBSTANTIAL` on work and `MILD` on care, because they
interrupt work far more than they create a personal-care need.

## 4. Accommodation is not incapacity — and the schema cannot yet say so

A recurring shape: the barrier is environmental, not functional.

- **Xeroderma pigmentosum** — near-total UV avoidance excludes most workplaces without impairing
  capability. Orphanet says *occasional*; SSA lists it as a Compassionate Allowance. They
  disagree because they are answering different questions.
- **Alström syndrome** — paid work rated severe/frequent, professional tasks only
  occasional/moderate. Blindness and deafness bar many standard workplaces while capability is
  better preserved.
- **Retinitis pigmentosa** — rated *moderate* throughout. The clearest case of the score reading
  a sensory impairment as incapacity.

The schema records the level but has no way to say *why* it is high. "Cannot do the work" and
"cannot be accommodated in a standard workplace" are different claims with different policy
consequences. Worth a facet.

## 4b. Subtype granularity is the score's blind spot, and Orphanet sees it

By batch 6 the dataset contains several disease families where subtypes land at different levels
on the same evidence standard. These are the clearest demonstration that disease-level curation is
doing real work the score cannot:

| Family | Subtype | Level | Why |
|---|---|---|---|
| Methylmalonic aciduria | `mut` | `VARIABLE` | cohort where 37% died, 32% uncompromised |
| | `cblA` | `SUBSTANTIAL` | B12-responsive, Orphanet rates complete |
| | `cblB` | `MILD` | B12-responsive, Orphanet rates occasional |
| Metachromatic leukodystrophy | late infantile | `NOT_APPLICABLE` (work) | 11/16 never walk; death in childhood |
| | juvenile | `TOTAL` | complete, permanent |
| | adult | `TOTAL` | presents in 3rd–4th decade, inside working life |
| Huntington disease | adult | `TOTAL`, `PRE_MANIFEST_EXCLUDED` | gene-positive ≠ affected |
| | juvenile | `TOTAL`, no exclusion | symptomatic before working age |

**Open question for review:** is disease-level the right grain, or should some of these entries
split further?

## 4c. The two axes genuinely come apart

A design choice that looked merely tidy is now earning its place: work capacity and care
dependence are decided from their own evidence, never derived from each other. Batch 7 produced
the clearest run of diseases where **care dependence outranks work capacity**:

| Disease | Work | Care | Why |
|---|---|---|---|
| Kearns-Sayre syndrome | `MILD` | `SUBSTANTIAL` | ophthalmoplegia is visually disabling, not cognitively limiting; bulbar dysphagia is severe and very frequent |
| Spinal muscular atrophy type IV | `MILD` | `SUBSTANTIAL` | adult onset, preserved ambulation; but transferring rated severe |
| Friedreich ataxia | `SUBSTANTIAL` | `TOTAL` | work rows rated severity *Unspecified*; care rows severe and very frequent |

**Someone can hold a job and still need help eating.** A single "how disabled is this person"
score cannot express that, and a scheme that routed both questions through one number would get
these diseases wrong in opposite directions.

## 5. Cross-disease citation is the most dangerous failure mode

Gene-matching before citing has rejected a paper in every batch. Numbered disease series are the
trap — the number is not the gene:

- DEE-19 is *GABRA1*, not *KCNQ2* (DEE-7); DEE-38 is *ARV1*; DEE-36 is *ALG13*
- EPM8 is *CERS1*, not *CSTB* (EPM1)
- EMPF2 is *MFF*, not *DNM1L* (EMPF1)
- SPG46 is *GBA2*, not AP-4
- "Duchenne" searches return *Becker* cohorts

Also caught: a **mouse study** (AAV9-ATP7A in a Menkes model) that would have been cited as human
evidence, and generic trials matching many diseases at once — one elamipretide study matched every
mitochondrial complex I entry, a Down syndrome caregiver survey matched unrelated ID syndromes.

**Verifying the gene against the Mondo definition before quoting is mandatory, not optional.**

## 6. Evidence strength caps levels more often than the clinical picture does

Many diseases sit at `SUBSTANTIAL` purely because Orphanet's record is *not expert-validated*, so
no `STRONG` line exists and `TOTAL` is unreachable. **ALS is the clearest case** — four sources
agree (Orphanet, Montana naming it directly, a state code list, SSA) yet the rules cap it.

Every such rationale says so explicitly, so a reviewer can raise it deliberately rather than
reverse-engineering why it is low. But it means **the dataset currently understates severity in a
systematic, predictable direction**, and that must be stated wherever these levels are used.

## 7. Method notes that cost us something

**Hand-matching ICD codes to state lists was wrong.** State lists enumerate 5–6 character children
(`G40811`); Mondo maps the 4-character concept (`G4081`). 492 of 1,164 hits — 42% — come from that
direction alone. Batches 1–3 happened to agree with the authoritative table by luck. Always read
`build/policy_evidence.tsv`; never re-derive it.

**A `git diff` deletions count is not an integrity check.** It read 0 for three batches, then 131
for batch 4 — which turned out to be a block move, with 0 keys lost and 98,170 HPO entries intact.
It produces both false confidence and false alarms. `apply_curation.py` now re-parses after writing
and refuses to save unless every pre-existing field is byte-identical.

**"Total checks: 0" from the reference validator counts *issues*, not checks.** A clean run and a
no-op look identical. The vendored snippet audit now reports `N/N verified` instead.

## 7b. What good evidence actually looks like, when we find it

Batch 6 produced the first **measured employment rate** in the whole dataset — Emery-Dreifuss
muscular dystrophy, where 54% of surveyed patients were employed and 90% of those held positions
matching their education. That is the top-preference evidence type for the work axis and it took
750 diseases to find one.

It is worth noting what it bought: a confident `SUBSTANTIAL` with a clear reading — employment is
reduced but far from precluded, and the work people do is skilled. Almost every other work-axis
level in the dataset rests on an expert rating or a proxy (wheelchair use, mortality, milestone
failure). **We are mostly inferring work capacity from things that are not work.**

Batch 7 found the second, in Usher syndrome type 1: of 47 working-age respondents in the Swedish
Usher database, 23 were working and 24 were not. Two employment figures in 900 diseases. That
study also carries a finding worth repeating wherever these levels are used — *having employment
counteracted the health and financial risks associated with the disability*. The dataset measures
whether people can work; it should not be read as saying whether they should.

## 8. What `UNKNOWN` is actually telling us

`UNKNOWN` means no source has recorded a functional expectation — **not** that the disease is mild,
and not that nobody looked. Each one records what was searched.

The 1,027 `UNKNOWN` assessments are a work queue, not a verdict. But their distribution is itself
the finding: evidence coverage runs *opposite* to our own priority ranking. The diseases we most
want to say something about are the ones nobody has studied.
