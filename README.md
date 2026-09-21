# SMARTLAB OS

SmartLab OS is an academic operating-systems project with two runnable applications:

- **SmartLab Control Center** — Next.js dashboard plus a FastAPI/SQLite control plane.
- **SmartLab Agent** — Python/psutil monitoring and authenticated WebSocket command worker for Windows guests or hosts.

The implementation uses real OS telemetry and real process actions. A process termination request is verified by PID and creation time, sent through the authenticated agent channel, executed with psutil, and confirmed with a bounded wait. Protected and inaccessible Windows processes are reported rather than bypassed.

## Repository layout

```text
apps/server/       FastAPI API, WebSockets, SQLite models, alerts, audit log
apps/dashboard/    Next.js App Router control center
apps/agent/        Headless agent, optional PySide6 shell, PyInstaller spec
packages/shared/   Protocol notes and shared contract documentation
scripts/           Windows startup and enrollment helpers
tests/             scheduling, memory, and real harmless-process tests
docs/              architecture, security, VMware, demo, and testing guides
```

## Quick start on Windows

Use Python 3.11+ and Node.js 20+.

```powershell
python -m pip install -e .
Set-Location apps/dashboard
npm.cmd install
Set-Location ../..

# terminal 1: control plane
python -m uvicorn apps.server.app.main:app --host 127.0.0.1 --port 8765

# terminal 2: dashboard
Set-Location apps/dashboard
npm.cmd run dev
```

Open http://localhost:3000 and use the development account `admin` / `smartlab-admin`. Change the password implementation or seed logic before a real lab deployment.

For VM networking and agent enrollment, read [docs/VMWARE_SETUP.md](docs/VMWARE_SETUP.md) and [docs/INSTALLATION.md](docs/INSTALLATION.md).

## What is implemented

Implemented and wired end-to-end: admin login, device enrollment and approval, per-agent credentials, authenticated agent WebSockets, exponential reconnect, real CPU/RAM/disk/network telemetry, bounded command queues, process inventory, PID-plus-creation-time validation, protected-process rules, force termination with exit verification, activity audit, telemetry persistence, basic alert deduplication/recovery, CSV export, device dashboard, process manager, workload recommendation scoring, and FCFS/SJF/SRTF/Round Robin/Priority plus First/Best/Worst Fit simulators.

Environment-dependent: VMware host/guest routing, Windows Firewall policy, code signing, TLS certificates, Windows graceful window-close integration, service installation, 50-machine measured load, and final PyInstaller clean-machine validation. No successful VMware hardware test is claimed from this development environment.

