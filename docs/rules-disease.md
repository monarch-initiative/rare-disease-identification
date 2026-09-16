# Mapping curation rules — disease and phenotype pack

Domain pack for disease, phenotype and clinical terminologies: Mondo, ICD-10-CM, ICD-11,
SNOMED CT, Orphanet, OMIM, DOID, NCIT, HPO, MedDRA, UMLS.

Load alongside the core registry (`curation-rules.md`), which supplies the `EV`, `SC`,
`PR`, `ST` and `RJ` families. This pack supplies `CM`.

**Namespace:** `maprule:` → `https://w3id.org/mapping-rules/`

Conflation is not an error. It is a decision, and it must be visible. The whole point of
this family is that `skos:exactMatch` alone cannot say "the labels agreed *and* I knowingly
crossed a conceptual model boundary to accept it". Cite the `CM` rule alongside the `EV`
rule that produced the match.

## Family CM — Conceptual model conflation (disease / phenotype)

The most important family, and the one usually left undocumented. These record that the
two resources hold **genuinely different models of what a disease is**, and that the
curator decided to cross that boundary anyway, for stated practical reasons.

Conflation is not an error. It is a decision, and it must be visible.

| ID | Title | Meaning |
|---|---|---|
| `CM-001` | disease/disorder conflation | Subject and object are technically distinct as disease vs disorder; conflated as acceptable. |
| `CM-002` | disease/phenotype conflation, murky case | The object is modelled as a sign, symptom or clinical finding while the subject is a disease, and the distinction is genuinely unclear. Conflated to avoid losing associations. **Acceptable.** |
| `CM-003` | disease/phenotype distinction clear-cut | Same shape as CM-002 but the distinction is unambiguous. **Rejection ground — do not conflate.** |
| `CM-004` | finding-vs-disorder conflation | Target separates "clinical finding" (may be normal or abnormal) from "disorder" (necessarily abnormal), as SNOMED does. Conflated deliberately. |
| `CM-005` | etiological vs phenomenological divergence | The same clinical picture is individuated by cause in one resource and by presentation in the other (the nocturnal enuresis case: psychiatric in Mondo, urological and explicitly organic in ICD-10-CM). Conflated on the grounds that the use case does not distinguish them. |
| `CM-006` | susceptibility vs disease | Subject is a susceptibility or predisposition locus; object is the clinical disease. **Rejection ground — these are not the same entity.** |
| `CM-007` | gene-centric vs disease-centric | One side denotes a gene or molecular defect, the other a disease. **Rejection ground.** |
| `CM-008` | cross-species analog | Entities are analogous across organisms rather than identical. Conflate only if the use case explicitly permits it. |
| `CM-009` | injury/event vs inherited condition | Target rubric denotes an acute event or procedural complication where the subject denotes an inherited trait (malignant hyperthermia susceptibility vs the anaesthetic crisis). **Rejection ground.** |

---

---

## Why this family is disease-specific

Disease terminologies disagree about what a disease *is* in ways that other domains do not
share. Mondo treats a disease as a disposition to undergo pathological processes; ICD-10-CM
is a statistical classification that also codes signs, symptoms and encounters; SNOMED CT
separates "clinical finding" from "disorder" on whether the state is necessarily abnormal.
None of those distinctions has an analogue in a chemical or anatomical mapping, which is
why the conflation vocabulary has to be a pack rather than part of the core.
