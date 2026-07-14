# Workflow: Postgres Database Tool Server

**Goal:** expose a read-only Postgres database to an LLM. Three operations: a guarded SELECT (`query`), schema introspection (`get_schema`), and a prompt (`generate_query`) that the LLM uses to plan the SELECT before running it. Single connection pool.

## Prerequisites

- Postgres reachable, `DATABASE_URL` env set.
- `pg` driver, mcp-use ≥ 1.21.5.

## Layout

```
postgres-mcp/
├── package.json
├── tsconfig.json
├── .env.example
└── src/
    ├── server.ts
    └── tools/db.ts
```

## `package.json` (key deps)

```json
{
  "type": "module",
  "scripts": { "dev": "mcp-use dev", "build": "mcp-use build", "start": "mcp-use start" },
  "dependencies": {
    "mcp-use": "^1.21.5",
    "pg": "^8.12.0",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@types/pg": "^8.11.0",
    "typescript": "^5.5.0"
  }
}
```

## `.env.example`

```env
PORT=3000
DATABASE_URL=postgres://user:pass@localhost:5432/app
```

## `src/tools/db.ts`

```typescript
import { object, error } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import pg from "pg";
import { z } from "zod";

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });

// Sanitize identifier inputs (table/schema names) — pg cannot bind them.
function safeIdent(s: string): string {
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(s)) {
    throw new Error(`Invalid identifier: ${s}`);
  }
  return s;
}

export function registerDbTools(server: MCPServer) {
  server.tool(
    {
      name: "query",
      description:
        "Run a read-only SELECT query. Anything other than a SELECT is rejected. Result rows are capped at 100.",
      schema: z.object({
        sql: z.string().describe("SQL SELECT statement (single statement only)"),
        params: z
          .array(z.union([z.string(), z.number(), z.boolean(), z.null()]))
          .optional()
          .describe("Bind parameters in $1, $2 order"),
      }),
    },
    async ({ sql, params }) => {
      if (!/^\s*SELECT\b/i.test(sql)) {
        return error("Only SELECT queries are allowed");
      }
      if (sql.includes(";") && sql.trim().replace(/;$/, "").includes(";")) {
        return error("Multiple statements are not allowed");
      }
      const limited = /\bLIMIT\b/i.test(sql) ? sql : `${sql.replace(/;$/, "")} LIMIT 100`;
      try {
        const { rows, rowCount } = await pool.query(limited, params ?? []);
        return object({ rows, count: rowCount, truncated: rowCount === 100 });
      } catch (e) {
        return error(`Query failed: ${(e as Error).message}`);
      }
    }
  );

  server.tool(
    {
      name: "get_schema",
      description: "Show columns, types, and nullability for a table",
      schema: z.object({
        table: z.string().describe("Table name"),
        schema: z.string().default("public").describe("Schema name"),
      }),
    },
    async ({ table, schema: s }) => {
      try {
        safeIdent(table);
        safeIdent(s);
      } catch (e) {
        return error((e as Error).message);
      }
      const { rows } = await pool.query(
        `SELECT column_name, data_type, is_nullable, column_default
         FROM information_schema.columns
         WHERE table_schema = $1 AND table_name = $2
         ORDER BY ordinal_position`,
        [s, table]
      );
      if (rows.length === 0) return error(`Table not found: ${s}.${table}`);
      return object({ table, schema: s, columns: rows });
    }
  );

  server.prompt(
    {
      name: "generate_query",
      description: "Plan a SELECT for a natural-language ask. Calls get_schema first.",
      schema: z.object({
        description: z.string().describe("What data you want, in plain English"),
        table_hint: z.string().optional().describe("Likely table name, if known"),
      }),
    },
    async ({ description, table_hint }) => ({
      messages: [
        {
          role: "user" as const,
          content:
            `You will write a single Postgres SELECT.\n` +
            `1. Call get_schema for the relevant table${table_hint ? ` (likely "${table_hint}")` : ""} first.\n` +
            `2. Then call query with a SELECT that answers: ${description}.\n` +
            `Constraints: SELECT only, parameters via $1/$2, no semicolons.`,
        },
      ],
    })
  );

  process.on("SIGINT", async () => {
    await pool.end();
    process.exit(0);
  });
}
```

## `src/server.ts`

```typescript
import "dotenv/config";
import { MCPServer } from "mcp-use/server";
import { registerDbTools } from "./tools/db.js";

const server = new MCPServer({
  name: "postgres-mcp",
  version: "1.0.0",
  description: "Read-only Postgres tools",
});

registerDbTools(server);

await server.listen(parseInt(process.env.PORT || "3000", 10));
```

## Run

```bash
cp .env.example .env
npm install
npm run dev
```

## Test

```bash
# get_schema
curl -N -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_schema","arguments":{"table":"users"}}}'

# query
curl -N -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"query","arguments":{"sql":"SELECT id, email FROM users WHERE id = $1","params":["abc"]}}}'

# rejected: non-SELECT
curl -N -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"query","arguments":{"sql":"DELETE FROM users"}}}'
```

The third request returns a structured `error` content — not an exception.

## Defensive patterns

- **Identifier sanitizer.** `safeIdent` rejects anything that is not `[a-zA-Z_][a-zA-Z0-9_]*`. Postgres cannot bind identifiers; this is the only way to prevent injection in `get_schema`.
- **Single-statement guard.** Reject `;` followed by more SQL even though `pg` would only run one anyway — defense in depth.
- **Hard LIMIT.** Append `LIMIT 100` if absent. Caps tool-call cost and prevents the LLM from accidentally returning a million rows.
- **One pool, lifetime-scoped.** Created at module load, closed on `SIGINT`. Do not create a pool per request.
- **Read-only role.** Pair this server with a Postgres role that has only `SELECT` privileges. Code-level filters are belt-and-braces; the database is the wall.

## See also

- General SQL safety: `../17-advanced/`
- Per-user data with auth: `03-oauth-protected-supabase-server.md`
- Production hardening: `../24-production/`
