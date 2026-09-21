import os
import platform
import socket
import time
from datetime import datetime, timezone
from typing import Any

import psutil


def safe(call, default=None):
    try:
        return call()
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess, NotImplementedError, OSError, ValueError):
        return default


class Monitor:
    def __init__(self) -> None:
        self.started_at = time.time()
        self._last_net = safe(psutil.net_io_counters, None)
        self._last_net_at = time.monotonic()
        self._process_samples: dict[tuple[int, float], tuple[float, float]] = {}
        psutil.cpu_percent(interval=None)

    def system_identity(self) -> dict[str, Any]:
        return {"device_id": f"{socket.gethostname()}-{platform.system().lower()}", "name": socket.gethostname(), "os_name": platform.system(), "os_version": platform.version(), "architecture": platform.machine(), "agent_version": "0.1.0"}

    def snapshot(self) -> dict[str, Any]:
        memory = safe(psutil.virtual_memory, None)
        disk = safe(lambda: psutil.disk_usage(os.environ.get("SystemDrive", "/")), None)
        net = safe(psutil.net_io_counters, None)
        now = time.monotonic()
        elapsed = max(0.001, now - self._last_net_at)
        upload_bps = download_bps = 0.0
        if net and self._last_net:
            upload_bps = max(0, net.bytes_sent - self._last_net.bytes_sent) / elapsed
            download_bps = max(0, net.bytes_recv - self._last_net.bytes_recv) / elapsed
        self._last_net, self._last_net_at = net, now
        return {"observed_at": datetime.now(timezone.utc).isoformat(), "cpu_percent": psutil.cpu_percent(interval=None), "logical_cores": psutil.cpu_count(logical=True), "physical_cores": psutil.cpu_count(logical=False), "memory_percent": memory.percent if memory else None, "memory_total": memory.total if memory else None, "memory_available": memory.available if memory else None, "disk_percent": disk.percent if disk else None, "disk_total": disk.total if disk else None, "disk_free": disk.free if disk else None, "upload_bps": upload_bps, "download_bps": download_bps, "uptime_seconds": max(0, time.time() - psutil.boot_time()), "agent_uptime_seconds": max(0, time.time() - self.started_at)}

    def processes(self) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for proc in psutil.process_iter(["pid", "name", "exe", "username", "status", "create_time", "ppid", "num_threads", "memory_info", "memory_percent", "nice", "cpu_affinity"]):
            try:
                info = proc.info
                key = (int(info.get("pid")), float(info.get("create_time") or 0))
                now = time.monotonic()
                raw_cpu = safe(lambda: proc.cpu_percent(interval=None), None)
                previous = self._process_samples.get(key)
                cpu_percent = raw_cpu if previous and now - previous[0] >= 0.5 else None
                if raw_cpu is not None:
                    self._process_samples[key] = (now, float(raw_cpu))
                output.append({"pid": info.get("pid"), "name": info.get("name") or "<unknown>", "executable": info.get("exe"), "username": info.get("username"), "status": info.get("status"), "create_time": info.get("create_time"), "ppid": info.get("ppid"), "thread_count": info.get("num_threads"), "memory_bytes": info.get("memory_info").rss if info.get("memory_info") else None, "memory_percent": info.get("memory_percent"), "priority": info.get("nice"), "cpu_affinity": info.get("cpu_affinity"), "cpu_percent": cpu_percent})
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
        return output

    @staticmethod
    def _verify_identity(proc: psutil.Process, create_time: float) -> None:
        if abs(proc.create_time() - create_time) > 1.0:
            raise RuntimeError("process_identity_changed")

    def process_detail(self, pid: int, create_time: float) -> dict[str, Any]:
        proc = psutil.Process(pid)
        self._verify_identity(proc, create_time)
        match = next((item for item in self.processes() if item["pid"] == pid and item["create_time"] == create_time), None)
        return {"ok": bool(match), "process": match, "reason": None if match else "process_not_found"}

    def terminate(self, pid: int, create_time: float, mode: str, tree: bool = False) -> dict[str, Any]:
        if pid in {0, 4, os.getpid()}:
            return {"ok": False, "reason": "protected_process"}
        try:
            proc = psutil.Process(pid)
            self._verify_identity(proc, create_time)
            if (safe(proc.name, "") or "").lower() in {"system", "smss.exe", "csrss.exe", "wininit.exe", "services.exe", "lsass.exe", "winlogon.exe"}:
                return {"ok": False, "reason": "protected_process"}
            children = proc.children(recursive=True) if tree else []
            if mode == "graceful" and platform.system() == "Windows":
                return {"ok": False, "reason": "graceful_close_requires_window_message", "supported": False}
            proc.terminate()
            _, alive = psutil.wait_procs([proc], timeout=5)
            if alive:
                return {"ok": False, "reason": "timed_out", "pid": pid}
            if tree:
                for child in children:
                    safe(child.terminate)
            return {"ok": True, "reason": "successfully_terminated", "pid": pid, "create_time": create_time, "mode": mode}
        except psutil.NoSuchProcess:
            return {"ok": False, "reason": "already_exited"}
        except psutil.AccessDenied:
            return {"ok": False, "reason": "access_denied"}
        except RuntimeError as exc:
            return {"ok": False, "reason": str(exc)}
        except Exception as exc:
            return {"ok": False, "reason": f"unsupported:{type(exc).__name__}"}

    def tune(self, pid: int, create_time: float, priority: str | int | None, affinity: list[int] | None) -> dict[str, Any]:
        try:
            proc = psutil.Process(pid)
            self._verify_identity(proc, create_time)
            if priority is not None:
                proc.nice(priority)
            if affinity is not None:
                proc.cpu_affinity(affinity)
            return {"ok": True, "priority": safe(proc.nice), "cpu_affinity": safe(proc.cpu_affinity)}
        except psutil.AccessDenied:
            return {"ok": False, "reason": "access_denied"}
        except psutil.NoSuchProcess:
            return {"ok": False, "reason": "already_exited"}
        except RuntimeError as exc:
            return {"ok": False, "reason": str(exc)}
        except Exception as exc:
            return {"ok": False, "reason": f"unsupported:{type(exc).__name__}"}
