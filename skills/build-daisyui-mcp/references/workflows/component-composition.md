# Building Complex UIs from Components

> Architectural patterns for composing daisyUI components into full pages and applications.

---

## Composition Philosophy

daisyUI components are atomic building blocks. Complex UIs emerge from combining them:

1. **Layout shell** — drawer, navbar, footer (page structure)
2. **Content containers** — cards, tables, stat blocks (data display)
3. **Interactive elements** — buttons, inputs, modals (user interaction)
4. **Feedback elements** — alerts, toasts, loading, skeleton (system state)

---

## Pattern 1: Dashboard

> Admin panel with sidebar navigation, stats overview, and data tables.

### Components Needed

```
Tool: daisyui-blueprint-daisyUI-Snippets
Parameters:
  components:
    drawer: true
    navbar: true
    menu: true
    stat: true
    card: true
    table: true
    button: true
    avatar: true
    badge: true
    breadcrumbs: true
  layouts:
    responsive-offcanvas-drawer-sidebar: true
  templates:
    dashboard: true
```

### Architecture

```
┌─────────────────────────────────────────────────┐
│ drawer                                          │
│ ┌──────────┬────────────────────────────────────┤
│ │ drawer-  │ drawer-content                     │
│ │ side     │ ┌──────────────────────────────────┤
│ │          │ │ navbar                           │
│ │ menu     │ ├──────────────────────────────────┤
│ │  ├ Home  │ │ breadcrumbs                     │
│ │  ├ Users │ ├──────────────────────────────────┤
│ │  ├ Data  │ │ grid: stat × 4                  │
│ │  └ Conf  │ ├──────────────────────────────────┤
│ │          │ │ card > table                     │
│ │          │ │                                  │
│ └──────────┴────────────────────────────────────┘
```

### Example Code

```html
<div class="drawer lg:drawer-open">
  <input id="sidebar" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content bg-base-200">
    <!-- Navbar -->
    <div class="navbar bg-base-100 shadow-sm">
      <div class="navbar-start">
        <label for="sidebar" class="btn btn-ghost lg:hidden">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
        </label>
      </div>
      <div class="navbar-end gap-2">
        <button class="btn btn-ghost btn-circle">🔔</button>
        <div class="avatar placeholder">
          <div class="bg-neutral text-neutral-content w-8 rounded-full">
            <span class="text-xs">JD</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="p-6 space-y-6">
      <!-- Breadcrumbs -->
      <div class="breadcrumbs text-sm">
        <ul>
          <li><a>Dashboard</a></li>
          <li>Overview</li>
        </ul>
      </div>

      <!-- Stats Row -->
      <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div class="stat bg-base-100 rounded-box shadow">
          <div class="stat-title">Total Users</div>
          <div class="stat-value text-primary">31K</div>
          <div class="stat-desc">↗ 12% from last month</div>
        </div>
        <div class="stat bg-base-100 rounded-box shadow">
          <div class="stat-title">Revenue</div>
          <div class="stat-value text-secondary">$24K</div>
          <div class="stat-desc">↗ 8% from last month</div>
        </div>
        <div class="stat bg-base-100 rounded-box shadow">
          <div class="stat-title">Active Now</div>
          <div class="stat-value">1,200</div>
          <div class="stat-desc">↘ 3% from yesterday</div>
        </div>
        <div class="stat bg-base-100 rounded-box shadow">
          <div class="stat-title">Satisfaction</div>
          <div class="stat-value text-accent">98%</div>
          <div class="stat-desc">Based on 500 reviews</div>
        </div>
      </div>

      <!-- Table Card -->
      <div class="card bg-base-100 shadow">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <h2 class="card-title">Recent Orders</h2>
            <button class="btn btn-primary btn-sm">View All</button>
          </div>
          <div class="overflow-x-auto">
            <table class="table">
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="flex items-center gap-3">
                    <div class="avatar placeholder">
                      <div class="bg-primary text-primary-content w-8 rounded-full">
                        <span class="text-xs">A</span>
                      </div>
                    </div>
                    Alice Johnson
                  </td>
                  <td>$250.00</td>
                  <td><span class="badge badge-success">Completed</span></td>
                  <td>Jan 15, 2025</td>
                </tr>
                <tr>
                  <td class="flex items-center gap-3">
                    <div class="avatar placeholder">
                      <div class="bg-secondary text-secondary-content w-8 rounded-full">
                        <span class="text-xs">B</span>
                      </div>
                    </div>
                    Bob Smith
                  </td>
                  <td>$180.00</td>
                  <td><span class="badge badge-warning">Pending</span></td>
                  <td>Jan 14, 2025</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Sidebar -->
  <div class="drawer-side">
    <label for="sidebar" aria-label="close sidebar" class="drawer-overlay"></label>
    <ul class="menu bg-base-100 min-h-full w-64 p-4 gap-1">
      <li class="menu-title">Main</li>
      <li><a class="active">📊 Dashboard</a></li>
      <li><a>👥 Users</a></li>
      <li><a>📦 Products</a></li>
      <li><a>📋 Orders</a></li>
      <li class="menu-title">Settings</li>
      <li><a>⚙️ General</a></li>
      <li><a>🔒 Security</a></li>
    </ul>
  </div>
</div>
```

---

## Pattern 2: E-commerce Product Page

> Product detail page with image gallery, description, reviews, and related products.

### Components Needed

```
components: navbar, card, carousel, badge, rating, button, breadcrumbs,
            tab, avatar, stat, footer, hover-gallery
component-examples:
  card.card-with-badge: true
  carousel.carousel-with-indicator-buttons: true
  tab.radio-tabs-lift-tab-content: true
  navbar.responsive-dropdown-menu-on-small-screen-center-menu-on-large-screen: true
  rating.mask-star-2-with-warning-color: true
layouts:
  top-navbar: true
```

### Architecture

```
┌─────────────────────────────────────────┐
│ navbar                                  │
├─────────────────────────────────────────┤
│ breadcrumbs                             │
├───────────────────┬─────────────────────┤
│                   │ Product Title       │
│   carousel /      │ badge (sale/new)    │
│   hover-gallery   │ rating (stars)      │
│   (images)        │ Price + stat        │
│                   │ Size select         │
│                   │ Add to Cart btn     │
├───────────────────┴─────────────────────┤
│ tabs: Description | Reviews | Specs     │
├─────────────────────────────────────────┤
│ "Related Products" — card grid          │
├─────────────────────────────────────────┤
│ footer                                  │
└─────────────────────────────────────────┘
```

### Example Code

```html
<div class="min-h-screen bg-base-200">
  <!-- Navbar (omitted for brevity — see dashboard pattern) -->

  <div class="max-w-7xl mx-auto px-4 py-8 space-y-8">
    <!-- Breadcrumbs -->
    <div class="breadcrumbs text-sm">
      <ul>
        <li><a>Home</a></li>
        <li><a>Clothing</a></li>
        <li>Premium Jacket</li>
      </ul>
    </div>

    <!-- Product Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Image Gallery -->
      <div class="carousel w-full rounded-box">
        <div id="img1" class="carousel-item w-full">
          <img src="product-1.jpg" class="w-full object-cover" alt="Product" />
        </div>
        <div id="img2" class="carousel-item w-full">
          <img src="product-2.jpg" class="w-full object-cover" alt="Product" />
        </div>
      </div>

      <!-- Product Info -->
      <div class="space-y-4">
        <div class="flex items-center gap-2">
          <h1 class="text-3xl font-bold">Premium Leather Jacket</h1>
          <span class="badge badge-secondary">NEW</span>
        </div>

        <div class="flex items-center gap-2">
          <div class="rating rating-sm">
            <input type="radio" name="rating-product" class="mask mask-star-2 bg-warning" />
            <input type="radio" name="rating-product" class="mask mask-star-2 bg-warning" />
            <input type="radio" name="rating-product" class="mask mask-star-2 bg-warning" />
            <input type="radio" name="rating-product" class="mask mask-star-2 bg-warning" checked />
            <input type="radio" name="rating-product" class="mask mask-star-2 bg-warning" />
          </div>
          <span class="text-sm text-base-content/60">(128 reviews)</span>
        </div>

        <div class="text-3xl font-bold text-primary">$299.99</div>
        <p class="text-base-content/70">Premium quality leather jacket with modern fit. Perfect for casual and semi-formal occasions.</p>

        <fieldset class="fieldset">
          <legend class="fieldset-legend">Size</legend>
          <select class="select w-full">
            <option>Small</option>
            <option>Medium</option>
            <option selected>Large</option>
            <option>X-Large</option>
          </select>
        </fieldset>

        <div class="flex gap-3">
          <button class="btn btn-primary flex-1">Add to Cart</button>
          <button class="btn btn-outline">♡</button>
        </div>
      </div>
    </div>

    <!-- Product Tabs -->
    <div role="tablist" class="tabs tabs-lift">
      <input type="radio" name="product_tabs" role="tab" class="tab" aria-label="Description" checked />
      <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6">
        <p>Detailed product description goes here...</p>
      </div>
      <input type="radio" name="product_tabs" role="tab" class="tab" aria-label="Reviews" />
      <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6">
        <!-- Chat component works great for reviews -->
        <div class="chat chat-start">
          <div class="chat-image avatar placeholder">
            <div class="bg-neutral text-neutral-content w-10 rounded-full"><span>A</span></div>
          </div>
          <div class="chat-header">Alice <time class="text-xs opacity-50">2 days ago</time></div>
          <div class="chat-bubble">Amazing quality! Fits perfectly.</div>
        </div>
      </div>
      <input type="radio" name="product_tabs" role="tab" class="tab" aria-label="Specifications" />
      <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6">
        <table class="table"><tbody>
          <tr><td class="font-medium">Material</td><td>Genuine Leather</td></tr>
          <tr><td class="font-medium">Weight</td><td>1.2 kg</td></tr>
        </tbody></table>
      </div>
    </div>

    <!-- Related Products -->
    <h2 class="text-2xl font-bold">Related Products</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Repeat card pattern -->
      <div class="card bg-base-100 shadow">
        <figure><img src="related-1.jpg" alt="Related" /></figure>
        <div class="card-body">
          <h3 class="card-title text-base">Classic Denim Jacket</h3>
          <p class="text-primary font-bold">$149.99</p>
          <div class="card-actions justify-end">
            <button class="btn btn-primary btn-sm">View</button>
          </div>
        </div>
      </div>
      <!-- ... more cards -->
    </div>
  </div>

  <!-- Footer (omitted for brevity) -->
</div>
```

---

## Pattern 3: Blog / CMS

> Content-focused layout with article cards, pagination, and author info.

### Components Needed

```
components: navbar, card, avatar, badge, breadcrumbs, pagination (join + button),
            divider, footer, menu, drawer
layouts: top-navbar
```

### Architecture

```
┌─────────────────────────────────────────┐
│ navbar                                  │
├─────────────────────────────────────────┤
│ hero (featured post)                    │
├──────────────────────┬──────────────────┤
│                      │ Sidebar          │
│  card grid           │  - Categories    │
│  (article cards)     │  - Tags (badges) │
│                      │  - Newsletter    │
│                      │                  │
├──────────────────────┴──────────────────┤
│ pagination (join + button)              │
├─────────────────────────────────────────┤
│ footer                                  │
└─────────────────────────────────────────┘
```

### Key Code Snippet

```html
<!-- Article Card -->
<div class="card bg-base-100 shadow hover:shadow-lg transition-shadow">
  <figure><img src="article-cover.jpg" alt="Article" class="h-48 w-full object-cover" /></figure>
  <div class="card-body">
    <div class="flex gap-2">
      <span class="badge badge-primary badge-sm">Technology</span>
      <span class="badge badge-ghost badge-sm">5 min read</span>
    </div>
    <h2 class="card-title">Article Title Goes Here</h2>
    <p class="text-base-content/70 line-clamp-2">Article excerpt that gives a preview of the content...</p>
    <div class="card-actions items-center justify-between mt-2">
      <div class="flex items-center gap-2">
        <div class="avatar placeholder">
          <div class="bg-neutral text-neutral-content w-6 rounded-full"><span class="text-xs">J</span></div>
        </div>
        <span class="text-sm">Jane Doe</span>
      </div>
      <span class="text-xs text-base-content/50">Jan 10, 2025</span>
    </div>
  </div>
</div>

<!-- Pagination -->
<div class="flex justify-center">
  <div class="join">
    <button class="join-item btn btn-sm">«</button>
    <button class="join-item btn btn-sm">1</button>
    <button class="join-item btn btn-sm btn-active">2</button>
    <button class="join-item btn btn-sm">3</button>
    <button class="join-item btn btn-sm">»</button>
  </div>
</div>
```

---

## Pattern 4: Settings Page

> Configuration interface with grouped settings using tabs, forms, and toggles.

### Components Needed

```
components: navbar, drawer, menu, tab, fieldset, input, select, textarea,
            toggle, checkbox, radio, button, divider, alert
```

### Architecture

```
┌─────────────────────────────────────────┐
│ drawer                                  │
│ ┌──────────┬────────────────────────────┤
│ │ menu     │ Settings Page              │
│ │ ├ Profile│                            │
│ │ ├ Account│ tabs: General|Security|... │
│ │ ├ Notif  │ ┌──────────────────────────┤
│ │ └ API    │ │ fieldset groups          │
│ │          │ │ input + toggle + select  │
│ │          │ │ ...                      │
│ │          │ │ save button              │
│ └──────────┴────────────────────────────┘
```

### Key Code Snippet

```html
<!-- Settings Form -->
<div role="tablist" class="tabs tabs-box">
  <input type="radio" name="settings" role="tab" class="tab" aria-label="General" checked />
  <div role="tabpanel" class="tab-content p-6 space-y-6">

    <fieldset class="fieldset">
      <legend class="fieldset-legend">Display Name</legend>
      <input type="text" class="input w-full" value="John Doe" />
    </fieldset>

    <fieldset class="fieldset">
      <legend class="fieldset-legend">Email</legend>
      <input type="email" class="input w-full" value="john@example.com" />
      <p class="fieldset-label">Used for notifications and login</p>
    </fieldset>

    <fieldset class="fieldset">
      <legend class="fieldset-legend">Language</legend>
      <select class="select w-full">
        <option selected>English</option>
        <option>Spanish</option>
        <option>French</option>
      </select>
    </fieldset>

    <divider></divider>

    <fieldset class="fieldset">
      <label class="label justify-between w-full">
        <span>Email Notifications</span>
        <input type="checkbox" class="toggle toggle-primary" checked />
      </label>
    </fieldset>

    <fieldset class="fieldset">
      <label class="label justify-between w-full">
        <span>Marketing Emails</span>
        <input type="checkbox" class="toggle" />
      </label>
    </fieldset>

    <fieldset class="fieldset">
      <label class="label justify-between w-full">
        <span>Two-Factor Authentication</span>
        <input type="checkbox" class="toggle toggle-success" checked />
      </label>
    </fieldset>

    <div class="flex justify-end gap-2">
      <button class="btn btn-ghost">Cancel</button>
      <button class="btn btn-primary">Save Changes</button>
    </div>
  </div>

  <input type="radio" name="settings" role="tab" class="tab" aria-label="Security" />
  <div role="tabpanel" class="tab-content p-6">
    <!-- Security settings -->
  </div>
</div>
```

---

## Pattern 5: Chat Application

> Real-time messaging interface with contacts sidebar, message area, and input.

### Components Needed

```
components: drawer, menu, chat, avatar, input, button, badge, divider, navbar
component-examples:
  chat.chat-with-image-header-and-footer: true
  drawer.responsive-sidebar-is-always-visible-on-large-screen-can-be-toggled-on-small-screen: true
```

### Architecture

```
┌─────────────────────────────────────────┐
│ drawer                                  │
│ ┌──────────┬────────────────────────────┤
│ │ Contacts │ Chat Header (navbar)       │
│ │          ├────────────────────────────┤
│ │ avatar   │                            │
│ │ + name   │ chat messages              │
│ │ + badge  │ (scrollable)               │
│ │ (online) │                            │
│ │          ├────────────────────────────┤
│ │          │ input + send button (join) │
│ └──────────┴────────────────────────────┘
```

### Key Code Snippet

```html
<!-- Chat Messages Area -->
<div class="flex-1 overflow-y-auto p-4 space-y-4">
  <div class="chat chat-start">
    <div class="chat-image avatar online">
      <div class="w-10 rounded-full">
        <img src="alice.jpg" alt="Alice" />
      </div>
    </div>
    <div class="chat-header">
      Alice
      <time class="text-xs opacity-50">12:45</time>
    </div>
    <div class="chat-bubble">Hey! How's the project going?</div>
  </div>

  <div class="chat chat-end">
    <div class="chat-image avatar">
      <div class="w-10 rounded-full">
        <img src="me.jpg" alt="Me" />
      </div>
    </div>
    <div class="chat-header">
      You
      <time class="text-xs opacity-50">12:46</time>
    </div>
    <div class="chat-bubble chat-bubble-primary">Going great! Almost done with the UI.</div>
  </div>
</div>

<!-- Input Area -->
<div class="border-t border-base-300 p-4">
  <div class="join w-full">
    <input type="text" class="input join-item flex-1" placeholder="Type a message..." />
    <button class="btn btn-primary join-item">Send</button>
  </div>
</div>
```

---

## Pattern 6: Landing Page

> Marketing page with hero, features, social proof, and CTA sections.

### Components Needed

```
components: navbar, hero, card, stat, steps, footer, button, badge,
            avatar, divider, carousel
component-examples:
  hero.centered-hero: true
  hero.hero-with-figure: true
  card.pricing-card: true
  stat.responsive-vertical-on-small-screen-horizontal-on-large-screen: true
  footer.footer-with-a-form: true
  navbar.responsive-dropdown-menu-on-small-screen-center-menu-on-large-screen: true
layouts:
  top-navbar: true
```

### Architecture

```
┌─────────────────────────────────────────┐
│ navbar (transparent or white)           │
├─────────────────────────────────────────┤
│ hero (big headline + CTA + image)       │
├─────────────────────────────────────────┤
│ stat row (social proof numbers)         │
├─────────────────────────────────────────┤
│ features: card grid (3 columns)         │
├─────────────────────────────────────────┤
│ steps (how it works)                    │
├─────────────────────────────────────────┤
│ pricing: card grid (pricing-card × 3)  │
├─────────────────────────────────────────┤
│ testimonials: carousel of chat/cards    │
├─────────────────────────────────────────┤
│ CTA hero (final call to action)         │
├─────────────────────────────────────────┤
│ footer (links + newsletter form)        │
└─────────────────────────────────────────┘
```

### Key Code Snippet

```html
<!-- Hero Section -->
<div class="hero min-h-[60vh] bg-base-200">
  <div class="hero-content text-center">
    <div class="max-w-2xl">
      <span class="badge badge-primary badge-lg mb-4">🚀 Now in Beta</span>
      <h1 class="text-5xl font-bold">Build Better Products Faster</h1>
      <p class="py-6 text-lg text-base-content/70">
        The all-in-one platform for modern teams. Ship features, track progress, and delight customers.
      </p>
      <div class="flex gap-3 justify-center">
        <button class="btn btn-primary btn-lg">Get Started Free</button>
        <button class="btn btn-outline btn-lg">Watch Demo</button>
      </div>
    </div>
  </div>
</div>

<!-- Social Proof Stats -->
<div class="bg-base-100 py-12">
  <div class="max-w-5xl mx-auto">
    <div class="stats stats-vertical sm:stats-horizontal shadow w-full">
      <div class="stat place-items-center">
        <div class="stat-value text-primary">10K+</div>
        <div class="stat-desc">Active Users</div>
      </div>
      <div class="stat place-items-center">
        <div class="stat-value text-secondary">500+</div>
        <div class="stat-desc">Companies</div>
      </div>
      <div class="stat place-items-center">
        <div class="stat-value">99.9%</div>
        <div class="stat-desc">Uptime</div>
      </div>
    </div>
  </div>
</div>

<!-- How It Works -->
<div class="py-16 px-4">
  <h2 class="text-3xl font-bold text-center mb-12">How It Works</h2>
  <ul class="steps steps-vertical lg:steps-horizontal w-full">
    <li class="step step-primary">Sign Up</li>
    <li class="step step-primary">Connect Tools</li>
    <li class="step">Invite Team</li>
    <li class="step">Launch</li>
  </ul>
</div>

<!-- Pricing Cards -->
<div class="py-16 px-4 bg-base-200">
  <h2 class="text-3xl font-bold text-center mb-12">Simple Pricing</h2>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
    <div class="card bg-base-100 shadow">
      <div class="card-body items-center text-center">
        <h3 class="card-title">Starter</h3>
        <div class="text-4xl font-bold my-4">$0<span class="text-sm font-normal">/mo</span></div>
        <ul class="space-y-2 text-sm">
          <li>✓ 3 Projects</li>
          <li>✓ Basic Analytics</li>
          <li>✓ Community Support</li>
        </ul>
        <div class="card-actions mt-6">
          <button class="btn btn-outline btn-primary btn-block">Get Started</button>
        </div>
      </div>
    </div>
    <div class="card bg-primary text-primary-content shadow-lg scale-105">
      <div class="card-body items-center text-center">
        <span class="badge badge-secondary">Popular</span>
        <h3 class="card-title">Pro</h3>
        <div class="text-4xl font-bold my-4">$29<span class="text-sm font-normal">/mo</span></div>
        <ul class="space-y-2 text-sm">
          <li>✓ Unlimited Projects</li>
          <li>✓ Advanced Analytics</li>
          <li>✓ Priority Support</li>
        </ul>
        <div class="card-actions mt-6">
          <button class="btn btn-secondary btn-block">Start Free Trial</button>
        </div>
      </div>
    </div>
    <div class="card bg-base-100 shadow">
      <div class="card-body items-center text-center">
        <h3 class="card-title">Enterprise</h3>
        <div class="text-4xl font-bold my-4">Custom</div>
        <ul class="space-y-2 text-sm">
          <li>✓ Everything in Pro</li>
          <li>✓ SSO / SAML</li>
          <li>✓ Dedicated Support</li>
        </ul>
        <div class="card-actions mt-6">
          <button class="btn btn-outline btn-block">Contact Sales</button>
        </div>
      </div>
    </div>
  </div>
</div>
```

---

## Composition Tips

### 1. Always Start with the Layout Shell
Pick a layout first, then fill components into it. Don't build bottom-up.

### 2. Use Semantic Colors Everywhere
Don't hardcode colors. Use `primary`, `secondary`, `accent`, `neutral`, `base-*`. This ensures theme switching works.

### 3. Responsive by Default
Always add responsive classes:
- Stats: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`
- Cards: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
- Drawer: `lg:drawer-open` for persistent sidebar on desktop

### 4. Consistent Spacing
Use a spacing scale:
- Between sections: `space-y-8` or `gap-8`
- Within cards: `card-body` (built-in padding)
- Page padding: `p-4 md:p-6 lg:p-8`

### 5. Component Hierarchy
```
Layout (drawer/navbar)
  └── Section (div with padding)
       └── Container (card)
            └── Content (table, form, stats)
                 └── Interactive (button, input, toggle)
                      └── Feedback (badge, alert, loading)
```
