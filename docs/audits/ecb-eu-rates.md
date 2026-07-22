# Audit — EU_MRO.RATE / EU_MLR.RATE / EU_DFR.RATE (folded ecb)

- Date: 2026-07-13
- Series: ECB key rates — main refinancing operations (`EU_MRO.RATE`, MRR_FR),
  marginal lending facility (`EU_MLR.RATE`), deposit facility (`EU_DFR.RATE`),
  all decimal fractions, daily observations.
- Source: folded `okama_macro.sources.ecb` (ECB Statistical Data Warehouse
  data-api, `csvdata`), fetched through the shared `okama_macro._http`.
- Verdict: **PASS** (with one pre-existing data-quality finding flagged, below)

## Framing

This fold is **behavior-preserving**: okama-API's rate cases already called
`ecb.kr.get_refinancing_rate/get_marginal_rate/get_deposit_rate`; the fold only
relocates them and swaps the HTTP. The three series fetch the same ECB SDW codes
as before (`MRR_FR.LEV`, `MLFR.LEV`, `DFR.LEV`).

## Part 1 — live folded fetch (validates the `_http` + parse swap)

Run 2026-07-13 (laptop reached the ECB data-api):

| Series | Rows | Range | Last obs | Last value |
|---|---|---|---|---|
| EU_MRO.RATE | 7025 | 1999-01-01 → 2026-07-13 | 2026-07-13 | 0.0240 (2.40%) |
| EU_MLR.RATE | 10056 | 1999-01-01 → 2026-07-13 | 2026-07-13 | 0.0265 (2.65%) |
| EU_DFR.RATE | 10056 | 1999-01-01 → 2026-07-13 | 2026-07-13 | 0.0225 (2.25%) |

- All fraction-scale (`abs < 1`).
- **Corridor ordering holds: MLR (2.65%) ≥ MRO (2.40%) ≥ DFR (2.25%)** — a strong
  internal consistency check; the three form the ECB interest-rate corridor, and
  the 25bp (MLR−MRO) / 15bp (MRO−DFR) spreads match the ECB's post-Sept-2024
  narrowed-corridor structure.

## Part 2 — current-value spot-check vs ECB published (primary)

Independent public confirmation (ECB / Euronews, decision effective 2026-06-17):
DFR **2.25%**, MRO **2.40%**, MLR **2.65%**. The folded series' last values match
**all three exactly**.

## Part 3 — EU_MRO vs BIS `WS_CBPOL/D.XM` overlap diff

- Overlap 9654 obs (1999 → 2025-07). Full mean abs diff 0.00388; but split at the
  regime boundary: **post-2008 mean abs diff ≈ 0.00010** (near-perfect), with the
  entire divergence concentrated in **2000–2008** (yearly mean peaking ~0.0225 in
  2003–2005). No sign flip.
- DFR vs BIS post-2015 mean 0.00406 — i.e. BIS `XM` tracks the **MRO**, and DFR
  sits ~a corridor-width below it, as expected. The recent MRO match to BIS
  (0.0001) validates the modern data end-to-end.

## Finding (pre-existing, flagged — NOT a fold regression, NOT a blocker)

**EU_MRO.RATE for ~2001–2008 is the ECB fixed-rate MRO (`MRR_FR`), which was
frozen at 4.25% during the variable-rate-tender era (mid-2000 → Oct-2008), while
the ECB's operative policy rate then was the lower *minimum bid rate* (~2.00% in
2003–2005).** Concretely: on 2004-06-15 the folded series (and **prod**, verified
`EU_MRO.RATE`=0.0425 on that date) shows 4.25%, whereas BIS's euro-area policy
rate shows 2.00% — a ~2.25pp gap. From Oct-2008 (fixed-rate full-allotment
resumed) onward the series and BIS agree to the basis point.

This is a **characteristic of which ECB series `MRR_FR` is** (the fixed rate), not
corruption introduced by this fold — prod has served exactly these values since
long before the consolidation (behavior-preserving, confirmed against the prod
DB). It is worth a **separate follow-up**: for 2000–2008 the "main refinancing
rate" arguably should be the minimum bid rate (`MRR_MBR`) or a splice, not the
frozen fixed rate. Out of scope for the #41 consolidation (which must not change
behavior); recorded here and surfaced to the user for a possible data-quality fix.

## Conclusion

Live folded fetch returns correct, current, corridor-consistent data; all three
current values match ECB published rates exactly; the modern MRO history matches
BIS to the basis point. The only divergence is the pre-existing 2000–2008
fixed-rate-MRO quirk, which the fold preserves (does not introduce) and which is
flagged for a separate follow-up. **PASS** — proceed to the registry + okama-API
rewire. No fold-caused corruption; no prod re-pull required for this fold.

## Follow-up resolved — 2026-07-22 (okama-API#53)

The finding above is fixed. `kr.get_refinancing_rate` now **splices** the two ECB
series instead of serving `MRR_FR` alone:

- `MRR_FR.LEV` outside the variable-rate tender era — it simply has **no
  observations** between 2000-06-28 and 2008-10-14 (verified against the live
  data-api: 0 rows in that window), which is why the monthly resample downstream
  forward-filled 4.25% for eight years;
- `MRR_MBR.LEV` (minimum bid rate) inside it — published exactly 2000-06-28 →
  2008-10-14, 3031 daily observations, 12 distinct levels.

`VARIABLE_TENDER_START`/`VARIABLE_TENDER_END` in `sources/ecb/kr.py` bound the
window; the `MRR_MBR` request is skipped entirely when the requested window does
not touch it (a pipeline refresh starts at the last stored date). `get_min_bid_rate`
is exported for direct use. `request_data.get_data_frame` now tolerates the empty
200-response the ECB returns outside a series' range (it used to raise
`EmptyDataError`).

Validation of the spliced series:

- 22 rate changes over 2000-06 → 2008-12 where there were none, matching the ECB's
  published MRO history (2001-05-11 → 4.50, 2001-09-18 → 3.75, 2003-06-06 → 2.00,
  2005-12-06 → 2.25, 2008-07-09 → 4.25, 2008-10-15 → 3.75).
- **BIS `WS_CBPOL/D.XM` overlap over the whole variable-tender window: 3031 days,
  max absolute difference 0.0 pp** (was ~2.25 pp at its worst). The 2000–2008
  divergence flagged in Part 3 is gone.
