# Inline Layer Construction
Use this when reusable layers are constructed inside functions, loops, or route handlers.

## Symptom — Bad Code
```typescript
import { Context, Effect, Layer } from "effect"

class Cache extends Context.Tag("Cache")<Cache, { readonly get: (key: string) => Effect.Effect<string> }>() {}

declare const makeCache: Effect.Effect<{ readonly get: (key: string) => Effect.Effect<string> }>

const handler = (key: string) =>
  Effect.gen(function* () {
    const layer = Layer.effect(Cache, makeCache)
    const cache = yield* Effect.provide(Cache, layer)
    return yield* cache.get(key)
  })
```

## Why Bad
The layer is recreated each time the handler description is built.
Inline layers hide application composition and memoization behavior.
Assistants often duplicate inline live layers instead of reusing canonical layers.

## Fix — Correct Pattern
```typescript
import { Context, Effect, Layer } from "effect"

class Cache extends Context.Tag("Cache")<Cache, { readonly get: (key: string) => Effect.Effect<string> }>() {}

declare const makeCache: Effect.Effect<{ readonly get: (key: string) => Effect.Effect<string> }>

const CacheLive = Layer.effect(Cache, makeCache)

const handler = (key: string) =>
  Effect.gen(function* () {
    const cache = yield* Cache
    return yield* cache.get(key)
  }).pipe(Effect.provide(CacheLive))
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
See also: [layer composition gotchas](../services-layers/12-layer-composition-gotchas.md), [layer composition](../services-layers/05-layer-composition.md), [context tags](../services-layers/02-context-tag.md).
