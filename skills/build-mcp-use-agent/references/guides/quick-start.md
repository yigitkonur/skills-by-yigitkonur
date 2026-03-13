# Quick Start Guide

## Prerequisites

- Node.js 22 LTS
- `mcp-use` v1.21+ (`npm install mcp-use`)
- At least one LLM provider package (e.g., `npm install @langchain/openai`)
- API key for your LLM provider (set as env var)

## Minimal agent (explicit mode)

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "./"],
    },
  },
});

const llm = new ChatOpenAI({ model: "gpt-4o" });
const agent = new MCPAgent({ llm, client, maxSteps: 30 });

try {
  const result = await agent.run({ prompt: "List files in this directory" });
  console.log(result);
} finally {
  await agent.close();
}
```

## Minimal agent (simplified mode)

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
  maxSteps: 30,
});

try {
  const result = await agent.run("What files are here?");
  console.log(result);
} finally {
  await agent.close();
}
```

## With custom LLM config

```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  llmConfig: {
    temperature: 0.3,
    maxTokens: 1000,
    // apiKey: "sk-..." // optional override
  },
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "./"],
    },
  },
});
```

## Interactive chat loop

```typescript
import readline from "node:readline";
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    airbnb: {
      command: "npx",
      args: ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
    },
  },
  maxSteps: 30,
});

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const ask = (prompt: string) => new Promise<string>(resolve => rl.question(prompt, resolve));

try {
  while (true) {
    const input = await ask("\nYou: ");
    if (input === "exit") break;
    if (input === "clear") { agent.clearConversationHistory(); continue; }

    const response = await agent.run(input);
    console.log(`\nAssistant: ${response}`);
  }
} finally {
  rl.close();
  await agent.close();
}
```

## Running and testing

```bash
# Run with tsx
npx tsx src/my-agent.ts

# Run with ts-node
npx ts-node src/my-agent.ts

# Required env vars
export OPENAI_API_KEY="sk-..."
# or ANTHROPIC_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY
```

## Next steps

- [LLM Integration](./llm-integration.md) — provider-specific setup
- [Agent Configuration](./agent-configuration.md) — all constructor options
- [Streaming](./streaming.md) — real-time output
- [Structured Output](./structured-output.md) — typed responses
