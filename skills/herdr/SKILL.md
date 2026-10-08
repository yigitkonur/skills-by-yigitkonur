---
name: herdr
description: Use if controlling interactive coding agents, tabs, worktrees, or session lifecycle through Herdr CLI.
disable-model-invocation: true
---

# Herdr

Use Herdr to run visible interactive agents and return verified work to the user.
Keep the requested deliverable central: coordinating sessions is a means of doing
that work. Reading, editing, or explaining this skill does not authorize launching
agents or controlling existing sessions.

## 1. Establish the caller and scope

Before any session control:

1. Require `HERDR_ENV=1`.
2. Run `herdr pane current --current` and parse the returned live pane, tab,
   terminal and workspace identities. Environment IDs alone are not proof.
3. If lookup fails, stop mutations and inspect the caller read-only. A persistent
   tool process can retain an old pane environment after a TUI resume. Reconcile
   only the exact current conversation and native session/process against a live
   pane; focus or a matching title alone is insufficient. With that evidence,
   pass corrected pane/tab/workspace IDs to individual commands and rerun current
   lookup. Do not change global environment/configuration. If identity remains
   ambiguous, report the diagnostic and continue independent authorized file work.
   Never guess an ID, adopt a focused stranger or bootstrap an external supervisor.
4. Record the deliverable, permitted side effects, project and return pane. A
   change of harness/model is not a change of assignment.
5. Discover the installed CLI with `herdr --help` and relevant subcommand help.
   Bare `herdr` can attach a TUI; it is not a discovery command.

Operate only on sessions created for this task or explicitly adopted with known
ownership. Leave other projects, accounts, settings and old sessions alone.

## 2. Choose the instruction mode

| Mode | Supervisor | When to use |
|---|---|---|
| **Simple — default** | Root directly supervises workers | Ordinary work, including several independent jobs |
| **Advanced — explicit choice** | Root plus one Engineering Manager | User requests delegated scheduling, durable reports and dependency management |

If a brief assigns you a worker/reviewer role, do that owned assignment and
return to its supervisor. Provisioning and scheduling belong to the assigned
supervisor; loading this skill does not authorize a worker to bootstrap a fleet.
AGY internal teamwork follows its explicit brief and capacity limits.

These are instruction modes, not CLI flags. There is no `--mode simple` command.
Task size, number of files, parallelism, or a request to use AGY does not select
Advanced. Simple can handle a coupled feature with one writer or serialize jobs.

If Advanced would help, explain its concrete benefit and extra manager/session
cost, then offer it. Continue Simple unless the user chooses Advanced. A refusal
must not create a manager. Advanced has no managerless variant.

## 3. Read the next needed recipe

Read one recipe for the current decision; follow its relevant links as needed.
Do not load every reference or execute an Advanced bootstrap in Simple.
When a brief supplies an absolute candidate skill path, resolve its references
from that directory. Do not fill gaps from an older global installation; report
the specific missing instruction to the supervisor instead.

| Decision | Read |
|---|---|
| Run an ordinary job or several directly supervised jobs | [Simple workflow](references/simple-workflow.md) |
| User explicitly selected Advanced | [Advanced orchestration](references/advanced-orchestration.md) |
| Select a harness, model and effort before launch | [Agent profiles](references/agent-profiles.md) |
| Write a task brief, send a callback or reconcile delivery | [Prompt and messaging](references/prompt-and-messaging.md) |
| Create tabs, split review panes or isolate concurrent writers | [Topology and worktrees](references/topology-and-worktrees.md) |
| Wait, inspect a modal, recover a stopped process or handle quota | [Event monitoring](references/event-monitoring.md) |
| Operate an AGY worker | [Antigravity harness](references/harness-antigravity.md) |
| Operate Codex or distinguish steering from a queued turn | [Codex harness](references/harness-codex.md) |
| Operate Claude | [Claude harness](references/harness-claude.md) |
| Close a finished pane or preserve/remove a checkout | [Lifecycle and cleanup](references/lifecycle-and-cleanup.md) |
| Resolve command syntax, IDs or an explicitly requested remote target | [Herdr primitives](references/herdr-primitives.md) |

## 4. Shared operating rules

### Launch and prompt

- All agents are visible interactive Herdr TUI sessions. Do not substitute hidden
  background agents, print-mode runs, `codex exec`, or CLI `codex queue`.
- For a new job, create a new task tab in the current workspace; root keeps its
  own pane. Reuse an owned, verified session for follow-up work.
- Simple workers default to AGY. User harness/model/effort overrides win.
- Advanced's sole EM is Codex or Claude, never AGY. If unspecified, ask once for
  Codex/Claude and effort, suggesting an effort appropriate to the assignment.
- Use the fixed difficulty profiles; do not silently resolve a newer model,
  downgrade effort, rotate accounts, or change billing settings.
- Every new task brief references this skill and its resolved absolute path:
  Codex `$herdr (/absolute/path/herdr/SKILL.md)`;
  AGY/Claude `/herdr (/absolute/path/herdr/SKILL.md)`.
- Nontrivial AGY briefs (difficulty 2–5) start with `/teamwork-preview` before
  `/herdr`. Difficulty 1 may omit it. This is AGY-only prompt authoring; do not
  add an installation/permission detour or silently drop the prefix.
- Include scope, owned areas, checks, authority and a live return pane in briefs.
  Short coordination notices are not new task briefs and need no skill prefixes.

### Observe and deliver

- Use bounded `herdr agent wait TARGET --timeout 30000` through the calling
  tool's session monitor. Never run an indefinite wait or detached polling loop.
- An idle/done badge means input readiness, not verified task completion.
  A timeout means inspect visible output and process state, not resubmit.
- An asynchronous question can coexist with ongoing work. Inspect its native
  panel and track unanswered items separately; continue only independent work.
- CLI success proves submission, not consumption or correctness. Match the
  returned job/attempt and evidence before accepting a handback.
- Workers send detailed result callbacks with `herdr agent prompt TARGET TEXT`
  without `--wait`, then yield. Supervisors inspect files and check evidence.
- Stream review when a coherent candidate is ready. Keep one writer for coupled
  changes; isolate concurrent writers to the same repository in worktrees.
- Review binds to an immutable candidate. A changed candidate invalidates its
  approval. Integrate accepted changes serially when integration is authorized.

### Bound intervention and retire work

- Read visible dialogs before any keys; verify foreground identity before text
  injection. Do not apply AGY Escape behavior to other harnesses.
- A pause stops dispatch, key injection and mutations until resumed.
- Two equivalent recovery failures stop automatic retries. Report the concrete
  blocker; do not reset the budget by creating another session.
- Read and verify the handback, settle remaining ownership, then promptly close
  finished owned panes. Pane closure does not require a PR merge or clean tree.
- Preserve dirty or undelivered worktrees. Deletion has its own checks in the
  cleanup recipe. Never force-delete branches, globally prune, blanket-kill,
  stop the Herdr server, or close unrelated panes.

## 5. Finish with the work

Return the requested changes and their verification. Report separately what was
launched, submitted, consumed, completed and validated when those differ.
If execution is blocked, name the failed command/state and the unverified step.
Do not present a session inventory or agent findings as completed implementation.
