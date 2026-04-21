# Cross-Runtime — Portability Notes

This skill is written natively for Claude Code but is designed to work on any runtime that supports an ask-user tool. This file covers runtime compatibility, the compact runtime lookup table, and the prose fallback for runtimes without structured tools.

The table below is self-contained. If the `enhance-prompt` skill is also installed in this pack, its `ask-user-tools.md` reference uses the same convention — the two are intentionally kept in sync.

## Runtime compatibility matrix

This skill requires ONE capability: the ability to ask the user a structured question mid-workflow. The tool's name and signature vary by runtime; the workflow logic is identical.

### Full runtime → tool lookup

| Runtime | Tool name | Style |
|---|---|---|
| **claude-code** (Anthropic SDK) | `AskUserQuestion` | PascalCase |
| **codex** (OpenAI) | `ask_user_question` | snake_case |
| **gemini-cli** | `ask_user` | snake_case |
| **deepagents** | `ask_user` | snake_case |
| **kimi-cli** | `AskUserQuestion` | PascalCase |
| **cline** | `ask_followup_question` | snake_case |
| **droid** (Factory) | `AskUser` | PascalCase |
| **cursor** | `AskQuestion` | PascalCase |
| **github-copilot** | `ask_user` | snake_case |
| **roo** | `ask_followup_question` | snake_case |
| **opencode** | `question` | plain |
| **continue** | `AskQuestion` | PascalCase |
| **antigravity** | `suggested_responses` | snake_case |
| **pi** | `ask_user` | snake_case |
| **qwen-code** | `ask_user_question` | snake_case |
| **mistral-vibe** | `ask_user_question` | snake_case |
| **unknown / other** | — | use prose fallback (see below) |

Casing matters. Lookup is exact-match.

### Picking at runtime

1. Look up the runtime in the table.
2. If the runtime isn't listed → try `AskUserQuestion` once; if the tool is unknown, try `ask_user` once; otherwise prose fallback.
3. Never silently skip a fork. If no tool works, fall back to prose. Do not proceed without the user's answer.

## Portable payload shape

The runtimes above share a payload shape. Code your calls to this shape and they'll work across nearly all of them:

```
questions: [
  {
    question: "<user-facing question text, ending with a question mark>",
    header: "<short chip label, max 12 chars>",
    multiSelect: true | false,
    options: [
      { label: "<short label, 1-5 words>", description: "<one-line description>" },
      ...
    ]
  },
  ...
]
```

**Portability constraints** (tightest across runtimes):

- 1-4 questions per call (Claude Code's cap)
- 2-4 options per question
- First option marked `(Recommended)` in the label, based on your analysis — not static
- Do NOT manually add "Other" — Claude Code auto-adds it; other runtimes may differ, but mimicking keeps the prompt clean
- Use `multiSelect: true` only when choices are genuinely orthogonal (e.g., "which failure modes to block")

## The five forks mapped to the ask-user tool

Each fork in the workflow dispatches one tool call:

| Fork | Typical question count | multiSelect? |
|---|---|---|
| Fork 1 (Classify) | 3 questions (Cynefin classifier) | No |
| Fork 2 (Decompose) | 1-2 questions (approve + optional missing branches) | No |
| Fork 3 (Explore) | 1 question (which options resonate, multiSelect if "add more") | Mixed |
| Fork 4 (Evaluate) | 1-2 questions (approve matrix + optional weight change) | No |
| Fork 5 (Stress-test) | 1 question (any of these change the pick?) | No |

Total across the session: 7-9 tool calls. Well within runtime limits.

## Prose fallback — when no tool is available

Some runtimes don't expose a structured ask-user tool. Fall back to markdown prose with the same decision surface:

### Prose template for Fork 1 (Classify)

```markdown
Before I pick the tools for this brainstorm, I need to classify the problem's shape. Three questions:

**1. What shape is this problem?**
- (Recommended) Design decision (architecture, framework, API)
- Root-cause hunt (recurring bug, unclear failure)
- Prioritization under constraint
- Novel exploration (no clear precedent)
- Stabilizing a crisis
- I'm not sure

**2. How clear is cause-effect here?**
- Fully understood
- (Recommended) Multiple plausible paths, analysis will resolve
- Unknown unknowns, not sure what to even measure
- Genuinely chaotic

**3. How reversible is the outcome?**
- Fully reversible, low-stakes
- (Recommended) Adjustable with effort
- Costly to reverse
- One-shot

Reply with your picks (e.g., "1-design, 2-plausible, 3-adjustable") or "other: <free text>".
```

### Prose template for Fork 3 (Options)

```markdown
Three options emerged from the exploration:

**Option A: <label>** — <1-sentence rationale + tradeoff>
**Option B: <label>** — <1-sentence rationale + tradeoff>
**Option C: <label>** — <1-sentence rationale + tradeoff>

Which of these resonates? Pick A, B, C, combo (e.g. "A+B"), "expand X", or "widen search with different tool".
```

Other forks follow the same pattern: same question content, same option set, rendered as markdown instead of a structured tool call.

## Claude-native affordances

When running on Claude Code specifically, a few things work extra well:

- **Markdown tables** render cleanly in the user's terminal — use them freely for the Evaluation matrix and Ranked summary
- **Code blocks** render with syntax highlighting — use for ASCII decomposition trees and Concept Maps
- **The `(Recommended)` suffix** is a rendering convention — highlighted in Claude Code's UI
- **`multiSelect: true`** is first-class in AskUserQuestion

Other runtimes may render differently. Keep the content portable; Claude-specific rendering is a nice-to-have, not a requirement.

## Formatting portability

- Markdown renders consistently across Claude Code, Codex, Gemini CLI, Cursor
- Some runtimes (terminal-based agents) may not render tables well — prefer bulleted hierarchies as a fallback for lists >4 items
- ASCII diagrams in code blocks are the most portable visual; mermaid / dot / flowcharts are not universally supported

When in doubt, prefer plain markdown over rich formatting. The brainstorm's value is in the content, not the rendering.

## When a runtime truly can't support the workflow

A few runtimes are text-completion only (no tool calls). In that case:

- Use prose fallback for every fork
- Collapse fork messages into single-response blocks
- The user replies in prose; you parse and proceed

This works but is friction-heavy. If the user is on such a runtime, suggest they switch to a tool-capable runtime for this particular skill. The skill still works; it's just less fluid.

## Mirroring the enhance-prompt convention

If the `enhance-prompt` skill is installed in this pack, its ask-user-tool reference uses the same convention and the two files contain equivalent runtime mappings. Duplicating the table locally means this skill is usable standalone (one-level-deep rule).

When a new runtime emerges with its own ask-user tool, update both files. The tables are small enough that manual propagation is cheap; single-source coupling across skills would break the one-level-deep rule.

## Common mistakes

| Mistake | Fix |
|---|---|
| Hard-coding `AskUserQuestion` in the skill's examples | Use the table; fall back to prose if the runtime isn't in it |
| Casing mistakes (e.g., `askuserquestion` instead of `AskUserQuestion`) | Exact-match lookup; casing matters |
| Skipping a fork because the tool call failed | Never skip — fall back to prose; a fork missed is a fork failed |
| Proliferating 5+ questions in a single tool call | Cap at 4 — Claude Code's limit and most portable |
| Manually adding "Other" to the options list | Most runtimes auto-add it; mimicking keeps prompts clean |
