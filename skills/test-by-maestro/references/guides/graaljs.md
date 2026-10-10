# GraalJS Scripting Runtime and Data Handling

Maestro embeds the Oracle Truffle GraalJS polyglot engine (GraalJS 24.2.0, `js.strict: true`) to execute JavaScript for dynamic data generation, API pre-flight requests, and conditional evaluation. Rhino was completely removed in Maestro 2.6.0.

---

## Engine Constraints and Runtime Model

The embedded GraalJS runtime differs significantly from standard browser or Node.js environments:

| Capability | Supported? | Details / Alternative |
|---|---|---|
| Synchronous Execution | **Yes** | All script statements execute sequentially and synchronously. |
| `async` / `await` | **No** | Asynchronous keywords, Promises, and event-loop scheduling are unsupported. |
| `fetch()` | **No** | Use the built-in synchronous `http` client (`http.get`, `http.post`, etc.). |
| Node.js APIs (`fs`, `path`, `require`) | **No** | No file system, process, or Node module resolution. |
| Browser DOM (`window`, `document`) | **No** | No web DOM or browser window globals. |
| Undeclared Variable Tolerance | **Yes** | A prototype Proxy on `globalThis` intercepts property accesses, returning `undefined` rather than throwing `ReferenceError`. Safe for `${VAR || 'fallback'}`. |
| IIFE Evaluation Scoping | **Yes** | External scripts and expressions are evaluated inside an IIFE (`evalWithIIFE`). Values must be assigned to `output` to persist across flow steps. |

---

## Injected HTTP Client (`maestro.js.GraalJsHttp`)

Maestro injects a synchronous `http` client backed by OkHttp:

```javascript
// scripts/fetch-test-token.js
var apiUrl = typeof API_BASE_URL !== "undefined" ? API_BASE_URL : "http://localhost:8080";

var response = http.get(apiUrl + "/api/v1/auth/mock-token", {
  headers: {
    "Accept": "application/json"
  }
});

if (!response.ok) {
  throw new Error("HTTP request failed with status: " + response.status);
}

// json() is a built-in helper equivalent to JSON.parse()
var payload = json(response.body);
output.AUTH_TOKEN = payload.token;
output.USER_EMAIL = payload.user.email;
```

### Critical HTTP Method Signatures

All HTTP mutation methods strictly take **at most two arguments** `(url, options)`:

- `http.get(url, options)`
- `http.post(url, options)`
- `http.put(url, options)`
- `http.delete(url, options)`
- `http.request(url, options)`

> **Warning**: Do not pass separate `body` and `headers` positional arguments (e.g. `http.post(url, body, headers)`). Passing three arguments causes runtime errors. `body`, `headers`, and `multipartForm` must be keys inside the `options` map.

#### POST Request with JSON Body:
```javascript
var postResponse = http.post("https://api.example.com/v1/login", {
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + output.API_KEY
  },
  body: JSON.stringify({
    username: "testuser",
    password: "Password123!"
  })
});

if (postResponse.ok) {
  var data = json(postResponse.body);
  output.SESSION_ID = data.sessionId;
}
```

#### POST with Multipart Form (File Upload):
File parts must be passed as an object containing `filePath` (resolved relative to the executing script directory) and an optional `mediaType`. Non-file form fields are passed directly as strings:

```javascript
var uploadResponse = http.post("https://api.example.com/v1/upload", {
  headers: {
    "Authorization": "Bearer " + output.AUTH_TOKEN
  },
  multipartForm: {
    file: {
      filePath: "fixtures/avatar.png",   // Resolved relative to current script directory
      mediaType: "image/png"             // Optional MIME type
    },
    userId: "1042"                       // Standard string form field
  }
});
```

### HTTP Response Object Schema
The response object returned by `http` methods contains:
- `ok`: Boolean (`true` if status code is in 200–299 range)
- `status`: Integer HTTP response code (e.g. `200`, `401`, `500`)
- `body`: Raw String response payload (parse with `json(res.body)` or `JSON.parse(res.body)`)
- `headers`: Map of response header keys and values

---

## Embedded Synthetic Data Generator (`faker`)

Maestro bundles `net.datafaker.Faker` (Datafaker 2.5.3) and injects it into the global GraalJS scope as `faker`. You can generate realistic test data immediately without external HTTP dependencies:

```javascript
// scripts/generate-test-user.js
output.FIRST_NAME = faker.name().firstName();
output.LAST_NAME = faker.name().lastName();
output.FULL_NAME = faker.name().fullName();
output.EMAIL = faker.internet().emailAddress();
output.PHONE = faker.phoneNumber().cellPhone();
output.STREET = faker.address().streetAddress();
output.CITY = faker.address().cityName();
output.ZIP = faker.address().zipCode();
output.VERIFICATION_CODE = faker.number().digits(6);
```

In your flow YAML:
```yaml
- runScript: scripts/generate-test-user.js
- tapOn:
    id: "name_input"
- inputText: ${output.FULL_NAME}
- tapOn:
    id: "email_input"
- inputText: ${output.EMAIL}
```

---

## Injected Global Helpers & Platform Bindings

### 1. `maestro` Global Object
- **`maestro.platform`**: Returns the active platform identifier string: `"android"`, `"ios"`, or `"web"`.
  ```javascript
  if (maestro.platform === "ios") {
    output.BUTTON_ID = "apple_pay_btn";
  } else {
    output.BUTTON_ID = "google_pay_btn";
  }
  ```
- **`maestro.copiedText`**: Contains text extracted via `copyTextFrom` or `setClipboard`.
  ```javascript
  var promoCode = maestro.copiedText;
  output.CLEAN_CODE = promoCode.trim().toUpperCase();
  ```

### 2. Built-in Parsing and Coordinate Helpers
- **`json(string)`**: Built-in JSON parser wrapper for `JSON.parse(string)`.
- **`relativePoint(x, y)`**: Formats fractional coordinates (0.0 to 1.0) into percentage strings:
  ```javascript
  var pt = relativePoint(0.5, 0.8); // Returns "50%,80%"
  ```

---

## Output Sharing between Scripts and Flows

Data generated in JavaScript is shared with YAML flows via the global `output` object. Any property assigned to `output.KEY` becomes accessible in subsequent flow steps as `${output.KEY}`:

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

---

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

---

## Script File Resolution Rules

- Script paths specified in `runScript.file` resolve **relative to the YAML flow file** declaring the command.
- Keep helper scripts in a `scripts/` directory adjacent to your flow files to maintain modular workspace portability.

---

## Related References

- [Flows and Selectors](../commands/flows-and-selectors.md) — Command structure and `${}` variable interpolation.
- [Expo and State](../troubleshooting/expo-and-state.md) — Auth state handling and session persistence.
- [Mobile Flakiness](../troubleshooting/mobile-flakiness.md) — Handling dynamic inputs and timing flakes.
