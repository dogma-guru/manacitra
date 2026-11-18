"""Read calls only: the account's spending limit for this device. Prints one line per limit; saves nothing.

The printed totals are the account's, not this probe's, and are not written to any file (runner prompt, item 5).
"""
import sys
import time
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import DEVICE_ARN, guard, utc

guard()
from braket.aws import AwsSession

client = AwsSession().braket_client
resp = client.search_spending_limits(filters=[{"name": "deviceArn", "operator": "EQUAL", "values": [DEVICE_ARN]}])
now = time.time()
limits = [x for x in resp.get("spendingLimits", []) if x.get("deviceArn") == DEVICE_ARN]
if not limits:
    print(f"{utc()} no spending limit found for this device")
for x in limits:
    tp = x.get("timePeriod", {})
    start, end = tp.get("startAt"), tp.get("endAt")
    covers = bool(start and end and start.timestamp() <= now <= end.timestamp())
    limit, queued, total = (Decimal(x.get(k, "0")) for k in ("spendingLimit", "queuedSpend", "totalSpend"))
    remaining = limit - queued - total
    print(f"{utc()} period {start} to {end}; covers now {covers}; remaining {remaining}; "
          f"covers [cost] {remaining >= Decimal('[cost]')}; limit updatedAt {x.get('updatedAt')}")
