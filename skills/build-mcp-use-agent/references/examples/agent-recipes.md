# Agent Recipes

Complete, runnable TypeScript examples for every common MCPAgent pattern. Each recipe includes all imports, proper error handling with try/finally, and agent cleanup via `agent.close()`.

---

## 1. Minimal One-Shot Agent

The simplest possible MCPAgent example. Uses simplified constructor mode with an inline server config. Sends a single prompt and prints the result.

---

```typescript
/**
 * Recipe 1 — Minimal One-Shot Agent
 *
 * Demonstrates the shortest path from zero to a working agent.
 * Uses the simplified constructor (string LLM identifier + inline
 * mcpServers map) so you don't need to create an MCPClient yourself.
 *
 * Requirements:
 *   OPENAI_API_KEY in environment
 *   npx available on PATH
 */

import { MCPAgent } from "mcp-use";

async function main(): Promise<void> {
  // Simplified constructor — pass the LLM as a string and servers inline.
  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: {
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
    maxSteps: 15,
  });

  try {
    // agent.run() requires an object with a prompt
    const result = await agent.run({ prompt: "List every tool you have access to and describe what each one does." });

    console.log("=== Agent Response ===");
    console.log(result);
  } finally {
    // Always close the agent to tear down MCP server processes.
    await agent.close();
  }
}

main().catch((err) => {
  console.error("Agent failed:", err);
  process.exit(1);
});
```

**Key takeaways:**

- `llm: "openai/gpt-4o"` — the simplified string form auto-creates a ChatOpenAI instance.
- `mcpServers` — define server configs inline; no need for a separate MCPClient.
- `agent.run({ prompt: "..." })` — standard execution.
- `agent.close()` — must always be called, even on error. Use try/finally.

---

## 2. Interactive Chat Loop

A readline-based conversational agent with persistent memory. Supports special commands: `exit` to quit, `clear` to reset conversation history, and `help` to show available commands. Memory accumulates across turns so the agent remembers earlier context.

---

```typescript
/**
 * Recipe 2 — Interactive Chat Loop
 *
 * Builds a terminal chat UI where each user message becomes an
 * agent.run() call. Because memoryEnabled defaults to true, the
 * agent remembers previous turns automatically.
 *
 * Special commands:
 *   exit  — end the conversation
 *   clear — wipe conversation history (agent.clearConversationHistory)
 *   help  — show command reference
 *
 * Requirements:
 *   OPENAI_API_KEY in environment
 *   npx available on PATH
 */

import readline from "node:readline";
import { MCPAgent } from "mcp-use";

async function chat(): Promise<void> {
  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: {
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
    maxSteps: 20,
    // memoryEnabled defaults to true — conversation accumulates automatically
  });

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const ask = (prompt: string): Promise<string> =>
    new Promise((resolve) => rl.question(prompt, resolve));

  const HELP_TEXT = `
Commands:
  exit   — end the conversation
  clear  — reset conversation memory
  help   — show this message
  
Anything else is sent to the agent as a prompt.
Memory persists across turns, so the agent remembers context.
`.trim();

  console.log("🤖 MCP Chat Agent (type 'help' for commands)\n");

  try {
    while (true) {
      const input = (await ask("You: ")).trim();
      if (!input) continue;

      // Handle special commands
      switch (input.toLowerCase()) {
        case "exit":
        case "quit":
          console.log("Goodbye!");
          return;

        case "clear":
          agent.clearConversationHistory();
          console.log("🧹 Conversation history cleared.\n");
          continue;

        case "help":
          console.log(`\n${HELP_TEXT}\n`);
          continue;
      }

      // Send user message to the agent
      console.log("  ⏳ Thinking...");
      const response = await agent.run({ prompt: input });
      console.log(`\nAssistant: ${response}\n`);
    }
  } finally {
    rl.close();
    await agent.close();
  }
}

chat().catch((err) => {
  console.error("Chat failed:", err);
  process.exit(1);
});
```

**Key takeaways:**

- Memory accumulates by default — turn 3 can reference answers from turn 1.
- `agent.clearConversationHistory()` wipes all memory, starting fresh.
- `agent.run({ prompt: input })` — pass input as the prompt property.
- Always close both `readline` and the agent in the finally block.

---

## 3. Filesystem Agent

Connects to the official `@modelcontextprotocol/server-filesystem` MCP server to analyze project structure, count files by type, and read configuration files. Shows both the simplified constructor mode and the explicit MCPClient mode side by side.

---

```typescript
/**
 * Recipe 3 — Filesystem Agent
 *
 * Variant A: Simplified mode (inline mcpServers).
 * Variant B: Explicit mode (MCPClient + ChatOpenAI).
 *
 * Task: Analyze the project directory — count files by extension,
 * read package.json and tsconfig.json, summarize structure.
 *
 * Requirements:
 *   OPENAI_API_KEY in environment
 *   npx available on PATH
 *   A real project directory to analyze
 */

import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";

// ---------- Variant A: Simplified mode ----------

async function simplifiedFilesystemAgent(): Promise<void> {
  const projectDir = process.argv[2] || process.cwd();
  console.log(`\n📂 Analyzing directory: ${projectDir}\n`);

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", projectDir],
      },
    },
    maxSteps: 30,
  });

  try {
    const result = await agent.run({
      prompt: `Analyze the project at ${projectDir}:
1. List the top-level directory structure.
2. Count files by extension (e.g., .ts, .js, .json, .md).
3. Read package.json (if it exists) and summarize dependencies.
4. Read tsconfig.json (if it exists) and summarize compiler options.
5. Provide a brief project overview based on your findings.`,
      maxSteps: 30,
    });
    console.log("=== Simplified Mode Result ===");
    console.log(result);
  } finally {
    await agent.close();
  }
}

// ---------- Variant B: Explicit MCPClient mode ----------

async function explicitFilesystemAgent(): Promise<void> {
  const projectDir = process.argv[2] || process.cwd();
  console.log(`\n📂 Analyzing directory (explicit mode): ${projectDir}\n`);

  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", projectDir],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o", temperature: 0 }),
    client,
    maxSteps: 30,
  });

  try {
    const result = await agent.run({
      prompt: `Perform a deep analysis of the project directory:
1. Recursively list all files and group them by directory.
2. Identify the main entry point (index.ts, main.ts, etc.).
3. Read any README.md and summarize the project purpose.
4. Check for common config files (.eslintrc, .prettierrc, Dockerfile).
5. Report total file count and estimated lines of code.`,
      maxSteps: 30,
    });
    console.log("=== Explicit Mode Result ===");
    console.log(result);
  } finally {
    await agent.close();
  }
}

// Run the variant based on a flag
const variant = process.argv.includes("--explicit") ? "explicit" : "simplified";

if (variant === "explicit") {
  explicitFilesystemAgent().catch(console.error);
} else {
  simplifiedFilesystemAgent().catch(console.error);
}
```

**Key takeaways:**

- **Simplified mode** — `llm: "openai/gpt-4o"` plus `mcpServers` inline is the fastest setup.
- **Explicit mode** — `new MCPClient(...)` + `new ChatOpenAI(...)` gives you full control over both the LLM and transport configuration.
- The filesystem server needs an allowed directory passed as the last arg.
- Use `process.cwd()` or a CLI argument to make the script reusable.

---

## 4. Browser Automation Agent

Connects to the Playwright MCP server to automate a real browser. Navigates to a URL, extracts page content, and takes a screenshot. Includes environment variable configuration for headless mode.

---

```typescript
/**
 * Recipe 4 — Browser Automation Agent
 *
 * Uses @playwright/mcp@latest to control a browser. The agent
 * navigates to a target URL, extracts structured data, and
 * captures a screenshot.
 *
 * Environment variables:
 *   OPENAI_API_KEY    — required
 *   BROWSER_HEADLESS  — set to "true" for headless mode (default: headed)
 *   TARGET_URL        — URL to visit (default: https://news.ycombinator.com)
 *
 * Requirements:
 *   npx available on PATH
 *   Playwright browsers installed (npx playwright install chromium)
 */

import { MCPAgent } from "mcp-use";

async function main(): Promise<void> {
  const targetUrl =
    process.env.TARGET_URL || "https://news.ycombinator.com";
  const isHeadless = process.env.BROWSER_HEADLESS === "true";

  console.log(`🌐 Browser Agent targeting: ${targetUrl}`);
  console.log(`   Headless mode: ${isHeadless}\n`);

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: {
      playwright: {
        command: "npx",
        args: [
          "@playwright/mcp@latest",
          ...(isHeadless ? ["--headless"] : []),
        ],
        env: {
          ...process.env,
          DISPLAY: process.env.DISPLAY || ":1",
        },
      },
    },
    maxSteps: 25,
  });

  try {
    const result = await agent.run({
      prompt: `Perform these browser tasks:
1. Navigate to ${targetUrl}.
2. Wait for the page to fully load.
3. Extract the page title and the first 10 headlines or link texts.
4. Take a screenshot of the current page.
5. Summarize what you found in a structured format.`,
      maxSteps: 25,
    });

    console.log("=== Browser Agent Result ===");
    console.log(result);
  } finally {
    await agent.close();
  }
}

main().catch((err) => {
  console.error("Browser agent failed:", err);
  process.exit(1);
});
```

**Key takeaways:**

- `@playwright/mcp@latest` starts a Playwright MCP server that the agent can control.
- Pass `--headless` to run without a visible browser window (CI/CD friendly).
- `DISPLAY` env var is needed on Linux for headed mode in X11 environments.
- The agent can navigate, click, type, extract text, and take screenshots.

---

## 5. Multi-Server Agent

Connects to three MCP servers simultaneously — filesystem, Playwright, and Everything. Performs a task that requires coordinating across all three servers. Uses `useServerManager: true` so the agent intelligently picks which server to use for each tool call.

---

```typescript
/**
 * Recipe 5 — Multi-Server Agent
 *
 * Connects to multiple MCP servers at once. The agent uses the
 * server manager to route tool calls to the correct server.
 *
 * Servers:
 *   filesystem  — read/write local files
 *   playwright  — automate a browser
 *   everything  — test/demo tools, resources, prompts
 *
 * Requirements:
 *   OPENAI_API_KEY in environment
 *   npx available on PATH
 */

import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";

async function main(): Promise<void> {
  const workDir = process.cwd();

  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", workDir],
      },
      playwright: {
        command: "npx",
        args: ["@playwright/mcp@latest", "--headless"],
        env: { ...process.env },
      },
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o", temperature: 0 }),
    client,
    maxSteps: 40,
    useServerManager: true,
    verbose: true,
  });

  try {
    const result = await agent.run({
      prompt: `You have access to three different MCP servers. Complete these tasks:

1. FILESYSTEM SERVER: List the files in the current directory and read any
   README.md file if present.

2. EVERYTHING SERVER: List all available tools from the Everything test server
   and try the "echo" tool with the message "Hello from multi-server agent".

3. PLAYWRIGHT SERVER: Navigate to https://example.com, extract the page title
   and main heading text.

4. CROSS-SERVER: Write a summary of everything you found to a file called
   "multi-server-report.txt" using the filesystem server.

Report which server you used for each step.`,
      maxSteps: 40,
    });

    console.log("\n=== Multi-Server Agent Result ===");
    console.log(result);
  } finally {
    await client.closeAllSessions();
  }
}

main().catch((err) => {
  console.error("Multi-server agent failed:", err);
  process.exit(1);
});
```

**Key takeaways:**

- `useServerManager: true` lets the agent dynamically pick servers per tool call.
- When using an explicit `MCPClient`, call `client.closeAllSessions()` in the finally block.
- Mix `npx` (Node servers) and `uvx` (Python servers) freely in the same config.
- `verbose: true` prints which server and tool the agent selects at each step.

---

## 6. Structured Output Agent

Uses a Zod schema with `agent.run({ prompt, schema })` to get validated, typed responses. Defines a complex nested schema with arrays and optional fields, demonstrating full type safety from the agent response.

---

```typescript
/**
 * Recipe 6 — Structured Output Agent
 *
 * Returns a validated Zod object instead of a plain string.
 * The schema is passed to agent.run() and the LLM is constrained
 * to produce output matching exactly that shape.
 *
 * Requirements:
 *   OPENAI_API_KEY in environment
 *   npx available on PATH
 *   zod installed (npm install zod)
 */

import { z } from "zod";
import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";

// Define a complex nested schema for project analysis
const ProjectAnalysisSchema = z.object({
  projectName: z.string().describe("Name of the project"),
  description: z.string().describe("Brief project description"),
  language: z.string().describe("Primary programming language"),
  framework: z.string().nullable().describe("Framework used, if any"),
  dependencies: z.object({
    production: z.array(z.string()).describe("Production dependency names"),
    development: z.array(z.string()).describe("Dev dependency names"),
    total: z.number().describe("Total number of dependencies"),
  }),
  structure: z.object({
    totalFiles: z.number().describe("Total number of files"),
    totalDirectories: z.number().describe("Total number of directories"),
    entryPoint: z.string().nullable().describe("Main entry point file"),
    hasTests: z.boolean().describe("Whether the project has tests"),
    hasCI: z.boolean().describe("Whether CI/CD config exists"),
  }),
  healthScore: z
    .number()
    .min(1)
    .max(10)
    .describe("Overall project health score from 1-10"),
  recommendations: z
    .array(z.string())
    .describe("List of improvement recommendations"),
});

type ProjectAnalysis = z.infer<typeof ProjectAnalysisSchema>;

async function main(): Promise<void> {
  const projectDir = process.argv[2] || process.cwd();

  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", projectDir],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o", temperature: 0 }),
    client,
    maxSteps: 30,
  });

  try {
    const analysis: ProjectAnalysis = await agent.run({
      prompt: `Thoroughly analyze the project at ${projectDir}:
1. Read package.json for project name, description, and dependencies.
2. Scan the directory structure for file counts and organization.
3. Check for test directories, CI configs (.github/workflows, .gitlab-ci.yml).
4. Identify the framework and primary language.
5. Assess overall project health and provide recommendations.`,
      schema: ProjectAnalysisSchema,
      maxSteps: 30,
    });

    // The result is fully typed — TypeScript knows the shape
    console.log("\n=== Project Analysis (Structured) ===\n");
    console.log(`Project:     ${analysis.projectName}`);
    console.log(`Language:    ${analysis.language}`);
    console.log(`Framework:   ${analysis.framework ?? "none"}`);
    console.log(`Description: ${analysis.description}`);
    console.log();
    console.log(`Files:        ${analysis.structure.totalFiles}`);
    console.log(`Directories:  ${analysis.structure.totalDirectories}`);
    console.log(`Entry Point:  ${analysis.structure.entryPoint ?? "unknown"}`);
    console.log(`Has Tests:    ${analysis.structure.hasTests}`);
    console.log(`Has CI:       ${analysis.structure.hasCI}`);
    console.log();
    console.log(`Dependencies: ${analysis.dependencies.total} total`);
    console.log(`  Production: ${analysis.dependencies.production.join(", ")}`);
    console.log(`  Dev:        ${analysis.dependencies.development.join(", ")}`);
    console.log();
    console.log(`Health Score: ${analysis.healthScore}/10`);
    console.log();
    console.log("Recommendations:");
    analysis.recommendations.forEach((rec, i) => {
      console.log(`  ${i + 1}. ${rec}`);
    });
  } finally {
    await agent.close();
  }
}

main().catch((err) => {
  console.error("Structured output agent failed:", err);
  process.exit(1);
});
```

**Key takeaways:**

- Pass a Zod schema to `agent.run({ prompt, schema })` for structured output.
- The return type is `z.infer<typeof Schema>` — fully typed, no casting needed.
- Use `.describe()` on every Zod field so the LLM understands what to populate.
- Complex nested schemas with arrays, nullables, and ranges all work.
- To stream structured output, pass the same `schema` to `agent.streamEvents({ prompt, schema })` and check `event.event` for `"on_structured_output_progress"`, `"on_structured_output"` (result at `event.data.output`), and `"on_structured_output_error"`.

---

## 7. Streaming CLI Agent

Uses `agent.stream()` to display real-time step-by-step progress as the agent works. Each tool call and observation is printed as it happens. Also demonstrates the `agent.prettyStreamEvents()` variant for automatic ANSI-formatted output, and `agent.streamEvents()` for low-level LangChain event access.

---

```typescript
/**
 * Recipe 7 — Streaming CLI Agent
 *
 * Three streaming modes:
 *   1. agent.stream(prompt)            — manual step iteration via AsyncGenerator
 *                                        accepts plain string (deprecated) or options object { prompt, maxSteps?, schema? }
 *   2. agent.streamEvents(prompt)      — low-level LangChain StreamEvents
 *                                        accepts plain string (deprecated) or options object { prompt, schema?, maxSteps? }
 *   3. agent.prettyStreamEvents({...}) — auto-formatted ANSI terminal output
 *                                        always takes an options object { prompt, maxSteps?, schema? }
 *
 * Requirements:
 *   OPENAI_API_KEY in environment
 *   npx available on PATH
 */

import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";

// ==========================================
// Mode 1: Manual streaming with agent.stream()
// ==========================================

async function manualStreaming(): Promise<void> {
  console.log("\n" + "=".repeat(60));
  console.log("  Mode 1: Manual Streaming (agent.stream)");
  console.log("=".repeat(60) + "\n");

  const client = new MCPClient({
    mcpServers: {
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    maxSteps: 15,
  });

  try {
    // agent.stream() takes a plain string prompt
    const stream = agent.stream(
      "List all available tools, then use the echo tool with 'Hello streaming world!'"
    );

    let stepNumber = 1;
    let finalResult = "";

    while (true) {
      const { done, value } = await stream.next();

      if (done) {
        // When done === true, `value` is the final string result
        finalResult = value;
        break;
      }

      // Each yielded value has { action: { tool, toolInput, log }, observation }
      const toolName = value.action.tool;
      const toolInput = JSON.stringify(value.action.toolInput, null, 2);

      console.log(`┌─── Step ${stepNumber} ───────────────────────`);
      console.log(`│ Tool:  ${toolName}`);
      console.log(`│ Input: ${toolInput}`);
      console.log(`└${"─".repeat(40)}\n`);

      stepNumber++;
    }

    console.log("─".repeat(60));
    console.log("Final Result:");
    console.log(finalResult);
  } finally {
    await agent.close();
  }
}

// ==========================================
// Mode 2: Low-level streaming with agent.streamEvents()
// ==========================================

async function lowLevelStreaming(): Promise<void> {
  console.log("\n" + "=".repeat(60));
  console.log("  Mode 2: Low-Level Stream Events (agent.streamEvents)");
  console.log("=".repeat(60) + "\n");

  const client = new MCPClient({
    mcpServers: {
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    maxSteps: 15,
  });

  try {
    // agent.streamEvents() takes a plain string prompt and yields LangChain StreamEvents
    for await (const event of agent.streamEvents(
      "Search for the latest Python news and summarize it"
    )) {
      if (event.event === "on_chat_model_stream") {
        // chunk.text or chunk.content depending on LLM provider
        const text = event.data?.chunk?.text || event.data?.chunk?.content;
        if (typeof text === "string" && text.length > 0) {
          process.stdout.write(text);
        }
      }
      if (event.event === "on_tool_start") {
        console.log(`\n[tool_start] ${event.name}`);
      }
      if (event.event === "on_tool_end") {
        console.log(`[tool_end] ${event.name}\n`);
      }
    }
    console.log(); // newline after streamed tokens
  } finally {
    await agent.close();
  }
}

// ==========================================
// Mode 3: Pretty stream events (auto ANSI)
// ==========================================

async function prettyStreaming(): Promise<void> {
  console.log("\n" + "=".repeat(60));
  console.log("  Mode 3: Pretty Stream Events (auto ANSI)");
  console.log("=".repeat(60) + "\n");

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: {
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
    maxSteps: 10,
  });

  try {
    // prettyStreamEvents takes an options object { prompt, maxSteps?, schema? }
    // and auto-prints formatted output to stdout
    for await (const _event of agent.prettyStreamEvents({
      prompt: "List available tools and try the echo tool with 'Pretty mode!'",
      maxSteps: 10,
    })) {
      // Output is automatically printed — no manual formatting needed.
      // The iterator yields raw LangChain StreamEvents if you need them.
    }
  } finally {
    await agent.close();
  }
}

// Run the selected mode
async function main(): Promise<void> {
  const mode = process.argv.includes("--pretty")
    ? "pretty"
    : process.argv.includes("--events")
    ? "events"
    : "manual";

  if (mode === "pretty") {
    await prettyStreaming();
  } else if (mode === "events") {
    await lowLevelStreaming();
  } else {
    await manualStreaming();
  }
}

main().catch((err) => {
  console.error("Streaming agent failed:", err);
  process.exit(1);
});
```

**Key takeaways:**

- `agent.stream("prompt")` — deprecated plain string form, still works. `agent.stream({ prompt, maxSteps?, schema? })` — preferred options object form. Returns an `AsyncGenerator<AgentStep, string | T, void>`. Each yielded `AgentStep` has `{ action: { tool, toolInput, log }, observation }`. When iterating with `.next()` and `done === true`, `value` is the final string result.
- `agent.streamEvents("prompt")` — deprecated plain string form. `agent.streamEvents({ prompt, schema? })` — preferred options object form. Yields low-level LangChain `StreamEvent` objects. Use `event.data?.chunk?.text || event.data?.chunk?.content` to extract tokens (`.text` for Anthropic, `.content` for OpenAI).
- When using `agent.streamEvents({ prompt, schema })` with a schema, listen for `"on_structured_output_progress"`, `"on_structured_output"` (result at `event.data.output`), and `"on_structured_output_error"` events.
- `agent.prettyStreamEvents({ prompt, maxSteps?, schema? })` — always takes an **options object** (no plain string form). Auto-formats everything with ANSI colors. Accepts an optional Zod `schema`.
- Use `stream()` when you need per-step tool call visibility; use `streamEvents()` when you need token-level or raw LangChain event access.

---

## 8. Code Execution Agent

Uses `codeMode: true` on MCPClient to enable code execution capabilities. Connects to a filesystem server and writes executable scripts to a temporary directory. Demonstrates proper temp directory management and cleanup.

Note: `codeMode` is an MCPClient option, not an MCPAgent option. The pattern is: enable `codeMode` on the client, then pair it with `PROMPTS.CODE_MODE` on the agent's `systemPrompt`.

---

```typescript
/**
 * Recipe 8 — Code Execution Agent
 *
 * Enables code mode on MCPClient so the agent can write and reason about code.
 * Uses PROMPTS.CODE_MODE for the system prompt and connects to a
 * filesystem server scoped to a temporary working directory.
 *
 * Requirements:
 *   OPENAI_API_KEY in environment
 *   npx available on PATH
 */

import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { MCPAgent, MCPClient, PROMPTS } from "mcp-use";

async function main(): Promise<void> {
  // Create a temporary working directory for the agent
  const tempDir = await mkdtemp(join(tmpdir(), "mcp-code-agent-"));
  console.log(`Working directory: ${tempDir}\n`);

  // codeMode belongs on MCPClient, not MCPAgent
  const client = new MCPClient(
    {
      mcpServers: {
        filesystem: {
          command: "npx",
          args: ["-y", "@modelcontextprotocol/server-filesystem", tempDir],
        },
      },
    },
    { codeMode: true }
  );

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    client,
    maxSteps: 30,
    systemPrompt: PROMPTS.CODE_MODE,
  });

  try {
    // Task 1: Write a utility module
    console.log("--- Task 1: Write a utility module ---\n");
    const task1 = await agent.run({
      prompt: `Write a TypeScript utility file called "string-utils.ts" in the working
directory. It should export these functions:
  - capitalize(str: string): string — capitalizes the first letter
  - slugify(str: string): string — converts to URL-safe slug
  - truncate(str: string, maxLen: number): string — truncates with "..."
  - countWords(str: string): number — counts words in a string

Include JSDoc comments for each function.`,
      maxSteps: 15,
    });
    console.log(task1);

    // Task 2: Write tests for the utility module
    console.log("\n--- Task 2: Write tests ---\n");
    const task2 = await agent.run({
      prompt: `Now write a test file called "string-utils.test.ts" that tests all four
functions from string-utils.ts. Use simple assert-style checks (no test
framework needed). Include edge cases like empty strings and special
characters. Write it to the same working directory.`,
      maxSteps: 15,
    });
    console.log(task2);

    // Task 3: Read back and verify the files
    console.log("\n--- Task 3: Verify written files ---\n");
    const task3 = await agent.run({
      prompt: `Read both files you just created (string-utils.ts and
string-utils.test.ts) and verify they are syntactically correct.
Report the total line count for each file.`,
      maxSteps: 10,
    });
    console.log(task3);
  } finally {
    await agent.close();

    // Clean up the temporary directory
    try {
      await rm(tempDir, { recursive: true, force: true });
      console.log(`\n🧹 Cleaned up temp directory: ${tempDir}`);
    } catch {
      console.warn(`⚠️  Could not clean up ${tempDir}`);
    }
  }
}

main().catch((err) => {
  console.error("Code execution agent failed:", err);
  process.exit(1);
});
```

**Key takeaways:**

- `codeMode: true` belongs on `MCPClient` (second constructor argument), not on `MCPAgent`.
- Pair `codeMode` with `PROMPTS.CODE_MODE` as the agent's `systemPrompt` for best results.
- Use `mkdtemp()` to create an isolated temp directory for the agent to work in.
- Always clean up the temp directory in the finally block with `rm(dir, { recursive: true })`.
- The agent can chain multiple `run()` calls, and memory persists between them.

---

## 9. Agent with Custom System Prompt

Demonstrates three ways to customize the agent's behavior through prompts: `systemPrompt` for a complete override, `systemPromptTemplate` with variable interpolation, and `additionalInstructions` for task-specific guidance layered on top of the default prompt.

---

```typescript
/**
 * Recipe 9 — Agent with Custom System Prompt
 *
 * Three customization levels:
 *   1. systemPrompt           — full system prompt override (string)
 *   2. systemPromptTemplate   — template with {variable} interpolation
 *   3. additionalInstructions — appended to the default system prompt
 *
 * Requirements:
 *   OPENAI_API_KEY in environment
 *   npx available on PATH
 */

import { MCPAgent } from "mcp-use";

// ---------- Example 1: Full system prompt override ----------

async function withFullSystemPrompt(): Promise<void> {
  console.log("\n" + "=".repeat(50));
  console.log("  Example 1: Full System Prompt Override");
  console.log("=".repeat(50) + "\n");

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: {
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
    maxSteps: 15,
    systemPrompt: `You are a pirate-themed technical assistant. You must:
- Always speak in pirate dialect ("Arrr", "ye", "matey", etc.)
- Still provide accurate technical information
- End every response with a pirate saying
- Use nautical metaphors when explaining concepts

You have access to MCP tools. Use them when asked, but describe
your actions in pirate speak.`,
  });

  try {
    const result = await agent.run({ prompt: "List all available tools and describe what each one does." });
    console.log(result);
  } finally {
    await agent.close();
  }
}

// ---------- Example 2: System prompt template ----------

async function withSystemPromptTemplate(): Promise<void> {
  console.log("\n" + "=".repeat(50));
  console.log("  Example 2: System Prompt Template");
  console.log("=".repeat(50) + "\n");

  const userName = process.env.USER || "developer";
  const expertise = "TypeScript and Node.js";

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: {
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
    maxSteps: 15,
    systemPrompt: `You are a personal coding assistant for ${userName}.
Their expertise level is intermediate in ${expertise}.

Guidelines:
- Adjust explanations for an intermediate ${expertise} developer.
- Use ${expertise} idioms and best practices.
- Reference official documentation when relevant.
- Proactively suggest improvements the user might not think of.

Available tools: Use any MCP tools to help answer questions.`,
  });

  try {
    const result = await agent.run({ prompt: "What tools do you have? Give me a quick overview." });
    console.log(result);
  } finally {
    await agent.close();
  }
}

// ---------- Example 3: Additional instructions ----------

async function withAdditionalInstructions(): Promise<void> {
  console.log("\n" + "=".repeat(50));
  console.log("  Example 3: Additional Instructions");
  console.log("=".repeat(50) + "\n");

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: {
      everything: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
      },
    },
    maxSteps: 15,
    additionalInstructions: `IMPORTANT task-specific rules:
- Always format output as markdown tables when comparing items.
- Include confidence percentages for any estimates.
- If unsure about something, say so explicitly rather than guessing.
- Limit responses to 300 words maximum.`,
  });

  try {
    const result = await agent.run({ prompt: "List all available tools and compare their capabilities in a table." });
    console.log(result);
  } finally {
    await agent.close();
  }
}

// Run all examples
async function main(): Promise<void> {
  await withFullSystemPrompt();
  await withSystemPromptTemplate();
  await withAdditionalInstructions();
}

main().catch((err) => {
  console.error("Custom prompt agent failed:", err);
  process.exit(1);
});
```

**Key takeaways:**

- `systemPrompt` completely replaces the default prompt — use when you need full control.
- Template interpolation uses standard JS template literals (`` `Hello ${name}` ``).
- `additionalInstructions` is appended to the default prompt — best for adding rules without losing built-in behavior.
- All three approaches work with any LLM and server configuration.

---

## 10. Agent with Tool Restrictions

Uses `setDisallowedTools()` to block specific tools at runtime. Demonstrates environment-based restrictions (e.g., blocking write operations in production) and dynamic restriction changes during agent lifecycle.

---

```typescript
/**
 * Recipe 10 — Agent with Tool Restrictions
 *
 * Shows how to restrict which tools an agent can use:
 *   - setDisallowedTools(tools) — block a list of tool names
 *   - getDisallowedTools()      — inspect current restrictions
 *   - Environment-based restrictions (prod vs dev)
 *
 * Requirements:
 *   OPENAI_API_KEY in environment
 *   npx available on PATH
 */

import { MCPAgent } from "mcp-use";

async function main(): Promise<void> {
  const isProduction = process.env.NODE_ENV === "production";

  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
      },
    },
    maxSteps: 20,
  });

  // Define environment-based restrictions
  const prodBlockedTools = [
    "write_file",
    "create_directory",
    "move_file",
    "edit_file",
  ];

  const devBlockedTools = [
    // In dev, only block truly dangerous operations
    "move_file",
  ];

  // Apply restrictions based on environment
  const blockedTools = isProduction ? prodBlockedTools : devBlockedTools;
  agent.setDisallowedTools(blockedTools);

  console.log(`🔒 Environment: ${isProduction ? "PRODUCTION" : "DEVELOPMENT"}`);
  console.log(`🚫 Blocked tools: ${agent.getDisallowedTools().join(", ")}\n`);

  try {
    // Task 1: Read-only operation (should work in both environments)
    console.log("--- Task 1: Read-only operation ---\n");
    const readResult = await agent.run({
      prompt: "List the files in the current directory and read any README.md.",
      maxSteps: 10,
    });
    console.log(readResult);

    // Task 2: Write operation (blocked in production)
    console.log("\n--- Task 2: Attempting write operation ---\n");
    const writeResult = await agent.run({
      prompt: `Try to create a file called "test-output.txt" with the content
"Hello from the restricted agent". Report whether you were able to do it.`,
      maxSteps: 10,
    });
    console.log(writeResult);

    // Dynamic restriction change — unlock write for a specific task
    if (isProduction) {
      console.log("\n--- Temporarily unlocking write for a specific task ---\n");
      agent.setDisallowedTools([]); // Clear all restrictions
      console.log(`🔓 Restrictions cleared: ${agent.getDisallowedTools().length} blocked tools`);

      const unlocked = await agent.run({
        prompt: "Write 'Authorized write' to a file called 'authorized-output.txt'.",
        maxSteps: 10,
      });
      console.log(unlocked);

      // Re-apply restrictions
      agent.setDisallowedTools(prodBlockedTools);
      console.log(`\n🔒 Restrictions re-applied: ${agent.getDisallowedTools().join(", ")}`);
    }
  } finally {
    await agent.close();
  }
}

main().catch((err) => {
  console.error("Restricted agent failed:", err);
  process.exit(1);
});
```

**Key takeaways:**

- `setDisallowedTools([...])` blocks specific tool names — the agent will refuse to call them.
- `getDisallowedTools()` returns the current list of blocked tools.
- Use environment variables (`NODE_ENV`) to apply different restriction profiles.
- Restrictions can be changed dynamically between `run()` calls.
- Clearing restrictions with `setDisallowedTools([])` unlocks all tools.

---

## Quick Reference: Constructor Options

```typescript
// Simplified mode — minimal setup
new MCPAgent({
  llm: "openai/gpt-4o",           // Auto-creates appropriate LLM (format: "provider/model")
  llmConfig: {                     // Optional LLM config overrides
    temperature: 0.3,
    maxTokens: 1000,
  },
  mcpServers: { ... },             // Inline server configs (MCPServerConfig)
  maxSteps: 30,                    // Max tool-call steps per run (default: 5)
});

// Explicit mode — full control
new MCPAgent({
  llm: new ChatOpenAI({ ... }),    // Your own LLM instance
  client: new MCPClient({ ... }),  // Your own MCPClient (set codeMode on the client, not here)
  connectors: [...],               // Alternative to client (BaseConnector[])
  maxSteps: 30,                    // Max tool-call steps per run (default: 5)
  autoInitialize: false,           // Auto-initialize on construction (default: false)
  useServerManager: true,          // Smart server routing (default: false)
  verbose: true,                   // Debug logging (default: false)
  observe: true,                   // Automatic observability (default: true)
  memoryEnabled: true,             // Conversation memory (default: true)
  systemPrompt: "...",             // Full system prompt override (use PROMPTS.CODE_MODE for code mode)
  systemPromptTemplate: "...",     // Template-based system prompt (overrides systemPrompt)
  additionalInstructions: "...",   // Appended to default prompt
  disallowedTools: ["tool1"],      // Block tools at construction time
  additionalTools: [...],          // Extra tools injected alongside MCP tools
  exposeResourcesAsTools: true,    // Expose MCP resources as tools (default: true)
  exposePromptsAsTools: true,      // Expose MCP prompts as tools (default: true)
  callbacks: [langfuseHandler],    // LangChain callbacks (e.g., Langfuse)
});

// Code mode — configure on MCPClient, not MCPAgent
new MCPClient(
  { mcpServers: { ... } },
  { codeMode: true }               // codeMode belongs on MCPClient
);
```

## Quick Reference: Agent Methods

```typescript
// Core execution
agent.run("prompt")                              // Standard execution — plain string (deprecated but works)
agent.run({ prompt: "prompt" })                  // Standard execution — options object form (preferred)
agent.run({ prompt, schema?, maxSteps?, signal? }) // Full options object form

// Streaming — note the different argument shapes:
agent.stream("prompt")                               // AsyncGenerator per step — plain string (deprecated)
agent.stream({ prompt, maxSteps?, schema?, signal? }) // preferred options object form
agent.streamEvents("prompt")                          // LangChain StreamEvents — plain string (deprecated)
agent.streamEvents({ prompt, schema?, maxSteps?, signal? }) // preferred options object form
agent.prettyStreamEvents({ prompt, maxSteps?, schema? }) // ANSI formatted — options object ONLY

// Memory & lifecycle
agent.getConversationHistory()               // Returns BaseMessage[] of current history
agent.clearConversationHistory()             // Wipe memory (preserves system message if memoryEnabled)
agent.initialize()                           // Async setup — called automatically when autoInitialize:true
agent.close()                                // Cleanup (always call!)
agent.flush()                                // Flush observability traces (important in serverless)

// Observability
agent.setMetadata({ key: "value" })          // Merge metadata into traces (accumulates)
agent.getMetadata()                          // Get current metadata copy
agent.setTags(["tag1", "tag2"])              // Add trace tags (deduplicates)
agent.getTags()                              // Get current tags copy

// Tool restrictions (also settable at construction via disallowedTools: [...])
agent.setDisallowedTools(["tool1", "tool2"]) // Block tools at runtime (call initialize() after)
agent.getDisallowedTools()                   // Get blocked list
```
