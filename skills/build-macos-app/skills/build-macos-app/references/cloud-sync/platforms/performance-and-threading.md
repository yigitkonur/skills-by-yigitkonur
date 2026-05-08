# Performance, Battery, And Threading

## Use This When
- Reviewing subscription count, battery impact, or UI-thread correctness.
- Designing production-safe Swift-side performance behavior.
- Explaining why one client and bounded subscriptions matter.

## Default Performance Rules
- Prefer one long-lived client per process.
- Prefer fewer, broader, well-bounded subscriptions over many overlapping live feeds.
- Keep live result width small enough that full-result re-send behavior stays acceptable.
- Consolidate state where possible instead of recreating the same pipelines repeatedly.

## Battery And Network Rules
- More active subscriptions and more concurrent clients cost more battery and network churn.
- Realtime should be treated as a budget, not as a free default for every screen.
- Respect expensive network conditions and Low Power Mode in product behavior where reasonable.

## Threading Rule
- Convex emissions are not automatically on the main queue for UI writes.
- Move subscription values to the main queue before mutating UI-observed state unless the surrounding context already guarantees main-actor behavior.
- Keep threading correctness visible in code review.

## Measurement Guidance
- Use Instruments and OSLog when behavior is unclear.
- Inspect websocket churn, reconnect frequency, and list width before speculating.
- Avoid strong binary-size claims unless they are freshly verified.

## Avoid
- Many duplicated subscriptions to the same dataset without a state-sharing reason.
- Background-thread UI mutations from publisher callbacks.
- Treating power or bandwidth cost as somebody else's problem.

## Read Next
- [../advanced/03-testing-debugging-and-observability.md](../advanced/03-testing-debugging-and-observability.md)
- [../advanced/01-pagination-live-tail-and-history.md](../advanced/01-pagination-live-tail-and-history.md)
- [../client-sdk/03-subscriptions-errors-logging-and-connection-state.md](../client-sdk/03-subscriptions-errors-logging-and-connection-state.md)
