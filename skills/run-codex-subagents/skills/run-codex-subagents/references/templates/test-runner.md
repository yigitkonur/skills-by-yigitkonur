# Test Runner Template

Use this when a turn should only run tests and report the result.

```markdown
## Context

Why this test run matters right now.

## Mission

Run the specified test command only. Do not edit files.

## Test Command

`npm test`

## Output Requirement

If tests fail:
- list each failing test
- include file and line details when available
- summarize the failure count

If tests pass:
- report the total pass count or success summary line
- report total duration when available
```

If a failure needs fixing, start a separate coding turn after the report.
