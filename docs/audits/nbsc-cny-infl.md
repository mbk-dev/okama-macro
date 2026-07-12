# Audit — CNY.INFL (folded nbsc) vs independent mirror

**Verdict: PASS** (2026-07-12). The folded `nbsc.get_recent_inflation` m/m
inflation fractions track an independent mirror closely; no bug signature.

## Method

- **Library side:** `nbsc.get_recent_inflation("2016")` (run on secondvds — the
  NBS China API `data.stats.gov.cn` is only reachable from the server; it times
  out from the laptop). The folded package is byte-identical to the deployed
  standalone `nbsc` (Phase-3 T2 changed only import paths, not logic), so the
  server result is valid for the fold. Output: m/m fractions, 2021-01 → 2026-05
  (65 months).
- **Mirror:** IMF monthly China CPI index `IMF/CPI/M.CN.PCPI_IX` via DBnomics,
  converted to m/m via `pct_change()`.
- **Overlap diff** on the common months.

## Result

| metric | value |
|---|---|
| overlap months | 55 (2021-01 … 2025-07) |
| mean abs diff | **0.00042** (≈0.04 pp/month) |
| max abs diff | 0.00207 (≈0.2 pp) |
| correlation | **0.9847** |

Top divergences are ~0.001–0.002, scattered, no systematic offset / sign flip /
one-month lag. `nbsc` rounds m/m to 0.001 granularity while IMF carries full
precision (e.g. 2025-01: nbsc 0.007 vs IMF 0.00583), which accounts for most of
the residual. This is basket/rounding noise between two independent CPI sources,
**not** a parsing bug. (For contrast, the BOE look-ahead bug showed a systematic
~0.49 pp mean offset — ~1000× larger.)

The 55-month overlap against IMF is itself the independent-value spot-check en
masse; no separate hand-picked values were invented (they could not be
independently verified here).

## Contract tests

Locked separately in `tests/test_nbsc_contract.py` (m/m fractions not index,
ascending monotonic index, the NBS not-published-0 guard) — the universal
boe#6-template checks that catch the look-ahead class regardless of mirror.
