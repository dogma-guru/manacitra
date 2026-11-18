"""Probe 03 at the go (rule sections 1 to 3). Builds one program set of two OpenQASM texts (E1, E2), submits it once with
shots=200, follows it to the end, reads the properties again at the fetch, and saves the raw result files before any
SDK parsing, then the SDK's parsed view of them.

Started from probe 02's hand-back scripts/run_probe.py (kept beside this file as run_probe-probe02-start.py).
Changed for probe 03: one task, a ProgramSet built from the two filled texts (strings, not circuit objects), with
shots=200 and shots_per_executable=100; a pricing estimate before the submission (stop at [cost] or more); every file
under the task's output folder downloaded raw; the SDK's parsed result described (type and shape of each
`measurements`) after the raw files are saved.
Kept: the guard (common.guard, extended to the program set), the choice of qubit, d and frames, the stop on every
creation error, the properties read again at the fetch.

Usage (from the probe working folder, after the author's go):
  AWS_PROFILE=<profile name> ../.venv/bin/python scripts/run_probe.py --rule-sha <hash from the public issue>
  AWS_PROFILE=<profile name> ../.venv/bin/python scripts/run_probe.py --rule-sha <hash> --fetch-only
      (read calls only: follows the task already created, for a resume after the follow loop stopped)

Order of work:
  1. Check the rule copy against the hash posted in the issue; stop if it differs.
  2. Wait for the device to be ONLINE inside an availability window with time to spare.
  3. Read the properties and save them; choose the qubit (longest T2), d (its T1, nearest 100 ns, capped at 60 us) and
     the three published frames; fill the templates and save task-E1.qasm and task-E2.qasm with their hashes.
  4. Estimate the cost from the price list (one task, 200 shots); stop if it is [cost] or more.
  5. Inside one Tracker, within ten minutes of the read: build the ProgramSet, save it as serialised, submit it once.
     A creation error is saved verbatim (with the service's response fields) and ends the run: no rewrite, no retry.
  6. Poll the task; at the end save its metadata and state history, read the properties again, download every file
     under its output folder, then parse with the SDK and describe what it returns. Record the tracker's cost.
"""
import argparse
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (_USED, DEVICE_ARN, HERE, LABELS, PROGRAMS, RAW, SHOTS_PER_EXECUTABLE, SHOTS_TOTAL, TAGS, guard,
                    save_clean, scrub, sha, stamp, utc)

guard()
from botocore.exceptions import ClientError
from braket.aws import AwsDevice, AwsQuantumTask
from braket.program_sets import ProgramSet
from braket.tracking import Tracker
from braket.tracking.tracker import _get_qpu_task_cost

RULE = HERE / "braket-probe-03-program-set-rule.md"
RULE_SHA = "b9748919eb26918976fbfd4ff0028899294cffbc97975e1cb6167e570811fb27"   # recorded at the copy, 2026-10-21
LOG = HERE / "run.log"
RUN_LOG = HERE / "run-log.json"
ARNS = HERE / ".task-arns.local.json"   # the task ARN carries the account number: kept in the working folder, never handed back
# Availability windows, UTC, as published in service.executionWindows (Everyday); checked again before the go.
WINDOWS = ((0, 0, 1, 59), (4, 0, 13, 59), (16, 0, 23, 59))
STOP_TASK = Decimal("[cost]")
PROPERTIES_MAX_AGE_S = 600
TERMINAL = ("COMPLETED", "FAILED", "CANCELLED")
POLL_S = 15
MAX_OUTPUT_OBJECTS = 100
KNOWN = []   # literal strings to redact everywhere (the results bucket name, once read)


def say(msg):
    line = f"{utc()} {scrub(str(msg), KNOWN)}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def save(path, text):
    return save_clean(path, text, KNOWN)


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
    return json.loads(RUN_LOG.read_text()) if RUN_LOG.exists() else {}


def write_log(state):
    save(RUN_LOG, json.dumps(state, indent=1, default=str))


def read_properties(device, tag):
    meta = device.aws_session.get_device(DEVICE_ARN)
    read_utc = utc()
    caps = json.loads(meta.pop("deviceCapabilities"))
    meta.pop("ResponseMetadata", None)
    s = stamp()
    save(RAW / f"properties-{tag}-{s}.json", json.dumps(caps, indent=1, sort_keys=True))
    meta["read_utc"] = read_utc
    save(RAW / f"device-meta-{tag}-{s}.json", json.dumps(meta, indent=1, default=str))
    return caps, read_utc, time.time(), s


def qubit_figures(caps, q):
    v = caps["standardized"]["oneQubitProperties"][str(q)]
    assert v["T1"]["unit"] == "S" and v["T2"]["unit"] == "S"
    fid = {f["fidelityType"]["name"]: f for f in v.get("oneQubitFidelity", [])}
    return {"T1_s": v["T1"]["value"], "T2_s": v["T2"]["value"],
            "readout_fidelity": fid.get("READOUT", {}).get("fidelity"),
            "rb_fidelity": fid.get("RANDOMIZED_BENCHMARKING", {}).get("fidelity"),
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
    for label in LABELS:
        t = (PROGRAMS / f"template-{label}.qasm").read_text()
        for k, v in subs.items():
            t = t.replace(k, v)
        assert "<" not in t, f"placeholder left in {label}"
        out = PROGRAMS / f"task-{label}.qasm"
        out.write_text(t)
        hashes.append(f"{sha(out)}  {out.name}")
    (PROGRAMS / "filled.sha256").write_text("\n".join(hashes) + "\n")
    return hashes


def estimate_cost():
    """The Tracker's own price lookup, for one task of 200 shots on this device (pricing read call only)."""
    region = DEVICE_ARN.split(":")[3]
    details = {"status": "CREATED", "device": DEVICE_ARN, "shots": SHOTS_TOTAL, "job_task": False}
    return _get_qpu_task_cost(f"arn:aws:braket:{region}::quantum-task/estimate", details)


OFFSET = [Decimal(0)]   # cost recorded by an earlier process of this run (only after a --fetch-only resume)


def cost(tracker):
    """The session total: this process's Tracker plus any earlier process's recorded total."""
    return OFFSET[0] + Decimal(str(tracker.qpu_tasks_cost())) + Decimal(str(tracker.simulator_tasks_cost()))


def submit(device, program_set, state, tracker, arns):
    """Submit the program set once. Returns the task, or None after a creation error (saved verbatim)."""
    before = cost(tracker)
    entry = state["task"] = {"cost_before_usd": str(before), "shots": SHOTS_TOTAL, "tags": TAGS,
                             "programs": {label: sha(PROGRAMS / f"task-{label}.qasm") for label in LABELS}}
    entry["submitted_utc"] = utc()
    write_log(state)
    say(f"submitting the program set ({len(program_set.entries)} entries, shots={SHOTS_TOTAL})")
    try:
        task = device.run(program_set, shots=SHOTS_TOTAL, tags=TAGS)
    except ClientError as e:
        resp = {k: v for k, v in e.response.items() if k != "ResponseMetadata"}
        text = f"{e}\n\n{json.dumps(resp, indent=1, default=str)}\n"
        save(RAW / "creation-error.txt", text)
        entry.update({"outcome": "ClientError at creation", "error_code": resp.get("Error", {}).get("Code"),
                      "error_utc": utc(), "cost_after_usd": str(cost(tracker))})
        write_log(state)
        say(f"creation error: {e}")
        return None
    except Exception as e:
        save(RAW / "creation-error.txt", repr(e) + "\n")
        entry.update({"outcome": "error before creation", "error_utc": utc(), "error": repr(e),
                      "cost_after_usd": str(cost(tracker))})
        write_log(state)
        say(f"stopping on {e!r}")
        return None
    entry["created_utc"] = utc()
    arns["program-set"] = task.id
    ARNS.write_text(json.dumps(arns))
    ARNS.chmod(0o600)
    after = cost(tracker)
    entry.update({"outcome": "created", "cost_after_submission_usd": str(after), "cost_task_usd": str(after - before)})
    write_log(state)
    say(f"created; tracker {after} (task {after - before})")
    return task


def follow(task, state):
    """Poll the task (read calls) until it is terminal, recording each state change."""
    seen = state["task"].setdefault("states_seen", [])
    last = seen[-1]["state"] if seen else None
    while True:
        st = task.state(use_cached_value=False)
        if st != last:
            seen.append({"state": st, "first_seen_utc": utc()})
            write_log(state)
            say(f"task: {st}")
            last = st
        if st in TERMINAL:
            return st
        time.sleep(POLL_S)


def fetch_raw(session, meta):
    """Download every object under the task's output folder, unparsed. Returns {relative key: parsed JSON or None}."""
    bucket, folder = meta["outputS3Bucket"], meta["outputS3Directory"]
    KNOWN.append(bucket)
    s3 = session.s3_client
    keys, token = [], None
    while True:
        kw = {"Bucket": bucket, "Prefix": folder + "/"}
        if token:
            kw["ContinuationToken"] = token
        page = s3.list_objects_v2(**kw)
        keys += [(o["Key"], o["Size"]) for o in page.get("Contents", [])]
        token = page.get("NextContinuationToken")
        if not token or len(keys) >= MAX_OUTPUT_OBJECTS:
            break
    listing = [{"relative_key": k[len(folder) + 1:], "size": n} for k, n in keys[:MAX_OUTPUT_OBJECTS]]
    save(RAW / "output-listing.json", json.dumps({"objects": listing, "truncated": len(keys) > MAX_OUTPUT_OBJECTS},
                                                 indent=1))
    parsed = {}
    for item in listing:
        rel = item["relative_key"]
        body = session.retrieve_s3_object_body(bucket, f"{folder}/{rel}")
        out = RAW / "output" / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        save(out, body)
        try:
            parsed[rel] = json.loads(body)
        except ValueError:
            parsed[rel] = None
    return parsed


def walk_raw(parsed):
    """Follow results.json by its own references (no SDK parsing). Returns per-program, per-executable records."""
    top = parsed.get("results.json") or {}
    rec = {"results.json keys": sorted(top), "s3Location_present": bool(top.get("s3Location")),
           "taskMetadata_ref": top.get("taskMetadata") if isinstance(top.get("taskMetadata"), str) else "inline",
           "programs": []}

    def resolve(x):
        return parsed.get(x) if isinstance(x, str) else x

    for i, pr in enumerate(top.get("programResults") or []):
        prog = resolve(pr) or {}
        p = {"ref": pr if isinstance(pr, str) else "inline", "keys": sorted(prog),
             "additionalMetadata": prog.get("additionalMetadata"), "executables": []}
        for j, er in enumerate(prog.get("executableResults") or []):
            ex = resolve(er) or {}
            m = ex.get("measurements")
            row = {"ref": er if isinstance(er, str) else "inline", "keys": sorted(ex),
                   "header": ex.get("braketSchemaHeader"), "inputsIndex": ex.get("inputsIndex"),
                   "measuredQubits": ex.get("measuredQubits"),
                   "measurementProbabilities": ex.get("measurementProbabilities"),
                   "measurements_type": type(m).__name__,
                   "measurements_len": len(m) if isinstance(m, list) else None,
                   "measurements_row_len": sorted({len(r) for r in m}) if isinstance(m, list) else None,
                   "measurements_first_ten": m[:10] if isinstance(m, list) else None}
            if isinstance(m, list) and m:
                ones = sum(1 for r in m if r and r[0] == 1)
                row.update({"ones": ones, "fraction_ones": ones / len(m)})
            other = {k: v for k, v in ex.items() if k not in ("measurements", "braketSchemaHeader")}
            row["other_fields"] = other
            p["executables"].append(row)
        rec["programs"].append(p)
    meta = resolve(top.get("taskMetadata"))
    rec["taskMetadata"] = meta
    return rec


def describe(x, depth=0):
    """Type and shape of an SDK object and its public attributes, for the record (no values beyond ten rows)."""
    import numpy as np
    if isinstance(x, np.ndarray):
        return {"type": "numpy.ndarray", "shape": list(x.shape), "dtype": str(x.dtype), "first_ten": x[:10].tolist()}
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x if not isinstance(x, str) or len(x) < 400 else x[:400] + "..."
    if isinstance(x, (list, tuple)):
        return {"type": type(x).__name__, "len": len(x), "items": [describe(v, depth + 1) for v in x[:4]]}
    if isinstance(x, dict):
        return {"type": "dict", "len": len(x), "items": {str(k): describe(v, depth + 1) for k, v in list(x.items())[:8]}}
    if depth > 4:
        return {"type": type(x).__module__ + "." + type(x).__name__}
    attrs = {}
    for name in dir(x):
        if name.startswith("_"):
            continue
        try:
            v = getattr(x, name)
        except Exception as e:
            attrs[name] = f"<raises {type(e).__name__}>"
            continue
        if callable(v):
            continue
        attrs[name] = describe(v, depth + 1)
    return {"type": type(x).__module__ + "." + type(x).__name__, "attributes": attrs}


def finish_task(device, task, state, tracker, qubit):
    session = task._aws_session
    meta = session.get_quantum_task(task.id)
    meta.pop("ResponseMetadata", None)
    entry = state["task"]
    entry.update({"status": meta.get("status"), "failureReason": meta.get("failureReason"),
                  "createdAt": meta.get("createdAt"), "endedAt": meta.get("endedAt"), "fetch_utc": utc()})
    save(RAW / "task-metadata.json", json.dumps(meta, indent=1, default=str))
    save(RAW / "task-states.json", json.dumps(entry.get("states_seen"), indent=1, default=str))
    caps, read_utc, _, s = read_properties(device, "fetch")
    entry["properties_at_fetch"] = {"read_utc": read_utc, "file": f"raw/properties-fetch-{s}.json",
                                    **qubit_figures(caps, qubit)}
    write_log(state)
    parsed = fetch_raw(session, meta)
    entry["raw_walk_file"] = "raw/raw-walk.json"
    save(RAW / "raw-walk.json", json.dumps(walk_raw(parsed), indent=1, default=str))
    say(f"raw files saved: {sorted(parsed)}")
    try:
        result = task.result()
        save(RAW / "sdk-result-described.json", json.dumps(describe(result), indent=1, default=str))
        entry["sdk_parse"] = "ok"
    except Exception as e:
        save(RAW / "sdk-result-error.txt", repr(e) + "\n")
        entry["sdk_parse"] = f"error: {e!r}"
    entry["cost_after_result_usd"] = str(cost(tracker))
    write_log(state)
    say(f"task {entry['status']}; T1 {entry['properties_at_fetch']['T1_s']} T2 "
        f"{entry['properties_at_fetch']['T2_s']} at fetch; tracker {entry['cost_after_result_usd']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule-sha", required=True, help="the hash the author posted in the public issue")
    ap.add_argument("--fetch-only", action="store_true", help="follow the task already created; submit nothing")
    a = ap.parse_args()

    if sha(RULE) != RULE_SHA or a.rule_sha.lower() != RULE_SHA:
        say(f"stop: rule hash {sha(RULE)} does not match the posted hash")
        sys.exit(2)
    state = load_log()
    arns = json.loads(ARNS.read_text()) if ARNS.exists() else {}
    if state.get("task") and not a.fetch_only:
        say("stop: a submission is already recorded in run-log.json; use --fetch-only")
        sys.exit(4)

    device = AwsDevice(DEVICE_ARN)
    with Tracker() as tracker:
        if a.fetch_only:
            _USED.append("program-set")   # run stays closed in a resume
            if "program-set" not in arns:
                say("stop: no task was created; nothing to follow")
                sys.exit(4)
            OFFSET[0] = Decimal(state["task"].get("cost_after_submission_usd", "0"))
            say(f"fetch only: carrying forward tracker total {OFFSET[0]}")
            task = AwsQuantumTask(arns["program-set"])
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
            est = estimate_cost()
            state["estimate_usd"] = str(est)
            write_log(state)
            say(f"price list estimate for one task of {SHOTS_TOTAL} shots: {est}")
            if est >= STOP_TASK:
                say(f"stop: estimate {est} is not under {STOP_TASK}")
                sys.exit(3)
            sources = [(PROGRAMS / f"task-{label}.qasm").read_text() for label in LABELS]
            program_set = ProgramSet(sources, shots_per_executable=SHOTS_PER_EXECUTABLE)
            ir = program_set.to_ir()
            save(RAW / "program-set-ir.json", json.dumps(json.loads(ir.json()), indent=1))
            state["program_set"] = {"ir_file_sha256": sha(RAW / "program-set-ir.json"),
                                    "total_executables": program_set.total_executables,
                                    "shots_per_executable": program_set.shots_per_executable,
                                    "total_shots": program_set.total_shots,
                                    "executables": list(program_set.enumerate_executables())}
            write_log(state)
            if time.time() - read_t > PROPERTIES_MAX_AGE_S:
                say("stop: properties older than ten minutes before the submission")
                sys.exit(3)
            device.refresh_metadata()
            if device.status != "ONLINE" or not in_window():
                say(f"stop before the submission: status {device.status}, in window {in_window()}")
                sys.exit(3)
            task = submit(device, program_set, state, tracker, arns)
            if task is None:
                say("stop: creation error recorded; no rewrite, no second task")
                finish(state, tracker)
                return
            if Decimal(state["task"]["cost_task_usd"]) >= STOP_TASK:
                state["hard_stop"] = f"tracker cost {state['task']['cost_task_usd']} is not under {STOP_TASK}"
                write_log(state)
                say(f"hard stop: {state['hard_stop']}; the task is not followed (resume with --fetch-only if the "
                    "author says so)")
                sys.exit(6)
        qubit = state["choice"]["qubit"]
        try:
            follow(task, state)
            finish_task(device, task, state, tracker, qubit)
        except Exception as e:
            say(f"stop in the follow loop on {e!r}; resume with --fetch-only")
            write_log(state)
            sys.exit(5)
        finish(state, tracker)


def finish(state, tracker):
    state["tracker_end_usd"] = str(cost(tracker))
    state["tracker_statistics"] = tracker.quantum_tasks_statistics()
    state["ended_utc"] = utc()
    write_log(state)
    say(f"tracker end {state['tracker_end_usd']}")


if __name__ == "__main__":
    main()
