# Project Setup

Scaffold a new TypeScript MCP server project from scratch.

Target Node.js 20+ for v2 work. The upstream `main` branch is pre-alpha today, so pin versions deliberately if you are building against v2 before the stable release.

## Step 0: Check Runtime

```bash
node --version
```

## Directory Structure

```
my-mcp-server/
├── src/
│   ├── index.ts          # Server entry point
│   ├── tools/            # Tool implementations
│   │   └── search.ts
│   └── resources/        # Resource providers
│       └── config.ts
├── package.json
├── tsconfig.json
├── .gitignore
└── .env.example
```

## Step 1: Initialize

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
```

## Step 2: Install Dependencies

```bash
# Core
npm install @modelcontextprotocol/server zod

# For HTTP transport (if needed)
npm install @modelcontextprotocol/node
npm install @modelcontextprotocol/express express
npm install -D @types/express

# Dev tooling
npm install -D typescript tsx @types/node
```

## Step 3: Configure package.json

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "dev": "tsx --watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "inspect": "npx @modelcontextprotocol/inspector tsx src/index.ts"
  }
}
```

## Step 4: Configure TypeScript

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true
  },
  "include": ["src"]
}
```

## Step 5: Create .gitignore

```
node_modules/
dist/
.env
```

## Step 6: Create .env.example

```bash
# Add your environment variables here
# API_KEY=your-api-key
# DATABASE_URL=postgres://...
```

## Step 7: Wire the Entry Point

```typescript
// src/index.ts
import { McpServer } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server/stdio';
import { z } from 'zod/v4';

const server = new McpServer({
  name: 'my-mcp-server',
  version: '1.0.0',
});

// Register your tools, resources, and prompts here
// See references/tools.md, references/resources.md, references/prompts.md

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Step 8: Test with Inspector

```bash
npx @modelcontextprotocol/inspector tsx src/index.ts
```

The Inspector opens a browser UI where you can list tools, call them with test inputs, and verify responses.

## Step 9: Add to Claude Desktop

```json
{
  "mcpServers": {
    "my-mcp-server": {
      "command": "npx",
      "args": ["-y", "tsx", "/absolute/path/to/src/index.ts"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

Config file locations:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`

## Environment Variables

Always pass secrets via `env` in the config, never hardcode in `args`:

```json
{
  "command": "node",
  "args": ["dist/index.js"],
  "env": {
    "DATABASE_URL": "postgres://...",
    "API_KEY": "sk-..."
  }
}
```

## Production Build

For npm-published servers, use `npx -y` for zero-install execution:

```json
{
  "command": "npx",
  "args": ["-y", "@myorg/my-mcp-server"],
  "env": {}
}
```
