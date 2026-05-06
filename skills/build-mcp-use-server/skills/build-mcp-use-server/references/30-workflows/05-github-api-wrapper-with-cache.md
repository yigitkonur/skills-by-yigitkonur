# Workflow: GitHub REST API Wrapper with In-Memory Cache

**Goal:** wrap a slice of the GitHub REST API as MCP tools (`get-repo`, `list-issues`, `search-repos`). Cache responses in-process for 5 minutes. Throttle to one request every two seconds to stay under the unauthenticated rate limit.

## Prerequisites

- (Optional) `GITHUB_TOKEN` for higher rate limits.
- mcp-use ≥ 1.21.5.

## Layout

```
github-mcp/
├── package.json
├── tsconfig.json
└── src/
    ├── server.ts
    └── lib/github.ts
```

## `src/lib/github.ts` — fetch with cache + rate limit

```typescript
const CACHE_TTL = 300_000; // 5 minutes
const MIN_GAP = 2000;       // 2 s between requests

const cache = new Map<string, { data: unknown; expires: number }>();
let lastReq = 0;

export async function ghFetch(endpoint: string): Promise<unknown> {
  const cached = cache.get(endpoint);
  if (cached && Date.now() < cached.expires) return cached.data;

  const wait = MIN_GAP - (Date.now() - lastReq);
  if (wait > 0) await new Promise((r) => setTimeout(r, wait));
  lastReq = Date.now();

  const token = process.env.GITHUB_TOKEN;
  const res = await fetch(`https://api.github.com${endpoint}`, {
    headers: {
      Accept: "application/vnd.github.v3+json",
      "User-Agent": "mcp-github-server",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (res.status === 403 && res.headers.get("x-ratelimit-remaining") === "0") {
    const reset = res.headers.get("x-ratelimit-reset");
    throw new Error(
      `GitHub rate limit exhausted. Resets at ${reset ? new Date(+reset * 1000).toISOString() : "unknown"}`
    );
  }
  if (!res.ok) throw new Error(`GitHub ${res.status}: ${res.statusText}`);

  const data = await res.json();
  cache.set(endpoint, { data, expires: Date.now() + CACHE_TTL });
  return data;
}
```

## `src/server.ts`

```typescript
import { MCPServer, object, error } from "mcp-use/server";
import { z } from "zod";
import { ghFetch } from "./lib/github.js";

const server = new MCPServer({
  name: "github-mcp",
  version: "1.0.0",
  description: "GitHub REST wrapper with caching and rate-limit handling",
});

server.tool(
  {
    name: "get-repo",
    description: "Fetch repository metadata",
    schema: z.object({
      owner: z.string().min(1),
      repo: z.string().min(1),
    }),
  },
  async ({ owner, repo }) => {
    try {
      const d = (await ghFetch(`/repos/${owner}/${repo}`)) as Record<string, unknown>;
      return object({
        name: d.full_name,
        description: d.description,
        stars: d.stargazers_count,
        forks: d.forks_count,
        language: d.language,
        default_branch: d.default_branch,
        url: d.html_url,
      });
    } catch (e) {
      return error((e as Error).message);
    }
  }
);

server.tool(
  {
    name: "list-issues",
    description: "List recent issues on a repository",
    schema: z.object({
      owner: z.string(),
      repo: z.string(),
      state: z.enum(["open", "closed", "all"]).default("open"),
      per_page: z.number().int().min(1).max(30).default(10),
    }),
  },
  async ({ owner, repo, state, per_page }) => {
    try {
      const params = new URLSearchParams({ state, per_page: String(per_page) });
      const data = (await ghFetch(`/repos/${owner}/${repo}/issues?${params}`)) as Array<Record<string, unknown>>;
      return object({
        issues: data.map((i) => ({
          number: i.number,
          title: i.title,
          state: i.state,
          author: (i.user as Record<string, unknown>)?.login,
          url: i.html_url,
        })),
        count: data.length,
      });
    } catch (e) {
      return error((e as Error).message);
    }
  }
);

server.tool(
  {
    name: "search-repos",
    description: "Search GitHub repositories",
    schema: z.object({
      query: z.string().min(1),
      sort: z.enum(["stars", "forks", "updated"]).default("stars"),
      limit: z.number().int().min(1).max(30).default(10),
    }),
  },
  async ({ query, sort, limit }) => {
    try {
      const params = new URLSearchParams({ q: query, sort, per_page: String(limit) });
      const d = (await ghFetch(`/search/repositories?${params}`)) as {
        total_count: number;
        items: Array<Record<string, unknown>>;
      };
      return object({
        total: d.total_count,
        repos: d.items.map((r) => ({
          name: r.full_name,
          stars: r.stargazers_count,
          language: r.language,
          url: r.html_url,
        })),
      });
    } catch (e) {
      return error((e as Error).message);
    }
  }
);

await server.listen();
```

## Run

```bash
GITHUB_TOKEN=ghp_... npm run dev
```

## Test

```bash
curl -N -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get-repo","arguments":{"owner":"mcp-use","repo":"mcp-use"}}}'
```

Run the same call twice — the second should return instantly because the response was cached.

## Cache invalidation

The cache is process-scoped and TTL-based. To invalidate manually, expose a tool:

```typescript
server.tool(
  { name: "cache-flush", description: "Flush the in-memory cache", schema: z.object({}) },
  async () => { (await import("./lib/github.js")).cache?.clear(); return object({ flushed: true }); }
);
```

For multi-pod deployments, swap the in-memory `Map` for Redis using the same shape — `get`, `set`, `expires`.

## Notes

- The 2-second throttle is intentionally below the unauthenticated 60-req/hour limit. With a token you have 5 000 req/hour and could lower the gap.
- Cached entries are not refreshed on background — they are recomputed on the next miss.
- This pattern composes with any external REST API. Replace `https://api.github.com` and the auth header.

## See also

- Webhook delivery alongside REST: `09-webhook-handler-with-notifications.md`
- Caching strategies: `../17-advanced/`
- Auth headers from `ctx.auth`: `03-oauth-protected-supabase-server.md`
