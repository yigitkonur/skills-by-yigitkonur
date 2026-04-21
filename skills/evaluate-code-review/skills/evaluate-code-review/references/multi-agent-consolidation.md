# Multi-Agent Feedback Consolidation

When a PR has feedback from multiple reviewers (human + Copilot + CodeRabbit + Devin + Greptile + Bito + random Claude review script), consolidation happens *before* evaluation. The goal: one flat list of items where each item is evaluated once, regardless of how many reviewers raised it.

Inspired by but not copied from `yigitkonur/cli-pr-consensus`. The patterns here are language-agnostic and do not require the TypeScript tool.

## The consolidation pipeline

```
Raw reviewer comments (N sources)
        │
        ▼
  Per-source parsing  ── each source has its own comment format / location
        │
        ▼
  Flat item list      ── {source, file, line, verbatim_text} per item
        │
        ▼
  Line-range clustering ── items on the same file + overlapping lines merge
        │
        ▼
  Deduplication       ── identical content → one item with multiple sources
        │
        ▼
  Conflict detection  ── two sources disagree → flag explicitly, don't silently pick
        │
        ▼
  Noise filtering     ── dismissible false positives → dropped with reason
        │
        ▼
  Consolidated list   ── fed to the evaluation step
```

## Per-source parsing

Each reviewer delivers feedback in a different shape. Recognize and extract.

| Reviewer | Where the comments land | Key field |
|---|---|---|
| Human reviewer | top-level PR review; inline comments on specific lines | `body` field (plain markdown) |
| GitHub Copilot (reviewer) | PR review comments, sometimes summary-only | `body` field (markdown with suggestion blocks) |
| CodeRabbit | inline review comments with callout icons (🟡🔴⚠️) | `body` field; parse callout type from emoji / preamble |
| Devin | structured review comments, often HTML-embedded metadata | comment `<!-- devin-review-comment {...} -->` JSON block |
| Bito | HTML-embedded issue/fix divs with citations | `<div class="...">` blocks in `body` |
| Greptile | generic markdown, similar to human | `body` field (markdown) |
| Cubic | structured `<violation>` blocks | XML-like blocks in `body` |
| Custom Claude / ad-hoc bot | whatever the integration produces | treat as generic markdown |

### gh fetch commands (per source cluster)

```bash
# All top-level PR reviews (the "Approved" / "Changes requested" summaries)
gh pr view <N> --repo <o>/<r> --json reviews \
  --jq '.reviews[] | {id, author: .author.login, state, body, submittedAt}'

# All inline review comments (line-pinned)
gh api repos/<o>/<r>/pulls/<N>/comments --paginate \
  --jq '.[] | {id, user: .user.login, path, line, body, commit_id}'

# All issue/PR discussion comments (top-level, non-review)
gh api repos/<o>/<r>/issues/<N>/comments --paginate \
  --jq '.[] | {id, user: .user.login, body}'
```

Those three sources together cover everything GitHub-tracked.

### Parsing known bot formats

- **Devin** — look for `<!-- devin-review-comment { ... } -->` HTML comments embedding JSON with fields like `file_path`, `start_line`, `end_line`, `side`. Strip the HTML comment and extract the JSON.
- **Cubic** — look for `<violation number="N" location="path:line">...</violation>` XML blocks.
- **CodeRabbit** — look for 🔴 / 🟡 / ⚠️ emoji prefixes signaling severity; the preamble often starts with "Potential issue" / "Nitpick" / "Suggestion".
- **Bito** — look for `<div class="...">` wrapping `<div>issue</div>`, `<div>fix</div>`, `<div>citation</div>`. Strip HTML, extract fields.

For unknown bots, fall through to generic markdown parsing.

## Line-range clustering

Two comments on the same file + overlapping line range refer to the same concern. Merge them.

**Algorithm:**

1. Group items by `file`.
2. Within each file-group, sort items by `line` (ascending).
3. Walk the sorted list. For each item, if it's within ±5 lines of the previous item's range, merge into the same cluster. Otherwise, start a new cluster.

The ±5 fuzz handles cases where bot A flags line 42 and bot B flags line 44 (same function body, different specific concern).

Output:

```
Cluster 1: src/auth.ts:40-47
  - Copilot (L42): "Missing null check on user lookup"
  - Bito (L44): "Potential NullReferenceException here"
  - Human (L45): "Should we handle this case, or is it unreachable?"

Cluster 2: src/session.ts:87
  - Human: "Mutex held across await — deadlock?"

Cluster 3: README.md:14
  - CodeRabbit: "Typo: 'recieve' → 'receive'"
```

Clusters get evaluated as one unit. All three comments in Cluster 1 are about "null/missing value at the auth lookup" — one verdict, one response.

## Deduplication

Within a cluster, if two comments have effectively identical content:

```
"Add a null check here." (Copilot)
"Add null guard at this line." (Bito)
```

Merge into:

```
item:
  cluster: src/auth.ts:40-47
  sources: [Copilot, Bito]
  merged_verbatim: "Add a null check / null guard here."
```

The subsequent evaluation runs once; the response cites both sources.

Don't over-merge: if one reviewer says "null check" and another says "rate limit" on the same function, they're different concerns even if line-adjacent. Keep them distinct within the cluster.

## Conflict detection

Two reviewers disagree within a cluster. Example:

```
Cluster: src/worker.ts:100-108 (retry logic)
  - Copilot (L104): "Use exponential backoff with jitter"
  - CodeRabbit (L105): "Linear retry with fixed delay is sufficient here"
```

Surface the conflict explicitly in the action plan:

```
## Conflict in Cluster src/worker.ts:100-108
  Copilot recommends exponential backoff with jitter.
  CodeRabbit recommends linear fixed delay.

  Resolution: unresolved — needs human or architectural input.
  My analysis: <parent agent's technical take with evidence>
  Subagent analysis: <Explore subagent's take>
```

Do not silently pick one side. The disagreement itself is information.

## Noise filtering

Some feedback is a clear false positive. Common patterns:

- A static analyzer flags `import x from './x'` as unused because it doesn't resolve barrel re-exports
- A style bot flags a deliberate semicolon / whitespace choice the project has overridden
- A doc bot suggests adding a README section that already exists

For each, dismiss with a stated reason:

```
item (dismissed):
  source: Copilot (L15)
  verbatim: "Unused import of ./session."
  dismissed_reason: "Re-exported via barrel in src/index.ts:12 — static analyzer false positive."
```

Dismissals should be rare. If more than ~10% of feedback is dismissed as noise, look at your filter — you may be mis-flagging real concerns.

## The consolidated output

After the pipeline, the evaluation step sees one consolidated list:

```
Item 1: Cluster src/auth.ts:40-47 (null check)
  Sources: Copilot, Bito, Human
  Severity hint (from bot tags): important
  [sent to evaluation]

Item 2: Cluster src/session.ts:87 (mutex deadlock)
  Sources: Human
  Severity hint: critical
  [sent to evaluation]

Item 3: README.md:14 (typo)
  Sources: CodeRabbit
  Severity hint: minor
  [sent to evaluation]

Item 4 (conflict): src/worker.ts:100-108 (retry strategy)
  Sources: Copilot, CodeRabbit (disagreement)
  [sent to evaluation, flagged]

Item 5 (dismissed): src/index.ts:15 (import)
  Sources: Copilot
  Reason: barrel re-export
  [not sent to evaluation]
```

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Treat each reviewer's output as a separate todo list | Consolidate into one flat item list first |
| Merge two concerns that happen to share a line | Keep distinct concerns separate even in the same cluster |
| Silently pick between conflicting reviewer suggestions | Surface the conflict; let the human or architecture decide |
| Dismiss bot feedback en masse as "just bots" | Bots catch real bugs; dismiss individually with reason |
| Cluster too aggressively (100-line fuzz) | ±5 lines is the default; widen only with explicit justification |
| Cluster too tightly (exact line match only) | Ignores adjacent-line related concerns; use the fuzz |
