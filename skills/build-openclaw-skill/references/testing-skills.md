# Testing OpenClaw Skills

How to test a skill's triggering accuracy, functional correctness, and overall quality before deployment.

## Testing tiers

Choose the tier that matches your audience and quality requirements.

| Tier | Method | Setup | Best for |
|---|---|---|---|
| 1 | Manual testing in OpenClaw | None | Personal skills, rapid iteration |
| 2 | Scripted testing | Test script | Team skills, repeatable validation |
| 3 | Programmatic testing via API | Eval suite | Published skills, enterprise deployment |

Most skills should reach Tier 1. Published skills should reach Tier 2. High-visibility skills benefit from Tier 3.

## Prerequisites: install before runtime testing

Trigger tests fail silently if the skill is not installed in a watched directory. Before counting any runtime result, make sure you have:

1. A runnable OpenClaw runtime
2. Write access to either `<workspace>/skills/<name>/` or `~/.openclaw/skills/<name>/`
3. A way to confirm loaded skills via `openclaw status` or another runtime surface that lists them

Before testing, install the skill:

```bash
# For personal testing
mkdir -p ~/.openclaw/skills/my-skill-name/
cp SKILL.md ~/.openclaw/skills/my-skill-name/
if [ -d references ]; then cp -r references/ ~/.openclaw/skills/my-skill-name/; fi

# For workspace-specific testing
WORKSPACE_DIR=/path/to/workspace
mkdir -p "$WORKSPACE_DIR/skills/my-skill-name/"
cp SKILL.md "$WORKSPACE_DIR/skills/my-skill-name/"
if [ -d references ]; then cp -r references/ "$WORKSPACE_DIR/skills/my-skill-name/"; fi
```

Restart or reload the agent after installation. OpenClaw's skills watcher may auto-reload, but verify with `openclaw status` or another loaded-skill view before trusting any trigger or functional test result.

### If a real OpenClaw runtime is not available or not writable

Do not pretend the skill passed end-to-end testing. Switch to a dry-run validation pass if any of the three prerequisites above is missing:

1. Validate frontmatter and file structure
2. Run the routing/orphan check
3. Verify install paths and copy commands are correct
4. Write down which runtime checks remain blocked (load confirmation, trigger behavior, functional run)

Dry-run success means the package is structurally ready to install. It does not mean the runtime trigger behavior is proven.

### Minimal runtime verification recipe

Use this before broader testing, especially for tiny skills:

1. Install the skill into `<workspace>/skills/<name>/` or `~/.openclaw/skills/<name>/`
2. Reload or restart if the watcher does not pick it up
3. Confirm the skill appears in `openclaw status` or another loaded-skill view
4. Run one direct query that should trigger the skill
5. Verify one observable skill-specific result

For small skills, acceptable observable results include:
- a new `SKILL.md` or reference file created in the expected location
- metadata added or rewritten in the requested format
- the agent routing to the correct reference file and acting on it

If you cannot prove both "skill loaded" and "skill-specific result happened," do not count the run as runtime-verified.

## Test category 1: trigger tests

**Goal:** Ensure the skill loads for relevant queries and stays silent for unrelated ones.

### Building a trigger test suite

Create at least 10 queries for your skill:

- 5+ should-trigger queries total
- at least 3 paraphrased should-trigger variants
- 5+ should-NOT-trigger queries

Split them into these three lists:

**Should trigger (direct)** — obvious requests that clearly match:

```
- "Help me create an OpenClaw skill"
- "I need to write a SKILL.md file"
- "How do I publish to ClawHub?"
```

**Should trigger (paraphrased)** — same intent, different words:

```
- "Build a custom agent skill" (instead of "create an OpenClaw skill")
- "Set up a new skill directory" (instead of "write a SKILL.md file")
- "Share my skill with the community" (instead of "publish to ClawHub")
```

**Should NOT trigger** — unrelated or adjacent queries:

```
- "What's the weather?"
- "Help me write Python code"
- "How do I configure the OpenClaw runtime?" (runtime, not skill)
- "Build an MCP server" (different skill domain)
```

### Running trigger tests

1. Enable only your skill (disable others to avoid interference)
2. Run each query in a fresh conversation
3. Record whether the skill loaded (after confirming it is visible in the runtime) and whether the response followed the skill's specific workflow
4. Targets:
   - 90%+ of should-trigger queries activate the skill
   - 0% of should-NOT-trigger queries activate the skill

### Debugging trigger failures

**Skill never auto-triggers:**

Ask the agent: "When would you use the [skill-name] skill?"

The agent quotes the description back. Compare what it says with your intent. Gaps indicate missing trigger phrases.

| Signal | Likely cause | Fix |
|---|---|---|
| Skill never loads | Description too vague | Add specific trigger phrases |
| Users always use `/name` manually | Description missing natural language | Rewrite with user-natural phrases |
| Skill loads for wrong queries | Description too broad | Add negative triggers ("Do NOT use for...") |
| Inconsistent triggering | Trigger phrases overlap with another skill | Differentiate the descriptions |

## Test category 2: functional tests

**Goal:** Verify the skill produces correct outputs and handles edge cases.

### Test case template

```
Test: [name]
Given: [preconditions — project state, installed tools, env vars]
When: [user query or action]
Then:
  - [expected output 1]
  - [expected output 2]
  - [expected state change]
  - [no errors or specific error handling]
```

### What to test functionally

| Category | What to verify |
|---|---|
| Happy path | Primary workflow completes successfully |
| Decision tree | Each branch routes to the correct reference file |
| Reference loading | Referenced files exist and contain relevant content |
| Guardrails | Guardrail violations are caught and reported |
| Edge cases | Empty inputs, unusual project structures |
| Error paths | Missing requirements handled gracefully |

### Defining the primary workflow

Use the smallest non-trivial request from the skill's direct trigger set.

- Good: "Create a new OpenClaw skill called deploy-staging"
- Good: "Add metadata gating for node and API_KEY to this existing skill"
- Weak: "When would you use this skill?"

The primary workflow should exercise the skill's real output contract, not just describe the skill. For a tiny skill, "real output contract" still means a concrete artifact, mutation, or routing decision, not a descriptive answer.

### Example functional test

```
Test: Create new skill from scratch
Given: Empty directory, agent has write access
When: "Create a new OpenClaw skill called deploy-staging"
Then:
  - Directory deploy-staging/ created
  - SKILL.md has valid frontmatter with name: deploy-staging
  - Description follows the "Use skill if you are..." formula
  - Body contains decision tree or workflow sections
  - Body is under 500 lines
```

### Running functional tests

1. Set up the preconditions (project state, env vars, etc.)
2. Confirm the skill is loaded in the runtime (`openclaw status` or equivalent) before trusting the result
3. Invoke the skill with a representative query
4. Walk through the entire workflow end-to-end
5. Verify all output contract items are produced
6. Check that reference routing loads the correct files

If runtime installation is blocked, stop after the dry-run checks and record the missing runtime verification explicitly.

## Test category 3: quality metrics

**Goal:** Measure the skill's quality against quantitative targets.

### Metrics to track

| Metric | Target | How to measure |
|---|---|---|
| Trigger accuracy | 90%+ on relevant queries | Run 10+ test queries |
| False positive rate | 0% on unrelated queries | Run 10+ negative queries |
| Workflow completion | 100% without user correction | Run the primary workflow 3+ times |
| Token efficiency | SKILL.md under 500 lines | `wc -l SKILL.md` |
| Reference coverage | 0 orphaned files | Run routing verification script |
| Consistency | Same structure across runs | Compare 3+ outputs |

### The self-check test

Ask the agent: "When would you use the [skill-name] skill?"

The agent should describe the skill's purpose accurately. If the answer doesn't match your intent:

1. Check the description for missing trigger phrases
2. Check for vague or overly broad language
3. Add negative triggers if the scope is being misinterpreted

## The iterate-on-one principle

The most effective approach to skill testing:

1. Pick the hardest use case your skill should handle
2. Work with the agent interactively until the result is right
3. Extract what worked into the skill instructions
4. Then expand to multiple test cases for coverage

This leverages in-context learning and provides faster signal than broad testing.

## Testing checklist

Before declaring a skill tested:

- [ ] Skill is installed to the correct location, or runtime testing is explicitly marked blocked
- [ ] Runtime path is explicit: `<workspace>/skills/<name>/` or `~/.openclaw/skills/<name>/`, or runtime testing is explicitly marked blocked
- [ ] Skill load is confirmed in the runtime (`openclaw status` or equivalent), or runtime testing is explicitly marked blocked
- [ ] 5+ should-trigger queries tested (90%+ pass rate)
- [ ] 5+ should-NOT-trigger queries tested (0% false positive)
- [ ] 3+ paraphrased variants tested
- [ ] Agent correctly describes when to use the skill (self-check)
- [ ] Primary workflow completes without error (end-to-end), or runtime testing is explicitly marked blocked
- [ ] At least one edge case tested
- [ ] Routing verification shows 0 orphaned reference files
- [ ] SKILL.md is under 500 lines after any test-driven fixes
- [ ] Token consumption is reasonable for the task

## Post-testing iteration

### Undertriggering fixes

| Signal | Fix |
|---|---|
| Skill never loads automatically | Add more trigger phrases to description |
| Users always invoke manually | Description missing user-natural language |
| Support questions about when to use it | Description doesn't match user mental model |

### Overtriggering fixes

| Signal | Fix |
|---|---|
| Skill loads for unrelated queries | Add negative triggers ("Do NOT use for...") |
| Users disable the skill | Description too broad — narrow scope |
| Confusion with another skill | Differentiate descriptions between skills |

### Execution fixes

| Signal | Fix |
|---|---|
| Inconsistent results | Add more specific instructions, add examples |
| Wrong reference file loaded | Fix decision tree routing |
| User corrections needed | Improve step-by-step guidance in workflow |
| Missing content in references | Fill gaps in reference files |
