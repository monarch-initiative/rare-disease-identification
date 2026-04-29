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
