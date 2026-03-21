# LLM Task Chains

LLM Task is a plugin-provided tool that executes a single LLM reasoning step and forces structured JSON output. It is designed for use within larger workflows where AI reasoning is needed with deterministic, parseable results.

## Core characteristics

| Property | Value |
|---|---|
| Provider | Plugin (not built-in -- verify availability) |
| Output format | JSON only (no freeform text) |
| Use case | Structured AI reasoning within a pipeline |
| Risk level | Low (produces data, does not execute actions) |

## When to use LLM Task

Use LLM Task when:

- You need AI reasoning that produces parseable structured output
- The output feeds into a subsequent step (exec, browser, or another LLM Task)
- You want to enforce a specific JSON schema on the AI's response
- You need classification, extraction, summarization, or analysis as a pipeline step

Do NOT use LLM Task when:

- You need freeform conversational response (use the agent's native response)
- The task requires tool use or code execution within the reasoning step
- A simple regex or string operation would accomplish the same goal

## Defining an LLM Task

An LLM Task requires:

1. **Prompt** -- the instruction for the LLM
2. **Output schema** -- the JSON structure the response must conform to
3. **Input data** -- optional context passed into the prompt

### Output schema design

Keep schemas flat and focused:

```json
{
  "sentiment": "positive | negative | neutral",
  "confidence": 0.95,
  "key_phrases": ["phrase1", "phrase2"],
  "summary": "One sentence summary"
}
```

**Rules for schemas:**

- Maximum one level of nesting (arrays of primitives are fine)
- Use descriptive field names
- Constrain enum values where possible
- Keep total fields under 10 per task
- Include only fields the next step actually needs

### Prompt engineering for LLM Task

Because the output is JSON-only, prompts must be explicit about the expected structure:

- State the exact fields expected in the output
- Provide enum values for classification fields
- Specify data types (string, number, boolean, array)
- Give one example of the expected output shape
- Do NOT ask for explanations or reasoning in the output -- those waste tokens in a pipeline

## Chaining multiple LLM Tasks

### Sequential chain

Each LLM Task's output feeds into the next:

```
LLM Task 1: Extract entities from raw text
  Input: { text: "..." }
  Output: { entities: [{name, type, context}] }

LLM Task 2: Classify entities by priority
  Input: { entities: [{name, type, context}] }
  Output: { high: [...], medium: [...], low: [...] }

LLM Task 3: Generate action items from high-priority entities
  Input: { high: [{name, type, context}] }
  Output: { actions: [{description, assignee, deadline}] }
```

### Fan-out chain

One LLM Task produces a list, then multiple parallel tasks process each item:

```
LLM Task 1: Split document into sections
  Output: { sections: [{title, content}] }

LLM Task 2a: Summarize section 1
LLM Task 2b: Summarize section 2
LLM Task 2c: Summarize section 3
  (each receives one section)

LLM Task 3: Combine summaries
  Input: { summaries: [...] }
  Output: { combined_summary: "..." }
```

### Decision chain

An LLM Task makes a classification, and the next step depends on the result:

```
LLM Task 1: Classify input type
  Output: { type: "bug_report | feature_request | question" }

If bug_report -> LLM Task 2a: Extract reproduction steps
If feature_request -> LLM Task 2b: Extract requirements
If question -> LLM Task 2c: Generate answer
```

## Integrating LLM Task with other tools

### LLM Task + exec

Use LLM Task to analyze data, then exec to act on the results:

```
Step 1 (LLM Task): Analyze log file for errors
  Input: { log_content: "..." }
  Output: { errors: [{line, severity, message}], recommendation: "restart | ignore | escalate" }

Step 2 (exec): Act on recommendation
  If "restart": exec restart command
  If "escalate": exec notification command
  If "ignore": log and skip
```

### LLM Task + browser

Use browser to extract page content, then LLM Task to analyze it:

```
Step 1 (browser): Navigate to page, extract text
  Output: { page_text: "...", page_title: "..." }

Step 2 (LLM Task): Analyze page content
  Input: { page_text: "...", page_title: "..." }
  Output: { is_relevant: true, extracted_data: {...} }
```

### LLM Task inside Lobster

Use LLM Task as the action within a Lobster step:

```
Lobster Workflow: content-pipeline
  Step 1 (exec): Fetch raw data
  Step 2 (LLM Task): Clean and structure data
  Step 3 (LLM Task): Generate insights
  Step 4 (approval): Review insights before publishing
  Step 5 (exec): Publish results
```

## Error handling

LLM Task can fail in several ways:

| Failure mode | Cause | Mitigation |
|---|---|---|
| Schema violation | LLM output does not match expected JSON shape | Include explicit schema in the prompt; retry once with tighter instructions |
| Empty output | LLM produced no meaningful content | Check input data quality; the prompt may be too vague |
| Hallucinated data | LLM invented facts not present in input | Constrain the prompt to only use provided data; add verification step |
| Plugin unavailable | LLM Task plugin is not loaded | Check availability at workflow start; fall back to exec + manual parsing |
| Token limit exceeded | Input data is too large for one task | Split input into chunks; use fan-out pattern |

## Adjusting reasoning depth

Use the `thinking_level` tool to control how much reasoning the LLM applies:

| Level | When to use |
|---|---|
| `fast` | Simple classification, entity extraction, format conversion |
| `deep` | Complex analysis, multi-factor decisions, nuanced summarization |

Set thinking level before the LLM Task call, not within it.

## Best practices

1. **One task, one responsibility.** Each LLM Task should do one thing well. Chain tasks rather than overloading a single prompt.
2. **Validate output between steps.** Check that the JSON output matches the expected schema before passing to the next step.
3. **Keep input data minimal.** Only pass the data the LLM needs. Large inputs waste tokens and increase hallucination risk.
4. **Use enums for classification.** Constrained choices produce more reliable output than open-ended fields.
5. **Include one example in the prompt.** A single example of the expected output dramatically improves schema compliance.
6. **Test each task independently.** Before chaining, verify each LLM Task produces correct output for representative inputs.
7. **Log intermediate outputs.** In a chain, log each step's output so failures can be diagnosed without re-running the entire chain.
