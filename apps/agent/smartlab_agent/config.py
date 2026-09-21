import json
import os
import socket
from dataclasses import asdict, dataclass
from pathlib import Path

APP_DIR = Path(os.getenv("PROGRAMDATA", Path.home())) / "SmartLab" / "Agent"
CONFIG_PATH = APP_DIR / "config.json"


@dataclass
class AgentConfig:
    server_url: str = "ws://127.0.0.1:8765/ws/agent"
    token: str = ""
    device_id: str = ""
    enrollment_code: str = "smartlab"
    telemetry_interval: float = 2.0
    process_interval: float = 5.0
    start_minimized: bool = False
    launch_on_login: bool = False

    @classmethod
    def load(cls) -> "AgentConfig":
        if CONFIG_PATH.exists():
            try:
                return cls(**json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
            except (OSError, ValueError, TypeError):
                pass
        return cls(device_id=f"{socket.gethostname()}-{os.environ.get('COMPUTERNAME', 'windows').lower()}")

    def save(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

