# Task Types

Route every task to the right `task_type`. The type controls which Codex profile handles execution and what tooling is available.

## The Five Types

### coder (default)

File creation, modification, extraction, refactoring, build fixes. The agent has full file-system and shell access.

**Route here when:**
- Creating new files from scratch
- Extracting code from one file into another
- Refactoring (rename, restructure, split)
- Fixing build or compile errors
- Implementing features from a spec
- Writing migrations, configs, manifests

**Examples:**
```
"Extract NotchHoverStateMachine from ContentView.swift into its own file"
"Create src/utils/debounce.ts with generic debounce function and tests"
"Fix the build error in Package.swift — missing target dependency"
"Refactor AuthService to use async/await instead of callbacks"
```

### tester

Running test suites, writing test cases, generating coverage reports. Optimized for test-execute-report cycles.

**Route here when:**
- Running existing test suites
- Writing new test files
- Checking test coverage
- Verifying a fix doesn't break anything

**Examples:**
```
"Run swift test and report all failures with file paths"
"Write unit tests for MusicHoverController covering play/pause/skip"
"Run pytest with coverage and report any files below 80%"
"Execute the full CI test matrix and summarize results"
```

### planner

Decomposing features into tasks, creating implementation plans, analyzing dependencies. Output is structured text, not code.

**Route here when:**
- Breaking a feature into sub-tasks
- Creating wave-based execution plans
- Analyzing file dependencies before refactoring
- Estimating effort or ordering work

**Examples:**
```
"Decompose the plugin architecture migration into ordered tasks"
"Create a 5-wave plan for splitting ContentView.swift (4200 lines)"
"Analyze which files depend on NotchViewModel and order the extraction"
"Plan the database migration from SQLite to PostgreSQL in safe steps"
```

### researcher

Reading code, understanding architecture, tracing data flows, auditing patterns. Output is a structured report with file paths and line numbers.

**Route here when:**
- Understanding how a subsystem works
- Auditing files for size, complexity, or patterns
- Tracing a call chain from entry to exit
- Finding all usages of a symbol or pattern

**Examples:**
```
"Read every file under FastNotch/Views/ and report which exceed 300 lines"
"Trace the haptic feedback flow from mouse event to NSHapticFeedbackManager"
"Find all @Published properties in the codebase and list their owners"
"Audit the auth module for hardcoded secrets or credentials"
```

### general

Anything that doesn't fit the above. Shell commands, file listing, environment checks, miscellaneous operations.

**Route here when:**
- Running arbitrary shell commands
- Listing or counting files
- Checking environment configuration
- One-off operations that aren't coding, testing, or research

**Examples:**
```
"List all TODO/FIXME comments in the project with file paths"
"Count lines of code per directory and report the top 10"
"Check which Swift version is active and report Xcode path"
"Download the latest schema from the API endpoint and save to schemas/"
```

## Decision Shortcut

```
Does it produce or modify source code?  → coder
Does it run or write tests?             → tester
Does it output a plan or task list?     → planner
Does it read/analyze without changing?  → researcher
None of the above?                      → general
```

## Reasoning Level by Type

| Type | Typical reasoning | Why |
|---|---|---|
| coder | `low` for simple, `medium` for multi-file | Code tasks are procedural |
| tester | `low` always | Run command, capture output |
| planner | `medium` | Needs to reason about dependencies |
| researcher | `low` to `medium` | Read + summarize is straightforward |
| general | `low` | Usually a single command |

## Gotcha: Don't Over-Route

If a task is "write tests and run them", that's `tester` — not two tasks. If a task is "read the file, then refactor it", that's `coder` — the reading is incidental. Route by the **primary deliverable**, not the first step.
