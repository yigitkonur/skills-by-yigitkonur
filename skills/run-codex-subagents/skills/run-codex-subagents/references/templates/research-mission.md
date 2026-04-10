# Research Mission Template

Template for codebase exploration, auditing, and analysis tasks. Output is a structured report, not code changes.

## Template

```
## Context

{What we need to understand and why. What triggered this research.
What decisions depend on the findings.}

## Objective

{What the report should contain. Be specific about the deliverable format.
The agent's output IS the report — there are no file changes.}

## Scope

- Directories to explore: {list}
- File types to include: {glob patterns}
- Maximum files to read: {number, prevents runaway reads}
- Exclude: {directories or patterns to skip}

## Output Format

Report must follow this structure:

### {Section 1 title}
{What goes here — e.g., file path, line count, summary}

### {Section 2 title}
{What goes here}

### Recommendations
{Actionable next steps based on findings}

Include absolute file paths and line numbers for every claim.
```

## Filled Example: Audit Oversized Files

```
## Context

The ContentView.swift extraction is underway but we don't have a
complete picture of which files exceed the 400-line target. Before
planning Wave 5, we need a full inventory of oversized files to
prioritize the next round of extractions.

## Objective

Produce a report listing every Swift file in the project that exceeds
400 lines, sorted by line count descending. For each file, identify
the largest logical section (class, struct, enum, or extension) and
estimate how many extractable units it contains.

## Scope

- Directories to explore: FastNotch/, Sources/
- File types to include: *.swift
- Maximum files to read: 50
- Exclude: .build/, DerivedData/, Tests/

## Output Format

### Oversized Files (>400 lines)

| File | Lines | Largest section | Extractable units |
|---|---|---|---|
| {path} | {count} | {section name} (L{start}-L{end}) | {estimate} |

### Size Distribution

- Files > 1000 lines: {count}
- Files 400-1000 lines: {count}
- Files < 400 lines: {count}
- Total Swift files scanned: {count}

### Extraction Priority

Ordered list of recommended extractions:
1. {file} — {what to extract} — {estimated effort}
2. ...

### Recommendations

{What to do next based on findings}

Include absolute file paths and line numbers for every entry.
```

## Filled Example: Trace Data Flow

```
## Context

Haptic feedback triggers in several places but we don't have a map
of the full call chain. Need to understand every path from user
input to NSHapticFeedbackManager before refactoring the haptic system.

## Objective

Trace every code path that leads to a haptic feedback call. For each
path, document the trigger (mouse event, gesture, notification),
the intermediary functions, and the final haptic call with its
feedback pattern.

## Scope

- Directories: FastNotch/
- File types: *.swift
- Max files: 30
- Focus: Any file importing or referencing NSHapticFeedbackManager,
  HapticManager, or .haptic

## Output Format

### Call Chains

Chain 1: {trigger description}
  {file}:{line} → {function}
  {file}:{line} → {function}
  {file}:{line} → NSHapticFeedbackManager.perform({pattern})

Chain 2: ...

### Haptic Patterns Used

| Pattern | Call sites | Trigger |
|---|---|---|
| .alignment | {file}:{line}, {file}:{line} | hover enter |
| .levelChange | {file}:{line} | notch open |

### Recommendations

{Findings and suggested refactoring approach}
```

## Usage Notes

- **Reasoning level:** `low` for simple counts/audits, `medium` for flow tracing or architectural analysis.
- **Task type:** Always `researcher`.
- **Context files:** Usually not needed — the agent reads files itself. Exception: prepend a project map or directory listing if the codebase is large.
- **CWD:** Set to the project root.
- **Labels:** `["research", "domain"]` — research tasks rarely run in parallel waves but labeling helps track them on the scoreboard.
- **Timeout:** Research tasks may read many files. Allow 120-180s for thorough exploration.
