"""Remove derived evidence lines from the curated source, once.

`build_functional_capacity.py` regenerates EXPERT_DATABASE, FEDERAL_POLICY_LIST,
STATE_POLICY_LIST, PHENOTYPE_ANCHOR and COMPUTED_SCORE from their source files,
and `merge.py` re-attaches them to the published list. Keeping copies in the
curated file serves nothing and invites edits to evidence nobody curated.

Text-level surgery, like the other writers here, so untouched entries stay
byte-identical and the diff shows only what moved.
"""
import pathlib, sys, yaml
from common import SOURCE, ASSESSMENTS

DERIVED = {"EXPERT_DATABASE", "FEDERAL_POLICY_LIST", "STATE_POLICY_LIST",
           "PHENOTYPE_ANCHOR", "COMPUTED_SCORE"}
IND = "    "


def main():
    dry = "--dry-run" in sys.argv
    before = pathlib.Path(SOURCE).read_text(encoding="utf-8")
    lines = before.splitlines()

    drop = []                       # (start, end) spans to delete
    i = 0
    while i < len(lines):
        if lines[i].startswith(f"{IND}- lane: "):
            lane = lines[i][len(f"{IND}- lane: "):].strip()
            j = i + 1
            while j < len(lines) and lines[j].startswith(IND) and not lines[j].startswith(f"{IND}- "):
                j += 1
            if lane in DERIVED:
                drop.append((i, j))
            i = j
        else:
            i += 1

    for start, end in reversed(drop):
        del lines[start:end]

    print(f"{len(drop)} derived evidence lines removed from the curated source")
    if dry:
        return
    after = "\n".join(lines) + "\n"
    verify(before, after)
    pathlib.Path(SOURCE).write_text(after, encoding="utf-8")
    print(f"written to {SOURCE}")


def verify(before_text, after_text):
    """Only derived evidence lines may vanish. Everything else stays identical."""
    b = yaml.safe_load(before_text)
    a = yaml.safe_load(after_text)
    ob = {d["mondo_id"]: d for d in b["diseases"]}
    oa = {d["mondo_id"]: d for d in a["diseases"]}
    if set(ob) != set(oa):
        sys.exit("REFUSING TO WRITE: disease set changed")
    removed = 0
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
            kept_before = [e for e in (v.get("evidence") or []) if e["lane"] not in DERIVED]
            after_ev = n[k].get("evidence") or []
            if after_ev != kept_before:
                sys.exit(f"REFUSING TO WRITE: {mid}.{k} curated evidence changed")
            if not after_ev:
                sys.exit(f"REFUSING TO WRITE: {mid}.{k} would have no evidence left")
            removed += len(v.get("evidence") or []) - len(after_ev)
    print(f"integrity: {len(ob)} diseases, {removed} derived lines removed, "
          "every curated line and field unchanged")


if __name__ == "__main__":
    main()
