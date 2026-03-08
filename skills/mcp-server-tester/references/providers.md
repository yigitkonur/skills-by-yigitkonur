# LLM Provider Configuration

The inspector's chat endpoints support three official providers and any OpenAI-compatible API via base URL override.

## Official Providers

### OpenAI

```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "apiKey": "sk-..."
}
```

Models: `gpt-4o`, `gpt-4o-mini`, `gpt-4.1`, `o3-mini`, etc.

### Anthropic

```json
{
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "apiKey": "sk-ant-..."
}
```

Models: `claude-opus-4-20250514`, `claude-sonnet-4-20250514`, `claude-haiku-3-5-20241022`, etc.

### Google

```json
{
  "provider": "google",
  "model": "gemini-2.5-pro",
  "apiKey": "AIza..."
}
```

Models: `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.0-flash`, etc.

## OpenRouter (and any OpenAI-Compatible API)

OpenRouter, vLLM, Ollama, Together AI, Azure OpenAI, and any other OpenAI-compatible endpoint work through the `openai` provider with a base URL override.

This works because the inspector passes the full `llmConfig` object to LangChain's `ChatOpenAI` constructor, which accepts a `configuration.baseURL` property. The `LLMConfig` interface has a `[key: string]: any` catch-all, so extra properties pass through.

### OpenRouter Configuration

```json
{
  "provider": "openai",
  "model": "anthropic/claude-sonnet-4",
  "apiKey": "sk-or-v1-...",
  "configuration": {
    "baseURL": "https://openrouter.ai/api/v1"
  }
}
```

Or depending on @langchain/openai version:
```json
{
  "provider": "openai",
  "model": "anthropic/claude-sonnet-4",
  "apiKey": "sk-or-v1-...",
  "baseURL": "https://openrouter.ai/api/v1"
}
```

### Other OpenAI-Compatible APIs

**Ollama (local):**
```json
{
  "provider": "openai",
  "model": "llama3.1",
  "apiKey": "ollama",
  "configuration": {"baseURL": "http://localhost:11434/v1"}
}
```

**Together AI:**
```json
{
  "provider": "openai",
  "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
  "apiKey": "...",
  "configuration": {"baseURL": "https://api.together.xyz/v1"}
}
```

**Azure OpenAI:**
```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "apiKey": "...",
  "configuration": {"baseURL": "https://YOUR_RESOURCE.openai.azure.com/openai/deployments/YOUR_DEPLOYMENT/v1"}
}
```

**vLLM:**
```json
{
  "provider": "openai",
  "model": "your-model",
  "apiKey": "token-abc123",
  "configuration": {"baseURL": "http://localhost:8000/v1"}
}
```

## Important Notes

- The `provider` field MUST be one of: `"openai"`, `"anthropic"`, `"google"`. You cannot add new provider names.
- For OpenAI-compatible APIs, always use `"provider": "openai"` and override the base URL.
- The `model` field is passed directly to the provider. For OpenRouter, use their model ID format (e.g., `"anthropic/claude-sonnet-4"`).
- The `temperature` field is optional and works with all providers.
- API keys are sent directly from the inspector server to the LLM provider. They are NOT sent to mcp-use servers.

## Asking the User for Credentials

When running `/mcp-test-llm`, ask the user which provider they want to use:

1. **OpenAI** — needs `OPENAI_API_KEY`
2. **Anthropic** — needs `ANTHROPIC_API_KEY`
3. **Google** — needs `GOOGLE_API_KEY`
4. **OpenRouter** — needs `OPENROUTER_API_KEY` (works with hundreds of models)
5. **Other OpenAI-compatible** — needs API key + base URL

If the user wants to save their key, write it to `.env` in the project root:

```bash
echo 'OPENAI_API_KEY=sk-...' >> .env
# or
echo 'OPENROUTER_API_KEY=sk-or-v1-...' >> .env
```

To read it back:
```bash
source .env 2>/dev/null
```

Always check for existing `.env` first to avoid duplicates:
```bash
grep -q 'OPENROUTER_API_KEY' .env 2>/dev/null || echo 'OPENROUTER_API_KEY=sk-or-v1-...' >> .env
```

## Building the llmConfig for curl

Based on provider choice, construct the config:

```bash
# OpenAI
LLM_CONFIG='{"provider":"openai","model":"gpt-4o-mini","apiKey":"'$OPENAI_API_KEY'"}'

# Anthropic
LLM_CONFIG='{"provider":"anthropic","model":"claude-sonnet-4-20250514","apiKey":"'$ANTHROPIC_API_KEY'"}'

# Google
LLM_CONFIG='{"provider":"google","model":"gemini-2.5-flash","apiKey":"'$GOOGLE_API_KEY'"}'

# OpenRouter
LLM_CONFIG='{"provider":"openai","model":"anthropic/claude-sonnet-4","apiKey":"'$OPENROUTER_API_KEY'","configuration":{"baseURL":"https://openrouter.ai/api/v1"}}'

# OpenRouter (cheaper model for high-volume testing)
LLM_CONFIG='{"provider":"openai","model":"meta-llama/llama-3.1-8b-instruct","apiKey":"'$OPENROUTER_API_KEY'","configuration":{"baseURL":"https://openrouter.ai/api/v1"}}'
```
