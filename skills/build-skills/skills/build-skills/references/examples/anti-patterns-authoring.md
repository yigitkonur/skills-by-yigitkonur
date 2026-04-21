# Anti-Patterns: Authoring Process

Anti-patterns in *how* a skill gets built, separated from anti-patterns in the skill's content itself. See `anti-patterns.md` for frontmatter, structure, content, and lifecycle anti-patterns.

These anti-patterns show up repeatedly when operators follow the build-skills workflow too loosely or make assumptions the skill does not support.

### AP-25: Reference overload

**Pattern:** Loading all 22+ reference files at once during Steps 3-4a.

**Why it fails:** Exhausts context window, causes the agent to lose track of which file informed which decision, and produces outputs that blend information without attribution.

**Fix:** Load only the 3-5 files relevant to the current step. Use the reference routing table in SKILL.md to select files.

**Detection:** Agent has read more than 5 reference files before completing Step 4.

### AP-26: Output batching

**Pattern:** Producing all output artifacts at the end instead of showing them at the step that produces them.

**Why it fails:** Prevents intermediate review, makes errors harder to catch, and creates a wall of output that's difficult to validate.

**Fix:** Show each artifact immediately after the step that produces it. Follow the timing hints in the output contract.

**Detection:** Agent reaches Step 7 without having shown any intermediate output.

### AP-27: Tool assumption

**Pattern:** Assuming `skill-dl` or other tools are installed because the skill mentions them.

**Why it fails:** First command fails, requiring backtracking and context recovery. Often leads to the agent fabricating results instead of using fallback methods.

**Fix:** Run `bash scripts/skill-dl --where` or `skill-dl --version` before first use. If `skill-dl` is missing globally, install it following the instructions in the cli-skill-downloader repo README. Have the fallback chain ready: skill-dl > MCP tools > manual GitHub search.

**Detection:** A tool command fails with "command not found" during execution.

### AP-28: Quality blindness

**Pattern:** Treating all downloaded skills as high-quality references regardless of their actual quality.

**Why it fails:** Produces comparison tables with only positive entries, missing the critical "avoid" patterns that inform synthesis decisions.

**Fix:** Apply the quality spectrum from `source-patterns.md`. Assign tiers. Document anti-patterns in the "avoid" column.

**Detection:** Comparison table has no "avoid" entries or all skills are rated positively.

### AP-29: Path confusion

**Pattern:** Writing test instructions that assume creation when the task is revision (or vice versa).

**Why it fails:** For new skills, trigger tests silently pass because the skill isn't installed. For revisions, tests miss regression against the existing version.

**Fix:** Explicitly identify which path you're on. Follow the creation vs. revision testing paths in `testing-methodology.md`.

**Detection:** All trigger tests "pass" but the skill wasn't installed before testing.

### AP-30: Research scope creep

**Pattern:** Downloading 20+ skills and reading all of them without a stopping criterion.

**Why it fails:** Consumes the entire research budget on discovery, leaving no time for deep comparison. Produces broad but shallow analysis.

**Fix:** Set a research budget before starting (see `research-workflow.md` phase gates). Stop when you have 3+ viable comparison entries.

**Detection:** More than 10 skills downloaded or more than 3 steps spent on research alone.

### AP-31: Checklist as workflow

**Pattern:** Treating the master checklist as a sequential todo list, working through all 100+ items for every task.

**Why it fails:** Simple revisions take as long as full builds. Checklist fatigue leads to rubber-stamping later items.

**Fix:** Use phase markers: "DRAFT ESSENTIAL" items (Phases 0-3) for every task, "FINAL AUDIT ONLY" items (Phases 4+) only for comprehensive quality passes.

**Detection:** Running Phase 6+ checklist items before having a complete draft.

### AP-32: Shipping a discipline skill without RED baseline

**Pattern:** Writing a discipline skill (TDD, research-before-synthesis, verification-before-merge) based on imagined rationalizations instead of ones actually observed.

**Why it fails:** The real loopholes are always ones you did not anticipate. The skill triggers correctly then gets bypassed under pressure.

**Fix:** Run a pressure scenario without the skill first, capture rationalizations verbatim, then address each one specifically. See `references/authoring/tdd-for-skills.md`.

**Detection:** No record of a RED baseline. Guardrails use generic "do not cheat" language instead of specific rationalization counters.

### AP-33: Persuasion mismatch

**Pattern:** Collaborative "we" language in a discipline skill, or absolute "YOU MUST" in a guidance skill.

**Why it fails:** Unity dilutes authority — agents read "the rule bends for us." Heavy authority in guidance skills makes every judgment call feel violable, so agents ignore the skill entirely.

**Fix:** Discipline → authority + commitment. Guidance → moderate authority + unity. Collaborative → unity + commitment. See `references/authoring/persuasion-principles.md`.

**Detection:** A discipline skill reads like an invitation. A reference skill reads like an interrogation.

### AP-34: Uniform freedom level

**Pattern:** The whole skill is at one freedom level — everything prescriptive or everything soft.

**Why it fails:** Uniform low freedom wastes judgment on deterministic steps. Uniform high freedom leaves the agent guessing at install commands and validation scripts.

**Fix:** Pick the level per step based on what breaks when the agent deviates. Install/validation → low. Workflow shape → medium. Approach selection → high. See `references/authoring/degrees-of-freedom.md`.

**Detection:** The skill feels uniformly prescriptive or uniformly loose.
