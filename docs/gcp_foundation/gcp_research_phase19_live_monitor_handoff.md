# GCP Research Phase Live Monitor Handoff

- Status: `phase25_intc_isolated_stress_blocked_no_promotion`
- Phase19 batch state: `FAILED`
- Active stage: `none_phase25_complete`
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
- Exit-lag feasibility job: `phase24-exit-lag-feas-20260428073500`
- Exit-lag feasibility state: `SUCCEEDED`
- Exit-lag feasibility phase id: `phase24_exit_lag_feasibility_20260428073500`
- Exit-lag feasibility runner commit: `95379e4`
- Exit-lag feasibility runner source: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_95379e4166b4.zip`
- Exit-lag feasibility launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase24_exit_lag_feasibility_20260428073500/launch/`
- Exit-lag feasibility packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase24_exit_lag_feasibility_20260428073500/exit_lag_feasibility/exit_lag_feasibility_packet.json`
- Exit-lag feasibility decision: `fill_feasible_under_full_stack`
- Exit-lag feasibility promotion effect: `none_research_only`
- Exit-lag feasibility candidate count: `5`
- Exit-lag feasibility full-stack pass count: `1`
- Exit-lag feasibility wide-lag-only count: `4`
- Exit-lag feasibility candidate scope: `five profitable Phase23 blocked candidates`
- Exit-lag feasibility purpose: `classify no-exit-bar gaps as data sparsity, execution timing mismatch, or strategy design issue`
- Isolated stress job: `phase25-intc-stress-20260428085000`
- Isolated stress state: `SUCCEEDED`
- Isolated stress phase id: `phase25_intc_isolated_stress_20260428085000`
- Isolated stress launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase25_intc_isolated_stress_20260428085000/launch/`
- Isolated stress candidate: `INTC` `b150__intc__long_call__tight_reward__exit_210__liq_baseline`
- Isolated stress purpose: `single-candidate economic stress after full-stack fill feasibility`
- Isolated stress portfolio report: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase25_intc_isolated_stress_20260428085000/portfolio_report/research_portfolio_report.json`
- Isolated stress promotion packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase25_intc_isolated_stress_20260428085000/promotion_review_packet/research_promotion_review_packet.json`
- Isolated stress decision: `research_only_blocked`
- Isolated stress eligible count: `0`
- Isolated stress blockers: `fill_coverage_below_0.90`, `test_net_pnl_not_above_0`, `min_net_pnl_not_positive`
- Isolated stress min net PnL: `$-2726.7175`
- Isolated stress min test PnL: `$-305.9375`
- Isolated stress min fill coverage: `0.8776`
- Isolated stress max fill coverage: `0.966`
- Wide-lag exit-policy job: `phase26-widelag-policy-20260428100000`
- Wide-lag exit-policy state: `SUCCEEDED`
- Wide-lag exit-policy phase id: `phase26_widelag_exit_policy_20260428100000`
- Wide-lag exit-policy launch packet: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase26_widelag_exit_policy_20260428100000/launch/`
- Wide-lag exit-policy result root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase26_widelag_exit_policy_20260428100000/`
- Wide-lag exit-policy scope: four Phase24 AAPL/NVDA wide-lag candidates only
- Wide-lag exit-policy purpose: `exit_policy_cost_sensitivity_for_wide_lag_candidates`
- Wide-lag exit-policy promotion effect: `none_research_only`
- Wide-lag exit-policy decision: `ready_for_governed_validation_review`
- Wide-lag exit-policy eligible count: `1`
- Wide-lag exit-policy review candidate: `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`
- Wide-lag exit-policy review candidate metrics: min net `$1715.93`, min test `$591.28`, fill `0.9474-1.0`, worst drawdown `$-3330.115`
- Wide-lag exit-policy blocker counts: `fill_coverage_below_0.90=3`, `test_net_pnl_not_above_0=1`
- Wide-lag exit-policy blocked leads: `NVDA exit_300`, `AAPL exit_210`, `NVDA exit_360`
- AAPL governance packet: `docs/gcp_foundation/gcp_research_aapl_candidate_governance_review_packet.md`
- AAPL governance state: `research_review_ready_for_governance_decision`
- AAPL adversarial stress job: `phase27-aapl-governance-stress-20260428141000`
- AAPL adversarial stress state: `SUCCEEDED`
- AAPL adversarial stress phase id: `phase27_aapl_governance_stress_20260428141000`
- AAPL adversarial stress result root: `gs://codexalpaca-control-us/research_results/top100_liquidity_research_20260426/portfolio_event_driven_data/phase27_aapl_governance_stress_20260428141000/`
- AAPL adversarial stress decision: `ready_for_governed_validation_review`
- AAPL adversarial stress metrics: min net `$1715.93`, min test `$341.155`, fill `0.9474-1.0`, worst drawdown `$-4167.955`
- AAPL adversarial stress blockers: `none`
- AAPL bounded validation plan: `docs/gcp_foundation/gcp_research_aapl_bounded_paper_validation_plan.md`
- AAPL bounded validation state: `ready_to_prepare_bounded_paper_validation`
- AAPL non-live manifest candidate: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_manifest_candidate.yaml`
- AAPL operator checklist: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_operator_checklist.md`

## Operator Rule

- Do not relaunch or terminate a running phase while the active stage is producing files or fresh logs.
- Phase19 is no longer running; it failed at the Batch runtime cap before final artifacts were produced.
- Phase21 succeeded but found no promotion-review eligible candidates under shorter-lag replay assumptions.
- Phase22 succeeded and opened a research-only governed-validation review queue for six candidates, but only under wider exit-lag assumptions.
- Treat Phase22 as a diagnostic review signal, not a production promotion or deployment authorization.
- Phase23 completed the candidate-only stress/holdout validation for those six candidates.
- Phase23 found zero eligible promotion-review candidates. All six were blocked by fill coverage below `0.90` across the full lag/cost stack; one `INTC` wide-reward variant also failed the positive holdout PnL gate.
- The best Phase23 read is not "bad strategy economics"; it is "not fill-clean enough under short-lag execution controls."
- Phase24 completed as the non-broker-facing no-exit-bar/exit-lag feasibility diagnostic for the five profitable blocked candidates.
- Phase24 found one full-stack fill-feasible candidate: `INTC` `b150__intc__long_call__tight_reward__exit_210__liq_baseline`.
- Phase24 found four wide-lag-only or short-lag-conditional candidates: `AAPL` wide-reward 360 passes at `30` minutes, while `NVDA` 300, `NVDA` 360, and `AAPL` 210 require `60` minutes or more.
- Phase24 is a feasibility classification packet, not a promotion packet.
- Phase25 completed as the isolated economic stress packet for the single full-stack fill-feasible INTC candidate.
- Phase25 blocked INTC from promotion review. The candidate remains positive under lighter cost assumptions, but harsher `10/10` cost stress turns net and holdout PnL negative, and `30/30 slip25 fee1.00` has negative holdout PnL.
- The current research read is `cost_sensitive_research_lead`, not a governed validation candidate.
- Phase26 completed as the non-broker-facing exit-policy and cost-sensitivity diagnostic for the AAPL/NVDA wide-lag candidates.
- Phase26 opened one research/governed-validation review candidate: `AAPL` `b150__aapl__long_call__wide_reward__exit_360__liq_baseline`.
- Phase26 did not authorize deployment. The candidate remains research review only and still requires governance review plus clean broker-audited paper-session evidence before any activation discussion.
- Phase27 completed as a non-broker-facing adversarial cost and lag stress test for that single AAPL candidate.
- Phase27 kept the AAPL candidate eligible for research/governed-validation review under harsher cost and lag assumptions.
- This is research-only. Do not arm windows, start trading, change live manifests, or change risk policy from this packet.

## Next Research Step

Do not promote the Phase22/Phase23 candidates from the current evidence. Keep the `0.90` fill-coverage gate intact and require clean broker-audited paper-session evidence before any activation discussion.

Keep INTC in research-only hold. The next safe research step is execution-cost sensitivity work and exit-policy design across the AAPL/NVDA wide-lag candidates, with explicit spread/slippage assumptions. Do not relax gates or modify live strategy selection from Phase24 or Phase25 alone.

Phase26 completed that next safe research step. Do not promote candidates, relax gates, or modify live strategy selection from Phase26 alone. The next safe step is to publish a governance review packet for the AAPL research candidate and keep the blocked NVDA/AAPL leads in data-repair or strategy-design review.

The AAPL governance review packet is now updated with Phase27 results. A planning-only bounded paper validation plan, non-live manifest candidate, and operator checklist exist. The next safe step is dry-run startup preflight on the sanctioned VM after copying the candidate config into the runner checkout. Do not modify live manifests or run a broker-facing session from this research packet alone.
