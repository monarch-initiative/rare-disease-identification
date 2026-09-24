# Issue #9 review worksheets

Two sheets for a collaborator to fill in, covering
[monarch-initiative/rare-disease-identification#9](https://github.com/monarch-initiative/rare-disease-identification/issues/9).
Everything already settled is pre-filled; only the `fill_*` columns are empty.
Leave a row's `fill_*` columns blank if you do not want to rule on it — blank
means "not looked at", which is deliberately distinguishable from a verdict.

They are two files because they ask two different questions at two different
granularities, and answering one in the other's place is what tangled the issue
thread: "not specific enough" is a verdict on a **code**, not on a disease.
Rubinstein-Taybi is a textbook rare disease; `Q87.2` is a grab-bag. Both facts
can be true, and the registry can now hold both.

## `issue9_value_set_tiering.tsv` — one row per (disease, ICD-10-CM code)

What does this code mean, relative to this disease, in a patient record?
Fills `value_sets` in `schema/value_set.yaml`.

| Column | Values |
|---|---|
| `fill_tier` | `exact` — the disease, no more and no less.<br>`narrower` — a subset; everyone returned has the disease, you miss people.<br>`proxy` — a superset; high recall, low precision, never a case definition.<br>`excluded` — considered and ruled out.<br>`reassign` — the code belongs to a different Mondo term; name it in `fill_reassign_to_mondo_id`. |
| `fill_proxy_basis` | Required when `fill_tier` is `proxy`. `SUBSUMPTION` (the rubric is a genuine superclass) / `TERMINOLOGY_INDEX` (ICD's own index or inclusion terms send coders here) / `CODING_CONVENTION` (an "other specified"/NEC bucket that is a superclass only tautologically). |
| `fill_reassign_to_mondo_id` | A `MONDO:NNNNNNN` id, when `fill_tier` is `reassign`. |
| `fill_comment` | Required for `proxy` and `excluded`: what else is in the code, and what a second filter would have to do. An unexplained proxy is indistinguishable from a mistake. |
| `fill_cohort_size` | Optional, and the one column a site with records access can fill and we cannot: how many patients sit on that code at your site. A signal for how much noise a second filter has to remove, not a prevalence estimate. |
| `fill_cohort_size_source` | Where the count came from, e.g. "UNC Health via TriNetX, 2026-03". |
| `fill_confidence` | Optional. `high` / `medium` / `low`. |

Read-only context columns: `n_billable_leaves` and `billable_leaves` are what a
query on that anchor actually pulls back, expanded through the NLM Clinical
Tables API. `mondo_asserts` is what Mondo already says about the pair — a
verdict that contradicts an existing `skos:exactMatch` is a **retraction**, and
lands in `mappings/retractions.tsv` with an upstream issue.

## `issue9_list_membership.tsv` — one row per disease

Should this Mondo term be on the prioritised list at all, and is it at the
right level of generality? This is the open question in
`issues/issue_list_membership_sop.md`, so a rationale here is worth more than
the yes/no.

| Column | Values |
|---|---|
| `fill_include_on_list` | `yes` / `no` / `defer` |
| `fill_level_is_right` | `yes` / `too broad` / `too narrow` — the term is a reasonable unit of disease, independent of whether any ICD code can find it. |
| `fill_rationale` | Free text. Most useful where it disagrees with `prior_position`. |

Read-only context: `mondo_subsets` carries Mondo's own granularity tags
(`disease_grouping`, `ordo_group_of_disorders`, `ordo_disorder`,
`ordo_subtype_of_a_disorder`); `n_descendants_on_list` of `n_descendants_total`
says how much of the subtree is already in, and `nearest_on_list_ancestor`
whether an umbrella is already carrying it.

## Built from

Mondo `releases/2026-09-01`, ICD-10-CM FY2026 via the NLM Clinical Tables API.
The generator prints both on every run, so a regeneration that moves either is
visible before the sheets go out.

## Regenerating

Both files are generated, not hand-maintained — regenerate rather than edit if
the candidate set changes, then re-apply any `fill_*` answers already received.

```bash
python scripts/build_issue9_worksheets.py
```

It reads `tmp/mondo.obo`, `tmp/sssom/*.sssom.tsv`, `tmp/icd10cm_expansion.json`
(topped up from the NLM API on a miss) and `src/prioritised-rare-disease-list.yml`.
