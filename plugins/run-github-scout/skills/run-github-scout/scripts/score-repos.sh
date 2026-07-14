#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  score-repos.sh [--input FILE]

Reads TSV from gh-search.sh and emits TSV:
  owner/repo, signal_score, signal_notes, caveats

This is a cheap metadata scorer, not a semantic relevance scorer.
USAGE
}

input="-"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --input|-i)
      [ "$#" -ge 2 ] || { echo "Missing value for $1" >&2; exit 2; }
      input="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

command -v awk >/dev/null 2>&1 || {
  echo "awk is required for scoring TSV input." >&2
  exit 127
}

awk -F '\t' -v current_year="$(date +%Y)" '
function idx(name, fallback, i) {
  for (i = 1; i <= NF; i++) if ($i == name) return i
  return fallback
}
function truthy(value) {
  value = tolower(value)
  return value == "true" || value == "yes" || value == "1" || value == "present"
}
function add_note(text) {
  notes = notes (notes ? "; " : "") text
}
function add_caveat(text) {
  caveats = caveats (caveats ? "; " : "") text
}
NR == 1 {
  repo_i = idx("repo", 1)
  stars_i = idx("stars", 2)
  pushed_i = idx("pushed", 3)
  language_i = idx("language", 5)
  license_i = idx("license", 6)
  archived_i = idx("archived", 7)
  disabled_i = idx("disabled", 8)
  readme_i = idx("readme", 0)
  ci_i = idx("ci", 0)
  print "owner/repo\tsignal_score\tsignal_notes\tcaveats"
  next
}
NF < 2 { next }
{
  repo = $repo_i
  stars = $stars_i + 0
  pushed = $pushed_i
  language = language_i ? $language_i : ""
  license = license_i ? $license_i : ""
  archived = archived_i ? tolower($archived_i) : "false"
  disabled = disabled_i ? tolower($disabled_i) : "false"
  score = 0
  notes = ""
  caveats = ""

  if (archived == "true") add_caveat("archived")
  else score += 15
  if (disabled == "true") add_caveat("disabled")
  else score += 10

  if (stars >= 10000) { score += 25; add_note("stars >=10k") }
  else if (stars >= 1000) { score += 20; add_note("stars >=1k") }
  else if (stars >= 100) { score += 12; add_note("stars >=100") }
  else if (stars >= 10) { score += 5; add_note("stars >=10") }
  else add_caveat("low stars")

  pushed_year = substr(pushed, 1, 4) + 0
  if (pushed_year >= current_year - 1) { score += 25; add_note("recent push " pushed) }
  else if (pushed_year >= current_year - 2) { score += 12; add_note("older push " pushed) }
  else if (pushed_year > 0) add_caveat("stale push " pushed)
  else add_caveat("missing pushed date")

  if (license != "" && license != "none") { score += 10; add_note("license " license) }
  else add_caveat("license unknown")

  if (language != "") { score += 5; add_note("language " language) }
  if (readme_i && truthy($readme_i)) { score += 5; add_note("README present") }
  if (ci_i && truthy($ci_i)) { score += 5; add_note("CI visible") }

  if (archived == "true") score -= 30
  if (disabled == "true") score -= 30
  if (score < 0) score = 0
  if (score > 100) score = 100
  if (notes == "") notes = "metadata only"
  if (caveats == "") caveats = "semantic fit not scored"

  print repo "\t" score "\t" notes "\t" caveats
}
' "$input"
