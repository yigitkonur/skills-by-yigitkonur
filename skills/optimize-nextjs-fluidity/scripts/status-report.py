#!/usr/bin/env python3
"""Status report for a nextjs-enhancement/ plan. Read-only.

Parses tasks/*.md and reports:
  * count by status
  * dependency violations (a `done` task whose dependency is not `done`)
  * `done` tasks with an unticked Fix-tracking box
  * `blocked-needs-human` tasks (prepared one-way doors — a deliverable)
  * tasks missing a verification command (must not have been auto-applied)

Exit code 1 if any integrity problem is found, so it can gate a run.

Usage:
    status-report.py <nextjs-enhancement-root> [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VALID = {"pending", "in-progress", "done", "blocked", "blocked-needs-human", "wontfix"}
FIELD = r"^\*\*{label}:\*\*\s*(.+?)\s*$"


def field(text: str, label: str) -> str | None:
    m = re.search(FIELD.format(label=re.escape(label)), text, re.M)
    return m.group(1).strip() if m else None


def parse_task(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    status = (field(text, "Status") or "").strip().strip("`")
    status = re.sub(r"^([a-z-]+).*$", r"\1", status) if status else ""

    deps_raw = field(text, "Depends on") or "none"
    deps = re.findall(r"\[Task\s*(\d+)\]|(?<![\w/])(\d{2})-[a-z0-9-]+\.md", deps_raw)
    dep_ids = sorted({a or b for a, b in deps if (a or b)})
    if deps_raw.strip().lower() in {"none", "—", "-"}:
        dep_ids = []

    m = re.match(r"^(\d+)", path.name)
    return {
        "file": path.name,
        "id": m.group(1) if m else path.stem,
        "title": (re.search(r"^#\s*(.+)$", text, re.M).group(1).strip()
                  if re.search(r"^#\s*(.+)$", text, re.M) else path.stem),
        "status": status,
        "severity": (field(text, "Severity") or "").strip(),
        "reversibility": (field(text, "Reversibility") or "").strip(),
        "auto_apply": (field(text, "Auto-apply") or "").strip(),
        "domain": (field(text, "Domain") or "").strip(),
        "depends_on": dep_ids,
        "tracking_ticked": bool(re.search(r"^\s*-\s*\[x\]", text, re.M | re.I)),
        "has_verification": "## Verification command" in text,
        "has_rollback": "## Rollback" in text,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only status report for a nextjs-enhancement plan.")
    ap.add_argument("plan_root")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = Path(args.plan_root).expanduser().resolve()
    tasks_dir = root / "tasks" if (root / "tasks").is_dir() else root
    if not tasks_dir.is_dir():
        print(f"error: no tasks directory under {root}", file=sys.stderr)
        return 2

    files = sorted(p for p in tasks_dir.glob("*.md") if p.name != "00-INDEX.md")
    if not files:
        print(f"error: no task files in {tasks_dir}", file=sys.stderr)
        return 2

    tasks = [parse_task(p) for p in files]
    by_id = {t["id"]: t for t in tasks}

    counts: dict[str, int] = {}
    for t in tasks:
        counts[t["status"] or "(unparsed)"] = counts.get(t["status"] or "(unparsed)", 0) + 1

    problems: list[str] = []
    for t in tasks:
        if t["status"] not in VALID:
            problems.append(f"{t['file']}: invalid status '{t['status']}' (expected one of {', '.join(sorted(VALID))})")
        if t["status"] == "done":
            if not t["tracking_ticked"]:
                problems.append(f"{t['file']}: status=done but Fix-tracking box is unticked")
            for d in t["depends_on"]:
                dep = by_id.get(d)
                if dep and dep["status"] != "done":
                    problems.append(
                        f"{t['file']}: done, but dependency {d} ({dep['file']}) is '{dep['status']}'"
                    )
                elif not dep:
                    problems.append(f"{t['file']}: depends on unknown task {d}")
        if t["status"] == "done" and not t["has_verification"]:
            problems.append(f"{t['file']}: done without a Verification command section")
        if t["reversibility"].startswith("migration-required") and t["status"] == "done":
            problems.append(
                f"{t['file']}: migration-required task marked done — one-way doors must not be auto-applied"
            )
        if not t["has_rollback"]:
            problems.append(f"{t['file']}: missing Rollback section")

    needs_human = [t for t in tasks if t["status"] == "blocked-needs-human"]
    blocked = [t for t in tasks if t["status"] == "blocked"]

    if args.json:
        print(json.dumps({"counts": counts, "tasks": tasks, "problems": problems}, indent=2))
        return 1 if problems else 0

    print(f"# Status — {root.name}\n")
    print(f"{len(tasks)} task file(s) in {tasks_dir.relative_to(root) if tasks_dir != root else '.'}\n")
    print("| Status | Count |")
    print("|---|---|")
    for k in sorted(counts):
        print(f"| {k} | {counts[k]} |")

    if needs_human:
        print("\n## Prepared, awaiting a human decision\n")
        for t in needs_human:
            print(f"- `{t['file']}` — {t['title']} ({t['reversibility'] or 'reversibility unstated'})")

    if blocked:
        print("\n## Blocked (verification failed or drift)\n")
        for t in blocked:
            print(f"- `{t['file']}` — {t['title']}")

    if problems:
        print("\n## Integrity problems\n")
        for p in problems:
            print(f"- {p}")
        print(f"\n{len(problems)} problem(s) found.")
        return 1

    print("\nNo integrity problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
