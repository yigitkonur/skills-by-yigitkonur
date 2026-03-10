# Tool API Reference

> **Definitive reference** for both daisyUI Blueprint MCP tools — parameters, syntax, every available key, output formats, calling patterns, and cross-tool workflows.
>
> See also: `references/component-catalog.md` for component class details.

---

## Tool 1: `daisyui-blueprint-daisyUI-Snippets`

Retrieve component code, layouts, templates, and theme configuration from the **500+ snippet library** for **daisyUI 5**.

Returns plain markdown with fenced HTML code blocks — no JSON wrapping, no CSS (except themes). Each snippet is self-contained and can be dropped directly into any daisyUI 5 project.

---

### Critical Syntax Rule

```jsonc
// ✅ CORRECT — Nested object syntax ONLY
{ "components": { "button": true, "card": true } }

// ❌ WRONG — Arrays will silently fail
{ "snippets": ["components/button", "components/card"] }
{ "components": ["button", "card"] }
```

Every parameter is an **object** where keys are snippet names and values are `true`. Multiple categories can be mixed in a **single call**.

---

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `components` | `object` | No | Component reference docs (class names + syntax + example list) |
| `component-examples` | `object` | No | Specific copy-paste HTML examples |
| `layouts` | `object` | No | Page layout structures with `<!-- content here -->` placeholders |
| `templates` | `object` | No | Full page HTML composing multiple components |
| `themes` | `object` | No | CSS configuration and color system reference (not HTML) |

**Mixed-category example (single call):**

```json
{
  "components": { "navbar": true, "card": true },
  "component-examples": { "card.pricing-card": true },
  "layouts": { "top-navbar": true },
  "templates": { "dashboard": true },
  "themes": { "colors": true }
}
```

---

### Category: `components`

**What it returns:** Class reference table + HTML syntax skeleton + list of available example names. **No ready-to-use code** — use `component-examples` for that.

**Token budget:** ~200–500 tokens per component.

#### Output Structure

```markdown
---
img: https://img.daisyui.com/images/components/{name}.webp
docs: https://daisyui.com/components/{name}/
width: 816
height: 480
---

# {Component Name}

{Brief description}

## Class Names

| Class name | Type | Description |
|------------|------|-------------|
| `btn` | COMPONENT | Required base class |
| `btn-primary` | COLOR | Primary color variant |
| `btn-outline` | STYLE | Outline style |
| `btn-sm` | SIZE | Small size |
| `btn-wide` | MODIFIER | Wide modifier |
| `btn-active` | BEHAVIOR | Active state |

## Syntax

```html
<button class="btn {MODIFIER}">{CONTENT}</button>
```

## Examples

- `button.button`
- `button.button-with-icon`
- `button.outline-buttons`
- ...
```

#### Class Name Type Reference

| Type | Description | Example |
|------|-------------|---------|
| **COMPONENT** | Required base class for the component | `btn`, `card`, `navbar` |
| **PART** | Child/sub-element of a component | `card-body`, `card-title`, `navbar-start` |
| **STYLE** | Visual style variant | `btn-outline`, `btn-dash`, `btn-soft`, `btn-ghost` |
| **BEHAVIOR** | Interactive behavior modifier | `collapse-open`, `collapse-close` |
| **COLOR** | Semantic color variant | `btn-primary`, `alert-error`, `badge-success` |
| **SIZE** | Size variant | `btn-xs`, `btn-sm`, `btn-lg`, `btn-xl` |
| **PLACEMENT** | Position/alignment | `dropdown-top`, `dropdown-end`, `toast-start` |
| **DIRECTION** | Layout direction | `footer-horizontal`, `stats-vertical` |
| **MODIFIER** | Appearance/layout modifier | `btn-wide`, `btn-block`, `btn-square`, `btn-circle` |
| **VARIANT** | Conditional style prefix (daisyUI 5) | `is-drawer-close:`, `is-drawer-open:` |

#### Variant Prefixes (daisyUI 5 Feature)

CSS-only conditional variants — **no JavaScript required**:

```html
<span class="is-drawer-close:hidden">Menu Label</span>
<div class="is-drawer-close:w-16 is-drawer-open:w-64">Sidebar</div>
```

#### All 64 Available Component Keys

| Category | Keys |
|----------|------|
| **Navigation** | `navbar`, `menu`, `drawer`, `footer`, `dock`, `breadcrumbs` |
| **Data Display** | `card`, `table`, `stat`, `list`, `timeline`, `chat`, `avatar`, `badge` |
| **Actions** | `button`, `dropdown`, `modal`, `swap`, `fab` |
| **Form Inputs** | `toggle`, `checkbox`, `radio`, `input`, `textarea`, `select`, `range`, `file-input` |
| **Feedback** | `alert`, `toast`, `loading`, `progress`, `radial-progress`, `skeleton`, `status`, `steps`, `rating` |
| **Content** | `accordion`, `collapse`, `carousel`, `diff`, `divider`, `indicator`, `join`, `kbd`, `label`, `link`, `mask`, `stack`, `tab`, `countdown`, `pagination` |
| **Form Helpers** | `fieldset`, `label`, `filter`, `validator`, `calendar` |
| **Presentation** | `hero`, `hover-3d`, `hover-gallery`, `text-rotate`, `theme-controller` |
| **Mockups** | `mockup-browser`, `mockup-code`, `mockup-phone`, `mockup-window` |

**Alphabetical full list:**

```
accordion       alert           avatar          badge           breadcrumbs
button          calendar        card            carousel        chat
checkbox        collapse        countdown       diff            divider
dock            drawer          dropdown        fab             fieldset
file-input      filter          footer          hero            hover-3d
hover-gallery   indicator       input           join            kbd
label           link            list            loading         mask
menu            mockup-browser  mockup-code     mockup-phone    mockup-window
modal           navbar          pagination      progress        radial-progress
radio           range           rating          select          skeleton
stack           stat            status          steps           swap
tab             table           text-rotate     textarea        theme-controller
timeline        toast           toggle          validator
```

---

### Category: `component-examples`

**What it returns:** Ready-to-use, copy-paste HTML code blocks. Each example is self-contained — no external CSS beyond daisyUI classes, no JavaScript (CSS-only patterns), SVG icons inlined.

**Token budget:** ~100–300 tokens per example.

**Key format:** `"component-name.example-name": true`

**Naming pattern:** Component name, dot, kebab-case example descriptor. Example names are descriptive of the variant shown.

#### Output Structure

```markdown
## button.button-with-icon

```html
<button class="btn">
  <svg ...>...</svg>
  Button
</button>
<button class="btn btn-primary">
  Button
  <svg ...>...</svg>
</button>
```
```

Multiple variants are often shown in a single example.

#### Example Counts by Component

| Component | # | Component | # | Component | # |
|-----------|---|-----------|---|-----------|---|
| accordion | 4 | alert | 10 | avatar | 9 |
| badge | 11 | breadcrumbs | 3 | button | 18 |
| calendar | 3 | card | 15 | carousel | 9 |
| chat | 5 | checkbox | 7 | collapse | 11 |
| countdown | 7 | divider | 2 | dock | 7 |
| drawer | 7 | dropdown | 18 | fab | 11 |
| fieldset | 5 | file-input | 6 | filter | 3 |
| footer | 11 | hero | 5 | hover-3d | 1 |
| hover-gallery | 2 | indicator | 15 | input | 18 |
| join | 6 | kbd | 7 | label | 6 |
| link | 9 | loading | 7 | mask | 16 |
| menu | 22 | modal | 8 | navbar | 9 |
| pagination | 6 | progress | 10 | radial-progress | 5 |
| radio | 12 | range | 11 | rating | 8 |
| select | 14 | skeleton | 4 | stack | 7 |
| stat | 6 | status | 5 | steps | 7 |
| swap | 6 | tab | 13 | table | 9 |
| text-rotate | 1 | textarea | 6 | theme-controller | 10 |
| timeline | 16 | toast | 11 | toggle | 8 |
| validator | 11 | | | | |

#### Complete List of All Component-Example Keys

##### accordion (4)

```
accordion.accordion-using-radio-inputs
accordion.accordion-with-arrow-icon
accordion.accordion-with-plus-minus-icon
accordion.using-accordion-and-join-together
```

##### alert (10)

```
alert.alert
alert.alert-dash-style
alert.alert-outline-style
alert.alert-soft-style
alert.alert-with-buttons-responsive
alert.alert-with-title-and-description
alert.error-color
alert.info-color
alert.success-color
alert.warning-color
```

##### avatar (9)

```
avatar.avatar
avatar.avatar-group
avatar.avatar-group-with-counter
avatar.avatar-in-custom-sizes
avatar.avatar-placeholder
avatar.avatar-rounded
avatar.avatar-with-mask
avatar.avatar-with-presence-indicator
avatar.avatar-with-ring
```

##### badge (11)

```
badge.badge
badge.badge-ghost
badge.badge-in-a-button
badge.badge-in-a-text
badge.badge-sizes
badge.badge-with-colors
badge.badge-with-dash-style
badge.badge-with-icon
badge.badge-with-outline-style
badge.badge-with-soft-style
badge.empty-badge
badge.neutral-badge-with-outline-or-dash-style
```

##### breadcrumbs (3)

```
breadcrumbs.breadcrumbs
breadcrumbs.breadcrumbs-with-icons
breadcrumbs.breadcrumbs-with-max-width
```

##### button (18)

```
button.active-buttons
button.button
button.button-block
button.button-sizes
button.button-with-icon
button.button-with-loading-spinner
button.buttons-colors
button.buttons-ghost-and-button-link
button.buttons-with-any-html-tags-like-checkbox-radio-etc
button.dash-buttons
button.disabled-buttons
button.login-with-social-media-auth-buttons
button.neutral-button-with-outline-or-dash-style
button.outline-buttons
button.responsive-button
button.soft-buttons
button.square-button-and-circle-button
button.wide-button
```

##### calendar (3)

```
calendar.cally-calendar-example
calendar.cally-date-picker-example
calendar.pikaday-cdn-example
```

##### card (15)

```
card.card
card.card-sizes
card.card-with-a-card-border
card.card-with-a-dash-border
card.card-with-action-on-top
card.card-with-badge
card.card-with-bottom-image
card.card-with-centered-content-and-paddings
card.card-with-custom-color
card.card-with-image-on-side
card.card-with-image-overlay
card.card-with-no-image
card.centered-card-with-neutral-color
card.pricing-card
card.responsive-card-vertical-on-small-screen-horizontal-on-large-screen
```

##### carousel (9)

```
carousel.carousel-with-full-width-items
carousel.carousel-with-half-width-items
carousel.carousel-with-indicator-buttons
carousel.carousel-with-nextprev-buttons
carousel.full-bleed-carousel
carousel.snap-to-center
carousel.snap-to-end
carousel.snap-to-start-default
carousel.vertical-carousel
```

##### chat (5)

```
chat.chat-bubble-with-colors
chat.chat-start-and-chat-end
chat.chat-with-header-and-footer
chat.chat-with-image
chat.chat-with-image-header-and-footer
```

##### checkbox (7)

```
checkbox.checkbox
checkbox.checkbox-with-custom-colors
checkbox.colors
checkbox.disabled
checkbox.indeterminate
checkbox.sizes
checkbox.with-fieldset-and-label
```

##### collapse (11)

```
collapse.collapse-using-details-and-summary-tag
collapse.collapse-with-checkbox
collapse.collapse-with-focus
collapse.custom-colors-for-collapse-that-works-with-checkbox
collapse.custom-colors-for-collapse-that-works-with-focus
collapse.force-close
collapse.force-open
collapse.moving-collapse-icon-to-the-start
collapse.with-arrow-icon
collapse.with-arrow-plusminus-icon
collapse.without-border-and-background-color
```

##### countdown (7)

```
countdown.clock-countdown
countdown.clock-countdown-with-colons
countdown.countdown
countdown.in-boxes
countdown.large-text-with-2-digits
countdown.large-text-with-labels
countdown.large-text-with-labels-under
```

##### diff (2)

```
diff.diff
diff.diff-text
```

##### divider (7)

```
divider.divider
divider.divider-horizontal
divider.divider-in-different-positions
divider.divider-in-different-positions-horizontal
divider.divider-with-colors
divider.divider-with-no-text
divider.responsive-lgdivider-horizontal
```

##### dock (7)

```
dock.dock
dock.dock-extra-large-size
dock.dock-extra-small-size
dock.dock-large-size
dock.dock-medium-size
dock.dock-small-size
dock.dock-with-custom-colors
```

##### drawer (7)

```
drawer.drawer-sidebar
drawer.drawer-sidebar-that-opens-from-right-side-of-page
drawer.example-this-sidebar-is-always-visible-on-large-screen-can-be-toggled-on-small-screen
drawer.example-this-sidebar-is-always-visible-when-its-close-we-only-see-iocns-when-its-open-we-see-icons-and-text
drawer.icon-only-drawer-sidebar-when-its-closed-using-is-drawer-close-and-is-drawer-open-variants
drawer.navbar-menu-for-desktop-sidebar-drawer-for-mobile
drawer.responsive-sidebar-is-always-visible-on-large-screen-can-be-toggled-on-small-screen
```

##### dropdown (18)

```
dropdown.card-as-dropdown
dropdown.dropdown-aligns-to-center-of-button-horizontally
dropdown.dropdown-aligns-to-end-of-button-horizontally
dropdown.dropdown-aligns-to-start-of-button-horizontally
dropdown.dropdown-bottom-default
dropdown.dropdown-bottom-default-aligns-to-center-of-button-horizontally
dropdown.dropdown-bottom-default-aligns-to-end-of-button-vertically
dropdown.dropdown-in-navbar
dropdown.dropdown-left
dropdown.dropdown-left-aligns-to-center-of-button-vertically
dropdown.dropdown-left-aligns-to-end-of-button-vertically
dropdown.dropdown-menu
dropdown.dropdown-on-hover
dropdown.dropdown-right
dropdown.dropdown-right-aligns-to-center-of-button-vertically
dropdown.dropdown-right-aligns-to-end-of-button-vertically
dropdown.dropdown-top
dropdown.dropdown-top-aligns-to-center-of-button-horizontally
dropdown.dropdown-top-aligns-to-end-of-button-horizontally
dropdown.dropdown-using-details-and-summary
dropdown.dropdown-using-popover-api-and-anchor-positioning
dropdown.force-open
dropdown.helper-dropdown
```

##### fab (11)

```
fab.a-single-fab-floating-action-button
fab.fab-and-flower-speed-dial-with-svg-icons
fab.fab-and-flower-speed-dial-with-tooltip
fab.fab-and-speed-dial-vertical
fab.fab-and-speed-dial-with-labels
fab.fab-and-speed-dial-with-labels-and-fab-close-button
fab.fab-and-speed-dial-with-labels-and-fab-main-action-button
fab.fab-and-speed-dial-with-rectangle-buttons
fab.fab-and-speed-dial-with-svg-icons
fab.fab-flower-and-speed-dial
```

##### fieldset (5)

```
fieldset.fieldset-fieldset-legend-and-label
fieldset.fieldset-with-background-and-border
fieldset.fieldset-with-multiple-inputs
fieldset.fieldset-with-multiple-join-items
fieldset.login-form-with-fieldset
```

##### file-input (6)

```
file-input.disabled
file-input.file-input
file-input.file-input-ghost
file-input.primary-color
file-input.sizes
file-input.with-fieldset-and-label
```

##### filter (3)

```
filter.filter-using-html-form-checkboxes-and-a-reset-button
filter.filter-using-html-form-radio-buttons-and-reset-button
filter.filter-without-html-form
```

##### footer (11)

```
footer.centered-footer-with-logo-and-social-icons
footer.centered-footer-with-social-icons
footer.footer-vertical-by-default-horizontal-for-sm-and-up
footer.footer-with-2-rows
footer.footer-with-a-form
footer.footer-with-a-logo-section
footer.footer-with-copyright-text
footer.footer-with-copyright-text-and-social-icons
footer.footer-with-links-and-social-icons
footer.footer-with-logo-and-social-icons
footer.two-footer
```

##### hero (5)

```
hero.centered-hero
hero.hero-with-figure
hero.hero-with-figure-but-reverse-order
hero.hero-with-form
hero.hero-with-overlay-image
```

##### hover-3d (1)

```
hover-3d.
```

##### hover-gallery (2)

```
hover-gallery.hover-gallery
hover-gallery.hover-gallery-in-a-card
```

##### indicator (15)

```
indicator.a-button-as-an-indicator-for-a-card
indicator.badge-as-indicator
indicator.for-an-input
indicator.for-avatar
indicator.for-button
indicator.for-tab
indicator.in-center-of-an-image
indicator.indicator-bottom-indicator-center
indicator.indicator-bottom-indicator-end-default
indicator.indicator-bottom-indicator-start
indicator.indicator-middle-indicator-center
indicator.indicator-middle-indicator-end-default
indicator.indicator-middle-indicator-start
indicator.indicator-top-default-indicator-center
indicator.indicator-top-default-indicator-end-default
indicator.indicator-top-default-indicator-start
indicator.multiple-indicators
indicator.responsive
indicator.status-indicator
```

##### input (18)

```
input.date-input
input.datetime-local-input
input.disabled
input.email-input-with-icon-and-validator
input.email-input-with-icon-validator-button-join
input.ghost-style
input.input-colors
input.number-input-with-validator
input.password-input-with-icon-and-validator
input.search-input-with-icon
input.sizes
input.telephone-number-input-with-icon-and-validator
input.text-input
input.text-input-with-data-list-suggestion
input.text-input-with-text-label-inside
input.time-input
input.url-with-icon-and-validator
input.username-text-input-with-icon-and-validator
input.with-fieldset-and-fieldset-legend
```

##### join (6)

```
join.custom-border-radius
join.group-items-vertically
join.join
join.join-radio-inputs-with-btn-style
join.responsive-its-vertical-on-small-screen-and-horizontal-on-large-screen
join.with-extra-elements-in-the-group
```

##### kbd (7)

```
kbd.a-full-keyboard
kbd.arrow-keys
kbd.function-keys
kbd.in-text
kbd.kbd
kbd.kbd-sizes
kbd.key-combination
```

##### label (6)

```
label.floating-label
label.floating-label-with-different-sizes
label.label-for-date-input
label.label-for-input
label.label-for-input-at-the-end
label.label-for-select
```

##### link (9)

```
link.accent-color
link.error-color
link.info-color
link.link
link.primary-color
link.secondary-color
link.show-underline-only-on-hover
link.success-color
link.warning-color
```

##### list (3)

```
list.list-second-column-grows-default
list.list-third-column-grows
list.list-third-column-wraps-to-next-row
```

##### loading (7)

```
loading.loading-ball
loading.loading-bars
loading.loading-dots
loading.loading-infinity
loading.loading-ring
loading.loading-spinner
loading.loading-with-colors
```

##### mask (16)

```
mask.circle
mask.decagon
mask.diamond
mask.heart
mask.hexagon
mask.hexagon-2-horizontal-hexagon
mask.pentagon
mask.square
mask.squircle
mask.star
mask.star-2-bold-star
mask.triangle-2-pointing-down
mask.triangle-3-pointing-left
mask.triangle-4-pointing-right
mask.triangle-pointing-top
```

##### menu (22)

```
menu.collapsible-submenu
menu.collapsible-submenu-that-works-with-class-names
menu.collapsible-with-submenu-responsive
menu.file-tree
menu.horizontal-menu
menu.horizontal-submenu
menu.mega-menu-with-submenu-responsive
menu.menu
menu.menu-sizes
menu.menu-with-active-item
menu.menu-with-disabled-items
menu.menu-with-icon-only
menu.menu-with-icon-only-horizontal
menu.menu-with-icon-only-horizontal-with-tooltip
menu.menu-with-icon-only-with-tooltip
menu.menu-with-icons
menu.menu-with-icons-and-badge-responsive
menu.menu-with-title
menu.menu-with-title-as-a-parent
menu.menu-without-padding-and-border-radius
menu.responsive-vertical-on-small-screen-horizontal-on-large-screen
menu.submenu
```

##### mockup-browser (2)

```
mockup-browser.browser-mockup-with-background-color
mockup-browser.browser-mockup-with-border
```

##### mockup-code (6)

```
mockup-code.highlighted-line
mockup-code.long-line-will-scroll
mockup-code.mockup-code-with-line-prefix
mockup-code.multi-line
mockup-code.with-color
mockup-code.without-prefix
```

##### mockup-phone (2)

```
mockup-phone.iphone-mockup
mockup-phone.with-color-and-wallpaper
```

##### mockup-window (2)

```
mockup-window.window-mockup-with-background-color
mockup-window.window-mockup-with-border
```

##### modal (8)

```
modal.dialog-modal
modal.dialog-modal-closes-when-clicked-outside
modal.dialog-modal-with-a-close-button-at-corner
modal.dialog-modal-with-custom-width
modal.modal-that-closes-when-clicked-outside
modal.modal-using-anchor-link
modal.modal-using-checkbox
modal.responsive
```

##### navbar (9)

```
navbar.navbar-with-colors
navbar.navbar-with-dropdown-center-logo-and-icon
navbar.navbar-with-icon-at-start-and-end
navbar.navbar-with-icon-indicator-and-dropdown
navbar.navbar-with-menu-and-submenu
navbar.navbar-with-search-input-and-dropdown
navbar.navbar-with-title-and-icon
navbar.navbar-with-title-only
navbar.responsive-dropdown-menu-on-small-screen-center-menu-on-large-screen
```

##### pagination (6)

```
pagination.extra-small-buttons
pagination.nexprev-outline-buttons-with-equal-width
pagination.pagination-with-an-active-button
pagination.sizes
pagination.using-radio-inputs
pagination.with-a-disabled-button
```

##### progress (10)

```
progress.accent-color
progress.error-color
progress.indeterminate-without-value
progress.info-color
progress.neutral-color
progress.primary-color
progress.progress
progress.secondary-color
progress.success-color
progress.warning-color
```

##### radial-progress (5)

```
radial-progress.custom-color
radial-progress.custom-size-and-custom-thickness
radial-progress.different-values
radial-progress.radial-progress
radial-progress.with-background-color-and-border
```

##### radio (12)

```
radio.accent-color
radio.disabled
radio.error-color
radio.info-color
radio.neutral-color
radio.primary-color
radio.radio
radio.radio-sizes
radio.radio-with-custom-colors
radio.secondary-color
radio.success-color
radio.warning-color
```

##### range (11)

```
range.accent-color
range.error-color
range.info-color
range.neutral-color
range.primary-color
range.range
range.range-with-custom-color-and-no-fill
range.secondary-color
range.sizes
range.success-color
range.warning-color
range.with-steps-and-measure
```

##### rating (8)

```
rating.half-stars
rating.mask-heart-with-multiple-colors
rating.mask-star-2-with-green-500-color
rating.mask-star-2-with-warning-color
rating.rating
rating.read-only-rating
rating.sizes
rating.with-rating-hidden
```

##### select (14)

```
select.accent-color
select.disabled
select.error-color
select.ghost-no-background
select.info-color
select.neutral-color
select.primary-color
select.secondary-color
select.select
select.sizes
select.success-color
select.using-os-native-style-for-the-options-dropdown
select.warning-color
select.with-fieldset-and-labels
```

##### skeleton (4)

```
skeleton.skeleton
skeleton.skeleton-circle-with-content
skeleton.skeleton-rectangle-with-content
skeleton.skeleton-text
```

##### stack (7)

```
stack.3-divs-in-a-stack
stack.stacked-cards
stack.stacked-cards-end-direction
stack.stacked-cards-start-direction
stack.stacked-cards-top-direction
stack.stacked-cards-with-shadow
stack.stacked-images
```

##### stat (6)

```
stat.centered-items
stat.responsive-vertical-on-small-screen-horizontal-on-large-screen
stat.stat
stat.stat-with-icons-or-image
stat.vertical
stat.with-custom-colors-and-button
```

##### status (5)

```
status.status
status.status-sizes
status.status-with-bounce-animation
status.status-with-colors
status.status-with-ping-animation
```

##### steps (7)

```
steps.custom-colors
steps.horizontal
steps.responsive-vertical-on-small-screen-horizontal-on-large-screen
steps.vertical
steps.with-custom-content-in-step-icon
steps.with-data-content
steps.with-scrollable-wrapper
```

##### swap (6)

```
swap.activate-using-class-name-instead-of-checkbox
swap.hamburger-button
swap.swap-icons-with-flip-effect
swap.swap-icons-with-rotate-effect
swap.swap-text
swap.swap-volume-icons
```

##### tab (13)

```
tab.radio-tabs-border-tab-content
tab.radio-tabs-box-tab-content
tab.radio-tabs-lift-tab-content
tab.radio-tabs-lift-tab-content-on-bottom
tab.radio-tabs-lift-with-icons-tab-content
tab.sizes
tab.tabs
tab.tabs-border
tab.tabs-box
tab.tabs-box-using-radio-inputs
tab.tabs-box-with-a-horizontal-scroll-when-theres-no-space
tab.tabs-lift
tab.tabs-with-custom-color
```

##### table (9)

```
table.table
table.table-with-a-row-that-highlights-on-hover
table.table-with-an-active-row
table.table-with-border-and-background
table.table-with-pinned-rows
table.table-with-pinned-rows-and-pinned-cols
table.table-with-visual-elements
table.table-xs
table.zebra
```

##### text-rotate (1)

```
text-rotate.
```

##### textarea (6)

```
textarea.disabled
textarea.ghost-no-background
textarea.sizes
textarea.textarea
textarea.textarea-colors
textarea.with-form-control-and-labels
```

##### theme-controller (10)

```
theme-controller.theme-controller-using-a-checkbox
theme-controller.theme-controller-using-a-dropdown
theme-controller.theme-controller-using-a-radio-button
theme-controller.theme-controller-using-a-radio-input
theme-controller.theme-controller-using-a-swap
theme-controller.theme-controller-using-a-toggle
theme-controller.theme-controller-using-a-toggle-with-custom-colors
theme-controller.theme-controller-using-a-toggle-with-icons
theme-controller.theme-controller-using-a-toggle-with-icons-inside
theme-controller.theme-controller-using-a-toggle-with-text
```

##### timeline (16)

```
timeline.responsive-vertical-by-default-horizontal-on-large-screen
timeline.timeline-with-bottom-side-only
timeline.timeline-with-colorful-lines
timeline.timeline-with-different-sides
timeline.timeline-with-icon-snapped-to-the-start
timeline.timeline-with-text-on-both-sides-and-icon
timeline.timeline-with-top-side-only
timeline.timeline-without-icons
timeline.vertical-timeline-with-colorful-lines
timeline.vertical-timeline-with-different-sides
timeline.vertical-timeline-with-left-side-only
timeline.vertical-timeline-with-right-side-only
timeline.vertical-timeline-with-text-on-both-sides-and-icon
timeline.vertical-timeline-without-icons
```

##### toast (11)

```
toast.toast-center-toast-bottom-default
toast.toast-center-toast-middle
toast.toast-end-default-toast-bottom-default
toast.toast-end-toast-middle
toast.toast-start-toast-bottom-default
toast.toast-start-toast-middle
toast.toast-top-toast-center
toast.toast-top-toast-end
toast.toast-top-toast-start
toast.toast-with-alert-inside
```

##### toggle (8)

```
toggle.colors
toggle.disabled
toggle.indeterminate
toggle.sizes
toggle.toggle-switch
toggle.toggle-with-custom-colors
toggle.toggle-with-icons-inside
toggle.with-fieldset-and-label
```

##### validator (11)

```
validator.checkbox-requirement-validator
validator.date-input-requirement-validator
validator.number-input-requirement-validator
validator.password-requirement-validator
validator.phone-number-requirement-validator
validator.select-requirement-validator
validator.toggle-requirement-validator
validator.url-input-requirement-validator
validator.username-requirement-validator
validator.validator-and-validator-hint
validator.writing-an-invalid-email-address-applies-error-color-to-the-input-valid-email-address-applies-success-color
```

---

### Category: `layouts`

**What it returns:** Complete page layout HTML with `<!-- content here -->` placeholders. Uses daisyUI structural components (drawer, navbar) + Tailwind grid/flex utilities.

**Token budget:** ~300–800 tokens per layout.

#### All 5 Available Layout Keys

| Key | Description | Best for |
|-----|-------------|----------|
| `bento-grid-5-sections` | Responsive bento grid with 5 asymmetric areas | Feature showcases, dashboards |
| `bento-grid-8-sections` | Responsive bento grid with 8 content areas | Complex dashboards, portfolios |
| `responsive-collapsible-drawer-sidebar` | Sidebar collapses to icon-only on toggle | Admin panels with persistent nav |
| `responsive-offcanvas-drawer-sidebar` | Sidebar slides off-screen on mobile | Standard dashboard/app layout |
| `top-navbar` | Navbar + content + footer vertical stack | Landing pages, blogs, simple apps |

#### Output Structure

```markdown
## responsive-collapsible-drawer-sidebar

```html
<div class="drawer lg:drawer-open">
  <input id="my-drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <!-- Page content -->
    <label for="my-drawer" class="btn btn-primary drawer-button lg:hidden">
      Open drawer
    </label>
  </div>
  <div class="drawer-side">
    <label for="my-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
    <ul class="menu bg-base-200 text-base-content min-h-full w-80 p-4">
      <li><a>Sidebar Item 1</a></li>
      <li><a>Sidebar Item 2</a></li>
    </ul>
  </div>
</div>
```
```

---

### Category: `templates`

**What it returns:** Full page HTML composing multiple daisyUI components together. Ready to customize.

**Token budget:** ~800–1500 tokens per template.

#### All 2 Available Template Keys

| Key | Contains | Token estimate |
|-----|----------|----------------|
| `dashboard` | Drawer sidebar + navbar + stats grid + content cards + CSS-only toggle (no JS) | ~800–1500 |
| `login-form` | Side image + floating labels + input validation + social auth buttons + remember-me toggle | ~500–1000 |

#### Output Structure

```markdown
## dashboard

```html
<!-- Complete dashboard with drawer, navbar, stats grid, and content area -->
<div class="drawer lg:drawer-open">
  <input id="dashboard-drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content flex flex-col">
    <!-- Navbar -->
    <div class="navbar bg-base-100 shadow-sm">...</div>
    <!-- Content -->
    <main class="flex-1 p-6">
      <!-- Stats row -->
      <div class="stats shadow mb-6">...</div>
      <!-- Content grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">...</div>
    </main>
  </div>
  <div class="drawer-side"><!-- sidebar menu --></div>
</div>
```
```

---

### Category: `themes`

**What it returns:** CSS configuration and reference. **Not HTML.**

**Token budget:** ~200–600 tokens per key.

#### All 3 Available Theme Keys

| Key | Returns |
|-----|---------|
| `builtin-themes` | List of all 35 built-in themes + how to enable them in CSS |
| `colors` | Complete semantic color system: 20 color variables + usage with Tailwind utilities |
| `custom-theme` | `@plugin "daisyui"` CSS directive template with all required variables |

#### Output Structure — `builtin-themes`

```markdown
## Built-in Themes

35 built-in themes available:

light, dark, cupcake, bumblebee, emerald, corporate, synthwave, retro,
cyberpunk, valentine, halloween, garden, forest, aqua, lofi, pastel,
fantasy, wireframe, black, luxury, dracula, cmyk, autumn, business,
acid, lemonade, night, coffee, winter, dim, nord, sunset, caramellatte,
abyss, silk

### Enable in CSS
...
```

#### Output Structure — `colors`

```markdown
## Color System

### Semantic Colors
| Color | CSS Variable | Usage |
|-------|-------------|-------|
| `primary` | `--color-primary` | Primary brand color |
| `primary-content` | `--color-primary-content` | Text on primary bg |
| `secondary` | `--color-secondary` | Secondary brand color |
| `secondary-content` | `--color-secondary-content` | Text on secondary bg |
| `accent` | `--color-accent` | Accent highlights |
| `neutral` | `--color-neutral` | Neutral elements |
| `info` | `--color-info` | Informational |
| `success` | `--color-success` | Success states |
| `warning` | `--color-warning` | Warning states |
| `error` | `--color-error` | Error states |

### Base Colors
| Color | CSS Variable | Usage |
|-------|-------------|-------|
| `base-100` | `--color-base-100` | Page background |
| `base-200` | `--color-base-200` | Slightly darker bg |
| `base-300` | `--color-base-300` | Even darker bg |
| `base-content` | `--color-base-content` | Default text color |
```

#### Output Structure — `custom-theme`

```markdown
## Custom Theme

```css
@plugin "daisyui" {
  themes: light --default,
  themes: dark --prefersdark,
  themes: mytheme {
    primary: oklch(65% 0.25 250);
    secondary: oklch(70% 0.20 200);
    accent: oklch(75% 0.15 150);
    neutral: oklch(30% 0.02 250);
    base-100: oklch(98% 0.01 250);
  }
}
```
```

---

### Token Budget Summary

| Category | Per-item tokens | Typical batch |
|----------|----------------|---------------|
| `components` | 200–500 | 5 components ≈ 1–2.5K |
| `component-examples` | 100–300 | 5 examples ≈ 0.5–1.5K |
| `layouts` | 300–800 | 2 layouts ≈ 0.6–1.6K |
| `templates` | 800–1500 | 1 template ≈ 0.8–1.5K |
| `themes` | 200–600 | All 3 keys ≈ 0.6–1.8K |

**Full dashboard build** (layout + 5 components + 5 examples + theme) ≈ **3–7K tokens**.

---

### Calling Patterns

| Pattern | Calls | Recommendation |
|---------|-------|----------------|
| Batch multiple components in one call | 1 | ✅ Always |
| Mix categories (components + examples + themes) | 1 | ✅ Excellent |
| Components first → then targeted examples | 2 | ✅ When unsure of example names |
| Component + known example together | 1 | ✅ When you know the exact example key |
| Layout first → fill with component examples | 2–3 | ✅ For full pages |
| Theme first → then components/templates | 2–3 | ✅ For branded UIs |
| One component per call | N | ❌ Never — always batch |
| All examples for one component | 1 | ❌ Wasteful — pick only 1–3 you need |
| Building page without layout/template | Many | ❌ Use templates/layouts first |

#### Pattern 1: Explore a Component

```jsonc
// Step 1: Get component reference to see available examples
{ "components": { "button": true } }

// Step 2: Fetch only the specific examples you need
{ "component-examples": { "button.button-with-icon": true, "button.outline-buttons": true } }
```

#### Pattern 2: Build a Full Page

```json
{
  "layouts": { "responsive-collapsible-drawer-sidebar": true },
  "components": { "navbar": true, "card": true, "stat": true, "table": true },
  "component-examples": {
    "navbar.responsive-dropdown-menu-on-small-screen-center-menu-on-large-screen": true,
    "card.card": true,
    "stat.stat-with-icons-or-image": true,
    "table.table-with-visual-elements": true
  }
}
```

#### Pattern 3: Start from a Template

```json
{
  "templates": { "dashboard": true },
  "themes": { "colors": true }
}
```

#### Pattern 4: Theme-First for Branded UIs

```
Step 1: { "themes": { "custom-theme": true, "colors": true } }
→ Generate custom theme CSS from brand colors

Step 2: { "templates": { "dashboard": true } }
→ Dashboard HTML uses semantic colors that adapt to your theme
```

---

## Tool 2: `daisyui-blueprint-Figma-to-daisyUI`

Extract Figma design structure as a hierarchical node tree for conversion to daisyUI code.

### Setup Requirement

Requires a **Figma API token** set as the `FIGMA` environment variable:

```bash
export FIGMA="figd_xxxxxxxxxxxxxxxxxxxxx"
```

Generate at [Figma Developer API](https://www.figma.com/developers/api#access-tokens). Token needs read access to the target file.

---

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `string` | **Yes** | — | Figma design URL |
| `depth` | `number` | No | `10` | Node tree traversal depth (1–20+) |
| `includeImages` | `boolean` | No | `false` | Include image download URLs for nodes |

### URL Format

```
https://www.figma.com/design/{FILE_KEY}/{FILE_NAME}?node-id={NODE_ID}
```

| Part | Required | Example | Description |
|------|----------|---------|-------------|
| Base URL | Yes | `https://www.figma.com/design/` | Must be a Figma design URL |
| File key | Yes | `abc123XYZ` | Unique file identifier |
| File name | Yes | `My-Design` | URL-encoded file name |
| `node-id` | No (recommended) | `1-2`, `42-100` | Target a specific frame/node |

**Tip:** Always target specific `node-id` for focused results. Right-click a frame in Figma → "Copy link".

### Depth Guide

| Depth | Response size | Use case |
|-------|--------------|----------|
| 1 | Minimal | File-level overview only |
| 3 | Small (~5–20 KB) | Top-level frames and sections |
| 5 | Medium | Page structure with component outlines |
| 7 | Large | Detailed component structure |
| 10 (default) | Very large (~20–100 KB) | Full detail including nested components |
| 15+ | Maximum (100+ KB) | Deeply nested designs |

**Strategy:** Start at depth 3–5, increase for specific sections that need more detail.

---

### Output Structure

Returns a **hierarchical JSON node tree** representing the Figma design:

```json
{
  "name": "Page Name",
  "type": "CANVAS",
  "children": [
    {
      "name": "Frame Name",
      "type": "FRAME",
      "absoluteBoundingBox": { "x": 0, "y": 0, "width": 1440, "height": 900 },
      "layoutMode": "VERTICAL",
      "primaryAxisAlignItems": "MIN",
      "counterAxisAlignItems": "MIN",
      "paddingLeft": 0, "paddingRight": 0, "paddingTop": 0, "paddingBottom": 0,
      "itemSpacing": 0,
      "fills": [{ "type": "SOLID", "color": { "r": 1, "g": 1, "b": 1, "a": 1 } }],
      "children": [ ... ]
    }
  ]
}
```

### Node Properties Reference

```
Node
├── name            (string)   — Figma layer name
├── type            (string)   — FRAME | GROUP | COMPONENT | INSTANCE | TEXT | RECTANGLE | ELLIPSE | VECTOR | IMAGE
├── children        (array)    — Child nodes
├── absoluteBoundingBox
│   ├── x, y        (number)   — Position
│   ├── width       (number)   — Width in px
│   └── height      (number)   — Height in px
├── fills           (array)    — Background colors/gradients
│   ├── type        (string)   — SOLID | GRADIENT_LINEAR | GRADIENT_RADIAL | GRADIENT_ANGULAR | IMAGE
│   └── color       (object)   — { r, g, b, a } (0–1 range)
├── strokes         (array)    — Border styles
├── effects         (array)    — Shadows, blur
│   ├── type        (string)   — DROP_SHADOW | INNER_SHADOW | LAYER_BLUR | BACKGROUND_BLUR
│   ├── color       (object)   — { r, g, b, a }
│   ├── offset      (object)   — { x, y }
│   └── radius      (number)   — Blur radius
├── layoutMode      (string)   — HORIZONTAL | VERTICAL | NONE
├── primaryAxisAlignItems       — Main axis: MIN | CENTER | MAX | SPACE_BETWEEN
├── counterAxisAlignItems       — Cross axis: MIN | CENTER | MAX | BASELINE
├── layoutSizingHorizontal      — FIXED | HUG | FILL
├── layoutSizingVertical        — FIXED | HUG | FILL
├── paddingLeft/Right/Top/Bottom (number)
├── itemSpacing     (number)   — Gap between children
├── cornerRadius    (number)   — Border radius
├── strokeWeight    (number)   — Border width
├── characters      (string)   — Text content (TEXT nodes only)
└── style           (object)   — Font properties (TEXT nodes only)
    ├── fontFamily  (string)
    ├── fontWeight  (number)
    ├── fontSize    (number)
    └── textAlignHorizontal (string) — LEFT | CENTER | RIGHT | JUSTIFIED
```

### Node Type → daisyUI Mapping

| Node Type | Description | Typical daisyUI mapping |
|-----------|-------------|------------------------|
| `FRAME` | Container/layout | `div` with flex/grid classes |
| `GROUP` | Grouped elements | Wrapper `div` |
| `COMPONENT` | Reusable definition | Map to daisyUI component |
| `INSTANCE` | Component instance | Map to daisyUI component |
| `TEXT` | Text element | `p`, `h1`–`h6`, `span` |
| `RECTANGLE` | Shape | Background div, card, button |
| `ELLIPSE` | Circle/oval | avatar, status indicator |
| `VECTOR` | SVG/icon | Inline SVG |
| `IMAGE` | Image fill | `<img>` or `<figure>` |

### With `includeImages: true`

Nodes with image fills include download URLs:

```json
{
  "name": "Hero Image",
  "type": "RECTANGLE",
  "imageUrl": "https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/...",
  "fills": [{ "type": "IMAGE", "imageRef": "abc123" }]
}
```

---

### Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Missing or invalid Figma token | Set `FIGMA` env var with a valid API token |
| 403 Forbidden | Token lacks access to the file | Ensure the token owner has view access |
| 404 Not Found | Invalid file key or node ID | Verify the URL is correct and the file exists |
| Empty response | Node ID doesn't exist in the file | Check `node-id` parameter in the URL |
| Very large response | High depth on complex file | Reduce `depth` or target a specific `node-id` |

---

## Cross-Tool Workflow

The two tools form a pipeline for Figma-to-code conversion. **Never skip a step.**

```
┌─────────────────────────────┐         ┌─────────────────────────────┐
│   Figma-to-daisyUI Tool     │         │    daisyUI Snippets Tool    │
│                             │         │                             │
│  Input:  Figma URL          │         │  Input:  Component names    │
│  Output: Design node tree   │         │  Output: HTML code          │
│                             │         │                             │
│  Step 1: FETCH design       │  ────▶  │  Step 3: GET snippets       │
└─────────────────────────────┘         └─────────────────────────────┘
              │                                       │
              ▼                                       ▼
     Step 2: ANALYZE                         Step 4: BUILD
     - Layout structure                      - Compose HTML from snippets
     - Identify components                   - Map Figma colors → semantic
     - Extract colors/text                   - Apply responsive breakpoints
     - Note spacing/typography               - Preserve text content
```

### Mandatory 4-Step Sequence

| Step | Action | Tool | Details |
|------|--------|------|---------|
| 1. FETCH | Call Figma tool | `Figma-to-daisyUI` | Pass `url` + `depth` (start 3–5) |
| 2. ANALYZE | Examine node tree | — (agent reasoning) | Layout type, components, colors, text, spacing |
| 3. GET SNIPPETS | Call Snippets tool | `daisyUI-Snippets` | Single batched call with ALL identified components |
| 4. BUILD | Compose HTML | — (agent coding) | Combine snippets + Tailwind layout + Figma content |

### Figma Element → daisyUI Component Mapping

| Figma element | daisyUI component |
|---------------|-------------------|
| Navigation bar frame | `navbar` |
| Card-like containers | `card` |
| Clickable rectangles with text | `button` (`btn`) |
| Side panel | `drawer` |
| Data grid/rows | `table` |
| Metric displays | `stat` |
| Tab-like navigation | `tab` |
| Form inputs | `input`, `select`, `textarea` |
| Toggle switches | `toggle` |
| Notification banners | `alert` |
| Popup overlays | `modal` |
| Avatar circles | `avatar` |
| Tag/label chips | `badge` |
| Loading indicators | `loading`, `skeleton` |
| Bottom navigation | `dock` |
| Breadcrumb trail | `breadcrumbs` |
| Progress indicators | `steps`, `progress` |
| Accordion/expandable sections | `accordion`, `collapse` |
| Dropdown menus | `dropdown` |
| Footer sections | `footer` |

### Figma Properties → Tailwind Classes

| Figma property | Tailwind class |
|---------------|---------------|
| `layoutMode: "HORIZONTAL"` | `flex flex-row` |
| `layoutMode: "VERTICAL"` | `flex flex-col` |
| `primaryAxisAlignItems: "MIN"` | `justify-start` |
| `primaryAxisAlignItems: "CENTER"` | `justify-center` |
| `primaryAxisAlignItems: "MAX"` | `justify-end` |
| `primaryAxisAlignItems: "SPACE_BETWEEN"` | `justify-between` |
| `counterAxisAlignItems: "MIN"` | `items-start` |
| `counterAxisAlignItems: "CENTER"` | `items-center` |
| `counterAxisAlignItems: "MAX"` | `items-end` |
| `counterAxisAlignItems: "BASELINE"` | `items-baseline` |
| `itemSpacing: 4` | `gap-1` |
| `itemSpacing: 8` | `gap-2` |
| `itemSpacing: 12` | `gap-3` |
| `itemSpacing: 16` | `gap-4` |
| `itemSpacing: 24` | `gap-6` |
| `itemSpacing: 32` | `gap-8` |
| `paddingLeft: 16` | `pl-4` |
| `paddingRight: 16` | `pr-4` |
| `paddingTop: 16` | `pt-4` |
| `paddingBottom: 16` | `pb-4` |
| `cornerRadius: 4` | `rounded` |
| `cornerRadius: 8` | `rounded-lg` |
| `cornerRadius: 12` | `rounded-xl` |
| `cornerRadius: 16` | `rounded-2xl` |
| `cornerRadius: 9999` | `rounded-full` |
| Font size 12px | `text-xs` |
| Font size 14px | `text-sm` |
| Font size 16px | `text-base` |
| Font size 18px | `text-lg` |
| Font size 20px | `text-xl` |
| Font size 24px | `text-2xl` |
| Font size 30px | `text-3xl` |
| Font weight 400 | `font-normal` |
| Font weight 500 | `font-medium` |
| Font weight 600 | `font-semibold` |
| Font weight 700 | `font-bold` |

### Figma Colors → daisyUI Semantic Colors

| Figma color | daisyUI mapping |
|-------------|----------------|
| Brand/accent tones | `primary`, `secondary`, `accent` |
| Gray/neutral tones | `neutral`, `base-100`/`200`/`300` |
| Green tones | `success` |
| Blue tones | `info` |
| Yellow/orange tones | `warning` |
| Red tones | `error` |
| White background | `base-100` |
| Dark text | `base-content` |

**Rule:** Never hard-code hex values. Map to semantic colors so they adapt across themes.

```html
<!-- ❌ DON'T -->
<button class="bg-blue-500 text-white">Click</button>

<!-- ✅ DO -->
<button class="btn btn-primary">Click</button>
```

### Spacing Scale Quick Reference

| Figma px | Tailwind value | Class example |
|----------|---------------|---------------|
| 4px | `1` | `p-1`, `gap-1` |
| 8px | `2` | `p-2`, `gap-2` |
| 12px | `3` | `p-3`, `gap-3` |
| 16px | `4` | `p-4`, `gap-4` |
| 20px | `5` | `p-5`, `gap-5` |
| 24px | `6` | `p-6`, `gap-6` |
| 32px | `8` | `p-8`, `gap-8` |
| 40px | `10` | `p-10`, `gap-10` |
| 48px | `12` | `p-12`, `gap-12` |
| 64px | `16` | `p-16`, `gap-16` |

---

## Color System Quick Reference

| Color | Usage | Content Variant |
|-------|-------|-----------------|
| `primary` | Primary actions, CTAs | `primary-content` |
| `secondary` | Secondary actions | `secondary-content` |
| `accent` | Accent highlights | `accent-content` |
| `neutral` | Neutral elements | `neutral-content` |
| `base-100` | Page background | `base-content` |
| `base-200` | Slightly darker bg | — |
| `base-300` | Even darker bg | — |
| `info` | Informational | `info-content` |
| `success` | Success states | `success-content` |
| `warning` | Warning states | `warning-content` |
| `error` | Error states | `error-content` |

**Convention:** Every color has a `-content` variant for text on that color's background: `bg-primary text-primary-content`.

---

## Agent Best Practices Summary

1. **Batch requests.** Fetch all needed snippets in a single call — never one-component-per-call.
2. **Components first, then examples.** The component reference lists available examples. Don't guess names.
3. **No JavaScript needed.** daisyUI 5 is CSS-only: drawers use checkbox toggles, modals use `<dialog>`, dropdowns use `<details>`.
4. **Semantic colors only.** Use `primary`, `secondary`, etc. — never hardcode hex. They auto-adapt per theme.
5. **`-content` convention.** Text on colored backgrounds: `bg-primary text-primary-content`.
6. **Layout/template first.** For full pages, start with a layout or template, then fill with components.
7. **Mix categories freely.** Request components + examples + themes in one call.
8. **Figma: target specific nodes.** Use `node-id` and start with low depth, increase as needed.
9. **Preserve Figma content.** Extract text from `characters` property; match layout from `layoutMode` + `itemSpacing`.
10. **2–4 MCP calls typical.** A full UI build should need 2–4 calls totaling 1–7K response tokens.
