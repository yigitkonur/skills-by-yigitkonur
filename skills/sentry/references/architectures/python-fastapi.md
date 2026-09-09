# Architecture: Python & FastAPI Sentry Integration

How to instrument Python FastAPI / Flask services with Sentry, envelope tunneling, and contextual tagging.

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
project_id = dsn.split("/")[-1] if dsn else None
tunnel_url = f"https://sentry.io/api/{project_id}/envelope/" if project_id else None

sentry_sdk.init(
    dsn=dsn,
    tunnel=tunnel_url,
    integrations=[
        StarletteIntegration(transaction_style="endpoint"),
        FastApiIntegration(transaction_style="endpoint"),
    ],
    traces_sample_rate=1.0,
    environment=os.getenv("ENVIRONMENT", "production"),
)

app = FastAPI()

@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id")
    if request_id:
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("requestId", request_id)
    response = await call_next(request)
    return response

@app.get("/health")
def health():
    return {"status": "ok"}
```
