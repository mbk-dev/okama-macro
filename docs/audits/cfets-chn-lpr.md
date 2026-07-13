# Audit — CHN_LPR1.RATE / CHN_LPR5.RATE (folded cfets)

- Date: 2026-07-13
- Series: China Loan Prime Rate, 1-year and 5-year, m/m-cadence, decimal fractions
- Source: folded `okama_macro.sources.cfets` (chinamoney.com.cn `LprChrtCSV`),
  fetched through the shared `okama_macro._http` layer (retry/back-off) with the
  source's original spoofed Chrome User-Agent preserved.
- Verdict: **PASS**

## Why the gate is lighter than a rate with a BIS mirror

The Loan Prime Rate is **not** a central-bank policy rate — BIS `WS_CBPOL/D.CN`
publishes China's policy (OMO / 7-day reverse-repo) rate, a different series — so
there is no directly-comparable full-history mirror. A DBnomics search
(`China loan prime rate`, `Loan Prime Rate LPR China`, `China LPR 1 year`)
returned **0 hits**. Per the Phase-3 spec, cfets therefore rests on (a) a live
folded-fetch check, (b) a spot-check against publicly documented PBoC fixings,
and (c) the universal contract tests — not an overlap diff.

## Part (a) — live folded fetch (the cfets-specific hard gate)

cfets is **not** byte-identical to the deployed standalone (its HTTP was
rewritten onto `_http`), so the live fetch through the new path is what
validates the swap + UA. Run 2026-07-13 from the laptop (the site was reachable;
no server fallback needed):

| Series | Rows | Range | Last obs | Last value |
|---|---|---|---|---|
| lpr1y | 153 | 2013-10-31 → 2026-06-22 | 2026-06-22 | 0.03 (3.00%) |
| lpr5y | 83 | 2019-08-30 → 2026-06-22 | 2026-06-22 | 0.035 (3.50%) |

- All values are fraction-scale (`abs < 1`): **True**.
- 1Y < 5Y across the series: **True**.
- Structural sanity: the 5Y LPR series begins **2019-08**, matching the August
  2019 LPR reform that introduced the 5-year tenor; the 1Y history runs from
  2013, matching the original LPR launch. Both consistent with the published
  history.

The fetch succeeded through the preserved Chrome UA — no 403/block — so the
`_http` + UA swap does not regress the live path.

## Part (b) — spot-check vs public PBoC figures

The CSV's dates are the fixing-effective dates (month-end style), not the
20th-of-month announcement dates, so the check is on the current standing level
rather than exact announcement rows. Independent public sources (fetched
2026-07-13):

- Current 1-year LPR **3.00%**, 5-year LPR **3.50%**, unchanged since May 2025 —
  CNBC (2026-01-20; 2026-04-20) and english.www.gov.cn (2026-05-20).

Folded series last values: 1Y **0.03 (3.00%)**, 5Y **0.035 (3.50%)** — **exact
match**. The series is flat at these levels through the recent tail, consistent
with "unchanged since May 2025".

## Part (c) — contract tests

`tests/test_cfets_contract.py` (boe#6 template) locks: fractions not percent
(`abs < 1`), observations-only (two raw rows → two observations, no padding),
and the fetch preserves the original Chrome User-Agent through `_http`. All 4
pass offline (network seam mocked).

## Conclusion

Live folded fetch returns recent, correctly-scaled, structurally-sound data;
the current level matches independent public sources exactly; contract tests
lock the parse and the UA. **PASS** — proceed to the registry + okama-API rewire.
No source-data corruption found; no prod re-pull required.
