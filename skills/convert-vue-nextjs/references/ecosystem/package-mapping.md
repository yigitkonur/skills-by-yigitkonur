# Vue → React/Next.js Package Mapping

> Comprehensive ecosystem mapping for converting Vue applications to React/Next.js, with migration effort ratings and code examples.

---

## Master Package Mapping Table

| Category | Vue Package | React/Next.js Equivalent | Effort | Notes |
|---|---|---|---|---|
| **Core Framework** | Vue 3 (Composition API) | React 18/19 (Hooks) | 🔴 High | Fundamentally different reactivity models |
| **Meta-Framework** | Nuxt 3 | Next.js 14/15 | 🔴 High | Full framework swap; similar concepts, different APIs |
| **Routing** | Vue Router 4 | Next.js App Router | 🔴 High | Config-based → file-system routing paradigm shift |
| **State (Simple)** | Pinia | Zustand | 🟡 Medium | Closest API similarity; `defineStore()` → `create()` |
| **State (Complex)** | Vuex | Redux Toolkit (RTK) | 🟡 Medium | Mutations → reducers, actions → thunks |
| **State (Atomic)** | Pinia (fine-grained) | Jotai | 🟡 Medium | Each `ref` becomes an `atom` |
| **DI / Globals** | `provide` / `inject` | React Context + `useContext` | 🟢 Low | Direct conceptual mapping |
| **Data Fetching** | @tanstack/vue-query | @tanstack/react-query | 🟢 Low | Same library, different framework adapter |
| **Data Fetching** | Nuxt `useFetch` | Server Components + `fetch()` | 🟡 Medium | Composable → async RSC pattern |
| **HTTP Client** | Axios | Axios / native `fetch` / ky | 🟢 Low | Axios works identically; consider native `fetch` in RSC |
| **Forms** | VeeValidate | React Hook Form + Zod | 🟡 Medium | Field-level → register-based; Yup schemas reusable |
| **Forms** | Vuelidate | React Hook Form + Zod | 🟡 Medium | Declarative rules → Zod schema definitions |
| **Forms** | FormKit | React Hook Form | 🟡 Medium | Schema-driven → hook-driven |
| **Validation** | Yup (shared) | Yup or Zod | 🟢 Low | Yup schemas reusable via `@hookform/resolvers/yup` |
| **i18n** | vue-i18n | next-intl (Next.js) | 🟡 Medium | JSON files reusable; pluralization syntax differs |
| **i18n** | vue-i18n | react-i18next (generic) | 🟡 Medium | Framework-agnostic alternative; `{{name}}` interpolation |
| **UI Components** | Vuetify | MUI (Material UI) | 🔴 High | Both Material Design; completely different APIs |
| **UI Components** | Quasar | Ant Design / MUI | 🔴 High | No single equivalent; cross-platform lost |
| **UI Components** | PrimeVue | PrimeReact | 🟢 Low | Same vendor, near-identical component API |
| **UI Components** | Element Plus | Ant Design | 🟡 Medium | Enterprise-focused; similar density |
| **UI Components** | Naive UI | Mantine | 🟡 Medium | Both TypeScript-first, composable API |
| **UI (Headless)** | Headless UI (Vue) | Headless UI (React) | 🟢 Low | Same library by Tailwind Labs |
| **UI (Headless)** | Radix Vue | Radix UI | 🟢 Low | Vue port → React original |
| **UI (Headless)** | shadcn-vue | shadcn/ui | 🟢 Low | Community port → original; copy-paste model |
| **Icons** | unplugin-icons | react-icons / lucide-react | 🟢 Low | Direct swap; Lucide icons work in both |
| **Animation** | `<Transition>` built-in | Framer Motion | 🟡 Medium | No built-in React equivalent |
| **Animation** | GSAP | GSAP | 🟢 None | Framework-agnostic; works identically |
| **Auth** | @sidebase/nuxt-auth | NextAuth.js (Auth.js) | 🟡 Medium | Different API; same OAuth concepts |
| **Meta/SEO** | @unhead/vue / useHead | `generateMetadata()` (Next.js) | 🟡 Medium | Composable → export function in page |
| **Date/Time** | date-fns / dayjs | date-fns / dayjs | 🟢 None | Framework-agnostic; no changes needed |
| **CSS Scoping** | `<style scoped>` | CSS Modules (`.module.css`) | 🟢 Low | Rename + import as object |
| **CSS Utility** | Tailwind CSS | Tailwind CSS | 🟢 None | `class` → `className` only |
| **CSS Utility** | UnoCSS | Tailwind CSS or UnoCSS | 🟢 Low | UnoCSS works with React; Tailwind has larger ecosystem |
| **Testing (Runner)** | Vitest | Vitest (same!) or Jest | 🟢 Low | Vitest works natively with React |
| **Testing (Component)** | Vue Test Utils | React Testing Library | 🟡 Medium | Philosophy shift to accessibility queries |
| **Testing (E2E)** | Cypress / Playwright | Cypress / Playwright | 🟢 None | Framework-agnostic; same tests work |
| **Dev Tools** | Vue DevTools | React DevTools | 🟢 N/A | Different browser extension |
| **Build Tools** | Vite | Next.js (Turbopack) or Vite | 🟡 Medium | Config rewrite; env var prefix change |
| **Linting** | eslint-plugin-vue | eslint-plugin-react + react-hooks | 🟢 Low | Swap ESLint plugins |
| **Auto-imports** | unplugin-auto-import | None (explicit imports) | 🟢 Low | React convention: explicit imports |
| **Storybook** | @storybook/vue3 | @storybook/react | 🟡 Medium | Framework config change; stories need JSX |
| **Docs** | VitePress | Nextra or Docusaurus | 🟡 Medium | Nextra is Next.js-native |

---

## UI Component Libraries

### Migration Paths

| Current Vue Library | Recommended React Target | Why |
|---|---|---|
| Vuetify | MUI or shadcn/ui + Tailwind | MUI for Material Design fidelity; shadcn/ui for modern approach |
| Quasar | shadcn/ui + Tailwind (web only) | No single React equivalent; cross-platform requires separate projects |
| PrimeVue | PrimeReact | Lowest effort — same vendor, same component names |
| Element Plus | Ant Design | Enterprise-focused, similar component density |
| Naive UI | Mantine | TypeScript-first, composable API |
| Headless UI (Vue) | Headless UI (React) | Same library, swap import path |
| Radix Vue | Radix UI | Vue port → original React library |
| shadcn-vue | shadcn/ui | Community port → better-maintained original |

### Vuetify → MUI Quick Map

| Vuetify | MUI | Notes |
|---|---|---|
| `<v-btn>` | `<Button>` | Props differ; `color`, `variant` patterns similar |
| `<v-card>` | `<Card>` | Subcomponents: `CardContent`, `CardActions` |
| `<v-dialog>` | `<Dialog>` | Controlled via open/onClose props |
| `<v-text-field>` | `<TextField>` | Closest mapping |
| `<v-row>` / `<v-col>` | `<Grid>` or CSS Grid | MUI Grid or use Tailwind grid |
| `<v-data-table>` | `<DataGrid>` (MUI X) | MUI X is a paid add-on for advanced tables |
| Vuetify theme | `createTheme()` | Both use Material tokens; different config format |

> **Key gotcha:** Vuetify's directive-based features (`v-ripple`, `v-scroll`) have no MUI equivalent — implement with custom React hooks or CSS.

---

## Form Handling

### VeeValidate → React Hook Form + Zod

**Vue (VeeValidate):**
```vue
<script setup>
import { useForm, useField } from 'vee-validate'
import * as yup from 'yup'

const schema = yup.object({
  email: yup.string().required().email(),
  password: yup.string().required().min(8),
})

const { handleSubmit } = useForm({ validationSchema: schema })
const { value: email, errorMessage: emailError } = useField('email')
const { value: password, errorMessage: passError } = useField('password')

const onSubmit = handleSubmit((values) => {
  console.log(values)
})
</script>
<template>
  <form @submit="onSubmit">
    <input v-model="email" type="email" />
    <span v-if="emailError">{{ emailError }}</span>
    <input v-model="password" type="password" />
    <span v-if="passError">{{ passError }}</span>
    <button type="submit">Submit</button>
  </form>
</template>
```

**React (React Hook Form + Zod):**
```tsx
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().min(1, 'Required').email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
});

type FormData = z.infer<typeof schema>;

export default function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = (data: FormData) => console.log(data);

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} type="email" />
      {errors.email && <span>{errors.email.message}</span>}
      <input {...register('password')} type="password" />
      {errors.password && <span>{errors.password.message}</span>}
      <button type="submit">Submit</button>
    </form>
  );
}
```

### Key Mapping

| VeeValidate | React Hook Form | Notes |
|---|---|---|
| `<Form>` component | `<form onSubmit={handleSubmit(fn)}>` | RHF uses native form + hook |
| `<Field name="x" />` | `<input {...register('x')} />` | `register()` returns input props |
| `<ErrorMessage name="x" />` | `{errors.x && <span>{errors.x.message}</span>}` | Manual error rendering |
| `useField('x')` | `useController({ name: 'x' })` | For custom/controlled components |
| Yup schemas | Yup or Zod via `@hookform/resolvers` | Yup schemas can be reused directly |

---

## Internationalization (i18n)

### vue-i18n → next-intl (Recommended for Next.js)

**Translation files are mostly reusable!** JSON structure stays the same. Key difference: pluralization syntax.

```json
// Vue (vue-i18n): src/locales/en.json
{
  "greeting": "Hello, {name}!",
  "items": "no items | one item | {count} items"
}

// Next.js (next-intl): messages/en.json
{
  "greeting": "Hello, {name}!",
  "items": "{count, plural, =0 {no items} one {one item} other {# items}}"
}
```

**Vue component usage:**
```vue
<script setup>
import { useI18n } from 'vue-i18n'
const { t, locale } = useI18n()
</script>
<template>
  <h1>{{ t('greeting', { name: 'World' }) }}</h1>
  <p>{{ t('items', { count: 5 }) }}</p>
  <select v-model="locale">
    <option value="en">English</option>
    <option value="fr">Français</option>
  </select>
</template>
```

**Next.js component usage (next-intl):**
```tsx
// app/[locale]/page.tsx (Server Component — works without 'use client'!)
import { useTranslations } from 'next-intl';

export default function Home() {
  const t = useTranslations();
  return (
    <>
      <h1>{t('greeting', { name: 'World' })}</h1>
      <p>{t('items', { count: 5 })}</p>
    </>
  );
}
```

| Feature | vue-i18n | next-intl | react-i18next |
|---|---|---|---|
| JSON format | Flat/nested | Same ✅ | Same ✅ |
| Pluralization | Pipe syntax (`\|`) | ICU format | ICU format |
| Interpolation | `{name}` | `{name}` ✅ | `{{name}}` (double braces!) |
| Server rendering | Nuxt SSR | RSC native ✅ | SSR with config |
| Recommendation | — | **Best for Next.js** | **Best for non-Next.js** |

---

## Testing

### Vue Test Utils → React Testing Library

**Philosophy shift:** VTU queries by component internals (CSS selectors, `wrapper.vm`). RTL queries by what the user sees (roles, text, labels).

| Vue Test Utils | React Testing Library | Notes |
|---|---|---|
| `mount(Comp, { props })` | `render(<Comp {...props} />)` | Access rendered output via `screen` |
| `shallowMount(Comp)` | `render(<Comp />)` (no shallow) | RTL renders fully; mock children if needed |
| `wrapper.find('.class')` | `screen.getByRole('button')` | Query by role, not CSS selector |
| `wrapper.find('[data-test]')` | `screen.getByTestId('x')` | Supported but discouraged |
| `wrapper.text()` | `screen.getByText('text')` | Queries are assertions |
| `wrapper.trigger('click')` | `fireEvent.click(el)` or `userEvent.click(el)` | Prefer `userEvent` for realistic interaction |
| `wrapper.setProps({...})` | `rerender(<Comp newProp />)` | Destructure from `render()` return |
| `wrapper.emitted('event')` | `expect(mockFn).toHaveBeenCalled()` | Test callback props, not emitted events |
| `wrapper.vm.someRef` | **No equivalent** | Test behavior, not internals |
| `wrapper.exists()` | `screen.queryByRole(...)` | Returns `null` if not found |
| `await nextTick()` | `await waitFor(() => ...)` | For async state updates |

**Vue Test (Vitest):**
```ts
import { mount } from '@vue/test-utils'

test('submits form', async () => {
  const wrapper = mount(LoginForm)
  await wrapper.find('input[type="email"]').setValue('test@example.com')
  await wrapper.find('input[type="password"]').setValue('password123')
  await wrapper.find('form').trigger('submit')
  expect(wrapper.emitted('submit')).toBeTruthy()
})
```

**React Test (Vitest + RTL):**
```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

test('submits form', async () => {
  const handleSubmit = vi.fn()
  render(<LoginForm onSubmit={handleSubmit} />)
  await userEvent.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com')
  await userEvent.type(screen.getByLabelText(/password/i), 'password123')
  await userEvent.click(screen.getByRole('button', { name: /submit/i }))
  expect(handleSubmit).toHaveBeenCalledOnce()
})
```

> **Vitest stays!** It works natively with React via `@vitejs/plugin-react`. Keep your test runner — only change the component testing library.

---

## Utility Libraries (VueUse → React Hooks)

VueUse has 200+ composables. No single React library matches it. Use a combination:

| VueUse Composable | React Equivalent | Library |
|---|---|---|
| `useStorage` | `useLocalStorage` | usehooks-ts |
| `useDebounce` | `useDebounce` | usehooks-ts |
| `useWindowSize` | `useWindowSize` | usehooks-ts |
| `useMediaQuery` | `useMediaQuery` | usehooks-ts |
| `useIntersectionObserver` | `useIntersectionObserver` | usehooks-ts |
| `useMouse` | `useMouse` | @uidotdev/usehooks |
| `useClipboard` | `useCopyToClipboard` | usehooks-ts |
| `useDark` | `useTheme` | next-themes (Next.js-optimized) |
| `useFetch` | `useQuery` | @tanstack/react-query |
| `useAsyncState` | `useQuery` + `useMutation` | @tanstack/react-query |
| `useEventListener` | `useEventListener` | usehooks-ts |
| `useInterval` | `useInterval` | usehooks-ts |
| `useToggle` | `useToggle` | usehooks-ts |
| `onClickOutside` | `useOnClickOutside` | usehooks-ts |

**Recommended libraries (in priority order):**
1. **usehooks-ts** — TypeScript-first, well-maintained, covers most VueUse equivalents
2. **@tanstack/react-query** — For all data fetching composables (replaces `useFetch`, `useAsyncState`)
3. **react-use** — Largest single hook library (~200 hooks), closest to VueUse in breadth
4. **next-themes** — Specifically for dark mode in Next.js (replaces `useDark`)

---

## HTTP & Data Fetching

### Axios — No Migration Needed

Axios works identically in React. In Next.js Server Components, prefer native `fetch` for automatic caching:

```tsx
// Server Component — native fetch with Next.js caching
async function getUsers() {
  const res = await fetch('https://api.example.com/users', {
    next: { revalidate: 60 },
  });
  return res.json();
}
```

### @tanstack/vue-query → @tanstack/react-query

Same library, nearly identical API. Change imports and wrap app with `<QueryClientProvider>`:

```tsx
// app/providers.tsx — required for React Query
'use client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
const queryClient = new QueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```

---

## Environment Variables

| Vite (Vue) | Next.js | Notes |
|---|---|---|
| `VITE_API_URL` | `NEXT_PUBLIC_API_URL` | Client-exposed prefix changes |
| `import.meta.env.VITE_X` | `process.env.NEXT_PUBLIC_X` | Access pattern changes |
| `import.meta.env.MODE` | `process.env.NODE_ENV` | Built-in equivalent |
| `import.meta.env.SSR` | `typeof window === 'undefined'` | Server detection |
| `.env.local` | `.env.local` | Same file, same behavior ✅ |
