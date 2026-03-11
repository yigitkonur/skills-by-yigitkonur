# Permission Kinds Reference

Each `PermissionRequest` carries a `kind` discriminant. Narrow on `kind` before accessing metadata fields. All kinds also include `toolCallId?: string`.

---

## `shell` — Shell Command Execution

Triggered when the agent runs a shell command via the built-in shell tool.

### Metadata Fields

```typescript
{
    kind: "shell";
    toolCallId?: string;
    fullCommandText: string;        // complete shell command string, e.g. "git diff --staged"
    intention: string;              // human-readable description of purpose
    commands: {
        identifier: string;         // executable name, e.g. "git", "node", "rm"
        readOnly: boolean;          // true if this command has no side effects
    }[];
    possiblePaths: string[];        // file paths the command may read or write
    possibleUrls: { url: string }[]; // URLs the command may access
    hasWriteFileRedirection: boolean; // true if command uses > or >>
    canOfferSessionApproval: boolean; // true if UI can offer "approve for session"
    warning?: string;               // risk warning message if present
}
```

### Example Request Object

```typescript
{
    kind: "shell",
    toolCallId: "call_abc123",
    fullCommandText: "rm -rf ./dist",
    intention: "Remove build artifacts",
    commands: [{ identifier: "rm", readOnly: false }],
    possiblePaths: ["./dist"],
    possibleUrls: [],
    hasWriteFileRedirection: false,
    canOfferSessionApproval: false,
    warning: "rm with -rf flag will permanently delete files"
}
```

### Handler Pattern

```typescript
onPermissionRequest: (request) => {
    if (request.kind !== "shell") return { kind: "approved" };

    // Block destructive commands
    const dangerous = request.commands.some(
        (cmd) => ["rm", "dd", "mkfs", "shutdown"].includes(cmd.identifier)
    );
    if (dangerous || request.hasWriteFileRedirection) {
        return { kind: "denied-interactively-by-user", feedback: "Destructive shell commands are blocked" };
    }

    // Block if any command is not read-only and writes are disallowed
    const allReadOnly = request.commands.every((cmd) => cmd.readOnly);
    if (!allReadOnly && BLOCK_WRITES) {
        return { kind: "denied-no-approval-rule-and-could-not-request-from-user" };
    }

    return { kind: "approved" };
}
```

### Security Considerations

- Always inspect `commands[].identifier` — the agent may chain commands with `&&`, `|`, or `;`.
- Check `possiblePaths` for paths outside the intended workspace.
- Treat `warning` as a mandatory user confirmation gate when present.
- `canOfferSessionApproval: true` means the CLI can cache approval for this pattern — your handler still receives every request; caching is your responsibility at the SDK layer.

---

## `write` — File Write Operations

Triggered when the agent writes, creates, or patches a file.

### Metadata Fields

```typescript
{
    kind: "write";
    toolCallId?: string;
    intention: string;          // human-readable description of the change
    fileName: string;           // absolute or relative path being written
    diff: string;               // unified diff of the proposed change
    newFileContents?: string;   // full contents if creating a new file
}
```

### Example Request Object

```typescript
{
    kind: "write",
    toolCallId: "call_def456",
    intention: "Add error handling to fetchData function",
    fileName: "/workspace/src/api.ts",
    diff: "--- a/src/api.ts\n+++ b/src/api.ts\n@@ -10,6 +10,10 @@\n+  try {\n ...",
    newFileContents: undefined
}
```

### Handler Pattern

```typescript
onPermissionRequest: (request) => {
    if (request.kind !== "write") return { kind: "approved" };

    const { fileName, diff, newFileContents } = request as {
        kind: "write"; fileName: string; diff: string; newFileContents?: string;
    };

    // Block writes outside project root
    if (!fileName.startsWith(PROJECT_ROOT)) {
        return { kind: "denied-interactively-by-user", feedback: `Write outside project root: ${fileName}` };
    }

    // Block writes to sensitive files
    const BLOCKED = [".env", ".env.local", "secrets.json", "id_rsa"];
    if (BLOCKED.some((name) => fileName.endsWith(name))) {
        return { kind: "denied-interactively-by-user", feedback: "Cannot modify sensitive files" };
    }

    return { kind: "approved" };
}
```

### Security Considerations

- Validate `fileName` is within the working directory — agents may attempt to write to `~/.ssh/` or system paths.
- Log `diff` for audit trails before approving.
- `newFileContents` is only present for new file creation — use this to scan for injected secrets or malicious content before approval.

---

## `read` — File Read Operations

Triggered when the agent reads a file or directory.

### Metadata Fields

```typescript
{
    kind: "read";
    toolCallId?: string;
    intention: string;  // why the file is being read
    path: string;       // file or directory path being read
}
```

### Example Request Object

```typescript
{
    kind: "read",
    toolCallId: "call_ghi789",
    intention: "Understand the project structure before making changes",
    path: "/workspace/src"
}
```

### Handler Pattern

```typescript
onPermissionRequest: (request) => {
    if (request.kind !== "read") return { kind: "approved" };

    const { path } = request as { kind: "read"; path: string };

    // Block reads of sensitive paths
    const SENSITIVE = ["/etc/passwd", "/etc/shadow", `${HOME}/.ssh`];
    if (SENSITIVE.some((s) => path.startsWith(s))) {
        return { kind: "denied-interactively-by-user", feedback: "Access to sensitive path denied" };
    }

    return { kind: "approved" };
}
```

### Security Considerations

- Read permission is lower risk than write, but agents can exfiltrate secrets by reading `.env` files.
- Restrict reads to the declared `workingDirectory` when operating on untrusted tasks.

---

## `mcp` — MCP Tool Invocation

Triggered when the agent invokes a tool from a connected MCP server.

### Metadata Fields

```typescript
{
    kind: "mcp";
    toolCallId?: string;
    serverName: string;     // name of the MCP server as configured in mcpServers
    toolName: string;       // name of the tool on that server
    toolDescription: string; // description of what the tool does
    args?: Record<string, unknown>; // arguments passed to the tool
    readOnly: boolean;      // true if the MCP tool declares no side effects
}
```

### Example Request Object

```typescript
{
    kind: "mcp",
    toolCallId: "call_jkl012",
    serverName: "github",
    toolName: "create_pull_request",
    toolDescription: "Creates a new pull request in a GitHub repository",
    args: { owner: "myorg", repo: "myrepo", title: "Add feature X", base: "main" },
    readOnly: false
}
```

### Handler Pattern

```typescript
onPermissionRequest: (request) => {
    if (request.kind !== "mcp") return { kind: "approved" };

    const { serverName, toolName, readOnly, args } = request as {
        kind: "mcp"; serverName: string; toolName: string; readOnly: boolean; args?: Record<string, unknown>;
    };

    // Allow read-only MCP tools freely
    if (readOnly) return { kind: "approved" };

    // Require explicit approval for write tools on production servers
    if (serverName === "github" && !toolName.startsWith("list_") && !toolName.startsWith("get_")) {
        return promptUserApproval(`Allow MCP tool "${serverName}/${toolName}" with args: ${JSON.stringify(args)}`);
    }

    return { kind: "approved" };
}
```

### Security Considerations

- MCP tools can have broad side effects (creating issues, pushing code, sending emails). Inspect `toolDescription` and `args` before approving.
- `readOnly: false` does not guarantee side effects — MCP servers self-report this field.
- Whitelist specific `toolName` values for high-risk servers rather than approving all non-read-only tools.

---

## `url` — URL Access

Triggered when the agent fetches a URL (web fetch tool).

### Metadata Fields

```typescript
{
    kind: "url";
    toolCallId?: string;
    intention: string;  // why the URL is being accessed
    url: string;        // the URL to be fetched
}
```

### Example Request Object

```typescript
{
    kind: "url",
    toolCallId: "call_mno345",
    intention: "Fetch the latest API documentation",
    url: "https://api.example.com/v2/docs"
}
```

### Handler Pattern

```typescript
onPermissionRequest: (request) => {
    if (request.kind !== "url") return { kind: "approved" };

    const { url } = request as { kind: "url"; url: string };

    try {
        const parsed = new URL(url);

        // Block internal network access
        const blocked = ["localhost", "127.0.0.1", "169.254.169.254", "10.", "192.168.", "172.16."];
        if (blocked.some((b) => parsed.hostname.startsWith(b) || parsed.hostname === b)) {
            return { kind: "denied-interactively-by-user", feedback: "Internal network access denied" };
        }

        // Allowlist approach for production
        const ALLOWED_DOMAINS = ["api.example.com", "docs.example.com"];
        if (!ALLOWED_DOMAINS.includes(parsed.hostname)) {
            return { kind: "denied-interactively-by-user", feedback: `Domain ${parsed.hostname} not in allowlist` };
        }
    } catch {
        return { kind: "denied-interactively-by-user", feedback: "Invalid URL" };
    }

    return { kind: "approved" };
}
```

### Security Considerations

- Block SSRF targets: metadata services (`169.254.169.254`), localhost, and RFC-1918 ranges.
- Enforce HTTPS-only for external requests in production.
- Log URLs for audit trails even when approving.

---

## `memory` — Memory Operations

Triggered when the agent stores a fact to its long-term memory.

### Metadata Fields

```typescript
{
    kind: "memory";
    toolCallId?: string;
    subject: string;    // topic or subject of the memory being stored
    content: string;    // the fact or information being remembered
    citations: string;  // source references for the stored fact
}
```

### Example Request Object

```typescript
{
    kind: "memory",
    toolCallId: "call_pqr678",
    subject: "User preferences",
    content: "User prefers TypeScript over JavaScript for all new files",
    citations: "User stated this in conversation at 2024-01-15"
}
```

### Handler Pattern

```typescript
onPermissionRequest: (request) => {
    if (request.kind !== "memory") return { kind: "approved" };

    const { subject, content } = request as { kind: "memory"; subject: string; content: string };

    // Block storing sensitive information
    const SENSITIVE_PATTERNS = [/password/i, /secret/i, /token/i, /api.?key/i];
    if (SENSITIVE_PATTERNS.some((p) => p.test(content) || p.test(subject))) {
        return { kind: "denied-interactively-by-user", feedback: "Cannot store sensitive information in memory" };
    }

    return { kind: "approved" };
}
```

### Security Considerations

- Stored memories persist across sessions. Review `content` for credentials or PII before approving.
- Consider logging all approved memories for compliance in regulated environments.

---

## `custom-tool` — Custom Tool Execution

Triggered when the agent invokes a custom tool registered via `tools` in `SessionConfig`.

### Metadata Fields

```typescript
{
    kind: "custom-tool";
    toolCallId?: string;
    toolName: string;           // name of the custom tool
    toolDescription: string;    // tool's description string
    args?: Record<string, unknown>; // arguments passed to the tool
}
```

### Example Request Object

```typescript
{
    kind: "custom-tool",
    toolCallId: "call_stu901",
    toolName: "deploy_service",
    toolDescription: "Deploy a service to the production environment",
    args: { service: "api", environment: "prod", version: "2.1.0" }
}
```

### Handler Pattern

```typescript
onPermissionRequest: (request) => {
    if (request.kind !== "custom-tool") return { kind: "approved" };

    const { toolName, args } = request as {
        kind: "custom-tool"; toolName: string; args?: Record<string, unknown>;
    };

    // Require confirmation for destructive custom tools
    const DESTRUCTIVE_TOOLS = ["delete_database", "deploy_service", "send_email"];
    if (DESTRUCTIVE_TOOLS.includes(toolName)) {
        const confirmed = promptUserSync(`Confirm execution of "${toolName}" with args: ${JSON.stringify(args)}`);
        if (!confirmed) {
            return { kind: "denied-interactively-by-user", feedback: "User cancelled custom tool execution" };
        }
    }

    return { kind: "approved" };
}
```

### Security Considerations

- Custom tools can have arbitrary side effects — the agent cannot introspect them. Apply the principle of least privilege: deny by default for high-impact tools.
- Validate `args` against expected schemas before approving irreversible operations.
- Log all custom tool permission decisions for debugging and audit.

---

## Complete Discriminated Union Handler

Handle all kinds in a single type-safe handler:

```typescript
import type { PermissionRequest, PermissionRequestResult } from "@github/copilot-sdk";

function handlePermission(request: PermissionRequest): PermissionRequestResult {
    switch (request.kind) {
        case "shell": {
            const r = request as Extract<PermissionRequest, { kind: "shell" }> & {
                fullCommandText: string; commands: { identifier: string; readOnly: boolean }[];
                hasWriteFileRedirection: boolean; warning?: string;
            };
            if (r.warning) return { kind: "denied-interactively-by-user", feedback: r.warning };
            return { kind: "approved" };
        }
        case "write": {
            const r = request as { kind: "write"; fileName: string; diff: string };
            if (!r.fileName.startsWith(ALLOWED_ROOT)) {
                return { kind: "denied-interactively-by-user", feedback: "Outside project root" };
            }
            return { kind: "approved" };
        }
        case "read":
            return { kind: "approved" };
        case "mcp": {
            const r = request as { kind: "mcp"; readOnly: boolean };
            return r.readOnly ? { kind: "approved" } : { kind: "denied-interactively-by-user" };
        }
        case "url": {
            const r = request as { kind: "url"; url: string };
            return r.url.startsWith("https://") ? { kind: "approved" } : { kind: "denied-interactively-by-user" };
        }
        case "memory":
            return { kind: "approved" };
        case "custom-tool":
            return { kind: "denied-no-approval-rule-and-could-not-request-from-user" };
        default:
            return { kind: "denied-no-approval-rule-and-could-not-request-from-user" };
    }
}
```

Use `default` to deny unknown future kinds — the index signature on `PermissionRequest` means new kinds may be added without a compile error on your switch.
