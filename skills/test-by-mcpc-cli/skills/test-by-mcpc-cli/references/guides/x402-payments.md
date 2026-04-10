# x402 Payments

`mcpc 0.2.x` exposes x402 wallet management and payment signing directly.

## Wallet commands

```bash
mcpc x402 init
mcpc x402 import <private-key>
mcpc x402 info
mcpc x402 sign <payment-required>
mcpc x402 sign <payment-required> --amount 0.10 --expiry 120
mcpc x402 remove
```

## Connect with auto-payment

```bash
mcpc connect https://mcp.example.com/mcp @paid --x402
mcpc connect https://mcp.example.com/mcp @paid-oauth --x402 --profile default
```

Important current rule:

- `--x402` skips default OAuth profile auto-detection unless `--profile` is explicit

So `login` followed by `connect --x402` is not enough when the server also requires OAuth, unless you add `--profile`.

## Current header and metadata names

- challenge header: `PAYMENT-REQUIRED`
- signed response header: `PAYMENT-SIGNATURE`
- MCP metadata field: `_meta["x402/payment"]`
- proactive metadata fields include `paymentRequired`, `scheme`, `network`, `amount`, `asset`, and `payTo`

Do not document the old `X-PAYMENT` header or `_meta.x402.payment` path.

## Storage note

Wallet storage prefers OS keychain integration and falls back to `~/.mcpc/wallets.json` when keychain storage is unavailable.
