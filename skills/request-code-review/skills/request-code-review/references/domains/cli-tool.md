# CLI Tool Review

Author-side checklist for PRs that add or modify a command-line tool — flag parsing, help text, exit codes, output formatting, scripting discipline, agent-readiness. Use when classifying the diff's domain as **cli-tool** in SKILL.md Step 4.

## What CLI reviewers care about

| Concern | Why it matters | Evidence they want |
|---|---|---|
| **Help text discoverability** | Users (human and agent) find the tool via `--help` | Every command has `--help`; usage examples included |
| **Exit code correctness** | 0 = success, non-zero = failure. Scripts depend on this. | Failure paths return non-zero; success paths return 0 |
| **Stdout vs. stderr discipline** | stdout = pipeable data; stderr = progress/errors | Data to stdout, noise to stderr, no mixing |
| **Agent-readable output** | LLMs parse structured output; prose is lossy | `--json` flag or structured default |
| **Idempotency (where applicable)** | Re-running should be safe or clearly errored | Re-run doesn't corrupt state |
| **Argument parsing robustness** | Edge cases: missing args, unknown flags, `--` separator | Graceful errors, not stack traces |
| **Env var conventions** | `TOOL_FOO=bar` flags that override config | Documented in `--help`; prefix with tool name |
| **Signals** | Ctrl-C, SIGTERM behavior | Cleanup on signal; no orphan processes |

## Weaknesses the author should pre-empt

- **`--help` output is the README.** Does it list every flag? Does it show a working example? Is the one-line description accurate?
- **Unknown flag handling.** `tool --xkjdf` — does it error clearly, or silently accept? Silent accept is a foot-gun.
- **Positional vs. option arg collisions.** `tool file1 --verbose file2` — does it parse correctly? Edge-case order matters.
- **Default exit codes.** Non-zero on failure is non-negotiable. What exit codes for specific failure classes? Document if the tool has a taxonomy.
- **Machine-readability.** Does the tool support `--json` / `--format json` / stable NDJSON? Agents and scripts need it.
- **Progress on long ops.** If an operation runs >5 seconds, is there any signal of life? If piped to a file, can you suppress progress?
- **Interactive prompts in non-TTY contexts.** `isatty(stdin)` check? Or a `--yes` / `--no-prompt` flag? A tool that hangs waiting for input in a CI environment is broken.
- **Concurrency.** If the tool runs in parallel with another instance of itself, what happens? File locks? Atomic writes?
- **Config-file discovery.** If the tool reads `~/.toolrc`, is the search path documented? What overrides what (env > flag > file)?

## Questions to ask the reviewer explicitly

- "Exit code for 'partial success' (some items processed, some failed) is `2`. Convention is often 0 or 1 — is 2 the right signal, or should I pick one extreme?"
- "The `--json` output stream is NDJSON, one record per line. Agents in this stack expect NDJSON — can you confirm?"
- "Ctrl-C during `tool sync` currently aborts and leaves the destination in an intermediate state. Is atomic rollback a requirement, or acceptable to document the behavior?"
- "Help text on `tool foo --help` is 42 lines. Is that too long, or is the detail warranted?"
- "I added a `TOOL_DEBUG=1` env var. Is the prefix `TOOL_` consistent with other env vars in this tool, or do we already have a namespace?"

## What to verify before opening the PR

- [ ] `tool --help` runs and output is correct
- [ ] `tool <subcommand> --help` runs for each subcommand
- [ ] Unknown flag (`tool --xyz`) exits non-zero with a clear message
- [ ] Missing required arg exits non-zero with a clear message
- [ ] Happy path produces the expected output on stdout
- [ ] Progress messages go to stderr (try `tool command 2>/dev/null | ...`)
- [ ] `--json` output (if present) is valid JSON when piped through `jq`
- [ ] If interactive: non-TTY mode exits or uses defaults rather than hanging
- [ ] Ctrl-C leaves no stale files or locks

## Signals the review is off-track

- "The help text is mostly self-explanatory." → Self-explanatory to whom? Add one example per subcommand.
- "Exit code is 1 on any error." → Users (and scripts) benefit from distinct codes for distinct failure classes. Minimum: 0, 1 (bad usage), 2 (runtime failure), 3 (precondition not met). Pick a taxonomy.
- "`--json` is a follow-up." → If an agent ever runs this tool, `--json` is part of the tool's purpose, not an add-on.
- "Progress is on stdout so it shows up by default." → Users piping to a file get progress mixed with data. stderr is the right channel.

## When to split the PR

- Adding a new subcommand + refactoring flag parsing → split; refactor first
- New subcommand + new output format → can bundle if closely related; split if the format is a system-wide change
- CLI + the backend it drives → usually split; CLI land after backend is stable

## CLI follow-up skills

For specific tooling ecosystems:

| Ecosystem | Skill |
|---|---|
| Agent-readiness audit | `optimize-cli-for-agents` |
| Raycast Script Commands | `build-raycast-script-command` |
| GitHub CLI scripting | `run-github-scout` |
| Codex CLI orchestration | `run-codex-exec`, `run-codex-subagents` |
| Playwright CLI | `run-playwright` |
| Railway CLI | `use-railway` |

If the PR introduces or modifies a CLI's agent-readiness (flag taxonomy, JSON output, error shapes), route additionally to `optimize-cli-for-agents`.
