# Manage Script Processing and Hoisting with is:inline Directives

> **Context:** Auditing & Next.js Migration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In Astro, `<script>` tags in `.astro` components are processed, bundled by Vite, hoisted to the document `<head>`, and executed as deferred ES modules (`<script type="module">`) by default. For critical execution paths—such as early theme initialization (preventing dark mode FOUC) or third-party tracking snippets—deferred modules execute too late or suffer from variable scoping issues. Understanding when to use `is:inline` gives developers exact control over script execution timing.

## 2. How It Differs From Classic React / Next.js

In Next.js, `<Script strategy="beforeInteractive" />` or `dangerouslySetInnerHTML` is used to inject inline scripts before hydration. In Astro, appending the `is:inline` directive directly to a standard HTML `<script>` tag instructs the Astro compiler to leave the script exactly where it was authored in the DOM without bundling, transforming, or hoisting it.

## 3. Common Mistakes & Anti-Patterns

Writing a theme toggle script without `is:inline`. Because standard Astro scripts are hoisted as `type="module"`, they execute asynchronously after the initial HTML render, causing a jarring flash of white background before dark mode classes are applied.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// Theme toggle without is:inline: Vite bundles and defers as type="module"
---
<!-- Hoisted to head as deferred module; triggers dark mode flash (FOUC) -->
<script>
  const theme = localStorage.getItem('theme') || 'light';
  if (theme === 'dark') document.documentElement.classList.add('dark');
</script>
```

### ✅ Best Practice / Idiomatic

```astro
---
// Critical blocking script with is:inline: Runs synchronously before body render
---
<!-- Executes immediately in-place before body paint; zero theme flicker -->
<script is:inline>
  const theme = (() => {
    if (typeof localStorage !== 'undefined' && localStorage.getItem('theme')) {
      return localStorage.getItem('theme');
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  })();
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
</script>
```

## 4. Verification & Audit

Verify the location and attributes of the script in the compiled HTML output:

```bash
# Verify is:inline scripts are preserved in-place without type="module"
grep -A 2 '<script>' dist/index.html && echo "PASS: Synchronous in-place script verified"
```
