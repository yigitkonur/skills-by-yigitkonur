# Capture Modes

Choose the most deterministic screenshot path the project already supports.

## Preference order

1. **In-app or in-process snapshot automation**
   - Best when the app can switch its own state and render its own views without OS-level clicks.
   - Use this first for native macOS apps when you can edit the project.

2. **Built-in UI-test harness**
   - Best when XCTest or another UI-test runner already knows how to launch and navigate the app.
   - Prefer identifiers, predicates, and existence waits over coordinate clicks.

3. **Browser driver**
   - Use for Electron, hybrid, or browser-hosted app surfaces.
   - Pair this skill with `run-playwright` or `run-agent-browser` when you need live browser control.

4. **Accessibility or window-capture fallback**
   - Use only when no internal or test harness exists.
   - Call out the fragility: focus dependence, accessibility tree drift, OS permissions, and window ordering.

## Selection heuristics

Pick the first mode that:

- reaches the target state without manual user clicks
- produces a stable, rerunnable image artifact
- avoids focus stealing when a better option exists
- keeps the state transition understandable to the next developer

## What to inspect first

- docs in `README`, `docs/`, or `scripts/`
- UI-test targets or build scripts that mention `snapshot`, `screenshot`, `capture`, or `automation`
- app entrypoints with debug flags or automation modes
- existing diagnostics or hidden routes that already expose the target state
