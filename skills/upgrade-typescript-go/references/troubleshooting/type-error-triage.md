# Type Error Triage & Strict Mode Alignment

## Overview

While TypeScript 7.0 preserves identical type semantics to TypeScript 6.0, stricter defaults or corrected compiler bugs may surface latent type issues in existing code.

## Top Common Type Errors & Remediation

### 1. TS2532: Object is possibly 'undefined' (Indexed Access)

**Cause**: Accessing array elements with `noUncheckedIndexedAccess: true` or accessing optional nested object fields without narrowing.

```ts
// ❌ Problematic
const message = messages[1];
expect(message.tools[0].name).toBe('calculator');

// ✅ Solution: Optional chaining or non-null assertion in tests
const message = messages[1];
expect(message?.tools?.[0]?.name).toBe('calculator');
// Or in strict test assertions:
expect(message!.tools![0]!.name).toBe('calculator');
```

### 2. TS2322: Type 'null' is not assignable to type 'string | undefined'

**Cause**: Passing `null` to a field typed strictly as `string | undefined`.

```ts
// ❌ Problematic
const topicId: string | null = getTopicId();
createContext({ topicId }); // Error: topicId accepts string | undefined

// ✅ Solution: Nullish coalescing
createContext({ topicId: topicId ?? undefined });
```

### 3. TS2304 / TS2552: Cannot find name / Cannot find global type

**Cause**: Missing ambient type definitions (e.g. `node`, `vitest/globals`, `react`).

**Solution**: Ensure `compilerOptions.types` in `tsconfig.json` includes the required ambient libraries:
```json
{
  "compilerOptions": {
    "types": ["node", "vitest/globals", "react"]
  }
}
```

### 4. TS7016: Could not find a declaration file for module

**Cause**: Importing an untyped JavaScript dependency.

**Solution**:
1. Install `@types/package-name` if available.
2. Or add a local ambient declaration `src/types/ambient.d.ts`:
   ```ts
   declare module 'untyped-package';
   ```
