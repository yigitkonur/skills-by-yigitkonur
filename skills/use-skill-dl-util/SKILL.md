---
name: use-skill-dl-util
description: Use skill if you are searching, discovering, and downloading AI coding skills using skill-dl with Serper-powered search and batch downloads.
---

# Skill Research

Search, download, and inspect AI coding skills from playbooks.com using `skill-dl`.

## Trigger boundary

Use this skill when:

- searching for existing skills on a topic before building a new one
- downloading one or more skills from playbooks.com for comparison
- building a corpus of skills for evidence-based skill design
- piping search results directly into batch download
- inspecting a downloaded corpus to decide what to inherit or avoid

Do not use this skill for:

- building or authoring a new skill from a corpus (use `build-skills`)
- testing a skill's instructional quality (use `test-skill-quality`)
- general web research unrelated to skill discovery (use `run-research`)

## Prerequisites

Verify `skill-dl` is installed before doing anything else.

```bash
skill-dl --version
```

If missing, install:

```bash
curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | bash
```

Requirements: Bash 4+, git, curl. No API keys needed — built-in defaults work.

## Workflow

### 1. Define your search intent

Before running any search, write down:

- The topic or domain you need skills for
- Whether you need broad coverage (landscape scan) or targeted matches (specific technique)
- How the downloaded skills will be used (comparison, evidence, reference)

This determines keyword strategy. Read `references/search-strategies.md` for keyword formulation rules.

### 2. Search for skills

Run `skill-dl search` with 3-20 space-separated keywords:

```bash
skill-dl search typescript mcp server sdk patterns --top 20
```

Output is a markdown table ranked by keyword match count. Higher match count means the skill matched more of your keywords.

**Search tuning flags:**

| Flag | Purpose |
|---|---|
| `--top N` | Cap results to top N (default: all) |
| `--min-match N` | Only show skills matching N+ keywords |

**Search backends:** Serper API (Google), playbooks.com scraping (always active), Scrapedo proxy (fallback). All run automatically.

If the first search returns too many results, add `--min-match 2` or narrow keywords. If results are sparse, broaden keywords or run a second search with different phrasing. Read `references/search-strategies.md` for multi-round search patterns.

### 3. Evaluate results and build a URL list

From the search table, pick candidates based on:

- **Match count** — more matched keywords means broader relevance
- **Skill name** — does the name suggest the right scope?
- **Owner/repo** — recognized authors or repos signal quality

For batch downloads, save selected URLs to a file (one per line, `#` comments allowed):

```bash
# React component skills
https://playbooks.com/skills/owner/repo/skill-one
https://playbooks.com/skills/owner/repo/skill-two
```

### 4. Download skills

Read `references/download-patterns.md` for the full download reference. Quick patterns:

**Single skill:**

```bash
skill-dl https://playbooks.com/skills/owner/repo/skill-name -o ./corpus
```

**Batch from file:**

```bash
skill-dl urls.txt -o ./corpus --no-auto-category -f
```

**Pipe search directly to download:**

```bash
skill-dl search react hooks testing | grep -oE 'https://playbooks\.com/skills/[^ |]+' | skill-dl - -o ./corpus -f
```

**Dry run first for large batches:**

```bash
skill-dl urls.txt --dry-run
```

### 5. Inspect the corpus

After download, inspect what you got. Read `references/corpus-inspection.md` for the full inspection protocol.

Quick inspection:

```bash
# Overview
tree -L 2 ./corpus

# Count skills and references
find ./corpus -name "SKILL.md" -maxdepth 2 | wc -l
find ./corpus -name "SKILL.md" -maxdepth 2 | while read f; do
  d=$(dirname "$f")
  echo "$(basename "$d"): $(find "$d" -type f | wc -l) files"
done
```

For each high-signal skill:

1. Read its SKILL.md fully — understand trigger boundary, workflow, decision rules
2. Tree its `references/` directory — see structure and decomposition
3. Read the 2-3 most relevant reference files
4. Note what to inherit and what to avoid

### 6. Use the end-to-end script (optional)

For one-command search-to-inspect, use `skill-research.sh` from the `build-skills` references:

```bash
bash ../build-skills/references/skill-research.sh "keyword1,keyword2,keyword3" ./corpus 6
```

This runs all three phases (discovery, download, inspection) with parallel execution.

## Decision rules

- If you need fewer than 5 skills, download them individually. Batch only when building a corpus.
- If results exceed 50 rows, use `--min-match 2` before manually scanning. For niche topics where max match count is 1-2, manually curate from the full list.
- If a skill fails to download (`[ERR] Not found in repo`), run with `-v` to see available skills in that repo. The skill may use a non-standard directory layout.
- If you need skills from the same repo, put all URLs in one file — `skill-dl` clones each repo only once.
- If the corpus will feed into `build-skills`, organize notes per skill before switching to that workflow.
- If `skill-dl` is unavailable and cannot be installed, search GitHub manually for repositories containing SKILL.md files.

## Do this, not that

| Do this | Not that |
|---|---|
| Use 3-20 diverse keywords covering different angles | Use 1-2 generic keywords and wonder why results are thin |
| Run `--dry-run` before large batch downloads | Download 100 skills and then realize half are irrelevant |
| Inspect each skill's SKILL.md and references before deciding | Judge skills by name alone |
| Pipe search to download for quick corpus building | Manually copy-paste 30 URLs one at a time |
| Group URLs by repo in batch files for efficient cloning | Download each URL independently and re-clone repos |
| Use `--no-auto-category` when you want flat output | Fight auto-categorization after the fact |

## Reference routing

| File | Read when |
|---|---|
| `references/search-strategies.md` | Formulating keywords, running multi-round searches, or tuning result quality |
| `references/download-patterns.md` | Downloading skills (single, batch, pipe, parallel) or troubleshooting download failures |
| `references/corpus-inspection.md` | Inspecting downloaded skills, assessing quality, or preparing notes for comparison |

## Guardrails

- Do not search with fewer than 3 keywords. `skill-dl` requires a minimum of 3.
- Do not exceed 20 keywords per search invocation.
- Do not skip the dry run for batches over 20 URLs.
- Do not treat downloaded skills as templates to copy. They are evidence for comparison.
- Do not download without first verifying `skill-dl --version`.
- Do not ignore download errors. Check with `-v` and verify URLs.
