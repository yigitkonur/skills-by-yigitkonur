# Body Size Validation

Pre-creation validation rules for issue bodies. Run before every `gh issue create` call.

## Validation sequence

Before creating any issue, run these checks in order:

### 1. Character count

```bash
BODY="$(<issue_body.md)"
CHAR_COUNT=${#BODY}

if [ "$CHAR_COUNT" -gt 60000 ]; then
  echo "SPLIT REQUIRED: $CHAR_COUNT chars exceeds 60,000 threshold"
  echo "GitHub hard limit: 65,536 chars. Using 60K for safety buffer."
  exit 1
fi

if [ "$CHAR_COUNT" -gt 40000 ]; then
  echo "WARNING: $CHAR_COUNT chars. Consider splitting for readability."
fi
```

### 2. Required sections

Every issue body must contain these sections. Reject if missing:

```bash
REQUIRED_SECTIONS=(
  "## Context & Rationale"
  "## Strategic Intent"
  "## Definition of Done"
  "## Wave & Dependencies"
)

for section in "${REQUIRED_SECTIONS[@]}"; do
  if ! grep -qF "$section" <<< "$BODY"; then
    echo "MISSING SECTION: $section"
    exit 1
  fi
done
```

### 3. BSV criteria check

Every DoD criterion must be Binary, Specific, and Verifiable. Flag vague criteria:

```bash
VAGUE_PATTERNS=(
  "should be fast"
  "works correctly"
  "code is clean"
  "follows best practices"
  "good performance"
  "handles errors gracefully"
  "is user-friendly"
  "tests pass"  # which tests?
)

for pattern in "${VAGUE_PATTERNS[@]}"; do
  if grep -qiF "$pattern" <<< "$BODY"; then
    echo "VAGUE DoD CRITERION DETECTED: '$pattern'"
    echo "Rewrite with specific, measurable threshold."
  fi
done
```

### 4. Cross-reference integrity

Check that referenced issue numbers exist:

```bash
REFERENCED=$(grep -oP '#\d+' <<< "$BODY" | sort -u)
for ref in $REFERENCED; do
  NUM=${ref#\#}
  if ! gh issue view "$NUM" --json number -q .number &>/dev/null; then
    echo "BROKEN REFERENCE: $ref does not exist"
  fi
done
```

### 5. Label existence

```bash
LABELS="wave:1,type:task,priority:high"
IFS=',' read -ra LABEL_ARRAY <<< "$LABELS"
EXISTING=$(gh label list --limit 200 --json name -q '.[].name')
for label in "${LABEL_ARRAY[@]}"; do
  if ! echo "$EXISTING" | grep -qxF "$label"; then
    echo "MISSING LABEL: $label — create it first"
  fi
done
```

## Split decision tree

```
Body > 60,000 chars?
├── YES → Split into parent-stub + child-detail
│         Read references/issue-size-management.md (in plan-prd skill)
│         Split at semantic boundaries (user story groups, vertical slices, modules)
│         Parent stub: < 2,000 chars (scope summary + child links + parent-level DoD)
│         Children: standard body template with parent reference
│
└── NO → Proceed with creation
         Body > 40,000 chars? → Log warning, consider splitting for readability
         Body < 5,000 chars for type:task? → Verify sufficient context for subagent
```

## Minimum body size

Issue bodies that are too short indicate insufficient context:

| Type | Min chars | Signal if below |
|---|---|---|
| `type:epic` | 500 | May need more child context |
| `type:feature` | 1,000 | Missing context or DoD |
| `type:task` | 1,500 | Subagent will lack context to execute |
| `type:subtask` | 800 | May be fine if parent provides context |

## Batch validation

When creating multiple issues in sequence, validate all bodies before creating any:

```bash
ISSUES_DIR="./issue-bodies"
ERRORS=0

for body_file in "$ISSUES_DIR"/*.md; do
  CHARS=$(wc -c < "$body_file")
  if [ "$CHARS" -gt 60000 ]; then
    echo "OVERSIZED: $body_file ($CHARS chars)"
    ERRORS=$((ERRORS + 1))
  fi
done

if [ "$ERRORS" -gt 0 ]; then
  echo "$ERRORS issues need splitting before creation can proceed."
  exit 1
fi
```
