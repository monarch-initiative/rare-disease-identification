# Rare Disease Identification - Build & ETL

SCHEMA := "src/rare_disease_identification/schema/rare_disease_prioritisation.yaml"
DATAMODEL_DIR := "src/rare_disease_identification/datamodel"
SOURCE := "src/prioritised-rare-disease-list.yml"
DRUGS := "data/drugs.yml"
MEDIC_DIR := "../medic"
OUTPUT := "prioritised-rare-disease-list.yml"
SUMMARY := "category_summary.yml"
TMP_DIR := "tmp"
MONDO_OBO := TMP_DIR / "mondo.obo"
MONDO_OBO_URL := "https://purl.obolibrary.org/obo/mondo.obo"

# Default recipe
default: all

# Full pipeline: setup, generate datamodel, build drugs, merge
all: setup gen-datamodel build-drugs merge

# Install Python dependencies via uv
setup:
    uv sync
    uv pip install -e .

# Generate LinkML Python dataclasses from the schema
gen-datamodel: setup
    mkdir -p {{DATAMODEL_DIR}}
    uv run gen-python {{SCHEMA}} > {{DATAMODEL_DIR}}/rare_disease_prioritisation.py
    touch {{DATAMODEL_DIR}}/__init__.py

# Download mondo.obo into the tmp/ directory if it isn't already there
fetch-mondo:
    mkdir -p {{TMP_DIR}}
    test -f {{MONDO_OBO}} || curl -L -o {{MONDO_OBO}} {{MONDO_OBO_URL}}

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

# Merge source disease list with drug data into final output
merge:
    uv run python -m rare_disease_identification.merge \
        -s "{{SOURCE}}" \
        -d "{{DRUGS}}" \
        -o "{{OUTPUT}}"

# Serve the site locally for development
serve:
    cd site && python3 -m http.server 8080

# Clean generated files
clean:
    rm -rf .venv/ {{DATAMODEL_DIR}} {{OUTPUT}} {{TMP_DIR}}

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
verify-frailty-quotes:
    bash {{FRAILTY}}/run_reference_validator.sh validate data "{{SOURCE}}" \
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
