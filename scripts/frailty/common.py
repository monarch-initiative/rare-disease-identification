"""Shared paths and helpers for the frailty curation tooling."""
import pathlib, re, yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/prioritised-rare-disease-list.yml"
FC = ROOT / "functional-capacity"
FC_XML = FC / "build/fc.xml"
RANKED = FC / "build/ranked.tsv"
ASSERTIONS = FC / "build/assertions.tsv"
STATE_LISTS = FC / "data/state_lists"
CACHE = ROOT / "references_cache"
TMP = ROOT / "tmp"

ASSESSMENTS = ("work_capacity", "care_dependence")


def load_source():
    with open(SOURCE, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def orpha_codes(disease):
    """Orphanet codes declared on a disease entry, as bare numeric strings."""
    out = []
    for code in disease.get("ontology_terminology_codes") or []:
        m = re.match(r"^(?:Orphanet|ORPHA|ORDO):(\d+)$", str(code))
        if m:
            out.append(m.group(1))
    return sorted(set(out), key=int)


def icd10cm_codes(disease):
    out = []
    for code in disease.get("ontology_terminology_codes") or []:
        m = re.match(r"^ICD10CM:(.+)$", str(code))
        if m:
            out.append(m.group(1))
    return sorted(set(out))


def cache_path(reference):
    """references_cache filename for a PMID:/ORPHA: style curie."""
    return CACHE / (reference.replace(":", "_").replace("/", "_") + ".md")
