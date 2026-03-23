# Observability: Evaluation & Testing Reference

Complete reference for LangSmith evaluation workflows, dataset management, LLM-as-judge, Feedback API, OpenTelemetry integration, third-party observability tools, self-hosted LangSmith, and pricing. All APIs verified against langsmith (latest), openevals (latest). TypeScript only.

---

## Quick Reference — Imports

```typescript
// Evaluation
import { Client, wrappers } from "langsmith";
import { create_llm_as_judge } from "openevals/llm";
import { CORRECTNESS_PROMPT } from "openevals/prompts";
import { OpenAI } from "openai";

// OpenTelemetry
import { trace } from "@opentelemetry/api";
import { TracerProvider } from "@opentelemetry/sdk-trace-node";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";

// Third-party
import { CallbackHandler } from "langfuse-langchain";
import { LangchainCallbackHandler } from "agentops/langchain";
```

---

## 1. Evaluation Quickstart

### Prerequisites

```bash
yarn add langsmith openevals openai @langchain/core
```

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="lsv2_pt_..."
export OPENAI_API_KEY="sk-..."
```

### Complete Evaluation Flow (Three Steps)

#### Step 1: Create a Dataset

```typescript
import { Client } from "langsmith";

const client = new Client();

const dataset = await client.createDataset({
  dataset_name: "QA Test Dataset",
  description: "Question-answer pairs for evaluation",
});

await client.createExamples({
  dataset_id: dataset.id,
  examples: [
    {
      inputs: { question: "Which country is Mount Kilimanjaro in?" },
      outputs: { answer: "Mount Kilimanjaro is located in Tanzania." },
    },
    {
      inputs: { question: "What is Earth's lowest point?" },
      outputs: { answer: "Earth's lowest point is The Dead Sea." },
    },
    {
      inputs: { question: "What is the capital of Japan?" },
      outputs: { answer: "The capital of Japan is Tokyo." },
    },
  ],
});
```

#### Step 2: Define Target Function and Evaluator

```typescript
import { Client, wrappers } from "langsmith";
import { OpenAI } from "openai";
import { create_llm_as_judge } from "openevals/llm";
import { CORRECTNESS_PROMPT } from "openevals/prompts";

const openai = wrappers.wrap_openai(new OpenAI());

// Target: the function under evaluation
async function target(inputs: Record<string, any>) {
  const resp = await openai.chat.completions.create({
    model: "gpt-4.1-mini",
    messages: [
      { role: "system", content: "Answer the following question accurately." },
      { role: "user", content: inputs.question },
    ],
  });
  return { answer: resp.choices[0].message.content?.trim() };
}

// Evaluator: LLM-as-judge for correctness
function correctnessEvaluator(
  inputs: Record<string, any>,
  outputs: Record<string, any>,
  reference_outputs: Record<string, any>
) {
  const evaluator = create_llm_as_judge({
    prompt: CORRECTNESS_PROMPT,
    model: "openai:o3-mini",
    feedback_key: "correctness",
  });
  return evaluator({ inputs, outputs, reference_outputs });
}
```

#### Step 3: Run Evaluation

```typescript
const results = await client.evaluate({
  target,
  data: "QA Test Dataset",
  evaluators: [correctnessEvaluator],
  experiment_prefix: "gpt-4.1-mini-eval",
  max_concurrency: 4,
  metadata: { model: "gpt-4.1-mini", version: "1.0" },
  tags: ["baseline"],
});

console.log(results);
```

---

## 2. Dataset Creation and Management

### Create a Dataset

```typescript
import { Client } from "langsmith";

const client = new Client();

// Named dataset (most common)
const dataset = await client.createDataset({
  dataset_name: "Customer Support QA v2",
  description: "Multi-turn customer support conversations for accuracy evaluation",
});
```

### Add Examples Individually

```typescript
await client.createExample(
  { question: "How do I reset my password?" },
  { answer: "Click 'Forgot Password' on the login page." },
  { datasetId: dataset.id }
);
```

### Add Examples in Batch

```typescript
await client.createExamples({
  dataset_id: dataset.id,
  examples: [
    {
      inputs: { question: "What payment methods do you accept?" },
      outputs: { answer: "We accept Visa, Mastercard, PayPal, and bank transfers." },
    },
    {
      inputs: { question: "What is your return policy?" },
      outputs: { answer: "Returns accepted within 30 days with original receipt." },
    },
  ],
});
```

### Populate Dataset from Existing Traces

```typescript
// Pull examples from real production traces into a dataset
const existingRuns = client.listRuns({
  project_name: "production-agent",
  run_type: "chain",
  is_root: true,
  filter: 'eq(feedback_key, "user_score") and eq(feedback_score, 1)',  // high-quality traces
});

for await (const run of existingRuns) {
  await client.createExample(
    run.inputs,
    run.outputs ?? {},
    { datasetId: dataset.id }
  );
}
```

### List and Retrieve Datasets

```typescript
// List all datasets
for await (const ds of client.listDatasets()) {
  console.log(ds.name, ds.id, ds.example_count);
}

// List examples in a dataset
for await (const example of client.listExamples({ datasetId: dataset.id })) {
  console.log(example.id, example.inputs, example.outputs);
}

// Get dataset by name
const ds = await client.readDataset({ datasetName: "QA Test Dataset" });
```

### Update and Delete Examples

```typescript
// Update an example
await client.updateExample(exampleId, {
  inputs: { question: "Updated question text?" },
  outputs: { answer: "Updated reference answer." },
});

// Delete an example
await client.deleteExample(exampleId);

// Delete an entire dataset
await client.deleteDataset({ datasetId: dataset.id });
```

---

## 3. `client.evaluate()` — All Options

### Full Signature

```typescript
const results = await client.evaluate({
  target,                        // function to evaluate
  data: "QA Test Dataset",       // dataset name or ID
  evaluators: [correctnessEvaluator, groundednessEvaluator],
  experiment_prefix: "gpt-4.1-mini-eval",
  max_concurrency: 4,            // parallel evaluation runs (default: 1)
  metadata: { model: "gpt-4.1-mini", version: "1.0", experiment_type: "baseline" },
  tags: ["baseline", "v1.0"],
  description: "Baseline evaluation for gpt-4.1-mini on QA dataset",
});
```

### Options Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `target` | `(inputs: Record<string, any>) => Promise<Record<string, any>>` | required | Function to evaluate; receives example inputs, returns outputs |
| `data` | `string` | required | Dataset name or UUID |
| `evaluators` | `Function[]` | required | One or more evaluator functions |
| `experiment_prefix` | `string` | `""` | Prefix for experiment name in LangSmith UI; auto-appended with timestamp |
| `max_concurrency` | `number` | `1` | Max parallel evaluations; increase for faster runs at cost of API rate limits |
| `metadata` | `Record<string, any>` | `{}` | Experiment metadata (model, version, hyperparams) |
| `tags` | `string[]` | `[]` | Experiment tags for filtering in UI |
| `description` | `string` | `""` | Human-readable description of the experiment |

### Evaluator Function Signature

Evaluators receive three arguments and return a score object:

```typescript
type EvaluatorFn = (
  inputs: Record<string, any>,           // example inputs from dataset
  outputs: Record<string, any>,          // target function's outputs
  reference_outputs: Record<string, any> // expected outputs from dataset
) => Promise<{ key: string; score: number }> | { key: string; score: number };
```

### Custom Evaluator Examples

```typescript
// Exact match evaluator
function exactMatchEvaluator(
  inputs: Record<string, any>,
  outputs: Record<string, any>,
  reference_outputs: Record<string, any>
): { key: string; score: number } {
  const predicted = (outputs.answer ?? "").trim().toLowerCase();
  const expected = (reference_outputs.answer ?? "").trim().toLowerCase();
  return {
    key: "exact_match",
    score: predicted === expected ? 1 : 0,
  };
}

// Contains-keyword evaluator
function containsKeywordEvaluator(
  inputs: Record<string, any>,
  outputs: Record<string, any>,
  reference_outputs: Record<string, any>
): { key: string; score: number } {
  const answer = (outputs.answer ?? "").toLowerCase();
  const keywords = (reference_outputs.keywords ?? []) as string[];
  const matched = keywords.filter((kw) => answer.includes(kw.toLowerCase()));
  return {
    key: "keyword_coverage",
    score: keywords.length > 0 ? matched.length / keywords.length : 0,
  };
}

// Multiple criteria from a single evaluator
async function multiEvaluator(
  inputs: Record<string, any>,
  outputs: Record<string, any>,
  reference_outputs: Record<string, any>
): Promise<{ key: string; score: number }[]> {
  return [
    { key: "relevance", score: 0.9 },
    { key: "conciseness", score: 0.7 },
    { key: "accuracy", score: 1.0 },
  ];
}
```

---

## 4. LLM-as-Judge via `openevals`

### Installation

```bash
yarn add openevals
```

### Available Built-in Prompts

```typescript
import {
  CORRECTNESS_PROMPT,
  GROUNDEDNESS_PROMPT,
  CONCISENESS_PROMPT,
  RELEVANCE_PROMPT,
  COHERENCE_PROMPT,
  HARMLESSNESS_PROMPT,
  HELPFULNESS_PROMPT,
} from "openevals/prompts";
```

### Using `create_llm_as_judge`

```typescript
import { create_llm_as_judge } from "openevals/llm";
import { CORRECTNESS_PROMPT, GROUNDEDNESS_PROMPT } from "openevals/prompts";

// Correctness judge (compares against reference)
const correctnessJudge = create_llm_as_judge({
  prompt: CORRECTNESS_PROMPT,
  model: "openai:o3-mini",        // model string: "openai:MODEL" or "anthropic:MODEL"
  feedback_key: "correctness",    // key name in LangSmith feedback
});

// Groundedness judge (checks if answer is grounded in provided context)
const groundednessJudge = create_llm_as_judge({
  prompt: GROUNDEDNESS_PROMPT,
  model: "openai:gpt-4.1-mini",
  feedback_key: "groundedness",
});

// Use in evaluate()
const results = await client.evaluate({
  target,
  data: "RAG Test Dataset",
  evaluators: [
    (inputs, outputs, reference_outputs) =>
      correctnessJudge({ inputs, outputs, reference_outputs }),
    (inputs, outputs, reference_outputs) =>
      groundednessJudge({ inputs, outputs, reference_outputs }),
  ],
  experiment_prefix: "rag-eval",
  max_concurrency: 2,
});
```

### Custom LLM-as-Judge Prompt

```typescript
import { create_llm_as_judge } from "openevals/llm";

const customPrompt = `You are evaluating an AI assistant's response to a customer support query.
Score the response from 0 to 1 based on:
- Whether it addresses the customer's issue (0-0.4)
- Tone and empathy (0-0.3)
- Actionability of the advice (0-0.3)

Customer Query: {inputs.question}
AI Response: {outputs.answer}

Return a JSON object: {"score": <float 0-1>, "reasoning": "<brief explanation>"}`;

const supportQualityJudge = create_llm_as_judge({
  prompt: customPrompt,
  model: "openai:gpt-4.1",
  feedback_key: "support_quality",
});
```

### Compare Model Outputs Side-by-Side

```typescript
// Run two experiments on the same dataset
const [baselineResults, improvedResults] = await Promise.all([
  client.evaluate({
    target: baselineModel,
    data: "QA Test Dataset",
    evaluators: [correctnessEvaluator],
    experiment_prefix: "baseline-gpt-4o-mini",
    tags: ["baseline"],
  }),
  client.evaluate({
    target: improvedModel,
    data: "QA Test Dataset",
    evaluators: [correctnessEvaluator],
    experiment_prefix: "improved-gpt-4.1",
    tags: ["improved"],
  }),
]);

// Compare in LangSmith UI: Projects → Experiments → select both → Compare
```

---

## 5. Feedback API

### Create Feedback

```typescript
import { Client } from "langsmith";

const client = new Client();

// Numeric feedback (0-1 or 0-5 range)
await client.createFeedback({
  key: "user_feedback",
  score: 1,
  trace_id: "trace-abc123",
  comment: "The response was accurate and helpful",
  metadata: { source: "user-thumbs-up-button" },
});

// Attach to a specific child run (not root)
await client.createFeedback({
  key: "correctness",
  score: 0,
  run_id: "child-run-id",
  trace_id: "trace-abc123",   // recommended for background ingestion
  comment: "Tool called with wrong parameters",
});

// Categorical feedback (no numeric score)
await client.createFeedback({
  key: "category",
  score: null,
  value: "CONCEPTUAL",          // categorical label
  trace_id: "trace-abc123",
});
```

### Feedback Data Schema

```typescript
interface Feedback {
  id: string;                    // UUID
  created_at: string;            // ISO-8601
  modified_at: string;           // ISO-8601
  session_id: string;            // project UUID
  run_id: string;                // run being evaluated
  key: string;                   // criterion (e.g., "correctness", "helpfulness")
  score?: number;                // numeric score
  value?: string;                // categorical value
  comment?: string;              // free-form annotation
  correction?: Record<string, any>;
  feedback_source: {
    type: "api" | "app" | "evaluator";
    metadata?: Record<string, any>;
    user_id?: string;
  };
}
```

### Feedback Sources

| Type | Description |
|------|-------------|
| `api` | Sent from your application code (`client.createFeedback`) |
| `app` | User-generated via LangSmith UI annotation queue |
| `evaluator` | Automated (offline evaluation or online LLM-as-judge) |

### Update and Delete Feedback

```typescript
// Update feedback (e.g., correct a score after human review)
await client.updateFeedback(feedbackId, {
  score: 0.8,
  comment: "Updated after manual review",
});

// Delete feedback
await client.deleteFeedback(feedbackId);

// List feedback for a run
for await (const fb of client.listFeedback({ runIds: [runId] })) {
  console.log(fb.key, fb.score, fb.value);
}
```

### Online Feedback Integration (Production Pattern)

Collect user feedback at API response time and attach it to the trace:

```typescript
import { Client } from "langsmith";
import { Hono } from "hono";

const app = new Hono();
const langsmith = new Client();

// Step 1: Run agent, return trace_id to frontend
app.post("/chat", async (c) => {
  const { message, traceId } = await c.req.json();

  const result = await agent.invoke(
    { messages: [{ role: "user", content: message }] },
    { run_id: traceId }  // deterministic trace ID from frontend
  );

  return c.json({ answer: result.output, traceId });
});

// Step 2: Frontend sends thumbs up/down later
app.post("/feedback", async (c) => {
  const { traceId, score } = await c.req.json();

  await langsmith.createFeedback({
    key: "user_rating",
    score: score,  // 1 = thumbs up, 0 = thumbs down
    trace_id: traceId,
    metadata: { source: "in-app-feedback-button" },
  });

  return c.json({ status: "ok" });
});
```

---

## 6. OpenTelemetry Integration

### Enable OTEL Mode

```bash
# Send LangSmith traces via OTEL protocol
export LANGSMITH_OTEL_ENABLED=true
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=<your_key>

# OTEL exporter variables (standard)
export OTEL_EXPORTER_OTLP_ENDPOINT=https://api.smith.langchain.com/otel
export OTEL_EXPORTER_OTLP_HEADERS="x-api-key=<your_key>"
export OTEL_SERVICE_NAME=my-langgraph-service

# Send ONLY to custom OTEL provider (skip LangSmith storage)
# Requires langsmith >= 0.4.1
export LANGSMITH_OTEL_ONLY=true
```

### LangSmith OTEL Attribute Mappings

| OpenTelemetry Attribute | LangSmith Field |
|-------------------------|-----------------|
| `langsmith.span.kind` | Run type (`"llm"`, `"chain"`, `"tool"`, etc.) |
| `langsmith.trace.name` | Run name |
| `langsmith.trace.session_id` | Session/project ID |
| `langsmith.trace.session_name` | Session name |
| `langsmith.span.tags` | Tags (comma-separated) |
| `langsmith.metadata.{key}` | `metadata.{key}` |
| `gen_ai.system` | `metadata.ls_provider` |
| `gen_ai.request.model` | `invocation_params.model` |
| `gen_ai.usage.input_tokens` | `usage_metadata.input_tokens` |
| `gen_ai.usage.output_tokens` | `usage_metadata.output_tokens` |

### Manual OTEL Instrumentation (Node.js)

```typescript
import { trace } from "@opentelemetry/api";
import { TracerProvider } from "@opentelemetry/sdk-trace-node";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import OpenAI from "openai";

const exporter = new OTLPTraceExporter({
  url: "https://api.smith.langchain.com/otel/v1/traces",
  headers: { "x-api-key": process.env.LANGSMITH_API_KEY },
});

const provider = new TracerProvider();
provider.addSpanProcessor(new BatchSpanProcessor(exporter));
provider.register();

const tracer = trace.getTracer("my-langgraph-app");
const openai = new OpenAI();

async function callLLM(messages: any[]) {
  const span = tracer.startSpan("llm_call");
  span.setAttribute("langsmith.span.kind", "LLM");
  span.setAttribute("langsmith.metadata.user_id", "user_123");
  span.setAttribute("gen_ai.system", "openai");
  span.setAttribute("gen_ai.request.model", "gpt-4.1-mini");

  try {
    const result = await openai.chat.completions.create({
      model: "gpt-4.1-mini",
      messages,
    });
    span.setAttribute("gen_ai.usage.input_tokens", result.usage?.prompt_tokens || 0);
    span.setAttribute("gen_ai.usage.output_tokens", result.usage?.completion_tokens || 0);
    return result;
  } finally {
    span.end();
  }
}
```

### Fan-Out: Send to Multiple Backends Simultaneously

Use an OpenTelemetry Collector to fan out traces to LangSmith AND other observability platforms simultaneously:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  otlphttp/langsmith:
    endpoint: https://api.smith.langchain.com/otel/v1/traces
    headers:
      x-api-key: ${env:LANGSMITH_API_KEY}
      Langsmith-Project: my_project
  otlphttp/datadog:
    endpoint: https://trace.agent.datadoghq.com/v0.4/traces
    headers:
      DD-API-KEY: ${env:DD_API_KEY}
  otlphttp/grafana:
    endpoint: https://tempo-prod-04-prod-us-east-0.grafana.net/tempo
    headers:
      Authorization: ${env:GRAFANA_TOKEN}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlphttp/langsmith, otlphttp/datadog, otlphttp/grafana]
```

With this setup your application sends traces to the local OTEL Collector, which forwards them to all three backends.

---

## 7. Third-Party Observability Tools

### Langfuse (Open-Source Alternative)

```bash
npm install langfuse langfuse-langchain
```

```typescript
import { CallbackHandler } from "langfuse-langchain";

const langfuseHandler = new CallbackHandler({
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  baseUrl: "https://cloud.langfuse.com",  // or self-hosted URL
  sessionId: "session-123",
});

await graph.invoke(
  { messages: [{ role: "user", content: "Hello" }] },
  { callbacks: [langfuseHandler] }
);

// Required for scripts — ensures traces are flushed
await langfuseHandler.flushAsync();
```

### AgentOps

```typescript
import { LangchainCallbackHandler } from "agentops/langchain";

const agentOpsHandler = new LangchainCallbackHandler({
  apiKey: process.env.AGENTOPS_API_KEY!,
});

await chain.invoke(input, { callbacks: [agentOpsHandler] });
```

### Datadog LLM Observability (TypeScript)

```typescript
// npm install dd-trace
import tracer from "dd-trace";

tracer.init({ llmobs: { enabled: true, mlApp: "my-langgraph-app" } });
// Automatically traces LangChain/LangGraph calls via dd-trace
```

Key metrics captured by Datadog LLM Obs:
- Latency (per span)
- Token usage and cost
- Error rates
- Input/output messages
- Tool call success rates

### Arize Phoenix (Open-Source, OpenInference)

```bash
npm install @arizeai/openinference-instrumentation-langchain
```

Uses OpenInference semantic conventions. Works with any OTEL collector. Suitable when already using Arize for ML model monitoring.

### LangWatch (TypeScript-Native)

```bash
npm install langwatch
```

```typescript
import * as LangWatch from "langwatch";

LangWatch.init({
  apiKey: process.env.LANGWATCH_API_KEY,
  endpoint: "https://app.langwatch.ai",
});

// Wrap LangGraph agent
const wrappedGraph = LangWatch.wrapLangGraph(graph, {
  name: "my-agent",
  metadata: { version: "1.0.0" },
});
```

### Upstash Rate Limit Callback

```typescript
import { UpstashRatelimitHandler } from "@langchain/community/callbacks/handlers/upstash_ratelimit";

const handler = new UpstashRatelimitHandler({ ratelimiter: myUpstashRatelimiter });
await model.invoke(input, { callbacks: [handler] });
// Throws if rate limit exceeded on LLM call
```

### Observability Tool Comparison

| Tool | License | Self-hostable | Strengths | Best For |
|------|---------|--------------|-----------|----------|
| **LangSmith** | Proprietary | Enterprise only | Deep LangGraph integration, eval suite, prompt management | Teams in LangChain ecosystem |
| **Langfuse** | MIT | Yes (Docker/K8s) | Open-source, good dashboards, free tier, no per-trace pricing | Cost-sensitive or privacy-first teams |
| **Datadog LLM Obs** | Proprietary | No | Unified infra + LLM monitoring, SLA integration | Teams already using Datadog |
| **Arize Phoenix** | Apache 2.0 | Yes | OpenInference conventions, ML model monitoring | ML teams with existing Arize stack |
| **LangWatch** | Proprietary | Partial | TypeScript-native, agent testing workflows | TypeScript-first teams |
| **Maxim AI** | Proprietary | No | Agent behavioral testing and production QA | Production quality assurance |
| **SigNoz** | Apache 2.0 | Yes | Standard OTEL collector, full observability stack | Teams wanting full OTEL stack |

**Community consensus (r/LangChain, 2025-2026):** Use LangSmith for development-time tracing and debugging; Langfuse for self-hosted/privacy environments; Datadog for infrastructure-level monitoring; Langfuse has 19k+ GitHub stars and is the most popular open-source alternative.

---

## 8. Self-Hosted LangSmith

### Deployment Models

| Model | Components | Best For |
|-------|-----------|---------|
| **Observability & Evaluation** | UI, API, backend services, queues, PostgreSQL, Redis, ClickHouse | Monitoring without agent deployment |
| **Observability + Deployment** | Above + Control Plane + Data Plane (Agent Server pods) | Full private LangChain Cloud |
| **Standalone Server** | Agent Server + PostgreSQL + Redis | Lightweight single-agent deployments |

### Core Services (Observability Model)

| Service | Description |
|---------|-------------|
| LangSmith frontend | Nginx-served UI |
| LangSmith backend | CRUD API, trace ingestion, hub API |
| LangSmith queue | Async trace ingestion with retry |
| LangSmith platform backend | Auth, run ingestion, high-volume tasks |
| LangSmith Playground | Proxies to LLM APIs |
| LangSmith ACE backend | Secure code execution sandbox |

### Storage Roles

| Storage | Role |
|---------|------|
| ClickHouse | Traces & feedback (high-volume OLAP) |
| PostgreSQL | Operational data (everything except traces/feedback) |
| Redis | Queue and cache |
| Blob storage (optional) | Large trace artifacts (S3, Azure Blob, GCP) |

### Setup Paths

- **Docker Compose**: development/testing only
- **Kubernetes + Helm**: recommended for production (EKS, GKE, AKS)
  - Helm chart available from LangSmith documentation
  - Requires Enterprise plan add-on

### License Requirements

- Self-hosted LangSmith is an Enterprise plan add-on
- `LANGSMITH_LICENSE_KEY` required in environment
- `langgraph up` with custom auth also requires a production license key

### Point to Self-Hosted Instance

```bash
export LANGSMITH_ENDPOINT=https://your-langsmith.internal.company.com
export LANGSMITH_API_KEY=<your-self-hosted-key>
```

```typescript
import { Client } from "langsmith";

const client = new Client({
  apiKey: process.env.LANGSMITH_API_KEY,
  apiUrl: "https://your-langsmith.internal.company.com",
});
```

---

## 9. LangSmith Pricing

### Plan Comparison

| Plan | Tracing | Evaluation | Deployment | Alerts | Bulk Export |
|------|---------|-----------|-----------|--------|-------------|
| **Free** | Yes (volume limits) | Yes | No | No | No |
| **Plus** | Yes (higher limits) | Yes | $0.001/node | Yes | Yes |
| **Enterprise** | Yes (unlimited) | Yes | $0.001/node (custom) | Yes | Yes + self-hosted |

### Deployment Pricing Details

- `langgraph dev` — local development, free, no Docker required
- `langgraph up` — local Docker stack, free, requires Docker
- `langgraph deploy` — LangSmith Cloud, **$0.001 per node execution**
- Self-hosted LangSmith — Enterprise plan add-on; requires `LANGSMITH_LICENSE_KEY`
- Custom auth (`langgraph up` with auth) requires a production license key

**Cost estimation example:** A 10-node agent graph executing 1,000 times per day = 10,000 node executions = **$10/day = ~$300/month**.

### Tracing Pricing

LangSmith tracing pricing is usage-based (volume of traces and spans). The Free plan covers development usage. Plus/Enterprise plans offer higher quotas. Check `smith.langchain.com/pricing` for current rates.

---

## 10. Production Security Checklist for Evaluation

```typescript
// Recommended production LangSmith configuration
import { Client } from "langsmith";
import { createAnonymizer } from "langsmith/anonymizer";
import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";

const anonymizer = createAnonymizer([
  { pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/, replace: "<email>" },
]);

const langsmithClient = new Client({
  apiKey: process.env.LANGSMITH_API_KEY,  // never hardcode
  anonymizer,                              // always anonymize in regulated environments
});

const tracer = new LangChainTracer({
  client: langsmithClient,
  projectName: "prod-agent",
});
```

```bash
# Required production env vars
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...           # from encrypted secret store
LANGSMITH_PROJECT=prod-agent

# For non-serverless
LANGCHAIN_CALLBACKS_BACKGROUND=true

# For serverless (Lambda, Vercel, Next.js API routes)
LANGCHAIN_CALLBACKS_BACKGROUND=false
```

**Checklist:**

- [ ] `LANGSMITH_API_KEY` stored as encrypted secret (not in code or git)
- [ ] Anonymizer configured for PII-containing inputs/outputs
- [ ] `waitForAllTracers()` called in all scripts and test suites
- [ ] `LANGCHAIN_CALLBACKS_BACKGROUND=false` in serverless deployments
- [ ] LangSmith alerts configured for error rate > 5% and latency > p95 threshold
- [ ] Metadata includes `userId`, `sessionId`, `environment`, `version` on every trace
- [ ] Bulk export destination configured for long-term trace retention
- [ ] EU endpoint used (`https://eu.api.smith.langchain.com`) if data residency requires it
- [ ] `ls_provider` and `ls_model_name` set in model metadata for cost tracking
- [ ] Feedback API integrated at user-facing endpoints (thumbs up/down, ratings)
- [ ] Evaluation datasets version-controlled (not just UI-managed)
- [ ] Regression evaluation runs against previous experiment on every model/prompt change

---

## Known Pitfalls

| Pitfall | Affected Components | Fix |
|---------|--------------------|----|
| `client.evaluate` default `max_concurrency=1` is very slow for large datasets | Evaluation jobs | Set `max_concurrency` to 4–16 depending on API rate limits |
| Evaluator receives `reference_outputs={}` (empty) | Evaluation datasets without expected outputs | Always populate `outputs` in `createExamples`; evaluation requires reference outputs for LLM judges |
| LLM-as-judge model cost adds up on large datasets | `openevals` evaluators | Use cheaper judge models (e.g., `gpt-4.1-mini`) for initial evaluations; `o3-mini` only for final reports |
| `wrappers.wrap_openai` required for auto-tracing of raw OpenAI calls | OpenAI SDK in evaluation targets | Wrap with `wrappers.wrap_openai(new OpenAI())` to get nested traces |
| Feedback attached to wrong run (child vs. root) | `createFeedback` without `trace_id` | Always include `trace_id` in `createFeedback`; it enables background ingestion and correct attribution |
| Dataset examples accumulate stale data | Long-lived evaluation datasets | Periodically audit and delete low-quality examples; use `deleteExample()` |
| OTEL `LANGSMITH_OTEL_ONLY=true` requires langsmith >= 0.4.1 | OpenTelemetry fan-out | Check version before using; falls back to LangSmith storage if not set |
| `langfuseHandler.flushAsync()` not called in scripts | Langfuse integration | Always call `flushAsync()` before process exit or in `finally` block |
| Self-hosted LangSmith ClickHouse not provisioned for production volume | Self-hosted deployments | Follow Helm chart sizing guidelines; default Docker Compose is for dev/test only |
| Evaluation experiment results not reproducible | Non-deterministic LLM targets | Set `temperature=0` in evaluation target function for reproducibility; log exact model version |
| `createFeedback` score range mismatch | Feedback API consumers | Decide on 0-1 or 0-5 range per key and document it; LangSmith normalizes differently per range |
