# GraalJS Scripting Runtime and Data Handling

Maestro embeds the Oracle GraalJS polyglot engine to execute JavaScript for dynamic data generation, API pre-flight requests, and conditional evaluation.

## Engine Constraints and Runtime Model

The embedded GraalJS runtime differs significantly from standard browser or Node.js environments:

| Capability | Supported? | Details / Alternative |
|---|---|---|
| Synchronous Execution | **Yes** | All script statements execute sequentially. |
| `async` / `await` | **No** | Asynchronous keywords and Promises are unsupported. |
| `fetch()` | **No** | Use the built-in synchronous `http` client. |
| Node.js APIs (`fs`, `path`) | **No** | No file system or Node runtime modules. |
| Variable Scope | `var` | Use `var` for declarations across script evaluation scopes. |

## Injected HTTP Client and JSON Parsing

Maestro injects a synchronous `http` object for network interactions:

```javascript
// scripts/fetch-test-token.js
var apiUrl = typeof API_BASE_URL !== "undefined" ? API_BASE_URL : "http://localhost:8080";

var response = http.get(apiUrl + "/api/v1/auth/mock-token");
if (!response.ok) {
  throw new Error("HTTP request failed with status: " + response.status);
}

var payload = json(response.body);
output.AUTH_TOKEN = payload.token;
output.USER_EMAIL = payload.user.email;
```

### Supported HTTP Methods

- `http.get(url, headers)`
- `http.post(url, body, headers)`
- `http.put(url, body, headers)`
- `http.delete(url, headers)`
- `http.request(options)`

## Output Sharing between Scripts and Flows

Data generated in JavaScript is shared with YAML flows via the global `output` object. Any property set on `output.KEY` becomes accessible in flow steps as `${output.KEY}`:

```yaml
# flows/auth-with-token.yaml
appId: com.example.demo
---
- runScript:
    file: scripts/fetch-test-token.js
    env:
      API_BASE_URL: "https://staging.example.com"

- tapOn:
    id: "token_input"
- inputText: ${output.AUTH_TOKEN}
- tapOn: "Verify"
- assertVisible: "Token accepted"
```

## Inline Expressions and `evalScript`

### 1. Inline String Interpolation

Use `${}` directly in command strings for basic dynamic expressions:

```yaml
- inputText: user_${Date.now()}@example.com
```

### 2. Computing Values with `evalScript`

Use `evalScript` to compute or transform values inline without an external script file:

```yaml
- evalScript: ${output.randomCode = Math.floor(100000 + Math.random() * 900000).toString()}
- inputText: ${output.randomCode}
```

> **Caution**: Do not use template literals (backticks) inside `evalScript`, as `evalScript` itself wraps the expression in `${}`. Use string concatenation instead.

## Script File Resolution Rules

- Script paths specified in `runScript.file` resolve **relative to the YAML flow file** declaring the command.
- Keep helper scripts in a `scripts/` directory adjacent to your flow files to maintain modular workspace portability.

## Related References

- [Flows and Selectors](../commands/flows-and-selectors.md) — Command structure and `${}` variable interpolation.
- [Expo and State](../troubleshooting/expo-and-state.md) — Auth state handling and session persistence.
