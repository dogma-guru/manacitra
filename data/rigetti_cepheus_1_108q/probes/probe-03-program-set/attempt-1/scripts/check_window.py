"""Read calls only: is the device ONLINE, is now inside an availability window, and what do the properties publish for
program sets? Saves nothing; prints a few lines."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import DEVICE_ARN, guard, scrub, utc

guard()
from braket.aws import AwsDevice

from run_probe import WINDOWS, in_window, window_left_s  # noqa: E402  (run_probe calls guard() again; harmless)

d = AwsDevice(DEVICE_ARN)
q = d.queue_depth()
print(scrub(f"{utc()} status {d.status}; in window {in_window()}; window seconds left {window_left_s()}; "
            f"queue {dict((str(k), v) for k, v in q.quantum_tasks.items())}"))
caps = json.loads(d.aws_session.get_device(DEVICE_ARN)["deviceCapabilities"])
print(f"published windows {caps['service'].get('executionWindows')}; runner windows {WINDOWS}; "
      f"properties updatedAt {caps['service'].get('updatedAt')}")
for name, action in caps.get("action", {}).items():
    if "program_set" in name:
        print(f"action {name}: {json.dumps(action, sort_keys=True)}")
print(f"actions published: {sorted(caps.get('action', {}))}")
