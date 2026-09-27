# Implement Progressive Enhancement With Astro Actions and `isInputError`

> **Context:** Data Fetching & Endpoints | **Impact:** High | **Target:** Astro 4.15+ / Astro 5

## 1. Why We Do This

Astro Actions provide type-safe server mutations. While they can be called imperatively via client-side JavaScript (`await actions.submit()`), they natively support HTML forms without client-side JavaScript. By setting `<form method="POST" action={actions.submit}>`, submissions execute via standard HTTP POST if JavaScript is disabled or fails to load. On re-render, `Astro.getActionResult()` retrieves the submission state, and the `isInputError()` type guard extracts Zod schema validation errors cleanly per input field.

## 2. How It Differs From Classic React / Next.js

Next.js Server Actions depend on the React client runtime (`useActionState`, `useFormStatus`), pulling React bundles into the browser. Astro Actions operate natively with pure HTML forms and frontmatter scripts, delivering zero client-side JavaScript.

## 3. Common Mistakes & Anti-Patterns

Hydrating an entire React form component (`client:load`) just to manage submit state and display Zod validation errors, adding 40+ KB of unnecessary client bundle overhead.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// Heavy React island imported solely for form validation
import ContactFormReact from "../components/ContactFormReact.jsx";
---
<!-- Bloats page bundle with React runtime and Zod validator on client -->
<ContactFormReact client:load />
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/contact.astro
import { actions, isInputError } from 'astro:actions';

export const prerender = false;

const result = Astro.getActionResult(actions.submitContact);
const inputErrors = isInputError(result?.error) ? result.error.fields : {};
---

<!-- Pure HTML form with progressive enhancement and zero client JS -->
<form method="POST" action={actions.submitContact}>
  <label for="email">Email</label>
  <input id="email" name="email" type="email" required />
  {inputErrors.email && <span class="error">{inputErrors.email.join(", ")}</span>}

  <label for="message">Message</label>
  <textarea id="message" name="message" required></textarea>
  {inputErrors.message && <span class="error">{inputErrors.message.join(", ")}</span>}

  <button type="submit">Send Message</button>
  {result?.data?.success && <p class="success">Message sent successfully!</p>}
</form>
```

## 4. Verification & Audit

In browser DevTools, disable JavaScript completely and submit the form with invalid data:

1. Verify the form posts to the action handler and returns server-rendered HTML.
2. Confirm field validation errors appear beneath each invalid input with zero console errors.
