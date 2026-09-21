# VMware networking

`localhost` inside a VM means the guest itself. The agent must use the Windows host address reachable through VMware.

## Option A — Host-only network

1. In VMware Workstation, open **VM > Settings > Network Adapter** and choose **Host-only**.
2. On the Windows host run:

   ```powershell
   ipconfig
   ```

   Find the `VMware Network Adapter VMnet1` IPv4 address, commonly `192.168.x.1`.
3. In the guest run `ipconfig` and find the guest IPv4 address on the same subnet.
4. Start the server bound to the host-only address:

   ```powershell
   python -m uvicorn apps.server.app.main:app --host 192.168.x.1 --port 8765
   ```

5. Test from the guest:

   ```powershell
   Test-NetConnection 192.168.x.1 -Port 8765
   ```

6. The agent WebSocket URL is `ws://192.168.x.1:8765/ws/agent`.

## Option B — Bridged network

Choose **Bridged** when multiple physical lab computers need to reach the laptop on the trusted LAN. Find the laptop’s active LAN IPv4 address with `ipconfig`, bind uvicorn to that address, and use that address in every agent config. Do not bind to `0.0.0.0` unless remote admin access is explicitly intended.

## Firewall

Allow inbound TCP 8765 only on the Private network profile and only from the lab subnet. An elevated PowerShell rule is:

```powershell
New-NetFirewallRule -DisplayName "SmartLab Control Plane 8765" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow -Profile Private
```

Remove it when finished: `Remove-NetFirewallRule -DisplayName "SmartLab Control Plane 8765"`.

NAT can work for guest-initiated connections if the host address is reachable, but host-only and bridged are the supported documented configurations.

