# Installation

## Server and dashboard laptop

```powershell
cd "C:\path\to\smartlab-os"
py -3.11 -m pip install -e .
cd apps\dashboard
npm.cmd install
cd ..\..
python -m uvicorn apps.server.app.main:app --host 127.0.0.1 --port 8765
```

In a second terminal:

```powershell
cd apps\dashboard
npm.cmd run dev
```

Production dashboard: `npm.cmd run build; npm.cmd start`. The API remains a separate FastAPI process in this straightforward local deployment.

The included `apps/control_center_launcher.py` can package the control center as a launcher after the Next standalone build exists:

```powershell
cd apps/dashboard
npm.cmd run build
cd ../..
pyinstaller apps\SmartLab-Control-Center.spec
```

This produces a real launcher executable that starts the local FastAPI process and the Next standalone server; it is not a renamed web project. Validate the bundle on a clean Windows machine before lab rollout.

## Guest agent

```powershell
py -3.11 -m pip install -r apps\agent\requirements.txt
$env:PYTHONPATH = (Get-Location).Path
python scripts\enroll_agent.py --server http://HOST_IP:8765 --code smartlab
```

Approve the printed `device_id` in the Control Center’s enrollment workflow or through the documented API. The returned one-time token is stored in the agent config:

```powershell
$configDir = Join-Path $env:PROGRAMDATA 'SmartLab\Agent'
New-Item -ItemType Directory -Force $configDir | Out-Null
@{ server_url='ws://HOST_IP:8765/ws/agent'; device_id='DEVICE_ID'; token='PASTE_APPROVED_TOKEN'; telemetry_interval=2; process_interval=5 } | ConvertTo-Json | Set-Content (Join-Path $configDir 'config.json')
python -m apps.agent.smartlab_agent.main
```

The token is not embedded in the frontend. For an executable build:

```powershell
pyinstaller apps\agent\SmartLab-Agent.spec
```

Service registration, code signing, and TLS/WSS certificates should be added for a real lab rollout. For development, use a trusted local certificate and configure `wss://`; never turn off certificate validation as a deployment default.
