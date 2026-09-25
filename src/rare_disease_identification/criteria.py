"""Evaluate the six prioritisation criteria against the registry.

One place decides which registry field counts as evidence for which criterion:
`config/prioritisation_criteria.yaml`. This module reads that file, applies it
to a disease list, and hands the result to whoever asked -- the upset-plot
pipeline, the review document, and the website all consume the same evaluation.

Nothing here knows what the criteria *are*. Adding a seventh, retiring one, or
moving a signal from one criterion to another is a config edit.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

import yaml

# ---------------------------------------------------------------- field access


def _get_path(record: dict, path: str) -> Any:
    """Resolve a dotted field path, returning None if any hop is missing."""
    cur: Any = record
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
        if cur is None:
            return None
    return cur


def _as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _term_strings(value: Any) -> list[str]:
    """Flatten a SimpleTerm list (or plain strings) to the labels and ids it carries."""
    out: list[str] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            out.extend(str(v) for v in (item.get("label"), item.get("id")) if v)
        else:
            out.append(str(item))
    return out


# ---------------------------------------------------------------- rule ops
#
# Each op takes (record, rule) and returns a bool. Keep them total: a missing
# field is False, never an exception, because the registry is sparse by design
# and a KeyError here would mean "criterion evaluation dies on disease 1,400".

def _op_present(record: dict, rule: dict) -> bool:
    value = _get_path(record, rule["field"])
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return True


def _op_in(record: dict, rule: dict) -> bool:
    return _get_path(record, rule["field"]) in set(rule["values"])


def _op_contains_any(record: dict, rule: dict) -> bool:
    values = set(rule["values"])
    return any(v in values for v in _as_list(_get_path(record, rule["field"])))


def _op_matches_any(record: dict, rule: dict) -> bool:
    pattern = re.compile(rule["pattern"])
    return any(pattern.search(str(v)) for v in _as_list(_get_path(record, rule["field"])))


def _op_term_label_any(record: dict, rule: dict) -> bool:
    values = set(rule["values"])
    return any(s in values for s in _term_strings(_get_path(record, rule["field"])))


def _op_count_at_least(record: dict, rule: dict) -> bool:
    return len(_as_list(_get_path(record, rule["field"]))) >= int(rule["n"])


def _op_number_at_least(record: dict, rule: dict) -> bool:
    value = _get_path(record, rule["field"])
    try:
        return value is not None and float(value) >= float(rule["value"])
    except (TypeError, ValueError):
        return False


def _op_value_set_tier_non_empty(record: dict, rule: dict) -> bool:
    terminology = rule["terminology"]
    tier = rule["tier"]
    for vs in _as_list(record.get("value_sets")):
        if isinstance(vs, dict) and vs.get("terminology") == terminology and vs.get(tier):
            return True
    return False


#: Signal tiers that represent something the registry actually recorded, as
#: opposed to an inference drawn across a gap.
NON_PROXY_TIERS = ("direct", "derived")

OPS: dict[str, Callable[[dict, dict], bool]] = {
    "present": _op_present,
    "in": _op_in,
    "contains_any": _op_contains_any,
    "matches_any": _op_matches_any,
    "term_label_any": _op_term_label_any,
    "count_at_least": _op_count_at_least,
    "number_at_least": _op_number_at_least,
    "value_set_tier_non_empty": _op_value_set_tier_non_empty,
}


# ---------------------------------------------------------------- satisfied_when
#
# `satisfied_when` is a boolean expression over the criterion's own signal ids,
# so a criterion can require a conjunction (criterion 5 does) rather than being
# stuck with any-of. Parsed with ast and walked by hand: eval() over a config
# file is how a data file turns into an execution vector.

_ALLOWED_NODES = (ast.Expression, ast.BoolOp, ast.UnaryOp, ast.Name, ast.And, ast.Or, ast.Not, ast.Load)


def _eval_expression(expr: str, values: dict[str, bool], where: str) -> bool:
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"{where}: cannot parse satisfied_when {expr!r}: {exc}") from exc

    def walk(node: ast.AST) -> bool:
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(
                f"{where}: satisfied_when may only use signal names, and/or/not "
                f"and parentheses; found {type(node).__name__}"
            )
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.BoolOp):
            results = [walk(v) for v in node.values]
            return all(results) if isinstance(node.op, ast.And) else any(results)
        if isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, ast.Not):
                raise ValueError(f"{where}: only `not` is allowed as a unary operator")
            return not walk(node.operand)
        if isinstance(node, ast.Name):
            if node.id not in values:
                raise ValueError(
                    f"{where}: satisfied_when references unknown signal {node.id!r}; "
                    f"known signals are {sorted(values)}"
                )
            return values[node.id]
        raise ValueError(f"{where}: unexpected node {type(node).__name__}")

    return walk(tree)


# ---------------------------------------------------------------- model


@dataclass(frozen=True)
class Signal:
    id: str
    label: str
    tier: str
    description: str
    rule: dict
    subcriterion: str | None = None

    def holds(self, record: dict) -> bool:
        op = OPS.get(self.rule.get("op"))
        if op is None:
            raise ValueError(
                f"signal {self.id!r}: unknown rule op {self.rule.get('op')!r}; "
                f"known ops are {sorted(OPS)}"
            )
        return op(record, self.rule)


@dataclass(frozen=True)
class Criterion:
    id: str
    number: int
    label: str
    short_label: str
    tagline: str
    colour: str
    icon: str
    evidence_status: str
    rationale: str
    #: How this criterion was determined during curation, for readers who need to
    #: know what kind of judgement produced it before they trust the result.
    curation_method: str
    coverage_note: str
    satisfied_when: str
    signals: tuple[Signal, ...]
    #: Which registry fields the website renders inside this criterion's section,
    #: in order. Presentation only -- it never affects whether a criterion is met.
    display: tuple[dict, ...] = ()

    def evaluate(self, record: dict, tiers: Iterable[str] | None = None) -> tuple[bool, list[str]]:
        """Return (criterion met, ids of signals that fired).

        `tiers` restricts which signals are allowed to count. Passing
        ("direct", "derived") answers "would this criterion still hold on
        evidence that was actually recorded, with every inference removed"
        -- the question the review document and the second upset plot turn on.
        Signals outside the allowed tiers are evaluated as False rather than
        dropped, so a `not` in `satisfied_when` still means what it says.
        """
        allowed = None if tiers is None else set(tiers)
        fired = {
            s.id: (allowed is None or s.tier in allowed) and s.holds(record)
            for s in self.signals
        }
        met = _eval_expression(self.satisfied_when, fired, f"criterion {self.id!r}")
        return met, [sid for sid, ok in fired.items() if ok]


@dataclass(frozen=True)
class CriteriaSpec:
    id: str
    version: str
    figure: str
    source_document: str
    narrative: dict
    evidence_status_labels: dict
    criteria: tuple[Criterion, ...]
    unassigned_fields: tuple[dict, ...] = field(default_factory=tuple)
    #: Fields the site renders outside the six sections, and fields it knowingly
    #: does not render. Together with the criteria's `display` blocks these
    #: account for every field the coverage check expects to find.
    rendered_outside_criteria: tuple[str, ...] = field(default_factory=tuple)
    not_rendered: tuple[dict, ...] = field(default_factory=tuple)

    def rendered_fields(self) -> set[str]:
        fields = set(self.rendered_outside_criteria)
        for crit in self.criteria:
            for item in crit.display:
                if item.get("field"):
                    fields.add(item["field"])
        return fields

    def by_id(self, criterion_id: str) -> Criterion:
        for c in self.criteria:
            if c.id == criterion_id:
                return c
        raise KeyError(criterion_id)

    def evaluate(self, record: dict) -> dict[str, Any]:
        """Evaluate every criterion against one disease record.

        `met_direct` repeats the evaluation with proxy signals switched off, so
        a consumer can separate "the registry says so" from "we inferred it".
        """
        met: list[str] = []
        met_direct: list[str] = []
        signals: list[str] = []
        for crit in self.criteria:
            ok, fired = crit.evaluate(record)
            if ok:
                met.append(crit.id)
            signals.extend(fired)
            if crit.evaluate(record, tiers=NON_PROXY_TIERS)[0]:
                met_direct.append(crit.id)
        return {"met": met, "met_direct": met_direct, "signals": signals}


DEFAULT_CRITERIA_PATH = Path("config/prioritisation_criteria.yaml")


def load_criteria(path: str | Path = DEFAULT_CRITERIA_PATH) -> CriteriaSpec:
    raw = yaml.safe_load(Path(path).read_text())
    criteria = []
    seen_signals: set[str] = set()
    for c in raw["criteria"]:
        signals = []
        for s in c["signals"]:
            if s["id"] in seen_signals:
                raise ValueError(f"signal id {s['id']!r} is used by more than one criterion")
            seen_signals.add(s["id"])
            signals.append(
                Signal(
                    id=s["id"],
                    label=s["label"],
                    tier=s["tier"],
                    description=(s.get("description") or "").strip(),
                    rule=s["rule"],
                    subcriterion=str(s["subcriterion"]) if s.get("subcriterion") else None,
                )
            )
        criteria.append(
            Criterion(
                id=c["id"],
                number=int(c["number"]),
                label=c["label"],
                short_label=c.get("short_label", c["label"]),
                tagline=(c.get("tagline") or "").strip(),
                colour=c["colour"],
                icon=c.get("icon", f"{c['id']}.png"),
                evidence_status=c.get("evidence_status", "mixed"),
                rationale=(c.get("rationale") or "").strip(),
                curation_method=(c.get("curation_method") or "").strip(),
                coverage_note=(c.get("coverage_note") or "").strip(),
                satisfied_when=c["satisfied_when"],
                signals=tuple(signals),
                display=tuple(c.get("display") or ()),
            )
        )
    criteria.sort(key=lambda c: c.number)
    return CriteriaSpec(
        id=raw["id"],
        version=str(raw["version"]),
        figure=raw.get("figure", ""),
        source_document=(raw.get("source_document") or "").strip(),
        narrative={k: (v or "").strip() for k, v in (raw.get("narrative") or {}).items()},
        evidence_status_labels=raw.get("evidence_status_labels", {}),
        criteria=tuple(criteria),
        unassigned_fields=tuple(raw.get("unassigned_fields") or ()),
        rendered_outside_criteria=tuple(raw.get("rendered_outside_criteria") or ()),
        not_rendered=tuple(raw.get("not_rendered") or ()),
    )


def evaluate_all(spec: CriteriaSpec, diseases: Iterable[dict]) -> dict[str, dict]:
    """mondo_id -> {"met": [criterion ids], "signals": [signal ids]}."""
    return {d["mondo_id"]: spec.evaluate(d) for d in diseases}


def load_diseases(path: str | Path) -> list[dict]:
    data = yaml.load(Path(path).read_text(), Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
    return data.get("diseases") or []
