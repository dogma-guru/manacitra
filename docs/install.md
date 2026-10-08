# Installing Manacitra: the details

The short version is in the [README](../README.md#install-and-try-it).

## As a plain package

With `pip install ".[aer]"` from a clone or `pip install "git+https://github.com/dogma-guru/manacitra"`. This installs the package only: the dataset is not in the wheel. The simulator and the backends work without it. Anything that reads the archive needs a clone's `data/` folder: the reproductions, examples 2 and 3, and `manacitra verdict` on an archived run. Point at it in one of two ways:

```bash
export MANACITRA_DATA=/path/to/manacitra/data
```

```bash
manacitra --data /path/to/manacitra/data verdict ibm_fez/k31-map.json
```

Without either, Manacitra stops and says how to get the data. In a plain install, the tests that need it are skipped, with that reason.

## Extras and provider backends

Extras: `[ibm]` for IBM Quantum, `[aer]` for Qiskit Aer, `[docs]` for the diagrams; `[openquantum]` and `[cirq]` are experimental. `[openquantum]` is limited to the SDK versions every adapter call was checked against (openquantum-sdk 0.4.3 and later 0.4 releases), and the adapter stops at import if the installed SDK lacks the two private methods it calls. On Open Quantum, a pair named in a program is not the physical pair: Kickoff 40 showed that the same named pairs, sent through a route that records placement, ran on other qubits than Open Quantum's programs had used. Use a map there only with the exact program that measured it, and read its pair names as labels. Placement cannot be pinned, because the platform's preprocessing breaks the provider's verbatim mode. The command line is `manacitra map | pick | verdict | persist | report`; a provider backend is a dry run unless `--submit` is given; the simulator runs at once, on your machine, and sends nothing.

## Before anything is sent to a provider

The estimate and the ledger entry are printed; a job already sent once is refused unless `--allow-resubmit` (in Python, `allow_resubmit=True`) is given, and that is logged, whether it is sent from the command line or through a backend's `submit()`; the check and the reservation are made under one lock that every process shares, so two commands started together cannot both send one job; on Open Quantum, the balance, the quote and the budget across waves are checked again immediately before sending, and the balance floor counts every credit reserved on the account and not yet settled; on IBM the usage is read, and the job is refused if the usage plus the estimates of jobs not yet counted plus this one would pass a cap (540 s of the 600 s window by default); and any transpiled circuit without exactly three CZ on every pair is refused. Credentials come only from each provider's own saved account, never from this repository.
