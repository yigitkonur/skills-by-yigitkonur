#!/usr/bin/env python3
"""Compare installed CLI command discovery with the skill's versioned index.

Only --version and --help invocations are executed. This checks discoverability,
not flag semantics, response fields, authentication, or live API behavior.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path


def run(binary, args):
    result = subprocess.run(
        [binary, *args], capture_output=True, text=True, timeout=10, check=False
    )
    if result.returncode:
        raise RuntimeError(f"Help/version failed for {args!r}: {result.stderr.strip()}")
    return result.stdout


def subcommands(help_text):
    section = re.search(r"^Commands:\n(.*?)(?=^\S|\Z)", help_text, re.M | re.S)
    if not section:
        return []
    return [
        match.group(1)
        for line in section.group(1).splitlines()
        if (match := re.match(r"  ([a-z][a-z0-9-]*)\s{2,}", line))
        and match.group(1) != "help"
    ]


def documented_paths(index):
    paths = {()}
    for line in index.read_text().splitlines():
        if not line.startswith("| `"):
            continue
        cells = line.split("|")
        group = re.fullmatch(r"\s*`([a-z][a-z0-9-]*)`\s*", cells[1])
        if not group:
            continue
        root = group.group(1)
        paths.add((root,))
        for name in re.findall(r"`([a-z][a-z0-9-]*)`", cells[2]):
            paths.add((root, name))
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", default="linear-cli")
    args = parser.parse_args()
    index = Path(__file__).resolve().parents[1] / "references" / "command-surface.md"
    try:
        version = run(args.binary, ["--version"]).strip()
        queue = [()]
        discovered = set()
        while queue:
            path = queue.pop(0)
            if path in discovered:
                continue
            if len(discovered) >= 600:
                raise RuntimeError("Discovery exceeded 600 paths; inspect the CLI manually")
            help_text = run(args.binary, [*path, "--help"])
            discovered.add(path)
            queue.extend((*path, name) for name in subcommands(help_text))
        documented = documented_paths(index)
        missing = sorted(" ".join(p) for p in discovered - documented)
        stale = sorted(" ".join(p) for p in documented - discovered)
        print(json.dumps({
            "version": version,
            "verification": "public command names and help availability only",
            "help_paths_checked": len(discovered),
            "root_groups": sum(len(p) == 1 for p in discovered),
            "missing_from_index": missing,
            "absent_from_binary": stale,
            "live_api_verified": False,
        }, indent=2))
        return 1 if missing or stale else 0
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
