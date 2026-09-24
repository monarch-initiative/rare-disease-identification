#!/usr/bin/env python3
"""Emit the two collaborator review worksheets for issue #9.

    mappings/review/issue9_value_set_tiering.tsv    36 (disease, ICD-10-CM code) pairs
    mappings/review/issue9_list_membership.tsv      17 diseases

Two files because issue #9 tangles two questions at two granularities. "Not
specific enough" is a verdict on a *code*: Rubinstein-Taybi is a textbook rare
disease and `Q87.2` is a grab-bag, and both can be true at once. Tiering is per
(disease, code); membership is per disease. Asking them in one sheet invites an
answer that resolves neither.

Nothing in either sheet is hand-typed except the candidate set and the verbatim
prior positions. Labels, billable-leaf expansions, Mondo's own assertions,
subset tags and subtree counts are all read from source at generation time, so
regenerating is how you correct a row, not editing the TSV.

Sources: `tmp/mondo.obo`, `tmp/sssom/*.sssom.tsv` (written by `build-value-sets`),
`tmp/icd10cm_expansion.json` (topped up from the NLM Clinical Tables API on a
miss) and `src/prioritised-rare-disease-list.yml`.

Run as `python scripts/build_issue9_worksheets.py` from the repo root.
"""
import sys, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from rare_disease_identification.build_value_sets import (
    Icd10cmExpander, load_hierarchy, ancestors_of, read_data_version, under)

OUT = ROOT / "mappings" / "review"
OUT.mkdir(parents=True, exist_ok=True)

# --- sources ---------------------------------------------------------------
EXPANDER = Icd10cmExpander(ROOT / "tmp/icd10cm_expansion.json")

asserts = {}
for pred, fn in [("skos:exactMatch", "mondo_exactmatch_icd10cm.sssom.tsv"),
                 ("skos:narrowMatch", "mondo_narrowmatch_icd10cm.sssom.tsv"),
                 ("skos:broadMatch", "mondo_broadmatch_icd10cm.sssom.tsv")]:
    p = ROOT / "tmp/sssom" / fn
    if not p.exists():
        continue
    for row in csv.DictReader((l for l in p.open() if not l.startswith("#")), delimiter="\t"):
        asserts[(row["subject_id"], row["object_id"])] = pred

parents, labels = load_hierarchy(ROOT / "tmp/mondo.obo")
children = {}
for c, ps in parents.items():
    for p in ps:
        children.setdefault(p, set()).add(c)

on_list = set()
for line in (ROOT / "src/prioritised-rare-disease-list.yml").open():
    if line.startswith("- mondo_id: "):
        on_list.add(line.split(": ", 1)[1].strip())


def descendants(term):
    seen, stack = set(), [term]
    while stack:
        t = stack.pop()
        for c in children.get(t, ()):
            if c not in seen:
                seen.add(c)
                stack.append(c)
    return seen


def leaves(code):
    """Billable leaves at or under an anchor.

    ICD-10-CM codes extend without a separator past the decimal point (H35.5 ->
    H35.50), so prefix containment is the subsumption test; `under` is the
    build's own helper for it.
    """
    # Any cached anchor that is a prefix of `code` holds it; longest first.
    for anchor in [code] + [code[:n] for n in range(len(code) - 1, 2, -1)]:
        if anchor in EXPANDER.cache:
            got = [(c, l) for c, l in EXPANDER.cache[anchor] if under(c, code)]
            if got:
                return got
    return [(c, l) for c, l in EXPANDER.expand(code)]


def leaf_label(code):
    got = leaves(code)
    for c, l in got:
        if c == code:
            return l
    return ""


# --- the candidate (disease, code) pairs -----------------------------------
# proposed_tier is the issue's / Mondo's position, NOT an answer.
# prior_position quotes bpow verbatim where he has already ruled.
B = "bpow 2026-09-21"
ROWS = [
    # --- SMA: the anchor G12 is too coarse; one row per billable leaf --------
    ("MONDO:0001516", "G12.0",  "exact",    f"{B}: needs split to G12.0 + G12.1. G12.0 is 'classic' SMA."),
    ("MONDO:0001516", "G12.1",  "narrower", f"{B}: G12.1 includes other forms of SMA that are in the non-leaf MONDO:0001516."),
    ("MONDO:0001516", "G12.8",  "proxy",    f"{B}: G12.8 is problematic as an 'other'."),
    ("MONDO:0001516", "G12.9",  "proxy",    f"{B}: 'unspecified' could include some cases that match MONDO:0001516, but others that don't."),
    ("MONDO:0001516", "G12.20", "",         f"{B}: G12.2 sub-codes probably all belong somewhere else. Not individually ruled."),
    ("MONDO:0001516", "G12.24", "",         f"{B}: G12.2 sub-codes probably all belong somewhere else. Not individually ruled."),
    ("MONDO:0001516", "G12.25", "",         f"{B}: 'I'm really not sure what to do with G12.25. Although it has a similar name, I think that is usually used to represent a variant of ALS, not the group of genetic conditions that I think MONDO:0001516 is intended to represent.'"),
    ("MONDO:0001516", "G12.29", "",         f"{B}: G12.2 sub-codes probably all belong somewhere else. Not individually ruled."),
    ("MONDO:0004976", "G12.21", "exact",    f"{B}: 'G12.21 maps to MONDO:0004976.' Mondo already asserts this exactMatch."),
    ("MONDO:0008890", "G12.22", "exact",    f"{B}: 'G12.22 maps to MONDO:0008890.'"),
    ("MONDO:0018155", "G12.23", "exact",    f"{B}: 'G12.23 maps to MONDO:0018155.'"),
    # --- ruled out at term level -------------------------------------------
    ("MONDO:0002457", "Q75.4",  "excluded", f"{B}: 'NO (use mandibulofacial dysostosis below)'. Q75.4 is the dysostosis group, TCS is a subtype."),
    ("MONDO:0007838", "Q93.59", "excluded", f"{B}: 'NO (not specific enough)'. 'That ICD is a grab-bag of so many different potential chromosomal deletions that I don't think we can make any sense of the code by itself.'"),
    ("MONDO:0008006", "Q87.0",  "excluded", f"{B}: 'NO (not specific enough)'."),
    ("MONDO:0019188", "Q87.2",  "excluded", f"{B}: 'NO (not specific enough)'."),
    # --- accepted ------------------------------------------------------------
    ("MONDO:0018068", "Q91.4",  "narrower", f"{B}: 'YES' for the Q91.4-Q91.7 range as a whole."),
    ("MONDO:0018068", "Q91.5",  "narrower", f"{B}: 'YES' for the Q91.4-Q91.7 range as a whole."),
    ("MONDO:0018068", "Q91.6",  "narrower", f"{B}: 'YES' for the Q91.4-Q91.7 range as a whole."),
    ("MONDO:0018068", "Q91.7",  "narrower", f"{B}: 'YES' for the Q91.4-Q91.7 range as a whole."),
    ("MONDO:0018071", "Q91.0",  "narrower", f"{B}: 'YES' for the Q91.0-Q91.3 range as a whole."),
    ("MONDO:0018071", "Q91.1",  "narrower", f"{B}: 'YES' for the Q91.0-Q91.3 range as a whole."),
    ("MONDO:0018071", "Q91.2",  "narrower", f"{B}: 'YES' for the Q91.0-Q91.3 range as a whole."),
    ("MONDO:0018071", "Q91.3",  "narrower", f"{B}: 'YES' for the Q91.0-Q91.3 range as a whole."),
    ("MONDO:0018923", "D82.1",  "narrower", f"{B}: 'YES' for D82.1 + Q93.81."),
    ("MONDO:0018923", "Q93.81", "narrower", f"{B}: 'YES' for D82.1 + Q93.81."),
    ("MONDO:0019118", "H35.5",  "exact",    f"{B}: 'YES'. Mondo already asserts this exactMatch."),
    ("MONDO:0015483", "Q75.4",  "exact",    f"{B}: 'YES'. Mondo already asserts this exactMatch."),
    ("MONDO:0016669", "D57.2",  "exact",    f"{B}: 'YES'. D57.2 is Hb-SC disease, not sickle cell disease; currently misplaced on MONDO:0011382, see mappings/retractions.tsv."),
    ("MONDO:0016668", "D57.4",  "exact",    f"{B}: 'YES'. D57.4 is sickle-cell thalassemia specifically."),
    ("MONDO:0019259", "E70.0",  "exact",    f"{B}: 'YES'. E70.0 is 'Classical phenylketonuria'; MONDO:0009861 is the PKU group."),
    # --- neurofibromatosis split --------------------------------------------
    ("MONDO:0021061", "Q85.0",  "",         f"{B}: 'NO (split as below)'. Mondo asserts exactMatch on this pair, so a NO here is a retraction."),
    ("MONDO:0021061", "Q85.00", "",         f"{B}: not ruled. 'Neurofibromatosis, unspecified' is left over by the split."),
    ("MONDO:0021061", "Q85.09", "",         f"{B}: not ruled. 'Other neurofibromatosis' is left over by the split."),
    ("MONDO:0018975", "Q85.01", "exact",    f"{B}: 'YES'. Already on the list; Mondo already asserts this exactMatch."),
    ("MONDO:0007039", "Q85.02", "exact",    f"{B}: 'YES'. Already on the list; Mondo already asserts this exactMatch."),
    ("MONDO:0008075", "Q85.03", "exact",    f"{B}: 'YES (probably)'. Written as Q83.03 in the comment; Q83 is breast anomalies, Q85.03 is Schwannomatosis. Mondo already asserts this exactMatch. 'We may find we need to disambiguate with a subsequent computational phenotype, possibly after records review, but it will be a good series to go ahead and collect so we can evaluate that.'"),
]

# `fill_cohort_size` is the one column a site with records access can fill and we
# cannot: ProxyEntry.approximate_cohort_size, how much noise a second filter has
# to remove. Not a prevalence estimate.
HEAD = ["row_id", "mondo_id", "mondo_label", "icd10cm_code", "icd10cm_label",
        "n_billable_leaves", "billable_leaves", "mondo_asserts", "proposed_tier",
        "prior_position", "fill_tier", "fill_proxy_basis", "fill_reassign_to_mondo_id",
        "fill_comment", "fill_cohort_size", "fill_cohort_size_source",
        "fill_confidence"]

with (OUT / "issue9_value_set_tiering.tsv").open("w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
    w.writerow(HEAD)
    for i, (mondo, code, proposed, prior) in enumerate(ROWS, 1):
        lv = leaves(code)
        w.writerow([
            f"VS-{i:03d}", mondo, labels.get(mondo, ""), f"ICD10CM:{code}",
            leaf_label(code) or (lv[0][1] if len(lv) == 1 else ""),
            len(lv), ";".join(c for c, _ in lv),
            asserts.get((mondo, f"ICD10CM:{code}"), ""),
            proposed, prior, "", "", "", "", "", "", "",
        ])
print(f"wrote {OUT/'issue9_value_set_tiering.tsv'} ({len(ROWS)} rows)")


# --- sheet 2: list membership ----------------------------------------------
# A different question from tiering, and deliberately a different file: the
# tiering call is per (disease, code), the membership call is per disease.
# Answering one in the other's sheet is what tangled the issue thread.
SUBSETS = {}
cur = None
for line in (ROOT / "tmp/mondo.obo").open():
    line = line.rstrip("\n")
    if line.startswith("id: MONDO:"):
        cur = line[4:]
    elif line.startswith("subset: ") and cur:
        SUBSETS.setdefault(cur, []).append(line[8:].split(" ")[0])

MEMBERS = [
    ("MONDO:0001516", "bpow: no explicit list verdict; ruled on the codes only."),
    ("MONDO:0002457", "bpow: 'NO (use mandibulofacial dysostosis below)' — a verdict on Q75.4."),
    ("MONDO:0007838", "bpow: 'NO (not specific enough)' — a verdict on Q93.59."),
    ("MONDO:0008006", "bpow: 'NO (not specific enough)' — a verdict on Q87.0."),
    ("MONDO:0018068", "bpow: 'YES'."),
    ("MONDO:0018071", "bpow: 'YES'."),
    ("MONDO:0018923", "bpow: 'YES'."),
    ("MONDO:0019118", "bpow: 'YES'. Tagged disease_grouping by Mondo."),
    ("MONDO:0019188", "bpow: 'NO (not specific enough)' — a verdict on Q87.2."),
    ("MONDO:0021061", "bpow: 'NO (split as below)'."),
    ("MONDO:0015483", "bpow: 'YES'."),
    ("MONDO:0016669", "bpow: 'YES'."),
    ("MONDO:0016668", "bpow: 'YES'."),
    ("MONDO:0019259", "bpow: 'YES'."),
    ("MONDO:0018975", "bpow: 'YES'. Already on the list."),
    ("MONDO:0007039", "bpow: 'YES'. Already on the list."),
    ("MONDO:0008075", "bpow: 'YES (probably)'."),
]

anchors_by_term = {}
for mondo, code, _p, _c in ROWS:
    anchors_by_term.setdefault(mondo, []).append(code)

MHEAD = ["row_id", "mondo_id", "mondo_label", "already_on_list", "mondo_subsets",
         "n_descendants_total", "n_descendants_on_list", "nearest_on_list_ancestor",
         "icd10cm_anchors_in_play", "prior_position",
         "fill_include_on_list", "fill_level_is_right", "fill_rationale"]

with (OUT / "issue9_list_membership.tsv").open("w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
    w.writerow(MHEAD)
    for i, (mondo, prior) in enumerate(MEMBERS, 1):
        desc = descendants(mondo)
        anc = [a for a in ancestors_of(mondo, parents) if a in on_list and a != mondo]
        w.writerow([
            f"LM-{i:03d}", mondo, labels.get(mondo, ""),
            "yes" if mondo in on_list else "no",
            ";".join(SUBSETS.get(mondo, [])),
            len(desc), len(desc & on_list),
            ";".join(f"{a} {labels.get(a,'')}" for a in sorted(anc)[:3]),
            ";".join(anchors_by_term.get(mondo, [])),
            prior, "", "", "",
        ])
print(f"wrote {OUT/'issue9_list_membership.tsv'} ({len(MEMBERS)} rows)")
EXPANDER.save()

# Printed rather than written into the TSVs: a leading comment row would break the
# clean spreadsheet import these are for. A regeneration that moves either version
# is visible here.
print(f"built from mondo {read_data_version(ROOT / 'tmp/mondo.obo')}, "
      f"icd-10-cm FY2026 via the NLM Clinical Tables API")
