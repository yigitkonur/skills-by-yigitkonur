# SaaS Dashboard-Specific Patterns

After shared components are documented, extract patterns unique to this specific dashboard product. These are the patterns that make THIS product feel different from every other SaaS tool.

---

## Why Dashboard Patterns Matter

Every SaaS dashboard shares the same components — buttons, inputs, tables, cards. What makes each product feel unique is how those components are composed into dashboard-specific patterns: how metrics are displayed, how data tables are configured, how the sidebar organizes navigation, how settings are laid out.

These patterns sit between "component" and "page." They're too complex to be a single component but too reusable to be a one-off page layout.

---

## Pattern Categories

### 1. Dashboard Layout

The top-level layout structure. Document:

```
+-----+------------------------------------+
|     |  Top bar (if any)                  |
|     +------------------------------------+
| S   |                                    |
| I   |  Main content area                 |
| D   |                                    |
| E   |  [how content is organized]        |
| B   |                                    |
| A   |                                    |
| R   |                                    |
|     +------------------------------------+
+-----+------------------------------------+
```

- Sidebar width (expanded/collapsed)
- Sidebar collapse breakpoint
- Sidebar collapse animation (instant, slide, push)
- Main content max-width (or full-width)
- Top bar height and content
- Content area padding
- How the grid shifts at responsive breakpoints
- Mobile navigation pattern (bottom tabs, hamburger, sheet)

### 2. Metric/KPI Displays

How the dashboard shows key numbers. Look for patterns like:

**Hero metric:**
```
+----------------------------------+
|  Total Revenue                    |
|  $2,847,392                       |
|  +12.5% from last month  ^       |
+----------------------------------+
```

**Metric grid:**
```
+----------+ +----------+ +----------+ +----------+
| Users    | | Revenue  | | Orders   | | Growth   |
| 12,847   | | $284K    | | 1,293    | | +14.2%   |
| +5.2%  ^ | | +12.1% ^ | | -2.3% v | | +1.8%  ^ |
+----------+ +----------+ +----------+ +----------+
```

Document for each metric pattern:
- Layout (grid columns, gap)
- Number formatting (currency, percentage, abbreviation)
- Trend indicator (arrow, badge, color-coded)
- Comparison period text
- Sparkline/mini chart if present
- Loading/skeleton state
- Empty state (no data yet)

### 3. Data Tables

The most complex dashboard pattern. Document:

**Table structure:**
- Header: sticky, background, sort indicators, column alignment
- Rows: height, padding, hover highlight, striped/plain, click behavior
- Cells: text alignment, truncation, monospace for numbers
- Borders: between rows, between columns, outer border
- Selection: checkbox column, selected row highlight, bulk action bar

**Table features:**
- Sort: indicator icon (arrows), active sort highlight
- Filter: filter bar position, active filter badges, clear all
- Search: inline search, search input position and styling
- Pagination: position (bottom), style (numbered/prev-next), page size selector
- Bulk actions: bar that appears on selection, action buttons, selection count
- Empty state: what shows when filtered to zero results
- Loading state: skeleton rows, loading spinner position
- Column resize: drag handle visibility and behavior
- Responsive: what happens on mobile (horizontal scroll, card view, hidden columns)

### 4. Settings Pages

How the app organizes preferences and configuration:

**Section pattern:**
```
+--------------------------------------------------+
| Section Title                                      |
| Description text explaining what this section does |
|                                                    |
| +----------------------------------------------+  |
| | Setting label          [Toggle]              |  |
| | Helper text explaining this setting          |  |
| +----------------------------------------------+  |
| | Setting label          [Select v]            |  |
| | Helper text                                  |  |
| +----------------------------------------------+  |
|                                                    |
|                            [Save changes]          |
+--------------------------------------------------+
```

Document:
- Section grouping (visual separator, heading style)
- Label + control + description layout (horizontal vs. vertical)
- Save pattern (auto-save, explicit save button, per-section vs. per-page)
- Form validation (inline errors, toast feedback)
- Dangerous settings (destructive zone styling, confirmation dialog)
- Plan/billing display (current plan card, upgrade CTA, usage meters)

### 5. Search/Command Patterns

**Command palette (Cmd+K):**
```
+------------------------------------------+
| > Search commands...                     |
+------------------------------------------+
| Recent                                    |
|   Dashboard                              |
|   Settings                               |
+------------------------------------------+
| Navigation                               |
|   > Dashboard         Cmd+1             |
|   > Analytics          Cmd+2             |
|   > Settings           Cmd+,             |
+------------------------------------------+
| Actions                                   |
|   + Create new project                   |
|   + Invite team member                   |
+------------------------------------------+
```


#### Command Palette Detection (cmdk)

Many modern SaaS dashboards use `cmdk` for their command palette:

```bash
grep '"cmdk"' package.json
grep -rn 'CommandDialog\|CommandInput\|CommandList' --include="*.tsx" --include="*.jsx" src/ | head -10
```

When documenting a cmdk-based command palette:

| Element | What to Document |
|---------|-----------------|
| `CommandDialog` | Backdrop overlay opacity, dialog width/max-height, border-radius, animation |
| `CommandInput` | Search icon, placeholder text, height, border treatment, font-size |
| `CommandList` | Max-height, overflow behavior, padding |
| `CommandGroup` | Group heading style (text-xs, muted-foreground, uppercase tracking) |
| `CommandItem` | Height, padding, icon-to-text gap, active/selected highlight, cursor |
| `CommandEmpty` | Empty state message style |
| `CommandShortcut` | Keyboard hint badge style (text-xs, muted, right-aligned) |

Document:
- Trigger (keyboard shortcut, button in top bar)
- Search input styling
- Result grouping and group labels
- Result item: icon, title, description, keyboard shortcut hint
- Active/selected item highlight
- Empty state
- Loading state (searching)
- Animation (open/close)
- Backdrop overlay opacity

### 6. Onboarding/Empty States

**First-run empty state:**
```
+--------------------------------------------------+
|                                                    |
|              [Illustration or icon]                |
|                                                    |
|           No projects yet                          |
|    Create your first project to get started        |
|                                                    |
|              [Create project]                      |
|                                                    |
+--------------------------------------------------+
```

Document:
- Icon/illustration style (line art, filled, custom illustration)
- Title and description text styling
- CTA button variant and size
- Layout (centered, offset, with sidebar context)
- Onboarding checklists (if any): progress indicator, step styling, completion animation

### 7. Multi-Tenant Patterns

**Workspace/org switcher:**
```
+---------------------------+
| [Logo] Acme Corp   v     |
+---------------------------+
| Acme Corp          [check]|
| Personal              |
| +  Create workspace       |
+---------------------------+
```

Document:
- Trigger location (sidebar header, top bar)
- Current workspace display (logo, name, plan badge)
- Dropdown content (workspace list, current indicator, create action)
- Workspace switching behavior (page reload, client-side switch)
- Context that changes with workspace (sidebar items, available features)

### 8. Notification/Activity Patterns

**Notification panel:**
```
+---------------------------+
| Notifications  [Mark all] |
+---------------------------+
| [avatar] User commented   |
| on Project Alpha  2h ago  |
|                           |
| [avatar] Deploy succeeded |
| Production  •  5h ago     |
+---------------------------+
```

Document:
- Trigger (bell icon, badge count)
- Panel type (dropdown, sheet, page)
- Notification item: avatar, title, description, timestamp, read/unread indicator
- Grouping (by date, by type)
- Empty state
- Mark as read behavior

### 9. Filter/Toolbar Patterns

**Filter bar above a data view:**
```
+--------------------------------------------------+
| [Search...] [Status v] [Date range v] [+ Filter] |
+--------------------------------------------------+
| Active filters: Status: Active x  Date: Last 7d x |
+--------------------------------------------------+
```

Document:
- Filter bar position (above content, in sidebar, in header)
- Filter types: dropdown, date range picker, search input, multi-select
- Active filter display: badges, inline chips, count
- Clear filters action
- Filter persistence (URL params, local storage, session)

### 10. Form/CRUD Patterns

**Create/edit form:**
```
+--------------------------------------------------+
| Create Project                          [x Close] |
+--------------------------------------------------+
|                                                    |
| Project name                                       |
| [                                            ]     |
|                                                    |
| Description                                        |
| [                                            ]     |
| [                                            ]     |
|                                                    |
| Team                                               |
| [Select team                              v ]     |
|                                                    |
+--------------------------------------------------+
|                    [Cancel]  [Create project]      |
+--------------------------------------------------+
```

Document:
- Form container (dialog, page, sheet)
- Field layout (stacked, grid, sections)
- Label position (above, inline, floating)
- Required field indicator (asterisk, text)
- Error display (inline below field, toast, summary at top)
- Submit button position (bottom-right, sticky footer, inline)
- Cancel behavior (dialog close, navigate back)
- Loading state during submission

### 11. AI & Chat Patterns

Modern SaaS products increasingly embed AI features. If the dashboard includes chat, AI assistance, or generative features, document these specialized patterns:

**Message Thread:**
- **Message bubbles**: User vs assistant styling (alignment, background, border)
- **Streaming state**: How text appears during generation (cursor? fade-in? typewriter?)
- **Markdown rendering**: How code blocks, tables, lists render inside messages
- **Branching/regeneration**: Can users navigate between alternative responses?
- **Attachment system**: File upload, image preview, drag-and-drop
- **Copy/feedback actions**: Thumbs up/down, copy button, retry

**Prompt Input:**
- **Auto-growing textarea**: Does it expand with content? What's the max height?
- **Attachment preview**: How are files shown before sending?
- **Submit button states**: Idle → Sending → Stop (icon transitions)
- **Model/context selector**: Dropdown for AI model or context selection
- **Command shortcuts**: Slash commands, @ mentions, # references

**Tool Calls & Actions:**
- **Collapsed/expanded tool display**: How are tool calls shown (card? inline?)
- **Status indicators**: Pending → Running → Success/Error (with animations)
- **Code execution blocks**: Terminal-style output display
- **File diff display**: Side-by-side or inline diff visualization
- **Web search results**: Source cards, citation inline

**AI-Specific Loading States:**
- **Thinking/reasoning indicator**: Shimmer, pulsing dots, "Thinking..." text
- **Streaming skeleton**: Progressive content reveal
- **Checkpoint indicators**: Progress markers in long operations
- **Queue position**: "You're #3 in queue" display

### 12. Desktop & Platform Patterns

If the dashboard is a desktop app (Electron, Tauri) or has platform-specific features:

**Window Chrome:**
- **Title bar**: Custom vs native, drag region, traffic light buttons
- **Window controls**: Minimize, maximize, close — custom styled?
- **Menu bar**: Native menu or in-app menu bar?

**Theme System:**
- **Theme injection**: How are CSS variables loaded? (JS runtime? CSS @import?)
- **Theme switching**: Toggle mechanism, persistence (localStorage? cookie?)
- **Platform-specific themes**: Does the desktop app have a different theme than web?
- **Flash prevention**: Does a theme boot script run before render?

**Terminal Integration:**
- **Terminal emulator styling**: Font, line-height, cursor style, selection
- **Scrollbar overrides**: Custom scrollbar in terminal panes?
- **ANSI color mapping**: How terminal colors map to the design system

**Tray & Status:**
- **System tray icon**: Active vs idle states
- **Status bar**: Bottom bar with connection status, sync indicators
- **Notifications**: Native OS notifications vs in-app toast

---

## Output Format

Create a directory named after the product (e.g., `[product-name]-patterns/`) and write one `.md` file per pattern found. Use the component template structure but adapt it for patterns — patterns are compositions, so focus on:

- Overall layout with ASCII diagram
- Component composition (what shared components are used where)
- Spacing between composed elements
- Responsive behavior
- States (empty, loading, error, populated)
- Dark mode differences

---

## Data Visualization Patterns (Enhanced)

Go deeper than basic chart colors. Document the COMPLETE visualization system:

### Chart System
- **Chart container**: ResponsiveContainer wrapper, aspect ratio, padding
- **Axis styling**: Tick labels (font size, color, rotation), grid lines (color, dash pattern)
- **Color system**: Per-series CSS variables (`--color-{key}`), light/dark palettes
- **Tooltip styling**: Background, border, shadow, padding, arrow
- **Legend styling**: Position, spacing, icon shape, text style
- **Recharts/D3 overrides**: Specific CSS selectors for chart library customization
- **Empty chart state**: What shows when there's no data?

### Data Table Patterns (Deep)
Document beyond basic styling:
- **Column types**: Text, number, date, status badge, action buttons, avatar, link
- **Sort indicators**: Icon style, active vs inactive color, animation
- **Filter bar**: Position (above table? sidebar?), filter chip styling, clear all
- **Row selection**: Checkbox column, selected row highlight, bulk action bar
- **Pagination**: Position, style (numbered vs prev/next), per-page selector
- **Empty state**: Message, illustration, CTA button
- **Loading state**: Skeleton rows, shimmer effect, count of skeleton rows
- **Sticky header**: Shadow on scroll, background on overlap
- **Column resizing**: Drag handle style, minimum width constraints
- **Row expansion**: Expandable row detail, indent level, toggle icon

### Metric Cards
- **Number formatting**: Locale-aware, abbreviated (1.2K, 3.5M), currency
- **Trend indicators**: Up/down arrow, color (green/red), percentage change
- **Sparkline integration**: Mini chart inside card, stroke/fill style
- **Comparison period**: "vs last week", "MoM", time period selector
- **KPI grouping**: Grid of metric cards, responsive columns

---

## Mega-Component Documentation

Some dashboard components are mega-components with 10-20+ sub-parts. These need special treatment.

### How to Identify Mega-Components
- Sidebar with 15+ sub-components (SidebarGroup, SidebarMenuItem, SidebarMenuAction, etc.)
- Data table with 8+ sub-components (Table, Header, Body, Row, Cell, Footer, Caption, etc.)
- Form layout with 5+ sub-components (Form, FormField, FormLabel, FormMessage, FormItem, etc.)
- Command palette with 5+ sub-components (Command, CommandInput, CommandList, CommandGroup, CommandItem, etc.)

### Documentation Strategy for Mega-Components
1. **Hierarchy diagram first** — show the full component tree with nesting
2. **Context/provider** — document the context API (state, callbacks)
3. **Each sub-component** — name, purpose, CSS, props, constraints
4. **Render modes** — desktop vs mobile, collapsed vs expanded, etc.
5. **Composition rules** — which sub-components are required, which optional
6. **CSS variables** — mega-components often define their own CSS variables (--sidebar-width, etc.)
7. **Keyboard shortcuts** — mega-components often have keyboard navigation
8. **Persistence** — state persistence (cookie, localStorage, URL params)

### Example: Sidebar Hierarchy
```
SidebarProvider (context: open/closed state, toggle function)
└── Sidebar (container: fixed position, width transitions)
    ├── SidebarHeader (sticky top area)
    ├── SidebarContent (scrollable middle)
    │   └── SidebarGroup (section container)
    │       ├── SidebarGroupLabel (section title, text-xs)
    │       ├── SidebarGroupAction (section-level action button)
    │       └── SidebarGroupContent
    │           └── SidebarMenu (list container)
    │               └── SidebarMenuItem (item wrapper)
    │                   ├── SidebarMenuButton (clickable item, isActive prop)
    │                   ├── SidebarMenuAction (hover-reveal action)
    │                   ├── SidebarMenuBadge (count/status indicator)
    │                   └── SidebarMenuSub (nested sub-menu)
    │                       └── SidebarMenuSubItem
    │                           └── SidebarMenuSubButton
    ├── SidebarSeparator (horizontal rule)
    ├── SidebarFooter (sticky bottom area)
    └── SidebarRail (click/drag edge for toggle)
└── SidebarInset (main content area, respects sidebar width)
```

---


### Chart and Visualization Wrappers

```bash
grep '"recharts"' package.json && echo "Recharts detected"
grep -rn 'ChartContainer\|ChartTooltip' --include="*.tsx" --include="*.jsx" src/ | head -20
grep -rn 'chart-1\|--color-' --include="*.css" --include="*.tsx" src/ | head -10
```

For each chart type, document:
1. **Container**: wrapper, aspect ratio, padding
2. **Color system**: per-series CSS variables, light/dark palettes
3. **Tooltip**: background, border, shadow, padding, content formatter
4. **Legend**: position, spacing, icon shape, text style
5. **Axis styling**: tick label font-size, color, grid line color/dash
6. **Empty state**: what renders when data is empty or loading


---

## Discovery Checklist

Before marking this phase complete:

- [ ] Dashboard layout structure documented (sidebar + content proportions)
- [ ] All metric/KPI display patterns found and documented
- [ ] Data table configuration documented (all features)
- [ ] Settings page layout documented (if settings exist)
- [ ] Command palette/search documented (if present)
- [ ] Empty states documented (at least 3 different contexts)
- [ ] Multi-tenant patterns documented (if applicable)
- [ ] Notification patterns documented (if present)
- [ ] Filter/toolbar patterns documented (if present)
- [ ] Form/CRUD patterns documented (create, edit, delete flows)
- [ ] AI/Chat patterns documented (if AI features present)
- [ ] Desktop/Platform patterns documented (if desktop app)
- [ ] Data visualization patterns documented in depth (charts, tables, metrics)
- [ ] Mega-components identified and hierarchy-documented
- [ ] Pattern composition documented (page templates)

---

## How Patterns Compose

Document how dashboard-specific patterns combine into full page layouts:

### Dashboard Page Template
```
┌──────────────┬────────────────────────────────────────┐
│              │ Top Bar (breadcrumb, search, user menu) │
│   Sidebar    ├────────────────────────────────────────┤
│   (nav +     │ Page Header (title, description, CTA)  │
│   workspace  ├────────────────────────────────────────┤
│   switcher)  │ Content Area                            │
│              │ ┌─────────┬─────────┬─────────┐        │
│              │ │ Metric  │ Metric  │ Metric  │        │
│              │ └─────────┴─────────┴─────────┘        │
│              │ ┌─────────────────────────────┐        │
│              │ │ Data Table (with filters)    │        │
│              │ │ ...                          │        │
│              │ └─────────────────────────────┘        │
└──────────────┴────────────────────────────────────────┘
```

### Settings Page Template
```
┌──────────────┬────────────────────────────────────────┐
│              │ Settings Header (tabs: General, Team)   │
│   Sidebar    ├────────────────────────────────────────┤
│              │ Form Section 1                          │
│              │ ┌─────────────────────────────┐        │
│              │ │ Label + Input                │        │
│              │ │ Label + Select               │        │
│              │ │ Label + Toggle               │        │
│              │ └─────────────────────────────┘        │
│              │ Save Bar (sticky bottom, cancel + save) │
└──────────────┴────────────────────────────────────────┘
```
