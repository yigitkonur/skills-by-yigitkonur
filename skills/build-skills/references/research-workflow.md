# Research Workflow

Use this file when the task is larger than a small local cleanup.

The rule is simple: research happens before synthesis.

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
2. **Select** — from the markdown table output, pick high-signal candidates; record skill name, source, URL, match count, rationale
3. **Write URL file** — one Playbooks URL per line, grouped with `#` comments by tier (high-install, community, niche)
4. **Download** — `skill-dl urls.txt -o ./research-corpus --no-auto-category -f`
   - Large batches: split by repo and run parallel (see `references/remote-sources.md`)
   - Or use the bundled script: `bash references/skill-research.sh "<topic>" ./research-corpus`
5. **Inspect** — the downloaded corpus is first-class evidence, not background noise

Treat the downloaded corpus as a second source tree that deserves the same attention as local files.

## Phase 3 — emit `skills.markdown`

Before synthesis, produce `skills.markdown` as the research artifact.

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
3. **Read the 2–3 most relevant reference files** — pick based on the file names and the skill's stated routing logic. Read them fully, not just the headings.
4. **Check `scripts/` if present** — script files reveal automation patterns, validation logic, and tooling choices that prose cannot fully convey.
5. **Capture notes per skill** — record: overall structure (flat vs. layered), workflow style (sequential, branching, iterative), reference organization, what it does well, what it does poorly, and 1–2 direct quotes or patterns worth inheriting.

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
