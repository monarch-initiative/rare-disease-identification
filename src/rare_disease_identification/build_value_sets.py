"""Regenerate the derived tiers of every disease's terminology value sets.

Output: data/value_sets.yml, joined into the final list by `merge.py`.

Only `exact` and `narrower` are produced here. `proxy` and `excluded` are curated
in `src/prioritised-rare-disease-list.yml` and this script never sees them — which
is the point. Derived data written into the curated source is how the ontology
enrichment fields on this list ended up frozen and unreproducible; see
`issues/issue_ontology_enrichment_dropped.md`.

The rule, from `schema/value_set.yaml`:

    exact    = skos:exactMatch asserted by Mondo on the disease itself
    narrower = skos:narrowMatch on the disease, plus exactMatch or narrowMatch on
               any is_a descendant of it (a subtype's code is by construction
               narrower than the disease)

    then each anchor is expanded down the target terminology's own hierarchy to
    the codes a query actually uses

Everything else is deliberately excluded and counted in the report:

  - `skos:broadMatch` is a superset of the disease. It belongs in `proxy`, which
    is curated, not here.
  - `oboInOwl:hasDbXref` carries no predicate. 104 of Mondo's ICD-10-CM dbxrefs
    have no matching SKOS row and are a mix of broad, narrow and block ranges
    (`MONDO:0005045` cardiomyopathy to `I42.1` hypertrophic obstructive, for
    instance), so treating them as exact would quietly put supersets in the
    safe tiers.
  - `skos:closeMatch` and `skos:relatedMatch` are not containment claims.
  - Block ranges (`E70-E88`) are not assignable codes.

Two overrides exist because Mondo lags what we know:

  --overlay adds proposed mappings from local SSSOM files, so a value set reflects
    a fix before it lands upstream.
  --retract drops a (subject, object) pair that Mondo asserts wrongly. SSSOM cannot
    express a retraction, so it lives in its own file with a reason per row.

Usage:
    python -m rare_disease_identification.build_value_sets
    python -m rare_disease_identification.build_value_sets --offline
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

import click
import yaml

try:
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

PURL = "http://purl.obolibrary.org/obo/mondo/mappings/mondo_{pred}_icd10cm.sssom.tsv"

# Predicates that can put a code in a safe tier, and which tier they land in when
# asserted on the disease itself. Everything absent from this map is reported and
# dropped.
SAFE_PREDICATES = {"exactmatch": "exact", "narrowmatch": "narrower"}
REPORTED_PREDICATES = ["exactmatch", "narrowmatch", "broadmatch",
                       "closematch", "relatedmatch", "hasdbxref"]

NLM_ICD10CM = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"


def is_block(code: str) -> bool:
    """ICD-10-CM block and chapter ranges (`E70-E88`) are not assignable."""
    return "-" in code.split(":", 1)[-1]


def under(child: str, parent: str) -> bool:
    """True if `child` sits at or beneath `parent` in ICD-10-CM's code hierarchy.

    Prefix containment is a sound subsumption test here because a code's
    ancestors are always its own prefixes: `E83.31` is under `E83.3` is under
    `E83`. Both arguments must carry the same CURIE prefix.
    """
    return child == parent or child.startswith(parent)


# --------------------------------------------------------------------------- #
# Mondo
# --------------------------------------------------------------------------- #

def fetch_sssom(pred: str, cache_dir: Path) -> list[dict]:
    """Download (and cache) one Mondo SSSOM mapping file."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"mondo_{pred}_icd10cm.sssom.tsv"
    if not path.exists():
        click.echo(f"  fetching {PURL.format(pred=pred)}")
        urllib.request.urlretrieve(PURL.format(pred=pred), path)
    with open(path) as f:
        lines = [line for line in f if not line.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


def load_sssom_file(path: Path) -> list[tuple[str, str, str, str]]:
    """Read (subject, predicate, object, object_label) out of any SSSOM TSV."""
    with open(path) as f:
        lines = [line for line in f if not line.startswith("#")]
    out = []
    for row in csv.DictReader(lines, delimiter="\t"):
        pred = row.get("predicate_id", "").split(":")[-1].lower()
        pred = {"exactmatch": "exactmatch", "narrowmatch": "narrowmatch",
                "broadmatch": "broadmatch", "closematch": "closematch",
                "relatedmatch": "relatedmatch"}.get(pred, pred)
        out.append((row["subject_id"], pred, row["object_id"],
                    row.get("object_label", "")))
    return out


def load_hierarchy(mondo_obo: Path) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Parse `is_a` edges and labels out of mondo.obo, skipping obsolete terms."""
    parents: dict[str, set[str]] = defaultdict(set)
    labels: dict[str, str] = {}
    current, obsolete = None, False
    with open(mondo_obo) as f:
        for line in f:
            line = line.rstrip("\n")
            if line == "[Term]":
                current, obsolete = None, False
            elif line.startswith("id: MONDO:"):
                current = line[4:].strip()
            elif not current:
                continue
            elif line.startswith("name: "):
                labels[current] = line[6:]
            elif line.startswith("is_obsolete: true"):
                obsolete = True
                parents.pop(current, None)
            elif line.startswith("is_a: ") and not obsolete:
                parents[current].add(line[6:].split()[0])
    return parents, labels


def ancestors_of(term: str, parents: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    frontier = set(parents.get(term, ()))
    while frontier:
        seen |= frontier
        frontier = {p for t in frontier for p in parents.get(t, ())} - seen
    return seen


# --------------------------------------------------------------------------- #
# ICD-10-CM expansion
# --------------------------------------------------------------------------- #

class Icd10cmExpander:
    """Expand an anchor code to the billable leaves beneath it.

    Cached on disk because the full list needs one API call per distinct anchor
    and the answer only changes once a year.
    """

    #: Flush to disk this often. The first run needs ~2,000 calls and takes about
    #: ten minutes; losing all of it to a Ctrl-C would be unkind.
    SAVE_EVERY = 50

    def __init__(self, cache_path: Path, offline: bool = False):
        self.cache_path = cache_path
        self.offline = offline
        self.cache: dict[str, list[list[str]]] = {}
        if cache_path.exists():
            self.cache = json.loads(cache_path.read_text())
        self.fetched = 0

    def expand(self, code: str) -> list[tuple[str, str]]:
        """Return [(code, label)] for the billable leaves at or under `code`."""
        if code not in self.cache:
            if self.offline:
                raise click.ClickException(
                    f"{code} is not in {self.cache_path} and --offline was given. "
                    f"Re-run without --offline to fetch it."
                )
            query = urllib.parse.urlencode(
                {"sf": "code", "terms": code, "maxList": "500"}
            )
            with urllib.request.urlopen(f"{NLM_ICD10CM}?{query}", timeout=30) as r:
                data = json.load(r)
            hits = data[3] if len(data) > 3 and data[3] else []
            self.cache[code] = [[c, l] for c, l in hits if under(c, code)]
            self.fetched += 1
            if self.fetched % self.SAVE_EVERY == 0:
                self.save()
            time.sleep(0.08)
        return [(c, l) for c, l in self.cache[code]]

    def label(self, code: str) -> str:
        """The code's own label, or the best available if it is not billable."""
        for c, l in self.expand(code):
            if c == code:
                return l
        return ""

    def save(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=0, sort_keys=True))


# --------------------------------------------------------------------------- #
# The rule
# --------------------------------------------------------------------------- #

def drop_redundant(anchors: dict[str, dict]) -> dict[str, dict]:
    """Drop any anchor that already sits inside another anchor's expansion.

    If Mondo gives both `E75.24` and `E75.242` for one disease, the second adds
    nothing: it is already in the first one's billable leaves. Keeping both would
    double-count the same patients and make the value set look larger than it is.
    """
    codes = sorted(anchors, key=len)
    keep: dict[str, dict] = {}
    for code in codes:
        if any(under(code, other) and code != other for other in keep):
            continue
        keep[code] = anchors[code]
    return keep


def build_entries(
    mondo_id: str,
    direct: dict[str, list[tuple[str, str]]],
    inherited: list[tuple[str, str, str, str]],
    expander: Icd10cmExpander,
    labels: dict[str, str],
) -> tuple[list[dict], list[dict]]:
    """Compute one disease's `exact` and `narrower` entries.

    `direct` maps predicate -> [(code, object_label)] asserted on this disease.
    `inherited` is [(code, object_label, via_mondo_id, predicate)] from descendants.
    """
    exact_anchors: dict[str, dict] = {}
    narrow_anchors: dict[str, dict] = {}

    for pred, tier in SAFE_PREDICATES.items():
        target = exact_anchors if tier == "exact" else narrow_anchors
        for code, obj_label in direct.get(pred, []):
            target[code] = {
                "code": code,
                "label": obj_label,
                "provenance": "MONDO_EXACT_MATCH" if tier == "exact" else "MONDO_NARROW_MATCH",
            }

    for code, obj_label, via, _pred in inherited:
        if code in exact_anchors:
            continue
        narrow_anchors[code] = {
            "code": code,
            "label": obj_label,
            "provenance": "MONDO_DESCENDANT",
            "via_mondo_id": via,
            "via_mondo_label": labels.get(via, ""),
        }

    # An exact anchor supersedes any narrower anchor inside it: the leaves are
    # already there, and the stronger provenance is the truer statement.
    exact_anchors = drop_redundant(exact_anchors)
    narrow_anchors = drop_redundant(narrow_anchors)
    narrow_anchors = {
        c: e for c, e in narrow_anchors.items()
        if not any(under(c, x) for x in exact_anchors)
    }

    def finish(anchors: dict[str, dict]) -> list[dict]:
        """Codes are carried bare internally so prefix containment works; the
        `ICD10CM:` prefix goes back on at the boundary, because the schema wants
        CURIEs and a value set is meaningless without knowing its terminology."""
        out = []
        for code in sorted(anchors):
            entry = dict(anchors[code])
            leaves = expander.expand(code)
            if not entry.get("label"):
                entry["label"] = expander.label(code)
            entry["code"] = f"ICD10CM:{code}"
            entry["expanded_codes"] = [f"ICD10CM:{c}" for c, _ in leaves]
            # Key order matches the schema so the YAML reads top-down.
            out.append({
                k: entry[k] for k in
                ("code", "label", "expanded_codes", "provenance",
                 "via_mondo_id", "via_mondo_label")
                if entry.get(k)
            })
        return out

    return finish(exact_anchors), finish(narrow_anchors)


# --------------------------------------------------------------------------- #

@click.command()
@click.option("--diseases", type=click.Path(exists=True, path_type=Path),
              default=Path("src/prioritised-rare-disease-list.yml"), show_default=True,
              help="Curated disease list. Read only; never written to.")
@click.option("--output", "-o", type=click.Path(path_type=Path),
              default=Path("data/value_sets.yml"), show_default=True)
@click.option("--cache-dir", type=click.Path(path_type=Path), default=Path("tmp/sssom"),
              show_default=True, help="Where Mondo's SSSOM releases are cached.")
@click.option("--mondo-obo", type=click.Path(exists=True, path_type=Path),
              default=Path("tmp/mondo.obo"), show_default=True,
              help="mondo.obo, for the is_a closure. Get it with `just fetch-mondo`.")
@click.option("--expansion-cache", type=click.Path(path_type=Path),
              default=Path("tmp/icd10cm_expansion.json"), show_default=True)
@click.option("--overlay", type=click.Path(exists=True, path_type=Path), multiple=True,
              help="Extra SSSOM files whose mappings are treated as if Mondo asserted them.")
@click.option("--retract", type=click.Path(path_type=Path),
              default=Path("mappings/retractions.tsv"), show_default=True,
              help="TSV of subject_id/object_id pairs to ignore from Mondo, with a reason.")
@click.option("--mondo-version", default="", help="Recorded in the output. Read from mondo.obo if unset.")
@click.option("--terminology-version", default="FY2026", show_default=True)
@click.option("--offline", is_flag=True, help="Fail rather than call the NLM API.")
def main(diseases: Path, output: Path, cache_dir: Path, mondo_obo: Path,
         expansion_cache: Path, overlay: tuple[Path, ...], retract: Path,
         mondo_version: str, terminology_version: str, offline: bool):
    """Regenerate `exact` and `narrower` ICD-10-CM value sets for every disease."""
    with open(diseases) as f:
        source = yaml.load(f, Loader=_Loader)
    entries = [d for d in source.get("diseases", []) if d.get("mondo_id")]
    on_list = {d["mondo_id"] for d in entries}
    click.echo(f"Loaded {len(entries)} diseases from {diseases}")

    guard_source(entries, diseases)

    retracted = load_retractions(retract)
    if retracted:
        click.echo(f"Loaded {len(retracted)} retraction(s) from {retract}")

    click.echo("Loading Mondo ICD-10-CM mappings:")
    mappings, dropped = collect_mappings(cache_dir, overlay, retracted)
    for pred in REPORTED_PREDICATES:
        n = sum(len(v.get(pred, [])) for v in mappings.values())
        note = "" if pred in SAFE_PREDICATES else "  (not a containment claim, dropped)"
        if pred == "hasdbxref":
            note = "  (no predicate, dropped)"
        click.echo(f"  {pred:13s} {n:6d}{note}")
    click.echo(f"  dropped {dropped['block']} block-range objects, "
               f"{dropped['retracted']} retracted")

    click.echo(f"Loading hierarchy from {mondo_obo}")
    parents, labels = load_hierarchy(mondo_obo)
    if not mondo_version:
        mondo_version = read_data_version(mondo_obo)

    # Invert once: for every mapped Mondo term, register its safe codes against
    # each of its ancestors that is on the list. Cheaper than a descendant walk
    # per disease, and the direction the data is already in.
    inherited: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)
    for subject, by_pred in mappings.items():
        rows = [(c, l, pred) for pred in SAFE_PREDICATES for c, l in by_pred.get(pred, [])]
        if not rows:
            continue
        for anc in ancestors_of(subject, parents) & on_list:
            if anc == subject:
                continue
            for code, obj_label, pred in rows:
                inherited[anc].append((code, obj_label, subject, pred))

    expander = Icd10cmExpander(expansion_cache, offline=offline)
    today = date.today().isoformat()
    out_diseases, n_exact, n_narrow, n_codes = [], 0, 0, 0

    with click.progressbar(entries, label="Building value sets") as bar:
        for disease in bar:
            mondo_id = disease["mondo_id"]
            exact, narrower = build_entries(
                mondo_id, mappings.get(mondo_id, {}), inherited.get(mondo_id, []),
                expander, labels,
            )
            if not exact and not narrower:
                continue
            value_set = {"terminology": "ICD10CM"}
            if exact:
                value_set["exact"] = exact
            if narrower:
                value_set["narrower"] = narrower
            value_set.update({
                "mondo_version": mondo_version,
                "terminology_version": terminology_version,
                "generated_on": today,
            })
            out_diseases.append({"mondo_id": mondo_id, "value_sets": [value_set]})
            n_exact += len(exact)
            n_narrow += len(narrower)
            n_codes += sum(len(e["expanded_codes"]) for e in exact + narrower)

    expander.save()
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        yaml.dump({"diseases": out_diseases}, f, default_flow_style=False,
                  allow_unicode=True, sort_keys=False)

    click.echo(f"\nWrote {len(out_diseases)} diseases to {output}")
    click.echo(f"  {n_exact} exact anchors, {n_narrow} narrower anchors")
    click.echo(f"  {n_codes} queryable codes after expansion")
    click.echo(f"  {len(entries) - len(out_diseases)} diseases have no safe code")
    if expander.fetched:
        click.echo(f"  {expander.fetched} anchors expanded from the NLM API, "
                   f"rest from {expansion_cache}")


def guard_source(entries: list[dict], path: Path):
    """Refuse to run if the curated source carries a derived tier.

    `exact` and `narrower` are regenerated here on every build, so anything hand
    written into them in `src/` is silently discarded. Better to stop and say so.
    """
    offenders = [
        d["mondo_id"] for d in entries
        for vs in d.get("value_sets", []) or []
        if vs.get("exact") or vs.get("narrower")
    ]
    if offenders:
        raise click.ClickException(
            f"{len(offenders)} disease(s) in {path} carry a hand-written `exact` or "
            f"`narrower` tier, which this script regenerates: "
            f"{', '.join(offenders[:5])}"
            f"{' ...' if len(offenders) > 5 else ''}. "
            f"Move them to `proxy`, or fix the mapping in Mondo so they derive."
        )


def load_retractions(path: Path) -> set[tuple[str, str]]:
    """(subject_id, object_id) pairs Mondo asserts but we do not trust."""
    if not path.exists():
        return set()
    with open(path) as f:
        rows = [line for line in f if not line.startswith("#")]
    out = set()
    for row in csv.DictReader(rows, delimiter="\t"):
        if row.get("subject_id") and row.get("object_id"):
            out.add((row["subject_id"], row["object_id"]))
    return out


def collect_mappings(cache_dir: Path, overlay: tuple[Path, ...],
                     retracted: set[tuple[str, str]]) -> tuple[dict, dict]:
    """subject -> predicate -> [(code, object_label)], plus a count of what was dropped."""
    mappings: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(lambda: defaultdict(list))
    dropped = {"block": 0, "retracted": 0}

    def add(subject: str, pred: str, obj: str, obj_label: str):
        if not subject or not obj:
            return
        if (subject, obj) in retracted:
            dropped["retracted"] += 1
            return
        if is_block(obj):
            dropped["block"] += 1
            return
        code = obj.replace("ICD10CM:", "")
        if (code, obj_label) not in mappings[subject][pred]:
            mappings[subject][pred].append((code, obj_label))

    for pred in REPORTED_PREDICATES:
        for row in fetch_sssom(pred, cache_dir):
            add(row.get("subject_id", ""), pred, row.get("object_id", ""),
                row.get("object_label", ""))

    for path in overlay:
        rows = load_sssom_file(path)
        click.echo(f"  overlay {path} ({len(rows)} mappings)")
        for subject, pred, obj, obj_label in rows:
            add(subject, pred, obj, obj_label)

    return mappings, dropped


def read_data_version(mondo_obo: Path) -> str:
    with open(mondo_obo) as f:
        for line in f:
            if line.startswith("data-version:"):
                return line.split(":", 1)[1].strip()
            if line.startswith("[Term]"):
                break
    return ""


if __name__ == "__main__":
    main()
