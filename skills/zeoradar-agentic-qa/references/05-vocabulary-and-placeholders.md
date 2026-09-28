# 05 — Universal Parameter Vocabulary and Placeholders

All 225 Gherkin test cases across the 20 suites in `zeoradar-agentic-qa` use a standardized, bracketed parameter notation. This allows any test case to run against any brand, country, or language without code modification.

---

## 1. Global Session Placeholders

| Placeholder | Meaning & Semantic Scope | Example Values | How Tester/Agent Injects It |
|---|---|---|---|
| `[APP_URL]` | Base URL of the ZeoRadar web application | `https://zeoradar.endpoints.lol/` (Production Live Deployment — Mandatory) | Permanently pinned to Production |
| `[DOMAIN]` | Target website / brand domain under analysis | `daikin.com.tr`, `example.com` | Interactive intake or project settings |
| `[BRAND]` | Monitored brand display name | `Daikin`, `Acme Corp` | Brand onboarding / baseline session |
| `[SLUG]` | Workspace / tenant URL slug | `daikin`, `daikin-tr` | Route path `#/[SLUG]/:tab` |
| `[COUNTRY]` | 2-letter ISO country code for geographic market | `TR`, `US`, `GB`, `DE` | Region dropdown or URL route |
| `[LANGUAGE]` | Active UI and query language | `tr`, `en` | Language toggle or user profile |
| `[USER_EMAIL]` | Authenticated test user identity | `e2e-agent@zeogen.com` | Login screen or auto-login parameter |
| `[PASSWORD]` | User password for authentication | `ZeoTest2026!` | Auth modal password input |
| `[OTP_CODE]` | 6-digit numeric verification code | `246810` (test code) | OTP input grid |
| `[WORKSPACE_SLUG]` | URL slug of active project workspace (alias of `[SLUG]`) | `daikin`, `daikin-tr` | Hash router path `#/[SLUG]/:tab` |
| `[VIEWPORT_SIZE]` | Browser window dimension | `1440x900` (desktop), `390x844` (mobile) | Ego-Browser viewport initialization |

---

## 2. Pillar-Specific Placeholders

### Step 03 & 04 (Intelligence & Benchmarking)
- `[ENGINE_NAME]`: AI engine identifier (`chat_gpt`, `perplexity`, `gemini`, `claude`, `aimode`).
- `[DATE_RANGE]`: Longitudinal filter timeframe (`7d`, `14d`, `30d`, `90d`).
- `[CITATION_URL]`: Normalized domain citation target (e.g. `en.wikipedia.org/wiki/[BRAND]`).
- `[THEME_KEY]`: 10-theme sentiment taxonomy (`pricing`, `quality`, `range`, `availability`, `service`, etc.).
- `[SORT_COLUMN]`: Benchmark matrix column (`brand`, `chat_gpt`, `perplexity`, `citations`).

### Step 05 & 06 (Prompt Studio & Analytics)
- `[PROMPT_QUERY]`: Search prompt text (e.g. `[BRAND] klimalar ve enerji tasarrufu`).
- `[TOPIC_NAME]`: Taxonomy category title (e.g. `Isı Pompası`, `Inverter Klima`).
- `[CREDIT_BALANCE]`: Available execution cells in billing account (e.g. `10001720`).
- `[BOT_NAME]`: Web crawler identifier (`GPTBot`, `ClaudeBot`, `PerplexityBot`, `other`).
- `[PROJECTION_MODEL]`: Volume statistical estimation model (`median`, `conservative`, `aggressive`).

### Step 07 & 08 (Content & Governance)
- `[OPPORTUNITY_ID]`: Unique opportunity backlog card identifier (e.g. `op-reddit-1`).
- `[TARGET_SLUG]`: Evaluated article URL slug (e.g. `en-iyi-isi-pompasi-rehberi`).
- `[FACT_ID]`: Unique verified brand fact key in Ground Truth Truth Vault.
- `[EXPECTED_VERSION]`: Integer version for Optimistic Concurrency Control (OCC).
- `[MEMBER_ROLE]`: Team workspace role (`owner`, `member`).
