#!/usr/bin/env bash
# record-finding.sh — Lightweight telemetry and evidence serializer for zeoradar-agentic-qa subagents
# Usage: record-finding.sh <case_result_dir> <case_id> <status: PASSED|FAILED|BLOCKED> <summary_narrative>

set -euo pipefail

RESULT_DIR="${1:-}"
CASE_ID="${2:-}"
STATUS="${3:-}"
NARRATIVE="${4:-}"

if [[ -z "$RESULT_DIR" || -z "$CASE_ID" || -z "$STATUS" ]]; then
  echo "Usage: $0 <case_result_dir> <case_id> <status> <narrative>" >&2
  exit 1
fi

mkdir -p "$RESULT_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Write or append to result.md
cat <<EOF > "$RESULT_DIR/result.md"
# Test Execution Result: $CASE_ID

- **Executed At**: $TIMESTAMP
- **Outcome**: $STATUS
- **Summary**: $NARRATIVE

## Observations & Telemetry
$NARRATIVE
EOF

# Initialize or write evidence.json
cat <<EOF > "$RESULT_DIR/evidence.json"
{
  "caseId": "$CASE_ID",
  "executedAt": "$TIMESTAMP",
  "outcome": "$STATUS",
  "summary": "$NARRATIVE"
}
EOF

echo "[EVIDENCE_RECORDED] $CASE_ID -> $RESULT_DIR ($STATUS)"
