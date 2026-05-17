#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: init-corpus.sh <topic-slug> [entity-slug ...]

Create deterministic run-industry-research corpus scaffolding:
  <topic-slug>/
    README.md
    _meta/research-plan.md
    _meta/methodology-and-source-policy.md
    _meta/discovered-entities.md
    _meta/file-budget.md
    _meta/_PRODUCT_TEMPLATE.md
    _meta/_COMPARISON_TEMPLATE.md
    _cross-product/09-sources/

Optional entity slugs create directories only:
  <topic-slug>/<entity-slug>/
  <topic-slug>/<entity-slug>/09-sources/

No entity evidence files are created.
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

mkdir -p "$topic_slug/_meta" "$topic_slug/_cross-product/09-sources"

write_if_missing "$topic_slug/README.md" "# ${topic_slug}

Start here after Phase 3. Record the corpus scope, capture date, highest-signal entry points, core entity index, cross-comparison index, caveats, and unresolved gaps."

write_if_missing "$topic_slug/_meta/research-plan.md" "# Research Plan

Record the Phase 0 scope statement, audience, geography, decision type, scale, entity tiers, and Phase 1 category-understanding note before Phase 2."

write_if_missing "$topic_slug/_meta/methodology-and-source-policy.md" "# Methodology And Source Policy

Record the available research tools, fallback path, source hierarchy, capture-date convention, quote discipline, and how confirmed facts, vendor claims, practitioner reports, inference, contradictions, and unverified claims are separated."

write_if_missing "$topic_slug/_meta/discovered-entities.md" "# Discovered Entities

Record Phase 1 candidates in this shape:

| Slug | Name | Vendor | URL | Tier | Status | Surfaced by | Notes |
|---|---|---|---|---|---|---|---|"

write_if_missing "$topic_slug/_meta/file-budget.md" "# File Budget

Record the Phase 3 tree plan, template-derived file-count expectation, entity tiers, profile-page decision, and the final reconciled file count after verification."

write_if_missing "$topic_slug/_meta/_PRODUCT_TEMPLATE.md" "# Product Template

Record the Phase 2 per-entity comprehensiveness contract here before Phase 4. Include every numbered section, the buyer question each section answers, insufficient-evidence handling, evidence header expectations, and source-ledger requirements."

write_if_missing "$topic_slug/_meta/_COMPARISON_TEMPLATE.md" "# Comparison Template

Record the Phase 2 compact comparison contract here, or replace this file with per-criterion _COMPARISON_TEMPLATE_<criterion>.md files for standard, deep, or tiered corpora. Include the base matrix columns and criterion-specific additions."

for entity_slug in "$@"; do
  mkdir -p "$topic_slug/$entity_slug/09-sources"
  printf 'created directories: %s/%s and %s/%s/09-sources\n' "$topic_slug" "$entity_slug" "$topic_slug" "$entity_slug"
done

printf 'initialized corpus scaffold: %s\n' "$topic_slug"
