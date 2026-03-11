# Research Workflow

Use this file when the task is larger than a small local cleanup.

The rule is simple: research happens before synthesis.

## Prerequisite

Before starting, verify `skill-dl` is installed:

```bash
skill-dl --version
```

If missing, install it:

```bash
curl -fsSL https://raw.githubusercontent.com/yigitkonur/cli-skill-downloader/main/install.sh | bash
```

Also confirm you have classified the skill type (see SKILL.md step 2) before beginning research.

## When remote research is mandatory

Run the remote research phase when any of these are true:

- you are creating a new skill
- you are substantially redesigning an existing skill
- you are merging patterns from multiple skills
- the local workspace is thin, stale, or obviously incomplete
- the user explicitly asks for outside references or comparative analysis

You may skip remote research only for small local edits where outside evidence would not materially change the result.

## Phase 1 — inspect the local workspace first

1. Run `tree` on the current working directory, or produce an equivalent tree-style listing.
2. Read the files surfaced by that listing that look like real sources of truth.
3. Capture the local evidence set before widening scope.

The local scan prevents you from importing outside patterns that conflict with the actual repo.

## Phase 2 — widen the evidence set

After the local scan:

1. **Discover** — run `skill-dl search` with 3–20 keyword arguments covering the topic from multiple angles
   - `skill-dl search` outputs a prioritized markdown table: rank, skill name, owner/repo, keywords matched, match count, URL
   - Skills appearing across more keywords rank higher — cross-keyword overlap is the primary signal
   - Run multiple keyword sets in parallel for broader coverage; deduplicate by URL before proceeding
   - Example: `skill-dl search "agent browser" "headless automation" "browser testing" "playwright"`
   - Requires at least 3 keywords; use varied phrasing to surface different result clusters
2. **Triage large result sets** — if results exceed 50 rows, use `--min-match 2` to focus on cross-keyword hits, or `--top 20` to cap results. If the max match count is ≤2 (niche topics), broaden keyword variety or switch to manual curation from the full list
3. **Select** — from the markdown table output, pick high-signal candidates; record skill name, source, URL, match count, rationale
4. **Download** — choose one of two paths:
   - **Manual path**: write a URL file (one Playbooks URL per line, `#` comments for grouping), then run `skill-dl urls.txt -o ./research-corpus --no-auto-category -f`
   - **Automated path**: run the bundled script `bash references/skill-research.sh "kw1,kw2,kw3" ./research-corpus` — it discovers, downloads, and inspects in one command (note: keywords are comma-separated in the script but space-separated when calling `skill-dl search` directly)
   - Large batches: split by repo and run parallel (see `references/remote-sources.md`)
5. **Inspect** — the downloaded corpus is first-class evidence, not background noise

Treat the downloaded corpus as a second source tree that deserves the same attention as local files.

## Phase 3 — write `skills.markdown`

Before synthesis, write `skills.markdown` to disk in the target skill directory (next to `SKILL.md`). This is the durable research artifact.

At minimum it should record:

- search query or topic
- pages or source coverage
- candidate results and why they matter
- selected downloads
- destination paths
- downloaded tree output
- next-use note telling the reader to compare the downloaded corpus before drafting

If `skills.markdown` is missing, the research phase is incomplete.

## Phase 4 — read the downloaded corpus thoroughly

Do not move directly from search results to a final design. Reading the corpus is a distinct, mandatory step — not a footnote.

**For each downloaded skill that made the shortlist:**

1. **Read `SKILL.md` fully** — understand the trigger boundary, workflow structure, decision rules, and output contract before anything else. Do not skim.
2. **Tree the `references/` directory** — run `tree <skill-dir>/references/` or equivalent listing to see what reference files exist, how they are named, and how deeply they are nested. This reveals the skill's structural philosophy.
3. **Read the most relevant reference files** — pick based on the file names and the skill's stated routing logic. Read them fully, not just the headings. Scale: 2–3 files for skills with fewer than 8 references; 4–5 for skills with 8+ references.
4. **Check `scripts/` if present** — script files reveal automation patterns, validation logic, and tooling choices that prose cannot fully convey.
5. **Capture notes per skill in `skills.markdown`** under a `## Per-skill notes` heading — record: overall structure (flat vs. layered), workflow style (sequential, branching, iterative), reference organization, size (SKILL.md line count + reference file count), what it does well, what it does poorly, and 1–2 direct quotes or patterns worth inheriting.

**What "reading" means here:**

- Load the file contents, not just the filenames.
- Note section headings, decision rules, and anti-patterns sections specifically.
- Record exact relative paths when citing evidence in `skills.markdown`.

**What to capture in your notes:**

- structural patterns that differ from your current approach
- reference file organization choices (flat file per topic vs. nested by phase)
- trigger boundary phrasing that is notably precise or notably weak
- any reusable logic, scripts, or validation patterns

This phase produces the raw material for Phase 5 (comparison table). If you skip it, the comparison table will be fabricated from memory rather than evidence.

## Phase 5 — build the comparison table

Build a markdown comparison table with at least these columns:

| Column | Purpose |
|---|---|
| Source | Skill name and origin |
| Focus | What the skill covers |
| Size | SKILL.md line count + reference file count |
| Strengths | What it does well |
| Gaps | What it's missing |
| Relevant paths | Specific files or sections worth citing |
| Inherit / Avoid | Decision — what to take vs. what to skip |

Every row must end with a decision (Inherit / Avoid), not just an observation. The comparison table is the bridge between reading and synthesis — it makes your reasoning visible and auditable.

## Selection heuristics

Prioritize sources that add one or more of these:

1. direct relevance to the requested skill
2. strong bundled references or scripts
3. distinctive workflow patterns
4. better structure or trigger design than the local examples
5. reusable logic instead of one-off examples

## Anti-patterns

Avoid these mistakes:

- treating local evidence as sufficient for a non-trivial design task
- downloading by keyword match only
- researching without leaving a durable artifact
- copying downloaded skills instead of distilling them
- packaging the transient research corpus into the final skill by default
- skipping the downloaded corpus scan and pretending the research already happened
