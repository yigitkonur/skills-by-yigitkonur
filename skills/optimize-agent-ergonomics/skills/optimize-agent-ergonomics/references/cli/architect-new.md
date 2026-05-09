# cli/architect-new.md

Mode B-CLI entry. Design a new agent-ready CLI from scratch with agent-readiness as a first-class constraint, not an afterthought. The 10-step workflow below produces a CLI that survives the audit checklist on day one — because every check was a design decision, not a bug to find later. Source: distilled from optimize-agentic-cli/SKILL.md (build order) and execution-patterns.md (verb semantics).

## Mode B-CLI workflow — 10 steps

Run these in order. Each step has a routing target; do not skip them.

1. **Run `../common/design-thinking.md` first.** The 8 surface-agnostic questions (workload, audience, statefulness, auth, scale, error semantics, observability, lifecycle) lock the basic shape. The surface decision lands on CLI — confirm by reading `../common/decide-surface.md` if you haven't already.

2. **Pick the 5–10 commands using intent-based granularity.** Commands map to verbs the agent might want to run, not to API endpoints. Aim for fewer, broader commands. Test each against `audit-checklist.md` (the 5 checks every command must pass).

3. **Define the JSON envelope shape.** Pick the envelope from `output-envelope.md` (`ok` / `result` / `error` / `schema_version`). Decide whether `result` carries a single object, a list, or both.

4. **Define the exit-code taxonomy.** Use the canonical 0–7 from `exit-codes.md`. Decide which commands can emit which codes; document in each command's help.

5. **Define the flag set.** Standard flags from `flags-and-discovery.md` (`--json`, `--quiet`, `--yes`, `--no-input`, `--dry-run`, `--force`, `--timeout`, `--config`, `--verbose`). Add command-specific flags only when they don't fit a standard.

6. **Define the auth model.** Read `auth-headless.md`. Decide which auth patterns to support and in what priority. Write the credential resolution chain.

7. **Decide if iterative is needed.** If the workflow has stages with validate-repair cycles (artifact submission, schema migration, batch import), use the iterative envelope from `iterative-pattern.md`. Otherwise, single-shot envelope.

8. **Pick a language and write the scaffold.** Use the templates in `code-templates.md`. Pick based on the team's stack and the CLI's distribution model (binary: Go/Rust; pip-installable: Python; npm-installable: Node; shell-only: Bash).

9. **Write the harness.** A small subprocess harness (Python or Node) that exercises the CLI under realistic agent conditions. See `subprocess-harness.md`. The harness IS the integration test.

10. **Test agent-driven invocation.** Run the CLI from the harness with synthetic agent prompts. Run the audit script from `audit-checklist.md` against your CLI. If anything fails, fix and re-run before declaring done.

## Verb-based command design

The CLI's commands are verbs. The agent's prompt has a verb in it; the CLI's verb should match.

| Verb | Semantics | Idempotency | Example |
|---|---|---|---|
| `create` | Make a new resource by name | Fails on conflict (exit 5) unless `--idempotency-key` set | `mytool create my-app --type=web` |
| `apply` | Reconcile from a desired-state file | Idempotent | `mytool apply -f config.yaml` |
| `ensure` | Make this state hold; create if absent, no-op if present | Idempotent | `mytool ensure database --name=mydb` |
| `delete` | Remove the resource | Idempotent (404 = success) | `mytool delete my-app` |
| `update` | Modify a field on an existing resource | Idempotent for the same value | `mytool update my-app --replicas=3` |
| `list` | Enumerate resources of a type | Read-only | `mytool list deployments` |
| `get` | Read one resource by ID | Read-only | `mytool get my-app` |
| `describe` | Read one resource with full details (incl. computed fields) | Read-only | `mytool describe my-app` |

The `apply` vs `create` distinction is load-bearing for agent retries. `apply` says "reconcile to this state, idempotently"; `create` says "make a new one, fail if it exists." Agents that retry safely use `apply` or `ensure`. Agents that intend exactly-once creation use `create` with an idempotency key.

`get` vs `describe`: `get` is the lean read for the agent's loop; `describe` is the full read for the human or for debugging. Both are read-only. If you only need one, use `get`.

## Sub-command structure: when to nest

Two patterns:

**Flat:** `mytool create-app`, `mytool create-database`, `mytool list-apps`. One level. Each command is self-contained. Best for CLIs with <10 commands.

**Nested noun-verb:** `mytool app create`, `mytool database create`, `mytool app list`. Two levels. Best for CLIs with 10+ commands across multiple resource types.

Pick noun-verb when:
- You have multiple resource types with parallel operations.
- Discovery via `mytool app --help` is valuable.
- The agent's prompt naturally says "create an app" / "list databases."

Pick flat when:
- You have <10 commands total.
- Commands are heterogeneous (don't share verbs).
- Two-level invocation is more typing than the user / agent will tolerate.

Avoid three-level nesting (`mytool resource app create`). Agents lose track; humans hate it; tab completion gets clumsy.

## Common mistakes when designing from scratch

**Verb-noun confusion.** `mytool app-create` (verb-noun fused) is worse than `mytool app create` (split) or `mytool create-app` (verb-first). Pick a discipline and apply it everywhere.

**Flag explosion.** A `mytool create` with 25 flags is a sign that `create` is doing too many things. Split into `mytool create web-app`, `mytool create worker`, etc., or use a config file (`mytool apply -f config.yaml`).

**Mixed-concerns commands.** A single `mytool deploy` that builds, pushes, deploys, and verifies is a sequence of three operations. The agent can't separate the failure modes. Split into `mytool build`, `mytool push`, `mytool deploy`, `mytool verify` — each with its own envelope.

**Wrapping a REST API 1:1.** If your underlying API has 47 endpoints and you make 47 commands, the agent loses context to the surface area. Pick the 5–10 verbs the agent actually needs and design those; don't expose the API directly. (Same anti-pattern in MCP — see `../mcp/patterns/tools.md`.)

**Forgetting the envelope on the failure path.** Every command emits the envelope. A "validation error" that prints to stderr and exits 6 with no envelope is broken — the agent has nothing to parse.

**Skipping auth design until the end.** Adding auth to a built-out CLI later means refactoring every command's preamble. Decide auth at step 6 of the workflow, not at step 10.

## Worked example: designing `gh-mini` from scratch

A minimal GitHub-flavored CLI focused on agent-driven PR workflows. Walk through the 10 steps.

### Step 1 — design-thinking

Run `../common/design-thinking.md`. Answers:

- **Workload:** read PRs, post comments, request reviews. Mostly read; occasional write.
- **Audience:** agents driving review workflows; humans rarely use it directly.
- **Statefulness:** none server-side from the CLI's perspective; GitHub holds state.
- **Auth:** GitHub PAT or app token via env var.
- **Scale:** dozens of calls per agent run; no need for streaming.
- **Error semantics:** 401 → exit 4 (auth); 404 → exit 3; rate limit → exit 7; otherwise standard.
- **Observability:** stderr prose for the human; envelope for the agent.
- **Lifecycle:** binary, distributed via Homebrew + GitHub Releases.

Surface decision (read `../common/decide-surface.md`): CLI. The workflow is shell-composable, agents drive it via subprocess, and there's no need for stateful sessions or per-user auth. Confirmed CLI.

### Step 2 — pick the commands

5 commands, intent-based:

| Command | Purpose | Verb |
|---|---|---|
| `gh-mini list-prs` | List open PRs in the current repo | `list` |
| `gh-mini show-pr <number>` | Show one PR's metadata + recent comments | `get` |
| `gh-mini comment <number>` | Post a comment to a PR | `create` |
| `gh-mini request-review <number> <reviewer>` | Request a review | `apply` (idempotent) |
| `gh-mini whoami` | Auth preflight | (special) |

Each passes the audit checklist mentally — JSON-emitting, semantic exits, non-interactive by default.

### Step 3 — envelope

Standard envelope from `output-envelope.md`. Examples:

```json
// gh-mini list-prs
{"ok": true, "result": {"prs": [{"number": 12, "title": "...", "author": "alice"}]}, "schema_version": "1"}

// gh-mini show-pr 12
{"ok": true, "result": {"number": 12, "title": "...", "comments": [...]}, "schema_version": "1"}

// gh-mini comment 12 (failure)
{"ok": false, "error": {"code": "FORBIDDEN", "message": "...", "next_action": "check token scopes"}, "schema_version": "1"}
```

### Step 4 — exit codes

- `0` — success on every read; comment posted; review requested.
- `2` — bad PR number format, missing required arg.
- `3` — PR doesn't exist (`show-pr 99999`).
- `4` — auth missing or invalid.
- `7` — rate limit (5000/hr cap on PATs).
- `1` — unhandled (network parse failure, server gave HTML for some reason).

### Step 5 — flags

Standard set from `flags-and-discovery.md`. Plus:
- `--repo=<owner/name>` for explicit repo selection (default: cwd).
- `--limit=<n>` for `list-prs` (default: 30).

### Step 6 — auth

Credential resolution chain:
1. `GH_MINI_TOKEN` env var
2. `GITHUB_TOKEN` env var (compatibility with `gh` and CI runners)
3. `~/.config/gh-mini/token` file (mode 0600)
4. fail with exit 4

No keyring (containers + CI use cases dominate). No OAuth (out of scope; users get a PAT from github.com).

### Step 7 — iterative?

No. Each command is a single round-trip. No multi-turn workflow.

### Step 8 — language and scaffold

Go. Single binary, easy distribution, mature GitHub SDK (`go-github`). Use the Go template from `code-templates.md`.

### Step 9 — harness

Python harness from `subprocess-harness.md`. Tests:
- `gh-mini whoami --json` returns `ok: true` when env var is set.
- `gh-mini list-prs --json` parses cleanly.
- `gh-mini show-pr 99999 --json` exits 3 with `RESOURCE_NOT_FOUND`.
- `MYTOOL_TOKEN=bogus gh-mini whoami --json` exits 4 with `UNAUTHENTICATED`.

### Step 10 — test agent-driven invocation

Run the audit script from `audit-checklist.md` against `gh-mini list-prs` and `gh-mini whoami`. Confirm all 5 checks pass. Run the Python harness end-to-end with a real PAT against a sandbox repo.

If any check fails, do not ship. Fix, re-run, declare done.

## Output of Mode B-CLI

The deliverable is:

1. The 10-step plan filled in (the work above for `gh-mini`).
2. A scaffolded binary with envelope + exit codes + flags + auth implemented (from `code-templates.md`).
3. A `subprocess-harness.md`-based smoke test that the user can run.
4. A `--help` page that documents the envelope, exit codes, examples.
5. A short note to the user: "ship this, then come back if you want iteration on streaming, observability, or distribution."

This skill ends here. There is no `build-cli` companion skill; the merged `optimize-agent-ergonomics` skill produces the scaffold and stops.

## Cross-references

- `audit-checklist.md` — the 5 checks every command must pass.
- `output-envelope.md` — the JSON envelope schema.
- `exit-codes.md` — the 0–7 taxonomy.
- `flags-and-discovery.md` — standard flags and TTY/CI detection.
- `auth-headless.md` — credential resolution chain.
- `iterative-pattern.md` — when the workflow needs validate-repair.
- `code-templates.md` — runnable scaffolds in 5 languages.
- `subprocess-harness.md` — how to test the CLI from an agent harness.
- `../common/design-thinking.md` — the 8 surface-agnostic questions that precede this workflow.
- `../common/decide-surface.md` — confirm the CLI choice.
