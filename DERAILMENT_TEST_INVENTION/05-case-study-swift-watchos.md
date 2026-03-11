# Case Study: Derailment Testing build-skills on Swift/watchOS

Full worked example of a Derailment Test, demonstrating every phase of the methodology on a real instruction set and a real task.

---

## Test context

| Field | Value |
|---|---|
| Instruction set | `build-skills` skill (SKILL.md + 22 reference files) |
| Test task | Research and design a "Swift Apple Watch development" skill |
| Tester role | AI agent (Claude), acting as naive executor |
| Date | 2026-03-11 |
| Skill version | Post-enhancement (258-line SKILL.md, 7 reference categories) |

## Why this task was chosen

The task exercises the full research path (steps 1–5 of SKILL.md): classification, local scan, remote research, corpus reading, and comparison table. It is genuinely non-trivial — Swift/watchOS is a niche topic with sparse representation in the Playbooks skill corpus, which stresses the search and triage logic. The task is also domain-independent for the tester — no prior Swift knowledge needed to follow the instructions.

## Phase 0: Pre-scan findings

Before execution, a read-through of SKILL.md revealed:

- 9 numbered workflow steps with branching at step 1
- 22 reference files across 7 categories
- Cross-references between SKILL.md, research-workflow.md, remote-sources.md, and skill-research.sh
- External tool dependency: `skill-dl` CLI

## Phase 1: Literal execution

### Step 1 — Classify the job

**Instruction:** Classify as "local-only" or "full research path."

**Execution:** The task is creating a new skill from scratch → full research path.

**Friction:** The boundary between "local-only" and "full research" used the word "substantial" without examples. A medium-sized change (e.g., adding one workflow branch) would be ambiguous.

→ **F-02** (P1, M1): "Substantial redesign" has no concrete threshold.

### Step 2 — Classify the skill type

**Instruction:** Identify as Document/Asset, Workflow Automation, or MCP Enhancement.

**Execution:** Swift/watchOS development guidance is Workflow Automation. Clean pass.

### Step 3 — Capture local evidence

**Instruction:** Tree the workspace, read SKILL.md, read relevant references.

**Execution:** Ran `tree` on the build-skills directory. Read SKILL.md (255 lines). Identified 22 reference files. No existing Swift/watchOS skill found locally. Clean pass.

### Step 4 — Remote research

**Instruction:** "Read `references/research-workflow.md`."

**Pre-execution friction:** The instruction reads as unconditional. If the user had classified as "local-only" in step 1, they might still follow this step and waste time on unnecessary research.

→ **F-03** (P1, M4): Step 4 reads as unconditional despite being gated by step 1.

**Reading research-workflow.md:**

1. **Prerequisite check:** The document's prerequisite section said to verify `skill-dl --version`. Ran it. `skill-dl` was installed at v1.2.0 from a previous session. However, had this been a fresh environment, the install instructions were originally buried in a troubleshooting table 100 lines deep in a different file.

→ **F-01** (P0, S1): skill-dl install check was buried. [Already fixed — prerequisite now at top of research-workflow.md]

2. **Discovery:** Ran `skill-dl search` with 6 keywords:

```
skill-dl search "swift" "apple watch" "watchos" "swiftui" "ios development" "xcode"
```

Got 47 results. Results ranked by cross-keyword overlap. Top results had 3–4 keyword matches.

3. **Triage:** Two niche keywords ("apple watch", "watchos") returned zero cross-keyword matches because so few skills cover those topics. The ranking-by-overlap paradigm breaks for niche domains.

→ **F-07** (P2, O4): Niche topics break cross-keyword ranking.

4. **URL file vs. script:** research-workflow.md described writing a URL file. But skill-research.sh existed as an alternative that handles discovery + download in one command. Neither document mentioned the other.

→ **F-04** (P0, S2): Two parallel workflows never reconciled.

5. **Keyword format:** The script expects comma-separated keywords: `"kw1,kw2,kw3"`. The CLI expects space-separated quoted args: `"kw1" "kw2" "kw3"`. No documentation explained the conversion.

→ **F-05** (P1, M3): Keyword format inconsistency.

6. **Download:** Selected 10 candidate URLs. Downloaded with `skill-dl`. 8 succeeded, 2 failed silently (skills indexed on playbooks.com but not found in their repos).

→ **F-09** (P2, O1): 2/10 downloads failed silently.

### Step 4a — Read the downloaded corpus

**Instruction:** "Read the 2–3 most relevant reference files."

7. **Reference file selection:** The instruction gave no heuristic for ranking when filenames are ambiguous (e.g., `best-practices.md` vs. `patterns.md` vs. `advanced.md`).

→ **F-10** (P2, M5): No heuristic for ranking ambiguous filenames.

8. **Notes structure:** Instruction said "capture notes per skill" but didn't specify what fields or where to write them.

→ **F-11** (P2, M2): No structure for per-skill notes.

9. **"Reading" definition:** Temptation to skim filenames instead of loading file contents. The distinction between "I saw the file list" and "I read the file" needed explicit callout.

→ **F-12** (P2, M5): What "reading" means is ambiguous.

**Actual reading results (8 skills):**

| Skill | Lines | Refs | Key finding |
|---|---|---|---|
| avdlee/swiftui-agent-skill | 282 | 19 | Best-in-class: 3-path decision tree, strong routing |
| fusengine/agents/watchos | 85 | 3 | Thin, repo-specific dependencies |
| rshankras/watchos | 356 | 4 | Good inline code examples |
| kylehughes/building-apple-platform-products | 208 | 15 | Excellent "When to Read" routing table |
| openclaw/swift-expert | 95 | 5 | Clean MUST DO / MUST NOT DO sections |
| frostist/swift-human-guidelines | 422 | 9 | Comprehensive but borders monolithic |
| swiftzilla/swiftzilla | 53 | 2 | MCP Enhancement, progressive disclosure model |
| 404kidwiz/swift-expert-skill | 293 | 0 | Anti-pattern: monolithic, persona-based |

### Step 5 — Compare

10. **`skills.markdown` location:** Instruction said "emit `skills.markdown`" without specifying where.

→ **F-13** (P0, M2): Output location for `skills.markdown` unspecified.

11. **Comparison table columns:** The required columns were in SKILL.md step 5 but not in research-workflow.md. A user following only the research workflow would miss the schema.

→ **F-15** (P1, S3): Schema only in one location.

**Comparison table built successfully after resolving the above issues.**

### Step 8 — Test

12. **Execution method:** "Run 5+ trigger queries" — the instruction didn't say where or how. In Claude.ai? Claude Code? Mentally?

→ **F-17** (P1, M4): Missing execution method for trigger tests.

## Phase 2: Evidence summary

| Metric | Value |
|---|---|
| Steps attempted | 7 (steps 1–5, 4a, 8) |
| Clean passes | 2 (steps 2, 3) |
| P0 derailments | 3 (F-01, F-04, F-13) |
| P1 derailments | 6 (F-02, F-03, F-05, F-06, F-15, F-17) |
| P2 derailments | 10 (F-07–F-12, F-14, F-16, F-18, F-19) |
| Total friction points | 19 |
| External knowledge required | 4 instances |

### Derailment density map

```
Step 1  ─ F-02 ·
Step 2  ─ clean
Step 3  ─ clean
Step 4  ─ F-01 ▓ F-03 · F-04 ▓ F-05 · F-06 · F-07 ░ F-08 ░ F-09 ░
Step 4a ─ F-10 ░ F-11 ░ F-12 ░
Step 5  ─ F-13 ▓ F-14 ░ F-15 · F-16 ░
Step 8  ─ F-17 ·

▓ = P0   · = P1   ░ = P2
```

**Observation:** Step 4 (remote research) has the highest derailment density — 7 friction points. This is the most complex phase with the most external dependencies, making it the highest-risk area.

## Phase 3: Root cause analysis

| Root cause | Count | Friction points |
|---|---|---|
| S1 Missing prerequisite | 1 | F-01 |
| S2 Contradictory paths | 1 | F-04 |
| S3 Scattered information | 1 | F-15 |
| M1 Ambiguous threshold | 1 | F-02 |
| M2 Unstated location | 2 | F-11, F-13 |
| M3 Format inconsistency | 2 | F-05, F-14 |
| M4 Missing execution method | 3 | F-03, F-06, F-17 |
| M5 Assumed knowledge | 2 | F-10, F-12 |
| O1 Silent failure | 1 | F-09 |
| O2 Tool output mismatch | 1 | F-08 |
| O4 Scaling breakdown | 1 | F-07 |
| Meta | 2 | F-16, F-18, F-19 |

**Pattern:** Semantic causes (M-codes) account for 10/19 friction points — the instructions describe *what* but not *how*, *where*, or *which*. This is the most common failure mode in procedural instructions written by domain experts.

## Phase 4: Fixes applied

| Fix pattern | Friction points | Files modified |
|---|---|---|
| Prerequisite Surfacing | F-01 | research-workflow.md, master-checklist.md |
| Threshold Concretization | F-02 | SKILL.md |
| Conditional Gating | F-03 | SKILL.md |
| Workflow Path Reconciliation | F-04 | research-workflow.md |
| Format Alignment | F-05 | skill-research.sh, research-workflow.md |
| Scaling Guidance | F-06, F-07, F-10 | research-workflow.md, remote-sources.md |
| Output Location Specification | F-11, F-13 | research-workflow.md |
| Schema Duplication | F-15, F-16 | research-workflow.md |
| Execution Method Specification | F-17 | SKILL.md, testing-methodology.md |

**Total files modified:** 6 files across the build-skills skill

## Phase 5: Post-fix verification

After applying all fixes:

- `grep -r "install count" skills/build-skills/` → 0 matches (stale terminology eliminated)
- `grep -r "skills.markdown" skills/build-skills/` → consistent usage across all files
- All 22 reference files routed from SKILL.md routing table — no orphans
- SKILL.md at 258 lines (under 500 limit)
- No contradictions between research-workflow.md and SKILL.md

## What this test proved

1. **Derailment Testing found 19 defects that traditional testing would have missed.** None were code bugs. All were instructional ambiguities.
2. **P0 items clustered at external boundaries** — tool dependencies, file locations, workflow branching. These are the highest-risk areas in any procedural instruction set.
3. **The naive executor mindset was essential.** An experienced author would have "filled in" all 19 gaps from memory and declared the instructions complete.
4. **Fix patterns are reusable.** The 9 patterns identified in this test (prerequisite surfacing, threshold concretization, etc.) apply to any procedural instruction set, not just AI skills.
5. **The derail notes have standalone value.** Even without the fixes, the structured friction report gives any reader a precise map of where the instructions break down.
