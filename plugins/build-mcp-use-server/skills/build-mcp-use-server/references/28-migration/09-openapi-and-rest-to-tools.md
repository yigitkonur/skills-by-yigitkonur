# Migrating REST APIs & OpenAPI Specifications to mcp-use v2

*Read this when migrating REST API endpoints, Swagger/OpenAPI specifications, or manual HTTP fetch wrappers to mcp-use v2 tools.*

Migrating existing REST APIs and OpenAPI specifications to `mcp-use v2` transforms traditional HTTP endpoints into AI-accessible semantic tools. Instead of forcing an LLM to navigate dozens of raw HTTP routes, URL query strings, and unstructured JSON payloads, `mcp-use v2` provides two first-class migration paths:
1. **Automated declarative ingestion** via `MCPServer.fromOpenAPI()` for rapid spec bootstrapping.
2. **Curated route forwarding** via `server.tool()` for production workflows requiring downstream authentication pass-through, payload pruning, and multi-endpoint orchestration.

---

## At a Glance: REST & OpenAPI Migration Diff

| Capability / Pattern | Legacy REST Integration | Canonical mcp-use v2 Architecture | Impact / Action |
|---|---|---|---|
| **API Ingestion** | Hand-rolled Express/Fastify routes or ad-hoc `fetch()` scripts | `MCPServer.fromOpenAPI({ spec, baseUrl, ... })` | Instant generation of validated MCP tools from OpenAPI 3.0/3.1 specs |
| **Tool Definition** | Manual route registration with string URL path parsing | Declarative `server.tool({ inputSchema, outputSchema }, handler)` | Schema-checked inputs and outputs validated via Standard Schema (Zod v4) |
| **Schema Derivation** | Loose TypeScript interfaces or manual runtime type guards | Automatic JSON Schema translation from OpenAPI parameters & bodies | Automatic validation before tool execution; zero manual parsing boilerplate |
| **Authentication Forwarding** | Static service tokens in process env or manual header injection | Dynamic caller token pass-through via `ctx.auth.token` or provider adapters | End-to-end user identity propagation to upstream REST APIs |
| **Error Containment** | Unhandled HTTP 4xx/5xx responses crashing handlers or leaking stack traces | Spec-compliant `{ isError: true, content: [...] }` envelopes | Contain upstream network/HTTP failures gracefully within LLM context |
| **Response Curation** | Dumping massive raw REST JSON objects into model prompts | Curated `structuredContent` and payload pruning to critical fields | Eliminates prompt token exhaustion and hallucination from noisy API fields |
| **Workflow Composition** | Client makes 5–10 round-trip HTTP requests to complete one task | Composite `server.tool()` executing multi-step REST sequences server-side | Drastically cuts model latency and reasoning complexity |

---

## Migration Paths: When to Use `fromOpenAPI` vs. Hand-Crafted `server.tool`

Before migrating, choose the appropriate migration strategy based on your API's scope and consumption model:

```
                  ┌────────────────────────────────────────┐
                  │ Do you have an OpenAPI 3.0/3.1 spec?   │
                  └───────────────────┬────────────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │ YES                     │ NO
                         ▼                         ▼
        ┌────────────────────────────────┐   ┌─────────────────────────────┐
        │ Is it an internal prototype,   │   │ Write curated server.tool() │
        │ small API, or quick bootstrap? │   │ wrapping fetch() calls with │
        └────────────────┬───────────────┘   │ Zod input/output schemas    │
                         │                   └─────────────────────────────┘
                ┌────────┴────────┐
                │ YES             │ NO (Production, multi-step, or custom auth)
                ▼                 ▼
   ┌─────────────────────────┐   ┌─────────────────────────────────────────┐
   │ Use MCPServer.          │   │ Hand-craft curated server.tool()        │
   │ fromOpenAPI({ spec })   │   │ forwarding to REST endpoints with:      │
   │ with tags/exclude rules │   │ - ctx.auth.token pass-through           │
   └─────────────────────────┘   │ - Response field filtering / pruning   │
                                 │ - Multi-call aggregation                │
                                 └─────────────────────────────────────────┘
```

---

## Pattern 1: Declarative Ingestion with `MCPServer.fromOpenAPI()`

`MCPServer.fromOpenAPI()` automatically maps paths, query parameters, request bodies, and operation summaries from an OpenAPI 3.0 or 3.1 document into registered MCP tools.

### Key Options (`FromOpenAPIOptions`)

```typescript
import { MCPServer } from "mcp-use";

const server = MCPServer.fromOpenAPI({
  spec: openapiDocument,               // Parsed OpenAPI 3.0/3.1 object (dereferenced)
  baseUrl: "https://api.example.com",  // Optional; defaults to spec.servers[0].url
  name: "weather-service",             // Optional; defaults to spec.info.title
  version: "1.0.0",                    // Optional; defaults to spec.info.version
  
  // Static service authentication
  auth: {
    type: "bearer",
    token: process.env.API_SERVICE_TOKEN,
  },
  // OR header-based API key:
  // auth: { type: "header", name: "x-api-key", value: process.env.API_KEY },

  headers: {
    "User-Agent": "mcp-use-server/2.8",
  },

  // Tag filtering: include only operations tagged with these names
  tags: ["public", "weather"],

  // Exclusion rules: ANDed within an object; array rules evaluated as OR
  exclude: [
    { method: "DELETE" },                       // Exclude all DELETE operations
    { path: "^/admin/.*" },                     // Exclude admin paths (RegExp string or RegExp)
    { tags: ["deprecated"] },                   // Exclude deprecated operations
    { operationId: "internalHealthCheck" },     // Exclude specific operation
  ],

  // Optional custom fetch override (e.g. for mock testing or proxy routing)
  fetch: customFetch,
});
```

### Parameter & Body Mapping Rules

OpenAPI operation parameters map directly to MCP tool `inputSchema` properties:

| OpenAPI Parameter Type | Generated `inputSchema` Field | Behavior |
|---|---|---|
| **Path Parameter** (`in: "path"`) | Top-level required property | Extracted from input and interpolated into URL (`/items/{id}`) |
| **Query Parameter** (`in: "query"`) | Top-level optional or required | Appended to URL query string (`?limit=10&status=active`) |
| **Header Parameter** (`in: "header"`) | Top-level property | Injected into upstream request headers |
| **Cookie Parameter** (`in: "cookie"`) | *Ignored* | Cookie parameters are unsupported in MCP tool schemas |
| **Request Body** (`application/json`) | Top-level merged or `body` object | Validated against schema and serialized as JSON payload |

### Upstream Response Mapping in `fromOpenAPI`

`MCPServer.fromOpenAPI()` translates HTTP responses into MCP `CallToolResult` envelopes automatically:
- **HTTP 2xx (JSON content)**: Returns `{ content: [{ type: "text", text: JSON.stringify(data) }], structuredContent: data }`.
- **HTTP 2xx (Non-JSON content)**: Returns `{ content: [{ type: "text", text: bodyText }] }`.
- **HTTP 4xx / 5xx**: Returns `{ isError: true, content: [{ type: "text", text: `HTTP ${status}: ${body}` }] }`.

---

## Pattern 2: Production Curated Route Forwarding with `server.tool`

While `fromOpenAPI()` is ideal for rapid prototyping, production MCP servers often should **not** expose 50+ raw REST endpoints directly to an LLM. Exposing too many low-level endpoints causes:
1. **Context Window Exhaustion**: OpenAPI schemas for dozens of endpoints consume thousands of prompt tokens on every turn.
2. **Model Navigation Confusion**: Models struggle to decide between overlapping endpoints (`GET /users`, `GET /users/search`, `GET /accounts/users`).
3. **Leaked Internal Credentials**: Inability to forward the active end-user's OAuth token dynamically.

The recommended production pattern is to declare high-signal tools with `server.tool()` that forward requests to upstream REST endpoints, prune noisy fields, and propagate dynamic caller authentication.

---

## Runnable Before & After Code Transformation

### Before: Legacy Ad-Hoc Express REST Client

In legacy systems, developers often wrote Express route handlers or loose scripts that performed unvalidated fetch calls with static credentials and unstructured error propagation:

```typescript
// Legacy REST wrapper: Unvalidated inputs, static service auth, unhandled 500 crashes
// legacy-rest-server.ts
import express from "express";

const app = express();
app.use(express.json());

const UPSTREAM_API = "https://api.linear.example.com";
const STATIC_API_KEY = process.env.LINEAR_API_KEY; // Static server key, not user identity

// Fragile REST forwarder
app.post("/api/create-issue", async (req, res) => {
  const { teamId, title, description, priority } = req.body;

  if (!teamId || !title) {
    return res.status(400).json({ error: "Missing required parameters" });
  }

  try {
    const response = await fetch(`${UPSTREAM_API}/issues`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${STATIC_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ teamId, title, description, priority }),
    });

    if (!response.ok) {
      // Leaking raw upstream stack trace or HTML error page to client
      const errorText = await response.text();
      return res.status(response.status).send(errorText);
    }

    // Returning massive raw payload containing 80+ unused internal metadata fields
    const rawData = await response.json();
    return res.json(rawData);
  } catch (err: any) {
    // Unhandled exception crashes connection
    return res.status(500).json({ error: err.message });
  }
});

app.listen(3000, () => console.log("Legacy REST wrapper running on port 3000"));
```

---

### After: Canonical mcp-use v2 Server with Dynamic Auth & Payload Pruning

In `mcp-use v2`, the server defines a semantically descriptive tool, validates inputs using Standard Schema (Zod v4), forwards the end-user's verified Bearer token from `ctx.auth.token`, catches upstream errors gracefully in an MCP error envelope, and prunes the response to essential fields:

```typescript
// Canonical mcp-use v2: Dynamic auth pass-through, payload pruning, robust error containment
// server.ts
import { MCPServer } from "mcp-use";
import { oauthAuth0Provider } from "mcp-use/oauth/auth0";
import { z } from "zod";

const UPSTREAM_API = "https://api.linear.example.com";

const server = new MCPServer({
  name: "project-management-mcp",
  version: "2.0.0",
  basePath: "/mcp",
  mixedAuth: true, // Enables unauthenticated tool discovery while protecting execution
  oauth: oauthAuth0Provider({
    domain: process.env.AUTH0_DOMAIN!,
    clientId: process.env.AUTH0_CLIENT_ID!,
  }),
});

// Standard Schema definitions (Zod v4)
const CreateIssueInputSchema = z.object({
  teamId: z.string().describe("Target team identifier (e.g. 'ENG', 'DES')"),
  title: z.string().min(3).max(120).describe("Concise issue title"),
  description: z.string().optional().describe("Markdown description of the task or defect"),
  priority: z.enum(["low", "medium", "high", "urgent"]).default("medium").describe("Issue priority level"),
});

const CreateIssueOutputSchema = z.object({
  issueId: z.string(),
  identifier: z.string(),
  url: z.string(),
  status: z.string(),
});

export const createIssue = server.tool(
  {
    name: "create-issue",
    title: "Create Project Issue",
    description: "Create a tracked issue in Linear using the caller's authorized account",
    inputSchema: CreateIssueInputSchema,
    outputSchema: CreateIssueOutputSchema,
    securitySchemes: [{ type: "oauth2", scopes: ["issues:write"] }],
  },
  async ({ teamId, title, description, priority }, ctx) => {
    // 1. Dynamic Authentication Pass-Through: Forward caller's verified OAuth Bearer token
    const userToken = ctx.auth?.token;
    if (!userToken) {
      return {
        isError: true,
        content: [{ type: "text", text: "Unauthorized: Missing active caller bearer token." }],
      };
    }

    try {
      // 2. Controlled Upstream Request Dispatch
      const upstreamResponse = await fetch(`${UPSTREAM_API}/issues`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${userToken}`,
          "Content-Type": "application/json",
          "User-Agent": "mcp-use-server/2.8",
        },
        body: JSON.stringify({
          teamId,
          title,
          description: description ?? "",
          priority,
        }),
        signal: ctx.signal, // Propagate client cancellation signal
      });

      // 3. Robust Error Containment: Keep model context clean
      if (!upstreamResponse.ok) {
        const errorText = await upstreamResponse.text();
        return {
          isError: true,
          content: [
            {
              type: "text",
              text: `Upstream Linear API rejected issue creation (HTTP ${upstreamResponse.status}): ${errorText}`,
            },
          ],
        };
      }

      const rawData = (await upstreamResponse.json()) as {
        id: string;
        identifier: string;
        url: string;
        state: { name: string };
      };

      // 4. Payload Pruning: Return only high-signal structured data to prevent context bloat
      const prunedResult = {
        issueId: rawData.id,
        identifier: rawData.identifier,
        url: rawData.url,
        status: rawData.state?.name ?? "Created",
      };

      return {
        content: [
          {
            type: "text",
            text: `Successfully created issue ${prunedResult.identifier}: "${title}" (${prunedResult.url})`,
          },
        ],
        structuredContent: prunedResult,
      };
    } catch (err: any) {
      // 5. Network Boundary Safety
      return {
        isError: true,
        content: [
          {
            type: "text",
            text: `Network failure connecting to upstream issue tracker: ${err.message}`,
          },
        ],
      };
    }
  }
);

export default server;
```

---

## Handling Multi-Endpoint Aggregation (Composite Tools)

In REST architectures, answering a user question often requires chaining multiple endpoints:
`GET /users/{id}` → `GET /users/{id}/teams` → `GET /teams/{teamId}/projects`.

Forcing an agent to call 3 distinct MCP tools sequentially incurs heavy token cost and latency. Instead, migrate the workflow into a single **Composite Tool**:

```typescript
export const getUserWorkspaces = server.tool(
  {
    name: "get-user-workspaces",
    description: "Fetch comprehensive profile, teams, and active projects for an account in a single call",
    inputSchema: z.object({ accountId: z.string() }),
    outputSchema: z.object({
      profile: z.object({ name: z.string(), email: z.string() }),
      teams: z.array(z.string()),
      activeProjectsCount: z.number(),
    }),
  },
  async ({ accountId }, ctx) => {
    const headers = { Authorization: `Bearer ${ctx.auth?.token}` };

    // Parallel fetch aggregation server-side
    const [profileRes, teamsRes] = await Promise.all([
      fetch(`${UPSTREAM_API}/users/${accountId}`, { headers, signal: ctx.signal }),
      fetch(`${UPSTREAM_API}/users/${accountId}/teams`, { headers, signal: ctx.signal }),
    ]);

    if (!profileRes.ok || !teamsRes.ok) {
      return { isError: true, content: [{ type: "text", text: "Failed to resolve user account data." }] };
    }

    const profile = await profileRes.json();
    const teams = await teamsRes.json();

    const structuredContent = {
      profile: { name: profile.name, email: profile.email },
      teams: teams.map((t: any) => t.name),
      activeProjectsCount: teams.reduce((acc: number, t: any) => acc + (t.projectCount || 0), 0),
    };

    return {
      content: [{ type: "text", text: `User ${profile.name} belongs to ${teams.length} teams.` }],
      structuredContent,
    };
  }
);
```

---

## Anti-Patterns and Common Migration Traps

| Anti-Pattern | Root Mechanism & Failure Mode | Canonical v2 Fix |
|---|---|---|
| **Passing Unbundled Remote `$ref` to `fromOpenAPI`** | `MCPServer.fromOpenAPI()` does not fetch remote HTTP schema references at runtime. Results in schema generation failure or unresolved pointer exceptions. | Dereference or pre-bundle the OpenAPI document before initializing (e.g. using `@apidevtools/json-schema-ref-parser` or `redocly bundle`). |
| **Dumping Raw REST Payloads into Tool Returns** | Returning raw database rows or 100-field REST JSON objects floods the LLM context window, causes token limits to trip, and induces hallucination. | Define a strict `outputSchema` with only relevant fields and return a pruned `structuredContent` object. |
| **Crashing on Upstream 4xx/5xx HTTP Statuses** | Throwing unhandled exceptions or returning raw HTML error pages crashes the MCP JSON-RPC call with an internal server error. | Check `if (!response.ok)` and return `{ isError: true, content: [{ type: "text", text: "Error message" }] }`. |
| **Ignoring Client Abort Signals (`ctx.signal`)** | Upstream fetch continues running even after the user cancels the query in ChatGPT/Inspector, wasting compute and API rate limits. | Pass `signal: ctx.signal` to all upstream `fetch()` options. |
| **Hardcoding Service API Keys for User Operations** | Using a shared static `API_KEY` for actions that should be attributed to the end user bypasses audit logging and authorization boundaries. | Enable `mixedAuth: true`, attach an OAuth provider, and extract `ctx.auth?.token` to forward with `Authorization: Bearer ${token}`. |
| **Exposing Destructive REST Routes Without Hints** | Exposing `DELETE /repos/{id}` without tool annotations causes LLMs to execute destructive operations without prompting for human approval. | Apply tool annotations: `annotations: { destructiveHint: true, readOnlyHint: false, idempotentHint: true }`. |

---

## Next Steps & Cross-References

- **Auth Pass-Through & Configuration**: See `05-v1-to-v2-auth.md` for provider configuration and `mixedAuth: true`.
- **Elicitation for Sensitive Operations**: If an upstream REST operation requires human confirmation (e.g. DELETE or payment), see `10-elicitation-and-state-evolution.md`.
- **Workflow Testing**: See `references/30-workflows/06-openapi-to-mcp.md` for CLI testing with `mcp-use dev` and the interactive Inspector.
