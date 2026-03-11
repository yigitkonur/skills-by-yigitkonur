# Derailment Test: Research Phase Deep-Dive

## Why this note exists

Steps 3-4a concentrate 8 of 18 friction points (44% of all friction) in just 2 workflow steps. This note does a deep-dive into the research/evidence capture phase to understand why it's the systemic weak point and propose targeted restructuring.

---

## The research phase today (Steps 3-4a)

```
Step 3: Capture local evidence first
  ├── Tree the workspace
  ├── Read current SKILL.md fully
  ├── Read every relevant file in references/
  ├── Note reference naming scheme and routing
  └── Note repo conventions and gaps

Step 4: Run remote research (Full Research Path only)
  ├── Read references/research-workflow.md
  ├── Use skill-dl search (3-20 keywords)
  ├── Use skill-dl to download candidates
  ├── See references/remote-sources.md
  ├── Prefer diverse, relevant sources
  └── Emit skills.markdown

Step 4a: Read downloaded corpus thoroughly
  ├── Read each SKILL.md fully
  ├── Tree each references/ directory
  ├── Read 2-3 most relevant reference files per skill
  ├── Check scripts/ if present
  └── Capture notes per skill
```

---

## Friction point concentration analysis

| Friction ID | Step | Root cause | Issue |
|---|---|---|---|
| F-02 | 3 | S3 | "Target workspace" ambiguous |
| F-05 | 3 | S2 | "Read every relevant file" with 22 files |
| F-03 | 4 | O1 | skill-dl not installed, no fallback |
| F-04 | 4 | M5 | skill-research.sh invocation unclear |
| F-06 | 4 | O2 | skill-dl search argument format undocumented |
| F-07 | 4 | S4 | skills.markdown output location unspecified |
| F-08 | 4a | M3 | Downloaded sources violate quality standards |
| F-09 | 4a | S3 | No format for per-skill notes |
| F-10 | 4 | M1 | "Emit" implies auto-generation |

**Pattern:** 5 of 9 friction points are about missing specifications (S3, S4, M5, O2, M1). The skill says WHAT to do but not HOW or WHERE.

---

## Root cause: The research phase was never dog-fooded

The evidence suggests the research phase was written descriptively ("here's what should happen") rather than prescriptively ("here's exactly how to do it"). Signs:

1. `skill-dl` is referenced without installation verification
2. `skill-research.sh` is referenced without invocation syntax
3. `skills.markdown` is mentioned without output path
4. Per-skill notes are required without a template
5. "Target workspace" assumes shared understanding

Compare with Steps 7-9 (synthesis and testing), which have more specific instructions, exact checklist references, and clearer acceptance criteria. The difference suggests Steps 7-9 were refined through use, while Steps 3-4a weren't.

---

## Restructuring proposal

### Problem: 3 steps that blend into each other

Steps 3, 4, and 4a have unclear boundaries:
- Step 3 says "read every relevant file" (could be all 22 files)
- Step 4 starts with "read references/research-workflow.md" (another read)
- Step 4a is ALL reading

### Solution: Reframe as 3 distinct phases with clear gates

```
Step 3: LOCAL SCAN (gate: workspace tree + convention notes exist)
  ├── Tree the skill repo workspace
  ├── If targeting external tech, also tree representative project
  ├── Read current SKILL.md + 3-5 most relevant reference files
  └── Output: workspace scan summary with conventions and gaps

Step 4: REMOTE DISCOVERY (gate: skills.markdown exists in workspace root)
  ├── Verify skill-dl: skill-dl --version
  │   └── If missing: see references/remote-sources.md or use
  │       skills-as-context-search-skills as fallback
  ├── Search: skill-dl search keyword1 keyword2 keyword3 --top 20
  ├── Download top 3-5: skill-dl <url1> <url2> ... -o ./skills-corpus
  └── Create skills.markdown summarizing downloads and shortlist

Step 4a: SOURCE READING (gate: per-skill notes exist for all shortlisted)
  ├── For each shortlisted skill:
  │   ├── Read its SKILL.md fully
  │   ├── Tree its references/
  │   ├── Read 2-3 most relevant reference files
  │   └── Capture notes (heading per skill, bullets mapping to
  │       comparison table columns)
  ├── Note: downloaded sources may not meet this skill's quality
  │   standards — that informs the "avoid" column
  └── Output: structured notes ready for comparison table
```

### Key changes:
1. Each step has an explicit **gate** (what must exist before moving on)
2. Step 3 scopes reference reading to "3-5 most relevant" instead of "every relevant"
3. Step 4 starts with prerequisite verification
4. Step 4 includes inline example syntax for skill-dl
5. Step 4a includes quality warning about downloaded sources
6. Step 4a includes notes format hint

---

## Estimated impact

| Metric | Before | After |
|---|---|---|
| Friction points in Steps 3-4a | 8 | 0 (all addressed) |
| P0 blockers | 1 (F-03) | 0 |
| P1 in adjacent steps | 5 (compound P0) | 0 |
| Lines added to SKILL.md | — | ~15 |
| Lines removed from SKILL.md | — | ~5 |
| New reference files needed | — | 0 |
