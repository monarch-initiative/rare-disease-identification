# Stage-2 adjudication guide: MONDO -> ICD-10-CM exact matches

You decide, for each Mondo term, whether any candidate ICD-10-CM code is an
**exact match** (`skos:exactMatch`): the code denotes *the same disease concept*.
Nothing else is wanted. Broader, narrower and merely-related codes are rejections.

Stage 1 already resolved every case that matched on strings. What reaches you is
the hard residue, so **most items have no exact match** and the expected answer is
usually `"exact": false`. Do not manufacture matches to be useful; a wrong mapping
silently pulls the wrong patient cohort, which is worse than a recorded absence.

## Accept (`exact: true`) only when

The ICD rubric and the Mondo term denote the same disease, allowing for house style:
word order, possessives, British/American spelling, `disease`/`disorder`, and
eponym-vs-descriptive naming of the same entity.

- `Marfan syndrome` = `Q87.4 Marfan syndrome` — same concept.
- `Fanconi anemia` = `D61.03 Fanconi anemia` — same concept.
- `cystic fibrosis` = `E84 Cystic fibrosis` — the rubric denotes the disease itself.

## Reject (`exact: false`) when

- **The code is a disjunction of two diseases.** `Duchenne muscular dystrophy` vs
  `G71.01 Duchenne or Becker muscular dystrophy` — the code covers Becker too, so it
  is broader. Reject.
- **The code is broader**, a grouping or chapter rubric. `X-linked hypophosphatemic
  rickets` vs `E83.31 Familial hypophosphatemia` — the code covers other familial
  hypophosphatemias. Reject.
- **The code is narrower**: a subtype, stage, site, laterality or complication
  variant (`... , right shoulder`, `... with systemic onset`).
- **`unspecified` / `other` / `NOS` / `NEC` rubrics.** These are residual buckets, not
  the disease. `E27.1 Primary adrenocortical insufficiency` is not
  `adrenocortical insufficiency`.
- **Same organ, different disease.** Token overlap is not equivalence; several
  candidates are retrieval noise and share only a word.
- **The Mondo term is a gene-level or molecular subtype** with no ICD counterpart.

If two or more candidates are equally defensible, reject: ambiguity is not an exact
match. Pick a single code or none.

## Output

Write a JSON array to the output path, one object per input term, same order:

```json
{"mondo_id": "MONDO:0011429",
 "exact": true,
 "code": "M08",
 "confidence": 0.9,
 "justification": "ICD-10-CM M08 'Juvenile arthritis' is the rubric for the same disease; 'idiopathic' vs the ICD wording is naming style, not a difference in extension."}
```

- `exact`: boolean. When false, set `"code": null`.
- `confidence`: 0.0-1.0, your certainty in the decision (not in the disease).
- `justification`: one sentence, concrete, naming the code and why it does or does
  not denote the same concept. This is the reviewable audit trail — "no suitable
  match" is not acceptable; say what the closest candidate was and what makes it wrong.

Emit an entry for **every** input term. Use only codes offered in that term's
candidate list. Do not invent codes, do not look anything up, decide from the labels
and your clinical knowledge.
