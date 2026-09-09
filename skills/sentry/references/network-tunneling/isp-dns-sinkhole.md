# ISP DNS Sinkhole & SSL Interception Analysis

Why Sentry event ingestion fails with self-signed certificate errors on certain ISPs and restricted networks, and how to detect it.

## The Phenomenon

In multiple regions—notably Turkey (Türk Telekom / TTNet) and certain corporate or campus firewalls—DNS queries for Sentry's ingest subdomains are hijacked:

```text
Domain: o279668.ingest.us.sentry.io (or *.ingest.sentry.io)
Expected IP: Official Sentry Ingest Anycast / Cloudflare IP
Resolved IP: 195.175.254.2 (TTNet DNS Sinkhole / Interception Gateway)
```

When the Sentry SDK initiates a TLS handshake with `195.175.254.2`, the gateway presents a self-signed certificate issued for the ISP's filtering page rather than a valid DigiCert/Let's Encrypt certificate for `*.sentry.io`.

### The Resulting Runtime Errors

- **Node.js:**
  ```text
  Error: self-signed certificate in certificate chain (DEPTH_ZERO_SELF_SIGNED_CERT)
      at TLSSocket.onConnectSecure (node:_tls_wrap:1674:34)
  ```
- **Browser:**
  ```text
  net::ERR_CERT_AUTHORITY_INVALID
  ```
- **Silent Drop:** Some SDKs catch connection errors internally, causing all error reports, traces, and logs to silently vanish without any console warning.

## How to Test and Prove the Sinkhole

Run this diagnostic probe from the terminal:

```bash
# 1. Resolve the ingest domain IP
dig +short o279668.ingest.us.sentry.io

# If it returns 195.175.254.2 or an ISP captive IP, DNS is sinkholed!

# 2. Check the TLS certificate presented by the server
openssl s_client -connect o279668.ingest.us.sentry.io:443 -servername o279668.ingest.us.sentry.io < /dev/null 2>&1 | grep -E "(CN=|depth=)"
```

Output on a hijacked connection:
```text
depth=0 CN = *.turktelekom.com.tr (or self-signed root)
verify error:num=18:self signed certificate
```

## Solution: Sentry Envelope Tunneling

Never disable TLS verification (`NODE_TLS_REJECT_UNAUTHORIZED=0`), as this compromises the security of the entire process.

Instead, route all envelopes through Sentry's official envelope tunnel endpoint:
`tunnel: https://sentry.io/api/${projectId}/envelope/`

`sentry.io` is never sinkholed and resolves to valid Cloudflare edge IPs with standard trusted certificates.
See `references/network-tunneling/envelope-tunneling.md`.
