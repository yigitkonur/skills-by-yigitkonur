# Tool Design Patterns

How to structure MCP tools so they map to user intent, minimize round-trips, and work across model sizes. These 8 patterns cover the full spectrum from single-tool consolidation to large-scale facade routing.

## Pattern 1: Design Around User Intent, Not API Endpoints

The most common MCP anti-pattern is wrapping each API endpoint as its own tool. This forces the model to orchestrate multi-step workflows that a human developer would automate.

**API-centric (bad):**
```
get_members()          -> list of member IDs
get_member_activity()  -> activity for one member
get_member_posts()     -> posts for one member
get_member_comments()  -> comments for one member
```
The model must call `get_members`, then loop through results calling 3 tools per member. This eats tokens, is error-prone, and takes 20+ tool calls.

**Intent-centric (good):**
```python
@tool(description="Get activity insights for all members in a space. Returns members sorted by engagement with their posts, comments, and last active date.")
def get_space_activity(space_id: str, days: int = 30, sort_by: str = "total_activity") -> dict:
    members = api.get_members(space_id)
    for m in members:
        m.activity = api.get_activity(m.id, days=days)
        m.posts = api.get_posts(m.id, days=days)
    return {
        "members": sorted(members, key=lambda m: m.activity.total, reverse=True),
        "summary": f"Found {len(members)} members active in the last {days} days.",
        "next_steps": "Use bulk_message(member_ids=[...]) to contact specific members."
    }
```

One tool call instead of 20+. The server does the orchestration internally because it knows the API better than the model ever will.

**The "Sable Principle"**: "When designing MCP capabilities, think about what actions the user would want to take, not what API endpoints exist. If the workflow involves Get Trending Tracks + 4 supporting calls - the 4 supporting calls should not be separate tools."

**When to consolidate:** If 3+ API calls always happen together for a common use case, they belong in one tool.

**Source:** [u/sjoti on r/mcp](https://reddit.com/r/mcp/comments/1lq69b3/) (279 upvotes); [u/glassBeadCheney on r/mcp](https://reddit.com/r/mcp)

---

## Pattern 2: Be a Smart Database, Not a Smart Analyst

Your MCP server should provide rich, structured data and let the LLM do the analysis. Don't try to be clever on the server side with keyword matching or opaque scoring algorithms.

**Wrong mental model: "Smart Analyst"**
```python
def analyze_threats(description: str):
    threats = []
    if "payment" in description:  # Brittle keyword matching
        threats.append("Payment fraud")
    if "user" in description:
        threats.append("Identity spoofing")
    return {"threats": threats[:5]}  # Artificial limit for "readability"
```

**Right mental model: "Smart Database"**
```python
def get_threat_framework(app_description: str):
    return {
        "stride_categories": {
            "spoofing": {
                "description": "Identity spoofing attacks",
                "traditional_threats": ["User impersonation", "Credential theft"],
                "ai_ml_threats": ["Deepfake attacks", "Prompt injection"],
                "mitigation_patterns": ["MFA", "Certificate-based auth"],
                "indicators": ["login", "auth", "session", "token", "identity"]
            },
            # ... all categories with COMPLETE data
        },
        "context_analysis": analyze_app_context(app_description),
        "report_template": "Use the above framework data to generate a threat report."
    }
```

**Key principles:**
1. **Information Provider, Not Analyzer** - Supply the framework, let the LLM apply it
2. **Completeness Over Convenience** - Return ALL data with metadata, not truncated slices
3. **Supply scaffolds, not conclusions** - Provide scoring criteria, not final scores
4. **Templates, not reports** - Return `report_template` + raw data, not a finished document

The LLM is better at semantic analysis than your keyword matcher. Your server is better at data retrieval and structured output than the LLM. Play to each side's strengths.

**Source:** [Matt Adams — MCP Server Design Principles](https://matt-adams.co.uk/2025/08/30/mcp-design-principles.html)

---

## Pattern 3: Consolidate Multi-Step Workflows Into Single Atomic Tools

When a common user task requires calling 4+ API endpoints in sequence, wrap the entire workflow into one tool. The agent doesn't need to know the internal steps.

**Before (4 separate tools):**
```python
create_project(name, repo)       # Tool 1
add_env_vars(pid, vars)          # Tool 2
create_deployment(pid, branch)   # Tool 3
add_domain(pid, domain)          # Tool 4
```

**After (1 workflow tool):**
```python
@tool(description="Deploy a new project end-to-end. Creates the project, configures environment variables, deploys from the specified branch, and sets up the custom domain.")
def deploy_project(
    repo_url: str,
    domain: str,
    env_vars: dict,
    branch: str = "main"
) -> dict:
    pid = create_project(repo_url)
    add_env_vars(pid, env_vars)
    deployment = create_deployment(pid, branch)
    add_domain(pid, domain)
    return {
        "status": "success",
        "project_id": pid,
        "deployment_url": deployment.url,
        "domain": domain,
        "message": f"Project deployed to {domain} from {branch} branch."
    }
```

**Benefits:**
- **Token savings**: One tool description vs four (3-4x reduction)
- **Fewer failure points**: Server handles the sequencing
- **Friendlier responses**: Return a conversational summary, not raw status codes
- **Simpler agent reasoning**: One decision instead of four

**When NOT to consolidate:**
- When steps are genuinely independent (user might want env vars without deployment)
- When individual steps need human confirmation between them
- When the workflow varies significantly between use cases

**Implementation tip:** Use try/except around each sub-step and return a structured error indicating which stage failed, so the model knows what was already completed.

**Source:** [Klavis AI — Less is More: MCP Design Patterns for AI Agents](https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents)

---

## Pattern 4: Use a Planner Tool to Teach the Model Your Workflow

For MCP servers with multiple tools that must be called in a specific order, create an explicit planner tool that returns the workflow as structured guidance.

```python
@tool(description="Get the recommended workflow plan for the current task. Call this FIRST before using any other visualization tools.")
def create_plan(task_description: str) -> dict:
    return {
        "workflow": [
            {"step": 1, "tool": "load_data", "description": "Load the dataset", "required_params": ["file_path"]},
            {"step": 2, "tool": "analyze_columns", "description": "Understand data types and distributions"},
            {"step": 3, "tool": "create_chart", "description": "Generate the visualization", "required_params": ["chart_type", "x_column", "y_column"]},
            {"step": 4, "tool": "export_dashboard", "description": "Export the final result"}
        ],
        "instructions": "Follow these steps in order. Each tool's response will provide specific guidance for the next step.",
        "important": "Do not skip steps. Step 2 output is required for step 3."
    }
```

**Why this works:** The model sees this tool first and now has a roadmap. Every subsequent tool response reinforces the workflow with further guidance about what comes next.

**Real-world example:** A data visualization MCP server (vizro-mcp by McKinsey) uses this exact pattern. The planner tool returns structured guidance, and every subsequent tool response contains next-step hints. The creator calls this "flattening the agent back into the model."

**Key detail:** Mark the planner tool's description with "Call this FIRST" or similar. The model treats this as a strong signal to invoke it before anything else.

**When to use:**
- Your server has 5+ tools that form a pipeline
- The order of operations matters
- New users (or models) can't intuit the correct sequence

**Source:** [u/Biggie_2018 on r/mcp](https://reddit.com/r/mcp) — McKinsey [vizro-mcp project](https://github.com/mckinsey/vizro); [u/sjoti on r/mcp](https://reddit.com/r/mcp/comments/1lq69b3/)

---

## Pattern 5: Expose a Code Execution Sandbox for Batch Operations

For data-heavy tasks (batch processing, pagination, custom analytics), expose a single `execute_code` tool that runs LLM-generated Python in a sandbox. This is dramatically more token-efficient than dozens of individual tool calls.

```json
{
  "name": "execute_code",
  "description": "Run Python code in a secure sandbox with access to pre-authenticated API clients (salesforce_client, s3_client). Use for batch operations, data processing, or any task requiring loops/parallelism.",
  "input_schema": {
    "type": "object",
    "properties": {
      "code": {"type": "string", "description": "Python code to execute."},
      "timeout": {"type": "integer", "default": 300, "description": "Execution timeout in seconds."}
    },
    "required": ["code"]
  }
}
```

**Example LLM-generated code:**
```python
from concurrent.futures import ThreadPoolExecutor
import json

def fetch_page(p):
    return salesforce_client.fetch_leads(page=p, limit=1000)

first = fetch_page(1)
total_pages = (first['total_count'] + 999) // 1000

all_leads = []
with ThreadPoolExecutor(max_workers=10) as exe:
    for f in exe.map(fetch_page, range(1, total_pages + 1)):
        all_leads.extend(f['leads'])

s3_url = s3_client.upload(
    data=json.dumps(all_leads),
    filename=f"leads_{len(all_leads)}.json"
)
return {"status": "success", "total": len(all_leads), "s3_url": s3_url}
```

**Security requirements (non-negotiable):**
- Run in isolated containers with `--no-new-privileges`
- Drop all capabilities, mount read-only filesystem
- Enforce CPU/memory limits via cgroups
- Restrict network egress to whitelisted endpoints
- Provide API clients pre-authenticated - never expose raw keys
- Disallow `eval`/`exec` on untrusted strings
- Set hard timeout limits

**When to use:** Batch exports, heavy pagination, custom analytics, file transformations - anywhere the final output is a file/URL rather than a conversational response.

**Source:** [Klavis AI — Less is More: MCP Design Patterns for AI Agents](https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents)

---

## Pattern 6: Design Tool Workflows for 3-5 Calls, Not 20+

Frontier models handle 20+ sequential tool calls, but smaller and open-source models degrade after 5-7 — they forget earlier results, hallucinate parameters, or loop. If your MCP server requires 15 tool calls to complete a common task, you've locked yourself into expensive frontier models.

Design tools so that the most common user goals complete in 3-5 calls. This doesn't mean fewer tools — it means each tool does more meaningful work per invocation.

**Before: 12+ calls to analyze a repo**
```python
list_repos()              # Call 1
get_repo(id)              # Call 2
list_branches(repo_id)    # Call 3
get_branch(repo_id, "main")  # Call 4
list_commits(branch_id)   # Call 5-6 (pagination)
get_commit(commit_id)     # Call 7-12 (per commit)
```

**After: 2 calls**
```python
@tool(description="Get recent activity summary for a repository. Returns latest commits, active branches, and contributor stats for the specified time range.")
def get_repo_activity(
    repo: str,
    days: int = 7,
    max_commits: int = 20
) -> dict:
    repo_info = api.get_repo(repo)
    branches = api.list_branches(repo)
    commits = api.list_commits(repo, since=days_ago(days), limit=max_commits)
    return {
        "repo": repo_info.name,
        "default_branch": repo_info.default_branch,
        "active_branches": [b.name for b in branches if b.updated_recently(days)],
        "recent_commits": [{"sha": c.sha[:8], "message": c.message, "author": c.author} for c in commits],
        "summary": f"{len(commits)} commits across {len(branches)} branches in the last {days} days."
    }
```

Designing for 3-5 calls means your MCP server works with GPT-4o-mini, Haiku, Gemma, and every future small model — not just Claude Opus. It also cuts latency and token costs by 4-10x.

**Source:** [u/sjoti on r/mcp](https://reddit.com/r/mcp/comments/1lq69b3/) — "Design things in a way that tasks only take 3-5 tool calls instead of 20+"

---

## Pattern 7: CRUD — Combined Tool vs Separate Tools Decision

When you have multiple entity types each needing create/read/update/delete, you face a design choice. The right answer depends on your tool count and approval requirements.

**Combine when:** you have many entity types (users, projects, teams, billing). Four CRUD operations x 8 entities = 32 tools. Most models degrade with 20+ tools in the prompt. Combining gives you 8 tools instead of 32.

**Keep separate when:** you have few entity types (3 or fewer), you need per-operation user approval (e.g., reads are auto-approved but deletes require confirmation), or your tools have very different parameter shapes per operation.

**Combined pattern:**
```python
@tool(description="Manage users. Actions: 'list' (filter by role/status), 'get' (by user_id), 'create' (name+email required), 'update' (user_id + fields to change), 'delete' (by user_id, irreversible).")
def manage_user(
    action: Literal["list", "get", "create", "update", "delete"],
    user_id: str | None = None,
    filters: dict | None = None,
    data: dict | None = None
) -> dict:
    match action:
        case "list":
            return {"users": db.users.find(filters or {})}
        case "get":
            return {"user": db.users.find_one(user_id)}
        case "create":
            return {"user": db.users.insert(data), "status": "created"}
        case "update":
            db.users.update(user_id, data)
            return {"user": db.users.find_one(user_id), "status": "updated"}
        case "delete":
            db.users.delete(user_id)
            return {"status": "deleted", "user_id": user_id}
```

**Decision matrix:**

| Factor | Combine | Separate |
|---|---|---|
| Entity types | >3 | 3 or fewer |
| Total tool count | Approaching 20+ | Under 15 |
| Approval granularity | Same for all ops | Different per operation |
| Parameter overlap | High | Low |

Tool count directly impacts model accuracy. With 30+ tools, models frequently pick the wrong tool or hallucinate parameters.

**Source:** [r/mcp](https://reddit.com/r/mcp) community consensus; [Klavis AI — Less is More: MCP Design Patterns for AI Agents](https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents)

---

## Pattern 8: The Toolhost/Facade Pattern for Many Related Operations

When your MCP server exposes 20+ closely related operations, you hit the tool count ceiling. The Toolhost pattern solves this: one dispatcher tool that routes to internal handlers via an `operation` parameter. This is the Gang of Four Facade pattern applied to MCP.

Instead of polluting the tool list with dozens of entries, you expose a single entry point. The model picks the operation from a well-documented enum, and the server dispatches internally. Shared logic (auth, logging, error handling) lives in the facade.

```python
OPERATIONS = {
    "list_users":    {"handler": list_users,    "args": ["filters", "page"]},
    "get_user":      {"handler": get_user,      "args": ["user_id"]},
    "create_user":   {"handler": create_user,   "args": ["name", "email", "role"]},
    "list_projects": {"handler": list_projects,  "args": ["owner_id", "status"]},
    "get_project":   {"handler": get_project,    "args": ["project_id"]},
    "export_data":   {"handler": export_data,    "args": ["entity", "format"]},
}

@tool(description=f"Admin API gateway. Operations: {', '.join(OPERATIONS.keys())}. Pass the operation name and its arguments.")
def admin_toolhost(
    operation: str,
    args: dict = {}
) -> dict:
    if operation not in OPERATIONS:
        return {"error": f"Unknown operation. Available: {list(OPERATIONS.keys())}"}

    op = OPERATIONS[operation]
    missing = [a for a in op["args"] if a not in args and a not in OPTIONAL_ARGS]
    if missing:
        return {"error": f"Missing required args for {operation}: {missing}"}

    try:
        result = op["handler"](**args)
        return {"operation": operation, "status": "success", "result": result}
    except Exception as e:
        return {"operation": operation, "status": "error", "error": str(e)}
```

**When to use:**
- 20+ operations that share common auth/validation/error-handling code
- Operations are closely related (same domain, same API backend)
- You want a single place to add logging, rate limiting, or retry logic

**When to avoid:**
- Fewer than 5 operations — the indirection adds complexity for no benefit
- Operations need individual user-approval flows (the facade hides which operation runs)
- Operations have radically different parameter shapes that don't fit a generic `args` dict

The Toolhost pattern lets you scale to 50+ operations without hitting model confusion limits. The tradeoff is discoverability — the model must know which operations exist, so your description string must be comprehensive.

**Source:** [glassBead — Design Patterns in MCP: Toolhost Pattern](https://glassbead-tc.medium.com/design-patterns-in-mcp-toolhost-pattern-59e887885df3); [u/glassBeadCheney on r/mcp](https://reddit.com/r/mcp)
