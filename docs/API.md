# API and WebSockets

OpenAPI is available at `http://127.0.0.1:8765/docs`.

Implemented REST endpoints include:

```text
GET  /api/health
POST /api/auth/login
GET  /api/auth/me
POST /api/agents/enroll
POST /api/agents/{device_id}/approve
POST /api/agents/{device_id}/revoke
GET  /api/devices
GET  /api/devices/{device_id}
GET  /api/devices/{device_id}/metrics
GET  /api/devices/{device_id}/processes
GET  /api/devices/{device_id}/processes/{pid}?create_time=...
POST /api/devices/{device_id}/processes/{pid}/terminate
POST /api/devices/{device_id}/processes/{pid}/priority
POST /api/devices/{device_id}/processes/{pid}/affinity
GET  /api/alerts
POST /api/alerts/{alert_id}/acknowledge
GET  /api/activity
GET  /api/reports/resource.csv
```

Agent WebSocket: `/ws/agent`. Dashboard fan-out WebSocket: `/ws/dashboard`. Process actions require `{ pid, create_time }`; termination additionally accepts `mode: graceful|force` and `tree: boolean`.

