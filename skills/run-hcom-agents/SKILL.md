---
name: run-hcom-agents
description: Use skill if you are orchestrating multiple AI coding agents via hcom — launching headless Claude or Codex agents, messaging between them, writing multi-agent workflow scripts, or applying patterns like worker-reviewer loops, ensemble consensus, and cascade pipelines.
---

# Run hcom Agents

Write and run hcom scripts that launch, coordinate, and manage multiple AI coding agents.

## Decision tree

1. **User wants to write a new hcom script** → Use the Script Template below
2. **User wants a specific pattern** (review loop, ensemble, etc.) → Read `references/patterns/tested-patterns.md`
3. **User wants Claude + Codex together** → Read `references/patterns/cross-tool.md`
4. **User wants advanced patterns** (reflexion, MoA, red/blue team) → Read `references/patterns/advanced-patterns.md`
5. **Script not working** → Read `references/gotchas.md`
6. **User wants to understand how hcom works** → Read `references/how-it-works.md`
7. **User needs command syntax** → Read `references/cli-reference.md`

## Script template (tested, production-ready)

Every hcom script must follow this exact structure:

```bash
#!/usr/bin/env bash
set -euo pipefail

LAUNCHED_NAMES=()
track_launch() {
  local names=$(echo "$1" | grep '^Names: ' | sed 's/^Names: //')
  for n in $names; do LAUNCHED_NAMES+=("$n"); done
}
cleanup() {
  for name in "${LAUNCHED_NAMES[@]}"; do
    hcom kill "$name" --go 2>/dev/null || true
  done
}
trap cleanup ERR

name_flag=""
task=""
while [[ $# -gt 0 ]]; do
  case "$1" in --name) name_flag="$2"; shift 2 ;; -*) shift ;; *) task="$1"; shift ;; esac
done
name_arg=""
[[ -n "$name_flag" ]] && name_arg="--name $name_flag"

thread="workflow-$(date +%s)"

# Launch, message, wait, cleanup — see patterns for specifics
```

## Required flags (every launch must include these)

| Flag | Why |
|------|-----|
| `--go` | Skips confirmation prompt. Without it, script hangs. |
| `--headless` | Runs agent as detached background process. Required for scripts. |
| `--tag X` | Groups agents for `@X-` routing. Without it, you must capture raw names. |
| `--hcom-prompt "..."` | Sets the agent's initial task. |

## Essential commands

### Launch
```bash
launch_out=$(hcom 1 claude --tag worker --go --headless \
  --hcom-prompt "Do X. Send result: hcom send \"@reviewer-\" --thread ${thread} --intent inform -- \"DONE: result\". Then: hcom stop" 2>&1)
track_launch "$launch_out"
name=$(echo "$launch_out" | grep '^Names: ' | sed 's/^Names: //' | tr -d ' ')
```

### Message
```bash
hcom send @worker- --thread "$thread" --intent request -- "do this task"
hcom send @"${name}" --thread "$thread" --intent inform -- "FYI: done"
hcom send -- "broadcast to all"
```

### Wait (replaces sleep — never use sleep in hcom scripts)
```bash
hcom events --wait 120 --sql "type='message' AND msg_thread='${thread}' AND msg_text LIKE '%DONE%'" $name_arg >/dev/null 2>&1
```

### Read another agent's work
```bash
hcom transcript @"${worker_name}" --full --detailed
```

### Cleanup
```bash
hcom kill "$name" --go    # Kill + close pane
hcom kill all --go        # Kill everything
```

## Timing (measured on real tests)

| Operation | Claude | Codex |
|-----------|--------|-------|
| Launch to ready | 3-5s | 5-10s |
| Message delivery | under 1s | 1-3s |
| Full 2-agent round-trip | 15-25s | 25-40s |

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Script hangs forever | Missing `--go` on launch or kill |
| Agent not receiving messages | Check `hcom list` — agent may have stopped or not bound yet |
| Codex gets stale_cleanup | Wait: `hcom events --wait 30 --idle "$codex_name"` before sending |
| Wrong agent targeted | Use `@tag-` prefix, not raw 4-letter name |
| Messages leaking between workflows | Always use `--thread` for isolation |
| LIKE matching surprises | `'%APPROVED%'` matches `"approved":true` in JSON — this is fine |

## Guardrails

- Never use `sleep` — use `hcom events --wait` or `hcom listen`
- Never send to agents before they are ready — wait for idle or batch launch
- Never skip `--go` — scripts hang waiting for confirmation
- Never hardcode agent names — parse from `Names:` line in launch output
- Never skip `--thread` — messages leak across workflows without it
- Always set `trap cleanup ERR` — orphan agents waste resources
- Always use `hcom kill` (not `stop`) for script cleanup — kill closes the pane

## Reference files

| File | When to read |
|------|-------------|
| `references/how-it-works.md` | Understanding hcom delivery pipeline, hooks, identity, bootstrap, relay |
| `references/cli-reference.md` | Complete hcom CLI command reference with all flags |
| `references/patterns/tested-patterns.md` | 6 tested multi-agent patterns with full scripts and real event JSON |
| `references/patterns/cross-tool.md` | Claude + Codex + Gemini + OpenCode collaboration details |
| `references/patterns/advanced-patterns.md` | 10 advanced patterns from 35-repo research (reflexion, MoA, red/blue team, etc.) |
| `references/gotchas.md` | Debugging: timing, stale agents, Codex binding, message delivery |
| `references/scripts/basic-messaging.sh` | Tested: two agents exchange messages |
| `references/scripts/review-loop.sh` | Tested: worker-reviewer feedback loop |
| `references/scripts/cross-tool-duo.sh` | Tested: Claude architect + Codex engineer |
| `references/scripts/ensemble-consensus.sh` | Tested: 3 independent agents + judge |
| `references/scripts/cascade-pipeline.sh` | Tested: sequential plan then execute |
| `references/scripts/codex-worker.sh` | Tested: Codex codes, Claude reviews transcript |
