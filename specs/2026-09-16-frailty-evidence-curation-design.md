# Functional-capacity evidence curation — design

**Status:** draft, 2026-09-16
**Home:** `rare-disease-identification`
**Relationship to prior work:** the ranking in `functional-capacity/` proposes *what to look at*.
This designs *how we establish it*. The ranking is a worklist generator, not an answer, and
nothing here changes it.

---

## 1. The shift

So far the output is a score. A score is not a curated fact, and a policy audience cannot use
one. What we need per disease is a **claim with evidence behind it**:

> *Work capacity: TOTAL. Because Orphanet's expert panel rates paid work as severely and
> permanently limited, and a 2019 UK cohort found 14% of adults in paid employment.*

Two assessments per disease, independently evidenced:

- **`work_capacity`** — can affected adults of working age sustain competitive employment?
- **`care_dependence`** — do affected people need daily personal assistance or supervision?

They are separate. Many diseases limit work without creating a care need; a few do the reverse.
Deriving one from the other would destroy the distinction that makes the data useful.

## 2. Scope

**Only the rare disease codes already in `prioritised-rare-disease-list.yml`.** 3,079 diseases,
already curated, already Mondo-keyed, already the project's subject. Not all of Mondo. This keeps
the work bounded and the data in one place.

## 3. Schema

`src/rare_disease_identification/schema/functional_capacity.yaml`, imported by the main schema.
`RareDisease` gains two slots, both `FunctionalCapacityAssessment`.

```yaml
- mondo_id: MONDO:0010726
  mondo_label: Rett syndrome
  care_dependence:
    impairment: TOTAL
    care_context: STANDARD_OF_CARE_TREATED
    life_stage: PAEDIATRIC
    score: 6.8
    score_method: phenotype-wsum-norm
    score_version: "2026-09-16"
    model_confidence: 93
    claims_selectable: true
    icd10cm_codes: [F84.2]
    curation_status: AI_CURATED
    rationale: >-
      Loss of purposeful hand use, loss of speech and impaired ambulation from early
      childhood leave most affected people dependent on daily assistance for feeding,
      dressing and transfers. No evidence line disputed this.
    evidence:
    - lane: EXPERT_DATABASE
      direction: SUPPORTS
      strength: STRONG
      reference: ORPHA:778
      source_statement: "Washing oneself | Very frequent | Complete | Permanent limitation"
      explanation: Orphanet's validated expert rating for self-care.
      curator_type: PIPELINE
    - lane: LITERATURE
      direction: SUPPORTS
      strength: STRONG
      reference: PMID:xxxxxxxx
      quote: "<exact sentence from the abstract>"
      population: <n, country, age range>
      explanation: Quantifies daily assistance need in an identified cohort.
      curator_type: AI_AGENT
```

**Impairment levels** — `NONE` / `MILD` / `SUBSTANTIAL` / `TOTAL` / `VARIABLE` /
`NOT_APPLICABLE` / `UNKNOWN`. Deliberately mirrors Orphanet's Low/Moderate/Severe/Complete so the
two are comparable, plus the three states that keep the model honest: `VARIABLE` for genuine
subtype variation, `NOT_APPLICABLE` for work capacity in a disease lethal before working age, and
`UNKNOWN` for assessed-and-nothing-found. **Never silence.**

**Two facets that are not optional**, because both are known failure modes:
- `care_context` — treated / untreated / refractory. The PKU trap. An assessment built only from
  untreated natural history must never reach a policy artefact.
- `life_stage` — including `PRE_MANIFEST_EXCLUDED` for Huntington-like cases.

**Evidence model** follows SEPIO via `monarch-initiative/sieve` (EvidenceLine = direction +
strength + item), flattened so it can be hand-written and reviewed in YAML. `direction` and
`strength` are the two slots that make disagreement representable instead of averaged away.

## 4. The five evidence lanes

| Lane | Source | Typical strength | Coverage |
|---|---|---|---|
| `EXPERT_DATABASE` | Orphanet functional consequences — 1,044 Mondo classes, names its validating expert, dates the annotation | STRONG when validated | ~1,000 |
| `POLICY_LIST` | Nebraska (4,806 codes), Minnesota (6,281), Montana, SSA Compassionate Allowances, NDIS lists | MODERATE | codeable diseases only |
| `LITERATURE` | PubMed, searched for *functional outcomes* — employment rate, ADL score, caregiver hours, institutionalisation | STRONG with a cohort | in principle all |
| `MODEL_JUDGEMENT` | Benchmarked LLM rubric (AUC 0.88 care / 0.80 work; 0.80 care on non-neuro disease) | WEAK alone | all |
| `COMPUTED_SCORE` | Phenotype score | WEAK always | 2,807 |

The lanes are chosen to be **independent**: a curated database, a government decision, a
measurement in patients, a model reading, and a computation over symptoms. When four lanes agree
the claim is defensible in a way no single source makes it. When they disagree, that is a finding
worth recording.

**The literature lane is the new work**, and it is the one that makes this citable. Everything
else is derived from sources someone else compiled.

## 5. Evidence discipline — inherited wholesale from dismech

Non-negotiable, because these failure modes are already documented and already cost rework there:

1. **Never fabricate a quote.** It must be an exact substring of the cached abstract.
2. **Fetch before citing.** `just fetch-reference PMID:…` writes the cache; never hand-write a
   cache file.
3. **A title is not a finding.** A title states that a question was examined, not what was found.
4. **A quote under five words carries no proposition.**
5. **If no quotable sentence exists, drop the line.** Do not manufacture one, and do not promote a
   weaker lane to compensate.
6. **Absence is not evidence.** A disease missing from a state list is almost always missing
   because it has no ICD-10 code, not because anyone judged it.

`linkml-reference-validator` (already a published package, already used by dismech) does the quote
checking, so this is reuse rather than new machinery.

## 6. Synthesis rules

- `TOTAL` requires at least one **STRONG** line.
- `SUBSTANTIAL` requires two lines from **different lanes** agreeing.
- Disagreeing lanes → `DISPUTED`. Record both sides. **Never average.**
- Fewer than two lanes → `UNKNOWN`, with a rationale naming what was searched.
- `curation_status: AI_CURATED` is the ceiling for an agent. `EXPERT_REVIEWED` requires a named human.

## 7. The skill

`.claude/skills/curate-frailty/` + `.claude/commands/curate-frailty.md`.

```
/curate-frailty 100
```

Takes the next 100 unreviewed diseases by score, runs the five lanes, synthesises, writes back,
validates. Modelled on dismech's `/curate` and `curate-next`.

Recipes to add to the justfile:

```
just frailty-worklist N      # next N unreviewed, by score -> tmp/frailty_worklist.tsv
just validate-frailty        # LinkML conformance
just verify-frailty-quotes   # every quote against its cached reference
just frailty-stats           # coverage, lane mix, disputed count
just fetch-reference PMID:…  # port from dismech
```

## 8. Order of work

| # | Step | Why first |
|---|---|---|
| 1 | Backfill lanes 1, 2, 5 deterministically for all 3,079 | Free. No agent needed. Establishes the baseline and shows where the gaps are. |
| 2 | Add the justfile recipes and the quote verifier | The skill cannot be trusted without them. |
| 3 | Run `/curate-frailty 50` as a pilot | Measure: how often does a LITERATURE line actually exist? That number decides whether this scales. |
| 4 | Read the pilot's DISPUTED rows | They are where the method is wrong, and the cheapest lesson available. |
| 5 | Scale to the full list | Only after the pilot's hit rate is known. |

**Step 3 is the real unknown.** If quotable functional-outcome literature exists for 60% of rare
diseases, this is a strong resource. If it exists for 10%, the honest output is mostly
`EXPERT_DATABASE` + `UNKNOWN`, and that is still useful but is a different claim. Measure it on 50
before committing to 3,079.

## 9. What this does not do

- It does not assess people. Every artefact says so.
- It does not replace the ranking; it consumes it.
- It does not settle disagreement between sources; it records it.
