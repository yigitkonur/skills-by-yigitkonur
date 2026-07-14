#!/usr/bin/env python3
"""Aggressively sweep non-essential files into a gitignored `to-delete/` and
consolidate docs into a gitignored `docs/`, managing `.gitignore` along the way.

Operates at the repo root. DRY-RUN by default — pass --execute to actually move.

Behavior (see references/to-delete-and-docs.md for the policy):
  1. Ensure .gitignore has the cleanup block (idempotent), BEFORE moving.
  2. KEEP-LIST: essential files never move.
  3. SWEEP candidates -> to-delete/ (relative path preserved).
  4. DOCS consolidation -> docs/ (stray root *.md + doc folders).
  5. UNCERTAIN files are left in place and reported "review manually".
  6. git mv for tracked files, os.rename/shutil.move for untracked.
  7. to-delete/.gitkeep and docs/.gitkeep created with the folders.

Usage:
    python3 sweep-artifacts.py            # dry-run
    python3 sweep-artifacts.py --execute  # move for real
    python3 sweep-artifacts.py --json     # machine-readable output

Exit codes:
    0  nothing to do (clean)
    1  moves to make (dry-run) OR moves were made
    2  not a git repo
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

GITIGNORE_HEADER = "# Added by run-repo-cleanup sweep-artifacts.py"

# The block to ensure under the header (exactly per the policy reference).
GITIGNORE_BLOCK = [
    "to-delete/",
    "docs/",
    "",
    "# Secrets (never tracked)",
    ".env",
    ".env.*",
    "*.pem",
    "id_rsa",
    "id_rsa.pub",
    "*.key",
    "credentials.json",
    "service-account.json",
    "",
    "# AI agent session artifacts",
    "*.claude-session*",
    ".cursor-session*",
    ".aider*",
    ".continues-handoff.md",
    ".design-soul/",
    "derailment-notes/",
]

# KEEP-LIST: exact names + globs matched at repo root that must never move.
KEEP_GLOBS = [
    "README*",
    "AGENTS.md",
    "CLAUDE.md",
    "LICENSE*",
    "CONTRIBUTING*",
    "CODE_OF_CONDUCT*",
    ".gitignore",
    ".git",
    "to-delete",
    "docs",
    # run / build essentials
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "pyproject.toml",
    "poetry.lock",
    "requirements*.txt",
    "setup.py",
    "setup.cfg",
    "Makefile",
    "Dockerfile",
    "docker-compose*",
    "tsconfig*.json",
    "*.config.js",
    "*.config.ts",
    ".github",
    # common source dirs
    "src",
    "lib",
    "app",
    "pkg",
    "cmd",
    "internal",
    "tests",
    "test",
    "public",
    "static",
    "assets",
]

# SWEEP globs -> to-delete/. Matched at repo root by name.
SWEEP_GLOBS = [
    ".continues-handoff.md",
    "*.claude-session*",
    ".cursor-session*",
    ".aider*",
    ".design-soul",
    "derailment-notes",
    "derail-*",
    "scratch",
    "tmp",
    "debug-*.sh",
    "one-off-*",
    "TODO.md",
    "NOTES.md",
    "PLAN.md",
    "IDEAS.md",
    "*.plan.md",
    ".env",
    ".env.*",
    "*.pem",
    "id_rsa*",
    "*.key",
    "credentials.json",
    "service-account.json",
    "*.log",
    "*.zip",
    "*.sqlite",
]

# Doc-like folders whose CONTENTS consolidate into docs/.
DOC_FOLDERS = {"agent-docs", "documentation", "notes"}

# Doc-keep names: root *.md files that are NOT swept into docs/ (they are kept).
DOC_KEEP_GLOBS = [
    "README*",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING*",
    "CODE_OF_CONDUCT*",
]


def sh(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout.rstrip("\n"), p.stderr.rstrip("\n")
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"


def repo_root() -> Path | None:
    rc, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(out) if rc == 0 else None


def matches_any(name: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, g) for g in globs)


def tracked_files(root: Path) -> set[str]:
    rc, out, _ = sh(["git", "ls-files"], cwd=root)
    if rc != 0:
        return set()
    return {line for line in out.splitlines() if line}


def is_tracked(rel: str, tracked: set[str]) -> bool:
    # rel may be a dir; tracked set is files. A dir is "tracked" if any file under it is.
    if rel in tracked:
        return True
    prefix = rel.rstrip("/") + "/"
    return any(f.startswith(prefix) for f in tracked)


def ensure_gitignore(root: Path, execute: bool) -> list[str]:
    """Ensure the cleanup block is present. Returns the list of lines added.

    Idempotent: only pattern lines (non-blank, non-comment) absent from the
    entire .gitignore are considered "to add". If any are missing we (re)write
    the full block under the header so it stays cohesive.
    """
    gitignore = root / ".gitignore"
    existing_lines: list[str] = []
    if gitignore.is_file():
        existing_lines = gitignore.read_text().splitlines()

    existing_patterns = {
        ln.strip()
        for ln in existing_lines
        if ln.strip() and not ln.strip().startswith("#")
    }

    block_patterns = [
        ln for ln in GITIGNORE_BLOCK if ln and not ln.startswith("#")
    ]
    missing = [p for p in block_patterns if p not in existing_patterns]
    if not missing:
        return []

    if execute:
        block_lines: list[str] = []
        if existing_lines and "".join(existing_lines).strip():
            block_lines.append("")
        block_lines.append(GITIGNORE_HEADER)
        block_lines.extend(GITIGNORE_BLOCK)
        with gitignore.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(block_lines) + "\n")

    return missing


def move_entry(
    root: Path, rel_src: str, rel_dst: str, tracked: set[str], execute: bool
) -> None:
    """Move src -> dst under root. git mv if tracked, else filesystem move."""
    if not execute:
        return
    dst_abs = root / rel_dst
    dst_abs.parent.mkdir(parents=True, exist_ok=True)
    if is_tracked(rel_src, tracked):
        rc, _, err = sh(["git", "mv", "-k", rel_src, rel_dst], cwd=root)
        if rc == 0:
            return
        # fall back to filesystem move if git mv refused
        sys.stderr.write(f"  (git mv failed for {rel_src}: {err}; using fs move)\n")
    src_abs = root / rel_src
    shutil.move(str(src_abs), str(dst_abs))


def plan_destination_to_delete(name: str) -> str:
    return f"to-delete/{name}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true", help="actually move files")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    root = repo_root()
    if root is None:
        if args.json:
            print(json.dumps({"error": "not a git repository"}))
        else:
            print("not inside a git repository", file=sys.stderr)
        return 2

    execute = args.execute
    tracked = tracked_files(root)

    # 1. .gitignore FIRST (so moved files don't show as deletions).
    gitignore_added = ensure_gitignore(root, execute)

    to_delete_moves: list[tuple[str, str]] = []  # (src, dst)
    to_docs_moves: list[tuple[str, str]] = []
    kept: list[str] = []
    uncertain: list[str] = []

    # Iterate the repo-root entries.
    entries = sorted(p.name for p in root.iterdir())

    for name in entries:
        entry = root / name
        is_dir = entry.is_dir()

        # KEEP-LIST: never move.
        if matches_any(name, KEEP_GLOBS):
            kept.append(name + ("/" if is_dir else ""))
            continue

        # DOCS consolidation: doc-like folders -> their contents into docs/.
        if is_dir and name in DOC_FOLDERS:
            for sub in entry.rglob("*"):
                if sub.is_file():
                    rel_src = str(sub.relative_to(root))
                    rel_dst = f"docs/{rel_src}"
                    to_docs_moves.append((rel_src, rel_dst))
            continue

        # SWEEP candidates -> to-delete/.
        if matches_any(name, SWEEP_GLOBS):
            to_delete_moves.append((name, plan_destination_to_delete(name)))
            continue

        # DOCS: stray root-level *.md not in doc-keep-list.
        if not is_dir and fnmatch.fnmatch(name, "*.md"):
            if not matches_any(name, DOC_KEEP_GLOBS):
                to_docs_moves.append((name, f"docs/{name}"))
                continue

        # UNCERTAIN: not clearly keep, not clearly sweep.
        uncertain.append(name + ("/" if is_dir else ""))

    # Decide whether folders need creating.
    need_to_delete = bool(to_delete_moves)
    need_docs = bool(to_docs_moves) or (root / "docs").is_dir()

    if execute:
        if need_to_delete or (root / "to-delete").is_dir():
            (root / "to-delete").mkdir(exist_ok=True)
            (root / "to-delete" / ".gitkeep").touch(exist_ok=True)
        if need_docs:
            (root / "docs").mkdir(exist_ok=True)
            (root / "docs" / ".gitkeep").touch(exist_ok=True)

    # Perform moves (gitignore already written above).
    for src, dst in to_delete_moves:
        move_entry(root, src, dst, tracked, execute)
    for src, dst in to_docs_moves:
        move_entry(root, src, dst, tracked, execute)

    # Clean up now-empty doc source folders.
    if execute:
        for name in DOC_FOLDERS:
            d = root / name
            if d.is_dir() and not any(d.iterdir()):
                try:
                    d.rmdir()
                except OSError:
                    pass

    total_moves = len(to_delete_moves) + len(to_docs_moves)

    if args.json:
        print(
            json.dumps(
                {
                    "execute": execute,
                    "gitignore_added": gitignore_added,
                    "to_delete": [{"from": s, "to": d} for s, d in to_delete_moves],
                    "to_docs": [{"from": s, "to": d} for s, d in to_docs_moves],
                    "uncertain": uncertain,
                    "kept": kept,
                },
                indent=2,
            )
        )
    else:
        mode = "EXECUTE" if execute else "DRY-RUN"
        print(f"sweep-artifacts.py [{mode}] @ {root}")
        print("")

        print(f"gitignore updates ({len(gitignore_added)}):")
        if gitignore_added:
            for p in gitignore_added:
                verb = "added" if execute else "would add"
                print(f"  [{verb}] {p}")
        else:
            print("  (already complete)")
        print("")

        verb = "moved" if execute else "would move"
        print(f"-> to-delete/ ({len(to_delete_moves)}):")
        for src, dst in to_delete_moves:
            print(f"  [{verb}] {src} -> {dst}")
        print("")

        print(f"-> docs/ ({len(to_docs_moves)}):")
        for src, dst in to_docs_moves:
            print(f"  [{verb}] {src} -> {dst}")
        print("")

        print(f"kept (essential) ({len(kept)}):")
        for k in kept:
            print(f"  {k}")
        print("")

        print(f"uncertain — review manually ({len(uncertain)}):")
        for u in uncertain:
            print(f"  {u}")
        print("")

    if total_moves == 0 and not gitignore_added:
        if not args.json:
            print("✓ clean. Nothing to sweep.")
        return 0
    if not execute:
        if not args.json:
            print("DRY-RUN complete. Re-run with --execute to apply.")
        return 1
    if not args.json:
        print(f"✓ sweep complete: {total_moves} move(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
