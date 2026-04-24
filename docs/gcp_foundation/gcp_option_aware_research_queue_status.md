# GCP Option-Aware Research Queue Status

- Generated at: `2026-04-24T00:43:48.316399-04:00`
- Status: `blocked_missing_option_market_data`
- Smoke unique variants: `1242`
- Smoke candidates: `218`
- Queue items: `50`
- Promotion allowed: `False`
- Broker facing: `False`

## Blocker Counts

- `missing_selected_option_contracts`: `50`

## Top Follow-Up IDs

- `rq002__slv_base_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_18__hard_exit_minute_300__liquidity_gate_baseline`
- `rq002__slv_fast_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_18__hard_exit_minute_300__liquidity_gate_baseline`
- `rq002__slv_base_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_18__hard_exit_minute_360__liquidity_gate_baseline`
- `rq002__slv_base_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_18__hard_exit_minute_360__liquidity_gate_tight`
- `rq002__slv_fast_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_18__hard_exit_minute_360__liquidity_gate_baseline`
- `rq002__slv_fast_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_18__hard_exit_minute_360__liquidity_gate_tight`
- `rq002__slv_base_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_24__hard_exit_minute_300__liquidity_gate_baseline`
- `rq002__slv_fast_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_24__hard_exit_minute_300__liquidity_gate_baseline`
- `rq002__slv_base_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_24__hard_exit_minute_360__liquidity_gate_baseline`
- `rq002__slv_base_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_24__hard_exit_minute_360__liquidity_gate_tight`

## Issues

- `warning` `missing_selected_option_contracts`: 50 queued follow-up items are blocked by missing_selected_option_contracts.

## Next Step Contract

- Keep all smoke candidates out of promotion until option-market-data blockers clear.
- Download bounded historical option bars for representative selected contracts first.
- Add option trades or quote/spread data before fill-cost calibration is trusted.
- Run option-aware entry/exit economics and walk-forward summary before strategy governance review.
