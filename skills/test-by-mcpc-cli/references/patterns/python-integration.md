# Python Integration Patterns

Drive mcpc from Python via subprocess for test automation, REST gateways, and batch processing.

## Synchronous wrapper class

This wrapper maps mcpc commands to Python methods, handles JSON parsing, and raises typed exceptions matching mcpc exit codes.

### Exception hierarchy

```python
class McpcError(Exception):
    """Base exception for all mcpc errors."""
    def __init__(self, error_type: str, message: str, code: int, details: dict | None = None):
        self.error_type = error_type
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, error={self.error_type}, message={self})"


class ClientError(McpcError):
    """Exit code 1: invalid args, unknown command, validation failure."""
    pass

class ServerError(McpcError):
    """Exit code 2: tool execution failed, resource not found."""
    pass

class NetworkError(McpcError):
    """Exit code 3: connection failed, timeout, DNS."""
    pass

class AuthError(McpcError):
    """Exit code 4: invalid credentials, 401/403, token expired."""
    pass


ERROR_MAP: dict[int, type[McpcError]] = {
    1: ClientError,
    2: ServerError,
    3: NetworkError,
    4: AuthError,
}
```

### Core Mcpc class

```python
import subprocess
import json
from typing import Any


class Mcpc:
    """Synchronous mcpc CLI wrapper.

    Usage:
        client = Mcpc("my-session")
        tools = client.tools_list()
        result = client.tools_call("search", query="test", limit=10)
    """

    def __init__(self, session: str, timeout: int = 300):
        self.session = session
        self.timeout = timeout

    def _run(self, *args: str, timeout: int | None = None) -> dict | list:
        """Execute an mcpc command and return parsed JSON output."""
        cmd = ["mcpc", "--json", f"@{self.session}", *args]
        effective_timeout = timeout or self.timeout

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=effective_timeout + 10,  # subprocess timeout > mcpc timeout
        )

        if result.returncode != 0:
            try:
                err = json.loads(result.stdout)
            except json.JSONDecodeError:
                err = {"error": "Unknown", "message": result.stderr or result.stdout}

            cls = ERROR_MAP.get(result.returncode, McpcError)
            raise cls(
                error_type=err.get("error", "Unknown"),
                message=err.get("message", f"mcpc exited with code {result.returncode}"),
                code=result.returncode,
                details=err.get("details"),
            )

        if not result.stdout.strip():
            return {}
        return json.loads(result.stdout)

    # --- Tool commands ---

    def tools_list(self, full: bool = False) -> list[dict]:
        """List all tools. Pass full=True for complete schemas."""
        args = ["tools-list"]
        if full:
            args.append("--full")
        return self._run(*args)

    def tools_get(self, name: str) -> dict:
        """Get a single tool's schema."""
        return self._run("tools-get", name)

    def tools_call(self, name: str, timeout: int | None = None, **kwargs: Any) -> dict:
        """Call a tool with keyword arguments.

        Arguments are formatted as key:=value with auto-typing:
        - str values: key:=value
        - int/float values: key:=123
        - bool values: key:=true
        - dict/list values: key:=<json-encoded>
        """
        args = ["tools-call", name]
        for k, v in kwargs.items():
            if isinstance(v, bool):
                args.append(f"{k}:={'true' if v else 'false'}")
            elif isinstance(v, (int, float)):
                args.append(f"{k}:={v}")
            elif isinstance(v, str):
                args.append(f"{k}:={v}")
            else:
                # dict, list, etc — JSON-encode
                args.append(f"{k}:={json.dumps(v)}")
        return self._run(*args, timeout=timeout)

    def tools_call_json(self, name: str, params: dict, timeout: int | None = None) -> dict:
        """Call a tool with a raw JSON parameter dict (piped via stdin)."""
        cmd = ["mcpc", "--json", f"@{self.session}", "tools-call", name]
        result = subprocess.run(
            cmd,
            input=json.dumps(params),
            capture_output=True,
            text=True,
            timeout=(timeout or self.timeout) + 10,
        )
        if result.returncode != 0:
            err = json.loads(result.stdout) if result.stdout.strip() else {}
            cls = ERROR_MAP.get(result.returncode, McpcError)
            raise cls(err.get("error", "Unknown"), err.get("message", ""), result.returncode)
        return json.loads(result.stdout)

    # --- Resource commands ---

    def resources_list(self) -> list[dict]:
        """List all resources."""
        return self._run("resources-list")

    def resources_read(self, uri: str) -> dict:
        """Read a resource by URI."""
        return self._run("resources-read", uri)

    def resources_templates_list(self) -> list[dict]:
        """List resource templates."""
        return self._run("resources-templates-list")

    # --- Prompt commands ---

    def prompts_list(self) -> list[dict]:
        """List all prompts."""
        return self._run("prompts-list")

    def prompts_get(self, name: str, **kwargs: str) -> dict:
        """Get a prompt with arguments."""
        args = ["prompts-get", name]
        for k, v in kwargs.items():
            args.append(f"{k}:={v}")
        return self._run(*args)

    # --- Utility commands ---

    def ping(self) -> dict:
        """Ping the server."""
        return self._run("ping")

    def help(self) -> dict:
        """Get server info and capabilities."""
        return self._run("help")
```

### Usage example

```python
client = Mcpc("my-session")

# List tools
tools = client.tools_list()
for tool in tools:
    print(f"  {tool['name']}: {tool.get('description', '—')}")

# Call a tool
result = client.tools_call("search", query="hello", limit=5)
text = result["content"][0]["text"]
print(f"Result: {text}")

# Error handling
try:
    client.tools_call("nonexistent-tool")
except ClientError as e:
    print(f"Client error: {e}")
except ServerError as e:
    print(f"Server error: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
except AuthError as e:
    print(f"Auth error: {e}")
```

## Async wrapper with asyncio

For concurrent tool calls and non-blocking I/O:

```python
import asyncio
import json
from typing import Any


class AsyncMcpc:
    """Async mcpc CLI wrapper using asyncio.create_subprocess_exec."""

    def __init__(self, session: str, timeout: int = 300):
        self.session = session
        self.timeout = timeout

    async def _run(self, *args: str, timeout: int | None = None) -> dict | list:
        cmd = ["mcpc", "--json", f"@{self.session}", *args]
        effective_timeout = timeout or self.timeout

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=effective_timeout + 10,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise NetworkError("Timeout", f"mcpc timed out after {effective_timeout}s", 3)

        output = stdout.decode()

        if proc.returncode != 0:
            try:
                err = json.loads(output)
            except json.JSONDecodeError:
                err = {"error": "Unknown", "message": output}
            cls = ERROR_MAP.get(proc.returncode, McpcError)
            raise cls(err.get("error", ""), err.get("message", ""), proc.returncode)

        if not output.strip():
            return {}
        return json.loads(output)

    async def tools_list(self, full: bool = False) -> list[dict]:
        args = ["tools-list"]
        if full:
            args.append("--full")
        return await self._run(*args)

    async def tools_call(self, name: str, timeout: int | None = None, **kwargs: Any) -> dict:
        args = ["tools-call", name]
        for k, v in kwargs.items():
            if isinstance(v, bool):
                args.append(f"{k}:={'true' if v else 'false'}")
            elif isinstance(v, (int, float)):
                args.append(f"{k}:={v}")
            elif isinstance(v, str):
                args.append(f"{k}:={v}")
            else:
                args.append(f"{k}:={json.dumps(v)}")
        return await self._run(*args, timeout=timeout)

    async def ping(self) -> dict:
        return await self._run("ping")

    async def resources_list(self) -> list[dict]:
        return await self._run("resources-list")

    async def prompts_list(self) -> list[dict]:
        return await self._run("prompts-list")
```

### Async usage

```python
async def main():
    client = AsyncMcpc("my-session")

    # Concurrent tool calls
    results = await asyncio.gather(
        client.tools_call("search", query="python"),
        client.tools_call("search", query="javascript"),
        client.tools_call("search", query="rust"),
    )
    for r in results:
        print(r["content"][0]["text"])

asyncio.run(main())
```

## Type-safe dataclasses

Parse mcpc JSON output into typed Python objects:

```python
from dataclasses import dataclass, field


@dataclass
class ToolParam:
    name: str
    type: str
    description: str = ""
    required: bool = False


@dataclass
class Tool:
    name: str
    description: str = ""
    inputSchema: dict = field(default_factory=dict)

    @property
    def params(self) -> list[ToolParam]:
        props = self.inputSchema.get("properties", {})
        required = set(self.inputSchema.get("required", []))
        return [
            ToolParam(
                name=k,
                type=v.get("type", "unknown"),
                description=v.get("description", ""),
                required=k in required,
            )
            for k, v in props.items()
        ]

    @classmethod
    def from_json(cls, data: dict) -> "Tool":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            inputSchema=data.get("inputSchema", {}),
        )


@dataclass
class ContentBlock:
    type: str
    text: str = ""
    data: str = ""
    mimeType: str = ""

    @classmethod
    def from_json(cls, data: dict) -> "ContentBlock":
        return cls(
            type=data["type"],
            text=data.get("text", ""),
            data=data.get("data", ""),
            mimeType=data.get("mimeType", ""),
        )


@dataclass
class ToolResult:
    content: list[ContentBlock]
    isError: bool = False

    @property
    def text(self) -> str:
        """Convenience: first text content block."""
        for block in self.content:
            if block.type == "text":
                return block.text
        return ""

    @classmethod
    def from_json(cls, data: dict) -> "ToolResult":
        return cls(
            content=[ContentBlock.from_json(c) for c in data.get("content", [])],
            isError=data.get("isError", False),
        )


@dataclass
class Resource:
    uri: str
    name: str = ""
    mimeType: str = ""

    @classmethod
    def from_json(cls, data: dict) -> "Resource":
        return cls(
            uri=data["uri"],
            name=data.get("name", ""),
            mimeType=data.get("mimeType", ""),
        )
```

### Typed Mcpc subclass

```python
class TypedMcpc(Mcpc):
    """Mcpc wrapper that returns typed dataclass objects."""

    def tools_list_typed(self, full: bool = False) -> list[Tool]:
        raw = self.tools_list(full=full)
        return [Tool.from_json(t) for t in raw]

    def tools_call_typed(self, name: str, **kwargs) -> ToolResult:
        raw = self.tools_call(name, **kwargs)
        return ToolResult.from_json(raw)

    def resources_list_typed(self) -> list[Resource]:
        raw = self.resources_list()
        return [Resource.from_json(r) for r in raw]
```

### Typed usage

```python
client = TypedMcpc("my-session")

for tool in client.tools_list_typed(full=True):
    print(f"{tool.name}: {len(tool.params)} params")
    for p in tool.params:
        req = " (required)" if p.required else ""
        print(f"  {p.name}: {p.type}{req}")

result = client.tools_call_typed("search", query="test")
if not result.isError:
    print(result.text)
```

## FastAPI integration

Expose mcpc-connected MCP tools as a REST API:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="MCP Gateway")

# Initialize mcpc wrapper (session must already be connected)
mcpc = Mcpc("my-session")


class ToolCallRequest(BaseModel):
    arguments: dict = {}


@app.get("/tools")
def list_tools():
    """List all available MCP tools."""
    try:
        return mcpc.tools_list()
    except McpcError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/tools/{tool_name}")
def get_tool(tool_name: str):
    """Get a specific tool's schema."""
    try:
        return mcpc.tools_get(tool_name)
    except ClientError:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    except McpcError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/tools/{tool_name}/call")
def call_tool(tool_name: str, req: ToolCallRequest):
    """Call an MCP tool with the given arguments."""
    try:
        return mcpc.tools_call(tool_name, **req.arguments)
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ServerError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except NetworkError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/resources")
def list_resources():
    """List all available MCP resources."""
    try:
        return mcpc.resources_list()
    except McpcError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/health")
def health():
    """Health check — pings the MCP server."""
    try:
        mcpc.ping()
        return {"status": "ok"}
    except McpcError as e:
        return {"status": "error", "message": str(e)}
```

### Running the gateway

```bash
# Terminal 1: ensure mcpc session is connected
mcpc https://mcp.example.com connect @my-session

# Terminal 2: start FastAPI gateway
pip install fastapi uvicorn
uvicorn gateway:app --host 0.0.0.0 --port 9000

# Test
curl http://localhost:9000/tools
curl -X POST http://localhost:9000/tools/search/call \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"query": "test"}}'
```

## Error handling patterns

### Retry decorator

```python
import time
from functools import wraps


def retry_mcpc(
    max_retries: int = 3,
    retry_on: tuple[type[McpcError], ...] = (NetworkError,),
    backoff_factor: float = 1.0,
):
    """Retry mcpc calls on transient failures."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_error = e
                    wait = backoff_factor * (2 ** attempt)
                    time.sleep(wait)
            raise last_error
        return wrapper
    return decorator


# Usage
@retry_mcpc(max_retries=3, retry_on=(NetworkError, ServerError))
def search(client: Mcpc, query: str):
    return client.tools_call("search", query=query)
```

### Context manager for session lifecycle

```python
import subprocess


class McpcSession:
    """Context manager that connects on enter and closes on exit."""

    def __init__(self, server: str, session: str, **connect_kwargs):
        self.server = server
        self.session = session
        self.connect_kwargs = connect_kwargs
        self.client: Mcpc | None = None

    def __enter__(self) -> Mcpc:
        cmd = ["mcpc", self.server, "connect", f"@{self.session}"]
        for k, v in self.connect_kwargs.items():
            cmd.extend([f"--{k}", str(v)])
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        self.client = Mcpc(self.session)
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.run(
            ["mcpc", f"@{self.session}", "close"],
            capture_output=True, text=True,
        )
        return False


# Usage
with McpcSession("https://mcp.example.com", "test-session") as client:
    tools = client.tools_list()
    result = client.tools_call("search", query="test")
    print(result)
# Session is automatically closed
```

### Async context manager

```python
class AsyncMcpcSession:
    """Async context manager for session lifecycle."""

    def __init__(self, server: str, session: str, **connect_kwargs):
        self.server = server
        self.session = session
        self.connect_kwargs = connect_kwargs
        self.client: AsyncMcpc | None = None

    async def __aenter__(self) -> AsyncMcpc:
        cmd = ["mcpc", self.server, "connect", f"@{self.session}"]
        for k, v in self.connect_kwargs.items():
            cmd.extend([f"--{k}", str(v)])
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        if proc.returncode != 0:
            raise McpcError("ConnectFailed", f"Failed to connect to {self.server}", proc.returncode)
        self.client = AsyncMcpc(self.session)
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        proc = await asyncio.create_subprocess_exec(
            "mcpc", f"@{self.session}", "close",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return False


# Usage
async def main():
    async with AsyncMcpcSession("https://mcp.example.com", "test") as client:
        tools = await client.tools_list()
        results = await asyncio.gather(
            client.tools_call("search", query="a"),
            client.tools_call("search", query="b"),
        )
```

## Batch processing with concurrency control

```python
import asyncio
from dataclasses import dataclass


@dataclass
class BatchResult:
    tool: str
    kwargs: dict
    result: dict | None = None
    error: McpcError | None = None


async def batch_tool_calls(
    client: AsyncMcpc,
    calls: list[tuple[str, dict]],
    max_concurrent: int = 5,
) -> list[BatchResult]:
    """Run multiple tool calls with a concurrency semaphore.

    Args:
        client: Async mcpc client
        calls: List of (tool_name, kwargs) tuples
        max_concurrent: Max simultaneous tool calls
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[BatchResult] = []

    async def _call(tool: str, kwargs: dict) -> BatchResult:
        async with semaphore:
            try:
                result = await client.tools_call(tool, **kwargs)
                return BatchResult(tool=tool, kwargs=kwargs, result=result)
            except McpcError as e:
                return BatchResult(tool=tool, kwargs=kwargs, error=e)

    tasks = [_call(tool, kwargs) for tool, kwargs in calls]
    results = await asyncio.gather(*tasks)
    return list(results)


# Usage
async def main():
    client = AsyncMcpc("my-session")

    calls = [
        ("search", {"query": "python"}),
        ("search", {"query": "javascript"}),
        ("search", {"query": "rust"}),
        ("search", {"query": "go"}),
        ("search", {"query": "java"}),
        ("search", {"query": "swift"}),
        ("search", {"query": "kotlin"}),
        ("search", {"query": "typescript"}),
    ]

    results = await batch_tool_calls(client, calls, max_concurrent=3)

    for r in results:
        if r.error:
            print(f"  FAIL {r.tool}({r.kwargs}): {r.error}")
        else:
            text = r.result["content"][0]["text"]
            print(f"  OK   {r.tool}({r.kwargs}): {text[:80]}...")

asyncio.run(main())
```

## pytest integration

```python
import pytest


@pytest.fixture(scope="session")
def mcpc_client():
    """Session-scoped fixture that connects and closes mcpc."""
    server = "https://mcp.example.com"
    session_name = f"pytest-{os.getpid()}"

    subprocess.run(
        ["mcpc", server, "connect", f"@{session_name}"],
        check=True, capture_output=True, text=True,
    )
    client = Mcpc(session_name)
    yield client
    subprocess.run(
        ["mcpc", f"@{session_name}", "close"],
        capture_output=True, text=True,
    )


def test_tool_list_not_empty(mcpc_client):
    tools = mcpc_client.tools_list()
    assert len(tools) > 0, "Server should expose at least one tool"


def test_every_tool_has_schema(mcpc_client):
    tools = mcpc_client.tools_list(full=True)
    for tool in tools:
        assert "inputSchema" in tool, f"Tool '{tool['name']}' missing inputSchema"
        assert tool.get("description"), f"Tool '{tool['name']}' has no description"


def test_search_returns_results(mcpc_client):
    result = mcpc_client.tools_call("search", query="test")
    assert not result.get("isError", False), "search should not error"
    assert len(result["content"]) > 0, "search should return content"


def test_search_with_invalid_args(mcpc_client):
    with pytest.raises(ServerError):
        mcpc_client.tools_call("search")  # missing required 'query'


def test_unknown_tool_raises_error(mcpc_client):
    with pytest.raises((ClientError, ServerError)):
        mcpc_client.tools_call("nonexistent-tool-xyz")
```

### Running tests

```bash
# Connect the session first
mcpc https://mcp.example.com connect @pytest-test

# Run tests (set session name via env or hardcode in fixture)
pytest test_mcp_server.py -v

# With isolated mcpc home
MCPC_HOME_DIR=/tmp/mcpc-pytest pytest test_mcp_server.py -v
```

## Tips

- The subprocess approach works with any mcpc version since it uses the CLI binary directly.
- Always pass `capture_output=True` and `text=True` to avoid blocking on stdout.
- Set the subprocess timeout higher than the mcpc `--timeout` to avoid killing the process before mcpc can report a proper error.
- Use `MCPC_HOME_DIR` environment variable for test isolation when running parallel pytest-xdist workers.
- For high-throughput scenarios, consider the async wrapper to avoid blocking the event loop.
- The `tools_call_json` method is useful when parameters are complex nested objects that are awkward with `key:=value` syntax.
