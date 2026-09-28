# Comprehensive Friction Taxonomy & Root-Cause Analysis Guide

A unified reference for identifying friction markers, assigning severity levels, and diagnosing root causes across Structural, Semantic, Operational, and Cognitive dimensions.

---

## 1. The 4 Friction Markers

Tag every deviation or unexpected event observed in execution scrollbacks or synthetic subagent traces with one of four standard markers:

| Marker | Severity | Definition | Concrete Example |
|---|---|---|---|
| `[STUCK]` | **P0** (Hard Stop) | The executor cannot proceed without external human intervention or unstated knowledge. | Page halts on an unhandled modal backdrop; required API token is missing; target output folder does not exist and script does not create parent dirs. |
| `[BROKE]` | **P0 / P1** (Runtime Crash) | A documented command, CLI flag, API call, or DOM selector threw an unhandled error. | Calling non-existent `page.isVisible()`; running `node script.mjs --ratio 16:9` where flag is `--aspect-ratio`; script syntax error. |
| `[GUESSED]` | **P1** (Ambiguity Gap) | The executor had to invent a decision or parameter that the skill should have made explicit. | Guessing which Google account profile to select when multiple are logged in; guessing whether video resolution should be 720p or 1080p. |
| `[NICE]` | **Keep** (Load-Bearing) | A specific instruction, selector pattern, or resilience check prevented an error. | Backdrop escape rule prevented element interception; atomic `.tmp` download check caught a corrupt file. **Never delete lines tagged [NICE].** |

---

## 2. Severity Hierarchy & Prioritization Rules

- **P0 (Critical / Blocker):** Hard stop or command crash that halted the workflow. Must be fixed before any other changes.
- **P1 (High / Wasteful):** Confusion, retried loops, path drift, or guessed parameters that wasted time but eventually allowed continuation.
- **P2 (Low / Minor Annoyance):** Minor wording ambiguity or cosmetic warning that did not cause measurable delay.
- **Compound P0 Rule:** Three or more P1 friction points occurring within a single workflow phase collapse into a **Compound P0** for prioritization purposes.

---

## 3. The 4 Root-Cause Families

Every friction point originates from one of four underlying defect families in the skill:

### A. Structural Causes (`S`)
Defects in how information is organized, layered, or connected across files.
- `S1` **Missing prerequisite:** Required tool, binary, environment variable, or parent folder not declared before use.
- `S2` **Contradictory paths:** Two sections or reference files prescribe conflicting workflows or CLI commands.
- `S3` **Scattered information:** Crucial instructions split across disparate files without direct links.
- `S4` **Orphaned reference:** Reference file exists in `references/` but is never linked from `SKILL.md`.
- `S5` **Circular dependency:** Document A instructs reader to see Document B; Document B instructs reader to see Document A.

### B. Semantic Causes (`M`)
Defects in phrasing, terminology, thresholds, or specificity.
- `M1` **Ambiguous threshold:** Vague qualitative adjectives ("substantial", "high quality", "fast") without numerical benchmarks.
- `M2` **Unstated location:** Target output path or naming convention not specified (causes agent to guess `/tmp` or cwd).
- `M3` **Format inconsistency:** The same entity or parameter described with differing syntaxes.
- `M4` **Missing execution method:** States *what* outcome to achieve, but omits the exact *how* (command or script).
- `M5` **Assumed knowledge:** Assumes domain expertise or hidden conventions not explained in the text.
- `M6` **Vague verb:** Action words open to multiple divergent interpretations ("process", "handle", "integrate").

### C. Operational Causes (`O`)
Defects in runtime mechanics, scripts, tool handling, and environments.
- `O1` **Silent failure:** Command or script fails without emitting a non-zero exit code or clear diagnostic message.
- `O2` **Tool output mismatch:** Script emits data in a format or schema different from what `SKILL.md` documents.
- `O3` **Edge case unhandled:** Valid input (e.g. prompt with `%` or quotes) breaks the underlying parser or selector.
- `O4` **Scaling breakdown:** Works on small test cases (1 file), hangs or crashes at realistic scale (10 scenes).
- `O5` **Stale reference:** Documents a CLI flag, tool version, or selector that no longer exists in production.
- `O6` **Harness-induced drift:** The test prompt or wrapper introduced artificial constraints not present in real use.

### D. Cognitive & Behavioral Causes (`C`)
Defects in instruction pacing and gating that lead autonomous models to derail.
- `C1` **Premature completion illusion:** Agent equates generating local files with total task completion, skipping remote or E2E gates.
- `C2` **Destructive / mutation hesitation:** Agent hesitates to delete, overwrite, or deprecate files without explicit authorization.
- `C3` **Missing tooling awareness:** Agent runs `--help` or invents workarounds because it is unaware a specialized tool or script exists.
- `C4` **Gate slack / step skipping:** Steps lack checkable exit gates, allowing the model to skim past critical verifications.

---

## 4. Comprehensive Root Cause to Fix Pattern Matrix (All 21 Codes)

| Code | Defect Description | Remediation Fix Pattern |
|---|---|---|
| `S1` | Missing tool/prerequisite | **Prerequisite Surfacing**: Add pre-flight check with exact install/config command before Step 1. |
| `S2` | Contradictory workflows | **Path Reconciliation**: Co-locate alternate paths in one table with explicit `if/then` selection criteria. |
| `S3` | Scattered documentation | **Schema Duplication / Inlining**: Place critical parameters and canonical schemas directly at point of use. |
| `S4` | Orphaned reference | **Router Integration**: Ensure every file in `references/` is explicitly routed with a "Read When" trigger from `SKILL.md`. |
| `S5` | Circular dependency | **Hierarchical Directionality**: Enforce a strict parent-router to leaf-reference topology with zero back-links or loops. |
| `M1` | Vague threshold | **Threshold Concretization**: Replace adjectives with strict numeric boundaries (e.g. `> 100_000 bytes`, `<= 120 chars`). |
| `M2` | Unknown output location | **Output Location Specification**: Specify exact canonical path using user-known directories (e.g. `~/Downloads/flow-videos/`). |
| `M3` | Format inconsistency | **Format Alignment**: Standardize on one canonical format/syntax once; provide conversion notes at boundaries. |
| `M4` | Missing command recipe | **Execution Method Specification**: Provide exact, copy-pasteable CLI commands or script recipes with all required flags. |
| `M5` | Assumed knowledge | **Scaling Guidance & Context Injection**: Surface implicit conventions, background context, or scale-dependent rules directly. |
| `M6` | Vague verb | **Actionable Verb Specification / Source Rewrite**: Replace ambiguous verbs ("process", "handle") with concrete operational verbs. |
| `O1` | Silent crash | **Error Recovery Addition**: Add explicit try/catch, non-zero exit codes, and fallback instructions. |
| `O2` | Tool output mismatch | **Format Alignment**: Reconcile script output schemas with `SKILL.md` parser expectations. |
| `O3` | Edge case unhandled | **Edge Case Hardening**: Add input sanitization, delimiter escaping, and explicit edge-case guards. |
| `O4` | Scaling breakdown | **Scaling Guidance**: Add batching, streaming pagination, or concurrency limits for realistic fleet scale. |
| `O5` | Stale CLI option | **Option Modernization**: Update script and documentation to current runtime CLI spec and flags. |
| `O6` | Harness-induced drift | **Harness Alignment**: Strip synthetic test-only constraints; judge executors strictly against real skill requirements. |
| `C1` | Premature completion | **Two-Tier Verification Enclosure**: Enforce strict Phase Exit gates requiring physical disk & exit code proof. |
| `C2` | Mutation hesitation | **Staged Deprecation & Safe Neutralization**: Prescribe a 4-step sequence (`Categorize` ➔ `Shadow` ➔ `Flip Required Check` ➔ `Neutralize Triggers`) to safely modify/retire legacy assets. |
| `C3` | Running `--help` avoidance | **Actionable Fast Probes**: Provide sub-second `--probe` or `--dry-run` commands that prove readiness. |
| `C4` | Skipped verification steps | **Rigid Checkable Gates**: Add machine-readable delimiter checks (`__TAKE_RESULT_JSON_START__` / `__TAKE_RESULT_JSON_END__`) before proceeding. |
