# Scenario Library

Complete example configurations for common repository types. Use as inspiration, but adapt every rule to the actual repository context — never copy verbatim.

---

## Scenario A: TypeScript Backend API

### `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "triggerOnUpdates": false,
  "ignorePatterns": "*.generated.*\ndist/**\nnode_modules/**\n**/__snapshots__/**\npackage-lock.json\n*.d.ts\n**/migrations/**",
  "excludeAuthors": ["dependabot[bot]", "renovate[bot]"],
  "includeBranches": ["main", "develop", "staging"],
  "excludeBranches": ["draft/**"],
  "fileChangeLimit": 75,
  "patternRepositories": ["acme/shared-utils", "acme/api-contracts"],
  "rules": [
    {
      "id": "no-raw-sql",
      "rule": "Use parameterized queries via the ORM. Never interpolate user input into SQL strings.",
      "scope": ["src/db/**", "src/repositories/**"],
      "severity": "high"
    },
    {
      "id": "api-rate-limiting",
      "rule": "All API endpoints must have rate limiting middleware. Import from src/middleware/rateLimit.",
      "scope": ["src/api/**/*.ts", "src/routes/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "structured-logging",
      "rule": "Use the structured logger (import from src/utils/logger). Never use console.log/warn/error.",
      "scope": ["src/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "async-error-handling",
      "rule": "All async functions must have try-catch with structured logging. Never swallow errors.",
      "scope": ["src/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "api-response-shape",
      "rule": "API error responses must include: status (number), message (string), timestamp (ISO 8601), requestId (UUID).",
      "scope": ["src/api/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "no-business-logic-in-controllers",
      "rule": "Controllers must only handle HTTP request/response. Business logic belongs in src/services/.",
      "scope": ["src/controllers/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "dependency-injection",
      "rule": "Services must receive dependencies via constructor injection. Never import service instances directly.",
      "scope": ["src/services/**/*.ts"],
      "severity": "medium"
    }
  ],
  "statusCheck": true,
  "updateExistingSummaryComment": true,
  "includeConfidenceScore": true,
  "summarySection": { "included": true, "collapsible": true, "defaultOpen": true },
  "issuesTableSection": { "included": true, "collapsible": true, "defaultOpen": false }
}
```

### `.greptile/files.json`
```json
{
  "files": [
    {
      "path": "docs/architecture.md",
      "description": "System architecture overview"
    },
    {
      "path": "openapi/spec.yaml",
      "description": "API contracts — validate endpoints match spec",
      "scope": ["src/api/**", "src/routes/**"]
    },
    {
      "path": "prisma/schema.prisma",
      "description": "Database schema — validate model relationships",
      "scope": ["src/db/**", "src/repositories/**"]
    }
  ]
}
```

---

## Scenario B: React Frontend (with backend pattern repo)

### `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax", "style"],
  "ignorePatterns": "*.generated.*\nbuild/**\nnode_modules/**\n**/__snapshots__/**\n**/*.stories.tsx\npackage-lock.json",
  "excludeAuthors": ["dependabot[bot]"],
  "patternRepositories": ["acme/backend-api", "acme/design-system"],
  "rules": [
    {
      "id": "api-contract-match",
      "rule": "API calls must match backend endpoint contracts defined in acme/backend-api.",
      "scope": ["src/api/**/*.ts", "src/hooks/use*.ts"],
      "severity": "high"
    },
    {
      "id": "design-system-usage",
      "rule": "Use components from @acme/design-system. Do not create custom UI primitives (buttons, inputs, modals).",
      "scope": ["src/components/**/*.tsx"],
      "severity": "medium"
    },
    {
      "id": "no-direct-dom",
      "rule": "Do not use document.querySelector or direct DOM manipulation. Use React refs.",
      "scope": ["src/**/*.tsx", "src/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "hooks-rules",
      "rule": "Custom hooks must be in src/hooks/ and prefixed with 'use'. Never call hooks conditionally.",
      "scope": ["src/**/*.ts", "src/**/*.tsx"],
      "severity": "high"
    }
  ],
  "statusCheck": true
}
```

---

## Scenario C: Monorepo with Cascading Overrides

### Root `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax", "style"],
  "ignorePatterns": "*.generated.*\ndist/**\nnode_modules/**\npackage-lock.json",
  "excludeAuthors": ["dependabot[bot]"],
  "rules": [
    {
      "id": "no-console-log",
      "rule": "Use structured logger. No console.log/warn/error in production code.",
      "scope": ["src/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "typescript-strict",
      "rule": "All new files must be TypeScript. Do not add new .js files.",
      "scope": ["**/*"],
      "severity": "medium"
    }
  ]
}
```

### `packages/payments/.greptile/config.json`
```json
{
  "strictness": 1,
  "rules": [
    {
      "id": "pci-no-pii-logging",
      "rule": "Never log credit card numbers, CVVs, or full SSNs. Mask all PII in logs.",
      "scope": ["**/*.ts"],
      "severity": "high"
    },
    {
      "id": "payments-idempotency",
      "rule": "All payment mutation endpoints must be idempotent. Require an idempotency key.",
      "scope": ["src/api/**/*.ts"],
      "severity": "high"
    }
  ]
}
```

### `packages/internal-admin/.greptile/config.json`
```json
{
  "strictness": 3,
  "disabledRules": ["no-console-log"]
}
```

---

## Scenario D: Python Django API

### `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "ignorePatterns": "*.pyc\n__pycache__/**\n*.egg-info/**\ndist/**\nbuild/**\n.tox/**\nhtmlcov/**\nmigrations/**\nstatic/**\nmedia/**",
  "excludeAuthors": ["dependabot[bot]"],
  "includeBranches": ["main", "develop"],
  "rules": [
    {
      "id": "no-raw-sql",
      "rule": "Use Django ORM or parameterized raw() calls. Never use string formatting for SQL.",
      "scope": ["**/views.py", "**/models.py", "**/managers.py", "**/queries.py"],
      "severity": "high"
    },
    {
      "id": "no-n-plus-one",
      "rule": "QuerySets used in templates or serializers must use select_related() or prefetch_related() to avoid N+1 queries.",
      "scope": ["**/views.py", "**/serializers.py", "**/viewsets.py"],
      "severity": "high"
    },
    {
      "id": "view-permission-classes",
      "rule": "All API views must declare permission_classes explicitly. Never rely on DEFAULT_PERMISSION_CLASSES alone.",
      "scope": ["**/views.py", "**/viewsets.py"],
      "severity": "high"
    },
    {
      "id": "model-str-method",
      "rule": "All Django models must implement __str__ returning a human-readable representation.",
      "scope": ["**/models.py"],
      "severity": "low"
    },
    {
      "id": "no-print-statements",
      "rule": "Use the logging module. No print() statements in production code.",
      "scope": ["**/*.py"],
      "severity": "medium"
    }
  ],
  "statusCheck": true,
  "updateExistingSummaryComment": true
}
```

---

## Scenario E: Go Microservice

### `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "ignorePatterns": "vendor/**\n*.pb.go\n*_generated.go\nbin/**\nmocks/**",
  "excludeAuthors": ["dependabot[bot]"],
  "rules": [
    {
      "id": "error-wrapping",
      "rule": "Errors must be wrapped with context using fmt.Errorf(\"...: %w\", err). Never return bare errors from functions.",
      "scope": ["**/*.go"],
      "severity": "high"
    },
    {
      "id": "context-propagation",
      "rule": "All functions that do I/O (HTTP, DB, gRPC) must accept context.Context as the first parameter.",
      "scope": ["**/*.go"],
      "severity": "high"
    },
    {
      "id": "no-goroutine-leak",
      "rule": "Every goroutine must have a clear termination path. Use context cancellation or done channels.",
      "scope": ["**/*.go"],
      "severity": "high"
    },
    {
      "id": "structured-logging",
      "rule": "Use the structured logger (slog or zerolog). No log.Println or fmt.Println in production code.",
      "scope": ["**/*.go"],
      "severity": "medium"
    }
  ],
  "statusCheck": true
}
```

---

## Scenario F: Tauri Desktop App (Rust + TypeScript Frontend)

### `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "ignorePatterns": "src-tauri/target/**\nnode_modules/**\ndist/**\n*.generated.*\npackage-lock.json\nyarn.lock\npnpm-lock.yaml\nsrc-tauri/Cargo.lock\n**/*.d.ts",
  "excludeAuthors": ["dependabot[bot]", "renovate[bot]"],
  "includeBranches": ["main", "develop"],
  "rules": [
    {
      "id": "tauri-command-error-handling",
      "rule": "All #[tauri::command] functions must return Result<T, String> or a custom error type. Never panic inside a command handler — panics crash the app. Use ? operator or match/if-let for fallible operations.",
      "scope": ["src-tauri/src/**/*.rs"],
      "severity": "high"
    },
    {
      "id": "tauri-command-input-validation",
      "rule": "All #[tauri::command] parameters that accept user-provided data (strings, paths, IDs) must be validated before use. Never pass unsanitized IPC input directly to file system operations, shell commands, or SQL queries.",
      "scope": ["src-tauri/src/**/*.rs"],
      "severity": "high"
    },
    {
      "id": "tauri-state-mutex-guard",
      "rule": "Shared mutable state accessed via State<Mutex<T>> or State<RwLock<T>> must hold locks for the shortest possible scope. Never hold a lock across an await point — this causes deadlocks. Extract the data, drop the guard, then do async work.",
      "scope": ["src-tauri/src/**/*.rs"],
      "severity": "high"
    },
    {
      "id": "tauri-no-unwrap-in-commands",
      "rule": "Never use .unwrap() or .expect() inside #[tauri::command] handlers. These panic on failure and crash the entire application. Use .map_err() to convert errors to serializable types.",
      "scope": ["src-tauri/src/**/*.rs"],
      "severity": "high"
    },
    {
      "id": "tauri-shell-command-safety",
      "rule": "When using tauri-plugin-shell or std::process::Command, never interpolate user input into command strings. Use argument arrays and validate all paths/arguments against an allowlist.",
      "scope": ["src-tauri/src/**/*.rs"],
      "severity": "high"
    },
    {
      "id": "tauri-invoke-error-handling",
      "rule": "All frontend invoke() calls to Rust commands must handle errors with try-catch or .catch(). Never fire-and-forget an invoke — unhandled IPC errors leave the UI in an inconsistent state.",
      "scope": ["src/**/*.ts", "src/**/*.tsx"],
      "severity": "high"
    },
    {
      "id": "tauri-invoke-type-safety",
      "rule": "Use typed invoke<ReturnType>('command', args) with explicit TypeScript types for both parameters and return values. Never pass untyped objects to invoke.",
      "scope": ["src/**/*.ts", "src/**/*.tsx"],
      "severity": "medium"
    },
    {
      "id": "tauri-no-sensitive-logging",
      "rule": "Never log file paths containing user home directories, API keys, tokens, or other credentials in Rust command handlers. Sanitize before logging.",
      "scope": ["src-tauri/src/**/*.rs"],
      "severity": "high"
    },
    {
      "id": "tauri-capability-scope",
      "rule": "New Tauri commands must be registered in tauri.conf.json capabilities with minimal required permissions. Do not add commands to the default capability — create scoped capabilities per feature.",
      "scope": ["src-tauri/tauri.conf.json", "src-tauri/capabilities/**"],
      "severity": "medium"
    }
  ],
  "statusCheck": true,
  "updateExistingSummaryComment": true,
  "includeConfidenceScore": true,
  "summarySection": { "included": true, "collapsible": true, "defaultOpen": true },
  "issuesTableSection": { "included": true, "collapsible": true, "defaultOpen": false }
}
```

### `.greptile/rules.md`
```markdown
## Tauri Command Safety

Tauri commands are the security boundary between the webview and OS-level operations.
Every command handler must be defensive.

### Error Handling in Commands

Commands must never panic. A panic in a command handler crashes the entire application.

#### Good
\`\`\`rust
#[tauri::command]
async fn read_file(path: String) -> Result<String, String> {
    let content = std::fs::read_to_string(&path)
        .map_err(|e| format!("Failed to read {}: {}", path, e))?;
    Ok(content)
}
\`\`\`

#### Bad
\`\`\`rust
#[tauri::command]
async fn read_file(path: String) -> String {
    std::fs::read_to_string(&path).unwrap() // panics on failure!
}
\`\`\`

### Mutex Lock Scope

Never hold a Mutex guard across an await point.

#### Good
\`\`\`rust
#[tauri::command]
async fn update_state(state: State<'_, Mutex<AppState>>, value: String) -> Result<(), String> {
    let data = {
        let guard = state.lock().map_err(|e| e.to_string())?;
        guard.data.clone()
    }; // guard dropped here
    do_async_work(data).await.map_err(|e| e.to_string())?;
    Ok(())
}
\`\`\`

#### Bad
\`\`\`rust
#[tauri::command]
async fn update_state(state: State<'_, Mutex<AppState>>, value: String) -> Result<(), String> {
    let guard = state.lock().map_err(|e| e.to_string())?;
    do_async_work(guard.data.clone()).await?; // lock held across await!
    Ok(())
}
\`\`\`
```

---

## Scenario G: MCP Server (Model Context Protocol — TypeScript)

### `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "ignorePatterns": "node_modules/**\ndist/**\nbuild/**\npackage-lock.json\nyarn.lock\n*.d.ts\ncoverage/**",
  "excludeAuthors": ["dependabot[bot]"],
  "rules": [
    {
      "id": "mcp-tool-input-validation",
      "rule": "All MCP tool handlers must validate input parameters using Zod schemas that match the advertised inputSchema. Use z.safeParse() and return a structured error (code -32602) on validation failure. Never trust raw parameters.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-tool-response-format",
      "rule": "Tool handler responses must return { content: [{ type: 'text', text: string }] } for success. Error responses must include { code: number, message: string }. Never return raw strings or unstructured objects.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-tool-error-handling",
      "rule": "All tool handlers must be wrapped in try-catch. Caught exceptions must be mapped to MCP error responses with appropriate error codes (-32000 to -32099 for server errors). Never let unhandled exceptions propagate — they crash the server.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-no-command-injection",
      "rule": "Tool handlers that execute shell commands must never interpolate user-provided parameters into command strings. Use child_process.execFile with argument arrays, or a sandboxed execution environment. Reject parameters containing shell metacharacters.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-tool-timeout",
      "rule": "All tool handlers that perform I/O (HTTP requests, file reads, subprocess execution) must enforce a timeout (30s default). Use AbortController or Promise.race with a timeout rejection. Never allow tool execution to hang indefinitely.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-schema-consistency",
      "rule": "The inputSchema declared in tools/list must exactly match the Zod schema used for validation in the tools/call handler. If the schema changes, both must be updated together. Schema mismatches cause silent failures.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-no-secrets-in-logs",
      "rule": "Never log raw tool parameters, API keys, tokens, or file contents. Use structured logging with parameter names only (not values) for debugging. Secrets must never appear in stdout/stderr.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-filesystem-access",
      "rule": "File system operations in tool/resource handlers must validate paths against an allowlist or configured root directory. Reject paths containing '..' or absolute paths outside the allowed scope. Use path.resolve() and check containment.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-resource-pagination",
      "rule": "Resource handlers that return file contents or large datasets must implement pagination or size limits. Never read an entire file into memory without checking size first. Return partial content with a cursor for large resources.",
      "scope": ["src/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "mcp-stdio-flush",
      "rule": "When using stdio transport, ensure every JSON-RPC response is followed by a flush (write + newline). Buffered output blocks the client from receiving responses.",
      "scope": ["src/**/*.ts"],
      "severity": "medium"
    }
  ],
  "statusCheck": true,
  "updateExistingSummaryComment": true,
  "includeConfidenceScore": true
}
```

### `.greptile/rules.md`
```markdown
## MCP Protocol Compliance

MCP servers must strictly follow the JSON-RPC 2.0 + MCP spec for interoperability.

### Tool Handler Pattern

Every tool handler should follow this structure:

#### Good
\`\`\`typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "search_files") {
    const parsed = SearchFilesSchema.safeParse(args);
    if (!parsed.success) {
      return {
        content: [{ type: "text", text: \`Invalid parameters: \${parsed.error.message}\` }],
        isError: true,
      };
    }

    try {
      const result = await searchFiles(parsed.data);
      return {
        content: [{ type: "text", text: JSON.stringify(result) }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: \`Search failed: \${error.message}\` }],
        isError: true,
      };
    }
  }

  throw new McpError(ErrorCode.MethodNotFound, \`Unknown tool: \${name}\`);
});
\`\`\`

#### Bad
\`\`\`typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  // No validation, no error handling, raw parameter usage
  const result = await eval(args.code); // command injection!
  return { content: [{ type: "text", text: result }] };
});
\`\`\`

### File System Safety

Never trust paths from tool parameters.

#### Good
\`\`\`typescript
function resolveAndValidate(basePath: string, relativePath: string): string {
  const resolved = path.resolve(basePath, relativePath);
  if (!resolved.startsWith(basePath)) {
    throw new Error("Path traversal attempt blocked");
  }
  return resolved;
}
\`\`\`

#### Bad
\`\`\`typescript
const content = fs.readFileSync(args.filePath, 'utf-8'); // no validation!
\`\`\`
```

---

## Scenario H: Next.js Marketing / Content Website

### `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "ignorePatterns": "node_modules/**\n.next/**\nout/**\nbuild/**\npackage-lock.json\npnpm-lock.yaml\nyarn.lock\n**/*.d.ts\npublic/**\ncoverage/**",
  "excludeAuthors": ["dependabot[bot]", "renovate[bot]"],
  "includeBranches": ["main", "develop", "staging"],
  "rules": [
    {
      "id": "nextjs-metadata-required",
      "rule": "Every page.tsx and layout.tsx must export a generateMetadata() function or a metadata object. Missing metadata degrades SEO — include at minimum: title, description, and openGraph properties.",
      "scope": ["app/**/page.tsx", "app/**/layout.tsx"],
      "severity": "high"
    },
    {
      "id": "nextjs-use-image-component",
      "rule": "Never use raw <img> tags. Always use next/image <Image> component for automatic optimization, lazy loading, and responsive sizing. Set priority={true} only on above-the-fold hero images.",
      "scope": ["app/**/*.tsx", "components/**/*.tsx"],
      "severity": "high"
    },
    {
      "id": "nextjs-server-client-boundary",
      "rule": "Do not add 'use client' to components that only render content or fetch data. Only mark components as client when they use useState, useEffect, event handlers, or browser APIs. Excessive client components hurt page load performance and SEO.",
      "scope": ["app/**/*.tsx", "components/**/*.tsx"],
      "severity": "high"
    },
    {
      "id": "nextjs-no-env-in-client",
      "rule": "Never reference process.env variables in client components unless they are prefixed with NEXT_PUBLIC_. Non-prefixed env vars are server-only — using them in client code exposes undefined values or leaks secrets.",
      "scope": ["app/**/*.tsx", "components/**/*.tsx"],
      "severity": "high"
    },
    {
      "id": "nextjs-suspense-for-async",
      "rule": "Server Components that perform data fetching (fetch, database queries, external API calls) should be wrapped in <Suspense> boundaries with meaningful fallback UI. Missing Suspense blocks streaming and makes the page feel slow.",
      "scope": ["app/**/*.tsx"],
      "severity": "medium"
    },
    {
      "id": "nextjs-parallel-fetches",
      "rule": "Multiple independent data fetches in a Server Component must use Promise.all() or be placed in separate components with their own Suspense boundaries. Sequential awaits create waterfall fetches that slow Time to First Byte.",
      "scope": ["app/**/*.tsx", "lib/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "nextjs-structured-data",
      "rule": "Content pages (blog posts, product pages, FAQ) must include JSON-LD structured data via <script type='application/ld+json'>. Use schema.org types appropriate to the content (Article, Product, FAQPage, etc.).",
      "scope": ["app/**/*.tsx"],
      "severity": "medium"
    },
    {
      "id": "nextjs-revalidation-strategy",
      "rule": "Pages with dynamic content must declare a revalidation strategy. Use 'export const revalidate = N' for time-based ISR, or revalidateTag/revalidatePath in Server Actions for on-demand revalidation. Pages without a strategy serve stale content indefinitely.",
      "scope": ["app/**/page.tsx"],
      "severity": "medium"
    }
  ],
  "statusCheck": true,
  "updateExistingSummaryComment": true
}
```

---

## Scenario I: Next.js Dashboard / Admin Panel

### `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "ignorePatterns": "node_modules/**\n.next/**\nbuild/**\npackage-lock.json\npnpm-lock.yaml\nyarn.lock\n**/*.d.ts\ncoverage/**\npublic/**",
  "excludeAuthors": ["dependabot[bot]"],
  "includeBranches": ["main", "develop"],
  "rules": [
    {
      "id": "dashboard-auth-middleware",
      "rule": "All routes under /dashboard/** must be protected by authentication middleware. Verify the session/token in middleware.ts with a matcher for '/dashboard/:path*'. Unauthenticated requests must redirect to /login, never render protected content.",
      "scope": ["middleware.ts", "app/dashboard/**/*.tsx"],
      "severity": "high"
    },
    {
      "id": "dashboard-server-action-validation",
      "rule": "All Server Actions that accept form data or parameters must validate inputs using Zod or a similar schema validator before processing. Never trust client-submitted data — validate types, ranges, and permissions server-side.",
      "scope": ["app/**/*.ts", "app/**/*.tsx", "actions/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "dashboard-rbac-check",
      "rule": "Server Components and Server Actions that perform mutations (create, update, delete) must verify the user's role/permissions before executing. Do not rely on UI-only access control — a direct API call bypasses hidden buttons.",
      "scope": ["app/dashboard/**/*.tsx", "actions/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "dashboard-route-handler-auth",
      "rule": "All Route Handlers (route.ts) must verify authentication by checking cookies() or headers() at the start of every handler. Return 401 for unauthenticated and 403 for unauthorized requests. Never assume Route Handlers inherit middleware protection.",
      "scope": ["app/api/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "dashboard-error-boundary",
      "rule": "Every major route segment under /dashboard must have an error.tsx boundary that catches rendering errors and displays a recovery UI. Without error boundaries, a single failing component crashes the entire page.",
      "scope": ["app/dashboard/**/error.tsx", "app/dashboard/**/page.tsx"],
      "severity": "medium"
    },
    {
      "id": "dashboard-no-env-in-client",
      "rule": "Never reference process.env variables in client components unless prefixed with NEXT_PUBLIC_. Dashboard components often need API URLs or feature flags — these must use the public prefix or be passed from Server Components as props.",
      "scope": ["app/**/*.tsx", "components/**/*.tsx"],
      "severity": "high"
    },
    {
      "id": "dashboard-server-client-boundary",
      "rule": "Data fetching (database queries, API calls, auth checks) must happen in Server Components. Client Components should only handle interactive state (forms, modals, filters). Fetching in Client Components exposes API routes and adds unnecessary client bundle size.",
      "scope": ["app/**/*.tsx", "components/**/*.tsx"],
      "severity": "medium"
    },
    {
      "id": "dashboard-pagination-required",
      "rule": "Data tables and list views must implement server-side pagination via URL search params. Never fetch all records and paginate client-side — this breaks with large datasets and wastes bandwidth.",
      "scope": ["app/dashboard/**/*.tsx", "components/**/*.tsx"],
      "severity": "medium"
    }
  ],
  "statusCheck": true,
  "updateExistingSummaryComment": true,
  "includeConfidenceScore": true,
  "summarySection": { "included": true, "collapsible": true, "defaultOpen": true },
  "issuesTableSection": { "included": true, "collapsible": true, "defaultOpen": false }
}
```

---

## Scenario J: mcp-use Framework (Python Agent Using MCP Servers)

### `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "ignorePatterns": "__pycache__/**\n*.pyc\n*.egg-info/**\ndist/**\nbuild/**\n.tox/**\n.venv/**\nvenv/**\n.mypy_cache/**\n.pytest_cache/**\nhtmlcov/**\ncoverage/**\n*.lock",
  "excludeAuthors": ["dependabot[bot]"],
  "rules": [
    {
      "id": "mcpuse-session-cleanup",
      "rule": "MCPClient and MCPAgent instances must use async context managers ('async with MCPAgent(...) as agent:') or explicit await agent.close() in a finally block. Leaked connections exhaust server resources and cause hanging processes.",
      "scope": ["**/*.py"],
      "severity": "high"
    },
    {
      "id": "mcpuse-tool-error-handling",
      "rule": "All tool calls via agent.call_tool() or client.call_tool() must handle MCPToolCallError and inspect error.data for debugging context. Never swallow tool errors — log the error code, message, and data fields. Implement retry logic for transient failures (connection errors, timeouts).",
      "scope": ["**/*.py"],
      "severity": "high"
    },
    {
      "id": "mcpuse-no-hardcoded-secrets",
      "rule": "MCP server URLs, API keys, and credentials must never be hardcoded in source code. Use environment variables (os.environ), .env files with python-dotenv, or keyring for secrets. MCPClient.from_env() is the preferred pattern.",
      "scope": ["**/*.py"],
      "severity": "high"
    },
    {
      "id": "mcpuse-timeout-enforcement",
      "rule": "All tool calls must specify a timeout parameter (e.g., client.call_tool(..., timeout=30)). The default 60s timeout is too long for most operations. Handle asyncio.TimeoutError explicitly with a fallback or user-facing error message.",
      "scope": ["**/*.py"],
      "severity": "medium"
    },
    {
      "id": "mcpuse-input-validation",
      "rule": "Validate tool input parameters with Pydantic models or manual checks before passing to agent.call_tool(). Client-side validation catches schema mismatches early and provides better error messages than server-side -32602 errors.",
      "scope": ["**/*.py"],
      "severity": "medium"
    },
    {
      "id": "mcpuse-connection-error-recovery",
      "rule": "Handle MCPConnectionError with retry logic (exponential backoff). Implement a maximum retry count and a circuit breaker pattern for repeated failures. Never let a connection error crash the entire agent workflow.",
      "scope": ["**/*.py"],
      "severity": "high"
    },
    {
      "id": "mcpuse-multi-server-routing",
      "rule": "When using multiple MCP servers (MCPAgent(servers=[...])), verify that tool namespaces do not collide. If two servers provide tools with the same name, configure explicit routing or namespace prefixes. Ambiguous routing causes unpredictable tool selection.",
      "scope": ["**/*.py"],
      "severity": "medium"
    },
    {
      "id": "mcpuse-refresh-tools",
      "rule": "After server restarts or config changes, call agent.refresh_tools() to reload available tools. Stale tool schemas cause silent validation failures or invoke removed tools.",
      "scope": ["**/*.py"],
      "severity": "low"
    }
  ],
  "statusCheck": true,
  "updateExistingSummaryComment": true
}
```

---

## Scenario K: Production MCP Server (TypeScript, Token-Optimized)

For MCP servers with middleware pipelines, multiple tools, and external API integrations.

### `.greptile/config.json`
```json
{
  "strictness": 2,
  "commentTypes": ["logic", "syntax"],
  "ignorePatterns": "node_modules/**\nbuild/**\ndist/**\npackage-lock.json\npnpm-lock.yaml\n**/*.d.ts\ncoverage/**\ntest-results/**\nscripts/**\n*.log",
  "excludeAuthors": ["dependabot[bot]"],
  "includeBranches": ["main", "develop"],
  "rules": [
    {
      "id": "mcp-tool-zod-validation",
      "rule": "Every tool handler must validate input parameters using the Zod schema declared in its tool definition. Use safeParse() and return a structured MCP error (isError: true) on validation failure. The inputSchema in tools/list and the runtime Zod schema must be identical — divergence causes silent failures.",
      "scope": ["src/mcp/tools/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-response-format",
      "rule": "Tool handler responses must return { content: [{ type: 'text', text: string }] } for success. Error responses must set isError: true. Never return raw strings, unstructured objects, or objects missing the content array.",
      "scope": ["src/mcp/tools/**/*.ts", "src/mcp/response/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-middleware-error-boundary",
      "rule": "The middleware pipeline must include an error boundary that catches all exceptions and converts them to MCP-compliant error responses. Unhandled exceptions in tool handlers crash the MCP server and break the client connection.",
      "scope": ["src/mcp/middleware/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-no-secrets-in-responses",
      "rule": "Tool responses must never include API keys, authentication credentials, or internal server details. Sanitize error messages before including them in MCP responses. Use structured logging for debugging — not response content.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-timeout-on-external-calls",
      "rule": "All external API calls, database queries, and subprocess executions must use AbortSignal or Promise.race() with a timeout. The MCP server must never hang waiting for an unresponsive upstream service. Propagate the request's AbortSignal to all downstream calls.",
      "scope": ["src/services/**/*.ts", "src/mcp/client/**/*.ts", "src/mcp/tools/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-circuit-breaker-usage",
      "rule": "External service calls should be wrapped in the circuit breaker middleware. When an upstream service fails repeatedly, the circuit breaker auto-rejects requests instead of wasting time on doomed calls. Check that new service integrations are routed through the circuit breaker.",
      "scope": ["src/services/**/*.ts", "src/mcp/middleware/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "mcp-token-budget-compliance",
      "rule": "Tool handlers that return variable-length data must respect the token budget. Use the ResponseBuilder's withData() method with maxItems limits. Never return unbounded arrays or full file contents — this overflows the LLM's context window.",
      "scope": ["src/mcp/tools/**/*.ts", "src/mcp/response/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-structured-logging",
      "rule": "Use the structured logger (src/observability/logger) for all logging. Never use console.log/warn/error — on stdio transport, console output corrupts the JSON-RPC stream and breaks client communication.",
      "scope": ["src/**/*.ts"],
      "severity": "high"
    },
    {
      "id": "mcp-env-validation",
      "rule": "All environment variables must be validated at startup using the Zod schema in config/secrets.ts. New environment variables must be added to the schema with proper defaults or required markers. Never read process.env directly in business logic.",
      "scope": ["src/config/**/*.ts", "src/**/*.ts"],
      "severity": "medium"
    },
    {
      "id": "mcp-registry-consistency",
      "rule": "Every tool defined in the registry (tools/list) must have a corresponding handler in tools/call. Adding a tool definition without a handler returns unhandled method errors. Removing a handler without removing the definition advertises phantom tools.",
      "scope": ["src/mcp/server/**/*.ts", "src/mcp/tools/**/*.ts"],
      "severity": "high"
    }
  ],
  "statusCheck": true,
  "updateExistingSummaryComment": true,
  "includeConfidenceScore": true,
  "summarySection": { "included": true, "collapsible": true, "defaultOpen": true },
  "issuesTableSection": { "included": true, "collapsible": true, "defaultOpen": false }
}
```

### `.greptile/rules.md`
```markdown
## MCP Server Code Quality

### Response Builder Pattern

All tool handlers should use the ResponseBuilder for consistent, token-optimized responses.

#### Good
\`\`\`typescript
return ResponseBuilder.create()
  .withSummary({ title: "Keyword Analysis", insights: [...] })
  .withData(results, { formatter: formatKeyword, maxItems: 10 })
  .withNextSteps([
    { tool: "analyze_competitors", reason: "Compare against top ranking domains" }
  ])
  .build();
\`\`\`

#### Bad
\`\`\`typescript
return {
  content: [{
    type: "text",
    text: JSON.stringify(allResults) // unbounded, no token budget, no structure
  }]
};
\`\`\`

### Stdio Transport Safety

On stdio transport, any console output corrupts the JSON-RPC protocol stream.

#### Good
\`\`\`typescript
import { logger } from '../observability/logger.js';
logger.info('Processing tool call', { tool: name, params: Object.keys(params) });
\`\`\`

#### Bad
\`\`\`typescript
console.log('Processing:', name, params); // BREAKS stdio transport!
\`\`\`

### AbortSignal Propagation

Every external call must respect the request's abort signal for proper timeout handling.

#### Good
\`\`\`typescript
async function fetchData(url: string, signal: AbortSignal) {
  const response = await fetch(url, { signal });
  if (!response.ok) throw new ApiError(response.status, await response.text());
  return response.json();
}
\`\`\`

#### Bad
\`\`\`typescript
async function fetchData(url: string) {
  const response = await fetch(url); // no signal, no timeout, hangs forever
  return response.json();
}
\`\`\`
```
