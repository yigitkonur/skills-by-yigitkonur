# Quick Diagnostic Template

Template for single-command checks. Minimal prompt, always low reasoning, fast turnaround.

## Template

```json
{
  "prompt": "{command} and report the output",
  "cwd": "{project_root}",
  "task_type": "general",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 30000
}
```

That's it. No mission protocol, no DoD, no context files. The task runs one command and returns the result.

## Examples

### Line count

```json
{
  "prompt": "Run `wc -l FastNotch/ContentView.swift` and report the number",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "general",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 30000
}
```

### File search

```json
{
  "prompt": "Run `grep -rn 'TODO\\|FIXME' FastNotch/ --include='*.swift'` and report all matches",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "general",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 30000
}
```

### Build check

```json
{
  "prompt": "Run `swift build 2>&1` and report whether it succeeded. If it failed, list every error with file path and line number.",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "general",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 60000
}
```

### Test failures

```json
{
  "prompt": "Run `swift test 2>&1` and report only the failures. For each failure: test name, file, line, error message.",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "tester",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 120000
}
```

### Git status

```json
{
  "prompt": "Run `git status` and `git diff --stat` and report what files are modified, added, and untracked.",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "general",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 30000
}
```

### Dependency check

```json
{
  "prompt": "Run `swift package show-dependencies` and list all direct dependencies with their versions.",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "general",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 60000
}
```

### Disk usage

```json
{
  "prompt": "Run `find . -name '*.swift' | xargs wc -l | sort -rn | head -20` and report the 20 largest Swift files.",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "general",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 30000
}
```

### Environment info

```json
{
  "prompt": "Report: Swift version (`swift --version`), Xcode path (`xcode-select -p`), and macOS version (`sw_vers`).",
  "cwd": "/Users/me/dev/fast-notch",
  "task_type": "general",
  "reasoning": "gpt-5.4(low)",
  "timeout_ms": 30000
}
```

## Rules

1. **Always `low` reasoning.** If the task needs more than low, it's not a quick diagnostic — use the coder or research template instead.
2. **Always set `timeout_ms`.** 30s for fast commands, 60s for builds, 120s for test suites.
3. **Task type is usually `general`.** Exception: use `tester` for test execution to get the test-optimized profile.
4. **No labels needed** unless you're batching multiple diagnostics together.
5. **No context files.** Diagnostics read nothing — they run commands.
6. **Prompt is the command plus "report the output."** Don't overthink it.
7. **One concern per diagnostic.** Don't combine "check build AND run tests AND count lines" — spawn separate tasks.

## When to Promote

If you catch yourself writing a 5-line prompt for a "diagnostic," stop. Promote to:
- **Coder template** if the task involves creating or modifying files
- **Research template** if the task involves reading multiple files and synthesizing findings
- **Test runner template** if the task involves running and analyzing a full test suite
