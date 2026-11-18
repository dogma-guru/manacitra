# What the installed SDK does with a program set

Read before the go, 21 October 2026, on the installed `amazon-braket-sdk` 1.127.3.post0 (Python 3.14, the existing
virtual environment). Paths are relative to `site-packages/braket/`. This is a reading of the code, not of the service.

## Building a ProgramSet from OpenQASM text

* `program_sets/program_set.py:32` `ProgramSet.__init__(programs, shots_per_executable=None)`. The entries may be
  `CircuitBinding`, `Circuit`, `Program` or `str`. A plain string is kept as given (line 60 to 64).
* `program_sets/program_set.py:90` and `:91`: at serialisation, a string entry becomes `Program(source=<string>)`
  with no inputs; the set is wrapped as `braket.ir.openqasm.ProgramSet(programs=[...])` (line 96), schema name
  `braket.ir.openqasm.program_set`.
* `program_sets/program_set.py:513` `_program_executable_count`: a program with no inputs is one executable. Two
  strings give `total_executables == 2` (line 106).
* `program_sets/program_set.py:142` `enumerate_executables`: executables are yielded in entry order. For this probe,
  (0, 0, 0) for E1, then (1, 0, 0) for E2.

## How the shots are divided

* At submission the SDK does not divide anything. `aws/aws_device.py:222` passes `shots` through when it is given;
  only when it is omitted does `_default_shots` (`aws/aws_device.py:548` to `:550`) return the sentinel -1 for a
  program set, and then `aws/aws_quantum_task.py:712` to `:715` replace it with `shots_per_executable *
  total_executables`. With `shots=200` passed, `CreateQuantumTask` receives `shots: 200`, the total for the task.
  `shots_per_executable` is not serialised (`to_ir`, lines 86 to 96); the SDK sends no per-executable figure.
* The `ProgramSet` docstring (`program_sets/program_set.py:52` to `:54`) says that without `shots_per_executable` the
  only check at creation is divisibility by the number of executables. No such check is made in the SDK code read
  here, so that check, if it exists, is the service's.
* At fetch, `tasks/program_set_quantum_task_result.py:455`: `shots_per_executable = metadata.requestedShots //
  num_executables`. The SDK takes the even split as given; it does not read a per-executable shot count from the
  result. Note: the schema's docstring (`task_result/program_set_task_metadata_v1.py:57`) describes `requestedShots`
  as "the total number of shots for each executable", which reads the other way; the returned value settles which.
* The runner builds `ProgramSet([E1 text, E2 text], shots_per_executable=100)` and passes `shots=200`, so the SDK's
  own `total_shots` (200) and the value sent agree.

## What the SDK does to the result

* `aws/aws_quantum_task.py:564` to `:568`: the SDK reads `results.json` from the task's output folder and parses it.
  For a program set (`task_result/program_set_task_result_v1.py:43` to `:45`), `programResults` and `taskMetadata`
  may be inline or relative paths under `s3Location`; each program result's `executableResults` likewise
  (`task_result/program_result_v1.py`).
* `task_result/program_set_executable_result_v1.py:48` to `:53`: an executable result carries `inputsIndex`,
  `measurements` (optional), `measurementProbabilities` (optional) and `measuredQubits`. No time field is defined at
  the executable level; `ProgramSetExecutableResultMetadata` (line 21) has no fields.
* `tasks/program_set_quantum_task_result.py:98` to `:107`: **when the device sends probabilities and no
  `measurements`, the SDK builds a `measurements` array from them** (`tasks/measurement_utils.py:59` to `:79`,
  repeating each bitstring `round(p * shots)` times, grouped by bitstring) and sets `measurements_from_device` to
  False. A parsed `measurements` attribute is therefore not evidence of per-shot data; only the raw executable file
  is. The runner saves every raw file under the output folder before the SDK parses anything, and records
  `measurements_from_device` beside the type and shape of each parsed array.
* `tasks/program_set_quantum_task_result.py:449`: the SDK's own download uses `boto3.client("s3")`, a default client
  rather than the session's. The runner downloads the raw files through the session itself, so the record does not
  depend on that.
* `aws/aws_quantum_task.py:410` to `:415`: a FAILED program-set task is treated as having a result to fetch
  (per-executable failures are carried in the result).
