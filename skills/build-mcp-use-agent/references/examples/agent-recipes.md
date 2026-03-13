# Agent Recipes

Complete working examples for common MCPAgent patterns.

## Basic file system agent

```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
    },
  },
  maxSteps: 30,
});

try {
  const result = await agent.run({
    prompt: "List all TypeScript files and count the total lines of code",
    maxSteps: 30,
  });
  console.log(result);
} finally {
  await agent.close();
}
```

## Browser automation agent

```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    playwright: {
      command: "npx",
      args: ["@playwright/mcp@latest"],
      env: { DISPLAY: ":1" },
    },
  },
  maxSteps: 30,
});

try {
  const result = await agent.run({
    prompt: "Navigate to https://github.com/mcp-use/mcp-use and summarize the project",
    maxSteps: 30,
  });
  console.log(result);
} finally {
  await agent.close();
}
```

## Interactive chat with memory

```typescript
import readline from "node:readline";
import { MCPAgent } from "mcp-use";

async function chat() {
  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: {
      airbnb: {
        command: "npx",
        args: ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
      },
    },
    maxSteps: 30,
    // memoryEnabled: true is the default
  });

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const ask = (p: string) => new Promise<string>(r => rl.question(p, r));

  console.log("Type 'exit' to quit, 'clear' to reset memory\n");

  try {
    while (true) {
      const input = await ask("You: ");
      if (input === "exit") break;
      if (input === "clear") { agent.clearConversationHistory(); continue; }

      const response = await agent.run(input);
      console.log(`\nAssistant: ${response}\n`);
    }
  } finally {
    rl.close();
    await agent.close();
  }
}

chat().catch(console.error);
```

## Multi-server agent

```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "anthropic/claude-3-5-sonnet-20241022",
  mcpServers: {
    airbnb: {
      command: "npx",
      args: ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
    },
    playwright: {
      command: "npx",
      args: ["@playwright/mcp@latest"],
      env: { DISPLAY: ":1" },
    },
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
    },
  },
  maxSteps: 30,
});

try {
  const result = await agent.run(
    "Search Airbnb for places in Barcelona, then save the results to a file"
  );
  console.log(result);
} finally {
  await agent.close();
}
```

## Structured output agent

```typescript
import { z } from "zod";
import { ChatAnthropic } from "@langchain/anthropic";
import { MCPAgent, MCPClient } from "mcp-use";

const RepoSchema = z.object({
  name: z.string().describe("Repository name"),
  description: z.string().describe("Brief description"),
  stars: z.number().describe("Star count"),
  language: z.string().describe("Primary language"),
  license: z.string().nullable().describe("License type"),
});

const client = new MCPClient({
  mcpServers: {
    playwright: {
      command: "npx",
      args: ["@playwright/mcp@latest"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatAnthropic({ model: "claude-haiku-4-5" }),
  client,
  maxSteps: 50,
  memoryEnabled: true,
});

try {
  const repo = await agent.run({
    prompt: "Research the mcp-use repository on GitHub",
    schema: RepoSchema,
  });

  console.log(`${repo.name}: ${repo.stars} stars (${repo.language})`);
} finally {
  await agent.close();
}
```

## Streaming step-by-step agent

```typescript
import { ChatAnthropic } from "@langchain/anthropic";
import { MCPAgent, MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    everything: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-everything"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatAnthropic({ model: "claude-sonnet-4-20250514" }),
  client,
  maxSteps: 10,
  verbose: true,
});

try {
  const stream = agent.stream("List all tools, try 2-3 of them");

  let stepNum = 1;
  let result = "";

  while (true) {
    const { done, value } = await stream.next();
    if (done) { result = value; break; }

    console.log(`\n--- Step ${stepNum++} ---`);
    console.log(`Tool: ${value.action.tool}`);
    console.log(`Input: ${JSON.stringify(value.action.toolInput)}`);
    console.log(`Result: ${value.observation.slice(0, 100)}...`);
  }

  console.log(`\nFinal result: ${result}`);
} finally {
  await client.closeAllSessions();
}
```

## Pretty streaming agent

```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "./"],
    },
  },
});

for await (const _ of agent.prettyStreamEvents({
  prompt: "Analyze the project structure and suggest improvements",
  maxSteps: 20,
})) {
  // auto-formatted ANSI output
}

await agent.close();
```

## Agent with server manager

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    web: { command: "npx", args: ["@playwright/mcp@latest"] },
    files: { command: "uvx", args: ["mcp-server-filesystem", "/tmp"] },
    database: { command: "uvx", args: ["mcp-server-sqlite"] },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  useServerManager: true,
  verbose: true,
});

try {
  const result = await agent.run(`
    1. List available servers
    2. Scrape data from a website
    3. Save it to a file
    4. Load it into a database
    Guide me through each step.
  `);
  console.log(result);
} finally {
  await client.closeAllSessions();
}
```

## Agent with Langfuse observability

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient, Logger } from "mcp-use";

Logger.setDebug(true);

const client = new MCPClient({
  mcpServers: {
    everything: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-everything"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o", temperature: 0 }),
  client,
  maxSteps: 30,
});

// Set metadata for trace filtering
agent.setMetadata({
  agent_id: "test-agent-123",
  test_run: true,
  example: "observability",
});
agent.setTags(["test", "observability"]);

const result = await agent.run({
  prompt: "List available tools and resources",
  maxSteps: 30,
});
console.log(result);
```

## MCP Everything test agent

```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    everything: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-everything"],
    },
  },
  maxSteps: 30,
});

const result = await agent.run({
  prompt: `Answer the following:
- Which resources do you have access to?
- Which prompts do you have access to?
- Which tools do you have access to?`,
  maxSteps: 30,
});
console.log(result);
await agent.close();
```
