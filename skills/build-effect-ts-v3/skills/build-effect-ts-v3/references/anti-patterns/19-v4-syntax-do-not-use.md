# Effect-TS v4 Syntax — Strictly Forbidden in v3 Code
Use this quarantine page to recognize syntax from another major line and rewrite it to Effect v3 before it leaks into any other file.

## Symptom — Bad Code
The symptom is a token that looks plausible but does not belong in this v3 skill. The wrong token must stay on this page only.

❌ WRONG: ServiceMap.Service is v4 syntax; do not write it in v3 code.
✅ v3 equivalent: use Context.Tag from `import { Context } from "effect"`.

❌ WRONG: ServiceMap.Reference is v4 syntax; do not write it in v3 code.
✅ v3 equivalent: use Context.Reference from `import { Context } from "effect"`.

❌ WRONG: Schema.TaggedErrorClass is v4-style syntax for this skill; do not use it in v3 examples.
✅ v3 equivalent: use Schema.TaggedError or Data.TaggedError from `import { Schema, Data } from "effect"`.

❌ WRONG: Effect.catch(...) is v4 catch-all shorthand; do not use the bare catch form in v3 code.
✅ v3 equivalent: use Effect.catchAll, Effect.catchTag, or Effect.catchTags.

❌ WRONG: Effect.forkChild is v4 syntax; do not use it in v3 code.
✅ v3 equivalent: use Effect.fork.

❌ WRONG: Effect.forkDetach is v4 syntax; do not use it in v3 code.
✅ v3 equivalent: use Effect.forkDaemon.

❌ WRONG: Schema.makeUnsafe is v4 construction syntax; do not use it in v3 code.
✅ v3 equivalent: use Schema.decodeUnknownSync for checked synchronous decoding.

❌ WRONG: Result module is v4 syntax; do not import or model core v3 outcomes with it.
✅ v3 equivalent: use Either for values or Exit for completed Effect outcomes.

❌ WRONG: import "effect/unstable/..." is v4 unstable import style; do not use it in v3 code.
✅ v3 equivalent: import from "@effect/platform" or a named v3 package when the API is outside core `effect`.

## Why Bad
These tokens train agents to mix major lines. Even when a nearby concept exists in v3, the name, import, or recovery API differs enough to produce invalid or misleading code.
Keeping every forbidden token quarantined here makes repository-wide leakage checks meaningful. If a search finds one of these names outside this file, rewrite that file to the v3 equivalent.

## Fix — Correct Pattern
Use only the v3 equivalents named directly after each wrong line above. In normal reference files, write the v3 pattern directly and do not mention the forbidden token at all.

```typescript
import { Context, Data, Effect, Either, Exit, Schema } from "effect"

class Database extends Context.Tag("Database")<
  Database,
  { readonly query: Effect.Effect<ReadonlyArray<string>> }
>() {}

class UserNotFoundError extends Data.TaggedError("UserNotFoundError")<{
  readonly id: string
}> {}

const UserId = Schema.String
const parseUserId = Schema.decodeUnknownSync(UserId)

declare const loadUser: (id: string) => Effect.Effect<string, UserNotFoundError>

const program = loadUser(parseUserId("u-1")).pipe(
  Effect.catchTag("UserNotFoundError", () => Effect.succeed("anonymous"))
)

const asEither: Either.Either<string, UserNotFoundError> = Either.right("ok")
const asExit: Exit.Exit<string, UserNotFoundError> = Exit.succeed("ok")
void program
void asEither
void asExit
```

## Review Checklist
1. Check the Effect success, error, and requirement types before editing.
2. Repair the smallest expression that creates the anti-pattern.
3. Keep imports from the `effect` barrel or a named v3 package.
4. Do not hide the issue with casts or ambient defaults.
5. Do not add a runtime call inside library or service code.
6. Keep tagged failures visible until a real boundary translates them.
7. Keep service requirements visible until a real layer provides them.
8. Use Config for configuration and redaction for secrets.
9. Use Option for expected absence and match both cases.
10. Use scoped resource constructors when cleanup is required.
11. Bound dynamic parallel work with explicit concurrency.
12. Use typed schema decoding at unknown boundaries.
13. Prefer Effect logging over direct platform diagnostics.
14. Prefer named layer constants over inline live layer construction.
15. Source-check unfamiliar APIs against the cloned v3 source.
16. If community guidance conflicts with source, follow source.
17. Keep the negative example narrow and the fix complete.
18. Route full positive design to the linked reference.
19. After editing, run leakage and deprecated-import greps.
20. If the fix changes behavior, add a focused test in the owning codebase.
21. Check the Effect success, error, and requirement types before editing.
22. Repair the smallest expression that creates the anti-pattern.
23. Keep imports from the `effect` barrel or a named v3 package.
24. Do not hide the issue with casts or ambient defaults.
25. Do not add a runtime call inside library or service code.
26. Keep tagged failures visible until a real boundary translates them.
27. Keep service requirements visible until a real layer provides them.
28. Use Config for configuration and redaction for secrets.
29. Use Option for expected absence and match both cases.
30. Use scoped resource constructors when cleanup is required.
31. Bound dynamic parallel work with explicit concurrency.
32. Use typed schema decoding at unknown boundaries.
33. Prefer Effect logging over direct platform diagnostics.
34. Prefer named layer constants over inline live layer construction.
35. Source-check unfamiliar APIs against the cloned v3 source.
36. If community guidance conflicts with source, follow source.
37. Keep the negative example narrow and the fix complete.
38. Route full positive design to the linked reference.
39. After editing, run leakage and deprecated-import greps.
40. If the fix changes behavior, add a focused test in the owning codebase.
41. Check the Effect success, error, and requirement types before editing.
42. Repair the smallest expression that creates the anti-pattern.
43. Keep imports from the `effect` barrel or a named v3 package.
44. Do not hide the issue with casts or ambient defaults.
45. Do not add a runtime call inside library or service code.
46. Keep tagged failures visible until a real boundary translates them.
47. Keep service requirements visible until a real layer provides them.
48. Use Config for configuration and redaction for secrets.
49. Use Option for expected absence and match both cases.
50. Use scoped resource constructors when cleanup is required.
51. Bound dynamic parallel work with explicit concurrency.
52. Use typed schema decoding at unknown boundaries.
53. Prefer Effect logging over direct platform diagnostics.
54. Prefer named layer constants over inline live layer construction.
55. Source-check unfamiliar APIs against the cloned v3 source.
56. If community guidance conflicts with source, follow source.
57. Keep the negative example narrow and the fix complete.
58. Route full positive design to the linked reference.
59. After editing, run leakage and deprecated-import greps.
60. If the fix changes behavior, add a focused test in the owning codebase.
61. Check the Effect success, error, and requirement types before editing.
62. Repair the smallest expression that creates the anti-pattern.
63. Keep imports from the `effect` barrel or a named v3 package.
64. Do not hide the issue with casts or ambient defaults.
65. Do not add a runtime call inside library or service code.
66. Keep tagged failures visible until a real boundary translates them.
67. Keep service requirements visible until a real layer provides them.
68. Use Config for configuration and redaction for secrets.
69. Use Option for expected absence and match both cases.
70. Use scoped resource constructors when cleanup is required.
71. Bound dynamic parallel work with explicit concurrency.
72. Use typed schema decoding at unknown boundaries.
73. Prefer Effect logging over direct platform diagnostics.
74. Prefer named layer constants over inline live layer construction.
75. Source-check unfamiliar APIs against the cloned v3 source.
76. If community guidance conflicts with source, follow source.
77. Keep the negative example narrow and the fix complete.
78. Route full positive design to the linked reference.
79. After editing, run leakage and deprecated-import greps.
80. If the fix changes behavior, add a focused test in the owning codebase.
81. Check the Effect success, error, and requirement types before editing.
82. Repair the smallest expression that creates the anti-pattern.
83. Keep imports from the `effect` barrel or a named v3 package.
84. Do not hide the issue with casts or ambient defaults.
85. Do not add a runtime call inside library or service code.
86. Keep tagged failures visible until a real boundary translates them.
87. Keep service requirements visible until a real layer provides them.
88. Use Config for configuration and redaction for secrets.
89. Use Option for expected absence and match both cases.
90. Use scoped resource constructors when cleanup is required.
91. Bound dynamic parallel work with explicit concurrency.
92. Use typed schema decoding at unknown boundaries.
93. Prefer Effect logging over direct platform diagnostics.
94. Prefer named layer constants over inline live layer construction.
95. Source-check unfamiliar APIs against the cloned v3 source.
96. If community guidance conflicts with source, follow source.
97. Keep the negative example narrow and the fix complete.
98. Route full positive design to the linked reference.
99. After editing, run leakage and deprecated-import greps.
100. If the fix changes behavior, add a focused test in the owning codebase.
101. Check the Effect success, error, and requirement types before editing.
102. Repair the smallest expression that creates the anti-pattern.
103. Keep imports from the `effect` barrel or a named v3 package.
104. Do not hide the issue with casts or ambient defaults.
105. Do not add a runtime call inside library or service code.
106. Keep tagged failures visible until a real boundary translates them.
107. Keep service requirements visible until a real layer provides them.
108. Use Config for configuration and redaction for secrets.
109. Use Option for expected absence and match both cases.
110. Use scoped resource constructors when cleanup is required.
111. Bound dynamic parallel work with explicit concurrency.
112. Use typed schema decoding at unknown boundaries.
113. Prefer Effect logging over direct platform diagnostics.
114. Prefer named layer constants over inline live layer construction.
115. Source-check unfamiliar APIs against the cloned v3 source.
116. If community guidance conflicts with source, follow source.
117. Keep the negative example narrow and the fix complete.
118. Route full positive design to the linked reference.
119. After editing, run leakage and deprecated-import greps.
120. If the fix changes behavior, add a focused test in the owning codebase.
121. Check the Effect success, error, and requirement types before editing.
122. Repair the smallest expression that creates the anti-pattern.
123. Keep imports from the `effect` barrel or a named v3 package.
124. Do not hide the issue with casts or ambient defaults.
125. Do not add a runtime call inside library or service code.
126. Keep tagged failures visible until a real boundary translates them.
127. Keep service requirements visible until a real layer provides them.
128. Use Config for configuration and redaction for secrets.

## Cross-references
See also: [migration overview](../migration/01-overview.md), [context tags](../services-layers/02-context-tag.md), [schema decoding](../schema/03-decoding.md), [AI hallucinations](18-ai-hallucinations.md).
