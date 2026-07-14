# Audit and Update Guide

How to audit a mature AGENTS.md hierarchy for drift and apply the corrections — falsifiable claims, grep verification, in-place edits.

## The two-phase contract

```
audit (claims → grep → findings) → triage → write (in-place edits) → re-audit
```

Auditors do not edit. Writers do not re-audit. The boundary is load-bearing because:

- Auditors that edit get rushed; they stop verifying carefully when the next claim is one Edit call away.
- Writers that re-audit double the work and silently disagree with the auditor's findings, leading to half-applied corrections.

Keep the phases separate.

## Drift categories

Every finding lands in one of four buckets. Use them in the Quality Report.

| Category | Definition | Impact | Fix urgency |
|---|---|---|---|
| **STALE** | The reference still points at the right concept; just the line number / file path / count is wrong | Low – cosmetic, but accumulates | Batch with surrounding edits |
| **INCORRECT** | The claim itself is no longer true — the rule, the count, the architecture, the symbol's purpose has changed | High – misroutes future agents | Fix this pass |
| **MISSING** | A file / export / verb / section that now exists but the doc still says "NOT YET LANDED" or doesn't mention | High – future agents won't know about it | Fix this pass |
| **UNVERIFIED** | The auditor couldn't cheaply confirm or refute (e.g. deeply nested helper, requires reading 500 lines of code) | Variable – flag with `[unverified]` in the doc | Defer to next pass or leave as `[unverified]` marker |
| **INTERNAL CONTRADICTION** | Same doc says X in §1 and not-X in §8 | High – picks a side for the reader | Pick the truth, propagate |

## Falsifiable-claim discipline

A claim is **falsifiable** if a grep / sed / wc / ls call can prove or disprove it. These are the only claims the auditor scores. Everything else is descriptive prose — leave it alone in update mode.

Falsifiable patterns to extract from a doc:

- `<file.ext>:<line>` or `<file.ext>:<line>-<line>` — line refs
- `` `<symbol>` `` in code-font where the symbol names a function, class, type, export, or constant
- "uses X" / "exports Y" / "imports Z" claims
- Numeric counts: "33 uses of `#hex`", "12 occurrences of `font-weight: 600`", "5 places call `formatDate`"
- Status claims: "NOT YET LANDED", "deferred", "removed in PR #N"
- Existence claims: "no test file exists", "no @vitejs/plugin-react"
- Schema literals: "`archive.compact.v1.1`" — sweep for the literal across multiple docs
- Verb / action enumerations: "data-action values: foo, bar, baz" — check for new verbs

For each, the auditor cites the exact verification command:

```bash
# line ref verification
sed -n '50,60p' src/services/audio-player.ts

# symbol existence
grep -n "function pickNextTrack" src/services/next-track.ts

# count recount
grep -oc "#3e463f" src/styles.css

# status check
ls src/services/leaderboard.ts 2>&1

# verb enumeration
rg -oN 'data-action="([^"]+)"' src/ui/ | sort -u
```

## Quality Report format

Ships **before** any edit. Headline + per-file detail + decision request.

```markdown
## Agent Instructions Quality Report

### Summary

| Surface | Count | Avg score | Stale-ref count | Notes |
|---|---|---|---|---|
| `AGENTS.md` | 6 | 9.7/10 | 47 lines flagged | All evidence-grounded; line refs drifted post-refactor |
| `CLAUDE.md` symlinks | 6 | ✅ | — | All correct |
| `REVIEW.md` | 6 | 9.8/10 | 12 | Severity tags accurate |
| Gap folders | 1 | — | — | `functions/` lacks local AGENTS.md |
| Native adapters | 0 | — | — | None present |

### File-by-file

#### `src/services/AGENTS.md` (246 lines)
**Score: 8 / 10** (was 10/10 at last edit; drift since `<commit-sha>`)

Findings:
- L9 "wraps HTMLAudioElement" — **INCORRECT**: now Web Audio (`AudioContext` + `AudioBufferSourceNode`); class at L140
- L62 "playTrack (:49)" — **STALE**: actual L204
- L186-197 outbound HTTP enumeration — **MISSING**: media-cdn.ts, leaderboard-api.ts, profile-cloud.ts added since
- §11 "Zero AbortController in src/" — **INCORRECT**: now used in 4 files

Drift driver: refactor commits `<sha-1>`, `<sha-2>` since doc's last edit `<doc-sha>`.

#### `src/ui/AGENTS.md` (266 lines)
**Score: 7 / 10**

...

### Recommended scope

- **Fix this pass (high-impact):** invalidated rules, missing content, internal contradictions — `src/services/AGENTS.md` §3 + §11, `src/AGENTS.md` §2 frequency table.
- **Batch with surrounding edits (low):** stale line refs that don't change meaning.
- **Author new (gap folders):** `functions/AGENTS.md` + `functions/REVIEW.md`, patterned after `src/services/AGENTS.md`.

### Awaiting user
1. Approve scope above? [y/n/edit]
2. Generate native review adapters (Copilot/Devin/Greptile) after corrections? [list/none]
```

After the user confirms, dispatch the auditor agents with the scope.

## Driving audit scope from git churn

The under-used steering signal. Skip the whole-doc audit; focus where the code has actually moved.

```bash
# Doc's last edit timestamp
DOC=src/services/AGENTS.md
T=$(git log -1 --format=%ct -- "$DOC")

# Files referenced by the doc (line-ref patterns)
REFS=$(grep -oE '\b[\w./-]+\.[a-z]+(:[0-9]+)?' "$DOC" | awk -F: '{print $1}' | sort -u)

# Source files that have churned since the doc was last touched
for f in $REFS; do
  COUNT=$(git log --since="@$T" --oneline -- "$f" 2>/dev/null | wc -l)
  [ "$COUNT" -gt 0 ] && echo "$COUNT commits  $f"
done | sort -rn
```

Files at the top of that list are where the auditor focuses. Files with zero commits since the doc's edit are unlikely to have drifted line refs.

For a single doc: pair this with `wc -l` then-vs-now on the largest referenced files. If `styles.css` grew 2,679 → 5,138 lines since the doc's edit, every line ref in that doc is stale by definition — recompute, don't grep one-by-one.

## Recounting frequency tables

Any numbered table in a doc (color frequencies, font-size frequencies, gap frequencies, escapeHtml call counts) is auto-recountable.

```bash
# Color hex counts in styles.css
for HEX in '#3e463f' '#9da89a' '#d8e6cd' '#98c684' '#2a2f29' '#5e7d56'; do
  COUNT=$(grep -oc "$HEX" src/styles.css)
  echo "$HEX  $COUNT"
done

# font-size counts
for SIZE in 9 10 11 12 13 14 15 16 18 24 28 40; do
  COUNT=$(grep -c "font-size: ${SIZE}px" src/styles.css)
  echo "${SIZE}px  $COUNT"
done

# escapeHtml call counts per UI module
for f in src/ui/*.ts; do
  [ -f "$f" ] && echo "$(grep -c escapeHtml "$f")  $f"
done | sort -rn
```

Run the recount, write the new numbers into the table. Do **not** "estimate" updated counts — that's the entire point of recounting.

## Internal-consistency checks

Within a single doc:

- Manifest tables in §1 must agree with later prose in §N. If §1 says "atom" and §8 says "persistentAtom", pick the truth.
- "Stub" / "NOT YET LANDED" entries must agree with `ls`. If the file exists, it's not a stub.
- Numbered count claims in prose (`"There are 4 breakpoints"`) must agree with code (`rg "@media \(max-width:"`).

Across docs:

- A symbol cited in `src/services/AGENTS.md` and again in `src/services/REVIEW.md` must have the same `file:line` in both.
- `i18n.ts` line numbers cited in `src/services/AGENTS.md` and in `src/services/REVIEW.md` must agree.

The auditor reports cross-doc disagreements; the writer picks the right one and propagates.

## Stub-graduation sweep

A common drift pattern: docs marked "NOT YET LANDED" for files that have since shipped. Sweep:

```bash
# Find stub claims
rg -nC1 'NOT YET LANDED|not yet built|deferred|will appear when' src/**/*.md AGENTS.md

# For each cited file in those stubs, check existence
ls src/services/leaderboard.ts src/services/profile-cloud.ts src/services/feedback.ts
```

Files that exist: remove the stub line, add a proper row in the manifest table.

## Symbol-rename detection

If the auditor reports "symbol `foo` no longer exists at the cited line":

```bash
# Was foo renamed? Find the commit that removed it
git log -S 'function foo' --oneline -- src/services/<file>.ts | head -5

# Find what replaced it
git diff <pre-rename-sha>..<post-rename-sha> -- src/services/<file>.ts | head -40
```

Update the doc to the new symbol name + line.

## Companion symlink checks

After writer edits, verify:

```bash
for AGENTS in $(find . -name AGENTS.md -not -path './node_modules/*'); do
  DIR=$(dirname "$AGENTS")
  CLAUDE="$DIR/CLAUDE.md"
  if [ -L "$CLAUDE" ]; then
    TARGET=$(readlink "$CLAUDE")
    [ "$TARGET" = "AGENTS.md" ] && echo "OK  $CLAUDE" || echo "BAD-LINK  $CLAUDE -> $TARGET"
  elif [ -f "$CLAUDE" ]; then
    grep -q '^@AGENTS.md' "$CLAUDE" && echo "WRAPPER  $CLAUDE" || echo "DRIFTED  $CLAUDE (not a symlink, not a wrapper)"
  else
    echo "MISSING  $CLAUDE"
  fi
done
```

For new gap folders: create the symlink (`ln -s AGENTS.md CLAUDE.md`).

## Re-audit gate (Phase 5)

Before declaring done:

1. `bash scripts/audit-agents-md.sh` — confirm surface counts match Phase 0 (or +N for newly created gap files).
2. Run the falsifiable-claim verification on 2–3 of the auditor's highest-impact corrections. If the writer applied them correctly, the new ref/count/symbol passes its grep.
3. Confirm no new `[unverified]` markers were introduced without a matching open-question entry.

## What NOT to do

- Audit headlines only and miss prose claims.
- Score whole files when only specific sections drifted — score per-section if drift is uneven.
- Rewrite sections in update mode because they "could be clearer". Update preserves voice.
- Strip the audit's `[unverified]` markers without verifying — they exist because the auditor couldn't cheaply confirm.
- Add new sections to capture new code. New scope = a separate `init-agent-config` pass.

## Final rule

If the audit says a file is mostly correct, tighten only the drifted lines. The goal is fewer agent mistakes, not prettier diffs.
