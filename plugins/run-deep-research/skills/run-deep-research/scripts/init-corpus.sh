#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: init-corpus.sh <topic-slug> [entity-slug ...]

Create deterministic run-deep-research corpus scaffolding (Dual-Layer Architecture):
  <topic-slug>/
    README.md
    _meta/manifest.json
    _meta/claims.jsonl
    _meta/01-charter.md
    _meta/02-entities.md
    _meta/03-axes.md
    _meta/04-product-template.md
    _meta/05-axis-templates.md
    _meta/06-file-budget.md
    _meta/07-dispatch-log.md
    _cross/

Optional entity slugs create directories only:
  <topic-slug>/<entity-slug>/

Entity research produces consolidated dossiers (<entity-slug>/dossier.md and sources.md).
No premature stub files are created.
USAGE
}

is_slug() {
  [[ "$1" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]
}

write_if_missing() {
  local path="$1"
  local content="$2"
  if [[ -e "$path" ]]; then
    printf 'exists: %s\n' "$path"
    return
  fi
  printf '%s\n' "$content" > "$path"
  printf 'created: %s\n' "$path"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

topic_slug="$1"
shift

if ! is_slug "$topic_slug"; then
  printf 'error: topic-slug must be kebab-case: %s\n' "$topic_slug" >&2
  exit 2
fi

for entity_slug in "$@"; do
  if ! is_slug "$entity_slug"; then
    printf 'error: entity slug must be kebab-case: %s\n' "$entity_slug" >&2
    exit 2
  fi
done

mkdir -p "$topic_slug/_meta" "$topic_slug/_cross"

write_if_missing "$topic_slug/README.md" "# ${topic_slug}

Start here after Phase 3. Record the corpus scope, capture date, highest-signal entry points, core entity index, cross-comparison index, caveats, and unresolved gaps."

write_if_missing "$topic_slug/_meta/manifest.json" "{
  \"topic\": \"${topic_slug}\",
  \"version\": \"1.0.0\",
  \"entities\": {},
  \"axes\": [],
  \"cross_axes\": []
}"

if [[ ! -e "$topic_slug/_meta/claims.jsonl" ]]; then
  touch "$topic_slug/_meta/claims.jsonl"
  printf 'created: %s\n' "$topic_slug/_meta/claims.jsonl"
else
  printf 'exists: %s\n' "$topic_slug/_meta/claims.jsonl"
fi

write_if_missing "$topic_slug/_meta/01-charter.md" "# Research Charter

Record the Phase 0 scope statement, audience, geography, decision type, scale, entity tiers, and Phase 1 category-understanding note before Phase 2."

write_if_missing "$topic_slug/_meta/02-entities.md" "# Discovered Entities

Record Phase 1 candidates in this shape:

| Slug | Name | Vendor | URL | Tier | Status | Surfaced by | Notes |
|---|---|---|---|---|---|---|---|"

write_if_missing "$topic_slug/_meta/03-axes.md" "# Evaluation Axes

Record the Phase 1B derived axis catalog, decision-flipping primitives, and practitioner channel list."

write_if_missing "$topic_slug/_meta/04-product-template.md" "# Product Dossier Template

Record the Phase 2 per-entity comprehensiveness contract here before Phase 4. Include frontmatter field definitions, required dossier sections, insufficient-evidence handling, and source-ledger expectations."

write_if_missing "$topic_slug/_meta/05-axis-templates.md" "# Axis Comparison Templates

Record the Phase 2 cross-comparison contracts here. Include matrix columns, ranking dimensions, and the required Executive Digest shape."

write_if_missing "$topic_slug/_meta/06-file-budget.md" "# File Budget

Record the Phase 3 tree plan, consolidated dossier expectations (MAX 3 per entity, MAX 3 per cross, MAX 8 in _meta), entity tiers, and the final reconciled file count."

write_if_missing "$topic_slug/_meta/07-dispatch-log.md" "# Dispatch Log

Running log tracking wave dispatches, subagent IDs, completion status, and evaluation gate results."

for entity_slug in "$@"; do
  mkdir -p "$topic_slug/$entity_slug"
  printf 'created directory: %s/%s\n' "$topic_slug" "$entity_slug"
done

printf 'initialized corpus scaffold: %s\n' "$topic_slug"
