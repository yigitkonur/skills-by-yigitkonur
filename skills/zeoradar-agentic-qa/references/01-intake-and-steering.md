# 01 — Interactive Intake and Conversational Steering

The `zeoradar-agentic-qa` skill establishes a precise, production-first testing context before executing browser actions.

> [!CRITICAL]
> **Production Target & Real User Mandate**:
> All End-to-End testing, QA audits, and journey simulations MUST run exclusively against the live production deployment: **`https://zeoradar.endpoints.lol/`**.
> Testing against local mock ports (`8090`, `8080`) or using backend database injection scripts (such as inserting directly into Supabase via service keys or fabricating mock data) is strictly prohibited. Every action must simulate an authentic human user clicking, typing, navigating, and inspecting the live UI through `ego-browser`.

---

## 1. Core Intake Parameters

Every testing session requires four foundational variables:

| Variable | Description | Meaningful Variants | Standard Production Default |
|---|---|---|---|
| `[APP_URL]` | Base URL of the ZeoRadar application under test | `https://zeoradar.endpoints.lol/` (Production Live Deployment — **MANDATORY**) | `https://zeoradar.endpoints.lol/` |
| `[DOMAIN]` | Target brand website or monitored competitor domain | `daikin.com.tr`, `example.com` | `[DOMAIN]` (interactive or config) |
| `[BRAND]` | Monitored brand display name | `Daikin`, `Acme Corp` | `[BRAND]` |
| `[SLUG]` | Workspace / tenant URL slug | `daikin`, `daikin-tr` | Inferred from brand name or domain |
| `[COUNTRY]` | Geographic market under test (ccTLD / region) | `TR` (Turkey)<br>`US` (United States)<br>`UK` (United Kingdom)<br>`DE` (Germany) | Inferred from `[DOMAIN]` (e.g. `.com.tr` -> `TR`) or `TR` |
| `[LANGUAGE]` | Language for UI controls and prompt queries | `tr` (Turkish)<br>`en` (English) | `tr` (or `en` for international brands) |
| `[SCOPE]` | Scope of test execution | `smoke` (Critical paths: Steps 01, 02, 03)<br>`full` (All 8 steps, 225 Gherkin cases)<br>`custom` (Specific pillar, e.g. `step-04`, `step-07`) | `smoke` for PR verification; `full` for audits |

---

## 2. Interactive Steering Protocol

When invoked without explicit target arguments, the agent confirms the production testing target:

### Conversational Ingestion Example
```text
Agent: "ZeoRadar Production E2E test orkestrasyonunu başlatıyorum. Lütfen parametreleri onaylayın:
1. Canlı Production Ortamı: https://zeoradar.endpoints.lol/ (Zorunlu / Yerel mock yasaktır)
2. Test Edilecek Marka Alan Adı: [DOMAIN] (Örn: daikin.com.tr)
3. Hedef Pazar Ülkesi: TR (Türkiye)
4. Arayüz Dili: tr (Türkçe)
5. Test Kapsamı: 'smoke' (Adım 1-3 Temel Akışlar) mı yoksa 'full' (Tüm 225 Gherkin Vakası) mı?"
```

### Silent Fallback for Autonomous Batch Execution
If operating inside an automated CI pipeline, orchestration script, or non-interactive subagent mission, the agent does **NOT** block or poll for approval. It logs:
```text
[INTAKE AUTO-RESOLVE]
Target App URL: https://zeoradar.endpoints.lol/ (Production)
Target Brand Domain: [DOMAIN]
Target Country: TR
Target Language: tr
Execution Scope: full
```
And proceeds directly to Stage 0 (Health Gate) and Stage 1 (Foundation Lane).

---

## 3. Pre-Flight Connectivity & Health Gate

Before triggering any subagent or opening browser tabs, verify production target accessibility:

1. **Production Origin Check**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" https://zeoradar.endpoints.lol/
   # Expected: 200
   ```
2. **MacBook Remote Display Gate**:
   ```bash
   ssh macbook "ego-browser --version || which ego-browser"
   # Expected: Valid path or binary version
   ```
3. **Account Credit Balance Gate**:
   Ensure the test user (`e2e-agent@zeogen.com`) has active testing balance (>1,000,000 credits).
4. **Storage Cleanliness Gate**:
   Ensure browser state does not carry stale onboarding drafts (`localStorage.getItem("zeo-ob-draft") === null`).

If the production origin returns non-200, credits are depleted, or the MacBook SSH gateway is unreachable, halt execution and report the exact network error signature to the operator.

---

## 4. The Zero-Mock & Anti-Injection Law

1. **No Local Mock Ports**: Running E2E tests against `http://127.0.0.1:8090` or `localhost:8080` is strictly forbidden. E2E QA exists to verify live production behavior.
2. **No Backend Database Injection**: Directly injecting data into PostgreSQL/Supabase (via REST APIs, service keys, or scripts like `seed-*-live-data.mjs`) to fake UI entities is prohibited.
3. **True User Interaction**: Every workspace, project, prompt, and setting MUST be created by simulating an authentic human user clicking buttons, typing in text boxes, and waiting for asynchronous backend jobs to complete in the UI.
