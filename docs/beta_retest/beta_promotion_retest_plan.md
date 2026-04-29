# Beta Promotion Retest Plan

Created: 2026-04-29T14:18:38 local time. Absolute date context: April 29, 2026.

No trading, broker-facing paper session, live-manifest change, runtime exception widening, or infrastructure creation was performed for this packet.

## Canonical State

- Runner repo used: `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner HEAD: `91ce125adb33003a1d999ccd74958eec60b9556d`
- `origin/codex/qqq-paper-portfolio`: `91ce125adb33003a1d999ccd74958eec60b9556d`
- Commit `91ce125` confirmed in origin branch: `true`
- Beta manifest: `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed\config\promotion_manifests\multi_ticker_portfolio_beta_promotions.yaml`
- Live manifest: `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed\config\strategy_manifests\multi_ticker_portfolio_live.yaml`
- Builder script: `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed\scripts\build_beta_promotion_manifest.py`
- Stale runner folder excluded: `C:\Users\abisa\Downloads\codexalpaca_repo`
- Control-plane repo used: `C:\Users\abisa\Downloads\CodexAlpacaTest-TradeMigratyion_gcp_lease_lane` on `main` tracking `origin/main`

## Counts

- Exact live strategies: 94
- Exact promoted/beta retest families: 6
- Retest-gap symbols: 29
- Families with retest gaps: 5
- Exact live underlyings: 21

Retest-gap symbols: `AAPL, ABBV, ADBE, AMD, AMZN, ARM, ASTS, AVGO, BA, BABA, CRWV, DAL, DIS, GME, GOOG, HIMS, IONQ, IREN, IWM, OXY, QCOM, RKLB, SMCI, SNDK, SPY, TTD, UPRO, URA, WULF`

## Retest Set Split

Exact live retest set: 94 checked-in live strategies from `exact_live_strategies`. Retest these exactly as listed in `config/promotion_manifests/multi_ticker_portfolio_beta_promotions.yaml` and `config/strategy_manifests/multi_ticker_portfolio_live.yaml`.

Promoted beta retest set: 6 promoted families from governance scope. These belong in beta retest because the family/ticker appears in governance artifacts, but not every promoted ticker is fully represented in the live manifest.

Promoted beta retest superset set: 5 families have `exact_promoted_base_strategies_available=false`: `Iron butterfly, Long straddle, Put backspread, Single-leg long call, Single-leg long put`. For these, the exact historical promoted subset was not preserved, so the listed `base_strategies` are a governed retest superset for the listed `promoted_tickers`.

Families with exact promoted base-strategy subsets preserved: `Call backspread`

## Family Matrix

| Family | Priority | Steward action | Promoted tickers | Live-manifest tickers | Retest-gap tickers | Exact subset preserved | Reconstruction mode |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| Call backspread | live_benchmark | benchmark_against_current_live_book | 1 | 1 | 0 | true | exact_promoted_subset |
| Iron butterfly | live_benchmark | benchmark_against_current_live_book | 5 | 1 | 4 | false | governed_retest_superset |
| Long straddle | promotion_follow_up | review_for_live_manifest_addition | 1 | 0 | 1 | false | governed_retest_superset |
| Put backspread | promotion_follow_up | review_for_live_manifest_addition | 6 | 0 | 6 | false | governed_retest_superset |
| Single-leg long call | live_benchmark | benchmark_against_current_live_book | 38 | 21 | 17 | false | governed_retest_superset |
| Single-leg long put | live_benchmark | benchmark_against_current_live_book | 44 | 20 | 24 | false | governed_retest_superset |

## Family Rationale

### Call backspread

- Priority: `live_benchmark`
- Steward action: `benchmark_against_current_live_book`
- Promoted tickers: `QQQ`
- Live-manifest tickers: `QQQ`
- Retest-gap tickers: `none`
- Exact promoted base-strategy subset preserved: `true`
- Reconstruction mode: `exact_promoted_subset`
- Present in exact_live_strategies and live_manifest_tickers, so it is part of the highest-confidence exact live retest set.
- priority=live_benchmark and steward_action=benchmark_against_current_live_book require benchmarking against the current live book rather than broad activation.
- exact_promoted_base_strategies_available=true, so its listed base_strategies can be retested as the preserved promoted subset.

### Iron butterfly

- Priority: `live_benchmark`
- Steward action: `benchmark_against_current_live_book`
- Promoted tickers: `AAPL, AMZN, IWM, QQQ, SPY`
- Live-manifest tickers: `QQQ`
- Retest-gap tickers: `AAPL, AMZN, IWM, SPY`
- Exact promoted base-strategy subset preserved: `false`
- Reconstruction mode: `governed_retest_superset`
- Present in the exact live manifest for QQQ, so the live QQQ entries belong in the exact live benchmark set.
- promoted_tickers exceed live_manifest_tickers; AAPL, AMZN, IWM, and SPY are retest-gap tickers that require beta retest before any live-manifest addition.
- exact_promoted_base_strategies_available=false, so the historical promoted subset was not preserved and the listed base_strategies must be treated as a governed retest superset.

### Long straddle

- Priority: `promotion_follow_up`
- Steward action: `review_for_live_manifest_addition`
- Promoted tickers: `AAPL`
- Live-manifest tickers: `none`
- Retest-gap tickers: `AAPL`
- Exact promoted base-strategy subset preserved: `false`
- Reconstruction mode: `governed_retest_superset`
- Family appears in governance beta_retest_families with priority=promotion_follow_up and steward_action=review_for_live_manifest_addition.
- It has promoted_tickers but no live_manifest_tickers, so AAPL is a beta retest gap rather than an exact live strategy.
- exact_promoted_base_strategies_available=false, so retest must use the governed superset and must not claim exact historical promoted names.

### Put backspread

- Priority: `promotion_follow_up`
- Steward action: `review_for_live_manifest_addition`
- Promoted tickers: `AAPL, ABBV, ADBE, AMD, AMZN, ARM`
- Live-manifest tickers: `none`
- Retest-gap tickers: `AAPL, ABBV, ADBE, AMD, AMZN, ARM`
- Exact promoted base-strategy subset preserved: `false`
- Reconstruction mode: `governed_retest_superset`
- Family appears in governance beta_retest_families with priority=promotion_follow_up and steward_action=review_for_live_manifest_addition.
- It has promoted_tickers but no live_manifest_tickers, so all listed tickers are beta retest gaps.
- exact_promoted_base_strategies_available=false, so AAPL/ABBV/ADBE/AMD/AMZN/ARM must be retested as base_strategies x promoted_tickers governed superset.

### Single-leg long call

- Priority: `live_benchmark`
- Steward action: `benchmark_against_current_live_book`
- Promoted tickers: `AMZN, ARKK, ARM, ASTS, BAC, CRM, CRWV, DAL, DIS, GDX, GLD, GME, GOOG, HIMS, IONQ, IREN, IWM, JPM, MSFT, NKE, NVDA, ORCL, PLTR, QCOM, QQQ, RKLB, SCHW, SHOP, SLV, SMCI, SNDK, SPY, TSLA, TTD, UPRO, URA, XLE, XOM`
- Live-manifest tickers: `AMZN, ARKK, BAC, CRM, GDX, GLD, IWM, JPM, MSFT, NKE, NVDA, ORCL, PLTR, QQQ, SCHW, SHOP, SLV, SPY, TSLA, XLE, XOM`
- Retest-gap tickers: `ARM, ASTS, CRWV, DAL, DIS, GME, GOOG, HIMS, IONQ, IREN, QCOM, RKLB, SMCI, SNDK, TTD, UPRO, URA`
- Exact promoted base-strategy subset preserved: `false`
- Reconstruction mode: `governed_retest_superset`
- Large exact live representation makes this a core benchmark family for the current live book.
- promoted_ticker_count exceeds live_manifest_ticker_count, creating a retest gap for additional promoted-scope tickers.
- exact_promoted_base_strategies_available=false, so non-live promoted-scope reconstruction is governed superset only.

### Single-leg long put

- Priority: `live_benchmark`
- Steward action: `benchmark_against_current_live_book`
- Promoted tickers: `AAPL, ABBV, ADBE, AMD, AMZN, ARKK, ARM, ASTS, AVGO, BA, BABA, BAC, CRM, CRWV, DAL, DIS, GDX, GLD, GME, GOOG, HIMS, IONQ, IREN, IWM, JPM, MSFT, NKE, NVDA, ORCL, OXY, PLTR, QQQ, RKLB, SCHW, SHOP, SLV, SMCI, SPY, TSLA, TTD, UPRO, URA, WULF, XLE`
- Live-manifest tickers: `AMZN, ARKK, BAC, CRM, GDX, GLD, IWM, JPM, MSFT, NKE, NVDA, ORCL, PLTR, QQQ, SCHW, SHOP, SLV, SPY, TSLA, XLE`
- Retest-gap tickers: `AAPL, ABBV, ADBE, AMD, ARM, ASTS, AVGO, BA, BABA, CRWV, DAL, DIS, GME, GOOG, HIMS, IONQ, IREN, OXY, RKLB, SMCI, TTD, UPRO, URA, WULF`
- Exact promoted base-strategy subset preserved: `false`
- Reconstruction mode: `governed_retest_superset`
- Large exact live representation makes this a core benchmark family for the current live book.
- promoted_ticker_count exceeds live_manifest_ticker_count, creating the largest retest-gap scope among the families.
- exact_promoted_base_strategies_available=false, so non-live promoted-scope reconstruction is governed superset only.

## Reconstruction Rules

- Retest `exact_live_strategies` exactly as listed; this is the highest-confidence promoted set because it is present in the checked-in live manifest.
- If `exact_promoted_base_strategies_available=true`, the listed `base_strategies` are the preserved exact promoted base-strategy subset for reconstruction.
- If `exact_promoted_base_strategies_available=false`, the exact historical promoted subset is not recoverable from current artifacts. Use `base_strategies x promoted_tickers` only as a governed retest superset.
- Do not claim a governed superset is an exact historical promotion. Fresh trusted replay evidence must narrow, validate, or reject it before any live-manifest change.
- Promotion interpretation remains governed by the current policy docs: trusted validation, after-cost economics, repeatability, loser-trade review, and portfolio-context behavior are required before promote; otherwise hold, quarantine, or kill.

## Offline Retest Status

No offline retests were run in this pass.

Reason: priority beta-gap retests require local selected-contract roots plus option bars/trades/stock bars for AAPL, ABBV, ADBE, AMD, AMZN, ARM, IWM, and SPY. The current local runner checkout has strong QQQ option data, but not a complete trusted local option replay input set for those priority gap tickers. Prior `top10_replay_fixed_03bfc25` outputs are excluded because the current handoff marks them invalid for promotion due `no_source_stock_trades`.

Observed usable local QQQ inputs:

- `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed\data\raw\historical\qqq_365d_next_trading_day_5x5_option_bars_20250429_20260428`
- `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed\reports\research_wave\qqq_365d_next_trading_day_5x5_20260428\dense_universe\selected_option_contracts`
- `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed\data\raw\historical\qqq_365d_stock_ref_20250429_20260428`

Representative QQQ exact-live sanity retest was also not run because this pass did not find a manifest-compatible offline replay input mapping for the exact live strategy names. Running adjacent research variant IDs would blur exact-live versus governed-superset semantics.

## Rerun Recipe

Priority order:

1. Put backspread governed superset: `base_strategies x AAPL/ABBV/ADBE/AMD/AMZN/ARM`.
2. Long straddle governed superset: `base_strategies x AAPL`.
3. Iron butterfly governed superset: `base_strategies x AAPL/AMZN/IWM/SPY`.
4. Representative exact-live sanity: QQQ exact live strategy names only, once exact-live replay mapping exists.

Required inputs:

- Stock bars covering the retest window for each promoted ticker.
- Selected option contracts generated from the same strategy universe for each promoted ticker/date.
- Option bars covering selected contracts.
- Option trades root, or an explicit trusted empty-trades fallback supported by the replay harness.
- Strategy queue/variants file preserving exact-live names or explicitly marking governed-superset reconstruction.
- Promotion gates preserving fill coverage >= 0.90 and current risk policy.

Output requirement: aggregate portfolio reports into a promotion-review packet and keep any live-manifest change as a separate governed decision.

## Verification

- `beta_promotion_retest_plan.json` parsed successfully with `python -m json.tool`.
- Runner manifest-builder tests passed with the repo-local venv: `python -m pytest tests/test_build_beta_promotion_manifest.py` returned `2 passed`.
- Generated packet files are ASCII-only.

## Source Artifacts

- Runner beta manifest: `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed\config\promotion_manifests\multi_ticker_portfolio_beta_promotions.yaml`
- Runner live manifest: `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed\config\strategy_manifests\multi_ticker_portfolio_live.yaml`
- Runner builder script: `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed\scripts\build_beta_promotion_manifest.py`
- Control-plane policy docs: `docs/PROJECT_TARGET_OPERATING_MODEL.md`, `docs/STRATEGY_PROMOTION_POLICY.md`, `docs/LOSER_TRADE_LEARNING_POLICY.md`, `docs/STRATEGY_REPO_OPERATING_MODEL.md`, `docs/gcp_foundation/research_strategy_governance_handoff.md`, `docs/strategy_family_registry/strategy_family_registry.json`, `docs/strategy_family_registry/strategy_family_registry.md`
- Full machine-readable plan: `docs/beta_retest/beta_promotion_retest_plan.json`
