# Derailment Report: OAuth Login Debugging with mcpc + Supabase

**Date:** 2026-03-25
**Skill:** `test-by-mcpc-cli`
**Scenario:** Testing `mcpc mcp.zeo.org/mcp login` against an MCP server using mcp-use + Supabase OAuth (Google provider)
**Duration wasted:** Multiple hours across 7+ friction points
**Root cause theme:** The skill documented OAuth superficially ("run `mcpc login`") without covering the actual protocol mechanics, environment traps, or Supabase-specific incompatibilities that agents encounter in practice.

---

## Friction Points

### F-01: OAuth metadata discovery chain — completely undocumented

**Severity:** Critical
**What happened:** Agent had no mental model of what `mcpc login` actually does under the hood. When errors appeared at various stages (metadata fetch, DCR, callback), the agent could not diagnose which stage failed or why.
**Root cause:** The skill's OAuth section was a one-liner (`mcpc login https://mcp.example.com`). The authentication reference guide documented the 10-step flow but the SKILL.md never linked to it or summarized the key stages.
**Actual flow:**
1. mcpc fetches `/.well-known/oauth-protected-resource` from the MCP server URL
2. mcpc reads `authorization_servers` from that response to find the authorization server (which may differ from the MCP server itself)
3. mcpc fetches `/.well-known/oauth-authorization-server` from the authorization server
4. mcpc checks for `registration_endpoint` in metadata (Dynamic Client Registration)
5. mcpc performs DCR to get `client_id` and `client_secret`
6. mcpc starts a local HTTP callback server on `127.0.0.1` (port 8000+)
7. mcpc opens the browser to `authorization_endpoint`
8. User authenticates, browser redirects to `http://127.0.0.1:<port>/callback`
9. mcpc exchanges the authorization code at `token_endpoint`
10. Tokens stored in keychain

**Fix applied:** Added "OAuth login deep dive" section to SKILL.md with the full flow, plus a debugging checklist.

### F-02: OrbStack port conflict — silent and devastating

**Severity:** Critical
**What happened:** `mcpc login` appeared to work (no port binding error), browser opened, user authenticated, but the callback never reached mcpc. Instead, OrbStack's `vcom-tunnel` service intercepted the request on `localhost:8000` and returned `{"detail":"Not Found"}` (FastAPI/Starlette JSON format).
**Root cause:** OrbStack binds `0.0.0.0:8000` and `0.0.0.0:8001` for its internal services. mcpc's port availability check binds `127.0.0.1:<port>`, which succeeds because the kernel treats `127.0.0.1` and `0.0.0.0` as non-conflicting for `bind()`. However, when the browser resolves `localhost`, OrbStack's wildcard binding captures the connection first.
**Diagnostic signature:** Callback returns JSON `{"detail":"Not Found"}` instead of mcpc's plain-text `Not found`. Any JSON 404 means something other than mcpc is handling the request.
**Detection command:** `lsof -i :8000-8010 | grep LISTEN`
**Fix applied:** Added OrbStack port conflict to Common Pitfalls table and OAuth debugging checklist with the `lsof` check as a mandatory pre-login step.

### F-03: "Incompatible auth server: does not support dynamic client registration"

**Severity:** High
**What happened:** mcpc fetched the OAuth metadata successfully but then immediately errored because `registration_endpoint` was missing from the metadata response.
**Root cause:** When using Supabase as the OAuth provider, the `oauth-protected-resource` metadata pointed to Supabase's auth server directly. Supabase does not implement RFC 7591 Dynamic Client Registration, so there is no `registration_endpoint` in its metadata. The MCP server must proxy this endpoint itself (e.g., mcp-use's `SupabaseOAuthProvider` needs `getRegistrationEndpoint()` to return a server-hosted DCR endpoint).
**Fix applied:** Added to Common Pitfalls table and OAuth debugging checklist with explanation of when DCR is server-side vs provider-side.

### F-04: Supabase OAuth parameter incompatibilities

**Severity:** High
**What happened:** Even after fixing DCR, the authorization and token exchange flows broke in multiple places because Supabase's OAuth API uses non-standard parameter names.
**Root cause:** Four distinct incompatibilities:
1. **`provider` parameter missing:** Supabase's `/auth/v1/authorize` requires `provider=google` (or whichever social provider). Standard OAuth clients like mcpc do not send this.
2. **`redirect_uri` vs `redirect_to`:** Supabase expects `redirect_to`, not the standard `redirect_uri` parameter. Without mapping, Supabase ignores the redirect and falls back to the Dashboard's "Site URL".
3. **`client_id` forwarding:** If the MCP server's DCR-generated `client_id` is forwarded to Supabase's authorize endpoint, Supabase passes it to Google, which rejects it as an unknown client.
4. **Token exchange body format:** Supabase's `/auth/v1/token?grant_type=pkce` expects a JSON body (`{"auth_code":"...","code_verifier":"..."}`), not `application/x-www-form-urlencoded` which is the OAuth standard. It also needs the `apikey` header (Supabase anon key).
**Fix applied:** Added "Supabase-specific OAuth traps" subsection and individual entries in Common Pitfalls.

### F-05: mcpc callback server internals — wrong assumptions

**Severity:** Medium
**What happened:** When debugging the callback failure, the agent assumed mcpc used Hono (because the MCP server uses Hono). This led to wrong debugging approaches (looking for Hono routes, middleware issues).
**Root cause:** mcpc's callback server is a raw Node.js `http.createServer()` binding `127.0.0.1`. It only handles the `/callback` path. Its 404 response is plain text `Not found` (not JSON). Knowing this is essential for distinguishing mcpc's responses from interceptors.
**Diagnostic:** Plain text `Not found` = mcpc's own 404 (wrong path). JSON `{"detail":"Not Found"}` = foreign process (port conflict). HTML with auth error = reached mcpc but code exchange failed.
**Fix applied:** Added callback server internals to OAuth deep dive section.

### F-06: Supabase redirect URL configuration

**Severity:** Medium
**What happened:** After fixing all parameter mappings, Supabase redirected to the production Site URL instead of `http://localhost:8000/callback` because the redirect URL was not whitelisted.
**Root cause:** Supabase Dashboard > Authentication > URL Configuration > Redirect URLs must include a pattern matching the callback. Without it, Supabase silently falls back to the Site URL. The required pattern: `http://localhost:*/**`.
**Fix applied:** Added to OAuth debugging checklist.

### F-07: mcp-use deploy uses git clone, not local files

**Severity:** Medium
**What happened:** Multiple deploy cycles were wasted because code changes (OAuth endpoint fixes, parameter mappings) were not taking effect after `mcp-use deploy`.
**Root cause:** `mcp-use deploy` clones the repository from GitHub rather than uploading local files. Uncommitted or unpushed changes are invisible to the deployment. This is similar to how Vercel/Railway work but was not called out in the skill.
**Fix applied:** Added to Common Pitfalls and OAuth debugging checklist as a deployment trap.

---

## Meta-observations

1. **The skill was optimized for the happy path.** Every OAuth example was "run `mcpc login`, then connect." Zero coverage of what happens when login fails partway through.
2. **Provider-specific traps need dedicated sections.** Supabase is a common OAuth backend for MCP servers (mcp-use recommends it). The skill should call out provider-specific pitfalls explicitly.
3. **Port conflicts are environment-specific but predictable.** OrbStack is extremely popular among macOS developers. Docker Desktop uses different ports but could cause similar issues. The skill needs a pre-flight port check.
4. **Response format fingerprinting is a powerful diagnostic.** Knowing that mcpc returns plain text while OrbStack returns JSON immediately identifies port conflicts. This kind of "know your tools' signatures" guidance was missing.
