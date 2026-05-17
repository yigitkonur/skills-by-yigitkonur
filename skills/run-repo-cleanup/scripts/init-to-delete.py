#!/usr/bin/env python3
"""Idempotent setup for the `to-delete/` quarantine pattern.

Ensures:
  1. `to-delete/` exists at the repo root with a `.gitkeep`.
  2. `.gitignore` has a `to-delete/` entry (idempotent).
  3. `.gitignore` has the recommended AI-artifact / secrets / scratch
     patterns appended under a clearly-labelled block (idempotent).

Safe to run repeatedly — the script only appends missing entries.

Usage:
    python3 init-to-delete.py
    python3 init-to-delete.py --dry-run
    python3 init-to-delete.py --print-patterns     # print patterns without changing repo

Exit codes:
    0  OK (changes made OR no changes needed)
    2  not in a git repo
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BLOCK_HEADER = "# ━━ Added by run-repo-cleanup init-to-delete.py ━━"
BLOCK_FOOTER = "# ━━ end run-repo-cleanup ━━"

PATTERNS = [
    "# to-delete/ sweep folder — never tracked, used for quarantine before real deletion",
    "to-delete/",
    "",
    "# Secrets (never tracked)",
    ".env",
    ".env.local",
    ".env.*.local",
    "*.pem",
    "*.p12",
    "id_rsa",
    "id_rsa.pub",
    "*.key",
    "credentials.json",
    "service-account.json",
    "",
    "# AI agent session artifacts",
    ".continues-handoff.md",
    ".claude-session*",
    ".cursor-session*",
    ".aider*",
    ".design-soul/",
    "derailment-notes/",
    "derail-notes/",
    "derail-results/",
    "",
    "# Editor scratch",
    ".vscode/settings.local.json",
    ".idea/workspace.xml",
    "*.swp",
    "*.swo",
    ".DS_Store",
    "Thumbs.db",
    "",
    "# Local-only test / debug output",
    "scratch/",
    "tmp/",
    "*.log",
]


def sh(cmd: list[str]) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def repo_root() -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(out) if rc == 0 else None


def existing_patterns(gitignore: Path) -> set[str]:
    if not gitignore.is_file():
        return set()
    patterns: set[str] = set()
    for raw in gitignore.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        patterns.add(line)
    return patterns


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--print-patterns", action="store_true")
    args = ap.parse_args()

    if args.print_patterns:
        for line in PATTERNS:
            print(line)
        return 0

    root = repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2

    to_delete = root / "to-delete"
    gitkeep = to_delete / ".gitkeep"
    gitignore = root / ".gitignore"

    actions: list[tuple[str, str]] = []

    # 1. to-delete/ directory + .gitkeep
    if not to_delete.is_dir():
        actions.append(("mkdir", str(to_delete)))
    if not gitkeep.is_file():
        actions.append(("touch", str(gitkeep)))

    # 2+3. .gitignore patterns
    existing = existing_patterns(gitignore)
    to_add = [p for p in PATTERNS if p and not p.startswith("#") and p not in existing]
    if to_add:
        actions.append(("append-gitignore", f"{len(to_add)} new pattern(s)"))

    if not actions:
        print("✓ to-delete/ + .gitignore patterns already in place. Nothing to do.")
        return 0

    print(f"{'DRY-RUN' if args.dry_run else 'APPLY'}: {len(actions)} action(s)")
    for verb, target in actions:
        print(f"  [{verb}] {target}")

    if args.dry_run:
        return 0

    # Execute
    to_delete.mkdir(exist_ok=True)
    gitkeep.touch(exist_ok=True)

    if to_add:
        # Append the full block (re-printing all patterns; only missing ones are new,
        # but appending the whole block keeps it cohesive and clearly labelled).
        block_lines = [""] if gitignore.is_file() and gitignore.read_text().strip() else []
        block_lines.append(BLOCK_HEADER)
        block_lines.extend(PATTERNS)
        block_lines.append(BLOCK_FOOTER)
        block_lines.append("")
        with gitignore.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(block_lines))

    print("")
    print("✓ to-delete/ ready. Use `mv <file> to-delete/` instead of `rm`.")
    print("  The folder + contents are gitignored. Owner reviews + flushes later.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
