# Ask-User Tools by Runtime

This skill dispatches planning questions via a user-question tool. The tool's name and signature vary by runtime. Pick the right one for the runtime you are running in; fall back to plain prose if the tool is unavailable.

## Runtime → tool mapping

| Runtime | Tool name | Invocation style |
|---|---|---|
| **Claude Code** (and Anthropic Agent SDK) | `AskUserQuestion` | 1-4 questions per call, 2-4 options each; first option marked `(Recommended)`; `multiSelect: true` for multi-choice; "Other" auto-provided |
| **OpenAI Codex** | `ask_user_question` | Snake-case variant of the same pattern; payload fields parallel Claude Code's shape |
| **Factory Droid CLI** | `ask_user` | Structured user-question flow; see Factory's hooks/tools reference for the exact schema |
| **Gemini CLI** | `ask-user` | Kebab-case CLI tool; used the same way as the structured-question pattern above |
| **GitHub Copilot CLI** | *(not clearly exposed in public docs)* | Public CLI docs describe approvals and interactive prompts but don't name a first-class ask-user tool; fall back to a prose prompt (see below) |
| **Unknown / other** | N/A | Fall back to prose prompt (see "Fallback" below) |

Sources for the mapping: Claude Code Agent SDK user-input docs; OpenAI Codex issue tracker referencing `ask_user_question`; Factory Droid CLI hooks reference mentioning `ask_user`; Gemini CLI tools docs mentioning `ask-user`. The GitHub Copilot CLI reference does not surface a direct equivalent name; treat as unknown.

## Picking the right one at runtime

Detect the runtime before invoking a tool:

1. **If running under Claude Code / Anthropic SDK** → `AskUserQuestion` is available. Prefer it.
2. **If running under OpenAI Codex** → `ask_user_question`.
3. **If running under Factory Droid CLI** → `ask_user`.
4. **If running under Gemini CLI** → `ask-user`.
5. **If the runtime is unclear** → try `AskUserQuestion` first; if it fails with "unknown tool," fall back to prose.
6. **If no tool works at all** → prose prompt.

If you are writing this skill's instructions into an agent's system prompt, include the table above so the agent routes correctly without calling a missing tool.

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
