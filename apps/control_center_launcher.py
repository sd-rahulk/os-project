"""Straightforward Windows launcher for a packaged local control center.

Build the Next app first (`npm.cmd run build`), then package this launcher
with PyInstaller. It starts the local FastAPI process and the Next standalone
server, then opens the dashboard in the default browser.
"""
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    env = os.environ.copy()
    api = subprocess.Popen([sys.executable, "-m", "uvicorn", "apps.server.app.main:app", "--host", "127.0.0.1", "--port", "8765"], cwd=ROOT, env=env)
    dashboard_dir = ROOT / "apps" / "dashboard" / ".next" / "standalone"
    next_server = dashboard_dir / "server.js"
    if not next_server.exists():
        api.terminate()
        raise SystemExit("Build apps/dashboard first with npm.cmd run build")
    web = subprocess.Popen(["node", str(next_server)], cwd=dashboard_dir, env=env)
    try:
        time.sleep(2)
        webbrowser.open("http://127.0.0.1:3000")
        web.wait()
    finally:
        web.terminate()
        api.terminate()


if __name__ == "__main__":
    main()

