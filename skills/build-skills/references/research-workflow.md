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

1. search remote skill directories
2. gather candidate rows with titles, source labels, summaries, and URLs
3. prefer high-signal candidates over many near-duplicates
4. download only the skills worth learning from
5. inspect the downloaded corpus as evidence, not as background trivia

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

## Phase 4 — read before you compare

Do not move directly from search results to a final design.

Before comparison:

- read the downloaded skills that matter
- capture relative paths and section pointers
- note what each source is strong at
- note what each source should not contribute

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
