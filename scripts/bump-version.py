#!/usr/bin/env python3
"""Bump the patch version in VERSION and regenerate the marketplace.

Called by CI on every push to main so `/plugin marketplace update` sees a
new version and refreshes installed plugins. Prints the new version.

    python3 scripts/bump-version.py           # patch bump (default)
    python3 scripts/bump-version.py minor      # minor bump, reset patch
    python3 scripts/bump-version.py major      # major bump, reset minor+patch
"""

import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_PATH = os.path.join(REPO_ROOT, "VERSION")


def read():
    try:
        parts = open(VERSION_PATH).read().strip().split(".")
        return [int(parts[0]), int(parts[1]), int(parts[2])]
    except (FileNotFoundError, IndexError, ValueError):
        return [1, 0, 0]


def main():
    level = sys.argv[1] if len(sys.argv) > 1 else "patch"
    major, minor, patch = read()
    if level == "major":
        major, minor, patch = major + 1, 0, 0
    elif level == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1

    new = f"{major}.{minor}.{patch}"
    with open(VERSION_PATH, "w") as f:
        f.write(new + "\n")

    # Propagate the new version into every plugin entry (silence its stdout so
    # callers capturing our stdout get only the version string).
    subprocess.run(
        [sys.executable, os.path.join(REPO_ROOT, "scripts", "gen-marketplace.py")],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    print(new)


if __name__ == "__main__":
    main()
