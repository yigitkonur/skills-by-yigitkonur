# Anti-Patterns

Common mistakes when building MCP agents and how to fix them.

## 1. Not closing the agent

❌ **Wrong:**
```typescript
const agent = new MCPAgent({ llm, client });
const result = await agent.run("Do something");
// agent and connections leak!
```

✅ **Correct:**
```typescript
const agent = new MCPAgent({ llm, client });
try {
  const result = await agent.run("Do something");
} finally {
  await agent.close();
}
```

## 2. Setting maxSteps too low

❌ **Wrong:**
```typescript
// Default maxSteps is 5 — too few for complex tasks
const agent = new MCPAgent({ llm, client });
await agent.run("Research a topic, write a report, and save it to a file");
// → likely fails with "max steps exceeded"
```

✅ **Correct:**
```typescript
const agent = new MCPAgent({ llm, client, maxSteps: 30 });
await agent.run("Research a topic, write a report, and save it to a file");
```

## 3. Forgetting to install provider packages

❌ **Wrong:**
```typescript
const agent = new MCPAgent({ llm: "anthropic/claude-3-5-sonnet-20241022", mcpServers: {} });
// → Error: Package '@langchain/anthropic' is not installed
```

✅ **Correct:**
```bash
npm install @langchain/anthropic
```

## 4. Using memory in stateless APIs

❌ **Wrong:**
```typescript
// Shared agent instance across requests — memory bleeds between users
const agent = new MCPAgent({ llm, client, memoryEnabled: true });

app.post("/api/chat", async (req, res) => {
  const result = await agent.run(req.body.prompt);
  // Previous user's conversation contaminates this response
  res.json({ result });
});
```

✅ **Correct:**
```typescript
app.post("/api/chat", async (req, res) => {
  const agent = new MCPAgent({ llm, client, memoryEnabled: false });
  try {
    const result = await agent.run(req.body.prompt);
    res.json({ result });
  } finally {
    await agent.close();
  }
});
```

## 5. Not setting API keys

❌ **Wrong:**
```typescript
const agent = new MCPAgent({ llm: "openai/gpt-4o", mcpServers: {} });
// → Error: API key not found for provider 'openai'
```

✅ **Correct:**
```bash
export OPENAI_API_KEY="sk-..."
```
Or:
```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  llmConfig: { apiKey: "sk-..." },
  mcpServers: {},
});
```

## 6. Ignoring streaming mode benefits

❌ **Wrong:**
```typescript
// Waits silently for minutes on complex tasks
const result = await agent.run("Analyze 50 files and generate a report");
console.log(result);
```

✅ **Correct:**
```typescript
// Show progress in real-time
for await (const _ of agent.prettyStreamEvents({
  prompt: "Analyze 50 files and generate a report",
  maxSteps: 50,
})) {
  // user sees progress
}
```

## 7. Mixing explicit and simplified mode options

❌ **Wrong:**
```typescript
const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),  // explicit mode
  mcpServers: { /* ... */ },                    // simplified mode option
  // TypeScript error: mcpServers not allowed with LLM instance
});
```

✅ **Correct:**
```typescript
// Explicit mode
const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client: myClient,
});

// OR simplified mode
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: { /* ... */ },
});
```
