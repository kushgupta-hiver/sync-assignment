## Gmail TrainShare

Auto-share Gmail messages whose subject matches "Training Exercise" across a fixed team (A/B/C/D) without forwarding. Uses Gmail Watch → Pub/Sub → History API, inserts raw RFC822 into teammate mailboxes, and applies a common label.

### Configuration defaults

- **STORE_BACKEND**: `firestore` (set `memory` for local dev)
- **FIRESTORE_COLLECTION_PREFIX**: `gts`
- **TEAM_USERS**: `A@example.com,B@example.com,C@example.com,D@example.com`
- **GMAIL_LABEL_NAME**: `Training Exercise`
- **Pub/Sub**: `gmail-trainshare-topic`, subscription `gmail-trainshare-sub`, DLQ `gmail-trainshare-dlq`
- **Subscriber**: `ACK_DEADLINE_SECONDS=60`, `MAX_DELIVERY_ATTEMPTS=10`

See `.env.example` for the full list of variables.

### Pub/Sub message schema

Message data (JSON):

```json
{
  "source": "gmail",
  "emailAddress": "user@example.com",
  "historyId": "1234567890",
  "eventTime": "2025-08-26T10:11:12Z",
  "projectId": "your-gcp-project"
}
```

Message attributes:

- `deliveryAttempt`: populated by Pub/Sub when enabled
- `traceId`: optional UUID (if absent, may be generated internally)
- `version`: defaults to `1` if missing

### Validation policy

- If `source != "gmail"`: log warning and ACK (skip)
- If required fields missing/invalid (`emailAddress`, `historyId`): log error and ACK (skip)
- If `version` present and not `1`: log warning, continue if payload validates
- Emit counters/metrics for all drops

### Retry and backoff

- Subscriber: `maxDeliveryAttempts=10`, `ackDeadline=60s`, then DLQ
- Gmail/API calls: exponential backoff with jitter (base=1s, factor=2.0, max=60s, maxRetries=6)
- Retryable: HTTP 429/5xx, timeouts; Non-retryable: 4xx (except 404 history out-of-range → triggers full resync)

### Labeling strategy

- Primary: thread-level via `users.threads.modify` using `threadId` from `messages.insert`
- Fallback: if `threadId` not available after one retry, temporarily apply message-level label and log a warning; later pass can upgrade thread

### Dev vs Prod state store

- Dev: in-memory KV (no setup)
- Prod: Firestore (Native mode) with prefix `gts`

### Notes

- Keep fixed team list via `TEAM_USERS` in env for now
- Terraform/Docker wiring can be added later

