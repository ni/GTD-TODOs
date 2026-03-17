# API Overview

Phase 0 exposes two routes:

## Page Routes

- `GET /`: Returns the initial HTML landing page.

## Operational Routes

- `GET /health`: Returns JSON health status.

### `GET /health`

Response:

```json
{
  "status": "ok"
}
```

Future phases will expand this document with task and project mutation routes, form payloads, and HTMX partial behaviors.