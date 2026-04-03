# Decision Tree Patterns

How to write effective decision trees that route agents to the correct reference files.

## Purpose

A decision tree is the primary navigation mechanism in a skill. It replaces linear lists with a visual hierarchy that helps the agent (and human readers) find the right reference file in one scan.

## Anatomy of a decision tree

```
What do you need?
│
├── Category A
│   ├── Specific task ──────────► references/category/file.md
│   └── Another task ───────────► references/category/other.md
│
├── Category B
│   ├── Sub-task ───────────────► Quick start (below)
│   └── Complex sub-task ───────► references/category/complex.md
│
└── Category C
    └── Only option ────────────► references/category/only.md
```

### Structure rules

| Rule | Why |
|---|---|
| Top-level branches = major categories | Agents scan top-level first |
| Leaf nodes = reference file pointers | Every leaf must resolve to a file or inline section |
| Max depth = 3 levels | Deeper trees confuse agents and slow routing |
| Mutually exclusive branches | Overlapping categories cause misroutes |
| Most common paths first | Agents tend to match the first applicable branch |

## Pattern 1: Task-based routing

Route by what the user is trying to accomplish. Best for skills with distinct workflows.

```
What do you need?
│
├── New project from scratch
│   ├── Install & setup ────────────────► Quick start (below)
│   └── Configuration options ──────────► references/setup/config-options.md
│
├── Add a feature
│   ├── Authentication ─────────────────► references/features/auth.md
│   ├── Database integration ───────────► references/features/database.md
│   └── API endpoints ─────────────────► references/features/api.md
│
├── Debug a problem
│   ├── Build errors ───────────────────► references/debug/build-errors.md
│   ├── Runtime errors ─────────────────► references/debug/runtime-errors.md
│   └── Performance issues ────────────► references/debug/performance.md
│
└── Deploy
    ├── Local testing ──────────────────► references/deploy/local.md
    └── Production ─────────────────────► references/deploy/production.md
```

**When to use**: Multi-purpose skills covering a tool or framework.

## Pattern 2: Phase-based routing

Route by where the user is in a workflow. Best for sequential processes.

```
Which phase are you in?
│
├── 1. Research
│   ├── Search for sources ────────────► references/research-workflow.md
│   └── Evaluate candidates ───────────► references/remote-sources.md
│
├── 2. Compare
│   ├── Build comparison table ────────► references/comparison-workflow.md
│   └── Apply source patterns ────────► references/source-patterns.md
│
├── 3. Synthesize
│   ├── Draft the skill ──────────────► Quick start (below)
│   └── Validate output ──────────────► references/validation.md
│
└── 4. Ship
    └── Final checks ─────────────────► references/shipping-checklist.md
```

**When to use**: Skills that guide a multi-step process.

## Pattern 3: Concept-based routing

Route by domain concept. Best for reference-heavy skills (SDKs, APIs).

```
What concept?
│
├── Authentication
│   ├── OAuth flow ────────────────────► references/auth/oauth.md
│   ├── API keys ──────────────────────► references/auth/api-keys.md
│   └── Token refresh ────────────────► references/auth/token-refresh.md
│
├── Data models
│   ├── User model ────────────────────► references/models/user.md
│   ├── Product model ─────────────────► references/models/product.md
│   └── Relationships ────────────────► references/models/relationships.md
│
└── Type reference
    ├── Request types ─────────────────► references/types/request.md
    ├── Response types ────────────────► references/types/response.md
    └── Error types ───────────────────► references/types/error.md
```

**When to use**: SDK or API documentation skills.

## Pattern 4: Hybrid routing

Combine task and concept routing. Use when the skill serves both "how do I" and "what is" questions.

```
What do you need?
│
├── Build something
│   ├── New app ───────────────────────► Quick start (below)
│   ├── Add auth ──────────────────────► references/guides/auth.md
│   └── Add payments ─────────────────► references/guides/payments.md
│
├── Understand a concept
│   ├── Architecture ──────────────────► references/concepts/architecture.md
│   └── Data flow ─────────────────────► references/concepts/data-flow.md
│
└── Fix something
    ├── Common errors ─────────────────► references/troubleshooting/errors.md
    └── Migration issues ─────────────► references/troubleshooting/migration.md
```

## Sizing guidelines

| Skill complexity | Branches | Leaf nodes | Reference files |
|---|---|---|---|
| Simple (single workflow) | 2-3 | 4-8 | 3-5 |
| Medium (multi-workflow) | 4-6 | 10-20 | 8-15 |
| Complex (full SDK/framework) | 6-10 | 20-50 | 15-40 |

## Writing leaf labels

Each leaf should clearly state what the reference covers, not just a filename.

### Good leaf labels

```
├── Install & basic example ────────────► Quick start (below)
├── Client constructor options ─────────► references/client/setup.md
├── Streaming subscription patterns ──► references/events/streaming.md
```

### Bad leaf labels

```
├── Setup ──────────────────────────────► references/setup.md
├── Options ────────────────────────────► references/options.md
├── Events ─────────────────────────────► references/events.md
```

The bad labels are too vague — the agent cannot distinguish between them when routing.

## Arrow alignment

Align arrows for readability. Use enough `─` characters to create a visual column.

```
├── Short label ────────────────────────► references/file.md
├── A much longer descriptive label ──► references/other-file.md
├── Medium label ───────────────────────► references/third.md
```

The `►` column should be roughly aligned. Exact alignment is less important than consistent visual structure.

## Inline section references

Not every leaf needs a separate file. Simple topics can point to sections within SKILL.md.

```
├── Install & basic example ────────────► Quick start (below)
├── Abort in-flight work ──────────────► Key patterns: Abort (below)
```

Use inline references when:
- The content is under 20 lines
- It's a universal pattern every user needs
- Splitting it into a file would create too many tiny files

## Self-referencing from SKILL.md

Every reference file must be reachable from the decision tree OR a reading set. Unreferenced files are dead weight.

### Verification rule

```
for each file in references/:
  assert file is mentioned in:
    - decision tree leaf, OR
    - minimal reading set, OR
    - reference routing table
```

## Common mistakes

| Mistake | Problem | Fix |
|---|---|---|
| Overlapping branches | Agent routes to wrong file | Make branches mutually exclusive |
| Too many levels | Agent loses track of context | Max 3 levels deep |
| Missing leaves | Category exists but has no routing target | Every branch must terminate at a reference |
| Alphabetical ordering | Uncommon paths appear first | Order by frequency of use |
| Filename-only labels | Agent cannot distinguish files | Use descriptive action labels |
| Giant flat list | No hierarchy — agent scans linearly | Group into 3-7 top-level categories |
| Orphaned references | Files exist but tree doesn't point to them | Audit: every file must appear in tree |

## Template for starting a new decision tree

```markdown
## Decision tree

\```
What do you need?
│
├── [Most common category]
│   ├── [Specific task] ────────────────► [target]
│   ├── [Specific task] ────────────────► [target]
│   └── [Specific task] ────────────────► [target]
│
├── [Second category]
│   ├── [Specific task] ────────────────► [target]
│   └── [Specific task] ────────────────► [target]
│
├── [Third category]
│   └── [Specific task] ────────────────► [target]
│
└── [Edge case / advanced]
    └── [Specific task] ────────────────► [target]
\```
```

Replace `[target]` with either:
- `references/category/file.md` for detailed content
- `Quick start (below)` for inline content
- `Key patterns: Section Name (below)` for inline patterns

## Evolving a decision tree

As a skill grows:

1. Start with a flat list of 3-5 references
2. Group related references into categories when count exceeds 8
3. Add the tree when categories emerge naturally
4. Split oversized categories (>7 leaves) into subcategories
5. Prune unused branches when reference files are removed

Never pre-build a complex tree for content that doesn't exist yet.
