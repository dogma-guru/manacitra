# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Provider text, cleaned before it is stored or shown (Amendment A18, ruling R1).

A provider's error message or log line can carry the account it came from: an instance name, a CRN, an account or
hub/group/project identifier, a token, an email address. `scrub` replaces each with MARKER. It runs on every piece of
provider text before the ledger stores it, and at the boundary between Manacitra and a provider's client:

- `scrubbed` makes a copy of an exception with its text cleaned, and `provider_call` re-raises a provider call's
  exception as that copy, without the original chained to it, so a printed traceback carries only the cleaned text;
- `guard_client_logging` cleans every log record of the providers' clients, their libraries, and requests and
  urllib3 (CLIENT_LOGGERS), at the moment it is made, so no handler, wherever it is attached, receives the original
  text; every other record passes untouched.

Exact values known at run time (the active account's instance and token, read from the client object, never from a
file) are added with `register` and replaced first. Nothing here keeps the original text.
"""

from __future__ import annotations

import functools
import logging
import re
import sys
import traceback

MARKER = "[redacted]"

#: Shapes of identifiers, each replaced whole
_SHAPES = [
    re.compile(r"crn:v\d+:[^\s'\"<>,;)\]}]*", re.IGNORECASE),  # IBM Cloud resource names
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*"),  # JSON web tokens
    re.compile(r"\b(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),  # authorisation headers
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"),  # email addresses
    re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),  # instance GUIDs
    re.compile(r"(?<![\w./-])[\w-]+/[\w-]+/[\w-]+(?![\w/-])"),  # hub/group/project
    # keys, tokens and account IDs: 32 or more characters, with letters and digits both
    re.compile(
        r"(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_-]*[0-9])(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]{32,}(?![A-Za-z0-9_-])"
    ),
    re.compile(r"(?:/Users|/home)/[^\s/'\"]+"),  # home folders, which carry a user name
]
#: A value after a word that names it: "instance X", "instance=X", '"instance": "X"', "account id X", "hub X", ...
_FIELD = re.compile(
    r"\b(instances?|crn|account|hub|group|project|token|api[ _-]?key|apikey|api[ _-]?token|access[ _-]?token|"
    r"refresh[ _-]?token|client[ _-]?id|client[ _-]?secret|organi[sz]ation|org[ _-]?id|password|secret|email|user)"
    r"((?:[ _-]?(?:name|named|id|crn))?)"
    r"((?:['\"]?\s*[:=]\s*|\s+)['\"]?)"
    r"([^\s'\",;)\]}]+)",
    re.IGNORECASE,
)
#: Words after a field name that are English, not a value
_NOT_A_VALUE = {
    "is",
    "was",
    "not",
    "has",
    "have",
    "had",
    "the",
    "a",
    "an",
    "or",
    "and",
    "of",
    "for",
    "to",
    "in",
    "on",
    "with",
    "from",
    "that",
    "this",
    "does",
    "did",
    "cannot",
    "could",
    "can",
    "must",
    "may",
    "will",
    "be",
    "been",
    "are",
    "at",
    "by",
    "as",
    "if",
    "no",
    "none",
    "given",
    "found",
    "list",
    "lists",
    "names",
    "usage",
    "limit",
    "details",
    "plan",
}
_known: set[str] = set()


def register(*values) -> None:
    """Exact values to replace wherever they appear (the active account's instance and token, for example)."""
    for v in values:
        if isinstance(v, str) and len(v.strip()) >= 4:
            _known.add(v.strip())


def _field(m: re.Match) -> str:
    value = m.group(4)
    if value.lower() in _NOT_A_VALUE or value.startswith(MARKER[:-1]):  # English, or already replaced
        return m.group(0)
    return m.group(1) + m.group(2) + m.group(3) + MARKER


def scrub(text) -> str:
    """The text with every known value, identifier shape and named value replaced by MARKER."""
    s = str(text)
    for v in sorted(_known, key=len, reverse=True):
        s = s.replace(v, MARKER)
    for rx in _SHAPES:
        s = rx.sub(MARKER, s)
    return _FIELD.sub(_field, s)


class ProviderError(RuntimeError):
    """A provider's exception whose type could not be rebuilt with cleaned text; its message names the type."""


#: Attributes the repository's own code sets on an exception and reads back (the tasks created before a failure)
_KEPT = ("job_ids_created",)


def scrubbed(e: BaseException) -> BaseException:
    """A copy of an exception with its text cleaned, of the same type where that type can be rebuilt from one
    message, otherwise a ProviderError naming the type. Nothing of the original is attached to it."""
    text = scrub(e)
    try:
        new = type(e)(text)
        if str(new) != text:
            raise TypeError("the type builds its text from other arguments")
    except Exception:
        new = ProviderError(f"{type(e).__name__}: {text}")
    for name in _KEPT:
        if hasattr(e, name):
            setattr(new, name, getattr(e, name))
    return new


def provider_call(fn):
    """A method that talks to a provider's client: any exception it raises is re-raised as `scrubbed`, raised outside
    the handler, so neither its cause nor its context is the original."""

    @functools.wraps(fn)
    def inner(*args, **kwargs):
        err = None
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            err = scrubbed(e)
        raise err

    return inner


#: The loggers whose records are cleaned, with their children (chosen by record.name, so a child logger is covered;
#: confirmed by A18, ruling R2): the IBM client and the IBM libraries it uses for its accounts and requests; the Open
#: Quantum client's packages, which log nothing themselves in the versions the adapter supports (openquantum-sdk
#: 0.4.3, openquantum-sdk-qiskit 0.3.3) and send their HTTP through requests; and requests and urllib3, which can log
#: URLs that carry identifiers. Every other record passes untouched.
CLIENT_LOGGERS = (
    "qiskit_ibm_runtime",
    "qiskit_ibm_provider",
    "ibm_cloud_sdk_core",
    "ibm_platform_services",
    "ibm_quantum_schemas",
    "openquantum_sdk",
    "openquantum_sdk_qiskit",
    "requests",
    "urllib3",
)
_guarded = False


def _is_client(name: str) -> bool:
    return any(name == p or name.startswith(p + ".") for p in CLIENT_LOGGERS)


def clean_record(record: logging.LogRecord) -> logging.LogRecord:
    """A log record's message, arguments, traceback and stack, cleaned in place."""
    try:
        message = record.getMessage()
    except Exception:
        message = str(record.msg)
    record.msg, record.args = scrub(message), None
    if record.exc_info:
        record.exc_text = scrub("".join(traceback.format_exception(*record.exc_info)).rstrip("\n"))
        record.exc_info = None
    elif record.exc_text:
        record.exc_text = scrub(record.exc_text)
    if record.stack_info:
        record.stack_info = scrub(record.stack_info)
    return record


def guard_client_logging() -> None:
    """Clean every record of the loggers in CLIENT_LOGGERS and their children, as it is made: the record factory is
    wrapped once, so every handler, on any logger, receives only cleaned text. A record of any other logger is passed
    through untouched. Installing again does nothing: the factory is never wrapped twice.

    And when a handler fails to emit such a record, logging prints an error report to stderr, with the exception in
    flight and every exception chained to it, which can be the client's own, uncleaned. For a client's record that
    report is cleaned too."""
    global _guarded
    if _guarded:
        return
    previous = logging.getLogRecordFactory()

    def factory(*args, **kwargs):
        record = previous(*args, **kwargs)
        return clean_record(record) if _is_client(record.name) else record

    factory._manacitra_redact = True
    factory._previous = previous
    logging.setLogRecordFactory(factory)
    report = logging.Handler.handleError

    def handle_error(self, record):
        if not _is_client(getattr(record, "name", "")):
            return report(self, record)
        if logging.raiseExceptions and sys.stderr:
            text = "".join(traceback.format_exception(*sys.exc_info()))
            try:
                sys.stderr.write(f"--- Logging error ---\n{scrub(text)}Message: {scrub(record.msg)!r}\n")
            except Exception:
                pass

    handle_error._manacitra_redact = True
    handle_error._previous = report
    logging.Handler.handleError = handle_error
    _guarded = True
