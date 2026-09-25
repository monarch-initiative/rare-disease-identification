# Rare Disease Identification - Build & ETL

SCHEMA := "src/rare_disease_identification/schema/rare_disease_prioritisation.yaml"
DATAMODEL_DIR := "src/rare_disease_identification/datamodel"
SOURCE := "src/prioritised-rare-disease-list.yml"
DRUGS := "data/drugs.yml"
FCEVIDENCE := "data/functional_capacity.yml"
VALUE_SETS := "data/value_sets.yml"
MAPPINGS := "mappings"
MEDIC_DIR := "../medic"
OUTPUT := "prioritised-rare-disease-list.yml"
CRITERIA := "config/prioritisation_criteria.yaml"
CRITERIA_JSON := "criteria.json"
CRITERIA_REPORT := "docs/criteria-assignment.md"
FIGURES := "docs/figures"
ICON_DIR := "site/assets/criteria"
# Page 1 of the manuscript's workflow figure. Not redistributed (background/ is
# gitignored); pull it out of the docx with `unzip -j <draft>.docx word/media/image4.png`.
WORKFLOW_FIGURE := "background/prioritisation-workflow-figure.png"
SUMMARY := "category_summary.yml"
TMP_DIR := "tmp"
MONDO_OBO := TMP_DIR / "mondo.obo"
MONDO_OBO_URL := "https://purl.obolibrary.org/obo/mondo.obo"
DISMECH_TSV := TMP_DIR / "mondo_emc.tsv"
DISMECH_TSV_URL := "https://github.com/monarch-initiative/dismech/releases/latest/download/mondo_emc.tsv"

# Default recipe
default: all

# Full pipeline: build drugs and value sets, merge, score against the six criteria
all: setup gen-datamodel build-drugs build-value-sets build-functional-capacity fetch-dismech merge build-criteria

# Install Python dependencies via uv
setup:
    uv sync
    uv pip install -e .

# Generate LinkML Python dataclasses from the schema
gen-datamodel: setup
    mkdir -p {{DATAMODEL_DIR}}
    uv run gen-python {{SCHEMA}} > {{DATAMODEL_DIR}}/rare_disease_prioritisation.py
    touch {{DATAMODEL_DIR}}/__init__.py

# Download mondo.obo, refreshing it whenever the release has moved on
fetch-mondo:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p {{TMP_DIR}}
    part="{{MONDO_OBO}}.part"
    etag="{{MONDO_OBO}}.etag"
    # Conditional GET: one round trip, and the 53MB body only crosses the wire
    # when the release has actually changed. Never guard on mere existence --
    # a stale mondo.obo silently poisons every recipe downstream of it.
    args=(-sSL --retry 3 --retry-delay 2 -o "$part" --etag-save "$etag.new")
    if [ -s "{{MONDO_OBO}}" ] && [ -s "$etag" ]; then
        args+=(--etag-compare "$etag")
    fi
    code=$(curl "${args[@]}" -w '%{http_code}' "{{MONDO_OBO_URL}}")
    if [ "$code" = "304" ]; then
        rm -f "$part" "$etag.new"
        echo "mondo.obo is current ($(grep -m1 '^data-version:' {{MONDO_OBO}}))"
        exit 0
    fi
    # Refuse to overwrite a good file with a redirect page or a truncated body.
    if [ ! -s "$part" ] || [ "$(wc -c < "$part")" -lt 10000000 ] \
       || ! head -50 "$part" | grep -q '^data-version:'; then
        rm -f "$part" "$etag.new"
        echo "fetch-mondo: download failed or did not look like mondo.obo (HTTP $code)" >&2
        exit 1
    fi
    mv "$part" "{{MONDO_OBO}}"
    mv "$etag.new" "$etag"
    echo "mondo.obo updated ($(grep -m1 '^data-version:' {{MONDO_OBO}}))"

# Assert mondo.obo is present without touching the network, for offline recipes
require-mondo:
    #!/usr/bin/env bash
    set -euo pipefail
    test -s "{{MONDO_OBO}}" || { echo "{{MONDO_OBO}} is missing; run \`just fetch-mondo\`" >&2; exit 1; }
    echo "using {{MONDO_OBO}} ($(grep -m1 '^data-version:' {{MONDO_OBO}}))"

# Download the dismech MONDO cross-reference, refreshing it when the release moved on
fetch-dismech:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p {{TMP_DIR}}
    part="{{DISMECH_TSV}}.part"
    etag="{{DISMECH_TSV}}.etag"
    # Same conditional GET as fetch-mondo, and for the same reason: never guard on
    # mere existence. `latest/download/` is a stable URL that silently follows the
    # releases, so a file that is merely present tells you nothing about its age.
    args=(-sSL --retry 3 --retry-delay 2 -o "$part" --etag-save "$etag.new")
    if [ -s "{{DISMECH_TSV}}" ] && [ -s "$etag" ]; then
        args+=(--etag-compare "$etag")
    fi
    code=$(curl "${args[@]}" -w '%{http_code}' "{{DISMECH_TSV_URL}}")
    if [ "$code" = "304" ]; then
        rm -f "$part" "$etag.new"
        echo "mondo_emc.tsv is current ($(($(wc -l < {{DISMECH_TSV}}) - 1)) disorders)"
        exit 0
    fi
    # A 404 page or a truncated body must not replace a good file. The header row
    # is the cheap structural check; the row floor catches a half-written asset.
    if [ ! -s "$part" ] \
       || ! head -1 "$part" | grep -q '^mondo_id	mondo_label	dismech_url' \
       || [ "$(wc -l < "$part")" -lt 100 ]; then
        rm -f "$part" "$etag.new"
        echo "fetch-dismech: download failed or did not look like mondo_emc.tsv (HTTP $code)" >&2
        exit 1
    fi
    mv "$part" "{{DISMECH_TSV}}"
    mv "$etag.new" "$etag"
    echo "mondo_emc.tsv updated ($(($(wc -l < {{DISMECH_TSV}}) - 1)) disorders)"

# Assert mondo_emc.tsv is present without touching the network, for offline recipes
require-dismech:
    #!/usr/bin/env bash
    set -euo pipefail
    test -s "{{DISMECH_TSV}}" || { echo "{{DISMECH_TSV}} is missing; run \`just fetch-dismech\`" >&2; exit 1; }
    echo "using {{DISMECH_TSV}} ($(($(wc -l < {{DISMECH_TSV}}) - 1)) disorders)"

# Update MONDO category fields via ontology ancestor traversal
update-categories: fetch-mondo
    uv run python -m rare_disease_identification.update_mondo_categories \
        --input "{{SOURCE}}" \
        --summary "{{SUMMARY}}" \
        --mondo-obo "{{MONDO_OBO}}"

# Build drug association report from MeDIC products
build-drugs:
    uv run python -m rare_disease_identification.build_drugs \
        --medic-dir "{{MEDIC_DIR}}" \
        --diseases "{{SOURCE}}" \
        --output "{{DRUGS}}"

# Regenerate derived (exact, narrower) ICD-10-CM value sets from Mondo
build-value-sets: fetch-mondo
    uv run python -m rare_disease_identification.build_value_sets \
        --diseases "{{SOURCE}}" \
        --mondo-obo "{{MONDO_OBO}}" \
        --overlay "{{MAPPINGS}}/mondo_icd10cm_exactmatch_mendelian.sssom.tsv" \
        --overlay "{{MAPPINGS}}/mondo_icd10cm_grouping_mendelian.sssom.tsv" \
        --retract "{{MAPPINGS}}/retractions.tsv" \
        --output "{{VALUE_SETS}}"

# Regenerate value sets without calling the NLM API (CI and offline work)
build-value-sets-offline: require-mondo
    uv run python -m rare_disease_identification.build_value_sets \
        --diseases "{{SOURCE}}" \
        --mondo-obo "{{MONDO_OBO}}" \
        --overlay "{{MAPPINGS}}/mondo_icd10cm_exactmatch_mendelian.sssom.tsv" \
        --overlay "{{MAPPINGS}}/mondo_icd10cm_grouping_mendelian.sssom.tsv" \
        --retract "{{MAPPINGS}}/retractions.tsv" \
        --output "{{VALUE_SETS}}" \
        --offline

# Merge source disease list with drug and value-set data into final output
# Derive the computable evidence lines of each functional-capacity assessment.
# EXPERT_DATABASE, the two policy lanes, PHENOTYPE_ANCHOR and COMPUTED_SCORE are
# functions of their source files, so they are regenerated rather than stored in
# SOURCE. Never writes to SOURCE; `merge` re-attaches them.
build-functional-capacity:
    uv run python -m rare_disease_identification.build_functional_capacity \
        -s "{{SOURCE}}" -o "{{FCEVIDENCE}}"

# One-off migration: drop derived evidence lines from the curated source
strip-derived-evidence:
    cd {{FRAILTY}} && uv run python strip_derived_evidence.py

merge:
    uv run python -m rare_disease_identification.merge \
        -s "{{SOURCE}}" \
        -d "{{DRUGS}}" \
        -v "{{VALUE_SETS}}" \
        -f "{{FCEVIDENCE}}" \
        -m "{{DISMECH_TSV}}" \
        -o "{{OUTPUT}}"

# ---------------------------------------------------------------- prioritisation criteria
# One config, config/prioritisation_criteria.yaml, decides which registry field
# counts as evidence for which of the six criteria. Everything below reads it.

# Score every disease against the six criteria -> criteria.json + the review document
build-criteria:
    uv run python -m rare_disease_identification.build_criteria \
        --diseases "{{OUTPUT}}" \
        --criteria "{{CRITERIA}}" \
        --output "{{CRITERIA_JSON}}" \
        --report "{{CRITERIA_REPORT}}"

# Upset plot over the six criteria, plus the full intersection table
upset: build-criteria
    uv run python scripts/figures/plot_criteria_upset.py \
        --criteria-json "{{CRITERIA_JSON}}" \
        --icon-dir "{{ICON_DIR}}" \
        --output-dir "{{FIGURES}}"

# Self-contained, shareable HTML report of the six criteria -> docs/criteria-report.html
criteria-report: build-criteria
    uv run python -m rare_disease_identification.build_criteria_report \
        --criteria "{{CRITERIA}}" \
        --criteria-json "{{CRITERIA_JSON}}" \
        --icon-dir "{{ICON_DIR}}" \
        --figure-dir "{{FIGURES}}" \
        --output "docs/criteria-report.html"

# Re-cut the six criterion glyphs from the workflow figure (the cut icons are committed)
criteria-icons:
    uv run python scripts/figures/extract_criteria_icons.py \
        --figure "{{WORKFLOW_FIGURE}}" \
        --criteria "{{CRITERIA}}" \
        --output-dir "{{ICON_DIR}}"

# Serve the site locally for development
serve:
    cd site && python3 -m http.server 8080

# Clean generated files
clean:
    rm -rf .venv/ {{DATAMODEL_DIR}} {{OUTPUT}} {{CRITERIA_JSON}} {{TMP_DIR}}

# ---------------------------------------------------------------- frailty curation
FRAILTY := "scripts/frailty"
REFCONFIG := "config/frailty_refval.yaml"
WORKLIST := TMP_DIR / "frailty_worklist.tsv"

# Cache Orphanet functional-consequence records as quotable markdown
frailty-orpha-cache:
    uv run python {{FRAILTY}}/build_orpha_cache.py

# Next N unreviewed diseases by score -> tmp/frailty_worklist.tsv
frailty-worklist n: frailty-orpha-cache frailty-ssa-cal
    cd {{FRAILTY}} && uv run python worklist.py {{n}} -o "{{justfile_directory()}}/{{WORKLIST}}"

# Cache a reference (PMID:..., DOI:...) for quoting
fetch-reference +refs:
    cd {{FRAILTY}} && uv run python fetch_reference.py {{refs}}

# Goes through the vendored wrapper (network-retry patch + affirmative snippet
# count), because the validator's own "Total checks: 0" counts issues found, not
# checks performed - a clean run and a no-op look identical without the audit.
#
# Every quote checked verbatim against its cached reference
verify-frailty-quotes: build-functional-capacity merge
    bash {{FRAILTY}}/run_reference_validator.sh validate data "{{OUTPUT}}" \
        --schema "{{SCHEMA}}" --target-class RareDiseaseCollection \
        --config "{{REFCONFIG}}" 2>&1 | grep -v fontTools

# LinkML schema conformance for the curated list
validate-frailty:
    uv run linkml-validate -s "{{SCHEMA}}" -C RareDiseaseCollection "{{SOURCE}}"

# Coverage, lane mix, disputed count
frailty-stats:
    cd {{FRAILTY}} && uv run python stats.py

# Crosswalk the SSA Compassionate Allowances list (POMS DI 23022.080) to Mondo
frailty-ssa-cal:
    cd {{FRAILTY}} && uv run python build_ssa_cal.py

# Affirmative, offline count of verified quotes (no network; advisory)
frailty-snippet-audit:
    uv run python -m rare_disease_identification.refval.reference_snippet_audit \
        --schema "{{SCHEMA}}" --config "{{REFCONFIG}}" "{{SOURCE}}"
