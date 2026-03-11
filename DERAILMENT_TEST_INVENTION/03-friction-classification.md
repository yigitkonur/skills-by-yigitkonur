# Friction Classification System

How to classify, score, and prioritize derailments found during testing.

---

## Severity levels

Every friction point receives exactly one severity level. The assignment is based on **impact on the executor**, not on how hard it is to fix.

### P0 — Blocks progress

The executor cannot continue without external intervention, guesswork, or abandoning the instructions entirely.

**Diagnostic questions:**
- Does the executor hit a hard stop (tool not installed, command fails, output location unknown)?
- Is there a contradiction between two authoritative sources that cannot be resolved from the text?
- Does the executor need to invent information that should have been specified?

**Examples from practice:**

| ID | Derailment | Why P0 |
|---|---|---|
| F-01 | `skill-dl: command not found` during research step | Tool prerequisite was undocumented. Executor cannot proceed. |
| F-04 | research-workflow.md says "write a URL file" but skill-research.sh skips it | Two parallel workflows with no guidance on which to follow. Executor is stuck. |
| F-13 | "Write `skills.markdown`" — no location specified | Executor must guess: repo root? skill dir? temp dir? Wrong choice corrupts the workflow. |

**Characteristics:**
- Always requires a fix before the next test cycle
- Usually caused by missing prerequisites, contradictory instructions, or unspecified outputs
- Typically discovered in the first execution of a workflow (not edge cases)

### P1 — Causes confusion or wasted time

The executor can eventually continue but wastes significant time, makes a wrong assumption, or takes an incorrect path before recovering.

**Diagnostic questions:**
- Did the executor need to re-read the instructions multiple times to understand what was meant?
- Did the executor take a wrong action before realizing the correct one?
- Did the executor use implicit knowledge to fill a gap that should have been explicit?

**Examples from practice:**

| ID | Derailment | Why P1 |
|---|---|---|
| F-02 | "Substantial redesign" has no examples | Executor second-guesses the classification for 5+ minutes |
| F-05 | Comma vs. space keyword formats undocumented | Executor uses wrong format, gets an error, then has to debug |
| F-15 | Comparison table columns listed in SKILL.md but not in research-workflow.md | Executor reading only the research guide builds a table with wrong columns |
| F-17 | "Run 5+ trigger queries" gives no execution method | Executor doesn't know whether to test in Claude.ai, script it, or just imagine results |

**Characteristics:**
- Should be fixed in the current cycle if possible
- Often caused by ambiguous language, missing examples, or scattered information
- Can compound with other P1s to create an effective P0

### P2 — Minor annoyance

The executor notices something off but can continue without material delay. The annoyance becomes significant only at scale or across multiple test runs.

**Diagnostic questions:**
- Did the executor briefly pause but then continue correctly?
- Is the issue cosmetic, naming-related, or a documentation inconsistency that doesn't affect execution?
- Would the issue only matter to a very thorough or pedantic executor?

**Examples from practice:**

| ID | Derailment | Why P2 |
|---|---|---|
| F-07 | Niche topics break cross-keyword ranking | Executor can still manually curate results |
| F-08 | URL-encoded skill names in output | Cosmetic, doesn't block download |
| F-14 | `.markdown` vs `.md` extension unexplained | Convention is followable even if unexplained |

**Characteristics:**
- Fix if time allows; defer if not
- Often about naming, cosmetics, or edge-case handling
- Useful signal for polish passes but not blockers

## Severity assignment flowchart

```
Does the executor hit a hard stop?
├── YES → P0
└── NO
    ├── Did the executor waste significant time or take a wrong action?
    │   ├── YES → P1
    │   └── NO → P2
    └── Did the executor need external knowledge to continue?
        ├── YES, and the knowledge gap is about a critical decision → P1
        └── YES, but the gap is minor or recoverable → P2
```

## Root cause taxonomy

Beyond severity, each friction point should be tagged with a root cause. This enables pattern analysis across multiple test runs.

### Structural causes (problems in the document architecture)

| Code | Root cause | Description | Typical severity |
|---|---|---|---|
| S1 | **Missing prerequisite** | Tool, file, or config required but not declared before first use | P0 |
| S2 | **Contradictory paths** | Two documents prescribe different workflows for the same situation | P0 |
| S3 | **Scattered information** | Required info split across files without cross-reference | P1 |
| S4 | **Orphaned reference** | File exists in references/ but is never routed from the main document | P2 |

### Semantic causes (problems in the language)

| Code | Root cause | Description | Typical severity |
|---|---|---|---|
| M1 | **Ambiguous threshold** | Vague boundary word ("substantial", "appropriate", "as needed") without examples | P1 |
| M2 | **Unstated location** | Output destination not specified | P0 |
| M3 | **Format inconsistency** | Same concept described with different syntax or naming | P1 |
| M4 | **Missing execution method** | What to do is stated, but how to do it is not | P1 |
| M5 | **Assumed knowledge** | Step requires information not present in the document | P1–P2 |

### Operational causes (problems discovered during execution)

| Code | Root cause | Description | Typical severity |
|---|---|---|---|
| O1 | **Silent failure** | Command fails without error message or recovery guidance | P1 |
| O2 | **Tool output mismatch** | Tool produces different output format than documented | P2 |
| O3 | **Edge case unhandled** | Valid input produces unexpected behavior | P2 |
| O4 | **Scaling breakdown** | Process works for small inputs but breaks at realistic scale | P2 |

## Compound severity

Multiple P1 friction points in the same workflow phase can create a **compound P0** — the combined confusion from several ambiguities effectively blocks progress even though each individual point is recoverable.

**Rule:** If 3+ P1 items cluster in a single workflow step, treat the cluster as P0 for prioritization purposes.

Example: In the Swift/watchOS dogfood test, Step 4 (remote research) had F-04, F-05, F-06, and F-07 clustered together. While each was individually recoverable, together they made the research phase feel like guesswork.

## Cross-run consistency

When running multiple Derailment Tests on the same instruction set:

- Friction point IDs are **per-run**, not global. Each run starts at F-01.
- Use the file name (`01-dogfood-swift.md`, `02-dogfood-react.md`) to scope IDs.
- If the same derailment appears in multiple runs, that is strong signal for higher severity.
- Track **recurrence count** in a summary table across runs:

```markdown
| Derailment type | Run 1 | Run 2 | Run 3 | Action |
|---|---|---|---|---|
| Missing prerequisite | F-01 | — | — | Fixed after run 1 |
| Ambiguous threshold | F-02 | F-03 | — | Improved but not fully resolved |
| Format inconsistency | F-05 | F-07 | F-02 | Systemic — needs architectural fix |
```

## Assignment checklist

For each friction point, verify:

- [ ] ID assigned (F-NN)
- [ ] Severity assigned (P0/P1/P2)
- [ ] Root cause tagged (S1, M1, O1, etc.)
- [ ] One-paragraph description written
- [ ] Specific fix proposed
- [ ] Fix location identified (which file, which section)
