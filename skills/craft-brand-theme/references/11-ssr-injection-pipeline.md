# SSR Injection Pipeline: Theme CSS on the First HTML Byte

This reference documents how to inject theme CSS directly into a Next.js App Router server-side rendered layout chunk, ensuring the theme is delivered on the very first TCP packet before any client JavaScript executes.

---

## 1. Why SSR Injection Is Required

Standard theme approaches (external stylesheets, client-side `useEffect` injection, `<link>` tags) all suffer from the same fatal flaw: the browser renders at least one frame of unstyled content before the theme applies.

In production with Cloudflare CDN or any edge cache:
- External `.css` files may be cached at a stale version or served from a different edge node than the HTML.
- Client-side injection (`document.createElement("style")`) fires after React hydration — causing a visible flash where default tokens render for 200–400ms before custom tokens replace them.
- `<link rel="stylesheet">` blocks rendering but adds a network round-trip.

SSR injection solves all three problems: the `<style>` tag is **embedded directly in the HTML response**, so the browser applies the theme tokens before painting the first pixel.

---

## 2. Anatomy of a Next.js App Router SSR Chunk

Next.js App Router compiles `layout.tsx` into a server-side rendering chunk. In standalone/production builds, this lives at:

```
/app/frontend/.next/server/chunks/ssr/_09aanm3._.js
```

> **Note**: The hash portion (`_09aanm3`) changes across builds. Use `grep` or `glob` to locate the correct file by searching for the anchor string.

Inside this file, the `<head>` children are expressed as compiled JSX calls:

```javascript
(0,b.jsx)("html",{lang:"en",children:[
  (0,b.jsxs)("head",{children:[
    (0,b.jsx)(K.PublicEnvScript,{}),   // <-- The anchor point
    (0,b.jsx)("meta",{charSet:"utf-8"}),
    // ... more head elements
  ]}),
  (0,b.jsx)("body",{/* ... */})
]})
```

The `PublicEnvScript` component is a stable anchor that appears in every App Router build. It injects public environment variables into the HTML.

---

## 3. The Injection Technique

### Step 1: Locate the Anchor

```python
layout_file = "/app/frontend/.next/server/chunks/ssr/_09aanm3._.js"
with open(layout_file, "r", encoding="utf-8") as f:
    content = f.read()

target_anchor = "(0,b.jsx)(K.PublicEnvScript,{})"
assert target_anchor in content, "Anchor not found — chunk hash may have changed"
```

### Step 2: Serialize CSS Safely

The CSS string must be serialized to a valid JavaScript string literal. `json.dumps()` handles all edge cases: newlines become `\n`, quotes are escaped, and backslashes are doubled.

```python
import json
css_literal = json.dumps(ZEO_CSS)  # Produces: "/* ... */\n@font-face { ... }\n:root { ... }"
```

### Step 3: Construct the JSX Call

Build a compiled React JSX call matching the exact syntax the Next.js compiler produces:

```python
injected_jsx = (
    f'(0,b.jsx)("style",{{id:"zeo-custom-theme-ssr",'
    f'dangerouslySetInnerHTML:{{__html:{css_literal}}}}})'
)
```

This compiles to the equivalent of:

```jsx
<style id="zeo-custom-theme-ssr" dangerouslySetInnerHTML={{ __html: ZEO_CSS }} />
```

### Step 4: Splice After the Anchor

```python
replacement = f"{target_anchor},{injected_jsx}"
content = content.replace(target_anchor, replacement, 1)

with open(layout_file, "w", encoding="utf-8") as f:
    f.write(content)
```

The comma after `PublicEnvScript` makes the style tag a sibling element in the JSX children array.

---

## 4. Idempotent In-Place Update

On subsequent runs, the CSS content may have changed (token tweaks, font additions). The injection must cleanly **replace** the existing style tag rather than appending a duplicate.

```python
MARKER = '"zeo-custom-theme-ssr"'

if MARKER in content:
    # Find the exact boundaries of the existing injection
    start_marker = '(0,b.jsx)("style",{id:"zeo-custom-theme-ssr",dangerouslySetInnerHTML:{__html:'
    start_idx = content.find(start_marker)
    end_idx = content.find('}})', start_idx) + 3  # Include the closing }}
    
    old_chunk = content[start_idx:end_idx]
    content = content.replace(old_chunk, injected_jsx)
else:
    # First-time injection: splice after anchor
    content = content.replace(target_anchor, f"{target_anchor},{injected_jsx}", 1)
```

---

## 5. Why This Eliminates FOUC

The server-side rendering pipeline works as follows:

```
1. Browser requests GET /chat
2. Next.js server executes the root layout SSR chunk
3. The compiled JSX children array renders <head> elements sequentially
4. Our <style> tag is serialized into the HTML response body BEFORE </head>
5. Browser receives HTML with <style> already present
6. First paint uses the correct custom properties — zero flash
```

Because the `<style>` tag is part of the HTML document (not a separate resource), it:
- Cannot be CDN-cached separately from the page
- Cannot be delayed by a network round-trip
- Cannot be FOUC'd by client hydration timing

---

## 6. Critical Implementation Notes

| Concern | Guidance |
| :--- | :--- |
| **Chunk hash changes** | The filename `_09aanm3._.js` changes across builds. Use `glob.glob("/app/frontend/.next/server/chunks/ssr/_*.js")` + content search for `PublicEnvScript` to locate dynamically. |
| **Multiple head children arrays** | Some layouts have nested `<head>` fragments. Always search for the specific `PublicEnvScript` anchor, not a generic `"head"` string. |
| **JSON serialization safety** | Never use string concatenation or f-strings for the CSS content. `json.dumps()` is the only safe serializer — it handles embedded quotes, newlines, and Unicode correctly. |
| **File encoding** | Always read/write with `encoding="utf-8"`. Compiled chunks may contain non-ASCII characters from internationalization strings. |
| **Process restart** | After modifying the SSR chunk, the running `next-server` process has the old file cached in V8 memory. A process restart (`pkill -9 -f next-server`) is mandatory. Supervisord or the container orchestrator will respawn it automatically. |
