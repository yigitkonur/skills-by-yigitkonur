#!/usr/bin/env python3
"""Eval runner for the ci-cd-optimize rebuild.

Modes:
  validate  (default) Deterministic schema/consistency checks. Safe for CI:
            no network, no model calls.
  list      Print case inventories for manual review.
  trigger   Print ready-to-run `claude -p` trigger probes for manual/dev use.
            Never run in CI; activation testing needs a live model.

Exit codes: 0 = all checks passed, 1 = validation failure, 2 = usage error.
"""

import json
import re
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")

TRIGGER_CATEGORIES = {
    "direct-positive": True,
    "indirect-positive": True,
    "uncommon-positive": True,
    "near-miss-negative": False,
    "simple-negative": False,
    "competing-negative": False,
}


def load(name: str):
    path = EVALS_DIR / name
    try:
        return json.loads(path.read_text()), []
    except FileNotFoundError:
        return None, [f"{name}: missing"]
    except json.JSONDecodeError as exc:
        return None, [f"{name}: invalid JSON: {exc}"]


def check_baseline(doc) -> list[str]:
    errors = []
    sha = doc.get("baseline_sha", "")
    if not FULL_SHA.match(sha):
        errors.append(f"baseline.json: baseline_sha must be a full 40-hex SHA, got {sha!r}")
    if not doc.get("baseline_skill_path", "").startswith("skills/"):
        errors.append("baseline.json: baseline_skill_path must live under skills/")
    return errors


def check_trigger(doc) -> list[str]:
    errors = []
    cases = doc.get("cases", [])
    ids = [c.get("id") for c in cases]
    if len(ids) != len(set(ids)):
        errors.append("trigger-cases.json: duplicate case ids")
    queries = [c.get("query") for c in cases]
    if len(queries) != len(set(queries)):
        errors.append("trigger-cases.json: duplicate query text (breaks per-query aggregation)")
    counts: dict[str, int] = {}
    for case in cases:
        cat = case.get("category")
        if cat not in TRIGGER_CATEGORIES:
            errors.append(f"trigger-cases.json[{case.get('id')}]: unknown category {cat!r}")
            continue
        counts[cat] = counts.get(cat, 0) + 1
        if case.get("should_trigger") is not TRIGGER_CATEGORIES[cat]:
            errors.append(
                f"trigger-cases.json[{case.get('id')}]: should_trigger contradicts category {cat}"
            )
        if not case.get("query", "").strip():
            errors.append(f"trigger-cases.json[{case.get('id')}]: empty query")
        if cat == "competing-negative" and not case.get("competing_skill"):
            errors.append(f"trigger-cases.json[{case.get('id')}]: competing-negative needs competing_skill")
    for cat in TRIGGER_CATEGORIES:
        if counts.get(cat, 0) < 2:
            errors.append(f"trigger-cases.json: category {cat} has fewer than 2 cases")
    if len(cases) < 20:
        errors.append(f"trigger-cases.json: {len(cases)} cases; corpus requires at least 20")
    return errors


def check_functional(doc) -> list[str]:
    errors = []
    cases = doc.get("cases", [])
    ids = [c.get("id") for c in cases]
    if len(ids) != len(set(ids)):
        errors.append("functional-cases.json: duplicate case ids")
    if len(cases) < 12:
        errors.append(f"functional-cases.json: {len(cases)} cases; corpus requires at least 12")
    critical_total = 0
    for case in cases:
        if not case.get("prompt", "").strip():
            errors.append(f"functional-cases.json[{case.get('id')}]: empty prompt")
        expectations = case.get("expectations", [])
        if not expectations:
            errors.append(f"functional-cases.json[{case.get('id')}]: no expectations")
        for exp in expectations:
            if "text" not in exp or "critical" not in exp:
                errors.append(
                    f"functional-cases.json[{case.get('id')}]: expectation missing text/critical"
                )
            if exp.get("critical") is True:
                critical_total += 1
    if critical_total < 5:
        errors.append("functional-cases.json: fewer than 5 critical release-gate expectations")
    return errors


def check_matrix(doc) -> list[str]:
    errors = []
    sha = doc.get("base_sha", "")
    if not FULL_SHA.match(sha):
        errors.append("requirements-matrix.json: base_sha must be a full 40-hex SHA")
    pr_rows = doc.get("pr_rows", [])
    expected_prs = {f"pr-{n}" for n in range(74, 86)}
    got_prs = {row.get("id") for row in pr_rows}
    if got_prs != expected_prs:
        errors.append(
            f"requirements-matrix.json: pr_rows must cover exactly #74-#85; missing {sorted(expected_prs - got_prs)}, unexpected {sorted(got_prs - expected_prs)}"
        )
    for row in pr_rows:
        if row.get("decision") not in {"adopt", "adapt", "reject"}:
            errors.append(f"requirements-matrix.json[{row.get('id')}]: invalid decision")
        if not row.get("acceptance"):
            errors.append(f"requirements-matrix.json[{row.get('id')}]: missing acceptance check")
    defect_rows = doc.get("defect_rows", [])
    expected_defects = {f"d85-{n}" for n in range(1, 12)}
    got_defects = {row.get("id") for row in defect_rows}
    if got_defects != expected_defects:
        errors.append("requirements-matrix.json: defect_rows must cover exactly d85-1..d85-11")
    for row in defect_rows:
        if not row.get("requirement") or not row.get("test_ids"):
            errors.append(f"requirements-matrix.json[{row.get('id')}]: defect needs requirement and test_ids")
    return errors


def validate() -> int:
    errors: list[str] = []
    for name, checker in (
        ("baseline.json", check_baseline),
        ("trigger-cases.json", check_trigger),
        ("functional-cases.json", check_functional),
        ("requirements-matrix.json", check_matrix),
    ):
        doc, load_errors = load(name)
        errors.extend(load_errors)
        if doc is not None:
            errors.extend(checker(doc))
    if errors:
        for err in errors:
            print(f"FAIL {err}")
        return 1
    print("OK all eval corpora valid")
    return 0


def list_cases() -> int:
    for name in ("trigger-cases.json", "functional-cases.json"):
        doc, load_errors = load(name)
        if load_errors:
            print("\n".join(load_errors))
            return 1
        print(f"== {name} ({len(doc['cases'])} cases)")
        for case in doc["cases"]:
            label = case.get("category") or case.get("name")
            print(f"  {case['id']}  {label}")
    return 0


def trigger_probes() -> int:
    doc, load_errors = load("trigger-cases.json")
    if load_errors:
        print("\n".join(load_errors))
        return 1
    print("# Manual trigger probes — run each in a fresh session; repeat 3x for borderline cases.")
    for case in doc["cases"]:
        expected = "TRIGGER" if case["should_trigger"] else "NO-TRIGGER"
        print(f"# {case['id']} expect={expected}")
        print(f"claude -p {json.dumps(case['query'])}")
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if mode == "validate":
        return validate()
    if mode == "list":
        return list_cases()
    if mode == "trigger":
        return trigger_probes()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
