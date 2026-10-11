# Skills over MCP (SEP-2640)

*Authoritative guide for serving reusable agent skills from mcp-use v2 servers and aligning with official skills conventions.*

Official documentation:
- [Skills over MCP](https://docs.mcp-use.com/v2/typescript/server/skills)

---

## 1. What are Skills over MCP?

Skills over MCP (standard extension proposal SEP-2640) enables an MCP server to distribute reusable operating workflows, domain knowledge, and step-by-step procedures directly alongside its tools. Prefer a Skill when a task requires a multi-step sequence, domain policies, output templates, or verification scripts that would otherwise overwhelm tool descriptions.

### Core Architectural Separation
Do not substitute executable capabilities with static prose:
- **Tools**: Perform atomic actions and mutations.
- **Resources**: Expose discoverable, read-only content and schemas.
- **Prompts**: Return model-ready message templates.
- **Skills**: Teach agents how to orchestrate tools, read resources, and apply business policies safely.

---

## 2. Directory Convention & File Layout

Place skills in the conventional `skills/` directory at the project root beside your server entry:

```text
my-mcp-server/
├── skills/
│   ├── process-refund/
│   │   ├── SKILL.md              # Skill instructions and YAML frontmatter
│   │   ├── references/           # Detailed policies and reference manuals
│   │   │   └── policy.md
│   │   ├── scripts/              # Deterministic validation or utility scripts
│   │   │   └── verify-limits.ts
│   │   └── templates/            # Structured confirmation/output templates
│   │       └── confirmation.md
│   └── issue-invoice/
│       └── SKILL.md
├── src/
│   └── index.ts
├── views/
├── package.json
└── tsconfig.json
```

### Skill Manifest & Frontmatter (`SKILL.md`)
Every skill requires a `SKILL.md` entrypoint with valid YAML frontmatter containing `name` and `description`:

```markdown
---
name: process-refund
description: Check refund eligibility against return policies and process approved customer refunds
---

# Process Refunds

Follow this procedure when a user requests a refund or return:
1. Verify customer order status using the `get_order` tool.
2. Read `references/policy.md` to evaluate return window and condition eligibility.
3. If approved, call `execute_refund` with the verified amount and reason.
4. Render confirmation using `templates/confirmation.md`.
```

> [!TIP]
> Keep `SKILL.md` lean, focused, and procedural. Delegate deep policies to `references/`, deterministic computation to `scripts/`, and output formats to `templates/`.

---

## 3. Server Configuration & Capability Advertising

The presence of a `skills/` directory at the project root automatically enables the Skills over MCP extension. You can also configure it explicitly in `MCPServer`:

```typescript
import { MCPServer } from "mcp-use";

// 1. Automatic discovery (default when skills/ exists)
const server = new MCPServer({
  name: "shop-server",
  version: "1.0.0",
  skills: true, // scans default skills/ directory
});

// 2. Explicit custom directory path
const customServer = new MCPServer({
  name: "shop-server",
  version: "1.0.0",
  skills: { directory: "custom-skills" },
});

// 3. Disable skills discovery
const headlessServer = new MCPServer({
  name: "shop-server",
  version: "1.0.0",
  skills: false,
});
```

---

## 4. Build-Time vs Development-Time Validation

`mcp-use` enforces strict validation to ensure skill packages conform to SEP-2640:
- **`mcp-use build` (Strict Build-Time Validation)**:
  During production builds, the compiler performs strict structural and frontmatter validation across all skill directories. If any skill directory is malformed, lacks a `SKILL.md`, or has invalid YAML frontmatter, `mcp-use build` **fails immediately with a non-zero exit code**. This prevents corrupt or incomplete skills from deploying to production environments or cloud registries.
- **`mcp-use dev` (Permissive Development-Time Validation)**:
  During local development, invalid skills emit a descriptive warning in the console and are skipped from registration without crashing the development server, allowing uninterrupted drafting and iteration.

---

## 5. Protocol Surface & Wire Contracts (SEP-2640)

The server advertises the official extension identifier in its server capabilities:
```json
{
  "capabilities": {
    "io.modelcontextprotocol/skills": {}
  }
}
```

The extension exposes two standard JSON-RPC protocol endpoints:

### 1. `skills/list`
Discovers all available skills registered on the server.
- **Request**: `{}`
- **Response**:
  ```json
  {
    "skills": [
      {
        "name": "process-refund",
        "description": "Check refund eligibility and process approved customer refunds"
      }
    ]
  }
  ```

### 2. `skills/get`
Retrieves the full instructions, manifest, and referenced files for a specific skill.
- **Request**: `{ "name": "process-refund" }`
- **Response**:
  ```json
  {
    "skill": {
      "name": "process-refund",
      "description": "Check refund eligibility and process approved customer refunds",
      "content": "# Process Refunds\n\n1. Verify customer order...",
      "files": [
        {
          "path": "references/policy.md",
          "content": "# Refund Policy\n\nRefunds must be requested within 30 days..."
        },
        {
          "path": "templates/confirmation.md",
          "content": "Refund ID: {{refundId}}\nAmount: {{amount}}"
        }
      ]
    }
  }
  ```

---

## 6. Architectural Conventions from the 4 Official Skills

The four official skills maintained by the `mcp-use` core team (`chatgpt-app-builder`, `mcp-apps-builder`, `mcp-builder`, `openapi-to-mcp`) codify key architectural invariants that every server author should emulate:

| Official Skill | Primary Focus | Key Architectural Invariant Codified |
|---|---|---|
| `chatgpt-app-builder` | End-to-end MCP Servers & ChatGPT Apps | Treat installed package declarations (`mcp-env.d.ts`) as authoritative ground truth. Never invent configuration fields. |
| `mcp-apps-builder` | Interactive React Views & Generative UI | Strict 1:1 view-to-tool binding. Clear separation between model-visible state (`structuredContent`, `useViewState`, `<ModelContext>`) and view-only metadata (`_meta`). |
| `mcp-builder` | Server infrastructure, tools, resources, prompts | Standard Schema validation for inputs/outputs, stateless request lifecycle, and Streamable HTTP transport over stdio. |
| `openapi-to-mcp` | Wrapping OpenAPI 3.x specifications | *"The spec is the contract"*: Tool names, descriptions, and parameter schemas must be derived mechanically from the OpenAPI specification, never invented. |

### Core Architectural Principles
1. **"The Spec is the Contract"**: Ground all tool inputs, outputs, and descriptions directly in unambiguous schemas (`zod` or Standard Schema). The language model relies on accurate descriptions to plan invocations.
2. **Raw Protocol Envelopes**: Always return raw protocol envelopes (`CallToolResult`, `structuredContent`, `_meta`) rather than deprecated v1 response helpers (`text()`, `object()`).
3. **Strict 1:1 View Binding**: Each view directory in `views/` belongs to at most one tool. Additional operations must be viewless tools invoked via `useCallTool` or client-side tools via `useViewTool`.
4. **Streamable HTTP Transport**: All production servers must run on streamable HTTP (`server.listen(port)`) at endpoint `/mcp`. Stdio transport cannot connect to Inspector, cannot deploy to cloud infrastructure, and cannot render interactive views in ChatGPT or Claude.
5. **Two-Layer Verification**:
   - **Layer 1 (Protocol Mechanics)**: Verify tools, resources, prompts, and skills directly via CLI (`mcp-use client <name> tools call ...`, `skills list`).
   - **Layer 2 (Model Interaction)**: Verify end-to-end LLM comprehension, tool planning, and view rendering in Inspector Chat (`mcp-use dev`).
