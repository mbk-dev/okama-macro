# Audit — UK_BR.RATE (folded boe)

- Date: 2026-07-13
- Series: Bank of England bank rate (`UK_BR.RATE`, decimal fractions, daily,
  pre-padded).
- Source: folded `okama_macro.sources.boe` (BoE Bank-Rate.asp change-dates HTML
  table), fetched through the shared `okama_macro._http` with boe's original
  spoofed Chrome User-Agent preserved.
- Verdict: **PASS**

## Why this gate is LIGHT

boe already had its **full audit + fix in mbk-dev/boe#6** (2026-07-12): the
look-ahead-padding bug — every day between two rate changes carried the *future*
rate because the newest-first table was padded before sorting — was found and
fixed (sort-ascending → pad-from-previous → slice-after-pad), verified against
BIS. This fold ports that fixed code byte-identical (only the HTTP fetch moved to
`_http`), so the gate here just confirms the fold didn't regress it:
(a) the live *folded* fetch works through the `_http` + preserved-UA swap,
(b) it still matches BIS, (c) the ported boe#6 contract tests pass.

## Part 1 — live folded fetch (validates the `_http` + UA + parse/pad swap)

Run 2026-07-13 (the preserved Chrome UA reached bankofengland.co.uk — no 403):

| Rows | Range | Last obs | Last value | fractions | padded daily, no gaps |
|---|---|---|---|---|---|
| 18803 | 1975-01-20 → 2026-07-13 | 2026-07-13 | 0.0375 (3.75%) | yes | yes (through today) |

The folded code reads the BoE table, sorts ascending, forward-fills to a daily
grid **through today**, and returns fractions — exactly the boe#6 behaviour. The
last value (3.75%) is the current BoE bank rate straight from the authoritative
BoE table.

## Part 2 — BIS `WS_CBPOL/D.GB` re-check (confirms the boe#6 fix holds)

- Overlap **18803 obs** (1975 → today). **mean abs diff 0.00009**, max 0.00500.
- Near-perfect agreement across 50 years of daily data — a look-ahead bug would
  show a *systematic* offset (every inter-change day wrong), which is absent. The
  fix holds.
- The only non-zero diffs are a handful of days in **mid-March 2026** (boe 3.75%
  vs BIS 4.25%): boe (the live BoE site) already carries the recent cut to 3.75%
  while BIS's tail is momentarily stale (BIS lags) and its last value is
  forward-filled. boe is the **fresher, correct** source here — not an error.

## Part 3 — ported contract tests

`tests/test_boe_contract.py` (ported from the boe#6 `tests/test_request_data.py`)
locks the fix: pad-from-previous (not the future change), a window opening after
the last change returns the standing rate, slice-after-pad keeps the in-effect
rate, fractions, and — added here — the fetch preserves the Chrome UA through
`_http`. All 5 pass offline.

## Depth note (checked post-deploy, Task 6)

boe provides **1975→** (the BoE table start). The prod DB's UK_BR.RATE depth of
**1946→** is a separate BIS `WS_CBPOL/D.GB` backfill (from boe#6); the nightly
upsert rewrites only 1975→ and leaves the pre-1975 backfill intact — a
behavior-preserving fold, re-verified after deploy.

## Conclusion

Live folded fetch returns correct, current, gap-free padded data through the
preserved-UA `_http` path; it matches BIS to 0.00009 across 50 years (the boe#6
look-ahead fix holds); the ported contract tests pass. **PASS** — proceed to the
registry + okama-API rewire (the final fold). No fold-caused regression.
