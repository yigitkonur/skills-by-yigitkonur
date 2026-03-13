# Component Mapping: Vue SFC → React/Next.js

Complete reference for converting Vue 3 Single File Components to React/Next.js components.

---

## Full Mapping Table

| Vue Pattern | React/Next.js Equivalent | Notes |
|---|---|---|
| `<template>` block | JSX `return (...)` | `class`→`className`, `for`→`htmlFor` |
| `<script setup>` | Function component body | Top-level code becomes code before `return` |
| `<style scoped>` | CSS Modules (`.module.css`) | `className={styles.x}` |
| `{{ interpolation }}` | `{expression}` | Double-curly → single-curly |
| `v-if` / `v-else-if` / `v-else` | `&&`, ternary, early return | See examples below |
| `v-show` | `style={{ display: x ? undefined : 'none' }}` | Element stays in DOM |
| `v-for` | `.map()` with `key` | `:key` → `key={}` |
| `v-model` (input) | `value` + `onChange` | Must wire both explicitly |
| `v-model` (component) | `value` + `onChange` props | Parent owns state |
| `v-bind:prop` / `:prop` | `prop={value}` | Direct mapping |
| `v-on:event` / `@event` | `onEvent={handler}` | `@click` → `onClick` |
| `v-bind:class` | `clsx()` or template literal | `clsx({ [styles.active]: isActive })` |
| `v-bind:style` | `style={{ prop: value }}` | camelCase CSS properties |
| Default `<slot>` | `{children}` | `PropsWithChildren<>` in TS |
| Named `<slot name="x">` | Named JSX props: `header={<X/>}` | Pass JSX as props |
| Scoped slots | Render props `renderItem={(d) => <X/>}` | Function-as-prop |
| `$emit('event', data)` | `onEvent(data)` callback prop | Parent passes function |
| `defineEmits` | TS interface with callbacks | `onSubmit: (d: T) => void` |
| `defineProps` | Destructured params + interface | `function Comp({ x }: Props)` |
| Template `ref="el"` | `useRef(null)` + `ref={el}` | `.current` not `.value` |
| `<component :is="x">` | `const Comp = map[x]; <Comp />` | Dynamic component |
| `<Teleport to="body">` | `createPortal(children, document.body)` | From `react-dom` |
| `<Transition>` | Framer Motion `<AnimatePresence>` | No built-in equivalent |
| `v-html="html"` | `dangerouslySetInnerHTML={{ __html: html }}` | Security warning |
| `v-text="msg"` | `{msg}` | Direct expression |
| `v-bind="obj"` | `{...obj}` | Spread operator |

---

## Template → JSX

### v-if / v-else / v-show

**Vue:**
```vue
<div v-if="type === 'A'">A</div>
<div v-else-if="type === 'B'">B</div>
<div v-else>C</div>
<span v-show="isVisible">Always in DOM</span>
```

**React:**
```tsx
// Simple: logical AND
{isLoggedIn && <UserGreeting />}

// Binary: ternary
{isLoggedIn ? <UserGreeting /> : <LoginPrompt />}

// Multi-branch: early return
function StatusMessage({ type }: { type: string }) {
  if (type === 'A') return <div>A</div>;
  if (type === 'B') return <div>B</div>;
  return <div>C</div>;
}

// v-show: toggle CSS display
<span style={{ display: isVisible ? undefined : 'none' }}>Always in DOM</span>
```

### v-for

**Vue:**
```vue
<li v-for="(item, index) in items" :key="item.id">{{ index }}: {{ item.name }}</li>
```

**React:**
```tsx
{items.map((item, index) => (
  <li key={item.id}>{index}: {item.name}</li>
))}
```

Use `.filter().map()` when Vue combines `v-for` with `v-if`.

### v-bind:class / v-bind:style

**Vue:**
```vue
<div :class="{ active: isActive, disabled: isDisabled }">Content</div>
<div :style="{ color: textColor, fontSize: size + 'px' }">Styled</div>
```

**React:**
```tsx
import clsx from 'clsx';
<div className={clsx('base', { active: isActive, disabled: isDisabled })}>Content</div>
<div style={{ color: textColor, fontSize: `${size}px` }}>Styled</div>
```

**Without a library** — use `filter(Boolean).join(' ')`:
```tsx
className={[
  'base',
  isActive ? 'active' : '',
  isDisabled ? 'disabled' : '',
].filter(Boolean).join(' ')}
```

> **Tip:** `clsx` or `cn` (tailwind-merge) is idiomatic in most React/Next.js codebases and should be preferred over manual joining.

### v-on / @event + Modifiers

| Vue Modifier | React Equivalent |
|---|---|
| `@click.prevent` | `onClick={e => { e.preventDefault(); handler(); }}` |
| `@click.stop` | `onClick={e => { e.stopPropagation(); handler(); }}` |
| `@keyup.enter` | `onKeyUp={e => e.key === 'Enter' && handler()}` |
| `@click.once` | `useEffect` + `addEventListener(..., { once: true })` |

Vue modifiers like `@click.stop.prevent` have no JSX shorthand — must be explicit:
```tsx
function handleClick(e: React.MouseEvent) {
  e.stopPropagation();
  e.preventDefault();
  // ... actual logic
}
<button onClick={handleClick}>Save</button>
```

---

## v-model → Controlled Components

**Vue:**
```vue
<script setup>
const name = ref('')
const agreed = ref(false)
const color = ref('red')
</script>
<template>
  <input v-model="name" />
  <input type="checkbox" v-model="agreed" />
  <select v-model="color"><option value="red">Red</option></select>
</template>
```

**React:**
```tsx
'use client';
const [name, setName] = useState('');
const [agreed, setAgreed] = useState(false);
const [color, setColor] = useState('red');

<input value={name} onChange={e => setName(e.target.value)} />
<input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} />
<select value={color} onChange={e => setColor(e.target.value)}>
  <option value="red">Red</option>
</select>
```

**Modifiers:** `.lazy` → `onBlur` | `.number` → `Number(e.target.value)` | `.trim` → `e.target.value.trim()`

> **⚠️ Controlled vs Uncontrolled Warning:**
> React warns when switching between controlled/uncontrolled inputs. Common cause: `value={undefined}` on first render, then setting state — React interprets this as a mode switch.
> **Fix:** Always initialize with a concrete value: `useState('')` not `useState()`. For checkboxes: `useState(false)`.
> Vue doesn't have this concept — `v-model` is always "controlled." Every migrated input must have an explicit initial value.

### Custom Component v-model

**Vue:** `<CustomInput v-model="query" />` uses `defineModel()` internally.

**React:** `<CustomInput value={query} onChange={setQuery} />` — parent owns state, child calls `onChange`.

**Multiple v-models:** `v-model:firstName` + `v-model:lastName` → `firstName` + `onFirstNameChange` + `lastName` + `onLastNameChange` props.

### Form Migration Heuristic

Choose your form strategy based on interactivity requirements:

- **Server-first forms** (simple submission, progressive enhancement): Use Next.js Server Actions (`"use server"` + `<form action={…}>`) with `revalidatePath()`. Works without JS.
- **Complex client forms** (multi-step wizards, real-time validation, dependent fields): Use React Hook Form + Zod/Yup schema validation. Requires `'use client'`.
- **Vue VeeValidate / FormKit** → Map to **React Hook Form** (closest mental model: declarative validation, field-level errors, form state).

> **One-liner:** If the form could work without JavaScript, use Server Actions. If it needs client-side orchestration, use React Hook Form.

---

## Slots → Children / Render Props

**Default slot → `children`:**
```tsx
function Card({ children }: { children?: React.ReactNode }) {
  return <div className="card">{children ?? 'Fallback'}</div>;
}
```

**Named slots → explicit props:**
```tsx
interface LayoutProps { header?: React.ReactNode; footer?: React.ReactNode; children: React.ReactNode }
function Layout({ header, footer, children }: LayoutProps) {
  return <><header>{header}</header><main>{children}</main><footer>{footer}</footer></>;
}
<Layout header={<h1>Title</h1>} footer={<p>Footer</p>}><p>Main</p></Layout>
```

**Scoped slots → render props:**
```tsx
interface DataListProps<T> { items: T[]; renderItem: (item: T, index: number) => React.ReactNode }
function DataList<T>({ items, renderItem }: DataListProps<T>) {
  return <ul>{items.map((item, i) => <li key={i}>{renderItem(item, i)}</li>)}</ul>;
}
<DataList items={users} renderItem={(item, i) => <span>{i}: {item.name}</span>} />
```

---

## Events: $emit → Callback Props

**Vue:** `emit('submit', formData)` / `emit('cancel')`

**React:**
```tsx
interface Props { onSubmit: (data: FormData) => void; onCancel: () => void }
function MyForm({ onSubmit, onCancel }: Props) {
  return <>
    <button onClick={() => onSubmit(formData)}>Submit</button>
    <button onClick={onCancel}>Cancel</button>
  </>;
}
```

Naming: Vue `@item-selected` → React `onItemSelected` (kebab → camelCase with `on` prefix).

---

## Styles: Scoped → CSS Modules

```css
/* Card.module.css */
.card { background: white; border-radius: 8px; }
.title { font-weight: bold; }
```
```tsx
import styles from './Card.module.css';
<div className={styles.card}><h2 className={styles.title}>Title</h2></div>
```

- Vue `:deep(.child)` → CSS Modules `:global(.child)` or pass `className` as prop
- SCSS supported via `.module.scss` (built-in Next.js support)

---

## Refs: Template Refs → useRef

| Aspect | Vue | React |
|---|---|---|
| Access | `.value` | `.current` |
| Reactivity | `ref()` is reactive | `useRef` is NOT reactive |
| Component ref | `defineExpose()` | `forwardRef` + `useImperativeHandle` |

```tsx
const inputRef = useRef<HTMLInputElement>(null);
useEffect(() => { inputRef.current?.focus(); }, []);
return <input ref={inputRef} />;
```

### defineExpose → useImperativeHandle

Vue's `defineExpose` selectively reveals methods to a parent's template ref. In React, use `forwardRef` + `useImperativeHandle` to expose only the imperative API the parent needs (e.g. `focus`, `scrollIntoView`, `reset`):

**Vue:**
```vue
<script setup>
const inputRef = ref<HTMLInputElement>()
defineExpose({ focus: () => inputRef.value?.focus() })
</script>
<template><input ref="inputRef" /></template>
```

**React:**
```tsx
import { forwardRef, useImperativeHandle, useRef } from 'react';

interface InputHandle { focus: () => void }

const Input = forwardRef<InputHandle, React.InputHTMLAttributes<HTMLInputElement>>(
  (props, ref) => {
    const inputRef = useRef<HTMLInputElement>(null);
    useImperativeHandle(ref, () => ({
      focus: () => inputRef.current?.focus(),
    }));
    return <input ref={inputRef} {...props} />;
  }
);
```

Parent usage: `const ref = useRef<InputHandle>(null)` → `ref.current?.focus()`.

---

## Fallthrough Attributes: $attrs → Rest Props

Vue automatically forwards unrecognized attrs to the root element. React requires explicit forwarding via rest/spread — critical for preserving `data-testid`, `aria-*`, and other passthrough attributes.

```tsx
type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary';
};

function Button({ variant = 'primary', className = '', ...rest }: Props) {
  return <button className={`btn btn-${variant} ${className}`} {...rest} />;
}
```

> **Why this matters:** Without `...rest`, attributes like `aria-label`, `data-testid`, and `disabled` are silently dropped — breaking accessibility and test selectors.

---

## Complete Example: SearchableDropdown

**Vue SFC:**
```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
const props = withDefaults(defineProps<{
  items: { id: string; label: string }[]
  placeholder?: string
}>(), { placeholder: 'Search...' })
const emit = defineEmits<{ select: [item: { id: string; label: string }] }>()

const query = ref('')
const isOpen = ref(false)
const filtered = computed(() =>
  props.items.filter(i => i.label.toLowerCase().includes(query.value.toLowerCase()))
)
function select(item: { id: string; label: string }) {
  query.value = item.label; isOpen.value = false; emit('select', item)
}
</script>
<template>
  <div class="dropdown">
    <input v-model="query" :placeholder="placeholder" @focus="isOpen = true" />
    <ul v-show="isOpen && filtered.length">
      <li v-for="item in filtered" :key="item.id" @click="select(item)">{{ item.label }}</li>
    </ul>
  </div>
</template>
<style scoped>
.dropdown { position: relative; }
.dropdown ul { position: absolute; width: 100%; list-style: none; padding: 0; }
.dropdown li { padding: 8px; cursor: pointer; }
.dropdown li:hover { background: #f0f0f0; }
</style>
```

**React/Next.js equivalent:**
```tsx
'use client';
import { useState, useMemo } from 'react';
import styles from './SearchableDropdown.module.css';

interface Item { id: string; label: string }
interface Props { items: Item[]; placeholder?: string; onSelect: (item: Item) => void }

export function SearchableDropdown({ items, placeholder = 'Search...', onSelect }: Props) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const filtered = useMemo(
    () => items.filter(i => i.label.toLowerCase().includes(query.toLowerCase())),
    [items, query]
  );

  function select(item: Item) { setQuery(item.label); setIsOpen(false); onSelect(item); }

  return (
    <div className={styles.dropdown}>
      <input value={query} onChange={e => setQuery(e.target.value)}
        placeholder={placeholder} onFocus={() => setIsOpen(true)} />
      {isOpen && filtered.length > 0 && (
        <ul>{filtered.map(item => (
          <li key={item.id} onClick={() => select(item)}>{item.label}</li>
        ))}</ul>
      )}
    </div>
  );
}
```
