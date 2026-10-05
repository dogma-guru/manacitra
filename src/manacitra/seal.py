# Copyright 2026 Anish Patel
# SPDX-License-Identifier: Apache-2.0
"""Sealed commitments: show later that a file (a set of predictions, a rule) existed, unchanged, before the results.

A plain SHA-256 beside a file only catches accidents: whoever can change the file can recompute the hash. A commitment
works differently. Sealing draws a secret random salt and publishes only

    hash = SHA-256(salt || the file's bytes)

somewhere the producer cannot edit (a chat with the reader, a public log). The file and the salt stay private. Later,
revealing the salt lets anyone recompute the hash and check that the file is the one committed to. The salt stops
anyone guessing a short file from its hash. Who sealed it, and when, is shown by where the hash was posted and, in
this repository, by the Sigstore signature on the commit record (see .github/workflows/sign.yml).

    manacitra seal FILE     salt into .seals/FILE.salt (git-ignored); FILE.commit.json; prints the hash to post
    manacitra reveal FILE   adds the salt to FILE.commit.json, after checking it, for publication
    manacitra verify FILE   checks FILE and the revealed salt against FILE.commit.json, and says whether they match
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

ALGORITHM = "sha256(salt || file)"
SALT_BYTES = 32
SEALS_DIR = ".seals"


class SealError(RuntimeError):
    pass


@dataclass
class Verification:
    match: bool
    message: str
    expected: str | None = None
    computed: str | None = None


def commitment(salt: bytes, data: bytes) -> str:
    return hashlib.sha256(salt + data).hexdigest()


def commit_path(path: Path) -> Path:
    return path.with_name(path.name + ".commit.json")


def salt_path(path: Path, root: Path | None = None) -> Path:
    """.seals/<the file's path relative to root>.salt; a file outside root keeps only its name."""
    root = Path(root or Path.cwd()).resolve()
    p = path.resolve()
    try:
        rel = p.relative_to(root)
    except ValueError:
        rel = Path(p.name)
    return root / SEALS_DIR / rel.with_name(rel.name + ".salt")


def _version() -> str:
    from . import __version__

    return f"manacitra {__version__}"


def seal(path, root=None, force: bool = False) -> dict:
    """Seal a file: draw a salt, keep it private, write the commit record, and return it (with the hash to post)."""
    path = Path(path)
    if not path.is_file():
        raise SealError(f"no such file: {path}")
    cp, sp = commit_path(path), salt_path(path, root)
    if (cp.exists() or sp.exists()) and not force:
        raise SealError(f"{path} is already sealed ({cp.name}); a commitment is made once")
    salt = secrets.token_bytes(SALT_BYTES)
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(salt.hex() + "\n")
    try:
        os.chmod(sp, 0o600)
    except OSError:
        pass
    record = {
        "file": path.name,
        "algorithm": ALGORITHM,
        "hash": commitment(salt, path.read_bytes()),
        "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": _version(),
        "salt": None,
    }
    cp.write_text(json.dumps(record, indent=1) + "\n")
    return record


def _read_record(path: Path) -> dict:
    cp = commit_path(path)
    if not cp.exists():
        raise SealError(f"no commit record for {path} (expected {cp.name})")
    record = json.loads(cp.read_text())
    if record.get("algorithm") != ALGORITHM:
        raise SealError(f"{cp.name}: unknown algorithm {record.get('algorithm')!r}")
    return record


def _salt_bytes(hex_text: str, where: str) -> bytes:
    try:
        salt = bytes.fromhex(hex_text.strip())
    except ValueError:
        raise SealError(f"{where}: the salt is not hexadecimal") from None
    if len(salt) != SALT_BYTES:
        raise SealError(f"{where}: the salt has {len(salt)} bytes, not {SALT_BYTES}")
    return salt


def reveal(path, root=None) -> dict:
    """Add the private salt to the commit record, after checking that it opens the commitment."""
    path = Path(path)
    record = _read_record(path)
    sp = salt_path(path, root)
    if not sp.exists():
        raise SealError(f"no salt for {path} (expected {sp}); only the machine that sealed it holds the salt")
    salt = _salt_bytes(sp.read_text(), str(sp))
    if not hmac.compare_digest(commitment(salt, path.read_bytes()), record["hash"]):
        raise SealError(f"{path} does not match its commitment with this salt; nothing revealed")
    record["salt"] = salt.hex()
    record["revealed_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    commit_path(path).write_text(json.dumps(record, indent=1) + "\n")
    return record


def verify(path, salt_hex: str | None = None) -> Verification:
    """Check a file against its commit record, with the revealed salt (or one given explicitly)."""
    path = Path(path)
    if not path.is_file():
        return Verification(False, f"no such file: {path}")
    try:
        record = _read_record(path)
    except SealError as e:
        return Verification(False, str(e))
    hex_text = salt_hex if salt_hex is not None else record.get("salt")
    if not hex_text:
        return Verification(
            False,
            f"the commit record for {path.name} has no salt: it has not been revealed, so the "
            "file cannot be checked yet (the sealer runs `manacitra reveal`)",
            record["hash"],
        )
    try:
        salt = _salt_bytes(hex_text, commit_path(path).name)
    except SealError as e:
        return Verification(False, str(e), record["hash"])
    got = commitment(salt, path.read_bytes())
    if hmac.compare_digest(got, record["hash"]):
        return Verification(
            True, f"MATCH: {path.name} is the file committed to at {record['sealed_utc']}", record["hash"], got
        )
    return Verification(
        False,
        f"NO MATCH: {path.name} and this salt do not give the committed hash; the file or the "
        "salt is not the one sealed",
        record["hash"],
        got,
    )
