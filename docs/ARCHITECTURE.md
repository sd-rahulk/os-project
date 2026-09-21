# Architecture

SmartLab is a hub-and-agent system.

```text
Windows dashboard (Next.js)
          │ localhost REST + /ws/dashboard
FastAPI control plane ─── SQLite
          │ authenticated /ws/agent
Windows SmartLab Agent ── psutil + optional PySide6 shell
```

The server owns enrollment, approval, credentials, device state, telemetry history, alerts, command records, and audit records. An agent owns OS observation and OS action. The frontend never terminates a process directly.

## Connection lifecycle

1. An agent submits its stable device identifier and system identity to `/api/agents/enroll`.
2. An administrator approves the request and receives a one-time agent credential.
3. The agent stores its credential under `%PROGRAMDATA%\SmartLab\Agent\config.json` and opens `/ws/agent`.
4. The server validates the credential and sends `hello_ack`.
5. Telemetry is sampled locally and sent every two seconds. Commands use bounded queues and unique request IDs.
6. On interruption the agent reconnects with exponential backoff and jitter (1s to 30s).

## Live versus retained state

`last_seen_at` and connection membership determine live status. The dashboard treats old metrics as historical once a device is stale or disconnected; it does not show them as live. SQLite samples are indexed by device and time. A production deployment should add retention pruning and rollups for long-term history.

## Process action trust boundary

The dashboard sends PID, creation time, action mode, and optional tree intent to the backend. The backend authorizes the admin, records an audit entry, dispatches a unique command to the correct connected agent, and waits for the agent result. The agent verifies the identity again, blocks core processes and itself, invokes the OS operation, waits for exit, and returns the genuine result.

