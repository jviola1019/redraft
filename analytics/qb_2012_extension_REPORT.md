# 2012 QB snap source availability check

Checked 2026-11-12. The nflreadr loader documents snap-count retrieval starting with the 2012 season (`https://github.com/nflverse/nflreadr/blob/main/R/load_snap_counts.R`). That establishes loader support, but not that the release contains observations for every supported year.

I fetched the exact official release URL used by `research/ingest.py`: `https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2012.csv`. The request returned HTTP 200 at 2026-11-12T20:31:21Z. The body is 154 bytes, consists only of the CSV header, and has zero data rows. The fresh response SHA-256 is `802475aec59f0b125de85a6c35eb69e289a512bcf62d6be007d385ea8d613ebd`; it matches the existing raw snapshot and its source-manifest checksum.

## Conclusion

The 2012 release cannot contribute QB annual snap outcomes. Consequently, adding the 2012 draft class does not extend the five-year donor pool: the first complete pre-2018 cohort remains 2013, and a 2012–2016 QB trajectory cannot be constructed from this source. This is an observation-availability limit, distinct from nflreadr's year-range support. No model, runtime file, or raw input was changed. No 2012 extension script or model comparison was run because there are no rows to model.

The existing strict analysis still has one pre-2018 donor cohort; this check neither validates wider QB uncertainty nor supports changing the interval width. A different, independently sourced outcome measure would need its own target definition and validation before it could be combined with snap counts.
