# x402 Agentic Payment Testing

Test MCP servers that charge for tool calls using the x402 HTTP payment protocol.

## What x402 is

x402 is an HTTP-native payment protocol for machine-to-machine transactions. It uses EIP-3009 (`TransferWithAuthorization`) to sign USDC transfer authorizations off-chain, which the server verifies and settles on-chain.

### Key properties

| Property | Value |
|---|---|
| Token | USDC |
| Chain (production) | Base Mainnet (`eip155:8453`) |
| Chain (testnet) | Base Sepolia (`eip155:84532`) |
| Signing standard | EIP-3009 TransferWithAuthorization |
| Settlement | On-chain via facilitator contract |
| Client action | Sign authorization; no gas fees |
| Server action | Submit to facilitator for settlement |

### Two signing modes

**Proactive signing**: The tool's metadata (`_meta.x402`) declares upfront that payment is required. mcpc signs the payment authorization _before_ sending the tool call.

**Reactive signing**: The server returns HTTP 402 with a `PAYMENT-REQUIRED` header containing payment details. mcpc parses the requirement, signs, and retries automatically.

Both modes are transparent to the user when `--x402` is enabled on the session.

## Wallet management

Before using x402, you need a wallet. mcpc manages wallets independently from sessions.

### Initialize a new wallet

```bash
# Generate a new random wallet
mcpc x402 init
# Output: wallet address (0x...) and confirmation
# Private key stored in ~/.mcpc/wallets.json
```

### Import an existing wallet

```bash
# Import from private key
mcpc x402 import 0xYOUR_PRIVATE_KEY_HEX

# Useful for testnet wallets with pre-funded USDC
```

### Check wallet info

```bash
# Show wallet address and network
mcpc x402 info
# Output: address, chain, balance info
```

### Remove wallet

```bash
# Delete wallet from local storage
mcpc x402 remove
# Removes private key from ~/.mcpc/wallets.json
```

### Wallet storage

The private key is stored in `~/.mcpc/wallets.json` with file permissions `0600` (owner read/write only):

```json
{
  "privateKey": "0x...",
  "address": "0x..."
}
```

On systems with OS keychains (macOS Keychain, Linux Secret Service), mcpc may use the keychain instead.

## Connecting with payment support

### Enable x402 on a session

```bash
# Connect with x402 enabled
mcpc https://paid-server.com connect @paid --x402

# Combine with authentication
mcpc https://paid-server.com connect @paid \
  --x402 \
  --header "Authorization: Bearer $TOKEN"

# Combine with OAuth
mcpc login https://paid-server.com
mcpc https://paid-server.com connect @paid --x402
```

The `--x402` flag tells the bridge to:
1. Load the wallet from `~/.mcpc/wallets.json`
2. Check tool metadata for proactive payment requirements
3. Listen for 402 responses for reactive payment requirements
4. Auto-sign and inject payment headers/body when needed

### Without x402 flag

If you connect without `--x402` and call a paid tool:
- Proactive: the tool call is sent without payment; server may reject with 402 or an error
- Reactive: server returns 402; mcpc has no wallet to sign with, so it reports an error

## Payment flow details

### Proactive flow

```
1. mcpc fetches tool metadata (tools/list with _meta)
2. Tool has _meta.x402.paymentRequired = true
3. mcpc reads _meta.x402.maxAmountRequired for the max USDC cost
4. mcpc signs EIP-3009 TransferWithAuthorization:
   - from: wallet address
   - to: server's payment address
   - value: maxAmountRequired
   - validAfter: now
   - validBefore: now + 1 hour (default)
   - nonce: random 32 bytes
5. Payment signature injected as:
   - HTTP header: X-PAYMENT (base64-encoded payment payload)
   - JSON-RPC params._meta.x402.payment (same payload, inline)
6. Server verifies signature and processes tool call
7. Server submits authorization to facilitator for on-chain settlement
```

### Reactive flow

```
1. mcpc sends tool call without payment
2. Server returns HTTP 402 Payment Required
3. Response includes payment details:
   - PAYMENT-REQUIRED header (or JSON body)
   - Contains: payTo address, amount, network, facilitator address
4. mcpc signs EIP-3009 authorization using the provided details
5. mcpc retries the tool call with payment signature attached
6. Server processes and settles
```

## Testing paid tools

### Discover which tools require payment

```bash
# List all tools with full metadata (need --full for _meta)
mcpc --json @paid tools-list --full | jq '
  [.[] | select(._meta.x402.paymentRequired == true) |
    {name, maxCost: ._meta.x402.maxAmountRequired}]
'

# Check a specific tool
mcpc --json @paid tools-get premium-search | jq '._meta.x402'

# List free vs paid tools
echo "=== Free tools ==="
mcpc --json @paid tools-list --full | jq -r '
  [.[] | select(._meta.x402.paymentRequired != true)] | .[].name'

echo "=== Paid tools ==="
mcpc --json @paid tools-list --full | jq -r '
  [.[] | select(._meta.x402.paymentRequired == true)] | .[].name'
```

### Call a paid tool

```bash
# Call paid tool (payment is auto-signed if --x402 was used on connect)
mcpc --json @paid tools-call premium-search query:=test

# The response is identical to a free tool call:
# {"content": [{"type": "text", "text": "..."}], "isError": false}

# Check the result
mcpc --json @paid tools-call premium-search query:=test | jq -r '.content[0].text'
```

### Test payment failure scenarios

```bash
# 1. Call paid tool without --x402 on session
mcpc https://paid-server.com connect @no-pay
mcpc --json @no-pay tools-call premium-search query:=test 2>&1
# Expected: error (402 or auth error depending on server)
mcpc @no-pay close

# 2. Call paid tool with empty wallet (no USDC balance)
# The signature is valid but settlement will fail on-chain
# Server behavior varies: some check balance before processing,
# others process and settle asynchronously
mcpc --json @paid tools-call premium-search query:=test 2>&1

# 3. Call free tool on a server with paid tools (should work without payment)
mcpc --json @paid tools-call free-health-check
```

### Verify payment metadata structure

```bash
# Full x402 metadata for a paid tool
mcpc --json @paid tools-get premium-search | jq '._meta.x402'

# Expected structure:
# {
#   "paymentRequired": true,
#   "maxAmountRequired": "100000",   (USDC in smallest unit, 6 decimals)
#   "network": "eip155:8453",
#   "payTo": "0x...",
#   "facilitator": "0x..."
# }

# Validate required fields exist
mcpc --json @paid tools-get premium-search | jq '
  ._meta.x402 |
  if .paymentRequired and .maxAmountRequired and .network and .payTo
  then "VALID"
  else "INVALID: missing required x402 fields"
  end
'
```

### Interpret payment amounts

```bash
# USDC has 6 decimal places
# "100000" = 0.10 USDC
# "1000000" = 1.00 USDC

# Convert to human-readable
mcpc --json @paid tools-list --full | jq '
  [.[] | select(._meta.x402.paymentRequired) |
    {
      name,
      cost_usdc: (._meta.x402.maxAmountRequired | tonumber / 1000000),
      cost_raw: ._meta.x402.maxAmountRequired
    }]
'
```

## Security considerations

### Private key protection

| Aspect | Implementation |
|---|---|
| Storage location | `~/.mcpc/wallets.json` |
| File permissions | `0600` (owner only) |
| Key format | Raw 32-byte hex with `0x` prefix |
| Backup | User's responsibility; mcpc does not back up keys |
| Removal | `mcpc x402 remove` deletes from disk |

### Payment authorization limits

Each signed authorization includes:

| Field | Purpose | Default |
|---|---|---|
| `value` | Maximum transfer amount | Matches tool's `maxAmountRequired` |
| `validAfter` | Earliest valid timestamp | Current time |
| `validBefore` | Latest valid timestamp | Current time + 1 hour |
| `nonce` | Unique random value | 32 random bytes per payment |

The `validBefore` window limits the risk of authorization replay. Each authorization can only be used once (nonce is consumed on-chain).

### Testnet vs mainnet

```bash
# Check which network the server expects
mcpc --json @paid tools-get premium-search | jq '._meta.x402.network'

# eip155:84532 → Base Sepolia (testnet) — safe for testing
# eip155:8453  → Base Mainnet — real USDC at stake
```

For testing, use a testnet wallet with testnet USDC. Never use a mainnet wallet with real funds for test automation.

### CI/CD with x402

x402 in CI requires a funded wallet private key as a secret:

```yaml
- name: Setup x402 wallet
  env:
    X402_PRIVATE_KEY: ${{ secrets.X402_TESTNET_PRIVATE_KEY }}
  run: mcpc x402 import "$X402_PRIVATE_KEY"

- name: Test paid tools
  run: |
    mcpc https://paid-server.com connect @paid --x402
    mcpc --json @paid tools-call premium-search query:=test
    mcpc @paid close
```

Use a dedicated testnet wallet for CI with limited funds. Monitor the wallet balance and top up as needed.

## Complete x402 test script

```bash
#!/bin/bash
set -euo pipefail

SERVER="${1:?Usage: $0 <server-url>}"
SESSION="x402-test-$$"

cleanup() { mcpc "@$SESSION" close 2>/dev/null || true; }
trap cleanup EXIT

export MCPC_JSON=1

echo "=== x402 Payment Test ==="

# Verify wallet exists
if ! mcpc x402 info > /dev/null 2>&1; then
  echo "FAIL: No x402 wallet configured. Run: mcpc x402 init"
  exit 1
fi
echo "Wallet: $(mcpc x402 info | jq -r '.address')"

# Connect with x402
mcpc "$SERVER" connect "@$SESSION" --x402

# Discover paid tools
PAID_TOOLS=$(mcpc "@$SESSION" tools-list --full | jq '[.[] | select(._meta.x402.paymentRequired)]')
PAID_COUNT=$(echo "$PAID_TOOLS" | jq 'length')
echo "Found $PAID_COUNT paid tool(s)"

if [ "$PAID_COUNT" -eq 0 ]; then
  echo "No paid tools found — nothing to test"
  exit 0
fi

# List paid tools and costs
echo "$PAID_TOOLS" | jq -r '.[] | "  \(.name): \(._meta.x402.maxAmountRequired | tonumber / 1000000) USDC"'

# Test first paid tool (optional — uncomment to actually pay)
# FIRST_TOOL=$(echo "$PAID_TOOLS" | jq -r '.[0].name')
# echo "Calling paid tool: $FIRST_TOOL"
# mcpc "@$SESSION" tools-call "$FIRST_TOOL" | jq '.isError'

echo "=== x402 test complete ==="
```

## Troubleshooting x402

| Symptom | Cause | Fix |
|---|---|---|
| "No wallet configured" | No wallet in `~/.mcpc/wallets.json` | Run `mcpc x402 init` or `mcpc x402 import` |
| 402 Payment Required (not auto-handled) | Session not connected with `--x402` | Reconnect: `mcpc <server> connect @s --x402` |
| Payment rejected by server | Insufficient USDC balance or wrong network | Check balance; verify network matches server expectation |
| "Invalid signature" | Wallet address mismatch or corrupt key | Re-import wallet: `mcpc x402 remove && mcpc x402 import 0xKEY` |
| Tool call succeeds but settlement fails | On-chain issue (gas, facilitator) | Server-side issue; check with server operator |
| `wallets.json` permission error | File permissions too open | `chmod 600 ~/.mcpc/wallets.json` |
