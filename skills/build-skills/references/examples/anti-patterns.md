# Anti-Patterns

Common mistakes in skill authoring and how to avoid them. Each anti-pattern includes what goes wrong, why it's a problem, and the correct approach.

## Category 1: Frontmatter problems

### AP-1: Vague description

**Wrong:**
```yaml
description: Helps with code reviews.
```

**Problem:** No trigger phrases. The agent cannot distinguish this from dozens of other skills. Auto-invocation fails because "code reviews" is too generic.

**Fix:**
```yaml
description: Use skill if you are reviewing a GitHub pull request with a systematic, evidence-based workflow that clusters files, correlates existing comments, validates goals, and produces actionable findings.
```

**Rule:** Description must answer: What action? What outcome? What context? Include keywords users would naturally say.

### AP-2: Angle brackets in frontmatter

**Wrong:**
```yaml
description: Use skill to <generate> React components with <proper> typing.
```

**Problem:** YAML parsers may interpret `<` and `>` as XML tags, injecting unintended instructions into the agent's context.

**Fix:**
```yaml
description: Use skill if you are generating React components with TypeScript types and test scaffolding.
```

**Rule:** Never use `<` or `>` in any frontmatter field.

### AP-3: Missing frontmatter delimiters

**Wrong:**
```markdown
name: my-skill
description: Does something.

# My Skill
...
```

**Problem:** Without `---` delimiters starting on line 1, the frontmatter is parsed as regular markdown. The skill loads without metadata, breaking auto-invocation.

**Fix:**
```markdown
---
name: my-skill
description: Does something useful when...
---

# My Skill
...
```

**Rule:** `---` must be on line 1. No blank lines before it.

### AP-4: Over-broad allowed-tools

**Wrong:**
```yaml
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, Task, Agent
```

**Problem:** Grants the skill access to every tool, including destructive ones. A read-only skill shouldn't have `Write` or `Bash` permissions.

**Fix:**
```yaml
allowed-tools: Read, Grep, Glob
```

**Rule:** List only the tools the skill actually needs. Principle of least privilege.

### AP-5: Missing disable-model-invocation on dangerous skills

**Wrong:**
```yaml
name: deploy-production
description: Deploy the application to production.
```

**Problem:** The agent may auto-invoke this skill when the user mentions "production," causing unintended deployments.

**Fix:**
```yaml
name: deploy-production
description: Deploy the application to production environment.
disable-model-invocation: true
```

**Rule:** Any skill with side effects (deploy, delete, commit, publish) should use `disable-model-invocation: true`.

## Category 2: Structure problems

### AP-6: Monolithic SKILL.md

**Wrong:**
```
my-skill/
└── SKILL.md    # 1200 lines — everything in one file
```

**Problem:** Exceeds the ~5K token Level 2 budget. The agent loads all 1200 lines on invocation, wasting context on irrelevant sections.

**Fix:**
```
my-skill/
├── SKILL.md              # 250 lines — routing + quick start + key patterns
└── references/
    ├── detailed-guide.md  # 300 lines
    ├── api-reference.md   # 250 lines
    └── troubleshooting.md # 200 lines
```

**Rule:** SKILL.md under 500 lines. Move detailed content to `references/`.

### AP-7: Empty SKILL.md with content only in references

**Wrong:**
```markdown
---
name: my-skill
description: Does things.
---

# My Skill

See references/ for all documentation.
```

**Problem:** The agent has no routing, no workflow, and no context when the skill is invoked. It must blindly read every reference file.

**Fix:** SKILL.md should contain a decision tree, quick start, key patterns, and routing to references. It should be self-sufficient for the 80% use case.

### AP-8: Orphaned reference files

**Wrong:**
```
references/
├── guide.md           # Referenced from decision tree ✅
├── old-draft.md       # Not referenced anywhere ❌
├── notes.md           # Author's personal notes ❌
└── backup-guide.md    # Backup of guide.md ❌
```

**Problem:** Orphaned files waste disk space and confuse anyone auditing the skill. The agent may accidentally read them.

**Fix:** Every file in `references/` must be reachable from SKILL.md (decision tree, reading set, or routing table). Delete everything else.

### AP-9: Deep directory nesting

**Wrong:**
```
references/
└── category/
    └── subcategory/
        └── topic/
            └── subtopic/
                └── file.md
```

**Problem:** Deep nesting makes paths long and hard to reference from SKILL.md. Agents may struggle with deeply nested file reads.

**Fix:** Max 2 levels: `references/category/file.md`. If you need more depth, the skill should be split.

### AP-10: Mixed concerns in reference files

**Wrong:** A single `everything.md` covering authentication, database setup, deployment, and error handling.

**Problem:** When the agent needs auth guidance, it loads 400 lines of unrelated content.

**Fix:** One topic per reference file. Split into `auth.md`, `database.md`, `deployment.md`, `error-handling.md`.

## Category 3: Content problems

### AP-11: Copying a source skill wholesale

**Wrong:** Downloading a skill from Playbooks, renaming the directory, and publishing it as your own.

**Problem:**
- Copyright violation (if the source has a restrictive license)
- No adaptation to the target use case
- Inherited bugs and outdated patterns
- Duplicate content in the ecosystem

**Fix:** Research multiple sources, build a comparison table, synthesize an original result. Acknowledge sources in README.

### AP-12: Imperative overload

**Wrong:**
```markdown
## Rules

1. Always use TypeScript strict mode.
2. Always add JSDoc comments.
3. Always use named exports.
4. Never use `any` type.
5. Never use `var`.
6. Never skip error handling.
7. Always write tests first.
8. Always use async/await.
9. Never use callbacks.
10. Always log errors.
... (50 more rules)
```

**Problem:** Too many "always/never" rules overwhelm the agent. It tries to follow all of them simultaneously and produces stilted, over-engineered output.

**Fix:** Keep to 5-7 essential rules. Put the rest in a reference file for edge cases.

### AP-13: No examples

**Wrong:**
```markdown
## Steps

1. Create the component file
2. Add TypeScript types
3. Write the test
```

**Problem:** The agent doesn't know what the expected output looks like. It will guess, often incorrectly.

**Fix:** Include at least one complete input/output example:

```markdown
## Example

For a component named `UserCard`:

\```tsx
export interface UserCardProps {
  name: string;
}
export function UserCard({ name }: UserCardProps) {
  return <div>{name}</div>;
}
\```
```

### AP-14: Outdated API references

**Wrong:** Examples using deprecated API methods, removed CLI flags, or old library versions without version context.

**Problem:** The agent produces code that doesn't compile or run. Users waste time debugging the skill's incorrect guidance.

**Fix:** Pin examples to specific versions. Include a version note. Test examples before publishing.

### AP-15: Prose where tables work better

**Wrong:**
```markdown
The most common pitfall is forgetting to set the permission handler,
which is required on every session creation. Another common issue is
the default timeout of 60 seconds, which is too short for long tasks.
You should also remember to enable streaming...
```

**Problem:** Agents parse prose less efficiently than tables. Important details get buried in paragraphs.

**Fix:**
```markdown
| Pitfall | Fix |
|---------|-----|
| Missing permission handler | Required on every `createSession`. Use `approveAll`. |
| Default 60s timeout | Pass explicit: `sendAndWait(opts, 300_000)`. |
| Streaming not working | Set `streaming: true` in SessionConfig. |
```

## Category 4: Workflow problems

### AP-16: Skipping research for non-trivial skills

**Wrong:** Creating a new skill entirely from memory or a single source, without checking what already exists.

**Problem:** You miss established patterns, repeat mistakes others solved, and produce a skill that's inferior to existing alternatives.

**Fix:** For new skills or major redesigns, always:
1. Search for existing skills on the same topic
2. Read 3-5 high-quality candidates
3. Build a comparison table
4. Synthesize an original result

### AP-17: Research without artifacts

**Wrong:** "I looked at some skills and this is what I think we should do."

**Problem:** No evidence trail. The comparison happened in the author's head. Nobody can verify, reproduce, or build on the research.

**Fix:** Produce `skills.markdown` with search queries, candidate list, download paths, and comparison table.

### AP-18: Comparison without decisions

**Wrong:**
```markdown
| Source | Description |
|--------|------------|
| Skill A | Interesting approach to auth |
| Skill B | Good reference structure |
| Skill C | Nice decision tree |
```

**Problem:** Observations without decisions. What should be inherited? What should be avoided? This table doesn't help synthesis.

**Fix:** Add decision columns:
```markdown
| Source | Strengths | Gaps | Inherit / Avoid |
|--------|----------|------|-----------------|
| Skill A | Auth workflow | No tree | Inherit auth patterns, avoid flat structure |
```

## Category 5: Lifecycle problems

### AP-19: No testing before shipping

**Wrong:** Publishing a skill without running any trigger or functional tests.

**Problem:** The skill may not trigger on intended queries, may trigger on unrelated ones, or may produce incorrect output. Users encounter these issues first.

**Fix:** Run at minimum: 5 should-trigger queries, 5 should-NOT-trigger queries, and 1 full workflow test. See `references/authoring/testing-methodology.md`.

### AP-20: No success criteria defined

**Wrong:** "The skill should work well" with no measurable definition of success.

**Problem:** No way to know if the skill is actually improving outcomes. Iteration has no direction.

**Fix:** Define before building: trigger accuracy target (90%+), tool call count target, token budget, qualitative criteria (no user corrections, consistent output).

### AP-21: No negative triggers on broad-scope skill

**Wrong:** A skill covering a broad topic ("data analysis") with no exclusions in the description.

**Problem:** The skill fires on tangentially related queries, interfering with other skills and confusing users.

**Fix:** Add explicit exclusions:
```yaml
description: Advanced statistical analysis for CSV files. Use for
  regression and clustering. Do NOT use for simple data exploration
  (use data-viz skill instead).
```

### AP-22: No iteration plan after deployment

**Wrong:** Shipping a skill and never updating it.

**Problem:** Users encounter issues, descriptions drift from actual usage patterns, API references become outdated, and the skill quietly degrades.

**Fix:** Plan for at least: weekly review during first month, monthly API reference checks, quarterly metrics review. See `references/iteration/feedback-signals.md`.

### AP-23: Using prose instead of scripts for deterministic checks

**Wrong:**
```markdown
Make sure the output has all required sections and proper formatting.
```

**Problem:** Language instructions are interpreted non-deterministically. The model may skip checks, interpret "proper" differently each time, or consider the check done after a cursory glance.

**Fix:** Bundle a validation script:
```markdown
After generating the report, run:
`python scripts/validate_report.py --input output.md`
This checks: section count, formatting, data completeness.
```

Code is deterministic; language instructions are not.

### AP-24: Reserved name containing "claude" or "anthropic"

**Wrong:**
```yaml
name: claude-code-helper
name: anthropic-review-tool
```

**Problem:** Anthropic reserves these prefixes. Skills with these names are rejected during upload.

**Fix:** Use descriptive names that don't reference the platform:
```yaml
name: code-review-helper
name: agent-review-tool
```

## Quick reference: anti-pattern checklist

Before publishing, verify none of these apply:

- [ ] Vague description without trigger phrases (AP-1)
- [ ] Angle brackets in frontmatter (AP-2)
- [ ] Missing `---` delimiters (AP-3)
- [ ] Over-broad `allowed-tools` (AP-4)
- [ ] Dangerous skill without `disable-model-invocation` (AP-5)
- [ ] SKILL.md over 500 lines (AP-6)
- [ ] Empty SKILL.md (AP-7)
- [ ] Orphaned reference files (AP-8)
- [ ] Deep directory nesting >2 levels (AP-9)
- [ ] Mixed concerns in reference files (AP-10)
- [ ] Copied without synthesis (AP-11)
- [ ] Too many imperative rules (AP-12)
- [ ] No examples (AP-13)
- [ ] Outdated API references (AP-14)
- [ ] Prose where tables work better (AP-15)
- [ ] No research for non-trivial skill (AP-16)
- [ ] Research without artifacts (AP-17)
- [ ] Comparison without decisions (AP-18)
- [ ] No testing before shipping (AP-19)
- [ ] No success criteria defined (AP-20)
- [ ] No negative triggers on broad-scope skill (AP-21)
- [ ] No iteration plan after deployment (AP-22)
- [ ] Using prose instead of scripts for deterministic checks (AP-23)
- [ ] Reserved name containing "claude" or "anthropic" (AP-24)


---

## Derailment anti-patterns (AP-D1 through AP-D7)

These anti-patterns were discovered through systematic derailment testing of the build-skills workflow.

### AP-D1: Reference overload

**Pattern:** Loading all 22+ reference files at once during Steps 3-4a.

**Why it fails:** Exhausts context window, causes the agent to lose track of which file informed which decision, and produces outputs that blend information without attribution.

**Fix:** Load only the 3-5 files relevant to the current step. Use the reference routing table in SKILL.md to select files.

**Detection:** Agent has read more than 5 reference files before completing Step 4.

### AP-D2: Output batching

**Pattern:** Producing all output artifacts at the end instead of showing them at the step that produces them.

**Why it fails:** Prevents intermediate review, makes errors harder to catch, and creates a wall of output that's difficult to validate.

**Fix:** Show each artifact immediately after the step that produces it. Follow the timing hints in the output contract.

**Detection:** Agent reaches Step 7 without having shown any intermediate output.

### AP-D3: Tool assumption

**Pattern:** Assuming `skill-dl` or other tools are installed because the skill mentions them.

**Why it fails:** First command fails, requiring backtracking and context recovery. Often leads to the agent fabricating results instead of using fallback methods.

**Fix:** Run `skill-dl --version` before first use. Have the fallback chain ready: skill-dl > MCP tools > manual GitHub search.

**Detection:** A tool command fails with "command not found" during execution.

### AP-D4: Quality blindness

**Pattern:** Treating all downloaded skills as high-quality references regardless of their actual quality.

**Why it fails:** Produces comparison tables with only positive entries, missing the critical "avoid" patterns that inform synthesis decisions.

**Fix:** Apply the quality spectrum from `source-patterns.md`. Assign tiers. Document anti-patterns in the "avoid" column.

**Detection:** Comparison table has no "avoid" entries or all skills are rated positively.

### AP-D5: Path confusion

**Pattern:** Writing test instructions that assume creation when the task is revision (or vice versa).

**Why it fails:** For new skills, trigger tests silently pass because the skill isn't installed. For revisions, tests miss regression against the existing version.

**Fix:** Explicitly identify which path you're on. Follow the creation vs. revision testing paths in `testing-methodology.md`.

**Detection:** All trigger tests "pass" but the skill wasn't installed before testing.

### AP-D6: Research scope creep

**Pattern:** Downloading 20+ skills and reading all of them without a stopping criterion.

**Why it fails:** Consumes the entire research budget on discovery, leaving no time for deep comparison. Produces broad but shallow analysis.

**Fix:** Set a research budget before starting (see `research-workflow.md` phase gates). Stop when you have 3+ viable comparison entries.

**Detection:** More than 10 skills downloaded or more than 3 steps spent on research alone.

### AP-D7: Checklist as workflow

**Pattern:** Treating the master checklist as a sequential todo list, working through all 100+ items for every task.

**Why it fails:** Simple revisions take as long as full builds. Checklist fatigue leads to rubber-stamping later items.

**Fix:** Use phase markers: "DRAFT ESSENTIAL" items (Phases 0-3) for every task, "FINAL AUDIT ONLY" items (Phases 4+) only for comprehensive quality passes.

**Detection:** Running Phase 6+ checklist items before having a complete draft.
