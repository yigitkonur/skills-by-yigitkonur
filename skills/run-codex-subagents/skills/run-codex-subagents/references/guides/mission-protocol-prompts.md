# Mission Protocol Prompts: How to Brief a Codex Agent

The single biggest lever on agent success is prompt quality. A well-structured brief at reasoning level `low` outperforms a vague brief at `high` every time. This guide covers the MISSION_PROTOCOL format — a battle-tested structure for Codex agent briefs.

## Core Principles

1. **Gravity, not walls** — Pull the agent toward the right solution. Don't enumerate every wrong path.
2. **Ceilings, not floors** — Set maximum scope, not minimum effort. Agents are eager; constrain them.
3. **Outcomes, not procedures** — Describe what done looks like. Never write code in the brief.
4. **Front-load context** — The agent reads top-to-bottom. Put the most important context first.
5. **Never write code in the brief** — The moment you put a code snippet in the prompt, the agent copies it verbatim instead of thinking. Describe the structure in words.

## The Structure

### 1. Context Block

```
## Context

This codebase is a macOS notch utility app (SwiftUI + AppKit hybrid).
ContentView.swift is currently 2,100 lines and owns too many responsibilities.
Wave 3 extracted lifecycle management. Wave 4 is extracting UI controllers.

The pattern established in Wave 3: each controller is a standalone class that
receives dependencies via init, communicates back through a delegate protocol,
and lives in FastNotch/Views/Notch/Controllers/.

Files you MUST read before writing any code:
- FastNotch/Views/Notch/Controllers/BluetoothPopupController.swift (pattern reference)
- FastNotch/ContentView.swift (source of extraction — look for // MARK: - Music Hover)
- FastNotch/Managers/MusicManager.swift (dependency you'll need to understand)
```

What makes this work:
- **Why** this task exists (ContentView too large)
- **What came before** (Wave 3, other controllers)
- **What to know** (the established pattern)
- **Files to read** (specific, ordered, with hints about what to look for)
- **Mental model** (delegate pattern, standalone class)

### 2. Mission Objective

```
## Mission

Extract all music hover handling from ContentView into a new MusicHoverController class.

Observable end-state: ContentView no longer contains any music hover logic. A new
MusicHoverController.swift exists in Controllers/. The app builds and music hover
behavior is functionally identical.

Hard constraints:
- Follow the exact same pattern as BluetoothPopupController
- Do NOT change any user-facing behavior
- Do NOT modify any file outside FastNotch/

Known risks:
- MusicManager has @Published properties that ContentView observes directly.
  The controller must mediate these, not bypass them.
- The hover detection uses NSTrackingArea which needs careful lifecycle management.

Priority: correctness over completeness. If you can't extract 100%, extract what
you can cleanly and leave a // TODO for the rest.
```

What makes this work:
- **Observable outcome** — not "refactor music stuff" but "ContentView no longer contains music hover logic"
- **Hard constraints** — only things that would make the work wrong if violated
- **Known risks** — saves the agent from discovering these the hard way
- **Priority signal** — tells the agent what to optimize for when tradeoffs arise

### 3. Definition of Done (BSV)

```
## Definition of Done

- [ ] MusicHoverController.swift exists in FastNotch/Views/Notch/Controllers/
- [ ] MusicHoverController conforms to a delegate protocol for callbacks to ContentView
- [ ] ContentView instantiates MusicHoverController and uses it for all music hover logic
- [ ] No music hover logic remains in ContentView (no NSTrackingArea, no hover state)
- [ ] Project builds with zero errors (xcodebuild)
- [ ] MusicHoverController.swift is added to the Xcode project file (project.pbxproj)
```

Every item is:
- **Binary** — yes or no, no partial credit
- **Specific** — names the file, the pattern, the tool
- **Verifiable** — a third party could check each one

### 4. Verification Commands

```
## Verification

Run these in order. ALL must pass before you consider the task done:

1. `xcodebuild -scheme FastNotch -configuration Debug build 2>&1 | tail -20`
   Expected: BUILD SUCCEEDED
2. `grep -c "NSTrackingArea" FastNotch/ContentView.swift`
   Expected: 0
3. `grep -c "musicHover" FastNotch/ContentView.swift`
   Expected: only delegation calls, no logic
4. `wc -l FastNotch/Views/Notch/Controllers/MusicHoverController.swift`
   Expected: 100-300 lines
```

### 5. Failure Protocol

```
## If Things Go Wrong

- Build fails with missing imports → check that all dependencies are passed through init
- Build fails with pbxproj errors → you probably have a merge conflict in the project file; 
  add the file reference manually using the PBXBuildFile/PBXFileReference pattern from 
  BluetoothPopupController
- Hover behavior breaks → check that NSTrackingArea options match the original
- If you cannot complete the extraction cleanly → extract what you can, leave the rest
  in ContentView with a // MARK: - TODO: Move to MusicHoverController, and document 
  what blocked you
```

### 6. Handback Format

```
## When Done

Report back with:
1. Files created (with line counts)
2. Files modified (with summary of changes)
3. Verification command results
4. Any remaining TODOs or concerns
```

## Anti-Patterns in Prompts

### Too vague
> "Refactor the music hover stuff into its own controller"

Agent doesn't know: what pattern to follow, where to put it, what counts as "music hover stuff", how to verify.

### Too procedural
> "Step 1: Create MusicHoverController.swift. Step 2: Add these properties: ... Step 3: Copy lines 450-520 from ContentView..."

You're writing the code yourself with extra steps. The agent can't adapt when reality differs from your assumptions.

### Code in the brief
> "The controller should look like this: `class MusicHoverController { var hoverState: Bool ... }`"

Agent will copy this verbatim even if it's wrong. Describe the structure, don't implement it.

### Unbounded scope
> "Extract all the controllers from ContentView"

This is 7 tasks pretending to be one. Each extraction should be a separate spawn.

## Prompt Length Guidelines

- **Simple extraction**: 300-500 words. Context + objective + DoD.
- **Multi-file refactor**: 500-800 words. Add failure protocol and verification.
- **Architecture task**: 800-1200 words. Full MISSION_PROTOCOL.
- **Over 1200 words**: You're probably trying to do too much in one task. Split it.

## Template (Copy-Paste Starter)

```
## Context
[Why this task. What came before. Mental model.]

Files to read first:
- [pattern reference]
- [source of changes]
- [key dependencies]

## Mission
[One-sentence objective]

Observable end-state: [what the world looks like when done]

Hard constraints:
- [only things that make work WRONG if violated]

Known risks:
- [things the agent would otherwise discover the hard way]

## Definition of Done
- [ ] [Binary, Specific, Verifiable item]
- [ ] [Binary, Specific, Verifiable item]
- [ ] [Binary, Specific, Verifiable item]
- [ ] Project builds with zero errors

## Verification
[Commands to run, expected output]

## If Things Go Wrong
[Common failure modes and what to do]
```
