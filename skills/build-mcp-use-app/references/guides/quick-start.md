# Quick Start

Build a working MCP App with an interactive widget in under 10 minutes using the `mcp-use` TypeScript framework.

---

## 1. Prerequisites

- **Node.js 18** (or higher) — [download](https://nodejs.org/)
- **Package manager** — npm (bundled with Node), pnpm, or yarn

Verify your setup:

```bash
node --version   # v18.x.x or higher
npm --version    # 9.x.x or higher
```

---

## 2. Scaffold Your MCP App

The fastest way to start is with `create-mcp-use-app` using the `mcp-apps` template:

```bash
npx create-mcp-use-app@latest my-app --template mcp-apps
cd my-app
npm run dev
```

This creates a fully configured project with:
- MCP server with example tools
- React widget components in `resources/`
- Tailwind CSS for styling
- HMR development server with Inspector
- Type-safe tool calling with auto-generated types

The dev server launches at `http://localhost:3000` with:
- **MCP endpoint:** `http://localhost:3000/mcp`
- **Inspector:** `http://localhost:3000/inspector`

### Template Options

```bash
# MCP Apps — widget-focused (recommended for this guide)
npx create-mcp-use-app my-app --template mcp-apps

# Starter — full-featured server with tools, resources, prompts, widgets
npx create-mcp-use-app my-app --template starter

# MCP-UI — iframe, raw HTML, Remote DOM widget types
npx create-mcp-use-app my-app --template mcp-ui
```

| Template | Includes | Best for |
|----------|----------|----------|
| `mcp-apps` | React widgets, useCallTool, ChatGPT compatibility | Interactive widget apps |
| `starter` (default) | Tools, resources, prompts, widgets | Full-featured servers |
| `mcp-ui` | iframe, raw HTML, Remote DOM UIResource types | Complex UI requirements |

If you used the scaffolder, skip to [Section 6](#6-development-workflow).

---

## 3. Manual Setup

For existing projects or custom configurations:

### Initialize the project

```bash
mkdir my-mcp-app && cd my-mcp-app
npm init -y
npm install mcp-use zod@^4.0.0
npm install -D typescript @types/node @types/react @mcp-use/cli tsx
```

### Configure package.json

```json
{
  "name": "my-mcp-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "mcp-use dev src/server.ts",
    "build": "mcp-use build",
    "start": "mcp-use start"
  },
  "dependencies": {
    "mcp-use": "^1.21.4",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@mcp-use/cli": "latest",
    "typescript": "^5.5.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "tsx": "^4.0.0"
  }
}
```

- **`"type": "module"`** — required; without this, imports from `mcp-use/server` fail.
- **`"dev"`** — uses `mcp-use dev` for hot-reload with Inspector and widget HMR.

### Configure tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "jsx": "react-jsx",
    "strict": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*", "resources/**/*", ".mcp-use/**/*"]
}
```

### Create directories

```bash
mkdir -p src/tools resources/greeting public
```

---

## 4. Project Structure

An MCP Apps project looks like this:

```
my-mcp-app/
├── resources/                     # React widgets
│   └── greeting/
│       └── widget.tsx             # Widget entry point
├── public/                        # Static assets
│   └── icon.svg
├── src/
│   ├── server.ts                  # MCP server entry point
│   └── tools/
│       └── greet.ts               # Tool registrations
├── .mcp-use/                      # Auto-generated (types, build artifacts)
│   └── tool-registry.d.ts
├── package.json
└── tsconfig.json
```

---

## 5. Build Your First Widget

### Step 1: Create the Server Tool

```typescript
// src/tools/greet.ts
import { widget, text } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerGreetTools(server: MCPServer) {
  server.tool(
    {
      name: "greet",
      description: "Generate a personalized greeting card",
      schema: z.object({
        name: z.string().describe("Person's name"),
        style: z.enum(["formal", "casual", "funny"]).default("casual").describe("Greeting style"),
      }),
      widget: {
        name: "greeting",           // Matches resources/greeting/ folder
        invoking: "Creating greeting...",
        invoked: "Greeting ready",
      },
    },
    async ({ name, style }) => {
      const greetings: Record<string, string> = {
        formal: `Dear ${name}, it is a pleasure to make your acquaintance.`,
        casual: `Hey ${name}! What's up? 👋`,
        funny: `${name}! You again? Just kidding, great to see you! 😄`,
      };

      return widget({
        props: { name, style, message: greetings[style], timestamp: new Date().toISOString() },
        output: text(`Greeting for ${name}: ${greetings[style]}`),
      });
    }
  );
}
```

### Step 2: Create the Server Entry Point

```typescript
// src/server.ts
import { MCPServer } from "mcp-use/server";
import { registerGreetTools } from "./tools/greet.js";

const server = new MCPServer({
  name: "my-mcp-app",
  version: "1.0.0",
  description: "My first MCP App with widgets",
});

registerGreetTools(server);

await server.listen();
```

### Step 3: Create the Widget Component

```tsx
// resources/greeting/widget.tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays a personalized greeting card with style variants",
  props: z.object({
    name: z.string(),
    style: z.enum(["formal", "casual", "funny"]),
    message: z.string(),
    timestamp: z.string(),
  }),
  metadata: { prefersBorder: true },
};

interface GreetingProps {
  name: string;
  style: "formal" | "casual" | "funny";
  message: string;
  timestamp: string;
}

const styleConfig = {
  formal: { bg: "bg-indigo-50 dark:bg-indigo-950", border: "border-indigo-200 dark:border-indigo-800", icon: "🎩" },
  casual: { bg: "bg-green-50 dark:bg-green-950", border: "border-green-200 dark:border-green-800", icon: "👋" },
  funny: { bg: "bg-amber-50 dark:bg-amber-950", border: "border-amber-200 dark:border-amber-800", icon: "😄" },
};

function GreetingContent() {
  const { props, isPending, theme } = useWidget<GreetingProps>();

  if (isPending) {
    return (
      <div className="animate-pulse p-6 space-y-3">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
      </div>
    );
  }

  const config = styleConfig[props.style] ?? styleConfig.casual;

  return (
    <div className={`p-6 rounded-lg border ${config.bg} ${config.border}`}>
      <div className="text-4xl mb-3">{config.icon}</div>
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">
        Hello, {props.name}!
      </h2>
      <p className="mt-2 text-gray-700 dark:text-gray-300">{props.message}</p>
      <p className="mt-4 text-xs text-gray-400">
        {new Date(props.timestamp).toLocaleString()}
      </p>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <GreetingContent />
    </McpUseProvider>
  );
}
```

---

## 6. Development Workflow

```bash
npm run dev
# or: npx mcp-use dev src/server.ts
```

This starts the server with:

- **Hot Module Reloading (HMR)** — edit tools or widgets and changes apply instantly
- **Built-in Inspector** — at `http://localhost:3000/inspector`
- **MCP endpoint** — at `http://localhost:3000/mcp`
- **Type generation** — auto-generates `.mcp-use/tool-registry.d.ts` for typed tool calls

### Testing Your Widget in the Inspector

1. Open `http://localhost:3000/inspector` in your browser
2. Find the "greet" tool in the tools list
3. Enter parameters: `{ "name": "Alice", "style": "casual" }`
4. Click **Run** — the greeting widget renders below
5. Edit `widget.tsx` — the widget hot-reloads instantly

### HMR Behavior

| Action | Effect |
|--------|--------|
| Edit widget component | Widget reloads in Inspector |
| Edit tool handler | New handler takes effect immediately |
| Add/remove widget | Widget list updates in connected clients |
| Edit widgetMetadata | Metadata refreshed on next tool call |

---

## 7. Adding Interactivity

Make your widget interactive with `useCallTool`:

```tsx
// Update resources/greeting/widget.tsx
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";

function GreetingContent() {
  const { props, isPending, theme } = useWidget<GreetingProps>();
  const { callTool: regreet, isPending: regenerating } = useCallTool("greet");

  if (isPending) return <div className="animate-pulse p-6">Loading...</div>;

  const config = styleConfig[props.style] ?? styleConfig.casual;

  return (
    <div className={`p-6 rounded-lg border ${config.bg} ${config.border}`}>
      <div className="text-4xl mb-3">{config.icon}</div>
      <h2 className="text-xl font-bold">{props.message}</h2>

      <div className="flex gap-2 mt-4">
        {(["formal", "casual", "funny"] as const).map((style) => (
          <button
            key={style}
            onClick={() => regreet({ name: props.name, style })}
            disabled={regenerating}
            className={`px-3 py-1 text-sm rounded capitalize ${
              props.style === style
                ? "bg-blue-500 text-white"
                : "bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600"
            }`}
          >
            {style}
          </button>
        ))}
      </div>
    </div>
  );
}
```

Now users can switch greeting styles by clicking buttons — each click calls the `greet` tool with a different style.

---

## 8. Testing Your Server

### Built-in Inspector (recommended)

Open `http://localhost:3000/inspector` to browse tools, invoke them, and see widget rendering.

### curl

```bash
# List tools
curl http://localhost:3000/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Call the greet tool
curl http://localhost:3000/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0","id":2,
    "method":"tools/call",
    "params":{"name":"greet","arguments":{"name":"Alice","style":"casual"}}
  }'
```

### Standalone MCP Inspector

```bash
npx @modelcontextprotocol/inspector
```

Set transport to **Streamable HTTP**, enter `http://localhost:3000/mcp`, and click **Connect**.

---

## 9. Connecting to Claude Desktop

Start your server (`npm run dev`), then edit Claude Desktop's config:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-app": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

Restart Claude Desktop. Ask: "Greet Alice in a funny style" — the greeting widget renders inline.

---

## 10. Building for Production

```bash
npm run build    # npx mcp-use build
npm run start    # npx mcp-use start
```

The production build bundles widgets, optimizes assets, and serves the MCP endpoint without HMR overhead.

---

## 11. Next Steps

- **[Widget Components](./widget-components.md)** — Complete API for useWidget, useCallTool, McpUseProvider
- **[Streaming and Preview](./streaming-and-preview.md)** — Live preview with streaming tool arguments
- **[ChatGPT Apps Flow](./chatgpt-apps-flow.md)** — Deploy widgets for ChatGPT
- **[MCP Apps Patterns](../patterns/mcp-apps-patterns.md)** — Production patterns for widgets
- **[Widget Recipes](../examples/widget-recipes.md)** — Complete widget examples (weather, kanban, forms)
- **[Tools Guide](./tools-and-schemas.md)** — Advanced tool patterns, streaming responses
- **[Authentication](./authentication.md)** — OAuth providers, token validation
- **[Deployment](../patterns/deployment.md)** — Docker, edge runtimes, cloud platforms
