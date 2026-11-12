# Dependency security remediation — 2026-11-12

## Result

The pre-remediation audit snapshot in `tests/results/dependency-audit.json` reported 35 high and 4 critical findings. The dependency graph is now clean in the fresh pnpm audit: 0 critical, 0 high, 0 moderate, and 0 low findings (Node 24.22.1, pnpm 11.25.0; 2026-11-12).

No audit suppressions or allowlists were added. The existing seven-day install-age rule (`minimumReleaseAge: 10080`) remains enabled. Both lockfile regeneration and `pnpm install --frozen-lockfile` passed pnpm's supply-chain policy check.

## Vulnerable dependencies updated

| Dependency | Previous resolved version(s) | Selected version | Advisory coverage |
| --- | --- | --- | --- |
| `next` / `eslint-config-next` | 16.3.4 | 16.4.1 | [GHSA-vcvr-r3jv-pc5j](https://github.com/advisories/GHSA-vcvr-r3jv-pc5j), [GHSA-cjq9-62q9-8jv4](https://github.com/advisories/GHSA-cjq9-62q9-8jv4), [GHSA-2464-fhr4-w9xw](https://github.com/advisories/GHSA-2464-fhr4-w9xw), [GHSA-p3m5-59mp-jv5r](https://github.com/advisories/GHSA-p3m5-59mp-jv5r), [GHSA-673q-mjm6-r5xr](https://github.com/advisories/GHSA-673q-mjm6-r5xr) |
| `react`, `react-dom`, `react-server-dom-webpack` | 19.2.6 | 19.2.9 | [GHSA-wx67-qw84-cm4g](https://github.com/advisories/GHSA-wx67-qw84-cm4g), [GHSA-xqc2-xf4c-x3h3](https://github.com/advisories/GHSA-xqc2-xf4c-x3h3) |
| `vite` | 8.0.13 | 8.1.6 | [GHSA-587h-7wmj-h5pm](https://github.com/advisories/GHSA-587h-7wmj-h5pm) |
| `undici` | 7.24.8 | 7.30.2 | [GHSA-vmh5-mc38-953g](https://github.com/advisories/GHSA-vmh5-mc38-953g), [GHSA-hm92-r4w5-c3mj](https://github.com/advisories/GHSA-hm92-r4w5-c3mj), [GHSA-4cwx-7wf7-3272](https://github.com/advisories/GHSA-4cwx-7wf7-3272), [GHSA-rfgv-xxqx-mfg5](https://github.com/advisories/GHSA-rfgv-xxqx-mfg5), [GHSA-w293-vg96-wgc3](https://github.com/advisories/GHSA-w293-vg96-wgc3), [GHSA-xjj6-f33q-929c](https://github.com/advisories/GHSA-xjj6-f33q-929c), [GHSA-4w7w-5xrc-9h26](https://github.com/advisories/GHSA-4w7w-5xrc-9h26), [GHSA-2m5v-pch6-74hx](https://github.com/advisories/GHSA-2m5v-pch6-74hx), [GHSA-qrxm-fqhp-jwvm](https://github.com/advisories/GHSA-qrxm-fqhp-jwvm), [GHSA-vxpw-j846-p89q](https://github.com/advisories/GHSA-vxpw-j846-p89q) |
| `ws` | 8.18.0 | 8.21.0 | [GHSA-96hv-2xvq-fx4p](https://github.com/advisories/GHSA-96hv-2xvq-fx4p) |
| `sharp` (including Miniflare) | 0.35.4 | 0.35.5 | [GHSA-wq5f-xc86-pv6w](https://github.com/advisories/GHSA-wq5f-xc86-pv6w) |
| `zod` | 3.25.76 | 4.6.6 | [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5) |
| `brace-expansion` | 1.1.14, 5.0.6 | 1.1.21, 5.0.12 | [GHSA-3jxr-9vmj-r5cp](https://github.com/advisories/GHSA-3jxr-9vmj-r5cp), [GHSA-mh99-v99m-4gvg](https://github.com/advisories/GHSA-mh99-v99m-4gvg), [GHSA-rgw5-rvv9-x895](https://github.com/advisories/GHSA-rgw5-rvv9-x895), [GHSA-qhr7-859c-m2p7](https://github.com/advisories/GHSA-qhr7-859c-m2p7), [GHSA-6j4f-fj2g-mc7p](https://github.com/advisories/GHSA-6j4f-fj2g-mc7p) |
| `js-yaml` | 4.1.1 | 4.3.2 | [GHSA-52cp-r559-cp3m](https://github.com/advisories/GHSA-52cp-r559-cp3m), [GHSA-5p4m-2wfm-xmqj](https://github.com/advisories/GHSA-5p4m-2wfm-xmqj), [GHSA-2883-xcg3-v3hh](https://github.com/advisories/GHSA-2883-xcg3-v3hh) |
| `browserslist` | 4.28.2 | 4.28.7 | [GHSA-c83g-rgw3-j3cx](https://github.com/advisories/GHSA-c83g-rgw3-j3cx), [GHSA-73wf-gq98-2v4g](https://github.com/advisories/GHSA-73wf-gq98-2v4g) |
| `image-size` | 2.0.2 | 2.0.3 | [GHSA-5p2g-fcmc-qvqq](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq), [GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr) |
| `source-map-js` | 1.2.1 | 1.2.2 | [GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q) |

The audit also showed lower-severity issues in `esbuild`, `minimatch`, and other transitive packages. Compatible-range overrides brought those to audited versions: `esbuild` 0.28.1, `minimatch` 11.0.1, `@babel/core` 7.29.6, `fflate` 0.7.5, `baseline-browser-mapping` 2.11.35, and `fast-uri` 3.1.9. The remaining advisories from that snapshot were also cleared by the selected overrides, including `satori` 0.33.5.

## Compatibility and checks

- Node runtime requirement is now `>=24.0.0`; the tested runtime was Node 24.22.1.
- React and React DOM were aligned to 19.2.9, matching `react-server-dom-webpack`'s declared peer range.
- The two `z.record` schemas in `scripts/connector-preview/protocol.mjs` now use Zod 4's explicit key and value schemas.
- `pnpm install --frozen-lockfile` — passed.
- `pnpm exec tsc --noEmit` — passed.
- `pnpm build` — passed (vinext build with Vite 8.1.6).
- `pnpm audit --json` — 0 advisories at all severity levels.

## Registry and advisory references

Package versions and peer/engine metadata were checked against the npm registry for [Next 16.4.1](https://registry.npmjs.org/next/16.4.1), [React 19.2.9](https://registry.npmjs.org/react/19.2.9), [React DOM 19.2.9](https://registry.npmjs.org/react-dom/19.2.9), [react-server-dom-webpack 19.2.9](https://registry.npmjs.org/react-server-dom-webpack/19.2.9), [Vite 8.1.6](https://registry.npmjs.org/vite/8.1.6), and [Zod 4.6.6](https://registry.npmjs.org/zod/4.6.6). The remaining advisories were checked against the official [GitHub Advisory Database](https://github.com/advisories).
