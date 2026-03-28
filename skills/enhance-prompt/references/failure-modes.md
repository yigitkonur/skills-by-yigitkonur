# Common Agent Failure Modes

Predict these before they happen and inject pre-emptions into the enhanced prompt.

## 1. The Infinite Loop

**What happens:** Agent keeps working without converging. Rewrites, re-tests, re-refactors endlessly.
**Cause:** No halt condition or done signal.
**Pre-empt:** Always add: "You're done when [specific condition]. If you've attempted 3 approaches and none work, stop and explain what you tried."

## 2. Scope Creep

**What happens:** User asks for one thing, agent "improves" ten surrounding things.
**Cause:** Agent optimizes for perceived code quality, not task completion.
**Pre-empt:** "Only modify files directly related to [task]. Do not refactor, add docstrings, or reorganize anything else."

## 3. The Guess-and-Go

**What happens:** Agent encounters ambiguity (which API version? which database?) and guesses instead of asking.
**Cause:** No halt condition for uncertainty.
**Pre-empt:** "If [specific ambiguity] is unclear, stop and ask. Don't assume."

## 4. The Kitchen Sink

**What happens:** Agent adds error handling, logging, type annotations, comments, tests, docs — everything — when asked for a simple change.
**Cause:** Training bias toward "comprehensive" responses.
**Pre-empt:** "Minimal viable change. No extras unless explicitly requested."

## 5. The Framework Astronaut

**What happens:** Agent creates abstractions, factories, dependency injection — for a 20-line script.
**Cause:** Training on enterprise code.
**Pre-empt:** "This is a [simple script / one-off utility]. Keep it flat and direct. Three lines of duplicate code is better than an abstraction."

## 6. The Stale Context

**What happens:** Agent acts on outdated information about the codebase.
**Cause:** Long context, old file reads cached.
**Pre-empt:** "Re-read [file] before modifying it — it may have changed since you last saw it."

## 7. The Phantom Dependency

**What happens:** Agent installs a package or imports a module that doesn't exist or isn't appropriate.
**Cause:** Hallucination of package names from training data.
**Pre-empt:** "Use only existing dependencies from package.json. If you need a new package, ask first."

## 8. The Wrong Starting Point

**What happens:** Agent starts modifying files before understanding the architecture.
**Cause:** No "orient first" instruction.
**Pre-empt:** "Before writing code, read [key files] to understand the existing patterns."

## 9. The Forgotten Backward Compatibility

**What happens:** Agent changes a public API or interface, breaking callers.
**Cause:** Not thinking about consumers.
**Pre-empt:** "This [function/endpoint/type] is used by [other modules/external consumers]. Changes must be backward-compatible."

## 10. The Test Theater

**What happens:** Agent writes tests that always pass (testing implementation details, mocking everything).
**Cause:** Optimizing for "tests exist" rather than "tests catch bugs."
**Pre-empt:** "Write tests that would FAIL if the feature is broken. Test behavior, not implementation. Minimize mocking."
