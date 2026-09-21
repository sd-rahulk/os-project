# Security model

- Admin sessions use signed JWTs and PBKDF2-SHA256 password hashes.
- Enrollment is explicit and produces a unique agent credential per device.
- Credentials are stored server-side as hashes and are never returned by device read APIs.
- Commands are authorization-gated, validated with Pydantic, recorded by command ID, and audited with actor/device/outcome.
- There is no unrestricted shell, PowerShell endpoint, arbitrary file upload, or public Internet binding by default.
- The agent command queue is bounded to 100 messages. The WebSocket reconnects with capped exponential backoff.
- Use WSS/TLS for remote deployment. For self-signed development certificates, install the trusted certificate in the appropriate Windows trust store rather than disabling validation.

Before production: replace the development JWT secret and default admin credential, add rate limiting, CSRF protection if cookie sessions are introduced, secret rotation UI, certificate automation, retention pruning, and Windows service ACL hardening.

