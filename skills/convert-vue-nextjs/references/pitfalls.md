# Vue → React/Next.js Conversion Pitfalls

> The most common mistakes developers make when converting Vue apps to React/Next.js, with wrong/right code examples and fixes.

---

## Mental Model Shifts

### Mutable → Immutable

Vue wraps data in Proxies that intercept mutations. React requires new references to trigger re-renders.

```js
// ❌ Vue habit — works in Vue, silent failure in React
const [user, setUser] = useState({ name: 'Bob', age: 25 });
user.name = 'Alice';       // Mutates but React won't re-render

// ✅ React way — create a new object
setUser(prev => ({ ...prev, name: 'Alice' }));
```

### Template → JSX

Vue templates compile to optimized render functions. JSX is JavaScript — no directives, only expressions.

```vue
<!-- Vue -->
<div v-if="show">Visible</div>
<li v-for="item in items" :key="item.id">{{ item.name }}</li>
<input v-model="name" />
```
```tsx
// React
{show && <div>Visible</div>}
{items.map(item => <li key={item.id}>{item.name}</li>)}
<input value={name} onChange={e => setName(e.target.value)} />
```

### Two-Way Binding → One-Way Data Flow

```vue
<!-- Vue: automatic two-way binding -->
<ChildInput v-model="username" />
```
```tsx
// React: explicit value + onChange
<ChildInput value={username} onChange={setUsername} />
```

### Auto Dependency Tracking → Manual Dependency Arrays

```js
// Vue: auto-tracked
const fullName = computed(() => `${firstName.value} ${lastName.value}`)
// React: must list deps manually
const fullName = useMemo(() => `${firstName} ${lastName}`, [firstName, lastName])
```

---

## Top 10 Conversion Mistakes

### 1. Mutating State Directly

```tsx
// ❌ WRONG
const [items, setItems] = useState(['a', 'b']);
items.push('c'); // no re-render

// ✅ RIGHT
setItems(prev => [...prev, 'c']);               // Append
setItems(prev => prev.filter(i => i !== 'b'));  // Remove
```

### 2. Missing useEffect Dependency Arrays

```tsx
// ❌ WRONG — runs every render, may infinite-loop
useEffect(() => { fetchData(userId); });

// ❌ WRONG — stale closure, always uses initial userId
useEffect(() => { fetchData(userId); }, []);

// ✅ RIGHT
useEffect(() => { fetchData(userId); }, [userId]);
```

### 3. Stale Closures in Event Handlers

```tsx
// ❌ WRONG — count captured as 0 forever
const [count, setCount] = useState(0);
useEffect(() => {
  const id = setInterval(() => setCount(count + 1), 1000);
  return () => clearInterval(id);
}, []);

// ✅ RIGHT — functional update uses latest value
useEffect(() => {
  const id = setInterval(() => setCount(c => c + 1), 1000);
  return () => clearInterval(id);
}, []);
```

### 4. Using useRef Like Vue ref()

Vue's `ref()` triggers re-renders. React's `useRef()` does NOT.

```tsx
// ❌ WRONG — UI never updates
const count = useRef(0);
count.current += 1;
return <p>{count.current}</p>;

// ✅ RIGHT — useState for UI-affecting values
const [count, setCount] = useState(0);
return <p>{count}</p>;
```

**Rule:** `useRef` = mutable, non-reactive (DOM refs, timers). `useState` = triggers re-render.

### 5. Over-Using useEffect for Derived State

```tsx
// ❌ WRONG — causes double render
const [items, setItems] = useState([]);
const [filtered, setFiltered] = useState([]);
useEffect(() => { setFiltered(items.filter(i => i.active)); }, [items]);

// ✅ RIGHT — compute during render
const filtered = useMemo(() => items.filter(i => i.active), [items]);
// For trivial derivations, skip useMemo entirely:
const fullName = `${firstName} ${lastName}`;
```

### 6. Creating Infinite Loops with useEffect + setState

```tsx
// ❌ WRONG — setState during render → infinite loop
function Component({ items }) {
  const [filtered, setFiltered] = useState([]);
  setFiltered(items.filter(i => i.active)); // triggers re-render → loop
}

// ✅ RIGHT — derive without state
function Component({ items }) {
  const filtered = useMemo(() => items.filter(i => i.active), [items]);
}
```

### 7. Forgetting Controlled Component Pattern for Forms

```tsx
// ❌ WRONG — uncontrolled, can't track value
let name = '';
<input onChange={e => { name = e.target.value; }} />

// ✅ RIGHT — controlled component
const [name, setName] = useState('');
<input value={name} onChange={e => setName(e.target.value)} />
```

### 8. Wrong Slot → Children Conversion

Scoped slots pass data back to the parent — plain `children` can't do this.

```tsx
// ❌ WRONG — children can't receive data from parent component
<DataList items={users}><span>{/* no item access */}</span></DataList>

// ✅ RIGHT — render prop pattern (scoped slot equivalent)
<DataList items={users} renderItem={(item, i) => <span>{i}: {item.name}</span>} />
```

**Mapping:** Default slot → `children`. Named slot → named prop. Scoped slot → render prop.

### 9. Missing Keys in .map() Iterations

```tsx
// ❌ WRONG — index as key breaks on reorder
{items.map((item, i) => <li key={i}>{item.name}</li>)}

// ✅ RIGHT — stable unique key
{items.map(item => <li key={item.id}>{item.name}</li>)}
```

### 10. Object/Array Reference Equality in Dependencies

```tsx
// ❌ WRONG — new object every render → effect runs infinitely
const options = { userId, limit: 10 };
useEffect(() => { fetchData(options); }, [options]);

// ✅ RIGHT — use primitive values in deps
useEffect(() => { fetchData({ userId, limit: 10 }); }, [userId]);
```

---

## Next.js-Specific Gotchas

### Server vs Client Component Boundary

```tsx
// ❌ WRONG — useState in Server Component (no 'use client')
export default function Counter() {
  const [count, setCount] = useState(0); // 💥 Error!
}

// ✅ RIGHT
'use client';
export default function Counter() {
  const [count, setCount] = useState(0); // Works
}
```

### Putting 'use client' Too High

```tsx
// ❌ WRONG — entire page becomes client-rendered
'use client';
export default function ProductPage() { /* loses SSR benefits */ }

// ✅ RIGHT — only interactive leaf is client
// app/products/page.tsx (Server Component)
export default async function ProductPage() {
  const products = await getProducts();
  return <ProductList products={products} />;
}
// components/ProductList.tsx
'use client';
export function ProductList({ products }: Props) { /* interactive */ }
```

### Hydration Pitfalls

Common causes — anything producing different output on server vs client:

```tsx
// ❌ Reading window/localStorage during render
const width = window.innerWidth;                    // 💥 SSR crash
const theme = localStorage.getItem('theme');        // 💥 SSR crash

// ❌ Random IDs that differ server ↔ client
const id = `input-${Math.random()}`;                // Hydration mismatch

// ❌ Date formatting that differs between environments
const label = new Date().toLocaleString();          // Server/client locale may differ
// ❌ Conditional markup based on browser state before hydration
const isMobile = window.innerWidth < 768;
return isMobile ? <MobileNav /> : <DesktopNav />;  // Mismatch on first render
```
Fixes:

```tsx
// ✅ Initialize browser-derived state in an Effect
const [width, setWidth] = useState(0);
useEffect(() => setWidth(window.innerWidth), []);

// ✅ Render a consistent placeholder until hydrated
const [mounted, setMounted] = useState(false);
useEffect(() => setMounted(true), []);
if (!mounted) return <NavPlaceholder />;            // Same markup server & client
return width < 768 ? <MobileNav /> : <DesktopNav />;

// ✅ Stable IDs with React.useId()
const id = useId();                                 // Consistent across server & client
```

### Browser-Only Libraries in Server Components

Most common migration failure: using browser-only libs (charts, maps, rich-text editors) in Server Components.
Fix: create thin `'use client'` adapter components — the wrapper imports the browser lib and exports a clean component.
Parent pages stay Server Components for performance; only the wrapper crosses the client boundary.

### Third-Party Library Wrapping Pattern

```tsx
// components/ChartWrapper.tsx
'use client';
import dynamic from 'next/dynamic';
const Chart = dynamic(() => import('heavy-chart-lib'), { ssr: false });
export function ChartWrapper(props) { return <Chart {...props} />; }
```

Use `dynamic` with `ssr: false` for libs that access `window`/`document` at import time.
The wrapper is the `'use client'` boundary — parent pages remain Server Components.

### Hydration Mismatch from URL Rewrites

When using Next.js rewrites to proxy Vue routes, client-side pathname can differ from server-side.
`usePathname` returns unexpected values when rewrites mask the destination URL — causes subtle hydration errors.
Fix: isolate pathname-dependent UI into dedicated client components.
Test by comparing SSR output vs client hydration for rewritten routes.

### Making Everything a Server Component Too Early

Start with `'use client'` parity — get it working, verify, then selectively remove `'use client'` where no interactivity is needed. Attempting Server Components first means fighting serialization boundaries.

### Keeping Server Data in Client Global State

> In Next, data that came from API calls often belongs in server fetching, not client-side stores. Don't automatically port Pinia stores that cache API responses into Zustand/Redux.

```tsx
// ❌ Vue habit — Pinia store ported to Zustand, fetching on client
const useProductStore = create((set) => ({
  products: [],
  fetch: async () => { set({ products: await fetchProducts() }); },
}));
// ✅ Next.js — fetch on server, no store needed
export default async function ProductsPage() {
  const products = await getProducts();
  return <ProductGrid products={products} />;
}
```

---

## Migration Strategy Pitfalls

### Rewriting Styles + Components Simultaneously

> Do not combine a framework migration with a design-system rewrite unless you absolutely must. That multiplies the risk.

When a visual regression appears, you can't tell whether it came from the framework switch or the design rewrite. Migrate first, then redesign.

### Translating Every watch() into useEffect()

Overlaps with pitfalls #5 and #6. Pure derivation belongs in render, not Effects.

```tsx
// ❌ Vue watch habit — effect that just derives state
useEffect(() => { setCount(items.length); }, [items]);
// ✅ Derive directly
const count = items.length;
```

Reserve `useEffect` for **side effects** (API calls, subscriptions, DOM manipulation) — not derivation.

### Replacing Every v-model with Local Child State

> That often breaks coordination. Prefer controlled components.

```tsx
// ❌ WRONG — child owns state, parent can't coordinate
function Dropdown() {
  const [open, setOpen] = useState(false); // Parent has no visibility
}

// ✅ RIGHT — controlled: parent owns state
function Dropdown({ open, onOpenChange }: Props) {
  return <>
    <button onClick={() => onOpenChange(!open)}>Toggle</button>
    {open && <ul>...</ul>}
  </>;
}
// Pattern: value/onValueChange, open/onOpenChange, selected/onSelectedChange
```

---

## Performance Pitfalls

- **Unnecessary re-renders:** Use `React.memo()` for expensive children; Vue does surgical updates, React re-renders subtrees
- **Giant useEffect:** Split by concern — one effect per responsibility, not one effect with 5 deps
- **No code-splitting:** Use `next/dynamic` or `React.lazy` — Vue's `defineAsyncComponent` has no auto equivalent

---

## Quick Reference Cheat Sheet

| Vue Concept | React Equivalent | Gotcha |
|---|---|---|
| `ref(0)` | `useState(0)` | Never mutate; always use setter |
| `reactive({})` | `useState({})` | Must spread to create new reference |
| `computed(() => ...)` | `useMemo(() => ..., [deps])` | Must specify deps manually |
| `watch(source, cb)` | `useEffect(cb, [source])` | Needs cleanup; beware stale closures |
| `watchEffect(cb)` | `useEffect(cb)` | Rarely correct — usually needs deps |
| `onMounted(cb)` | `useEffect(cb, [])` | Runs after paint, not before |
| `onUnmounted(cb)` | Return cleanup from `useEffect` | `useEffect(() => () => cleanup, [])` |
| `nextTick()` | `flushSync()` or `useEffect` | Different timing semantics |
| `$emit('event', data)` | `props.onEvent(data)` | No event system; explicit callbacks |
| `v-model="x"` | `value={x} onChange={setX}` | Always controlled components |
| `v-if` / `v-else` | `{cond && <X/>}` or ternary | Falsy values (0, '') can render |
| `v-show="visible"` | `style={{display: visible ? '' : 'none'}}` | Or className toggle |
| `v-for` | `{list.map(i => <X key={i.id}/>)}` | Always provide stable key |
| `<slot />` | `{children}` | Implicit prop |
| `<slot name="x" />` | Named prop: `{header}` | Pass JSX as prop value |
| `<slot :data="d" />` | Render prop: `{renderItem(d)}` | Function-as-prop pattern |
| `provide / inject` | `createContext / useContext` | Context re-renders all consumers |
| `<Teleport to="#x">` | `createPortal(el, target)` | Import from `react-dom` |
| `<Transition>` | Framer Motion | No built-in equivalent |
| `defineProps<T>()` | `function Comp(props: T)` | Props are function arguments |
| `defineEmits<T>()` | Callback props in interface | No emit type system |
| `class="x"` | `className="x"` | Reserved word in JS |
| `@click.prevent` | `e.preventDefault()` in handler | No event modifiers |
| Scoped CSS | CSS Modules or Tailwind | No built-in scoped styles |
| `app.use(plugin)` | `<Provider>` component tree | Different plugin model |
