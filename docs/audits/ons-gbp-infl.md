# Audit — GBP.INFL (folded ons, UK CPIH)

- Date: 2026-07-13
- Series: UK CPIH m/m inflation (`GBP.INFL`, fractions), ONS series `l522`
- Source: folded `okama_macro.sources.ons` (ONS timeseries API), fetched through
  the shared `okama_macro._http` layer (which also gives this source working
  retry — ons's own retry adapter was dead code, mounted on `http://` while the
  API is `https://`).
- Verdict: **PASS**

## Framing

This fold is **behavior-preserving for GBP.INFL**: okama-API's `get_uk_inflation`
already just called `ons.infl.get_inflation_cpih()`; the fold only relocates that
function into okama-macro and swaps its HTTP. So the audit asks the two questions
the spec separates: (1) is the data right? and (2) does the live folded fetch work
through the new `_http` path? The spec pre-labelled the IMF mirror "loose" because
IMF `PCPI_IX` is nominally headline CPI, not CPIH — but in practice (below) the two
track to rounding precision over the full overlap.

## Part 1 — live folded fetch (validates the `_http` + parse swap)

Run 2026-07-13 (laptop reached ons.gov.uk):

| Rows | Range | Last obs | Last value | fractions? |
|---|---|---|---|---|
| 460 | 1988-02-01 → 2026-05-01 | 2026-05-01 | 0.0021 | yes (all `abs < 1`) |

Recent tail: 2026-03 `0.0057`, 2026-04 `0.0071`, 2026-05 `0.0021` (m/m CPIH). The
folded code fetches and parses the ONS `l522` timeseries correctly through `_http`.

Note ons returns **1988→ only**. The prod DB's GBP.INFL depth of 1955→ is a
**separate one-time boe#6 backfill**; the nightly `okama-inflation` upsert rewrites
only the 1988→ months ons returns and leaves 1955–1988 intact (verified post-deploy).

## Part 2 — overlap diff vs IMF CPI GB (`IMF/CPI/M.GB.PCPI_IX` via DBnomics)

- Overlap: **450 months**. **mean abs diff 0.00002**, max abs diff **0.00005**.
- The largest divergences (e.g. 2005-12 ons 0.0037 vs imf 0.00375) are exactly
  ons's 4-decimal rounding (`pct_change().round(4)`) against IMF's more precise
  values — a ±0.00005 rounding band, nothing more. No sign flip, no one-month lag,
  no systematic offset.
- Despite the spec's "CPIH ≠ CPI, expect a basket gap" caveat, the IMF UK series
  tracks the folded CPIH-derived m/m to rounding precision across the entire 1988→
  overlap. This is a **tight** independent confirmation, stronger than the
  anticipated loose proxy.

## Conclusion

The live folded fetch returns correct, current, fraction-scale CPIH inflation; it
matches the independent IMF UK CPI mirror to 4-decimal rounding across 450 months
with no structural discrepancy. **PASS** — proceed to the registry + okama-API
rewire. No prod re-pull required; the 1955 GBP.INFL depth (boe#6 backfill) is
untouched by this behavior-preserving fold.
