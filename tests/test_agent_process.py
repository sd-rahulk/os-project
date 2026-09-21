import subprocess
import sys
import time

import psutil

from apps.agent.smartlab_agent.monitor import Monitor


def test_real_process_termination_by_pid_and_creation_time():
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        proc = psutil.Process(child.pid)
        result = Monitor().terminate(child.pid, proc.create_time(), "force")
        assert result["ok"] is True
        child.wait(timeout=5)
        assert child.poll() is not None
    finally:
        if child.poll() is None:
            child.kill()

