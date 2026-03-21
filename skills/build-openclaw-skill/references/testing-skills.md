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

## Prerequisites: install before testing

Trigger tests fail silently if the skill is not installed. Before testing, install the skill:

```bash
# For personal testing
mkdir -p ~/.openclaw/skills/my-skill-name/
cp SKILL.md ~/.openclaw/skills/my-skill-name/
cp -r references/ ~/.openclaw/skills/my-skill-name/

# For project-specific testing
mkdir -p project/skills/my-skill-name/
cp SKILL.md project/skills/my-skill-name/
cp -r references/ project/skills/my-skill-name/
```

Restart or reload the agent after installation. OpenClaw's skills watcher may auto-reload, but verify by checking that the skill appears in the available skills list.

## Test category 1: trigger tests

**Goal:** Ensure the skill loads for relevant queries and stays silent for unrelated ones.

### Building a trigger test suite

Create three lists for your skill:

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
3. Record whether the skill loaded (check for skill-specific behavior in the response)
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
2. Invoke the skill with a representative query
3. Walk through the entire workflow end-to-end
4. Verify all output contract items are produced
5. Check that reference routing loads the correct files

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

- [ ] Skill is installed to the correct location
- [ ] 5+ should-trigger queries tested (90%+ pass rate)
- [ ] 5+ should-NOT-trigger queries tested (0% false positive)
- [ ] 3+ paraphrased variants tested
- [ ] Agent correctly describes when to use the skill (self-check)
- [ ] Primary workflow completes without error (end-to-end)
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
