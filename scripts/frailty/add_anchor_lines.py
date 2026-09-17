"""Retrofit PHENOTYPE_ANCHOR lines onto existing UNKNOWN assessments.

Text-level surgery, for the same reason apply_curation.py works that way: a YAML
round-trip of the 3,079-disease list reformats every untouched entry and buries the
change. Here we replace exactly one evidence entry - the COMPUTED_SCORE line - inside
assessments whose impairment is UNKNOWN, and leave everything else byte-identical.

The score is not lost: it stays in the assessment's own `score` / `score_method`
fields. What changes is that the evidence list now names the findings instead of
citing a weighted sum of them.
"""
import pathlib, re, sys, yaml
from common import SOURCE, ASSESSMENTS
from anchors import term_scores, corpus, anchor_evidence

IND = "    "   # evidence entries sit at four spaces under the assessment


def render(entry):
    txt = yaml.safe_dump([entry], sort_keys=False, allow_unicode=True, width=96,
                         default_flow_style=False)
    return [IND + l if l.strip() else l for l in txt.splitlines()]


def main():
    dry = "--dry-run" in sys.argv
    scores, corp = term_scores(), corpus()
    lines = pathlib.Path(SOURCE).read_text(encoding="utf-8").splitlines()

    # locate every disease block and, inside it, each assessment's COMPUTED_SCORE entry
    starts = [i for i, l in enumerate(lines) if l.startswith("- mondo_id: ")]
    edits = []                      # (start, end, replacement_lines)
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        mid = lines[i][len("- mondo_id: "):].strip()
        for slot in ASSESSMENTS:
            try:
                s_at = next(j for j in range(i, end) if lines[j] == f"  {slot}:")
            except StopIteration:
                continue
            s_end = next((j for j in range(s_at + 1, end)
                          if lines[j].startswith("  ") and not lines[j].startswith("   ")), end)
            if not any(lines[j].strip() == "impairment: UNKNOWN" for j in range(s_at, s_end)):
                continue
            try:
                e_at = next(j for j in range(s_at, s_end)
                            if lines[j] == f"{IND}- lane: COMPUTED_SCORE")
            except StopIteration:
                continue
            e_end = next((j for j in range(e_at + 1, s_end)
                          if lines[j].startswith(f"{IND}- ") or not lines[j].startswith(IND)),
                         s_end)
            ev = anchor_evidence(mid, slot, scores, corp)
            if ev:
                edits.append((e_at, e_end, render(ev[0])))

    for start, end, repl in sorted(edits, reverse=True):
        lines[start:end] = repl

    print(f"{len(edits)} COMPUTED_SCORE lines replaced with PHENOTYPE_ANCHOR")
    if dry:
        return
    out = "\n".join(lines) + "\n"
    verify(pathlib.Path(SOURCE).read_text(encoding="utf-8"), out)
    pathlib.Path(SOURCE).write_text(out, encoding="utf-8")
    print(f"written to {SOURCE}")


def verify(before_text, after_text):
    """Only evidence lists inside UNKNOWN assessments may differ. Nothing else."""
    b = yaml.safe_load(before_text)
    a = yaml.safe_load(after_text)
    ob = {d["mondo_id"]: d for d in b["diseases"]}
    oa = {d["mondo_id"]: d for d in a["diseases"]}
    if set(ob) != set(oa):
        sys.exit("REFUSING TO WRITE: disease set changed")
    touched = 0
    for mid, d in ob.items():
        n = oa[mid]
        if set(d) != set(n):
            sys.exit(f"REFUSING TO WRITE: {mid} key set changed")
        for k, v in d.items():
            if k not in ASSESSMENTS:
                if n[k] != v:
                    sys.exit(f"REFUSING TO WRITE: {mid} altered {k!r}")
                continue
            if not isinstance(v, dict):
                continue
            for f, fv in v.items():
                if f == "evidence":
                    continue
                if n[k].get(f) != fv:
                    sys.exit(f"REFUSING TO WRITE: {mid}.{k} altered {f!r}")
            if n[k].get("evidence") != v.get("evidence"):
                if v.get("impairment") != "UNKNOWN":
                    sys.exit(f"REFUSING TO WRITE: {mid}.{k} evidence changed on a "
                             f"non-UNKNOWN assessment ({v.get('impairment')})")
                touched += 1
    print(f"integrity: {len(ob)} diseases, {touched} UNKNOWN evidence lists changed, "
          "nothing else touched")


if __name__ == "__main__":
    main()
