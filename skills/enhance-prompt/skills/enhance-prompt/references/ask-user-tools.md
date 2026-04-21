# Ask-User Tools by Runtime

This skill dispatches planning questions via a user-question tool. The tool's name and signature vary by runtime. Pick the right one for the runtime you are running in; fall back to plain prose if the tool is unavailable.

## Runtime → tool mapping

Detect the runtime first, then look up its tool name below. Invoke that tool with the shared payload shape in the next section.

| Agent / runtime | Tool name | Confidence basis |
|---|---|---|
| **claude-code** | `AskUserQuestion` | All 3 docs agree |
| **codex** | `ask_user_question` | All 3 docs agree |
| **gemini-cli** | `ask_user` | All 3 docs agree |
| **deepagents** | `ask_user` | All 3 docs agree |
| **kimi-cli** | `AskUserQuestion` | 2 docs agree; 1 silent → positive wins |
| **cline** | `ask_followup_question` | 2 docs agree; 1 silent → positive wins |
| **droid** (Factory) | `AskUser` | Research overrode vote — Factory release notes use PascalCase exclusively across 6+ changelog entries |
| **cursor** | `AskQuestion` | 2 docs agree + research confirmed native Plan Mode tool via official bug reports |
| **github-copilot** | `ask_user` | Research overrode vote — changelog proves shipped Jan 2025, listed in official tool reference table |
| **roo** | `ask_followup_question` | 1 doc positive; 2 silent → positive wins |
| **opencode** | `question` | 1 doc positive; 2 silent → positive wins |
| **continue** | `AskQuestion` | 1 doc positive; 2 silent → positive wins |
| **antigravity** | `suggested_responses` | 1 doc positive; 2 silent → positive wins |
| **pi** | `ask_user` | 1 doc positive; 2 silent → positive wins |
| **qwen-code** | `ask_user_question` | 1 doc positive; 2 silent → positive wins |
| **mistral-vibe** | `ask_user_question` | 1 doc positive; 2 silent → positive wins |
| **unknown / other** | — | Prose fallback (see "Fallback" below) |

### Fast lookup by naming convention

When you know the runtime but forget the exact casing, the grouping below is a memory aid:

| Pattern | Runtimes |
|---|---|
| PascalCase `AskUserQuestion` | claude-code, kimi-cli |
| PascalCase `AskUser` | droid |
| PascalCase `AskQuestion` | cursor, continue |
| `ask_user_question` | codex, qwen-code, mistral-vibe |
| `ask_user` | gemini-cli, deepagents, github-copilot, pi |
| `ask_followup_question` | cline, roo |
| `suggested_responses` | antigravity |
| `question` | opencode |

Casing matters — the tool is an exact-match lookup. `ask_user_question` and `AskUserQuestion` are different tools in different runtimes.

## Picking the right one at runtime

1. Look at the runtime table above; invoke the listed tool.
2. If the runtime is not in the table → try `AskUserQuestion` (most common PascalCase) once; if it fails with "unknown tool," try `ask_user` (most common snake_case) once.
3. If both fail → prose fallback. Do not skip the planning round.

When writing this skill's instructions into an agent's system prompt on a specific runtime, pre-resolve the tool name so the agent does not have to route at runtime.

## Signature shape (common across structured-question tools)

Each of the structured tools (Claude's `AskUserQuestion`, Codex's `ask_user_question`, etc.) exposes roughly the same payload shape:

```
questions: [
  {
    question: "<user-facing question text>",
    header: "<short chip label>",
    multiSelect: true | false,
    options: [
      { label: "<short label>", description: "<one-line description>" },
      ...
    ]
  },
  ...
]
```

Constraints to honor across runtimes:

- **1-4 questions per call** (Claude Code's cap; other runtimes may allow more but keeping to 4 is portable)
- **2-4 options per question** (same portability logic)
- **First option marked `(Recommended)`** in the label, based on your Step 1 diagnosis
- **Do NOT include an "Other" option manually** — Claude Code auto-adds it; other runtimes may differ, but mimicking this convention keeps the prompt clean
- **Use `multiSelect: true`** only when the choices are genuinely orthogonal (e.g., "which failure modes to block" — multiple can apply)

## Fallback — prose prompt

When no structured tool is available, produce the same decision surface in prose. Format:

```markdown
Before I enhance the prompt, pick your preference on these axes:

1. **Outcome type** — which primary outcome do you need?
   - (Recommended) Working code — runnable code that solves the task
   - Plan or strategy — a plan to execute later
   - Understanding — explanation or walkthrough
   - Research summary — gathered info, synthesized

2. **Enhancement depth** — how aggressive should the rewrite be?
   - (Recommended) Moderate — narrative + failure pre-emption + halt
   - Light touch — only halt + verification
   - Full restructure — all 5 layers

3. **Verification style** — how should the agent confirm it's done?
   - (Recommended) Run tests
   - Smoke-test manually
   - Self-describe the fix
   - Visual / screenshot

4. **Failure modes to block** — pick all that apply:
   - (Recommended) Scope creep
   - (Recommended) Over-engineering
   - Silent degradation
   - Assumption cascade

Reply with your picks (e.g., "1A, 2B, 3A, 4: scope creep + silent degradation") or "other" with free text.
```

Key rule: the prose fallback presents the *same* options as the structured tool — don't reduce the decision surface just because the tool is missing.

## Why this matters

Hard-coding `AskUserQuestion` in a skill means the skill quietly breaks on non-Claude runtimes — the call fails, the agent either skips the planning round or makes up an answer. Neither is a good failure mode.

Routing via this reference keeps the planning round portable: the skill works on Claude Code, Codex, Factory Droid, Gemini CLI, or (with the prose fallback) any runtime.

## When this reference is read

This reference is primarily consumed by:

- **`enhance-prompt`** — during Step 2 (Round 1 planning), the skill dispatches a question tool. The tool name depends on the runtime.

Other skills in this pack that occasionally ask user questions (e.g. `check-completion` when scope is unclear, `build-skills` when design tradeoffs need user input) can reuse the table above without a cross-skill dependency — the table is short enough to inline by reference when needed.

## Update policy

When a new runtime emerges with its own ask-user tool, add a row to the table above and include the source. When a documented tool name changes, update the row and note the change date in a footnote.

Do not silently drop rows. A runtime's absence from this table means "not yet verified", not "doesn't exist."
