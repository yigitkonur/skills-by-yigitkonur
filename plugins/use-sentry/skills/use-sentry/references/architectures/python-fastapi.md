# Architecture: Python & FastAPI Sentry Integration

How to instrument Python FastAPI / Starlette / Flask services with Sentry, context propagation, and continuous profiling.

## Installation

```bash
pip install sentry-sdk
```

## FastAPI Setup (`main.py`)

```python
import os
import sentry_sdk
from fastapi import FastAPI, Request
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

dsn = os.getenv("SENTRY_DSN")

sentry_sdk.init(
    dsn=dsn,
    integrations=[
        StarletteIntegration(transaction_style="endpoint"),
        FastApiIntegration(transaction_style="endpoint"),
    ],
    traces_sample_rate=1.0,
    # Continuous Profiling
    profiles_sample_rate=1.0,
    environment=os.getenv("ENVIRONMENT", "production"),
    # Forward traces locally to Spotlight in development
    spotlight=os.getenv("ENVIRONMENT") == "development",
)

app = FastAPI()

@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id")
    if request_id:
        # Modern sentry-sdk 2.x API for setting tags on the active isolation scope
        sentry_sdk.set_tag("requestId", request_id)
    response = await call_next(request)
    return response

@app.get("/health")
def health():
    return {"status": "ok"}
```

## Corporate Egress Proxies

If your backend is behind an enterprise firewall or HTTP forward proxy, set standard environment variables or configure `proxy`:

```python
# Sentry automatically respects HTTP_PROXY and HTTPS_PROXY environment variables
# Alternatively, specify explicitly:
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    proxy=os.getenv("HTTPS_PROXY"),
)
```
