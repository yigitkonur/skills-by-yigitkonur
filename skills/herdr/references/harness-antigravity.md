# Antigravity workers

Read for AGY startup, delivery and recovery. AGY is a worker harness, never the
Advanced EM: a manager's incoming-message backlog can stall delegation.

## Startup and brief

Use the explicit profile in agent-profiles.md. Start interactively in a verified
shell pane; inspect native identity/readiness. Do not use print mode or change
account/proxy wrapper settings. `--model gemini-3.8-flash --effort high` is the
chosen default; listing suffix variants does not authorize changing it.

Every nontrivial new task (difficulty 2–5) starts:

```text
/teamwork-preview /herdr (/resolved/absolute/path/herdr/SKILL.md)
```

Difficulty 1 can start `/herdr (absolute path)` directly. Include authority,
checks and callback from prompt-and-messaging.md. `/teamwork-preview` is required
AGY prompt context, not an invitation to create an external EM or change the
assignment. Account for its internal agents when measuring capacity.

## Ready, busy and unknown

- Ready: a controller submits one brief with `herdr agent prompt TARGET TEXT
  --wait --timeout 30000`; monitor that existing submission. Worker callbacks
  always omit `--wait`.
- Busy: record the pending notice/task. Prefer a bounded wait for a ready composer
  before sending a new task; do not pile repeated briefs into the queue.
- Blocked: read visible dialog and resolve only an authorized choice.
- Unknown: check process-info and the visible screen. If and only if the expected
  AGY TUI has a clean input-ready composer, pane-level text plus Enter can be used.
  `pane run` is keystroke injection, not a shell execution API.

## Escape is an intervention, not a scheduler

Do not use Escape merely to make a callback arrive faster. Before a targeted
interruption, inventory session/conversation, child processes, pending writes
and Git/test operations; read the visible screen. If interruption is necessary
and within authority, send one key then inspect its actual effect. Background
children may survive; an Escape key is not proof of a paused or clean session.
Never use a repeated Escape/text/Enter macro or transfer this behavior to Codex.

If startup/prefix parsing fails, preserve the actual error. Read the supplied
absolute Herdr path when discovery is unavailable; fix concrete syntax/discovery
rather than strip `/teamwork-preview` or retry the same rejected prompt.
Workers callback without `--wait`, then yield. Recovery and the two-failure quota
boundary are in event-monitoring.md; do not add account switching here.
