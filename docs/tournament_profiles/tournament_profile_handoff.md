# Tournament Profile Handoff

## Resolution

- Generated at: `2026-04-22T11:11:00.395790`
- Requested profile: `auto`
- Resolved profile: `down_choppy_coverage_ranked`
- Resolution mode: `auto_recommended`
- Resolution warning: `none`
- Execution posture: `caution`
- Evidence strength: `limited_entry_only`
- Preferred research bias: `defined_risk_and_premium_defense`
- Recommended executable profile: `down_choppy_coverage_ranked`
- Recommended executable profiles: `down_choppy_coverage_ranked`
- Deprioritized executable profiles: `none`

## Execution Policy Inputs

- Recommended profiles from execution: `down_choppy_coverage_ranked, opening_30m_premium_defense`
- Deprioritized profiles from execution: `opening_30m_convexity_butterfly, opening_30m_single_vs_multileg`

## Profile Scores

### down_choppy_coverage_ranked

- Score: `97`
- Execution risk tier: `moderate`
- Entry friction sensitivity: `medium`
- Exit model dependency: `medium`
- Research bias: `premium_defense_mixed`
- Discovery source: `coverage_ranked`
- Bootstrap ready universe: `true`
- Reasons:
  - execution handoff explicitly recommends this profile (+100)
  - posture caution favors moderate risk tier (+5)
  - elevated entry friction penalizes medium sensitivity (-10)
  - exit telemetry gap penalizes medium exit-model dependency (-8)
  - profile keeps a premium-defense tilt under cautious execution posture (+10)

### down_choppy_full_ready

- Score: `-3`
- Execution risk tier: `moderate`
- Entry friction sensitivity: `medium`
- Exit model dependency: `medium`
- Research bias: `premium_defense_mixed`
- Discovery source: `full_ready`
- Bootstrap ready universe: `false`
- Reasons:
  - posture caution favors moderate risk tier (+5)
  - elevated entry friction penalizes medium sensitivity (-10)
  - exit telemetry gap penalizes medium exit-model dependency (-8)
  - profile keeps a premium-defense tilt under cautious execution posture (+10)
