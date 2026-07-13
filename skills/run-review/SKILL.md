---
name: run-review
description: "Use if reviewing a PR/diff, requesting review on your branch, triaging feedback, or delegating."
---

# run-review

Single entry point for every code-review intent. The skill does **not** silently pick a workflow — it routes by mode. On activation, pick the mode explicitly (or ask), then execute the per-mode procedure.

The four modes cover the only four review intents that exist in practice:

| Mode | Intent in one sentence | What used to live here |
|---|---|---|
| **A — Do a review** | Review someone's PR, branch, or diff for merge readiness. | the old `review-pr` / `do-review` skill |
| **B — Ask for review** | Hand off your own branch as a reviewable PR (self-review body, optional `gh pr create`). | the old `review-self` / `ask-review` skill |
| **C — Evaluate received feedback** | Triage human + bot comments, markdown audit docs, or earlier session feedback into accept / pushback / clarify / defer / dismiss. | the old `review-feedback` / `evaluate-code-review` skill |
| **D — Delegate to codex** | Run `codex review` (or `codex exec review`) against the same target; surface findings back inside Claude. | new — wraps the codex CLI's native review command |

This skill replaces those three older skills and folds codex review in as a peer mode, so the user never has to guess which review skill to pick.

## When to use this skill

Trigger phrases (any one is sufficient):

- *"review PR #N"*, *"review github.com/owner/repo/pull/N"*, *"walk this diff"*, *"is this safe to merge?"* → Mode A
- *"open a PR for this"*, *"write me a self-review"*, *"this is ready for review"*, *"hand this off"* → Mode B
- *"address the review comments on PR #N"*, *"the bots reviewed my PR"*, *"go back over the reviewer's notes"*, *"read review.md and give me an action plan"* → Mode C
- *"run codex review on this"*, *"have codex review the diff"*, *"codex review --uncommitted"*, *"second opinion from codex"* → Mode D

Do **not** use this skill for:

- per-branch codex review fix loops over a list of branches → multi-branch codex review orchestration
- repo-cleanup of dirty trees across multiple worktrees with no review handoff yet → `run-repo-cleanup`
- chasing a runtime bug with no diff to judge → `debug-runtime`
- generic codex-CLI orchestration without a review intent → parallel `codex exec` orchestration or parallel `codex exec` orchestration

## Mode selection (load-bearing — do not skip)

On every activation, before any tool call beyond reading state:

1. **Read the user's literal phrasing** against the trigger table above.
2. **Apply the inference rules** (next subsection). If a single mode wins with high confidence, state the mode in one line and proceed.
3. **If two or more modes are plausible, ASK.** Default to asking when in doubt — a wrong mode wastes a lot of subagent compute. Use `AskUserQuestion` when available; otherwise emit the inline numbered prompt below.

### Inference rules

Apply in order; the first matching rule wins. Each rule lists the *literal cue* and the mode it routes to.

| # | Cue in the user's request | Mode |
|---|---|---|
| 1 | The phrase `codex review`, `codex exec review`, `have codex review`, or any direct mention of running the codex CLI to review code. | **D** |
| 2 | Words *open a PR / hand off / ready for review / self-review / write the review body / ship this branch* applied to the user's own work, AND no third-party review comments are named. | **B** |
| 3 | Words *evaluate / triage / address / respond to / answer / sort out* applied to feedback already in hand — PR comments, named bots (Copilot, CodeRabbit, Greptile, Devin, Bito, Codex), or a markdown file like `review.md` / `audit.md` / `feedback.md`. | **C** |
| 4 | A PR number, URL, branch comparison, or `gh pr view` target named by the user with words *review / look at / merge-readiness / walk this diff / sanity-check*, and no mention of codex CLI. | **A** |
| 5 | None of the above OR multiple rules fire at the same confidence. | **ASK** |

When confidence is borderline (e.g., the user names a PR but also says "have codex take a look") — that is rule 1 first; codex CLI wins. When the user says "open a PR and have codex review it" — that is **two modes in sequence**: B (open the PR) then D (codex review against the new branch). Run them in order and say so out loud before starting.

### How to ask when ambiguous

If the user's phrasing does not uniquely select a mode, surface the four choices verbatim and stop. Use the `AskUserQuestion` tool when available with one question and these four options. Otherwise emit this block in chat and wait:

```
I can run this in one of four review modes. Which do you want?

  A) Do a review — I review your PR / branch / diff for merge readiness.
  B) Ask for review — I clean up your branch and open a PR with a self-review body.
  C) Evaluate received feedback — I triage comments / bot output / a review doc into an action plan.
  D) Delegate to codex — I run `codex review` against the diff and surface its findings.

Reply with A, B, C, or D (or describe the work in one line).
```

Never hide a mode to "narrow" the choice. The user must always see all four. Multi-mode requests are fine — they execute in sequence.

### Once the mode is locked

State the chosen mode in one line before starting. Do **not** swap modes mid-workflow without re-asking. If, while executing, you discover the user actually wanted a different mode, stop, name the mismatch, and re-route.

## Mode A — Do a review (review someone's PR / branch / diff)

### Trigger phrases

*"review PR #123"*, *"review github.com/owner/repo/pull/N"*, *"is this safe to merge?"*, *"walk this diff"*, *"review main...feature-branch"*, *"review my working tree"*, *"the PR already has CodeRabbit comments — what's left?"*, *"this PR has 40 files; tell me what to look at first"*.

### Required inputs

Exactly one comparison target. Name it in one line before reading code:

- `owner/repo#N` for GitHub PR mode
- `<base>...<head>` for branch diff mode (e.g. `origin/main...HEAD`)
- `HEAD + staged + unstaged` for working-tree mode

If the target cannot be named in one line, stop and ask. Do not invent a diff target.

### Procedure (8 phases, owned by Mode A)

1. **Triage the request** — full vs targeted, draft vs ready, security-only vs general. Inline; no reference.
2. **Gather context before code** — `references/mode-a-do-review/workflow/review-workflow.md` (Phase 1). Tooling: `scripts/parse-pr.sh` (see `scripts/parse-pr.md`), `references/mode-a-do-review/workflow/gh-cli-reference.md`.
3. **Scope and cluster files** — `references/mode-a-do-review/analysis/file-clustering.md`. Tooling: `scripts/cluster-files.sh` (see `scripts/cluster-files.md`).
4. **Read existing review state** — `references/mode-a-do-review/workflow/comment-correlation.md`, `references/mode-a-do-review/workflow/automation.md`. Treat Copilot, CodeRabbit, Greptile, Devin, Bito, CodeQL, Snyk, etc. as prior review — dedupe, do not repeat.
5. **Validate goals** — `references/mode-a-do-review/workflow/review-workflow.md` (Phase 4). A PR that passes every quality check but misses its stated outcome is a failed PR.
6. **Review by cluster** — apply dimensions in order: security → correctness → data integrity → API contract → performance → tests → maintainability. Detail: `references/mode-a-do-review/dimensions/review-dimensions.md`, `references/mode-a-do-review/dimensions/security-review.md`, `references/mode-a-do-review/dimensions/performance-review.md`, `references/mode-a-do-review/dimensions/bug-patterns.md`, `references/mode-a-do-review/dimensions/language-specific.md`. Diff reading help: `references/mode-a-do-review/analysis/diff-analysis.md`.
7. **Cross-cutting sweep** — `references/mode-a-do-review/analysis/cross-cutting.md`. Large PR strategy: `references/mode-a-do-review/analysis/large-pr-strategy.md`.
8. **Calibrate, synthesize, output** — `references/mode-a-do-review/output/output-templates.md`, `references/mode-a-do-review/output/communication.md`, `references/mode-a-do-review/output/anti-patterns.md`. Severity calibration: `references/mode-a-do-review/dimensions/severity-guide.md`.

### Subagent dispatch — when to fan out

Mode A is **single-agent by default**. Dispatch subagents only when ALL of:

- changed files ≥ 15 OR changed lines > 500
- cluster map (Phase 3) shows ≥ 2 high-risk clusters that can be reviewed independently
- the user has not asked for a quick / shallow review

If those conditions hold, dispatch one subagent per cluster. Each subagent receives: cluster file list, base/head refs, the dimensions checklist at `references/mode-a-do-review/dimensions/review-dimensions.md`, and the actionability gate from Phase 6. Subagents return findings only — the parent agent owns calibration, dedup, and verdict.

For PR < 100 changed lines, do not dispatch — single-agent inline is faster.

### Output shape

Markdown review in chat by default. The body includes: verdict (✅ Approve / 💬 Comment / 🔄 Request Changes), findings grouped by severity (🔴 blocker, 🟡 important, 🟢 suggestion, 💡 question), at least one specific positive observation (🎯), summary of existing review state (or "unavailable in local diff mode"), deep-reviewed vs skimmed clusters, CI/check state. Each finding contains: severity, title, exact `file:line`, observed behavior, impact, and suggested fix or question.

GitHub mutation (posting a formal review or inline comments) happens only when the user **explicitly** says submit / post / publish / comment. Default is markdown only.

### Hand-off contract

After Mode A: the user has a markdown review (or, on explicit request, a posted GitHub review). No commits made, no PR opened, no fixes applied. If the user asks "now go fix the blockers," that is a new task — not part of Mode A.

### Per-item programmatic mode

When this skill is called from multi-branch codex review orchestration (or its the retired the now-retired codex review skill shim) with a single candidate finding plus a branch diff, output **JSON only** per the contract:

```json
{
  "decision": "accepted|rejected|ambiguous",
  "severity": "blocker|important|suggestion|question",
  "evidence": ["file:line"],
  "rationale": "Why the item does or does not survive review.",
  "intended_fix_shape": "Only for accepted items."
}
```

## Mode B — Ask for review (open a PR with a self-review body)

### Trigger phrases

*"open a PR for this"*, *"hand this off for review"*, *"this is ready for review"*, *"write me a self-review"*, *"clean up my commits and open a PR"*, *"give me a review doc — no PR, just the markdown"*, *"summarize this branch for the reviewer"*.

### Required inputs

- The user's current branch (must not be `main` / `master` / default).
- A clean or tidy-able working tree.
- Owner/repo for `gh` (read from `git remote -v`; pass `--repo` explicitly every time).
- The user's intent: PR handoff (default) vs markdown review doc (explicit request only).

### Two output modes

| Sub-mode | Trigger phrase | Produced artifact |
|---|---|---|
| **PR handoff** (default) | silence on format, "open a PR", "ready for review", "hand this off" | clean branch pushed, `gh pr create` executed, self-review body posted |
| **Markdown review doc** | "just the text", "no PR", "give me a review doc", "write the review as markdown" | markdown file or inline output; no git writes, no PR |

If ambiguous, ask once before doing anything. Default is **not** a license to skip the ask when intent is genuinely unclear.

### Procedure

1. **Classify the sub-mode** — state PR handoff or markdown-doc out loud before proceeding.
2. **Inspect current state** — `git status --short`, `git branch --show-current`, `git log --oneline origin/main..HEAD`, `git remote -v`, `gh pr list --head <branch>`. Capture: dirty? on default branch? unpushed? PR already exists?
3. **Handle dirty tree first** — commit before opening the PR, never after. Diff-walk commits, group by domain, one conventional commit per concern. No `git commit -am`, no blind `git add -A`. If on default branch, create a branch first (`git switch -c <type>/<scope>-<slug>`). Detail: `references/mode-b-ask-review/handoff-mechanics.md`. RED-baseline excuses to refuse: `references/mode-b-ask-review/rationalizations.md`.
4. **Classify the diff's domain** — match the changed paths against one of seven domains. Read **the one** that matches before drafting:
   - server / API / SQL / auth / infra → `references/mode-b-ask-review/domains/backend.md`
   - client-side TS / JS / React / Vue / Svelte (outside `server/`) → `references/mode-b-ask-review/domains/frontend-ts-js.md`
   - `@modelcontextprotocol/sdk` imports, Zod tool schemas, SKILL.md authoring → `references/mode-b-ask-review/domains/mcp-server.md`
   - CSS / Tailwind / design tokens / a11y / layout → `references/mode-b-ask-review/domains/ui-engineering.md`
   - `bin/`, `scripts/*.sh`, argparse / commander, flag parsing, exit codes → `references/mode-b-ask-review/domains/cli-tool.md`
   - prose `*.md` under `content/`, `posts/`, `docs/`, README bodies → `references/mode-b-ask-review/domains/content-markdown.md`
   - anything else or a clear mix that does not split cleanly → `references/mode-b-ask-review/domains/generic.md`
5. **Draft the body** — follow `references/mode-b-ask-review/review-text-template.md`. Under 50,000 chars; explain every change; surface ≥ 2 weaknesses the author already knows about; ask ≥ 1 explicit reviewer question.
6. **Ship it** — `gh pr create --repo <owner>/<repo> --base <target> --head <current> --title "<type>(<scope>): <subject>" --body-file /tmp/pr-body.md`, then verify with `gh pr view <N> --repo <owner>/<repo> --json url,baseRefName,headRefName`. URL must point to the intended repo; base must be the intended target.

### Subagent dispatch — when to fan out

Dispatch when the diff touches **2+ domains AND each domain has ≥ 5% of the changed lines**. One subagent per domain cluster. Each subagent receives: `BASE_SHA` + `HEAD_SHA`, paths restricted to its cluster, the matching domain reference, and the prompt template at `references/mode-b-ask-review/subagent-dispatch.md`. Each returns per-domain change summary, weaknesses, 1-3 reviewer questions.

Combine outputs into one coherent body — one section per domain under an `## Areas` heading, plus an overall summary. Single-domain diffs skip this step.

### Output shape

PR handoff: PR URL plus the verification block from `gh pr view`. Markdown mode: the body inline or written to the user-named path. Body must include weaknesses (≥ 2) and reviewer questions (≥ 1).

### Hand-off contract

After Mode B: branch is pushed, PR is open (PR mode) or markdown is delivered (doc mode). `git status --short` is empty on the author's branch. The reviewer now owns the next move. Do not start running fixes from your own self-review weaknesses — those are signals to the reviewer.

## Mode C — Evaluate received feedback

### Trigger phrases

*"address the review comments on PR #42"*, *"what do the bots say on my PR"*, *"Copilot and CodeRabbit disagree — sort it out"*, *"merge what the three reviewers said"*, *"go back and check the reviewer's notes from earlier"*, *"read review.md and give me an action plan"*, *"the reviewer's notes are in audit.md"*, *"reply in the PR threads with my answers"*.

### Required inputs

Feedback in one of three shapes:

| Input mode | Detection | Source |
|---|---|---|
| **PR mode** | user names a PR (number, URL) and review comments | `scripts/parse-pr-comments.sh --repo <owner/name> --pr <N> --out <dir>` (see `scripts/parse-pr-comments.md`) |
| **Session-audit mode** | user references review notes earlier in *this* conversation | prior messages |
| **Markdown-doc mode** | user names a file like `review.md`, `audit.md`, `feedback.md` | the file on disk |

If genuinely ambiguous: scan prior messages, then `gh pr view` on the current branch, then look for `review*.md` / `audit*.md` / `feedback*.md` in the working dir. Report what was found before proceeding.

### Procedure

1. **Identify the input mode and surface the feedback** — extract every item as a flat list with verbatim text, source, location, code-range metadata, severity hint. For PR mode, run `scripts/parse-pr-comments.sh` to fetch all three GitHub feedback channels (top-level reviews, inline review comments, PR-discussion comments).
2. **Reconstruct ground truth** — what change set should the reviewer have been looking at? Fallback chain at `references/mode-c-evaluate-feedback/understand-changes.md`: branch commits → tool-trail (Edit/Write calls in the session) → bash trail → uncertain. Stop and name uncertainty rather than guessing.
3. **Dispatch an Explore subagent — ALWAYS.** Even single-item reviews. Self-contained prompt — no "as we discussed earlier", no session references. Template: `references/mode-c-evaluate-feedback/subagent-dispatch.md`. Subagent returns per-item `{verdict, evidence: file:line + reasoning, severity}`.
4. **Consolidate multi-source feedback** — if 2+ reviewers, line-range cluster (same file + overlapping range, ±5 lines) and merge duplicates. Surface conflicts explicitly — never silently pick one. Detail: `references/mode-c-evaluate-feedback/multi-agent-consolidation.md`. Tooling: `scripts/cluster-feedback.py --input normalized.jsonl --output clusters.json` (see `scripts/cluster-feedback.md`).
5. **Evaluate each item** — combine the subagent's verdict with parent verification. Six-check lens at `references/mode-c-evaluate-feedback/verification.md`. Each item gets one verdict:

   | Verdict | Meaning |
   |---|---|
   | ACCEPT | feedback is correct and worth acting on |
   | PUSHBACK | feedback is wrong; respond with technical reasoning |
   | CLARIFY | feedback is unclear or evidence is missing; ask |
   | DEFER | correct but out of scope for this PR; log as follow-up |
   | DISMISS | noise, unambiguously wrong, or reviewer lacks context |

6. **Produce the action plan** — format depends on input mode. See `references/mode-c-evaluate-feedback/action-plan-output.md`. PR mode: reply in threads via `gh api repos/{o}/{r}/pulls/{pr}/comments/{id}/replies`. Session-audit mode: markdown action plan inline. Markdown-doc mode: write `<source>-action-plan.md` next to the source.
7. **Implement (only if authorized)** — order: blocking → simple → complex. One item at a time, test each before the next. After each item, reply in the thread (PR mode) or update the plan (markdown mode) with `Fixed. <what changed>.` — no gratitude, no praise, no apology.

### Voice discipline (load-bearing)

No performative agreement. No gratitude. No praise. No apology. No agreement-before-verification. The diff is the acknowledgment. Phrase-level rules at `references/mode-c-evaluate-feedback/voice.md`. Pressure-scenario excuses at `references/mode-c-evaluate-feedback/rationalizations.md`. GH thread mechanics at `references/mode-c-evaluate-feedback/gh-review-workflow.md`.

### Subagent dispatch — when to fan out

The single Explore subagent in Step 3 is **mandatory** even for one-item reviews — bias control, not parallelism. Fan out further when ≥ 30 distinct feedback items survive deduplication. Group items by file or by cluster (Step 4) and dispatch one subagent per cluster with: ground-truth diff, the cluster's items, and `references/mode-c-evaluate-feedback/verification.md`. Parent agent reconciles conflicting subagent verdicts and surfaces irreconcilable ones in the final plan.

### Output shape

Decision register: per item, `{id, channel, source, source_type, file:line, commit_id, verbatim_text, verdict, evidence, planned_action, implementation_status}`. Action plan grouped by verdict. PR-thread reply log if PR mode and replies were authorized.

### Hand-off contract

After Mode C: every received item has a verdict. If implementation was authorized, accepted items are fixed in order (blocking → simple → complex), each with a thread reply. If implementation was not authorized, the action plan is the deliverable and the user owns the next step. Never implement without authorization just because the verdict was ACCEPT.

## Mode D — Delegate to codex

### Trigger phrases

*"run codex review on this"*, *"codex review --uncommitted"*, *"have codex review the diff"*, *"codex review against main"*, *"have codex sanity-check this commit"*, *"second opinion from codex"*, *"non-interactive codex review"*.

### Required inputs

- `codex` binary on PATH (`command -v codex` succeeds; the skill is built against `codex-cli 0.130.0+`).
- One review target — see flag table below.
- Optional custom prompt (`[PROMPT]` positional arg) when the user wants a focused review (security only, perf only, against a spec doc, etc.).

### `codex review` flag surface (from live `codex review --help`)

The codex root-level `review` subcommand runs a one-shot code review non-interactively. Confirmed against `codex review --help` in `codex-cli 0.130.0`:

```
Usage: codex review [OPTIONS] [PROMPT]

Arguments:
  [PROMPT]                Custom review instructions. If `-` is used, read from stdin.

Options:
  -c, --config <key=value>   Override a config value (TOML-parsed; dotted paths supported).
                             Examples: -c model="o3", -c 'sandbox_permissions=["disk-full-read-access"]'.
      --uncommitted          Review staged, unstaged, and untracked changes.
      --base <BRANCH>        Review changes against the given base branch.
      --enable <FEATURE>     Enable a feature (repeatable). Equivalent to -c features.<name>=true.
      --commit <SHA>         Review the changes introduced by a commit.
      --disable <FEATURE>    Disable a feature (repeatable). Equivalent to -c features.<name>=false.
      --title <TITLE>        Optional commit title to display in the review summary.
  -h, --help                 Print help.
```

Target selection — pick exactly one:

| User intent | Flag |
|---|---|
| review the diff against `main` (or other base) | `--base main` |
| review uncommitted work (staged + unstaged + untracked) | `--uncommitted` |
| review the changes a single commit introduced | `--commit <SHA>` |
| review against the default base inferred from repo state | (no target flag — codex picks) |

Auxiliary flags worth exposing to the user:

- `--title "<text>"` — display in the summary header; useful when reviewing a `--commit` or `--uncommitted` change with no PR title.
- `--enable <feature>` / `--disable <feature>` — toggle codex features (`-c features.<name>=true|false`).
- `-c key=value` — override config. Common: `-c model="o3"` to pin model, `-c model_reasoning_effort="high"` to raise effort.
- `[PROMPT]` — positional. Custom review instructions. `-` reads from stdin (useful when the user has a long brief).

The root `codex review` does **not** accept `--json`, `-o`, or `--dangerously-bypass-approvals-and-sandbox`. If the user needs machine-readable output, structured logs, or a non-interactive sandbox-bypass surface, switch to `codex exec review` (the broader surface — see "When to use `codex exec review`" below).

### Procedure

1. **Pre-flight** —
   - `command -v codex` succeeds.
   - `git rev-parse --is-inside-work-tree` succeeds in cwd.
   - If `--base <BRANCH>` is chosen, `git rev-parse --verify <BRANCH>` succeeds (fetch first if not).
   - If `--commit <SHA>` is chosen, `git rev-parse --verify <SHA>` succeeds.
   - `codex login status` succeeds — OR `USE_CODEX_SKIP_CODEX_AUTH=1` is set when bearer-token / managed-companion / proxy auth is in use.
   - If any pre-flight fails, stop and report; do not improvise into `codex exec`.

2. **Pick the target flag** — one of `--base <BRANCH>`, `--uncommitted`, or `--commit <SHA>`. State the choice and rationale in one line.

3. **Compose the invocation.** Default (no custom prompt):

   ```bash
   codex review --base main
   ```

   With a custom prompt:

   ```bash
   codex review --base main "Review focuses on auth and session handling. Flag any missing input validation, replay vulnerabilities, or token leakage."
   ```

   With a long brief on stdin:

   ```bash
   cat brief.md | codex review --base main -
   ```

   With config overrides:

   ```bash
   codex review --base main -c model="o3" -c model_reasoning_effort="high"
   ```

4. **Run it.** Run interactively (the operator watches the stream) **or** capture stdout when the output is long:

   ```bash
   mkdir -p /tmp/codex-review
   codex review --base main "<prompt>" 2>&1 | tee /tmp/codex-review/$(date +%Y%m%dT%H%M%S)-review.md
   ```

   Capture the output verbatim — codex review prints the findings to stdout. When the review is long (> 200 lines or large repos), always tee to disk so the user can scroll without losing scrollback.

5. **Surface the result back to the user.** Default surface: paste the codex review findings inside chat under a clear heading. If long, write to disk and report the path. Do **not** silently drop or summarize codex output — the user asked for codex's opinion, surface it intact.

6. **Optional: chain into Mode A or Mode C.**
   - If the user asks Claude to *validate* codex's findings against the diff → switch to Mode A's per-item programmatic mode (one JSON object per item with `accepted | rejected | ambiguous`).
   - If the user asks Claude to *act on* codex's findings → switch to Mode C, treating codex output as one more reviewer (source `codex`, source_type `bot`).

### When to use `codex exec review` instead

`codex exec review` accepts the broader exec flag surface and is preferred when:

- the user wants `--json` JSONL events,
- the user wants `-o <file>` to write the last message to disk,
- the user wants `-m <model>` or `--dangerously-bypass-approvals-and-sandbox` (e.g. inside a CI worker / sandbox already),
- the user wants `--ephemeral` (no session files persisted),
- a fleet driver (multi-branch codex review orchestration) is the caller — that path always uses `codex exec review`.

Quick `codex exec review` invocation (one-shot, machine-readable):

```bash
mkdir -p /tmp/codex-review
codex exec review \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  --json \
  -o /tmp/codex-review/last.md \
  --base main \
  "Review the auth subsystem changes for replay and token-leak issues."
```

For per-branch convergence loops over multiple branches, do **not** wire that yourself — route to multi-branch codex review orchestration by writing a thin orchestrator that fans out `codex exec review --base <ref>` calls per branch (the dedicated dispatcher skill was retired).

### Subagent dispatch — when to fan out

Mode D is **single-agent by default** — the codex CLI is itself the worker; Claude orchestrates. Dispatch a subagent only when:

- the user names ≥ 3 review targets (e.g., three commits) that should each get their own codex pass, AND
- the targets are independent (not stacked).

In that case, dispatch one subagent per target with a self-contained prompt: target flag, optional brief, output path. Subagents collect codex output; the parent surfaces the merged result. For ≥ 2 branches with stacked dependencies, do **not** subagent — route to multi-branch codex review orchestration.

### Output shape

Codex's review text, surfaced verbatim (in chat or in `/tmp/codex-review/<ts>-review.md`). When the user asked Claude to act on the output, the next mode (A or C) owns its own output shape.

### Hand-off contract

After Mode D: the user has codex's review (text on stdout or markdown on disk). No git mutation, no PR opened, no fixes applied. Codex review never opens PRs (Mode B does); codex review never auto-applies fixes (the user does, or Mode C orchestrates).

## Cross-mode rules

1. **Never silently switch modes.** If, while running mode X, you realize the user actually wanted mode Y, stop, name the mismatch, and re-route. Do not just start doing Y.
2. **Never combine mode bodies in one output.** Modes have distinct output shapes; do not produce a "PR body and a review" simultaneously. If two modes are queued, run them in order, produce two outputs.
3. **Authorization is per destructive action.** `gh pr create` (Mode B), `gh pr review --request-changes` (Mode A), `gh api .../replies` (Mode C posting replies), `git push` (Mode B), and any `codex exec` with `--dangerously-bypass-approvals-and-sandbox` (Mode D) all require explicit user authorization. Authorization for one such action is not authorization for the next.
4. **No GitHub mutation in Modes A or D by default.** Mode A produces markdown by default; explicit submit/post/publish/comment switches it to GitHub mutation mode. Mode D never mutates GitHub at all.
5. **Voice discipline applies in every mode.** No gratitude, no praise, no apology, no agreement-before-verification — most load-bearing in Mode C but never wrong anywhere. `references/mode-c-evaluate-feedback/voice.md` is the canonical phrase reference.
6. **multi-branch codex review orchestration owns multi-branch convergence.** If the user names ≥ 2 branches and a "review/ship/merge/close out" intent, this skill routes to parallel `codex exec` orchestration — not Mode D, not Mode A.
7. **the now-retired codex review skill is a routing shim.** It points at this skill plus parallel `codex exec` orchestration. Do not restore the old runner; the canonical owners are `run-review` (this file) and multi-branch codex review orchestration.

## Final checks (run after every mode)

- [ ] Mode locked in one line at the start; no silent swaps.
- [ ] Exact target named (PR URL, branch comparison, PR number, commit SHA, or markdown file path).
- [ ] Output matches the mode's documented shape — no cross-contamination.
- [ ] No GitHub mutation unless the user explicitly authorized it (and authorization was per-action).
- [ ] No `git push`, `gh pr create`, `gh pr review --request-changes`, or `gh api .../replies` ran without explicit authorization.
- [ ] Voice: no gratitude, praise, apology, or agreement-before-verification anywhere in the output.
- [ ] All findings (Mode A) or items (Mode C) carry `file:line` evidence; Mode B carries ≥ 2 weaknesses + ≥ 1 reviewer question.
- [ ] Mode D output is surfaced verbatim or written to disk — never summarized away.

## Reference and script routing

### Mode A — Do a review (the old `review-pr`)

| Need | Load |
|---|---|
| End-to-end review procedure and goal validation | `references/mode-a-do-review/workflow/review-workflow.md` |
| Exact GitHub CLI and MCP equivalents | `references/mode-a-do-review/workflow/gh-cli-reference.md` |
| CI, static analysis, bot/scanner interpretation | `references/mode-a-do-review/workflow/automation.md` |
| Existing review threads, bot dedupe, team discussion state | `references/mode-a-do-review/workflow/comment-correlation.md` |
| File grouping, test/type pairing, initial cluster map | `references/mode-a-do-review/analysis/file-clustering.md` |
| Deep diff interpretation and base/head comparison | `references/mode-a-do-review/analysis/diff-analysis.md` |
| Large PR depth tiers and split suggestions | `references/mode-a-do-review/analysis/large-pr-strategy.md` |
| Cross-cluster coordination gaps | `references/mode-a-do-review/analysis/cross-cutting.md` |
| Full review dimension checklist | `references/mode-a-do-review/dimensions/review-dimensions.md` |
| Security-focused review | `references/mode-a-do-review/dimensions/security-review.md` |
| Performance-focused review | `references/mode-a-do-review/dimensions/performance-review.md` |
| Common correctness traps | `references/mode-a-do-review/dimensions/bug-patterns.md` |
| Language-specific pitfalls | `references/mode-a-do-review/dimensions/language-specific.md` |
| Severity examples and boundary cases | `references/mode-a-do-review/dimensions/severity-guide.md` |
| Output templates and verdict formats | `references/mode-a-do-review/output/output-templates.md` |
| Comment wording, batching, positive observations | `references/mode-a-do-review/output/communication.md` |
| Anti-noise checklist when review drifts | `references/mode-a-do-review/output/anti-patterns.md` |
| Read-only PR context collection | `scripts/parse-pr.sh` and `scripts/parse-pr.md` |
| Changed-file cluster map from a diff | `scripts/cluster-files.sh` and `scripts/cluster-files.md` |

### Mode B — Ask for review (the old `review-self`)

| Need | Load |
|---|---|
| Diff-walk commits, branching, push, `gh pr create` mechanics | `references/mode-b-ask-review/handoff-mechanics.md` |
| PR body / self-review structure with weaknesses + questions | `references/mode-b-ask-review/review-text-template.md` |
| Per-domain subagent prompt template and combination | `references/mode-b-ask-review/subagent-dispatch.md` |
| Counters when tempted to skip commits, push to default, shortcut the body | `references/mode-b-ask-review/rationalizations.md` |
| Backend (server, API, SQL, auth, infra) review angle | `references/mode-b-ask-review/domains/backend.md` |
| Client-side TS/JS / React / Vue / Svelte review angle | `references/mode-b-ask-review/domains/frontend-ts-js.md` |
| MCP server / `@modelcontextprotocol/sdk` review angle | `references/mode-b-ask-review/domains/mcp-server.md` |
| Visual changes / CSS / design tokens / a11y review angle | `references/mode-b-ask-review/domains/ui-engineering.md` |
| CLI / flag parsing / exit codes review angle | `references/mode-b-ask-review/domains/cli-tool.md` |
| Blog / docs / SKILL.md prose review angle | `references/mode-b-ask-review/domains/content-markdown.md` |
| Mixed diffs and fallback domain | `references/mode-b-ask-review/domains/generic.md` |

### Mode C — Evaluate received feedback (the old `review-feedback`)

| Need | Load |
|---|---|
| Reconstructing what was reviewed (commits → tool-trail → bash → uncertain) | `references/mode-c-evaluate-feedback/understand-changes.md` |
| Explore-subagent prompt template (self-contained, no session refs) | `references/mode-c-evaluate-feedback/subagent-dispatch.md` |
| Six-check verification lens against the codebase | `references/mode-c-evaluate-feedback/verification.md` |
| Multi-source clustering, conflict resolution | `references/mode-c-evaluate-feedback/multi-agent-consolidation.md` |
| GH `gh` commands for fetching reviews, replying in threads | `references/mode-c-evaluate-feedback/gh-review-workflow.md` |
| Action-plan output format per input mode (PR / session / markdown-doc) | `references/mode-c-evaluate-feedback/action-plan-output.md` |
| Forbidden phrases, "Fixed." alternatives, pushback templates | `references/mode-c-evaluate-feedback/voice.md` |
| RED-baseline excuses that bypass verify-before-implement; counters | `references/mode-c-evaluate-feedback/rationalizations.md` |
| Raw PR comment capture (all three channels) | `scripts/parse-pr-comments.sh` and `scripts/parse-pr-comments.md` |
| Cluster normalized JSONL into stable items before verification | `scripts/cluster-feedback.py` and `scripts/cluster-feedback.md` |

### Mode D — Delegate to codex (new)

| Need | Load |
|---|---|
| `codex review` flag table, prompt-on-stdin pattern, output capture | `references/mode-d-codex-review/codex-review-flags.md` |
| When to drop to `codex exec review` for `--json` / `-o` / `--ephemeral` | `references/mode-d-codex-review/codex-exec-review.md` |
| Pre-flight checks and failure-mode recovery | `references/mode-d-codex-review/pre-flight.md` |
