# Verification Lens — Checking Feedback Against the Codebase

Every feedback item gets the same six-check lens before you assign a verdict. This file is the checklist the parent agent *and* the Explore subagent both run.

## The six checks

### 1. Correctness

*Would the reviewer's suggested change break existing functionality?*

Trace the call sites of every function/value the suggestion touches:

```bash
# Find direct callers
grep -rn "functionName(" src/

# Find imports
grep -rn "import.*functionName" src/
grep -rn "require.*functionName" src/

# Find test references
grep -rn "functionName" test/ tests/ __tests__/
```

If the suggestion changes a function's behavior, every caller needs to tolerate the new behavior. Especially watch for:

- Error types returned (new exception class breaks old `catch` clauses)
- Return shape changes (optional field added is safe; field removed or renamed is not)
- Async-ness changes (sync → async breaks any caller that didn't `await`)
- Side-effect changes (adding a DB write or cache invalidation affects downstream tests)

**Verdict rule:** if the check reveals broken callers → PUSHBACK unless the suggestion includes migrating them.

### 2. YAGNI — is the feature actually used?

When a reviewer suggests "implement X properly" or "add Y capability", grep the codebase first.

```bash
# Is the affected function called anywhere outside tests?
grep -rn "theFunction" --include='*.ts' | grep -v '_test.ts\|\.test\.'

# Is the affected endpoint actually hit?
grep -rn "/api/path/foo" src/ client/

# Is the affected CLI flag used in docs, scripts, or README?
grep -rn "\-\-the-flag" docs/ scripts/ README.md
```

From obra's rule: "If we don't need this feature, don't add it."

**Verdict rule:** if grep returns zero callers → PUSHBACK with "suggest removal instead of expansion". If the reviewer's suggestion adds machinery for an unused code path, that's the wrong direction.

### 3. Stack fit — is this correct for THIS codebase?

A suggestion that's right in the abstract may be wrong for this project's stack. Check:

- Does the repo's `package.json` / `Cargo.toml` / `go.mod` have the library the reviewer references?
- Does the repo's style (lint config, existing patterns) match the suggestion?
- Does the repo's runtime support the suggestion? (e.g., "use top-level await" fails in CJS projects; "use `structuredClone`" fails on Node ≤ 16)
- If the reviewer cites a pattern, does the repo already use that pattern elsewhere, or is it foreign?

**Verdict rule:** if the suggestion brings in a new pattern where the repo has an existing idiomatic one → PUSHBACK with the existing-idiom reference. Consistency wins over cleverness.

### 4. Compat — legacy or compatibility reasons?

The current implementation may look wrong in isolation but exists for a reason. Check:

- `git log --follow` on the affected file to see when the current shape landed and why (commit messages, linked PRs/issues)
- `git blame` on the exact lines the reviewer is flagging
- Comments in the code near the line (`// LEGACY:`, `// COMPAT:`, `// hack for <version>`)
- Related docs (`docs/`, `CHANGELOG.md`, `MIGRATION.md`)

**Verdict rule:** if git history or code comments reveal a deliberate legacy/compat reason → PUSHBACK with the citation. The reviewer may not have seen the history.

### 5. Context — does the reviewer have the full picture?

Reviewers see the diff; they don't see the surrounding architecture. Check:

- Does the file's docstring / header comment explain a constraint the reviewer may not know?
- Are there related files (same module, same feature) the reviewer didn't look at?
- Is the reviewer assuming the wrong call site? (e.g., reviewer thinks the function is user-facing when it's internal)
- Is there an architectural decision recorded in `docs/arch/` or `AGENTS.md` / `CLAUDE.md` that the reviewer's suggestion violates?

**Verdict rule:** if the reviewer lacks context → PUSHBACK with the missing context surfaced. Link the doc / file / decision. Provide what the reviewer needed to see.

### 6. Architecture — conflicts with a prior decision?

The strongest form of "reviewer lacks context" — an actual documented decision.

Sources:
- `docs/arch/*.md`
- `docs/decisions/*.md` (ADRs)
- `README.md` principles section
- `CLAUDE.md` / `AGENTS.md` instructions
- `CONTRIBUTING.md` conventions

**Verdict rule:** if the suggestion conflicts with an architectural decision → stop and discuss with the human before proceeding. Do not silently re-decide. The decision may be re-openable, but that's a separate conversation.

## The verification worksheet

For each feedback item, fill in:

```
Item: <id>
Source: <reviewer>
Verbatim: <the comment>

Correctness check:
  Callers of affected code: <list>
  Any breaks? <yes/no + reason>

YAGNI check:
  Grep result for <path/symbol>: <count> callers
  Verdict: used / unused

Stack fit:
  Repo idiom: <pattern>
  Reviewer's pattern: <pattern>
  Match? <yes/no>

Compat:
  Git history of affected lines: <summary>
  Comments near the line: <any "LEGACY" / "COMPAT" flags?>

Context:
  Related files reviewer may not have seen: <list>
  Any architectural docs? <list>

Architecture:
  Relevant decisions: <list>
  Conflict? <yes/no>

VERDICT: ACCEPT | PUSHBACK | CLARIFY | DEFER | DISMISS
REASONING: <one or two sentences>
```

The Explore subagent runs this same worksheet per its prompt template.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Accept feedback because the reviewer "probably knows better" | Verify. "Probably right" is not a verdict. |
| Accept feedback without checking callers of the affected function | Grep for callers. Broken callers are the #1 bug shipped via review-acceptance. |
| Skip the YAGNI check on "implement properly" suggestions | Grep first. Unused code should be removed, not expanded. |
| Trust the reviewer's claim that "this is the repo's convention" | Grep for the convention across the repo. Convention is plural occurrences, not one. |
| Dismiss a bot comment as "just a bot" without the six-check run | Bots surface real bugs. Run the checks; only dismiss with a stated reason. |

## Speed notes

If you have 20 feedback items and the full six-check on each takes 5 minutes, that's 100 minutes. Triage first:

- **Obvious ACCEPT** (typo, rename, import missing): 30 seconds each. Do these in a batch.
- **Obvious DISMISS** (false positive from a bot, comment on unchanged code): 1 minute to state the reason.
- **Non-obvious** (suggested refactor, architectural change, "should we add X?"): full six-check.

A realistic mix is 70% obvious, 30% non-obvious. Don't run the full six-check where it's not needed, but don't skip it where it is.
