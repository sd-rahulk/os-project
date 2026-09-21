# Testing

Run Python syntax checks and unit tests with:

```powershell
python -m compileall -q apps/server/app apps/agent/smartlab_agent
python -m pytest -q
```

The test suite covers scheduling output, memory-fit placement, and a harmless subprocess created with `time.sleep`. The process test reads its actual PID and creation time, calls the same `Monitor.terminate` code path, waits for exit, and asserts that the child is gone. It never targets an operating-system process.

The dashboard production check is:

```powershell
cd apps/dashboard
npm.cmd install
npm.cmd run build
```

Load testing for 50 agents is not claimed in this environment. A future `scripts/load_test_agents.py` should be explicitly synthetic and use a separate database/configuration so generated metrics cannot appear in the normal lab.

