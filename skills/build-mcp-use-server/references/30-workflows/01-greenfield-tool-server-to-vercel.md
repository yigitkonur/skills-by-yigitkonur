# Workflow: Greenfield Tool Server to Vercel

*Read this for an end-to-end workflow: scaffold, add a tool, test locally, deploy to Vercel.*

## Prerequisites

- Node.js >= 22
- `npm` or `pnpm`
- GitHub account with a repo (for Vercel deploy)
- Vercel account linked to GitHub

## Steps

### 1. Scaffold

```bash
npx create-mcp-use-app@2.0.0-beta.14 my-weather-server --template mcp-server --npm --install
cd my-weather-server
```

**Verify:** `package.json` has scripts `dev`, `build`, `deploy`. `index.ts` exports an empty MCPServer.

### 2. Add a Tool

Edit `index.ts` to add a weather tool:

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "weather-server",
  version: "1.0.0",
  basePath: "/api/mcp", // matches the Vercel Function path used in step 5
});

export const getWeather = server.tool(
  {
    name: "get-weather",
    description: "Get current weather for a city",
    inputSchema: z.object({
      city: z.string().describe("City name (e.g., 'San Francisco')"),
      unit: z.enum(["celsius", "fahrenheit"]).default("celsius").describe("Temperature unit"),
    }),
    outputSchema: z.object({
      city: z.string(),
      temperature: z.number(),
      condition: z.string(),
    }),
  },
  async ({ city, unit }) => {
    // Mock data; in reality, call an API
    const temp = unit === "celsius" ? 22 : 72;
    return {
      content: [{ type: "text", text: `Weather in ${city}: ${temp}°${unit[0].toUpperCase()}` }],
      structuredContent: { city, temperature: temp, condition: "Partly cloudy" },
    };
  }
);

export default server;
```

Never call `server.listen()` in this file — the CLI (`mcp-use dev`/`mcp-use start`) owns the listener locally, and the Vercel Function adapter in step 5 owns it in production.

**Verify:** No TypeScript errors: `npm run typecheck`.

### 3. Test Locally

```bash
npm run dev
# Output: "MCP server listening on http://127.0.0.1:3000/api/mcp"
# Inspector opens at http://127.0.0.1:3000/api/mcp/inspector
```

In Inspector:
1. Click **Tools** tab.
2. Click **get-weather**.
3. Enter city: `"Paris"`.
4. Click **Call**.

**Verify:** Response shows `{ city: "Paris", temperature: 22, condition: "Partly cloudy" }`.

### 4. Create the Vercel Function Entry Point

Vercel Functions are stateless. Create `api/mcp.ts` re-exporting the configured server (`MCPServer` exposes a Web-standard Fetch handler, so Vercel accepts it directly):

```typescript
import server from "../index.ts";

export default server;
```

Match Vercel's function path (`/api/mcp`) to `basePath` — that's why step 2 set `basePath: "/api/mcp"`. A mismatch here means Hono has no matching route and every request returns 404.

### 5. Push to GitHub and Deploy to Vercel

```bash
git init
git add .
git commit -m "feat: initial weather server"
git remote add origin https://github.com/YOUR_USERNAME/my-weather-server.git
git push -u origin main

npx vercel deploy
# Output: https://my-weather-server.vercel.app/api/mcp
```

`npx vercel deploy` is the standard Vercel CLI — this workflow never calls `mcp-use login` or `mcp-use deploy`. Those commands target Manufact Cloud, a separate deployment platform (see `../25-deploy/platforms/01-mcp-use-cloud.md`); do not mix the two.

**Verify:** Point the standalone Inspector at the deployed URL:

```bash
npx @mcp-use/inspector --url https://my-weather-server.vercel.app/api/mcp
```

## Common Issues

| Issue | Solution |
|-------|----------|
| 404 on `/api/mcp` | `basePath` in `index.ts` must match the Vercel function path exactly |
| Views/assets missing at runtime | Build with `MCP_URL=https://<project>.vercel.app npm run build` before `vercel deploy --prod`; the framework appends `/api/mcp` from `basePath` — see `../25-deploy/platforms/02-vercel.md` |
| 500 from deployed function | Run `npx vercel logs <deployment-url>` |

## Next

- Add more tools to `index.ts`.
- Add resources (read `../06-resources/01-overview.md`).
- Add OAuth to protect endpoints (read `../11-auth/01-overview.md`).
- Deploy on other platforms, including Manufact Cloud (read `../25-deploy/01-decision-matrix.md`).
