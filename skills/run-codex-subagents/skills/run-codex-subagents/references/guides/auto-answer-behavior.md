# Auto-Answer Behavior: How Questions Get Answered Without You

When a Codex agent calls `request_user_input`, the daemon auto-selects the first (recommended) option instantly. You never see the question. The agent continues as if you answered. Understanding this mechanism is critical for designing prompts that don't derail.

## The Mechanism

1. Agent reaches a decision point and calls `request_user_input`
2. daemon receives the question with answer options
3. Daemon immediately returns the first option (index 0) as the answer
4. Agent receives the answer and continues execution
5. An `AUTO` line appears in the timeline log

Response format sent back to the agent:
```json
{
  "answers": {
    "<questionId>": {
      "answers": ["<label of first option>"]
    }
  }
}
```

## Why Auto-Answer Exists

The Codex `request_user_input` tool has a 4-second timeout. The orchestrator round-trip (agent → daemon → CLI → you → CLI → daemon → agent) takes 5-30 seconds minimum. The timeout would ALWAYS fire before a human could respond.

Auto-answer is the only way to keep agents running. The alternative is every question kills the agent.

## What Triggers Questions

Agents ask questions when they encounter ambiguity. Common triggers:

- **"Apply these changes?"** — Agent wants confirmation before writing files
- **"Which pattern should I use?"** — Multiple valid approaches exist
- **"This file is large. Read the whole thing?"** — Agent is being cautious about token usage
- **"Create this new directory?"** — Agent wants permission for filesystem changes
- **"The build failed. Should I try to fix it?"** — Agent hit an error and isn't sure whether to continue

## The AUTO Line in Timeline

```
17:05:30.300 AUTO "Apply changes to ContentView.swift? → Yes (Recommended)"
```

The text after `→` is what was auto-selected. This is the label of the first option the agent provided.

## Designing Prompts for Correct Auto-Answers

Since the first option is always selected, you control auto-answer behavior through prompt design.

### Make the right answer obvious

Bad prompt:
```
Extract the music hover handling. Use whatever pattern you think is best.
```

Agent might ask: "Should I use (a) closures or (b) delegate pattern?" If closures is listed first, it gets selected even if delegate is correct.

Good prompt:
```
Extract the music hover handling using the delegate pattern 
(same as BluetoothPopupController).
```

Agent won't ask because the decision is already made.

### Eliminate ambiguity preemptively

Every question an agent MIGHT ask is a potential wrong auto-answer. For each, either:
1. Answer it in the prompt (preferred)
2. Make the first option the correct one (requires knowing what options the agent will present)

Since you can't always predict option ordering, option 1 is almost always better.

### Common questions and how to prevent them

| Question Agent Asks | Prevention |
|---|---|
| "Which pattern?" | Specify the pattern in the prompt |
| "Apply changes?" | Add "Apply all changes without confirmation" to developer_instructions |
| "Create directory?" | Specify the directory path explicitly |
| "Fix build errors?" | Add "If the build fails, fix all errors" to the prompt |
| "This file has X lines, read it?" | Specify exactly which files to read |

## When Auto-Answer Goes Wrong

Signs that auto-answer chose incorrectly:
- Agent takes an unexpected approach after an AUTO event
- Build fails because agent used the wrong pattern
- Agent creates files in the wrong location
- Agent modifies files it shouldn't have

### Steering After Wrong Auto-Answer

Wait for the task to finish (or cancel if needed), then steer with `task steer`:

```bash
# Wait for completion
cli-codex-subagent task wait tsk_abc123

# Steer: correct the wrong choice
cat > /tmp/correction.md << 'EOF'
You used the closures pattern but this codebase uses delegates everywhere.
Undo your last changes and redo using the delegate approach from BluetoothPopupController.swift.
EOF
cli-codex-subagent task steer tsk_abc123 /tmp/correction.md --follow
```

Note: `task steer` only works on tasks that have reached a terminal state (completed or failed). If the task is still running and you need to redirect it mid-flight, you must cancel and re-run.

If the task produced corrupt output, recover partial work or re-spawn with a better prompt.

## The 4-Second Timeout Detail

The exact flow:

```
T+0.000s  Agent calls request_user_input
T+0.050s  daemon receives the question
T+0.100s  daemon sends auto-answer back
T+0.150s  Agent receives answer
           (Agent continues working normally)
```

But if the auto-answer mechanism fails for any reason:

```
T+0.000s  Agent calls request_user_input
T+4.000s  Codex timeout fires
T+4.001s  Process begins shutdown
T+4.050s  EXIT
```

The 4-second timeout is the hard ceiling. If auto-answer doesn't arrive within 4 seconds (network latency, server error, deserialization failure), the process dies.

## dynamic_tool Pauses

There is one exception to auto-answering: `dynamic_tool` invocations actually pause and wait for the orchestrator. These are different from `request_user_input` — they represent tool calls that the agent is making, not questions it's asking.

If you see a task stuck in `input_required` status from a `dynamic_tool` call, use `request answer <reqId>` to provide the tool result.

## Testing Auto-Answer Behavior

To verify your prompt eliminates questions:

1. Spawn the task
2. Monitor the timeline
3. Count AUTO events
4. If AUTO events appear → the agent asked questions you didn't preempt
5. Check what was auto-selected
6. If wrong → improve the prompt to eliminate that question
7. Re-spawn and verify zero AUTO events

Zero AUTO events is the goal. Every question the agent asks is a failure of prompt design.

## Real Example

### Before (bad prompt)
```
Refactor the hover handling in ContentView.
```

Timeline:
```
STARTED → CMD(read) → AUTO("Use ObservableObject? → Yes") → 
THINK → AUTO("Create new file? → Yes") → CMD(create) →
AUTO("Naming: HoverManager or HoverController? → HoverManager") →
WRITE → EXIT
```

Three AUTO events. The naming one chose "HoverManager" but the codebase convention is "Controller". Agent created a file with wrong naming.

### After (good prompt)
```
Extract hover handling from ContentView into HoverController.swift in
FastNotch/Views/Notch/Controllers/. Follow the same pattern as
BluetoothPopupController.swift. Use @Published properties, not 
ObservableObject protocol conformance. Create the file directly
without confirmation.
```

Timeline:
```
STARTED → CMD(read) → CMD(read) → THINK → WRITE → CMD(edit) → CMD(build) → EXIT
```

Zero AUTO events. Every decision was preempted by the prompt.
