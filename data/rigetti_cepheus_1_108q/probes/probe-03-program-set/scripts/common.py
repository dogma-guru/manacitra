"""Shared helpers for Braket probe 03, attempt 2, one unchanged resubmission (rule of 21 October 2026).

Attempt 2: copied from attempt 1's scripts/common.py (attempt-1/scripts/common.py). Changed: the tags carry a second
tag, {"attempt-2": "resubmission"}; the guard also requires the serialised program set, in the form attempt 1 saved it
(json.dumps(..., indent=1) of the action), to hash to attempt 1's raw/program-set-ir.json, both at run and below it.
Attempt 1's description follows.

Copied from probe 02's hand-back scripts/common.py (kept beside this file as common-probe02-start.py). The redaction
search is probe 02's, with one addition: save_clean also replaces any literal string passed in `known` (the results
bucket name read from the task metadata), so a bucket with a name outside the patterns is still kept out.
The guard is changed for probe 03: AwsDevice.run is allowed exactly once, on this device, for a ProgramSet whose two
entries are the OpenQASM texts of programs/task-E1.qasm and programs/task-E2.qasm in that order, with shots=200 and the
one tag {"probe-03": "program-set"}. A second run, run_batch, hybrid jobs, any other task specification and the local
simulator all raise. Credentials come from the named AWS profile in the environment (AWS_PROFILE); they are never
printed or stored.
"""
import contextvars
import hashlib
import json
import os
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent          # probe working folder
RAW = HERE / "raw"
PROGRAMS = HERE / "programs"
DEVICE_ARN = "arn:aws:braket:us-west-1::device/qpu/rigetti/Cepheus-1-108Q"   # public identifier, no account number
DEVICE_NAME = "Cepheus-1-108Q"
REDACTION_LOG = HERE / "redaction-log.md"

# Guard limits, from sections 1 and 3 of the rule.
LABELS = ("E1", "E2")                                  # the executables, in program-set order
SHOTS_TOTAL = 200                                      # passed to run as shots=
SHOTS_PER_EXECUTABLE = 100
TAGS = {"probe-03": "program-set", "attempt-2": "resubmission"}
PROGRAM_SET_SCHEMA = "braket.ir.openqasm.program_set"
IR_SHA = "7b283c57b488513b9cd0a489d8db53e69df6b88aab8befac3a5fb4e6f5ba89d2"   # attempt 1, raw/program-set-ir.json


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stamp():
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# Secret patterns. A run of exactly 12 digits preceded by "." is a decimal fraction (a calibration figure),
# not an account number; it is counted and logged but not redacted.
ACCT_ARN_RE = re.compile(r"arn:aws[a-z-]*:[a-z0-9-]*:[a-z0-9-]*:\d{12}:[^\s\"']*")
TWELVE_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")
SHA_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z][\w.]*")
PRESIGN_RE = re.compile(r"(X-Amz-(?:Credential|Signature|Security-Token)=)[^&\"\s]*")
S3_HOST_RE = re.compile(r"https://([a-z0-9][a-z0-9.-]{1,61}[a-z0-9])\.s3[.-]")
S3_PATH_RE = re.compile(r"https://s3[.-][a-z0-9.-]*amazonaws\.[a-z.]+/([a-z0-9][a-z0-9.-]{1,61}[a-z0-9])/")
# Braket's default results buckets start "amazon-braket-"; the Python packages and repositories with that prefix are not buckets.
# Narrowed 2026-10-21T12:02:29Z after the first final audit matched package names (recorded in the redaction log).
BRAKET_BUCKET_RE = re.compile(r"amazon-braket-(?!sdk\b|schemas\b|schemas-python\b|default-simulator\b|qdmi-device\b)[a-z0-9-]+")


def redact(text, label):
    """Return (clean_text, entries). Each entry describes one kind of redaction or one considered non-redaction."""
    entries = []
    out = text

    def sub(rx, repl, kind):
        nonlocal out
        n = len(rx.findall(out))
        if n:
            out = rx.sub(repl, out)
            entries.append({"file": label, "kind": kind, "count": n, "action": "redacted"})

    sub(ACCT_ARN_RE, "[redacted]", "arn with account number")
    sub(KEY_RE, "[redacted]", "access key id")
    sub(PRESIGN_RE, lambda m: m.group(1) + "[redacted]", "presigned URL credential, signature or token")
    sub(S3_HOST_RE, lambda m: m.group(0).replace(m.group(1), "[redacted]"), "bucket name in URL host")
    sub(S3_PATH_RE, lambda m: m.group(0).replace(m.group(1), "[redacted]"), "bucket name in URL path")
    sub(BRAKET_BUCKET_RE, "[redacted]", "bucket name")
    sub(EMAIL_RE, "[redacted]", "email address")
    # Added 2026-10-21 for probe 02's final search: a 12-digit run inside a 64-character hex string is part of a
    # SHA-256 hash (the rule's hash begins with twelve digits), not an account number; it is counted and logged but not
    # redacted. The runner first checked that no such run equals the account number.
    hashes = [(m.start(), m.end()) for m in SHA_RE.finditer(out)]
    in_hash = lambda m: any(h0 <= m.start() and m.end() <= h1 for h0, h1 in hashes)
    fractions, others, hash_runs = 0, 0, 0
    for m in TWELVE_RE.finditer(out):
        if m.start() > 0 and out[m.start() - 1] == ".":
            fractions += 1
        elif in_hash(m):
            hash_runs += 1
        else:
            others += 1
    if others:
        out = re.sub(r"(?<![\d.])\d{12}(?!\d)", lambda m: m.group(0) if in_hash(m) else "[redacted]", out)
        entries.append({"file": label, "kind": "12-digit number", "count": others, "action": "redacted"})
    if fractions:
        entries.append({"file": label, "kind": "12-digit run after a decimal point (a figure's fraction digits)",
                        "count": fractions, "action": "not redacted"})
    if hash_runs:
        entries.append({"file": label, "kind": "12-digit run inside a SHA-256 hash", "count": hash_runs,
                        "action": "not redacted"})
    return out, entries


def log_redactions(entries, when=None):
    when = when or utc()
    new = not REDACTION_LOG.exists()
    with REDACTION_LOG.open("a") as f:
        if new:
            f.write("# Redaction log\n\nEach saved raw file was searched before writing. One line per kind found.\n\n"
                    "| UTC | file | kind | count | action |\n|---|---|---|---|---|\n")
        for e in entries:
            f.write(f"| {when} | {e['file']} | {e['kind']} | {e['count']} | {e['action']} |\n")


def redact_known(text, label, known):
    """Replace each literal string in `known` (bucket names read at run time) before the pattern search."""
    entries = []
    for k in known or ():
        if k and k in text:
            entries.append({"file": label, "kind": "bucket name (literal, from task metadata)",
                            "count": text.count(k), "action": "redacted"})
            text = text.replace(k, "[redacted]")
    return text, entries


def save_clean(path, text, known=None):
    """Redact, log, write. Returns the entries."""
    path = Path(path)
    label = path.relative_to(HERE).as_posix()
    text, known_entries = redact_known(text, label, known)
    clean, entries = redact(text, label)
    entries = known_entries + entries
    path.write_text(clean)
    log_redactions(entries or [{"file": path.relative_to(HERE).as_posix(), "kind": "none found", "count": 0,
                                "action": "none"}])
    return entries


def scrub(s, known=None):
    return redact(redact_known(s, "stdout", known)[0], "stdout")[0]


_ARMED = contextvars.ContextVar("probe_armed", default=False)   # True only inside the one guarded run
_USED = []                                                         # filled once run has been entered


def blocked(*a, **k):
    raise RuntimeError("blocked by probe-03 guard: only one AwsDevice.run on the program set is allowed")


def filled_sources():
    """The two filled program texts, read from programs/task-E1.qasm and task-E2.qasm."""
    return [(PROGRAMS / f"task-{label}.qasm").read_text() for label in LABELS]


def saved_form_sha(action_json):
    """SHA-256 of the action in the form attempt 1 saved it: json.dumps(json.loads(action), indent=1)."""
    return hashlib.sha256(json.dumps(json.loads(action_json), indent=1).encode()).hexdigest()


def guard():
    """Assert the AWS profile is set by name; allow one AwsDevice.run on the program set; block the rest.

    Call as device.run(program_set, shots=SHOTS_TOTAL, tags=TAGS). The guard checks, before anything is sent:
    run has not been entered before in this process; the device is Cepheus-1-108Q; the specification is a
    braket.program_sets.ProgramSet with shots_per_executable 100 whose entries are exactly two OpenQASM strings equal,
    in order, to programs/task-E1.qasm and task-E2.qasm; shots is exactly 200; the tags are exactly TAGS. Run is marked
    used before the call, so a failed call is never retried.
    Underneath, AwsQuantumTask.create and AwsSession.create_quantum_task refuse unless the guarded run is in progress,
    allow one creation only, and check again that the action sent is an OpenQASM program set of those two texts with
    no inputs, shots 200, on this device.
    """
    assert os.environ.get("AWS_PROFILE"), "AWS_PROFILE must name the profile"
    import braket.aws.aws_device as ad
    if getattr(ad.AwsDevice.run, "_probe_guard", False):
        return                                                    # already installed in this process
    import braket.aws.aws_quantum_job as aqj
    import braket.aws.aws_quantum_task as aqt
    import braket.aws.aws_session as asess
    from braket.program_sets import ProgramSet

    orig_run = ad.AwsDevice.run
    orig_create = aqt.AwsQuantumTask.create
    orig_session_create = asess.AwsSession.create_quantum_task
    created = []

    def guarded_run(self, task_specification, *args, shots=None, tags=None, **kwargs):
        if _USED:
            raise RuntimeError("probe-03 guard: run was already entered once; no second task")
        if args:
            raise RuntimeError("probe-03 guard: positional arguments after the program set are not allowed")
        if self.arn != DEVICE_ARN:
            raise RuntimeError(f"probe-03 guard: device {self.arn} is not {DEVICE_NAME}")
        if type(task_specification) is not ProgramSet:
            raise RuntimeError("probe-03 guard: only a braket.program_sets.ProgramSet is allowed")
        entries = task_specification.entries
        if len(entries) != 2 or any(type(e) is not str for e in entries):
            raise RuntimeError("probe-03 guard: the program set must be exactly two OpenQASM strings")
        if list(entries) != filled_sources():
            raise RuntimeError("probe-03 guard: program texts do not match programs/task-E1.qasm and task-E2.qasm")
        if task_specification.shots_per_executable != SHOTS_PER_EXECUTABLE:
            raise RuntimeError("probe-03 guard: shots_per_executable must be 100")
        if shots != SHOTS_TOTAL:
            raise RuntimeError(f"probe-03 guard: shots must be {SHOTS_TOTAL}, got {shots}")
        if tags != TAGS:
            raise RuntimeError(f"probe-03 guard: tags must be exactly {TAGS}")
        if saved_form_sha(task_specification.to_ir().json()) != IR_SHA:
            raise RuntimeError("probe-03 guard: the serialised program set differs from attempt 1's")
        allowed_kw = {"poll_timeout_seconds", "poll_interval_seconds"}
        if set(kwargs) - allowed_kw:
            raise RuntimeError(f"probe-03 guard: arguments not allowed: {sorted(set(kwargs) - allowed_kw)}")
        _USED.append("program-set")
        token = _ARMED.set(True)
        try:
            return orig_run(self, task_specification, shots=shots, tags=tags, **kwargs)
        finally:
            _ARMED.reset(token)

    def guarded_create(*a, **k):
        if not _ARMED.get():
            raise RuntimeError("probe-03 guard: AwsQuantumTask.create outside the guarded run")
        if created:
            raise RuntimeError("probe-03 guard: a second creation")
        created.append(True)
        return orig_create(*a, **k)

    def guarded_session_create(self, **boto3_kwargs):
        if not _ARMED.get():
            raise RuntimeError("probe-03 guard: create_quantum_task outside the guarded run")
        action = json.loads(boto3_kwargs.get("action", "{}"))
        if action.get("braketSchemaHeader", {}).get("name") != PROGRAM_SET_SCHEMA:
            raise RuntimeError("probe-03 guard: action is not an OpenQASM program set")
        programs = action.get("programs") or []
        if [p.get("source") for p in programs] != filled_sources() or any(p.get("inputs") for p in programs):
            raise RuntimeError("probe-03 guard: program set changed below run")
        if boto3_kwargs.get("shots") != SHOTS_TOTAL or boto3_kwargs.get("deviceArn") != DEVICE_ARN:
            raise RuntimeError("probe-03 guard: shots or device changed below run")
        if boto3_kwargs.get("tags") != TAGS:
            raise RuntimeError("probe-03 guard: tags changed below run")
        if saved_form_sha(boto3_kwargs.get("action", "{}")) != IR_SHA:
            raise RuntimeError("probe-03 guard: the serialised program set differs from attempt 1's below run")
        return orig_session_create(self, **boto3_kwargs)

    guarded_run._probe_guard = True
    ad.AwsDevice.run = guarded_run
    ad.AwsDevice.run_batch = blocked
    aqt.AwsQuantumTask.create = staticmethod(guarded_create)
    asess.AwsSession.create_quantum_task = guarded_session_create
    asess.AwsSession.create_job = blocked
    aqj.AwsQuantumJob.create = blocked
    try:
        import braket.jobs.quantum_job_creation as qjc
        qjc.prepare_quantum_job = blocked
    except Exception:
        pass
    try:
        import braket.jobs as jobs
        jobs.hybrid_job = blocked
    except Exception:
        pass
    try:
        import braket.devices.local_simulator as ls
        ls.LocalSimulator.run = blocked
        ls.LocalSimulator.run_batch = blocked
    except Exception:
        pass
