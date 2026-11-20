# Execution capabilities

GitHub connector and Git CLI support revision inspection. GitHub Actions supports hosted WebKit and Chromium. Local shell, Python, SQLite, Node and pnpm support the existing application and validation pipelines. Design work uses source-controlled SVG and CSS. Figma, Sites and Library connectors are discoverable. No external design document was imported. No deployment credential was verified.

| CLI | Found on PATH |
|---|---|
| git | True |
| node | True |
| pnpm | True |
| python3 | True |
| R | False |
| duckdb | False |
| sqlite3 | False |
| semgrep | False |
| codeql | False |
| osv-scanner | False |
| docker | False |
| chromium | True |
| wrangler | False |

| Selected capability | Action | Evidence | Boundary |
|---|---|---|---|
| Git CLI and hosted GitHub integration | Read main, create isolated local review worktrees, submit and verify the remote review tree and pull request | Baseline, PR #1 and commit trees | No production deployment |
| Hosted GitHub Actions | Install from lockfile, type-check, run tests, build and initialize local D1, exercise browsers | Workflow ci.yml and commit-specific run IDs in release report | Hosted runner with local database |
| Node 24, pnpm 11.25.0, TypeScript | Frozen installation, build artifact inspection, domain and API suites | Dependency patch report, gauntlet manifests and BUILD_INSPECTION.json | Single dependency snapshot |
| Python, NumPy, pandas and SQLite | Reconcile records, exercise schema, compare candidate distributions and score on historical forecast origins | Versioned experiment scripts, archived predictions and data integrity report | Restricted historical coverage |
| Chromium, WebKit and Playwright | Eight hosted responsive journeys, screenshots, reload and keyboard checks | BROWSER_QA.md and visual reports | Emulated devices. Local browser sockets and missing binaries prevented local execution |
| PNG analysis | Inspect hosted captures and compare two WebKit phone layouts | visual/phone-comparison.png | State differs between screenshots |
| Dependency advisory scanner | Resolve findings against patched lockfile | dependency-evidence/ | Registry snapshot, no deployed infrastructure attestation |
| Parallel specialist reviews | Isolate statistical comparisons, historical integrity, security, mobile changes, independent QA and repository transfer | Scoped research reports, separate commits and frozen checks | Shared underlying source data and previously exposed historical cohorts |

External Figma, Canva, Adobe, Lovable and model-hosting services did not contribute production assets or model evidence. The visual changes use the existing application components and football artwork. No external AI inference API was added. Raw-data downloads, build caches, credentials and local saves are excluded from source delivery.
