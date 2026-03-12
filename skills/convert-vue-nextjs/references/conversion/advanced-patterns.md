# Advanced Patterns: Vue → React/Next.js

Advanced conversion patterns for TypeScript, animations, portals, directives, plugins, and error handling.

---

## TypeScript Migration

### defineProps → Interface Props

```vue
<!-- Vue -->
<script setup lang="ts">
const props = defineProps<{ title: string; count?: number; items: string[] }>()
</script>
```
```tsx
// React
interface Props { title: string; count?: number; items: string[] }
function MyComponent({ title, count, items }: Props) { ... }
```

### defineEmits → Callback Prop Types

```vue
<script setup lang="ts">
const emit = defineEmits<{ change: [id: number]; 'item-click': [item: Item, index: number] }>()
</script>
```
```tsx
interface Props { onChange: (id: number) => void; onItemClick: (item: Item, index: number) => void }
```

Rules: Event → `on` prefix + camelCase. Tuple `[arg: T]` → function `(arg: T) => void`.

### withDefaults → Destructuring Defaults

```vue
<script setup lang="ts">
const props = withDefaults(defineProps<{ msg?: string; labels?: string[] }>(), {
  msg: 'hello', labels: () => ['one', 'two'],
})
</script>
```
```tsx
const DEFAULT_LABELS = ['one', 'two']; // stable reference for deps
function MyComponent({ msg = 'hello', labels = DEFAULT_LABELS }: Props) { ... }
```

### Generic Components

```vue
<script setup lang="ts" generic="T extends { id: string }">
defineProps<{ items: T[]; selected?: T }>()
defineEmits<{ select: [item: T] }>()
</script>
```
```tsx
interface ListProps<T extends { id: string }> {
  items: T[]; selected?: T; onSelect: (item: T) => void;
}
function GenericList<T extends { id: string }>({ items, selected, onSelect }: ListProps<T>) {
  return <ul>{items.map(item => (
    <li key={item.id} onClick={() => onSelect(item)}
      className={selected?.id === item.id ? 'active' : ''}>
      {item.id}
    </li>
  ))}</ul>;
}
// Usage — T inferred: <GenericList items={users} onSelect={handleSelect} />
```

### Type Mapping Summary

| Concept | Vue | React |
|---|---|---|
| State | `Ref<T>` (`.value`) | `T` (direct) |
| Setter | `ref.value = x` | `Dispatch<SetStateAction<T>>` |
| Props | `defineProps<T>()` | `(props: T)` param |
| Events | `defineEmits<T>()` | `onX: (...) => void` props |
| Context | `InjectionKey<T>` | `Context<T>` |
| Template ref | `Ref<HTMLElement \| null>` | `RefObject<HTMLElement \| null>` |

---

## Composables → Custom Hooks (Advanced)

### Lifecycle Cleanup

```ts
// Vue
export function useEventListener(target: EventTarget, event: string, handler: EventListener) {
  onMounted(() => target.addEventListener(event, handler))
  onUnmounted(() => target.removeEventListener(event, handler))
}

// React
export function useEventListener(target: EventTarget, event: string, handler: EventListener) {
  useEffect(() => {
    target.addEventListener(event, handler);
    return () => target.removeEventListener(event, handler);
  }, [target, event, handler]);
}
```

### Shared State Composables → Zustand

Vue module-level `ref()` = singleton. React needs external store:

```ts
// Vue: const notifications = ref<Notification[]>([]) — module singleton
// React (Zustand):
export const useNotifications = create<NotificationStore>((set) => ({
  items: [],
  add: (msg) => set(s => ({ items: [...s.items, { id: Date.now(), msg }] })),
  dismiss: (id) => set(s => ({ items: s.items.filter(n => n.id !== id) })),
}));
```

### Async Composables → Hooks with Loading/Error

```ts
// React
export function useFetchData<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(url).then(r => r.json())
      .then(d => { if (!cancelled) setData(d); })
      .catch(e => { if (!cancelled) setError(e); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [url]);

  return { data, error, loading };
}
```

---

## Teleport → createPortal

**Vue:**
```vue
<Teleport to="#modal-root">
  <div class="modal" v-if="show">Content</div>
</Teleport>
```

**React:**
```tsx
import { createPortal } from 'react-dom';

function Modal({ isOpen, children }: { isOpen: boolean; children: React.ReactNode }) {
  if (!isOpen) return null;
  return createPortal(
    <div className="modal">{children}</div>,
    document.getElementById('modal-root')!
  );
}
```

For Vue's `disabled` prop (render in-place): conditionally return `<>{children}</>` or `createPortal(...)`.

Add portal targets in `app/layout.tsx`:
```tsx
<body>{children}<div id="modal-root" /><div id="tooltip-root" /></body>
```

---

## Transitions & Animation

### `<Transition>` → Framer Motion

**Vue:**
```vue
<Transition name="fade"><div v-if="show">Content</div></Transition>
<style>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
```

**React:**
```tsx
'use client';
import { AnimatePresence, motion } from 'framer-motion';

function FadeContent({ show }: { show: boolean }) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0 }}        // .fade-enter-from
          animate={{ opacity: 1 }}         // .fade-enter-to
          exit={{ opacity: 0 }}            // .fade-leave-to
          transition={{ duration: 0.3 }}
        >Content</motion.div>
      )}
    </AnimatePresence>
  );
}
```

### `<TransitionGroup>` → AnimatePresence + layout

```tsx
<AnimatePresence>
  <ul>{items.map(item => (
    <motion.li key={item.id} layout
      initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 30 }} transition={{ duration: 0.3 }}>
      {item.text}
    </motion.li>
  ))}</ul>
</AnimatePresence>
```

The `layout` prop enables reorder animations (Vue's `.list-move`).

**CSS-only alternative** (no exit animations): use conditional Tailwind classes like `transition-opacity duration-300 ${show ? 'opacity-100' : 'opacity-0'}`.

---

## KeepAlive

Vue's `<KeepAlive>` caches component state. **No React equivalent.** Workarounds:

1. **Zustand/Context** — persist state externally so it survives unmount
2. **CSS display toggle** — keep all tabs mounted, toggle `display: none`
3. **Lift state up** so it persists across tab switches

```tsx
function TabPanel({ active, children }: { active: boolean; children: React.ReactNode }) {
  return <div style={{ display: active ? 'block' : 'none' }}>{children}</div>;
}
```

---

## Custom Directives → Hooks / Ref Callbacks

### v-focus → useRef + useEffect

```tsx
function useAutoFocus() {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => { ref.current?.focus(); }, []);
  return ref;
}
// Usage: <input ref={useAutoFocus()} />
```

### v-click-outside → Custom Hook

```tsx
function useClickOutside(ref: RefObject<HTMLElement | null>, handler: () => void) {
  useEffect(() => {
    function listener(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) handler();
    }
    document.addEventListener('click', listener);
    return () => document.removeEventListener('click', listener);
  }, [ref, handler]);
}
```

### v-intersection → Observer Hook

```tsx
function useIntersection(ref: RefObject<HTMLElement | null>, options?: IntersectionObserverInit) {
  const [isVisible, setIsVisible] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    const obs = new IntersectionObserver(([e]) => setIsVisible(e.isIntersecting), options);
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, [ref, options]);
  return isVisible;
}
```

---

## Plugin System → Provider Pattern

| Vue Plugin Feature | React Equivalent |
|---|---|
| `app.use(Plugin, options)` | `<Provider options={}>` in layout |
| `app.provide(key, value)` | `createContext` + `Provider` |
| `inject(key)` | `useContext(Ctx)` |
| `app.config.globalProperties.$x` | Context or module export |
| `app.directive('name', def)` | Custom hook or ref callback |
| `app.component('Name', Comp)` | Regular import (no global registry) |

```tsx
const AnalyticsCtx = createContext<Analytics | null>(null);

export function AnalyticsProvider({ children, trackingId }: { children: React.ReactNode; trackingId: string }) {
  const analytics = useMemo(() => createAnalytics({ trackingId }), [trackingId]);
  return <AnalyticsCtx.Provider value={analytics}>{children}</AnalyticsCtx.Provider>;
}

export function useAnalytics() {
  const ctx = useContext(AnalyticsCtx);
  if (!ctx) throw new Error('useAnalytics must be within AnalyticsProvider');
  return ctx;
}
```

**ComposeProviders** to avoid nesting:
```tsx
function ComposeProviders({ providers, children }: {
  providers: Array<React.FC<{ children: React.ReactNode }>>; children: React.ReactNode
}) {
  return providers.reduceRight((child, Provider) => <Provider>{child}</Provider>, children);
}
<ComposeProviders providers={[ThemeProvider, AuthProvider]}><App /></ComposeProviders>
```

---

## Dynamic Imports

| Vue | React | Next.js |
|---|---|---|
| `defineAsyncComponent(loader)` | `lazy(loader)` | `dynamic(loader)` |
| `loadingComponent` | `<Suspense fallback={}>` | `loading` option |
| `errorComponent` | `<ErrorBoundary>` | `error.tsx` |
| N/A | N/A | `ssr: false` (client-only) |

```tsx
import dynamic from 'next/dynamic';
const HeavyChart = dynamic(() => import('./HeavyChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});
```

---

## Error Boundaries

**Vue:** `onErrorCaptured` hook in any component. Return `false` to stop propagation.

**React:** Must be a class component (no hook API):
```tsx
'use client';
class ErrorBoundary extends Component<{ children: ReactNode; fallback?: ReactNode }, { hasError: boolean }> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error: Error, info: React.ErrorInfo) { console.error(error, info); }
  render() { return this.state.hasError ? (this.props.fallback ?? <div>Error</div>) : this.props.children; }
}
```

**Next.js convention (preferred):**
```tsx
// app/dashboard/error.tsx
'use client';
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return <div><h2>Something went wrong</h2><button onClick={reset}>Retry</button></div>;
}
```
