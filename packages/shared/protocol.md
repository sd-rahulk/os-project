# SmartLab protocol

The server and agent exchange JSON WebSocket messages. Agent credentials are issued only after explicit enrollment approval.

- `hello`: `{ type, device_id, token }`
- `hello_ack`: server acceptance and server timestamp
- `telemetry`: `{ type, payload }`, emitted about every two seconds
- `heartbeat`: lightweight liveness message
- `command`: server-to-agent request with a unique `request_id`, command type, and validated payload
- `command_result`: agent response keyed by `request_id`

Process actions always carry both `pid` and `create_time` to guard against PID reuse.

