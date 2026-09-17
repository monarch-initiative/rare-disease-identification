"""PHENOTYPE_ANCHOR evidence: the HPO findings behind the score, cited individually.

An anchor is a clinician-scored, functionally decisive HPO term (score >=2 of 3 on
the axis in data/term_scores.tsv) that HPOA records at a curated frequency >=30% -
the same bar the impairment levels use.

This lane exists because collapsing HPOA into a scalar threw away its structure.
`Inability to walk | Very frequent` is the same kind of object as Orphanet's
`Moving around within the home | Very frequent | Severe`; one was being treated as
expert evidence and the other as a weak number.

It can never set a level. Benchmarked on the 538-disease Orphanet validation set the
scoring never saw, the tightest usable rule reaches PPV 59% (work) / 65% (care)
against base rates of 25% / 16% - a real signal, and wrong one time in three.
"""
import csv
from common import FC

TERM_SCORES = FC / "data/term_scores.tsv"
CORPUS = FC / "build/corpus.tsv"
MIN_FREQ = 0.30          # the >=30% bar from ImpairmentLevelEnum
MIN_TERM_SCORE = 2       # "implies inability" / "implies need for care", not merely associated
AXIS = {"work_capacity": "work", "care_dependence": "care"}


def term_scores():
    out = {}
    with open(TERM_SCORES, encoding="utf-8") as fh:
        for r in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"):
            hp = list(r.values())[0]
            if str(hp).startswith("HP:"):
                out[hp] = {"work": int(r["work"]), "care": int(r["care"]), "label": r["label"]}
    return out


def corpus():
    """MONDO id -> {HP id: curated frequency}."""
    out = {}
    with open(CORPUS, encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            phen = {}
            for item in (r["phenotypes"] or "").split("|"):
                hp, _, freq = item.rpartition(":")
                if not hp.startswith("HP:"):
                    continue
                try:
                    phen[hp] = float(freq)
                except ValueError:
                    continue
            out[r["mondo_id"]] = phen
    return out


def anchors_for(mid, slot, scores, corp):
    """Anchor findings for one disease and axis, most frequent first."""
    axis = AXIS[slot]
    out = []
    for hp, freq in (corp.get(mid) or {}).items():
        s = scores.get(hp)
        if s and freq >= MIN_FREQ and s[axis] >= MIN_TERM_SCORE:
            out.append((freq, hp, s["label"], s[axis]))
    return sorted(out, reverse=True)


def anchor_evidence(mid, slot, scores, corp, top=6):
    """One PHENOTYPE_ANCHOR line, or [] when the disease has no anchor findings."""
    found = anchors_for(mid, slot, scores, corp)
    if not found:
        return []
    shown = found[:top]
    listed = "; ".join(f"{lab} ({hp}) {freq:.0%}" for freq, hp, lab, _ in shown)
    more = f" and {len(found) - len(shown)} more" if len(found) > len(shown) else ""
    axis_phrase = ("inability to sustain work" if slot == "work_capacity"
                   else "need for daily personal care")
    return [{
        "lane": "PHENOTYPE_ANCHOR",
        "direction": "SUPPORTS",
        "strength": "MODERATE",
        "reference": f"HPOA:{mid.replace('MONDO:', '')}",
        "reference_title": "Human Phenotype Ontology annotations (phenotype.hpoa)",
        "source_statement": listed + more,
        "explanation": (
            f"{len(found)} curated findings that imply {axis_phrase}, each recorded in at least "
            "30% of affected people. Suggestive, but benchmarked at only 59-65% positive "
            "predictive value against Orphanet, so it cannot set a level on its own - and it is "
            "the same HPOA data the phenotype score is computed from, so it is never an "
            "independent second source."),
        "curator_type": "PIPELINE",
    }]
