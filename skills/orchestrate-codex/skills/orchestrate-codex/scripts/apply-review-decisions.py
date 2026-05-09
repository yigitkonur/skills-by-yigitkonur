#!/usr/bin/env python3
"""Print the ordered apply queue for a per-branch evaluator-decisions JSON.

Reads the evaluator's decisions JSON for one branch and prints:
  - Ambiguous items first with a BLOCKED warning (main agent must NOT apply
    when any item is ambiguous; the whole branch is BLOCKED for the round).
  - Accepted items in source-deduped order with `file:line` + intended-shape
    + rationale, ready for main agent to walk and apply via Edit.
  - Rejected items as a footer (informational; main agent skips them).

This script is **read-only**: it does NOT modify the worktree, does NOT commit,
does NOT push. It exists so the main agent can offload the queue derivation
rather than re-deriving it inline per branch.

Expected `<branch>.evaluation.json` shape (produced by main agent or evaluator):

    {
      "branch": "feat/foo",
      "round": 1,
      "totals": {"accepted": 5, "rejected": 4, "ambiguous": 1},
      "items": [
        {
          "id": "<source>-<n>",
          "decision": "accepted|rejected|ambiguous",
          "source": "codex-review|<other>",
          "file": "src/foo.ts",
          "line_start": 42,
          "line_end": 42,
          "title": "...",
          "intended_shape": "<the fix the evaluator approved>",
          "rationale": "<why the evaluator accepted/rejected/marked ambiguous>",
          "current_shape": "<excerpt of code as the evaluator saw it>"
        }
      ]
    }

Usage:
    apply-review-decisions.py --eval <path.json>
    apply-review-decisions.py --eval <path.json> --json
    apply-review-decisions.py --eval <path.json> --branch feat/foo

Exit codes:
    0  Queue printed; branch has accepted items to apply (zero ambiguous).
    1  Branch is BLOCKED — at least one ambiguous item; main agent must NOT apply.
    2  Evaluation file missing or malformed; or bad input.
    3  No accepted items AND no ambiguous items (round done).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_evaluation(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"evaluation file not found: {path}")
    try:
        with path.open() as f:
            payload = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"evaluation file is not valid JSON: {e}")
    if not isinstance(payload, dict):
        raise ValueError(
            f"evaluation file root must be an object, got {type(payload).__name__}"
        )
    return payload


def dedupe_items(items: list[dict]) -> list[dict]:
    """Deduplicate accepted items across review sources by (file, line, title-prefix).
    Preserves the FIRST seen rationale (earliest source wins).
    """
    seen: dict[tuple, dict] = {}
    for item in items:
        if item.get("decision") != "accepted":
            continue
        key = (
            (item.get("file") or "").strip().lower(),
            int(item.get("line_start") or item.get("line") or 0),
            ((item.get("title") or "").strip().lower())[:60],
        )
        if key not in seen:
            seen[key] = item
    return list(seen.values())


def render_human(payload: dict, branch_override: str | None) -> tuple[str, int]:
    """Render the apply queue. Returns (text, exit_code)."""
    branch = branch_override or payload.get("branch", "?")
    round_n = payload.get("round")
    items = payload.get("items") or []

    by_decision: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        if not isinstance(item, dict):
            continue
        d = item.get("decision", "unknown")
        by_decision[d].append(item)

    ambiguous = by_decision.get("ambiguous", [])
    accepted = dedupe_items(items)
    rejected = by_decision.get("rejected", [])

    out: list[str] = []
    header = f"branch: {branch}"
    if round_n is not None:
        header += f"  round: {round_n}"
    out.append(header)
    out.append(
        f"  totals: accepted={len(accepted)} (deduped from "
        f"{len(by_decision.get('accepted', []))} raw), "
        f"rejected={len(rejected)}, ambiguous={len(ambiguous)}"
    )
    out.append("")

    # Ambiguous goes FIRST so main agent sees the BLOCKED gate.
    if ambiguous:
        out.append("=" * 72)
        out.append("⚠  BRANCH IS BLOCKED FOR THIS ROUND — DO NOT APPLY ACCEPTED ITEMS EITHER")
        out.append("=" * 72)
        out.append(
            "Invariant: a single ambiguous item BLOCKS the entire round."
        )
        out.append(
            "Half-apply ships unreviewed code with a half-decided intent."
        )
        out.append("")
        for i, item in enumerate(ambiguous, start=1):
            out.append(f"  [AMBIGUOUS #{i}] {item.get('title', '<no title>')}")
            out.append(f"    source:    {item.get('source', '?')}")
            out.append(
                f"    file:line: {item.get('file', '?')}:"
                f"{item.get('line_start', item.get('line', '?'))}"
            )
            rationale = (item.get("rationale") or "").strip()
            if rationale:
                out.append(f"    question:  {rationale}")
            out.append("")
        out.append("Action: mark branch BLOCKED in manifest with terminal_reason citing the items above.")
        out.append("Action: surface in deliverable. Action: do NOT merge.")
        return "\n".join(out), 1  # exit 1 = BLOCKED

    if not accepted:
        out.append("No accepted items. Round is either DONE-after-eval (rejected-only)")
        out.append("or there were no items to begin with. Apply step is a no-op for this round.")
        return "\n".join(out), 3

    out.append("=" * 72)
    out.append("APPLY QUEUE (in dedup-source order — apply each via Edit, commit per concern)")
    out.append("=" * 72)
    for i, item in enumerate(accepted, start=1):
        out.append(f"  [{i}/{len(accepted)}] {item.get('title', '<no title>')}")
        out.append(f"    source:    {item.get('source', '?')}")
        line_start = item.get('line_start', item.get('line', '?'))
        line_end = item.get('line_end')
        line_str = f"{line_start}"
        if line_end and line_end != line_start:
            line_str += f"-{line_end}"
        out.append(f"    file:line: {item.get('file', '?')}:{line_str}")
        rationale = (item.get("rationale") or "").strip()
        if rationale:
            out.append(f"    rationale: {rationale}")
        current = (item.get("current_shape") or "").rstrip()
        intended = (item.get("intended_shape") or "").rstrip()
        if current:
            out.append("    current shape:")
            for line in current.splitlines()[:8]:
                out.append(f"      {line}")
            if len(current.splitlines()) > 8:
                out.append(f"      ... ({len(current.splitlines()) - 8} more lines)")
        if intended:
            out.append("    intended shape:")
            for line in intended.splitlines()[:8]:
                out.append(f"      {line}")
            if len(intended.splitlines()) > 8:
                out.append(f"      ... ({len(intended.splitlines()) - 8} more lines)")
        commit_msg = (
            f"<type>(<scope>): {item.get('title', 'apply review decision')[:60]}"
        )
        out.append(f"    commit:    {commit_msg}")
        out.append("")

    out.append("Reminders for main agent:")
    out.append("  - Stage by concern from the start (do NOT `git add .` then `git restore --staged .`).")
    out.append("  - Validate before push: build + test (per repo conventions).")
    out.append("  - If intended_shape doesn't apply cleanly: do NOT improvise — record")
    out.append("    `apply_failed_after_evaluation: <id>` in manifest, continue, surface at end.")
    out.append("  - One concern per commit by default; multi-concern only with bullets-in-message.")

    if rejected:
        out.append("")
        out.append("-" * 72)
        out.append(f"REJECTED ({len(rejected)}, informational — DO NOT apply):")
        for item in rejected[:8]:
            out.append(f"  - [{item.get('source', '?')}] {item.get('title', '<no title>')[:80]}")
        if len(rejected) > 8:
            out.append(f"  ... ({len(rejected) - 8} more rejected)")

    return "\n".join(out), 0


def render_json(payload: dict, branch_override: str | None) -> tuple[str, int]:
    """JSON-shaped output for downstream tooling. Returns (json_text, exit_code)."""
    items = payload.get("items") or []
    by_decision: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        if not isinstance(item, dict):
            continue
        by_decision[item.get("decision", "unknown")].append(item)

    ambiguous = by_decision.get("ambiguous", [])
    accepted = dedupe_items(items)
    rejected = by_decision.get("rejected", [])

    if ambiguous:
        exit_code = 1
        status = "BLOCKED"
    elif not accepted:
        exit_code = 3
        status = "NO-OP"
    else:
        exit_code = 0
        status = "READY"

    output = {
        "branch": branch_override or payload.get("branch"),
        "round": payload.get("round"),
        "status": status,
        "totals": {
            "accepted_raw": len(by_decision.get("accepted", [])),
            "accepted_deduped": len(accepted),
            "rejected": len(rejected),
            "ambiguous": len(ambiguous),
        },
        "ambiguous": ambiguous,
        "queue": accepted,
        "rejected_titles": [
            f"[{i.get('source', '?')}] {i.get('title', '')[:120]}" for i in rejected
        ],
    }
    return json.dumps(output, indent=2, default=str), exit_code


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--eval", "--evaluation",
        dest="eval_path", required=True,
        help="Path to <branch>.evaluation.json",
    )
    ap.add_argument(
        "--branch", default=None,
        help="Override branch name (informational; default reads from JSON).",
    )
    ap.add_argument(
        "--json", action="store_true",
        help="Machine-readable JSON output for downstream tooling",
    )
    args = ap.parse_args()

    eval_path = Path(args.eval_path)
    try:
        payload = load_evaluation(eval_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.json:
        text, exit_code = render_json(payload, args.branch)
    else:
        text, exit_code = render_human(payload, args.branch)

    print(text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
