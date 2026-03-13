# Common Errors

## "API key not found for provider 'X'"

**Cause:** Missing API key for the LLM provider.

**Fix:**
```bash
export OPENAI_API_KEY="sk-..."
# or ANTHROPIC_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY
```
Or pass directly:
```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  llmConfig: { apiKey: "sk-..." },
  mcpServers: {},
});
```

## "Package '@langchain/X' is not installed"

**Cause:** Missing LLM provider package.

**Fix:**
```bash
npm install @langchain/openai      # for OpenAI
npm install @langchain/anthropic   # for Anthropic
npm install @langchain/google-genai # for Google
npm install @langchain/groq        # for Groq
```

## "Invalid LLM string format"

**Cause:** Incorrect `"provider/model"` string.

**Fix:** Use exact format: `"openai/gpt-4o"`, `"anthropic/claude-3-5-sonnet-20241022"`, etc.

## "Unsupported LLM provider 'X'"

**Cause:** Using an unsupported provider string.

**Supported providers:** `openai`, `anthropic`, `google`, `groq`

## Max steps exceeded

**Cause:** Agent hit the `maxSteps` limit before completing.

**Fix:** Increase `maxSteps`:
```typescript
const agent = new MCPAgent({ llm, client, maxSteps: 50 });
```
Or simplify the prompt to require fewer steps.

## Tool execution failures

**Cause:** MCP server tool returned an error.

**Debugging:**
1. Enable `verbose: true` on the agent
2. Check the MCP server is running and accessible
3. Verify the server command and args are correct
4. Test the server independently with MCP Inspector

## "Agent not found" (RemoteAgent)

**Cause:** Invalid `agentId` or missing permissions.

**Fix:** Verify the agent ID exists in your MCP Use Cloud account.

## "Authentication failed" (RemoteAgent)

**Cause:** Invalid or missing API key.

**Fix:** Set `MCP_USE_API_KEY` environment variable or pass `apiKey` to RemoteAgent constructor.

## Connection timeout

**Cause:** MCP server took too long to start.

**Fix:**
1. Ensure the server command is correct
2. Check if dependencies need to be installed (e.g., `npx` may need to download packages)
3. Verify network connectivity for remote servers

## Memory overflow in long conversations

**Cause:** Accumulated conversation history exceeds token limits.

**Fix:**
```typescript
// Periodically clear history
if (agent.getConversationHistory().length > 50) {
  agent.clearConversationHistory();
}
```

## Structured output validation failure

**Cause:** LLM response doesn't match Zod schema after 3 retries.

**Fix:**
1. Simplify the schema
2. Add `.describe()` to all fields
3. Use `z.nullable()` for optional data
4. Increase `maxSteps` so the agent has more attempts to gather data

## Server manager confusion

**Cause:** Agent connects to wrong server or can't find tools.

**Fix:**
1. Use descriptive server names
2. Enable `verbose: true` to see server selection decisions
3. Reduce the number of servers to minimize tool overload

## Debugging checklist

1. Set `verbose: true` on the agent
2. Enable `Logger.setDebug(true)` for framework-level logging
3. Check environment variables are set correctly
4. Verify MCP servers start independently
5. Test with a simple prompt first
6. Use `agent.prettyStreamEvents()` to see step-by-step execution
