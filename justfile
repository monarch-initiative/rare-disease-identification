# Rare Disease Identification - Build & ETL

SCHEMA := "src/rare_disease_identification/schema/rare_disease_prioritisation.yaml"
DATAMODEL_DIR := "src/rare_disease_identification/datamodel"
EXCEL := "data/prioritizing rare diseases for phenotypic characterization.xlsx"
DRUGS := "data/drugs.yml"
MEDIC_DIR := "../medic"
OUTPUT := "prioritised-rare-disease-list.yml"

# Default recipe
default: all

# Full pipeline: setup, generate datamodel, extract data, build drugs
all: setup gen-datamodel extract-list build-drugs

# Install Python dependencies via uv
setup:
    uv sync
    uv pip install -e .

# Generate LinkML Python dataclasses from the schema
gen-datamodel: setup
    mkdir -p {{DATAMODEL_DIR}}
    uv run gen-python {{SCHEMA}} > {{DATAMODEL_DIR}}/rare_disease_prioritisation.py
    touch {{DATAMODEL_DIR}}/__init__.py

# Extract rare disease list from Excel into YAML, merging treatments
extract-list: gen-datamodel
    uv run python -m rare_disease_identification.extract \
        -i "{{EXCEL}}" \
        -t "{{DRUGS}}" \
        -o "{{OUTPUT}}"

# Build drug association report from MeDIC products
build-drugs:
    uv run python -m rare_disease_identification.build_drugs \
        --medic-dir "{{MEDIC_DIR}}" \
        --diseases "{{OUTPUT}}" \
        --output "{{DRUGS}}"

# Serve the site locally for development
serve:
    cd site && python3 -m http.server 8080

# Clean generated files
clean:
    rm -rf .venv/ {{DATAMODEL_DIR}} {{OUTPUT}}
