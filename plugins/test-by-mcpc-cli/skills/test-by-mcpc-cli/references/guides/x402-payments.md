# x402 Payments

`mcpc` 0.6.0 exposes x402 wallet management and payment signing directly (still labeled EXPERIMENTAL). Verified against 0.6.0 (`mcpc help x402`, `mcpc x402`).

## Safety boundary

The commands below describe syntax, not authorization. Use an isolated `MCPC_HOME_DIR` and prefer `x402 init` with a throwaway Base Sepolia wallet for tests. Obtain explicit authorization before importing/removing a wallet, signing a challenge, enabling `--x402`, spending funded assets, or allowing Permit2 approval. `mcpc 0.6.0` accepts imported keys only as the positional `x402 import <private-key>` argument — it has no stdin, file, environment-variable, or interactive secret-input option — so do not import a real production key for routine testing. If an owner explicitly accepts that argv/history exposure for a necessary import, use a restricted ephemeral host and keep the command out of logs, examples, and committed scripts. The `upto` flow can grant `MAX_UINT256` allowance and may cost gas.

## Wallet commands

```bash
mcpc x402 init
mcpc x402 import <private-key>
mcpc x402
mcpc x402 sign <payment-required>
mcpc x402 sign <payment-required> --amount 0.10 --expiry 120
mcpc x402 sign <payment-required> --scheme upto --no-approve
mcpc x402 remove
```

Bare `mcpc x402` shows wallet address, ETH/USDC balances, and a funding QR code — replaced the `info` subcommand in 0.5.0. `x402 info` is deprecated, no longer listed in `mcpc help x402`; use bare `mcpc x402`. With no wallet, it prints a hint to run `x402 init` and exits 0 (not an error).

## Payment schemes

`sign` and `connect --x402` both take a scheme preference: `auto` (default, prefers `upto`), `upto`, `exact`.

- `exact` — EIP-3009 `TransferWithAuthorization`, settles on-chain at call time.
- `upto` — Permit2 `PermitWitnessTransferFrom`; sign a max cap, facilitator settles usage later. First `upto` sign auto-grants a one-time on-chain `USDC.approve(PERMIT2, MAX_UINT256)` allowance (costs gas); `--no-approve` skips that check.

## Connect with auto-payment

```bash
mcpc connect https://mcp.example.com/mcp @paid --x402
mcpc connect https://mcp.example.com/mcp @paid --x402 upto
mcpc connect https://mcp.example.com/mcp @paid-oauth --x402 --profile default
```

`--x402 [scheme]` flag position is unrestricted; bare `--x402` = `auto`. Scheme persists to `sessions.json`, reused on `restart`. x402 sessions show a yellow `[x402]` marker in listings.

Important current rule:

- `--x402` skips default OAuth profile auto-detection, but — unlike `-H`/`--header` — it **can** combine with `--profile` to use both.

## Current header and metadata names

- challenge header: `PAYMENT-REQUIRED`
- signed response header: `PAYMENT-SIGNATURE`
- proactive pricing field on tool definitions: `_meta.x402` — tools that advertise pricing there are signed before the first call, skipping the 402 round-trip
- supported networks: Base Mainnet and Base Sepolia testnet only

Do not document `X-PAYMENT` (the generic x402-spec header) as mcpc's header, and do not invent sub-fields (`payTo`, `asset`, `paymentRequired`) for `_meta.x402` — none are documented; verify shape against a live `PAYMENT-REQUIRED` header instead.

## Storage note

Wallet storage prefers OS keychain integration and falls back to `~/.mcpc/wallets.json` (`0600`) when keychain storage is unavailable.
