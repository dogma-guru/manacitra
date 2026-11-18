"""Shared helpers for Braket probe 02, the scaling of the wait on Cepheus-1-108Q (rule of 21 October 2026).

Copied from probe 01's hand-back scripts/common.py. The redaction search is unchanged; the guard is probe 01's with the
labels and shots of probe 02: AwsDevice.run is allowed for exactly the labelled tasks of the rule (A0, A1, A2, B1), each
once, with that label's shots (A0 100, A1 200, A2 100, B1 200), on this device, with the program text equal to the saved
filled program for that label. run_batch, hybrid jobs, program sets and the local simulator still raise.
Credentials come from the named AWS profile in the environment (AWS_PROFILE); they are never printed or stored.
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
LETTERS = ("A0", "A1", "A2", "B1")                     # the labels, in submission order
SHOTS = {"A0": 100, "A1": 200, "A2": 100, "B1": 200}
TAG_KEY = "probe-02"
MAX_TASKS = 4


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


def save_clean(path, text):
    """Redact, log, write. Returns the entries."""
    path = Path(path)
    clean, entries = redact(text, path.relative_to(HERE).as_posix())
    path.write_text(clean)
    log_redactions(entries or [{"file": path.relative_to(HERE).as_posix(), "kind": "none found", "count": 0,
                                "action": "none"}])
    return entries


def scrub(s):
    return redact(s, "stdout")[0]


_ARMED = contextvars.ContextVar("probe_armed", default=None)   # the label being submitted, set only inside run
_USED = []                                                        # labels already passed to run, in order


def blocked(*a, **k):
    raise RuntimeError("blocked by probe-02 guard: only AwsDevice.run for the labelled tasks is allowed")


def guard():
    """Assert the AWS profile is set by name; allow AwsDevice.run only for the rule's labelled tasks; block the rest.

    Call as device.run(program, shots=SHOTS[label], letter=label). The guard checks, before anything is sent:
    the device is Cepheus-1-108Q; the label is one of A0, A1, A2, B1 and has not been used; at most four tasks in all;
    shots is exactly that label's; the specification is a single OpenQASM program whose source hashes to
    programs/task-<label>.qasm; the tags are exactly {"probe-02": label}. The label is marked used before the call,
    so a failed call is never retried.
    Underneath, AwsQuantumTask.create and AwsSession.create_quantum_task refuse unless a guarded run is in progress,
    and only one creation per run is allowed.
    """
    assert os.environ.get("AWS_PROFILE"), "AWS_PROFILE must name the profile"
    import braket.aws.aws_device as ad
    if getattr(ad.AwsDevice.run, "_probe_guard", False):
        return                                                    # already installed in this process
    import braket.aws.aws_quantum_job as aqj
    import braket.aws.aws_quantum_task as aqt
    import braket.aws.aws_session as asess
    from braket.ir.openqasm import Program

    orig_run = ad.AwsDevice.run
    orig_create = aqt.AwsQuantumTask.create
    orig_session_create = asess.AwsSession.create_quantum_task
    created = {}

    def guarded_run(self, task_specification, *args, letter=None, shots=None, tags=None, **kwargs):
        if args:
            raise RuntimeError("probe-02 guard: positional arguments after the program are not allowed")
        if self.arn != DEVICE_ARN:
            raise RuntimeError(f"probe-02 guard: device {self.arn} is not {DEVICE_NAME}")
        if letter not in LETTERS:
            raise RuntimeError(f"probe-02 guard: letter {letter!r} is not a labelled task")
        if letter in _USED:
            raise RuntimeError(f"probe-02 guard: task {letter} was already submitted once")
        if len(_USED) >= MAX_TASKS:
            raise RuntimeError("probe-02 guard: four tasks already submitted")
        if shots != SHOTS[letter]:
            raise RuntimeError(f"probe-02 guard: shots for {letter} must be {SHOTS[letter]}, got {shots}")
        if type(task_specification) is not Program:
            raise RuntimeError("probe-02 guard: only a single OpenQASM program is allowed (no circuit object, no program set)")
        if task_specification.inputs:
            raise RuntimeError("probe-02 guard: program inputs are not allowed")
        filled = PROGRAMS / f"task-{letter}.qasm"
        if hashlib.sha256(task_specification.source.encode()).hexdigest() != sha(filled):
            raise RuntimeError(f"probe-02 guard: program does not match {filled.name}")
        if tags != {TAG_KEY: letter}:
            raise RuntimeError("probe-02 guard: tags must be exactly {'probe-02': label}")
        allowed_kw = {"poll_timeout_seconds", "poll_interval_seconds"}
        if set(kwargs) - allowed_kw:
            raise RuntimeError(f"probe-02 guard: arguments not allowed: {sorted(set(kwargs) - allowed_kw)}")
        _USED.append(letter)
        token = _ARMED.set(letter)
        try:
            return orig_run(self, task_specification, shots=shots, tags=tags, **kwargs)
        finally:
            _ARMED.reset(token)

    def guarded_create(*a, **k):
        letter = _ARMED.get()
        if letter is None:
            raise RuntimeError("probe-02 guard: AwsQuantumTask.create outside a guarded run")
        if created.get(letter):
            raise RuntimeError(f"probe-02 guard: a second creation for task {letter}")
        created[letter] = True
        return orig_create(*a, **k)

    def guarded_session_create(self, **boto3_kwargs):
        letter = _ARMED.get()
        if letter is None:
            raise RuntimeError("probe-02 guard: create_quantum_task outside a guarded run")
        action = json.loads(boto3_kwargs.get("action", "{}"))
        if action.get("braketSchemaHeader", {}).get("name") != "braket.ir.openqasm.program":
            raise RuntimeError("probe-02 guard: action is not a single OpenQASM program")
        if boto3_kwargs.get("shots") != SHOTS[letter] or boto3_kwargs.get("deviceArn") != DEVICE_ARN:
            raise RuntimeError("probe-02 guard: shots or device changed below run")
        if hashlib.sha256(action.get("source", "").encode()).hexdigest() != sha(PROGRAMS / f"task-{letter}.qasm"):
            raise RuntimeError("probe-02 guard: program changed below run")
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
