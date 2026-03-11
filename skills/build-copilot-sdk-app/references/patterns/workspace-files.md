# Workspace File Operations

## Three Workspace RPC Methods

The session workspace namespace provides three operations for managing files within the session's workspace directory:

```typescript
// List all files in the workspace
const { files } = await session.rpc.workspace.listFiles();
// Returns: { files: string[] } — relative paths within workspace

// Read a file by relative path
const { content } = await session.rpc.workspace.readFile({ path: "output.json" });
// Returns: { content: string } — UTF-8 file content

// Create or overwrite a file
await session.rpc.workspace.createFile({
  path: "config/settings.json",
  content: JSON.stringify({ key: "value" }, null, 2),
});
// Returns: {} — empty result on success
```

## Workspace vs. Built-in File Tools

The workspace RPCs operate on the session's **workspace files directory** — a managed directory separate from the working directory used by the agent's built-in file tools (`str_replace_editor`, `bash`, etc.).

| Aspect | Workspace RPCs | Built-in File Tools (agent) |
|---|---|---|
| Operated by | Your SDK code (the controller) | The agent (LLM-directed) |
| Scope | Session workspace directory | Working directory and filesystem |
| Paths | Relative to workspace root | Absolute or relative to `workingDirectory` |
| Use case | Injecting inputs, reading outputs | Code editing, file manipulation |

Use workspace RPCs to **communicate with the agent** — pass structured inputs in, read structured outputs out. Do not use them as a general filesystem API.

## Path Resolution

Paths passed to `readFile` and `createFile` are **relative** to the session's workspace files directory. Do not use absolute paths or path traversal sequences.

```typescript
// CORRECT: relative path within workspace
await session.rpc.workspace.createFile({
  path: "tasks/task-001.md",
  content: "# Task\nImplement feature X",
});

// CORRECT: nested paths are supported
await session.rpc.workspace.createFile({
  path: "context/api-spec.json",
  content: JSON.stringify(apiSpec),
});

// WRONG: absolute path — behavior undefined
await session.rpc.workspace.createFile({
  path: "/tmp/file.txt",  // Do not use
  content: "...",
});
```

The workspace directory is created and managed by the CLI. Its absolute path is returned by `session.rpc.plan.read()` when the plan file exists (the `path` field in the result).

## Listing Workspace Files

```typescript
const result = await session.rpc.workspace.listFiles();
// result.files: string[] — relative paths, e.g. ["output.json", "logs/step1.txt"]

console.log("Workspace contains:", result.files);

for (const filePath of result.files) {
  console.log(" -", filePath);
}
```

Returns an empty array if no workspace files exist yet.

## Reading Workspace Files

```typescript
const { content } = await session.rpc.workspace.readFile({ path: "output.json" });

// Parse structured output from agent
const output = JSON.parse(content);
console.log("Agent output:", output);
```

`readFile` throws if the file does not exist. Always check `listFiles()` first or handle the error:

```typescript
async function readWorkspaceFileSafe(
  session: CopilotSession,
  path: string
): Promise<string | null> {
  try {
    const { content } = await session.rpc.workspace.readFile({ path });
    return content;
  } catch {
    return null;
  }
}
```

## Creating Workspace Files

`createFile` creates a file or overwrites it if it already exists. It creates parent directories as needed.

```typescript
// Inject a task specification for the agent to consume
await session.rpc.workspace.createFile({
  path: "task.md",
  content: `# Task\n\n${taskDescription}\n\n## Requirements\n${requirements}`,
});

// Inject structured configuration
await session.rpc.workspace.createFile({
  path: "config.json",
  content: JSON.stringify({
    apiEndpoint: "https://api.example.com",
    retryLimit: 3,
    outputFormat: "json",
  }, null, 2),
});
```

## When to Use Workspace RPCs

**Use workspace RPCs when:**
- Injecting input files before sending a prompt (structured specs, config, reference data)
- Reading output files the agent was instructed to write
- Passing large structured data that would bloat the prompt itself
- Checking whether the agent produced expected output files

**Do not use workspace RPCs when:**
- You want the agent to read arbitrary files from the project — use `workingDirectory` and let the agent use its built-in tools
- You need general file I/O in your application — use Node.js `fs` module directly
- The agent needs to edit source code files — those live in the working directory, not the workspace

## Injecting Input Before Prompting

```typescript
const session = await client.createSession({
  model: "claude-sonnet-4.5",
  onPermissionRequest: async () => ({ kind: "approved" }),
});

// Step 1: Write input files to workspace
await session.rpc.workspace.createFile({
  path: "spec.md",
  content: featureSpecContent,
});

await session.rpc.workspace.createFile({
  path: "examples.json",
  content: JSON.stringify(exampleData, null, 2),
});

// Step 2: Send prompt referencing workspace files
await session.send({
  prompt: "Read spec.md and examples.json from your workspace, then implement the feature described.",
});

await session.waitForIdle();

// Step 3: Read output the agent was asked to produce
const report = await readWorkspaceFileSafe(session, "implementation-report.md");
console.log(report);
```

## Batch File Operation Patterns

### Inject Multiple Files

```typescript
const inputFiles: Array<{ path: string; content: string }> = [
  { path: "requirements/auth.md", content: authSpec },
  { path: "requirements/payments.md", content: paymentSpec },
  { path: "context/existing-models.ts", content: existingModels },
];

// Create all input files in parallel
await Promise.all(
  inputFiles.map(({ path, content }) =>
    session.rpc.workspace.createFile({ path, content })
  )
);

await session.send({
  prompt: "Review all files in requirements/ and implement them. Use context/ for reference.",
});
```

### Read All Output Files

```typescript
await session.waitForIdle();

// List and read all output files the agent produced
const { files } = await session.rpc.workspace.listFiles();
const outputFiles = files.filter(f => f.startsWith("output/"));

const outputs = await Promise.all(
  outputFiles.map(async (path) => ({
    path,
    content: await session.rpc.workspace.readFile({ path }).then(r => r.content),
  }))
);

for (const { path, content } of outputs) {
  console.log(`\n=== ${path} ===\n${content}`);
}
```

## RPC Type Reference

From the generated RPC schema:

```typescript
// session.rpc.workspace.listFiles()
interface SessionWorkspaceListFilesResult {
  files: string[];  // Relative paths within workspace
}

// session.rpc.workspace.readFile({ path })
interface SessionWorkspaceReadFileParams {
  path: string;  // Relative path within workspace files directory
}
interface SessionWorkspaceReadFileResult {
  content: string;  // UTF-8 file content
}

// session.rpc.workspace.createFile({ path, content })
interface SessionWorkspaceCreateFileParams {
  path: string;   // Relative path within workspace files directory
  content: string; // UTF-8 content to write
}
interface SessionWorkspaceCreateFileResult {}  // Empty on success
```

All methods are on `session.rpc.workspace.*`. The `sessionId` is injected automatically by the SDK — do not pass it manually.
