# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pipeline that takes a curated rare disease list, merges drug/treatment associations from the MeDIC knowledge base, and publishes results as a static site to GitHub Pages.

The source of truth is the curated `src/prioritised-rare-disease-list.yml`, **not** the Excel spreadsheet. The Excel ingest and its OAK-based ontology enrichment were retired in `87a76dd` and the module has since been deleted; read it with `git show 87a76dd:src/rare_disease_identification/extract-from-excel-old.py`. Consequence: the ontology-derived fields it produced — labels, synonyms, `ontology_terminology_codes`, HPO categories — are frozen at April 2026 and no recipe re-derives them. ICD-10-CM codes are the exception: `build-value-sets` now derives those from Mondo into `value_sets`. See `issues/issue_ontology_enrichment_dropped.md`.

## Build & Run

Uses `just` (justfile) as task runner and `uv` for Python dependency management.

```bash
just setup              # uv sync + install package in editable mode
just gen-datamodel      # generate LinkML Python dataclasses from schema
just build-drugs        # aggregate drug associations from MeDIC products -> data/drugs.yml
just build-value-sets   # derive exact/narrower ICD-10-CM value sets from Mondo -> data/value_sets.yml
just merge              # merge curated list + drug + value-set + DisMech data -> prioritised-rare-disease-list.yml
just build-criteria     # score every disease against the six criteria -> criteria.json + docs/criteria-assignment.md
just upset              # upset plot over the six criteria -> docs/figures/
just criteria-icons     # re-cut the six glyphs from the manuscript workflow figure
just all                # setup + gen-datamodel + build-drugs + build-value-sets + build-functional-capacity + fetch-dismech + merge + build-criteria
just fetch-mondo        # download tmp/mondo.obo, refreshed whenever the release has moved
just require-mondo      # assert tmp/mondo.obo exists, no network (used by offline recipes)
just fetch-dismech      # download tmp/mondo_emc.tsv, refreshed whenever the release has moved
just require-dismech    # assert tmp/mondo_emc.tsv exists, no network
just update-categories  # refresh the six mondo_category_* fields, in place, in SOURCE
just serve              # serve the site locally on port 8080
just clean              # remove .venv, generated datamodel, output YAML and tmp/
```

`update-categories` is **not** part of `all` and writes back into `src/prioritised-rare-disease-list.yml` in place.

`fetch-mondo` **always refreshes** `tmp/mondo.obo`, via an ETag conditional GET against
`tmp/mondo.obo.etag`: one round trip, and the 53MB body only crosses the wire when the release has
moved. It downloads to a `.part` file and refuses to replace a good `mondo.obo` with anything under
10MB or missing a `data-version:` header, so a redirect page or a truncated body cannot clobber it.
It used to guard with `test -f`, which left the file five months stale and silently poisoned every
recipe downstream. `require-mondo` asserts the file is present without touching the network, for
offline recipes.

`build-value-sets` derives only the `exact` and `narrower` tiers of each disease's
`value_sets`, from Mondo's `skos:exactMatch` and `skos:narrowMatch` SSSOM releases plus the `is_a`
closure in `tmp/mondo.obo`, expanded to billable leaves through the NLM Clinical Tables API and
cached in `tmp/icd10cm_expansion.json`. It **never writes to `SOURCE`** — `proxy` and `excluded` are
curated there and `merge` joins the two. It refuses to run if `SOURCE` carries a hand-written
derived tier. `--offline` builds from the expansion cache alone. `mappings/retractions.tsv` lists
Mondo mappings we drop, because SSSOM cannot express a retraction.

`build-criteria` scores the merged list against the six prioritisation criteria from the
manuscript's workflow figure. **`config/prioritisation_criteria.yaml` is the single source of
truth** for what those criteria are, which registry field counts as evidence for each
(`signals`, each tagged `direct`/`derived`/`proxy`), when a criterion counts as met
(`satisfied_when`, a boolean expression over signal ids), and what the website renders inside
each section (`display`). Criterion logic lives nowhere else: not in the plot script, not in
`site/js/app.js`. Both consume the generated `criteria.json`.

`build-functional-capacity` derives the computable evidence lines of each functional-capacity
assessment — `EXPERT_DATABASE`, the two policy lanes, `PHENOTYPE_ANCHOR` and `COMPUTED_SCORE` —
from Orphanet's `fc.xml`, the SSA crosswalk, `build/policy_evidence.tsv` and HPOA. Same asymmetry
as the value sets: it **never writes to `SOURCE`**, where only the judgement (`impairment`,
`care_context`, `rationale`, `curation_status`) and the two uncomputable lanes (`LITERATURE`,
`MODEL_JUDGEMENT`) are curated. `merge` re-attaches the derived lines and **drops any derived lane
it finds on the curated side**, so a hand-edited copy is overwritten rather than trusted. It
refuses to run if `SOURCE` hand-carries a derived lane; `just strip-derived-evidence` is the
one-off migration. Quote verification therefore runs against `OUTPUT`, not `SOURCE`.

`fetch-dismech` downloads the DisMech MONDO cross-reference
(`mondo_emc.tsv`) from the project's `releases/latest/download/` URL, with the same
ETag conditional GET and the same "never guard on mere existence" reasoning as
`fetch-mondo`: `latest/download/` silently follows the releases, so a file that is
present tells you nothing about its age. It refuses to replace a good file with a
body that lacks the expected header row or has fewer than 100 rows.

The DisMech linkout is the one derived field with no `build-*` step behind it.
There is nothing to derive - one column looked up by MONDO ID - so `merge` reads
`tmp/mondo_emc.tsv` directly via `-m` and sets `dismech_url`, rather than a
`build_dismech.py` writing a YAML that would be a verbatim re-encoding of the
release asset. It is derived all the same: a `dismech_url` hand-written in
`SOURCE` is dropped by the join, not trusted. DisMech covers about half the list
(1,649 of 3,079 as of the September 2026 release); the rest simply carry no slot,
and the site renders nothing for them.

`build-drugs` expects a sibling `../medic` directory containing `products/indication_list.yaml`, `products/contraindication_list.yaml`, and `products/research_list.yaml`. MeDIC nests one evidence row and one `regulatory_status` per *assertion*; `build_drugs.py` flattens both up to the association and de-duplicates repeated statuses.

## Architecture

- **`src/rare_disease_identification/schema/`** — LinkML YAML schemas:
  - `rare_disease_prioritisation.yaml` — main schema (RareDiseaseCollection, RareDisease, DrugIndication, Evidence, etc.)
  - `mondo_drugs.yaml` — schema for the disease-centric drug report output
  - `value_set.yaml` — terminology value sets per disease, in three tiers (`exact`, `narrower`, `proxy`). `exact` and `narrower` are derived; `proxy` is curated
- **`src/rare_disease_identification/build_drugs.py`** — aggregates MeDIC drug association data into a disease-centric report. Run as `python -m rare_disease_identification.build_drugs`.
- **`src/rare_disease_identification/build_value_sets.py`** — derives the `exact` and `narrower` ICD-10-CM value-set tiers from Mondo. Run as `python -m rare_disease_identification.build_value_sets`.
- **`src/rare_disease_identification/criteria.py`** — loads `config/prioritisation_criteria.yaml`
  and evaluates it against disease records. The rule ops and the `satisfied_when` expression
  walker live here; `satisfied_when` is parsed with `ast` and walked by hand, never `eval`ed.
- **`src/rare_disease_identification/build_criteria.py`** — writes `criteria.json` (definitions +
  per-disease membership, read by the site and the plot) and `docs/criteria-assignment.md` (the
  human review document, rendered from the config's prose plus live counts — do not hand-edit it).
- **`scripts/figures/plot_criteria_upset.py`** — the upset plot. Draws the upset by hand rather
  than via `upsetplot`, whose 0.9.0 release is broken under pandas 3.
- **`scripts/figures/extract_criteria_icons.py`** — cuts the six glyphs out of the workflow
  figure by matching each donut wedge colour exactly. The wedge colours in the criteria config
  are therefore load-bearing.
- **`src/rare_disease_identification/merge.py`** — joins the curated list with `data/drugs.yml`, `data/value_sets.yml`, `data/functional_capacity.yml` and `tmp/mondo_emc.tsv` by MONDO ID. Copies every other source field through untouched. The value-set join is tier-aware: derived tiers come from the generated file, curated tiers from the source.
- **`src/rare_disease_identification/update_mondo_categories.py`** — rewrites the six `mondo_category_*` fields by traversing `tmp/mondo.obo`.
- **`src/rare_disease_identification/datamodel/`** — auto-generated from LinkML schema; do not edit manually.
- **`scripts/`** — standalone exports (`export_indications_table.py`) and the SSSOM proposal builder (`build_mendelian_sssom.py`). Not part of `just all`. `export_icd10cm_table.py` was removed once `build_value_sets.py` superseded it; its flat `data/icd10cm_table.tsv` had no consumer and carried no predicate tiering.
- **`site/`** — static site deployed to GitHub Pages. The six criteria are the primary visual
  structure of every disease card: one colour-coded section per criterion, in figure order, each
  carrying the registry fields the config's `display` block assigns to it. Reads
  `data/prioritised-rare-disease-list.yml` and `data/criteria.json` at runtime; locally `site/data` is a symlink to the repo root, and `.github/workflows/deploy.yml` copies the output into `site/data/` on deploy.
- **`src/prioritised-rare-disease-list.yml`** — the curated source list (tracked, hand-maintained).
- **`data/drugs.yml`** — drug association report output (generated by `build-drugs`). `data/` is gitignored.
- **`data/value_sets.yml`** — derived value-set tiers (generated by `build-value-sets`).
- **`prioritised-rare-disease-list.yml`** — main pipeline output at the repo root (generated by `merge`).
- **`criteria.json`** — criterion definitions plus per-disease membership at the repo root
  (generated by `build-criteria`). Served to the site as `data/criteria.json`.
- **`site/assets/criteria/`** — the six criterion glyphs, cut from the workflow figure and committed.

## Key Dependencies

- **LinkML** — schema definition and Python dataclass generation (`gen-python`)
- **OAK (oaklib)** — ontology access for Mondo. Now used only by `update_mondo_categories.py`, over a local `tmp/mondo.obo`; the broader enrichment that used it went with the Excel ingest
- **openpyxl** — Excel file reading. Declared, but only the retired Excel ingest ever used it
- **click** — CLI interface for every entry point

## Conventions

- MONDO IDs are normalized to `MONDO:NNNNNNN` format (7-digit zero-padded)
- Ontology terms are represented as `{id, label}` dicts (SimpleTerm in schema)
- Large MeDIC product files are parsed with `yaml.CSafeLoader`; the pure-Python loader takes minutes on the 100MB+ `indication_list.yaml`
- The `datamodel/` directory is generated code — regenerate with `just gen-datamodel` after schema changes
