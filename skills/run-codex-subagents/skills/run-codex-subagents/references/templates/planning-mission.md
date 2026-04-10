# Planning Mission Template

Template for decomposition tasks: breaking features into ordered tasks with dependencies, file paths, and per-task DoD.

## Template

```
## Context

{What needs building and why. What already exists. What the end-state
looks like at a high level. Reference any specs, PRs, or prior work.}

## Objective

Produce an implementation plan as a numbered task list. Each task must
be independently executable by a Codex coding agent. The plan is the
deliverable — do not implement anything.

## Constraints

- Task granularity: each task should take 1-3 minutes for a coding agent
- Each task must specify: target file paths, what to create/modify, DoD
- Dependencies between tasks must be explicit
- Group tasks into waves (parallel batches)
- No task should modify more than 3 files
- {Additional project-specific constraints}

## Output Format

### Overview
{1-2 sentence summary of the plan}

### Wave 1: {wave theme}
No dependencies — all tasks run in parallel.

**Task 1.1: {short title}**
- Files: {create/modify which files}
- Action: {what the agent does}
- DoD: {binary checklist}
- Reasoning: low

**Task 1.2: {short title}**
- Files: ...
- Action: ...
- DoD: ...
- Reasoning: low

### Wave 2: {wave theme}
Depends on: Wave 1 complete.

**Task 2.1: {short title}**
- Files: ...
- Action: ...
- DoD: ...
- Reasoning: medium

### Execution Notes
- {Risk areas, rollback strategy, verification between waves}
```

## Filled Example: Plan Wave 5 File Splits

```
## Context

Waves 1-4 extracted 7 controllers from ContentView.swift, reducing it
from 4200 to 2800 lines. The remaining code contains 3 large sections:
overlay transition logic (L400-L850), closed chin presentation (L1200-L1600),
and the window coordinator (L1900-L2400). Each needs extraction to hit
the 400-line target.

Read these files to understand current state:
- FastNotch/ContentView.swift (the file to decompose)
- FastNotch/Views/Notch/Controllers/ (existing extraction pattern)

## Objective

Produce a wave-based implementation plan to extract the 3 remaining
large sections from ContentView.swift. Each extraction follows the
established pattern: new file under Controllers/, ObservableObject class,
@Published properties, dependency injection via init.

## Constraints

- Each task targets exactly 1 new file
- No task modifies ContentView.swift (wiring happens in a separate wave)
- Follow the naming convention: {Feature}Controller.swift
- Each extracted file must be under 300 lines
- Build must pass after each wave independently

## Output Format

### Overview
3-wave plan: extract files (Wave 1), wire into ContentView (Wave 2),
verify and clean up (Wave 3).

### Wave 1: Extract controllers
No dependencies.

**Task 1.1: Extract OverlayTransitionController**
- Files: create FastNotch/Views/Notch/Controllers/OverlayTransitionController.swift
- Action: Extract overlay transition logic from ContentView L400-L850
- DoD:
  - [ ] File exists with `final class OverlayTransitionController: ObservableObject`
  - [ ] Contains animateOverlayIn, animateOverlayOut, resetOverlayState methods
  - [ ] `swift build` passes
  - [ ] Under 300 lines
- Reasoning: low

**Task 1.2: Extract ClosedChinPresenter**
- Files: create Controllers/ClosedChinPresenter.swift
- Action: Extract from ContentView L1200-L1600
- DoD: file exists, builds, under 300 lines
- Reasoning: low

**Task 1.3: Extract WindowCoordinator**
- Files: create Controllers/WindowCoordinator.swift
- Action: Extract from ContentView L1900-L2400
- DoD: file exists, builds, under 300 lines
- Reasoning: low

### Wave 2: Wire into ContentView (depends on Wave 1)

**Task 2.1: Wire all 3 controllers into ContentView**
- Files: modify ContentView.swift
- Action: Replace extracted sections with @StateObject controller references
- DoD: builds, ContentView under 1500 lines, controllers used
- Reasoning: medium

### Wave 3: Verify (depends on Wave 2)

**Task 3.1: Run full test suite**
- Action: `swift test`, report results
- DoD: all existing tests pass
- Reasoning: low

### Execution Notes
- Wave 1 failures are isolated — retry only the failed task
- Verify files exist between waves: `ls Controllers/`
- Wave 2 is highest risk — back up with `git stash` first
```

## Usage Notes

- **Reasoning level:** `medium` — planning requires understanding dependencies.
- **Task type:** Always `planner`.
- **Context files:** Prepend the file being decomposed if it's under 500 lines. For larger files, let the agent read it.
- **CWD:** Project root.
- **Labels:** `["planning"]` — planning tasks are usually singular, not batched.
- **Follow-up:** After receiving the plan, execute it using the batch-wave template.
