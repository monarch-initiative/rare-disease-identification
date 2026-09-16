# MONDO -> ICD-10-CM exact-match mapping

Produces `mappings/mondo_icd10cm_exactmatch.sssom.tsv`: one SSSOM row per term in the
prioritised rare disease list, recording either an exact ICD-10-CM match or an explicit
`sssom:NoTermFound`. **Exact matches only** — broader, narrower and related codes are
rejections, not weaker rows.

The design follows MeDIC's lexical grounder
(`medic/src/medic/grounding/lexical/`): a normalized index on both sides, a tiered
ladder where the first unambiguous hit wins, ambiguity resolving to "no decision"
rather than a guess, and every transform recorded so a human can audit the decision.

## Run

```bash
uv run python scripts/map_icd10cm/lexmatch.py        # stage 1: deterministic
uv run python scripts/map_icd10cm/make_batches.py    # split the review queue
#   ... stage 2: dispatch one agent per batch (see REVIEW_GUIDE.md) ...
uv run python scripts/map_icd10cm/build_sssom.py     # merge into SSSOM
uv run python scripts/map_icd10cm/validate.py        # structural checks
```

## Stages

**Stage 1 — deterministic ladder** (`lexmatch.py`). Query side is the Mondo label plus
its EXACT synonyms from `tmp/mondo.obo`; target side is ICD-10-CM `skos:prefLabel` and
`skos:altLabel`. Tiers: raw exact -> base-normalized -> exact-preserving surgery. More
than one distinct code in a tier means no emission — the term goes to review.

**Stage 2 — agentic adjudication** (`REVIEW_GUIDE.md`). Everything stage 1 could not
settle gets a candidate pool from three sources: lexical ambiguity, broad-scope rule
variants, edit-1 neighbours, and IDF-weighted token retrieval. An LLM decides concept
equivalence per term and writes a one-sentence justification, which lands in the SSSOM
`comment`. Candidates are capped per 3-character ICD category so laterality subcodes
(`M08.011`, `M08.012`, …) cannot crowd out the general rubric.

**Merge** (`build_sssom.py`). Three provenance tiers, strongest first: Mondo's own
asserted exact matches (`semapv:ManualMappingCuration`), stage 1
(`semapv:LexicalMatching`), stage 2 (`semapv:CompositeMatching`).

## Rules

Rule ids, predicates and certainties mirror MeDIC's
`RULE_PREDICATE` / `RULE_CERTAINTY` tables. Rules MeDIC scopes as
`skos:broadMatch` (`qualifier_strip`, `strip_leading_other`) or `skos:closeMatch`
(`fuzzy_edit1_unique`) are **never emitted** here — they only widen the stage-2
candidate pool, because the brief is exact matches only.

Deliberately not ported, and why:

| MeDIC rule | Why not |
|---|---|
| `salt_ester_strip`, `inn_*`, `formulation_strip`, `rxnorm_resolve` | Drug-only. |
| `cyrillic_transliteration`, `translation_*` | Source strings are English Mondo labels. |
| `combination_split` | Splits a combination literal into components. A Mondo label denotes one disease concept; splitting would yield a 1:many mapping, which is not an exact match of the whole term. |

Added beyond MeDIC, for Mondo<->ICD-10-CM label conventions: `strip_possessive` /
`add_possessive` (ICD keeps eponym possessives Mondo drops — this alone recovered
Marfan syndrome), `comma_inversion`, `deficiency_inversion`, and
`syndrome_to_disease` / `disease_to_syndrome`. The last pair is the weakest of the
additions and is scored 0.88 accordingly; the others sit at 0.95-0.97.

## Source data

ICD-10-CM comes from `medic/background/ontsrc/icd10cm.owl` (UMLS2RDF, 2024ab),
**not** the sibling `icd10cm.ttl`. The TTL is truncated: 22,168 codes against the
OWL's 97,904, and it is missing whole rubrics including `Q87.4 Marfan syndrome`.

## Caveats

- `semapv:CompositeMatching` rows are LLM proposals for human review, not curated
  assertions. Every one carries its reason in `comment`.
- The deterministic tiers are reproducible; stage 2 is not byte-stable across reruns.
- Mondo's own exact-match release contains object_ids that are not ICD-10-CM codes
  (chapter ranges `E00-E90`, `I10-I16`; the ICD-11-style `QA0.0142`). Four set-wide,
  two on this list. They are emitted as `NoTermFound` with the assertion named in
  `comment` rather than passed on as pullable codes.
- Coverage is ~13.5%. That is a real property of the list, which is dominated by
  gene-level and numbered OMIM subtypes for which ICD-10-CM has no counterpart.
