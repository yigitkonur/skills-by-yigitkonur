# SPA Hook Patching, Theme Registry Injection & Backend Validation

This reference documents how to ensure a custom theme persists across client-side SPA route transitions, appears in the theme picker UI, and passes backend schema validation.

---

## 1. The SPA Route Transition Problem

SSR injection (Reference 11) handles the initial page load. But in a single-page application, subsequent navigations happen entirely on the client:

```
User clicks sidebar link → React Router pushes new route → Client renders new page
                                                          ↓
                                    React may re-run theme provider logic
                                    Virtual DOM reconciliation may strip <style> tags
                                    not managed by the active route component
```

If the SSR-injected `<style id="zeo-custom-theme-ssr">` is removed during reconciliation, the theme reverts to the default on the second page view.

---

## 2. The Client Theme Hook Guard

### Locating the Theme Hook

The client-side theme logic lives in the `useOrgTheme` hook, compiled into a static chunk:

```python
hook_file = "/app/frontend/.next/static/chunks/283d92mv_0-gw.js"
```

> **Note**: The chunk hash changes across builds. Locate it by searching for `useOrgTheme` across all static chunks.

### The Original Theme Class Toggle

Inside the compiled hook, the theme class application function looks like:

```javascript
s=t=>{
  let e=document.documentElement;
  for(let t of Array.from(e.classList).filter(t=>t.startsWith("theme-")))
    e.classList.remove(t);
  e.classList.add(`theme-${t}`)
}
```

This runs every time the theme changes or a route transition triggers `useOrgTheme`. It manages CSS classes but has no awareness of our injected `<style>` tag.

### Splicing the DOM Guard

We patch this function to add a style persistence check after the class toggle:

```javascript
s=t=>{
  let e=document.documentElement;
  for(let t of Array.from(e.classList).filter(t=>t.startsWith("theme-")))
    e.classList.remove(t);
  e.classList.add(`theme-${t}`);
  // --- Zeo Theme Persistence Guard ---
  try{
    let st=document.getElementById("zeo-custom-theme-ssr");
    if(!st){
      st=document.createElement("style");
      st.id="zeo-custom-theme-ssr";
      st.textContent=<css_literal>;   // json.dumps(ZEO_CSS)
      document.head.appendChild(st);
    }
  }catch(e){}
}
```

### How It Works

1. Every time a route changes, `useOrgTheme` calls `s(t)` to set the theme class.
2. After setting the class, the guard checks if `<style id="zeo-custom-theme-ssr">` exists in the DOM.
3. If missing (stripped by reconciliation), it recreates the element with the full CSS and appends it to `<head>`.
4. The `try/catch` ensures any DOM API failure is silently caught — the theme degrades to default tokens rather than crashing the app.

### Python Implementation

```python
import json

css_literal = json.dumps(ZEO_CSS)

target_orig = (
    's=t=>{let e=document.documentElement;'
    'for(let t of Array.from(e.classList).filter(t=>t.startsWith("theme-")))'
    'e.classList.remove(t);e.classList.add(`theme-${t}`)}'
)

guard_code = (
    f's=t=>{{let e=document.documentElement;'
    f'for(let t of Array.from(e.classList).filter(t=>t.startsWith("theme-")))'
    f'e.classList.remove(t);e.classList.add(`theme-${{t}}`);'
    f'try{{let st=document.getElementById("zeo-custom-theme-ssr");'
    f'if(!st){{st=document.createElement("style");'
    f'st.id="zeo-custom-theme-ssr";'
    f'st.textContent={css_literal};'
    f'document.head.appendChild(st);}}}}catch(e){{}}}}'
)

content = content.replace(target_orig, guard_code, 1)
```

---

## 3. Theme Registry Injection (tweakcn)

For the custom theme to appear in the Settings → Appearance → Theme picker, it must exist in the theme registry metadata.

### The Registry Structure

Modern UI platforms (Archestra/tweakcn) embed theme definitions as a JSON array inside compiled JavaScript chunks. Each entry follows this schema:

```json
{
  "name": "zeo-custom",
  "type": "registry:style",
  "title": "Zeo Custom",
  "description": "Zeo Canonical Brand Design System",
  "css": {
    "@layer base": {
      "body": { "letter-spacing": "var(--tracking-normal)" }
    }
  },
  "cssVars": {
    "theme": { "font-sans": "...", "radius": "0.25rem", ... },
    "light": { "background": "#ffffff", "primary": "#cc0a4d", ... },
    "dark":  { "background": "#0e1521", "primary": "#cc0a4d", ... }
  }
}
```

### Locating the Registry

```python
# Search for chunks containing the registry identifier
for root, _, files in os.walk("/app/frontend/.next/server/chunks"):
    for f in files:
        if f.endswith(".js"):
            content = open(os.path.join(root, f), "r", errors="ignore").read()
            if '"tweakcn-theme-registry"' in content:
                print(f"Found registry in {f}")
```

The registry typically appears in both SSR and client chunks — patch both.

### Injection Technique

Find the end of the registry array and splice the new entry before the closing bracket:

```python
target = '"tracking-normal":"0em"}}}]\''      # End of last theme entry + array close
replacement = '"tracking-normal":"0em"}}}' + ZEO_REGISTRY_JSON_SNIPPET + ']}}\''

content = content.replace(target, replacement, 1)
```

### Self-Healing for Malformed JSON

Previous patch runs may leave syntax errors (missing braces). Always check and repair:

```python
buggy = '"tracking-normal":"0em"}},{"name":"zeo-custom"'   # Missing closing brace
fixed = '"tracking-normal":"0em"}}},{"name":"zeo-custom"'  # Correct

if buggy in content:
    content = content.replace(buggy, fixed)
```

---

## 4. Frontend Theme Array Whitelist

Separate from the registry metadata, the theme name must exist in the `SUPPORTED_THEMES` string array used for validation:

```python
target = '"monokai-dark","moonlight-dark"'          # Last two entries in the array
replacement = '"monokai-dark","moonlight-dark","zeo-custom"'

# Patch both server and client chunk directories
for sdir in ["/app/frontend/.next/server/chunks", "/app/frontend/.next/static/chunks"]:
    for root, _, files in os.walk(sdir):
        for f in files:
            if f.endswith(".js"):
                fp = os.path.join(root, f)
                content = open(fp, "r", errors="ignore").read()
                if target in content and '"zeo-custom"' not in content:
                    content = content.replace(target, replacement)
                    open(fp, "w").write(content)
```

---

## 5. Backend Zod Schema Patching

The backend validates theme values against a Zod enum. If the custom theme ID isn't in the enum, API requests to set the theme will return `400 Bad Request`.

```python
# Locate the backend schema file
backend_files = glob.glob("/app/backend/dist/logging-*.mjs")

for path in backend_files:
    content = open(path, "r").read()
    
    if '"zeo-custom"' in content:
        continue  # Already patched
    
    # Append to the SUPPORTED_THEMES array
    target = '"moonlight-dark"\n];'
    replacement = '"moonlight-dark",\n\t"zeo-custom"\n];'
    content = content.replace(target, replacement, 1)
    open(path, "w").write(content)
```

---

## 6. Full Stack Registration Checklist

A custom theme is only fully registered when ALL of these are patched:

| Layer | What to Patch | Failure If Missing |
| :--- | :--- | :--- |
| Backend Zod enum | `logging-*.mjs` SUPPORTED_THEMES | API rejects theme selection with 400 |
| Frontend theme arrays | String arrays in SSR + client chunks | Theme doesn't appear in validation |
| Theme registry metadata | tweakcn JSON in SSR + client chunks | Theme missing from Settings picker |
| SSR `<style>` injection | Root layout SSR chunk (see Ref 11) | FOUC on initial page load |
| Client DOM guard | `useOrgTheme` client chunk | Theme reverts on SPA navigation |
| Database | `organization.theme` column | Theme doesn't persist across sessions |

---

## 7. Idempotency Patterns

Every patching function must be safe to run multiple times:

```python
# Pattern: Check for marker before patching
if '"zeo-custom"' in content:
    print(f"Already patched: {filepath}")
    continue  # Skip — don't double-inject

# Pattern: Replace exact target (not append)
content = content.replace(target, replacement, 1)  # count=1 prevents double replacement
```
