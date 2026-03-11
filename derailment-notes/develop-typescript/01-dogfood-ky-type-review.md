# Derailment Test: develop-typescript on "ky HTTP client type review"

Date: 2026-03-11
Skill under test: develop-typescript
Test task: Review and improve type safety in the ky HTTP client library
Method: Follow SKILL.md steps 1–5 exactly as written
Project: sindresorhus/ky (~3200 LOC, 27 TypeScript files)

---

## Friction points

### Step 1: Classification

**F-01 — Multi-category task has no classification guidance** (P0, M1)
The task maps to 4+ categories: anti-patterns (audit), type-system (type guards), modern-features (TS 5.x adoption), strict-config (tsconfig audit). SKILL.md says "Classify the job first" (singular noun) and "load the smallest relevant reference set" but gives no guidance on multi-faceted tasks. The "Smallest useful reading sets" section has pre-composed sets but none match this task. I had to combine "Make this code strict and safe" + modern-features.md using my own judgment.
Fix: Add to Step 1: "If the task spans multiple categories, pick the primary category first, then add at most one adjacent reference. For review/audit tasks, start with `anti-patterns.md` plus the most relevant domain reference."

**F-02 — "Load" verb is undefined** (P1, M6)
"Load the smallest relevant reference set" — does this mean read the file into LLM context? Open it in an editor? Bookmark it for later reference? The mechanical action is completely unstated. I assumed "read into context" but an agent or junior dev would not know.
Fix: Replace "load" with "read into your working context (or pass as context to the LLM)" in Step 1.

**F-03 — No review mode entry point** (P1, M4)
Step 4 mentions "In review mode, prioritize correctness, boundary safety, async behavior, and config mismatches before style notes." But there is no formal review mode toggle, entry criteria, or different workflow path for review vs. authoring tasks. When the task says "review," the skill doesn't change its behavior.
Fix: Add a sub-section under Step 1 or a separate heading: "If the task is a review or audit (not authoring new code), follow the same 5 steps but treat each as an audit checklist rather than an implementation plan. Prioritize findings by: (1) correctness/boundary safety, (2) async behavior, (3) config, (4) style."

---

### Step 2: Baseline

**F-04 — No sub-step to compare config against recommended baseline** (P1, S3)
Step 2 says "Keep strictness on; do not fix errors by weakening compiler settings first." The "Compiler baseline" section elsewhere lists 8 recommended strict flags plus 3 deliberate additions. But Step 2 doesn't say "compare the project's tsconfig against the recommended flags." I had to know to do this. The baseline flags are in "Strictness and tooling defaults" — a different section not cross-referenced from Step 2.
Fix: Add to Step 2 bullet 2: "Compare the project's tsconfig against the compiler baseline listed in this skill's 'Strictness and tooling defaults' section. Note any recommended flags that are missing and decide whether to add them."

**F-05 — "Annotate exported function parameters and return types" — no audit method** (P2, M4)
Step 2 bullet 3 says to annotate exports but doesn't say how to find unannotated ones. I used `grep 'export function'` and manual inspection. The skill could suggest `tsc` with `isolatedDeclarations` (which enforces explicit return types on exports) or a grep pattern.
Fix: Add to Step 2 bullet 3: "To find unannotated exports, run `grep -rn 'export function\|export async function' source/` or enable `isolatedDeclarations` temporarily to surface missing annotations."

**F-06 — "Prefer the repo's existing toolchain" contradicts "block any"** (P0, S2)
ky's xo config explicitly disables `@typescript-eslint/no-unsafe-argument`, `@typescript-eslint/no-unsafe-assignment`, `@typescript-eslint/no-unsafe-return`, `@typescript-eslint/no-unsafe-call`, and `@typescript-eslint/ban-ts-comment`. Step 2 bullet 5 says "Prefer the repo's existing toolchain" but Step 4 says "Block `any`, unchecked `as`, `@ts-ignore`." These directly conflict — the repo's toolchain allows what the skill blocks. No resolution path.
Fix: Add to Step 2 bullet 5: "If the repo's lint config disables safety rules that conflict with this skill's Step 4 blocklist (e.g., `no-unsafe-*` rules disabled), note the conflict in findings but do not unilaterally re-enable rules. Flag the disabled safety rules as a recommendation."

---

### Step 3: Type mechanism

**F-07 — No methodology for auditing missed `satisfies` opportunities** (P1, M4)
Step 3 says "Reach for `satisfies` before whole-object annotations that widen literals." This is a forward-looking preference for new code, not an audit checklist for existing code. ky uses zero `satisfies` — is that a finding? How do I systematically identify places where `satisfies` would improve the code? No grep pattern, no heuristic, no examples of what to look for.
Fix: Add to Step 3 a review-mode sub-bullet: "In review mode, search for `const x: SomeType = { ... }` annotations on objects with string/number literals. These are candidates for `satisfies` if narrower literal inference would benefit callers."

**F-08 — No quality criteria for type guards** (P1, M5)
The task asks about "type guard quality." The type-system.md reference shows type guard examples but defines no quality rubric. ky's type guards use `(error as any)?.name === HTTPError.name` as a cross-realm fallback — is this acceptable or an anti-pattern? The anti-patterns ref says `as any` is bad, but for cross-realm `instanceof` fallbacks this is a known necessity. No guidance for this edge case.
Fix: Add to type-system.md's "Type Guards" section: "Cross-realm `instanceof` may fail when objects cross iframe/module boundaries. A name-based fallback like `(error as {name?: string})?.name === 'ErrorClass'` is acceptable when `instanceof` alone is unreliable. Prefer `as {name?: string}` over `as any` in the fallback."

---

### Step 4: Remove unsafe shortcuts

**F-09 — `@ts-expect-error` not distinguished from `@ts-ignore`** (P1, S2)
Step 4 blocklist includes `@ts-ignore` but not `@ts-expect-error`. testing.md reference explicitly RECOMMENDS `@ts-expect-error` for type tests. ky uses `@ts-expect-error` (never `@ts-ignore`) with comments like "Types are outdated." When grepping for anti-patterns, both show up. Is `@ts-expect-error` a violation or not?
Fix: Amend Step 4 blocklist: "Block `@ts-ignore` (prefer `@ts-expect-error` with an explanatory comment, which is allowed for documented type system gaps and type tests)."

**F-10 — "Unchecked `as`" has no definition** (P0, M1)
Step 4 says to block "unchecked `as`." ky has ~15 `as` assertions. Some are clearly needed for DOM/Fetch API interop (`this.#options as RequestInit`), some are suspicious (`error as Error`), some have preceding guards. What makes an `as` "checked"? No definition, no criteria, no examples in the skill.
Fix: Add to Step 4 or anti-patterns.md: "An `as` assertion is 'checked' if it is preceded by a runtime narrowing guard (typeof, instanceof, discriminator check, or type guard function) that validates the cast. An `as` assertion is 'unchecked' if the cast bypasses runtime validation. `as` casts required for known TypeScript lib type mismatches (e.g., `RequestInit`, `HeadersInit`) should be annotated with a comment explaining why."

**F-11 — "Block `any`" has no threshold or review-mode behavior** (P1, M1)
ky has ~10 `any` usages. The merge utility has 3 with an explicit `// TODO: Make this strongly-typed (no any).` comment. "Block" implies preventing new additions, but in review mode, what's the expected output? Flag all? Refactor all? Open issues? The verb "block" doesn't map to review actions.
Fix: Amend Step 4: "In review mode, 'block' means: flag each occurrence, categorize as (a) fixable now, (b) needs refactor plan, or (c) intentional/documented. Prioritize boundary-crossing `any` (function parameters, return types) over internal implementation `any`."

**F-12 — `moduleResolution: "node"` vs `"node16"` is clear enough but could be explicit** (P2, M1)
Step 4 says "legacy `moduleResolution: "node"`." ky uses `"node16"` which is modern. The module table in the skill correctly shows `"node16"` as the choice for Node.js ESM. This was clear, but the word "legacy" is only in Step 4 — someone might wonder if `"node16"` is legacy too.
Fix: Amend Step 4: "Block legacy `moduleResolution: "node"` (the bare `"node"` value — not `"node16"` or `"nodenext"`, which are modern)."

---

### Step 5: Verify

**F-13 — No "produce output" step** (P0, M4)
Step 5 says "run [the commands]" and "separate type checking from transpilation." Both `tsc --noEmit` and `xo` passed. But the skill never says what to DO with the findings from Steps 2–4. There's no "summarize findings," "produce a report," or "suggest changes" step. The workflow just... ends. For a review task, the deliverable is the findings list, but the skill doesn't say to produce one.
Fix: Add a Step 6: "Summarize findings. For review tasks: list each finding with (a) file and line, (b) which blocklist item or preference it violates, (c) severity, (d) suggested fix. For authoring tasks: verify the change compiles and passes lint before committing."

**F-14 — No guidance on interpreting lint warnings vs errors** (P2, M5)
xo produced 9 warnings (complexity, TODO comments, file length). Step 5 doesn't say whether lint warnings are in scope for a TypeScript type safety review, or how to triage them. I used my own judgment to exclude style/complexity warnings from the type safety findings.
Fix: Add to Step 5: "Treat type-related lint errors as blocking. Treat warnings (style, complexity, TODO comments) as informational unless they indicate a type safety issue."

**F-15 — "Feels uncertain" is unmeasurable** (P2, M6)
Step 5 says "If the first pass still feels uncertain, read one adjacent reference." For a well-typed project like ky where tsc passes cleanly, nothing "feels uncertain" — but there are still real findings (as any in type guards, missing satisfies, disabled safety rules). "Feels uncertain" is not an actionable trigger.
Fix: Replace with: "If you found anti-pattern instances in Step 4 that you're unsure how to categorize (fixable vs. intentional), read one adjacent reference for context."

---

## What worked well

**W-01**: The 10-category classification system is comprehensive and covers real TS work domains. Every aspect of the ky review could be mapped to at least one category.

**W-02**: Anti-derail guardrails ("Do not cargo-cult advanced type tricks") actively prevented scope creep. I was tempted to suggest branded types for ky's error hierarchy but the guardrail correctly stopped me — structural typing works fine here.

**W-03**: Step 2's five bullets are individually clear and directly applicable. Checking `unknown` usage, strict mode, and export annotations produced real findings.

**W-04**: The "Do this, not that" table is excellent quick-reference material. The `satisfies` row directly informed the finding that ky has zero `satisfies` usage.

**W-05**: Recovery paths map errors to solutions clearly. "Boundary data is untrusted → replace unchecked `as` with `unknown` plus a type guard" directly applies to ky's merge.ts.

**W-06**: Reference files are high-quality. `type-system.md` type guard examples match the exact pattern ky uses. `modern-features.md` covers TS 5.0–5.7 features comprehensively with practical examples.

**W-07**: The strict config baseline is thorough. ky's extended `@sindresorhus/tsconfig` includes ALL recommended flags plus extras (`erasableSyntaxOnly`, `noPropertyAccessFromIndexSignature`, `noUncheckedSideEffectImports`). The skill's baseline made it easy to confirm this.

**W-08**: The anti-pattern examples in the references directly match real issues found in ky (e.g., `as any` in type guards, `any` parameters in merge utilities).

---

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 4 | F-01, F-06, F-10, F-13 |
| P1 | 7 | F-02, F-03, F-04, F-07, F-08, F-09, F-11 |
| P2 | 4 | F-05, F-12, F-14, F-15 |

## Derailment density map

| Workflow Phase | Steps | P0 | P1 | P2 | Total |
|---|---|---|---|---|---|
| Step 1: Classify | 1 | 1 | 2 | 0 | 3 |
| Step 2: Baseline | 5 | 1 | 1 | 1 | 3 |
| Step 3: Type mechanism | 5 | 0 | 2 | 0 | 2 |
| Step 4: Remove unsafe | 1 | 1 | 2 | 1 | 4 |
| Step 5: Verify | 3 | 1 | 0 | 2 | 3 |

## Root cause analysis

| Root Cause | Count | IDs |
|---|---|---|
| M1 Ambiguous threshold | 4 | F-01, F-10, F-11, F-12 |
| M4 Missing exec method | 4 | F-03, F-05, F-07, F-13 |
| M6 Vague verb | 3 | F-02, F-11, F-15 |
| S2 Contradictory paths | 2 | F-06, F-09 |
| M5 Assumed knowledge | 2 | F-08, F-14 |
| S3 Scattered information | 1 | F-04 |
