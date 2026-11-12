# Install the recovered REDRAFT research alpha

This package contains the saved2018-only application, analytical artifacts and tests. It is not the requested all-years completed release. The uncommitted personnel changes from the interrupted session are not present.

## Requirements

Node.js22.13or later; pnpm11.25.0; Python3.11+for analytics; network access to dependency registries. Use a trusted Node/pnpm installation. Do not send API keys or passwords in chat.

```sh
node scripts/setup.mjs
# Optional isolated analytical environment:
node scripts/setup.mjs --python
```

The setup uses the frozen lockfile and runs real domain tests. It stops on any failure. It does not modify global Python packages, overwrite an existing virtual environment, publish a server or create accounts. Windows/macOS behavior is not verified by the Linux execution.

## Tests

```sh
node tests/run.mjs
python3 tests/warehouse_test.py
node node_modules/typescript/bin/tsc --noEmit
```

Research ingestion needs source access. Activate .venv before Python research commands, then follow README.md and SOURCE_REGISTRY.md. Do not interpret missing raw files as zero data. The full gauntlet requires reacquiring source inputs and can legitimately exit2when statistical gates fail.

## Web application dependencies

The web application currently relies on Cloudflare D1 and Sites identity/request context. Installing packages alone does not provide a standalone authenticated web server. Existing migrations are in drizzle/. Read DEPLOYMENT.md for the hosted environment. A portable identity adapter and independently verified local DB startup are release-plan tasks; no production auth bypass is provided.

## GitHub import

Intended new repository: jviola1019/redraft. Do not copy this into an unrelated existing project. Repository creation and upload have not been completed. After creating a private empty repository and authenticating Git locally:

```sh
git init -b main
git add .
git commit -m "Import REDRAFT research alpha and release plan"
git remote add origin https://github.com/jviola1019/redraft.git
git push -u origin main
```

Review the ignore rules and source licensing first. Exclude .venv,node_modules,raw downloads,runtime state and credentials. These commands are instructions, not evidence of a completed upload.
