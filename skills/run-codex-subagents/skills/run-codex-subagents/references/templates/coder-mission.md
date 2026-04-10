# Coder Mission Template

Standard template for coding tasks: file creation, extraction, refactoring, build fixes.

## Template

```
## Context

{What exists today. What changed recently. What patterns the codebase uses.
Reference specific files the agent should read first.}

## Objective

{What to create or modify. Be concrete: file paths, function signatures,
class names. Describe the observable end-state, not the steps to get there.}

## Constraints

- {File scope: which files to touch, which to leave alone}
- {Pattern compliance: naming, architecture, imports}
- {Behavior preservation: what must NOT change}
- {Size limits: max lines per file if relevant}

## Definition of Done

All criteria must be met. Partial completion is not acceptable.

- [ ] {File exists at expected path}
- [ ] {File contains required exports/types/functions}
- [ ] {Build passes: `{build command}`}
- [ ] {Tests pass: `{test command}`}
- [ ] {No unrelated files modified}

## Verification Commands

Run these in order after implementation:

1. `wc -l {new_file}` — confirm file is non-empty
2. `{build_command}` — confirm project builds
3. `{test_command}` — confirm tests pass
4. `git diff --stat` — confirm only expected files changed
```

## Filled Example: SwiftUI Controller Extraction

```
## Context

ContentView.swift (4200 lines) contains NotchHoverStateMachine logic
mixed with UI code. The project follows the extraction pattern established
in Wave 4: each controller gets its own file under
FastNotch/Views/Notch/Controllers/, takes dependencies via init, and
exposes state via @Published properties.

Read these files first:
- FastNotch/Views/Notch/Controllers/BluetoothPopupController.swift (extraction pattern)
- FastNotch/ContentView.swift lines 1800-2100 (hover state machine code)

## Objective

Create FastNotch/Views/Notch/Controllers/NotchHoverStateMachine.swift
containing the NotchHoverStateMachine class extracted from ContentView.
The class should be an ObservableObject with @Published properties for
hoverState, isHovering, and hoverRegion. All hover-related methods
(handleMouseEntered, handleMouseExited, updateHoverRegion, resetHoverState)
move to this class.

## Constraints

- Only create NotchHoverStateMachine.swift — do NOT modify ContentView.swift
- Follow the same import pattern as BluetoothPopupController.swift
- Use `import SwiftUI` and `import Combine` only
- Class must be `final class NotchHoverStateMachine: ObservableObject`
- No force unwraps, no implicitly unwrapped optionals
- File must be under 300 lines

## Definition of Done

- [ ] FastNotch/Views/Notch/Controllers/NotchHoverStateMachine.swift exists
- [ ] File contains `final class NotchHoverStateMachine: ObservableObject`
- [ ] File contains @Published properties: hoverState, isHovering, hoverRegion
- [ ] File contains methods: handleMouseEntered, handleMouseExited, updateHoverRegion, resetHoverState
- [ ] `swift build` passes (file compiles in isolation)
- [ ] `wc -l` reports under 300 lines
- [ ] No other files modified (`git diff --stat` shows only the new file)

## Verification Commands

1. `wc -l FastNotch/Views/Notch/Controllers/NotchHoverStateMachine.swift`
2. `swift build 2>&1 | tail -5`
3. `grep -c '@Published' FastNotch/Views/Notch/Controllers/NotchHoverStateMachine.swift`
4. `git diff --stat`
```

## Usage Notes

- **Reasoning level:** `low` for single-file extraction, `medium` for multi-file refactoring.
- **Task type:** Always `coder`.
- **Context files:** Prepend the pattern-reference file (e.g., BluetoothPopupController.swift) if the agent needs to match an existing style.
- **CWD:** Set to the project root so all relative paths resolve correctly.
- **Labels:** Use `["wave-N", "domain"]` for tracking in parallel batches.
