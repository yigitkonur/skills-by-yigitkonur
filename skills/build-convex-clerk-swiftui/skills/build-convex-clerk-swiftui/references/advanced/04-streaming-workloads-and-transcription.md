# Streaming Workloads And Transcription

## Use This When
- Designing streaming ingestion, live transcripts, or other append-only realtime workloads.
- Evaluating whether Convex can support repeated chunk writes safely.
- Planning audio-provider integration and bandwidth control.

## Default Streaming Rules
- Insert one document per segment or chunk; never append forever to one array field.
- Batch writes in small groups when the domain allows it.
- Keep the live subscription focused on the latest window and paginate older history.
- Persist stable or final units when the domain has a distinction between draft and final output.

## Why This Matters
- Mutations have runtime and payload limits.
- Full-result re-send behavior makes naive ever-growing subscriptions expensive.
- Append-only writes with minimal read sets reduce OCC conflicts.
- Streaming products become bandwidth problems before they become raw database-size problems.

## Provider And Capture Guidance
- Treat provider integration as action-backed or external-runtime work, not as direct mutation logic.
- Keep audio-capture, provider websocket handling, and durable Convex state clearly separated.
- Do not describe file-upload-only APIs as if they were true live-streaming APIs.

## Product Guidance
- Flush buffered work before background where feasible.
- Use live-tail plus historical pagination rather than one giant realtime transcript.
- Carry timing and speaker metadata intentionally if the product needs them.

## Avoid
- Array-append transcript models.
- Read-before-write insert logic that adds conflict pressure.
- Assuming incremental delta delivery exists today.

## Read Next
- [01-pagination-live-tail-and-history.md](01-pagination-live-tail-and-history.md)
- [02-file-storage-upload-download-and-document-ids.md](02-file-storage-upload-download-and-document-ids.md)
- [../playbooks/03-streaming-and-transcription-playbook.md](../playbooks/03-streaming-and-transcription-playbook.md)
