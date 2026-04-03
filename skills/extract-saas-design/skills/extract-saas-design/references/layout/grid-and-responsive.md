# Grid Systems & Responsive Layout

How to document the layout architecture of a SaaS dashboard — grid structure, sidebar behavior, content areas, and responsive breakpoints.

---

## Dashboard Layout Architecture

### The Standard SaaS Layout

```
┌─────────────────────────────────────────────────────────┐
│ Top Bar (optional — some apps omit this)        h: 48-64px │
├────────────┬────────────────────────────────────────────┤
│            │                                            │
│  Sidebar   │  Main Content Area                         │
│  w: 240-   │  max-w: varies                             │
│  280px     │                                            │
│            │  ┌──────────────────────────────────┐      │
│  Collapsed:│  │ Page Header                      │      │
│  48-64px   │  │ (title, description, CTA)        │      │
│  (icon     │  ├──────────────────────────────────┤      │
│   only)    │  │ Content (scrollable)             │      │
│            │  │                                  │      │
│            │  │                                  │      │
│            │  └──────────────────────────────────┘      │
│            │                                            │
├────────────┴────────────────────────────────────────────┤
│ (No bottom bar on desktop — mobile may have dock)       │
└─────────────────────────────────────────────────────────┘
```

### Extracting the Layout

```bash
# Find the root layout structure
grep -rn 'SidebarProvider\|SidebarInset\|AppShell\|DashboardLayout' \
  --include="*.tsx" --include="*.jsx" src/ | head -10

# Find sidebar width definitions
grep -rn 'sidebar-width\|SIDEBAR_WIDTH\|--sidebar' \
  --include="*.tsx" --include="*.css" src/

# Find content area constraints
grep -rn 'max-w-\|max-width\|container' --include="*.tsx" --include="*.jsx" src/ | head -20
```

---

## Sidebar Behavior

### Width States

| State | Width | Transition | Content Display |
|-------|-------|------------|-----------------|
| Expanded | 240-280px | 300ms ease-in-out | Icon + label + badge |
| Collapsed (icon-only) | 48-64px | 300ms ease-in-out | Icon only (tooltip on hover) |
| Mobile (hidden) | 0px | Sheet overlay slide | Full sidebar in sheet/drawer |

### Collapse Mechanism

```bash
# Find collapse implementation
grep -rn 'collapsible\|collapsed\|toggle.*sidebar\|useSidebar' \
  --include="*.tsx" --include="*.jsx" src/ | head -10
```

Document:
- **Trigger**: Button click, keyboard shortcut (Cmd+B), auto at breakpoint
- **Animation**: Width transition or instant toggle
- **Content shift**: Does main content expand or stay fixed?
- **Persistence**: Cookie, localStorage, or session state

### Mobile Behavior

| Approach | Description | Trigger |
|----------|-------------|---------|
| Sheet/Drawer | Sidebar slides in as overlay | Hamburger button |
| Bottom tabs | Replace sidebar with bottom navigation | Auto at breakpoint |
| Offcanvas | Sidebar pushes content off-screen | Swipe gesture |

---

## Content Area Layout

### Page Structure

```bash
# Find page layout patterns
grep -rn 'PageHeader\|PageTitle\|page-header\|content-area' \
  --include="*.tsx" --include="*.jsx" src/ | head -10
```

### Common Page Templates

**Dashboard page:**
```
Page Header (h1 + description + date picker)
├── Metric Cards (grid: 2-4 columns)
├── Charts (grid: 1-2 columns)
└── Data Table (full width)
```

**Settings page:**
```
Page Header (h1 + tabs)
├── Section 1 (heading + form group)
├── Section 2 (heading + form group)
└── Danger Zone (destructive section)
```

**Detail page:**
```
Page Header (breadcrumb + title + actions)
├── Tabs (sections)
└── Tab Content (varies per section)
```

---

## Responsive Breakpoints

### Extraction

```bash
# Tailwind config breakpoints
grep -A 10 'screens:' tailwind.config.*

# CSS media queries
grep -rn '@media.*min-width\|@media.*max-width' --include="*.css" src/ | \
  grep -oh '[0-9]*px' | sort -n | uniq
```


### Tailwind Responsive Prefix Syntax

Tailwind uses responsive prefixes that apply styles at a breakpoint AND above:

```
sm:grid-cols-2    -- applies at >=640px
md:grid-cols-3    -- applies at >=768px
lg:grid-cols-4    -- applies at >=1024px
```

**Detection:**
```bash
grep -roh 'sm:\|md:\|lg:\|xl:\|2xl:' --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

This tells you which breakpoints are actually used and how heavily.

### Standard Tailwind Breakpoints

| Name | Width | Layout Changes |
|------|-------|---------------|
| sm | 640px | Single column → 2 columns for metric cards |
| md | 768px | Sidebar collapse point (sidebar → sheet) |
| lg | 1024px | Sidebar expands, 3-column metric grid |
| xl | 1280px | 4-column metric grid, wider content |
| 2xl | 1536px | Max content width reached |

### What Changes at Each Breakpoint

Document for each breakpoint:

1. **Sidebar**: visible/hidden/collapsed/expanded
2. **Grid columns**: metric cards, chart grid, form layout
3. **Content max-width**: constrained or full-width
4. **Navigation**: sidebar → hamburger → bottom tabs
5. **Tables**: full → horizontal scroll → card view
6. **Typography**: scale adjustments (if any)

---

## Spacing Scales for Layout

### Page-Level Spacing

| Element | Spacing | Tailwind | Context |
|---------|---------|----------|---------|
| Content padding (x) | 16-32px | px-4 to px-8 | Main content horizontal padding |
| Content padding (y) | 16-24px | py-4 to py-6 | Main content vertical padding |
| Section gap | 24-32px | gap-6 to gap-8 | Between major page sections |
| Card gap | 16-24px | gap-4 to gap-6 | Between cards in a grid |
| Page header margin-bottom | 16-24px | mb-4 to mb-6 | Below page title |

### Component-Level Spacing

| Element | Internal Padding | Child Gap | Context |
|---------|-----------------|-----------|---------|
| Card | 24px (p-6) | 8-16px | Standard card |
| Dialog | 24px (p-6) | 16px | Modal content |
| Sidebar section | 8-12px | 2-4px | Nav group |
| Table cell | 8-16px (py-2 px-4) | — | Data rows |
| Form field | 0 | 8px | Label + input + error |

---

## Grid Systems

### CSS Grid Patterns

```bash
# Find grid usage
grep -roh 'grid-cols-[0-9]*\|grid-cols-\[.*\]' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

### Common Grid Layouts

| Pattern | Grid | Responsive | Used For |
|---------|------|-----------|----------|
| Metric cards | 1 → 2 → 4 cols | `grid-cols-1 md:grid-cols-2 xl:grid-cols-4` | KPI dashboard |
| Charts | 1 → 2 cols | `grid-cols-1 lg:grid-cols-2` | Analytics charts |
| Settings form | 1 col, max-w | `max-w-2xl mx-auto` | Form-heavy pages |
| Gallery | 1 → 2 → 3 cols | `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` | Card listings |

---

## Scroll Behavior

```bash
# Find scroll areas
grep -rn 'overflow-auto\|overflow-y-auto\|overflow-scroll\|ScrollArea' \
  --include="*.tsx" --include="*.jsx" src/ | head -10

# Find sticky elements
grep -rn 'sticky\|position:\s*sticky' --include="*.tsx" --include="*.css" src/ | head -10
```

### Document

- **Sidebar**: entire sidebar scrollable, or just the content area?
- **Main content**: page-level scroll or section-level?
- **Tables**: horizontal scroll on overflow, sticky header
- **Custom scrollbar**: styled scrollbar or native?

---

## Output Checklist

- [ ] Dashboard layout ASCII diagram with dimensions
- [ ] Sidebar width states (expanded, collapsed, mobile)
- [ ] Sidebar collapse mechanism and animation documented
- [ ] Content area max-width and padding documented
- [ ] Responsive breakpoints listed with layout changes
- [ ] Grid patterns documented with responsive variants
- [ ] Page templates documented (dashboard, settings, detail)
- [ ] Scroll behavior documented (sidebar, content, tables)
- [ ] Spacing scale for layout (page-level and component-level)
