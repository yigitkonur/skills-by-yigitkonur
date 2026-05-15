# Master Misinformation Report — orchestrate-codex `scripts/*.md`

**Method:** 23 Opus agents read each script source-only (no .md access), wrote facts files to `/tmp/orchestrate-codex-audit/<name>.facts.md`. 22 Opus agents then diffed each facts file against the sibling .md doc, writing `<name>.discrepancies.md`. Comparison artifacts: 45 files / 3,121 lines.

## Verdict tally

| Verdict | Count | Docs |
|---|---|---|
| **fictional** (large parts invented) | 1 | `list-worktrees.md` |
| **misleading** (load-bearing wrong claims) | 9 | `audit-sizes.md`, `manifest-update.md`, `render-prompts.md`, `rescue-detect.md`, `run-batch.md`, `run-fleet.md`, `run-review.md`, `run-single.md`, `test-runner-contracts.md` |
| **partial** (mostly right, gaps + a few wrongs) | 12 | `apply-review-decisions.md`, `audit-fleet-state.md`, `bootstrap.md`, `classify-review-feedback.md`, `cleanup-worktrees.md`, `codex-flags.md`, `codex-json-filter.md`, `codex-monitor.md`, `orchestrate-codex.md`, `render-task-prompts.md`, `setup-worktree.md`, `test-monitor-integration.md` |
| **trustworthy** | **0** | — |

**Aggregate finding counts**: 87 CRITICAL · 113 MAJOR · 102 MINOR · 211 MISSING · 82 EXTRA = **595 findings across 22 docs**.

## Per-doc severity summary

| Doc | Verdict | CRIT | MAJ | MIN | MISS | EXTRA |
|---|---|---|---|---|---|---|
| `apply-review-decisions.md` | partial | 0 | 1 | 3 | 10 | 2 |
| `audit-fleet-state.md` | partial | 2 | 3 | 4 | 15 | 3 |
| `audit-sizes.md` | **misleading** | 4 | 3 | 4 | 9 | 6 |
| `bootstrap.md` | partial | 3 | 4 | 4 | 10 | 3 |
| `classify-review-feedback.md` | partial | 1 | 4 | 5 | 8 | 3 |
| `cleanup-worktrees.md` | partial | 6 | 5 | 5 | 9 | 3 |
| `codex-flags.md` | partial | 0 | 2 | 4 | 5 | 4 |
| `codex-json-filter.md` | partial | 3 | 3 | 5 | 12 | 2 |
| `codex-monitor.md` | partial | 5 | 5 | 5 | 13 | 4 |
| `list-worktrees.md` | **fictional** | 3 | 2 | 2 | 10 | 4 |
| `manifest-update.md` | **misleading** | 8 | 9 | 6 | 14 | 4 |
| `orchestrate-codex.md` | partial | 2 | 13 | 13 | 16 | 3 |
| `render-prompts.md` | **misleading** | 3 | 3 | 3 | 10 | 4 |
| `render-task-prompts.md` | partial | 0 | 2 | 5 | 8 | 2 |
| `rescue-detect.md` | **misleading** | 6 | 6 | 6 | 12 | 3 |
| `run-batch.md` | **misleading** | 4 | 7 | 5 | 12 | 6 |
| `run-fleet.md` | **misleading** | 9 | 16 | 9 | 10 | 9 |
| `run-review.md` | **misleading** | 13 | 7 | 5 | 18 | 6 |
| `run-single.md` | **misleading** | 7 | 6 | 4 | 11 | 4 |
| `setup-worktree.md` | partial | 3 | 5 | 4 | 9 | 3 |
| `test-monitor-integration.md` | partial | 1 | 4 | 5 | 6 | 3 |
| `test-runner-contracts.md` | **misleading** | 4 | 4 | 3 | 14 | 3 |

## Top-line patterns (themes that recur across multiple docs)

### Pattern A — Fabricated Monitor line shapes (run-batch, run-fleet, run-review, run-single)

The four runners produce stdout lines that the Monitor and downstream consumers parse. Docs systematically get them wrong:

- **Double-space → single-space.** Source emits `DONE␣␣<id>`, `FAIL␣␣<id>`, `SKIP␣␣<id>`. Every doc shows single space. Any regex written against the docs will silently miss every terminal line.
- **Fictional DONE fields.** `run-fleet.md` shows `DONE 01-search-rewrite (commits=3, post_verify=0)`. Source emits `DONE  <id> (runtime=Xs verify=<not-run|pass|fail>)`. `commits=N` and `post_verify=0` don't exist.
- **Fictional FAIL payloads.** `run-batch.md` shows `FAIL ... (codex_exit=1, see logs/...)`. Source uses `exit=N; see <log>` — `codex_exit=` is invented, separator is `;` not `,`.
- **Fictional SKIP payloads.** `run-batch.md`/`run-fleet.md` show `SKIP <id> (already done)`. Source SKIP has no parenthetical.
- **`run-review.md` DONE line** claims `DONE feat-auth (round=1 findings=<rounds-dir>/feat-auth.r1.md)`. Source is `DONE  <id> (runtime=Xs findings=<B>B json=<path>)`.

### Pattern B — Fictional signal-handling code

Three runners (`run-batch.md`, `run-fleet.md`, `run-review.md`) all claim:

> `trap 'kill 0' TERM INT EXIT` runs near the top

This string doesn't appear in any source. The actual mechanism is a named handler function (e.g. `_run_fleet_signal`) on `TERM INT` only (no EXIT), which does `kill -TERM <xargs_pid>`, then `pkill -TERM -g $$`, sleep 0.5, then `pkill -KILL -g $$`, exit 143. The EXIT trap is separate and only cleans up the worklist file. The "kill 0" claim is a single piece of misinformation that's been copy-pasted into three docs verbatim.

### Pattern C — "Soft warn / soft gate" lies on concurrency

Both `run-batch.md` and `run-fleet.md` claim concurrency above 20 is a "soft warn" or "soft gate". Source emits `FATAL JOBS=$JOBS exceeds 20; pass --i-have-measured` and exits 3. There is no warn code path. Worse, both docs omit:
- The `--i-have-measured` flag entirely (no way for the reader to discover the override).
- The `JOBS > 100` hard cap (no override possible at any value above 100).

### Pattern D — Wrong / incomplete exit code tables

Almost every doc has an incorrect exit-code table:

| Doc | What's wrong |
|---|---|
| `audit-fleet-state.md` | Exit 2 documented; **never emitted** (manifest-missing returns 1, not 2). Also hallucinates `--repair-dry-run`/`--repair-execute` flags as "Planned". |
| `bootstrap.md` | Exit 1 omits `cd "$PROJECT_DIR"` failure path. |
| `classify-review-feedback.md` | "Exit 1 if no major" — wrong; unclassified-only also exits 0. |
| `cleanup-worktrees.md` | Exit 2 only for "refusals" — actually also covers "not a git repo" and "entries not a list". Dry-run with refusals exits **1**, not 2 (doc says 2). Exit 4 covers lock timeout too (doc says "Manifest write failed" only). |
| `codex-json-filter.md` | Exit 1 documented "Internal error (rare)" — no such code path in script. Exit 2 omits invalid `--level` value path. |
| `manifest-update.md` | "Canonical — bash and python agree" header is **fictional**. Lock-timeout → py exits 1, sh exits 3. Dry-run → py always exits 1. Exit 5 only on bash. |
| `orchestrate-codex.md` | Exit-2 list omits `unknown_mode`. Exit-3 list omits `manifest_stale`, `schema_version_too_new`. |
| `run-batch.md` | Exit 3 description doesn't mention `MIN_BYTES` regex or `JOBS > 100`. Omits 143. |
| `run-fleet.md` | Concurrency cap shown only "above 20"; misses 100 hard cap. Omits 143. Misses 1 for manifest parse failure. |
| `run-review.md` | Exit 2 says only "codex missing" — also `jq` missing. Exit 1 omits invalid JSON case. Exit 3 omits invalid round number, invalid JOBS. Omits 143. |
| `run-single.md` | Exit-code table lists 0, 1, 2; source has 6 distinct exit-3 paths. |

### Pattern E — Missing CLI flags

Several docs hide entire flag surfaces from their inputs tables:

- **`orchestrate-codex.md`** — `--dry-run` missing from every mode's table; `--cwd` listed only for `single` (actually all modes); `--monitor-root` listed only for `exec` (also batch/single/review); `--run-id` shown only with `--force-new-run` (works standalone for exec/batch/single/review); rescue is missing `--concurrency`, `--i-have-measured`, `--redo`, `--json`; review is missing positional-branch form and file-auto-detection rule; tidy missing `--json`; audit missing `--cwd`.
- **`run-batch.md`** — `--i-have-measured`, `--only`, `--audit-report`, `--runner-log` all missing. Aliases (`--jobs`, `--prompts`, `--answers`, `--logs`) missing.
- **`run-single.md`** — `--output-schema`, `--resume-thread`, `--resume-last`, `--filter-level` all missing. Synopsis falsely marks `--manifest`, `--out`, `--jsonl` as required (all default sensibly).
- **`render-prompts.md`** — 4th optional positional arg `PLACEHOLDER` undocumented despite being a CLI-exposed override.

### Pattern F — Fictional features

Eight docs invent capabilities the script does not have:

| Doc | Fictional feature |
|---|---|
| `audit-fleet-state.md` | `--repair-dry-run` and `--repair-execute` "listed in earlier drafts" — no such flags exist in source. |
| `audit-sizes.md` | Entire `--json` flag/mode (fabricates JSON output example, "Total entries:", "Min/Median/Max", `[BELOW-FLOOR]`/`[BOTTOM-DECILE]` flag tags). Source emits multi-section text only, with `count/mean/stdev` (not min/median/max). |
| `bootstrap.md` | "Detects monorepo layout (multiple `package.json`s with workspace fields)" — script does no such detection. Also: positional `MONITOR_ROOT` argument (only env, not positional). |
| `classify-review-feedback.md` | "Tolerant of minor schema drift" reads as explicit feature; reality is `.get()` chains accidentally preserving extras. |
| `codex-flags.md` | `codex exec resume` table row — script source never mentions it. |
| `list-worktrees.md` | Entire tabular human output (`PATH BRANCH DIRTY UNPUSHED AHEAD`); entire JSON schema with wrong keys (`"dirty"`/`"ahead"` vs real `"dirty_count"`/`"commits_ahead_of_origin_main"`); wrong git commands cited. |
| `render-prompts.md` | "First occurrence wins on collision" — script aborts exit 1 on the second occurrence. Wrong slug char class (`[a-z0-9-]` instead of `[a-z0-9._-]`). Wrong awk env-var name (`CONTENT` vs real `PROMPT_VAL`). |
| `rescue-detect.md` | `MAX_JOBS=50` constant — doesn't exist. `never_started` rule names a `"review"` mode that script doesn't branch on. `running + dead pid → unknown` (actually → `failed`). |
| `run-fleet.md` | Auto-commit format `<emoji> <type>(<scope>): <task-id> auto-commit` — actual format is `agent($id): <prompt>`. "No commits despite exit 0 → failed" — not a real failure trigger. `COMMIT_LEVEL` default = 2 (actual = 3). |
| `run-review.md` | `PROJECT_DIR` defaults "from manifest workspace_root" — actually `$(pwd)`. `ALLOW_REUSE=1` "propagated by dispatcher" — hardcoded inline. `mode_state.review.base_branch` lookup — script reads `entries[].base_branch` only. `mode_state.terminal_state="three_all_rejected"` — script never writes this. |
| `run-single.md` | `LEVEL=verbose` env to enable verbose filter — actual is `--filter-level` flag which exports `CODEX_FILTER_LEVEL`. `last_error="json_event_dropped"` advisory — never written by source. `--reuse-worktree` "no new worktree created" — flag is vestigial, has zero effect. |
| `setup-worktree.md` | "Refuses to create the worktree inside the source repo" — no such guard; `WORKTREE_DIR_NAME=worktrees` explicitly places it inside. |
| `test-runner-contracts.md` | "PASS: 30" pass count — actual harness is 16 scenarios / 166 assertions. "deterministic `single` entry id" contract — never asserted. |

### Pattern G — Hidden divergence between sibling implementations

`manifest-update.md` is the standout. It documents `manifest-update.py` and `manifest-update.sh` as one surface under a header that reads *"Exit codes (canonical — bash and python agree)"*. They do not agree:

| Aspect | bash | python | doc says |
|---|---|---|---|
| Lock-acquire timeout | exit 3 | exit 1 (uncaught SystemExit) | "Exit 3 (both)" |
| Boolean coercion | allowlist of 5 leaf keys | every `true`/`false` literal | "Both agree on listed keys" (contradicts itself) |
| Dry-run mode | not supported | exit 1 always, no lock acquired | "Exit 0 on dry-run preview" (wrong) |
| Exit 5 | yes (missing jq) | never | "bash sibling only" (acknowledged here) |
| Temp file pattern | `<manifest>.tmp.XXXXXX` | `.manifest.XXXXXX.tmp` (leading dot, hidden) | `<manifest>.json.tmp.<rand>` (neither) |
| Lock backend | external `flock(1)` binary | `fcntl.flock` (Python) | "flock(LOCK_EX)" (ambiguous) |
| `--lock-timeout` flag | hardcoded 30s, no override | configurable, default 30s | not documented |
| `@file:<path>` | silent literal pass-through | reads file contents | "python only" (right but doesn't warn bash silently corrupts) |
| `--reason`/`--actor` flag position | parsed in any position **before** key=value | parsed independently | Doc shows them **after** key=value list — bash will reject as `bad pair`. |

A consumer treating these as interchangeable will mishandle every divergence.

### Pattern H — Missing env vars

15+ env vars across the skill are completely absent from their respective doc inputs tables. The most impactful:

| Env var | Doc that omits it | Effect |
|---|---|---|
| `ORCHESTRATE_CODEX_MODEL` / `ORCHESTRATE_CODEX_EFFORT` | `orchestrate-codex.md`, `run-fleet.md`, `run-batch.md`, `run-review.md`, `bootstrap.md` | Operators can't change codex model/effort without editing `codex-flags.sh`. |
| `ORCHESTRATE_QUIET_AFTER` | `orchestrate-codex.md` | Default `"1"`, affects monitor sentinel emission. |
| `ORCHESTRATE_SLUG` / `ORCHESTRATE_RUN_ID` / `ORCHESTRATE_MODE` | `bootstrap.md` | Slug-override / run-id-reuse / mode-stamping invisible. |
| `WORKTREE_DIR_NAME` / `WORKTREE_DIR` / `PROJECT_DIR` / `LINK_NODE_MODULES` / `LINK_ENV_FILE` / `PRISMA_GENERATE` | `setup-worktree.md` | 5 of 8 env vars missing from env table (audit-prompt called this out). |
| `AUTO_COMMIT` / `POST_VERIFY` | `run-fleet.md` | Master knobs for auto-commit and post-verify entirely hidden. |
| `CLAUDE_PLUGIN_DATA` | `audit-fleet-state.md`, `rescue-detect.md` | Controls codex-companion state dir resolution. |
| `ORCHESTRATE_DRY_RUN` | `test-runner-contracts.md` | Third env var that selectively gates dry-run; doc lists only 2 envs. |
| `ORCHESTRATE_MANIFEST` (env fallback to `--manifest`) | `run-fleet.md` | Doc says manifest is "required" but env fallback exists. |

### Pattern I — Wrong default values

| Doc | Field | Doc says | Reality |
|---|---|---|---|
| `run-fleet.md` | `COMMIT_LEVEL` default | 2 | 3 |
| `run-batch.md` | Default paths | `./prompts`, `./answers`, `./logs` | `prompts`, `answers`, `logs` (no `./`) |
| `bootstrap.md` | `MONITOR_ROOT` default | `resolveStateDir(cwd)/orchestrate-codex/logs` | `$STATE_DIR/logs` where `$STATE_DIR` already ends in `orchestrate-codex` |
| `bootstrap.md` | `PROJECT_DIR` default | `$PWD` | `$(pwd)` (different when symlinks resolve unevenly) |
| `audit-fleet-state.md` | Workspace-root `--workspace-root` resolution | "from manifest" | argparse `default=None`; resolution happens later |

## Top 20 most dangerous individual findings (cross-doc, severity weighted)

These would derail an agent following the doc on a real task:

1. **`codex-monitor.md`** — Five wrong things in the canonical tick-line template (timestamp shape "UTC-iso-z" is actually `HH:MM:SSZ`; `manifest=none` actually renders as `manifest=[manifest=none]`; spacing wrong; `manifest=parse-error` undocumented; note values shown without their literal parentheses).
2. **`run-fleet.md` / `run-batch.md` / `run-review.md`** — Fictional `trap 'kill 0' TERM INT EXIT` claim (3× duplicated lie).
3. **`run-batch.md`** — `JOBS > 20` documented as "soft warn"; reality is fatal exit 3. `--i-have-measured` override flag entirely undocumented.
4. **`manifest-update.md`** — "Canonical — bash and python agree" exit code table is false on at least four counts (lock timeout, dry-run signal, boolean coercion, temp file naming).
5. **`list-worktrees.md`** — JSON schema has wrong keys (`"dirty"`/`"ahead"` don't exist in source; real keys are `"dirty_count"`/`"commits_ahead_of_origin_main"`). Tabular output is entirely invented.
6. **`audit-sizes.md`** — Entire `--json` mode documented but doesn't exist; example output banner shape is fabricated; statistic labels wrong (`Min/Median/Max` vs real `count/mean/stdev`); `[BELOW-FLOOR]`/`[BOTTOM-DECILE]` inline flag tags fabricated.
7. **`rescue-detect.md`** — `running + dead pid` classified as `unknown` (says doc); actually `failed`. An operator triaging rescue would skip work the dispatcher should redispatch. Also: fictional `MAX_JOBS=50` constant.
8. **`run-review.md`** — `PROJECT_DIR` default "from manifest workspace_root" is fictional (actual `$(pwd)`). `ALLOW_REUSE` listed as input env (actually hardcoded inline). `--branches` positional form undocumented.
9. **`run-single.md`** — `LEVEL=verbose` env var to enable verbose filter doesn't exist. `--reuse-worktree` flag is documented as "records reuse"; it's vestigial with zero effect. Synopsis falsely marks three flags as required.
10. **`run-fleet.md`** — Auto-commit subject format `<emoji> <type>(<scope>): <task-id> auto-commit` is fictional. Real format: `agent($id): <prompt> [auto]`.
11. **`bootstrap.md`** — Positional `MONITOR_ROOT` argument advertised; script accepts no positional args. Monorepo-detection claim is fictional.
12. **`audit-fleet-state.md`** — Exit code 2 documented; never emitted.
13. **`render-prompts.md`** — Three load-bearing details wrong: wrong awk env var name (`CONTENT` vs real `PROMPT_VAL`); collision behavior inverted (says "first wins", actually aborts); slug char class wrong (`[a-z0-9-]` vs real `[a-z0-9._-]`).
14. **`cleanup-worktrees.md`** — Dry-run with refusals exits 1, not the documented 2. JSON `summary` field shape changes between dict (normal-path) and string (early-exit paths); doc shows only dict shape.
15. **`codex-json-filter.md`** — Claims "No `awk`"; script invokes awk twice. `orchestrate.done` sentinel and `--- single done (...) ---` output line entirely undocumented (Monitor stop-signal).
16. **`run-fleet.md`** — `COMMIT_LEVEL` default documented as 2; actual default is 3.
17. **`test-runner-contracts.md`** — `PASS: 30` shown as canonical output; harness now runs 16 scenarios / 166 assertions; no run command provided.
18. **`test-monitor-integration.md`** — Scenario 11 (`unknown_mode` dispatcher regression pin) entirely absent from doc; only this scenario spawns the real dispatcher subprocess.
19. **`orchestrate-codex.md`** — Example envelope shows `meta.pid === runner_pid`; structurally impossible (meta.pid is dispatcher process, runner_pid is detached child). `--dry-run` undocumented for every mode.
20. **`classify-review-feedback.md`** — Exit-0 condition documented as "≥1 major"; reality also exits 0 when `unclassified_n > 0`. Caller running a converge loop will treat unclassified-only round as converged.

## Cross-cutting recommendations

1. **Fix the line-shape lies first.** The Monitor parser is the most consumer-facing surface; every fabricated `DONE/FAIL/SKIP/START` shape will silently fail real grep/regex usage. Single PR can fix all four runners.
2. **Delete the `kill 0` lie everywhere.** It originated in the runners' own header comments and was copy-pasted into three docs. Fix runners' comments AND docs in one pass.
3. **Resolve the manifest-update.md "canonical" claim.** Either remove the unification claim and document py and sh separately, or pick one as primary and bash as legacy (or vice versa). The current doc fictionalizes parity that doesn't exist.
4. **Audit every exit-code table.** Adopt a convention: every `exit N` and `return N` in source maps to one row in the doc. Easy to mechanically check.
5. **Audit every flag table.** Map argparse / case-block in source → table row. The dispatcher (`orchestrate-codex.mjs`) systematically hides `--dry-run`, `--cwd`, `--monitor-root` on multiple modes.
6. **Stop describing dispatcher / orchestrator / Skill behavior in script docs.** Several docs (`run-review.md`, `classify-review-feedback.md`, `apply-review-decisions.md`, `rescue-detect.md`, `setup-worktree.md`) mix script-level facts with workflow narratives about features in other components (`mode_state.terminal_state`, `Skill(do-review)`, `WORKTREE_SETUP_HOOK`, `--accept-stale`). Source-only readers can't verify these claims; users get derailed.
7. **List EVERY env var in the inputs table, not selectively.** Pattern H shows 15+ env vars hidden. The audit prompt for `setup-worktree.md` specifically called out `WORKTREE_DIR_NAME`/`PROJECT_DIR` — only 1 of 8 env vars is in that doc's table.
8. **Verify output samples against source.** Several docs show "example output" that doesn't match what the script actually emits, often missing required header lines (`[run-fleet] manifest: ...`, `=== Runner log summary ===`, startup/shutdown sentinels).
9. **The fictional-feature docs warrant complete rewrites** (`list-worktrees.md`, `audit-sizes.md`, `manifest-update.md`, `run-batch.md`, `run-fleet.md`, `run-review.md`, `run-single.md`, `rescue-detect.md`, `render-prompts.md`). Editing won't catch the systemic invention pattern.

## Artifacts on disk

```
/tmp/orchestrate-codex-audit/
├── MASTER-REPORT.md                          ← this file
├── *.facts.md (23 files)                     ← source-only facts (Phase 1)
└── *.discrepancies.md (22 files)             ← facts vs doc diffs (Phase 2)
```

Per-doc deep dives are in the `*.discrepancies.md` files. Each has a Verdict, totals, and quote-quote-quote findings with line numbers in both source and doc.
