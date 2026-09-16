# Functional Capacity Screen — proof of concept

**Question.** Can we rank Mondo diseases by two functional claims — *affected people are likely
unable to sustain work*, and *affected people are likely to need daily personal care* — using
the clinical findings already recorded for each disease?

**Answer.** Yes, well enough to be a triage ranking. Not well enough to be a determination.
And only for diseases with neurological involvement.

## The method in five steps

1. **Score the findings.** A clinician rates each HPO term 0–3 on two axes: does this finding imply
   inability to work, does it imply need for daily care. 373 terms scored (prototype scores in
   `data/term_scores.tsv` — one editable TSV, nothing else to change).
2. **Inherit down the ontology.** An unscored term takes the score of its most specific scored
   ancestor. 373 scored terms cover all 8,721 distinct annotations in the corpus.
3. **Add up per disease.** Weight each finding by its HPO frequency, sum, divide by `sqrt(n)` so
   thoroughly-documented diseases don't win on length.
4. **Rank.** The output is an ordering, not a classification. The claim is that the *top* is enriched.
5. **Check against experts.** Orphanet's functional-consequences dataset independently rates 538 of
   these diseases on paid work and self-care. The scoring never saw it.

## What it scores

| | AUC | top-25 correct | base rate | lift |
|---|---|---|---|---|
| Unable to sustain work | 0.80 | 64% | 25% | 2.5× |
| Needs daily personal care | 0.86 | 68% | 16% | 4.3× |

**It is not just counting annotations.** Split the diseases into three groups by how many findings
they carry and compare against a "count the findings" null model *within* each group:

| annotation depth | n | count-only (work/care) | scored (work) | scored (care) |
|---|---|---|---|---|
| few | 179 | 0.61 / 0.53 | **0.64** | **0.64** |
| medium | 179 | 0.60 / 0.57 | **0.73** | **0.86** |
| many | 180 | 0.66 / 0.65 | **0.74** | **0.81** |

The scored ranking beats counting in every stratum. That is the check that distinguishes this from
the "≥3 organ systems" proxy, which measured curation depth and flagged 73% of everything.

## Known limits

- **Neurological disease only.** AUC 0.79 / 0.89 on the 449 diseases with neuro findings;
  **0.51 / 0.55** on the 89 without — a coin flip. Pain, fatigue, breathlessness and organ-failure
  disability are invisible, because HPO barely encodes them.
- **Untreated natural history.** Wilson disease ranks 17th for work incapacity; treated Wilson
  disease usually isn't disabling. Needs a treatment-status facet.
- **Presence ≠ severity.** Half the diseases annotated `HP:0002540 Inability to walk` are *not*
  rated care-dependent by Orphanet's experts.
- **No working-age gate.** "Cannot work" is undefined for a disease lethal in infancy.
- **The scores are a prototype**, not clinician-authored. The PoC tests the pipeline, not the scores.

## Scope

| | n |
|---|---|
| prioritised rare disease list | 3,079 |
| …resolved in current Mondo | 3,066 |
| …with ≥1 HPO finding → **ranked** | **2,807** |
| …with an Orphanet functional label | 382 |
| validation cohort (all in-scope Orphanet-labelled, with HPO) | 538 |
| …expert-validated labels (tier A) | 141 |

## Against the live state lists

Nebraska (4,806 ICD-10-CM codes), Minnesota (6,281), Montana (~50 conditions by statutory category).

- **The coded layer is nearly solved.** Of 324 assessed classes with an ICD-10-CM code, Nebraska
  reaches 148, Minnesota 128. We can name **3** codeable rare diseases neither reaches that we flag.
- **91% of assessed classes carry no ICD-10-CM code at all** (3,389 of 3,713). A diagnosis-code
  screen cannot reach them in principle — that is where the whole problem is, and it routes to
  per-person attestation, which needs exactly the per-disease expectation this produces.
- **The two states agree on 47% of codes.** One statute, no shared source.
- **The states are ahead of us on treatment.** MSUD, propionic and isovaleric acidemia rank high
  here and are absent from Nebraska — correctly; they are newborn-screened and treated. Our
  ranking reads untreated natural history. The treatment gate is blocking, not optional.

We adopt **Minnesota's** inclusion criteria as the operational definition — see
`data/state_lists/PROVENANCE.md`.

## Run it

```bash
python3 scripts/step1_corpus.py      # corpus + validation set + term list
python3 scripts/step2_score.py       # propagate, aggregate, compare aggregators
python3 scripts/step3_apply.py       # robustness checks + ranked output
python3 scripts/step4_policy.py      # compare against state code lists
python3 scripts/step5_assertions.py  # merged four-state assertion table
```

Outputs in `build/`: `assertions.tsv` (3,713 classes, both axes, status + evidence + rule +
`claims_selectable`), `state_comparison.tsv`, `ranked.tsv`, `validation.tsv` (the answer key),
`terms_to_score.tsv` (what a clinician fills in), `index.html` (the shareable page).

Inputs: `build/fc.xml` (Orphanet functional consequences, CC BY 4.0,
`https://www.orphadata.com/data/xml/en_funct_consequences.xml`), `build/hpoa.tsv`
(`https://purl.obolibrary.org/obo/hp/hpoa/phenotype.hpoa`, 2026-09-02),
`~/ws/ont/mondo/mondo.obo`, `~/.data/oaklib/hp.db`.

## What changes next

Swap `data/term_scores.tsv` for clinician scores and re-run — the measurement re-runs unchanged, and
the delta between prototype and clinician scores is itself the interesting number. Then add the
treatment-status facet and the working-age gate.

Design context: `../specs/2026-09-15-functional-capacity-design.md`.
