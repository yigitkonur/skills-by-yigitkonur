# Developer Instructions: System-Level Text Injection for Codex Agents

The `developer_instructions` parameter injects text before the user prompt at system level. The agent sees it as environmental context, not task-specific direction. Use it for repo-wide conventions, safety rails, and behavioral defaults.

## How It Works

When you run a task with `developer_instructions` in the frontmatter:

```yaml
---
developer_instructions: "Always prefix shell commands with `rtk`. Read AGENTS.md before starting any task."
effort: low
---
Extract MusicHoverController from ContentView...
```

Or via CLI flag:

```bash
cli-codex-subagent run task.md --effort low
```

The agent receives:

```
[System-level context]
Always prefix shell commands with `rtk`. Read AGENTS.md before starting any task.

[User prompt]
Extract MusicHoverController from ContentView...
```

The developer instructions appear BEFORE the task prompt. They set the operating environment.

## What the Server Also Injects

Beyond your custom instructions, the daemon automatically injects a QUESTION POLICY that tells the agent when to ask questions vs decide independently. This policy is what makes auto-answer behavior predictable — the agent is instructed to only ask questions for truly ambiguous situations.

You don't need to include question-handling instructions in your developer_instructions. The server handles this.

## Good Uses

### Coding conventions
```
developer_instructions: "Prefix all shell commands with `rtk`. Use SwiftUI for views, not UIKit. Follow the delegate pattern for controller communication."
```

This ensures every agent in your fleet follows the same conventions without repeating them in every prompt.

### Safety rails
```
developer_instructions: "Never modify files outside FastNotch/. Never delete files. Never force-push."
```

Hard boundaries that should apply to ALL tasks, not just one.

### Repo contracts
```
developer_instructions: "Read AGENTS.md before starting. It contains file structure conventions and naming rules."
```

Points the agent to a ground-truth document that may be more current than your prompt.

### Build/test commands
```
developer_instructions: "Build with: xcodebuild -scheme FastNotch -configuration Debug build. Test with: swift test."
```

Every agent knows how to verify its work without you specifying it per task.

### File organization
```
developer_instructions: "New controllers go in FastNotch/Views/Notch/Controllers/. New tests go in Tests/FastNotchRuntimeTests/. Add new files to project.pbxproj."
```

## Bad Uses

### Task-specific instructions
```
# DON'T do this
developer_instructions: "Extract the music hover handling into MusicHoverController.swift"
```

This belongs in the prompt, not developer_instructions. Developer instructions are for cross-task concerns.

### Lengthy context dumps
```
# DON'T do this
developer_instructions: "Here is the full architecture of the app: [500 words of context]..."
```

Developer instructions consume token budget. Keep them short. Put detailed context in the task prompt or in a file the agent can read (like AGENTS.md).

### Contradicting the prompt
```
# DON'T do this
developer_instructions: "Use the singleton pattern for all controllers."
prompt: "Create MusicHoverController using dependency injection via init."
```

Agent will be confused. Developer instructions set defaults; prompts override for specific tasks.

## Token Budget Considerations

Developer instructions are injected at system level, which means they consume tokens from the agent's total budget. Every character counts.

**Keep instructions under 500 characters.** This is roughly 100-120 tokens, leaving the vast majority of budget for the actual task.

Good (87 chars):
```
Prefix commands with rtk. Read AGENTS.md first. New controllers go in Controllers/.
```

Bad (650 chars):
```
This is a macOS application built with SwiftUI and AppKit. The project uses a delegate pattern for communication between controllers and views. When you create new files, make sure to add them to the Xcode project file (project.pbxproj) using the PBXBuildFile and PBXFileReference sections. Always run the build after making changes to verify they compile correctly. Use xcodebuild with the FastNotch scheme...
```

The bad example wastes 150+ tokens on information that should be in the prompt or in AGENTS.md.

## Fleet Mode and Multi-Profile Setups

When running multiple CLI daemon instances (e.g., one for each project or reasoning level), the server adds a `[codex-worker-fleet]` sentinel to developer instructions. This marks the agent as part of a managed fleet, which affects:

- Logging behavior (fleet agents log to a shared directory)
- Session management (fleet agents can be batch-cancelled)
- Identity (fleet agents include the fleet ID in their output)

You don't need to add this manually. The server handles it. But if you see `[codex-worker-fleet]` in agent output, that's where it comes from.

## Composing Developer Instructions

For a typical project, your developer instructions should cover:

```
[Build tool] + [File conventions] + [Safety rails] + [Entry point doc]
```

Example:
```
rtk prefix for commands. Controllers in Controllers/. Tests in Tests/. Never modify Info.plist. Read AGENTS.md first.
```

That's 107 characters. Covers everything the agent needs as environmental context.

## Per-Task Override Pattern

Developer instructions are set per spawn, not globally. This lets you adjust for different task types:

```
# For extraction tasks
developer_instructions: "rtk prefix. Controllers in Controllers/. Read AGENTS.md. Build: xcodebuild -scheme FastNotch build."

# For test-writing tasks
developer_instructions: "rtk prefix. Tests in Tests/FastNotchRuntimeTests/. Test: swift test. Follow XCTest conventions."

# For documentation tasks
developer_instructions: "rtk prefix. Docs in docs/. Use markdown. No emoji."
```

Same project, different conventions per task type.

## Interaction With AGENTS.md

Many repos include an `AGENTS.md` (or `CLAUDE.md`, `CODEX.md`) that contains detailed instructions for AI agents. The ideal pattern:

- `developer_instructions`: Short, points to AGENTS.md → `"Read AGENTS.md first. rtk prefix."`
- `AGENTS.md`: Full conventions, file structure, patterns, examples
- `prompt`: Task-specific instructions

This three-layer approach keeps developer_instructions small, puts living documentation in a version-controlled file, and reserves the prompt for the actual task.

## Debugging Developer Instructions

If an agent isn't following your developer instructions:

1. Check that instructions are under 500 chars (may be truncated if too long)
2. Check for contradictions with the prompt
3. Check that the instruction is specific enough ("follow conventions" is vague; "delegate pattern for controllers" is specific)
4. Try making the instruction a prompt-level instruction instead (agents weight prompt text higher than system text for specific behaviors)
