# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""Patterns for tools/scan_secrets.py.

This file holds patterns only, never a real value. Words that must stay out of the repository are written with a
character class (for example ``x[y]z``), so that the regular expression matches the word while the text of this file
does not. The author's home path is caught by the generic home-path patterns; the user name of whoever runs the scan
is added at run time (see scan_secrets.py), so it is never written down here.
"""

# (name, regular expression, flags) ; flags: "i" for case-insensitive
PATTERNS = [
    # IBM Quantum / IBM Cloud
    ("ibm-cloud-crn", r"crn:v1:[A-Za-z0-9:/_.-]+", ""),
    (
        "ibm-api-key-44",
        r"(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_-]*[A-Za-z])(?=[A-Za-z0-9_-]*[0-9])[A-Za-z0-9_-]{44}(?![A-Za-z0-9_-])",
        "",
    ),
    ("instance-field", r"[\"']?instance[\"']?\s*[:=]\s*[\"'][^\"'\s]{6,}[\"']", "i"),
    # Open Quantum and generic client credentials
    ("client-id-field", r"client[_-]?id[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9._-]{8,}", "i"),
    ("client-secret-field", r"client[_-]?secret[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9._~+/=-]{8,}", "i"),
    ("organization-id-field", r"organi[sz]ation[_-]?id[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9._-]{8,}", "i"),
    ("uuid", r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", ""),
    # Tokens of any provider
    ("bearer-token", r"bearer\s+[A-Za-z0-9._~+/-]{12,}=*", "i"),
    ("jwt", r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*", ""),
    (
        "token-field",
        r"[\"']?(api[_-]?key|api[_-]?token|access[_-]?token|refresh[_-]?token|token)[\"']?\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']",
        "i",
    ),
    ("private-key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", ""),
    # Amazon Web Services (Amendment A7, before any Amazon Braket file is copied): resource names, bucket addresses,
    # account numbers and access keys. Profile and region names (us-west-1) are not identifiers and are allowed.
    ("aws-arn", r"\b[a]rn:", "i"),
    ("aws-s3-uri", r"s[3]://", "i"),
    ("aws-account-number", r"(?<![0-9A-Za-z_.+-])[0-9]{12}(?![0-9A-Za-z_])", ""),
    ("aws-access-key-field", r"aws_[a]ccess_key", "i"),
    ("aws-access-key-id", r"\bA[K]IA[A-Z0-9]{16}\b", ""),
    ("aws-secret-field", r"aws_[s]ecret", "i"),
    # People and machines
    ("email-address", r"[A-Za-z0-9._%+\[\]-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", ""),
    ("home-path-mac", r"/Users/[A-Za-z0-9._-]+", ""),
    ("home-path-linux", r"/home/[A-Za-z0-9._-]+", ""),
    ("home-path-windows", r"[A-Za-z]:\\\\?Users\\\\?[A-Za-z0-9._-]+", ""),
    # The other-project words of the kickoff's vocabulary boundary (section 1)
    ("vocabulary-w1", r"\bm[a]la\b", "i"),
    ("vocabulary-w2", r"\bk[n]ots?\b", "i"),
    ("vocabulary-w3", r"\br[i]ngs?\b", "i"),
    ("vocabulary-w4", r"\bg[l]ass(es)?\b", "i"),
    ("vocabulary-w5", r"k[u]ndala", "i"),
    ("vocabulary-w6", r"g[u]rutva", "i"),
    # W7 (Amendment A1): the first word on its own, or with the second in any spacing or case; allowed only in
    # the exact strings of ALLOW below
    ("vocabulary-w7", r"\bd[o]gma(?:[\s_.-]*guru)?\b", "i"),
]

# A match that lies inside one of these is not a finding.
ALLOW = [
    # IBM job IDs may stay (kickoff, section 5)
    ("ibm-job-id", r"\b[a-z0-9]{20}\b", ""),
    # The repository's own address, which carries the hosting organisation's name (kept by the author's ruling)
    ("repository-url", r"github\.com/d[o]gmaguru/manacitra", "i"),
    # Amendment A1: the ownership and publisher lines, exactly as written (case-sensitive)
    ("owner", r"D[o]gma LLC", ""),
    ("owner-and-trade-name", r"D[o]gma LLC \(doing business as D[o]gma Guru\)", ""),
    ("owner-short", r"D[o]gma LLC \(D[o]gma Guru\)", ""),
    ("publisher", r"published by D[o]gma Guru", ""),
    # Amendment A3: GitHub's public automation identity for workflow commits (the Sigstore bundle commits, and the
    # DCO check's exemption for them). It is a published noreply address, not a person's and not a secret. Exactly
    # this string; any other address, including another bot's, is still a finding.
    ("github-actions-bot", r"41898282\+github-actions\[bot\]@users\.noreply\.github\.com", ""),
    # Amendment A7: a counts key of exactly twelve 0s and 1s (a six-pair measurement) is not an AWS account number.
    # Only a quoted string of 0s and 1s; a twelve-digit number with any other digit is still a finding.
    ("bitstring-key", r"\"[01]{12}\"", ""),
    # Synthetic placeholder identifiers used in recorded test responses
    ("synthetic-uuid", r"\b00000000-0000-0000-0000-[0-9]{12}\b", ""),
]

# Never scanned: generated caches and binary formats
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", "build", "dist", ".mypy_cache"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".zip", ".gz", ".whl", ".pyc"}
# Sigstore bundles: public signatures (base64 certificates and log entries), written by the signing workflow
SKIP_NAME_ENDINGS = (".sigstore.json",)

# Amendment A4 (R2), the author's ruling of 6 October: the identities allowed in the repository's reachable git
# metadata, each in its roles only (scan_secrets.py --git). Written as regular expressions, escaped, so that this file
# carries no address the tree scan would match. Any other address, in any role, is a finding.
GIT_IDENTITIES = [
    # the author's public authorship identity: author, committer and sign-off
    (r"anish@d[o]gma\.guru", {"author", "committer", "Signed-off-by"}),
    # the coding assistant's co-author line
    (r"noreply@anthropic\.com", {"Co-Authored-By"}),
    # GitHub, as committer of commits made through its web interface
    (r"noreply@github\.com", {"committer"}),
]
