# Security-Focused Review Patterns

Systematic approach to reviewing PRs for security vulnerabilities. Apply these patterns to every cluster, with heightened attention on API endpoints, authentication flows, and any code handling user input.

---

## STRIDE Threat Model per Change

For each significant code change, run through the STRIDE categories. This is not a full threat model — it is a quick mental scan that catches the most common security gaps in PRs.

| Category | Question to Ask | What to Look For |
|----------|----------------|-----------------|
| **Spoofing** | Can an attacker impersonate a legitimate user here? | Missing auth middleware on new endpoints, JWT validation gaps, session fixation |
| **Tampering** | Can an attacker modify data they shouldn't? | Mass assignment, unvalidated input written to DB, missing CSRF tokens |
| **Repudiation** | Can an attacker act without leaving an audit trail? | Missing audit logs on sensitive operations, no request logging |
| **Information Disclosure** | Can sensitive data leak? | Secrets in code, PII in logs, verbose error messages, CORS misconfiguration |
| **Denial of Service** | Can an attacker exhaust resources? | Missing rate limiting, unbounded queries, regex DoS (ReDoS), no timeouts |
| **Elevation of Privilege** | Can a user gain unauthorized access? | Missing RBAC checks, privilege escalation paths, IDOR vulnerabilities |

### How to apply STRIDE during review

```
For each new or modified function/endpoint:
1. Identify the trust boundary (where does user input enter?)
2. Run through S-T-R-I-D-E mentally (10 seconds each)
3. If any category triggers concern, trace the data flow
4. Record findings with file:line evidence
```

---

## Input Validation Patterns

### Taint tracking through code

Trace user input from entry point to usage. Any path where user input reaches a sensitive sink without validation is a potential vulnerability.

**Entry points (sources):**
```
HTTP request body          → req.body, request.json(), @Body()
Query parameters           → req.query, request.args, @Query()
Path parameters            → req.params, path variables
HTTP headers               → req.headers (especially Cookie, Authorization, X-Forwarded-*)
File uploads               → req.files, multipart data
WebSocket messages         → ws.on('message')
Environment variables      → process.env (when user-configurable)
Database results           → when used to construct further queries
```

**Sensitive sinks:**
```
SQL queries                → db.query(), .raw(), .execute()
Shell commands             → exec(), spawn(), system()
File system operations     → fs.readFile(), open(), path.join() with user input
Template rendering         → innerHTML, dangerouslySetInnerHTML, v-html, {!! !!}
Redirects                  → res.redirect(), location.href
HTTP requests (SSRF)       → fetch(), axios(), http.get() with user-controlled URLs
Deserialization            → JSON.parse(), pickle.loads(), yaml.load()
Regular expressions        → new RegExp(userInput) — ReDoS risk
Logging                    → console.log(sensitiveData), logger.info(req.body)
```

### Common injection patterns by language

**SQL Injection:**
```javascript
// VULNERABLE — string concatenation
db.query(`SELECT * FROM users WHERE id = ${userId}`);
db.query("SELECT * FROM users WHERE id = " + userId);

// SAFE — parameterized
db.query('SELECT * FROM users WHERE id = $1', [userId]);
db.query('SELECT * FROM users WHERE id = ?', [userId]);
```

**Command Injection:**
```python
# VULNERABLE — shell=True with user input
subprocess.run(f"convert {filename} output.png", shell=True)

# SAFE — argument list, no shell
subprocess.run(["convert", filename, "output.png"])
```

**XSS:**
```jsx
// VULNERABLE — raw HTML insertion
<div dangerouslySetInnerHTML={{ __html: userComment }} />
element.innerHTML = userInput;

// SAFE — React auto-escapes by default
<div>{userComment}</div>
```

**Path Traversal:**
```javascript
// VULNERABLE — user controls path
const file = path.join('/uploads', req.params.filename);

// SAFE — resolve and verify prefix
const resolved = path.resolve('/uploads', req.params.filename);
if (!resolved.startsWith('/uploads/')) throw new Error('Invalid path');
```

---

## Authentication and Authorization Checklist

### New endpoint review

Every new endpoint or route must answer these questions:

```
1. Is authentication required?
   → Check: auth middleware applied in route definition
   → Red flag: endpoint defined without auth decorator/middleware

2. Is authorization checked?
   → Check: role/permission validation after auth
   → Red flag: auth present but no role check on admin-only operations

3. Is the resource scoped to the authenticated user?
   → Check: query includes user ID filter (e.g., WHERE user_id = ?)
   → Red flag: endpoint returns all records without user scoping (IDOR)

4. Are elevated operations protected?
   → Check: admin/write operations have appropriate guards
   → Red flag: DELETE endpoint accessible to any authenticated user
```

### Auth bypass patterns to watch for

| Pattern | Example | Risk |
|---------|---------|------|
| Middleware ordering | Auth middleware added after route handler | Auth check never runs |
| Conditional auth | `if (process.env.NODE_ENV !== 'test') requireAuth()` | Auth disabled in some environments |
| Fallback defaults | `const role = user?.role || 'admin'` | Unauthenticated users get admin |
| Path matching gaps | Auth on `/api/users` but not `/api/users/` (trailing slash) | Bypass via URL variant |
| Method mismatch | Auth on GET but not POST for same route | Write operations unprotected |
| Nested routes | Parent route has auth, child route overrides with none | Auth stripped on child |

---

## Secrets and Sensitive Data

### What to scan for in diffs

```
High-confidence secret patterns:
  AKIA[0-9A-Z]{16}                     → AWS Access Key
  [a-z0-9]{32}                          → Generic API key (needs context)
  -----BEGIN (RSA|DSA|EC) PRIVATE KEY   → Private key
  ghp_[a-zA-Z0-9]{36}                  → GitHub personal access token
  sk-[a-zA-Z0-9]{48}                   → OpenAI API key
  xoxb-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}  → Slack bot token
  mongodb\+srv://[^@]+@                 → MongoDB connection string
  postgres://[^@]+@                     → PostgreSQL connection string

Variable name patterns (check values assigned to these):
  *_KEY, *_SECRET, *_TOKEN, *_PASSWORD, *_CREDENTIAL
  api_key, secret_key, access_token, auth_token
  DATABASE_URL, REDIS_URL, SMTP_PASSWORD
```

### Sensitive data in logs

```
Red flags in logging statements:
  logger.info(`User login: ${JSON.stringify(req.body)}`);  → logs passwords
  console.log('Auth header:', req.headers.authorization);   → logs tokens
  logger.error('Failed:', error.stack);                     → may leak internal paths

Safe patterns:
  logger.info(`User login: user=${req.body.username}`);     → selective fields
  logger.error('Auth failed', { userId, reason });          → structured, no secrets
```

---

## Common Vulnerability Patterns in PRs

### SSRF (Server-Side Request Forgery)

```javascript
// VULNERABLE — user controls URL
const response = await fetch(req.body.webhookUrl);

// SAFE — validate against allowlist
const allowed = ['https://api.example.com', 'https://hooks.slack.com'];
if (!allowed.some(base => req.body.webhookUrl.startsWith(base))) {
  throw new Error('URL not allowed');
}
```

### Mass Assignment

```javascript
// VULNERABLE — all body fields passed to model
const user = await User.create(req.body);
// Attacker sends: { name: "foo", role: "admin", isVerified: true }

// SAFE — explicit field allowlist
const user = await User.create({
  name: req.body.name,
  email: req.body.email,
});
```

### Insecure Direct Object Reference (IDOR)

```javascript
// VULNERABLE — no ownership check
app.get('/api/orders/:id', async (req, res) => {
  const order = await Order.findById(req.params.id);
  res.json(order);  // Any user can see any order
});

// SAFE — scoped to authenticated user
app.get('/api/orders/:id', async (req, res) => {
  const order = await Order.findOne({
    _id: req.params.id,
    userId: req.user.id,  // Only returns user's own orders
  });
  if (!order) return res.status(404).json({ error: 'Not found' });
  res.json(order);
});
```

### Open Redirect

```javascript
// VULNERABLE — user controls redirect target
res.redirect(req.query.returnUrl);

// SAFE — validate redirect is relative or to known domain
const url = new URL(req.query.returnUrl, 'https://myapp.com');
if (url.origin !== 'https://myapp.com') {
  return res.status(400).json({ error: 'Invalid redirect' });
}
res.redirect(url.pathname);
```

---

## Security Review Decision Tree

```
New code touches user input?
  YES → Trace input to all sinks. Check validation at each step.
  NO  → Continue to next check.

New endpoint or route added?
  YES → Verify auth middleware, authorization, rate limiting.
  NO  → Continue to next check.

Secrets, tokens, or credentials referenced?
  YES → Verify they come from env/vault, not hardcoded.
       Check they don't appear in logs.
  NO  → Continue to next check.

Third-party dependency added or updated?
  YES → Check for known CVEs. Verify version is pinned.
  NO  → Continue to next check.

CORS, CSP, or security header changed?
  YES → Verify the change doesn't widen the attack surface.
  NO  → Continue to next check.

Cryptographic operation present?
  YES → Verify strong algorithms (no MD5/SHA1 for security).
       Check key management (not hardcoded).
  NO  → Security review complete for this file.
```

---

## Severity Mapping for Security Findings

| Finding | Default Severity | Escalation Condition |
|---------|-----------------|---------------------|
| SQL injection | 🔴 Blocker | Always |
| Auth bypass | 🔴 Blocker | Always |
| Hardcoded secret | 🔴 Blocker | Always (once committed, consider it leaked) |
| XSS | 🔴 Blocker (stored) / 🟡 Important (reflected) | Stored XSS is always a blocker |
| SSRF | 🟡 Important | 🔴 if internal network accessible |
| Missing rate limiting | 🟡 Important | 🔴 if on auth endpoints |
| IDOR | 🟡 Important | 🔴 if exposes sensitive data |
| Missing input validation | 🟡 Important | 🔴 if data reaches DB/shell unvalidated |
| Overly permissive CORS | 🟡 Important | 🔴 if allows credential-bearing requests |
| Weak cryptography | 🟡 Important | 🔴 if protecting auth or encryption keys |
| Missing CSP headers | 🟢 Suggestion | 🟡 if app renders user content |
| Missing audit logging | 🟢 Suggestion | 🟡 on admin or financial operations |
