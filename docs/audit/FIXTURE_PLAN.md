# Fixture validation and release protocol

Recorded before application edits, November 19 Chicago. Base review source 9157a87, equivalent to published bfc5bd0. Main separately includes the Jekyll workflow at 6006d80.

1. Freeze expected release years (2018–2026), 32 franchises per scenario, the three named draft seeds, two replicate indices and first-seed replays. Validate reports against source scenario team IDs and versions. Treat aggregate counts alone as insufficient.
2. Use a known successful archived matrix as positive control. Preserve its summary while removing rows, repeating cases or replicates, substituting a different scenario, or corrupting a hash as negative controls. First demonstrate what the existing runner accepts. Reject a missing class, duplicate class or empty manifest before declaring a successful run.
3. Reproduce the domain suite and the archived statistical decision. Evaluate scoring, quarterback and CPU changes independently on time-ordered fixtures. Maintain actual measurements, previous gate tolerances and rejected candidates. Report sampling limitations.
4. Verify Daily disclosure, revisions, persisted scores, two complete game flows, narrow viewport and the actual build in CI. Score-weight perturbations must preserve the official result.
5. Audit the Jekyll publication source and artifact, verify a page contains a working game access path, distinguish access-controlled hosting from publicly readable static files, and check that source data, uploads, saved games and project internals cannot enter the published artifact. Inspect the live deployment after its workflow succeeds.

**Independent reviewer prompt**

Start with the named revision and the actual input files. Enumerate the cases before inspecting outcomes. For each positive fixture, construct a minimally changed invalid counterpart. Run both against the unmodified implementation. Repair only demonstrated defects. Verify that the repair rejects the invalid input for the intended reason and still accepts complete evidence. Record commands, versions, sample sizes, failures, decisions and release boundaries. A prediction or security claim requires its own evidence. A green deploy records artifact delivery only.
