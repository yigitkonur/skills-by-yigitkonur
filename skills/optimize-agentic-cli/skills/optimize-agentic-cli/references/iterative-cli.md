# Iterative CLI Patterns

This reference covers a higher-level pattern than `--json` alone: CLIs that actively guide an agent through repeated improvement cycles.

An iterative CLI does not just say "failed." It explains what is wrong, what can be retried, what should be fixed next, and when the workflow is ready to move to the next stage.

---

## 1. When To Use Iterative CLI

Use this pattern when the CLI expects an agent to:
- generate an artifact and submit it back for validation
- repair invalid output over multiple attempts
- work through a staged workflow such as `init`, `fetch`, `submit`, `status`, `finalize`
- handle partial progress rather than all-or-nothing success

Strong fits:
- subtitle or localization translation
- code generation with validation gates
- manifest, schema, or migration generation
- patch, diff, or batch-edit workflows
- import or sync tools that process work in chunks

Avoid this pattern for trivial one-shot lookups where a single structured response is enough.

---

## 2. The Semantic Shift

Most CLI guidance stops at machine-readable output.

That is necessary, but not sufficient for agent workflows that improve work product over time.

An iterative CLI treats the command surface as a protocol with feedback:
- the agent proposes work
- the CLI validates the work
- the CLI returns structured correction guidance
- the agent repairs the artifact
- the workflow advances only when the artifact is acceptable

This turns the CLI into a collaborator rather than a passive validator.

---

## 3. Core Response Requirements

For repair loops, every response should make these questions easy to answer:

1. What stage am I in?
2. Did the last step succeed, fail, or partially succeed?
3. What exactly is wrong?
4. Is retrying allowed, and how many attempts remain?
5. What should I run next?
6. How close am I to completion?

Recommended fields:

```json
{
  "ok": false,
  "phase": "submit_patch",
  "progress": {
    "completed": 3,
    "total": 10,
    "percent": 30.0
  },
  "next_action": {
    "action": "retry",
    "command": "mycli submit --session session.json --batch 4 --patch batch_4.patch",
    "description": "Fix the invalid entries and resubmit batch 4"
  },
  "attempt": 2,
  "max_attempts": 3,
  "validation_errors": [
    {
      "scope": "entry",
      "id": "subtitle-49",
      "code": "MISSING_PLACEHOLDER",
      "message": "Placeholder %d was removed",
      "suggestion": "Preserve %d exactly in the translated line"
    }
  ]
}
```

The exact shape can vary, but the semantics should not.

---

## 4. What Makes The Feedback High Quality

High-quality feedback is:
- specific enough to repair without guessing
- aggregated enough to avoid one-error-at-a-time thrash
- stable enough to script against
- actionable enough to tell the agent the next move

Good feedback usually includes:
- the failed batch, item, resource, line, or identifier
- a typed error code
- a concise human-readable explanation
- a concrete fix suggestion
- retryability and attempt budget
- the next command or action

Bad feedback looks like:
- `invalid input`
- `something went wrong`
- exit code `1` with no body
- interactive prompts asking the operator how to recover

---

## 5. Case Study: Segmented Translation CLI

Consider a CLI that translates localization assets in batches, including SRT subtitle files.

The agent workflow is not a single `translate` command. It is a staged loop:

1. `init` creates a session and reports batch counts, language pair, and the next command.
2. `batch` returns the next translation segment in a compact machine format, plus parseable guidance about where to save it and how to submit it.
3. The agent translates only the requested entries.
4. `submit` validates the artifact and returns structured feedback when it fails.
5. `status` reports progress and the next pending batch.
6. `finalize` reconstructs the final output when all required batches are complete.

The important idea is not localization itself. The important idea is that the CLI keeps the agent inside a bounded repair loop.

### Why this works especially well for SRT

SRT translation has several properties that benefit from iterative CLI design:
- the input is naturally chunkable into subtitle blocks
- context matters, so batches may need surrounding entries as read-only context
- formatting mistakes are easy to validate
- partial completion is acceptable if the session state is tracked

An iterative CLI can therefore:
- give the agent only the current subtitle slice to translate
- preserve surrounding context without asking the agent to regenerate the whole file
- validate missing entries, malformed structure, or placeholder drift
- tell the agent exactly which subtitle entries need repair
- continue batch by batch until finalization

This same pattern applies outside translation. Replace subtitle blocks with SQL migrations, JSON patches, or generated config fragments and the loop is still valid.

---

## 6. Designing The Artifact Channel

Some workflows do not want JSON as the primary payload.

Examples:
- a translation block
- a unified diff
- a SQL migration
- a config file fragment
- a patch file to be reviewed and resubmitted

In those cases:
- keep the primary artifact in its native machine format
- keep the guidance parseable, not conversational
- reserve a stable marker, trailer, or companion command for metadata
- make sure an agent can split artifact from guidance deterministically

Acceptable patterns:
- artifact on stdout, guidance under a reserved marker such as `#STATUS:` or `#GUIDANCE:`
- artifact on stdout, machine-readable status available from a separate `status` command
- artifact written to a file, structured result returned in JSON

Avoid:
- mixing prose paragraphs between machine-readable lines
- changing marker names or field types across commands
- forcing the agent to scrape help text to recover from normal validation failures

---

## 7. Validation Design Rules

For iterative CLI workflows:
- validate structure before semantics
- validate semantics before expensive downstream work
- return all repairable errors for the current artifact, not just the first one
- separate hard failures from warnings
- preserve progress already completed
- make retry budget explicit

Useful validation dimensions:
- syntax or framing errors
- missing or extra identifiers
- count mismatches
- placeholder preservation
- cross-field consistency
- batch or segment mismatches

When possible, include both a machine code and a human fix suggestion.

---

## 8. Command Set Pattern

Many iterative CLIs benefit from this command family:

| Command | Purpose |
|---|---|
| `init` | Create session state and report next action |
| `fetch` or `batch` | Return the next unit of work |
| `submit` | Validate and accept or reject the artifact |
| `status` | Report progress and the next pending unit |
| `finalize` | Assemble final output |

This pattern works because it separates:
- planning state
- artifact production
- validation
- progress inspection
- completion

Trying to collapse all of that into one command often makes the CLI harder for agents to recover from.

---

## 9. Anti-Patterns

- Returning only `success` or `failure` without stage information.
- Emitting human explanations without machine codes.
- Using the same exit code for usage mistakes, validation errors, and transient failures.
- Prompting interactively during a repair loop.
- Throwing away session state after a failed attempt.
- Accepting partial work silently without reporting what was skipped.
- Requiring the agent to infer the next command from narrative text.

---

## 10. Checklist

Before calling a repair-loop CLI agent-ready, verify that it:
- exposes stable machine-readable responses for every stage
- reports exact repair targets, not generic failure
- distinguishes retryable and non-retryable outcomes
- provides progress and next-step guidance
- preserves enough session state to resume safely
- supports deterministic completion through an explicit finalization step
