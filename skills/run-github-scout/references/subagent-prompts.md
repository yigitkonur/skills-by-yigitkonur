# Subagent Prompt Templates

Copy-paste prompts for launching search and evaluation subagents.

## Search Subagent (wave 1)

```
I need to find all GitHub repos for: {TOPIC}

{CONTEXT_FROM_USER — any constraints, languages, known repos}

There's a skill for this at ~/.claude/skills/github-repo-search/.
Read the SKILL.md and reference files, then run the full workflow.

Write your final ranked table to: .githubresearch/search-findings/wave-01.md

Include at the top of the file:
- Total repos found
- Which search hypotheses were most productive
- Any categories you noticed

Prefix all commands with rtk.
```

## Search Retry Subagent (wave 2+)

```
A previous search for "{TOPIC}" found only {N} repos. Here's what it found:

{PASTE_PREVIOUS_TABLE}

This missed the mark because: {REASON}

Try these angles:
- {ANGLE_1}
- {ANGLE_2}
- {ANGLE_3}

Skill at ~/.claude/skills/github-repo-search/.
Write results to: .githubresearch/search-findings/wave-{N}.md

Don't repeat repos already found above. Only add NEW finds.

Prefix all commands with rtk.
```

## Evaluation Subagent

```
Evaluate these GitHub repos for quality:

{REPO_LIST — one per line}

There's a skill at ~/.claude/skills/github-repo-evaluate/.
Read SKILL.md and its references, then run the full workflow.

Custom criteria for this evaluation:
{FEATURE_CHECKLIST}

Write your results to: .githubresearch/repo-reviews/batch-{N}.md

Format per repo:
## owner/repo
Score: X/100 | Stars: N | Health: X/100 | Author: X/100 | Code: X/100
Key strength: one line
Key risk: one line
Feature fit:
- [x] feature 1
- [ ] feature 2
- [x] feature 3

Then 2-3 sentences of analysis.

Prefix all commands with rtk.
```

## Agent Configuration

All subagents use:
- **Model:** sonnet
- **Mode:** bypassPermissions
- **run_in_background:** true (launch all eval agents in parallel)

## Swarm Sizing Quick Reference

```
repos ≤ 5   → 1 agent, all repos
repos ≤ 15  → 2-3 agents, ~5 each
repos ≤ 30  → 3-5 agents, ~6-10 each
repos ≤ 60  → 5 agents, ~12 each
repos ≤ 150 → 5 agents, ~30 each
repos > 150 → 5 agents, top 150 by stars, 30 each
```

**Always round up.** If 17 repos with 3 agents: 6 + 6 + 5. Give the first batch(es) the higher-star repos.

## Feature Detection Subagent

```
Check which features are present in these repos.

Repos: {REPO_LIST}

Features to check (slug | description):
{FEATURE_LIST}

For each repo + feature:
1. Search README for feature mentions
2. Check package.json / Cargo.toml / go.mod for relevant dependencies
3. List source tree (top-level + src/) for indicative files/directories
4. If still uncertain, read up to 2 source files for confirmation

Write results to: .githubresearch/feature-matrix/batch-{N}.md

Format per repo:
## owner/repo
FEATURES_JSON:
{
  "feature_slug": {"present": true, "evidence": "one line — where/how found", "confidence": "high"},
  "another_slug": {"present": false, "evidence": "no relevant code or deps found", "confidence": "high"},
  ...
}

Confidence guide:
- high: found explicitly in code, config, or README
- medium: inferred from dependencies or file structure
- low: guessing from project description only

Prefix all commands with rtk.
```
