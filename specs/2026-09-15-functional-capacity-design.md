# Mondo Functional Capacity Screen (MFCS) — design

**Status:** draft v2, 2026-09-16 (v1 2026-09-15; §4 and §7 substantially revised — see §11)
**Home:** `rare-disease-identification/functional-capacity/`
**Context:** `~/ws/ont/mondo/background/frailty/review-medically-frail-2026-09-11.md`

---

## 1. What this is

Two per-disease labels asserted on Mondo classes, each independently evidenced:

- **Work-capacity impairment** — a substantial proportion of affected adults of working age cannot
  sustain competitive employment under standard of care.
- **Care dependence** — a substantial proportion require substantial daily personal assistance with
  ADLs, or continuous supervision.

Not "frailty". Frailty has no universal definition and the previous attempt died on that.

## 2. The definition — adopted, not invented

Minnesota's draft clinical definition (Appendix A, Public Law 119-21 §71119) includes a code if it is

> likely to result in **ongoing medical care needs** OR impairment that limits **likelihood of
> employment, number of hours worked if employed**, extent of community participation…;
> AND likely to **last 6 months or longer**; AND is **not easily curable with treatment**.

Methodology attributed by MN to a memo by Ne'eman, McIntyre, Smithers and Sommers (27 Feb 2026).

That sentence contains both our axes plus a duration gate and a treatment gate. **Adopt it verbatim.**
We are then never arguing about the definition, only presenting evidence against one a state wrote.

Facets per assertion — never collapsed to a score:

| Facet | Values |
|---|---|
| `label` | work-capacity-impairment / care-dependence |
| `status` | EXPERT_POSITIVE / EXPERT_NEGATIVE / EXPERT_NOT_APPLICABLE / PREDICTED_CANDIDATE / PREDICTED_LOWER / PREDICTED_UNLIKELY / NOT_ASSESSED — **never silence** |
| `evidence_tier` | A (Orphanet expert-validated) / B (Orphanet unvalidated) / C (rule or ranking) |
| `claims_selectable` | does an ICD-10-CM code exist at all — **the routing field** |
| `care_context` | standard-of-care-treated / untreated-natural-history / treatment-refractory — **not yet implemented** |
| `life_stage` | incl. a working-age gate — **not yet implemented** |

## 3. The evidence base

**Orphanet functional consequences** (`https://www.orphadata.com/data/xml/en_funct_consequences.xml`,
CC BY 4.0, v1.3.42) — 1,048 disorders × 128 ICF items, each with frequency × severity × temporality ×
a LossOfAbility flag. Contains our constructs by name (*"engaging in paid work in a standard
environment"*, the full self-care cluster). It ships its own tiering: `StatusDisability`
(404 validated), `SourceOfValidation` (names the expert), `DisabilityCategory`
(609 in scope / 95 *"no functional disability"* / 344 not applicable), `AnnotationDate` (2012–2026).

Internal consistency check: on the 95 disorders Orphanet independently categorises as having no
functional disability, our extraction rule fires **zero** times.

## 4. What the state lists changed (new in v2)

Three live state artefacts reviewed: Nebraska (295 pp, 4,806 ICD-10-CM codes), Minnesota (6,281 codes,
73 diagnosis groups), Montana (~50 plain-language conditions mapped to the five statutory categories).

**Finding 1 — the coded layer is nearly solved.** Of 324 assessed classes carrying an ICD-10-CM code,
Nebraska reaches 148 and Minnesota 128. We can name exactly **3** codeable rare diseases that neither
state reaches and we would flag. *"A better code list" is not a product.*

**Finding 2 — almost nothing is codeable.** 3,389 of 3,713 assessed Mondo classes (**91%**) carry no
ICD-10-CM code. A diagnosis-code screen cannot reach them in principle. For these the only route is
per-person attestation — which needs a per-disease expectation of what the condition typically means
for daily life. **That artefact does not exist. It is what this project makes.**

**Finding 3 — the states disagree with each other more than either disagrees with us.** Only 2,974 of
Minnesota's 6,281 codes appear in Nebraska's list (47%). Two states, one statute, no shared source.
That is the argument for an evidenced reference, and it is stronger than telling a state it is wrong.

**Finding 4 — Montana already screens on function**, not only diagnosis: bed confinement, ventilator /
wheelchair / oxygen dependence, gait and mobility, history of falling. ICF-shaped concepts in a live
state screen. This validates the functional framing directly.

**Finding 5 — the states are ahead of us on treatment status.** MSUD, propionic acidemia and isovaleric
acidemia rank high for us and are absent from Nebraska — correctly, since they are newborn-screened and
treated. Our ranking reads untreated natural history. The treatment gate moves from deferred to
**blocking**.

## 5. Routes

**Route 1 — Orphanet direct (Tier A/B).** 691 expert-evidenced assertions, 152 tier A, plus a curated
negative set and an explicit not-assessed set. **Built** (`step5_assertions.py`).

**Route 2 — phenotype scoring (Tier C).** Clinician scores each HPO term 0–3 on both axes; scores
inherit down the ontology; aggregate per disease weighted by frequency and normalised by √n; rank.
**Built and measured** — see §6.

**Route 3 — LLM adjudication.** Not started. Now well-posed: hold out the 538, run blind, beat the
measured floor (AUC 0.80/0.86). The decisive test is whether it beats 0.51/0.55 on the 89 non-neuro
diseases, i.e. whether the method generalises past neurology.

**Route 4 — downward Mondo propagation + sibling-consistency QC.** Not started.

## 6. Measured performance of Route 2

| | AUC | top-25 correct | base rate | lift |
|---|---|---|---|---|
| Work-capacity impairment | 0.80 | 64% | 25% | 2.5× |
| Care dependence | 0.86 | 68% | 16% | 4.3× |

**Not curation depth.** Raw weighted sum correlates 0.90 with annotation count, and count-alone scores
AUC 0.75/0.77 — so the headline uses a √n-normalised score, and within every annotation-depth stratum
it beats count-only (0.64/0.73/0.74 work, 0.64/0.86/0.81 care, against 0.61/0.60/0.66 and 0.53/0.57/0.65).
This is the check the "≥3 organ systems" rule failed.

**Negative guardrail.** A disease with no high-frequency anchor finding is negative at NPV 0.94 (work) /
0.97 (care), ruling out 1,028 classes deterministically.

**Scope limit.** AUC 0.79/0.89 on the 449 diseases with neurological findings; **0.51/0.55** on the 89
without — chance. Pain, fatigue, breathlessness and organ-failure disability are invisible because HPO
barely encodes them.

## 7. Deliverables

```
functional-capacity/
  README.md                       narrative
  data/term_scores.tsv            373 scored HPO terms  <- the clinician-editable file
  data/state_lists/               extracted NE + MN code sets, PROVENANCE.md
  scripts/step1..step5            corpus -> scoring -> apply -> policy -> assertions
  build/assertions.tsv            3,713 classes, both axes, status + evidence + rule + claims_selectable
  build/state_comparison.tsv      per-disease reach by Nebraska and Minnesota
  build/validation.tsv            the 538-disease answer key
  build/index.html                shareable page
```

## 8. Excluded by design

No frailty index. No organ-system-count trigger. No pure severity modifiers as anchors. Lane A
instruments (HFRS, Kim CFI, eFI) stay internal — never validated for eligibility determination.
`untreated-natural-history` evidence must not ship once the facet exists.

## 9. Next

1. Clinician scores replace the 373 prototype ones; re-run and report the delta.
2. Treatment-status facet — **blocking**, per Finding 5.
3. Working-age gate.
4. Route 3 benchmark, targeting the non-neuro failure.
5. Inter-rater reliability: two clinicians, blinded, ~200 stratified diseases, report κ.
6. ICF / I-CAN domain substrate as the eventual model (see §10).

## 10. The per-person half

`DisabilitEASE` (a six-stage NDIS support-letter pipeline, ICF-framed, profiling against the I-CAN 12
domains) is the per-person consumer this needs. Its `Phenotype-based intensity estimate` currently
returns **3/5 on all ten domains it fires on**, eight of them justified by `HP:0001263` alone — for a
GMFCS V child needing 2:1 transfer assistance. That is the same presence-≠-severity collapse measured
in §6, reproduced independently. MFCS is the disease-expectation prior it lacks; it is MFCS's consumer.
Its I-CAN domains (ICF chapters d1–d9 plus three) are a better substrate than our two binary axes, and
Orphanet's items are ICF items, so they join natively.

## 11. Changed from v1

- Definition **adopted from Minnesota** instead of authored by us (§2).
- Route 2 **demoted** from classifier to ranking + guardrail; single-term rules max out at PPV 0.57 and
  do not work.
- `claims_selectable` added as the routing field; the deliverable reframed around the 91% (§4).
- Treatment-status facet promoted from deferred to blocking.
- A v1 claim that state lists systematically miss rare disease **did not survive checking** — with
  correct child-code matching, Nebraska reaches 8/8 of our top 100 codeable. Corrected.
