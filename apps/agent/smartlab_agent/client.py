import asyncio
import json
import logging
import random

import websockets

from .config import AgentConfig
from .monitor import Monitor

log = logging.getLogger("smartlab-agent")


class AgentClient:
    def __init__(self, config: AgentConfig, monitor: Monitor) -> None:
        self.config, self.monitor = config, monitor
        self.stop_event = asyncio.Event()
        self.connected = False

    async def run(self) -> None:
        delay = 1.0
        while not self.stop_event.is_set():
            if not self.config.token:
                await asyncio.sleep(1)
                continue
            try:
                async with websockets.connect(self.config.server_url, ping_interval=20, ping_timeout=10, max_queue=50) as socket:
                    await socket.send(json.dumps({"type": "hello", "device_id": self.config.device_id, "token": self.config.token}))
                    if json.loads(await socket.recv()).get("type") != "hello_ack":
                        raise RuntimeError("server_rejected_agent")
                    self.connected, delay = True, 1.0
                    await self._connected_loop(socket)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.connected = False
                log.warning("connection lost: %s", exc)
                await asyncio.sleep(delay + random.uniform(0, min(1.0, delay / 2)))
                delay = min(30.0, delay * 2)

    async def _connected_loop(self, socket) -> None:
        loop = asyncio.get_running_loop()
        last_telemetry = 0.0
        last_process_sample = 0.0
        while not self.stop_event.is_set():
            now = loop.time()
            if now - last_telemetry >= self.config.telemetry_interval:
                await socket.send(json.dumps({"type": "telemetry", "payload": self.monitor.snapshot()}))
                last_telemetry = now
            if now - last_process_sample >= self.config.process_interval:
                await asyncio.to_thread(self.monitor.processes)
                last_process_sample = now
            try:
                raw = await asyncio.wait_for(socket.recv(), timeout=0.25)
                message = json.loads(raw)
                if message.get("type") == "command":
                    result = await self.handle_command(message.get("command"), message.get("payload", {}))
                    await socket.send(json.dumps({"type": "command_result", "request_id": message.get("request_id"), "result": result}))
            except asyncio.TimeoutError:
                continue

    async def handle_command(self, command: str, payload: dict) -> dict:
        try:
            if command == "list_processes":
                return {"ok": True, "processes": await asyncio.to_thread(self.monitor.processes)}
            if command == "process_detail":
                return await asyncio.to_thread(self.monitor.process_detail, int(payload["pid"]), float(payload["create_time"]))
            if command == "terminate_process":
                return await asyncio.to_thread(self.monitor.terminate, int(payload["pid"]), float(payload["create_time"]), payload.get("mode", "force"), bool(payload.get("tree", False)))
            if command in {"set_priority", "set_affinity"}:
                return await asyncio.to_thread(self.monitor.tune, int(payload["pid"]), float(payload["create_time"]), payload.get("priority"), payload.get("affinity"))
            return {"ok": False, "reason": "unsupported_action"}
        except (KeyError, ValueError, TypeError) as exc:
            return {"ok": False, "reason": f"invalid_request:{type(exc).__name__}"}
        except Exception as exc:
            return {"ok": False, "reason": type(exc).__name__}
