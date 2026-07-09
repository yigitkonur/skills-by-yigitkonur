#!/usr/bin/env bash
# scan-verdicts.sh — extract verdicts + high/medium finding headlines from a set
# of Codex adversarial-review report files, for fast Phase-4 triage.
#
# Usage:
#   scan-verdicts.sh <report-file> [<report-file> ...]
#   scan-verdicts.sh <dir>                # scans *.output and *.md under <dir>
#
# Each report is the codex-companion output (ends with a "# Codex Adversarial
# Review" block containing "Verdict:" and "- [high]/[medium]" finding lines).
# Prints one summary line per file, then every high/medium finding headline.

set -u

files=()
for arg in "$@"; do
  if [ -d "$arg" ]; then
    while IFS= read -r f; do files+=("$f"); done < <(find "$arg" -maxdepth 1 -type f \( -name '*.output' -o -name '*.md' \) 2>/dev/null)
  elif [ -f "$arg" ]; then
    files+=("$arg")
  fi
done

if [ "${#files[@]}" -eq 0 ]; then
  echo "usage: scan-verdicts.sh <report-file|dir> [...]" >&2
  exit 2
fi

echo "=== SUMMARY (verdict + finding counts) ==="
for f in "${files[@]}"; do
  v=$(grep -m1 '^Verdict:' "$f" 2>/dev/null | sed 's/^Verdict: //')
  [ -n "$v" ] || v="(no verdict / running / clean)"
  hi=$(grep -c '^- \[high\]' "$f" 2>/dev/null); hi=${hi:-0}
  me=$(grep -c '^- \[medium\]' "$f" 2>/dev/null); me=${me:-0}
  printf '%-45s %-18s hi=%s med=%s\n' "$(basename "$f")" "$v" "$hi" "$me"
done

echo
echo "=== FINDINGS (high + medium headlines) ==="
for f in "${files[@]}"; do
  grep -E '^- \[(high|medium)\]' "$f" 2>/dev/null | sed "s|^|$(basename "$f")  |"
done

echo
echo "Next: dedupe by (file, defect-class); send candidate-real + verify-vs-recent-fix items to Phase 5 verifiers BEFORE any fix."
