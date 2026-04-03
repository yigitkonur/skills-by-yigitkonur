# Streaming And Transcription Playbook

## Use This When
- Building a live transcript, streaming AI, or append-only realtime workload.
- Translating the advanced and transcription docs into a build order.
- Stress-testing whether Convex is still a fit under sustained write volume.

## Default Sequence
1. Model sessions and segments as separate tables.
2. Index by session and time shape before writing the client.
3. Decide which units are transient and which are durable finals.
4. Batch writes where the domain allows it.
5. Keep the live tail small and history paginated.
6. Route provider or AI work through safe action flows.
7. Add reconnect, background flush, and stale-state UX.

## Default Safety Rules
- One document per segment.
- No unbounded arrays.
- No read-before-write insert mutations.
- No single giant live transcript subscription.
- No assumption of incremental delta delivery.

## Operational Checks
- Estimate bandwidth under full-result re-send behavior.
- Confirm provider API shape actually matches streaming needs.
- Confirm capture permissions and platform-specific audio constraints early.
- Confirm background behavior does not silently lose buffered work.

## Read Next
- [../advanced/04-streaming-workloads-and-transcription.md](../advanced/04-streaming-workloads-and-transcription.md)
- [../advanced/01-pagination-live-tail-and-history.md](../advanced/01-pagination-live-tail-and-history.md)
- [../advanced/02-file-storage-upload-download-and-document-ids.md](../advanced/02-file-storage-upload-download-and-document-ids.md)
