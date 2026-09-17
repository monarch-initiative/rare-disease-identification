"""Pre-generate the deterministic evidence lanes for the worklist.

The EXPERT_DATABASE, FEDERAL_POLICY_LIST, STATE_POLICY_LIST and COMPUTED_SCORE
lanes are derived
from files, not judgement, so they are built here rather than hand-written. The
curator then adds the LITERATURE and MODEL_JUDGEMENT lanes and sets the level.

Emits a YAML patch skeleton; nothing is written to the source list by this script.
"""
import argparse, csv, re, yaml, pathlib
from common import (CACHE, TMP, RANKED, FC, ASSESSMENTS, cache_path)
from anchors import term_scores, corpus, anchor_evidence

SCORE_METHOD = "phenotype-wsum-norm"
SCORE_VERSION = "2026-09-16"

WORK_ITEMS = {"Engaging in paid work in a standard environment",
              "Performing professional tasks"}
CARE_ITEMS = {"Washing oneself", "Dressing/undressing", "Eating", "Drinking",
              "Transferring oneself", "Regulating urination", "Regulating defecation",
              "Caring for body parts (skin, teeth, nails, hair, genitals)",
              "Managing one's health (diet, medications, prevention, needs, assistance, monitoring)",
              "Moving around within the home"}
SEV_RANK = {"Complete": 4, "Severe": 3, "Moderate": 2, "Low": 1, "Unspecified": 0}
# Orphanet frequency bands map onto the >=30% bar in the impairment definitions:
# "Very frequent" and "Frequent" clear it, "Occasional" sits below it. A severe
# limitation that is only occasional argues for a LOWER level, not a higher one.
FREQ_MEETS_BAR = {"Very frequent", "Frequent"}
CAL_XWALK = TMP / "ssa/cal_mondo_crosswalk.tsv"

POLICY_TSV = FC / "build/policy_evidence.tsv"

SRC_TITLE = {
    "Nebraska": "Nebraska Medicaid Medically Frail Exemption Conditions Index",
    "Minnesota": "Minnesota DHS Appendix A, medically frail definition (PL 119-21 s71119)",
    "Montana": "Montana DPHHS medically frail conditions",
}


def policy_index():
    """MONDO id -> policy rows, from functional-capacity/build/policy_evidence.tsv.

    Never match ICD codes against the state lists by hand. The lists enumerate 5-6
    character children (G40811, Lennox-Gastaut *with status epilepticus*) while Mondo
    maps the 4-character concept (G4081); 492 of the 1,164 hits in that table come
    from that direction alone. Exact matching yields a confident, wrong "no state
    lists this" - the worst error this lane can make.
    """
    if not POLICY_TSV.exists():
        raise SystemExit(f"missing {POLICY_TSV}\nRebuild: python3 "
                         "functional-capacity/scripts/step9_policy_evidence.py")
    out = {}
    with open(POLICY_TSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            out.setdefault(r["mondo_id"], []).append(r)
    return out


def orpha_rows(code):
    """Parse the quotable bullet lines back out of the cached markdown."""
    p = CACHE / f"ORPHA_{code}.md"
    if not p.exists():
        return None
    txt = p.read_text(encoding="utf-8")
    validated = "**Validation status:** Validated" in txt
    expert = "**Expert-validated:** yes" in txt
    rows = []
    for line in txt.splitlines():
        m = re.match(r"^- (.+?) \| (.+?) \| (.+?) \| (.+?)(?: \(work\))?$", line.strip())
        if m:
            rows.append(tuple(x.strip() for x in m.groups()))
    return {"validated": validated, "expert": expert, "rows": rows}


def orpha_evidence(code, slot):
    info = orpha_rows(code)
    if not info:
        return []
    items = WORK_ITEMS if slot == "work_capacity" else CARE_ITEMS
    picked = [r for r in info["rows"] if r[0] in items]
    if not picked:
        return []
    picked.sort(key=lambda r: SEV_RANK.get(r[2], 0), reverse=True)
    keep = picked[:2] if slot == "work_capacity" else picked[:4]
    strong = info["validated"] and info["expert"]
    out = []
    for name, freq, sev, temp in keep:
        meets = freq in FREQ_MEETS_BAR and sev in ("Severe", "Complete")
        below = freq not in FREQ_MEETS_BAR or sev in ("Low", "Unspecified")
        direction = "SUPPORTS" if meets else ("DISPUTES" if below else "NEUTRAL")
        out.append({
            "lane": "EXPERT_DATABASE",
            "direction": direction,
            "strength": "STRONG" if strong else "MODERATE",
            "reference": f"ORPHA:{code}",
            "reference_title": "Orphanet functional consequences dataset",
            "quote": f"{name} | {freq} | {sev} | {temp}",
            "explanation": (
                f"Orphanet{' expert-validated' if strong else ''} rating of "
                f"{name.lower()}: {sev.lower()} limitation, {freq.lower()} in this disease"
                + ("." if meets else
                   f" - {freq.lower()} sits below the >=30% bar, so this argues for a lower level."
                   if freq not in FREQ_MEETS_BAR else ".")),
            "curator_type": "PIPELINE",
        })
    return out


def policy_evidence(rows):
    """One STATE_POLICY_LIST line per state that reaches this disease.

    Montana lists by name rather than code and assigns each condition to one of the
    five statutory categories in 42 CFR 440.315. That category is the most directly
    citable thing in this lane, so it lands in source_statement.
    """
    out = []
    for r in rows:
        src, mt, val = r["source"], r["match_type"], r["matched_value"]
        if mt == "name_match":
            stmt = f'listed as "{val}"'
            if r.get("statutory_category"):
                stmt += f" | statutory category: {r['statutory_category']}"
            how = "names this condition directly"
            ref = f"MTFRAIL:{val.replace(' ', '_')[:60]}"
        else:
            stmt = f"{val} reached by {mt.replace('_', ' ')}"
            how = f"reaches {val} on its code list"
            ref = val
        out.append({
            "lane": "STATE_POLICY_LIST",
            "direction": "SUPPORTS",
            "strength": "MODERATE",
            "reference": ref,
            "reference_title": SRC_TITLE.get(src, src),
            "source_statement": stmt,
            "explanation": (f"{src} {how}, treating it as qualifying for the "
                            "medically-frail exemption."),
            "curator_type": "PIPELINE",
        })
    return out


def cal_index():
    """MONDO id -> [(condition, POMS section)] from the SSA CAL crosswalk."""
    out = {}
    if not CAL_XWALK.exists():
        return out
    with open(CAL_XWALK, encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            out.setdefault(r["mondo_id"], []).append(
                (r["cal_condition"], r["poms_section"]))
    return out


def cal_evidence(mid, slot, cal):
    """SSA Compassionate Allowances lines.

    Only ever attached to work_capacity: a CAL listing is a determination that the
    condition precludes substantial gainful activity. It is silent on whether the
    person needs help with personal care, and asserting it on that axis would be
    inventing a claim SSA did not make.
    """
    if slot != "work_capacity":
        return []
    out = []
    for cond, sec in cal.get(mid, []):
        code = sec.replace("DI ", "").replace(".", "")
        out.append({
            "lane": "FEDERAL_POLICY_LIST",
            "direction": "SUPPORTS",
            "strength": "MODERATE",
            "reference": f"SSACAL:{code}",
            "reference_title": ("SSA Compassionate Allowances condition list "
                                "(POMS DI 23022.080)"),
            "quote": f"{cond} | {sec} | Compassionate Allowance condition",
            "explanation": (
                "The US Social Security Administration fast-tracks this condition as a "
                "Compassionate Allowance, a national determination that it precludes "
                "substantial gainful activity - the same question this axis asks."),
            "curator_type": "PIPELINE",
        })
    return out


def score_evidence(row, slot):
    s = row["work_score"] if slot == "work_capacity" else row["care_score"]
    axis = "inability to sustain work" if slot == "work_capacity" else "need for daily care"
    drivers = row["top_work_drivers"] if slot == "work_capacity" else row["top_care_drivers"]
    return [{
        "lane": "COMPUTED_SCORE",
        "direction": "SUPPORTS",
        "strength": "WEAK",
        "reference": f"RDIDRUN:{SCORE_METHOD}/{SCORE_VERSION}",
        "reference_title": "Functional capacity phenotype score",
        "source_statement": f"{slot} score {s} over {row['n_phenotypes']} HPO annotations",
        "explanation": (f"Weighted HPO findings for {axis}"
                        + (f", driven by: {drivers}." if drivers else ".")
                        + " Ranking signal only."),
        "curator_type": "PIPELINE",
    }]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--worklist", default=str(TMP / "frailty_worklist.tsv"))
    ap.add_argument("-o", "--output", default=str(TMP / "frailty_skeleton.yaml"))
    args = ap.parse_args()

    with open(args.worklist, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    cal = cal_index()
    policy = policy_index()
    scores, corp = term_scores(), corpus()
    patch = {}
    for r in rows:
        icd = [c for c in r["icd10cm"].split(";") if c]
        prows = policy.get(r["mondo_id"], [])
        codes = [c.split(":")[1] for c in r["orpha_cached"].split(";") if c]
        entry = {}
        for slot in ASSESSMENTS:
            ev = []
            for c in codes:
                ev += orpha_evidence(c, slot)
            ev += policy_evidence(prows)
            ev += cal_evidence(r["mondo_id"], slot, cal)
            anch = anchor_evidence(r["mondo_id"], slot, scores, corp)
            # PHENOTYPE_ANCHOR is the same HPOA data as COMPUTED_SCORE, cited
            # finding by finding. Never emit both: they are one source.
            ev += anch if anch else score_evidence(r, slot)
            entry[slot] = {
                "impairment": "UNKNOWN",
                "score": float(r["work_score"] if slot == "work_capacity" else r["care_score"]),
                "score_method": SCORE_METHOD,
                "score_version": SCORE_VERSION,
                "care_context": "UNKNOWN",
                "rationale": "TODO",
                "evidence": ev,
                "curation_status": "UNREVIEWED",
                "claims_selectable": bool(icd),
            }
            if icd:
                # CURIEs, never bare codes: a bare "E83.01" is not resolvable or checkable.
                entry[slot]["icd10cm_codes"] = [f"ICD10CM:{c}" for c in icd]
        patch[r["mondo_id"]] = entry

    with open(args.output, "w", encoding="utf-8") as fh:
        yaml.safe_dump(patch, fh, sort_keys=False, allow_unicode=True, width=100)
    n_orpha = sum(1 for v in patch.values()
                  if any(e["lane"] == "EXPERT_DATABASE"
                         for s in ASSESSMENTS for e in v[s]["evidence"]))
    print(f"skeleton: {len(patch)} diseases -> {args.output}")
    print(f"  with an EXPERT_DATABASE line: {n_orpha}")
    n_cal = sum(1 for v in patch.values()
                if any(e["reference"].startswith("SSACAL:")
                       for e in v["work_capacity"]["evidence"]))
    print(f"  with an SSA CAL line         : {n_cal}")


if __name__ == "__main__":
    main()
