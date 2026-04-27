#!/usr/bin/env python3
"""Apply major-vs-minor policy to a normalized Codex review JSON.

Reads the JSON written by run-codex-review.py and partitions items into
{major, minor, unclassified_treated_as_major} per the policy in
references/major-vs-minor-policy.md. Default-when-ambiguous: major
(conservative — better to over-loop than miss a real issue).

Usage:
    python3 classify-review-feedback.py --review-json <path>
    python3 classify-review-feedback.py --review-json <path> --policy <path>
    python3 classify-review-feedback.py --review-json <path> --json

Exit codes:
    0  ≥1 major item — caller continues the loop
    1  no major items — caller marks branch DONE
    2  fatal parse error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# Default trigger lists (kept in lock-step with references/major-vs-minor-policy.md)
DEFAULT_MAJOR_TRIGGERS = [
    # correctness
    r"\bcorrectness\b", r"\bwrong\b", r"\bincorrect\b", r"\bbug\b",
    r"\boff[- ]?by[- ]?one\b", r"\bdoes not handle\b", r"\breturns wrong\b",
    # runtime stability
    r"\bcrash\w*\b", r"\bpanic\b", r"\binfinite loop\b", r"\bdeadlock\b",
    r"\bleak\b", r"\bunbounded\b", r"\boom\b", r"\bstack overflow\b",
    # data integrity
    r"\bdata loss\b", r"\bdata corruption\b", r"\blost write\b",
    r"\brace condition\b", r"\bracey?\b", r"\binconsistent state\b",
    r"\bnon[- ]?atomic\b",
    # security
    r"\binjection\b", r"\bxss\b", r"\bcsrf\b", r"\bsql inject\w*\b",
    r"\bauth bypass\b", r"\bunsafe deserialization\b", r"\bsecret\b",
    r"\bcredential\b", r"\brce\b", r"\bpath traversal\b", r"\bssrf\b",
    r"\bsecurity\s+(risk|issue|hole)\b",
    # regressions
    r"\bregression\b", r"\bbreaks?\b", r"\bbroken\b",
    r"\bpreviously worked\b", r"\bremoved without replacement\b",
    # hygiene that hides bugs
    r"\bsilently? swallow\b", r"\bsilent fail\b", r"\bunreachable\b",
    r"\bdead code that should run\b", r"\bunhandled exception\b",
    r"\bmissing error check\b",
    # branch structure
    r"\bmixed concerns?\b", r"\bcommit does too much\b",
    r"\bshould be split\b", r"\bmultiple unrelated changes\b",
]

DEFAULT_MINOR_TRIGGERS = [
    # formatting
    r"\bformatting\b", r"\bwhitespace\b", r"\bindentation\b",
    r"\bline length\b", r"\bsemicolon\b",
    # naming
    r"\brename\b", r"\bnaming\b", r"\bconsider naming\b",
    r"\bconvention prefers\b", r"\bmore descriptive name\b",
    # style
    r"\bprefer\w*\b", r"\bidiomatic\b", r"\bstyle\b",
    r"\bnits?\b", r"\bnitpicks?\b", r"\bcosmetic\b",
    # docs polish
    r"\btypo in comment\b", r"\bcomment phrasing\b",
    r"\bdocs polish\b", r"\bwording\b",
    # speculative perf
    r"\bmight be faster\b", r"\bconsider caching\b",
    r"\bspeculative\b", r"\bmicro[- ]?optimization\b",
    # scope creep
    r"\bwhile you'?re at it\b", r"\balso consider\b",
    r"\bbonus\b", r"\bwould be nice\b",
]

SEVERITY_MAJOR = {"critical", "high", "error", "blocker", "must-fix"}
SEVERITY_MINOR = {"low", "info", "style", "nit", "polish", "optional"}


def load_policy(path: str | None) -> dict:
    """Load policy.json overrides, or return defaults."""
    policy = {
        "major_triggers": list(DEFAULT_MAJOR_TRIGGERS),
        "minor_triggers": list(DEFAULT_MINOR_TRIGGERS),
        "severity_major": set(SEVERITY_MAJOR),
        "severity_minor": set(SEVERITY_MINOR),
    }
    if not path or not Path(path).is_file():
        return policy
    try:
        with open(path) as f:
            override = json.load(f)
    except (OSError, json.JSONDecodeError):
        return policy
    # promote_to_major: keywords that should now classify as major
    for kw in override.get("promote_to_major", []):
        pattern = rf"\b{re.escape(kw)}\b"
        if pattern not in policy["major_triggers"]:
            policy["major_triggers"].append(pattern)
        # remove from minor if present
        policy["minor_triggers"] = [
            p for p in policy["minor_triggers"] if pattern not in p
        ]
    # demote_to_minor: keywords that should now classify as minor
    for kw in override.get("demote_to_minor", []):
        pattern = rf"\b{re.escape(kw)}\b"
        if pattern not in policy["minor_triggers"]:
            policy["minor_triggers"].append(pattern)
        policy["major_triggers"] = [
            p for p in policy["major_triggers"] if pattern not in p
        ]
    # additional triggers (added without removing from the other list)
    for kw in override.get("additional_major_triggers", []):
        policy["major_triggers"].append(rf"\b{re.escape(kw)}\b")
    for kw in override.get("additional_minor_triggers", []):
        policy["minor_triggers"].append(rf"\b{re.escape(kw)}\b")
    return policy


def count_matches(text: str, patterns: list[str]) -> int:
    """How many distinct patterns match the text (case-insensitive)."""
    text_lower = text.lower() if text else ""
    return sum(
        1 for p in patterns
        if re.search(p, text_lower, flags=re.IGNORECASE)
    )


def classify_item(item: dict, policy: dict) -> str:
    """Return 'major', 'minor', or 'unclassified' for one item."""
    severity_raw = (item.get("severity_raw") or "").strip().lower()

    # Severity short-circuit
    if severity_raw in policy["severity_major"]:
        return "major"
    if severity_raw in policy["severity_minor"]:
        return "minor"

    # Keyword scan over body
    body = item.get("body") or ""
    major_n = count_matches(body, policy["major_triggers"])
    minor_n = count_matches(body, policy["minor_triggers"])

    if major_n > minor_n:
        return "major"
    if minor_n > major_n:
        return "minor"
    if major_n == 0 and minor_n == 0:
        return "unclassified"
    # tie with both > 0: default major (conservative)
    return "major"


def classify_unstructured(raw_text: str, policy: dict) -> tuple[list, list, list]:
    """When items[] is empty, scan raw_text for triggers as a single virtual item."""
    if not raw_text:
        return [], [], []
    virtual = {
        "id": "raw-text-fallback",
        "severity_raw": "unstructured",
        "body": raw_text,
        "file": None,
        "line": None,
    }
    cls = classify_item(virtual, policy)
    if cls == "major":
        return [virtual], [], []
    if cls == "minor":
        return [], [virtual], []
    return [], [], [virtual]


def classify_review(review: dict, policy: dict) -> dict:
    items = review.get("items") or []
    if not items:
        major, minor, unclassified = classify_unstructured(
            review.get("raw_text", ""), policy
        )
    else:
        major, minor, unclassified = [], [], []
        for item in items:
            cls = classify_item(item, policy)
            if cls == "major":
                major.append(item)
            elif cls == "minor":
                minor.append(item)
            else:
                unclassified.append(item)

    return {
        "review_id": review.get("review_id"),
        "branch": review.get("branch"),
        "head_sha": review.get("head_sha"),
        "major": major,
        "minor": minor,
        "unclassified_treated_as_major": unclassified,
        "summary": {
            "total": len(major) + len(minor) + len(unclassified),
            "major_n": len(major),
            "minor_n": len(minor),
            "unclassified_n": len(unclassified),
        },
    }


def render_text(result: dict) -> str:
    lines = []
    s = result["summary"]
    lines.append(f"branch:        {result['branch']}")
    lines.append(f"review:        {result['review_id']}")
    lines.append(f"head:          {result['head_sha']}")
    lines.append(f"summary:       {s['total']} total  ({s['major_n']} major, {s['minor_n']} minor, {s['unclassified_n']} unclassified→major)")
    lines.append("")
    if result["major"]:
        lines.append(f"MAJOR ({len(result['major'])}):")
        for it in result["major"]:
            loc = f" {it.get('file', '')}:{it.get('line', '')}" if it.get("file") else ""
            body = (it.get("body") or "").splitlines()[0][:120]
            lines.append(f"  • [{it.get('severity_raw', '?')}]{loc}  {body}")
    if result["unclassified_treated_as_major"]:
        lines.append("")
        lines.append(f"UNCLASSIFIED → MAJOR ({len(result['unclassified_treated_as_major'])}):")
        for it in result["unclassified_treated_as_major"]:
            loc = f" {it.get('file', '')}:{it.get('line', '')}" if it.get("file") else ""
            body = (it.get("body") or "").splitlines()[0][:120]
            lines.append(f"  • [{it.get('severity_raw', '?')}]{loc}  {body}")
    if result["minor"]:
        lines.append("")
        lines.append(f"minor ({len(result['minor'])}):")
        for it in result["minor"]:
            loc = f" {it.get('file', '')}:{it.get('line', '')}" if it.get("file") else ""
            body = (it.get("body") or "").splitlines()[0][:80]
            lines.append(f"  • [{it.get('severity_raw', '?')}]{loc}  {body}")
    lines.append("")
    if result["major"] or result["unclassified_treated_as_major"]:
        lines.append("→ continue loop (≥1 major)")
    else:
        lines.append("→ DONE (no major)")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--review-json", required=True, help="path to normalized review JSON")
    ap.add_argument("--policy", default=None, help="path to policy.json overrides")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    try:
        with open(args.review_json) as f:
            review = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"failed to read review JSON: {e}", file=sys.stderr)
        return 2

    policy = load_policy(args.policy)
    result = classify_review(review, policy)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(render_text(result))

    has_major = result["summary"]["major_n"] > 0 or result["summary"]["unclassified_n"] > 0
    return 0 if has_major else 1


if __name__ == "__main__":
    sys.exit(main())
