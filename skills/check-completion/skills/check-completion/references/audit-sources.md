# Audit Sources — Where to Find Task Evidence

Phase 1 Step 2 scans six sources. Each one reveals tasks and evidence the others miss. Skip any source and you introduce silent gaps — tasks that were done but you don't see, or tasks that were promised but you don't know about.

## The six sources

Scan in this order — earlier sources tend to be richer for fresh work, later sources tend to catch older / committed work.

### 1. Conversation messages

**What it reveals**: user asks, agent promises, intent statements, "I'll do X next" that never happened.

**Extraction recipe**:

Walk the conversation from the earliest user message to the latest. Collect:

- User asks ("please do X", "can you also Y", "don't forget Z") — these are candidate tasks
- Agent promises ("I'll start with X", "Next I'll do Y") — these are commitments to audit
- Agent questions to the user ("Should I X?") — if unresolved, potentially `Deferred to Human`
- Explicit scope decisions ("Let's skip W for now") — candidates for `Skipped` / `Deprioritized` / `Cancelled`

**Output**: A list of `{source: message, turn: N, speaker: user|assistant, candidate_task: ..., status_hint: ...}`.

**Gotcha**: promise drift. The agent may promise X, then quietly deliver Y. Record both.

### 2. Tool-call history

**What it reveals**: what the agent actually touched — files edited, commands run, files created or deleted.

**Extraction recipe**:

For each recent tool call, capture:

| Tool | What to extract |
|---|---|
| `Edit` | `{file_path, old_string, new_string}` — a file was modified |
| `Write` | `{file_path, content}` — a file was created or overwritten |
| `NotebookEdit` | Notebook cell modification |
| `Bash` | The command + output + exit status |
| `Task` | Subagent dispatched; note whether it returned with completion evidence |

Cross-reference with candidate tasks from messages: which tasks had corresponding tool calls? Which didn't?

**Output**: Per candidate task, whether tool calls support the claim.

**Gotcha**: `Edit` on a file doesn't prove the task is done — it proves the file was modified. Check what was modified, against the task description.

### 3. TodoList state

**What it reveals**: explicit task list with statuses (if the session used `TaskCreate` / `TaskUpdate` patterns).

**Extraction recipe**:

If a TodoList exists for this session:

- Dump the current state of each task
- Note any task marked `completed` without a corresponding verification — these are immediate `Assumed Complete` candidates
- Note any task stuck at `in_progress` with no recent updates — `Stalled` or `Timed Out` candidate
- Tasks marked `pending` → `Planned / Queued`

**Output**: Per-task status mapped from TodoList state to `check-completion` status.

**Gotcha**: TodoList statuses map noisily to audit statuses. `completed` in a TodoList means "agent toggled it"; that's `Assumed Complete` at best until verified independently.

### 4. Git log + diff

**What it reveals**: committed work, commit boundaries, rename/delete operations.

**Extraction recipe**:

```bash
# Commits in scope (branch divergence is the typical boundary)
git log --oneline origin/main..HEAD

# Per-commit detail
git log --patch --stat origin/main..HEAD

# Aggregate diff
git diff --stat origin/main...HEAD

# Uncommitted changes (working tree)
git status --short
git diff  # unstaged
git diff --cached  # staged
```

**Output**: List of changed files with net line deltas; commit messages; uncommitted state.

**Gotcha**: commits don't prove `Implemented`. A commit changes files; whether the files satisfy the task requires further verification.

### 5. Test output / CI status

**What it reveals**: automated verification results.

**Extraction recipe**:

Look for:

- Recent test command output in the session (`pytest`, `cargo test`, `pnpm test`, `vitest`, `jest`, etc.) — what passed, what failed, what was not run
- CI status on the current branch or PR (`gh pr checks` / `gh run list`)
- Lint / type-check output (`tsc`, `ruff`, `eslint`, `clippy`) — these verify different things than test runs
- Build output (`pnpm build`, `cargo build`, `make`) — exit code matters

**Output**: Per verifier, the result and what it covers.

**Gotcha**: a test pass for one test does not verify a different task. `Implemented` on task X requires the test that covers task X. Don't cross-claim.

### 6. Bash filesystem operations

**What it reveals**: file operations that don't show up in Edit/Write or git (yet).

**Extraction recipe**:

Scan bash commands in the session for:

- `rm <path>` / `rm -rf <dir>` — deletions
- `mv <src> <dst>` — renames / moves
- `cp <src> <dst>` — copies
- `mkdir <dir>` — new directories
- `touch <file>` — new empty files
- `> <file>` / `>> <file>` (shell redirects) — overwrites / appends
- `sed -i ...` — in-place edits
- `git mv`, `git rm` — tracked moves / deletes

**Output**: List of file-system operations with timestamps (or relative order).

**Gotcha**: bash file ops can create, delete, or move files in ways that don't show in git until committed. Cross-reference with current filesystem state.

## Combining extractions

After scanning all six, produce a deduplicated flat task list. Each row has:

- `candidate_task`: what the task is
- `sources`: which of the six mentioned it (e.g., "message + tool trace + git commit")
- `evidence_for_implemented`: what would prove `Implemented` (used in Step 3 classification)

Tasks that appear in zero sources are not in scope (they don't exist yet in this audit). Tasks that appear in one source only are suspect — single-source claims are fragile. Tasks that appear in multiple sources with consistent evidence are candidates for `Implemented`.

## Source-availability fallback

Not all sources are always available. The fallback chain:

1. If the session has no TodoList → scan messages + tool trace instead (skip TodoList)
2. If no test output is visible → note "no test run this session"; do not claim tests pass on faith
3. If git is not initialized → fall back to tool trace + bash history as the diff source
4. If bash history is partial (new session) → rely on tool trace + git

Each missing source expands the suspect-status surface area. If multiple sources are missing, the audit has lower confidence — state this explicitly in the audit table's intro.

## Cross-reference

The fallback chain for understanding what changed is similar to (but not the same as) the `evaluate-code-review` skill's `understand-changes.md`. That skill's chain is about reconstructing the diff the reviewer saw; this skill's sources are about reconstructing every task in scope. The two chains share the mechanics (git → tool trace → bash) but differ in purpose.

Do not require reading `evaluate-code-review/understand-changes.md` to act on this file. This file is self-sufficient.

## Budget

Source scanning can consume the entire token budget for a large session. Cap each source at a reasonable time / output length:

| Source | Cap |
|---|---|
| Messages | Scan in full; extract bullets only (don't quote full messages) |
| Tool trace | Scan in full for the most recent ~50 calls; older ones only if the task hasn't been covered elsewhere |
| TodoList | Dump current state only; ignore historical transitions unless relevant |
| Git log | `origin/main..HEAD` only unless branch is huge — then sub-range |
| Test output | Most recent run per test suite |
| Bash history | Last ~50 bash commands |

Under budget pressure, prioritize sources 1-3 (recent, session-specific) over 4-6 (historical).
