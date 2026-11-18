"""Probe 02 at the go (rule sections 1 to 3). Submits A0, A1, A2 and B1 in that order without waiting for results,
then follows all four to the end, reading the properties again as each result is fetched.

Started from probe 01's hand-back scripts/run_probe.py (kept beside this file as run_probe-probe01-start.py).
Changed for probe 02: the labels and shots of section 3; frames filled from the properties; all four submitted before
any result is awaited; the properties read again at each fetch; probe 01's --outside-window override removed.
Kept: the guard (common.guard), and the stop on every creation error.

Usage (from the probe working folder, after the author's go):
  AWS_PROFILE=<profile name> ../.venv/bin/python scripts/run_probe.py --rule-sha <hash from the public issue>
  AWS_PROFILE=<profile name> ../.venv/bin/python scripts/run_probe.py --rule-sha <hash> --fetch-only
      (read calls only: follows the tasks already created, for a resume after the follow loop stopped)

Order of work:
  1. Check the rule copy against the hash posted in the issue; stop if it differs.
  2. Wait for the device to be ONLINE inside an availability window with time to spare.
  3. Read the properties and save them; choose the qubit (longest T2), d (its T1, nearest 100 ns, capped at 60 us) and
     the three published frames; fill the templates and save task-<label>.qasm with their hashes.
  4. Inside one Tracker: submit A0, A1, A2, B1 in order, within ten minutes of the read, recording the cost after each.
     Any creation error is saved verbatim and stops further submissions (a rejected program is not resubmitted);
     a cost over a hard stop stops further submissions. Tasks already created are still followed, by read calls.
  5. Poll every created task; when one ends, save its records and result, read the properties again and record the
     qubit's T1 and T2 beside it, and record the cost. Any error in the follow loop stops it; --fetch-only resumes.
"""
import argparse
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (_USED, DEVICE_ARN, HERE, LETTERS, PROGRAMS, RAW, SHOTS, TAG_KEY, guard, save_clean, scrub, sha,
                    stamp, utc)

guard()
from botocore.exceptions import ClientError
from braket.aws import AwsDevice, AwsQuantumTask
from braket.ir.openqasm import Program
from braket.tracking import Tracker

RULE = HERE / "braket-probe-02-scaling-rule.md"
RULE_SHA = "024783547852c52ab9f834c2a85f10d2eb73227aef73b8cc0ec895013acb8e41"   # recorded at the copy, 2026-10-21
LOG = HERE / "run.log"
RUN_LOG = HERE / "run-log.json"
ARNS = HERE / ".task-arns.local.json"   # task ARNs carry the account number: kept in the working folder, never handed back
# Availability windows, UTC, as published in service.executionWindows (Everyday).
WINDOWS = ((0, 0, 1, 59), (4, 0, 13, 59), (16, 0, 23, 59))
STOP_PER_TASK = Decimal("[cost]")
STOP_TOTAL = Decimal("[cost]")
PROPERTIES_MAX_AGE_S = 600
TERMINAL = ("COMPLETED", "FAILED", "CANCELLED")
POLL_S = 15


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


def wait_ready(device, margin_s=0):
    """Block until the device is ONLINE and inside a window with at least margin_s left. Read calls only."""
    while True:
        device.refresh_metadata()
        if device.status == "ONLINE" and in_window() and window_left_s() >= margin_s:
            return
        say(f"waiting: status {device.status}, in window {in_window()}, window seconds left {window_left_s()}")
        time.sleep(60)


def load_log():
    return json.loads(RUN_LOG.read_text()) if RUN_LOG.exists() else {"tasks": []}


def write_log(state):
    save_clean(RUN_LOG, json.dumps(state, indent=1, default=str))


def read_properties(device, tag):
    meta = device.aws_session.get_device(DEVICE_ARN)
    read_utc = utc()
    caps = json.loads(meta.pop("deviceCapabilities"))
    meta.pop("ResponseMetadata", None)
    s = stamp()
    save_clean(RAW / f"properties-{tag}-{s}.json", json.dumps(caps, indent=1, sort_keys=True))
    meta["read_utc"] = read_utc
    save_clean(RAW / f"device-meta-{tag}-{s}.json", json.dumps(meta, indent=1, default=str))
    return caps, read_utc, time.time(), s


def qubit_figures(caps, q):
    v = caps["standardized"]["oneQubitProperties"][str(q)]
    assert v["T1"]["unit"] == "S" and v["T2"]["unit"] == "S"
    return {"T1_s": v["T1"]["value"], "T2_s": v["T2"]["value"],
            "properties_updatedAt": caps["service"].get("updatedAt")}


def choose(caps):
    """Section 2: the qubit with the longest published T2; d is its T1 to the nearest 100 ns, capped at 60 us;
    the frames are the published ones for that qubit."""
    one = caps["standardized"]["oneQubitProperties"]
    ranked = sorted(((v["T2"]["value"], q) for q, v in one.items()), key=lambda x: (-x[0], int(x[1])))
    top_t2, q = ranked[0]
    tie = [x for x in ranked if x[0] == top_t2]
    v = one[q]
    assert v["T1"]["unit"] == "S" and v["T2"]["unit"] == "S"
    d_ns = min(int(round(v["T1"]["value"] * 1e9 / 100.0)) * 100, 60000)
    fid = {f["fidelityType"]["name"]: f for f in v.get("oneQubitFidelity", [])}
    frames = caps["pulse"]["frames"]
    names = {"drive": f"Transmon_{q}_charge_tx", "readout_tx": f"Transmon_{q}_readout_tx",
             "readout_rx": f"Transmon_{q}_readout_rx"}
    missing = [n for n in names.values() if n not in frames]
    if missing:
        raise RuntimeError(f"stop: frames not published at the read: {missing}")
    return {
        "qubit": int(q), "tied_on_T2": [int(x[1]) for x in tie], "runner_up": [(int(x[1]), x[0]) for x in ranked[1:3]],
        "T1_s": v["T1"]["value"], "T2_s": v["T2"]["value"],
        "readout_fidelity": fid.get("READOUT", {}).get("fidelity"),
        "rb_fidelity": fid.get("RANDOMIZED_BENCHMARKING", {}).get("fidelity"),
        "rb_standard_error": fid.get("RANDOMIZED_BENCHMARKING", {}).get("standardError"),
        "simultaneous_rb_fidelity": fid.get("SIMULTANEOUS_RANDOMIZED_BENCHMARKING", {}).get("fidelity"),
        "properties_updatedAt": caps["service"].get("updatedAt"),
        "d_ns": d_ns, "d_capped": d_ns == 60000 and v["T1"]["value"] * 1e9 > 60000,
        "frames": names, "frame_records": {k: frames[n] for k, n in names.items()},
    }


def fill(choice):
    f = choice["frames"]
    subs = {"<QUBIT>": str(choice["qubit"]), "<D_NS>": str(choice["d_ns"]), "<DRIVE_FRAME>": f["drive"],
            "<READOUT_TX_FRAME>": f["readout_tx"], "<READOUT_RX_FRAME>": f["readout_rx"]}
    hashes = []
    for label in LETTERS:
        t = (PROGRAMS / f"template-{label}.qasm").read_text()
        for k, v in subs.items():
            t = t.replace(k, v)
        assert "<" not in t, f"placeholder left in {label}"
        out = PROGRAMS / f"task-{label}.qasm"
        out.write_text(t)
        hashes.append(f"{sha(out)}  {out.name}")
    (PROGRAMS / "filled.sha256").write_text("\n".join(hashes) + "\n")
    return hashes


def count_ones(measurements):
    ones = sum(1 for shot in measurements if shot and shot[0] == 1)
    return ones, len(measurements)


def save_task(task, label, seen):
    session = task._aws_session
    meta = session.get_quantum_task(task.id)
    meta.pop("ResponseMetadata", None)
    record = {"states_seen": seen, "status": meta.get("status"),
              "failureReason": meta.get("failureReason"), "createdAt": meta.get("createdAt"),
              "endedAt": meta.get("endedAt"), "queueInfo": meta.get("queueInfo")}
    save_clean(RAW / f"task-{label}-metadata.json", json.dumps(meta, indent=1, default=str))
    save_clean(RAW / f"task-{label}-states.json", json.dumps({"label": label, **record}, indent=1, default=str))
    if meta.get("status") != "COMPLETED":
        return record
    body = session.retrieve_s3_object_body(meta["outputS3Bucket"], f"{meta['outputS3Directory']}/results.json")
    raw = json.loads(body)
    save_clean(RAW / f"task-{label}-results.json", json.dumps(raw, indent=1, sort_keys=True))
    meas = raw.get("measurements")
    save_clean(RAW / f"task-{label}-measurements.json", json.dumps(meas))
    save_clean(RAW / f"task-{label}-additional-metadata.json",
               json.dumps(raw.get("additionalMetadata"), indent=1, sort_keys=True))
    ones, n = count_ones(meas or [])
    record.update({"ones": ones, "shots_returned": n, "fraction_ones": ones / n if n else None,
                   "measuredQubits": raw.get("measuredQubits")})
    return record


OFFSET = [Decimal(0)]   # cost recorded by an earlier process of this run (only after a --fetch-only resume)


def cost(tracker):
    """The session total: this process's Tracker plus any earlier process's recorded total."""
    return OFFSET[0] + Decimal(str(tracker.qpu_tasks_cost())) + Decimal(str(tracker.simulator_tasks_cost()))


def entry_for(state, label):
    return next(t for t in state["tasks"] if t["label"] == label)


def submit(device, label, state, tracker, arns):
    """Submit one labelled task once, without waiting for it. Returns the task, or None after a creation error."""
    program = Program(source=(PROGRAMS / f"task-{label}.qasm").read_text())
    before = cost(tracker)
    entry = {"label": label, "shots": SHOTS[label], "program_sha256": sha(PROGRAMS / f"task-{label}.qasm"),
             "cost_before_usd": str(before)}
    state["tasks"].append(entry)
    entry["submitted_utc"] = utc()
    write_log(state)
    say(f"submitting task {label} ({SHOTS[label]} shots)")
    try:
        task = device.run(program, shots=SHOTS[label], letter=label, tags={TAG_KEY: label})
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        text = str(e)
        save_clean(RAW / f"task-{label}-error.txt", text + "\n")
        # As in probe 01: a ValidationException can be an account condition (a spending limit or window) rather than
        # the program, so every creation error stops further submissions for the runner to read.
        entry.update({"outcome": ("ValidationException at creation; runner to read" if code == "ValidationException"
                                  else "service error at creation"),
                      "error_code": code, "error_utc": utc(), "cost_after_usd": str(cost(tracker))})
        write_log(state)
        say(f"task {label}: {code}: {text}")
        return None
    except Exception as e:
        save_clean(RAW / f"task-{label}-error.txt", repr(e) + "\n")
        entry.update({"outcome": "error before creation", "error_utc": utc(), "error": repr(e),
                      "cost_after_usd": str(cost(tracker))})
        write_log(state)
        say(f"task {label}: stopping on {e!r}")
        return None
    entry["created_utc"] = utc()
    arns[label] = task.id
    ARNS.write_text(json.dumps(arns))
    ARNS.chmod(0o600)
    after = cost(tracker)
    entry.update({"outcome": "created", "cost_after_submission_usd": str(after),
                  "cost_task_usd": str(after - before)})
    write_log(state)
    say(f"task {label}: created; tracker {after} (task {after - before})")
    return task


def over_stop(state, tracker):
    total = cost(tracker)
    per = [Decimal(t["cost_task_usd"]) for t in state["tasks"] if "cost_task_usd" in t]
    if total > STOP_TOTAL or any(p > STOP_PER_TASK for p in per):
        return f"cost: highest task {max(per, default=0)}, total {total}"
    return None


def follow_all(device, tasks, state, tracker, qubit):
    """Poll every created task (read calls). When one is terminal: save it, read the properties again, record cost."""
    seen = {label: [] for label in tasks}
    last = {label: None for label in tasks}
    pending = dict(tasks)
    while pending:
        for label, task in list(pending.items()):
            st = task.state(use_cached_value=False)
            if st != last[label]:
                seen[label].append({"state": st, "first_seen_utc": utc()})
                say(f"task {label}: {st}")
                last[label] = st
            if st not in TERMINAL:
                continue
            entry = entry_for(state, label)
            entry["states_seen"] = entry.get("states_seen", []) + seen[label]
            record = save_task(task, label, entry["states_seen"])
            entry.update(record)
            entry["result_utc"] = utc()
            caps, read_utc, _, s = read_properties(device, f"fetch-{label}")
            entry["properties_at_fetch"] = {"read_utc": read_utc, "file": f"raw/properties-fetch-{label}-{s}.json",
                                            **qubit_figures(caps, qubit)}
            entry["cost_after_result_usd"] = str(cost(tracker))
            write_log(state)
            say(f"task {label}: {record['status']}; ones {record.get('ones')} of {record.get('shots_returned')}; "
                f"T1 {entry['properties_at_fetch']['T1_s']} T2 {entry['properties_at_fetch']['T2_s']} at fetch; "
                f"tracker {entry['cost_after_result_usd']}")
            if record["status"] == "FAILED":
                save_clean(RAW / f"task-{label}-error.txt", f"{record.get('failureReason')}\n")
            del pending[label]
        if pending:
            time.sleep(POLL_S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule-sha", required=True, help="the hash the author posted in the public issue")
    ap.add_argument("--fetch-only", action="store_true", help="follow tasks already created; submit nothing")
    a = ap.parse_args()

    if sha(RULE) != RULE_SHA or a.rule_sha.lower() != RULE_SHA:
        say(f"stop: rule hash {sha(RULE)} does not match the posted hash")
        sys.exit(2)
    state = load_log()
    arns = json.loads(ARNS.read_text()) if ARNS.exists() else {}
    _USED.extend(t["label"] for t in state["tasks"])   # labels already sent stay sent
    if state["tasks"] and not a.fetch_only:
        say("stop: tasks already recorded in run-log.json; use --fetch-only")
        sys.exit(4)

    device = AwsDevice(DEVICE_ARN)
    with Tracker() as tracker:
        if a.fetch_only:
            OFFSET[0] = max((Decimal(t.get(k, "0")) for t in state["tasks"]
                             for k in ("cost_after_submission_usd", "cost_after_result_usd", "cost_after_usd")),
                            default=Decimal(0))
            say(f"fetch only: carrying forward tracker total {OFFSET[0]}")
            done = {t["label"] for t in state["tasks"] if t.get("result_utc")}
            tasks = {label: AwsQuantumTask(arn) for label, arn in arns.items() if label not in done}
        else:
            state["tracker_start_usd"] = str(cost(tracker))
            wait_ready(device, margin_s=PROPERTIES_MAX_AGE_S + 600)
            caps, read_utc, read_t, s = read_properties(device, "presubmission")
            choice = choose(caps)
            hashes = fill(choice)
            state.update({"properties_read_utc": read_utc, "properties_file": f"raw/properties-presubmission-{s}.json",
                          "choice": choice, "filled": hashes})
            write_log(state)
            say(f"qubit {choice['qubit']} (T2 {choice['T2_s']}, T1 {choice['T1_s']}), d {choice['d_ns']} ns, "
                f"frames {choice['frames']}")
            tasks = {}
            for label in LETTERS:
                if time.time() - read_t > PROPERTIES_MAX_AGE_S and label == LETTERS[0]:
                    say("stop: properties older than ten minutes before the first submission")
                    sys.exit(3)
                device.refresh_metadata()
                if device.status != "ONLINE" or not in_window():
                    say(f"stop before {label}: status {device.status}, in window {in_window()}")
                    break
                task = submit(device, label, state, tracker, arns)
                if task is None:
                    say(f"stop after task {label}: creation error; no further submissions")
                    break
                tasks[label] = task
                stop = over_stop(state, tracker)
                if stop:
                    state["hard_stop"] = stop
                    write_log(state)
                    say(f"hard stop: {stop}; no further submissions")
                    break
            state["submissions_ended_utc"] = utc()
            state["tracker_after_submissions_usd"] = str(cost(tracker))
            write_log(state)
        qubit = state["choice"]["qubit"]
        try:
            follow_all(device, tasks, state, tracker, qubit)
        except Exception as e:
            say(f"stop in the follow loop on {e!r}; resume with --fetch-only")
            write_log(state)
            sys.exit(5)
        finish(state, tracker)


def finish(state, tracker):
    state["tracker_end_usd"] = str(cost(tracker))
    state["tracker_statistics"] = tracker.quantum_tasks_statistics()
    state["ended_utc"] = utc()
    stop = over_stop(state, tracker)
    if stop:
        state["hard_stop_at_end"] = stop
    write_log(state)
    say(f"tracker end {state['tracker_end_usd']}")


if __name__ == "__main__":
    main()
