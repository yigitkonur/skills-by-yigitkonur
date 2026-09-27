# Pass Static Content to Islands Through Slots, Not Props

> **Context:** Islands & Hydration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

When data is passed as props to a hydrated framework component, Astro must serialize that data into JSON and embed it into the HTML page as island metadata. If you pass large HTML strings, blog post bodies, or static lists via props, the payload is duplicated. Passing static HTML through Astro `<slot />` or named slots allows the static content to remain pure HTML without JSON serialization overhead.

## 2. How It Differs From Classic React / Next.js

In React, passing components as children or render props (`renderHeader={() => <Header />}`) passes JavaScript functions. Astro components cannot be passed as render props because Astro has no client runtime. Instead, Astro projects static HTML into React's `props.children` or named slot props (e.g. `props.header`).

## 3. Common Mistakes & Anti-Patterns

Serializing entire article bodies or product specs into complex props objects for an interactive wrapper (like a collapsible accordion), inflating the page payload.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/AccordionWrapper.astro - Passing massive HTML/text as JSON props
import Accordion from './Accordion.jsx';
const { title, fullMarkdownHtml } = Astro.props;
---
<!-- Serializes fullMarkdownHtml into an inline <script type="application/json"> -->
<Accordion client:idle title={title} contentHtml={fullMarkdownHtml} />
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/AccordionWrapper.astro - Projecting static children through slots
import Accordion from './Accordion.jsx';
const { title } = Astro.props;
---
<!-- The content remains static server HTML projected into props.children -->
<Accordion client:idle>
  <span slot="title">{title}</span>
  <div class="prose">
    <slot />
  </div>
</Accordion>
```

In `Accordion.jsx`:

```jsx
export default function Accordion({ title, children }) {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <div>
      <button onClick={() => setIsOpen(!isOpen)}>{title}</button>
      {isOpen && <div className="content">{children}</div>}
    </div>
  )
}
```

## 4. Verification & Audit

Inspect the page source (HTML output) of your built site:

```bash
curl -s http://localhost:4321/faq | grep -C 2 "astro-island"
```

Verify that the `props` attribute on `<astro-island>` contains only small control state and not the heavy HTML text of the children.
