# Security Research Guide

## Quick Reference: Which Tools For Which Security Problem

| Use Case | Primary Tool | Secondary Tool | Why This Combination |
|---|---|---|---|
| 01. OWASP Top 10 Compliance | `deep_research` | `search_google` + `search_reddit` | Stack-specific checklist + current list + real audit stories |
| 02. Authentication | `deep_research` | `search_reddit` + `search_google` | Holistic auth architecture + breach stories + CVE monitoring |
| 03. Secrets Management | `deep_research` | `search_google` | Team-size-calibrated tool selection + breach reports |
| 04. CORS & CSP Config | `deep_research` | `search_google` | Cross-layer config (app+proxy+CDN) + error-driven debugging |
| 05. Dependency Scanning | `deep_research` | `search_google` | Multi-language strategy + triage workflow + tool comparison |
| 06. Encryption & Hashing | `deep_research` | `search_google` | Use-case-specific algorithms + NIST recommendations |
| 07. Input Validation | `deep_research` | `search_google` | Multi-layer defense design + bypass technique discovery |
| 08. Rate Limiting | `deep_research` | `search_google` | Tiered limit design + algorithm comparisons + Redis patterns |
| 09. Secure File Upload | `deep_research` | `search_google` | Complete upload pipeline + attack vector catalog |
| 10. API Security | `deep_research` | `search_google` + `search_reddit` | Multi-auth architecture + OWASP API Top 10 |

---

## 01. OWASP Top 10 Compliance

**deep_research** -- attach your server entry point:
```
WHAT I NEED: Prioritized compliance checklist for OWASP Top 10 2025 applied to
Node.js/Express + React + PostgreSQL.
SPECIFIC QUESTIONS:
1) Which OWASP categories are most violated in Express + React apps?
2) What does "Cryptographic Failures" (A02) look like in Node.js?
3) How do we test for SSRF in an app with outbound HTTP calls?
4) How to structure automated OWASP checks in CI/CD?
FOCUS: Practical remediation steps, not theory
```

**search_google**: `["OWASP Top 10 2025 2026 updated list", "OWASP A01 broken access control prevention", "OWASP compliance Node.js", "OWASP scanning tools comparison site:github.com"]`

**search_reddit**: `["OWASP compliance real world audit experience", "r/netsec OWASP 2025 changes", "r/devsecops OWASP CI/CD pipeline", "OWASP Top 10 overrated vs real security"]`

**Best Practices**: Attach server entry point -- middleware chain shows which categories you address. Be specific about auth model ("JWT in httpOnly cookies" vs "localStorage"). Include your ORM since A03 (Injection) depends on it. Run iteratively: first pass finds gaps, second dives into top 3.

---

## 02. Authentication Implementation

**deep_research** -- describe deployment architecture:
```
WHAT I NEED: Complete auth strategy for Node.js/Express API + React SPA frontend.
SPECIFIC QUESTIONS:
1) argon2id vs bcrypt: concrete parameters for 100 logins/sec on 2-core machine?
2) httpOnly cookies with CSRF, or Authorization header with refresh rotation?
3) Session fixation handling -- what does express-session do by default?
4) Correct SameSite config for cross-origin SPA (app.example.com, api.example.com)?
5) Secure "remember me" implementation?
```

**search_reddit**: `["bcrypt vs argon2 which should I use", "JWT vs session cookies security debate", "CSRF still needed SameSite cookies 2025", "r/webdev authentication mistakes learned"]`

**search_google**: `["bcrypt vs argon2id 2025 recommendation", "\"next-auth\" OR \"auth.js\" CVE", "passport.js vs lucia auth security comparison"]`

**Best Practices**: Same-origin vs cross-origin changes advice completely. Check for CVEs before committing to any auth library. On Reddit, search for mistakes and failures -- they teach more than "best library" posts. Ask about the full lifecycle: registration through logout.

---

## 03. Secrets Management

**deep_research** -- describe current approach honestly:
```
WHAT I NEED: Secrets strategy for 5-dev team on AWS ECS with Terraform.
WHY: Currently using .env files in private repo. Near-miss with public fork.
SPECIFIC QUESTIONS:
1) Is Vault overkill for 5 people? Minimum viable approach?
2) AWS Secrets Manager vs Parameter Store: when does cost justify?
3) How to handle secrets in local development?
4) Automatic RDS credential rotation with ECS?
5) Pre-commit hooks to prevent .env commits?
```

**search_google**: `["Vault vs AWS Secrets Manager vs Doppler 2025", ".env file security risks", "\"exposed API key\" breach site:bleepingcomputer.com", "git secrets pre-commit hook setup"]`

**Best Practices**: Describe starting point honestly for better migration advice. Include IaC tooling (Terraform/Pulumi). Specify compliance requirements (SOC2/HIPAA). Ask about developer experience -- painful tools get circumvented. Search for breach reports to justify investment.

---

## 04. CORS & CSP Configuration

**deep_research** -- list all origins and third-party deps:
```
WHAT I NEED: CORS + CSP config for React SPA (app.example.com) calling Express API (api.example.com),
using Google Fonts, Stripe.js, CDN (cdn.example.com).
SPECIFIC QUESTIONS:
1) CORS config for credentials with specific origin (not wildcard)?
2) Handle preflight in nginx without conflicting with Express?
3) CSP directives for React, styled-components, Google Fonts, Stripe.js, CDN?
4) CSP nonces with styled-components?
5) Report-only mode deployment process?
FOCUS: Exact header values and nginx config
```

**search_google**: `["CORS Access-Control-Allow-Origin error Express React", "CSP header generator tool", "CORS preflight 403 nginx reverse proxy", "blocked by CORS policy credentials include"]`

**Best Practices**: List ALL origins and third-party deps -- CORS/CSP are whitelist-based. Attach nginx config -- the most common bug is proxy + app both setting headers. Specify CSS-in-JS solution for CSP. Always deploy CSP in report-only mode first. Search exact error messages in quotes.

---

## 05. Dependency Vulnerability Scanning

**deep_research** -- list all language ecosystems:
```
WHAT I NEED: Scanning strategy for monorepo (npm + pip + cargo), Docker to Kubernetes.
SPECIFIC QUESTIONS:
1) One scanner (Snyk/Trivy) or per-language (npm audit + cargo audit + pip-audit)?
2) CI thresholds: fail on critical/high, warn on medium, ignore low?
3) Container scanning: build time, registry, or deploy time?
4) Triage workflow for transitive deps with no fix?
5) Handling Dependabot PR noise (20+ PRs/week)?
```

**search_google**: `["Snyk vs Grype vs Trivy comparison", "npm audit false positives handling", "Dependabot auto-merge configuration", "Trivy container scanning"]`

**Best Practices**: List all ecosystems -- polyglot advice differs from single-language. Describe pain points ("too many PRs", "false positives"). Request SLA framework: critical 24h, high 1 week. Ask about container scanning separately -- different tools and timing.

---

## 06. Encryption & Hashing Choices

**deep_research** -- specify compliance and data type:
```
WHAT I NEED: Encryption/hashing for Node.js encrypting health data (PHI) in PostgreSQL, hashing files.
SPECIFIC QUESTIONS:
1) AES-256-GCM vs ChaCha20-Poly1305 for DB columns -- nonce management burden?
2) Key derivation: HKDF vs Argon2 (data encryption, not passwords)?
3) SHA-256 vs BLAKE3 for integrity: BLAKE3 production-ready for HIPAA?
4) Key rotation for already-encrypted columns without downtime?
5) node:crypto pitfalls for AES-GCM (IV, key handling, auth tag)?
FOCUS: Correctness and compliance. HIPAA non-negotiable.
```

**search_google**: `["AES-GCM vs ChaCha20-Poly1305 2025", "AES-GCM nonce reuse catastrophic", "NIST post-quantum cryptography standard", "libsodium vs node:crypto"]`

**Best Practices**: Specify compliance (HIPAA, FIPS, PCI-DSS) -- each restricts choices. Describe what you encrypt (columns, files, payloads). Ask about key management -- most crypto failures are key management failures. Search for failure modes, not just recommendations. Include hardware context for algorithm selection.

---

## 07. Input Validation & Sanitization

**deep_research** -- attach schemas and rendering components:
```
WHAT I NEED: Validation/sanitization strategy for Express + React with rich text, uploads, API params.
SPECIFIC QUESTIONS:
1) Rich text from TipTap: server sanitization? DOMPurify, allowlisted tags?
2) Where should validation happen: client, API (zod), service, or all three?
3) Does Prisma reintroduce injection risk ($queryRaw)?
4) File upload: prevent path traversal, null byte, double extension?
5) How to check regex patterns for ReDoS?
```

**search_google**: `["SQL injection ORM bypass 2025", "XSS React dangerouslySetInnerHTML DOMPurify", "path traversal Node.js filename sanitization", "ReDoS detection prevention", "Unicode normalization attack bypass"]`

**Best Practices**: Attach zod/yup schemas for review. Attach dangerouslySetInnerHTML components. Search bypass techniques, not just defenses. Include your ORM name specifically. Request test cases (XSS payloads, SQLi attempts) for automated testing.

---

## 08. Rate Limiting & Abuse Prevention

**deep_research** -- describe traffic and infrastructure:
```
WHAT I NEED: Rate limiting for public REST API (authenticated + anonymous).
WHY: Credential stuffing, scraping, traffic spikes.
SPECIFIC QUESTIONS:
1) Token bucket vs sliding window: which and why?
2) Rate limits per tier (public, authenticated, admin)? Starting values?
3) Distributed rate limiting with Redis for ECS cluster?
4) /login credential stuffing defense without blocking legitimate users?
5) Layering Cloudflare edge with application rate limiting?
FOCUS: Specific values, Redis key design, Cloudflare config
```

**search_google**: `["token bucket vs sliding window comparison", "rate limiting Redis distributed pattern", "API rate limiting per-user per-IP per-endpoint", "Cloudflare Turnstile vs reCAPTCHA comparison"]`

**Best Practices**: Describe traffic patterns ("100 rps, 500 peaks") to calibrate limits. List endpoint categories for tiered limits. Multi-dimensional limiting (IP + user + API key) handles shared IPs. Ask about 429 error responses and Retry-After headers for API UX. Include monitoring.

---

## 09. Secure File Upload Handling

**deep_research** -- attach upload handler:
```
WHAT I NEED: Secure upload pipeline for Node.js/Express storing images in S3.
SPECIFIC QUESTIONS:
1) Correct order? (parse -> validate -> scan -> transform -> store -> respond)
2) MIME validation beyond extension? Magic bytes library for Node.js?
3) Filename sanitization: what to remove? UUID instead?
4) Virus scanning: ClamAV vs VirusTotal vs AWS-native for a startup?
5) S3 bucket policy and presigned URL configuration?
FOCUS: Implementation order, specific libraries, S3 config
```

**search_google**: `["secure file upload Node.js 2025", "MIME magic bytes validation", "S3 presigned URL security", "file upload OWASP checklist", "SVG XSS file upload", "zip bomb detection"]`

**Best Practices**: Describe all accepted file types -- each has different attack vectors. Ask about serving too (presigned URLs, CDN). Search specific attacks: SVG XSS, polyglot files, ZIP bombs. Extension checking alone is always insufficient. Request test files the pipeline should reject.

---

## 10. API Security Hardening

**deep_research** -- describe all API consumers:
```
WHAT I NEED: API security hardening for Express serving SPA + third-party integrators.
SPECIFIC QUESTIONS:
1) API key storage/validation -- hash like passwords? Rotation?
2) OAuth 2.0 scope design granularity (read:users vs users:read)?
3) JWT validation: claims beyond exp/iss? JWK rotation?
4) Webhook signing: HMAC-SHA256 implementation?
5) Need API gateway (Kong, AWS) at ~1000 RPM?
FOCUS: Implementation patterns with Express middleware
```

**search_google**: `["API security 2025 OWASP API Top 10", "JWT validation Node.js jose library", "API key hashing rotation storage", "HMAC webhook verification", "GraphQL security depth limiting"]`

**Best Practices**: Describe all consumers: SPA, mobile, third-party, webhooks -- each needs different auth. Attach auth middleware for JWT check review. OWASP API Top 10 is separate from regular Top 10. Check JWT library for CVEs (algorithm confusion, none bypass). Follow Stripe pattern for webhook signing.

---

## Universal Security Research Workflow

1. **`search_google`** (5-7 keywords) -- current threats, OWASP/NIST updates, library CVEs
2. **`search_reddit`** -- target r/netsec, r/AskNetsec, r/devsecops for audit stories and tool opinions
3. **`scrape_pages`** (3-5 URLs) -- OWASP cheat sheets, framework docs for exact config values
4. **`fetch_reddit`** (`fetch_comments=True`) -- breach stories and expert correction chains
5. **`deep_research`** (1-2 questions) -- synthesize into security architecture; attach your actual code

**Key principles:**
- Search for attacks, not just defenses -- understanding the attack informs better defense
- Include framework, ORM, and library versions -- security advice is version-specific
- Attach actual code for specific vulnerability identification
- Search for failures/breaches -- they teach better than best practices
- Specify compliance requirements upfront (HIPAA, SOC2, PCI-DSS)
- Deploy controls with monitoring first (report-only CSP, alert-only limits) before enforcement
