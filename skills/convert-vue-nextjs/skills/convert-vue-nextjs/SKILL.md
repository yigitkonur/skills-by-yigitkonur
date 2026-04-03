---
name: convert-vue-nextjs
description: Use skill if you are converting Vue 2/3 or Nuxt components to Next.js App Router with React, including component mapping, state migration, routing, SSR, or ecosystem packages.
---

# Vue to Next.js

Convert Vue/Nuxt applications and components to idiomatic Next.js App Router code. Treat the Vue source as the contract: match its public API exactly, then rebuild internals with React patterns.

## Use this skill when

- Converting Vue SFC (`.vue`) files to React/Next.js components
- Migrating Nuxt pages or layouts to Next.js App Router
- Converting Vue state management (Pinia/Vuex) to React equivalents
- Mapping Vue Router config to Next.js file-system routing
- Replacing Vue ecosystem packages with React equivalents
- Planning or executing a full Vue-to-Next.js migration

## Do not use this skill when

- Building a new React/Next.js app from scratch (no Vue source)
- Converting between React frameworks (CRA → Next.js, Remix → Next.js)
- Converting React to Vue (reverse direction)
- General React or Next.js questions unrelated to migration

## Start with these decisions

| Situation | Action |
|---|---|
| Converting a single Vue SFC | Quick start below — if complex: `references/conversion/component-mapping.md` |
| Migrating a full page/route with many interactive descendants | Load `references/conversion/migration-workflow.md` and `references/conversion/ssr-data-fetching.md` — start with a route-local client component for parity, then split server/client boundaries afterward |
| Migrating Pinia or Vuex stores | Load `references/conversion/state-management.md` |
| Converting Vue Router config | Load `references/conversion/routing-conversion.md` |
| Converting Nuxt SSR or data fetching | Load `references/conversion/ssr-data-fetching.md` |
| Complex patterns (transitions, teleport, plugins, generics) | Load `references/conversion/advanced-patterns.md` |
| Need per-component step-by-step workflow | Load `references/conversion/migration-workflow.md` |
| Choosing React replacements for Vue libraries | Load `references/ecosystem/package-mapping.md` |
| Planning a full app migration | Load `references/strategy/assessment-checklist.md` then `references/strategy/migration-strategies.md` |
| Running Vue and Next.js simultaneously | Load `references/strategy/coexistence-patterns.md` |
| Testing migration parity | Load `references/strategy/testing-strategy.md` |
| Request is ambiguous | Default to single-component conversion. Do not assume full migration. |

## Non-negotiable rules

1. **Preserve the contract, not the syntax.** Match the component's public API — props, events, slots, DOM output — exactly. Internal implementation will differ.
2. **Read Vue source before converting.** Identify all patterns (reactivity, state, routing, slots, emits) before writing any React code.
3. **Immutable state updates only.** Never mutate. Always produce new references with spread, `map`, or `filter`.
4. **Explicit dependency arrays.** Every `useEffect`, `useMemo`, `useCallback` must list dependencies. Vue auto-tracks; React does not.
5. **Choose the smallest client boundary that preserves parity.** For single components and refined routes, push `'use client'` as deep as possible. For first-pass page/route migrations, keep a route-local client island until parity is proven, then split it later.
6. **Map emits to callback props.** Vue's `$emit('event', data)` becomes `onEvent(data)` prop calls.
7. **Convert `<style scoped>` to CSS Modules.** Import as `styles` object. Use dot access for identifier-safe class names and bracket access for names like `counter-card` (`styles['counter-card']`).

## Quick start — Single component conversion

### Conversion algorithm

1. Read the `.vue` file — identify template directives, script setup patterns, style scoping.
2. Determine Server vs Client — if component uses `ref`, `reactive`, event handlers, or browser APIs → `'use client'`; if data-only display → Server Component.
3. Convert `<template>` → JSX using the directive map below.
4. Convert `<script setup>` → function body with hooks.
5. Convert `<style scoped>` → CSS Module import.
6. Convert emits → callback props, slots → children/props.

### Template → JSX directive map

| Vue | JSX |
|---|---|
| `{{ label }}` | `{label}` |
| `v-if="show"` | `{show && <El />}` |
| `v-if` / `v-else` | `{show ? <A /> : <B />}` |
| `v-show="visible"` | `<div style={{ display: visible ? undefined : 'none' }}>` |
| `v-for="item in items" :key="item.id"` | `{items.map(item => <El key={item.id} />)}` |
| `v-model="name"` | `value={name} onChange={e => setName(e.target.value)}` |
| `:class="{ active: isActive }"` | `className={isActive ? 'active' : ''}` |
| `:style="{ color }"` | `style={{ color }}` |
| `@click="handler"` | `onClick={handler}` |
| `@click="count += 1"` | `onClick={() => setCount(c => c + 1)}` or extract a named handler first |
| `@click.prevent` | `onClick={e => { e.preventDefault(); handler() }}` |
| `@click.stop` | `onClick={e => { e.stopPropagation(); handler() }}` |
| `@keyup.enter` | `onKeyUp={e => e.key === 'Enter' && handler()}` |
| `v-html="raw"` | `dangerouslySetInnerHTML={{ __html: raw }}` |
| `<slot />` | `{children}` |
| `<slot name="header" />` | `{header}` (pass as prop) |
| `<Teleport to="body">` | `createPortal(children, document.body)` |

### Reactivity → Hooks map

| Vue | React | Note |
|---|---|---|
| `ref(0)` | `useState(0)` | Replace via setter, never mutate |
| `reactive({})` | `useState({})` | Spread to update: `setState(p => ({...p, key: val}))` |
| `computed(() => x)` | Derive during render; use `useMemo(() => x, [deps])` only when expensive or identity-sensitive | React does not auto-track deps |
| `watch(src, cb)` | `useEffect(() => { cb() }, [src])` | Add cleanup return if needed |
| `watchEffect(cb)` | `useEffect(() => { ... }, [explicitDeps])` | Extract every external value from the body into the deps array |
| `onMounted(cb)` | `useEffect(cb, [])` | Empty deps = run once |
| `onUnmounted(cb)` | `useEffect(() => cb, [])` | Return the cleanup function from the effect |
| `provide/inject` | `createContext` / `useContext` | Wrap tree with Provider |
| `$emit('name', data)` | `props.onName(data)` | Callback prop pattern |
| `defineProps<T>()` | Destructure from typed props | `function C({ title }: Props)` |

### Complete example

**Vue SFC (before):**

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ initialCount?: number }>()
const emit = defineEmits<{ (e: 'change', value: number): void }>()

const count = ref(props.initialCount ?? 0)
const doubled = computed(() => count.value * 2)

function increment() {
  count.value++
  emit('change', count.value)
}
</script>

<template>
  <div class="counter">
    <p>Count: {{ count }} (doubled: {{ doubled }})</p>
    <button @click="increment">+1</button>
    <slot name="footer" />
  </div>
</template>

<style scoped>
.counter { padding: 1rem; border: 1px solid #ccc; border-radius: 8px; }
</style>
```

**Next.js component (after):**

```tsx
'use client';
import { useState } from 'react';
import styles from './Counter.module.css';

interface CounterProps {
  initialCount?: number;
  onChange?: (value: number) => void;
  footer?: React.ReactNode;
}

export default function Counter({ initialCount = 0, onChange, footer }: CounterProps) {
  const [count, setCount] = useState(initialCount);
  const doubled = count * 2;

  function increment() {
    const next = count + 1;
    setCount(next);
    onChange?.(next);
  }

  return (
    <div className={styles.counter}>
      <p>Count: {count} (doubled: {doubled})</p>
      <button onClick={increment}>+1</button>
      {footer}
    </div>
  );
}
```

**What changed:** `defineProps` → interface + destructured params. `defineEmits` → callback prop. `ref()` → `useState()`. `computed()` → derived render value (reserve `useMemo()` for expensive or identity-sensitive work). `count.value++` → `setCount(next)`. Named slot → `footer` prop. `<style scoped>` → CSS Module.

## Key conversion patterns

### Pinia store → Zustand store

```ts
// Vue (Pinia)                           // React (Zustand)
export const useStore = defineStore(      import { create } from 'zustand';
  'counter', () => {
  const count = ref(0)                   export const useStore = create((set, get) => ({
  const doubled = computed(                count: 0,
    () => count.value * 2)                 doubled: () => get().count * 2,
  function inc() { count.value++ }         inc: () => set(s => ({ count: s.count + 1 })),
  return { count, doubled, inc }         }));
})
```

### Vue Router → Next.js App Router

| Vue Router | Next.js |
|---|---|
| `path: '/users/:id'` | `app/users/[id]/page.tsx` |
| `children: [...]` | Nested folders + `layout.tsx` |
| `beforeEach` guard | `middleware.ts` with `config.matcher` |
| `<router-link>` | `<Link>` from `next/link` |
| `router.push()` | `useRouter().push()` from `next/navigation` |
| `<router-view />` | `{children}` in layout |

### Nuxt data fetching → Next.js

| Nuxt | Next.js |
|---|---|
| `useFetch('/api/data')` | `async` Server Component + `fetch()` |
| `useLazyFetch` | Client Component + TanStack Query |
| `server/api/route.ts` | `app/api/route/route.ts` (Route Handler) |
| `useRuntimeConfig()` | `process.env` / `NEXT_PUBLIC_*` |
| `refreshNuxtData()` | `router.refresh()` or `revalidatePath()` |

### Composable → Custom Hook

```ts
// Vue composable                         // React hook
export function useToggle(init = false) {  export function useToggle(init = false) {
  const value = ref(init)                    const [value, setValue] = useState(init);
  function toggle() {                        const toggle = useCallback(
    value.value = !value.value                 () => setValue(v => !v), []
  }                                          );
  return { value, toggle }                   return { value, toggle };
}                                          }
```

## Common mistakes

| # | Mistake | Why it happens | Fix |
|---|---|---|---|
| 1 | Mutating state directly | Vue allows `items.push()`; React ignores mutations | Always use setter: `setItems(prev => [...prev, item])` |
| 2 | Missing dependency arrays | Vue auto-tracks; React needs explicit deps | Add `[dep1, dep2]` to every `useEffect`/`useMemo`/`useCallback` |
| 3 | Overusing `useEffect` for derived data | Vue `watch` habit; React has simpler path | Compute during render: `const full = first + ' ' + last` |
| 4 | Forgetting `'use client'` | Vue has no server/client boundary concept | Add `'use client'` to any component using hooks or event handlers |
| 5 | Placing `'use client'` too high | Marks entire subtree as client-rendered | Push `'use client'` to the smallest interactive leaf component |
| 6 | No cleanup in `useEffect` | Vue `onUnmounted` is separate; React combines setup+cleanup | Return cleanup function: `return () => ws.close()` |
| 7 | Creating objects in render | Vue `setup()` runs once; React re-runs every render | Wrap with `useMemo`/`useCallback` or move outside component |
| 8 | Using `useRef` for reactive state | Confusing Vue `ref` with React `useRef` | Use `useState` for UI state; `useRef` is for non-reactive values |
| 9 | Expecting reactive prop destructuring | Vue needs `toRefs`; React props are fresh each render | Destructure freely — React gives new values on each render |
| 10 | Index keys on reorderable lists | Same issue in both frameworks but more visible in React | Use stable unique IDs: `key={item.id}` |

## Do this / not that

| Do this | Not that |
|---|---|
| Use `useState` setter with spread/map/filter for updates | Mutate state objects or arrays directly |
| List all dependencies in `useEffect`, `useMemo`, `useCallback` | Omit dependency arrays or leave them empty when deps exist |
| Compute derived values inline or with `useMemo` | Use `useEffect` + `setState` to compute derived data |
| Add `'use client'` only at leaf interactive components | Place `'use client'` at page or layout level |
| Use `useRef` for DOM refs and non-reactive values | Use `useRef` as a replacement for Vue `ref()` reactive state |
| Use Framer Motion for enter/exit animations | Convert Vue `<Transition>` to CSS-only animations |
| Return cleanup functions in `useEffect` for subscriptions/timers | Forget cleanup and cause memory leaks |
| Destructure React props directly | Wrap props with `toRefs`-style patterns |

## Reference map

| Need | Read |
|---|---|
| Full directive/slot/emit mapping | `references/conversion/component-mapping.md` |
| State migration (Pinia, Vuex, composables) | `references/conversion/state-management.md` |
| Vue Router → App Router conversion | `references/conversion/routing-conversion.md` |
| SSR, data fetching, caching | `references/conversion/ssr-data-fetching.md` |
| Transitions, teleport, plugins, generics | `references/conversion/advanced-patterns.md` |
| Per-component 10-step workflow | `references/conversion/migration-workflow.md` |
| React equivalents for Vue libraries | `references/ecosystem/package-mapping.md` |
| Migration planning and execution order | `references/strategy/migration-strategies.md` |
| Pre-migration scope assessment | `references/strategy/assessment-checklist.md` |
| Running Vue and Next.js simultaneously | `references/strategy/coexistence-patterns.md` |
| Testing parity during migration | `references/strategy/testing-strategy.md` |
| Expanded pitfall explanations | `references/pitfalls.md` |

Read only the references needed for the current conversion task.
