# Go / stdlib testing — Condition-Based Waiting

Drop-in utilities for Go test files. Uses only the stdlib — no external polling library required.

## Utilities

```go
// testutil/poll.go
package testutil

import (
	"context"
	"fmt"
	"testing"
	"time"
)

type WaitOpts struct {
	Timeout     time.Duration
	Interval    time.Duration
	Description string
}

func WaitFor(t *testing.T, condition func() bool, opts WaitOpts) {
	t.Helper()
	if opts.Timeout <= 0 {
		opts.Timeout = 5 * time.Second
	}
	if opts.Interval <= 0 {
		// time.NewTicker panics on zero or negative intervals. Default rather
		// than let the caller surface a panic during Phase 1 repro attempts.
		opts.Interval = 10 * time.Millisecond
	}
	if opts.Description == "" {
		opts.Description = "condition"
	}
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()
	ticker := time.NewTicker(opts.Interval)
	defer ticker.Stop()
	for {
		if condition() {
			return
		}
		select {
		case <-ctx.Done():
			t.Fatalf("WaitFor timed out after %s: %s", opts.Timeout, opts.Description)
		case <-ticker.C:
			continue
		}
	}
}

func WaitForCount(t *testing.T, getCount func() int, expected int, opts WaitOpts) {
	t.Helper()
	if opts.Description == "" {
		opts.Description = fmt.Sprintf("count >= %d", expected)
	}
	WaitFor(t, func() bool { return getCount() >= expected }, opts)
}
```

## Usage

```go
package mypkg_test

import (
	"testing"
	"time"

	"myapp/testutil"
)

func TestCleanupCompletes(t *testing.T) {
	store := &Store{}
	go store.Clear()

	testutil.WaitFor(t,
		func() bool { return store.Size() == 0 },
		testutil.WaitOpts{
			Timeout:     5 * time.Second,
			Description: "store to empty",
		},
	)
	if store.Size() != 0 {
		t.Fatal("store not empty")
	}
}

func TestBothWorkersCommit(t *testing.T) {
	log := &CommitLog{}
	go worker1(log)
	go worker2(log)

	testutil.WaitForCount(t, func() int { return len(log.Entries()) }, 2,
		testutil.WaitOpts{Timeout: 10 * time.Second})

	unique := make(map[string]bool)
	for _, c := range log.Entries() {
		unique[c.WorkerID] = true
	}
	if len(unique) != 2 {
		t.Fatalf("expected 2 unique workers, got %d", len(unique))
	}
}
```

## Test-framework integration

**`go test`**: native. Uses `*testing.T` for `t.Helper()` and `t.Fatalf`.
**`-race`**: polling utilities must be race-safe. The `condition` closure is the user's code; make sure any shared state is guarded by the user.
**Parallel tests**: `t.Parallel()` works with `WaitFor`; each subtest has its own deadline.
**`testify/require` / `testify/assert`**: compatible — `WaitFor` is plain Go and interoperates.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `time.Sleep(500 * time.Millisecond)` in tests | `WaitFor` with a named condition |
| Condition closure holds a lock between calls | Read and release; polling 100x/s with held lock is contention |
| No `t.Helper()` call — test failure points at WaitFor's line, not the test's | Always `t.Helper()` at the top |
| Timeout without context | Always include `Description` so the failure message names the condition |
