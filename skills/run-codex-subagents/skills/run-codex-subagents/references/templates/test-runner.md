# Test Runner Template

Template for test execution tasks. The agent runs a test command, captures output, and reports structured results.

## Template

```json
{
  "prompt": "Run `{test_command}` and capture the full output.\n\nIf any tests fail:\n- Report each failure with: test name, file path, line number, error message\n- Group failures by file\n- Report total: X passed, Y failed, Z skipped\n\nIf all tests pass:\n- Report total count and duration\n- Confirm: 'All {N} tests passed in {duration}'",
  "cwd": "{project_root}",
  "task_type": "tester",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 120000
}
```

## Key Rules

1. **Always `tester` task type.** Routes to the test-optimized profile.
2. **Always `low` reasoning.** Test execution is procedural — run, capture, format.
3. **Always set timeout.** 120s for unit tests, 300s for integration, 600s for full suites.
4. **Prompt must specify both paths:** what to report on success AND on failure.

## Examples by Language

### Swift

```json
{
  "prompt": "Run `swift test 2>&1` and capture the full output.\n\nIf any tests fail:\n- Report each failure: test name, file path, line number, assertion message\n- Group by test target\n- Report: X passed, Y failed\n\nIf all pass: report count and duration.",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "tester",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 180000
}
```

### JavaScript / TypeScript (vitest)

```json
{
  "prompt": "Run `npx vitest run --reporter=verbose 2>&1` and capture the full output.\n\nIf any tests fail:\n- Report each: test name, file path, line number, error + expected vs received\n- Group by test file\n- Report: X passed, Y failed, Z skipped\n\nIf all pass: report count and duration.",
  "cwd": "/Users/me/dev/project",
  "task_type": "tester",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 120000
}
```

### Python (pytest)

```json
{
  "prompt": "Run `pytest -v --tb=short 2>&1` and capture the full output.\n\nIf any tests fail:\n- Report each: test function name, file:line, short traceback, assertion message\n- Group by test file\n- Report: X passed, Y failed, Z errors, W skipped\n\nIf all pass: report count and duration.",
  "cwd": "/Users/me/dev/project",
  "task_type": "tester",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 120000
}
```

### Rust (cargo)

```json
{
  "prompt": "Run `cargo test 2>&1` and capture the full output.\n\nIf any tests fail:\n- Report each: test name (full path), assertion message, stdout capture\n- Group by test module\n- Report: X passed, Y failed, Z ignored\n\nIf all pass: report count and duration.",
  "cwd": "/Users/me/dev/project",
  "task_type": "tester",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 120000
}
```

### Go

```json
{
  "prompt": "Run `go test ./... -v 2>&1` and capture the full output.\n\nIf any tests fail:\n- Report each: test function, package, file:line, error output\n- Group by package\n- Report: X passed, Y failed\n\nIf all pass: report count and duration.",
  "cwd": "/Users/me/dev/project",
  "task_type": "tester",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 120000
}
```

## Variants

### Targeted test (single file or pattern)

```json
{
  "prompt": "Run `swift test --filter NotchHoverStateMachineTests 2>&1`. Report all results — pass or fail — with test names and durations.",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "tester",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 60000
}
```

### Coverage report

```json
{
  "prompt": "Run `pytest --cov=src --cov-report=term-missing 2>&1`. Report:\n1. Overall coverage percentage\n2. Files below 80% coverage with their percentages\n3. Total uncovered lines count\n\nDo NOT list fully covered files.",
  "cwd": "/Users/me/dev/project",
  "task_type": "tester",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 120000
}
```

### Regression check

```json
{
  "prompt": "Run `swift test 2>&1`. Regression check after NotchHoverStateMachine extraction.\n\nIf all pass: report 'Regression check passed: {N} tests, {duration}'\nIf any fail: report each failure, flag if test name contains 'Hover' or 'StateMachine'.",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "tester",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 180000,
  "labels": ["regression", "hover"]
}
```

## Follow-up Pattern

When tests fail: read the failure report, spawn a `coder` task to fix, then re-run the test runner. `test-runner → failures → coder (fix) → test-runner → all pass`.

## Anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Using `coder` task type for tests | Wrong profile, may try to "fix" tests | Use `tester` |
| Medium/high reasoning for tests | Wastes tokens on simple execution | Always `low` |
| No timeout | Test suite might hang forever | Always set timeout |
| Combining test + fix in one task | Agent may silently change tests to pass | Separate: test, then fix |
| Not specifying output format | Agent returns raw test output (noisy) | Specify structured report format |
