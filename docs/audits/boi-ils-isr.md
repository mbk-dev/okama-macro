# Audit — ILS.INFL / ISR_IR.RATE (folded boi)

- Date: 2026-07-13
- Series: Israel CPI m/m inflation (`ILS.INFL`, fractions) and Bank of Israel
  policy rate (`ISR_IR.RATE`, fractions, daily observations)
- Source: folded `okama_macro.sources.boi` (Bank of Israel SDMX, edge.boi.gov.il),
  fetched through the shared `okama_macro._http` layer (which also gives this
  source working retry for the first time — boi's own retry adapter was dead code).
- Verdict: **PASS** (both series)

## Why boi got the fullest gate

boi is the fold the consolidation plan flagged specifically for the IMF/BIS
overlap audit (the BOE look-ahead incident motivated auditing every micro-repo).
Both consumed series have a **direct** independent mirror, so this is a genuine
full-history overlap diff — the real BOE-style corruption check — not a
spot-check.

## Prod baseline (step 0)

Both series are current in prod as of 2026-07-13 (`ILS.INFL` max_date 2026-05-01
/ 896 rows; `ISR_IR.RATE` max_date 2026-07-13 / 11856 rows). So standalone boi
runs on prod pandas 3.x — the SDMX endpoint and the `pd.read_xml` parse (left
byte-identical across the fold) are healthy, and the stored series are the
comparison target.

## Live folded fetch (validates the `_http` + parse swap)

boi is **not** byte-identical to the deployed standalone (its HTTP was rewritten),
so the live fetch through the new path is what validates it. Run 2026-07-13
(laptop reached edge.boi.gov.il; no server fallback needed):

| Series | Type | Rows (from 2015) | Last obs | Last value | fractions? |
|---|---|---|---|---|---|
| ILS.INFL | Series | 136 | 2026-05 | -0.0029 | yes |
| ISR_IR.RATE | Series | 4212 | 2026-07-13 | 0.035 | yes |

Both return the correct shape (the SDMX multi-column payload squeezes to a Series
as the consumed functions expect), fraction scale, and recent dates matching prod.

## Part 1 — ILS.INFL vs IMF CPI IL (`IMF/CPI/M.IL.PCPI_IX` via DBnomics)

- Overlap: **426 months**. **mean abs diff 0.00072**, max abs diff 0.00560.
- The five largest divergences are all in **1990–1993** (Israel's high-inflation
  era, ~18%/yr), where a monthly print of ~1.8% vs ~1.3% differs by basket and
  rounding. They **alternate sign** (boi higher some months, IMF higher others) —
  no systematic offset, no sign flip, no one-month lag. The modern period (where
  okama actually uses the series) tracks tightly.
- Mean is below the 0.001 tracking threshold; the early-90s spread is
  basket-difference noise, not the BOE class (which was a systematic ~0.49pp
  offset across the whole history). **PASS.**

## Part 2 — ISR_IR.RATE vs BIS `WS_CBPOL/D.IL` (folded `bis.get_policy_rate('IL')`)

- BIS IL: 11688 obs, 1993-07 → 2025-06. Overlap after forward-filling the boi
  daily series to BIS observation dates: **11478 obs**.
- **mean abs diff 0.00000**, max abs diff 0.00250. The single non-zero
  divergence is **one date, 2010-09-30** (boi 1.75% vs BIS 2.00%) — a rate-change
  transition-day boundary effect (the two sources stamp the effective date one
  step apart), not systematic. Otherwise the two agree to the basis point across
  32 years of daily data.
- Near-perfect agreement with the independent central-bank-policy-rate mirror.
  **PASS.**

## Conclusion

Live folded fetch returns correct, current, correctly-scaled data for both
series; ILS.INFL tracks IMF CPI (mean 0.00072, only early-90s basket noise);
ISR_IR.RATE matches BIS to the basis point (mean 0.00000). No systematic offset,
sign flip, lag, or stored-data corruption. **PASS** — proceed to the registry +
okama-API rewire. No prod re-pull required.
