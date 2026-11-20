# Next.js advisory remediation — 2026-11-20

The registry audit reported seven moderate Next.js advisories with `next@16.4.1`; every reported advisory specifies a patched range of `>=16.4.5`. This change pins `next`, its workspace override, and `eslint-config-next` to `16.4.5` and regenerates the pnpm lockfile. Framework companion packages follow the patch. No application behavior change is intended.

The registry reports `next@16.4.5` published on **2026-11-03T18:01:54.667Z**. The workspace's `minimumReleaseAge: 10080` (seven days), strict build approval policy and frozen CI installation remain unchanged. No release-age exception was needed. Lock regeneration removes nine obsolete dependency entries (776 → 767); it does not upgrade unrelated top-level dependencies.

## Reported advisories

| Advisory | Registry audit title | Patched range |
| --- | --- | --- |
| [GHSA-mfr8-8qww-v76h](https://github.com/advisories/GHSA-mfr8-8qww-v76h) | Next.js: Information disclosure across root params when a 'use cache' function is called through unstable_cache() | `>=16.4.5` |
| [GHSA-vc7v-qv4w-wrv8](https://github.com/advisories/GHSA-vc7v-qv4w-wrv8) | Next.js: Cache leak across root param values in nested 'use cache' functions via delayed inner stream metadata | `>=16.4.5` |
| [GHSA-7qx7-33qx-rqx2](https://github.com/advisories/GHSA-7qx7-33qx-rqx2) | Next.js: SVG rejection bypass in the image optimization | `>=16.4.5` |
| [GHSA-f3mh-rxg3-f5g2](https://github.com/advisories/GHSA-f3mh-rxg3-f5g2) | Next.js: HttpOnly cookie exposure through internal response header on Next.js Edge runtime routes | `>=16.4.5` |
| [GHSA-pc58-hwjq-p385](https://github.com/advisories/GHSA-pc58-hwjq-p385) | Next.js: Cross-client response injection and disclosure in self-hosted Next.js applications forwarding fetched responses | `>=16.4.5` |
| [GHSA-rhh4-g77r-r9qj](https://github.com/advisories/GHSA-rhh4-g77r-r9qj) | Next.js: Cross-user cache disclosure and poisoning in Next.js use cache with binary arguments | `>=16.4.5` |
| [GHSA-vvgp-ww4w-46vf](https://github.com/advisories/GHSA-vvgp-ww4w-46vf) | Next.js: Cache poisoning of shared fallback shells in Cache Components via request-supplied placeholder route params | `>=16.4.5` |

## Verification

Executed in isolated worktree `/tmp/redraft-security-next-patch`, based on commit `1a35ce8`, with Node 24.22.3 and pnpm 11.25.0:

- `pnpm install --frozen-lockfile`: passed with release policy enforced.
- `pnpm audit --json`: exited 0; **0 info, 0 low, 0 moderate, 0 high, 0 critical** across 767 dependency entries. Before/after raw reports are in `docs/audit/dependency-evidence/`.
- `pnpm exec tsc --noEmit`: passed.
- `node tests/run.mjs`: 82 passed, 0 failed.
- `pnpm run build`: passed. Existing vinext static route-classification warning remains; it does not classify dynamic routes completely.

This is a dependency advisory remediation, not a security certification. Registry coverage is time-dependent. The audit did not establish exploitation in this application, and production edge configuration, identity trust and deployment verification remain separate requirements. No production deployment or original worktree mutation was performed as part of this isolated patch verification.
