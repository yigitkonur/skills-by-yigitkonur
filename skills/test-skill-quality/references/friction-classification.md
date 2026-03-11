# Friction Classification

How to assign severity and classify derailments found during a Derailment Test.

## Severity levels

### P0 — Blocks progress

The executor cannot continue without external intervention, guesswork, or abandoning the instructions.

**Assign P0 when:**
- The executor hits a hard stop (tool not installed, command fails, output location unknown)
- Two authoritative sources contradict each other and the text cannot resolve it
- The executor must invent information that should have been specified

**Examples:**

| Derailment | Why P0 |
|---|---|
| `skill-dl: command not found` during research step | Tool prerequisite undocumented. Cannot proceed. |
| Document A says "write a URL file"; Document B says "run the script" | Two parallel workflows, no guidance on which to follow. |
| "Write `skills.markdown`" — no location specified | Must guess: repo root? skill dir? Wrong choice corrupts workflow. |

### P1 — Causes confusion or wasted time

The executor can eventually continue but wastes significant time, makes a wrong assumption, or takes an incorrect path before recovering.

**Assign P1 when:**
- The executor re-reads the instructions multiple times to understand what was meant
- The executor takes a wrong action before realizing the correct one
- The executor uses implicit knowledge to fill a gap that should have been explicit

**Examples:**

| Derailment | Why P1 |
|---|---|
| "Substantial redesign" with no examples | Executor second-guesses classification for 5+ minutes |
| Comma vs. space keyword formats undocumented | Wrong format → error → debugging |
| Comparison table columns in Document A but not Document B | Executor builds table with wrong columns |

### P2 — Minor annoyance

The executor notices something off but can continue without material delay.

**Assign P2 when:**
- The executor pauses briefly but continues correctly
- The issue is cosmetic, naming-related, or a documentation inconsistency that doesn't affect execution
- The issue only matters to a very thorough executor

**Examples:**

| Derailment | Why P2 |
|---|---|
| Niche topics break cross-keyword ranking | Can still manually curate results |
| URL-encoded names in tool output | Cosmetic, doesn't block download |
| `.markdown` vs `.md` extension unexplained | Convention is followable even if unexplained |

## Severity assignment flowchart

```
Does the executor hit a hard stop?
├── YES → P0
└── NO
    ├── Did the executor waste significant time or take a wrong action?
    │   ├── YES → P1
    │   └── NO → P2
    └── Did the executor need external knowledge to continue?
        ├── YES, critical decision → P1
        └── YES, minor gap → P2
```

## Compound severity

Multiple P1 items in the same workflow step can create a **compound P0**. The combined confusion effectively blocks progress.

**Rule:** If 3+ P1 items cluster in a single workflow step, treat the cluster as P0 for prioritization purposes.

## Cross-run consistency

- Friction point IDs are **per-run** (each run starts at F-01)
- Use the file name (`01-dogfood-swift.md`, `02-dogfood-react.md`) to scope IDs
- If the same derailment appears in multiple runs, that signals higher severity
- Track recurrence in a summary table:

```markdown
| Derailment type | Run 1 | Run 2 | Run 3 | Action |
|---|---|---|---|---|
| Missing prerequisite | F-01 | — | — | Fixed after run 1 |
| Ambiguous threshold | F-02 | F-03 | — | Improved, not fully resolved |
```

## Per friction point checklist

- [ ] ID assigned (F-NN)
- [ ] Severity assigned (P0/P1/P2)
- [ ] Root cause tagged (see `root-cause-taxonomy.md`)
- [ ] One-paragraph description written
- [ ] Specific fix proposed
- [ ] Fix location identified (which file, which section)
