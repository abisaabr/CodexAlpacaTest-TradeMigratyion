# GCP Option-Aware Research Queue Status

- Generated at: `2026-04-23T23:19:42.913512-04:00`
- Status: `blocked_missing_option_market_data`
- Smoke unique variants: `160`
- Smoke candidates: `48`
- Queue items: `25`
- Promotion allowed: `False`
- Broker facing: `False`

## Blocker Counts

- `missing_historical_option_bars`: `25`
- `missing_historical_option_trades`: `25`

## Top Follow-Up IDs

- `rq002__gld_base_trend_long_put_next_expiry__profit_target_multiple_0_35__stop_loss_multiple_0_24__hard_exit_minute_360__liquidity_gate_baseline`
- `rq002__gld_base_trend_long_put_next_expiry__profit_target_multiple_0_35__stop_loss_multiple_0_24__hard_exit_minute_360__liquidity_gate_tight`
- `rq002__gld_base_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_18__hard_exit_minute_360__liquidity_gate_baseline`
- `rq002__gld_base_trend_long_put_next_expiry__profit_target_multiple_0_55__stop_loss_multiple_0_18__hard_exit_minute_360__liquidity_gate_baseline`
- `rq002__gld_base_trend_long_put_next_expiry__profit_target_multiple_0_35__stop_loss_multiple_0_3__hard_exit_minute_300__liquidity_gate_baseline`
- `rq002__gld_base_trend_long_put_next_expiry__profit_target_multiple_0_35__stop_loss_multiple_0_3__hard_exit_minute_300__liquidity_gate_tight`
- `rq002__gld_base_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_3__hard_exit_minute_300__liquidity_gate_baseline`
- `rq002__gld_base_trend_long_put_next_expiry__profit_target_multiple_0_45__stop_loss_multiple_0_3__hard_exit_minute_300__liquidity_gate_tight`
- `rq002__gld_base_trend_long_put_next_expiry__profit_target_multiple_0_55__stop_loss_multiple_0_3__hard_exit_minute_300__liquidity_gate_baseline`
- `rq002__gld_base_trend_long_put_next_expiry__profit_target_multiple_0_55__stop_loss_multiple_0_3__hard_exit_minute_300__liquidity_gate_tight`

## Issues

- `warning` `missing_historical_option_bars`: 25 queued follow-up items are blocked by missing_historical_option_bars.
- `warning` `missing_historical_option_trades`: 25 queued follow-up items are blocked by missing_historical_option_trades.

## Next Step Contract

- Keep all smoke candidates out of promotion until option-market-data blockers clear.
- Download bounded historical option bars for representative selected contracts first.
- Add option trades or quote/spread data before fill-cost calibration is trusted.
- Run option-aware entry/exit economics and walk-forward summary before strategy governance review.
