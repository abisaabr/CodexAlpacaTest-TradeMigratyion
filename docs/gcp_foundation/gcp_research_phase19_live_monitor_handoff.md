# GCP Research Phase Live Monitor Handoff

- Status: `phase23_research_only_blocked_no_promotions`
- Phase19 batch state: `FAILED`
- Active stage: `none_phase23_complete`
- Latest observed symbol family: `AMZN option contracts`
- Latest observed download date: `2026-04-16`
- Selected-contract files at checkpoint: `266`
- Raw download files at checkpoint: `17073`
- Silver download files at checkpoint: `17339`
- Phase19 replay files: `0`
- Phase19 portfolio-report files: `0`
- Promotion-review state: `research_review_queue_open`
- GCS final artifacts visible: `False`
- Latest checkpoint prefix: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/phase19_live_checkpoints/20260427T155608Z`
- Repair job: `phase20-sharded-fill-repair-20260428031000`
- Repair state: `SUCCEEDED`
- Repair launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase20_sharded_fill_repair_20260428031000/launch/`
- Repair failed chunks: `0`
- Repair option bar rows: `1002599`
- Repair option trade rows: `2317496`
- Replay job: `phase21-replay-from-phase20-20260428034200`
- Replay state: `SUCCEEDED`
- Replay launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase21_replay_from_phase20_20260428034200/launch/`
- Replay decision: `research_only_blocked`
- Replay candidate count: `13`
- Replay eligible count: `0`
- Replay blocker counts: `fill_coverage_below_0.90=13`, `test_net_pnl_not_above_0=3`
- Diagnostic job: `phase22-wide-lag-diagnostic-20260428045000`
- Diagnostic state: `SUCCEEDED`
- Diagnostic launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase22_wide_lag_diagnostic_20260428045000/launch/`
- Diagnostic portfolio report: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase22_wide_lag_diagnostic_20260428045000/portfolio_report/research_portfolio_report.json`
- Diagnostic promotion packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase22_wide_lag_diagnostic_20260428045000/promotion_review_packet/research_promotion_review_packet.json`
- Diagnostic decision: `ready_for_governed_validation_review`
- Diagnostic promotion scope: `research_governed_validation_review_only`
- Diagnostic candidate count: `13`
- Diagnostic eligible count: `6`
- Diagnostic eligible symbols: `AAPL`, `INTC`, `NVDA`
- Diagnostic blocker counts: `fill_coverage_below_0.90=5`, `test_net_pnl_not_above_0=2`
- Diagnostic caveat: `wide_exit_lag_diagnostic_not_deployment_authorization`
- Candidate stress job: `phase23-candidate-stress-20260428062500`
- Candidate stress state: `SUCCEEDED`
- Candidate stress phase id: `phase23_candidate_stress_holdout_20260428062500`
- Candidate stress launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase23_candidate_stress_holdout_20260428062500/launch/`
- Candidate stress portfolio report: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase23_candidate_stress_holdout_20260428062500/portfolio_report/research_portfolio_report.json`
- Candidate stress promotion packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase23_candidate_stress_holdout_20260428062500/promotion_review_packet/research_promotion_review_packet.json`
- Candidate stress decision: `research_only_blocked`
- Candidate stress eligible count: `0`
- Candidate stress blocker counts: `fill_coverage_below_0.90=6`, `test_net_pnl_not_above_0=1`
- Candidate stress scope: `six Phase22 review candidates only`
- Candidate stress underlyings: `AAPL`, `INTC`, `NVDA`
- Candidate stress profiles: `10/10`, `30/30`, `60/60`, `60/90`, `60/120`, `60/180 high-cost`
- Candidate stress holdout: `test_date_count=5`
- Candidate stress result summary: `profitable_but_not_fill_clean_under_short_lag_controls`

## Operator Rule

- Do not relaunch or terminate a running phase while the active stage is producing files or fresh logs.
- Phase19 is no longer running; it failed at the Batch runtime cap before final artifacts were produced.
- Phase21 succeeded but found no promotion-review eligible candidates under shorter-lag replay assumptions.
- Phase22 succeeded and opened a research-only governed-validation review queue for six candidates, but only under wider exit-lag assumptions.
- Treat Phase22 as a diagnostic review signal, not a production promotion or deployment authorization.
- Phase23 completed the candidate-only stress/holdout validation for those six candidates.
- Phase23 found zero eligible promotion-review candidates. All six were blocked by fill coverage below `0.90` across the full lag/cost stack; one `INTC` wide-reward variant also failed the positive holdout PnL gate.
- The best Phase23 read is not "bad strategy economics"; it is "not fill-clean enough under short-lag execution controls."
- This is research-only. Do not arm windows, start trading, change live manifests, or change risk policy from this packet.

## Next Research Step

Do not promote the Phase22 candidates from the current evidence. Keep the `0.90` fill-coverage gate intact and require clean broker-audited paper-session evidence before any activation discussion.

The next safe research action is a no-exit-bar/exit-lag feasibility diagnostic for the five profitable blocked candidates. It should classify whether the short-lag fill gap is repairable market-data sparsity, an execution timing mismatch, or a strategy design issue that needs alternate exits.
