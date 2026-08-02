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
server.listen();
```

**Verify:** No TypeScript errors: `npm run typecheck`.

### 3. Test Locally

```bash
npm run dev
# Output: "MCP server listening on http://127.0.0.1:3000/mcp"
# Inspector opens at http://127.0.0.1:3000/mcp/inspector
```

In Inspector:
1. Click **Tools** tab.
2. Click **get-weather**.
3. Enter city: `"Paris"`.
4. Click **Call**.

**Verify:** Response shows `{ city: "Paris", temperature: 22, condition: "Partly cloudy" }`.

### 4. Push to GitHub

```bash
git init
git add .
git commit -m "feat: initial weather server"
git remote add origin https://github.com/YOUR_USERNAME/my-weather-server.git
git push -u origin main
```

**Verify:** Repo appears on GitHub.

### 5. Deploy to Vercel

```bash
mcp-use login
# Opens browser for device-code OAuth (Manufact Cloud login)

npm run deploy
# Prompts: create Vercel project? (yes) → GitHub App install → deploying...
# Output: https://my-weather-server.vercel.app/mcp
```

**Verify:** Visit the URL in inspector by setting MCP URL to `https://my-weather-server.vercel.app/mcp` + re-connecting.

## Common Issues

| Issue | Solution |
|-------|----------|
| `login` returns 401 | Run `mcp-use login --no-open` and paste the device code manually |
| Vercel deploy hangs on "Waiting for GitHub App" | Approve the Manufact Cloud GitHub App in your account settings |
| 502 from deployed server | Check `mcp-use deployments list` + `mcp-use deployments logs <id>` for errors |

## Next

- Add more tools to `index.ts`.
- Add resources (read `../06-resources/01-overview.md`).
- Add OAuth to protect endpoints (read `../11-auth/01-overview.md`).
- Deploy on other platforms (read `../25-deploy/01-decision-matrix.md`).
