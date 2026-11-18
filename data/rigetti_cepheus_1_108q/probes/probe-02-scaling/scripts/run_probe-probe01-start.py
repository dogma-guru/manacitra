"""Probe 01 at the go (rule sections 1 to 4). Submits Task A, then B, then C or D only if the one before was rejected.

Usage (from the probe working folder, after the author's go):
  AWS_PROFILE=<profile name> ../.venv/bin/python scripts/run_probe.py --rule-sha <hash from the public issue>
  AWS_PROFILE=<profile name> ../.venv/bin/python scripts/check_window.py        (read calls only; any time)

Order of work:
  1. Check the rule copy against the hash posted in the issue; stop if it differs.
  2. Wait for the device to be ONLINE inside an availability window.
  3. Read the properties and save them; choose the qubit (longest T2) and d (its T1, nearest 100 ns, capped at 60 us);
     fill the templates and save task-<letter>.qasm with their hashes.
  4. Inside one Tracker: submit A (within ten minutes of the read), wait for its result, record the cost;
     then B; on a rejection C; on a rejection D. After each task, record the cost and check the hard stops.

A rejection is a ValidationException at creation, or a task that ends FAILED with a failure reason. Any other error,
or a CANCELLED task, stops the run (section 1, item 3). A FAILED task also stops the run, so that the runner reads
the failure reason before the next letter is sent: `--from <letter>` resumes, and the guard still refuses any letter
already listed in run-log.json.
"""
import argparse
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (_USED, DEVICE_ARN, DEVICE_NAME, HERE, PROGRAMS, RAW, SHOTS, guard, save_clean, scrub, sha,
                    stamp, utc)

guard()
from botocore.exceptions import ClientError
from braket.aws import AwsDevice
from braket.ir.openqasm import Program
from braket.tracking import Tracker

RULE = HERE / "braket-probe-01-wait-rule.md"
RULE_SHA = "1d60b3b1ae8796d47197ea9bd58bb8d4f8fd3b8671aa8cf1a5d4191a49c1afb6"   # recorded at the copy, 2026-10-21
LOG = HERE / "run.log"
RUN_LOG = HERE / "run-log.json"
# Availability windows, UTC, as published in service.executionWindows (Everyday).
WINDOWS = ((0, 0, 1, 59), (4, 0, 13, 59), (16, 0, 23, 59))
STOP_PER_TASK = Decimal("[cost]")
STOP_TOTAL = Decimal("[cost]")
PROPERTIES_MAX_AGE_S = 600
TERMINAL = ("COMPLETED", "FAILED", "CANCELLED")


def say(msg):
    line = f"{utc()} {scrub(str(msg))}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def in_window(t=None):
    g = time.gmtime(t)
    m = g.tm_hour * 60 + g.tm_min
    return any(h0 * 60 + m0 <= m <= h1 * 60 + m1 for h0, m0, h1, m1 in WINDOWS)


def window_left_s(t=None):
    """Seconds until the current window closes (0 outside a window)."""
    g = time.gmtime(t)
    s = g.tm_hour * 3600 + g.tm_min * 60 + g.tm_sec
    for h0, m0, h1, m1 in WINDOWS:
        if h0 * 3600 + m0 * 60 <= s <= h1 * 3600 + m1 * 60 + 59:
            return h1 * 3600 + m1 * 60 + 59 - s
    return 0


IGNORE_WINDOW = [False]   # set by --outside-window: the author's override of 2026-10-21T14:05Z, recorded in go.log


def wait_ready(device, margin_s=0):
    """Block until the device is ONLINE and inside a window with at least margin_s left. Read calls only.
    With the author's override, only ONLINE is required."""
    while True:
        device.refresh_metadata()
        if device.status == "ONLINE" and (IGNORE_WINDOW[0] or (in_window() and window_left_s() >= margin_s)):
            return
        say(f"waiting: status {device.status}, in window {in_window()}, window seconds left {window_left_s()}")
        time.sleep(60)


def load_log():
    return json.loads(RUN_LOG.read_text()) if RUN_LOG.exists() else {"tasks": []}


def write_log(state):
    save_clean(RUN_LOG, json.dumps(state, indent=1, default=str))


def read_properties(device):
    meta = device.aws_session.get_device(DEVICE_ARN)
    read_utc = utc()
    caps = json.loads(meta.pop("deviceCapabilities"))
    meta.pop("ResponseMetadata", None)
    s = stamp()
    save_clean(RAW / f"properties-presubmission-{s}.json", json.dumps(caps, indent=1, sort_keys=True))
    meta["read_utc"] = read_utc
    save_clean(RAW / f"device-meta-presubmission-{s}.json", json.dumps(meta, indent=1, default=str))
    return caps, read_utc, time.time()


def choose(caps):
    """Section 2: the qubit with the longest published T2; d is its T1 to the nearest 100 ns, capped at 60 us."""
    one = caps["standardized"]["oneQubitProperties"]
    ranked = sorted(((v["T2"]["value"], q) for q, v in one.items()), key=lambda x: (-x[0], int(x[1])))
    top_t2, q = ranked[0]
    tie = [x for x in ranked if x[0] == top_t2]
    v = one[q]
    assert v["T1"]["unit"] == "S" and v["T2"]["unit"] == "S"
    d_ns = min(int(round(v["T1"]["value"] * 1e9 / 100.0)) * 100, 60000)
    fid = {f["fidelityType"]["name"]: f for f in v.get("oneQubitFidelity", [])}
    return {
        "qubit": int(q), "tied_on_T2": [int(x[1]) for x in tie], "runner_up": [(int(x[1]), x[0]) for x in ranked[1:3]],
        "T1_s": v["T1"]["value"], "T2_s": v["T2"]["value"],
        "readout_fidelity": fid.get("READOUT", {}).get("fidelity"),
        "rb_fidelity": fid.get("RANDOMIZED_BENCHMARKING", {}).get("fidelity"),
        "rb_standard_error": fid.get("RANDOMIZED_BENCHMARKING", {}).get("standardError"),
        "simultaneous_rb_fidelity": fid.get("SIMULTANEOUS_RANDOMIZED_BENCHMARKING", {}).get("fidelity"),
        "properties_updatedAt": caps["service"].get("updatedAt"),
        "d_ns": d_ns, "d_capped": d_ns == 60000 and v["T1"]["value"] * 1e9 > 60000,
    }


def fill(choice):
    frame = f"Transmon_{choice['qubit']}_charge_tx"
    hashes = []
    for letter in "ABCD":
        t = (PROGRAMS / f"template-{letter}.qasm").read_text()
        t = t.replace("<QUBIT>", str(choice["qubit"])).replace("<D_NS>", str(choice["d_ns"]))
        assert "<QUBIT>" not in t and "<D_NS>" not in t, "placeholder left"
        out = PROGRAMS / f"task-{letter}.qasm"
        out.write_text(t)
        hashes.append(f"{sha(out)}  {out.name}")
    (PROGRAMS / "filled.sha256").write_text("\n".join(hashes) + "\n")
    return frame, hashes


def count_ones(measurements):
    ones = sum(1 for shot in measurements if shot and shot[0] == 1)
    return ones, len(measurements)


def follow(task, letter):
    """Poll the task's state (read calls) and record every transition seen, until it is terminal."""
    seen = []
    last = None
    while True:
        st = task.state(use_cached_value=False)
        if st != last:
            seen.append({"state": st, "first_seen_utc": utc()})
            say(f"task {letter}: {st}")
            last = st
        if st in TERMINAL:
            return seen
        time.sleep(10)


def save_task(task, letter, seen):
    session = task._aws_session
    meta = session.get_quantum_task(task.id)
    meta.pop("ResponseMetadata", None)
    record = {"letter": letter, "states_seen": seen, "status": meta.get("status"),
              "failureReason": meta.get("failureReason"), "createdAt": meta.get("createdAt"),
              "endedAt": meta.get("endedAt"), "queueInfo": meta.get("queueInfo")}
    save_clean(RAW / f"task-{letter}-metadata.json", json.dumps(meta, indent=1, default=str))
    save_clean(RAW / f"task-{letter}-states.json", json.dumps(record, indent=1, default=str))
    if meta.get("status") != "COMPLETED":
        return record, None
    body = session.retrieve_s3_object_body(meta["outputS3Bucket"], f"{meta['outputS3Directory']}/results.json")
    raw = json.loads(body)
    save_clean(RAW / f"task-{letter}-results.json", json.dumps(raw, indent=1, sort_keys=True))
    meas = raw.get("measurements")
    save_clean(RAW / f"task-{letter}-measurements.json", json.dumps(meas))
    save_clean(RAW / f"task-{letter}-additional-metadata.json",
               json.dumps(raw.get("additionalMetadata"), indent=1, sort_keys=True))
    ones, n = count_ones(meas or [])
    record.update({"ones": ones, "shots_returned": n, "fraction_ones": ones / n if n else None,
                   "measuredQubits": raw.get("measuredQubits")})
    return record, raw


OFFSET = [Decimal(0)]   # cost recorded by an earlier process of this run (only after a --from resume)


def cost(tracker):
    """The session total: this process's Tracker plus any earlier process's recorded total."""
    return OFFSET[0] + Decimal(str(tracker.qpu_tasks_cost())) + Decimal(str(tracker.simulator_tasks_cost()))


def submit(device, letter, state, tracker):
    """Submit one lettered task once. Returns 'ran', 'rejected', or 'stop'."""
    program = Program(source=(PROGRAMS / f"task-{letter}.qasm").read_text())
    before = cost(tracker)
    entry = {"letter": letter, "program_sha256": sha(PROGRAMS / f"task-{letter}.qasm"), "cost_before_usd": str(before)}
    state["tasks"].append(entry)
    entry["submitted_utc"] = utc()
    write_log(state)
    say(f"submitting task {letter}")
    try:
        task = device.run(program, shots=SHOTS, letter=letter, tags={"probe-01": letter})
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        text = str(e)
        save_clean(RAW / f"task-{letter}-error.txt", text + "\n")
        # Changed 2026-10-21 after Task A's first attempt: a ValidationException can be an account condition
        # (a spending limit window) rather than the program, so every creation error now stops for the runner to read.
        # A program rejection is then continued with --from <next letter>.
        entry.update({"outcome": ("ValidationException at creation; runner to read before the next letter"
                                  if code == "ValidationException" else "service error"),
                      "error_code": code, "error_utc": utc(), "cost_after_usd": str(cost(tracker))})
        write_log(state)
        say(f"task {letter}: {code}: {text}")
        return "stop"
    except Exception as e:
        save_clean(RAW / f"task-{letter}-error.txt", repr(e) + "\n")
        entry.update({"outcome": "error before creation", "error_utc": utc(), "error": repr(e),
                      "cost_after_usd": str(cost(tracker))})
        write_log(state)
        say(f"task {letter}: stopping on {e!r}")
        return "stop"
    entry["created_utc"] = utc()
    write_log(state)
    seen = follow(task, letter)
    record, raw = save_task(task, letter, seen)
    entry.update(record)
    entry["result_utc"] = utc()
    after = cost(tracker)
    entry["cost_after_usd"] = str(after)
    entry["cost_task_usd"] = str(after - before)
    write_log(state)
    say(f"task {letter}: {record['status']}; ones {record.get('ones')} of {record.get('shots_returned')}; "
        f"tracker {after} (task {after - before})")
    if after - before > STOP_PER_TASK or after > STOP_TOTAL:
        entry["hard_stop"] = f"cost: task {after - before}, total {after}"
        write_log(state)
        say("hard stop: cost limit reached")
        return "stop"
    if record["status"] == "COMPLETED":
        return "ran"
    if record["status"] == "FAILED":
        save_clean(RAW / f"task-{letter}-error.txt", f"{record.get('failureReason')}\n")
        entry["outcome"] = "FAILED; runner to read the failure reason before the next letter"
        write_log(state)
        return "stop"
    return "stop"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule-sha", required=True, help="the hash the author posted in the public issue")
    ap.add_argument("--from", dest="start", default="A", choices=list("ABCD"))
    ap.add_argument("--outside-window", action="store_true", help="author's override: submit outside a window")
    a = ap.parse_args()
    IGNORE_WINDOW[0] = a.outside_window
    if a.outside_window:
        say("author's override in force: availability windows not required (see go.log)")

    if sha(RULE) != RULE_SHA or a.rule_sha.lower() != RULE_SHA:
        say(f"stop: rule hash {sha(RULE)} does not match the posted hash")
        sys.exit(2)
    state = load_log()
    _USED.extend(t["letter"] for t in state["tasks"])   # letters already sent stay sent
    if state["tasks"]:
        OFFSET[0] = max(Decimal(t.get("cost_after_usd", "0")) for t in state["tasks"])
        if a.start == "A":
            say("stop: tasks already recorded in run-log.json; resume with --from")
            sys.exit(4)

    device = AwsDevice(DEVICE_ARN)
    with Tracker() as tracker:
        state.setdefault("tracker_start_usd", str(cost(tracker)))
        if a.start == "A":
            wait_ready(device, margin_s=PROPERTIES_MAX_AGE_S + 60)
            caps, read_utc, read_t = read_properties(device)
            choice = choose(caps)
            frame, hashes = fill(choice)
            state.update({"properties_read_utc": read_utc, "choice": choice, "frame": frame, "filled": hashes})
            write_log(state)
            say(f"qubit {choice['qubit']} (T2 {choice['T2_s']}, T1 {choice['T1_s']}), d {choice['d_ns']} ns")
            if time.time() - read_t > PROPERTIES_MAX_AGE_S or not (IGNORE_WINDOW[0] or in_window()):
                say("stop: properties older than ten minutes or window closed before Task A")
                sys.exit(3)
            if submit(device, "A", state, tracker) != "ran":
                say("stop after Task A: no control result")
                return finish(state, tracker)
            nxt = "B"
        else:
            nxt = a.start
        for letter in "BCD"[("BCD".index(nxt)):]:
            wait_ready(device)
            out = submit(device, letter, state, tracker)
            if out == "ran":
                say(f"task {letter} ran; C and D not submitted" if letter == "B" else f"task {letter} ran")
                break
            if out == "stop":
                say(f"stop after task {letter}")
                break
        else:
            say("B, C and D rejected: NOT ACCEPTED at every level tried")
        finish(state, tracker)


def finish(state, tracker):
    state["tracker_end_usd"] = str(cost(tracker))
    state["tracker_statistics"] = tracker.quantum_tasks_statistics()
    state["ended_utc"] = utc()
    write_log(state)
    say(f"tracker end {state['tracker_end_usd']}")


if __name__ == "__main__":
    main()
