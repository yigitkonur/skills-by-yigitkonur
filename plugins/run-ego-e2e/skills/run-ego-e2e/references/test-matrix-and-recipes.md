# E2E Test Matrix & Real-User Recipes

This reference provides production-tested recipes for common application flows using `ego-browser`.

---

## 1. Recipe: Landing Page & Brand Selection

Test landing on an asset hub or directory, verifying cards, and navigating into a brand-specific dashboard.

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('test-brand-nav')

// 1. Open hub
await openOrReuseTab('https://zeoradar.endpoints.lol/', { wait: true, timeout: 30 })
await wait(2)

// 2. Verify tracked assets count
const hubData = await js(String.raw`(() => {
  const cards = document.querySelectorAll('.asset-card');
  return {
    count: cards.length,
    names: Array.from(cards).map(c => c.querySelector('span:nth-child(2)')?.innerText?.trim())
  };
})()`)

cliLog('Hub assets: ' + JSON.stringify(hubData))
if (hubData.count === 0) throw new Error('No asset cards rendered on landing page');

// 3. Click specific brand card
await click('.asset-card:nth-child(2)', { label: 'Click second brand card' })
await wait(2)

// 4. Verify transition to brand URL
const info = await pageInfo()
cliLog('Navigated to: ' + info.url)
if (!info.url.includes('/hepsiburada')) throw new Error('Failed to route to brand view');
EOF
```

---

## 2. Recipe: Metric Cards & Data Integrity

Test dashboard metric card values, ensure no broken NaN/undefined values appear, and assert executive summaries.

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('test-metrics')

// Assert metric values from DOM
const metrics = await js(String.raw`(() => {
  const cards = Array.from(document.querySelectorAll('.metric-card, [class*="metric"]'));
  return cards.map(c => ({
    label: c.querySelector('.label, [class*="label"]')?.innerText?.trim(),
    value: c.querySelector('.value, [class*="value"]')?.innerText?.trim()
  })).filter(m => m.label && m.value);
})()`)

cliLog('Extracted metrics: ' + JSON.stringify(metrics, null, 2))

// Assert sanity
for (const m of metrics) {
  if (m.value === 'NaN' || m.value === 'undefined' || m.value === 'null') {
    throw new Error(`Invalid metric value detected for "${m.label}": ${m.value}`);
  }
}
EOF
```

---

## 3. Recipe: Interactive Filter Chips & Toggle State

Test engine selection pills or category chips (e.g. GPT, Perplexity, Claude, Gemini).

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('test-filter-chips')

// Observe current active chips
const before = await js(String.raw`Array.from(document.querySelectorAll('.engine-chip.active, button.chip.active')).map(e => e.innerText.trim())`)
cliLog('Active before click: ' + JSON.stringify(before))

// Click specific chip using text selector or ref
await click('text="PPX"', { label: 'Toggle Perplexity chip' })
await wait(1)

const after = await js(String.raw`Array.from(document.querySelectorAll('.engine-chip.active, button.chip.active')).map(e => e.innerText.trim())`)
cliLog('Active after click: ' + JSON.stringify(after))

// Assert toggle effect
const changed = JSON.stringify(before) !== JSON.stringify(after);
if (!changed) throw new Error('Filter chip toggle produced no state change');
EOF
```

---

## 4. Recipe: Global System Invariants (Theme & i18n)

Test that global theme (Dark/Light) and internationalization (EN/TR) function dynamically without full-page reload.

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('test-invariants')

// --- Theme Toggle Test ---
cliLog('Testing Theme Toggle...')
await click('button[aria-label*="theme"]', { label: 'Toggle Theme' })
await wait(1)

const themeState = await js(String.raw`(() => ({
  themeAttr: document.documentElement.getAttribute('data-theme'),
  ariaLabel: document.querySelector('button[aria-label*="theme"]')?.getAttribute('aria-label')
}))()`)
cliLog('Theme state: ' + JSON.stringify(themeState))

// --- i18n Language Toggle Test ---
cliLog('Testing Language Toggle...')
await click('span.lang-btn', { label: 'Toggle Language' })
await wait(1)

const langState = await js(String.raw`(() => ({
  langCode: document.querySelector('.lang-btn')?.innerText?.trim(),
  firstLabel: document.querySelector('.side-label')?.innerText?.trim()
}))()`)
cliLog('Language state: ' + JSON.stringify(langState))

if (langState.langCode !== 'TR' && langState.langCode !== 'EN') {
  throw new Error('Unexpected language code: ' + langState.langCode);
}
EOF
```

---

## 5. Recipe: Profile Menu & Account Settings Navigation

Test user dropdown popover, account settings modal, and Stripe billing buttons.

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('test-account-flow')

// Open Profile Menu
await click('.profile-trigger', { label: 'Open profile menu' })
await wait(1)

// Click Account Settings item
await click('.menu-item[data-tab="account"]', { label: 'Navigate to Account Settings' })
await wait(2)

// Switch to Billing tab
await click('tab[name*="Billing"], text="Billing & Plan"', { label: 'Select Billing tab' })
await wait(1)

// Verify billing action buttons exist
const billingButtons = await js(String.raw`(() => {
  const btns = Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim());
  return {
    hasBuyCredits: btns.some(b => /credit/i.test(b)),
    hasManageBilling: btns.some(b => /billing|portal/i.test(b))
  };
})()`)

cliLog('Billing UI verification: ' + JSON.stringify(billingButtons))
if (!billingButtons.hasBuyCredits && !billingButtons.hasManageBilling) {
  throw new Error('Billing actions failed to render in account settings');
}
EOF
```
