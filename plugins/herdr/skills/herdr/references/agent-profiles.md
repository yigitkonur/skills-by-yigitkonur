# Agent profiles

Read before starting a worker or EM. Explicit user harness/model/effort choices
win. Otherwise Simple workers use AGY; Advanced asks once for its Codex/Claude
EM and effort. Recommend effort from difficulty without creating more modes.

## Fixed defaults

| Difficulty | Typical assignment | Claude model | Claude effort | AGY model / effort | Codex model / effort |
|---|---|---|---|---|---|
| 1 | Brief read-only check or arithmetic | `claude-sonnet-5-5` | `medium` | `gemini-3.8-flash` / `high` | `gpt-6.1-sol` / `low` |
| 2 | Narrow fix with local checks | `claude-sonnet-5-5` | `high` | `gemini-3.8-flash` / `high` | `gpt-6.1-sol` / `medium` |
| 3 | Coupled component changes | `claude-opus-5-5` | `high` | `gemini-3.8-flash` / `high` | `gpt-6.1-sol` / `high` |
| 4 | Architecture or multi-service work | `claude-opus-5-5` | `xhigh` | `gemini-3.8-flash` / `high` | `gpt-6.1-sol` / `xhigh` |
| 5 | Broad breaking or cross-repo change | `claude-opus-5-5` | `max` | `gemini-3.8-flash` / `high` | `gpt-6.1-sol` / `max` |

These literal identifiers are the pack's chosen profiles, not a claim that every
account/client supports them. Keep `gemini-3.8-flash` as written; a model list's
suffix variants do not authorize replacing this user-tested alias. If a runtime
rejects a model/effort, report the exact error and stop that launch. Never choose
an undocumented fallback or resolve “latest” automatically.

## Pass native arguments after `--`

Examples use difficulty 2 and already verified shell panes. Substitute the pane
and a unique name; these are individual commands, not a fleet bootstrap.

```bash
herdr agent start job-a --kind agy --pane "$PANE_ID" --timeout 30000 -- --model gemini-3.8-flash --effort high
```

```bash
herdr agent start job-b --kind codex --pane "$PANE_ID" --timeout 30000 -- --model gpt-6.1-sol --config 'model_reasoning_effort="medium"' --sandbox workspace-write
```

```bash
herdr agent start job-c --kind claude --pane "$PANE_ID" --timeout 30000 -- --model claude-sonnet-5-5 --effort high
```

Codex reviewers can use `--sandbox read-only`. Do not add global permission
bypasses by default. Inspect installed harness help when an option is rejected;
do not edit account/proxy/wrapper configuration to make a task launch succeed.
Before relying on callbacks or EM control, verify Herdr socket access with the
chosen sandbox/approval policy. The tested permission blocker and scoped native
approval path are in [Codex harness](harness-codex.md).

All examples start interactive TUIs. No print mode, `codex exec`, `codex review`
subcommand, CLI `codex queue`, or hidden background runner is a substitute.

## Exact Codex identifier

Use literal `gpt-6.1-sol`, including the suffix. The live pilot successfully
produced a question and consumed an answer with that model at low effort. The
shorter `gpt-6.1` opened a TUI but its first request was rejected by the ChatGPT
account. A header is not proof of a successful model request. Report rejected
profiles; do not navigate a model picker or silently substitute a model.

## Verify identity honestly

Record the requested model/effort and observed binary. A process argv proves
launch intent. Only a native TUI identity/status surface or session query proves
the active model/effort. If that surface is unavailable, mark observed identity
unverified rather than repeating requested args as evidence. Inspect mismatches
before engineering work. Do not send speculative identity slash commands.
