# Mapping curation rules — core registry

A registry of named, citable rules for curating and reviewing mappings. Each rule has a
stable ID so a mapping can record *why* it was accepted or rejected, in the SSSOM
`curation_rule` / `curation_rule_text` slots.

**This file is the domain-neutral core.** It judges evidence, scope, predicates and
structural integrity — not biology or chemistry. Conflation rules, which record that two
resources hold genuinely different models of what an entity *is*, are domain-specific and
live in packs:

| Pack | Family | For |
|---|---|---|
| `rules-disease.md` | `CM-*` | disease, phenotype and clinical terminologies |
| `rules-chemical.md` | `CX-*` | chemical structures, substances and roles |

Load the core plus exactly one pack. A review in a domain with no pack yet should say so
in the set-level protocol rather than force-fit a conflation rule from another domain.

The point of naming these is that a mapping decision is only meaningful relative to the
rules it was made under. As the OBO Academy guide puts it, you can never determine the
correctness of a mapping in the abstract — only whether, *under the curation rules
declared for the set*, subject and object relate as the predicate claims. Writing the
rules down is what makes a mapping set reviewable rather than merely asserted.

**Namespace:** `maprule:` → `https://w3id.org/mapping-rules/`
(proposed; the prefix needs registering before `curation_rule` URIs resolve. Until then,
use `curation_rule_text` with the rule ID and title.)

**Citing a rule.** A mapping may cite several. Record the evidence rule that produced the
match *and* any conflation or scope rule that had to be invoked to accept it. The second
is the interesting one:

```
curation_rule_text:  maprule:EV-001 exact match on primary label |
                     maprule:CM-001 disease/disorder conceptual model conflation
```

That pair says something a bare `skos:exactMatch` cannot: the labels agreed, *and* the
curator knowingly crossed a conceptual model boundary to accept it.

---

## Family EV — Evidence for sameness

What was actually observed that supports the mapping. Ordered roughly by the strength
and cost hierarchy in the OBO Academy guide. These record evidence, not verdicts.

| ID | Title | Meaning |
|---|---|---|
| `EV-001` | exact match on primary label | Subject and object primary labels are identical. High confidence, very low cost — primary labels are largely unique. |
| `EV-002` | exact match on normalised label | Identical after non-semantic normalisation only (case, accents, punctuation, whitespace). Equivalent in strength to EV-001. |
| `EV-003` | exact match on exact synonym | One side's primary label equals the other's *exact* synonym. Medium-to-high confidence. |
| `EV-004` | match after declared lexical transformation | Matched only after a documented, bounded rewrite (possessive, word order, British/American spelling, `disease`↔`disorder`). The specific rule MUST be recorded in `subject_preprocessing`. |
| `EV-005` | proxy mapping via third resource | Both sides already mapped to the same concept in a trusted third resource. Medium-to-high confidence, very low cost. |
| `EV-006` | lexical similarity only | Low edit distance, or one label contained in the other. **Low confidence — never sufficient alone for exactMatch.** |
| `EV-007` | synonym similarity | Non-exact synonym overlap. Low confidence, not sufficient alone. |
| `EV-008` | hierarchical corroboration | Parents, children or linked features are comparable. Medium confidence. Note the asymmetry: a *failing* hierarchical comparison is weak evidence against, because primary organising relationships rarely correspond across semantic spaces. |
| `EV-009` | definition comparison | A domain expert compared textual definitions. Medium-to-high confidence, high cost. |
| `EV-010` | full expert review | An expert aggregated hierarchy, axioms, definitions and external sources. Highest confidence, very high cost. |
| `EV-011` | external source confirmation | The mapping is asserted by the source itself, via an explicit exact match to the subject class. |
| `EV-012` | automated adjudication over retrieved candidates | Candidates were retrieved lexically and a model judged equivalence. Records the reasoning; **does not by itself license a curated assertion** — see the tiering in the Mondo curation guide. |

---

## Family SC — Scope, granularity and undefined subsets

Where the two concepts differ in *extension* rather than in kind.

| ID | Title | Meaning |
|---|---|---|
| `SC-001` | undefined residual subset ("Other X") | Object is a semantically undefined remainder class — "Other porphyria", "Other specified muscular dystrophies". **MUST NOT be an exactMatch**, even when the subject disease is listed under it as an inclusion term. Map as `skos:narrowMatch` to the more general subject and exclude on the grounds of `MONDO:undefinedGrouping`. |
| `SC-002` | "unspecified" or "excluding X" rubric | Object is scoped by exclusion (ICD-10-CM `G62.9 Polyneuropathy, unspecified`, which excludes `G62.1`). Its extension is not stable. **MUST NOT be an exactMatch**; `skos:narrowMatch`, excluded as `MONDO:undefinedGrouping`. |
| `SC-003` | "related conditions" grouping | Object is an open-ended association bucket ("cancer-related conditions"). **MUST be `skos:relatedMatch`.** Should not enter Mondo as a class. |
| `SC-004` | disjunctive rubric | Object names two or more distinct diseases (`G71.01 Duchenne or Becker muscular dystrophy`, `E22.0 Acromegaly and pituitary gigantism`). Broader by construction. **Not an exactMatch.** |
| `SC-005` | target finer than subject | Object is a site, laterality, encounter, severity or stage variant. Object is narrower. |
| `SC-006` | subtype under type-agnostic rubric | Subject is a subtype and the object is the rubric that abstracts over it. Commonly numbered or gene-defined (`immunodeficiency 112`, `CVID 12`, `Fanconi anemia complementation group C`), but equally an aetiological subtype under an aetiology-agnostic parent (`Cushing disease due to pituitary adenoma` under `E24 Cushing's syndrome`, which also spans ectopic-ACTH, drug-induced and Nelson's). Object is broader. **Not an exactMatch** unless SC-008 is declared. Check first whether a subtype-specific code exists — `E24.0` did. |
| `SC-007` | rubric coextensive with subject | Object's own subdivisions are all subtypes of the subject concept, so their extensions coincide — `E76.21 Morquio mucopolysaccharidoses` divides only into Morquio A, Morquio B and unspecified, and is therefore exactly MPS IV. **exactMatch is correct**, including when the rubric's label carries "unspecified". Distinguishing this from SC-001 is the single hardest judgement in this registry. |
| `SC-008` | granularity tolerance declared | The use case explicitly permits mapping up to the next best available concept. Only valid when declared at set level, and the predicate MUST still reflect the true relation (`broadMatch`), never `exactMatch`. |

---

## Family PR — Predicate selection

Direction convention, stated once: in `subject predicate object`, `skos:narrowMatch`
means **the object is narrower** (subject broader); `skos:broadMatch` means **the object
is broader** (subject narrower).

| ID | Title | Meaning |
|---|---|---|
| `PR-001` | same real-world concept | Subject and object denote the same disease → `skos:exactMatch`. |
| `PR-002` | object is a subclass | No target concept equals the subject → `skos:narrowMatch`. |
| `PR-003` | object is a superclass | No target concept equals the subject → `skos:broadMatch`. |
| `PR-004` | object is a sibling | → `skos:closeMatch`. |
| `PR-005` | conceptually related only | No exact, broad, narrow or close fit → `skos:relatedMatch`. Should be rare. |
| `PR-006` | exactMatch is not OWL equivalence | `skos:exactMatch` asserts referential sameness for integration purposes, not `owl:equivalentClass`. Do not upgrade it silently. |
| `PR-007` | prefer exact or broad | `closeMatch` and `relatedMatch` are hard to use analytically. Where the external concept is out of scope entirely, another predicate is acceptable but an exclusion reason MUST be given. |
| `PR-008` | ambiguity is not a match | Two or more equally defensible candidates → assert nothing. Recording no mapping is better than recording an arbitrary one. |

---

## Family ST — Structural integrity

Checks over the set, not the individual mapping. Violations are set-level defects.

| ID | Title | Meaning |
|---|---|---|
| `ST-001` | proxy merge | Two object concepts from one resource both exactMatch a single subject. Disallowed for core-, community- and AI-curated precise mappings (Tiers 1–3); a core curator must resolve it. Acceptable for Tier 4. |
| `ST-002` | reverse proxy merge | Two subject concepts both exactMatch a single object id. **Disallowed at every tier.** |
| `ST-003` | object identifier must exist | The object id must be a real, current identifier in the target vocabulary at the declared version. |
| `ST-004` | object must not be obsolete | Deprecated or obsoleted target concepts must not carry exact matches. |
| `ST-005` | identifier is not a code | The object id is a chapter range (`ICD10CM:E00-E90`) or belongs to a different vocabulary than its prefix claims (an ICD-11-shaped id under an `ICD10CM:` prefix). Invalid regardless of the label's plausibility. |
| `ST-006` | subject must be in scope | The subject must be a disease, not a phenotypic feature or a gene. |

---

## Family RJ — Rejection grounds

Terminal outcomes. A rejection is a finding and should be recorded, not dropped —
`sssom:NoTermFound` with the reason beats a missing row, because it distinguishes
"no code exists" from "nobody looked".

| ID | Title | Meaning |
|---|---|---|
| `RJ-001` | no candidate found | Nothing in the target vocabulary denotes this concept. |
| `RJ-002` | ambiguous candidates | Several defensible candidates, none clearly best. |
| `RJ-003` | homonym | Labels agree but the concepts differ — the classic failure mode of label-only evidence. |
| `RJ-004` | token overlap only | Candidate shares words but denotes a different disease. Retrieval noise. |
| `RJ-005` | target out of scope | The target concept is not a disease under the subject resource's model. |

---

## Using these in a review

A review that changes nothing still records something. Minimum per mapping:

- `reviewer_id` — who reviewed
- `reviewer_agreement` — `1.0` full agreement, `-1.0` full disagreement, `0.0` uncertain
- `curation_rule_text` — the rules the verdict rests on
- `comment` — one sentence of reasoning, naming the object concept

Set-level, declare once in the SSSOM header: the curation rules in force, the use case
they serve, and every conflation the set knowingly permits. A set that conflates disease
and phenotype without saying so is not reviewable, however good its individual rows.
