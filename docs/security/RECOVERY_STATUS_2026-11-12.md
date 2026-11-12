# Recovery checkpoint status — 2026-11-12

## Scope

This is a **partial evidence checkpoint** for frozen local commit `73755533c6a34cb3a3b1e1e4c76a40e87400881a`, parented on baseline commit `81cc2b89b8867c69a01e9ee71eb27fe80b0731e4`.

The source environment became unavailable during transfer. 166 of 196 changed source paths are included; 30 paths (all test/evidence paths, 30 unique blobs) are missing. Critical production source, dependencies, security remediation, season scenario JSONs, and model files are preserved. The original README and CI file are archived; the top-level README has this notice and the CI workflow has a recovery edit that adds wider release checks.

This branch is **not a byte-identical copy of the complete tested checkout and is not a full release claim**. The execution receipt records a mixed final gauntlet result, API and browser/install observations; it does not certify this incomplete branch. See [execution receipt](../release/EXECUTION_RECEIPT_2026-11-12.md) and the [machine-readable path manifest](RECOVERY_MANIFEST_2026-11-12.json).

## Missing paths

- `tests/results/gauntlet/2026-11-12T20-32-32-973Z-nov12-release-audit-20f4fe7b/17-statistical-integrity-tests.stderr.log` — `fd39e6272269b82c454d6fb3912cfc1b095bb0c6` (1110 bytes)
- `tests/results/gauntlet/2026-11-12T20-32-32-973Z-nov12-release-audit-20f4fe7b/18-statistical-gates.result.json` — `8761a353dccbcfdeae35d098242164ff56d9ace3` (560 bytes)
- `tests/results/gauntlet/2026-11-12T20-32-32-973Z-nov12-release-audit-20f4fe7b/REPORT.md` — `5a4bbc7c7f628b3af1a448f6e36ef73bf333bb39` (3256 bytes)
- `tests/results/gauntlet/2026-11-12T20-32-32-973Z-nov12-release-audit-20f4fe7b/league-matrix.json` — `46f146f59fd4c8dabffb06f0f08438daaaff9952` (91009 bytes)
- `tests/results/gauntlet/2026-11-12T20-32-32-973Z-nov12-release-audit-20f4fe7b/manifest.json` — `5fc3a2ec0da00b6a737dd35f441f6d4efcf6c4b3` (28406 bytes)
- `tests/results/gauntlet/2026-11-12T20-32-32-973Z-nov12-release-audit-20f4fe7b/report.json` — `b0c6628b10f26a9e5abaf1dbf4ac845529985ccc` (48925 bytes)
- `tests/results/local-http-server.log` — `284193a2f4751b367735b46648d2e50cab463192` (753 bytes)
- `tests/results/local-http.json` — `cf0ceb9e2b82fd22de6a5bafa5f062f2cf1a5c6a` (369 bytes)
- `tests/results/playoff-backtest.json` — `809fbdd2f6db0694c7d712bfba80d5003f149ae5` (8218 bytes)
- `tests/results/recorded-coverage-2026-11-12.json` — `292c607990c5c1fddcc3006b2170894d32f38bb3` (6123 bytes)
- `tests/results/year-matrix-2026-11-12/2018.json` — `7488b54747cab2054e649080349e2530e2067859` (91023 bytes)
- `tests/results/year-matrix-2026-11-12/2018.log` — `1138e82f38328079ff99f40abd74b71714843cfd` (1249 bytes)
- `tests/results/year-matrix-2026-11-12/2019.json` — `4f6f4f7b14448d2bfeee9a3f83cb25e87f7ed3bc` (90988 bytes)
- `tests/results/year-matrix-2026-11-12/2019.log` — `8d3974420d5ddcf12a5b45dc140d5747d6eb78ee` (1249 bytes)
- `tests/results/year-matrix-2026-11-12/2020.json` — `01120bb31bdd6ebe6580299e014f5bc05748104f` (90986 bytes)
- `tests/results/year-matrix-2026-11-12/2020.log` — `2ac63703049becaf2cd58ff3b058501fb7c5327c` (1249 bytes)
- `tests/results/year-matrix-2026-11-12/2021.json` — `c7369bf03eddac1efd62dcbdae6bdcec16b2ae60` (91016 bytes)
- `tests/results/year-matrix-2026-11-12/2021.log` — `d4a06b69cee58084514a36f38b8812ea9c92e2f5` (1249 bytes)
- `tests/results/year-matrix-2026-11-12/2022.json` — `c5fa921c00ffeabe2ab4133a284e56340326e641` (91032 bytes)
- `tests/results/year-matrix-2026-11-12/2022.log` — `3a0a55f462f95eb720a2a58b92df8508ac3a92aa` (1249 bytes)
- `tests/results/year-matrix-2026-11-12/2023.json` — `35b5c1435177b984a11d88b21d67a37b81349cda` (91022 bytes)
- `tests/results/year-matrix-2026-11-12/2023.log` — `41b44e66f95ee117ccc2cbb7b623ce00f9e2d245` (1249 bytes)
- `tests/results/year-matrix-2026-11-12/2024.json` — `db3080d46e69066b2a416503dddca97d22fab8c2` (91018 bytes)
- `tests/results/year-matrix-2026-11-12/2024.log` — `8ff44a17c65c021b70e5470415dbf6388cd56f30` (1249 bytes)
- `tests/results/year-matrix-2026-11-12/2025.json` — `b91469a86a3c9735985398eb922fb95b045aebd8` (91013 bytes)
- `tests/results/year-matrix-2026-11-12/2025.log` — `ce05b1b0a708163bc6c45905d818c0e8d637a6d8` (1249 bytes)
- `tests/results/year-matrix-2026-11-12/2026.json` — `4a450d0e0c7ca30b2bd3d3105aeb7b5784e6082c` (91012 bytes)
- `tests/results/year-matrix-2026-11-12/2026.log` — `0cc8ec7991aba54896939016b23c7b36159c23a0` (1249 bytes)
- `tests/results/year-matrix-2026-11-12/summary.json` — `fd0181a5e408e493dd6b6a3be037223c3879657e` (408 bytes)
- `tests/year-contract.test.ts` — `a7fa2a152be358392a9f4887de61ea87e330088f` (5102 bytes)

## Recovery note

This checkpoint preserves baseline ancestry and does not update `main`. Recover the missing source blobs from local commit `73755533c6a34cb3a3b1e1e4c76a40e87400881a` if its object database becomes available. `tests/scenario-data.test.ts` is included with its exact frozen blob. `tests/year-contract.test.ts` is absent from this checkpoint; a later replacement must be marked as a recovery edit if it differs from the frozen blob SHA.
