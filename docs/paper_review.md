# Paper review: where the criteria and the registry disagree

Concerns raised while mapping the manuscript's six prioritisation criteria onto
registry fields. `config/prioritisation_criteria.yaml` follows the paper —
criterion names and subcriteria are the paper's own, from Table 1 and the
workflow figure. This file is where the objections live instead, so that the
config stays a faithful implementation and the arguments stay reviewable.

Source: *Which Rare Diseases Are Best Suited to Diagnostic AI? Towards a Systematic
Selection Framework* (2026 draft), Table 1, Table 2, Table 3 and Methods.

**Numbering.** Criterion numbers below are **ours**, not the current draft's. The
manuscript is being revised to adopt our order, so this is the numbering that will
survive. Where a quotation carries the draft's own number it is given as "the
draft's N".

| Ours | Criterion | Draft |
|---|---|---|
| 1 | Impactful intervention | 2 |
| 2 | Phenotypic complexity and/or multimodal detectability | 6 |
| 3 | Progressive / multi-system diseases | 4 |
| 4 | Available gold-standard training cohort | 1 |
| 5 | Low diagnostic rates for higher prevalence rare diseases | 3 |
| 6 | Inexpensive, less invasive, or widely available test | 5 |

Two of the items below have now been acted on in the config, and say so where they
stand. The rest have not.

---

## 1. Criterion 4 does not measure a cohort

**Paper** (the draft's 1): "Available gold-standard training cohort" — *1a. Existence
of a registry or specialty clinic within the network. 1b. Existence of an ICD10CM code.*

**What the registry actually tests:**

| Signal | Subcriterion | What it reads |
|---|---|---|
| `icd10cm_exact_value_set` | 4b | Mondo asserts `skos:exactMatch` to a billable ICD-10-CM code |
| `icd10cm_xref` | 4b | Mondo carries an ICD-10-CM cross-reference |
| `nord_listed` | 4a | A NORD/GARD/Orphanet cross-reference exists |

Two of the three signals are 4b. They test **coding coverage**, not whether a cohort
exists. The third is the only one aimed at 4a, and a NORD cross-reference is evidence
that a patient organisation exists, not that anyone is enrolled anywhere.

So a disease can satisfy "Available gold-standard training cohort" while zero
identified patients exist in the partner network. The criterion's name promises a
cohort and the implementation delivers an ICD code.

**The paper has the right number and we do not use it.** The Methods describe the
evidence stream directly:

> ...through partner engagement quantified the number of individuals enrolled in
> shareable registries. Where possible, we performed de-identified queries of EHR
> data (e.g., Slicer-Dicer searches using ICD-10-CM or SNOMED CT codes for unique
> patients seen within the past five years).

and give a fallback where coding fails: `estimated enrollment = 0.2 × total patient
population × disease prevalence`. Table 3 shows the result for a worked example —
per-site counts across Truveta, UNC Health, Johns Hopkins and Emory.

**That count never reached the registry.** There is no cohort, registry, enrolment or
patient-count field in `schema/rare_disease_prioritisation.yaml`. The single number
that would make criterion 4 mean what its name says was collected by the team and
then dropped on the way into the data model.

**Proposed fix:** add a per-disease cohort field — enrolled or identifiable patients,
per partner site, with the estimation method recorded — and move 4a onto it. Until
then criterion 4 should be reported as *4b only*, and the NORD signal should be
labelled for what it is.

**Partly acted on.** ICD-11 Foundation codes (673 diseases) and SNOMED CT codes
(1,198) are now rendered on the card, against 348 for ICD-10-CM. They deliberately do
**not** satisfy the criterion: 4b is "existence of an ICD10CM code", and combining
ICD-10-CM, ICD-11 and SNOMED CT appears in Table 2 only as the *proposed mitigation
for iterative future work*. No US partner site codes in ICD-11 today. Scoring them
would move several hundred diseases into this criterion on the strength of something
the paper lists as future work. Showing them keeps the gap visible without
overstating what a cohort can currently be built from.

---

## 2. Criterion 6 has no method in the paper

**Paper** (the draft's 5): "Inexpensive, less invasive, or widely available test" —
*Availability of confirmation after computational identification; improve utilization
of medically appropriate test.*

The Methods name six evidence streams: ICD code coverage, disease prevalence,
underdiagnosis risk, treatments, phenotypic breadth, and registries and specialty
clinics. **Test accessibility is not among them.** Every other criterion maps onto a
described method; this one has none. The only Methods sentence touching it is an
example inside the actionability paragraph (hypophosphatasia and alkaline phosphatase).

What the paper gives instead is Table 1's six worked exemplars, each a clinician's
judgement with a citation: alpha-1 antitrypsin serum levels, Wilson ceruloplasmin and
urinary copper, targeted NGS panels for monogenic dyslipidemias, hypophosphatasia ALP,
the Fanconi DEB breakage test, Diamond-Blackfan eADA activity. Per-condition expert
judgement, not a rule.

The four signals under it are therefore **this registry's own construction**: is the
disease genetic, does it have an OMIM entry, do its phenotypes touch metabolism, do
they touch blood. The last two loosely echo the exemplars. "Has an OMIM entry" as
evidence of an *inexpensive, widely available* test is a stretch, and it is what drives
the saturation — nearly every Mendelian disease has one.

Result: 96.8% of diseases met, 0% on recorded evidence. The criterion separates almost
nothing, and what little it separates tracks OMIM coverage.

Note also that **Table 2 does not list this as a gap.** Its five entries are coding,
prevalence, diagnostic rate and delay, treatment and actionability, and phenotypic
characterisation. The omission is not one the manuscript acknowledges.

**Proposed fix:** either source test cost/invasiveness/availability per disease, or
report the criterion as explicitly unevaluated rather than letting four proxies imply
it was assessed. Tracked as `issues/issue_accessible_test_evidence.md`.

---

## 3. Criterion 1 is true by construction

**Paper** (the draft's 2): "Impactful intervention" — *2a. Diagnostic delay impact.
2b. Indicated management change.*

Both halves are curated directly, which is the strongest evidence status any criterion
has. But `Diagnostic delay impact` is asserted for **3,052 of 3,079 diseases** (99.1%).
A label carried by essentially every record cannot discriminate between records.

The approved-indication signal, which reads MeDIC, is the only part of the criterion
grounded in evidence external to the curators' own labelling.

This is visible rather than hidden — the criterion reports 99.2% met — but it means
criterion 1 contributes almost no ranking signal, and any downstream analysis treating
the six criteria as independent discriminators should exclude it.

**Acted on.** The criterion previously also counted two functional-capacity proxies,
`high_work_impairment` and `high_care_impairment`, which let an agent-curated severity
assessment satisfy it on its own. The paper scopes 1a to diagnostic-delay impact and
1b to indicated management change; disease severity is neither. Both were removed from
`satisfied_when` and the assessments moved to "Everything else on record". The
criterion fell from 3,055 to 3,053 — they were carrying two diseases.

---

## 4. Phenotypic breadth straddles criteria 3 and 2

**Paper:** criterion 3 (the draft's 4) is *"Potential for recognition of pleiotropic
features across medical specialties"*; criterion 2 (the draft's 6) is *"Phenotype
signatures exist with established genomic, imaging, and/or lab-based features"*.

Read strictly, 3 is about **organ-system breadth** and 2 is about **data modalities**.
The registry implements that split: "five or more HPO organ systems" sits under 3,
and the multimodal/complexity labels sit under 2.

But the Methods' breadth/depth metric — mean information content summed across the 20
HPO organ-system branches — is the paper's *only* computed phenotype measure, and it
feeds `hpo_treatment_rank`, which the registry displays under **2**. So organ-system
breadth informs both criteria by two different routes: as a count under 3 and as an IC
sum under 2.

This is not a registry error; the paper does not separate them cleanly either. But it
means 3 and 2 are correlated by construction, and an upset plot showing them
co-occurring is partly reporting that shared input rather than two findings.

---

## 5. Criterion 2 never tests a modality

**Paper** (the draft's 6): "Phenotype signatures exist with established **genomic,
imaging, and/or lab-based** features; AI models that work in the context of general
care are realizable."

The requirement is explicitly about **data modalities** — that a signature exists in
genomic, imaging or laboratory data. The three signals under the criterion are two
curated `justification_summary` labels ("Phenotypic complexity", "Multi-modal
detectability") and a count of at least ten curated HPO terms. None of them looks at a
modality. `deep_phenotype_profile` measures the **depth of HPO annotation**, which is
a property of how well the disease has been curated in HPOA, not of what data a
patient's record would contain.

The two curated labels do carry the clinicians' judgement, and "Multi-modal
detectability" is the paper's own term — but they are near-duplicates of each other
(2,458 and 2,459 diseases, almost entirely the same ones), so the criterion rests on
one bulk judgement plus an annotation-density count.

Compounding this: `hpo_treatment_rank` is displayed under criterion 2, but the workflow
figure assigns it to *criteria 1b and 3* (the draft's 2b and 4) — it is the
breadth/depth metric combined with treatment availability. It is the one computed
number the paper produced, and it is rendered under the criterion it does not belong
to. See §4.

**Proposed fix:** move the `hpo_treatment_rank` display to criterion 3. For the
criterion itself, either record per-disease modality evidence — does an imaging
finding, a lab signature or a molecular test exist — or state that the criterion rests
on curator judgement alone and drop `deep_phenotype_profile`, which currently lends it
a derived-evidence badge it has not earned.

---

## 6. The prevalence half of criterion 5 can be satisfied without prevalence

**Paper** (the draft's 3): "Low diagnostic rates for higher prevalence RDs."

The config is explicit that the "for higher prevalence RDs" half is load-bearing, and
makes the criterion the only conjunction of the six:

```yaml
satisfied_when: underdiagnosis_flagged and (higher_prevalence or misdiagnosis_bias_recorded)
```

The `coverage_note` explains why the conjunction is required — `underdiagnosis_flagged`
alone fires on 3,067 of 3,079 diseases and is worthless by itself. Then the second
disjunct lets `misdiagnosis_bias` stand in for prevalence. Misdiagnosis bias records
*who gets missed* — a demographic or presentation skew. It is not a prevalence claim,
and substituting it silently weakens the conjunction the note says is deliberate.

The numerical effect is small: `misdiagnosis_bias` is recorded on 20 diseases and the
criterion is met by 154 against 153 on prevalence alone. But the rule and the prose
disagree about what the criterion means, and the paper is unambiguous — the Results
say "low diagnostic rates were present for RDs experts determined to be relatively
high prevalence".

**Proposed fix:** drop the `misdiagnosis_bias_recorded` disjunct and keep the field as
displayed context, or, if it is meant to be evidence, say in the config what it is
evidence *for*. One disease changes either way.

---

## 7. One curated label conflates two criteria

The curated `justification_summary` value **"Insufficient ICD coding/underdiagnosis"**
packs together two different things: absence of an ICD code, which is the *negation*
of criterion 4b, and underdiagnosis, which is criterion 5.

The registry assigns it to criterion 5 alone. A disease flagged only because it lacks
an ICD code therefore counts as evidence of underdiagnosis, and simultaneously fails
criterion 4b for the same underlying fact.

**Proposed fix:** split the label at curation time into two values. Tracked as
`issues/issue_justification_summary_enum.md`.

---

## 8. `justification_summary` is close to binary

2,404 of 3,079 diseases carry all five labels, and 593 carry exactly two. Any criterion
leaning on this field inherits that bimodality rather than adding information to it.
Four of the six criteria read it.

---

## 9. The paper never scores diseases against the criteria

The workflow figure routes all six criteria into a single box — "Expert consensus,
weighs all criteria" — which then produces the Phase I set. The Discussion is explicit:

> The prioritization was guided by expert consensus when quantitative evidence was
> sparse **(Table 2)** [...] We have not yet performed inferential testing or formal
> optimization of the prioritization criteria.

All 3,079 diseases in the registry were *already selected* by that consensus. The
per-disease "Met / Not met" verdicts on the website are a reconstruction after the
fact, not the process the paper describes. A "Not met" badge does not mean the disease
was considered and rejected on that criterion; it means the registry cannot retro-fit
the reason a human gave.

Four of the six criteria are met by 90–99% of the list, and only criterion 4 (20.3%)
and criterion 5 (5.0%) discriminate at all. That pattern is what a reconstruction looks
like when the fields were not recorded for this purpose.

**Proposed fix:** say so on the site, once, where the verdicts are introduced.
