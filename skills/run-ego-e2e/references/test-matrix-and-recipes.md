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

---

## 7. Recipe: OAuth Providers & SAML SSO Enterprise Auth

Test authentication view, Google and GitHub brand button rendering, SAML SSO drawer expansion, and domain validation.

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('test-auth-sso')

// 1. Clear session to avoid automatic boot gate redirects to /
await js(String.raw`(() => {
  localStorage.removeItem('supabaseAuth');
  localStorage.removeItem('mockAuth');
  sessionStorage.clear();
})()`)

// 2. Open auth view
await openOrReuseTab('https://zeoradar.endpoints.lol/auth', { wait: true, timeout: 20 })
await wait(2)

// 3. Assert OAuth buttons exist with brand attributes
const oauthCheck = await js(String.raw`(() => {
  const g = document.querySelector('.auth-btn-google, [aria-label*="Google"]');
  const gh = document.querySelector('.auth-btn-github, [aria-label*="GitHub"]');
  const sso = document.querySelector('.auth-btn-sso, [aria-label*="SSO"]');
  return {
    hasGoogle: !!g,
    hasGitHub: !!gh,
    hasSSO: !!sso,
    googleLabel: g?.innerText?.trim(),
    ssoLabel: sso?.innerText?.trim()
  };
})()`)
cliLog('OAuth UI Check: ' + JSON.stringify(oauthCheck, null, 2))
if (!oauthCheck.hasGoogle || !oauthCheck.hasGitHub || !oauthCheck.hasSSO) {
  throw new Error('Missing OAuth or SSO provider buttons');
}

// 4. Click SSO button to expand domain drawer
await click('.auth-btn-sso, [aria-label*="SSO"]', { label: 'Expand SSO domain drawer' })
await wait(1)

// 5. Test domain input and validation
await fillInput('input[type="text"], input[name*="domain"], .sso-domain-input', 'enterprise-acme.com')
await wait(1)
const ssoState = await js(String.raw`(() => {
  const input = document.querySelector('input[name*="domain"], .sso-domain-input');
  return { value: input?.value, isVisible: input?.offsetParent !== null };
})()`)
cliLog('SSO Drawer Input State: ' + JSON.stringify(ssoState))
if (ssoState.value !== 'enterprise-acme.com') throw new Error('SSO domain input failed');
EOF
```

---

## 8. Recipe: Sliding Citation Drawer & Prompt Modal Inspection

Test opening deep telemetry modal inspectors and sliding drawers from table rows.

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('test-modals-drawers')

// 1. Navigate to citations view
await openOrReuseTab('https://zeoradar.endpoints.lol/hepsiburada/citations', { wait: true, timeout: 30 })
await wait(3)

// 2. Click citation row to open sliding drawer
const clickResult = await js(String.raw`(() => {
  const row = document.querySelector('[data-action="open-citation-drawer"], tbody tr');
  if (!row) return { error: 'No citation row found' };
  row.click();
  return { clicked: true, text: row.innerText.slice(0, 60) };
})()`)
cliLog('Citation click result: ' + JSON.stringify(clickResult))
await wait(2)

// 3. Assert drawer opened with metadata
const drawerCheck = await js(String.raw`(() => {
  const drawer = document.querySelector('.cite-drawer, .drawer, [class*="drawer"]');
  return {
    isOpen: !!drawer,
    hasCloseBtn: !!document.querySelector('.cite-drawer-close, [data-action="close-citation-drawer"], .close-btn'),
    snippet: drawer ? drawer.innerText.slice(0, 300) : null
  };
})()`)
cliLog('Citation Drawer Check: ' + JSON.stringify(drawerCheck, null, 2))
if (!drawerCheck.isOpen) throw new Error('Citation detail drawer failed to open');

// 4. Close drawer
await js(String.raw`(() => {
  const close = document.querySelector('.cite-drawer-close, [data-action="close-citation-drawer"], .close-btn');
  if (close) close.click();
})()`)
await wait(1)
EOF
```

