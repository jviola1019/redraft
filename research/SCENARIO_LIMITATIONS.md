# Scenario data limitations

## 2021 actual-selection reference identity

The 2021 playable prospect pool is the official 323-name invitee list. Its measurement join uses the audited exact normalized player-name and school pair; 182 invitees have a provider row and 141 do not. Eligibility does not depend on provider measurements or a PFR ID.

Actual selection references use canonical PFR IDs when available. The fallback requires an exact normalized player name and raw school name; it does not apply school aliases or fuzzy matching. If those fields do not match exactly and no PFR ID is available, the actual selection stays a separate reference-only row. This can represent the same person twice: once as an eligible invitee and once as an unresolved reference. The scenario contains 83 reference-only rows; unresolved aliases were not merged into the eligible pool.

The 2021 owner sequence is reconstructed by reversing nflverse draft-day transaction rows, with zero unresolved reversal issues and 32 owner franchises. No complete archived pre-draft order comparison is claimed. The NFL.com page published March 19 is excluded as a reliable as-of source because its current body includes a trade dated March 26.
