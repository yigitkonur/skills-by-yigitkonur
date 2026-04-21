# Testing Methodology

How to test a skill before shipping, at the right level of rigor for your audience.

## Contents
- [Before you test live triggers](#before-you-test-live-triggers) — identify runtime and install path first
- [Testing tiers](#testing-tiers) — choose the tier matching your audience
- [The iterate-on-one principle](#the-iterate-on-one-principle) — fastest signal: one hard case, worked to success
- [Defining success criteria](#defining-success-criteria) — what "done" looks like before you test
- [Using skill-creator for review](#using-skill-creator-for-review) — automated review tooling
- [Iteration after testing](#iteration-after-testing) — what to do when tests fail
- [Test checklist](#test-checklist) — final checklist before shipping
- [Creation vs. revision testing paths](#creation-vs-revision-testing-paths) — different steps for new vs. updated skills
- [Discipline-enforcing skills need the RED phase](#discipline-enforcing-skills-need-the-red-phase) — RED-GREEN-REFACTOR for rules agents can rationalize away

## Before you test live triggers

Identify the active runtime before you install or test anything. New and revised skills must be tested in the runtime that will actually load them.

- Use that runtime's skill directory, not a Claude-only default. Common personal-scope examples are `~/.claude/skills/[skill-name]/`, `~/.cursor/skills/[skill-name]/`, and `~/.codex/skills/[skill-name]/`. For project-scoped testing, use the runtime's project skill directory instead.
- If you are unsure which directories a runtime supports, check `references/authoring/skillmd-format.md` for the location table.
- If the current environment forbids writing to the installed skill directory, do manual trigger review plus a functional workflow test, state that live trigger coverage was blocked, and do not claim live trigger coverage.

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

**Execution method:** Open Claude.ai or Claude Code. Disable all skills except the one under test to avoid interference. Paste each query as a new conversation message. Observe whether the skill loaded (Claude.ai shows the skill name in the response header; Claude Code shows skill invocation in the output).

1. Enable only your skill (disable others to avoid interference)
2. Run each query in a fresh message and record whether the skill loaded
3. Target: 90%+ of should-trigger queries activate the skill
4. Target: 0% of should-NOT-trigger queries activate the skill

For scripted testing (Tier 2), write a test file with one query per line and run them sequentially in Claude Code, capturing output to verify skill activation.

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


---

## Creation vs. revision testing paths

Testing differs significantly between creating a new skill and revising an existing one. Use the appropriate path:

### Path A: Testing a NEW skill

**Setup required before testing:**
1. Determine the active runtime's skill directory.
2. Create the skill directory there, for example: `mkdir -p ~/.claude/skills/[skill-name]/`, `mkdir -p ~/.cursor/skills/[skill-name]/`, or `mkdir -p ~/.codex/skills/[skill-name]/`
3. Copy your draft `SKILL.md` into that directory.
4. Copy `references/` and any required `scripts/` or `assets/` into the same directory.
5. Restart or reload the runtime so it picks up the new skill.

**Trigger testing (new skill):**
- Open a fresh Claude conversation with only this skill enabled
- Paste each should-trigger query as a new message
- Record whether the skill actually loaded (check for skill-specific behavior)
- **Critical:** Trigger tests fail silently if the skill isn't installed. A "pass" with an uninstalled skill is a false positive.

**Functional testing (new skill):**
- Run the complete primary workflow end-to-end
- Verify all output contract items are produced
- Check that reference routing loads the correct files

### Path B: Testing a REVISION

**Setup:**
- Locate the currently installed copy in the active runtime
- Test against the current installed version first
- Then install the revision into that same runtime location and re-test

**Trigger testing (revision):**
- Run the same trigger queries against both old and new versions
- Verify the revision doesn't break existing triggers
- If scope changed, add new should-trigger and should-NOT-trigger queries

**Functional testing (revision):**
- Focus on the changed functionality
- Verify unchanged workflows still work
- Run at least one full end-to-end test

### Key distinction: installation before testing

New skills must be installed to the active runtime's skill directory before trigger testing. Without installation, trigger tests produce false positives — the skill appears to "pass" because the runtime never had the opportunity to load it. This is the most common source of silent test failures for new skills.

Revisions test against the currently installed version in that same runtime. The skill is already in place, so trigger testing works immediately.

### Common testing mistakes

| Mistake | Impact | Fix |
|---|---|---|
| Testing triggers without installing | False positives | Always install before trigger testing |
| Only testing the happy path | Misses edge cases | Include at least 2 edge cases |
| Testing only creation OR revision | Other path untested | Document which path you tested |
| No should-NOT-trigger queries | Over-triggering undetected | Always include 5+ negative queries |
| Skipping functional test | Workflow bugs ship | Run at least one end-to-end |
| Writing a discipline skill without RED baseline | Skill prevents failures you imagined, not the ones agents actually produce | Run pressure scenarios without the skill first — see `references/authoring/tdd-for-skills.md` |

---

## Discipline-enforcing skills need the RED phase

For skills that enforce a rule an agent can rationalize away (TDD, research-before-synthesis, verification requirements), trigger and functional tests are not enough. The skill can trigger correctly and still be bypassed under pressure.

Run the RED-GREEN-REFACTOR cycle before shipping:

1. **RED** — run a pressure scenario *without* the skill. Watch the agent fail. Capture its exact rationalizations verbatim.
2. **GREEN** — write the skill addressing those specific rationalizations. Re-run.
3. **REFACTOR** — any new rationalization that emerges? Add a counter. Re-test.

Full protocol, including scenario templates and the meta-test, is in `references/authoring/tdd-for-skills.md`.

### Pressure scenario template

```
IMPORTANT: This is a real scenario. Choose and act.

[Context with 3+ pressures: time, sunk cost, authority, exhaustion, consequence.]

Options:
A) [The disciplined choice]
B) [The expedient choice]
C) [A compromise]

Choose A, B, or C. Be honest.
```

Combine at least three pressure sources — single-pressure scenarios produce single-pressure data.

### Rationalization capture

When the agent violates the rule, record its exact words:

| Rationalization | Counter to add |
|---|---|
| "I already manually tested it" | State explicitly that manual testing is not a substitute, with the reason. |
| "Being pragmatic, not dogmatic" | State that following the rule *is* the pragmatic choice. Name the cost of the shortcut. |
| "I will add tests after" | State that "after" almost always means "never" and cite the specific failure mode. |

Add one row per excuse observed. Generic counters ("do not cheat") prevent nothing. Specific counters ("do not keep the file open while writing tests") prevent the specific failure.

### When a discipline skill is bulletproof

1. Agent picks the correct option under the maximum-pressure scenario.
2. Agent cites specific sections of the skill as justification.
3. Agent acknowledges the temptation but follows the rule anyway.
4. Meta-testing returns "skill was clear, I should follow it."
5. No new rationalizations emerge across multiple runs on different scenarios.
