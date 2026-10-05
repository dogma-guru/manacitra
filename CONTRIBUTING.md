# Contributing

Thank you for looking. Manacitra is small on purpose: it maps qubit pairs, gives three verdicts, and chooses pairs.

## Set up

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev,aer]"
git config core.hooksPath .githooks
```

The last line turns on the pre-commit hook, which runs the identifier scan (`tools/scan_secrets.py`) on every staged
file.

## Before a pull request

```bash
ruff check src tests tools examples docs
ruff format --check src tests tools examples docs
pytest -q
python tools/scan_secrets.py
```

`tests/test_reproduction.py` recomputes every archived statistic in `data/` from the archived counts and fails if any
differs by more than 10⁻⁶. A change that moves a published number is not a fix; it is a different method, and it
needs its own discussion first.

## Rules the code keeps

- **No secrets in the repository, ever.** Credentials come from each provider's own saved-account mechanism or from
  environment variables. Never print, log, store or commit a token, an account or instance identifier, a client ID or
  secret, or an email address. The scan fails on all of these.
- **Nothing is sent to a provider by default.** The command line is a dry run unless `--submit` is given, and the
  submit-once guard in `backends/base.py` refuses a second send of the same job unless `--allow-resubmit` is given.
- **Exactly three two-qubit gates per pair.** A transpiled circuit that carries anything else on a pair is refused.
- **Words.** The tool maps pairs; it does not rank machines. No vendor is compared with
  another as a product. Every number carries its processor and its date.

## Licences, and signing off your commits

**Inbound as outbound.** Contributions are accepted under the Apache License 2.0, the licence the code is published
under (`LICENSE`). Data and documentation are contributed under CC BY 4.0, as published (`data/LICENSE`,
`docs/LICENSE`). There is no contributor licence agreement.

**The Developer Certificate of Origin.** Each commit carries a sign-off line, by which you certify the
[Developer Certificate of Origin 1.1](https://developercertificate.org/): that you wrote the change, or otherwise have
the right to submit it under the project's licence.

```bash
git commit -s -m "fix: what changed"     # adds: Signed-off-by: Your Name <your address>
git rebase --signoff main                 # signs off commits you already made on a branch
```

A CI check (`.github/workflows/dco.yml`, `tools/check_dco.py`) fails a pull request that has a commit without a
`Signed-off-by:` line. The signing workflow's bot commits, which only add Sigstore bundles, are exempt.

The copyright holder is Dogma LLC (Dogma Guru). Each source file starts with:

```python
# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
```
