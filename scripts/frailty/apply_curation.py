"""Splice curated work_capacity / care_dependence blocks into the source list.

Text-level insertion on purpose: a YAML round-trip of the 426k-line curated list
would reformat every untouched entry and bury the curation in the diff. Each
disease block is located by its `- mondo_id:` line and the new keys are appended
at the end of that block.

The patch file is a mapping of MONDO id -> {work_capacity: {...}, care_dependence: {...}}.
"""
import argparse, io, pathlib, sys, yaml
from common import SOURCE, ASSESSMENTS

ENTRY = "- mondo_id: "
IND = "  "


def block_bounds(lines):
    """-> {mondo_id: (start_idx, end_idx_exclusive)}"""
    starts = [i for i, l in enumerate(lines) if l.startswith(ENTRY)]
    out = {}
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        out[lines[i][len(ENTRY):].strip()] = (i, end)
    return out


def render(slot, data):
    txt = yaml.safe_dump({slot: data}, sort_keys=False, allow_unicode=True,
                         width=100, default_flow_style=False)
    return [IND + l if l.strip() else l for l in txt.splitlines()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("patch")
    ap.add_argument("--source", default=str(SOURCE))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    patch = yaml.safe_load(pathlib.Path(args.patch).read_text(encoding="utf-8"))
    src = pathlib.Path(args.source)
    lines = src.read_text(encoding="utf-8").splitlines()
    bounds = block_bounds(lines)

    missing = [m for m in patch if m not in bounds]
    if missing:
        sys.exit(f"not in source list: {missing}")

    # apply bottom-up so earlier indices stay valid
    applied = 0
    for mid in sorted(patch, key=lambda m: bounds[m][0], reverse=True):
        start, end = bounds[mid]
        body = lines[start:end]
        # trim trailing blank lines inside the block, remember them
        tail = []
        while body and not body[-1].strip():
            tail.insert(0, body.pop())
        for slot in ASSESSMENTS:
            if slot not in patch[mid]:
                continue
            if any(l.startswith(IND + slot + ":") for l in body):
                print(f"  skip {mid} {slot}: already present")
                continue
            body += render(slot, patch[mid][slot])
            applied += 1
        lines[start:end] = body + tail

    out = "\n".join(lines) + "\n"
    if args.dry_run:
        print(f"[dry run] would write {applied} assessment blocks")
        return
    src.write_text(out, encoding="utf-8")
    print(f"applied {applied} assessment blocks to {src}")


if __name__ == "__main__":
    main()
