"""Render Orphanet functional-consequence records into references_cache/ORPHA_<code>.md.

The EXPERT_DATABASE lane quotes these files verbatim, and the same quote checker
that guards PMIDs guards them. One file per disorder, one table row per
disability, so `source_statement` can be copied straight out.
"""
import argparse, xml.etree.ElementTree as ET
from common import FC_XML, CACHE

WORK_ITEMS = {
    "Engaging in paid work in a standard environment",
    "Performing professional tasks",
}


def records():
    for d in ET.parse(FC_XML).getroot().iter("DisorderDisabilityRelevance"):
        dis = d.find("Disorder")
        yield {
            "code": dis.findtext("OrphaCode"),
            "name": dis.findtext("Name"),
            "type": (dis.find("DisorderType").findtext("Name")
                     if dis.find("DisorderType") is not None else ""),
            "status": d.find("StatusDisability").findtext("Name"),
            "category": d.find("DisabilityCategory").findtext("Name"),
            "source": (d.findtext("SourceOfValidation") or "").strip(),
            "annotated": (d.findtext("AnnotationDate") or "")[:10],
            "rows": [
                (
                    a.find("Disability").findtext("Name"),
                    a.find("FrequenceDisability").findtext("Name"),
                    a.find("SeverityDisability").findtext("Name"),
                    a.find("TemporalityDisability").findtext("Name"),
                    a.findtext("LossOfAbility"),
                )
                for a in d.iter("DisabilityDisorderAssociation")
                if a.findtext("Type") == "Disability"
            ],
        }


def render(r):
    expert = "[Expert]" in r["source"]
    out = [
        f"# ORPHA:{r['code']} — {r['name']}",
        "",
        "Source: Orphanet functional consequences (`en_funct_consequences.xml`), CC BY 4.0.",
        "",
        f"- **Disorder type:** {r['type']}",
        f"- **Disability category:** {r['category']}",
        f"- **Validation status:** {r['status']}",
        f"- **Source of validation:** {r['source'] or '(none recorded)'}",
        f"- **Expert-validated:** {'yes' if expert and r['status'] == 'Validated' else 'no'}",
        f"- **Annotation date:** {r['annotated']}",
        "",
        "## Functional consequences",
        "",
    ]
    if not r["rows"]:
        out.append("_No disability rows recorded._")
    else:
        out.append("Each row is quotable verbatim as `source_statement`, pipe-separated:")
        out.append("")
        for name, freq, sev, temp, loss in sorted(r["rows"], key=lambda t: tuple(x or "" for x in t)):
            lane = " (work)" if name in WORK_ITEMS else ""
            out.append(f"- {name} | {freq} | {sev} | {temp}{lane}")
        out.append("")
        out.append("| Disability | Frequency | Severity | Temporality | Loss of ability |")
        out.append("|---|---|---|---|---|")
        for name, freq, sev, temp, loss in sorted(r["rows"], key=lambda t: tuple(x or "" for x in t)):
            out.append(f"| {name} | {freq} | {sev} | {temp} | {loss} |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="rewrite files that already exist")
    args = ap.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    written = skipped = 0
    for r in records():
        path = CACHE / f"ORPHA_{r['code']}.md"
        if path.exists() and not args.force:
            skipped += 1
            continue
        path.write_text(render(r), encoding="utf-8")
        written += 1
    print(f"ORPHA cache: {written} written, {skipped} already present -> {CACHE}")


if __name__ == "__main__":
    main()
