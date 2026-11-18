"""Read calls only: is the device ONLINE, and is now inside an availability window? Saves nothing; prints one line."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import DEVICE_ARN, guard, scrub, utc

guard()
from braket.aws import AwsDevice

from run_probe import in_window, window_left_s  # noqa: E402  (run_probe calls guard() again; harmless)

d = AwsDevice(DEVICE_ARN)
q = d.queue_depth()
print(scrub(f"{utc()} status {d.status}; in window {in_window()}; window seconds left {window_left_s()}; "
            f"queue {dict((str(k), v) for k, v in q.quantum_tasks.items())}"))
