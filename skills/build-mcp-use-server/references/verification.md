# Verification & Testing

*Authoritative verification workflow for mcp-use v2 servers and ChatGPT MCP Apps.*

Official documentation:
- [CLI Reference](https://docs.mcp-use.com/v2/typescript/api-reference/cli-reference)
- [Client CLI Guide](https://docs.mcp-use.com/v2/typescript/tooling/client-cli)
- [Tunneling Guide](https://docs.mcp-use.com/tunneling)

---

## 1. Static Checks

Always verify types and production builds before committing or deploying:

```bash
# Refresh MCP view types and run TypeScript compiler
npx mcp-use typecheck

# Build server bundle and Vite view assets
npx mcp-use build
```

---

## 2. Server & Capability Checks

Start the development server with live reload and Inspector:

```bash
# Terminal 1: Start dev server
npx mcp-use dev
# Or with a public authenticated tunnel for testing in live ChatGPT:
npx mcp-use dev --tunnel
```

Use the built-in `mcp-use client` CLI to verify protocol capabilities:

```bash
# Terminal 2: Save and connect local endpoint
npx mcp-use client connect dev http://localhost:3000/mcp

# List discovered tools
npx mcp-use client dev tools list

# Describe tool schema and metadata
npx mcp-use client dev tools describe lookup-inventory

# Call tool with arguments (key=value or JSON string)
npx mcp-use client dev tools call lookup-inventory sku=SKU-100
npx mcp-use client dev tools call lookup-inventory '{"sku": "SKU-100"}'

# Interactive REPL session
npx mcp-use client dev interactive
```

---

## 3. View Verification & Automated Screenshots

Verify React View rendering, theme adaptation, and data flow. Capture visual screenshots of view-backed tools:

```bash
npx mcp-use screenshot --server dev --tool show-product sku=SKU-100
```

Verify in the Inspector (`http://localhost:3000/mcp/inspector`):
- Pending skeleton states while tool execution is in flight.
- Ready state with correct `toolOutput` rendering.
- Error state when `isError: true` or tool execution is cancelled (`ToolCancelledError`).
- Theme switching between light and dark (`[data-theme]`).
- Responsive layouts across mobile (`xs`, `sm`) and desktop (`md`, `lg`, `xl`).

---

## 4. Advanced & Security Verification

- **Mixed Auth**: Verify public tools work without token; verify protected tools fail with `401` or require sign-in.
- **Elicitation**: Test multi-round interactive prompt, user accept, decline, and cancel paths.
- **Skills over MCP**: Verify `skills/list` advertises conventional skills and `mcp-use build` embeds the catalog without errors.
