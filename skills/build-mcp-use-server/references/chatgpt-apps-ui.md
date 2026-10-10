# OpenAI Apps SDK UI Component & Styling Guide

*Authoritative reference for building ChatGPT MCP Apps compliant with `@openai/apps-sdk-ui` by default.*

Primary sources:
- [OpenAI Apps SDK UI Repository](https://github.com/openai/apps-sdk-ui)
- [Apps SDK UI Storybook](https://openai.github.io/apps-sdk-ui/?path=/docs/overview-introduction--docs)
- [mcp-use ChatGPT Plugin Extensions](https://docs.mcp-use.com/v2/typescript/mcp-apps/chatgpt-extensions)

---

## 1. Prerequisites & Package Installation

Apps SDK UI is designed specifically for building ChatGPT apps. It requires **React 18 or 19** and **Tailwind 4**.

```bash
npm install @openai/apps-sdk-ui tailwindcss @tailwindcss/vite
```

### Setup Stylesheet Foundations
Add the foundation styles and Tailwind 4 layers to the top of your view stylesheet (e.g. `views/main.css`):

```css
@import "tailwindcss";
@import "@openai/apps-sdk-ui/css";
/* Required for Tailwind to find class references in Apps SDK UI components */
@source "../node_modules/@openai/apps-sdk-ui";

/* Application-specific styles below */
```

In `views/<name>/view.tsx`, import your stylesheet before importing or rendering components:

```tsx
import "./main.css";
import React from "react";
```

---

## 2. Root Provider & Router Configuration (`AppsSDKUIProvider`)

`<AppsSDKUIProvider>` configures router link resolution across components such as `<TextLink>` and `<ButtonLink>`:

```tsx
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";

export function AppRoot({ children }: { children: React.ReactNode }) {
  return (
    <AppsSDKUIProvider>
      {children}
    </AppsSDKUIProvider>
  );
}
```

If your view uses client-side routing (e.g. `react-router`), pass the router `Link` component:

```tsx
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";
import { Link } from "react-router";

<AppsSDKUIProvider linkComponent={Link}>
  <App />
</AppsSDKUIProvider>
```

---

## 3. Dark Mode & Theme Synchronization

Apps SDK UI styles adapt to light and dark themes using a `[data-theme]` attribute on the root HTML element or container.

### Synchronize with `mcp-use` Host Theme
In an `mcp-use` view, the host communicates theme changes via `useViewTheme()`. Synchronize with `@openai/apps-sdk-ui/theme`:

```tsx
import { useEffect } from "react";
import { useViewTheme } from "mcp-use/react";
import { applyDocumentTheme, useDocumentTheme } from "@openai/apps-sdk-ui/theme";

export function ThemeSync() {
  const { theme } = useViewTheme(); // "light" | "dark"

  useEffect(() => {
    if (theme) {
      applyDocumentTheme(theme);
    }
  }, [theme]);

  return null;
}
```

### Theme Utilities (`@openai/apps-sdk-ui/theme`)
- `applyDocumentTheme(theme: "light" | "dark")`: Sets `data-theme` on the root `<html>` element.
- `getDocumentTheme()`: Reads current theme string from document.
- `useDocumentTheme()`: Reactive hook listening to theme changes via `MutationObserver`.

---

## 4. Complete Component Inventory

All components are imported directly from `@openai/apps-sdk-ui/components/<Component>`.

### Feedback & Status Components

#### `Alert`
Inline feedback banners for alerts, notifications, and confirmations.
```tsx
import { Alert } from "@openai/apps-sdk-ui/components/Alert";

<Alert color="info" title="System Maintenance">
  Order processing will be paused on Sunday at 02:00 UTC.
</Alert>
```
- Colors: `info`, `warning`, `danger`, `success`, `neutral`.

#### `Badge`
Compact tags indicating status, category, or counts.
```tsx
import { Badge } from "@openai/apps-sdk-ui/components/Badge";

<Badge color="success">Paid</Badge>
<Badge color="warning">Pending Review</Badge>
<Badge color="danger">Failed</Badge>
```

#### `Indicator`
Visual dot indicating real-time presence or health.
```tsx
import { Indicator } from "@openai/apps-sdk-ui/components/Indicator";

<Indicator color="green" /> {/* Online */}
<Indicator color="gray" />  {/* Idle */}
```

#### `EmptyMessage`
Standardized placeholder when tables, lists, or search results are empty.
```tsx
import { EmptyMessage } from "@openai/apps-sdk-ui/components/EmptyMessage";
import { Search } from "@openai/apps-sdk-ui/components/Icon";

<EmptyMessage
  icon={<Search className="size-6" />}
  title="No items found"
  description="Try adjusting your filter or search keywords."
/>
```

#### `ShimmerText`
Animated text shimmer effect for streaming AI tokens or loading skeletons.
```tsx
import { ShimmerText } from "@openai/apps-sdk-ui/components/ShimmerText";

<ShimmerText>Generating personalized recommendations…</ShimmerText>
```

---

### Actions & Navigation

#### `Button` & `ButtonLink`
Accessible action buttons with variants and icons.
```tsx
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { Plus } from "@openai/apps-sdk-ui/components/Icon";

<Button color="primary" variant="solid" onClick={handleCreate}>
  <Plus className="size-4" />
  New Record
</Button>

<Button color="secondary" variant="soft">
  Cancel
</Button>
```
- `variant`: `solid` | `soft` | `outline` | `ghost`
- `color`: `primary` | `secondary` | `danger`
- `block`: `boolean` (full-width)

---

### Form Controls & Inputs

#### `Input`
Single-line text entry with validation and icon slots.
```tsx
import { Input } from "@openai/apps-sdk-ui/components/Input";
import { Search } from "@openai/apps-sdk-ui/components/Icon";

<Input
  placeholder="Search SKU or name…"
  prefix={<Search className="size-4" />}
  value={query}
  onChange={(e) => setQuery(e.target.value)}
  clearable
/>
```

#### `Textarea`
Multi-line text input with optional automatic height growth.
```tsx
import { Textarea } from "@openai/apps-sdk-ui/components/Textarea";

<Textarea
  placeholder="Add notes or remarks…"
  rows={3}
  autoGrow
  value={notes}
  onChange={(e) => setNotes(e.target.value)}
/>
```

#### `Checkbox`
```tsx
import { Checkbox } from "@openai/apps-sdk-ui/components/Checkbox";

<Checkbox
  checked={agreed}
  onCheckedChange={setAgreed}
  label="I agree to terms"
/>
```

#### `Switch`
Toggle control for binary preferences.
```tsx
import { Switch } from "@openai/apps-sdk-ui/components/Switch";

<Switch
  checked={notifications}
  onCheckedChange={setNotifications}
  label="Enable notifications"
/>
```

#### `RadioGroup`
```tsx
import { RadioGroup, RadioGroupItem } from "@openai/apps-sdk-ui/components/RadioGroup";

<RadioGroup value={plan} onValueChange={setPlan}>
  <RadioGroupItem value="standard" label="Standard ($10/mo)" />
  <RadioGroupItem value="pro" label="Pro ($25/mo)" />
</RadioGroup>
```

#### `SegmentedControl`
Tabbed toggle control for switching view filters or modes.
```tsx
import { SegmentedControl } from "@openai/apps-sdk-ui/components/SegmentedControl";

<SegmentedControl
  value={viewMode}
  onValueChange={setViewMode}
  options={[
    { label: "List", value: "list" },
    { label: "Grid", value: "grid" },
    { label: "Timeline", value: "timeline" },
  ]}
/>
```

#### `Select` & `SelectControl`
Accessible dropdown selector built on Radix UI.
```tsx
import { Select } from "@openai/apps-sdk-ui/components/Select";

<Select
  value={category}
  onValueChange={setCategory}
  options={[
    { label: "All Categories", value: "all" },
    { label: "Hardware", value: "hardware" },
    { label: "Electronics", value: "electronics" },
  ]}
/>
```

#### `TagInput`
Multi-value input for keywords, labels, or emails.
```tsx
import { TagInput } from "@openai/apps-sdk-ui/components/TagInput";

<TagInput
  tags={tags}
  onTagsChange={setTags}
  placeholder="Add tag and press Enter…"
/>
```

#### `DatePicker` & `DateRangePicker`
```tsx
import { DatePicker } from "@openai/apps-sdk-ui/components/DatePicker";
import { DateRangePicker } from "@openai/apps-sdk-ui/components/DateRangePicker";

<DatePicker value={selectedDate} onChange={setSelectedDate} />
<DateRangePicker value={range} onChange={setRange} />
```

---

### Overlays & Menus

#### `Menu`
Contextual or action dropdown menus.
```tsx
import { Menu, MenuItem, MenuTrigger } from "@openai/apps-sdk-ui/components/Menu";
import { Button } from "@openai/apps-sdk-ui/components/Button";

<Menu>
  <MenuTrigger asChild>
    <Button variant="outline">Options</Button>
  </MenuTrigger>
  <MenuItem onSelect={handleExport}>Export CSV</MenuItem>
  <MenuItem onSelect={handleArchive} color="danger">Archive</MenuItem>
</Menu>
```

#### `Popover`
Anchored floating cards for detailed controls.
```tsx
import { Popover, PopoverContent, PopoverTrigger } from "@openai/apps-sdk-ui/components/Popover";
```

#### `Tooltip` & `CopyTooltip`
```tsx
import { Tooltip } from "@openai/apps-sdk-ui/components/Tooltip";
import { CopyTooltip } from "@openai/apps-sdk-ui/components/Tooltip";

<CopyTooltip text="INV-2026-99" content="Copy invoice ID" />
```

---

### Media, Identity & Icons

#### `Avatar` & `AvatarGroup`
```tsx
import { Avatar, AvatarGroup } from "@openai/apps-sdk-ui/components/Avatar";

<Avatar src="/avatars/user.jpg" name="Alex Doe" size="md" />
<AvatarGroup>
  <Avatar src="/u1.png" name="User 1" />
  <Avatar src="/u2.png" name="User 2" />
</AvatarGroup>
```

#### `Icon` (700+ Native Monochrome SVGs)
Import any icon from `@openai/apps-sdk-ui/components/Icon`:
```tsx
import {
  Cart,
  Checkmark,
  Calendar,
  Invoice,
  Search,
  Settings,
  User,
  Warning,
  ArrowRight,
  ChevronDown
} from "@openai/apps-sdk-ui/components/Icon";

<Cart className="size-4 text-primary" />
```

---

### Typography & Content

#### `Markdown`
Render formatted markdown directly inside the app.
```tsx
import { Markdown } from "@openai/apps-sdk-ui/components/Markdown";

<Markdown content="## Product Specs\n- 120Hz Refresh Rate\n- OLED display" />
```

#### `CodeBlock`
Syntax-highlighted code container with language badge and copy action.
```tsx
import { CodeBlock } from "@openai/apps-sdk-ui/components/CodeBlock";

<CodeBlock code={jsonString} language="json" filename="response.json" />
```

#### `TextLink`
```tsx
import { TextLink } from "@openai/apps-sdk-ui/components/TextLink";

<TextLink href="/docs">Read documentation</TextLink>
```

---

### Motion & Transitions

Import layout animation utilities from `@openai/apps-sdk-ui/components/Transition`:
- `Animate`: Smooth height or opacity fade transitions.
- `AnimateLayout`: Automatic layout morphing when siblings resize.
- `TransitionGroup`: Staggered entry and exit lists.

---

## 5. Design Tokens Reference

### Typography Scales
Apply utility classes directly in JSX:
- Headings: `heading-5xl` (72px), `heading-4xl` (60px), `heading-3xl` (48px), `heading-2xl` (36px), `heading-xl` (32px), `heading-lg` (24px), `heading-md` (20px), `heading-sm` (16px), `heading-xs` (14px).
- Body Text: `text-lg` (18px), `text-md` (16px), `text-sm` (14px), `text-xs` (12px), `text-2xs` (11px).

### Semantic Colors
- Backgrounds: `bg-surface`, `bg-surface-subtle`, `bg-surface-elevated`
- Text: `text-primary`, `text-secondary`, `text-tertiary`
- Borders: `border-default`, `border-subtle`, `border-strong`
- Accents: `bg-primary`, `text-primary`, `bg-success`, `bg-danger`, `bg-warning`, `bg-info`

### Responsive Breakpoints
Follow mobile-first responsive design:
| Breakpoint | Minimum Width | Common Device / Context |
|---|---|---|
| `xs` | `380px` | Portrait mobile |
| `sm` | `576px` | Large mobile / phablet |
| `md` | `768px` | Tablet / inline ChatGPT frame |
| `lg` | `1024px` | Laptop / fullscreen ChatGPT view |
| `xl` | `1280px` | Desktop display |
| `2xl` | `1536px` | Widescreen |

Use `useBreakpoint("md")` from `@openai/apps-sdk-ui/hooks/useBreakpoint` for conditional rendering based on viewport width.
