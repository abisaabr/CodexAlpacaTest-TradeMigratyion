# RS Hardening Input Digest

## Exact files

- `C:\Users\rabisaab\Downloads\master_strategy_memo.txt`: opened successfully
- `C:\Users\rabisaab\Downloads\tournament_master_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\monday_paper_plan.md`: opened successfully
- `C:\Users\rabisaab\Downloads\next_edge_research_ranking.md`: opened successfully
- `C:\Users\rabisaab\Downloads\next_edge_action_plan.md`: opened successfully
- `C:\Users\rabisaab\Downloads\truth_test_elimination_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\concentration_portability_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\edge_survival_scorecard.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_deployment_decision.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_next_action_plan.md`: opened successfully
- `C:\Users\rabisaab\Downloads\best_day_dependence_report.md`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_wrapper_metrics.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_edge_quality_scorecard.csv`: opened successfully
- `C:\Users\rabisaab\Downloads\rs_stability_report.md`: opened successfully

## Exact implementations under test

- Primary RS implementation: `relative_strength_vs_benchmark` with params `{"excess_return_threshold": 0.05, "holding_bars": 20, "lookback_window": 60, "profit_target_pct": 0.0, "use_profit_target": false}` on the prior 9-symbol user subset daily engine.
- Challenger implementation: `cross_sectional_momentum` with params `{"holding_bars": 20, "lookback_window": 60, "profit_target_pct": 0.0, "rank_cutoff": 0.2, "use_profit_target": false}` on the same daily engine and symbol subset.
- Control implementation: `down_streak_exhaustion` with params `{"holding_bars": 5, "profit_target_pct": 0.0, "rsi_cap": 30, "streak_length": 4, "use_profit_target": false}` on the same daily engine and symbol subset.

## Prior baseline reports reused

- `rs_deployment_decision.md` and `rs_next_action_plan.md` for the narrowed disciplined sleeve interpretation.
- `best_day_dependence_report.md` for the prior finding that RS and CSM survive a light haircut but fail a hard one.
- `rs_wrapper_metrics.csv`, `rs_edge_quality_scorecard.csv`, and `rs_stability_report.md` as the immediate hardening baseline stack.

## Remaining data limits

- Native apples-to-apples sleeve keeps the prior 9-symbol daily subset only.
- `GOOG` is still absent from the native subset. `GOOGL` exists locally and is used only in the explicit mega-cap ex-NVDA sleeve.
- Daily entries still rely on the same simplified local research execution model rather than a production paper packet.
- Options remain blocked and are intentionally excluded.
