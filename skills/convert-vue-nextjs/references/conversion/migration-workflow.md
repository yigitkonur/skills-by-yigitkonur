# Vue 3 → Next.js Migration Workflow

Step-by-step operational guide for migrating a Vue 3 application to Next.js, one route and one component at a time.

---

## 1. The Contract Preservation Principle

> Do not rewrite the app in React. Migrate one route and one component boundary at a time, preserving each component's public behavior.

Every Vue component has a **public contract**. Preserve it exactly:

| Contract surface | What to preserve |
|---|---|
| **Props** | Names, types, defaults, required vs optional |
| **Events** | Every `$emit` call → callback prop |
| **Slots / extensibility** | Default → `children`, named → explicit props, scoped → render props |
| **DOM structure & classes** | CSS depends on this — change it and styling breaks |
| **Router / store / data deps** | `useRoute`, Pinia stores, inject/provide |
| **Imperative behavior** | Focus, scroll, keyboard shortcuts, `defineExpose` refs |

If the React version honors the same contract, tests, CSS, and parent components keep working.

---

## 2. The 6-Phase Migration Order

Migrate **within each route**, from lowest risk to highest:

1. **Presentational leaf components** — `Button`, `Card`, `Avatar`, `Badge`. No state, pure props → markup.
2. **Input and form field components** — `TextField`, `Select`, `DatePicker`. `v-model` → `value` + `onChange`.
3. **Overlays and behavior-heavy UI** — Modals, popovers, tooltips. Touch `Teleport`, transitions, focus traps.
4. **Container components** — Compose children, manage state, connect to stores/routes.
5. **Route components and layouts** — Vue Router → App Router `page.tsx` / `layout.tsx`.
6. **Global state and data fetching** — Pinia → Zustand/Context, route guards → middleware.

---

## 3. Per-Component Migration Worksheet

Before migrating **any** component, document every contract surface:

| Category | What to capture |
|---|---|
| Props & defaults | `prop: type = defaultValue` |
| Emitted events | `emit('eventName', payload)` |
| v-model bindings | `modelValue` / `update:modelValue`, custom `v-model:propName` |
| Slots | default, named (`header`, `footer`), scoped (`item({ row, index })`) |
| Fallthrough attrs | `$attrs` — passed to root or inner element? |
| Refs / exposed methods | `defineExpose`: `focus()`, `open()`, `close()`, `reset()` |
| Local state | `ref(initial)`, `reactive({ ... })` |
| Computed values | `computed(() => ...)` |
| Watchers | `watch(source, handler, options)` |
| Router usage | `useRoute()`: params, query; `useRouter()`: push, replace |
| Store usage | `useXxxStore()`: state, getters, actions |
| Directives | `v-focus`, `v-click-outside`, `v-tooltip` |
| Teleport / Transition | `Teleport to="body"`, `Transition name="fade"` |
| CSS dependencies | Class names, scoped styles, CSS modules |
| Accessibility | `aria-*`, `role`, `tabindex`, test IDs |

> That worksheet is more valuable than blindly translating lines of code.

---

## 4. The 10-Step Per-Component Workflow

### Step 1: Port markup literally

`v-if` → conditional (`&&`, ternary), `v-for` → `.map()`, `:class` → `className`, `v-show` → `style={{ display }}`, `@click` → `onClick`.

```vue
<!-- Vue -->
<li v-for="item in items" :key="item.id"
    :class="{ active: item.id === activeId, disabled: item.disabled }">
  {{ item.label }}
</li>
```
```tsx
// React
{items.map((item) => (
  <li key={item.id}
      className={[
        item.id === activeId ? 'active' : '',
        item.disabled ? 'disabled' : '',
      ].filter(Boolean).join(' ')}>
    {item.label}
  </li>
))}
```

### Step 2: Port props — keep same names, match types and defaults

```vue
const props = withDefaults(defineProps<{
  variant?: 'primary' | 'secondary'
  disabled?: boolean
}>(), { variant: 'primary', disabled: false })
```
```tsx
function Button({ variant = 'primary', disabled = false }: ButtonProps) {
```

### Step 3: Translate emits → callback props

Every `$emit('name', payload)` becomes an optional callback:

```vue
const emit = defineEmits<{ save: [data: FormData]; cancel: [] }>()
emit('save', formData)
```
```tsx
interface Props { onSave?: (data: FormData) => void; onCancel?: () => void }
onSave?.(formData)
```

### Step 4: Translate local state

`ref()` → `useState()`. For `reactive()` where fields change independently, use separate `useState` calls. Only group into one state object when values always change together.

### Step 5: Translate computed correctly

First ask: **"Is this just derived from props/state?"** If yes — compute inline during render, no hook:

```tsx
function UserList({ users, filter }: Props) {
  const filtered = users.filter((u) => u.role === filter)
  return <ul>{filtered.map(/* ... */)}</ul>
}
```

Only `useMemo` when genuinely expensive **and** you've measured a problem:

```tsx
const sorted = useMemo(() => hugeList.slice().sort(expensiveComparator), [hugeList])
```

### Step 6: Translate watch → useEffect ONLY for true side effects

**Good** (true side effects): localStorage sync, subscriptions, timers, DOM listeners, analytics, network cleanup.

**Bad** (not side effects — derive inline instead): recomputing display values, copying props into state, sorting/filtering for render, transforming data for display.

### Step 7: Translate slots

| Vue slot | React equivalent |
|---|---|
| `<slot />` | `children` prop |
| `<slot name="footer" />` | `footer?: ReactNode` prop |
| `<slot :item="item" />` | `renderItem?: (item: T) => ReactNode` |

### Step 8: Handle fallthrough attrs

```tsx
function Button({ variant = 'primary', className = '', ...rest }: ButtonProps) {
  return <button className={`btn btn-${variant} ${className}`} {...rest} />
}
```

### Step 9: Port refs and exposed methods

Convert `defineExpose` to `useImperativeHandle`. Only preserve small imperative APIs:

```tsx
const TextInput = forwardRef<InputHandle, InputProps>((props, ref) => {
  const inputRef = useRef<HTMLInputElement>(null)
  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current?.focus(),
    reset: () => { if (inputRef.current) inputRef.current.value = '' },
  }))
  return <input ref={inputRef} {...props} />
})
```

### Step 10: Port composables → custom hooks

Migrate **before** container components since containers depend on them:

```vue
<!-- Vue composable -->
export function useDebounce<T>(value: Ref<T>, delay: number): Ref<T> {
  const debounced = ref(value.value) as Ref<T>
  let timeout: ReturnType<typeof setTimeout>
  watch(value, (v) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => { debounced.value = v }, delay)
  })
  return debounced
}
```
```tsx
// React hook
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(id)
  }, [value, delay])
  return debounced
}
```

---

## 5. Full Example: Migrating a Modal Component

### Vue: BaseModal.vue

```vue
<script setup lang="ts">
import { watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps<{ open: boolean; title: string }>()
const emit = defineEmits<{ 'update:open': [value: boolean]; close: [] }>()

function handleClose() {
  emit('update:open', false)
  emit('close')
}
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') handleClose()
}
watch(() => props.open, (isOpen) => {
  document.body.style.overflow = isOpen ? 'hidden' : ''
})
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="modal-overlay" @click.self="handleClose">
      <div class="modal-content" role="dialog" aria-modal="true">
        <h2>{{ title }}</h2>
        <slot />
        <div v-if="$slots.footer" class="modal-footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>
```

### React: BaseModal.tsx

```tsx
'use client'
import { useEffect, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

interface BaseModalProps {
  open: boolean
  title: string
  onOpenChange?: (open: boolean) => void
  onClose?: () => void
  children: ReactNode
  footer?: ReactNode
}

export default function BaseModal({
  open, title, onOpenChange, onClose, children, footer,
}: BaseModalProps) {
  useEffect(() => {
    if (!open) return
    document.body.style.overflow = 'hidden'
    function onKeydown(e: KeyboardEvent) {
      if (e.key === 'Escape') { onOpenChange?.(false); onClose?.() }
    }
    document.addEventListener('keydown', onKeydown)
    return () => {
      document.body.style.overflow = ''
      document.removeEventListener('keydown', onKeydown)
    }
  }, [open, onOpenChange, onClose])

  if (!open) return null
  return createPortal(
    <div className="modal-overlay"
         onClick={(e) => { if (e.target === e.currentTarget) { onOpenChange?.(false); onClose?.() } }}>
      <div className="modal-content" role="dialog" aria-modal="true">
        <h2>{title}</h2>
        {children}
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>,
    document.body
  )
}
```

### Why each mapping is correct

| Vue concept | React equivalent | Reasoning |
|---|---|---|
| `open` prop | `open` prop | Read-only value, same role |
| `emit('update:open', false)` | `onOpenChange?.(false)` | v-model pattern → controlled callback |
| `emit('close')` | `onClose?.()` | Semantic event → callback prop |
| Default `<slot />` | `children` | Standard content projection |
| Named `<slot name="footer" />` | `footer?: ReactNode` prop | Named slot → explicit prop |
| `watch` + `onMounted` + `onBeforeUnmount` | Single `useEffect` with cleanup | Consolidate related side effects |
| `<Teleport to="body">` | `createPortal(jsx, document.body)` | Same DOM escape hatch |

---

## 6. Per-Component Verification Checklist

### Public API
- [ ] Prop names and defaults preserved?
- [ ] Every emitted event mapped to a callback prop with same semantics?
- [ ] Every `v-model` pair now an explicit controlled API?

### Composition & Extensibility
- [ ] Default slot → `children`? Named slots → explicit props? Scoped → render props?
- [ ] Fallthrough attributes still reach the intended element?

### State & Reactivity
- [ ] `ref()` / `reactive()` → sensible local state?
- [ ] `computed` stayed derived (not redundant state copies)?
- [ ] `watch` → `useEffect` only for true side effects?

### DOM Behavior
- [ ] Refs / focus / scroll / portal behavior survived?
- [ ] Transitions preserve timing and mount/unmount rules?
- [ ] Click-outside, keyboard shortcuts, and cleanup survived?

### Routing & Data
- [ ] Route params and search params map correctly?
- [ ] Navigation calls behave the same?
- [ ] Data fetching moved to the right layer (server vs client)?

### UI Parity
- [ ] Class names and DOM structure compatible with existing CSS?
- [ ] Loading, empty, and error states identical?
- [ ] ARIA attributes and keyboard behavior preserved?

---

## 7. The Client-Heavy-First Pattern

When migrating a route, start with **everything in a client component** — this mirrors Vue (client-side by default) and guarantees behavioral parity.

**Step 1 — Thin server entry:**
```tsx
// app/dashboard/page.tsx — Server Component
import DashboardPageClient from './DashboardPageClient'
export default function Page() {
  return <DashboardPageClient />
}
```

**Step 2 — All logic in client component:**
```tsx
// app/dashboard/DashboardPageClient.tsx
'use client'
import { useState, useEffect } from 'react'

export default function DashboardPageClient() {
  const [data, setData] = useState(null)
  useEffect(() => {
    fetch('/api/dashboard').then((r) => r.json()).then(setData)
  }, [])
  if (!data) return <div>Loading...</div>
  return <div>{/* full dashboard UI */}</div>
}
```

**Step 3 — After parity, progressively extract:** static markup → Server Component, data fetching → async server page, non-interactive UI → Server Component children.

```tsx
// app/dashboard/page.tsx — After optimization
import { getDashboardData } from '@/lib/data'
import DashboardCharts from './DashboardCharts' // 'use client'

export default async function Page() {
  const data = await getDashboardData()
  return (
    <main>
      <h1>Dashboard</h1>              {/* Server-rendered */}
      <DashboardCharts data={data} />  {/* Client interactive */}
    </main>
  )
}
```

> Get it working first, then get it optimized. Never both at once.
