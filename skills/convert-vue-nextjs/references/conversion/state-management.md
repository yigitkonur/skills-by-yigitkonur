# State Management Conversion: Vue → React

Patterns for converting Vue's reactivity system and state management to React equivalents.

---

## Reactivity Model Differences

Vue uses **Proxy-based automatic tracking** — mutations are direct and dependencies auto-detected. React uses **explicit setState with immutable updates**.

```ts
// Vue — mutable, auto-tracked
const count = ref(0)
count.value++                            // ✅ Vue detects this
const state = reactive({ items: [] })
state.items.push('new')                  // ✅ Vue detects nested mutations

// React — immutable, explicit
const [count, setCount] = useState(0);
setCount(c => c + 1);                    // ✅ New value via setter
setState(s => ({ ...s, items: [...s.items, 'new'] })); // ✅ Spread for update
// state.items.push('new')  ❌ NEVER mutate directly
```

---

## Primitives Mapping

### ref() → useState()

```ts
// Vue: const count = ref(0); count.value++
// React:
const [count, setCount] = useState(0); // [value, setter] — no .value
```

### reactive() → useState() with objects

```ts
// Vue: const form = reactive({ name: '' }); form.name = 'John'
// React:
const [form, setForm] = useState({ name: '' });
setForm(prev => ({ ...prev, name: 'John' })); // must spread
```

For deeply nested state, consider `useImmer` (from `use-immer`) which allows Vue-like mutations.

### computed() → Render Derivation (not always useMemo)

In React, the first question should be: **is this really state, or just a value derived from props/state during render?**

**Simple derivation — just compute inline:**
```tsx
// Vue: const fullName = computed(() => `${first.value} ${last.value}`)
// React — NO useMemo needed:
const fullName = `${firstName} ${lastName}`;
const activeItems = items.filter(i => i.active);
const sortedList = [...items].sort((a, b) => a.name.localeCompare(b.name));
```

**Only use useMemo when:**
- Calculation is genuinely expensive (large lists, complex transforms)
- Referential stability matters for child props (objects/arrays passed to `React.memo` children)

```ts
// Vue: const total = computed(() => price.value * (1 + tax.value)) — auto-tracks deps
// React — expensive or referentially sensitive:
const total = useMemo(() => price * (1 + tax), [price, tax]); // explicit deps
```

> Many derived values should simply be computed during render and only memoized when expensive. Over-memoizing is a common migration mistake.

⚠️ Missing deps in `useMemo` = stale values. Vue auto-tracks; React requires explicit arrays.

### watch() → useEffect()

```ts
// Vue: watch(userId, (newId, oldId) => { ... })
// React:
const prevUserId = useRef(userId);
useEffect(() => {
  console.log(`Changed from ${prevUserId.current} to ${userId}`);
  prevUserId.current = userId;
  fetchUser(userId).then(setUserData);
}, [userId]);
```

No `oldValue` in React — use `useRef` to track previous values.

### watchEffect() → useEffect()

```ts
// Vue: watchEffect(() => { document.title = query.value }) — auto-tracks
// React:
useEffect(() => { document.title = query; }, [query]); // must list deps
```

### Watch Options

| Vue Option | React Equivalent |
|---|---|
| `immediate: true` | `useEffect` already runs on mount |
| `deep: true` | No equivalent; restructure or `JSON.stringify` |
| `flush: 'post'` | `useEffect` (default) |
| `flush: 'sync'` | `useLayoutEffect` |

### watch → useEffect: Good vs Bad Migrations

Not every Vue `watch` should become a `useEffect`. Many watches compute derived values — those belong in render, not effects.

**✅ Good watch → useEffect** (true side effects):
- Syncing to localStorage / sessionStorage
- Managing subscriptions (WebSocket, EventSource)
- Timers (`setTimeout`, `setInterval`)
- DOM event listeners (`resize`, `scroll`)
- Imperative library integration (chart libs, maps)
- Analytics / telemetry tracking
- Network request cancellation / cleanup

**❌ Bad watch → useEffect** (should stay in render):
- Recomputing display values (→ inline derivation or `useMemo`)
- Copying props into state (→ derive from props directly)
- Sorting / filtering data purely for render (→ compute inline)
- Resetting state when props change (→ use `key` prop to remount)

```ts
// ❌ BAD — copying prop to state via effect
const [filtered, setFiltered] = useState(items);
useEffect(() => { setFiltered(items.filter(i => i.active)); }, [items]);

// ✅ GOOD — derive during render
const filtered = items.filter(i => i.active);
```

---

## Composables → Custom Hooks

Nearly identical structure (`useX()` functions), different internals.

### useAuth — Before/After

**Vue composable:**
```ts
const user = ref<User | null>(null) // module-level singleton
const token = ref('')

export function useAuth() {
  const isLoggedIn = computed(() => !!user.value)
  async function login(creds: Credentials) {
    const res = await api.login(creds)
    user.value = res.user; token.value = res.token
  }
  function logout() { user.value = null; token.value = '' }
  return { user, isLoggedIn, login, logout }
}
```

**React hook (Zustand for shared state):**
```ts
import { create } from 'zustand';

const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: '',
  login: async (creds) => {
    const res = await api.login(creds);
    set({ user: res.user, token: res.token });
  },
  logout: () => set({ user: null, token: '' }),
}));

export function useAuth() {
  const { user, login, logout } = useAuthStore();
  return { user, isLoggedIn: !!user, login, logout };
}
```

| Aspect | Vue Composable | React Hook |
|---|---|---|
| Execution | `setup()` runs once | Function runs every render |
| Shared state | Module-level `ref()` | Zustand/Context needed |
| Return values | Reactive refs | Plain values + setters |

---

## Store Conversion

### Pinia Store Migration: 3-Category Decision Framework

Before converting any Pinia store, categorize it first. This distinction is a major source of over-engineering during migrations.

| Category | Examples | React Target |
|---|---|---|
| **1. Local UI state** disguised as global | Modal open/closed, current tab, panel collapsed, transient route filters | Local `useState`, `useReducer`, or route-scoped Context |
| **2. Shared client state** | Auth session, theme preference, cart, multi-step form progress | Context (small), `useReducer` + Context (structured), Zustand (large/complex) |
| **3. Server state** cached in client | Fetched lists, dashboard metrics, API records, paginated data | Server Component data fetching (preferred), TanStack Query (client cache + background refresh) |

**Migration workflow:**
1. Audit each Pinia store → assign a category
2. Category 1 stores often disappear entirely — extract to the component that owns the UI
3. Category 3 stores should not be Zustand/Redux — use proper data-fetching patterns
4. Only Category 2 stores map directly to Zustand/Context

### Pinia → Zustand (Recommended)

Closest API match — both use closure-based stores with state + actions.

**Pinia:**
```ts
export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const total = computed(() => items.value.reduce((s, i) => s + i.price * i.qty, 0))
  function addItem(p: Product) {
    const existing = items.value.find(i => i.id === p.id)
    if (existing) existing.qty++
    else items.value.push({ ...p, qty: 1 })
  }
  function removeItem(id: string) { items.value = items.value.filter(i => i.id !== id) }
  return { items, total, addItem, removeItem }
})
```

**Zustand:**
```ts
import { create } from 'zustand';

export const useCartStore = create<CartState>((set) => ({
  items: [],
  addItem: (p) => set(s => {
    const existing = s.items.find(i => i.id === p.id);
    if (existing) return { items: s.items.map(i => i.id === p.id ? { ...i, qty: i.qty + 1 } : i) };
    return { items: [...s.items, { ...p, qty: 1 }] };
  }),
  removeItem: (id) => set(s => ({ items: s.items.filter(i => i.id !== id) })),
}));

export const useCartTotal = () => useCartStore(s => s.items.reduce((sum, i) => sum + i.price * i.qty, 0));
```

**Concept mapping:**

| Pinia | Zustand |
|---|---|
| `defineStore('id', () => {...})` | `create((set, get) => ({...}))` |
| `ref()` for state | Plain properties |
| `computed()` for getters | Selector functions |
| Actions (functions) | Functions calling `set()` |
| `$patch({ ... })` | `set({ ... })` |
| `$reset()` | `set(initialState)` |
| `$subscribe(cb)` | `useStore.subscribe(cb)` |
| `storeToRefs(store)` | `useStore(s => s.prop)` per-property |

### Vuex → Zustand or Redux Toolkit

**Vuex module → Zustand (simpler):**
```ts
// Vuex: state + mutations + actions + getters → single Zustand store
export const useCounterStore = create<CounterState>((set) => ({
  count: 0,
  increment: () => set(s => ({ count: s.count + 1 })),
  fetchCount: async () => { const data = await api.getCount(); set({ count: data }); },
}));
export const useDoubleCount = () => useCounterStore(s => s.count * 2);
```

Use **Redux Toolkit** instead when: 10+ stores, need time-travel debugging, or team prefers Redux patterns. Vuex `mutations` → RTK `reducers` (both use Immer), `actions` → `createAsyncThunk`, `getters` → `createSelector`, `modules` → slices.

---

## provide/inject → React Context

**Vue:**
```ts
provide('theme', ref<'light' | 'dark'>('dark'))
// descendant: const theme = inject('theme')
```

**React:**
```tsx
const ThemeCtx = createContext<{ theme: 'light' | 'dark'; setTheme: (t: 'light' | 'dark') => void } | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  return <ThemeCtx.Provider value={{ theme, setTheme }}>{children}</ThemeCtx.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeCtx);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
```

| Vue | React |
|---|---|
| `provide(key, value)` | `<Context.Provider value={...}>` |
| `inject(key)` | `useContext(Context)` |
| No wrapper needed | Requires `<Provider>` wrapper |

---

## Decision Tree

```
What Vue state pattern?
├─ Local ref/reactive → useState()
├─ Computed/derived → useMemo() or inline
├─ Shared across components?
│  ├─ Parent-child → props + callbacks
│  ├─ Deep tree → React Context
│  └─ Global → Zustand store
├─ Pinia store → Zustand (closest match)
├─ Vuex store?
│  ├─ Simple (1-5 modules) → Zustand
│  └─ Complex (5+, devtools needed) → Redux Toolkit
└─ provide/inject → React Context
```