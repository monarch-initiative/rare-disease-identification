"""Crosswalk the SSA Compassionate Allowances list to Mondo, for the FEDERAL_POLICY_LIST lane.

Source: POMS DI 23022.080, "List of Compassionate Allowances (CAL) Conditions".
CAL is a fast-track determination list: SSA presumes a listed condition meets the
disability standard, i.e. precludes substantial gainful activity. That is a claim
about WORK CAPACITY. It says nothing directly about personal-care dependence, so
the crosswalk is only ever used on the work_capacity axis.

CAL names are clinical labels, not codes, so the match is lexical and deliberately
conservative: exact normalised equality against the Mondo label or a Mondo synonym,
after stripping SSA's qualifier clauses. Anything less certain is left unmatched and
listed, rather than guessed.
"""
import argparse, html, json, pathlib, re, urllib.request, yaml
from common import SOURCE, TMP, CACHE, load_source

URL = "https://secure.ssa.gov/apps10/poms.nsf/lnx/0423022080"
RAW = TMP / "ssa/poms_0423022080.html"
CONDS = TMP / "ssa/cal_conditions.json"
XWALK = TMP / "ssa/cal_mondo_crosswalk.tsv"

# SSA appends staging/onset qualifiers after an en- or em-dash; the disease is the head.
QUALIFIER = re.compile(r"\s*[–—-]\s.*$")
PARENS = re.compile(r"\s*\([^)]*\)")
NOISE = re.compile(r"[^a-z0-9 ]+")


def norm(s):
    s = html.unescape(s).lower().replace("’", "'")
    s = PARENS.sub(" ", s)
    s = NOISE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def variants(name):
    """Normalised forms of a CAL condition name worth matching on."""
    base = QUALIFIER.sub("", name)
    out = {norm(name), norm(base)}
    # "Alpers Disease" <-> "Alpers syndrome" style: also try without a trailing noun
    for v in list(out):
        out.add(re.sub(r"\b(disease|syndrome|disorder)$", "", v).strip())
    return {v for v in out if len(v) > 3}


def download(force=False):
    RAW.parent.mkdir(parents=True, exist_ok=True)
    if RAW.exists() and not force:
        return RAW.read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read().decode("utf-8", "replace")
    RAW.write_text(t, encoding="utf-8")
    return t


def parse(t):
    out = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S | re.I):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)
        if len(cells) < 2:
            continue
        clean = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
        name, sec = clean(cells[0]), clean(cells[1])
        if re.match(r"^DI \d{5}\.\d+$", sec) and name and name.lower() != "section title":
            out.append({"condition": name, "poms": sec})
    return out


def write_cache(conds):
    """One quotable markdown file per CAL condition, so the lane is checkable."""
    CACHE.mkdir(parents=True, exist_ok=True)
    for c in conds:
        code = c["poms"].replace("DI ", "").replace(".", "")
        p = CACHE / f"SSACAL_{code}.md"
        p.write_text(
            f"# SSA Compassionate Allowances — {c['condition']}\n\n"
            f"Source: POMS {c['poms']}, listed in DI 23022.080 "
            f"\"List of Compassionate Allowances (CAL) Conditions\".\n"
            f"Retrieved from {URL}\n\n"
            "## Listing\n\n"
            f"{c['condition']} | {c['poms']} | Compassionate Allowance condition\n\n"
            "A Compassionate Allowance condition is fast-tracked by SSA because it so "
            "clearly meets the statutory disability standard - an inability to engage in "
            "substantial gainful activity. The listing is a determination about capacity "
            "for work, not about need for personal care.\n",
            encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force-download", action="store_true")
    args = ap.parse_args()

    conds = parse(download(args.force_download))
    CONDS.write_text(json.dumps(conds, indent=1), encoding="utf-8")
    write_cache(conds)

    # index Mondo labels + synonyms
    idx = {}
    for d in load_source()["diseases"]:
        for s in [d.get("mondo_label", "")] + list(d.get("mondo_synonyms") or []):
            n = norm(str(s))
            if n:
                idx.setdefault(n, []).append(d["mondo_id"])

    rows, unmatched = [], []
    for c in conds:
        hit = None
        for v in sorted(variants(c["condition"]), key=len, reverse=True):
            if v in idx and len(set(idx[v])) == 1:
                hit = idx[v][0]
                break
        if hit:
            rows.append((hit, c["condition"], c["poms"]))
        else:
            unmatched.append(c["condition"])

    XWALK.write_text("mondo_id\tcal_condition\tpoms_section\n" +
                     "\n".join("\t".join(r) for r in sorted(set(rows))) + "\n",
                     encoding="utf-8")
    print(f"CAL conditions parsed : {len(conds)}")
    print(f"matched to the list   : {len(set(r[0] for r in rows))} diseases")
    print(f"unmatched CAL names   : {len(unmatched)}")
    print(f"crosswalk -> {XWALK}")


if __name__ == "__main__":
    main()
