# Three probes of the Amazon Braket route to Cepheus-1-108Q

Three probes of Rigetti's Cepheus-1-108Q through Amazon Braket, run on 21 October 2026, each under a rule whose SHA-256 was posted in a public issue before its go. A probe is not a test, and nothing in it is a finding. Each folder holds one probe's hand-back as its runner delivered it, with the changes listed below.

## The questions and the words

- Probe 01 (`probe-01-wait/`, issue 74) asked whether a program containing a wait is accepted by this device and, if it runs, whether the wait acts as time; its report gives the words ACTS AS TIME for the reading and WAIT PRESENT for the compiled program.
- Probe 02 (`probe-02-scaling/`, issue 75) asked whether twice the wait gives twice the decay, and whether a barrier between the drive frame and the readout frames changes what the measurement waits for; its report gives the words SCALES and BARRIER ADDS WAIT.
- Probe 03 (`probe-03-program-set/`, issue 76) asked what a program-set result carries on this device: its shots one by one, a time per executable, and the order in which the executables ran; its report gives the word REJECTED at both attempts, and NOT APPLICABLE for the other three words.

## The rules

Each rule file is published byte for byte, its dollar caps included (Amendment A29, ruling R1: a hashed rule is not edited). Its SHA-256 matches the probe's `rule.sha256` and the hash posted in its issue:

| probe | rule | SHA-256 | issue, created (UTC) | go (UTC) |
|---|---|---|---|---|
| 01 | `braket-probe-01-wait-rule.md` | `1d60b3b1ae8796d47197ea9bd58bb8d4f8fd3b8671aa8cf1a5d4191a49c1afb6` | 74, 21 October 2026, 13:46:28 | 13:47:37 |
| 02 | `braket-probe-02-scaling-rule.md` | `024783547852c52ab9f834c2a85f10d2eb73227aef73b8cc0ec895013acb8e41` | 75, 21 October 2026, 19:53:46 | 19:56:20 |
| 03 | `braket-probe-03-program-set-rule.md` | `b9748919eb26918976fbfd4ff0028899294cffbc97975e1cb6167e570811fb27` | 76, 21 October 2026, 20:29:34 | 20:38:18, and 21:17:08 for attempt 2 |

## The attempts

- Probe 01 was started three times, and only the third produced results. `probe-01-wait/attempt-1/` and `attempt-2/` hold the first two; `go.log` quotes the author's rulings that allowed each later start, and the report's section 2 describes all three.
- Probe 03 was submitted twice, the same bytes each time. `probe-03-program-set/attempt-1/` is attempt 1's hand-back as it was, with its own report, `SHA256SUMS` and redaction logs; `go.log` quotes the author's ruling that allowed the second attempt, "Yes, let's try one resubmission."

## What each folder holds

The rule and `rule.sha256`; the report (`report-probe-01.md` and so on); `go.log`; the programs as written and as sent, with their hashes (`programs/`); the raw records (`raw/`: the device's properties and status at each read, and each task's result, metadata, states, per-shot measurements and compiled program, or its error); the run's logs (`run-log.json`, `run.log` and, where there is one, `run-stdout.log`); the scripts as run (`scripts/`); the two redaction logs, `raw-redaction-log.md` (the search made as each raw file was saved) and `redaction-log.md` (the final search); and `SHA256SUMS`; in probe 03 also the checks before each go (`pre-go-checks.md`) and attempt 1's reading of the SDK (`attempt-1/sdk-program-set-notes.md`). In probes 01 and 02, `redaction-log.md` was written after `SHA256SUMS` and is not in it, as their runner prompts ordered.

The runner redacted the task ARNs, which carry the account number, the results bucket and the account number from every saved file, as the redaction logs record. The device's ARN carries no account number and is kept; each task's ID is kept in its results directory, as job IDs are elsewhere in `data/`. The JSON files here are records of the probes, not run records: they carry no `meta` block, and `tests/` reads them as files of this folder only. Their programs are listed in each probe's `programs/` folder, not in [`../../PROGRAMS.md`](../../PROGRAMS.md).

## What was changed when copying

Three kinds of change, in 52 files; every other file is byte for byte as handed back.

- **Dollar figures** (Amendment A29, ruling R1). In every file but the three rules, each dollar figure is written "[cost]": the tracker's figures, the price list's estimates and the spending limit's coverage in the reports, logs and run logs; the caps in the scripts (`Decimal("[cost]")`); and the published price per shot in each properties file, where the number becomes the string `"[cost]"`. Zeros written as code defaults in the scripts are kept. 173 replacements.
- **The hand-back folder's path.** Each `scripts/finalize.py` named the folder its runner wrote the hand-back to; the path is written `"[the hand-back folder]"`. 4 replacements.
- **Withheld in probe 03** (the author's answers of 18 November 2026). Probe 03's final search matched six lines of two of attempt 1's scripts, which the author ruled were kept as run and logged by file and line without the matched text. Together, the line numbers, the reason given for keeping them and the hashes of the lines' text would let a reader infer one of the account's figures. In both redaction logs (`redaction-log.md` and `attempt-1/redaction-log.md`), each of the six rows' line and reason is written "[withheld]" (12 cells in each); in both copies of `explain_kept.py` (`scripts/` and `attempt-1/scripts/`), the reason and each of the six entries' line number and hash are written "[withheld]" (13 values in each). The scripts that hold the six lines, and `attempt-1/go.log`, which records the ruling, are as handed back. 50 values.

The `SHA256SUMS` in each folder is the hand-back's, unchanged, so it reports the files below as changed. Their SHA-256 values as handed back and as published (the published ones are also in [`../../SHA256SUMS`](../../SHA256SUMS)):

| file | replacements | bytes as published | SHA-256 in the probe's `SHA256SUMS` | SHA-256 as published |
|---|---|---|---|---|
| `probe-01-wait/attempt-1/raw/properties-presubmission-20261021T134740Z.json` | 1 | 674,274 | `84abb8fc772cb960741c27c662c5d00d072b0571ce2ab75e05cf44c763db7701` | `7049834ee3271a04fbb0fad4ba254f001d3e4778251c8539ca30430aab820f00` |
| `probe-01-wait/attempt-1/run-log.json` | 4 | 2,178 | `8d230b44dea46aff4354b2ad5d8ebb2a49b9644f00d45ddead9f6f309bbc0c10` | `37ed4190bca90f4211a0d46c16a038af97d563955b0b85edf58626b2979492c4` |
| `probe-01-wait/attempt-1/run-stdout.log` | 1 | 449 | `d1dbb45b53b6a82239777fe61c1ff30de44960623427df3300a02ca3e348e7d2` | `ddcb405a45ae3720f00b5026d328e96cb892874739c5c5769e467ee5a8bae38d` |
| `probe-01-wait/attempt-1/run.log` | 1 | 631 | `6079ea63b6c36108c096cfb05c169ca0940b435910207becfd6bed71f56208ba` | `f58405408b713cd7776d1231e8482b649c5da0876d37c81d723945ff3351398a` |
| `probe-01-wait/attempt-2/raw/properties-presubmission-20261021T140551Z.json` | 1 | 674,274 | `dcdee7588baffc4bd7b1d26e7513d559fd5e39d11c6c5b07822e9a5eb675ccca` | `c617094573a82bf4c61d0c496886cfd862658a6fc23609e6941ec8bfca297542` |
| `probe-01-wait/attempt-2/run-log.json` | 2 | 1,204 | `a38cfcd57c3318ad214f0f775994c44bba669b111a0364d3f40932389f079d5d` | `c866389515ee36807e7e4f2b8911f16094b07832ee483457cde89513ba37df77` |
| `probe-01-wait/go.log` | 2 | 2,000 | `e1cbfa7d78cff3494d81d7a8dfc2718e5a8c3e83dc2761a7d4010d642ac62ff9` | `2f9bde59df7d299e5b2551084233a8ef8bc88bb25aa6705df2c64598e0f55c65` |
| `probe-01-wait/raw/properties-presubmission-20261021T160033Z.json` | 1 | 674,360 | `6c8626ac1aaba9e1463ce8aa7fab8781ec5e13c58bf38302e8fccb50f912ac78` | `3b97c34045f4ab7a0e269b286599e06316d098e46dea3db1494106a34e55f02a` |
| `probe-01-wait/report-probe-01.md` | 20 | 9,728 | `9c5e77842db86aaccb71ffce32d7b9acacf416a8ddcb7651a0bf901c87d12822` | `d6b02d960e57564f641447dc9e662898bd295ab75a652c964a647e7d1c2b26b5` |
| `probe-01-wait/run-log.json` | 12 | 4,492 | `19cac602e7a2eefc52acac2624ddae85010b4d6bad751cc8e5ba059ccd33e5b5` | `41c96f5c96f88d14f272d2f00b56ce966f2b8c99557ce5aa9f2ded6322b13eb5` |
| `probe-01-wait/run.log` | 7 | 7,142 | `ae68e5d23eb35749f0eaddbe81f7045a2e961b3d54150a67a75d4e68be7e4ba4` | `c3afd42a2ebd2e34a32e59364adcf98506595f1e0184cc8bc10f019acd18dbf4` |
| `probe-01-wait/scripts/finalize.py` | 1 (the folder's path) | 3,806 | `1e7a8b69cbe9fffc387e5680fb40c8575c87b5928b72304b7d071dd987339f6a` | `d8269692e4dc82be5f290cc712575d891c6affa4f27cad8774d8ed06297bba14` |
| `probe-01-wait/scripts/run_probe-as-run-20261021T134740Z.py` | 2 | 13,346 | `e179024d1a32dfa073b9a65075c5534f1854466afb0e9a8e8d7726ce115d5c3c` | `6b8bbd112873c91801e7a2ec06fa09c1c82bbfeb6df53735e00c28a63e6e1e90` |
| `probe-01-wait/scripts/run_probe.py` | 2 | 14,174 | `d7d49e103a5d0d36f888dc3c7eff1d962bd3d209ff665b1d4e53e4f6ad237cfd` | `806fd46aeffd98189bff44c1a565c4bd15b4f7b561804e108eb70e0d5a66df3d` |
| `probe-02-scaling/go.log` | 1 | 1,414 | `f264a409d5cb71599fa3cbd6039b3763d3c94dc4fae3d1f2a1befa2cfebdcceb` | `0a98f00edd101c7f1b7797f739ab8ae7782973462a5510e6858ef47c45907781` |
| `probe-02-scaling/raw/properties-fetch-A0-20261021T195956Z.json` | 1 | 674,520 | `401cc7e29ab2d8f6d6b5b89ed1cd69c3e28d28a2fee5fdcaab01c51c85b8820d` | `649cbe59b411e093c93896ce27cc33de3b7143a1a5aca6273f5f4fa1bfb8b5f2` |
| `probe-02-scaling/raw/properties-fetch-A1-20261021T195957Z.json` | 1 | 674,520 | `401cc7e29ab2d8f6d6b5b89ed1cd69c3e28d28a2fee5fdcaab01c51c85b8820d` | `649cbe59b411e093c93896ce27cc33de3b7143a1a5aca6273f5f4fa1bfb8b5f2` |
| `probe-02-scaling/raw/properties-fetch-A2-20261021T195958Z.json` | 1 | 674,520 | `401cc7e29ab2d8f6d6b5b89ed1cd69c3e28d28a2fee5fdcaab01c51c85b8820d` | `649cbe59b411e093c93896ce27cc33de3b7143a1a5aca6273f5f4fa1bfb8b5f2` |
| `probe-02-scaling/raw/properties-fetch-B1-20261021T195959Z.json` | 1 | 674,520 | `401cc7e29ab2d8f6d6b5b89ed1cd69c3e28d28a2fee5fdcaab01c51c85b8820d` | `649cbe59b411e093c93896ce27cc33de3b7143a1a5aca6273f5f4fa1bfb8b5f2` |
| `probe-02-scaling/raw/properties-presubmission-20261021T195947Z.json` | 1 | 674,520 | `401cc7e29ab2d8f6d6b5b89ed1cd69c3e28d28a2fee5fdcaab01c51c85b8820d` | `649cbe59b411e093c93896ce27cc33de3b7143a1a5aca6273f5f4fa1bfb8b5f2` |
| `probe-02-scaling/report-probe-02.md` | 15 | 11,679 | `c2a67429930121cd1ddf8d2912986ed0416fd7d6d5e8f42bdfa723e682d74aff` | `d47f954bd61a007c059575dca544c819ba6ae8c1f071d4554ba93e5e0f199d81` |
| `probe-02-scaling/run-log.json` | 19 | 7,278 | `f3467329ebff6915506f1dcd1c48b2576bd077329659701bc50f4f81c080bbd8` | `95ef306bbb5cb7356446e678746b1aece99d974360ce07a5532e94955b61fb11` |
| `probe-02-scaling/run-stdout.log` | 13 | 1,422 | `75c34d1008df76a86c1be207530de53a4c1969096d357611ba242d3fd53ace4e` | `0e0b9783cf19ac6c857bd5c08c93dc749a7fdfc4619d7c1deb189f92859aa9cc` |
| `probe-02-scaling/run.log` | 13 | 1,422 | `75c34d1008df76a86c1be207530de53a4c1969096d357611ba242d3fd53ace4e` | `0e0b9783cf19ac6c857bd5c08c93dc749a7fdfc4619d7c1deb189f92859aa9cc` |
| `probe-02-scaling/scripts/check_limit.py` | 2 | 1,291 | `6ede4d8682c33c1748eac6360a9997dff0a132a3a2673fea4fe0d6107d49d486` | `ba2758104220f34430c6dbb628d2887a4a2ef321e8792de327f0585bdac5d161` |
| `probe-02-scaling/scripts/finalize.py` | 1 (the folder's path) | 5,117 | `7e593c39e9893e46b28413d2ede25d81fc08c4916190e437bd03fea30e71ffc3` | `c2bdd264216498f4567e3beba8752e526228247a67221181e69fb6e4386eeb20` |
| `probe-02-scaling/scripts/run_probe-as-run-20261021T195945Z.py` | 2 | 17,623 | `79ccf8f299367582b59e4a9b79ad72d0f36087479181ead072ba21d06b0544a8` | `88586a1a590092278353ff00d8954746d38596227cba644363113b19656666fb` |
| `probe-02-scaling/scripts/run_probe-probe01-start.py` | 2 | 14,174 | `d7d49e103a5d0d36f888dc3c7eff1d962bd3d209ff665b1d4e53e4f6ad237cfd` | `806fd46aeffd98189bff44c1a565c4bd15b4f7b561804e108eb70e0d5a66df3d` |
| `probe-02-scaling/scripts/run_probe.py` | 2 | 17,623 | `79ccf8f299367582b59e4a9b79ad72d0f36087479181ead072ba21d06b0544a8` | `88586a1a590092278353ff00d8954746d38596227cba644363113b19656666fb` |
| `probe-03-program-set/attempt-1/go.log` | 1 | 1,323 | `9fc813f27a5716f4686f079de2c2dda44f01eb455bfb6a34f811c4026a60c31a` | `4f2637b590da57dad3e53937355e6aa21fc110a8229d6da8f00b74eb4286c4ed` |
| `probe-03-program-set/attempt-1/pre-go-checks.md` | 2 | 1,130 | `5f55b9aca9c13bb9faf5106333858095a2efc89cc4f2bdaa82b4d538fa7515fa` | `ce2c2fd06adc3532f2e0ed07c4ecf5d08fb82156e5a8e3d04f62423ed97b5c6a` |
| `probe-03-program-set/attempt-1/raw/properties-presubmission-20261021T203820Z.json` | 1 | 674,522 | `b468cae835daf0d8b01a9161c3cab48cb59c8e1c72024cc3b2246e6715f3d52a` | `149f122b86673f7b0103b3c47e002cf31c2c6ba6e84cbc4fb272634c4b5e75eb` |
| `probe-03-program-set/attempt-1/redaction-log.md` | 12 (withheld) | 4,291 | `a09231cfa9a11e4a681a94b8e225f3de963043bda6d018ce9dc254f02bcbd008` | `49d318284696c878b7bc69ab20cfb91ccbe75c296ee20d7a1a3571b72597f85f` |
| `probe-03-program-set/attempt-1/report-probe-03.md` | 3 | 8,941 | `48f26bd084cd9a4a5379cb9e52349b6d430aa755d01ee93ec6380e9afe52b17d` | `9df5668bf46cac4eadf6c4f1d1abf9d7ebcc4e7170fbd894d97e1138c25c0495` |
| `probe-03-program-set/attempt-1/run-log.json` | 5 | 2,549 | `c32d51edd4820bdeb2ae3059546b07dc024b9a6acf574a84cf96a4527457ad7c` | `3e202cc5717da9124ac8dff14c7ce96c0e9e0a46da48c049bcf925d21fd6265d` |
| `probe-03-program-set/attempt-1/run-stdout.log` | 2 | 831 | `19be844367e10e09c326aa3676ea5efd0c6f79b092a8e10711229622cc1086ce` | `32fb62c3201735f76f2384d4c029c922d667658a04b01e06865384f42a776be5` |
| `probe-03-program-set/attempt-1/run.log` | 2 | 824 | `f46335a5f49023d9b59e1e7a20490607e4225249746ed90e5717dc16ef36e681` | `26f5c124030feffd5cf66c4a8bb50e73c8ba7fc54daa50ffe50fa7de973d7e4f` |
| `probe-03-program-set/attempt-1/scripts/explain_kept.py` | 7 (withheld) | 6,291 | `a056af7556e73ba0c5c618890f127e74e61a5ad158add97ea8a7aadc002e8a9a` | `bde7db7d209fd7c3daf32a4dec4d1d9c02b1120214a879b75bffc5c5f0e89865` |
| `probe-03-program-set/attempt-1/scripts/finalize.py` | 1 (the folder's path) | 5,606 | `21e5bfb079eb4a3a80d1b59cab9b5ebf8e4b7c53fbe7df9b04c7fe9269bb049e` | `afa4c56e038afb054c3bc8a86a4f3b2f8baba69b0b7100e2f502c1161b922458` |
| `probe-03-program-set/attempt-1/scripts/run_probe-probe02-start.py` | 2 | 17,623 | `79ccf8f299367582b59e4a9b79ad72d0f36087479181ead072ba21d06b0544a8` | `88586a1a590092278353ff00d8954746d38596227cba644363113b19656666fb` |
| `probe-03-program-set/attempt-1/scripts/run_probe.py` | 3 | 22,300 | `d3fbde083ff058855d6c750130a1936d0596909cdd1de1fa451ab862138dbade` | `5e05cee67e67036462c13cfd0c43af53ee2fe14e22a0ceb4f464af37f136d6ac` |
| `probe-03-program-set/go.log` | 2 | 1,830 | `d217bde29026408454e298cc0e7ffeeb4ccd972137f1e1b62efb51994137c2cb` | `5c190ad70bd26d1599471d906a8c93c800456c8aa715295afcb89321c71b7566` |
| `probe-03-program-set/pre-go-checks.md` | 2 | 1,613 | `5d665dcf8035f46cf21c98571a10eabf2417261f133a412c5c0f7ffc1bf3119c` | `14061b2a00460eb1a03f38809a2050ded40d9fdca3fecd2567e61313a5a50c66` |
| `probe-03-program-set/raw/properties-presubmission-20261021T211710Z.json` | 1 | 674,522 | `a383a76c8d608c8082ac2ca2c1e34a1b20611cbce00cf62f1c47e574f4271536` | `edeb501463e3acedb523284b0f33451a407022c1e7c1a8089e966b4871213ae2` |
| `probe-03-program-set/redaction-log.md` | 12 (withheld) | 6,459 | `d4c3ea357c56afffa0c8b40769a75de0e0e96ff41dd9b6e8fc5a1d361c4f8d08` | `5df0ea38cbc59951f109c93da39c0b804224e1d76ea192ead204f60b0b581b2c` |
| `probe-03-program-set/report-probe-03.md` | 6 | 11,480 | `ce2a2dc57ed787b2a91c93419adb1ac9ffd72b7cd2f935057f379c8147a12b19` | `cd965cd3f94d120a8b155cd7fb9b3af2fa8fc26556739c571355e77ba2bddc85` |
| `probe-03-program-set/run-log.json` | 5 | 2,044 | `78046510db3aedee622124cccfabfe20e47b6229d840ecefe05b412c7b737dd6` | `f345dcc2b635480350a03d0150e1cab0835d8b722dded73d902e031a2c114203` |
| `probe-03-program-set/run-stdout.log` | 2 | 1,389 | `134af21fbec05bbfc5c9ef55112d9b45ab3d4656047a9fcccb7c09fe9a27d53b` | `f5e1962757444e2627e419eae11bae3d13f155daaab90d397164aec66fe19de5` |
| `probe-03-program-set/run.log` | 2 | 1,382 | `4303a6379622c837a1aed12980bca50a26e5ea4f0dcd100becd566c81b6b47da` | `a370feb4a0f5f1b5415ec0b0b4f2c7e1092bfaa83c28db4c2e263077ffbcecc4` |
| `probe-03-program-set/scripts/explain_kept.py` | 7 (withheld) | 6,593 | `44c62067e6cb4f7308ba23cb85d02c711efd37f374f0cab1723dd34faf5bdf5c` | `6092d44dd090c516962979fdc403b6b981ed12dddb0e2114ba78dab8aa2515ac` |
| `probe-03-program-set/scripts/finalize.py` | 1 (the folder's path) | 5,852 | `afa6ac650135a26cd8510c5cd14ece2a3058236faa1570a7af03f466db1b287c` | `f7a8654005f64ae0c5408294bc56e1f4d5747ea816ae7ef68b7a80f88e9975ea` |
| `probe-03-program-set/scripts/run_probe.py` | 2 | 23,014 | `ab8f7125b4f89222dfe06048e231709fbfedea20d6ba71cce2776a75572d09e0` | `84ec6ea1a3bea4606da9f80dfb2bd8db1ed1381ae76c5c5784ffc112c384426b` |
