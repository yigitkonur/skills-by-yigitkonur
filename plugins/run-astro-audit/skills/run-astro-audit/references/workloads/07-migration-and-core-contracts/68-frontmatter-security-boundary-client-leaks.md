# Mission Brief: Frontmatter Security Boundary & Client Data Leak Audit

## 3.0 Skills / Tools: view_file, run_command.

## 3.1 Context Block

Astro component scripts enclosed by triple-dash fences (`---`) execute exclusively on the server during static build or on-demand SSR. `@astrojs/compiler` physically strips frontmatter code from the final response rendered to the browser.
However, severe client-side data leaks occur when developers inadvertently bridge server data across the client boundary via:

1. **`define:vars` Script Injections:** Passing frontmatter variables to `<script define:vars={{ secretKey, userSSN }}>` serializes private values into raw, unminified inline `<script>` tags in the HTML DOM, fully readable in browser "View Source".
2. **Client Island Props:** Passing private configuration to hydrated components (`<Island client:load token={SECRET_TOKEN} />`) serializes the props into `<astro-island>` HTML attributes for client hydration.
3. **Overexposed DOM Data Attributes:** Storing raw database records or private JSON blobs in `data-*` attributes.
   Astro best practices require using `astro:env/server` (`getSecret`) for server-only environment variables and projecting only non-sensitive, public presentation fields to client scripts and islands.

### Authoritative Astro Architectural & Best Practice Rules

Auditors must inspect, evaluate, and verify all frontmatter and component data boundaries against the repository's authoritative Astro best practices:

- **Primary Security Contract**: [03-frontmatter-security-boundary.md](../../best-practices/01-architecture-and-philosophy/03-frontmatter-security-boundary.md) — Isolate secrets and database calls in frontmatter without leaking to client bundles.
- **Server Islands Architecture**: [11-defer-personalized-content-with-server-islands.md](../../best-practices/02-islands-and-hydration/11-defer-personalized-content-with-server-islands.md) — Defer personalized content with Server Islands (`server:defer`).
- **Island URL Boundary**: [12-keep-server-island-props-under-url-limit.md](../../best-practices/02-islands-and-hydration/12-keep-server-island-props-under-url-limit.md) — Keep Server Island props lightweight and under URL length limits (< 2048 bytes).
- **Middleware State Contract**: [04-mutate-locals-never-reassign.md](../../best-practices/06-middleware-and-auth/04-mutate-locals-never-reassign.md) — Mutate `context.locals` properties; never overwrite the object.
- **Static Asset Bypass**: [05-filter-static-asset-requests.md](../../best-practices/06-middleware-and-auth/05-filter-static-asset-requests.md) — Filter out static assets before executing heavy middleware logic.
- **Streaming Pipeline Contract**: [19-avoid-consuming-streaming-response-body-in-middleware.md](../../best-practices/06-middleware-and-auth/19-avoid-consuming-streaming-response-body-in-middleware.md) — Avoid consuming streaming response bodies in post-execution middleware.
- **Headless Unit Testing**: [21-unit-test-components-with-astro-container-api.md](../../best-practices/10-auditing-testing-and-nextjs-migration/21-unit-test-components-with-astro-container-api.md) — Unit test `.astro` components headlessly with the Astro Container API.

Critical files to inspect:

- `src/components/`
- `src/pages/`
- `src/layouts/`
- `src/features/`
- `src/actions/`

## 3.2 Mission Objective

Perform an exhaustive security audit across all component templates to detect and eliminate any accidental serialization of server secrets, private tokens, or sensitive records into client island props, `define:vars`, or HTML attributes.
Outcome: Guarantee 100% server isolation for private environment variables and sensitive configuration across all client bundles.
Constraints: Read-only audit; do not alter production code.
Autonomy Grant: You own this mission end-to-end. Scan all template variables, check island props, and verify HTML output sanitization. The destination is fixed; the path is yours.

## 3.3 Research Guidance & Boundaries

1. Search for `define:vars` across all `.astro` files and audit the variable payloads being injected.
2. Inspect props passed to React client islands (components with `client:load`, `client:idle`, `client:visible`).
3. Verify that environment variables imported from `astro:env/server` or `process.env` never reach client island props or inline scripts.
4. Verify that `data-*` dataset attributes only contain minimal public identifiers rather than sensitive internal objects.
5. Ensure server-side data fetching projects only necessary presentation fields before rendering.

### ❌ Bad Practice / Anti-Pattern (Leaking Secrets & Full DB Records into Client DOM)

```astro
---
// src/components/OrderSummary.astro (Leaking secrets & full DB records to client)
// Next.js developers sometimes assume server component props to client components are obfuscated;
// in Astro, props to client islands are serialized into plain-text HTML attributes!
import { DB } from '../lib/db';
const user = await DB.users.findUnique({ where: { id: Astro.props.userId } });
const STRIPE_SECRET = process.env.STRIPE_SECRET_KEY;
---
<!-- ❌ DANGEROUS: define:vars serializes private server secrets directly into HTML source -->
<script define:vars={{ secretKey: STRIPE_SECRET, userSSN: user.ssn }}>
  console.log("Client initialized with:", secretKey, userSSN);
</script>

<!-- ❌ DANGEROUS: Passing private tokens or full server models to hydrated island -->
<!-- Serialized into <astro-island props="..."> in plain HTML view-source! -->
<PaymentWidget client:load stripeSecret={STRIPE_SECRET} fullUser={user} />
```

### ✅ Best Practice / Idiomatic (Strict Server Secret Isolation & Minimal Presentation Props)

```astro
---
// src/components/OrderSummary.astro (Isolated server secrets & minimized client props)
// Bound to RULE-ID: 01-architecture-and-philosophy/03-frontmatter-security-boundary
import { DB } from '../lib/db';
import { getSecret } from 'astro:env/server'; // Guaranteed server-only secret

const stripeSecret = getSecret('STRIPE_SECRET_KEY'); // Never leaves server frontmatter

// ✅ Select only minimal, non-sensitive public presentation fields
const order = await DB.orders.findUnique({
  where: { id: Astro.props.orderId },
  select: { id: true, total: true, status: true }
});
---
<div class="order-summary">
  <span>Order #{order.id}: {order.status}</span>
</div>

<!-- ✅ Hydrated island receives only minimal, public client tokens (never server secrets) -->
<PaymentWidget client:load publishableKey="pk_live_public..." orderId={order.id} />
```

## 3.4 Reporting Specification & Repository-Native Deliverables

You are operating strictly in **READ-ONLY AUDIT & DISCOVERY MODE**. Do not modify production application code in this phase.
All audit artifacts and defect inventories must be written directly to the repository under:
`docs/audits/results/07-migration-and-core-contracts/68-frontmatter-security-boundary-client-leaks/`

### Mandatory Audit Scope & Guardrails:

1. **Full-Repo Sweep Mandate**: Superficial or regional single-file scans are strictly forbidden. The audit must sweep the ENTIRE repository across all relevant bilingual routes, components, Content Layer collections, and edge pipelines.
2. **Strict Issue Size Ceiling**: The primary issue body MUST NOT exceed 60,000 characters (GitHub comment/body ceiling is 65,536; 60,000 provides safe headroom).
3. **Verified Audit Criteria Checklist**:
   - The issue MUST start with a comprehensive, verified checklist of every criterion checked.
   - Formatted as a nested list up to three levels deep (`- [x] Level 1`, `  - [x] Level 2`, `    - [x] Level 3`).
   - Strictly capped at **no more than 200 items total**.
   - Must be verified directly against the code before writing to `issue-body.md`.
4. **Mandatory Rule-ID Mapping**: Every item in `findings.json` MUST explicitly map to an authoritative Astro best practice rule ID (e.g. `RULE-ID: 01-architecture-and-philosophy/03-frontmatter-security-boundary`).

You must create and populate the following deliverables in `docs/audits/results/07-migration-and-core-contracts/68-frontmatter-security-boundary-client-leaks/`, and publish a GitHub Issue using `gh`:

1. **`findings.json`**: A machine-readable JSON inventory of all discovered defects, anti-patterns, or gaps:

```json
[
  {
    "id": "68-FRONTMATTER-SECURITY-BOUNDARY-CLIENT-LEAKS-001",
    "rule_id": "RULE-ID: 01-architecture-and-philosophy/03-frontmatter-security-boundary",
    "file": "src/components/HeaderNav.astro",
    "line": 42,
    "severity": "critical" | "high" | "medium" | "low",
    "category": "security" | "syntax" | "hydration" | "parity" | "performance",
    "defect": "Precise description of what is broken or violating invariants",
    "remediation": "Concrete, actionable instruction on how to fix it"
  }
]
```

2. **`evidence.md`**: Comprehensive investigative research log:
   - Full command outputs, vitest runs, grep matches, AST dumps.
   - Analysis of confirmed facts vs assumptions.
   - Step-by-step reproduction proof.

3. **`handoff.md`**: The executive, action-oriented implementation blueprint for the next subagent:
   - **Executive Summary:** Overall health of this domain (Clean / Minor Defects / Blockers).
   - **Architectural Invariants:** Rules that the fixing agent must NEVER violate while remediating.
   - **Step-by-Step Remediation Checklist:** Prioritized action items (ordered from highest to lowest severity).
   - **Exact Code Replacements:** File paths, line numbers, current faulty snippet, and drop-in replacement snippet.
   - **Verification Battery:** The exact commands the fixing agent must run post-remediation to prove 100% success.

4. **`issue-body.md`**: The publication-ready GitHub Issue markdown body adhering to the two-tier structure:
   - **Checklist Header**: The verified nested checklist of up to 200 items (3 levels max).
   - **Outer Tier (localized primary locale)**: Conversational human summary (1-2 sentences), affected URLs/routes table, surface area table (viewports, themes, components), observed defect vs expected behavior (WITHOUT prescribing code fixes).
   - **Inner Tier (English `<details>`)**: Collapsed block titled `<details><summary><strong>Agent implementation brief — scope, source map, behavior contracts, and verification</strong></summary>...</details>`. Contains exact `file:line` citations, quoted 3-8 lines of code, defect classification (`bug` | `by-design` | `drift` | `reversal`), required behavioral invariants, known traps, acceptance checklist, and embeds the structured `findings.json` table and `handoff.md` remediation steps.

5. **Publication via GitHub CLI (`gh`) & Sub-Issue Creation**:
   Execute the turnkey publisher script `scripts/audit/publish-audit-issue.mjs --sub-issues --git-push` which automatically verifies the 60,000-char limit, checklist nesting (<=200 items, max 3 levels), creates the primary issue, spawns linked sub-issues (capped at 20) for critical/high defects, and pushes the JSON deliverables to `origin main`:

```bash
# Turnkey Script (Validates <= 60,000 chars, creates primary issue + sub-issues, and pushes to main):
node scripts/audit/publish-audit-issue.mjs \
  --body "docs/audits/results/07-migration-and-core-contracts/68-frontmatter-security-boundary-client-leaks/issue-body.md" \
  --title "[Audit - Frontmatter Security Boundary & Client Data Leak Audit]: <Concise Defect Summary>" \
  --findings "docs/audits/results/07-migration-and-core-contracts/68-frontmatter-security-boundary-client-leaks/findings.json" \
  --sub-issues \
  --git-push
```

## 3.5 Verification Criteria

1. Run `git grep -n "define:vars" src/` to audit all inline script variable injections.
2. Run `git grep -n "client:load\|client:idle\|client:visible" src/` to verify island props.
3. Run `git grep -n "defineMiddleware" src/` to ensure middleware context does not expose sensitive session tokens to public cookies.
4. Run `git grep -n "server:defer" src/` to verify Server Island prop boundaries.
5. Execute headless component testing with Vitest using `experimental_AstroContainer` from `astro/container` to render components and verify that secret strings do not appear in rendered HTML:
   ```bash
   pnpm exec vitest run tests/components/ --run
   ```
6. Grep production client assets for secret patterns or environment variable names:
   ```bash
   grep -rn "sk_live_\|SECRET\|API_KEY\|TOKEN" dist/client/ dist/_astro/ || echo "No secrets found in client bundle."
   ```
7. Confirm zero private secrets or server-only credentials appear in client props or HTML attributes.

## 3.6 Handoff Contract

When your audit is complete, all deliverables are written to `docs/audits/results/07-migration-and-core-contracts/68-frontmatter-security-boundary-client-leaks/`, the GitHub Issue and any linked sub-issues are published, and changes are pushed to `main`, your final response message to the parent must be structured as follows:

1. **Domain & Role:** Frontmatter Security Boundary & Client Data Leak Audit
2. **Outcome:** Clean (0 defects) or Defects Found (Total count: N)
3. **Artifacts Written & Published:**
   - `file://docs/audits/results/07-migration-and-core-contracts/68-frontmatter-security-boundary-client-leaks/findings.json` (N defects logged with RULE-ID mappings)
   - `file://docs/audits/results/07-migration-and-core-contracts/68-frontmatter-security-boundary-client-leaks/evidence.md` (Complete command outputs and research proofs)
   - `file://docs/audits/results/07-migration-and-core-contracts/68-frontmatter-security-boundary-client-leaks/handoff.md` (Prioritized implementation brief for next agent)
   - `file://docs/audits/results/07-migration-and-core-contracts/68-frontmatter-security-boundary-client-leaks/issue-body.md` (Published GitHub Issue body, < 60,000 chars)
   - `file://docs/audits/results/07-migration-and-core-contracts/68-frontmatter-security-boundary-client-leaks/issue-meta.json` (Saved metadata)
   - **Primary GitHub Issue URL:** `https://github.com/<owner>/<repo>/issues/<issue_number>`
   - **Linked Sub-Issues (if any):** List of sub-issue URLs created (up to 20)
4. **Severity Breakdown:** Critical: X | High: Y | Medium: Z | Low: W
5. **Key Architectural Finding & Immediate Next Step:** 2-3 sentences summarizing the single most important action the subsequent fixing agent must take based on the issue and `handoff.md`.
