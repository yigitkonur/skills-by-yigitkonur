# Quick Start

Complete reference for getting started with the mcp-use client — installation, first connection, and basic usage patterns.

---

## Table of Contents

1. [Installation](#installation)
2. [Entry Point Comparison](#entry-point-comparison)
3. [Minimal Node.js Client (STDIO)](#minimal-nodejs-client-stdio)
4. [HTTP Client](#http-client)
5. [Browser Client](#browser-client)
6. [React Client](#react-client)
7. [CLI Quick Start](#cli-quick-start)
8. [Loading Configuration](#loading-configuration)
9. [Project Structure](#project-structure)
10. [Common First Steps After Connection](#common-first-steps-after-connection)
11. [Package Configuration](#package-configuration)
12. [Common Mistakes](#common-mistakes)
13. [Next Steps](#next-steps)

---

## Installation

Install the `mcp-use` package from npm. This single package provides Node.js, browser, and React entry points. Node.js 18+ is supported; Node 22 LTS is the best default when you want parity with current examples.

```bash
npm install mcp-use
```

If you want to run the TypeScript examples directly with `tsx`, also add a TypeScript runner unless the repo already has one:

```bash
npm install -D tsx typescript
```

For yarn or pnpm:

```bash
yarn add mcp-use
```

```bash
pnpm add mcp-use
```

> **Note:** Do NOT install `@modelcontextprotocol/sdk` directly. The `mcp-use` package re-exports everything you need. Importing from `@modelcontextprotocol/sdk` will cause version conflicts and bundling issues.

---

## Entry Point Comparison

Choose the correct import based on your runtime environment. Each entry point exposes a tailored API surface.

| Feature            | Node.js (`mcp-use`)     | Browser (`mcp-use/browser`) | React (`mcp-use/react`) | CLI (`npx mcp-use`)     |
| ------------------ | ----------------------- | --------------------------- | ----------------------- | ----------------------- |
| **Import**         | `import { MCPClient } from 'mcp-use'` | `import { MCPClient } from 'mcp-use/browser'` | `import { useMcp } from 'mcp-use/react'` | N/A (shell command) |
| **Transport**      | STDIO + HTTP            | HTTP only                   | HTTP only               | STDIO + HTTP            |
| **Use Case**       | Backend services, scripts, agents | Frontend web apps     | React components        | Interactive exploration |
| **OAuth Support**  | Yes                     | Yes                         | Yes                     | Yes                     |
| **File System**    | Yes                     | No                          | No                      | Yes                     |
| **Code Mode**      | Yes                     | No                          | No                      | Yes                     |
| **Session Mgmt**   | Manual                  | Manual                      | Automatic (hook)        | Automatic               |

---

## Minimal Node.js Client (STDIO)

Use the Node.js entry point to connect to a local MCP server over STDIO. This is the most common pattern for backend scripts and AI agent integrations.

### Full Example

```typescript
import { MCPClient } from 'mcp-use'

async function main(): Promise<void> {
  // 1. Create the client with server configuration
  const client = new MCPClient({
    mcpServers: {
      'my-server': {
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-everything']
      }
    }
  })

  // 2. Initialize all server sessions
  await client.createAllSessions()

  // 3. Get a specific session by server name
  const session = client.requireSession('my-server')

  // 4. Discover available tools
  const tools = await session.listTools()
  console.log('Available tools:', tools)

  // 5. Call a tool with parameters
  const result = await session.callTool('greet-user', { name: 'Ada', formal: false })
  // result.content is an array of TextContent | ImageContent | EmbeddedResource
  console.log('Result:', result.content)

  // 6. Always clean up sessions when done
  await client.closeAllSessions()
}

main().catch(console.error)
```

Save the first Node example as `src/client.ts` or `src/mcp-client.ts`. Both are conventional; prefer the one that matches the repo's existing naming, then keep your `npm start` script and `tsx` command aligned with that filename.

### How It Works

1. **`MCPClient` constructor** — accepts a configuration object (or a path to a JSON config file) with one or more named servers. Each STDIO server requires `command` and `args`. An optional second argument (`MCPClientOptions`) sets global defaults such as `clientInfo`, `onSampling`, `onElicitation`, and `onNotification`.
2. **`createAllSessions()`** — spawns all configured server processes and establishes communication channels. Returns a `Promise<Record<string, MCPSession>>`. This must complete before calling `getSession()`.
3. **`getSession(name)`** — retrieves the active session for the named server. Returns `MCPSession | null` — returns `null` if the session does not exist. Use `requireSession(name)` if you want an error thrown when the session is missing.
4. **`listTools()`** — queries the server for its advertised tool definitions. Returns a `Promise<Tool[]>` where each element has `name`, `description`, and `inputSchema`.
5. **`callTool(name, args)`** — invokes a tool by name with the provided arguments. Returns a `Promise<CallToolResult>` with `content` and `isError` fields.
6. **`closeAllSessions()`** — terminates all server processes and cleans up resources. Always call this to avoid orphaned processes.

> **Note:** Some environments print an anonymized telemetry banner the first time `mcp-use` runs. That message is informational and does not block the client.

### STDIO Server Configuration Parameters

| Parameter     | Type       | Required | Description                                         |
| ------------- | ---------- | -------- | --------------------------------------------------- |
| `command`     | `string`   | Yes      | The executable to run (e.g., `'npx'`, `'node'`)     |
| `args`        | `string[]` | Yes      | Command-line arguments passed to the executable      |
| `env`         | `Record<string, string>` | No | Environment variables for the server process |
| `clientInfo`  | `ClientInfo` | No     | Overrides default client metadata sent on `initialize` |

---

## HTTP Client

Connect to a remote MCP server over HTTP or HTTPS. Use this when the server runs as a standalone web service.

### Full Example

```typescript
import { MCPClient } from 'mcp-use'

async function main(): Promise<void> {
  const client = new MCPClient({
    mcpServers: {
      'remote-server': {
        url: 'http://localhost:3000/mcp',
        headers: {
          Authorization: 'Bearer YOUR_TOKEN'
        }
      }
    }
  })

  await client.createAllSessions()
  const session = client.requireSession('remote-server')

  // Discover tools
  const tools = await session.listTools()
  console.log('Remote tools:', tools.map(t => t.name))

  // Call a tool
  const result = await session.callTool('search', { query: 'hello world' })
  console.log('Search result:', result)

  await client.closeAllSessions()
}

main().catch(console.error)
```

### HTTP Server Configuration Parameters

| Parameter    | Type                      | Required | Description                                        |
| ------------ | ------------------------- | -------- | -------------------------------------------------- |
| `url`        | `string`                  | Yes      | Full URL of the MCP server endpoint                |
| `headers`    | `Record<string, string>`  | No       | Custom headers sent with every request             |
| `clientInfo` | `ClientInfo`              | No       | Overrides default client metadata sent on `initialize` |

> **Transport note:** HTTP servers use the unified "Streamable HTTP" transport (`POST /mcp` + `GET /mcp`). The legacy SSE transport (separate POST and SSE endpoints) is **deprecated** and should not be used for new integrations.

### ClientInfo Type

Both STDIO and HTTP server configurations accept an optional `clientInfo` field that overrides the default client metadata sent during the MCP `initialize` handshake. The same type is accepted at the root `options` level as a fallback for all servers.

| Property      | Type       | Required | Description                                     |
| ------------- | ---------- | -------- | ----------------------------------------------- |
| `name`        | `string`   | Yes      | Identifier of the client                        |
| `version`     | `string`   | Yes      | Semantic version string                         |
| `title`       | `string`   | No       | Human-readable display name                     |
| `description` | `string`   | No       | Free-form description                           |
| `icons`       | `Icon[]`   | No       | Array of icon objects (`src`, `mimeType`, `sizes`) |
| `websiteUrl`  | `string`   | No       | URL to the client's website                     |

### Root-Level Options (Second Constructor Argument)

`MCPClient` accepts an optional second argument — `MCPClientOptions` — that sets global defaults applied to all servers:

```typescript
import { acceptWithDefaults, MCPClient } from 'mcp-use'

const client = new MCPClient(
  {
    mcpServers: {
      'my-server': {
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-everything']
      }
    }
  },
  {
    clientInfo: {
      name: 'my-client',
      version: '1.0.0'
    },
    onElicitation: acceptWithDefaults,
    onNotification: (notification) => {
      console.log('Server notification:', notification)
    }
  }
)
```

| Option           | Type                                                                                            | Required | Description                                               |
| ---------------- | ----------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------- |
| `clientInfo`     | `ClientInfo`                                                                                    | No       | Fallback metadata for servers without their own `clientInfo` |
| `onSampling`     | `(params: CreateMessageRequest["params"]) => Promise<CreateMessageResult>`                      | No       | Default sampling callback for all servers                 |
| `onElicitation`  | `(params: ElicitRequestFormParams \| ElicitRequestURLParams) => Promise<ElicitResult>`          | No       | Default elicitation callback; use `acceptWithDefaults` for a no-op |
| `onNotification` | `(notification: Notification) => void \| Promise<void>`                                        | No       | Default notification handler for all servers              |
| `codeMode`       | `boolean \| CodeModeConfig`                                                                     | No       | Enable code execution mode (Node.js only). `true` uses the default VM executor. |

### Multiple Servers

Connect to multiple servers simultaneously. Each server gets its own session.

```typescript
import { MCPClient } from 'mcp-use'

const client = new MCPClient({
  mcpServers: {
    'search-api': {
      url: 'https://search.example.com/mcp',
      headers: { Authorization: 'Bearer SEARCH_TOKEN' }
    },
    'database-api': {
      url: 'https://db.example.com/mcp',
      headers: { Authorization: 'Bearer DB_TOKEN' }
    },
    'local-tools': {
      command: 'node',
      args: ['./my-local-server.js']
    }
  }
})

await client.createAllSessions()

const searchSession = client.requireSession('search-api')
const dbSession = client.requireSession('database-api')
const localSession = client.requireSession('local-tools')

// Use each session independently
const searchTools = await searchSession.listTools()
const dbTools = await dbSession.listTools()
const localTools = await localSession.listTools()

await client.closeAllSessions()
```

---

## Browser Client

Use `mcp-use/browser` for frontend web applications. The browser entry point strips out STDIO, file system, and code mode capabilities — HTTP transport only.

### Full Example

```typescript
import { MCPClient } from 'mcp-use/browser'

async function connectToServer(): Promise<void> {
  const client = new MCPClient({
    mcpServers: {
      myServer: {
        url: 'https://api.example.com/mcp',
        headers: {
          Authorization: 'Bearer YOUR_TOKEN'
        }
      }
    }
  })

  await client.createAllSessions()
  const session = client.requireSession('myServer')

  // Call a tool
  const result = await session.callTool('tool_name', { param: 'value' })
  console.log('Result:', result.content) // array of content items

  await client.closeAllSessions()
}
```

### Browser Limitations

The browser environment imposes hard constraints. Know these before choosing the browser entry point.

| Capability      | Available | Reason                                    |
| --------------- | --------- | ----------------------------------------- |
| HTTP Transport  | ✅ Yes    | Fetch API available in all browsers       |
| STDIO Transport | ❌ No     | No child process spawning in browsers     |
| File System     | ❌ No     | No `fs` module in browsers                |
| Code Mode       | ❌ No     | No `child_process.exec` in browsers       |
| OAuth           | ✅ Yes    | Redirect-based OAuth flows supported      |

❌ **BAD** — Attempting STDIO in the browser:

```typescript
// This will throw an error at runtime
import { MCPClient } from 'mcp-use/browser'

const client = new MCPClient({
  mcpServers: {
    'local-server': {
      command: 'npx',  // STDIO is not available in browsers
      args: ['-y', '@modelcontextprotocol/server-everything']
    }
  }
})
```

✅ **GOOD** — Using HTTP transport in the browser:

```typescript
import { MCPClient } from 'mcp-use/browser'

const client = new MCPClient({
  mcpServers: {
    'remote-server': {
      url: 'https://api.example.com/mcp',
      headers: { Authorization: 'Bearer YOUR_TOKEN' }
    }
  }
})
```

---

## React Client

The `useMcp` hook manages the full connection lifecycle inside a React component. It handles session creation, state transitions, and cleanup automatically on unmount.

The `useMcp` hook accepts the following options:

| Option          | Type                          | Required | Description                                                    |
| --------------- | ----------------------------- | -------- | -------------------------------------------------------------- |
| `url`           | `string`                      | Yes      | Base URL of the MCP server                                     |
| `headers`       | `Record<string, string>`      | No       | Custom headers sent with every request                         |
| `transportType` | `'auto' \| 'http' \| 'sse'`  | No       | Transport protocol. Defaults to `'auto'`. **`'sse'` is deprecated** — use `'http'` or `'auto'`. |

### Full Example

```typescript
import { useMcp } from 'mcp-use/react'

function MyComponent() {
  const mcp = useMcp({
    url: 'https://api.example.com/mcp',
    headers: {
      Authorization: 'Bearer YOUR_API_KEY'
    }
  })

  if (mcp.state !== 'ready') return <div>Connecting...</div>

  return (
    <div>
      <h2>Available Tools</h2>
      <ul>
        {mcp.tools.map((tool) => (
          <li key={tool.name}>
            {tool.name}: {tool.description}
          </li>
        ))}
      </ul>
    </div>
  )
}
```

### Connection States

The `mcp.state` property transitions through these values during the connection lifecycle. Handle each state in your UI.

| State              | Description                                        | Action                          |
| ------------------ | -------------------------------------------------- | ------------------------------- |
| `discovering`      | Connecting to the server and negotiating protocol   | Show a loading spinner          |
| `authenticating`   | Running OAuth or token exchange                     | Show authentication progress    |
| `pending_auth`     | Waiting for user to complete OAuth redirect         | Show "Complete login" prompt    |
| `ready`            | Fully connected, tools and resources available      | Render the main UI              |
| `failed`           | Connection failed or server unreachable             | Show error message with retry   |

### Handling All States

```typescript
import { useMcp } from 'mcp-use/react'

function RobustMcpComponent() {
  const mcp = useMcp({
    url: 'https://api.example.com/mcp',
    headers: { Authorization: 'Bearer YOUR_API_KEY' }
  })

  switch (mcp.state) {
    case 'discovering':
      return <div>Discovering server capabilities...</div>
    case 'authenticating':
      return <div>Authenticating...</div>
    case 'pending_auth':
      return <div>Please complete authentication in the popup window.</div>
    case 'failed':
      return <div>Connection failed. Check your server URL and credentials.</div>
    case 'ready':
      return (
        <div>
          <p>Connected! Found {mcp.tools.length} tools.</p>
          <ul>
            {mcp.tools.map((tool) => (
              <li key={tool.name}>{tool.name}</li>
            ))}
          </ul>
        </div>
      )
  }
}
```

### Calling Tools from React

```typescript
import { useMcp } from 'mcp-use/react'
import { useState } from 'react'

function ToolCaller() {
  const mcp = useMcp({
    url: 'https://api.example.com/mcp',
    headers: { Authorization: 'Bearer YOUR_API_KEY' }
  })
  const [result, setResult] = useState<unknown>(null)

  async function handleCallTool(toolName: string): Promise<void> {
    if (mcp.state !== 'ready') return
    const response = await mcp.callTool(toolName, { param: 'value' })
    setResult(response)
  }

  if (mcp.state !== 'ready') return <div>Connecting...</div>

  return (
    <div>
      {mcp.tools.map((tool) => (
        <button key={tool.name} onClick={() => handleCallTool(tool.name)}>
          Call {tool.name}
        </button>
      ))}
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  )
}
```

---

## CLI Quick Start

The `mcp-use` CLI provides interactive exploration of MCP servers without writing code. Use it to test servers, inspect tool schemas, and run ad-hoc tool calls.

### Connect to a Server

Connect via HTTP:

```bash
npx mcp-use client connect http://localhost:3000/mcp --name my-server
```

Connect via STDIO:

```bash
npx mcp-use client connect --stdio "npx -y @modelcontextprotocol/server-filesystem /tmp" --name fs
```

### List and Call Tools

List all available tools across connected servers:

```bash
npx mcp-use client tools list
```

Call a specific tool with JSON arguments:

```bash
npx mcp-use client tools call read_file '{"path": "/tmp/test.txt"}'
```

### Interactive Mode

Enter an interactive REPL session for exploratory use:

```bash
npx mcp-use client interactive
```

Inside interactive mode, type tool names and provide arguments interactively. Use `help` to see available commands and `exit` to quit.

### CLI Command Reference

| Command                                  | Description                                |
| ---------------------------------------- | ------------------------------------------ |
| `client connect <url> --name <n>`        | Connect to an HTTP MCP server              |
| `client connect --stdio "<cmd>" --name <n>` | Connect to a STDIO MCP server           |
| `client tools list`                      | List all tools from all connected servers  |
| `client tools call <name> '<json>'`      | Call a tool with JSON arguments            |
| `client interactive`                     | Enter interactive REPL mode                |
| `client disconnect --name <n>`           | Disconnect from a named server             |

---

## Loading Configuration

There are three convenient ways to load a JSON configuration file. The simplest is to pass the file path directly to the constructor. You can also use `MCPClient.fromConfigFile()` as a convenience factory, or use the `loadConfigFile()` named export when you want to inspect or modify the parsed object before constructing the client.

### From a Config File (via constructor path string)

Pass the file path as a string directly to the `MCPClient` constructor:

```typescript
import { MCPClient } from 'mcp-use'

const client = new MCPClient('path/to/config.json')
await client.createAllSessions()
```

### From a Config File (via `MCPClient.fromConfigFile`)

Use the convenience factory when you want explicit "load from file" intent without manually calling `loadConfigFile()`:

```typescript
import { MCPClient } from 'mcp-use'

const client = MCPClient.fromConfigFile('path/to/config.json')
await client.createAllSessions()
```

### From a Config File (via `loadConfigFile`)

Load and parse the config file manually with `loadConfigFile`, then pass it to the constructor:

```typescript
import { MCPClient, loadConfigFile } from 'mcp-use'

const config = loadConfigFile('path/to/config.json')
const client = new MCPClient(config)
await client.createAllSessions()
```

The config file format matches the constructor's `mcpServers` structure:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    },
    "remote-api": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### From a Dictionary

Pass a pre-built configuration object directly to the constructor:

```typescript
import { MCPClient } from 'mcp-use'

const config = {
  mcpServers: {
    'my-server': {
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-everything']
    }
  }
}

const client = new MCPClient(config)
await client.createAllSessions()
```

This is useful when configuration comes from environment variables, a database, or another dynamic source.

---

## Project Structure

Organize a new mcp-use client project with this recommended layout:

```
my-mcp-client/
├── src/
│   └── client.ts         # Client entry point
├── package.json
├── tsconfig.json
└── README.md
```

### Minimal `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

### Minimal `package.json`

```json
{
  "name": "my-mcp-client",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "start": "tsx src/client.ts",
    "build": "tsc"
  },
  "dependencies": {
    "mcp-use": "latest"
  },
  "devDependencies": {
    "tsx": "latest",
    "typescript": "latest"
  }
}
```

---

## Common First Steps After Connection

Once a session is established, these are the core operations available on every session object. Use them to explore the server's capabilities before building higher-level logic.

### List Tools

Retrieve all tool definitions the server exposes:

```typescript
const tools = await session.listTools()
for (const tool of tools) {
  console.log(`${tool.name}: ${tool.description}`)
  console.log('  Schema:', JSON.stringify(tool.inputSchema, null, 2))
}
```

### Call a Tool

Invoke a tool by name with a parameter object that matches its `inputSchema`:

```typescript
const result = await session.callTool('read_file', { path: '/tmp/example.txt' })
console.log('File contents:', result)
```

### List Resources

Discover static resources the server provides. `listResources()` supports pagination via a cursor; use `listAllResources()` to retrieve the full list in one call:

```typescript
// Paginated (one page at a time)
const page = await session.listResources()
for (const resource of page.resources) {
  console.log(`${resource.name}: ${resource.uri}`)
}

// All resources without pagination
const all = await session.listAllResources()
for (const resource of all.resources) {
  console.log(`${resource.name}: ${resource.uri}`)
}
```

### Read a Resource

Fetch the contents of a specific resource by URI:

```typescript
const content = await session.readResource('file:///tmp/example.txt')
console.log('Resource content:', content)
```

### List Prompts

Retrieve prompt templates the server offers:

```typescript
const prompts = await session.listPrompts()
for (const prompt of prompts) {
  console.log(`${prompt.name}: ${prompt.description}`)
}
```

### Get a Prompt

Render a specific prompt template with arguments:

```typescript
const prompt = await session.getPrompt('summarize', {
  text: 'The quick brown fox jumps over the lazy dog.'
})
console.log('Rendered prompt:', prompt)
```

### Cleanup

Always close sessions when the client is no longer needed:

```typescript
await client.closeAllSessions()
```

---

## Package Configuration

Reference table for `package.json` fields relevant to mcp-use client projects.

| Field                     | Value              | Purpose                                           |
| ------------------------- | ------------------ | ------------------------------------------------- |
| `"type"`                  | `"module"`         | Enable ESM imports (required for `mcp-use`)       |
| `"dependencies.mcp-use"`  | `"latest"`         | The mcp-use client library                        |
| `"devDependencies.tsx"`   | `"latest"`         | TypeScript execution without compilation step     |
| `"devDependencies.typescript"` | `"latest"`    | TypeScript compiler for type checking and builds  |
| `"scripts.start"`         | `"tsx src/client.ts"` | Run the client directly during development      |
| `"scripts.build"`         | `"tsc"`            | Compile TypeScript to JavaScript for production   |

---

## Common Mistakes

Avoid these pitfalls when building mcp-use clients.

### Session Lifecycle Errors

❌ **BAD** — Calling `getSession()` before `createAllSessions()` and not checking for `null`:

```typescript
import { MCPClient } from 'mcp-use'

const client = new MCPClient({
  mcpServers: {
    'my-server': { command: 'npx', args: ['-y', '@modelcontextprotocol/server-everything'] }
  }
})

// getSession() returns null when no session exists — calling methods on null throws
const session = client.getSession('my-server') // returns null
await session!.listTools() // TypeError: Cannot read properties of null
```

✅ **GOOD** — Always call `createAllSessions()` or `createSession()` before accessing any session. Use `requireSession()` if you want an explicit error when a session is missing:

```typescript
import { MCPClient } from 'mcp-use'

const client = new MCPClient({
  mcpServers: {
    'my-server': { command: 'npx', args: ['-y', '@modelcontextprotocol/server-everything'] }
  }
})

await client.createAllSessions()

// Option 1: getSession returns null — check before use
const session = client.getSession('my-server')
if (session) {
  const tools = await session.listTools()
}

// Option 2: requireSession throws if not found — use when session must exist
const session2 = client.requireSession('my-server')
const tools = await session2.listTools()
```

### Missing Cleanup

❌ **BAD** — Not calling `closeAllSessions()`, leaving orphaned server processes:

```typescript
import { MCPClient } from 'mcp-use'

const client = new MCPClient({
  mcpServers: {
    'my-server': { command: 'npx', args: ['-y', '@modelcontextprotocol/server-everything'] }
  }
})

await client.createAllSessions()
const session = client.requireSession('my-server')
const tools = await session.listTools()
// Process exits without cleanup — server process is orphaned
```

✅ **GOOD** — Always close sessions, even on error. Use try/finally:

```typescript
import { MCPClient } from 'mcp-use'

const client = new MCPClient({
  mcpServers: {
    'my-server': { command: 'npx', args: ['-y', '@modelcontextprotocol/server-everything'] }
  }
})

try {
  await client.createAllSessions()
  const session = client.requireSession('my-server')
  const tools = await session.listTools()
  console.log('Tools:', tools)
} finally {
  await client.closeAllSessions()
}
```

### Wrong Transport for Environment

❌ **BAD** — Using STDIO transport in a browser environment:

```typescript
import { MCPClient } from 'mcp-use/browser'

// STDIO is not available in browsers — this will fail
const client = new MCPClient({
  mcpServers: {
    'local-server': {
      command: 'node',
      args: ['./server.js']
    }
  }
})
```

✅ **GOOD** — Using HTTP transport in the browser, STDIO in Node.js:

```typescript
// Browser — use HTTP
import { MCPClient } from 'mcp-use/browser'

const browserClient = new MCPClient({
  mcpServers: {
    'api-server': {
      url: 'https://api.example.com/mcp',
      headers: { Authorization: 'Bearer TOKEN' }
    }
  }
})
```

```typescript
// Node.js — STDIO or HTTP both work
import { MCPClient } from 'mcp-use'

const nodeClient = new MCPClient({
  mcpServers: {
    'local-server': {
      command: 'node',
      args: ['./server.js']
    }
  }
})
```

### Wrong Import Path

❌ **BAD** — Importing from `@modelcontextprotocol/sdk` directly:

```typescript
// Do NOT do this — causes version conflicts
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
```

✅ **GOOD** — Always import from the `mcp-use` package:

```typescript
import { MCPClient } from 'mcp-use'           // Node.js
import { MCPClient } from 'mcp-use/browser'   // Browser
import { useMcp } from 'mcp-use/react'        // React
```

---

## Next Steps

After completing this quick start, continue with these topics:

- **OAuth & Authentication** — Configure OAuth flows for servers that require user authorization.
- **Error Handling** — Handle transport errors, timeout failures, and server disconnections gracefully.
- **Advanced Patterns** — Dynamic server discovery, session reconnection, and multi-agent architectures.
- **Tool Schema Validation** — Validate tool arguments against `inputSchema` before calling.
- **Resource Subscriptions** — Subscribe to resource changes for real-time updates from the server.
