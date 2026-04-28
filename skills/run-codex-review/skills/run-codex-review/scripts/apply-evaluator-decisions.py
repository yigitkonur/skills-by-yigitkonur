#!/usr/bin/env python3
"""Print the ordered apply queue for a Phase 8a (main-agent direct apply).

Reads the Phase 7 Evaluator's decisions JSON for one PR and prints:
  - Ambiguous items first with a BLOCKED warning (Phase 8a must NOT apply
    when any item is ambiguous; the whole PR is BLOCKED).
  - Accepted items in source-deduped order with `file:line` + intended-shape
    + rationale, ready for main agent to walk and apply via Edit.
  - Rejected items as a footer (informational; main agent skips them).

This script is **read-only**: it does NOT modify the worktree, does NOT commit,
does NOT push. It exists so main agent can offload the queue derivation rather
than re-deriving it inline per PR (which production traces showed costs ~5
extra tool calls per PR × 9 PRs × multiple sessions).

The expected `pr-<n>.evaluation.json` shape (produced by Phase 7 Evaluator):

    {
      "pr": 53,
      "branch": "feat/foo",
      "totals": {"accepted": 5, "rejected": 4, "ambiguous": 1},
      "items": [
        {
          "id": "<source>-<n>",
          "decision": "accepted|rejected|ambiguous",
          "source": "codex-rescue|copilot|copilot-pull-request-reviewer|cubic-dev-ai|devin|greptile|<human>",
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
    python3 apply-evaluator-decisions.py \\
        --pr 53 \\
        --worktree /path/to/wt \\
        --eval /repo/.codex-review-rounds/pr-53.evaluation.json \\
        --print-queue

    # JSON output for downstream tools (one-line-per-item):
    python3 apply-evaluator-decisions.py --pr 53 --worktree /path --eval /path --json

Exit codes:
    0  Queue printed; PR has accepted items to apply (and zero ambiguous).
    1  PR is BLOCKED — at least one ambiguous item; main agent must NOT apply.
    2  Evaluation file missing or malformed.
    3  No accepted items AND no ambiguous items (PR done already).
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
        raise ValueError(f"evaluation file root must be an object, got {type(payload).__name__}")
    return payload


def dedupe_items(items: list[dict]) -> list[dict]:
    """Deduplicate accepted items across review sources by (file, line, title-prefix).
    Preserves the FIRST seen rationale (earliest source wins). Production traces
    showed multiple bots flagging the same issue with slightly different wording;
    main agent applies once.
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


def render_human(payload: dict) -> tuple[str, int]:
    """Render the apply queue for human / main-agent reading. Returns
    (text, exit_code). exit_code semantics match the module docstring.
    """
    pr = payload.get("pr", "?")
    branch = payload.get("branch", "?")
    items = payload.get("items") or []

    by_decision: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        d = item.get("decision", "unknown")
        by_decision[d].append(item)

    ambiguous = by_decision.get("ambiguous", [])
    accepted = dedupe_items(items)
    rejected = by_decision.get("rejected", [])

    out: list[str] = []
    out.append(f"PR #{pr} — branch: {branch}")
    out.append(f"  totals: accepted={len(accepted)} (deduped from {len(by_decision.get('accepted', []))} raw), "
               f"rejected={len(rejected)}, ambiguous={len(ambiguous)}")
    out.append("")

    # Ambiguous goes FIRST so main agent sees the BLOCKED gate before the queue.
    if ambiguous:
        out.append("=" * 72)
        out.append("⚠  PR IS BLOCKED — DO NOT APPLY ACCEPTED ITEMS EITHER")
        out.append("=" * 72)
        out.append("Per Phase 8a invariant: a single ambiguous item BLOCKS the entire PR.")
        out.append("Half-apply ships unreviewed code with a half-decided intent.")
        out.append("")
        for i, item in enumerate(ambiguous, start=1):
            out.append(f"  [AMBIGUOUS #{i}] {item.get('title', '<no title>')}")
            out.append(f"    source:    {item.get('source', '?')}")
            out.append(f"    file:line: {item.get('file', '?')}:"
                       f"{item.get('line_start', item.get('line', '?'))}")
            rationale = item.get("rationale", "").strip()
            if rationale:
                out.append(f"    question:  {rationale}")
            out.append("")
        out.append("Action: mark PR BLOCKED in manifest with terminal_reason citing the items above.")
        out.append("Action: surface in deliverable. Action: do NOT merge.")
        return "\n".join(out), 1  # exit 1 = BLOCKED

    if not accepted:
        out.append("No accepted items. PR is either DONE-after-eval (rejected-only)")
        out.append("or there were no items to begin with. Phase 8a is a no-op for this PR.")
        return "\n".join(out), 3

    out.append("=" * 72)
    out.append("APPLY QUEUE (in dedup-source order — apply each via Edit, commit per concern)")
    out.append("=" * 72)
    for i, item in enumerate(accepted, start=1):
        out.append(f"  [{i}/{len(accepted)}] {item.get('title', '<no title>')}")
        out.append(f"    source:    {item.get('source', '?')}")
        out.append(f"    file:line: {item.get('file', '?')}:"
                   f"{item.get('line_start', item.get('line', '?'))}"
                   + (f"-{item['line_end']}" if item.get('line_end')
                      and item.get('line_end') != item.get('line_start') else ""))
        rationale = item.get("rationale", "").strip()
        if rationale:
            out.append(f"    rationale: {rationale}")
        current = (item.get("current_shape") or "").rstrip()
        intended = (item.get("intended_shape") or "").rstrip()
        if current:
            out.append(f"    current shape:")
            for line in current.splitlines()[:8]:
                out.append(f"      {line}")
            if len(current.splitlines()) > 8:
                out.append(f"      ... ({len(current.splitlines()) - 8} more lines)")
        if intended:
            out.append(f"    intended shape:")
            for line in intended.splitlines()[:8]:
                out.append(f"      {line}")
            if len(intended.splitlines()) > 8:
                out.append(f"      ... ({len(intended.splitlines()) - 8} more lines)")
        commit_msg = (
            f"<emoji> <type>(<scope>): {item.get('title', 'apply evaluator decision')[:60]} "
            f"(#{pr})"
        )
        out.append(f"    commit:    {commit_msg}")
        out.append("")

    out.append("Reminders for main agent:")
    out.append("  - Stage by concern from the start (do NOT `git add .` then `git restore --staged .`).")
    out.append("  - Validate before push: `pnpm run build && pnpm test` (or repo-equivalent).")
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


def render_json(payload: dict) -> tuple[str, int]:
    """JSON-shaped output for downstream tooling. Returns (json_text, exit_code)."""
    items = payload.get("items") or []
    by_decision: dict[str, list[dict]] = defaultdict(list)
    for item in items:
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
        "pr": payload.get("pr"),
        "branch": payload.get("branch"),
        "status": status,
        "totals": {
            "accepted_raw": len(by_decision.get("accepted", [])),
            "accepted_deduped": len(accepted),
            "rejected": len(rejected),
            "ambiguous": len(ambiguous),
        },
        "ambiguous": ambiguous,  # full items so caller can format BLOCKED messages
        "queue": accepted,        # the order to walk
        "rejected_titles": [
            f"[{i.get('source', '?')}] {i.get('title', '')[:120]}" for i in rejected
        ],
    }
    return json.dumps(output, indent=2), exit_code


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pr", type=int, required=True, help="PR number (informational)")
    ap.add_argument("--worktree", required=True,
                    help="Worktree path (informational; not actually read by this script)")
    ap.add_argument("--eval", "--evaluation", dest="eval_path", required=True,
                    help="Path to pr-<n>.evaluation.json from Phase 7")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--print-queue", action="store_true", default=True,
                      help="(default) Human-readable apply queue")
    mode.add_argument("--json", action="store_true",
                      help="Machine-readable JSON output for downstream tooling")
    args = ap.parse_args()

    eval_path = Path(args.eval_path)
    try:
        payload = load_evaluation(eval_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    # Make sure the PR number in the file matches the CLI arg (catches mistyped --pr)
    file_pr = payload.get("pr")
    if file_pr is not None and int(file_pr) != args.pr:
        print(f"ERROR: --pr={args.pr} but evaluation file is for PR #{file_pr} ({eval_path})",
              file=sys.stderr)
        return 2

    if args.json:
        text, exit_code = render_json(payload)
    else:
        text, exit_code = render_human(payload)

    print(text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
