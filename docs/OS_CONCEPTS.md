# Operating-systems concepts mapping

1. **Process management** — real enumeration, identity-safe termination, priority, affinity, parent/child relationships, and access-denied handling through psutil.
2. **CPU scheduling** — FCFS, SJF, SRTF, Round Robin, and Priority are genuine discrete scheduling simulations with Gantt output and calculated metrics. They do not change Windows kernel scheduling.
3. **Memory management** — real available/used/pagefile observations are collected where psutil exposes them. First Fit, Best Fit, and Worst Fit are isolated educational allocation simulations; they do not replace Windows virtual memory.
4. **Multithreading and concurrency** — asyncio WebSockets, background sender queues, `asyncio.to_thread` for psutil calls, and separate UI/service lifecycles.
5. **IPC/network communication** — authenticated JSON messages over persistent WebSockets, REST control APIs, and dashboard fan-out.
6. **Synchronization** — per-connection pending-future maps and bounded queues prevent unbounded command buffering; server connection registration uses an asyncio lock.
7. **Resource allocation** — deterministic machine recommendation ranks measured CPU/RAM/disk availability after hard eligibility checks. It does not migrate a workload.
8. **Deadlock considerations** — commands are bounded and time out; the server does not hold a database transaction while waiting indefinitely for an agent.
9. **Performance monitoring** — psutil sampling, telemetry persistence, status classification, thresholds, alerts, and real-time charts.

