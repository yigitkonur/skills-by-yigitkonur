# AI Hallucination Correction Table
Use this table to replace common assistant-generated Effect mistakes with verified v3 patterns before editing application code.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

declare const fetchUser: (id: string) => Effect.Effect<{ readonly id: string }, Error>

const program = Effect.gen(function* () {
  const user = yield fetchUser("u-1")
  return user
})
```

## Why Bad
Effect has a broad surface area, so assistant output often blends ordinary TypeScript, old examples, and APIs from neighboring packages.
The most common hallucinations cluster around generators, runtime boundaries, layers, schema decoding, Option, and error recovery.
Do not accept an unfamiliar API until the v3 source or official docs confirm it.

## Fix — Correct Pattern
Use this wrong-to-right map as a first pass, then verify the final code against the positive reference.

## Wrong to Right Table
| Wrong assistant output | Correct v3 pattern | Check reference |
|---|---|---|
| `yield effect` inside `Effect.gen` | `yield* effect` | Generator delegation |
| `return Effect.fail(error)` in a branch | `return yield* Effect.fail(error)` | Control flow |
| Throwing a domain error | `Effect.fail(new TaggedDomainError(...))` | Typed failures |
| Running each step with runtime calls | Compose and run once at the edge | Runtime boundary |
| Service returns Promise after running Effect | Service returns Effect | Service design |
| Large `Effect.all(items.map(fn))` | `Effect.all(items.map(fn), { concurrency: n })` | Parallelism |
| `Promise.all` in workflow | `Effect.all` or `Effect.forEach` | Concurrency |
| Direct environment lookup | `Config.string` or `Config.redacted` | Config |
| Raw secret in log message | Redacted config plus structured Effect log | Secrets |
| `Effect.sync(() => asyncWork())` | `Effect.tryPromise` | Constructor |
| `Effect.succeed(promise)` | `Effect.promise` or `Effect.tryPromise` | Constructor |
| `Effect.promise` around rejecting API | `Effect.tryPromise` with catch mapper | Error channel |
| `Option.getOrThrow(option)` | `Option.match` | Option |
| Nullable domain field | `Option.Option<A>` in domain | Domain |
| Generic `Error` failure | Tagged domain error | Errors |
| One catch-all for known failures | `catchTag` or `catchTags` | Recovery |
| String matching on error message | Match on `_tag` | Recovery |
| Cast away requirements | Provide the required layer | Requirements |
| Cast away failures | Handle or expose the failure | Errors |
| Decode then broad cast | `Schema.decodeUnknown` or `Schema.decodeUnknownSync` | Schema |
| Legacy schema package import | `import { Schema } from "effect"` | Imports |
| Deep core module import by default | Barrel import from `effect` | Imports |
| Inline live layer in handler | Named layer constant | Layers |
| Expecting provider output after provide | Use `Layer.provideMerge` | Layers |
| Merging dependent layers | Use provide or provideMerge | Layers |
| Manual finalizer in Promise callback | `Effect.acquireRelease` with scope | Resources |
| Fork and forget in request path | Join or scope the fiber deliberately | Concurrency |
| Manual retry loop | `Effect.retry` with Schedule | Scheduling |
| Raw timer Promise sleep | `Effect.sleep` | Scheduling |
| Direct diagnostic output | Effect logging APIs | Observability |

## Source Verification Rule
Search `/tmp/effect-corpus/source/effect/packages/effect/src/Module.ts` first, then cached official docs, then community skills. If only a community skill mentions an API, do not use it until source confirms it.

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
129. Use Option for expected absence and match both cases.
130. Use scoped resource constructors when cleanup is required.
131. Bound dynamic parallel work with explicit concurrency.
132. Use typed schema decoding at unknown boundaries.
133. Prefer Effect logging over direct platform diagnostics.
134. Prefer named layer constants over inline live layer construction.
135. Source-check unfamiliar APIs against the cloned v3 source.
136. If community guidance conflicts with source, follow source.
137. Keep the negative example narrow and the fix complete.
138. Route full positive design to the linked reference.
139. After editing, run leakage and deprecated-import greps.
140. If the fix changes behavior, add a focused test in the owning codebase.
141. Check the Effect success, error, and requirement types before editing.
142. Repair the smallest expression that creates the anti-pattern.
143. Keep imports from the `effect` barrel or a named v3 package.
144. Do not hide the issue with casts or ambient defaults.
145. Do not add a runtime call inside library or service code.
146. Keep tagged failures visible until a real boundary translates them.
147. Keep service requirements visible until a real layer provides them.
148. Use Config for configuration and redaction for secrets.
149. Use Option for expected absence and match both cases.
150. Use scoped resource constructors when cleanup is required.
151. Bound dynamic parallel work with explicit concurrency.
152. Use typed schema decoding at unknown boundaries.
153. Prefer Effect logging over direct platform diagnostics.
154. Prefer named layer constants over inline live layer construction.
155. Source-check unfamiliar APIs against the cloned v3 source.
156. If community guidance conflicts with source, follow source.
157. Keep the negative example narrow and the fix complete.
158. Route full positive design to the linked reference.
159. After editing, run leakage and deprecated-import greps.
160. If the fix changes behavior, add a focused test in the owning codebase.
161. Check the Effect success, error, and requirement types before editing.
162. Repair the smallest expression that creates the anti-pattern.
163. Keep imports from the `effect` barrel or a named v3 package.
164. Do not hide the issue with casts or ambient defaults.
165. Do not add a runtime call inside library or service code.

## Cross-references
See also: [core generators](../core/05-generators.md), [layer composition gotchas](../services-layers/12-layer-composition-gotchas.md), [schema decoding](../schema/03-decoding.md), [v3 syntax quarantine](19-v4-syntax-do-not-use.md).
