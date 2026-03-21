# Lobster Workflow Patterns

Lobster is a typed workflow runtime provided as an OpenClaw plugin. It enables multi-step processes with structured execution, resumable approvals, and typed data flow between steps.

## Enabling Lobster

Lobster is a plugin-provided tool. It must be explicitly allowed in your OpenClaw configuration.

**CRITICAL:** Use `tools.alsoAllow`, not `tools.allow`. Using `tools.allow` creates a restrictive allowlist that blocks all tools not listed. `tools.alsoAllow` adds Lobster alongside the defaults.

```yaml
# CORRECT -- adds Lobster without restricting other tools
tools:
  alsoAllow:
    - "lobster"

# WRONG -- restricts ALL tools to only Lobster
# tools:
#   allow:
#     - "lobster"
```

## Tool API: lobster

The `lobster` tool accepts two actions: `run` and `resume`.

### run action

Executes a Lobster workflow pipeline.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action` | string | Yes | - | Must be `"run"` |
| `pipeline` | string | Yes | - | Path to the `.lobster` workflow file |
| `cwd` | string | No | - | Working directory for the workflow execution |
| `timeoutMs` | int | No | 20000 | Maximum execution time in milliseconds |
| `maxStdoutBytes` | int | No | 512000 | Maximum stdout capture size in bytes |
| `argsJson` | string | No | - | JSON string of arguments passed to workflow `args` |

Example call:

```json
{
  "action": "run",
  "pipeline": "./workflows/daily-report.lobster",
  "cwd": "/opt/openclaw/workflows",
  "timeoutMs": 60000,
  "argsJson": "{\"target\": \"production\", \"verbose\": true}"
}
```

### resume action

Continues a paused workflow after an approval gate.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action` | string | Yes | - | Must be `"resume"` |
| `token` | string | Yes | - | The `resumeToken` from the approval request |
| `approve` | boolean | Yes | - | `true` to approve, `false` to reject |

Example call:

```json
{
  "action": "resume",
  "token": "abc123-resume-token",
  "approve": true
}
```

### Output envelope

Every Lobster call returns an envelope with this shape:

```json
{
  "ok": true,
  "status": "ok",
  "output": [
    { "stepId": "gather-data", "stdout": "...", "stderr": "" },
    { "stepId": "analyze", "stdout": "...", "stderr": "" }
  ]
}
```

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `ok` | boolean | `true` / `false` | Whether the workflow completed without error |
| `status` | string | `"ok"`, `"needs_approval"`, `"cancelled"` | Workflow outcome |
| `output` | array | - | Array of step outputs (when `status` is `"ok"`) |
| `requiresApproval` | object | - | Present only when `status` is `"needs_approval"` |

When `status` is `"needs_approval"`, the envelope includes:

```json
{
  "ok": true,
  "status": "needs_approval",
  "requiresApproval": {
    "type": "approval_request",
    "prompt": "Deploy to production?",
    "items": [
      { "description": "Deploy artifact v2.3.1 to prod cluster" }
    ],
    "resumeToken": "abc123-resume-token"
  }
}
```

Use the `resumeToken` with the `resume` action to continue or reject the workflow.

## Workflow file format (.lobster)

Lobster workflows are defined in `.lobster` files with this schema:

```yaml
name: daily-report
args:
  target:
    type: string
    default: "staging"
  verbose:
    type: boolean
    default: false
env:
  DATABASE_URL: "${DATABASE_URL}"
  REPORT_DIR: "/opt/reports"
steps:
  - id: gather-data
    command: "psql $DATABASE_URL -c 'SELECT * FROM metrics' --csv"

  - id: analyze
    command: "python3 analyze.py"
    stdin: "$gather-data.stdout"

  - id: deploy-report
    command: "scp report.csv user@server:/reports/"
    stdin: "$analyze.stdout"
    approval: "required"
    condition: "$analyze.stdout"
    when: "$analyze.approved"
```

### Workflow file fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Workflow identifier |
| `args` | object | No | Key-value argument definitions with defaults |
| `env` | object | No | Environment variables for all steps |
| `steps` | array | Yes | Ordered list of step definitions |

### Step fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique step identifier (used in `$stepId.stdout` references) |
| `command` | string | Yes | Shell command to execute |
| `stdin` | string | No | Pipe previous step output, e.g. `$gather-data.stdout` |
| `approval` | string | No | `"required"` or `"optional"` -- pauses for human approval |
| `condition` | string | No | Expression that must be truthy for step to run |
| `when` | string | No | Conditional like `$stepId.approved` -- runs only when referenced step was approved |

### Data flow between steps

Use `$stepId.stdout` to pipe one step's output into another:

```yaml
steps:
  - id: fetch
    command: "curl -s https://api.example.com/data"

  - id: transform
    command: "jq '.items[] | {name, value}'"
    stdin: "$fetch.stdout"

  - id: store
    command: "tee /data/output.json"
    stdin: "$transform.stdout"
```

### Approval gates

Place approval gates before steps that are destructive, costly, or irreversible:

```yaml
steps:
  - id: plan
    command: "terraform plan -out=tfplan"

  - id: apply
    command: "terraform apply tfplan"
    approval: "required"
    when: "$plan.approved"
```

When a step has `approval: "required"`:
1. Execution pauses
2. The Lobster output envelope returns `status: "needs_approval"` with a `resumeToken`
3. A human reviews and calls `resume` with `approve: true` or `approve: false`
4. On approval, execution continues from that step
5. On rejection, the workflow terminates with `status: "cancelled"`

## Error handling

Lobster produces specific error messages for common failures:

| Error | Cause | Fix |
|-------|-------|-----|
| `lobster subprocess timed out` | Step exceeded `timeoutMs` | Increase `timeoutMs` or optimize the command |
| `lobster output exceeded maxStdoutBytes` | Step produced too much output | Increase `maxStdoutBytes` or reduce output (e.g., add `| head`) |
| `lobster returned invalid JSON` | Internal parse error | Check that the `.lobster` file is valid YAML |
| `lobster failed (code N)` | Step command exited with non-zero code | Check the command and stderr output |

## llm-task plugin

LLM Task is a complementary plugin often used within Lobster workflows for AI reasoning steps.

### Enabling llm-task

```yaml
plugins:
  entries:
    llm-task:
      enabled: true
```

### llm-task schema

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Instruction for the LLM |
| `thinking` | string | No | Reasoning depth: `"low"`, `"medium"`, or `"high"` |
| `input` | object | No | Structured data passed as context to the prompt |
| `schema` | JSON Schema | No | Output schema enforcing structured JSON response |

The `schema` field uses standard JSON Schema:

```json
{
  "prompt": "Classify this support ticket by urgency and category.",
  "thinking": "medium",
  "input": {
    "ticket_text": "My production database is down and customers cannot log in.",
    "ticket_id": "TICK-4521"
  },
  "schema": {
    "type": "object",
    "properties": {
      "urgency": { "type": "string", "enum": ["critical", "high", "medium", "low"] },
      "category": { "type": "string", "enum": ["infrastructure", "billing", "feature", "bug"] },
      "summary": { "type": "string" }
    },
    "required": ["urgency", "category", "summary"],
    "additionalProperties": false
  }
}
```

## When to use Lobster

Use Lobster when:

- The task has 3+ steps that must execute in a defined order
- Steps produce structured data that feeds into subsequent steps
- Destructive or expensive actions need human approval before proceeding
- The workflow may need to be paused, inspected, and resumed later
- You need an audit trail of what happened at each step

Do NOT use Lobster when:

- A single exec call or LLM Task accomplishes the goal
- The task is a one-off command with no data flow between steps
- The workflow is purely browser automation (use the browser tool directly)

## Combining Lobster with other tools

### Lobster + cron

Use cron to trigger a Lobster workflow on a schedule. The cron job starts the workflow; Lobster handles the typed execution.

**Warning:** If the Lobster workflow includes approval gates, the cron-triggered instance will pause at the gate and wait for human approval. Design cron-triggered workflows to either skip approval (for trusted automated actions) or alert the human that approval is needed.

### Lobster + LLM Task

Use LLM Task as a reasoning step within a Lobster workflow. The Lobster step defines the data flow; LLM Task provides structured AI analysis.

### Lobster + exec

Lobster steps execute shell commands by design. Wrapping exec in Lobster provides audit trails, typed data flow, and approval gates that raw exec lacks.

### Lobster + browser

Each browser interaction (navigate, extract, screenshot) can be one Lobster step. This gives typed data between browser actions and approval gates before sensitive operations.

## Debugging workflows

When a workflow fails or produces unexpected results:

1. **Check the output envelope** -- look at `ok`, `status`, and individual step outputs
2. **Check the failing step's stderr** -- the `output` array includes stderr per step
3. **Check approval state** -- a workflow may be paused at a gate, not failed
4. **Check timeoutMs** -- increase if steps legitimately take longer than 20 seconds
5. **Check maxStdoutBytes** -- increase if steps produce large output
6. **Run the failing step in isolation** -- test the command independently
7. **Check plugin availability** -- verify Lobster is loaded with `tools.alsoAllow`

## Safety considerations

- Always use approval gates before destructive or irreversible actions
- Log workflow execution for audit purposes
- Set appropriate `timeoutMs` on workflows to prevent hanging
- Handle step failures gracefully -- a workflow should not leave external systems in an inconsistent state
- When a workflow is rejected at an approval gate, clean up any resources created by earlier steps
- Never include secrets in `.lobster` files -- use `env` references to environment variables
