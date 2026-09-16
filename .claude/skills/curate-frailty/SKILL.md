---
name: curate-frailty
description: Use when asked to curate work-capacity and care-dependence evidence for the next N rare diseases in prioritised-rare-disease-list.yml. Gathers evidence from five independent lanes (Orphanet, state policy lists, literature/PMIDs, model judgement, computed score), synthesises an impairment level, and writes it back. Accepts a positional integer N.
---

# curate-frailty

Walk the ranked worklist and add **evidence-backed** functional-capacity assessments to
`src/prioritised-rare-disease-list.yml`. Two assessments per disease: `work_capacity` and
`care_dependence`. Schema: `src/rare_disease_identification/schema/functional_capacity.yaml`.

## When to use

- "/curate-frailty 100" — curate the next 100 diseases on the worklist
- "add frailty evidence for the next 20 diseases"
- "re-curate the DISPUTED assessments"

Skip when the user names one disease — do that one directly, same workflow, no batching.

## Inputs

Positional integer **N**, the number of diseases to curate. No default — if N is missing,
non-integer, or `<= 0`, ask. Above 200, warn about runtime and confirm before starting.

## The rule this skill exists to enforce

**An impairment level without evidence is not curation.** Every assessment must carry at
least two evidence lines from **different lanes**, or be recorded as `UNKNOWN` with a
rationale saying what was searched and not found. Recording UNKNOWN honestly is a completed
curation, not a skipped one.

## Workflow

### 1. Build the worklist

```bash
just frailty-worklist N        # -> tmp/frailty_worklist.tsv
```

Selection, in order:
1. `curation_status` is absent or `UNREVIEWED` — never re-curate `EXPERT_REVIEWED` without being asked.
2. Sort by the computed score descending, so the highest-signal diseases are done first.
3. Take N.

`DISPUTED` rows are a separate queue — curate those only when the user asks for them by name.

### 2. Gather evidence — five lanes, in this order

Do the cheap deterministic lanes first. They frequently settle the case and save the expensive ones.

**Lane 1 — EXPERT_DATABASE (Orphanet).** `references_cache/ORPHA_*.md`, built from
`en_funct_consequences.xml`. If the disease has an ORPHA xref with functional-consequence
data, quote the row verbatim:

```yaml
- lane: EXPERT_DATABASE
  direction: SUPPORTS
  strength: STRONG          # STRONG only when StatusDisability is Validated and an expert is named
  reference: ORPHA:558
  source_statement: "Engaging in paid work in a standard environment | Frequent | Severe | Permanent limitation"
  explanation: Orphanet's expert panel rates paid work as severely and permanently limited.
  curator_type: PIPELINE
```

This lane alone can justify `TOTAL` when the rating is Validated, severe, permanent and frequent.
When Orphanet says *No functional disability*, that is a **DISPUTES** line and usually settles it at `NONE`.

**Lane 2 — POLICY_LIST. Do not compute this — look it up.**

```bash
python3 functional-capacity/scripts/policy_lookup.py --yaml MONDO:0016532
```

That prints the evidence block ready to paste, or a NOT LISTED note. Coverage today:
Nebraska (600 Mondo classes), Minnesota (530), Montana (34, name-matched). The table is
`functional-capacity/build/policy_evidence.tsv`, rebuilt by
`functional-capacity/scripts/step9_policy_evidence.py`.

**Never match ICD codes to state lists yourself.** State lists enumerate 5-6 character ICD
children (`G40811`, Lennox-Gastaut *with status epilepticus*) while Mondo maps the 4-character
concept (`G4081`). Exact matching misses it; parent-only matching misses it. **492 of the 1,164
hits in the table — 42% — come from that direction alone.** Hand-matching produces a confident,
wrong "no state lists this", which is the worst possible error for a policy artefact.

**NOT LISTED is not a DISPUTES line.** Most rare diseases carry no ICD-10-CM code at all, so a
code-based list cannot reach them whatever a state thinks. Absence carries no information — omit
the lane entirely. Record a DISPUTES line only if the disease *has* a code and a state has
explicitly considered and excluded it, which requires reading the state document, not the table.

**Montana is the interesting one** — it lists conditions by name, not code, so it reaches diseases
with no ICD code, and it assigns each to one of the five statutory categories from 42 CFR 440.315.
That category is the most directly citable thing in this lane: it is a government body saying which
statutory ground this disease qualifies under. It lands in `source_statement`.

*Lane to add:* SSA Compassionate Allowances (~280 conditions that qualify for expedited disability
determination) would be the strongest POLICY_LIST source for `work_capacity`, since it is a federal
list of conditions accepted as meeting the disability standard. ssa.gov blocks automated fetching —
drop the list into `data/state_lists/` by hand and extend `step9_policy_evidence.py`; the
name-matching path for Montana already does what is needed.

**Lane 3 — LITERATURE (PMIDs). This is the new work and the point of the skill.**

Search PubMed for functional outcomes, not for the disease in general:

```
"<disease>" AND (employment OR "return to work" OR "work capacity" OR "occupational outcome"
  OR "activities of daily living" OR "functional outcome" OR "caregiver burden"
  OR "quality of life" OR disability OR institutionalisation OR "natural history")
```

Then, for every PMID you intend to cite:

```bash
just fetch-reference PMID:12345678        # writes references_cache/PMID_12345678.md
just verify-frailty-quotes                # checks every quote against the cache
```

**The quote must be an exact substring of the cached abstract.** Never paraphrase. This
follows the dismech evidence SOP verbatim, including its failure modes — a title is not a
finding, and a quote under five words carries no proposition. If you cannot find a quotable
sentence, drop the line; do not manufacture one.

What to quote, in preference order: an employment rate, an ADL or dependency score, a
caregiver-hours figure, an institutionalisation rate, a disability-benefit uptake rate. A
sentence saying the disease is "severe" is not functional evidence.

```yaml
- lane: LITERATURE
  direction: SUPPORTS
  strength: STRONG
  reference: PMID:28123456
  reference_title: Employment outcomes in adults with <disease>
  quote: "Only 12 of 84 adults (14%) were in paid employment at last follow-up"
  population: 84 adults, UK national cohort, mean age 34
  explanation: Direct measurement of employment rate in an identified adult cohort.
  curator_type: AI_AGENT
```

Set `strength: MODERATE` for a cohort under ~20, a single centre, or a related-disease
proxy. Set `WEAK` for expert opinion without data.

**Lane 4 — MODEL_JUDGEMENT.** Structured rating from the disease description, with the
confidence from the benchmarked rubric (`functional-capacity/scripts/step7_llm_benchmark.py`).
Record the confidence, and record it as `WEAK` unless a benchmark run supports otherwise.
**Never let this lane alone carry an assessment.**

**Lane 5 — COMPUTED_SCORE.** The phenotype score. Always `WEAK`. It proposed the disease for
curation; it is not evidence that the answer is right.

### 3. Synthesise

Set `impairment` from the evidence, not from the score. Rules:

- `TOTAL` requires at least one **STRONG** line (Orphanet validated, or a quantitative cohort).
- `SUBSTANTIAL` needs two lines from different lanes agreeing.
- Lanes that disagree → set `curation_status: DISPUTED`, state both sides in the rationale,
  and stop. Do not average them.
- Fewer than two lanes → `UNKNOWN`, and say in the rationale what you searched.

Always set `care_context`. If every line describes untreated natural history, say
`UNTREATED_NATURAL_HISTORY` — and then the assessment must not be used for policy. This is the
PKU trap: newborn-screened, treated diseases look devastating in the literature describing
their untreated course.

Set `work_capacity.impairment: NOT_APPLICABLE` when the disease is near-universally lethal
before working age. Care dependence still applies in those cases.

Write `curation_status: AI_CURATED` — never `EXPERT_REVIEWED`. Only a named human sets that.

### 4. Write and validate

```bash
just validate-frailty                  # LinkML schema conformance
just verify-frailty-quotes             # every quote against its cached reference
just frailty-stats                     # coverage, lane mix, disputed count
```

All three must pass before reporting done.

### 5. Report

Per batch: how many curated, the breakdown by impairment level, how many landed `UNKNOWN`
and `DISPUTED`, how many carry a LITERATURE line, and any disease where the evidence
contradicted the computed score — that last one is the most interesting output, because it
is where the method is learning something.

## What not to do

- Do not set an impairment level the evidence does not carry, however confident the score is.
- Do not cite a PMID you have not fetched and quote-checked.
- Do not treat absence from a state list as evidence of anything.
- Do not reconcile disagreeing lanes yourself. Mark DISPUTED and let a human decide.
- Do not skip a disease because it is hard. Record `UNKNOWN` with a rationale.
