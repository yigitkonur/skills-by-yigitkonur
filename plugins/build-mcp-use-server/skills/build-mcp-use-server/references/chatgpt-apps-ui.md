# OpenAI Apps SDK UI Component & Styling Guide

*Authoritative reference for building ChatGPT MCP Apps compliant with `@openai/apps-sdk-ui` v0.2.2.*

Official resources:
- [OpenAI Apps SDK UI Repository](https://github.com/openai/apps-sdk-ui)
- [Apps SDK UI Storybook Docs](https://openai.github.io/apps-sdk-ui/?path=/docs/overview-introduction--docs)
- [mcp-use ChatGPT Plugin Extensions](https://docs.mcp-use.com/v2/typescript/mcp-apps/chatgpt-extensions)
- [mcp-use MCP Apps Quickstart](https://docs.mcp-use.com/v2/typescript/mcp-apps/quickstart)

---

## 1. Prerequisites & Package Installation

Apps SDK UI is engineered specifically for ChatGPT MCP Apps. It requires **React 18 or 19** and **Tailwind CSS 4**.

```bash
npm install @openai/apps-sdk-ui tailwindcss @tailwindcss/vite
```

### Setup Stylesheet Foundations
Add the foundation styles, Tailwind 4 layers, and mandatory `@source` directive to the top of your view stylesheet (e.g. `views/main.css`):

```css
@import "tailwindcss";
@import "@openai/apps-sdk-ui/css";
/* Required for Tailwind v4 to find class references inside Apps SDK UI components */
@source "../node_modules/@openai/apps-sdk-ui";

/* Application-specific styles below */
```

> [!IMPORTANT]
> **Why `@source` is Mandatory in Tailwind CSS v4:**
> In Tailwind CSS v4, automatic content scanning purges classes from external packages in `node_modules`. Without `@source "../node_modules/@openai/apps-sdk-ui";`, Tailwind will not generate utility classes used internally by `@openai/apps-sdk-ui` (such as `size-4`, `heading-lg`, `tabular-nums`), resulting in unstyled or broken component layouts.

### CSS Import Ordering Invariant
In `views/<name>/view.tsx`, import your stylesheet before rendering any components:

```tsx
import "./main.css";
import React from "react";
```

---

## 2. Root Provider & Router Configuration (`AppsSDKUIProvider`)

All views using `@openai/apps-sdk-ui` must be wrapped in `<AppsSDKUIProvider>`. This provider holds shared context, primarily configuring the router link component used in `<TextLink>`, `<ButtonLink>`, and `<Menu.Link>`.

> [!IMPORTANT]
> The `linkComponent` prop is **required** by TypeScript on `<AppsSDKUIProvider>`. For standard HTML anchor tags, use `linkComponent="a"`.

```tsx
import React from "react";
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";

export function AppRoot({ children }: { children: React.ReactNode }) {
  return (
    <AppsSDKUIProvider linkComponent="a">
      {children}
    </AppsSDKUIProvider>
  );
}
```

### Router Decoupling Pattern (React Router / Next.js)
When using a client-side router, pass the router's `Link` component and declare the global interface for TypeScript prop inheritance:

```tsx
import React from "react";
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";
import { Link } from "react-router";

// Declare global LinkComponent type for TypeScript prop inheritance
declare global {
  interface AppsSDKUIConfig {
    LinkComponent: typeof Link;
  }
}

export function AppRoot({ children }: { children: React.ReactNode }) {
  return (
    <AppsSDKUIProvider linkComponent={Link}>
      {children}
    </AppsSDKUIProvider>
  );
}
```

---

## 3. Dark Mode & Theme Synchronization

Apps SDK UI styles adapt dynamically to light and dark themes using a `[data-theme]` attribute on the root HTML element (`<html data-theme="dark">` or `<html data-theme="light">`).

### Synchronize with `mcp-use` Host Theme
In `mcp-use`, `useViewTheme()` returns a primitive string union `"light" | "dark"`.

> [!WARNING]
> **Primitive String Invariant:**
> `useViewTheme()` returns a primitive string `"light" | "dark"`, NOT an object `{ theme }`. Destructuring `const { theme } = useViewTheme()` produces `undefined` at runtime and silently breaks theme synchronization. Call `const theme = useViewTheme();`.

```tsx
import { useEffect } from "react";
import { useViewTheme } from "mcp-use/react";
import { applyDocumentTheme, useDocumentTheme, getDocumentTheme } from "@openai/apps-sdk-ui/theme";

export function ThemeSync() {
  const theme = useViewTheme(); // Returns string: "light" | "dark"

  useEffect(() => {
    if (theme) {
      applyDocumentTheme(theme);
    }
  }, [theme]);

  return null;
}
```

### Theme Utilities (`@openai/apps-sdk-ui/theme`)
- `applyDocumentTheme(theme: "light" | "dark")`: Sets `<html data-theme="${theme}">` and `document.documentElement.style.colorScheme = theme`.
- `getDocumentTheme(): "light" | "dark"`: Reads current `data-theme` attribute on `<html>`, falling back to `classList.contains("dark")`.
- `useDocumentTheme(): "light" | "dark"`: Reactive hook using a `MutationObserver` on `document.documentElement` observing `["data-theme", "class"]`.

### Tailwind 4 Variant Binding
From `@openai/apps-sdk-ui/css`:
```css
@custom-variant dark (&:where([data-theme=dark], [data-theme=dark] *));
@custom-variant light (&:where([data-theme=light], [data-theme=light] *));
```
This enables Tailwind utility classes like `bg-white dark:bg-black` or `text-default` to respond instantly to ChatGPT theme transitions.

---

## 4. Complete Component Inventory (29 Official Components)

The `@openai/apps-sdk-ui` library contains exactly 29 component directory modules under `src/components/`.

> [!NOTE]
> **No `Card` Component in `@openai/apps-sdk-ui`:**
> There is **no `<Card>` component** in the package. Surfaces and cards are standard `<div>` elements styled with Tailwind semantic classes:
> ```tsx
> <div className="w-full rounded-2xl border border-default bg-surface p-4 shadow-sm">
>   {/* Card content */}
> </div>
> ```

---

### 1. Alert (`src/components/Alert`)
**Category**: Feedback  
Call attention to messages with status icons, wrapping action buttons, and accessible ARIA attributes. Automatically sets `role="alert"` when `color="danger"`.
- `color`: `"primary" | "danger" | "success" | "info" | "discovery" | "caution" | "warning"` (default: `"primary"`, **no `"neutral"`**)
- `variant`: `"solid" | "soft" | "outline"` (default: `"outline"`)
- `title?: ReactNode`, `description?: ReactNode`, `actions?: ReactNode`
- `actionsPlacement?: "end" | "bottom"` (default: auto)
- `indicator?: ReactNode | false` (default: semantic icon based on `color`)

```tsx
import { Alert } from "@openai/apps-sdk-ui/components/Alert";
import { Button } from "@openai/apps-sdk-ui/components/Button";

<Alert
  color="warning"
  variant="soft"
  title="Scheduled Maintenance"
  description="System will be offline on Sunday at 02:00 UTC."
  actions={
    <Button size="sm" variant="outline" color="warning">
      Details
    </Button>
  }
/>
```

---

### 2. AppsSDKUIProvider (`src/components/AppsSDKUIProvider`)
**Category**: Provider / Configuration  
Shared context provider configuring the router link component for all child link controls (`<TextLink>`, `<ButtonLink>`, `<Menu.Link>`).
- `children: ReactNode`
- `linkComponent: ComponentType<any> | ForwardRefExoticComponent<any> | "a"` (required)

---

### 3. Avatar & AvatarGroup (`src/components/Avatar`)
**Category**: Data Display  
Displays user identities via image, initials, or icon. Stacks into multi-user groups with compact overflow count badges.
- `Avatar`:
  - `size?: number` (numeric pixel dimension, e.g. `size={32}`, **not string "md"**)
  - `imageUrl?: string` (**`imageUrl`**, not `src`)
  - `name?: string`, `color?: string`, `variant?: "solid" | "soft"`, `Icon?: ComponentType`
- `AvatarGroup`:
  - `size?: number`, `stack?: "start" | "end"`, `overflowCount?: number`, `children: ReactNode`

```tsx
import { Avatar, AvatarGroup } from "@openai/apps-sdk-ui/components/Avatar";

<Avatar size={32} name="Alex Doe" imageUrl="/avatars/alex.jpg" />

<AvatarGroup size={32} stack="start">
  <Avatar name="Sarah Connor" imageUrl="/avatars/sarah.jpg" />
  <Avatar name="John Connor" imageUrl="/avatars/john.jpg" />
  <Avatar name="Kyle Reese" imageUrl="/avatars/kyle.jpg" />
</AvatarGroup>
```

---

### 4. Badge (`src/components/Badge`)
**Category**: Data Display  
Compact tags indicating status, category, or counts.
- `color`: `"primary" | "secondary" | "danger" | "success" | "warning" | "discovery" | "info"`
- `variant`: `"solid" | "soft" | "outline"` (default: `"soft"`)
- `size`: `"sm" | "md" | "lg"` (default: `"md"`)
- `pill?: boolean`, `children: ReactNode`

```tsx
import { Badge } from "@openai/apps-sdk-ui/components/Badge";

<Badge color="success" variant="soft">Paid</Badge>
<Badge color="warning" pill>Pending</Badge>
```

---

### 5. Button, ButtonLink & CopyButton (`src/components/Button`)
**Category**: Action / Form  
Core pressable actions, router-aware link buttons, and animated copy-to-clipboard buttons.
- `Button`:
  - `color`: `"primary" | "secondary" | "danger"`
  - `variant`: `"solid" | "soft" | "outline" | "ghost"`
  - `size`: `"xs" | "sm" | "md" | "lg"`
  - `pill?: boolean`, `loading?: boolean`, `disabled?: boolean`, `block?: boolean`
- `ButtonLink`: Router-aware button styled anchor.
- `CopyButton`:
  - `copyValue: string | ClipboardContent | (() => string) | (() => ClipboardContent)` (**`copyValue`**, not `value`)
  - `children?: ReactNode` (button text, **not `text`**)
  - Shows animated checkmark upon copy.

```tsx
import { Button, ButtonLink, CopyButton } from "@openai/apps-sdk-ui/components/Button";

<Button color="primary" variant="solid" onClick={handleSave}>Save</Button>
<ButtonLink to="/dashboard" variant="outline">Back to Dashboard</ButtonLink>
<CopyButton copyValue="INV-2026-99">Copy Invoice ID</CopyButton>
```

---

### 6. Checkbox (`src/components/Checkbox`)
**Category**: Form / Input  
Accessible checkbox built on Radix UI supporting checked, unchecked, and indeterminate states.
- `checked?: boolean | "indeterminate"`, `defaultChecked?: boolean`
- `onCheckedChange?: (checked: boolean) => void`
- `label?: ReactNode`, `orientation?: "horizontal" | "vertical"`, `disabled?: boolean`

```tsx
import { Checkbox } from "@openai/apps-sdk-ui/components/Checkbox";

<Checkbox
  checked={agreed}
  onCheckedChange={setAgreed}
  label="I accept the terms and conditions"
/>
```

---

### 7. CodeBlock & CodeBlockBase (`src/components/CodeBlock`)
**Category**: Data Display  
Syntax-highlighted code display using Prism light across 22 programming languages with embedded clipboard copy button.
- `children: string` (code snippet passed as **`children`**, not `code` prop)
- `language?: string` (e.g. `"json"`, `"typescript"`, `"python"`)
- `className?: string` (**no `filename` prop**)

```tsx
import { CodeBlock } from "@openai/apps-sdk-ui/components/CodeBlock";

<CodeBlock language="json">
  {JSON.stringify({ status: "active", count: 42 }, null, 2)}
</CodeBlock>
```

---

### 8. DatePicker (`src/components/DatePicker`)
**Category**: Form / Input  
Luxon DateTime single-date picker integrated with popover calendar, formatted trigger, and clear button.
- `value: DateTime | null`, `onChange: (value: DateTime | null) => void`
- `min?: DateTime`, `max?: DateTime`, `placeholder?: string`
- `triggerDateFormat?: string`, `clearable?: boolean`

```tsx
import { DatePicker } from "@openai/apps-sdk-ui/components/DatePicker";

<DatePicker
  value={selectedDate}
  onChange={setSelectedDate}
  placeholder="Select delivery date"
  clearable
/>
```

---

### 9. DateRangePicker (`src/components/DateRangePicker`)
**Category**: Form / Input  
Date range selection with predefined shortcuts ("Last 7 days", "This month") and multi-month calendar.
- `value: [DateTime | null, DateTime | null]`, `onChange: (range: [DateTime | null, DateTime | null]) => void`
- `min?: DateTime`, `max?: DateTime`, `maxRangeDays?: number`, `shortcuts?: boolean`

```tsx
import { DateRangePicker } from "@openai/apps-sdk-ui/components/DateRangePicker";

<DateRangePicker value={dateRange} onChange={setDateRange} shortcuts />
```

---

### 10. EmptyMessage (`src/components/EmptyMessage`)
**Category**: Feedback  
Compound component for graceful zero-data feedback screens with icons, titles, descriptions, and action rows.

> [!IMPORTANT]
> `EmptyMessage` is a compound component. It does NOT take flat `icon`, `title`, or `description` props.

```tsx
import { EmptyMessage } from "@openai/apps-sdk-ui/components/EmptyMessage";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { Search } from "@openai/apps-sdk-ui/components/Icon";

<EmptyMessage fill="static">
  <EmptyMessage.Icon size="md" color="secondary">
    <Search className="size-6" />
  </EmptyMessage.Icon>
  <EmptyMessage.Title>No results found</EmptyMessage.Title>
  <EmptyMessage.Description>
    Try adjusting your filters or search keywords.
  </EmptyMessage.Description>
  <EmptyMessage.ActionRow>
    <Button variant="outline" onClick={handleReset}>Clear Filters</Button>
  </EmptyMessage.ActionRow>
</EmptyMessage>
```

---

### 11. Icon (`src/components/Icon`)
**Category**: Media / Icons  
745+ native monochrome SVG icons exported from `@openai/apps-sdk-ui/components/Icon`. Standard monochrome icons designed for 20×20 viewports with `size-4` (16px) or `size-5` (20px) styling.

```tsx
import { Search, Check, AlertTriangle, Plus, ChevronDown } from "@openai/apps-sdk-ui/components/Icon";

<Search className="size-4 text-secondary" />
<Check className="size-4 text-success" />
```

---

### 12. Image (`src/components/Image`)
**Category**: Media / Display  
Cached remote image loader preventing layout shift, with graceful failure recovery and broken-image suppression.
- `src: string`, `forceRenderAfterLoadFail?: boolean`, `draggable?: boolean`, standard `HTMLImageElementProps`

```tsx
import { Image } from "@openai/apps-sdk-ui/components/Image";

<Image src="/catalog/item.jpg" alt="Item preview" className="rounded-lg object-cover" />
```

---

### 13. Indicator (`src/components/Indicator`)
**Category**: Feedback / Loading  
The `Indicator` module exports three distinct loading indicators.

> [!CAUTION]
> There is **no presence dot** component called `<Indicator color="green" />`. The module exports `CircularProgress`, `LoadingDots`, and `LoadingIndicator`.

- **`CircularProgress`**: Simulated progress loader.
  - `progress: number` (0–100), `maxDuration?: number`, `size?: number`, `strokeWidth?: number`
- **`LoadingDots`**: Bouncing dots matching conversational ChatGPT loading state.
- **`LoadingIndicator`**: Indeterminate spinning progress indicator.
  - `size?: number` (default: 16)

```tsx
import { CircularProgress, LoadingDots, LoadingIndicator } from "@openai/apps-sdk-ui/components/Indicator";

<LoadingIndicator size={20} />
<LoadingDots />
<CircularProgress progress={75} size={32} />
```

---

### 14. Input (`src/components/Input`)
**Category**: Form / Input  
Single-line text input with optical alignment, password manager suppression, and adornments.
- `startAdornment?: ReactNode`, `endAdornment?: ReactNode` (**`startAdornment` / `endAdornment`**, not `prefix`)
- `variant?: "solid" | "soft" | "outline"`, `size?: "sm" | "md" | "lg"`, `pill?: boolean`
- `invalid?: boolean`, `autoSelect?: boolean` (**no `clearable`**; clearable belongs to DatePicker/SelectControl)

```tsx
import { Input } from "@openai/apps-sdk-ui/components/Input";
import { Search } from "@openai/apps-sdk-ui/components/Icon";

<Input
  placeholder="Search products…"
  startAdornment={<Search className="size-4 text-secondary" />}
  value={query}
  onChange={(e) => setQuery(e.target.value)}
/>
```

---

### 15. Markdown (`src/components/Markdown`)
**Category**: Data Display  
Rich Markdown renderer with KaTeX math formula support, custom directives, sanitized links, and integrated CodeBlocks.
- `children: string` (markdown text passed as **`children`**, not `content` prop)
- `includeMath?: boolean`, `breakNewLines?: boolean`, `directives?: boolean`, `copyableCodeBlocks?: boolean`

```tsx
import { Markdown } from "@openai/apps-sdk-ui/components/Markdown";

<Markdown includeMath>
  {"### Specifications\n- 120Hz OLED Display\n- Battery life: $T = 24\\text{ hrs}$"}
</Markdown>
```

---

### 16. Menu (`src/components/Menu`)
**Category**: Overlay / Navigation  
Compound component built on Radix DropdownMenu supporting cascading submenus, router links, checkbox items, and radio groups.

> [!IMPORTANT]
> Items MUST be wrapped inside `<Menu.Content>`. Subcomponents are accessed via `Menu.*` (e.g. `Menu.Trigger`, `Menu.Content`, `Menu.Item`, `Menu.Separator`, `Menu.Link`, `Menu.CheckboxItem`, `Menu.RadioGroup`).

```tsx
import { Menu } from "@openai/apps-sdk-ui/components/Menu";
import { Button } from "@openai/apps-sdk-ui/components/Button";

<Menu>
  <Menu.Trigger asChild>
    <Button variant="outline">Actions</Button>
  </Menu.Trigger>
  <Menu.Content>
    <Menu.Item onSelect={handleExport}>Export to CSV</Menu.Item>
    <Menu.Link href="/reports">View Reports</Menu.Link>
    <Menu.Separator />
    <Menu.Item onSelect={handleArchive}>Archive</Menu.Item>
  </Menu.Content>
</Menu>
```

---

### 17. Popover (`src/components/Popover`)
**Category**: Overlay  
Compound floating overlay with pointer grace-area tracking (safe triangular hover corridors) and focus trapping.
- Subcomponents: `Popover.Trigger`, `Popover.Content`
- Hooks: `usePopoverController()`
- Props: `open`, `onOpenChange`, `showOnHover`, `hoverOpenDelay`, `side`, `align`

```tsx
import { Popover } from "@openai/apps-sdk-ui/components/Popover";
import { Button } from "@openai/apps-sdk-ui/components/Button";

<Popover>
  <Popover.Trigger asChild>
    <Button variant="outline">Filter Settings</Button>
  </Popover.Trigger>
  <Popover.Content className="p-4 space-y-2">
    <p className="text-sm font-medium">Custom Filters</p>
  </Popover.Content>
</Popover>
```

---

### 18. RadioGroup (`src/components/RadioGroup`)
**Category**: Form / Input  
Accessible single-choice radio group supporting horizontal (`row`) and vertical (`col`) orientations.

> [!IMPORTANT]
> `RadioGroup` requires `"aria-label"`, uses `onChange` (**not `onValueChange`**), and its items are compound `<RadioGroup.Item>` taking `children` (**not `label`**).

```tsx
import { RadioGroup } from "@openai/apps-sdk-ui/components/RadioGroup";

<RadioGroup
  aria-label="Select pricing tier"
  value={tier}
  onChange={setTier}
  direction="col"
>
  <RadioGroup.Item value="basic">Basic ($9/mo)</RadioGroup.Item>
  <RadioGroup.Item value="pro">Pro ($29/mo)</RadioGroup.Item>
</RadioGroup>
```

---

### 19. SegmentedControl (`src/components/SegmentedControl`)
**Category**: Form / Navigation  
Tabbed toggle bar with animated sliding thumb pill and subpixel alignment.

> [!IMPORTANT]
> Requires `"aria-label"`, uses `onChange` (**not `onValueChange`**), and uses compound `<SegmentedControl.Option>` (**not an `options` array prop**).

```tsx
import { SegmentedControl } from "@openai/apps-sdk-ui/components/SegmentedControl";

<SegmentedControl
  aria-label="View layout mode"
  value={viewMode}
  onChange={setViewMode}
>
  <SegmentedControl.Option value="grid">Grid</SegmentedControl.Option>
  <SegmentedControl.Option value="table">Table</SegmentedControl.Option>
  <SegmentedControl.Option value="list">List</SegmentedControl.Option>
</SegmentedControl>
```

---

### 20. Select (`src/components/Select`)
**Category**: Form / Input  
Accessible dropdown selector built on Radix UI.
- `options: Array<{ value: string; label: string }>`
- `value?: Option | Option[]`
- `onChange?: ((option: Option) => void) | ((options: Option[]) => void)` (**receives Option object, not `onValueChange`**)
- `multiple?: boolean`, `clearable?: boolean`, `searchable?: boolean`, `actions?: ReactNode`

```tsx
import { Select } from "@openai/apps-sdk-ui/components/Select";

const categoryOptions = [
  { value: "all", label: "All Categories" },
  { value: "hardware", label: "Hardware" },
  { value: "software", label: "Software" },
];

<Select
  options={categoryOptions}
  value={selectedCategory}
  onChange={(opt) => setSelectedCategory(opt)}
  searchable
/>
```

---

### 21. SelectControl (`src/components/SelectControl`)
**Category**: Form / Input Primitive  
Base pressable input container mimicking native button semantics on span elements for DatePicker and Select triggers.
- `variant`, `size`, `pill`, `block`, `selected: boolean`, `loading: boolean`
- `StartIcon?: ComponentType`, `dropdownIconType?: "chevron" | "calendar"`, `onClearClick?: () => void`

---

### 22. ShimmerText & ShimmerableText (`src/components/ShimmerText`)
**Category**: Feedback / Typography  
Animated shimmering gradient text indicating AI generation, reasoning, or real-time streaming state.
- `as?: ElementType` (default: `"span"`), `shimmer?: boolean`, `children: ReactNode`

```tsx
import { ShimmerText } from "@openai/apps-sdk-ui/components/ShimmerText";

<ShimmerText>Analyzing revenue trends…</ShimmerText>
```

---

### 23. Slider (`src/components/Slider`)
**Category**: Form / Input  
Precision numeric range slider with integrated editable text input and tick marks.

> [!IMPORTANT]
> Takes a single numeric `value: number` (**not an array `[threshold]`**) and uses `onChange: (val: number) => void` (**not `onValueChange`**).

```tsx
import { Slider } from "@openai/apps-sdk-ui/components/Slider";

<Slider
  value={threshold}
  onChange={setThreshold}
  min={0}
  max={100}
  step={5}
  unit="%"
/>
```

---

### 24. Switch (`src/components/Switch`)
**Category**: Form / Input  
Accessible binary toggle switch built on Radix UI with animated thumb and flexible label placement.
- `checked?: boolean`, `defaultChecked?: boolean`, `onCheckedChange?: (checked: boolean) => void`
- `label?: ReactNode`, `labelPosition?: "start" | "end"`, `disabled?: boolean`

```tsx
import { Switch } from "@openai/apps-sdk-ui/components/Switch";

<Switch
  checked={notifications}
  onCheckedChange={setNotifications}
  label="Enable email notifications"
  labelPosition="end"
/>
```

---

### 25. TagInput (`src/components/TagInput`)
**Category**: Form / Input  
Tokenized chip input supporting custom delimiters, validation, and error states.
- `type Tag = { value: string; valid: boolean }`
- `value?: Tag[]` (**`value`**, not `tags`)
- `onChange?: (tags: Tag[]) => void` (**`onChange`**, not `onTagsChange`)
- `validator?: (text: string) => boolean`, `maxTags?: number`, `delimiters?: string[]`, `placeholder?: string`

```tsx
import { TagInput } from "@openai/apps-sdk-ui/components/TagInput";

<TagInput
  value={tags}
  onChange={setTags}
  placeholder="Type tag and press Enter…"
  delimiters={[",", " "]}
/>
```

---

### 26. TextLink (`src/components/TextLink`)
**Category**: Navigation / Typography  
Router-aware semantic anchor linking to internal routes or external URLs with automatic `target="_blank" rel="noopener noreferrer"`.
- `href?: string`, `to?: string`, `as?: ComponentType`, `primary?: boolean`, `underline?: boolean`, `forceExternal?: boolean`

```tsx
import { TextLink } from "@openai/apps-sdk-ui/components/TextLink";

<TextLink href="/analytics" underline>View Analytics</TextLink>
```

---

### 27. Textarea (`src/components/Textarea`)
**Category**: Form / Input  
Multi-line text input with automatic height resizing based on content.

> [!IMPORTANT]
> The auto-resizing prop is `autoResize: boolean` (**`autoResize`**, not `autoGrow`).

```tsx
import { Textarea } from "@openai/apps-sdk-ui/components/Textarea";

<Textarea
  placeholder="Add notes…"
  rows={3}
  maxRows={8}
  autoResize
  value={notes}
  onChange={(e) => setNotes(e.target.value)}
/>
```

---

### 28. Tooltip (`src/components/Tooltip`)
**Category**: Overlay / Feedback  
Contextual hover tooltips with inverse compact styling, rich interactive popovers, and specialized CopyTooltips.
- Subcomponents: `Tooltip`, `Tooltip.Root`, `Tooltip.Content`, `Tooltip.Trigger`, `CopyTooltip`
- Props: `content: ReactNode`, `side?: "top" | "bottom" | "left" | "right"`, `openDelay?: number`, `compact?: boolean`

```tsx
import { Tooltip } from "@openai/apps-sdk-ui/components/Tooltip";

<Tooltip content="Total revenue before tax">
  <span className="cursor-help underline decoration-dotted">Gross Revenue</span>
</Tooltip>
```

---

### 29. Transition (`src/components/Transition`)
**Category**: Animation / Motion  
Five orchestrated animation primitives powering enter/exit transitions, FLIP height/width layout animations, and list staggering:
1. `Animate`: Smooth height or opacity fade transitions.
2. `AnimateLayout`: Automatic layout morphing when siblings resize.
3. `AnimateLayoutGroup`: Synchronizes layout animations across multiple sibling items.
4. `SlotTransitionGroup`: Slot-based transitions for state switches.
5. `TransitionGroup`: Staggered list additions and removals.

---

## 5. Official Hooks Suite (`@openai/apps-sdk-ui/hooks` & `theme`)

### Breakpoint Hook (`useBreakpoint`)
In `@openai/apps-sdk-ui/hooks/useBreakpoints`, the hook is `useBreakpoint(breakpoint: Breakpoint): boolean`. It queries a single breakpoint string:

```tsx
import { useBreakpoint } from "@openai/apps-sdk-ui/hooks/useBreakpoints";

export function ResponsiveView() {
  const isDesktop = useBreakpoint("lg");
  const isTablet = useBreakpoint("md");

  return isDesktop ? <DesktopLayout /> : <CompactLayout />;
}
```

### Full Hooks Index
| Hook | Location | Purpose |
|---|---|---|
| `useBreakpoint(breakpoint)` | `hooks/useBreakpoints` | Evaluates single breakpoint boolean (`"xs" \| "sm" \| "md" \| "lg" \| "xl" \| "2xl"`). |
| `useDocumentTheme()` | `theme` | Reactive hook listening to theme transitions on `<html>`. |
| `useAnimatedScrollTo()` | `hooks/useAnimatedScrollTo` | Programmatic smooth scrolling with cancel tokens. |
| `useAutoGrowTextarea()` | `hooks/useAutoGrowTextarea` | Dynamic height calculation for multi-line inputs. |
| `useCharactersPerSecond()` | `hooks/useCharactersPerSecond` | Measures typing or LLM token streaming speed. |
| `useDocumentVisible()` | `hooks/useDocumentVisible` | Detects iframe visibility and tab switching. |
| `useEscCloseStack()` | `hooks/useEscCloseStack` | Stack-ordered Escape key handling for nested modals and popovers. |
| `useIsMounted()` | `hooks/useIsMounted` | Detects component mount status to avoid stale async state updates. |
| `useLatestValue(val)` | `hooks/useLatestValue` | Mutable ref keeping latest value without triggering re-render. |
| `usePrevious(val)` | `hooks/usePrevious` | Returns value from previous render. |
| `useScrollable()` | `hooks/useScrollable` | Tracks scroll container position and edge reaches. |
| `useSimulatedProgress()` | `hooks/useSimulatedProgress` | Simulated progress incrementer for long-running tool calls. |
| `useStableCallback(fn)` | `hooks/useStableCallback` | Memoized callback ref surviving re-renders. |
| `useTextSelection()` | `hooks/useTextSelection` | Tracks highlighted text within the component. |
| `useTrailingValue(val, delay)`| `hooks/useTrailingValue` | Debounced trailing edge value listener. |

---

## 6. Design Tokens Reference

### Typography Scales
Tailwind classes mapped to official `@openai/apps-sdk-ui` CSS custom properties:
- **Headings**:
  - `heading-5xl`: `72px` (4.5rem)
  - `heading-4xl`: `60px` (3.75rem)
  - `heading-3xl`: `48px` (3rem)
  - `heading-2xl`: `36px` (2.25rem)
  - `heading-xl`: `32px` (2rem)
  - `heading-lg`: `24px` (1.5rem)
  - `heading-md`: `20px` (1.25rem)
  - `heading-sm`: `18px` (1.125rem)
  - `heading-xs`: `16px` (1rem)
- **Body Text**:
  - `text-lg`: `18px` (1.125rem)
  - `text-md`: `16px` (1rem)
  - `text-sm`: `14px` (0.875rem)
  - `text-xs`: `12px` (0.75rem)
  - `text-2xs`: `10px` (0.625rem)
  - `text-3xs`: `8px` (0.5rem)

### Semantic Colors
- **Surfaces**: `bg-surface`, `bg-surface-subtle`, `bg-surface-elevated`
- **Text**: `text-primary`, `text-secondary`, `text-tertiary`
- **Borders**: `border-default`, `border-subtle`, `border-strong`
- **Status & Accents**: `bg-primary`, `text-primary`, `bg-success`, `bg-danger`, `bg-warning`, `bg-info`, `bg-discovery`, `bg-caution`

### Responsive Breakpoints
| Breakpoint | Minimum Width | Context |
|---|---|---|
| `xs` | `380px` | Portrait mobile |
| `sm` | `576px` | Large mobile |
| `md` | `768px` | Inline ChatGPT iframe frame |
| `lg` | `1024px` | Fullscreen ChatGPT view |
| `xl` | `1280px` | Desktop display |
| `2xl` | `1536px` | Widescreen |
