# Architecture: AI & LLM Observability

How to instrument LLM applications, autonomous agents, and AI pipelines (OpenAI, Anthropic, LangChain) with Sentry to track token consumption, latencies, model costs, and prompt security.

## 1. Node.js / TypeScript AI Instrumentation

Modern `@sentry/node` provides official integrations for major AI model providers and orchestration frameworks.

```typescript
import * as Sentry from '@sentry/node';
import OpenAI from 'openai';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 1.0,
  integrations: [
    // Automatically instruments OpenAI API calls
    Sentry.openAiIntegration({
      // Set to false if company policy forbids sending raw prompt strings to Sentry
      recordInputs: true,
      recordOutputs: true,
    }),
    // Automatically instruments Anthropic SDK calls
    Sentry.anthropicIntegration(),
  ],
  beforeSendSpan(span) {
    // Scrub sensitive PII from LLM prompts before span transmission
    if (span.data?.['gen_ai.prompt']) {
      span.data['gen_ai.prompt'] = scrubPii(String(span.data['gen_ai.prompt']));
    }
    return span;
  },
});

const openai = new OpenAI();

export async function generateAgentResponse(userPrompt: string) {
  // Sentry wraps this call into an OpenTelemetry GenAI span:
  // - Attributes: gen_ai.system (openai), gen_ai.request.model (gpt-4o)
  // - Metrics: gen_ai.usage.input_tokens, gen_ai.usage.output_tokens
  const completion = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: userPrompt }],
  });

  return completion.choices[0]?.message.content;
}

function scrubPii(text: string): string {
  return text.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[EMAIL]');
}
```

## 2. Python AI & LangChain Instrumentation

In Python with `sentry-sdk`:

```python
import os
import sentry_sdk
from sentry_sdk.integrations.openai import OpenAIIntegration
from sentry_sdk.integrations.anthropic import AnthropicIntegration
from sentry_sdk.integrations.langchain import LangchainIntegration
from openai import OpenAI

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    integrations=[
        OpenAIIntegration(
            include_prompts=True, # Set False in strict zero-retention environments
        ),
        AnthropicIntegration(),
        LangchainIntegration(),
    ],
)

client = OpenAI()

def call_model(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
```

## 3. Custom Agentic Loop & Multi-Step Tracing

For complex agent loops (e.g. planner -> tool caller -> reflection):

```typescript
export async function runAgenticWorkflow(goal: string) {
  return Sentry.startSpan(
    {
      name: 'agent.workflow',
      op: 'gen_ai.workflow',
      attributes: {
        'agent.goal': goal,
      },
    },
    async (workflowSpan) => {
      // Step 1: Plan
      const plan = await Sentry.startSpan(
        { name: 'agent.plan', op: 'gen_ai.step' },
        async () => generatePlan(goal)
      );

      // Step 2: Execute Tool
      const toolOutput = await Sentry.startSpan(
        { name: 'agent.tool_execution', op: 'gen_ai.tool' },
        async () => executeTool(plan.selectedTool)
      );

      workflowSpan.setStatus({ code: 1 }); // OK
      return toolOutput;
    }
  );
}
```

## 4. Key AI Telemetry Metrics in Sentry

| Telemetry Dimension | Sentry Span / Metric Attribute | Purpose |
|---|---|---|
| **Input Tokens** | `gen_ai.usage.input_tokens` | Track prompt size and cost drivers |
| **Output Tokens** | `gen_ai.usage.output_tokens` | Track completion volume |
| **Model Name** | `gen_ai.request.model` | Group performance and latency by model |
| **System** | `gen_ai.system` (`openai`, `anthropic`) | Provider breakdown |
| **Rate Limit Drops** | HTTP 429 errors | Detect provider quota exhaustion |
