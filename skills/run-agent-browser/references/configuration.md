# Configuration

agent-browser uses a layered configuration system. Settings merge from lowest to highest priority.

## Config File Locations

| Priority | Location | Scope |
|----------|----------|-------|
| 1 (lowest) | `~/.agent-browser/config.json` | User-level defaults |
| 2 | `./agent-browser.json` | Project-level overrides |
| 3 | `AGENT_BROWSER_*` env vars | Override config values |
| 4 (highest) | CLI flags | Override everything |

Custom config file:

```bash
agent-browser --config <path> open example.com
# or
AGENT_BROWSER_CONFIG=./my-config.json agent-browser open example.com
```

## All Config Options

Config keys are camelCase equivalents of CLI flags.

| Key | Type | Description |
|-----|------|-------------|
| `headed` | boolean | Run browser in headed mode |
| `json` | boolean | Output results as JSON |
| `full` | boolean | Full page content |
| `debug` | boolean | Enable debug logging |
| `session` | string | Session name to use |
| `sessionName` | string | Persistent session name |
| `executablePath` | string | Path to browser executable |
| `extensions` | string[] | Browser extensions to load |
| `profile` | string | Browser profile directory |
| `state` | string | State file path |
| `proxy` | string | Proxy server URL |
| `proxyBypass` | string | Proxy bypass rules |
| `args` | string | Extra browser args (comma-separated) |
| `userAgent` | string | Custom user agent string |
| `provider` | string | Browser provider |
| `device` | string | Device emulation |
| `ignoreHttpsErrors` | boolean | Ignore HTTPS certificate errors |
| `allowFileAccess` | boolean | Allow file:// URLs |
| `cdp` | string | Chrome DevTools Protocol URL |
| `autoConnect` | boolean | Auto-connect to running browser |
| `colorScheme` | string | Preferred color scheme |
| `downloadPath` | string | Download directory path |
| `contentBoundaries` | boolean | Enable content boundaries |
| `maxOutput` | number | Maximum output size |
| `allowedDomains` | string[] | Restrict navigation to domains |
| `actionPolicy` | string | Path to action policy file |
| `confirmActions` | string[] | Actions requiring confirmation |
| `confirmInteractive` | boolean | Confirm interactive actions |
| `engine` | string | Browser engine (chrome\|lightpanda) |
| `native` | boolean | Use native browser features |
| `headers` | object | Custom request headers |

## Common Configurations

### Local Development

```json
{
  "headed": true,
  "profile": "./browser-data"
}
```

### Behind a Proxy

```json
{
  "proxy": "http://proxy.corp.example.com:8080",
  "proxyBypass": "localhost,*.internal.com",
  "ignoreHttpsErrors": true
}
```

### CI / Devcontainer

```json
{
  "args": "--no-sandbox,--disable-gpu",
  "ignoreHttpsErrors": true
}
```

### iOS Testing

```json
{
  "provider": "ios",
  "device": "iPhone 16 Pro"
}
```

### AI Agent Security

```json
{
  "contentBoundaries": true,
  "maxOutput": 50000,
  "allowedDomains": ["your-app.com", "*.your-app.com"],
  "actionPolicy": "./policy.json"
}
```

## Boolean Overrides

Boolean flags default to `true` when used bare. To explicitly disable:

```bash
agent-browser --headed false open example.com
```

Applies to: `--headed`, `--debug`, `--json`, `--ignore-https-errors`, `--allow-file-access`, `--auto-connect`, `--content-boundaries`, `--confirm-interactive`, `--native`

## Extensions Merging

Extensions from user-level (`~/.agent-browser/config.json`) and project-level (`./agent-browser.json`) configs are **concatenated**, not replaced. Both sets of extensions load together.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENT_BROWSER_AUTO_CONNECT` | Auto-connect to running browser |
| `AGENT_BROWSER_ALLOW_FILE_ACCESS` | Allow file:// URLs |
| `AGENT_BROWSER_COLOR_SCHEME` | Preferred color scheme |
| `AGENT_BROWSER_DOWNLOAD_PATH` | Download directory |
| `AGENT_BROWSER_DEFAULT_TIMEOUT` | Default timeout in ms (default: 25000, keep below 30000) |
| `AGENT_BROWSER_SESSION_NAME` | Persistent session name |
| `AGENT_BROWSER_STATE_EXPIRE_DAYS` | Days before state auto-expires (default: 30) |
| `AGENT_BROWSER_ENCRYPTION_KEY` | 64-char hex key for AES-256-GCM state encryption |
| `AGENT_BROWSER_EXTENSIONS` | Browser extensions to load |
| `AGENT_BROWSER_HEADED` | Run in headed mode |
| `AGENT_BROWSER_STREAM_PORT` | Streaming port |
| `AGENT_BROWSER_IOS_DEVICE` | iOS device name |
| `AGENT_BROWSER_IOS_UDID` | iOS device UDID |
| `AGENT_BROWSER_DEBUG` | Enable debug logging |
| `AGENT_BROWSER_CONTENT_BOUNDARIES` | Enable content boundaries |
| `AGENT_BROWSER_MAX_OUTPUT` | Maximum output size |
| `AGENT_BROWSER_ALLOWED_DOMAINS` | Restrict navigation to domains |
| `AGENT_BROWSER_ACTION_POLICY` | Path to action policy file |
| `AGENT_BROWSER_CONFIRM_ACTIONS` | Actions requiring confirmation |
| `AGENT_BROWSER_CONFIRM_INTERACTIVE` | Confirm interactive actions |
| `AGENT_BROWSER_ENGINE` | Browser engine (chrome\|lightpanda) |
| `AGENT_BROWSER_NATIVE` | Use native browser features |

## Error Handling

- **Auto-discovered configs** (`~/.agent-browser/config.json`, `./agent-browser.json`): missing files are silently ignored
- **`--config <path>`**: missing or malformed file causes an error exit
- **Malformed JSON** in auto-discovered configs: warning printed to stderr, execution continues
- **Unknown keys**: silently ignored
