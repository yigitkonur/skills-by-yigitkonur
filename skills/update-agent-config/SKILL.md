---
name: update-agent-config
description: "Use skill if you are auditing AGENTS.md/CLAUDE.md/REVIEW.md hierarchies for drift after refactors: stale file:line refs, frequency-table recounts, invalidated rules, or missing AGENTS.md for code-bearing gap folders."
---

# Update Agent Config

Refresh a **mature** AGENTS.md hierarchy that has drifted from current code. Audit first, in evidence. Then dispatch parallel writers fed by the audit. Add files only for code-bearing folders that genuinely lack one. Preserve voice, structure, length — patch, do not rewrite.

This skill assumes the AGENTS hierarchy already exists. For greenfield creation of root + folder AGENTS.md files, route to `init-agent-config`.

## When to use

- *"audit our AGENTS.md / CLAUDE.md / REVIEW.md files"*
- *"the AGENTS docs are stale after the recent refactor — refresh them"*
- *"verify every `file:line` reference in `src/AGENTS.md` is correct"*
- *"recompute the color / font-size / spacing frequency tables in `src/AGENTS.md`"*
- *"the doc claims X but the code now says Y — sweep the drift across all docs"*
- *"find every code folder without an `AGENTS.md` and write one"*
- *"the schema version changed; sweep all docs that quote the old literal"*
- *"docs marked `NOT YET LANDED` for files that now exist — fix the manifest tables"*

## Do NOT use for

- **Greenfield setup** (root + folder AGENTS.md from scratch) → use `init-agent-config`
- **PR review** → use `run-review` Mode A
- **Skill creation/maintenance** → use `build-skill`
- **One-off doc fix** where the audit overhead doesn't pay off (e.g., correct a single typo)
- **Native review adapter generation** (Copilot/Devin/Greptile) when AGENTS is already accurate — the existing `init-agent-config` Step 12 covers that

## File responsibilities (same contract as init)

| Surface | Purpose | Update-mode concern |
|---|---|---|
| `AGENTS.md` | How agents should work, where code lives, what local boundaries exist | Refresh refs, recount tables, drop "NOT YET LANDED" stubs that landed |
| `CLAUDE.md` | Compatibility companion symlink → `AGENTS.md` | Verify symlink integrity; create for new gap folders |
| `REVIEW.md` | What diffs should be flagged, protected, or held to a higher bar | Update severity refs; drop trigger phrases for rules that became false |
| Folder `AGENTS.md` | Local delta only — never restate root | Same; add for newly-discovered code-bearing folders |

## Non-negotiables

Hard guardrails — read every run.

1. **Audit before editing.** Always. The Quality Report ships before any Edit/Write call.
2. **Falsifiable claims only.** Every statement that names `file:line`, a function/symbol/CLI flag, or a count is verified by `grep -n` / `sed -n` / `wc -l` against current HEAD before correction. Drift is a fact, not a guess.
3. **Parallel Opus auditors then parallel Opus writers.** Two phases, hard boundary. Auditors do not edit; writers do not re-audit (they trust their brief).
4. **Preserve voice, structure, length.** Patch in place. Don't rewrite a 313-line file into 280 lines because the new wording is "cleaner". The goal is accurate, not prettier.
5. **Internal consistency.** When fixing §1, check §8 doesn't contradict. When the manifest table says "Y is a stub", check the prose later doesn't already describe Y as landed.
6. **Gap folders get new files patterned after the closest sibling.** No greenfield template. The closest sibling `AGENTS.md` is the model — its tone, density, and section structure transfer.
7. **Companion `CLAUDE.md` symlinks intact.** Verify post-edit. Create for new gap folders. Fallback to `@AGENTS.md` wrapper only when symlinks are forbidden — call it out.
8. **Re-audit before declaring done.** `scripts/audit-agents-md.sh` runs once before edits and once after. Diff the surface counts.
9. **No new sections without 3+ repo-specific facts.** Updating ≠ expanding. If a section is missing because the code is missing, leave it missing.

## Anti-derail guardrails

| Derail | Correction |
|---|---|
| Editing the doc before the audit completes | Audit-first is the contract; the Quality Report ships first |
| Rewriting from memory ("I recall the file changed") | Always re-grep / re-sed; cite line numbers from the actual file |
| Auditor agent also edits | Auditors produce findings only; writers act |
| Writer agent re-runs the audit | Writers trust the brief; re-grep only for the specific recount they're applying |
| Frequency tables left untouched because "they're roughly right" | Recount every numbered table via grep — the cascade of additions silently shifts counts |
| "NOT YET LANDED" stub claims left in place | `ls` the alleged-missing files; if they exist, document them and remove the stub line |
| Internal contradictions silently surviving (§1 row vs §8 prose) | Cross-check the rule in §N against every later reference to the same symbol/file |
| Voice rewrite ("I made it more readable") | Patch in place; if you can't make a surgical edit, the change isn't ready |
| Auditing only headlines, missing prose claims | Every paragraph with a `file.ext:line` token is in scope |
| Adding new sections during update | Update mode only — new content goes to a separate `init-agent-config` pass |

## Scripts

Resolve script paths relative to this skill directory.

| Script | Use when | Mutates |
|---|---|---|
| `scripts/audit-agents-md.sh` | Phase 0 inventory + post-edit re-audit: existing surfaces, line counts, companion symlink status, duplicate-source risk. See `scripts/audit-agents-md.sh.md`. | No |

The init-only `scaffold-agents-md.sh` was dropped — update-mode never emits greenfield skeletons.

## The Five Phases

```
mature AGENTS hierarchy with drift after code churn
                            │
       Phase 0 — Scan + Gap detection + Last-edit churn signal
                            │
       Phase 1 — Quality Report (BEFORE any edit; ask user)
                            │
       Phase 2 — Parallel Opus auditor dispatch (falsifiable claims)
                            │
       Phase 3 — Triage findings + scope confirmation
                            │
       Phase 4 — Parallel Opus writer dispatch (patch in place + author gap files)
                            │
       Phase 5 — Post-edit re-audit + commit + push
                            │
                   refreshed hierarchy
```

Each phase has a gate. Do not skip forward. See `references/audit-and-update.md` for the per-phase detail and Quality Report format.

### Phase 0 — Scan + Gap detection + Churn signal

Three reads, no writes:

1. **Existing surfaces.** `bash scripts/audit-agents-md.sh` from the repo root — lists every `AGENTS.md`, `CLAUDE.md` (with symlink target), `REVIEW.md`, native adapter, and current line counts.
2. **Gap folders.** `tree -dL 2 .` (or `tree -dL 3` for monorepos). Cross-reference: which **code-bearing** folders (have `*.ts` / `*.py` / `*.rs` / etc., usually with a `tsconfig.json` / `package.json` of their own) have **no** local `AGENTS.md`? Those are gap candidates. Skip data/asset folders, generated output, and planning artifacts.
3. **Churn signal — the steering trick.** For each existing doc, get its last edit timestamp:
   ```bash
   git log -1 --format=%ct -- <doc>
   ```
   Then for the source files that doc references (anything matching `\b[\w./-]+\.[a-z]+:\d+\b` in the doc), list commits since that timestamp:
   ```bash
   git log --since=<timestamp> --oneline -- <referenced-file>
   ```
   **This is the audit scope.** If the doc was last touched at `T` and `styles.css` has had 12 commits since `T`, that file's line refs and counts are guaranteed stale. Drive auditor focus there. Files with zero churn since the doc's last edit can be lower-priority.

### Phase 1 — Quality Report (BEFORE editing)

Output the report — no edits yet. Format in `references/audit-and-update.md`. Headline rows:

| Surface | Count | Avg score | Stale-ref count | Notes |
|---|---|---|---|---|
| `AGENTS.md` | N | X/10 | M lines flagged | … |
| `CLAUDE.md` symlinks | N | ✅ / ⚠ | — | … |
| `REVIEW.md` | N | X/10 | M | … |
| Gap folders | N | — | — | List |
| Native adapters | N | — | — | List |

Per-file: score + 5-line summary of what's drifted (line refs / invalidated rules / missing content / internal contradictions). Then ask the user:

1. Which files to fix (default: all flagged as drift > 0)
2. Which gap folders to fill (default: code-bearing ones only)
3. Skip the post-edit native-adapter regeneration unless explicitly requested

### Phase 2 — Parallel Opus auditor dispatch

After user confirms scope. Dispatch **3–5 parallel Opus agents**, one per logical group of files. Sample grouping for a typical repo:

- Auditor A: root `AGENTS.md` + `REVIEW.md` + `scripts/AGENTS.md` + `scripts/REVIEW.md` (orchestration + pipeline)
- Auditor B: `src/AGENTS.md` + `src/REVIEW.md` (design system / styles)
- Auditor C: `src/services/AGENTS.md` + `src/stores/AGENTS.md` + their `REVIEW.md` (TypeScript code refs)
- Auditor D: `src/ui/AGENTS.md` + `src/ui/REVIEW.md` (UI module contract)

Each auditor follows the **falsifiable-claim discipline** — see `references/agent-dispatch.md` Auditor section. They:

- Quote each statement that names `file:line` / symbol / count
- Verify with `grep -n` / `sed -n` / `wc -l` / `ls`
- Report **VERIFIED ✓** / **STALE: <actual>** / **INCORRECT: <reality>** / **UNVERIFIED: <reason>**
- Do **not** edit. They return a findings list only.

Use the churn signal from Phase 0 to focus their attention.

### Phase 3 — Triage findings

Classify the returned findings:

- **High impact** — rule is now wrong (e.g., "every `$playback.set` must live in audio-player.ts" is no longer true). These are dangerous; future agents will misroute work.
- **Medium impact** — content missing (new files, new exports, new verbs not in the manifest). Future agents won't know about features.
- **Low impact** — line numbers shifted but semantic content correct. Cosmetic; batch these.
- **Internal contradiction** — same doc says X in §1 and not-X in §8. Pick the truth, propagate.

Decide which to fix this pass vs. defer. Default: fix high + medium; fix low only in surrounding edits.

### Phase 4 — Parallel Opus writer dispatch

Dispatch **3–5 parallel Opus writers** with the same grouping. Each writer gets:

- Target file paths
- The auditor's findings list for that group
- Instructions to **preserve voice, structure, length** (see Non-negotiable #4)
- Permission to re-grep for recounts (frequency tables) but not re-audit
- For gap folders: pattern after the closest sibling `AGENTS.md` (cite which one)

Each writer applies Edit calls in place. They do **not** add new sections. They report which paths they touched and a 3-line summary per file. See `references/agent-dispatch.md` Writer section.

### Phase 5 — Post-edit re-audit + commit + push

1. Re-run `bash scripts/audit-agents-md.sh` — diff against the Phase 0 snapshot. Surface counts should match (or +N for gap folders newly created). No new orphan symlinks.
2. Spot-check 2–3 high-impact corrections via grep — confirm the new ref points where the doc claims.
3. Commit. One commit per concern:
   - `docs(agents): refresh stale refs + counts after <churn-event>`
   - `docs(<folder>): add AGENTS.md + REVIEW.md` (separate commit per gap folder if substantial)
4. Push. Watch CI (typecheck on docs is no-op; the push exists to land the refresh).

## Creative steering signals

These are the under-used patterns. Reach for them when the audit feels generic.

- **`git log` since doc's last edit** (Phase 0) — drives scope toward files that have actually churned. Don't audit the whole tree blindly; audit where the diff is.
- **File-size delta as drift proxy.** If a referenced file grew 2× since the doc's last edit (e.g., `styles.css` 2,679 → 5,138 lines), every line ref is stale by definition.
- **`ls` against "NOT YET LANDED" stubs.** A doc's stub-table is a falsifiable claim too. `ls` each alleged-missing file; if it exists, the stub is wrong.
- **Frequency-table auto-recount.** Every numbered table in the doc (colors, font-sizes, spacing, escape-html call counts) is recountable via `grep -c`. Recount before correcting.
- **Cross-doc consistency.** If two docs independently cite the same symbol's location, both must agree. A pre-edit grep finds the surviving stale one.
- **Symbol rename detector.** If the auditor finds "function `foo` no longer exists at the cited line", run `git log -S 'foo' -- <file>` to find the rename commit. Update to the new name.
- **Stub-graduation sweep.** Any line containing "NOT YET LANDED" / "not yet built" / "deferred" is a candidate for an `ls`-based audit.
- **Test-file existence cross-check.** Manifest tables that claim "Tests: none" can be falsified by `ls <module>.test.*`.

## Reference routing

Read the smallest reference set that unblocks the current decision.

| Need | Reference |
|---|---|
| Quality Report format, drift categories, post-edit verification, falsifiable-claim discipline | `references/audit-and-update.md` |
| Auditor + writer prompt scaffolds (parallel-Opus dispatch) | `references/agent-dispatch.md` |
| AGENTS authoring, folder scoping, WHAT/WHY/HOW filter (applies to in-place edits too) | `references/agents-md-format.md` |
| Companion `CLAUDE.md` symlinks, native review adapter rules, cross-agent surfaces | `references/agent-entrypoints.md` |
| `REVIEW.md` purpose, root/scoped split, severity tagging | `references/review-context.md` |

### Quick-start mapping

| Situation | Start with | Then read |
|---|---|---|
| Big refactor just landed; sweep all docs | `references/audit-and-update.md` | `references/agent-dispatch.md` |
| Just need to refresh frequency tables | `references/audit-and-update.md` (recount section) | — |
| Add AGENTS.md for newly-discovered code folder | `references/agents-md-format.md` | `references/agent-entrypoints.md` |
| REVIEW.md needs severity refresh after rule changes | `references/review-context.md` | `references/audit-and-update.md` |

## Final output expectations

When you finish a run, return:

1. **Phase 0 scan** — surface counts before and after; gap folders identified
2. **Quality Report** — pre-edit, with per-file scores and drift findings
3. **Triage decision** — which findings landed this pass, which deferred
4. **Files edited + files authored** — explicit list with line-count deltas
5. **Companion symlink status** — verified intact; new ones for gap folders
6. **Re-audit diff** — Phase 5 output vs Phase 0
7. **Commits + push state** — commit SHAs, CI status
8. **Unresolved unknowns** — `[unverified]` markers left in place, why
