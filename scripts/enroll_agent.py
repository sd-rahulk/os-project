import argparse
import json
import platform
import socket
import urllib.request


parser = argparse.ArgumentParser(description="Create or refresh a SmartLab agent enrollment request")
parser.add_argument("--server", required=True, help="http://HOST:8765")
parser.add_argument("--code", default="smartlab")
parser.add_argument("--device-id", default="")
args = parser.parse_args()
device_id = args.device_id or f"{socket.gethostname()}-{platform.system().lower()}"
payload = {"device_id": device_id, "name": socket.gethostname(), "os_name": platform.system(), "os_version": platform.version(), "architecture": platform.machine(), "agent_version": "0.1.0", "enrollment_code": args.code}
request = urllib.request.Request(f"{args.server.rstrip('/')}/api/agents/enroll", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(request, timeout=10) as response:
    print(json.dumps(json.load(response), indent=2))

