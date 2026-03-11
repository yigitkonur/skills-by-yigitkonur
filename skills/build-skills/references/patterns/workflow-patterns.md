# Workflow Patterns

Five proven patterns for structuring skill instructions. Choose the pattern that matches your skill's primary workflow shape.

## Choosing your approach: problem-first vs. tool-first

Before picking a pattern, decide your framing:

- **Problem-first**: "I need to set up a project workspace." The skill orchestrates the right tool calls in the right sequence. Users describe outcomes; the skill handles the tools.
- **Tool-first**: "I have Linear MCP connected." The skill teaches Claude the optimal workflows and best practices. Users have tool access; the skill provides expertise.

Most skills lean one direction. Know which framing fits before choosing a pattern.

## Pattern 1: Sequential workflow orchestration

**Use when**: Users need multi-step processes in a specific order with dependencies between steps.

### Structure

```markdown
## Workflow: [Name]

### Step 1: [First action]
[What happens, what tool to call, what parameters]
Expected output: [describe success]

### Step 2: [Second action]
Requires: output from Step 1
[What happens, dependencies]

### Step 3: [Final action]
[Completion criteria]
```

### Key techniques

| Technique | Purpose |
|---|---|
| Explicit step ordering | Prevents out-of-order execution |
| Dependencies between steps | Ensures data flows correctly |
| Validation at each stage | Catches errors before they cascade |
| Rollback instructions | Recovers from mid-workflow failures |

### When to use

- Customer onboarding workflows
- Project setup sequences
- Build-test-deploy pipelines
- Any process with strict ordering requirements

### Example: customer onboarding

```markdown
### Step 1: Create Account
Call: `create_customer` with name, email, company
Validate: customer_id returned, no duplicate error

### Step 2: Setup Payment
Call: `setup_payment_method` with customer_id from Step 1
Wait for: payment method verification
Rollback: If payment fails, delete account from Step 1

### Step 3: Create Subscription
Call: `create_subscription` with plan_id, customer_id
Validate: subscription active, billing date set

### Step 4: Send Welcome
Call: `send_email` with welcome_template, customer_id
```

## Pattern 2: Multi-MCP coordination

**Use when**: Workflows span multiple services and data must flow between them.

### Structure

```markdown
## Workflow: [Cross-service name]

### Phase 1: [Source service] (via [MCP name])
1. Fetch/create in first service
2. Capture output data for next phase

### Phase 2: [Storage service] (via [MCP name])
1. Use output from Phase 1
2. Organize and store

### Phase 3: [Action service] (via [MCP name])
1. Create tasks/tickets using stored data
2. Link back to source

### Phase 4: [Notification service] (via [MCP name])
1. Notify stakeholders
2. Include links from all phases
```

### Key techniques

| Technique | Purpose |
|---|---|
| Clear phase separation | Each MCP call is isolated |
| Data passing between MCPs | Explicit about what flows where |
| Validation before phase transition | Prevents cascade failures |
| Centralized error handling | One recovery strategy |

### When to use

- Design-to-development handoffs (Figma → Drive → Linear → Slack)
- Content publishing pipelines (CMS → CDN → Social → Analytics)
- Cross-team workflows that touch multiple tools

## Pattern 3: Iterative refinement

**Use when**: Output quality improves with iteration and there are measurable quality criteria.

### Structure

```markdown
## Iterative [Output Type] Creation

### Initial Draft
1. Gather inputs
2. Generate first version
3. Save to temporary location

### Quality Check
1. Run validation: `scripts/check_output.py`
2. Identify issues:
   - [Quality dimension 1]
   - [Quality dimension 2]
   - [Quality dimension 3]

### Refinement Loop
1. Address each identified issue
2. Regenerate affected sections
3. Re-validate
4. Repeat until quality threshold met (max 3 iterations)

### Finalization
1. Apply final formatting
2. Generate summary
3. Save final version
```

### Key techniques

| Technique | Purpose |
|---|---|
| Explicit quality criteria | Defines what "good enough" means |
| Validation scripts | Deterministic checking where possible |
| Iteration cap | Prevents infinite loops (max 3 is typical) |
| Separate draft from final | Clean output path |

### When to use

- Report generation
- Code review and improvement
- Document formatting
- Any output where first draft is rarely final

## Pattern 4: Context-aware tool selection

**Use when**: The same goal requires different tools or approaches depending on the context.

### Structure

```markdown
## Smart [Action Name]

### Decision Tree
1. Assess context:
   - [Dimension 1]: value → approach A
   - [Dimension 2]: value → approach B
   - [Default]: approach C

### Execute Based on Decision
- **Approach A**: [steps with tool A]
- **Approach B**: [steps with tool B]
- **Approach C**: [fallback steps]

### Explain Decision
Tell the user why this approach was chosen.
```

### Key techniques

| Technique | Purpose |
|---|---|
| Clear decision criteria | Agent makes the right choice |
| Fallback options | Handles unexpected contexts |
| Transparency about choices | Users understand and trust the decision |
| Separation of routing from execution | Clean architecture |

### When to use

- File storage (cloud vs. local vs. version control)
- Communication routing (email vs. Slack vs. ticket)
- Data processing (batch vs. stream vs. real-time)
- Any scenario with multiple valid approaches

### Example: smart file storage

```markdown
### Decision Tree
1. Check file type and size:
   - Large files (>10MB) → cloud storage MCP
   - Collaborative docs → Notion/Docs MCP
   - Code files → GitHub MCP
   - Temporary files → local storage

### Execute
Based on decision, call the appropriate MCP tool,
apply service-specific metadata, and generate access link.

### Explain
Tell the user: "Stored in [location] because [reason]."
```

## Pattern 5: Domain-specific intelligence

**Use when**: The skill adds specialized knowledge beyond what the tools provide — compliance rules, best practices, industry standards.

### Structure

```markdown
## [Domain] Workflow with [Expertise]

### Pre-check ([Domain] Rules)
1. Gather relevant data
2. Apply domain rules:
   - [Rule 1]: check condition, document result
   - [Rule 2]: check condition, document result
3. Make go/no-go decision

### Execute (if pre-check passed)
1. Perform the action with domain constraints applied
2. Apply domain-specific validations during execution

### Audit Trail
1. Log all domain checks performed
2. Record decisions with rationale
3. Generate compliance/audit report
```

### Key techniques

| Technique | Purpose |
|---|---|
| Domain expertise embedded in logic | Goes beyond raw tool access |
| Pre-checks before action | Compliance before execution |
| Comprehensive documentation | Audit trail for governance |
| Clear governance model | Who decides, who approves |

### When to use

- Financial compliance (sanctions, risk assessment)
- Healthcare workflows (HIPAA considerations)
- Legal document review (clause analysis)
- Security audits (vulnerability assessment)
- Any domain where expertise matters more than tool access

## Pattern selection guide

| If your skill... | Use pattern |
|---|---|
| Has steps that must run in order | 1: Sequential |
| Coordinates multiple services | 2: Multi-MCP |
| Produces output that needs polishing | 3: Iterative refinement |
| Chooses between approaches based on context | 4: Context-aware |
| Embeds specialized knowledge | 5: Domain intelligence |
| Combines multiple patterns | Pick primary, reference secondary |

## Combining patterns

Complex skills often combine patterns. The key is to pick a primary pattern for the overall structure and embed secondary patterns within steps.

```
Primary: Sequential (overall workflow)
  Step 1: Context-aware (choose which service to use)
  Step 2: Domain intelligence (apply compliance rules)
  Step 3: Iterative refinement (polish the output)
  Step 4: Multi-MCP (distribute results across services)
```

Keep the primary pattern visible in SKILL.md. Move secondary pattern details to reference files.
