"""Probe 03, attempt 2 at the go: one unchanged resubmission of attempt 1's program set (the author's ruling of
21 October 2026, under the same rule). Reads and saves the properties for the record, checks the serialised set
against attempt 1's, submits it once with shots=200, follows it to the end, reads the properties again at the fetch,
and saves the raw result files before any SDK parsing, then the SDK's parsed view of them.

Started from attempt 1's scripts/run_probe.py (attempt-1/scripts/run_probe.py).
Changed for attempt 2: no choice of qubit, d or frames and no fill (the programs are attempt 1's, checked by hash);
the properties are read once before the call for the record only; the serialised set is hashed in the form attempt 1
saved it and must equal attempt 1's raw/program-set-ir.json, or the run stops before the call; the tags carry
{"attempt-2": "resubmission"}; a creation error is compared with attempt 1's; at the fetch, each executable's
`measurements_from_device` flag and whether its raw result carries `measurements` or only `measurementProbabilities`
are recorded in raw/executable-flags.json.
Kept: the guard (common.guard), the price list estimate (stop at [cost] or more), the stop on every creation error,
the raw download of every file under the task's output folder, the SDK description.

Usage (from the probe working folder, after the author's go for attempt 2):
  AWS_PROFILE=<profile name> ../.venv/bin/python scripts/run_probe.py --rule-sha <hash from the public issue>
  AWS_PROFILE=<profile name> ../.venv/bin/python scripts/run_probe.py --rule-sha <hash> --fetch-only
      (read calls only: follows the task already created, for a resume after the follow loop stopped)
"""
import argparse
import hashlib
import json
import stat
import sys
import time
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (_USED, DEVICE_ARN, HERE, IR_SHA, LABELS, PROGRAMS, RAW, SHOTS_PER_EXECUTABLE, SHOTS_TOTAL, TAGS,
                    guard, save_clean, saved_form_sha, scrub, sha, stamp, utc)

guard()
from botocore.exceptions import ClientError
from braket.aws import AwsDevice, AwsQuantumTask
from braket.program_sets import ProgramSet
from braket.tracking import Tracker
from braket.tracking.tracker import _get_qpu_task_cost

RULE = HERE / "braket-probe-03-program-set-rule.md"
RULE_SHA = "b9748919eb26918976fbfd4ff0028899294cffbc97975e1cb6167e570811fb27"   # recorded at the copy, 2026-10-21
ATTEMPT_1 = HERE / "attempt-1"
PROGRAM_SHA = {"E1": "63eb31af921a4fb2e6c844c32b404c51da7725972ea90742a519e8603ebcdaae",
               "E2": "a00a679a705fb7cae25e92687fe0228a81bc4ff1d943ed8a40c4e6be765e2761"}   # attempt 1, as submitted
QUBIT = 99          # attempt 1's choice, fixed
D_NS = 30900        # attempt 1's d, fixed
LOG = HERE / "run.log"
RUN_LOG = HERE / "run-log.json"
ARNS = HERE / ".task-arns.local.json"   # the task ARN carries the account number: kept in the working folder, never handed back
# Availability windows, UTC, as published in service.executionWindows (Everyday); checked again before the go.
WINDOWS = ((0, 0, 1, 59), (4, 0, 13, 59), (16, 0, 23, 59))
STOP_TASK = Decimal("[cost]")
PROPERTIES_MAX_AGE_S = 10 * 60
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


def longest_t2(caps):
    """For the record only: which qubit has the longest published T2 at this read. Nothing is re-chosen."""
    one = caps["standardized"]["oneQubitProperties"]
    t2, q = sorted(((v["T2"]["value"], q) for q, v in one.items()), key=lambda x: (-x[0], int(x[1])))[0]
    return {"qubit": int(q), "T2_s": t2}


def estimate_cost():
    """The Tracker's own price lookup, for one task of 200 shots on this device (pricing read call only)."""
    region = DEVICE_ARN.split(":")[3]
    details = {"status": "CREATED", "device": DEVICE_ARN, "shots": SHOTS_TOTAL, "job_task": False}
    return _get_qpu_task_cost(f"arn:aws:braket:{region}::quantum-task/estimate", details)


OFFSET = [Decimal(0)]   # cost recorded by an earlier process of this run (only after a --fetch-only resume)


def cost(tracker):
    """The session total: this process's Tracker plus any earlier process's recorded total."""
    return OFFSET[0] + Decimal(str(tracker.qpu_tasks_cost())) + Decimal(str(tracker.simulator_tasks_cost()))


def compare_with_attempt_1(text):
    """Is the creation error the same text as attempt 1's? Compared on the saved file and on the response fields."""
    first = (ATTEMPT_1 / "raw" / "creation-error.txt").read_text()
    def fields(t):
        try:
            return json.loads(t[t.index("\n\n{") + 2:])
        except ValueError:
            return None
    return {"same_file_text": text == first, "same_response_fields": fields(text) == fields(first)
            and fields(text) is not None, "attempt_1_file_sha256": sha(ATTEMPT_1 / "raw" / "creation-error.txt")}


def submit(device, program_set, state, tracker, arns):
    """Submit the program set once. Returns the task, or None after a creation error (saved verbatim)."""
    before = cost(tracker)
    entry = state["task"] = {"cost_before_usd": str(before), "shots": SHOTS_TOTAL, "tags": TAGS,
                             "programs": {label: sha(PROGRAMS / f"task-{label}.qasm") for label in LABELS}}
    entry["submitted_utc"] = utc()
    write_log(state)
    say(f"submitting the program set ({len(program_set.entries)} entries, shots={SHOTS_TOTAL}, tags {TAGS})")
    try:
        task = device.run(program_set, shots=SHOTS_TOTAL, tags=TAGS)
    except ClientError as e:
        resp = {k: v for k, v in e.response.items() if k != "ResponseMetadata"}
        text = f"{e}\n\n{json.dumps(resp, indent=1, default=str)}\n"
        save(RAW / "creation-error.txt", text)
        entry.update({"outcome": "ClientError at creation", "error_code": resp.get("Error", {}).get("Code"),
                      "error_utc": utc(), "cost_after_usd": str(cost(tracker)),
                      "compared_with_attempt_1": compare_with_attempt_1((RAW / "creation-error.txt").read_text())})
        write_log(state)
        say(f"creation error: {e}")
        say(f"compared with attempt 1: {entry['compared_with_attempt_1']}")
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
    ARNS.chmod(stat.S_IRUSR | stat.S_IWUSR)
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


def executable_flags(result, walk):
    """The record the rule does not name (runner prompt, attempt 2): per executable, the SDK's
    measurements_from_device flag, and whether the raw result carries measurements or only measurementProbabilities."""
    raw_rows = [e for p in walk["programs"] for e in p["executables"]]
    sdk_rows = []
    for i, comp in enumerate(getattr(result, "entries", []) or []):
        for j, me in enumerate(getattr(comp, "entries", [comp]) or []):
            m = getattr(me, "measurements", None)
            sdk_rows.append({"program_index": i, "executable_index": j,
                             "measurements_from_device": getattr(me, "measurements_from_device", None),
                             "probabilities_from_device": getattr(me, "probabilities_from_device", None),
                             "sdk_measurements_shape": list(m.shape) if hasattr(m, "shape") else None})
    out = []
    for k in range(max(len(raw_rows), len(sdk_rows))):
        raw = raw_rows[k] if k < len(raw_rows) else {}
        carries = ("measurements" if raw.get("measurements_type") == "list"
                   else "measurementProbabilities only" if raw.get("measurementProbabilities") else "neither")
        out.append({"order": k, "raw_carries": carries, "raw_measurements_len": raw.get("measurements_len"),
                    **(sdk_rows[k] if k < len(sdk_rows) else {"sdk": "no parsed entry"})})
    return out


def finish_task(device, task, state, tracker):
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
                                    **qubit_figures(caps, QUBIT)}
    write_log(state)
    parsed = fetch_raw(session, meta)
    walk = walk_raw(parsed)
    entry["raw_walk_file"] = "raw/raw-walk.json"
    save(RAW / "raw-walk.json", json.dumps(walk, indent=1, default=str))
    say(f"raw files saved: {sorted(parsed)}")
    result = None
    try:
        result = task.result()
        save(RAW / "sdk-result-described.json", json.dumps(describe(result), indent=1, default=str))
        entry["sdk_parse"] = "ok"
    except Exception as e:
        save(RAW / "sdk-result-error.txt", repr(e) + "\n")
        entry["sdk_parse"] = f"error: {e!r}"
    flags = executable_flags(result, walk)
    save(RAW / "executable-flags.json", json.dumps(flags, indent=1, default=str))
    entry["executable_flags"] = flags
    entry["cost_after_result_usd"] = str(cost(tracker))
    write_log(state)
    say(f"task {entry['status']}; flags {flags}; T1 {entry['properties_at_fetch']['T1_s']} T2 "
        f"{entry['properties_at_fetch']['T2_s']} at fetch; tracker {entry['cost_after_result_usd']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule-sha", required=True, help="the hash the author posted in the public issue")
    ap.add_argument("--fetch-only", action="store_true", help="follow the task already created; submit nothing")
    a = ap.parse_args()

    if sha(RULE) != RULE_SHA or a.rule_sha.lower() != RULE_SHA:
        say(f"stop: rule hash {sha(RULE)} does not match the posted hash")
        sys.exit(2)
    for label in LABELS:
        if sha(PROGRAMS / f"task-{label}.qasm") != PROGRAM_SHA[label]:
            say(f"stop: programs/task-{label}.qasm is not attempt 1's program")
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
            device.refresh_metadata()
            if device.status != "ONLINE" or not in_window() or window_left_s() < 20 * 60:
                say(f"stop: status {device.status}, in window {in_window()}, window seconds left {window_left_s()}")
                sys.exit(3)
            caps, read_utc, read_t, s = read_properties(device, "presubmission")
            state.update({"properties_read_utc": read_utc, "properties_file": f"raw/properties-presubmission-{s}.json",
                          "fixed": {"qubit": QUBIT, "d_ns": D_NS, "programs": PROGRAM_SHA},
                          "qubit_at_read": qubit_figures(caps, QUBIT), "longest_T2_at_read": longest_t2(caps)})
            write_log(state)
            say(f"properties read for the record: qubit {QUBIT} {state['qubit_at_read']}; longest T2 at this read "
                f"{state['longest_T2_at_read']} (nothing re-chosen)")
            est = estimate_cost()
            state["estimate_usd"] = str(est)
            write_log(state)
            say(f"price list estimate for one task of {SHOTS_TOTAL} shots: {est}")
            if est >= STOP_TASK:
                say(f"stop: estimate {est} is not under {STOP_TASK}")
                sys.exit(3)
            sources = [(PROGRAMS / f"task-{label}.qasm").read_text() for label in LABELS]
            program_set = ProgramSet(sources, shots_per_executable=SHOTS_PER_EXECUTABLE)
            action = program_set.to_ir().json()
            got = saved_form_sha(action)
            save(RAW / "program-set-ir.json", json.dumps(json.loads(action), indent=1))
            state["program_set"] = {"saved_form_sha256": got, "attempt_1_sha256": IR_SHA, "equal": got == IR_SHA,
                                    "ir_file_sha256": sha(RAW / "program-set-ir.json"),
                                    "compact_action_sha256": hashlib.sha256(action.encode()).hexdigest(),
                                    "total_executables": program_set.total_executables,
                                    "shots_per_executable": program_set.shots_per_executable,
                                    "total_shots": program_set.total_shots,
                                    "executables": list(program_set.enumerate_executables())}
            write_log(state)
            say(f"serialised set {got}; attempt 1 {IR_SHA}; equal {got == IR_SHA}")
            if got != IR_SHA or sha(RAW / "program-set-ir.json") != IR_SHA:
                say("stop: the serialised program set differs from attempt 1's; nothing submitted")
                sys.exit(3)
            if time.time() - read_t > PROPERTIES_MAX_AGE_S:
                say("stop: properties older than ten minutes before the submission")
                sys.exit(3)
            device.refresh_metadata()
            if device.status != "ONLINE" or not in_window():
                say(f"stop before the submission: status {device.status}, in window {in_window()}")
                sys.exit(3)
            task = submit(device, program_set, state, tracker, arns)
            if task is None:
                say("stop: creation error recorded; no rewrite, no further task")
                finish(state, tracker)
                return
            if Decimal(state["task"]["cost_task_usd"]) >= STOP_TASK:
                state["hard_stop"] = f"tracker cost {state['task']['cost_task_usd']} is not under {STOP_TASK}"
                write_log(state)
                say(f"hard stop: {state['hard_stop']}; the task is not followed (resume with --fetch-only if the "
                    "author says so)")
                sys.exit(6)
        try:
            follow(task, state)
            finish_task(device, task, state, tracker)
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
