#!/usr/bin/env bash
# detect-project.sh — print the project type for routing: macos | node | python | generic
# Heuristic, cheapest signals first. A repo can be several; we pick the backend-deciding one.
# macOS wins only when the work clearly needs Apple toolchain (Xcode/Swift/CocoaPods).
set -euo pipefail
root="${1:-$PWD}"

has() { compgen -G "$root/$1" >/dev/null 2>&1; }

if has '*.xcodeproj' || has '*.xcworkspace' || [ -f "$root/Package.swift" ] || [ -f "$root/Podfile" ]; then
  echo macos
elif [ -f "$root/package.json" ]; then
  echo node
elif [ -f "$root/pyproject.toml" ] || [ -f "$root/requirements.txt" ] || [ -f "$root/setup.py" ] || [ -f "$root/Pipfile" ] || [ -f "$root/poetry.lock" ]; then
  echo python
else
  echo generic
fi
