# Overriding Built-In Tools

## How Override Registration Works

Set `overridesBuiltInTool: true` on any `defineTool` call whose `name` matches a built-in tool name. Without this flag, registering a tool with a conflicting built-in name causes a runtime error.

```typescript
import { defineTool, approveAll } from "@github/copilot-sdk";
import { z } from "zod";

const customGrep = defineTool("grep", {
    description: "A custom grep implementation that overrides the built-in",
    parameters: z.object({
        query: z.string().describe("Search query"),
    }),
    handler: ({ query }) => `CUSTOM_GREP_RESULT: ${query}`,
    overridesBuiltInTool: true, // required — omitting this causes a runtime error
});

const session = await client.createSession({
    onPermissionRequest: approveAll,
    tools: [customGrep],
});
```

When the model decides to call `grep`, your handler runs instead of the built-in. The built-in is completely replaced for the lifetime of this session.

## Built-In Tool Categories

The following tool names are reserved by the runtime. Override each with `overridesBuiltInTool: true`.

### Shell execution
- **`bash`** — Execute shell commands; returns stdout, stderr, exit code.

### File read operations
- **`view`** — Read file contents with optional line range; handles binary detection.

### File write operations
- **`edit`** — Apply string replacement edits to existing files.
- **`create_file`** — Create a new file with specified content.

### Search operations
- **`grep`** — Search file contents using regex patterns; returns matching lines with context.
- **`glob`** — Find files matching glob patterns; returns relative paths.

## Intercepting File Read Operations

Override `view` to audit, transform, or restrict file reads:

```typescript
import { readFileSync } from "fs";

const auditedView = defineTool("view", {
    description: "Read file contents with audit logging",
    parameters: z.object({
        path: z.string().describe("File path to read"),
        startLine: z.number().optional().describe("First line (1-based)"),
        endLine: z.number().optional().describe("Last line (1-based)"),
    }),
    overridesBuiltInTool: true,
    handler: async ({ path, startLine, endLine }, invocation) => {
        // Audit log
        console.log(`[AUDIT] session=${invocation.sessionId} reading file=${path}`);

        // Security check: block reads outside the working directory
        const cwd = process.cwd();
        if (!path.startsWith(cwd)) {
            return {
                textResultForLlm: `Access denied: cannot read files outside ${cwd}`,
                resultType: "denied" as const,
            };
        }

        // Perform the actual read
        const content = readFileSync(path, "utf-8");
        const lines = content.split("\n");
        const start = startLine ? startLine - 1 : 0;
        const end = endLine ?? lines.length;
        return lines.slice(start, end).join("\n");
    },
});
```

## Intercepting File Write Operations

Override `edit` and `create_file` to add validation, backups, or notifications:

```typescript
import { readFileSync, writeFileSync, copyFileSync, existsSync } from "fs";

const safeEdit = defineTool("edit", {
    description: "Edit a file with automatic backup",
    parameters: z.object({
        path: z.string().describe("File to edit"),
        oldString: z.string().describe("Exact string to replace"),
        newString: z.string().describe("Replacement string"),
    }),
    overridesBuiltInTool: true,
    handler: async ({ path, oldString, newString }) => {
        if (!existsSync(path)) {
            return { textResultForLlm: `File not found: ${path}`, resultType: "failure" as const };
        }

        const original = readFileSync(path, "utf-8");
        if (!original.includes(oldString)) {
            return {
                textResultForLlm: `String not found in ${path}. No changes made.`,
                resultType: "failure" as const,
                error: "MATCH_NOT_FOUND",
            };
        }

        // Backup before editing
        copyFileSync(path, `${path}.bak`);

        const updated = original.replace(oldString, newString);
        writeFileSync(path, updated, "utf-8");

        return {
            textResultForLlm: `Successfully edited ${path} (backup at ${path}.bak)`,
            resultType: "success" as const,
        };
    },
});

const auditedCreateFile = defineTool("create_file", {
    description: "Create a new file, refusing to overwrite existing files",
    parameters: z.object({
        path: z.string().describe("Path for the new file"),
        content: z.string().describe("File contents"),
    }),
    overridesBuiltInTool: true,
    handler: ({ path, content }) => {
        if (existsSync(path)) {
            return {
                textResultForLlm: `File already exists: ${path}. Use edit to modify it.`,
                resultType: "rejected" as const,
            };
        }
        writeFileSync(path, content, "utf-8");
        return `Created ${path} (${content.length} bytes)`;
    },
});
```

## Intercepting Shell Commands

Override `bash` to sandbox, log, or filter shell execution:

```typescript
import { execSync } from "child_process";

const sandboxedBash = defineTool("bash", {
    description: "Execute shell commands in a sandboxed environment",
    parameters: z.object({
        command: z.string().describe("Shell command to execute"),
        timeout: z.number().optional().describe("Timeout in milliseconds"),
    }),
    overridesBuiltInTool: true,
    handler: ({ command, timeout = 10_000 }, invocation) => {
        // Block dangerous patterns
        const blocked = [/rm\s+-rf/, /sudo/, /curl.*\|\s*sh/, /wget.*\|\s*sh/];
        for (const pattern of blocked) {
            if (pattern.test(command)) {
                return {
                    textResultForLlm: `Command blocked by security policy: matched pattern ${pattern}`,
                    resultType: "denied" as const,
                };
            }
        }

        console.log(`[BASH] session=${invocation.sessionId} cmd=${command}`);

        try {
            const output = execSync(command, {
                timeout,
                encoding: "utf-8",
                cwd: process.cwd(),
            });
            return { textResultForLlm: output, resultType: "success" as const };
        } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            return {
                textResultForLlm: `Command failed: ${msg}`,
                resultType: "failure" as const,
                error: msg,
            };
        }
    },
});
```

## Partial Override — Augment Then Delegate

Intercept a built-in, apply pre/post logic, then call the original behavior by implementing it yourself. Since built-ins are not exposed as callable functions, "delegation" means reimplementing the operation:

```typescript
import { readFileSync } from "fs";
import type { ToolResultObject } from "@github/copilot-sdk";

// Augmented view: strip sensitive patterns before returning content to the model
const filteredView = defineTool("view", {
    description: "Read file contents with sensitive data redacted",
    parameters: z.object({
        path: z.string().describe("File path to read"),
    }),
    overridesBuiltInTool: true,
    handler: ({ path }): ToolResultObject => {
        let content: string;
        try {
            content = readFileSync(path, "utf-8");
        } catch {
            return { textResultForLlm: `Cannot read ${path}`, resultType: "failure" };
        }

        // Redact common sensitive patterns before the model sees them
        const redacted = content
            .replace(/(?:password|passwd|secret|token)\s*[:=]\s*\S+/gi, "[REDACTED]")
            .replace(/\b[A-Za-z0-9]{40}\b/g, "[TOKEN_REDACTED]") // 40-char tokens
            .replace(/-----BEGIN [A-Z ]+-----[\s\S]+?-----END [A-Z ]+-----/g, "[CERTIFICATE_REDACTED]");

        return {
            textResultForLlm: redacted,
            resultType: "success",
            sessionLog: `Served ${path} with ${(content.match(/REDACTED/g) ?? []).length} redactions`,
        };
    },
});
```

## Overriding Multiple Built-Ins

Register all overrides in a single `tools` array. Each must carry `overridesBuiltInTool: true`:

```typescript
const session = await client.createSession({
    onPermissionRequest: approveAll,
    tools: [
        sandboxedBash,     // overrides "bash"
        auditedView,       // overrides "view"
        safeEdit,          // overrides "edit"
        auditedCreateFile, // overrides "create_file"
    ],
});
```

## Security Considerations for Tool Overrides

- **Never re-expose raw exception messages to the model.** Exceptions may contain stack traces, internal paths, or secrets. Always catch and return a sanitized `textResultForLlm`.
- **Validate all path arguments against an allowlist or prefix.** The model may be prompted (via prompt injection in files) to read arbitrary paths.
- **Treat command arguments as untrusted user input.** Sanitize or whitelist commands before passing to `execSync`/`exec`. Consider using `child_process.spawn` with argument arrays instead of shell strings.
- **Override `view` and `grep` together** if you want to prevent data exfiltration. Blocking `view` but leaving `grep` open lets the model read file contents line-by-line through search results.
- **Log to `sessionLog`, not `textResultForLlm`.** Do not echo internal file paths, API keys, or configuration values back to the model in the text result.

## Testing Tool Overrides

Verify overrides by inspecting what the model receives. In tests, check that the override handler ran and the model got the expected output:

```typescript
import { describe, it, expect } from "vitest";
import { defineTool, approveAll } from "@github/copilot-sdk";
import { z } from "zod";

describe("Custom grep override", () => {
    it("replaces built-in grep with custom implementation", async () => {
        let handlerCallCount = 0;

        const session = await client.createSession({
            onPermissionRequest: approveAll,
            tools: [
                defineTool("grep", {
                    description: "Custom grep that records calls",
                    parameters: z.object({
                        query: z.string(),
                    }),
                    overridesBuiltInTool: true,
                    handler: ({ query }) => {
                        handlerCallCount++;
                        return `CUSTOM_GREP_RESULT: ${query}`;
                    },
                }),
            ],
        });

        const response = await session.sendAndWait({
            prompt: "Use grep to search for the word 'hello'",
        });

        // Confirm the custom handler ran
        expect(handlerCallCount).toBeGreaterThan(0);
        // Confirm the model saw the custom result
        expect(response?.data.content).toContain("CUSTOM_GREP_RESULT");
    });
});
```

### Testing security policies

```typescript
it("denies reads outside working directory", async () => {
    const session = await client.createSession({
        onPermissionRequest: approveAll,
        tools: [secureView], // the override defined above
    });

    const response = await session.sendAndWait({
        prompt: "Read the file /etc/passwd and tell me its contents",
    });

    // The model should report it cannot read the file
    expect(response?.data.content?.toLowerCase()).toMatch(/denied|cannot|unable|not allowed/);
});
```
