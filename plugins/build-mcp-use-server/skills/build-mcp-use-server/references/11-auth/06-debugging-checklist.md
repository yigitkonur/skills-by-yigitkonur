# Debugging OAuth

*Read this when authentication is failing or tokens aren't being validated.*

## Checklist

1. **Token format**: Request includes `Authorization: Bearer <token>` header
   ```bash
   curl -H "Authorization: Bearer eyJ..." https://mcp.example.com/mcp/
   ```

2. **Token validity**: Verify token hasn't expired
   - Check `expiresAt` in `ctx.auth`
   - Decode token: `jwtparse.io` or `jwt.io`
   - Check `exp` claim (Unix seconds)

3. **Provider configuration**: Matches identity provider's settings
   - Clerk: Frontend API URL correct
   - Auth0: Tenant domain correct
   - Keycloak: Server URL and realm correct
   - Supabase: Project ID or full URL correct

4. **JWKS endpoint**: Provider's key signing endpoint is reachable
   ```bash
   curl https://auth.example.com/.well-known/jwks.json
   ```

5. **Audience (`aud`)**: Token's audience claim matches MCP resource URL
   - Default: `https://<Host header>/<basePath>`
   - Override with `resource` option if ambiguous

6. **Issuer (`iss`)**: Token's issuer matches provider's issuer URL
   - Keycloak: `https://keycloak.example.com/realms/production`
   - Auth0: `https://example.us.auth0.com/`

7. **Scopes**: Token includes required scopes
   - Check `ctx.auth.scopes`
   - Compare with `requiredScopes` in provider config

## Inspector Debugging

Inspector mounts at `/mcp/inspector` during `mcp-use dev`:

1. Open `http://localhost:3000/mcp/inspector`
2. Use **Auth** panel to test token validation
3. See full request/response headers and payload

## Curl Testing

Test a tool with a real token:

```bash
# 1. Get a token from your identity provider (e.g., via Clerk dashboard)
TOKEN="eyJ..."

# 2. Call the MCP server
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"arguments":{},"_meta":{}}' \
  https://mcp.example.com/mcp/tools/my-tool/call
```

Expected response: 200 with `CallToolResult`

Actual response: 401 Unauthorized? Check token expiration, audience, issuer, scopes.

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` on all requests | Token missing/invalid/expired | Check token format, expiration, issuer |
| `401` but token is valid elsewhere | Audience mismatch | Override `resource` option with full canonical URL |
| `401` after token refresh | Old token cached | Ensure client sends new token |
| `403` on specific tools | Scope or role missing | Check `ctx.auth.scopes` and user roles in `ctx.auth.user` |

## Logging

Enable debug logging in server config:

```typescript
const server = new MCPServer({
  logging: { level: "debug" }, // or "trace"
  oauth: ...,
});
```

Logs include token claims (truncated for security); use `"trace"` for full headers/bodies.
