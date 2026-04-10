# Partial Work Recovery: Salvaging Agent Work After Process Death

This is the most important operational pattern in the Codex workflow. When an agent dies mid-task, it has usually done 60-95% of the work. The files are on disk. Recovery is almost always faster than re-spawning.

## Why Agents Die Mid-Task

- Process timeout (reasoning took too long)
- Auth token expiration
- Shared-process death (another parallel task caused exit)
- OOM on large file operations
- Approval gate timeout (agent asked a question, 4s timeout hit)

In every case, the agent was writing files to the working directory before it died. Those files persist.

## Recovery Flowchart

```
Agent died (EXIT in timeline)
  │
  ├─ 1. Check: rtk git status
  │     Are there new/modified files?
  │     → NO → Nothing to recover. Re-spawn.
  │     → YES ↓
  │
  ├─ 2. Check: Do the new files look complete?
  │     rtk wc -l <new_files>
  │     Read key files to check for truncation
  │     → TRUNCATED → Delete truncated files, re-spawn with narrower scope
  │     → COMPLETE ↓
  │
  ├─ 3. Try build: rtk xcodebuild ... 2>&1 | tail -30
  │     → BUILD SUCCEEDED → Skip to step 5
  │     → BUILD FAILED ↓
  │
  ├─ 4. Fix build errors yourself
  │     Usually 1-3 errors: missing import, wrong type, stale reference
  │     Fix each one. Rebuild after each fix.
  │     → STILL FAILING after 3 fixes → Re-spawn with better prompt
  │     → BUILD SUCCEEDED ↓
  │
  ├─ 5. Run tests: rtk swift test (or verification commands)
  │     → PASS → Commit the agent's work + your fixes
  │     → FAIL ↓
  │
  ├─ 6. Fix test failures
  │     Usually 1-2 failures from incomplete wiring
  │     → FIXED → Commit
  │     → TOO MANY FAILURES → Re-spawn
  │
  └─ 7. Commit with attribution
        "W4-13a: Extract BluetoothPopupController from ContentView"
        (Same message the agent would have used)
```

## Real Example: W4-13a BluetoothPopupController

### What happened
Agent was spawned to extract Bluetooth popup handling from ContentView into a new BluetoothPopupController. Timeline showed:

```
STARTED → THINK → CMD(read files) → THINK → CMD(create file) → CMD(edit ContentView) → 
CMD(edit pbxproj) → THINK → EXIT(approval_gate_timeout)
```

The agent created the file, edited ContentView, updated the project file, then died when it tried to ask a question about a naming choice and hit the 4-second timeout.

### Recovery steps

1. `rtk git status` showed:
   - New: `FastNotch/Views/Notch/Controllers/BluetoothPopupController.swift` (206 lines)
   - Modified: `FastNotch/ContentView.swift`
   - Modified: `FastNotch.xcodeproj/project.pbxproj`

2. Read BluetoothPopupController.swift — complete, well-structured, followed the pattern.

3. Build attempt:
   ```
   error: use of unresolved identifier 'bluetoothPopupController'
   error: type 'BluetoothPopupController' has no member 'showPopup'
   ```

4. Two fixes:
   - ContentView needed `let bluetoothPopupController: BluetoothPopupController` property declaration (agent wrote the init but forgot the stored property)
   - Method was named `presentPopup` not `showPopup` (agent's ContentView edit used the old name)

5. Build succeeded after fixes. Manual testing confirmed popup behavior identical.

6. Committed: `W4-13a: Extract BluetoothPopupController from ContentView`

**Agent did 95% of the work. Recovery took 4 minutes. Re-spawning would have taken 5-10 minutes plus risked another death.**

## What to Check in Each File Type

### New Swift files
- Is the file complete? (has closing brace, all methods have bodies)
- Are imports correct? (SwiftUI, AppKit, Combine as needed)
- Does it follow the established pattern? (delegate protocol, init with dependencies)

### Modified ContentView.swift
- Were the old code sections removed or just commented out?
- Are the new delegation calls wired up?
- Are stored properties declared for the new controller?

### Modified project.pbxproj
- Is the new file in the correct group?
- Are both PBXBuildFile and PBXFileReference entries present?
- Is the file in the Sources build phase?

If pbxproj is corrupted (merge conflict markers, duplicate entries), it's often faster to:
1. Revert the pbxproj: `rtk git checkout -- FastNotch.xcodeproj/project.pbxproj`
2. Add the file through Xcode or manually with a known-good pbxproj edit pattern

## When NOT to Recover

- Agent wrote fewer than 20 lines total → re-spawn, not worth fixing
- Agent created files but never edited the source → it was still in the reading phase
- Multiple files are truncated mid-line → process died during write, data is corrupt
- The approach the agent took is fundamentally wrong → re-spawn with a clearer prompt

## Recovery vs Re-Spawn Decision Matrix

| Situation                                    | Action    |
|----------------------------------------------|-----------|
| New file complete, 1-3 build errors          | Recover   |
| New file complete, build passes              | Commit    |
| New file truncated                           | Re-spawn  |
| No new files, only partial edits             | Re-spawn  |
| Agent took wrong approach                    | Re-spawn  |
| 5+ build errors                              | Re-spawn  |
| Agent completed 80%+ but died at approval    | Recover   |

## Commit Messages for Recovered Work

Use the same commit message format as if the agent completed normally. The recovery fixes are trivial — the commit represents the agent's architectural work, not your 2-line fixes.

```
W4-13a: Extract BluetoothPopupController from ContentView
```

Not:
```
Fix partial work from failed Codex agent for bluetooth controller extraction
```

## Automation Opportunity

Before re-spawning a failed task, always run this check sequence:

```bash
# Quick partial-work check
rtk git status
rtk git diff --stat
# If new files exist:
rtk xcodebuild -scheme FastNotch -configuration Debug build 2>&1 | tail -5
```

If build succeeds with zero errors, you can commit immediately without reading a single file. The agent's work is complete — it just died before it could report success.
