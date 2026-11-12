# Additional NFL order source review

Checked 2026-11-12. Parsed owner sequences are in `additional_order_sources.json`; `analytics/additional_order_sources.py` reproduces them from ignored `data/raw/nfl_draft_order_YEAR_webtext.txt` captures. These captures are verbatim text returned by web extraction, not original HTTP bytes. Their hashes and URLs are recorded. No runtime files were changed.

## Order-source readiness

| Draft | Expected picks | Source date / cutoff | Readiness |
|---:|---:|---|---|
| 2020 | 255 | Titans PDF released Apr 16; complete order explicitly as of Apr 15 | Usable |
| 2021 | 259 | NFL.com published Mar 19; no modified date or explicit as-of | Blocked |
| 2022 | 262 | NFL.com published Mar 16; editor says order entering Day 1 | Usable |
| 2023 | 259 | NFL.com Published/Updated fields blank; states accurate as of beginning of Round 1 | Usable with missing publication metadata |
| 2024 | 257 | Published Mar 8, updated Apr 25 8:13 PM ET; states accurate as of beginning of Round 1 (8:00 PM ET) | Usable for stated cutoff |

2021 is blocked because its current page body cannot be tied to the March 19 publication snapshot. The page assigns pick No. 3 to San Francisco, but the official 49ers announcement dates that trade from Miami to March 26. There is no exposed modified timestamp or order-as-of statement. The 259 extracted rows are retained for audit but marked `usableForPreDraftOwnership: false`.

The four usable pages parse to the expected complete overall sequences. Their source owner differs from the eventual drafting team at 76 picks in 2020, 95 in 2022, 104 in 2023 and 83 in 2024. These are documented in JSON as owner-sequence differences against the actual draft-pick table, with overall pick and both team IDs. They should be treated as post-cutoff transfers when scenario logic needs the original holder.

## 2021 combine invitees

An official New York Giants reprint of the league's invitee list was published March 4, 2021 at 9:09 AM. It states 323 invitees and lists them by school with player names and positions. The cached source text is hashed in JSON. The recovered 2021 `combine.csv` has 464 rows. Exact normalized player-name plus school matching yields **182 unique measurement matches**, **141 invitees with no matching measurement row**, and **0 ambiguous matches**. No school aliases or fuzzy matches are applied. The artifact emits all 323 official invitees as eligible; each has a nullable `measurementMatch`. A PFR ID is optional and does not determine eligibility. The 141 unmatched prospects retain null measurements.

## Reproduction

```sh
python analytics/additional_order_sources.py
```
