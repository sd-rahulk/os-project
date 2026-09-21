# Five-minute demonstration

1. Start the FastAPI server on the Windows laptop.
2. Start the Next.js dashboard and sign in.
3. Put the VMware guest on Host-only or Bridged networking and enroll the guest using `scripts/enroll_agent.py`.
4. Approve the device, copy the one-time credential into the guest agent config, and start `python -m apps.agent.smartlab_agent.main`.
5. Open Lab computers and confirm the VM becomes connected with real CPU, memory, disk, and network readings.
6. In the guest, run `python -m apps.server.app.demo 120` with `PYTHONPATH` set to the project root. This is a harmless CPU-intensive workload.
7. Watch CPU rise and the agent’s measured values update. Alert policy defaults are critical-only in the current foundation; configure warning thresholds in the next policy pass if you need the exact 75%/30s classroom trigger.
8. Open Process manager, select the workload, choose Force End Task, confirm, and observe the actual exit confirmation.
9. Open Activity logs and verify the command outcome and device ID.
10. Use the Smart allocation page for transparent target ranking. Scheduling and memory-fit simulators are available in `apps/server/app/simulations.py` and are intentionally labeled simulations.

