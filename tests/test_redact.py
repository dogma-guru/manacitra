# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Amendment A18, ruling R1: a provider's text reaches neither the ledger, nor stdout or stderr, nor any log handler
with an account's identifier in it, on every backend (the review of pull request 21, category 6).

Every marker here is made up, shaped like a CRN, an instance name, a token, an account ID, a hub/group/project and an
email address. Each is assembled at run time, so this file's own text holds none of them (the identifier scan reads
it). No account is read and nothing is sent: the provider's clients are fakes, or the installed client's own code run
on a fabricated object."""

import importlib.util
import io
import logging
import traceback
from pathlib import Path
from types import SimpleNamespace

import pytest

from manacitra.backends import redact
from manacitra.backends.base import GuardedSubmit, JobHandle, Ledger, MapJob, submit_once

ROOT = Path(__file__).resolve().parents[1]
CRN = (
    "c"
    + "rn:v1:bluemix:public:quantum-computing:us-east:a/"
    + "5ynth3t1c" * 4
    + ":"
    + "-".join(["0" * 8, "0" * 4, "4000", "8000", "0" * 12])
    + "::"
)
FREE_NAME = "synthetic-" + "instance-7f3a"
TOKEN = "s7Nt" * 11
ACCOUNT = "a1b2" * 8
HGP = "/".join(["synthetic-hub", "synthetic-group", "synthetic-project"])
EMAIL = "someone" + "@" + "example.invalid"
MARKERS = (CRN, FREE_NAME, TOKEN, ACCOUNT, HGP, EMAIL)
MESSAGE = (
    f"backend discovery failed for instance {FREE_NAME}; Invalid instance {CRN}; token {TOKEN}; "
    f"account {ACCOUNT}; {HGP}; contact {EMAIL}"
)
PAIRS = [(114, 115), (70, 71)]


def leaks(text: str) -> list[str]:
    return [m for m in MARKERS if m in text]


def shown(e: BaseException) -> str:
    """Everything a printed traceback of the exception shows, its chain included."""
    return "".join(traceback.format_exception(e))


# --------------------------------------------------------------------------- the cleaning itself
def test_every_marker_is_replaced_and_the_rest_kept():
    s = redact.scrub(MESSAGE)
    assert leaks(s) == [] and s.count(redact.MARKER) == 6
    assert s.startswith("backend discovery failed for instance [redacted]; Invalid instance [redacted];")


@pytest.mark.parametrize(
    "own",
    [
        "refused: used 310 s + open reservations 0.0 s + estimate 5.3 s > cap 540 s",
        "refused: this job (hash 0123456789ab) was already sent at 2026-10-10T12:00:00Z; pass allow_resubmit (CLI: "
        "--allow-resubmit) to send it again",
        "job db51hoamb58s7389sja0 is QUEUED; nothing fetched",
        "circuit 3 is not on the backend's 156 qubits",
        "the runtime client gave no usage (RuntimeError); read it on the platform dashboard and decide before "
        "submitting",
        "an offline snapshot has no usage; nothing can be submitted through it",
        "balance floor: balance 122 - open reservations 24 - 24 for this job = 74 < floor 90; open reservations on "
        "openquantum:account-0123456789ab: none",
    ],
)
def test_the_repositorys_own_messages_pass_unchanged(own):
    """The cleaning runs on the guard's own refusals too; they carry no identifier and are kept as written."""
    assert redact.scrub(own) == own


def test_an_exception_is_copied_clean_with_nothing_chained():
    try:
        try:
            raise ValueError(f"inner {TOKEN}")
        except ValueError as inner:
            raise RuntimeError(MESSAGE) from inner
    except RuntimeError as e:
        e.job_ids_created = ["t1"]
        new = redact.scrubbed(e)
    assert type(new) is RuntimeError and leaks(shown(new)) == []
    assert new.__cause__ is None and new.__context__ is None and new.job_ids_created == ["t1"]
    odd = redact.scrubbed(UnicodeDecodeError("utf-8", b"\xff", 0, 1, f"bad byte for {EMAIL}"))
    assert isinstance(odd, redact.ProviderError) and str(odd).startswith("UnicodeDecodeError: ") and not leaks(str(odd))


def test_a_provider_call_raises_only_the_clean_copy():
    @redact.provider_call
    def call():
        try:
            raise KeyError(CRN)
        except KeyError as inner:
            raise RuntimeError(MESSAGE) from inner

    with pytest.raises(RuntimeError) as e:
        call()
    assert leaks(shown(e.value)) == [] and e.value.__cause__ is None and e.value.__context__ is None


# --------------------------------------------------------------------------- the guard, for every backend
class Spender(GuardedSubmit):
    """A backend that spends, with a provider that fails before the send or during it."""

    name, processor, spends = "fake", "fake-processor", True

    def __init__(self, ledger, fail_in):
        self.ledger, self.fail_in = ledger, fail_in

    def _preflight(self, job, ledger):
        if self.fail_in == "preflight":
            raise RuntimeError(MESSAGE)
        return {}

    def _send(self, job):
        e = RuntimeError(MESSAGE)
        e.job_ids_created = ["task-1"]
        raise e


@pytest.mark.parametrize("fail_in", ["preflight", "send"])
def test_the_guard_stores_and_raises_only_clean_text(tmp_path, capfd, fail_in):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(RuntimeError) as e:
        submit_once(Spender(ledger, fail_in), MapJob(PAIRS), ledger)
    out, err = capfd.readouterr()
    assert leaks(shown(e.value)) == [] and leaks(ledger.path.read_text()) == [] and leaks(out + err) == []
    last = ledger.entries()[-1]
    if fail_in == "preflight":
        assert last["event"] == "refused" and last["reason"].startswith("backend discovery failed for instance")
    else:
        assert last["event"] == "failed" and last["job_ids_created"] == ["task-1"]
        assert e.value.job_ids_created == ["task-1"]


# --------------------------------------------------------------------------- IBM
needs_ibm = pytest.mark.skipif(importlib.util.find_spec("qiskit_ibm_runtime") is None, reason="needs the ibm extra")


class ErrorService:
    """A runtime client whose backend lookup fails with an account's text in its message (the review's case)."""

    def usage(self):
        return {"usage_consumed_seconds": 0}

    def backend(self, name):
        raise RuntimeError(MESSAGE)


@needs_ibm
def test_an_ibm_submission_that_fails_leaks_nothing(tmp_path, capfd):
    from manacitra import wait
    from manacitra.backends.ibm import CircuitJob, IBMCircuitsBackend

    ledger = Ledger(tmp_path / "ledger.jsonl")
    be = IBMCircuitsBackend("ibm_fez", service=ErrorService(), ledger=ledger)
    with pytest.raises(RuntimeError) as e:
        be.submit(CircuitJob([wait.wait_test_logical()], [{}], [1]), log=lambda _: None)
    out, err = capfd.readouterr()
    assert leaks(shown(e.value)) == [] and leaks(ledger.path.read_text()) == [] and leaks(out + err) == []
    with pytest.raises(RuntimeError) as e:
        be.target()
    assert leaks(shown(e.value)) == []


class FailingClient:
    """Stands in for QiskitRuntimeService: creating it fails, as a wrong saved account does, naming the account."""

    def __init__(self, *a, **k):
        raise ValueError(MESSAGE)


class NamedClient:
    """Stands in for QiskitRuntimeService: created, with an instance whose free-form name has no shape to catch."""

    free = "my-own-" + "free-name"

    def __init__(self, *a, **k):
        pass

    def active_account(self):
        return {"instance": self.free, "token": "t0k3n" * 9}

    def backend(self, name):
        raise RuntimeError(f"no backend {name} for {self.free}")


@needs_ibm
def test_the_ibm_client_failing_to_start_leaks_nothing(monkeypatch, capfd):
    """The runtime client created from the saved account, failing with the account in its message: the backend and the
    command line (a dry run of `manacitra map --backend ibm`) show only the cleaned text."""
    import qiskit_ibm_runtime

    from manacitra import cli
    from manacitra.backends.ibm import IBMBackend

    monkeypatch.setattr(qiskit_ibm_runtime, "QiskitRuntimeService", FailingClient)
    with pytest.raises(ValueError) as e:
        IBMBackend("ibm_fez").backend()
    assert leaks(shown(e.value)) == []
    with pytest.raises(ValueError) as e:
        cli.main(["map", "--backend", "ibm", "--processor", "ibm_fez"])
    out, err = capfd.readouterr()
    assert leaks(shown(e.value)) == [] and leaks(out + err) == []


@needs_ibm
def test_the_active_accounts_own_values_are_cleaned(monkeypatch):
    """A free-form instance name has no shape; read from the client object when it is created, it is cleaned exactly."""
    import qiskit_ibm_runtime

    from manacitra.backends.ibm import IBMBackend

    monkeypatch.setattr(qiskit_ibm_runtime, "QiskitRuntimeService", NamedClient)
    with pytest.raises(RuntimeError) as e:
        IBMBackend("ibm_fez").backend()
    assert NamedClient.free not in shown(e.value) and str(e.value) == "no backend ibm_fez for [redacted]"


def _handler(*names):
    stream = io.StringIO()
    h = logging.StreamHandler(stream)
    h.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
    for n in names:
        logging.getLogger(n).addHandler(h)
    return stream, h


@needs_ibm
def test_the_ibm_clients_own_warning_is_cleaned(capfd):
    """The review: the installed client's backend discovery, failing, logs "Invalid instance" and the instance. Run on
    a fabricated client object (no account), after an IBM backend is made: no handler receives the instance, neither
    one attached here nor the client's own on stderr."""
    from qiskit_ibm_runtime import QiskitRuntimeService

    from manacitra.backends.ibm import IBMBackend

    if not hasattr(QiskitRuntimeService, "_discover_backends_from_instance"):
        pytest.skip("this client version has no backend discovery to exercise")
    IBMBackend("ibm_fez", service=ErrorService())
    names = ("qiskit_ibm_runtime.qiskit_runtime_service", "qiskit_ibm_runtime")
    stream, h = _handler(*names)
    service = object.__new__(QiskitRuntimeService)

    def fails():
        raise RuntimeError("fake 403")

    service._active_api_client = SimpleNamespace(_instance=CRN, list_backends=fails)
    try:
        assert service._discover_backends_from_instance(CRN) == []
    finally:
        for n in names:
            logging.getLogger(n).removeHandler(h)
    out, err = capfd.readouterr()
    assert "Invalid instance [redacted]" in stream.getvalue()
    assert leaks(stream.getvalue()) == [] and leaks(out + err) == []


@needs_ibm
def test_every_client_record_is_cleaned_with_its_traceback(capfd):
    """Any record from the clients' loggers, its arguments and its traceback included, reaches every handler cleaned;
    a record from any other logger is left as it is."""
    from manacitra.backends.ibm import IBMBackend

    IBMBackend("ibm_fez", service=ErrorService())
    names = ("qiskit_ibm_runtime.api.session", "ibm_cloud_sdk_core", "urllib3.connectionpool", "elsewhere")
    stream, h = _handler(*names)
    try:
        try:
            raise RuntimeError(MESSAGE)
        except RuntimeError:
            logging.getLogger(names[0]).exception("request for %s failed", CRN)
        logging.getLogger(names[1]).warning("token %s refused for %s", TOKEN, EMAIL)
        logging.getLogger(names[2]).warning("GET /api/v1/instances/%s", ACCOUNT)
        logging.getLogger(names[3]).warning("not a client: %s", ACCOUNT)
    finally:
        for n in names:
            logging.getLogger(n).removeHandler(h)
    text = stream.getvalue()
    client, other = text.split("elsewhere WARNING", 1)
    assert "Traceback" in client and "RuntimeError: backend discovery failed for instance [redacted]" in client
    assert leaks(client) == [] and ACCOUNT in other
    out, err = capfd.readouterr()
    assert leaks(out + err) == []


@needs_ibm
def test_a_failing_handler_reports_clean_text(capfd):
    """A handler that fails to emit a client's record, while an exception carrying the account's text is in flight:
    logging's error report on stderr, which prints that exception, is cleaned."""
    from manacitra.backends.ibm import IBMBackend

    IBMBackend("ibm_fez", service=ErrorService())

    class Broken(logging.Handler):
        def emit(self, record):  # as StreamHandler does: a failed write goes to handleError
            try:
                raise OSError("the stream is closed")
            except Exception:
                self.handleError(record)

    lg, h = logging.getLogger("qiskit_ibm_runtime.api.session"), Broken()
    lg.addHandler(h)
    try:
        try:
            raise RuntimeError(MESSAGE)
        except RuntimeError:
            lg.warning("retrying %s", CRN)
    finally:
        lg.removeHandler(h)
    out, err = capfd.readouterr()
    assert "--- Logging error ---" in err and "OSError: the stream is closed" in err
    assert "RuntimeError: backend discovery failed for instance [redacted]" in err and leaks(out + err) == []


@needs_ibm
def test_the_wait_examples_dry_run_leaks_nothing(monkeypatch, capfd):
    """examples/04_wait_test.py, its backend's lookup failing with the account's text: nothing of it is shown."""
    from manacitra.backends import ibm

    spec = importlib.util.spec_from_file_location("wait_example", ROOT / "examples" / "04_wait_test.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(
        mod, "IBMCircuitsBackend", lambda p, service=None: ibm.IBMCircuitsBackend(p, service=ErrorService())
    )
    with pytest.raises(RuntimeError) as e:
        mod.main(["--chain", "144-143-142"])
    out, err = capfd.readouterr()
    assert leaks(shown(e.value)) == [] and leaks(out + err) == []


def _example():
    spec = importlib.util.spec_from_file_location("wait_example", ROOT / "examples" / "04_wait_test.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class EstimateJob:
    """A sent job whose usage estimate is the given value, or raises it."""

    def __init__(self, jid, estimate):
        self._id, self.estimate = jid, estimate

    def job_id(self):
        return self._id

    @property
    def usage_estimation(self):
        if isinstance(self.estimate, Exception):
            raise self.estimate
        return self.estimate


def _estimate():
    """The documented number, beside a made-up CRN, a made-up instance name and a field the client does not document."""
    return {"quantum_seconds": 12.5, "crn": CRN, "instance": FREE_NAME, "unexpected": {"note": TOKEN, "n": 7}}


@needs_ibm
@pytest.mark.parametrize(
    "estimate, line",
    [
        (_estimate(), "IBM's estimate: 12.5 s of quantum time"),
        ({"crn": CRN, "instance": FREE_NAME}, None),  # no documented number
        ({"quantum_seconds": float("nan"), "instance": FREE_NAME}, None),  # not finite
        ({"quantum_seconds": True}, None),  # not a number
        (f"quantum_seconds 12 for {CRN}", None),  # not the documented shape
        (RuntimeError(MESSAGE), None),  # reading it fails
    ],
)
def test_ibms_estimate_prints_only_its_documented_number(estimate, line):
    """Review 2, finding 6: only the estimate's documented number is printed, never the object, its repr or an
    exception's text; otherwise one fixed line."""
    mod = _example()
    got = mod.estimate_line(EstimateJob("j", estimate))
    assert got == (line or mod.ESTIMATE_UNREADABLE) and leaks(got) == []
    assert mod.estimate_line(None) == mod.ESTIMATE_UNREADABLE


class EstimateSampler:
    def __init__(self, service, estimate):
        self.service, self.estimate = service, estimate

    def __call__(self, mode):
        outer = self

        class _S:
            options = SimpleNamespace(
                dynamical_decoupling=SimpleNamespace(enable=True),
                twirling=SimpleNamespace(enable_gates=True, enable_measure=True),
            )

            def run(self, pubs):
                jid = "fakejob" + "0" * 13
                outer.service.jobs[jid] = EstimateJob(jid, outer.estimate)
                return outer.service.jobs[jid]

        return _S()


@needs_ibm
@pytest.mark.parametrize("case", ["estimate", "no estimate", "job lookup fails"])
def test_a_submission_prints_only_the_estimates_number(monkeypatch, capfd, tmp_path, case):
    """examples/04_wait_test.py sent through fakes: after the send, stdout carries the estimate's number, or the fixed
    line when it cannot be read, and nothing of the estimate's other fields or of an exception."""
    from _fakes import FakeIBMService

    from manacitra.backends import ibm

    class Service(FakeIBMService):
        def job(self, job_id):
            if case == "job lookup fails":
                raise RuntimeError(MESSAGE)
            return super().job(job_id)

    svc = Service()
    estimate = _estimate() if case == "estimate" else RuntimeError(MESSAGE)
    mod = _example()
    monkeypatch.setattr(
        mod,
        "IBMCircuitsBackend",
        lambda p, service=None: ibm.IBMCircuitsBackend(
            p, service=svc, sampler_factory=EstimateSampler(svc, estimate), ledger=Ledger(tmp_path / "ledger.jsonl")
        ),
    )
    args = [
        "--chain",
        "144-143-142",
        "--copies",
        "1",
        "--shots-wait",
        "1",
        "--shots-b",
        "1",
        "--submit",
        "--cap-s",
        "600",
    ]
    assert mod.main(args + ["--handle-out", str(tmp_path / "handle.json")]) == 0
    out, err = capfd.readouterr()
    last = out.strip().splitlines()[-1]
    assert last == ("IBM's estimate: 12.5 s of quantum time" if case == "estimate" else mod.ESTIMATE_UNREADABLE)
    assert leaks(out + err) == [] and "unexpected" not in out and "note" not in out


# --------------------------------------------------------------------------- the scope of the log cleanup (ruling R2)
def _one_record(name: str, *args) -> str:
    stream, h = _handler(name)
    try:
        logging.getLogger(name).warning("request for %s failed", *args)
    finally:
        logging.getLogger(name).removeHandler(h)
    return stream.getvalue()


def test_an_unrelated_loggers_record_passes_untouched():
    """A program's own logger, with a made-up CRN in its record: once the cleanup is installed, the record reaches
    its handler exactly as it was made."""
    redact.guard_client_logging()
    assert _one_record("myapp.service", CRN) == f"myapp.service WARNING request for {CRN} failed\n"


@pytest.mark.parametrize("client", redact.CLIENT_LOGGERS)
def test_a_named_clients_child_logger_is_cleaned(client):
    """The same made-up CRN on a child logger of each named client is cleaned: the choice is by the record's name,
    so a child is covered without a filter on it."""
    redact.guard_client_logging()
    name = f"{client}.something"
    assert _one_record(name, CRN) == f"{name} WARNING request for [redacted] failed\n"


def test_installing_twice_does_not_wrap_twice():
    redact.guard_client_logging()
    factory, report = logging.getLogRecordFactory(), logging.Handler.handleError
    redact.guard_client_logging()
    redact.guard_client_logging()
    assert logging.getLogRecordFactory() is factory and logging.Handler.handleError is report
    assert factory._manacitra_redact and not getattr(factory._previous, "_manacitra_redact", False)
    assert report._manacitra_redact and not getattr(report._previous, "_manacitra_redact", False)


# --------------------------------------------------------------------------- Open Quantum
def test_an_open_quantum_fetch_that_fails_leaks_nothing(tmp_path):
    """Open Quantum's calls into its client go through the same boundary: a failing scheduler's text is cleaned."""
    from manacitra.backends.openquantum import OpenQuantumBackend

    class Scheduler:
        def get_job(self, jid):
            raise RuntimeError(MESSAGE)

    be = OpenQuantumBackend(service=SimpleNamespace(scheduler=Scheduler()), ledger=Ledger(tmp_path / "ledger.jsonl"))
    handle = JobHandle(
        "openquantum", be.processor, ["task-1"], "0" * 64, positions=[1], pairs=PAIRS, order=["x"], shots=1
    )
    with pytest.raises(RuntimeError) as e:
        be.fetch(handle)
    assert leaks(shown(e.value)) == []
