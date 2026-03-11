# Dogfood Report: build-skills workflow on "Swift Apple Watch Development"

Date: 2026-03-11
Skill under test: `build-skills`
Test topic: Swift Apple Watch Development
Method: Follow SKILL.md steps 1–5 exactly as written for a real research task

---

## Executive summary

Followed the build-skills workflow end-to-end for a real topic (swift/watchOS development). Downloaded and read 8 skills from the Playbooks corpus. Discovered 19 friction points across all workflow phases. 3 are P0 (block progress), 6 are P1 (cause confusion or wasted time), 10 are P2 (minor annoyances). All P0 and P1 fixes have been applied.

---

## Friction points

### Pre-workflow

**F-01 — skill-dl install check is buried** (P0)
The prerequisite to install `skill-dl` was in a troubleshooting table at the bottom of `remote-sources.md`, not at the top of `research-workflow.md`. First-time users hit `command not found` mid-flow.
Fix: Added prerequisite section at top of `research-workflow.md` and checklist item in `master-checklist.md`.

**F-02 — "Substantial redesign" has no concrete threshold** (P1)
Step 1 classification ("local-only" vs "full research path") requires experienced judgment. No examples are given for either path.
Fix: Added concrete examples for both paths and a rule of thumb: "if the change would alter the comparison table you'd build for this skill, it's the full research path."

**F-03 — Step 4 reads as unconditional** (P1)
Step 4 says "Read `references/research-workflow.md`" without any gate. A user on the local-only path might follow it anyway and waste time.
Fix: Added "Only execute this step if step 1 classified the job as Full research path. Skip to step 7 for local-only work."

### Step 1: Classify the job

No additional friction beyond F-02.

### Step 4: Remote research

**F-04 — URL file vs bundled script are parallel workflows never reconciled** (P0)
`research-workflow.md` prescribes writing a URL file as a distinct step. `skill-research.sh` skips it entirely. A first-time user doesn't know which path to follow.
Fix: Rewrote Phase 2 of `research-workflow.md` to present both as named alternatives ("Manual path" vs "Automated path") with clear guidance on when each applies.

**F-05 — Keyword format inconsistency between script and CLI** (P1)
`skill-research.sh` takes comma-separated keywords in one string. `skill-dl search` takes space-separated quoted arguments. No documentation explains the conversion.
Fix: Added explanatory comment in `skill-research.sh`; noted the difference in `research-workflow.md` Phase 2 automated path description.

**F-06 — No triage guidance for large result sets** (P1)
Running `skill-dl search` with broad keywords returns 50+ rows. No guidance on filtering.
Fix: Added triage step in both `research-workflow.md` and `remote-sources.md`: use `--min-match 2` or `--top 20` to focus results.

**F-07 — Niche topics break the cross-keyword ranking** (P2)
"apple watch" and "watchos" returned zero cross-keyword overlap. The ranking-by-overlap paradigm breaks for niche domains where max match count is 1–2.
Fix: Added guidance in triage step: "If the max match count is ≤2 (niche topics), broaden keyword variety or switch to manual curation from the full list."

**F-08 — URL-encoded skill names in search output** (P2)
`skill-dl search` returned `swift%206%20best%20practices%20guide` — spaces not decoded.
Status: Documented. Fix requires change in `cli-skill-downloader`, not the skill files.

**F-09 — 2/10 skill downloads failed silently** (P2)
`bluewaves-creations/bluewaves-skills/swiftui-patterns` and `shotaiuchi/dotclaude/ios-architecture` were indexed on playbooks.com but not found in their repos.
Fix: Enhanced troubleshooting entry in `remote-sources.md`: "The skill may use a non-standard directory layout."

### Step 4a: Read the downloaded corpus

**F-10 — "Read 2–3 most relevant reference files" gives no heuristic** (P2)
When filenames are ambiguous (e.g., `best-practices.md`, `patterns.md`, `advanced.md`), there's no guidance on which to prioritize.
Fix: Added scaling guidance in `research-workflow.md`: "2–3 files for skills with fewer than 8 references; 4–5 for skills with 8+ references." Pick based on filenames and the skill's stated routing logic.

**F-11 — No structure for per-skill notes** (P2)
The instruction says "capture notes" but doesn't say what fields or where.
Fix: Added "Capture notes per skill in `skills.markdown` under a `## Per-skill notes` heading" with explicit fields: overall structure, workflow style, reference organization, size, strengths, weaknesses, patterns to inherit.

**F-12 — "What reading means" section needed** (P2)
Users were tempted to skim filenames rather than loading file contents. The distinction between "I saw the file list" and "I read the file" needed explicit callout.
Fix: Added "What reading means here" subsection in Phase 4 of `research-workflow.md`.

### Step 5: Compare before synthesizing

**F-13 — `skills.markdown` location is unspecified** (P0)
No file says where to write this artifact — repo root? skill dir? corpus dir?
Fix: Specified in Phase 3 of `research-workflow.md`: "write `skills.markdown` to disk in the target skill directory (next to `SKILL.md`)."

**F-14 — `skills.markdown` vs `skills.md` naming** (P2)
Nothing explains why `.markdown` extension is used instead of `.md`.
Status: Cosmetic. The `.markdown` extension prevents the file from being mistaken for a skill component. Left as-is with implicit convention.

**F-15 — Comparison table column schema only in SKILL.md** (P1)
`research-workflow.md` says "build a comparison table" but doesn't list the required columns. Users reading only the research guide miss the schema.
Fix: Added Phase 5 to `research-workflow.md` with the full column specification table matching SKILL.md.

### Step 8: Test the skill

**F-17 — "Run 5+ queries" gives no execution method** (P1)
Users don't know whether to test interactively in Claude.ai, script it, or just imagine the queries.
Fix: Added execution method to SKILL.md step 8 and expanded "Running trigger tests" in `testing-methodology.md` with concrete instructions for Claude.ai and Claude Code.

### General

**F-16 — No size column in SKILL.md comparison table** (P2)
SKILL.md's step 5 comparison columns didn't include "Size" (SKILL.md line count + reference count), which is useful for assessing complexity.
Fix: Added to the comparison table in `research-workflow.md` Phase 5.

**F-18 — `skill-dl --version` timing** (P2)
The prerequisite check happens after the user has already started the workflow. Could be earlier.
Status: Fixed via F-01 — prerequisite is now at the very top of `research-workflow.md` and first item in `master-checklist.md`.

**F-19 — `derail-notes/` does not exist** (P2)
Meta-friction: the notes directory for the dogfooding exercise didn't exist and wasn't documented.
Status: Created as part of this exercise.

---

## What worked well

1. **skill-dl search** returned relevant results quickly — the markdown table output was easy to parse and prioritize
2. **Progressive disclosure** in the skill architecture worked — SKILL.md stayed lean while references held the detail
3. **Step 4a** (read the corpus) was the most valuable addition — skills that were read deeply produced far better comparison notes than those only skimmed
4. **Comparison table format** forced clear inherit/avoid decisions rather than vague "this is nice"
5. **Reference routing table** in SKILL.md made it obvious which file to read for each concern

---

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 (blocks progress) | 3 | F-01, F-04, F-13 |
| P1 (causes confusion) | 6 | F-02, F-03, F-05, F-06, F-15, F-17 |
| P2 (minor annoyance) | 10 | F-07, F-08, F-09, F-10, F-11, F-12, F-14, F-16, F-18, F-19 |

---

## Downloaded corpus

8 skills successfully downloaded to `/tmp/swift-research-corpus/`:

| Skill | SKILL.md lines | Refs | Category | Signal |
|---|---|---|---|---|
| avdlee/swiftui-agent-skill | 282 | 19 | Workflow | 3-path decision tree, strongest model |
| fusengine/agents/watchos | 85 | 3 | Workflow | Thin, repo-specific |
| rshankras/watchos | 356 | 4 | Workflow | Good inline code examples |
| kylehughes/building-apple-platform-products | 208 | 15 | Workflow | Excellent "When to Read" routing |
| openclaw/swift-expert | 95 | 5 | Domain | Clean MUST DO / MUST NOT DO |
| frostist/swift-human-guidelines | 422 | 9 | Document | Comprehensive but monolithic |
| swiftzilla/swiftzilla | 53 | 2 | MCP Enhancement | Progressive disclosure |
| 404kidwiz/swift-expert-skill | 293 | 0 | Domain | Anti-pattern: monolithic, persona-based |

2 skills failed to download (F-09): `bluewaves-creations/swiftui-patterns`, `shotaiuchi/ios-architecture`
