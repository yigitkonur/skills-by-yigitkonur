#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Usage:
  scaffold-agents-md.sh --type root-agents --title "Project Name" [--write AGENTS.md]
  scaffold-agents-md.sh --type folder-agents --title "src/api" [--write src/api/AGENTS.md]
  scaffold-agents-md.sh --type review --title "Project Name" [--write REVIEW.md]

After-discovery helper. Emits one minimal skeleton to stdout by default.
Use --write only with an explicit target path after the file plan is known.
EOF
}

type=
title=
write_path=

while [ "$#" -gt 0 ]; do
  case "$1" in
    --type)
      type=${2:-}
      shift 2
      ;;
    --title)
      title=${2:-}
      shift 2
      ;;
    --write)
      write_path=${2:-}
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$type" ] || [ -z "$title" ]; then
  echo "error: --type and --title are required" >&2
  usage >&2
  exit 2
fi

emit() {
  case "$type" in
    root-agents)
      cat <<EOF
# $title

## Commands
- Add only verified repo-wide commands and cite their source file.

## Architecture
- Add only top-level boundaries discovered from the repo.

## Conventions
- Add repo-specific rules that prevent real mistakes.

## Boundaries
- Always: preserve critical repo invariants found during discovery.
- Ask: list changes that need user or maintainer approval.
- Never: list dangerous actions proven relevant to this repo.
EOF
      ;;
    folder-agents)
      cat <<EOF
# $title

## Local Focus
- State what this folder owns.

## Local Commands
- Add only verified commands local to this folder.

## Local Conventions
- Add folder-specific rules not already covered by the parent file.

## Local Boundaries
- Always: preserve local invariants found during Wave 2.
- Never: avoid local mistakes discovery proved likely.
EOF
      ;;
    review)
      cat <<EOF
# $title Review Context

## Critical Areas
- Add repo-specific changes that deserve high scrutiny.

## Security
- Add security review rules only when discovery found real security boundaries.

## Conventions
- Add semantic review rules not already enforced by deterministic tooling.

## Ignore
- Add generated or irrelevant paths reviewers should ignore.

## Testing
- Add validation expectations reviewers should require for risky diffs.
EOF
      ;;
    *)
      echo "error: --type must be root-agents, folder-agents, or review" >&2
      exit 2
      ;;
  esac
}

if [ -z "$write_path" ]; then
  emit
  exit 0
fi

parent=$(dirname "$write_path")
if [ ! -d "$parent" ]; then
  echo "error: target directory does not exist: $parent" >&2
  exit 2
fi

if [ -e "$write_path" ] || [ -L "$write_path" ]; then
  echo "error: refusing to overwrite existing file: $write_path" >&2
  exit 2
fi

tmp="$write_path.tmp.$$"
emit > "$tmp"
mv "$tmp" "$write_path"
printf 'wrote %s\n' "$write_path"
