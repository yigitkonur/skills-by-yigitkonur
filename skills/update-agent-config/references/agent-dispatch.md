# Agent Dispatch Scaffolds

Reusable prompt templates for the two parallel-Opus phases: **auditor** (falsifiable-claim verification) and **writer** (in-place corrections + gap-folder authoring). Fill the placeholders with repo evidence before dispatching.

## Contents

- [Auditor Agent](#auditor-agent) — Phase 2
- [Writer Agent — In-Place Correction](#writer-agent--in-place-correction) — Phase 4
- [Writer Agent — Gap-Folder Author](#writer-agent--gap-folder-author) — Phase 4 (new files)

## Auditor Agent

The auditor reads existing AGENTS / REVIEW docs, extracts every falsifiable claim, verifies against current code, and returns a findings list. **It does not edit.**

Dispatch one auditor per logical group (3–5 in parallel for a typical repo). Each prompt 500–1500 words.

```text
You are an auditor in a multi-phase AGENTS.md refresh. Your job is to find drift between the docs and the current code state. **Do not edit anything — just produce a list of inaccuracies.**

Repo: <absolute path>
Current HEAD: <SHA> (mature; significant recent changes: <one-line summary of churn>)

## Files to audit

1. <absolute path to AGENTS.md #1> (<N> lines)
2. <absolute path to REVIEW.md #1> (<N> lines)
... up to ~4 files per auditor

## Drift hypotheses (from main agent's Phase 0 scan)

<paste the specific things you already know are stale, e.g.:>
- Schema version was bumped from v1.1 → v1.3 — sweep doc literal references
- styles.css grew 2,679 → 5,138 lines since these docs were last edited (commit <sha>) — every styles.css line ref is presumed stale
- Files marked "NOT YET LANDED" that may now exist: <list>
- Refactor commit <sha> moved every $playback.set out of audio-player.ts into stores/playback.ts action helpers

## Verification discipline

For each statement that names a specific `file:line`, `file:line-range`, a function/symbol/CLI flag, or a count, verify against current code:

- `grep -n "<symbol>" <file>` to confirm symbols still exist where claimed
- `sed -n 'L_START,L_ENDp' <file>` to confirm lines say what the doc claims
- `wc -l <file>` to confirm size claims
- `ls <file>` for existence claims (especially "NOT YET LANDED" stubs)
- `git log -S "<symbol>" --oneline -- <file>` if a symbol moved (rename/refactor)
- `grep -oc "<pattern>" <file>` to recount frequency-table entries
- For Make targets and npm scripts: check actual `Makefile` and `package.json`

For each falsifiable claim, report exactly one of:

- **VERIFIED ✓** — claim matches current code
- **STALE: <actual state with file:line>** — concept still right, location/count drifted
- **INCORRECT: <reality>** — claim itself is now wrong (rule invalidated, architecture changed, status flipped)
- **MISSING: <new content the doc should mention>** — code has something the doc doesn't acknowledge
- **UNVERIFIED: <why couldn't check>** — auditor couldn't cheaply confirm; flag for `[unverified]` marker

## Output format

```
## File: <path>
- L<N> "<exact quoted claim>" — VERIFIED ✓
- L<N> "<exact quoted claim>" — STALE: <actual state>
- L<N> "<exact quoted claim>" — INCORRECT: <reality + file:line evidence>
- L<N> "<exact quoted claim>" — MISSING: <new fact the doc should add>
- L<N> "<exact quoted claim>" — UNVERIFIED: <why>
```

Show the verification commands you ran for the non-trivial cases. Skip statements that are evidently general guidance (no file:line, no count, no symbol). Focus on the falsifiable ones.

End with a 3-bullet summary of the largest drifts found across all your files.

## Constraints

- **Read-only.** No Edit, no Write, no Bash mutations.
- **Be ruthless.** These files were authored months ago and the codebase has shifted. Default-suspect every line ref, every count.
- **Cite evidence, not opinion.** A claim is wrong because grep returned X, not because "it seems off".
- Aim for <800 words in the findings list. Don't audit prose that has no falsifiable content.
```

### What to vary per auditor

- **Files** — disjoint sets per auditor.
- **Drift hypotheses** — give each auditor the specific churn signals from Phase 0 that affect their files.
- **Domain hint** — if files are domain-specific (design system, audio engine, etc.), say so so the auditor knows which grep patterns matter.

## Writer Agent — In-Place Correction

The writer receives the auditor's findings and applies Edit calls in place. **It does not re-audit.**

Dispatch one writer per logical group, same grouping as auditors. Prompts 500–2000 words.

```text
Apply corrections to <N> files at <repo path>. Use the Edit tool. **Preserve voice, structure, and length** — do not aggressively rewrite. Re-grep / re-sed only to verify current line numbers before each edit. Repo HEAD: <SHA>.

## Files to update

1. <path #1> (<N> lines)
2. <path #2> (<N> lines)
...

## Audit findings to fix

<paste the auditor's findings list for these files verbatim>

For each finding:
- **STALE** → update the line number / file path / count to current
- **INCORRECT** → rewrite the rule/claim to match current reality, citing file:line evidence
- **MISSING** → add the new content where it belongs in the existing section structure (do not invent new sections)
- **UNVERIFIED** → leave the original claim or mark `[unverified]` if the doc supports it

## Approach

For each file:
1. Read the current content.
2. Re-verify line refs and counts via `grep -n` / `sed -n` / `wc -l` before each edit — the auditor's findings may be slightly stale by now, and recount is cheap.
3. Apply Edit calls in place. One concern per Edit (don't bundle).
4. Preserve the existing section structure. Don't renumber. Don't reorder.
5. Length should stay within ±5% of original. If a single section grew substantially, you're rewriting, not patching — stop and reconsider.

## Frequency tables

When the audit flagged a frequency-table recount: re-grep against the current source file, fill in the new counts. Examples:

```bash
# Color counts
for HEX in <list>; do grep -oc "$HEX" src/styles.css; done

# escapeHtml call counts per UI module
for f in src/ui/*.ts; do grep -c escapeHtml "$f"; done
```

Write the new counts, not the auditor's numbers — recompute fresh.

## Internal consistency

If the audit flags a §1 row contradicting §8 prose: pick the truth (verify against code), edit both sections to match. Don't leave one stale while fixing the other.

## Stub graduation

For each "NOT YET LANDED" / "deferred" entry the audit flagged as now-shipped:
1. Add a proper row in the manifest table describing the file.
2. Remove the stub line.
3. If the doc has a §1 manifest table and a separate §N "Stubs" paragraph, edit both.

## Forbidden

- **No new sections.** Update mode only edits existing structure. If the code has new scope, that's a separate `init-agent-config` pass.
- **No voice rewrites.** Surgical edits only.
- **No "while I'm here" cleanups.** If the audit didn't flag it, don't touch it.
- **No commits/pushes.** The main agent handles git.

## Output

Report: 3-line summary per file of what shifted (e.g., "Updated 12 line refs, fixed §3 rule about HTMLAudioElement → Web Audio, dropped two stub-marked entries"). Then the absolute path list.
```

### What to vary per writer

- **Files** — same grouping as the corresponding auditor.
- **Audit findings** — feed the relevant subset of the auditor's report verbatim.
- **Stylistic constraints** — if the file has a known voice quirk (e.g., uses `**bold**` for verb names), call it out.

## Writer Agent — Gap-Folder Author

When the Phase 0 scan found a code-bearing folder without a local `AGENTS.md`. **Pattern after the closest sibling — no greenfield template.**

Prompt 1500–3000 words because the author needs to read the target folder's code AND the sibling AGENTS.md as a stylistic model.

```text
Write `<absolute path>/AGENTS.md` and `<absolute path>/REVIEW.md` for the <folder name> folder. Do NOT create the CLAUDE.md symlink — the main agent will.

## Context

The repo has a mature AGENTS hierarchy with files at: <list root + all existing folder AGENTS.md paths>. The folder at <gap path> is the only code-bearing folder without local guidance.

Code in this folder:

```
<paste `find <gap path> -type f -not -name '*.test.*' | head -20`>
```

## Style template — MIMIC this file

Read `<closest sibling AGENTS.md path>` BEFORE writing as the stylistic template. It sets the bar for:
- evidence-grounded prose (file:line refs everywhere)
- "Verified DON'Ts" closing section
- Density (information per line, table layouts where they fit)
- Tone (terse, no marketing, direct)

Also read the corresponding `<sibling REVIEW.md>` as the model for REVIEW format.

## What to discover

Before writing, read the actual code in the target folder. Capture:

1. **Module manifest** — every file in the folder + its role + exports + tests
2. **Canonical handler/render/entry shape** — what's the common code skeleton?
3. **Cross-file conventions** — does it have a `_shared.ts` / `helpers.ts` pattern?
4. **Runtime / environment differences from parent** — e.g., Workers vs browser, server vs client
5. **Test pattern** — vitest? jest? in-band? fake-env?
6. **Error model / response shapes** — what status codes, what envelope, what failure modes
7. **Verified DON'Ts** — what mistakes would a coder make if these docs didn't exist?

## What to write

### `<path>/AGENTS.md` (target ~150 lines)

Section sketch (adapt to fit what the folder actually has):

1. Framing paragraph — what this folder owns, how it differs from src/
2. Module manifest (table)
3. Canonical handler/render shape (with file:line citation)
4. Common patterns (e.g., `_shared.ts` rule, D1 binding access, etc.)
5. Local dev incantation (exact CLI, verified against Makefile / package.json)
6. Testing pattern (from an actual test file)
7. Error model
8. The no-throw rule (or equivalent invariant)
9. Verified DON'Ts (≥6 items, each with `file:line` evidence)
10. Open questions / `[unverified]` (be honest — flag anything you couldn't validate)

### `<path>/REVIEW.md` (target ~50 lines)

Section sketch:

1. Framing — diff-scrutiny rules; operating guidance lives in `<path>/AGENTS.md`
2. Critical Areas (numbered list, each tagged **Block** or **Hold** with evidence)
3. Security (auth, validation, escaping)
4. Conventions
5. Patterns
6. Trigger words for deeper review (grep-able phrases)

## Style requirements

- **Concrete `file:line:column` references**, not "see the file".
- **Each statement is falsifiable** — reviewer can grep and confirm.
- **`[unverified]` for any claim you couldn't validate.**
- **No marketing language.** Direct, terse.
- **Verified DON'Ts section mandatory**, ≥6 items.
- **Complete enough that a coder editing this folder need not read another AGENTS.md.**

## Constraints

- Do NOT write the CLAUDE.md symlink — the main agent owns that.
- Do NOT modify any file outside the target folder.
- Do NOT invent claims — if the code doesn't show it, don't write it.
- Length should be roughly in line with the sibling template you used.

## Output

Report: absolute paths created, 4-sentence summary of AGENTS.md content + 3-sentence summary of REVIEW.md content.
```

### What to vary per gap-folder dispatch

- **Closest sibling** — pick the AGENTS.md whose runtime/concerns are most similar. For a Pages Functions folder, `src/services/AGENTS.md` is closer than `src/ui/AGENTS.md`.
- **Code reading hints** — if the folder has unusual conventions (e.g., a `_shared.ts` per-subfolder pattern), call it out so the author looks for it.
- **Length target** — match the sibling's density.

## Why three scaffolds, not one

- The **auditor** must be cognitively committed to *reading and verifying*, not *fixing*. Mixing the role contaminates the audit.
- The **in-place writer** must trust the audit and stay surgical. If it re-audits, it second-guesses and rewrites.
- The **gap-folder author** is doing a different cognitive task: discovery + drafting, more like `init-agent-config`'s writer pass. Different brief, different freedom.

Dispatch them as separate agents. Don't try to merge.
