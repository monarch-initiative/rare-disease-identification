#!/usr/bin/env python3
"""Deterministic MONDO -> ICD-10-CM exact matcher.

Stage 1 of the mapping pipeline. The approach is lifted from MeDIC's lexical
grounder (`medic/src/medic/grounding/lexical/`): a normalized string index over
label + exact synonyms on both sides, then a tiered ladder where the first
single-id hit wins, with every transform recorded so the decision is reviewable.

Tier order per Mondo term, first unambiguous hit wins:

  1  raw exact                -> skos:exactMatch, confidence 1.00
  2  base-normalized          -> skos:exactMatch, confidence 0.95
  3  surgery variants         -> skos:exactMatch, confidence 0.90
  4  fuzzy edit-distance 1    -> candidate only, never auto-accepted

Only tiers 1-3 are emitted as mappings. Tier 4 and every near-miss are written to
the review queue for stage 2 (agentic adjudication), because the brief is exact
matches only and an edit-1 neighbour is not evidence of concept equivalence.

Ambiguity rule, also from MeDIC: if a tier produces more than one distinct
ICD-10-CM code, nothing is emitted and the term goes to review. Silently picking
one of several codes is how a crosswalk becomes untrustworthy.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import click
import yaml

try:
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

# --- normalization (ported from medic/grounding/lexical/preprocess.py) ---------------

_BRACKETS = re.compile(r"\[[^\]]*\]")
_WS = re.compile(r"\s+")
_DASHES = {"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-"}
_QUOTES = {"’": "'", "‘": "'", "“": '"', "”": '"'}


def base_normalize(s: str) -> str:
    """Non-semantic normalization: diacritics, case, punctuation, whitespace."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    for a, b in {**_DASHES, **_QUOTES}.items():
        s = s.replace(a, b)
    s = _BRACKETS.sub("", s)
    s = s.casefold()
    return _WS.sub(" ", s).strip()


_ARABIC_TO_ROMAN = {1: "i", 2: "ii", 3: "iii", 4: "iv", 5: "v", 6: "vi",
                    7: "vii", 8: "viii", 9: "ix", 10: "x", 11: "xi", 12: "xii"}
_ROMAN_TO_ARABIC = {v: k for k, v in _ARABIC_TO_ROMAN.items()}
_INDICATORS = "type|stage|grade|class|group|factor"
_BRIT_AM = {
    "tumour": "tumor", "oesophag": "esophag", "haemat": "hemat", "haemo": "hemo",
    "anaemia": "anemia", "leukaemia": "leukemia", "coeliac": "celiac",
    "oedema": "edema", "paediatric": "pediatric", "colour": "color",
    "diarrhoea": "diarrhea", "gynaecolog": "gynecolog", "fibre": "fiber",
    "ischaemi": "ischemi", "hypercalcaemi": "hypercalcemi", "glycaemi": "glycemi",
}
_CELL_TOKENS = ("t", "b", "nk")


def _r_disease_disorder(s):
    out = []
    if "disease" in s:
        out.append((s.replace("disease", "disorder"), "disease_to_disorder"))
    if "disorder" in s:
        out.append((s.replace("disorder", "disease"), "disorder_to_disease"))
    return out


def _r_syndrome_disease(s):
    """`X syndrome` <-> `X disease`. Not a MeDIC rule; see module docstring."""
    out = []
    if "syndrome" in s:
        out.append((s.replace("syndrome", "disease"), "syndrome_to_disease"))
    if "disease" in s:
        out.append((s.replace("disease", "syndrome"), "disease_to_syndrome"))
    return out


def _r_arabic_roman(s):
    out = []
    m = re.search(rf"\b({_INDICATORS})\s+(\d{{1,2}})\b", s)
    if m and int(m.group(2)) in _ARABIC_TO_ROMAN:
        roman = _ARABIC_TO_ROMAN[int(m.group(2))]
        out.append((s[:m.start(2)] + roman + s[m.end(2):], "arabic_to_roman"))
    m = re.search(rf"\b({_INDICATORS})\s+([ivx]{{1,4}})\b", s)
    if m and m.group(2) in _ROMAN_TO_ARABIC:
        arabic = str(_ROMAN_TO_ARABIC[m.group(2)])
        out.append((s[:m.start(2)] + arabic + s[m.end(2):], "roman_to_arabic"))
    return out


def _r_comma_drop_type(s):
    m = re.search(r",\s+(type\s+\w+)$", s)
    return [(s[:m.start()] + " " + m.group(1), "comma_drop_type")] if m else []


def _r_hyphen_type(s):
    new = re.sub(r"\btype-(\w+)", r"type \1", s)
    return [(new, "hyphen_type")] if new != s else []


def _r_brit_am(s):
    out = []
    for brit, am in _BRIT_AM.items():
        if brit in s:
            out.append((s.replace(brit, am), "brit_to_am"))
        elif am in s:
            out.append((s.replace(am, brit), "am_to_brit"))
    return out


def _r_cell_hyphen(s):
    out = []
    for tok in _CELL_TOKENS:
        if re.search(rf"\b{tok}-cell\b", s):
            out.append((re.sub(rf"\b{tok}-cell\b", f"{tok} cell", s), "cell_hyphen_to_space"))
        elif re.search(rf"\b{tok} cell\b", s):
            out.append((re.sub(rf"\b{tok} cell\b", f"{tok}-cell", s), "cell_space_to_hyphen"))
    return out


def _r_possessive(s):
    """`X's Y` <-> `X Y`. ICD-10-CM keeps eponym possessives that Mondo drops."""
    out = []
    if "'s " in s or s.endswith("'s"):
        out.append((re.sub(r"'s\b", "", s), "strip_possessive"))
    else:
        m = re.match(r"^(\w+)(\s+.+)$", s)
        if m:
            out.append((f"{m.group(1)}'s{m.group(2)}", "add_possessive"))
    return out


def _r_comma_invert(s):
    """`X, congenital` -> `congenital X`. ICD-10-CM inverts far more than Mondo does."""
    if s.count(",") != 1:
        return []
    head, tail = [p.strip() for p in s.split(",")]
    if not head or not tail or len(tail.split()) > 3:
        return []
    return [(f"{tail} {head}", "comma_inversion")]


def _r_deficiency_of(s):
    """`deficiency of X` <-> `X deficiency`."""
    m = re.match(r"^deficiency of (.+)$", s)
    if m:
        return [(f"{m.group(1)} deficiency", "deficiency_inversion")]
    m = re.match(r"^(.+) deficiency$", s)
    if m:
        return [(f"deficiency of {m.group(1)}", "deficiency_inversion")]
    return []


# --- broad-scope rules: candidate generation only, never emitted as exactMatch --------

_QUALIFIERS = (
    "severe", "moderate", "mild", "acute", "chronic", "advanced", "metastatic",
    "recurrent", "refractory", "relapsed", "relapsing", "newly diagnosed", "primary",
    "secondary", "malignant", "active", "persistent", "resistant", "unresectable",
    "locally advanced", "inoperable", "early", "late", "progressive", "generalized",
    "generalised", "localized", "localised", "familial", "hereditary", "congenital",
    "idiopathic", "classic", "classical", "juvenile", "infantile", "adult", "neonatal",
)
_QUAL_RE = re.compile(
    r"^((?:" + "|".join(_QUALIFIERS) + r")(?:[\s,/]+(?:to|and|or)?[\s,/]*)?)+", re.I)


def _r_qualifier_strip(s):
    """Strip a leading clinical-qualifier run. MeDIC scopes this broadMatch."""
    m = _QUAL_RE.match(s)
    if m and m.end() < len(s):
        rest = s[m.end():].strip()
        if rest and rest != s:
            return [(rest, "qualifier_strip")]
    return []


def _r_strip_other(s):
    """`other X` -> `X`. MeDIC scopes this broadMatch."""
    return [(s[len("other "):], "strip_leading_other")] if s.startswith("other ") else []


# Rule tables mirror medic/grounding/lexical/preprocess.py. Rules whose predicate is
# not skos:exactMatch are never emitted here: they only widen the candidate pool that
# stage 2 adjudicates, because the brief is exact matches only.
RULE_PREDICATE = {
    "base_normalization": "skos:exactMatch",
    "comma_drop_type": "skos:exactMatch", "hyphen_type": "skos:exactMatch",
    "cell_hyphen_to_space": "skos:exactMatch", "cell_space_to_hyphen": "skos:exactMatch",
    "disease_to_disorder": "skos:exactMatch", "disorder_to_disease": "skos:exactMatch",
    "arabic_to_roman": "skos:exactMatch", "roman_to_arabic": "skos:exactMatch",
    "brit_to_am": "skos:exactMatch", "am_to_brit": "skos:exactMatch",
    # additions beyond MeDIC's set, for the Mondo<->ICD-10-CM label conventions
    "strip_possessive": "skos:exactMatch", "add_possessive": "skos:exactMatch",
    "comma_inversion": "skos:exactMatch", "deficiency_inversion": "skos:exactMatch",
    "syndrome_to_disease": "skos:exactMatch", "disease_to_syndrome": "skos:exactMatch",
    # broad-scope: candidate generation only
    "strip_leading_other": "skos:broadMatch", "qualifier_strip": "skos:broadMatch",
    "fuzzy_edit1_unique": "skos:closeMatch",
}
RULE_CERTAINTY = {
    "base_normalization": 1.0,
    "comma_drop_type": 0.98, "hyphen_type": 0.98,
    "cell_hyphen_to_space": 0.97, "cell_space_to_hyphen": 0.97,
    "disease_to_disorder": 0.95, "disorder_to_disease": 0.95,
    "arabic_to_roman": 0.95, "roman_to_arabic": 0.95,
    "brit_to_am": 0.97, "am_to_brit": 0.97,
    "strip_possessive": 0.97, "add_possessive": 0.97,
    "comma_inversion": 0.95, "deficiency_inversion": 0.96,
    "syndrome_to_disease": 0.88, "disease_to_syndrome": 0.88,
    "strip_leading_other": 0.70, "qualifier_strip": 0.75,
    "fuzzy_edit1_unique": 0.60,
}

_EXACT_RULES = (_r_possessive, _r_disease_disorder, _r_syndrome_disease, _r_arabic_roman,
                _r_comma_drop_type, _r_hyphen_type, _r_brit_am, _r_cell_hyphen,
                _r_comma_invert, _r_deficiency_of)
_BROAD_RULES = (_r_qualifier_strip, _r_strip_other)


def _apply(rules, normalized):
    seen, out = set(), []
    for rule in rules:
        for produced, rule_id in rule(normalized):
            produced = _WS.sub(" ", produced).strip()
            if produced and produced != normalized and produced not in seen:
                seen.add(produced)
                out.append((produced, rule_id))
    return out


def generate_variants(normalized: str) -> list[tuple[str, str]]:
    """Exact-preserving surgery. Single-pass, deterministic, bounded."""
    return _apply(_EXACT_RULES, normalized)


def generate_broad_variants(normalized: str) -> list[tuple[str, str]]:
    """Non-exact surgery, used only to widen the stage-2 candidate pool."""
    return _apply(_BROAD_RULES, normalized)


_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789 -',./"


def edits1(word: str) -> set[str]:
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [a + b[1:] for a, b in splits if b]
    transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
    replaces = [a + c + b[1:] for a, b in splits if b for c in _ALPHABET]
    inserts = [a + c + b for a, b in splits for c in _ALPHABET]
    return set(deletes + transposes + replaces + inserts) - {word}


# --- ICD-10-CM index (loader ported from medic/.../loaders/icd10cm.py) ---------------

_IRI = "http://purl.bioontology.org/ontology/ICD10CM/"
_SUBJECT = re.compile(rf"^<{re.escape(_IRI)}([^>]+)>")
_QUOTED = re.compile(r'"""(.*?)"""|"((?:[^"\\]|\\.)*)"')


def _values(line: str) -> list[str]:
    out = []
    for triple, single in _QUOTED.findall(line):
        val = triple if triple else single
        if val:
            out.append(val.replace('\\"', '"'))
    return out


def load_icd10cm(ttl_path: Path):
    """Yield (code, pref_label, string_value, match_field) from the UMLS2RDF Turtle."""
    labels: dict[str, str] = {}
    alts: dict[str, list[str]] = defaultdict(list)
    current = None
    with open(ttl_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = _SUBJECT.match(line)
            if m:
                current = m.group(1)
                continue
            if current is None:
                continue
            if "skos:prefLabel" in line:
                vals = _values(line)
                if vals:
                    labels[current] = vals[0]
            elif "skos:altLabel" in line:
                alts[current].extend(_values(line))
    for code, label in labels.items():
        yield code, label, label, "label"
        for alt in alts.get(code, []):
            yield code, label, alt, "exactSynonym"


# --- Mondo side ----------------------------------------------------------------------

def load_mondo_strings(obo: Path, wanted: set[str]):
    """Return {mondo_id: {"label": str, "exact": [str], "obsolete": bool}}."""
    out: dict[str, dict] = {}
    cur = None
    rec: dict = {}

    def flush():
        if cur and cur in wanted:
            out[cur] = {"label": rec.get("label", ""),
                        "exact": sorted(set(rec.get("exact", []))),
                        "obsolete": rec.get("obsolete", False)}

    with open(obo) as f:
        for line in f:
            line = line.rstrip("\n")
            if line == "[Term]":
                flush()
                cur, rec = None, {"exact": []}
            elif line.startswith("id: MONDO:"):
                cur = line[4:].strip()
            elif line.startswith("name: "):
                rec["label"] = line[6:]
            elif line.startswith("is_obsolete: true"):
                rec["obsolete"] = True
            elif line.startswith("synonym: "):
                m = re.match(r'synonym: "((?:[^"\\]|\\.)*)" (EXACT)\b', line)
                if m:
                    rec.setdefault("exact", []).append(m.group(1).replace('\\"', '"'))
    flush()
    return out


# --- index ---------------------------------------------------------------------------

# ICD-10-CM files a specific disease as an *inclusion term* under a residual rubric
# ("Hereditary coproporphyria" sits under E80.29 "Other porphyria"). That is a lexically
# exact hit on a semantically broader class: the rubric is where the disease gets coded,
# not a class denoting it. Such hits are routed to stage-2 review instead of emitted.
_RESIDUAL_RE = re.compile(r"\b(other|unspecified|not elsewhere classified|nec|nos)\b", re.I)


def is_residual(icd_label: str) -> bool:
    return bool(_RESIDUAL_RE.search(icd_label or ""))


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {"the", "of", "and", "or", "with", "without", "in", "to", "a", "an",
         "unspecified", "other", "nos", "nec", "disease", "disorder", "syndrome"}


def _tokens(s: str) -> frozenset[str]:
    """Content tokens for retrieval scoring. Stopwords carry no discriminative power."""
    return frozenset(t for t in _TOKEN_RE.findall(s) if t not in _STOP and len(t) > 1)


class Index:
    """In-memory normalized string index over ICD-10-CM, backed by sqlite for edit-1."""

    def __init__(self):
        self.by_raw: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.by_norm: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.label: dict[str, str] = {}
        self.norm_strings: dict[str, set[str]] = defaultdict(set)

    def add(self, code, pref_label, value, field):
        self.label[code] = pref_label
        self.by_raw[(" ".join(value.split()), field)].add(code)
        n = base_normalize(value)
        if n:
            self.by_norm[(n, field)].add(code)
            self.norm_strings[n].add(code)

    def lookup_raw(self, value, field):
        return self.by_raw.get((" ".join(value.split()), field), set())

    def lookup_norm(self, value, field):
        return self.by_norm.get((value, field), set())

    def lookup_any_norm(self, value):
        return self.norm_strings.get(value, set())

    # --- candidate retrieval -----------------------------------------------------
    def build_retriever(self):
        """Token -> codes inverted index with IDF weights, for stage-2 candidates."""
        import math
        self.postings: dict[str, set[str]] = defaultdict(set)
        self.code_tokens: dict[str, set[str]] = defaultdict(set)
        for (norm, _field), codes in self.by_norm.items():
            toks = _tokens(norm)
            for t in toks:
                self.postings[t] |= codes
                for c in codes:
                    self.code_tokens[c] |= toks
        n = max(len(self.label), 1)
        self.idf = {t: math.log(n / (1 + len(cs))) for t, cs in self.postings.items()}

    def retrieve(self, query: str, top_k: int = 8) -> list[tuple[str, float]]:
        """Rank codes by IDF-weighted token overlap against the query string."""
        qt = _tokens(query)
        if not qt:
            return []
        scores: dict[str, float] = defaultdict(float)
        for t in qt:
            w = self.idf.get(t)
            if w is None or w <= 0:
                continue
            posting = self.postings.get(t, ())
            if len(posting) > 4000:      # ignore near-stopword tokens
                continue
            for c in posting:
                scores[c] += w
        if not scores:
            return []
        qmass = sum(self.idf.get(t, 0.0) for t in qt) or 1.0
        ranked = sorted(
            ((c, sc / qmass) for c, sc in scores.items()),
            key=lambda kv: (-kv[1], kv[0]),
        )
        return [(c, round(sc, 4)) for c, sc in ranked[:top_k] if sc >= 0.25]


FIELDS = ("label", "exactSynonym")
FIELD_MATCH = {"label": "rdfs:label", "exactSynonym": "oio:hasExactSynonym"}


def main_match(index: Index, label: str, synonyms: list[str]):
    """Run the ladder. Returns (decision|None, review_payload|None)."""
    queries = [("label", label)] + [("synonym", s) for s in synonyms]

    # Tier 1: raw exact. Mondo label first, then exact synonyms.
    for qkind, q in queries:
        if not q:
            continue
        for field in FIELDS:
            hits = index.lookup_raw(q, field)
            if len(hits) == 1:
                code = next(iter(hits))
                if is_residual(index.label.get(code, "")):
                    return (None, {"reason": "residual_rubric", "ambiguous": [code],
                                   "match_string": " ".join(q.split())})
                return ({"code": code, "tier": "raw_exact", "field": field,
                         "match_string": " ".join(q.split()), "query_kind": qkind,
                         "preprocessing": [],
                         "confidence": 1.0 if qkind == "label" else 0.98}, None)
            if len(hits) > 1:
                return (None, {"reason": "ambiguous_raw", "ambiguous": sorted(hits),
                               "match_string": " ".join(q.split())})

    # Tier 2: base-normalized.
    for qkind, q in queries:
        if not q:
            continue
        n = base_normalize(q)
        for field in FIELDS:
            hits = index.lookup_norm(n, field)
            if len(hits) == 1:
                code = next(iter(hits))
                if is_residual(index.label.get(code, "")):
                    return (None, {"reason": "residual_rubric", "ambiguous": [code],
                                   "match_string": n})
                return ({"code": code, "tier": "normalized", "field": field,
                         "match_string": n, "query_kind": qkind,
                         "preprocessing": ["base_normalization"],
                         "confidence": RULE_CERTAINTY["base_normalization"] * (
                             1.0 if qkind == "label" else 0.98)}, None)
            if len(hits) > 1:
                return (None, {"reason": "ambiguous_normalized", "ambiguous": sorted(hits),
                               "match_string": n})

    # Tier 3: exact-preserving surgery. Confidence comes from the rule table.
    for qkind, q in queries:
        if not q:
            continue
        n = base_normalize(q)
        for variant, rule_id in generate_variants(n):
            for field in FIELDS:
                hits = index.lookup_norm(variant, field)
                if len(hits) == 1:
                    code = next(iter(hits))
                    if is_residual(index.label.get(code, "")):
                        return (None, {"reason": "residual_rubric", "ambiguous": [code],
                                       "match_string": variant})
                    conf = RULE_CERTAINTY[rule_id] * (1.0 if qkind == "label" else 0.98)
                    return ({"code": code, "tier": "surgery", "field": field,
                             "match_string": variant, "query_kind": qkind,
                             "preprocessing": ["base_normalization", rule_id],
                             "confidence": round(conf, 4)}, None)
    return (None, {"reason": "no_exact_hit"})


def build_review(index: Index, label: str, synonyms: list[str], payload: dict) -> dict:
    """Assemble the stage-2 candidate pool for one unmatched term.

    Three sources, strongest first: any ambiguity the ladder hit, broad-rule variants
    (qualifier/other stripping — deliberately not exact), edit-1 neighbours, and
    IDF-weighted token retrieval. All are *candidates*; stage 2 decides equivalence.
    """
    cands: dict[str, dict] = {}

    def offer(code, how, score=None):
        if code not in cands:
            cands[code] = {"code": code, "icd_label": index.label.get(code, ""),
                           "found_by": how, "score": score}

    for code in payload.get("ambiguous", []):
        offer(code, "lexical_ambiguous", 1.0)

    n = base_normalize(label)
    for variant, rule_id in generate_broad_variants(n):
        for field in FIELDS:
            for code in index.lookup_norm(variant, field):
                offer(code, rule_id, RULE_CERTAINTY.get(rule_id))

    if 6 <= len(n) <= 60:
        fuzzy = set()
        for cand in sorted(edits1(n)):
            fuzzy |= index.lookup_any_norm(cand)
        for code in sorted(fuzzy):
            offer(code, "fuzzy_edit1", RULE_CERTAINTY["fuzzy_edit1_unique"])

    # Retrieve deep, then let the per-category cap below do the selecting. Truncating
    # per-query hides good candidates behind laterality subcode runs: the M08
    # "Juvenile arthritis" rubric loses its own top-8 slot to M08.0* siblings.
    for q in [label] + synonyms[:8]:
        for code, score in index.retrieve(base_normalize(q), top_k=40):
            offer(code, "token_retrieval", score)

    # ICD-10-CM explodes single concepts into laterality/encounter subcodes
    # (M08.011, M08.012, ...). Two failure modes to avoid: those subcodes crowding
    # out everything else, and a hyper-specific sibling outranking the general rubric
    # that is usually the real equivalent of a Mondo term. So group by 3-character
    # category, keep each category's best-scoring code plus its most general ones,
    # and order the categories by their best score.
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for c in cands.values():
        by_cat[c["code"].split(".")[0]].append(c)

    picked: list[dict] = []
    for cat, members in by_cat.items():
        best = max(members, key=lambda c: ((c["score"] or 0), -len(c["code"])))
        chosen = [best]
        for c in sorted(members, key=lambda c: (len(c["code"]), c["code"])):
            if len(chosen) >= 3:
                break
            if c["code"] != best["code"]:
                chosen.append(c)
        picked.append((max(m["score"] or 0 for m in members), cat, chosen))

    ranked: list[dict] = []
    for _score, _cat, chosen in sorted(picked, key=lambda t: (-t[0], t[1])):
        for c in sorted(chosen, key=lambda c: (len(c["code"]), c["code"])):
            ranked.append(c)
            if len(ranked) >= 12:
                break
        if len(ranked) >= 12:
            break

    return {"label": label, "synonyms": synonyms[:12],
            "reason": payload.get("reason", "no_exact_hit"),
            "candidates": ranked}


@click.command()
@click.option("--diseases", type=click.Path(exists=True, path_type=Path),
              default=Path("src/prioritised-rare-disease-list.yml"))
@click.option("--mondo-obo", type=click.Path(exists=True, path_type=Path),
              default=Path("tmp/mondo.obo"))
@click.option("--icd-ttl", type=click.Path(exists=True, path_type=Path),
              default=Path(Path.home() / "ws/projects/medic/background/ontsrc/icd10cm.owl"))
@click.option("--out-dir", type=click.Path(path_type=Path), default=Path("tmp/icd10cm"))
def main(diseases, mondo_obo, icd_ttl, out_dir):
    """Stage 1: deterministic lexical matching + review-queue construction."""
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(diseases) as f:
        data = yaml.load(f, Loader=_Loader)
    entries = [d for d in data.get("diseases", []) if d.get("mondo_id")]
    wanted = {d["mondo_id"] for d in entries}
    list_label = {d["mondo_id"]: d.get("mondo_label", "") for d in entries}
    click.echo(f"Loaded {len(entries)} diseases")

    click.echo(f"Indexing ICD-10-CM from {icd_ttl}")
    index = Index()
    n_rows = 0
    for code, pref, value, field in load_icd10cm(icd_ttl):
        index.add(code, pref, value, field)
        n_rows += 1
    click.echo(f"  {n_rows} index rows over {len(index.label)} codes")
    index.build_retriever()

    click.echo(f"Loading Mondo strings from {mondo_obo}")
    mondo = load_mondo_strings(mondo_obo, wanted)
    click.echo(f"  {len(mondo)} of {len(wanted)} terms found in mondo.obo")

    matched, review = {}, {}
    for d in entries:
        mid = d["mondo_id"]
        m = mondo.get(mid, {})
        label = m.get("label") or list_label.get(mid, "")
        syns = m.get("exact", [])
        # ST-006 / ST-004: an obsolete subject must not carry an exact match. Its label
        # still reads normally ("obsolete X"), and its stale synonyms still match, so
        # without this guard obsoleted terms silently acquire mappings.
        if m.get("obsolete"):
            review[mid] = {"label": label, "synonyms": syns[:12],
                           "reason": "obsolete_subject", "candidates": []}
            continue
        decision, rev = main_match(index, label, syns)
        if decision:
            decision["label"] = label
            decision["object_label"] = index.label.get(decision["code"], "")
            decision["predicate"] = "skos:exactMatch"
            matched[mid] = decision
        else:
            review[mid] = build_review(index, label, syns, rev or {})

    (out_dir / "lexical_matches.json").write_text(json.dumps(matched, indent=1, sort_keys=True))
    (out_dir / "review_queue.json").write_text(json.dumps(review, indent=1, sort_keys=True))

    tiers = defaultdict(int)
    for v in matched.values():
        tiers[v["tier"]] += 1
    reasons = defaultdict(int)
    for v in review.values():
        reasons[v["reason"]] += 1
    with_c = sum(1 for v in review.values() if v["candidates"])

    click.echo(f"\nDeterministic exact matches: {len(matched)}")
    for k, v in sorted(tiers.items()):
        click.echo(f"    {k:12s} {v}")
    click.echo(f"To review: {len(review)}  ({with_c} with candidates, "
               f"{len(review) - with_c} with none -> NoTermFound)")
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        click.echo(f"    {k:22s} {v}")


if __name__ == "__main__":
    main()
