# Cross-Runtime — Portability Notes

This skill runs on any runtime that supports an ask-user tool (needed at the 3-fails handoff fork, per `references/escalation.md`) or a prose fallback. Most debugging work is solo — the user is invoked only when the skill hands off to `do-brainstorm`.

If the `enhance-prompt` skill is installed in this pack, its `ask-user-tools.md` reference is the canonical source and uses the same mapping. The two are intentionally kept in sync.

## Runtime → tool lookup

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

## When this skill asks the user

Only at the 3-fails handoff fork. Every other interaction is solo-reasoning — the skill produces evidence-bearing artifacts inline and the user reads them at their own pace.

At the handoff:

1. The skill has already written the handoff template (see `references/escalation.md` and `references/integration.md`).
2. The skill uses the runtime's ask-user tool to present 1-4 options:
   - Continue investigating (re-enter Phase 2 with a new framing)
   - Route to `do-brainstorm` (recommended at Fail 3)
   - Defer and surface the architectural question to a human
   - Abandon the session (document the failed hypotheses and stop)

## Portable payload shape

```
questions: [
  {
    question: "Three hypothesis-driven fixes failed. What should happen next?",
    header: "3-fails fork",
    multiSelect: false,
    options: [
      { label: "Route to do-brainstorm (Recommended)", description: "Hand off with the full 3-fails template; do-brainstorm investigates the architectural question" },
      { label: "Re-open Phase 2 once more", description: "Try one more pattern family before escalating" },
      { label: "Defer to a human", description: "Document and stop; surface the question to a named owner" },
      { label: "Abandon the session", description: "Document all three fails and close without a fix" }
    ]
  }
]
```

Portability constraints (tightest across runtimes):

- 1-4 questions per call (Claude Code cap)
- 2-4 options per question
- First option marked `(Recommended)` in label, based on the current state (at Fail 3, "Route to do-brainstorm" is the recommended option)
- Do NOT manually add "Other" — Claude Code auto-adds it; other runtimes may differ, but mimicking keeps the prompt clean

## Prose fallback — when no ask-user tool is available

```markdown
## Three hypothesis-driven fixes failed — what should happen next?

The skill has reached the 3-fails gate. Full handoff template is below. Pick one:

**1. Route to do-brainstorm (Recommended)**
Hand off with the 3-fails template; do-brainstorm investigates the architectural
question surfaced by the three fails.

**2. Re-open Phase 2 once more**
Try one more pattern family. Only do this if the three fails all trace to the
same pattern-family assumption and you have an alternative family in mind.

**3. Defer to a human**
Document the architectural question and stop. A named owner picks it up.

**4. Abandon the session**
Close without a fix. Document all three fails so the next session does not
repeat them.

Reply with "1", "2", "3", "4", or "other: <your note>".
```

## Mirroring the enhance-prompt convention

If `enhance-prompt` is installed, its `ask-user-tools.md` is the canonical source. When a new runtime emerges with its own ask-user tool, update both files. The tables are small enough that manual propagation is cheap; single-source coupling across skills would break the one-level-deep rule.

## Picking at runtime

1. Look up the runtime in the table above.
2. If the runtime isn't listed → try `AskUserQuestion` once; if unknown-tool error, try `ask_user` once; otherwise use the prose fallback.
3. Never silently skip the handoff. If no tool works, emit the prose fallback and wait for the user's reply.

## Claude-native affordances

On Claude Code:

- Markdown tables render well — use them for the handoff template and the 3-fails context.
- The `(Recommended)` suffix is a rendering convention Claude Code highlights in its UI.
- `multiSelect: true` is first-class in `AskUserQuestion` (not used in this skill — the 3-fails fork is single-select).

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Hard-coding `AskUserQuestion` in the skill's examples | Use the runtime table; fall back to prose if the runtime isn't listed |
| Skipping the 3-fails handoff because "no tool is available" | Use the prose fallback; a missed handoff is worse than a prose prompt |
| Asking the user at Fail 1 or Fail 2 | No — those are handled by re-opening prior phases inline. The ask-user tool fires only at Fail 3. |
| Asking multiple questions at the handoff ("which pattern family? which layer? which fix?") | One question, 2-4 options. More is friction. |
