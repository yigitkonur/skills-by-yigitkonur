# Ruby / RSpec — Condition-Based Waiting

Drop-in utilities for RSpec. Small pure-Ruby implementation; alternatives like the `timeout` or `wait_for` gems exist but the stdlib is sufficient.

## Utilities

```ruby
# spec/support/poll_utils.rb
module PollUtils
  class WaitTimeout < StandardError; end

  def wait_for(timeout: 5.0, interval: 0.01, description: "condition")
    deadline = Process.clock_gettime(Process::CLOCK_MONOTONIC) + timeout
    last_error = nil
    loop do
      begin
        result = yield
        return result if result
      rescue StandardError => err
        last_error = err
      end
      if Process.clock_gettime(Process::CLOCK_MONOTONIC) >= deadline
        msg = "wait_for timed out after #{timeout}s: #{description}"
        msg += " (last error: #{last_error.class}: #{last_error.message})" if last_error
        raise WaitTimeout, msg
      end
      sleep interval
    end
  end

  def wait_for_count(get_count, expected, **opts)
    desc = opts.delete(:description) || "count >= #{expected}"
    wait_for(description: desc, **opts) { get_count.call >= expected }
  end
end

RSpec.configure do |c|
  c.include PollUtils
end
```

## Usage

```ruby
require "rails_helper"

RSpec.describe "cleanup" do
  it "completes before next example" do
    store = Store.new
    Thread.new { store.clear }

    wait_for(timeout: 5.0, description: "store to empty") { store.size == 0 }
    expect(store.size).to eq(0)
  end
end

RSpec.describe "two workers" do
  it "both commit" do
    log = CommitLog.new
    Thread.new { worker1(log) }
    Thread.new { worker2(log) }

    wait_for_count(-> { log.size }, 2, timeout: 10.0)
    expect(log.map(&:worker_id).uniq.size).to eq(2)
  end
end
```

## Test-framework integration

**RSpec**: include the module globally via `RSpec.configure`; `wait_for` is available in every `describe`.
**Minitest**: use as a mixin in the test base class; same API.
**Capybara / system specs**: Capybara has its own `have_selector` matchers with auto-waiting; prefer those for UI assertions. Use `wait_for` for state-level polls not covered by Capybara.
**Time mocks (`Timecop`, `ActiveSupport::Testing::TimeHelpers`)**: `Process.clock_gettime(Process::CLOCK_MONOTONIC)` is not affected by time mocks — the wait measures real wall-clock time, which is what you want.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `sleep 0.5` with "this should be enough" | `wait_for` + named condition |
| Using `Time.now` instead of `Process::CLOCK_MONOTONIC` | `Time.now` can jump backward under NTP; use monotonic |
| `retry` without a deadline | `wait_for` adds the deadline — never retry forever in tests |
| Swallowing errors silently in the condition | Capture `last_error`; surface in timeout message |
