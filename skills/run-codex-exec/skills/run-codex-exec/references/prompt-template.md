# Prompt Template

The prompt is the one lever you have after dispatch. Get it right and the agent ships. Get it wrong and the agent either bails silently or ruminates for 40 minutes without writing code.

This template was refined across ~20 dispatches against Codex CLI `gpt-5.4 xhigh reasoning`. It reflects real failure modes observed.

## The full template

```
YOU ARE A CODING AGENT. SKIP ALL META-SKILLS. DO NOT READ SKILL FILES.
DO NOT WRITE PLANNING DOCS. DO NOT ASK QUESTIONS. BEGIN EDITING
IMMEDIATELY. THE TASK:

Implement <plan name>. Read only:
- <primary plan file, absolute path>
- <orchestrator enhancement notes, if any>

<If orchestrator deltas exist: paste them inline as 1-3 bullet points.>

Deliverables (in order):
1. <Concrete schema / model changes if any>
2. <Concrete server actions / libs to add>
3. <Concrete UI changes>
4. <Tests>

Hard constraints:
- TypeScript strict mode with noUncheckedIndexedAccess / exactOptionalPropertyTypes
- No `@ts-ignore`, no `as any`
- Follow existing action shape: `{ success: boolean, error?: string, data?: T }`
- TanStack Query/Form/Table patterns per existing components
- Do NOT push; do NOT touch files outside the listed scope

Definition of Done:
- npx tsc --noEmit: 0 errors
- npx vitest run: all existing + N new tests pass
- npx eslint .: 0 errors
- ≥N commits with multi-paragraph bodies

Work inside this worktree only. The monitor watches for you.
```

## Why the prefix matters

**SKIP ALL META-SKILLS / DO NOT READ SKILL FILES / DO NOT WRITE PLANNING DOCS**

Codex exec loads any installed skills on startup (like the `superpowers` suite). These often include `using-superpowers`, `brainstorming`, `writing-plans`, `executing-plans`. If you don't explicitly bypass them, a coding agent will:

1. Spend 20–40k tokens reading skill files
2. Decide it needs to "brainstorm first"
3. Try to write a design document
4. Run out of reasoning budget before writing any code
5. Exit clean with no commits

The SUBAGENT-STOP shortcut documented inside those skills (`<SUBAGENT-STOP>If you were dispatched as a subagent to execute a specific task, skip this skill.</SUBAGENT-STOP>`) is triggered by the right opening words in the prompt. This template's prefix is designed to trigger it.

**BEGIN EDITING IMMEDIATELY**

Reinforces the same message. Codex agents with `xhigh` reasoning have a tendency to deliberate extensively before writing anything. Explicit "write first" framing reduces that.

## Why the deliverables must be concrete

Abstract: "implement the authentication feature"
Concrete: "create src/lib/auth/verify-token.ts exporting verifyToken(jwt: string): AuthContext | null; modify src/middleware.ts to call it for every /api route except /api/webhooks/*"

Concrete prompts ship. Abstract ones cause the agent to re-derive the design, which it doesn't have context for and will do poorly. The orchestrator has already read the plan — transcribe the what into the prompt.

## Why you tell it what NOT to touch

Codex agents will aggressively refactor adjacent code if they think it's beneficial. If your plan is "add a head-to-head modal to rank-content.tsx", the agent might also refactor how `getRankSummary` paginates — causing merge conflicts with a parallel plan that's supposed to own rank-summary changes.

Scope-fence explicitly: "Do NOT modify `src/actions/rank-tracking.ts#getRankSummary`; only add `headToHead`. Do NOT touch `src/components/rank-content.tsx#summaryPanel`; only add the Compare-with dropdown near the top."

## Why you include DoD

Without a DoD, the agent's "done" is subjective. It might decide it's done after writing the action but before the UI. It might decide the tests are optional. With an explicit DoD:

- `npx tsc --noEmit: 0 errors` — deterministic, the agent can run it itself and see.
- `≥N commits` — forces the agent to commit logical slices rather than one giant commit or no commit.

Codex respects these quantifiable targets far better than it respects narrative goals.

## Per-plan prompt tailoring

Paired plans (two related plans in the same worktree): explicitly serialize them in the prompt — "First, complete <plan 1> end-to-end and commit. Then start <plan 2>." Otherwise the agent will interleave the two and produce one giant commit you can't split.

Plans that conflict with a parallel agent's scope: call it out. "Another agent is concurrently modifying `src/actions/sentiment.ts`. Do NOT touch that file. Create `src/actions/sentiment-keywords.ts` as a new file instead." Prevents race-conflicts.

Plans that need specific deps: "Run `npm install d3-sankey d3-scale` first; commit the lockfile change as a separate slice."

Plans with clear gotchas: surface them. "The Zod schema for widgetLayout uses `z.union([z.array(z.unknown()), ...])`; when passing to Prisma, cast via `as Prisma.InputJsonValue` because exactOptionalPropertyTypes rejects the raw union."

## Anti-patterns

- **Multi-paragraph narrative about why the plan matters.** Waste of tokens. The agent doesn't need the backstory. Tell it what to build.
- **Open-ended "implement feature X with good tests".** The agent chooses the scope. You want to choose the scope.
- **"Follow best practices."** Meaningless signal. Replace with concrete constraints.
- **No DoD.** The agent's idea of done will not match yours.
- **Instructions on HOW to write the code.** Costs tokens, caps quality. Tell it the WHAT and let it write.

## Length target

400–800 tokens. Short enough the agent reads it in the first seconds. Long enough to specify the what, not-touch, and DoD. Everything past 1000 tokens of prompt is usually re-stating things that should be in the plan file (linked, not inlined).
