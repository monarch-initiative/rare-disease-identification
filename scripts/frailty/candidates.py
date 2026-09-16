"""Surface candidate functional-outcome sentences from the triage dumps.

Filters hard, because the triage's loose fallback query pulls unrelated papers:
a sentence only surfaces if it mentions a functional outcome AND carries a
number. The curator still reads the abstract before quoting -- this only decides
what is worth reading.
"""
import argparse, pathlib, re, csv
from common import TMP

FUNC = re.compile(
    r"\b(employ|unemploy|work|occupation|school|educat|independent|independence|"
    r"assist|caregiv|carer|daily living|ADL|self-care|wheelchair|ambulat|walk|"
    r"tube feed|gastrostom|ventilat|institution|nursing home|residential|"
    r"supervis|disab|died|death|mortality|survival|life expectancy|lifespan|"
    r"seizure-free|nonverbal|non-verbal|speech|dependent|dependency)\w*", re.I)
NUM = re.compile(r"\b\d+(\.\d+)?\s*%|\b\d+\s*(of|/)\s*\d+\b|\bn\s*=\s*\d+|"
                 r"\b(all|none|most|median|mean)\b.{0,40}\b\d+", re.I)
SENT = re.compile(r"(?<=[.!?])\s+")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=str(TMP / "frailty_triage"))
    ap.add_argument("--worklist", default=str(TMP / "frailty_worklist.tsv"))
    ap.add_argument("--only", help="restrict to one MONDO id")
    args = ap.parse_args()

    order = {}
    with open(args.worklist, encoding="utf-8") as fh:
        for i, r in enumerate(csv.DictReader(fh, delimiter="\t")):
            order[r["mondo_id"]] = (i, r["label"])

    for path in sorted(pathlib.Path(args.dir).glob("*.md"),
                       key=lambda p: order.get(p.stem.replace("_", ":"), (999, ""))[0]):
        mid = p_id = path.stem.replace("_", ":")
        if args.only and args.only != mid:
            continue
        text = path.read_text(encoding="utf-8")
        blocks = re.split(r"\n## ", text)
        head = blocks[0].splitlines()[0].replace("# ", "")
        hits = []
        for b in blocks[1:]:
            pm = b.split()[0].rstrip("()")
            title = ""
            m = re.search(r"\*\*(.+?)\*\*", b, re.S)
            if m:
                title = re.sub(r"\s+", " ", m.group(1))
            body = b.split("**", 2)[-1]
            for s in SENT.split(body):
                s = s.strip()
                if 40 < len(s) < 400 and FUNC.search(s) and NUM.search(s):
                    hits.append((pm, title, s))
        if not hits:
            print(f"\n=== {head}\n  (no candidate sentence)")
            continue
        print(f"\n=== {head}")
        for pm, title, s in hits[:6]:
            print(f"  [{pm}] {title[:80]}")
            print(f"      {s}")


if __name__ == "__main__":
    main()
