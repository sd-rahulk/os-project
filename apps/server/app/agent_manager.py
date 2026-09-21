import asyncio
import secrets
from typing import Any

from fastapi import WebSocket


class AgentConnection:
    def __init__(self, websocket: WebSocket, device_id: str) -> None:
        self.websocket = websocket
        self.device_id = device_id
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self.pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self.sender_task: asyncio.Task | None = None

    async def start(self) -> None:
        self.sender_task = asyncio.create_task(self._sender())

    async def _sender(self) -> None:
        while True:
            await self.websocket.send_json(await self.queue.get())

    async def send_command(self, command: str, payload: dict[str, Any], timeout: float = 15) -> dict[str, Any]:
        request_id = secrets.token_urlsafe(18)
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self.pending[request_id] = future
        await self.queue.put({"type": "command", "request_id": request_id, "command": command, "payload": payload})
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            return {"ok": False, "reason": "timed_out", "request_id": request_id}
        finally:
            self.pending.pop(request_id, None)

    def resolve(self, request_id: str, result: dict[str, Any]) -> None:
        if (future := self.pending.get(request_id)) and not future.done():
            future.set_result(result)

    async def close(self) -> None:
        if self.sender_task:
            self.sender_task.cancel()


class AgentManager:
    def __init__(self) -> None:
        self.connections: dict[str, AgentConnection] = {}
        self.dashboard_sockets: set[WebSocket] = set()
        self.lock = asyncio.Lock()

    async def register(self, connection: AgentConnection) -> None:
        async with self.lock:
            if previous := self.connections.get(connection.device_id):
                await previous.close()
            self.connections[connection.device_id] = connection
            await connection.start()

    async def unregister(self, device_id: str, connection: AgentConnection) -> None:
        async with self.lock:
            if self.connections.get(device_id) is connection:
                self.connections.pop(device_id, None)
        await connection.close()

    def get(self, device_id: str) -> AgentConnection | None:
        return self.connections.get(device_id)

    async def broadcast_dashboard(self, message: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for socket in list(self.dashboard_sockets):
            try:
                await socket.send_json(message)
            except Exception:
                stale.append(socket)
        for socket in stale:
            self.dashboard_sockets.discard(socket)


manager = AgentManager()

