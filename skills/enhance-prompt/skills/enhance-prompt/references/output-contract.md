# Enhanced Prompt Output Contract

Use this contract when producing the final enhanced prompt. The enhanced prompt is the artifact; commentary stays minimal.

## Response Shape

Return exactly:

````markdown
```text
<enhanced prompt>
```
Key improvement: <one sentence naming the main execution risk you blocked>
````

Do not add a generic offer, tutorial, or analysis unless the user requested it or the prompt's risk warrants a brief note.

## Enhanced Prompt Skeleton

Use the smallest structure that makes the executor less likely to fail:

```markdown
Context:
<current situation and relevant known facts>

Task:
<specific outcome the executor must produce>

Approach:
<how to start, what to inspect first, and what framing to use>

Constraints:
<scope fence, non-goals, dependencies, style or runtime limits>

Verification:
<observable check the executor must run or perform>

Done signal:
<specific state that means the task is complete>

Halt condition:
<ambiguity, blocker, or risk that requires stopping instead of guessing>
```

Use headings only when they help the target executor. For a short prompt, a compact paragraph with explicit verification, done signal, and halt condition can be enough.

## Code-Task Variant

Include:

- Files or paths the user named, plus any obvious scope fence.
- A read-before-write instruction only when unfamiliar architecture or stale context is likely.
- Existing test, lint, typecheck, or smoke command when known.
- A diff-scope check such as "confirm only expected files changed" when scope creep is likely.

Do not mention tools the target agent may not have. If the target agent is unknown, keep the wording generic.

## Non-Code Variant

Include:

- Source or corpus boundary: what material is in scope, and what is out of scope.
- Audience and use context: who the output is for and what decision it supports.
- Acceptance criteria: what a useful answer must contain or avoid.
- Verification method: citation check, consistency check, stakeholder review, rubric pass, or other observable check.

## Assumptions

State assumptions inside the enhanced prompt only when they affect execution. Prefer direct wording:

```markdown
Assumption: the target repo already has a test command. If not, identify the closest smoke check and report that substitution.
```

Do not add assumptions just to explain ordinary prompt-editing choices.

## Prompt Lint Checklist

Before returning the enhanced prompt, confirm:

- Task outcome is explicit.
- Scope boundary exists.
- Likely failure modes are blocked.
- Verification method is observable.
- Done signal is specific.
- Halt condition names the ambiguity or blocker.
