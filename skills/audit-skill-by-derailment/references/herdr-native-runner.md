# Herdr Native Runner & CLI Orchestration Guide

Self-contained operational manual for launching, controlling, monitoring, and harvesting AI agent panes via the `herdr` CLI without requiring an external `herdr` skill installation.

---

## 1. Pre-Flight Environment & Session Verification

Herdr communicates with the active session over a local UNIX socket. Before running control commands, verify Herdr environment readiness:

```bash
# Verify running inside a Herdr-managed environment
test "${HERDR_ENV:-}" = 1 || { echo "Warning: HERDR_ENV is not 1. Verifying socket connectivity..."; }

# Check server connectivity and active workspaces
herdr status client
herdr workspace list
```

If `herdr` is not in `PATH`, verify installed location at `~/.cargo/bin/herdr` or `/usr/local/bin/herdr`.

---

## 2. Workspace & Tab Lifecycle Management

### List Active Workspaces & Panes
```bash
# List all workspaces with active tab IDs and agent status
herdr workspace list

# List all panes across workspaces or for a specific workspace (e.g. w2N)
herdr pane list --workspace w2N

# List all recognized running agents and their state
herdr agent list
```

### Create a Dedicated Workspace
```bash
# Create a fresh workspace for a skill audit run
herdr workspace create --label "skill-audit-lab"
```

### Create a Tab & Resolve its Pane ID
Creating a tab automatically provisions a terminal pane:
```bash
# Create a tab in workspace w2N without stealing terminal focus
herdr tab create --workspace w2N --label "perfume-take" --cwd "/Users/mac/dev/skill-flow-video-director" --no-focus
```

**JSON Output Resolution:**
```json
{
  "id": "cli:tab:create",
  "result": {
    "tab": { "id": "w2N:tP", "label": "perfume-take" },
    "pane": { "id": "w2N:pP" }
  }
}
```
Extract the pane ID using `jq`:
```bash
PANE_ID=$(herdr tab create --workspace "$WS_ID" --label "$LABEL" --cwd "$CWD" --no-focus | jq -r '.result.pane.id // .result.tab.id')
```

---

## 3. Launching Worker Agents (`herdr agent start`)

Herdr can initialize various agent engines directly in an idle terminal pane:

```bash
# Start an Antigravity CLI (Gemini) agent in an existing pane
herdr agent start "agent-aether" --kind agy --pane w2N:pP

# Start Claude Code in a pane
herdr agent start "agent-claude" --kind claude --pane w2N:pQ

# Start Codex in a pane
herdr agent start "agent-codex" --kind codex --pane w2N:pR
```

Supported `--kind` values: `agy`, `claude`, `codex`, `gemini`, `cursor`, `devin`, `cline`, `amp`, etc.

**Readiness Gate:** `herdr agent start` automatically waits until the agent engine displays its interactive prompt and reports `interactive_ready: true`.

---

## 4. Prompting Worker Agents (`herdr agent prompt`)

Send the mission or task prompt directly into the agent's interactive input:

```bash
# Submit a prompt and return immediately
herdr agent prompt w2N:pP "Execute Act 1 perfume luxury reel using flow-video-director skill."

# Submit a prompt and wait until the agent finishes (synchronous)
herdr agent prompt w2N:pP "Run video critique in AI Studio" --wait
```

---

## 5. Detecting Task Completion (`herdr agent wait`)

To orchestrate multi-agent or two-tier workflows asynchronously, monitor the agent until it enters an `idle`, `done`, or `blocked` state:

```bash
# Wait for the agent to complete work (matches idle, done, or blocked by default)
herdr agent wait w2N:pP --timeout 300000

# Wait specifically for 'done' or 'idle'
herdr agent wait w2N:pP --until done --until idle --timeout 180000
```

### Fallback Polling Loop (via `herdr agent list`)
If running in a shell without direct wait signals:
```bash
wait_for_agent() {
  local target_pane="$1"
  local max_seconds="${2:-300}"
  local elapsed=0

  while [ "$elapsed" -lt "$max_seconds" ]; do
    local status
    status=$(herdr agent list | jq -r --arg p "$target_pane" '.result.agents[] | select(.pane_id == $p) | .agent_status')
    
    if [ "$status" = "done" ] || [ "$status" = "idle" ]; then
      echo "Agent on pane $target_pane finished with status: $status"
      return 0
    elif [ "$status" = "blocked" ]; then
      echo "Agent on pane $target_pane is blocked (awaiting user input or approval)"
      return 2
    fi

    sleep 5
    elapsed=$((elapsed + 5))
  done

  echo "Timeout waiting for agent on pane $target_pane after ${max_seconds}s"
  return 1
}
```

---

## 6. Capturing Terminal Scrollback (`herdr pane read`)

Terminal scrollback provides the physical, unedited record of agent execution.

```bash
# Read recent unwrapped scrollback (soft wraps re-joined for clean parsing)
herdr pane read w2N:pP --source recent-unwrapped --lines 500

# Read current visible viewport snapshot
herdr pane read w2N:pP --source visible

# Read raw detection snapshot
herdr pane read w2N:pP --source detection
```

**Why `recent-unwrapped` is Mandatory:**
Standard terminal width wraps long commands (e.g., `node scripts/flow-render.mjs --prompt "..." --resolution 720p`). `recent-unwrapped` reconstructs the original contiguous strings, preventing broken regexes and incomplete JSON delimiters.

---

## 7. Keystroke Injection & Interactivity (`send-keys`)

Send special control keys to active agent terminals:

```bash
# Toggle Antigravity CLI (AGY) verbose mode (expands tool calls & thoughts)
herdr pane send-keys w2N:pP ctrl+o

# Send Escape to dismiss open menus or backdrops
herdr pane send-keys w2N:pP esc

# Send Enter or Cancel
herdr pane send-keys w2N:pP enter
herdr pane send-keys w2N:pP ctrl+c
```

---

## 8. Teardown & Lifecycle Cleanup

When an audit is complete and all evidence has been gathered and merged:

```bash
# Close a finished tab
herdr tab close w2N:tP

# Close a pane
herdr pane close w2N:pP
```
