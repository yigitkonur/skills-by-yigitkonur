# Python / pytest — Condition-Based Waiting

Drop-in utilities for pytest (sync and async) that replace `time.sleep(n)`.

## Utilities

```python
# poll_utils.py
import asyncio
import time
from typing import Awaitable, Callable, Optional, TypeVar

T = TypeVar("T")


class WaitTimeout(AssertionError):
    pass


def wait_for(
    condition: Callable[[], Optional[T]],
    *,
    timeout: float = 5.0,
    interval: float = 0.01,
    description: str = "condition",
) -> T:
    deadline = time.monotonic() + timeout
    last_error: Optional[BaseException] = None
    while time.monotonic() < deadline:
        try:
            result = condition()
            if result:
                return result
        except BaseException as err:
            last_error = err
        time.sleep(interval)
    msg = f"wait_for timed out after {timeout}s: {description}"
    if last_error:
        msg += f" (last error: {last_error!r})"
    raise WaitTimeout(msg)


async def wait_for_async(
    condition: Callable[[], Awaitable[Optional[T]]],
    *,
    timeout: float = 5.0,
    interval: float = 0.01,
    description: str = "condition",
) -> T:
    deadline = time.monotonic() + timeout
    last_error: Optional[BaseException] = None
    while time.monotonic() < deadline:
        try:
            result = await condition()
            if result:
                return result
        except BaseException as err:
            last_error = err
        await asyncio.sleep(interval)
    msg = f"wait_for_async timed out after {timeout}s: {description}"
    if last_error:
        msg += f" (last error: {last_error!r})"
    raise WaitTimeout(msg)


def wait_for_count(
    get_count: Callable[[], int],
    expected: int,
    **opts,
) -> None:
    wait_for(
        lambda: get_count() >= expected,
        description=opts.pop("description", f"count >= {expected}"),
        **opts,
    )
```

## Usage

```python
from poll_utils import wait_for, wait_for_count

def test_cleanup_completes(global_store):
    wait_for(
        lambda: global_store.size == 0,
        timeout=5.0,
        description="global_store to empty",
    )
    assert global_store.size == 0


async def test_both_workers_commit(commit_log):
    wait_for_count(lambda: len(commit_log), 2, timeout=10.0)
    assert len({c.worker_id for c in commit_log}) == 2
```

## Test-framework integration

**pytest**: no special setup. Install once as a fixture if you want shared defaults:

```python
# conftest.py
import pytest
from poll_utils import wait_for as _wait_for

@pytest.fixture
def wait_for():
    return _wait_for
```

**pytest-asyncio**: use `wait_for_async` inside `async def test_...`.

**pytest-xdist**: polling utilities are worker-local — no shared state needed; works with `-n auto`.

**Mock time**: if the test uses `freezegun` or `pytest-freezer`, `time.sleep` still blocks wall-clock but `time.monotonic()` advances with the frozen time. Use real time for tests that use `wait_for`.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `time.sleep(0.5)` with a "flaky, but usually works" comment | `wait_for` + named condition |
| Using `time.time()` instead of `time.monotonic()` | `time.monotonic()` is clock-drift immune |
| Raising `AssertionError` without context on timeout | Always include the `description` in the timeout message |
| Polling at 0.5s intervals | 10ms default; slower only when the check is expensive |
