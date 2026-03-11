# Testing Methodology

How to test a skill before shipping, at the right level of rigor for your audience.

## Testing tiers

Choose the tier that matches your quality requirements and audience size.

| Tier | Method | Setup | Best for |
|---|---|---|---|
| 1 | Manual testing in Claude.ai | None | Personal skills, rapid iteration |
| 2 | Scripted testing in Claude Code | Test script | Team skills, repeatable validation |
| 3 | Programmatic testing via API | Eval suite | Published skills, enterprise deployment |

Most skills should reach Tier 1. Published skills should reach Tier 2. High-visibility skills benefit from Tier 3.

## The iterate-on-one principle

The most effective skill creators iterate on a single challenging task until Claude succeeds, then extract the winning approach into a skill. This leverages in-context learning and provides faster signal than broad testing.

1. Pick the hardest use case your skill should handle
2. Work with Claude interactively until the result is right
3. Extract what worked into the skill instructions
4. Then expand to multiple test cases for coverage

## Test category 1: Triggering tests

**Goal**: Ensure the skill loads at the right times and stays silent otherwise.

### Building a trigger test suite

For each skill, create three lists:

**Should trigger (obvious)** — direct requests that clearly match:
```
- "Help me set up a new ProjectHub workspace"
- "Create sprint tasks in Linear"
- "Build a React component with tests"
```

**Should trigger (paraphrased)** — same intent, different words:
```
- "I need to initialize a project" (instead of "set up")
- "Organize the next sprint" (instead of "create sprint tasks")
- "Generate a typed component" (instead of "build a React component")
```

**Should NOT trigger** — unrelated or adjacent queries:
```
- "What's the weather?"
- "Help me write Python code" (if skill is React-specific)
- "Create a spreadsheet" (if skill is project management)
```

### Running trigger tests

1. Enable only your skill (disable others to avoid interference)
2. Run each query and record whether the skill loaded
3. Target: 90%+ of should-trigger queries activate the skill
4. Target: 0% of should-NOT-trigger queries activate the skill

### Debugging trigger failures

Ask Claude directly:
```
"When would you use the [skill-name] skill?"
```

Claude quotes the description back. Compare what Claude says with what you intended. Adjust the description to close gaps.

## Test category 2: Functional tests

**Goal**: Verify the skill produces correct outputs and handles errors.

### Test case template

```
Test: [name]
Given: [preconditions — project state, available data, MCP connections]
When: [user query or action]
Then:
  - [expected output 1]
  - [expected output 2]
  - [expected state change]
  - [no errors or specific error handling]
```

### Example functional test

```
Test: Create project with 5 tasks
Given: ProjectHub MCP connected, user authenticated
When: "Create a Q4 planning project with 5 tasks"
Then:
  - Project created in ProjectHub with name "Q4 Planning"
  - 5 tasks created with correct properties
  - All tasks linked to project
  - No API errors in MCP logs
  - Confirmation message shown to user
```

### What to test functionally

| Category | Test |
|---|---|
| Happy path | Primary workflow completes successfully |
| Input variations | Different parameter combinations work |
| Error handling | Graceful failure on bad input |
| Edge cases | Empty inputs, large inputs, special characters |
| MCP failures | Skill handles connection/auth failures |
| Multi-step | Dependencies between steps resolve correctly |

## Test category 3: Performance comparison

**Goal**: Prove the skill improves results vs. no skill.

### Baseline comparison framework

Run the same task 3-5 times with and without the skill:

```
Without skill:
- User provides instructions each time
- N back-and-forth messages
- M failed API calls requiring retry
- X tokens consumed

With skill:
- Automatic workflow execution
- N' clarifying questions (should be fewer)
- M' failed API calls (should be zero)
- X' tokens consumed (should be lower)
```

### Metrics to track

| Metric | Target | How to measure |
|---|---|---|
| Trigger accuracy | 90%+ on relevant queries | Run 10-20 test queries |
| Tool call count | Lower than baseline | Count in conversation |
| Token consumption | Lower than baseline | Compare total tokens |
| API error rate | 0 per workflow | Monitor MCP server logs |
| User corrections | 0 per workflow | Count redirections needed |
| Consistency | Same structure across 3+ runs | Compare outputs |

## Defining success criteria

Before building, write down what success looks like. These are aspirational targets, not precise thresholds.

### Quantitative criteria

```
- Skill triggers on 90% of relevant queries
- Completes workflow in ≤N tool calls
- 0 failed API calls per workflow
- Token consumption ≤X per workflow
```

### Qualitative criteria

```
- Users don't need to prompt Claude about next steps
- Workflows complete without user correction
- Consistent results across sessions
- A new user can accomplish the task on first try
```

## Using skill-creator for review

The skill-creator skill (built into Claude.ai) can review your skill:

```
"Review this skill and suggest improvements"
```

It can flag:
- Vague descriptions
- Missing triggers
- Structural problems
- Over/under-triggering risks
- Missing test cases

It cannot run automated test suites or produce quantitative results.

## Iteration after testing

### Undertriggering fixes

| Signal | Fix |
|---|---|
| Skill never loads automatically | Add more trigger phrases to description |
| Users manually invoke with `/name` | Description missing user-natural language |
| Support questions about when to use it | Description doesn't match user mental model |

### Overtriggering fixes

| Signal | Fix |
|---|---|
| Skill loads for unrelated queries | Add negative triggers ("Do NOT use for...") |
| Users disable the skill | Description too broad — narrow scope |
| Confusion about purpose | Clarify scope in description |

### Execution fixes

| Signal | Fix |
|---|---|
| Inconsistent results | Add more specific instructions, add examples |
| API call failures | Add error handling, verify tool names |
| User corrections needed | Improve step-by-step guidance |

## Test checklist

Before shipping, verify all of the following:

- [ ] 5+ should-trigger queries tested
- [ ] 5+ should-NOT-trigger queries tested
- [ ] 3+ paraphrased variants tested
- [ ] Claude correctly describes when to use the skill
- [ ] Primary workflow completes without error
- [ ] Error handling works for at least one failure case
- [ ] Results are consistent across 3+ runs
- [ ] Token usage is reasonable for the task
