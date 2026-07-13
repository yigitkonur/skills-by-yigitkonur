# Jean State and Steering

Use this reference before resolving projects, reading session identity, sending prompts, changing backend/model/execution mode, or creating any worker/session/worktree.

## Contents

- [Truth-source split](#truth-source-split)
- [Project and root discovery](#project-and-root-discovery)
- [Bare file and plan resolution](#bare-file-and-plan-resolution)
- [Session identity and ownership](#session-identity-and-ownership)
- [YOLO mode](#yolo-mode)
- [Exact-state steering packet](#exact-state-steering-packet)
- [Existing supervisors and slot ownership](#existing-supervisors-and-slot-ownership)
- [Removed-session transcript fallback](#removed-session-transcript-fallback)
- [UI unavailable](#ui-unavailable)

## Truth-source split

No single surface is sufficient. Use each for what it can actually prove.

| Source | Authoritative for | Not sufficient for |
|---|---|---|
| Fresh Jean UI through Computer Use | selected project/session, visible current history, running/cancel state, chosen backend/model/mode, prompt visibly started | exact git/provider truth by itself |
| `scripts/jean_ops.py` over Jean MCP | discovered project/worktree/session IDs, compact inventory, recent messages, change summaries, status transitions and bounded wait verdicts | mutation, UI ownership, visible turn start, or completion approval |
| Native Jean MCP live schema | the same explicit-ID reads plus deliberate fire-and-forget control when supported | UI ownership or visible turn start by acknowledgment alone |
| Repo/CI/provider/runtime probes | branch, HEAD, dirt, process ownership, exact-SHA CI, deploy and live behavior | which Jean tab/input is selected |

When sources conflict, stop mutations and reconcile identity. Prefer fresh visible history/header for UI ownership, exact repo state for git truth, and provider/runtime evidence for deployed truth. Record stale titles or metadata; do not make them the identity.

## Project and root discovery

Never derive a filesystem path from a Jean display name.

1. Read the fresh selected project/session header and any visible repo/worktree path.
2. Resolve `JEAN_OPS="${CODEX_HOME:-$HOME/.codex}/skills/orchestrate-projects-by-jean/scripts/jean_ops.py"`, run `/usr/bin/python3 "$JEAN_OPS" doctor --probe`, then use its `projects`, `worktrees`, and `sessions` commands to map display name to live project ID/path and explicit worktree/session IDs. Use native `get_project_context` or the script's allowlisted `read` command for deeper context.
3. If current-context discovery is unavailable or refers only to the caller, use the explicit-ID chain: projects → worktrees → sessions.
4. Confirm the candidate with `git -C <path> rev-parse --show-toplevel`, current branch/HEAD, and worktree inventory.
5. If multiple labels match, use current history, worktree branch, and repo remote to disambiguate. Leave it unresolved rather than guessing.

Do not probe `/opt/nvme/dev/<display-name>` or any other constructed root as if it were evidence. A failed guessed path is not a project blocker; it is a discovery failure that must use the explicit-ID route.

## Bare file and plan resolution

If the UI or session names `PLAN.md`, a task graph, or another bare filename:

1. establish the exact repo/worktree first;
2. if current history/transcript provides an exact absolute path, verify that exact file and record that it is external to the repo when applicable;
3. otherwise list candidates within the repo root using a bounded path query such as `rg --files -g '<basename>'`;
4. use the session's verified cwd, adjacent references, or current diff to choose among duplicates;
5. read the selected file before steering;
6. record the resolved absolute path or repo-relative path in the ledger.

Never invent `.planning/`, `.herdr-pm/`, `docs/`, or another conventional parent.

## Session identity and ownership

A tab title can outlive the mission currently shown in its history. Bind session identity to:

- selected project and session IDs when available;
- visible current history and latest user/agent messages;
- repo/worktree/branch named in that history;
- current backend/model/mode and running state.

Record a stale title as a UI defect, then steer the verified current mission. Do not cancel or prompt based on the title alone.

Only one manager owns a session turn:

- prefer Computer Use for a visible UI-owned running session;
- inspect `jean_ops.py leases` before attaching; a conflicting live session lease is a semantic stop, not a ledger hint;
- do not send MCP and UI prompts concurrently;
- a Jean MCP `send_chat_message` response is fire-and-forget, not queue or start proof;
- `jean_ops.py` is deliberately read-only; do not weaken it to route around this ownership rule;
- `get_session_status` may disagree with a genuinely UI-owned turn; verify fresh UI history/running controls before cancelling or duplicating;
- after any send, require the new prompt in history plus a fresh running/cancel/status marker.

If the prompt did not visibly start, resolve selection and ownership before one bounded resend. Never stack retries.

### Run-aware native MCP fast path

Native Jean MCP may send to a nonselected idle session without navigating the UI only when all of these are true:

1. explicit project, worktree, and session IDs were freshly resolved;
2. no UI controller, shell watcher, Codex task, or live lease owns that session;
3. the baseline latest run ID and latest message marker were captured;
4. one durable controller lease is acquired for the session;
5. exactly one prompt is sent to the explicit session ID;
6. a fresh status/message read proves a different run ID or newer user-message marker;
7. the watcher is pinned with `--expect-run-id NEW_ID` or `--after-run-id BASELINE_ID`;
8. any conflict routes back to fresh UI reconciliation without a second send.

An MCP acknowledgment alone is not success. Do not use this fast path for the selected/running UI session, approvals, backend/model/YOLO changes, or ambiguous ownership.

## YOLO mode

When the user authorizes YOLO:

1. select the intended existing session;
2. choose only a backend/model/mode actually visible or accepted by the live schema;
3. set execution mode to YOLO in that same session;
4. refresh UI and verify the selection;
5. send the exact-state prompt and verify turn start.

YOLO means the coding agent may execute routine in-scope actions without pausing. It does not mean bulk-approve completions, skip evidence, weaken tests, bypass Computer Use confirmation policy, or expand external authorization.

## Exact-state steering packet

Every nontrivial prompt should carry:

```text
Product outcome: <customer/business result>.
Repo/worktree/branch/HEAD: <verified exact values>.
Current session/backend/model/mode: <visible values>.
Already complete; do not redo: <evidenced milestones>.
Preserve: <dirty overlays, plans, stashes, unrelated branches/processes>.
Own only: <one bounded objective>.
Do not: restart Jean, create replacement sessions/worktrees, spawn helpers,
repeat failed routes, invent flags/paths, or wait without a deadline.
Return with: <diff/test/exact-SHA CI/deploy/runtime/cleanup evidence>.
```

Answer routine questions from evidence in the packet. Keep startup work proportional: the smallest reversible implementation that proves the product outcome, with deeper rigor only for auth, payments, data, security, destructive history, and deployment.

## Existing supervisors and slot ownership

Before spawning or attaching a worker:

1. inspect the ledger owner, live agents, relevant processes, session messages, and worktree locks;
2. keep one persistent owner per independent project;
3. reserve manager capacity for Jean UI, cross-project decisions, and verification;
4. queue excess projects by release/customer priority;
5. wake or follow up the existing owner instead of replacing it;
6. attach the next queued project only when a slot is genuinely free.

An external supervisor process is an owner even if it is not a Codex subagent. Observe its handback; do not duplicate or kill it.

## Removed-session transcript fallback

If a session/worktree was removed and Jean MCP can no longer read its messages:

1. verify git integration and worktree removal independently;
2. locate the session ID from the ledger/UI/MCP history;
3. inspect Jean's application-support session data when present under `~/Library/Application Support/com.jean.desktop/sessions/data/<session-id>/`;
4. select only the newest relevant JSONL first; cap the initial read by file count, bytes, and lines instead of recursively scanning every session;
5. parse a few complete JSON lines to observe the actual schema before writing a filter;
6. filter by observed top-level/message types with a JSON parser; never interpolate transcript text or shell escapes into a `jq` program;
7. extract only relevant agent messages and redacted tool evidence, expanding the bound once only when a named proof item is missing;
8. never echo secrets, tokens, environment dumps, or unrelated user content.

This is an evidence-recovery fallback, not a reason to remove sessions early. If the bounded newest transcript cannot establish identity, record the proof gap instead of broad-scanning all Jean data.

## UI unavailable

When the Mac is locked or Jean is inaccessible, do not relaunch it. Continue safe MCP/repo/CI/provider/transcript proof, mark UI-only actions explicitly, and retry on the next bounded check or heartbeat. Ask the user to unlock only when no autonomous non-UI work remains.
