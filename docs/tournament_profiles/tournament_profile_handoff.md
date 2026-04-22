# Tournament Profile Handoff

## Resolution

- Generated at: `2026-04-22T16:07:00.489805`
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
- Executable now: `true`
- Execution risk tier: `moderate`
- Entry friction sensitivity: `medium`
- Exit model dependency: `medium`
- Research bias: `premium_defense_mixed`
- Minimum execution evidence strength: `limited_entry_only`
- Requires broker-order audit coverage: `false`
- Requires broker-activity audit coverage: `false`
- Requires exit telemetry: `false`
- Activation blocked by policy: `false`
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
- Executable now: `true`
- Execution risk tier: `moderate`
- Entry friction sensitivity: `medium`
- Exit model dependency: `medium`
- Research bias: `premium_defense_mixed`
- Minimum execution evidence strength: `limited_entry_only`
- Requires broker-order audit coverage: `false`
- Requires broker-activity audit coverage: `false`
- Requires exit telemetry: `false`
- Activation blocked by policy: `false`
- Discovery source: `full_ready`
- Bootstrap ready universe: `false`
- Reasons:
  - posture caution favors moderate risk tier (+5)
  - elevated entry friction penalizes medium sensitivity (-10)
  - exit telemetry gap penalizes medium exit-model dependency (-8)
  - profile keeps a premium-defense tilt under cautious execution posture (+10)

### opening_30m_premium_defense

- Score: `-628`
- Executable now: `true`
- Execution risk tier: `conservative`
- Entry friction sensitivity: `low`
- Exit model dependency: `medium`
- Research bias: `defined_risk_and_premium_defense`
- Minimum execution evidence strength: `entry_and_reconciliation`
- Requires broker-order audit coverage: `true`
- Requires broker-activity audit coverage: `true`
- Requires exit telemetry: `false`
- Activation blocked by policy: `true`
- Discovery source: `coverage_ranked`
- Bootstrap ready universe: `true`
- Reasons:
  - execution handoff explicitly recommends this profile (+100)
  - posture caution favors conservative risk tier (+15)
  - current execution evidence `limited_entry_only` is below the profile floor `entry_and_reconciliation` (-250)
  - profile requires broker-order audit coverage, which is not yet permitted by current execution policy (-250)
  - profile requires broker-activity audit coverage, which is not yet permitted by current execution policy (-250)
  - elevated entry friction penalizes low sensitivity (-0)
  - exit telemetry gap penalizes medium exit-model dependency (-8)
  - profile research bias matches preferred execution-informed research bias (+15)

### balanced_family_expansion_benchmark

- Score: `-763`
- Executable now: `true`
- Execution risk tier: `moderate`
- Entry friction sensitivity: `medium`
- Exit model dependency: `medium`
- Research bias: `balanced`
- Minimum execution evidence strength: `entry_and_reconciliation`
- Requires broker-order audit coverage: `true`
- Requires broker-activity audit coverage: `true`
- Requires exit telemetry: `false`
- Activation blocked by policy: `true`
- Discovery source: `coverage_ranked`
- Bootstrap ready universe: `true`
- Reasons:
  - posture caution favors moderate risk tier (+5)
  - current execution evidence `limited_entry_only` is below the profile floor `entry_and_reconciliation` (-250)
  - profile requires broker-order audit coverage, which is not yet permitted by current execution policy (-250)
  - profile requires broker-activity audit coverage, which is not yet permitted by current execution policy (-250)
  - elevated entry friction penalizes medium sensitivity (-10)
  - exit telemetry gap penalizes medium exit-model dependency (-8)

### opening_30m_convexity_butterfly

- Score: `-1420`
- Executable now: `false`
- Execution risk tier: `aggressive`
- Entry friction sensitivity: `high`
- Exit model dependency: `high`
- Research bias: `convexity_and_long_vol`
- Minimum execution evidence strength: `broad`
- Requires broker-order audit coverage: `true`
- Requires broker-activity audit coverage: `true`
- Requires exit telemetry: `true`
- Activation blocked by policy: `true`
- Discovery source: `coverage_ranked`
- Bootstrap ready universe: `true`
- Reasons:
  - execution handoff explicitly deprioritizes this profile (-100)
  - posture caution favors aggressive risk tier (-15)
  - current execution evidence `limited_entry_only` is below the profile floor `broad` (-250)
  - current execution policy caps profile risk at `moderate`, below this profile's `aggressive` tier (-250)
  - profile requires broker-order audit coverage, which is not yet permitted by current execution policy (-250)
  - profile requires broker-activity audit coverage, which is not yet permitted by current execution policy (-250)
  - profile requires reliable exit telemetry, but the current execution posture still flags an exit-telemetry gap (-250)
  - elevated entry friction penalizes high sensitivity (-20)
  - exit telemetry gap penalizes high exit-model dependency (-15)
  - sample size is still limited, so aggressive profiles are discounted (-10)
  - recent guardrail pressure further discounts aggressive profiles (-10)

### opening_30m_single_vs_multileg

- Score: `-1420`
- Executable now: `false`
- Execution risk tier: `aggressive`
- Entry friction sensitivity: `high`
- Exit model dependency: `high`
- Research bias: `balanced_directional_vs_multileg`
- Minimum execution evidence strength: `broad`
- Requires broker-order audit coverage: `true`
- Requires broker-activity audit coverage: `true`
- Requires exit telemetry: `true`
- Activation blocked by policy: `true`
- Discovery source: `coverage_ranked`
- Bootstrap ready universe: `true`
- Reasons:
  - execution handoff explicitly deprioritizes this profile (-100)
  - posture caution favors aggressive risk tier (-15)
  - current execution evidence `limited_entry_only` is below the profile floor `broad` (-250)
  - current execution policy caps profile risk at `moderate`, below this profile's `aggressive` tier (-250)
  - profile requires broker-order audit coverage, which is not yet permitted by current execution policy (-250)
  - profile requires broker-activity audit coverage, which is not yet permitted by current execution policy (-250)
  - profile requires reliable exit telemetry, but the current execution posture still flags an exit-telemetry gap (-250)
  - elevated entry friction penalizes high sensitivity (-20)
  - exit telemetry gap penalizes high exit-model dependency (-15)
  - sample size is still limited, so aggressive profiles are discounted (-10)
  - recent guardrail pressure further discounts aggressive profiles (-10)
