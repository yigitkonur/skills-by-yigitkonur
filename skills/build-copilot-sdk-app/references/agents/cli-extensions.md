# CLI Extensions — Reference

Extensions add custom tools, lifecycle hooks, and event-driven behaviors to the Copilot CLI. Each extension is a Node.js ES module that runs as a forked child process and communicates with the CLI parent over JSON-RPC via stdio. Extensions use `@github/copilot-sdk` for all SDK interactions.

---

## Extension File Format

Extensions must be `.mjs` files (ES modules). No other file format is supported — `.js` (CommonJS), `.ts`, `.cjs` all fail. The file must be named exactly `extension.mjs`.

```
.github/extensions/
  my-extension/
    extension.mjs      ← required name, must be .mjs
```

The minimal valid extension:

```js
import { approveAll } from "@github/copilot-sdk";
import { joinSession } from "@github/copilot-sdk/extension";

await joinSession({
    onPermissionRequest: approveAll,  // required
    tools: [],                        // optional
    hooks: {},                        // optional
});
```

Do not add a `package.json` or `node_modules` — `@github/copilot-sdk` is resolved automatically by the CLI's module resolver. Do not run `npm install` inside the extension directory.

---

## `joinSession()` — Connecting to the Current Session

`joinSession()` is the only entry point. Call it at the top level of your `.mjs` file (not inside a function). It establishes a JSON-RPC connection over stdio and attaches to the user's current foreground session.

```js
import { approveAll, defineTool } from "@github/copilot-sdk";
import { joinSession } from "@github/copilot-sdk/extension";

const session = await joinSession({
    onPermissionRequest: approveAll,
    tools: [ /* tool definitions */ ],
    hooks: { /* hook handlers */ },
});

// session is now live — tools are registered, hooks are active
await session.log("Extension loaded successfully.");
```

`joinSession()` returns the session object, which provides `send`, `sendAndWait`, `log`, `on`, `rpc`, and `workspacePath`. The extension process stays alive as long as `joinSession()` is awaited (which it should be — `joinSession` resolves only when the session terminates).

---

## Extension Tool Registration

Tools are registered by passing them in the `tools` array to `joinSession()`. Tool names must be globally unique across all loaded extensions.

```js
import { approveAll } from "@github/copilot-sdk";
import { joinSession } from "@github/copilot-sdk/extension";

const session = await joinSession({
    onPermissionRequest: approveAll,
    tools: [
        {
            name: "my_extension_lookup",   // globally unique — use a namespace prefix
            description: "Looks up a value in the internal knowledge base.",
            parameters: {
                type: "object",
                properties: {
                    query: {
                        type: "string",
                        description: "The search query",
                    },
                    limit: {
                        type: "number",
                        description: "Max results to return",
                    },
                },
                required: ["query"],
            },
            handler: async (args, invocation) => {
                // args is typed according to your parameters schema
                // invocation: { sessionId, toolCallId, toolName }
                const results = await lookupKnowledgeBase(args.query, args.limit ?? 5);
                return JSON.stringify(results);  // return string or ToolResultObject
            },
        },
    ],
});
```

Handler return values:
- Return a `string` → treated as a successful result
- Return `{ textResultForLlm: string, resultType: "success" | "failure" | "rejected" | "denied" }` → structured result
- Return `undefined` → empty success
- Throw an error → the CLI sends a failure result with the error message

---

## `session.log()` vs `console.log` — Critical Distinction

stdout is **reserved for JSON-RPC**. Writing anything to stdout (via `console.log`, `process.stdout.write`, or any library that does so) corrupts the JSON-RPC framing and will crash the extension or cause silent protocol errors.

Use `session.log()` for all user-visible output:

```js
// CORRECT — routes through the session timeline
await session.log("Extension initialized");
await session.log("Rate limit approaching: 10 requests remaining", { level: "warning" });
await session.log("Connection to external API failed", { level: "error" });
await session.log("Fetching data...", { ephemeral: true });  // transient — not persisted

// WRONG — corrupts the JSON-RPC stream
console.log("Extension initialized");         // fatal
process.stdout.write("fetching...\n");        // fatal
```

`session.log()` parameters:
```js
await session.log(message: string, options?: {
    level?: "info" | "warning" | "error",  // default: "info"
    ephemeral?: boolean,                    // default: false
});
```

`console.error()` writes to stderr, which is safe for debugging. But prefer `session.log()` for anything the user should see.

---

## Extension Lifecycle and Cleanup

The CLI manages the extension process lifecycle:

1. **Discovery**: on CLI startup, the CLI scans `.github/extensions/` (relative to the git root) and the user config extensions directory. Each immediate subdirectory containing `extension.mjs` is an extension candidate.
2. **Launch**: each extension is forked as a child process. `@github/copilot-sdk` is injected via module resolver.
3. **Connection**: the extension calls `joinSession()` to attach to the foreground session.
4. **Reload**: on `/clear`, all extensions are stopped and re-launched. In-memory state is lost.
5. **Shutdown**: on CLI exit, SIGTERM is sent to the extension process. If it does not exit within 5 seconds, SIGKILL is sent.

Perform cleanup in the process `SIGTERM` handler:

```js
process.on("SIGTERM", async () => {
    await cleanup();   // flush pending writes, close connections
    process.exit(0);
});
```

Do not store session state in module-level variables if you need it to survive across `/clear` cycles — state is wiped on reload. Use the session workspace (`session.workspacePath`) for persistence.

---

## Tool Name Collision Rules

Tool names must be **globally unique** across all extensions loaded in a session. If two extensions register a tool with the same name, the second extension fails to initialize entirely — not just the conflicting tool.

Naming rules:
- Use a unique prefix that identifies your extension: `myextension_toolname` not `lookup`
- Use snake_case: `my_extension_lookup` not `myExtensionLookup` or `my-extension-lookup`
- Avoid names that conflict with built-in Copilot tools: `bash`, `edit`, `view`, `grep`, `glob`, etc.
- Check for conflicts by running `extensions_manage({ operation: "list" })` and inspecting loaded tools

```js
// BAD — generic name, likely to collide with other extensions
{ name: "lookup" }
{ name: "search" }
{ name: "run" }

// GOOD — namespaced, collision-resistant
{ name: "acmetools_knowledge_lookup" }
{ name: "acmetools_jira_create_ticket" }
{ name: "acmetools_deploy_preview" }
```

---

## Extension Packaging and Distribution

### Project-scoped extensions

Place under `.github/extensions/` in your repository. The extension is available to all users of the repo who have the Copilot CLI installed. Commit `extension.mjs` to version control.

```
my-project/
  .github/
    extensions/
      my-tool/
        extension.mjs
```

### User-scoped extensions

Place in the user's Copilot config extensions directory (outside of any specific repo). Available across all repositories for that user. Add `location: "user"` when scaffolding via `extensions_manage`.

### Shadowing rules

If a project extension and a user extension share the same directory name, the **project extension takes precedence**. The user extension with the same name is silently skipped.

### Reloading during development

Use `extensions_reload({})` after editing `extension.mjs`. This stops all running extensions and relaunches them with the new code. No CLI restart is required.

```
extensions_reload({})
```

Verify after reload:
```
extensions_manage({ operation: "list" })
extensions_manage({ operation: "inspect", name: "my-extension" })
```

Check the inspect output for `"status": "failed"` to diagnose load errors.

---

## Complete Extension Example

```js
import { approveAll } from "@github/copilot-sdk";
import { joinSession } from "@github/copilot-sdk/extension";
import { execSync } from "child_process";

const session = await joinSession({
    onPermissionRequest: approveAll,

    tools: [
        {
            name: "myext_run_lint",
            description: "Runs ESLint on a specific file and returns the results.",
            parameters: {
                type: "object",
                properties: {
                    filePath: {
                        type: "string",
                        description: "Absolute or relative path to the file to lint",
                    },
                },
                required: ["filePath"],
            },
            handler: async (args, invocation) => {
                try {
                    const output = execSync(`npx eslint --format compact "${args.filePath}"`, {
                        encoding: "utf8",
                        cwd: process.cwd(),
                    });
                    return output || "No lint errors found.";
                } catch (err) {
                    // eslint exits non-zero on lint errors — output is still useful
                    return err.stdout || err.message;
                }
            },
        },
    ],

    hooks: {
        onSessionStart: async (input, invocation) => {
            await session.log(`Extension ready. Session source: ${input.source}`);
        },

        onPreToolUse: async (input, invocation) => {
            // Allow all tool calls — log writes for audit
            if (input.toolName === "edit" || input.toolName === "bash") {
                await session.log(`Tool call: ${input.toolName}`, { ephemeral: true });
            }
            // Return undefined to allow the tool call to proceed unchanged
        },

        onSessionEnd: async (input, invocation) => {
            // Return a summary to be persisted with the session
            return { sessionSummary: `Session ended: ${input.reason}` };
        },
    },
});
```

---

## Hook Reference

All hooks are passed as `hooks` in `joinSession()`. All handlers are async-safe and receive `(input, invocation)`.

| Hook | Input fields | Return fields |
|---|---|---|
| `onUserPromptSubmitted` | `prompt`, `timestamp`, `cwd` | `modifiedPrompt`, `additionalContext` |
| `onPreToolUse` | `toolName`, `toolArgs`, `timestamp`, `cwd` | `permissionDecision`, `permissionDecisionReason`, `modifiedArgs`, `additionalContext` |
| `onPostToolUse` | `toolName`, `toolArgs`, `toolResult`, `timestamp`, `cwd` | `modifiedResult`, `additionalContext` |
| `onSessionStart` | `source`, `initialPrompt?`, `timestamp`, `cwd` | `additionalContext` |
| `onSessionEnd` | `reason`, `finalMessage?`, `error?`, `timestamp`, `cwd` | `sessionSummary`, `cleanupActions` |
| `onErrorOccurred` | `error`, `errorContext`, `recoverable`, `timestamp`, `cwd` | `errorHandling`, `retryCount`, `userNotification` |

All return fields are optional. Returning `undefined` (or `void`) means no-op for that hook.

---

## Key Gotchas

- Do not call `session.send()` synchronously inside `onUserPromptSubmitted`. Wrap it in `setTimeout(() => session.send(...), 0)` to prevent infinite prompt loops.
- Extensions are reloaded on `/clear` — any in-memory state (caches, open connections) is lost. Re-initialize in `onSessionStart`.
- Only `.mjs` is supported. There is no TypeScript support — transpile `.ts` to `.mjs` with `esbuild` or `tsc` before use if needed.
- The `handler` return value is the complete tool result. Returning `undefined` sends an empty success to the model.
- `overridesBuiltInTool: true` must be set on a tool definition if the tool name intentionally matches a built-in tool name. Without it, loading fails with a collision error.
