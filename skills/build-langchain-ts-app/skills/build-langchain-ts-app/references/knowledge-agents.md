# Knowledge Agents Reference

Complete reference for building knowledge-domain agents in LangChain.js v1: SQL agents, voice pipelines, and multi-knowledge-base routing. All APIs verified against langchain@1.2+, @langchain/core@1.1+, @langchain/langgraph@1.2+. TypeScript only unless labeled Python.

---

## SQL Agent — Core Architecture

### Internal Workflow (8 Steps)

The SQL agent follows a fixed ReAct (Reasoning + Acting) loop that alternates between LLM reasoning and tool execution:

1. Fetch available tables via `sql_db_list_tables`
2. Determine which tables are relevant to the question
3. Retrieve schemas for those tables via `sql_db_schema`
4. Generate SQL query using the LLM
5. Run the query through `sql_db_query_checker` (pre-execution validation)
6. Execute the query via `sql_db_query`
7. If error — iteratively rewrite and retry (up to N attempts configured in system prompt)
8. Formulate natural-language answer from results

The pattern is ReAct-style: the LLM reasons about what to do, calls a tool, observes the output, then reasons again. This means the number of LLM calls scales with schema complexity and query difficulty — budget accordingly.

### SQL Toolkit Tools

Four tools ship with `SqlToolkit`. Each tool has two name aliases (the tool object name and the human-readable label used in traces).

| Tool | Description | When Called |
|---|---|---|
| `sql_db_list_tables` / `list-tables-sql` | Returns comma-separated list of all available tables | First step always — agent must know what exists before selecting tables |
| `sql_db_schema` / `info-sql` | Returns CREATE TABLE DDL + sample rows for the specified tables | After listing tables — agent selects relevant tables and inspects their shape |
| `sql_db_query` / `query-sql` | Executes a SELECT query, returns result set or error string | Final execution — after the checker passes |
| `sql_db_query_checker` / `query-checker` | LLM validates the SQL syntax and semantics before execution | Before every `query-sql` call — catches hallucinated columns, wrong JOINs |

---

## SQL Agent — Safety Layer

### Read-Only Enforcement

The safety layer runs before any query reaches the database. Apply it inside every custom `execute_sql` tool, not just at the LLM prompt level.

```typescript
// Pattern from official LangChain JS SQL agent tutorial
const DENY_RE = /\b(INSERT|UPDATE|DELETE|ALTER|DROP|CREATE|REPLACE|TRUNCATE)\b/i;
const HAS_LIMIT_TAIL_RE = /\blimit\b\s+\d+(\s*,\s*\d+)?\s*;?\s*$/i;

function sanitizeSqlQuery(query: string): string {
  const trimmed = query.trim();

  // Must be a single statement — reject stacked queries
  if (trimmed.includes(";") && trimmed.indexOf(";") < trimmed.length - 1) {
    throw new Error("Only single SQL statements are allowed.");
  }

  // Must start with SELECT
  if (!/^\s*SELECT\b/i.test(trimmed)) {
    throw new Error("Only SELECT queries are allowed.");
  }

  // No DML or DDL anywhere in the query
  if (DENY_RE.test(trimmed)) {
    throw new Error("DML and DDL statements are not allowed.");
  }

  // Auto-append LIMIT if missing — prevents full-table scans
  if (!HAS_LIMIT_TAIL_RE.test(trimmed)) {
    return trimmed.replace(/;?\s*$/, " LIMIT 5");
  }

  return trimmed;
}
```

The two regex patterns cover distinct failure modes: `DENY_RE` blocks destructive keywords anywhere in the query (including inside subqueries), and `HAS_LIMIT_TAIL_RE` matches a `LIMIT N` at the end of the statement (with optional offset syntax).

### Zod-Validated `executeSql` Tool

Wrap the sanitizer in a typed LangChain tool so the LLM receives a clean schema and error messages propagate as tool observations (not thrown errors that break the agent loop).

```typescript
import { tool } from "langchain";
import * as z from "zod";

const executeSql = tool(
  async ({ query }) => {
    const safeQuery = sanitizeSqlQuery(query);
    const result = await db.run(safeQuery);
    return typeof result === "string" ? result : JSON.stringify(result, null, 2);
  },
  {
    name: "execute_sql",
    description: "Execute a READ-ONLY SQLite SELECT query and return results.",
    schema: z.object({
      query: z.string().describe("SQLite SELECT query (read-only, no DML/DDL)."),
    }),
  }
);
```

Returning a string from the tool handler (rather than throwing) ensures the agent sees the error as a tool result and can revise its SQL rather than crashing.

### Production Security Checklist

- [ ] Use read-only DB credentials/user for the agent connection — the agent should not be able to write even if the sanitizer fails
- [ ] Prohibit DML at the SQL level: INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE — enforce in code, not just prompt
- [ ] Run `sql_db_query_checker` before every execution — catches hallucinated column names before they hit the DB
- [ ] Auto-append `LIMIT N` (default 5) if missing — prevents full-table scans that expose PII
- [ ] Inject security predicates (e.g. `customer_id = ?`) via DB-level Row Level Security (RLS) — **do not trust the LLM to enforce access control**
- [ ] Consider human-in-the-loop approval for any query touching production data (see LangGraph interrupt pattern)
- [ ] Never allow `SELECT *` — prefer explicit column lists to avoid leaking unexpected columns

**Community warning (u/lgastako, r/LangChain):** "For #1 you should be using something like RLS in the database. You absolutely cannot trust LLMs to enforce security policies."

---

## SQL Agent — Full TypeScript Setup

### Package Installation

```bash
npm install langchain @langchain/core @langchain/openai typeorm sqlite3 zod
# For Postgres
npm install pg
# Optional: enable LangSmith tracing
# Set LANGSMITH_TRACING=true and LANGSMITH_API_KEY in env
```

### Database Setup (SQLite + Chinook)

The `resolveDbPath` helper downloads the sample Chinook database on first run and caches it locally, making the setup self-contained for development.

```typescript
import fs from "node:fs/promises";
import path from "node:path";
import { SqlDatabase } from "@langchain/classic/sql_db";
import { DataSource } from "typeorm";

const url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db";
const localPath = path.resolve("Chinook.db");

async function resolveDbPath(): Promise<string> {
  try {
    await fs.access(localPath);
    return localPath;
  } catch {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`Failed to download DB: ${resp.status}`);
    const buf = Buffer.from(await resp.arrayBuffer());
    await fs.writeFile(localPath, buf);
    return localPath;
  }
}

let db: SqlDatabase | undefined;

async function getDb(): Promise<SqlDatabase> {
  if (!db) {
    const dbPath = await resolveDbPath();
    const datasource = new DataSource({ type: "sqlite", database: dbPath });
    db = await SqlDatabase.fromDataSourceParams({ appDataSource: datasource });
  }
  return db;
}

async function getSchema(): Promise<string> {
  const database = await getDb();
  return await database.getTableInfo();
}
```

### Postgres DataSource Config

```typescript
const datasource = new DataSource({
  type: "postgres",
  host: process.env.DB_HOST || "localhost",
  port: parseInt(process.env.DB_PORT || "5432"),
  username: process.env.DB_USER || "admin",
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME || "demo_db",
});
```

### SQLToolkit Classic Approach

`SqlToolkit` provides all four tools pre-wired. Prefer this when you want the default ReAct loop without a custom sanitizer.

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { SqlToolkit } from "@langchain/classic/agents/toolkits/sql";
import { SqlDatabase } from "@langchain/classic/sql_db";
import { DataSource } from "typeorm";

const llm = new ChatOpenAI({ model: "gpt-4.1-mini", temperature: 0 });
const datasource = new DataSource({
  type: "sqlite",
  database: "path/to/Chinook.db",
});
const database = await SqlDatabase.fromDataSourceParams({ appDataSource: datasource });
const toolkit = new SqlToolkit(database, llm);
const tools = toolkit.getTools();
// Tools: query-sql, info-sql, list-tables-sql, query-checker
```

### System Prompt

The system prompt must embed the full authoritative schema. Without it the LLM hallucinates column names.

```typescript
import { SystemMessage } from "langchain";

const getSystemPrompt = async () => new SystemMessage(`
You are a careful SQLite analyst.

Authoritative schema (do not invent columns or tables):
${await getSchema()}

Rules:
- Think step-by-step.
- When you need data, call the tool \`execute_sql\` with ONE SELECT query.
- READ-ONLY only. No INSERT/UPDATE/DELETE/ALTER/DROP/CREATE/REPLACE/TRUNCATE.
- Limit to 5 rows unless the user explicitly asks for more.
- If the tool returns an error, revise the SQL and try again.
- Maximum 5 attempts; after that, tell the user you could not complete the query.
- Prefer explicit column lists; avoid SELECT *.
`);
```

### Agent Construction

```typescript
import { createAgent, initChatModel } from "langchain";

// LLM must support tool-calling
const model = await initChatModel("gpt-4.1");  // or claude-sonnet-4-6, gemini-2.5-flash-lite

const agent = createAgent({
  model,
  tools: [executeSql],           // or toolkit.getTools() for classic approach
  systemPrompt: getSystemPrompt, // async function — called fresh each invocation
});
```

### SQL Agent with Streaming

Stream results to show the agent's intermediate tool calls alongside the final answer. Use `streamMode: "values"` to receive the full state after each step.

```typescript
const question = "Which genre, on average, has the longest tracks?";

const stream = await agent.stream(
  { messages: [{ role: "user", content: question }] },
  { streamMode: "values" }
);

for await (const step of stream) {
  const msg = step.messages.at(-1);
  if (msg?.tool_calls?.length) {
    // Show tool calls as they happen
    console.dir(msg.tool_calls, { depth: null });
  } else if (msg?.content) {
    console.log(`${msg.role}: ${msg.content}`);
  }
}

// Example output:
// human: Which genre, on average, has the longest tracks?
// ai: [tool call: execute_sql]
// tool: [{"Genre":"Sci Fi & Fantasy","AvgMilliseconds":2911783}]
// ai: Sci Fi & Fantasy — average track length ≈ 48.5 minutes.
```

---

## SQL Agent — Production Patterns

### Pattern 1: Report Builder Tool

Instead of letting the LLM write raw SQL joins, expose a structured report builder where the LLM only picks metrics and dimensions. This solves the "complex joins" failure mode without blocking agentic behavior.

```typescript
const reportBuilderTool = tool(
  async ({ metrics, dimensions, dateRange }) => {
    // LLM decides WHAT — programmatic layer builds the actual SQL
    // Auto-injects date range and user access filters
    const sql = buildReportQuery({ metrics, dimensions, dateRange });
    return await db.run(sql);
  },
  {
    name: "build_report",
    description: "Build a data report. Specify metrics and dimensions.",
    schema: z.object({
      metrics: z.array(z.string()).describe("List of metrics to include (e.g. revenue, count)"),
      dimensions: z.array(z.string()).describe("List of dimensions to group by (e.g. region, product)"),
      dateRange: z.object({ start: z.string(), end: z.string() }).optional(),
    }),
  }
);
```

**Why it works (u/cipher982, r/LangChain):** "SQL databases can be too complex for correct joins unless using GPT-4, which is too slow." The report builder pattern makes the LLM pick from known-valid options; joins and filters are programmatic.

### Pattern 2: Stored Procedure Routing

Route common queries to stored procedures (pre-validated, fast) and fall through to free-form SQL only when no procedure matches. This dramatically reduces hallucination surface area for predictable query patterns.

```typescript
import { StateGraph, START } from "@langchain/langgraph";

function routeToProcedure(state: { query: string }): string {
  const procedure = classifyToStoredProcedure(state.query);
  return procedure ? "runProcedure" : "naturalLanguageSql";
}

// Stored procedures return fully formatted, pre-validated answers
// Much more reliable than open-ended SQL generation for known query shapes
```

### Pattern 3: Skills-Based SQL Assistant (Progressive Disclosure)

For schemas larger than ~1K tokens, load skill content on demand rather than stuffing the entire schema into the system prompt. This reduces prompt size and focuses the LLM on the relevant subset.

| Skill Size | Strategy |
|---|---|
| < 1K tokens | Embed directly in system prompt |
| 1–10K tokens | Progressive disclosure — load on demand via tool call |
| > 10K tokens | Pagination, semantic search within skill, hierarchical drill-down |

```typescript
interface Skill {
  name: string;
  description: string;  // lightweight — shown in system prompt always
  content: string;      // full schema + business logic — loaded only when needed
}

const SKILLS: Skill[] = [
  {
    name: "sales_analytics",
    description: "Query sales data: customers, orders, revenue, CLV, high-value orders.",
    content: `
      Tables: customers, orders, order_items
      Business rules:
      - Active customer: last_order_date > NOW() - INTERVAL '90 days'
      - CLV: SUM(order_total) WHERE customer_id = ?
      - High-value order: order_total > 1000

      Example queries:
      -- Top 10 customers by CLV
      SELECT customer_id, SUM(order_total) as clv
      FROM orders
      WHERE customer_id IN (SELECT id FROM customers WHERE status = 'active')
      GROUP BY customer_id
      ORDER BY clv DESC
      LIMIT 10
    `,
  },
  {
    name: "inventory_management",
    description: "Query inventory: stock levels, reorder alerts, warehouse locations.",
    content: `
      Tables: products, warehouses, inventory, stock_movements
      Business rules:
      - Reorder threshold: current_stock < reorder_point
      - Stock value: current_stock * unit_cost
    `,
  },
];

const loadSkill = tool(
  async ({ skillName }) => {
    const skill = SKILLS.find(s => s.name === skillName);
    if (!skill) return `Skill '${skillName}' not found. Available: ${SKILLS.map(s => s.name).join(", ")}`;
    return skill.content;
  },
  {
    name: "load_skill",
    description: "Load full schema and business logic for a skill before writing SQL queries.",
    schema: z.object({ skillName: z.string().describe("Name of the skill to load.") }),
  }
);
```

**Progressive disclosure flow:**

```
User: "Show top 5 customers by revenue this month"
Agent: → calls load_skill("sales_analytics")
       ← receives full schema + business rules + example queries
Agent: → calls execute_sql(query=...)
       ← returns results
Agent: → formats natural language answer
```

---

## SQL Agent — Complex Schema Strategies

**Core principle (u/KyleDrogo, r/LangChain, +20 upvotes):** "You need to build short pipelines that create downstream tables specifically for the LLM to query."

### Schema Preparation Checklist

- [ ] Use clean, semantic column names (rename `acct_cd` → `account_code`)
- [ ] Reduce high-cardinality categorical columns before exposing to LLM
- [ ] Include only columns that might appear in agent-generated queries
- [ ] Lowercase all categorical values for consistency
- [ ] Standardize date/timestamp formats across all tables
- [ ] Extract useful data from `extra_data`/`metadata` JSON columns into typed columns
- [ ] Create semantic views or materialized tables that the LLM can query directly

### Strategy Table

| Strategy | When to Use | Notes |
|---|---|---|
| Rename columns to semantic names | Always — non-negotiable | LLM generates wrong queries for opaque names like `acct_cd` |
| Create semantic views | Schemas with 50+ tables or legacy naming | Views hide complexity and provide stable names |
| Vector index for high-cardinality columns | Store names, product names, brand names | Map free-text input to exact DB values before SQL generation |
| Few-shot examples via vector similarity | When query accuracy is below threshold | Inject 3 most similar Q&A pairs at query time |
| Table classification before SQL | Schemas with 20+ tables | LLM picks the right table first; then generates targeted SQL |

### Few-Shot Examples via Vector Similarity

Retrieve examples at query time rather than hard-coding them. This scales to hundreds of examples without bloating the system prompt.

```typescript
import { MemoryVectorStore } from "@langchain/classic/vectorstores/memory";
import { OpenAIEmbeddings } from "@langchain/openai";
import { Document } from "@langchain/core/documents";

const examples = [
  { question: "How many customers are active?", query: "SELECT COUNT(*) FROM customers WHERE status = 'active'" },
  { question: "Top 5 revenue products this month?", query: "SELECT product_id, SUM(revenue) FROM orders WHERE date >= DATE_TRUNC('month', NOW()) GROUP BY product_id ORDER BY 2 DESC LIMIT 5" },
];

const exampleDocs = examples.map(e => new Document({ pageContent: e.question, metadata: { query: e.query } }));
const exampleStore = await MemoryVectorStore.fromDocuments(exampleDocs, new OpenAIEmbeddings());

// At query time: retrieve 3 most similar examples
const similar = await exampleStore.similaritySearch(userQuestion, 3);
const fewShot = similar.map(d => `Q: ${d.pageContent}\nSQL: ${d.metadata.query}`).join("\n\n");
```

### High-Cardinality Categorical Columns

When a column has thousands of distinct values (store names, product names), vector-index all values and look up the closest match before generating SQL.

```typescript
import { MemoryVectorStore } from "@langchain/classic/vectorstores/memory";
import { OpenAIEmbeddings } from "@langchain/openai";
import { Document } from "@langchain/core/documents";

// Index all store names once at startup
const storeNames: string[] = JSON.parse(await db.run("SELECT DISTINCT store_name FROM stores"));
const nameDocs = storeNames.map(n => new Document({ pageContent: n }));
const nameIndex = await MemoryVectorStore.fromDocuments(nameDocs, new OpenAIEmbeddings());

async function lookupStoreName(userInput: string): Promise<string> {
  const results = await nameIndex.similaritySearch(userInput, 1);
  return results[0].pageContent;
}
```

**Community refinement (u/nitagr):** Map product names to stable IDs in the vector DB — `"Cadbury Silk 50g" → product_id=12345` — then generate SQL with `WHERE product_id IN (12345)` rather than `WHERE name = 'Cadbury Silk 50g'`.

---

## SQL Agent — Multi-Database Routing

Three approaches for queries that span multiple databases or schemas. Choose based on whether queries can be isolated per DB (Approach 1 or 2) or require cross-database JOINs (Approach 3).

### Approach 1: Multiple Agents as Tools

Each database gets its own `SqlDatabase` instance and a dedicated agent. An orchestrator agent routes the user question to the right specialist.

```typescript
import { createAgent, tool } from "langchain";
import * as z from "zod";

const salesAgent = createAgent({ model, tools: [salesDbTool], systemPrompt: "Sales DB expert." });
const inventoryAgent = createAgent({ model, tools: [inventoryDbTool], systemPrompt: "Inventory DB expert." });

const routeSalesQuery = tool(
  async ({ query }) => {
    const result = await salesAgent.invoke({ messages: [{ role: "user", content: query }] });
    return result.messages.at(-1)?.content;
  },
  {
    name: "query_sales_db",
    description: "Query the sales database for revenue, orders, and customer data.",
    schema: z.object({ query: z.string() })
  }
);

const orchestratorAgent = createAgent({
  model,
  tools: [routeSalesQuery, routeInventoryQuery],
  systemPrompt: "Route questions to the appropriate database agent.",
});
```

### Approach 2: Separate SQLDatabase per DB, Supervisor Routes

One chain per DB, a single supervisor agent decides which chain to call.

**Community note (u/mehul_gupta1997):** "It will all depend on the prompting. It's not one agent one db, it's one chain per DB managed by a single agent."

### Approach 3: Federated Query via Trino/Presto

For queries that require cross-database JOINs, configure a Trino/Presto federation layer and expose a single connection to the agent.

- Configure Trino catalogs for each source (PostgreSQL, MySQL, Snowflake, BigQuery, MongoDB)
- Single Trino connection gives SQL access across all configured databases
- Connect with `SQLDatabase.from_uri("trino://user@localhost:8080/catalog")`
- LLM uses `catalog.schema.table` notation for cross-source queries

### `view_support` Flag for Views

```typescript
// TypeORM DataSource with view support (TypeScript equivalent)
const datasource = new DataSource({
  type: "postgres",
  url: "postgresql://...",
});
const db = await SqlDatabase.fromDataSourceParams({
  appDataSource: datasource,
  includesTables: ["sales_view", "inventory_summary"],
  sampleRowsInTableInfo: 2,
});
```

---

## Multi-Knowledge-Base Routing

### When to Use a Router vs. Subagents

| Use Router When | Use Subagents When |
|---|---|
| Distinct knowledge verticals with different tools/prompts | LLM can dynamically decide routing at runtime |
| Need parallel low-latency querying across verticals | Simpler setup, fewer sources |
| Fine-grained control over routing logic | Dynamic, unpredictable query patterns |
| Custom preprocessing required per source | Single domain |

### LangGraph Router — Full Pattern with Send

The canonical pattern uses `Send` to fan out to multiple vertical agents in parallel, then a `synthesize` node merges the results. The `ReducedValue` accumulator collects parallel outputs safely.

```typescript
import { StateGraph, START, END, Send } from "@langchain/langgraph";
import { StateSchema, ReducedValue } from "@langchain/langgraph";
import { z } from "zod/v4";
import { createAgent } from "langchain";
import { ChatOpenAI } from "@langchain/openai";

// State schema with reducer for parallel result collection
const AgentOutput = z.object({
  source: z.string(),
  result: z.string(),
});

const RouterState = new StateSchema({
  query: z.string(),
  classifications: z.array(
    z.object({
      source: z.enum(["github", "notion", "slack"]),
      query: z.string(),
    })
  ),
  results: new ReducedValue(
    z.array(AgentOutput).default(() => []),
    { reducer: (cur, upd) => cur.concat(upd) }  // collects parallel outputs
  ),
  finalAnswer: z.string(),
});
```

### Tool Definitions Per Vertical

```typescript
import { tool } from "langchain";

const searchCode = tool(
  async ({ query, repo = "main" }) =>
    `Found code matching '${query}' in ${repo}: ...`,
  {
    name: "search_code",
    description: "Search code in GitHub repositories.",
    schema: z.object({ query: z.string(), repo: z.string().optional().default("main") }),
  }
);

const searchNotion = tool(
  async ({ query }) => `Found Notion docs matching '${query}': ...`,
  {
    name: "search_notion",
    description: "Search Notion workspace for documentation.",
    schema: z.object({ query: z.string() }),
  }
);

const searchSlack = tool(
  async ({ query }) => `Found Slack messages matching '${query}': ...`,
  {
    name: "search_slack",
    description: "Search Slack messages and threads.",
    schema: z.object({ query: z.string() }),
  }
);
```

### Specialized Agents Per Vertical

```typescript
const llm = new ChatOpenAI({ model: "gpt-4.1" });

const githubAgent = createAgent({
  model: llm,
  tools: [searchCode, searchIssues, searchPrs],
  systemPrompt: `You are a GitHub expert. Answer questions about code,
API references, and implementation details.`,
});

const notionAgent = createAgent({
  model: llm,
  tools: [searchNotion, getPage],
  systemPrompt: `You are a Notion expert. Answer questions about internal
processes, policies, and team documentation.`,
});

const slackAgent = createAgent({
  model: llm,
  tools: [searchSlack, getThread],
  systemPrompt: `You are a Slack expert. Answer questions by searching
relevant threads and discussions.`,
});
```

### Classification + Routing Logic

```typescript
const routerLlm = new ChatOpenAI({ model: "gpt-4.1-mini" });

const ClassificationResultSchema = z.object({
  classifications: z.array(
    z.object({
      source: z.enum(["github", "notion", "slack"]),
      query: z.string(),
    })
  ),
});

async function classifyQuery(state: typeof RouterState.State) {
  const structuredLlm = routerLlm.withStructuredOutput(ClassificationResultSchema);
  const result = await structuredLlm.invoke([
    {
      role: "system",
      content: `Analyze this query and determine which knowledge bases to consult.
Return ONLY relevant sources with a targeted sub-question for each.`,
    },
    { role: "user", content: state.query },
  ]);
  return { classifications: result.classifications };
}

// Fan-out: returns Send objects for parallel execution
function routeToAgents(state: typeof RouterState.State): Send[] {
  return state.classifications.map(
    c => new Send(c.source, { query: c.query })
  );
}
```

### Synthesis Node

```typescript
async function synthesizeResults(state: typeof RouterState.State) {
  if (state.results.length === 0) return { finalAnswer: "No results found." };

  const formatted = state.results.map(r =>
    `**From ${r.source}:**\n${r.result}`
  );

  const synthesis = await routerLlm.invoke([
    {
      role: "system",
      content: `Synthesize these search results to answer: "${state.query}"`,
    },
    { role: "user", content: formatted.join("\n\n") },
  ]);

  return { finalAnswer: synthesis.content };
}
```

### Graph Assembly

```typescript
const workflow = new StateGraph(RouterState)
  .addNode("classify", classifyQuery)
  .addNode("github", queryGithub)
  .addNode("notion", queryNotion)
  .addNode("slack", querySlack)
  .addNode("synthesize", synthesizeResults)
  .addEdge(START, "classify")
  .addConditionalEdges("classify", routeToAgents, ["github", "notion", "slack"])
  .addEdge("github", "synthesize")
  .addEdge("notion", "synthesize")
  .addEdge("slack", "synthesize")
  .addEdge("synthesize", END)
  .compile();

// Invoke
const result = await workflow.invoke({ query: "How do I authenticate API requests?" });
console.log("Final Answer:", result.finalAnswer);
```

### Stateful Multi-Turn with Memory

Wrap the entire router as a tool for a conversational agent so users can ask follow-up questions.

```typescript
import { MemorySaver } from "@langchain/langgraph";

const searchKnowledgeBase = tool(
  async ({ query }) => {
    const result = await workflow.invoke({ query });
    return result.finalAnswer;
  },
  {
    name: "search_knowledge_base",
    description: "Search across GitHub, Notion, and Slack to find information.",
    schema: z.object({ query: z.string() }),
  }
);

const conversationalAgent = createAgent({
  model: "gpt-4.1",
  tools: [searchKnowledgeBase],
  checkpointer: new MemorySaver(),  // persists multi-turn context
});
```

---

## Voice Pipeline Architecture

### Architecture Options

| Architecture | Components | Pros | Cons |
|---|---|---|---|
| **STT → Agent → TTS ("Sandwich")** | STT provider → LangChain text agent → TTS provider | Full control, swap providers independently, clear stage boundaries, works with latest text models | Multiple service dependencies, added orchestration latency, loses speaker tone/emotion |
| **Speech-to-Speech (S2S)** | Multimodal audio-in → audio-out model | Simpler setup, lower theoretical latency, preserves prosody | Fewer model options, vendor lock-in, less observability |

**Recommendation:** The Sandwich architecture is the approach demonstrated in official LangChain docs. It achieves sub-700ms latency with suitable providers and gives full control over each stage.

### Voice Event Types

The pipeline uses a single discriminated union event type that flows through all three stages (STT → Agent → TTS), allowing each stage to pass through events from upstream and add its own.

| Event | Stage | Description |
|---|---|---|
| `stt_chunk` | STT | Partial transcript emitted in real-time as the user speaks |
| `stt_output` | STT | Final transcript for a complete turn — triggers agent invocation |
| `agent_chunk` | Agent | LLM text token/chunk — forwarded to TTS immediately |
| `tts_chunk` | TTS | Audio bytes ready to send to the browser/telephony client |

```typescript
// VoiceAgentEvent discriminated union
type VoiceAgentEvent =
  | { type: "stt_chunk"; transcript: string; ts: number }
  | { type: "stt_output"; transcript: string; ts: number }
  | { type: "agent_chunk"; text: string; ts: number }
  | { type: "tts_chunk"; audio: ArrayBuffer; ts: number };
```

### Demo Application Details (Official LangChain Docs)

- **Scenario:** Voice-driven sandwich-shop order assistant
- **STT:** AssemblyAI (real-time WebSocket, 16 kHz PCM)
- **TTS:** Cartesia (streaming WebSocket, version 2024-06-10)
- **Transport:** WebSockets — browser sends PCM audio, server sends PCM audio back
- **Server framework:** Hono + Bun
- **Memory:** `MemorySaver` + unique UUID `thread_id` per session
- **Adaptable to:** Twilio (telephony), Vonage, WebRTC

---

## Voice Pipeline — AssemblyAI STT Integration

### AssemblyAI Client (TypeScript)

The client connects once and exposes `sendAudio` / `receiveEvents` interfaces. The WebSocket stays open for the entire voice session.

```typescript
export class AssemblyAISTT {
  protected _bufferIterator = writableIterator<VoiceAgentEvent>();
  protected _connectionPromise: Promise<WebSocket> | null = null;
  private apiKey: string;

  constructor({ sampleRate = 16000, apiKey }: { sampleRate?: number; apiKey?: string }) {
    this.apiKey = apiKey ?? process.env.ASSEMBLYAI_API_KEY!;
  }

  async sendAudio(buf: Uint8Array): Promise<void> {
    const ws = await this._connection;
    ws.send(buf);
  }

  async close(): Promise<void> {
    const ws = await this._connection;
    ws.close();
  }

  async *receiveEvents(): AsyncGenerator<VoiceAgentEvent> {
    yield* this._bufferIterator;
  }

  protected get _connection(): Promise<WebSocket> {
    if (this._connectionPromise) return this._connectionPromise;
    this._connectionPromise = new Promise((resolve) => {
      const url = `wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&format_turns=true`;
      const ws = new WebSocket(url, {
        headers: { Authorization: this.apiKey },
      });
      ws.on("open", () => resolve(ws));
      ws.on("message", (data) => {
        const msg = JSON.parse(data.toString());
        if (msg.type === "Turn") {
          const ev: VoiceAgentEvent = msg.turn_is_formatted
            ? { type: "stt_output", transcript: msg.transcript, ts: Date.now() }
            : { type: "stt_chunk", transcript: msg.transcript, ts: Date.now() };
          this._bufferIterator.push(ev);
        }
      });
      ws.on("error", (err) => this._bufferIterator.cancel(err));
    });
    return this._connectionPromise;
  }
}
```

### STT Stream Function

Wraps the `AssemblyAISTT` class in an async generator that accepts an audio byte stream and emits `VoiceAgentEvent` objects.

```typescript
async function* sttStream(
  audioStream: AsyncIterable<Uint8Array>
): AsyncGenerator<VoiceAgentEvent> {
  const stt = new AssemblyAISTT({ sampleRate: 16000 });
  const passthrough = writableIterator<VoiceAgentEvent>();

  const producer = (async () => {
    for await (const chunk of audioStream) {
      await stt.sendAudio(chunk);
    }
    await stt.close();
  })();

  const consumer = (async () => {
    for await (const ev of stt.receiveEvents()) {
      passthrough.push(ev);
    }
    passthrough.done();
  })();

  try {
    yield* passthrough;
  } finally {
    await Promise.all([producer, consumer]);
  }
}
```

---

## Voice Pipeline — LangChain Agent Stage

### Voice-Optimized System Prompt

The agent's system prompt must be written for TTS output. Markdown formatting breaks TTS rendering — `**bold**` is read as "asterisk asterisk bold asterisk asterisk".

```typescript
import { createAgent } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

const agent = createAgent({
  model: "claude-haiku-4-5",  // Fast model for low latency
  tools: [addToOrder, confirmOrder],
  checkpointer: new MemorySaver(),  // Preserves context across turns within session
  systemPrompt: `You are a helpful sandwich shop assistant.
Your goal is to take the customer's order. Be concise and friendly.
Do NOT use emojis, special characters, or markdown formatting.
Do NOT use asterisks, bullet points, or numbered lists.
Your responses will be spoken aloud by a text-to-speech engine.
Keep responses under 2 sentences when possible.`,
});
```

**Critical TTS rules:**
- No emojis or special characters
- No markdown (`* # ** _ \` ~~`)
- No bullet points or numbered lists
- Short, conversational sentences — punctuation (commas, periods) controls TTS rhythm
- Responses should be under 2 sentences per turn for conversational feel

### Voice-Specific Streaming with `streamEvents`

Use `streamMode: "messages"` (not `"values"`) to emit tokens as they arrive, enabling TTS to start speaking before the LLM finishes generating. This cuts perceived latency by ~40%.

```typescript
import { HumanMessage } from "@langchain/core/messages";
import { v4 as uuidv4 } from "uuid";

async function* agentStream(
  eventStream: AsyncIterable<VoiceAgentEvent>
): AsyncGenerator<VoiceAgentEvent> {
  const threadId = uuidv4();  // unique per voice session

  for await (const ev of eventStream) {
    yield ev;  // pass through upstream events (stt_chunk, stt_output)

    if (ev.type === "stt_output") {
      const stream = await agent.stream(
        { messages: [new HumanMessage(ev.transcript)] },
        {
          configurable: { thread_id: threadId },
          streamMode: "messages",  // token-by-token, not step-by-step
        }
      );

      for await (const [msg] of stream) {
        if (msg.text) {
          yield { type: "agent_chunk", text: msg.text, ts: Date.now() };
        }
      }
    }
  }
}
```

---

## Voice Pipeline — Full Wiring

### `writableIterator` Helper

All three pipeline stages (STT, Agent, TTS) communicate through this producer-consumer async iterator. It queues items until a consumer is ready, handling backpressure without external libraries.

```typescript
function writableIterator<T>() {
  const queue: Array<{ value?: T; done?: boolean; error?: Error }> = [];
  let resolve: (() => void) | null = null;

  return {
    push(value: T) {
      queue.push({ value });
      resolve?.();
    },
    done() {
      queue.push({ done: true });
      resolve?.();
    },
    cancel(error?: Error) {
      queue.push({ done: true, error });
      resolve?.();
    },
    async *[Symbol.asyncIterator](): AsyncGenerator<T> {
      while (true) {
        if (queue.length > 0) {
          const item = queue.shift()!;
          if (item.error) throw item.error;
          if (item.done) return;
          yield item.value!;
        } else {
          await new Promise<void>(r => { resolve = r; });
          resolve = null;
        }
      }
    },
  };
}
```

### Hono WebSocket Server (Full Pipeline)

The three stages are wired as composable async generators. Audio in from the browser flows through STT → Agent → TTS, with the final `tts_chunk` events sent back as binary WebSocket frames.

```typescript
import { Hono } from "hono";
import { upgradeWebSocket } from "hono/bun";

const app = new Hono();

app.get(
  "/ws",
  upgradeWebSocket(async () => {
    const input = writableIterator<Uint8Array>();
    let currentSocket: WebSocket | null = null;

    // Wire the three-stage pipeline
    const sttEvents = sttStream(input);
    const agentEvents = agentStream(sttEvents);
    const output = ttsStream(agentEvents);

    // Drain output — forward tts_chunk audio back to browser
    const flush = (async () => {
      for await (const ev of output) {
        if (ev.type === "tts_chunk" && currentSocket) {
          currentSocket.send(ev.audio);
        }
      }
    })();

    return {
      onOpen(_event: Event, ws: WebSocket) {
        currentSocket = ws;
      },
      onMessage(event: MessageEvent) {
        const data = event.data;
        if (Buffer.isBuffer(data)) {
          input.push(new Uint8Array(data));
        }
      },
      async onClose() {
        input.cancel();
        await flush;
      },
    };
  })
);

export default app;
```

### Interruption Handling

The "barge-in" problem is one of the hardest production challenges. Without it, the bot talks over the user.

```typescript
// Pattern: cancel current TTS + reset when new STT input arrives mid-response
let currentTtsController: AbortController | null = null;

if (ev.type === "stt_output" && currentTtsController) {
  currentTtsController.abort();  // Cancel in-progress TTS
  currentTtsController = null;
}
```

**Community note (u/ChatEngineer, r/AI_Agents):** "Most demos fail on 'user interrupts during tool call'. State management gaps are where voice agents break in production." For PSTN calls, consider FreeSWITCH/SignalWire instead of Twilio for tighter media control. Twilio Streams add 150–300ms before the agent sees audio.

---

## Voice Pipeline — Latency Optimization

**Target:** Sub-700ms end-to-end (STT → LLM → TTS)

| Stage | Technique | Latency Impact |
|---|---|---|
| STT | AssemblyAI streaming WebSocket — not batch transcription | Real-time partial transcripts vs. full-turn delay |
| LLM | Use fast models: `claude-haiku-4-5`, `gpt-4o-mini`, `gemini-flash` | 200–400ms vs 1–2s for large models |
| LLM | `streamMode: "messages"` — start TTS before LLM finishes | Cuts perceived latency by ~40% |
| TTS | Cartesia streaming WebSocket | First audio chunk in ~50–100ms |
| Transport | WebSockets over HTTP polling | Eliminates per-turn connection overhead |
| Architecture | Concurrent producer-consumer generators | STT and TTS run simultaneously, no serial blocking |

**Community benchmark (u/Ok-Diver2792, r/AI_Agents):** "Started at ~7 seconds latency, optimized to 3–4 seconds. Target 1–2 seconds for conversational feel."

### STT + TTS Provider Options

| Component | Provider | Notes |
|---|---|---|
| STT | AssemblyAI | Official LangChain docs choice, real-time WebSocket |
| STT | Deepgram | Community favorite, often lower latency |
| STT | OpenAI Whisper | Good accuracy, slightly higher latency |
| TTS | Cartesia | Official LangChain docs choice, WebSocket streaming |
| TTS | ElevenLabs | Market leader, scales well |
| TTS | PlayHT | Good alternative voice quality |
| TTS | pyttsx3 | Local/offline, lower quality |
| S2S | OpenAI Realtime API | Simplest for speech-to-speech, skips Sandwich wiring |

---

## Community Anti-Patterns and War Stories

### SQL Agent Anti-Patterns

| Anti-Pattern | Root Cause | Fix |
|---|---|---|
| Complex joins with raw LLM SQL | LLMs struggle with multi-table joins at speed | Use a programmatic report builder — LLM picks metrics/dimensions only |
| Sending full schema to LLM | Too much schema confuses routing and wastes tokens | Table classification + vector schema lookup — inject only relevant tables |
| Trusting LLM for access control | LLMs cannot be relied on for security enforcement | DB-level RLS, row-level permissions, or CTE restrictions post-processing |
| Using deprecated `create_sql_agent` | Old API, no LangGraph integration | Use `createAgent` (TypeScript) or `create_agent` (Python) with explicit nodes |
| Opaque column names like `acct_cd` | LLM cannot reason about undescribed columns | Rename columns semantically, or inject a `column_descriptions` dict |
| Sending raw LLM SQL output to DB | LLM wraps SQL in markdown fences, adds commentary | Strip code fences, normalize whitespace before execution |

### Knowledge Base Anti-Patterns

| Anti-Pattern | Root Cause | Fix |
|---|---|---|
| Re-embedding on every startup | No separation between ingestion and serving | Separate `ingest.ts` pipeline; production loads persisted vector store |
| One index for all documents | Mixed domains degrade retrieval relevance | Separate indexes per domain + router classification |
| Wrong parser for document type | PyPDF fails on tables; Tesseract loses structure | Evaluate parsers against actual documents; use LlamaParse for tables |
| Default chunk size without tuning | `chunkSize` and `chunkOverlap` affect retrieval precision | Tune per document type: 500–1500 size, 10–20% overlap |

**Community insight (r/LangChain RAG Engineer's Guide):** "Switching parsers can yield 10–20% RAG performance improvements — often more than adding advanced retrieval techniques."

### Voice Agent Anti-Patterns

| Anti-Pattern | Root Cause | Fix |
|---|---|---|
| Markdown in voice responses | TTS reads `**bold**` as "asterisk asterisk bold..." | Strict system prompt: no markdown, no bullet points, no special chars |
| HTTP polling instead of WebSockets | 200–500ms per-turn overhead | WebSockets are required for real-time voice |
| No interrupt (barge-in) handling | Agent talks over user who starts speaking | AbortController on TTS; reset on new `stt_output` event |
| Testing only in browser audio quality | Phone compression sounds different | Test over actual PSTN/telephony with full signal compression |
| No Voice Activity Detection (VAD) | Pauses misclassified as turn ends | Implement VAD or use provider-side VAD settings |
| Single `thread_id` across sessions | Conversation context bleeds between sessions | Generate new UUID `thread_id` per voice session |

---

## Known Pitfalls

| Issue | Domain | Fix |
|---|---|---|
| LLM generates DML (INSERT/UPDATE/DELETE) | SQL | Enforce read-only with `sanitizeSqlQuery` + DB-level read-only user — prompt instructions alone are insufficient |
| LLM invents column names not in schema | SQL | Inject the full `getTableInfo()` schema string in the system prompt; never rely on the LLM's training knowledge of the DB |
| No `LIMIT` clause on generated queries | SQL | Auto-append `LIMIT 5` in the sanitizer before execution |
| LLM trusted for row-level access control | SQL | Use database RLS — the LLM cannot reliably filter by `customer_id` or tenant |
| Full schema overflows context window | SQL | Progressive skill loading or table classification to inject only relevant subset |
| Router routes to wrong vertical | Multi-KB | Add confidence scoring in the classification step; include a fallback `general` vertical |
| Voice latency above 1s | Voice | Use `streamMode: "messages"`, fast model (haiku/flash), streaming TTS WebSocket |
| TTS reads markdown formatting aloud | Voice | System prompt must prohibit markdown — enforce it, not just suggest it |
| User interruptions break agent state | Voice | AbortController on TTS; detect `stt_output` during active TTS and cancel |
| Phone call audio quality differs from browser | Voice | Test over PSTN/telephony compression — μ-law 8kHz sounds different from PCM 16kHz |
| Single vector index for mixed domains | Knowledge Base | Separate indexes per domain with classifier routing |
| Re-embedding documents on every app startup | Knowledge Base | Separate ingestion pipeline; production app loads persisted store |
