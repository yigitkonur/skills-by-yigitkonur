# Derailment Test: run-playwright on "Navigate HN, fill forms, multi-tab, responsive screenshots"

Date: 2025-03-11
Skill under test: run-playwright
Test task: Navigate Hacker News, fill a search form, manage multiple tabs, take responsive screenshots
Method: Follow SKILL.md steps 1-5 literally

---

## Friction points

### Step 1: Attach or bootstrap

**F-01 — Invocation model never explained** (P0)
SKILL.md lists bare commands (`snapshot`, `click e0`) without stating they run inside
the `playwright-cli` interactive prompt, not as shell commands. A literal reader would
try `snapshot` in bash and get "command not found".
Root cause: M4 (missing prerequisite knowledge)
Fix: Add invocation-model blockquote after the intro paragraph.

**F-02 — Bootstrap install runs unconditionally** (P1)
Text says "only bootstrap when missing" but the code block always runs `install --browser=chrome`.
The `config --isolated` pattern from tabs.md is not mentioned.
Root cause: M1 (missing step) + S2 (contradiction)
Fix: Add comment clarifying `install` is always needed; add isolated-session bootstrap.

### Step 2: Tab and session ground truth

**F-11 — tab-new <url> unreliable but reason not documented** (P2)
The "Do this, not that" table says use `tab-new` then `open <url>` instead of `tab-new <url>`,
but step 2 doesn't explain why — the URL often fails to load with the combined form.
Root cause: S3 (missing rationale)
Fix: Add parenthetical explanation in step 2.

### Step 3: Observe before touching

**F-03 — snapshot returns file path, not inline tree** (P0)
SKILL.md implies `snapshot` prints an accessibility tree to stdout. In reality, it writes
a YAML file to `.playwright-cli/page-<timestamp>.yml` and prints only the file path.
You must `cat` the file to see refs.
Root cause: S3 (incorrect output description)
Fix: Update snapshot line in step 3 with YAML file + cat pattern.

**F-04 — Snapshot format mismatch: HTML tree vs actual YAML** (P1)
selectors.md shows an HTML-like tree with Unicode box-drawing characters.
The actual output is a YAML accessibility tree with role/name/ref keys.
Root cause: O2 (external tool behavior changed)
Fix: Replace HTML tree example with YAML format in selectors.md.

### Step 4: Act with direct commands

**F-05 — Missing commands in step 4** (P1)
Step 4 lists only navigation, inputs, clicks, and tabs. Missing: `press`, `resize`,
`mousewheel`, `upload` trigger pattern, `dialog-accept`/`dialog-dismiss`.
Root cause: S3 (incomplete enumeration)
Fix: Add keyboard, viewport, uploads, dialogs categories + summary table.

**F-06 — mousewheel parameter order swapped** (P1)
`mousewheel 0 900` should scroll down (deltaY=900) but the CLI internally swaps
parameters, causing horizontal scroll. This is an external CLI bug.
Root cause: O2 (external tool bug)
Fix: Add warning in screenshots.md viewport sweep section.

**F-09 — Many commands only in reference files** (P1)
Commands like `press`, `dialog-accept`, `resize` exist only deep in reference files
with no index or routing from SKILL.md. Undiscoverable during literal execution.
Root cause: S3 (missing cross-reference)
Fix: Add command summary table to step 4.

### Step 5: Verify

**F-07 — Artifact file inspection not explained** (P1)
Step 5 says "inspect returned artifact files" but never explains these are file paths
that need `cat` to read. A literal reader would expect inline output.
Root cause: M4 (missing prerequisite knowledge)
Fix: Add artifact-inspection callout in step 5.

**F-08 — --clear produces no output** (P2)
`console --clear` and `network --clear` produce no visible output (silent success).
Not documented — causes confusion about whether the command worked.
Root cause: O2 (undocumented behavior)
Fix: Add --clear note in SKILL.md and debugging.md.

### Cross-cutting

**F-10 — Bootstrap divergence: SKILL.md vs tabs.md** (P1)
tabs.md adds `session-stop` cleanup and `config --isolated` bootstrap steps not
mentioned in SKILL.md. Following only SKILL.md misses these important patterns.
Root cause: S2 (contradiction between files)
Fix: Add isolated-session bootstrap in step 1; add session-stop in cleanup notes.

---

## What worked well

1. **Non-negotiable rules 3-6** prevented stale-ref errors consistently
2. **Recovery rules** were actionable and correctly ordered by frequency
3. **Do this / not that table** caught real mistakes (tab-new vs tab-new + open)
4. **Reference routing table** was accurate — every file matched its declared scope
5. **Progressive evidence levels** (state → behavior → visual → diagnosis) felt natural
6. **eval for truth checks** caught a stale page header that snapshot missed
7. **Form verification pattern** (fill → eval value → submit → eval result) was reliable
8. **fill --submit** shortcut worked well for simple forms (undocumented but useful)

---

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 2 | F-01, F-03 |
| P1 | 7 | F-02, F-04, F-05, F-06, F-07, F-09, F-10 |
| P2 | 2 | F-08, F-11 |

## Derailment density map

| Workflow phase | P0 | P1 | P2 | Total |
|---|---|---|---|---|
| Step 1: Bootstrap | 1 | 1 | 0 | 2 |
| Step 2: Tab ground truth | 0 | 0 | 1 | 1 |
| Step 3: Observe | 1 | 1 | 0 | 2 |
| Step 4: Act | 0 | 3 | 0 | 3 |
| Step 5: Verify | 0 | 1 | 1 | 2 |
| Cross-cutting | 0 | 1 | 0 | 1 |

## Root cause distribution

| Code | Count | Description |
|---|---|---|
| M4 | 3 | Missing prerequisite knowledge |
| S3 | 3 | Missing or incorrect specification |
| O2 | 3 | External tool behavior mismatch |
| M1 | 1 | Missing step |
| S2 | 1 | Contradiction between documents |
