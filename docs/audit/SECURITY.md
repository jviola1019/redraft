# Defensive security review — 2026-11-20

## Scope and decision

Static review of the game HTTP boundary, authentication adapter, runtime schema and CI configuration. This is a threat applicability assessment, not penetration testing, a certification or proof of absence. No offensive reproduction, network flooding, credential attempts, intrusion or production changes were performed. “Controlled in source” means an inspected implementation exists; it does not mean its hosting configuration was verified.

## Plan and completed change

1. Identify the runtime trust boundary and map all 92 requested labels without silently dropping platform concerns.
2. Preserve owner-scoped SQL, revision/idempotency handling and strict action schemas.
3. Extract the bounded JSON reader into `lib/request-body.ts`; require the exact JSON media type (parameters allowed), reject malformed UTF-8, and release the reader lock. Wire the existing game route to the helper.
4. Add normal contract tests in `tests/request-body.test.ts` for valid same-origin JSON, media type/document errors, cross-origin denial and the actual-byte budget, including multi-byte text.
5. Record verification and remaining operational gaps below.

The old media-type prefix comparison accepted non-JSON subtype names such as `application/jsonx`; the default UTF-8 decoder silently replaced malformed bytes. This is parser ambiguity hardening; no exploitability or account compromise is claimed.

## Evidence index

- `app/api/game/route.ts`: authenticated handlers, strict action schema, owner predicates, prepared SQL, receipts, bounded response projections and server-generated scores.
- `lib/request-body.ts`, `tests/request-body.test.ts`: HTTP body boundary and normal contract tests.
- `app/chatgpt-auth.ts`: provider identity header trust and constrained return paths.
- `db/schema.ts`: persistence entities; `.github/workflows/ci.yml` (or workflow file in that directory): CI permissions and frozen dependency installation.
- `vite.config.ts`, `next.config.ts`: local hosting integration; these do not establish deployed edge security settings.

## Applicability matrix

| # | Threat label | Assessment | Evidence or required control |
| --- | --- | --- | --- |
| 1 | rapid reset | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 2 | bcrypt truncation | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 3 | SAML signature | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 4 | nOAuth | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 5 | GraphQL batching | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 6 | 2FA replay | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 7 | ReDoS | Applicable | Fixed simple pick-ID regex and bounded schema strings; dependency regex behavior not exhaustively reviewed. |
| 8 | JWT alg | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 9 | smuggling | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 10 | cache poisoning | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 11 | proxy IP | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 12 | DB-view RLS | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 13 | insecure token RNG | Controlled in source | Blind salts/seeds use crypto.randomUUID; verify production crypto implementation. |
| 14 | timing | Residual | No custom credential comparison found; owner existence uses generic 404. No timing measurements performed. |
| 15 | padding oracle | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 16 | prototype pollution | Controlled in route | Strict Zod objects exclude unknown fields; no recursive user-object merging in route. |
| 17 | SSTI | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 18 | XXE | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 19 | WebSocket hijack | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 20 | Unicode identities | Platform-dependent | Identity is opaque provider userId, not display name; provider normalization not verified. |
| 21 | BOLA | Controlled in source | run() selects by id AND owner; mutation UPDATE also checks owner and revision. |
| 22 | privilege escalation | Applicable | No app admin role observed; owner-bound saved-game operations reviewed. Platform privileges unverified. |
| 23 | mass assignment | Controlled in source | Strict action schemas; server derives owner, score, revisions and stored state. |
| 24 | missing auth | Platform-dependent | Both handlers call identity(); trusts oai-authenticated-* headers. Edge MUST strip spoofed inbound values and set verified values. |
| 25 | OAuth redirect | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 26 | PKCE/state | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 27 | session fixation | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 28 | CSRF | Controlled in route | Origin and Fetch Metadata checks plus required JSON; absent Origin supported for non-browser clients. Edge/auth trust remains required. |
| 29 | cookies | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 30 | revocation | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 31 | refresh replay | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 32 | credential stuffing | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 33 | reset poisoning | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 34 | enumeration | Controlled in source | Missing and foreign-owned games share Draft not found response; no live enumeration test performed. |
| 35 | WebAuthn | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 36 | MFA downgrade | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 37 | SSRF | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 38 | redirect | Controlled in source | app/chatgpt-auth.ts restricts return paths to same-origin relative paths and excludes reserved auth paths. |
| 39 | SQLi | Controlled in route | Runtime D1 SQL uses prepare().bind(); no user SQL concatenation observed in game route. |
| 40 | NoSQLi | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 41 | shell injection | Not exposed in game API | Game route invokes no shell. Build/research scripts require separate trusted execution boundary. |
| 42 | traversal | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 43 | Zip Slip | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 44 | uploads | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 45 | MIME | Hardened | Exact application/json media-type comparison; malformed UTF-8 rejected; byte cap maintained. Contract tests cover these. |
| 46 | deserialization | Applicable | JSON body validated by strict Zod schemas; stored state JSON trusts DB contents and deployment integrity. |
| 47 | dynamic eval | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 48 | CORS | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 49 | CSP | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 50 | framing | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 51 | DOM XSS | Review limited | React-rendered UI; no browser XSS assessment performed. Repository-wide sink coverage is not claimed. |
| 52 | stored XSS | Review limited | Bounded seeds and server projections exist; no exhaustive stored-content sink analysis performed. |
| 53 | reflected XSS | Review limited | Generic outer error responses; some engine validation messages returned. Browser rendering unverified. |
| 54 | DOM clobbering | Review limited | No custom HTML sanitizer/DOM boundary reviewed; requires browser sink and dependency review. |
| 55 | cookie tossing | Provider-owned / unverified | No local implementation of this credential or federation feature observed; validate the hosting identity provider and session lifecycle. |
| 56 | header injection | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 57 | host poisoning | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 58 | TLS | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 59 | mixed content | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 60 | dangling DNS | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 61 | DNS rebinding | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 62 | property auth | Controlled in route | Public projection removes blindSalt and remaps IDs; pre-reveal masking is conditional. Inference anonymity is not guaranteed. |
| 63 | function auth | Controlled in route | Authenticated discriminated action union and status/version checks; no app administrator functions found. |
| 64 | excess fields | Controlled in route | Strict Zod inputs and explicit response projection; public model metadata remains intentionally disclosed. |
| 65 | quotas | Partial | Authenticated 240 requests/minute D1 counter. No unauthenticated edge quota, spend cap or distributed operational evidence. |
| 66 | unbounded workloads | Partial | 16,000 request bytes; board/trade bounds; four replicates/action; storage budget 1.8MB. Aggregate traffic remains a platform concern. |
| 67 | async exhaustion | Residual | Stream byte cap bounds storage but no application stream deadline; edge body/time/concurrency limits unverified. |
| 68 | pagination/overflow | Controlled in source | History LIMIT 30, leaderboard LIMIT 100; bounded integer inputs. No arbitrary pagination exposed. |
| 69 | race | Controlled in source | Optimistic revision UPDATE and batch receipt predicate; daily uniqueness in schema. Full distributed concurrency proof not performed. |
| 70 | idempotency | Controlled in source | Receipt compares owner and request hash; repeats return saved view. Not a guarantee of identical original response bytes. |
| 71 | webhook signatures | Not exposed in reviewed route | No corresponding protocol, interpreter or endpoint observed in game API; revisit if architecture changes. |
| 72 | secrets | Review limited | No secret values printed or enumerated; deployment secrets and git history secret scanning not performed. |
| 73 | workflow permissions | Partial | CI workflow declares contents:read. Third-party actions use version tags rather than immutable commit digests. |
| 74 | dependencies | Unverified current state | Prior dependency remediation report exists; no fresh registry audit completed in this subreview. |
| 75 | install scripts | Residual | Install and build execute package scripts; dependency sandbox/allowlist controls need explicit review. |
| 76 | confusion/typosquat | Partial | pnpm lockfile and frozen CI install reduce drift; registry/account integrity remains external. |
| 77 | build tampering | Residual | CI builds trusted checkout with dependencies; provenance and isolated protected publishing not verified. |
| 78 | lock drift | Controlled in CI source | pnpm install --frozen-lockfile configured; current dependency installation absent at initial test attempt. |
| 79 | artifact signatures | Unverified | No signed production artifact attestation reviewed. |
| 80 | public storage | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 81 | D1/Worker auth | Platform-dependent / unverified | Requires deployed proxy, TLS, DNS, response headers or binding policy evidence; local route review does not verify it. |
| 82 | migrations | Partial | db/schema.ts defines runtime entities; production migration authorization, backup and rollback unverified. |
| 83 | privacy retention | Residual | Owner IDs, saved runs and receipts persist; no verified user deletion/retention schedule found in route. |
| 84 | logs | Partial | Outer failure logs error name only, no body; platform request logs and retention unverified. |
| 85 | backup restore | Unverified | No production backup recovery drill performed. |
| 86 | leaderboard forgery | Controlled in source | Scores computed server-side, bounded, complete ensemble required; daily_attempts predicate binds eligible game. |
| 87 | security RNG | Controlled in source | crypto.randomUUID used for private seeds/salts; seeded PRNG reserved for simulation, not authentication. |
| 88 | seed/replay | Partial | Seed hidden during drafting/current daily challenge; game versions checked. Statistical fingerprint/replay inference not eliminated. |
| 89 | external prompt injection | Not exposed in runtime | No LLM prompt or agent execution in game route. External source content remains untrusted research input. |
| 90 | repository injection | Workflow concern | Repository instructions/data must not authorize secret disclosure or external side effects; no autonomous runtime agent observed. |
| 91 | agent permissions | Workflow concern | Agent/deployment credentials and approvals are outside application route; least privilege must be enforced by operator. |
| 92 | model/data poisoning | Applicable | Version compatibility blocks stale mutations; provenance, outcome leakage and calibration require independent data/science audit. |

## Verification and limitations

Four contract tests passed under Node 24.22.3 using Node's TypeScript support and a temporary copy of the test with its relative import resolved to the helper. The repository's standard `node tests/run.mjs` could not start at initial verification because its esbuild dependency was absent. These four tests exercise the extracted helper directly, not Cloudflare routing, authentication, D1 atomicity or production traffic. The parent audit should append any subsequent full-suite result rather than treating this local result as full integration evidence.

Highest-priority unresolved controls: prove authenticated header sanitization at the deployed edge; verify D1/Worker/R2 access and DNS/TLS; add/verify response CSP and framing policy with browser compatibility checks; establish unauthenticated abuse limits and budgets; verify current dependency advisories, immutable CI dependencies/provenance, retention/deletion and restoration procedures. No current vulnerability-free dependency claim is made.

Reference guidance for operator follow-up: OWASP ASVS and API Security Top 10, Cloudflare Workers/D1 security documentation, and the platform identity documentation. This report's implementation findings are grounded in the repository and explicitly bounded tests, not an assertion that general guidance proves production safety.

## Integrated follow-up

The frozen install, domain suite, route integration, hosted build and browser evidence are indexed in the release report. The dependency inventory went from seven moderate advisories to zero in the scan documented in DEPENDENCY_PATCH.md. DAILY_BOUNDARY.md covers a subsequent UTC disclosure race. Production edge and operational controls still require independent verification.

[Full 92-item register with per-item verification, severity, remediation and residual risk](SECURITY_REGISTER.md).
