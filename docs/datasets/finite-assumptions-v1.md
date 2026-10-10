# Finite-assumptions-v1

Authored2026-10-09, MIT project fixture, no external data, no train/test split or model.
Five numeric fields(price input/output, latency fact, cost/latency contract) times four
inputs(NaN,positive infinity,negative infinity,10**400) form20 independent mutations of
the original safe profile. All should yield controlled ValueError. Observations record
field/input category/outcome, never embed non-standard JSON numbers in result artifacts.

Original clean wheel0.3.0 is an actual baseline:5controlled rejections,10accepted,
5uncontrolled OverflowError. Fixed0.3.1:20controlled,0accepted,0uncontrolled. Separate
tests cover JSON/YAML/CLI, large exponent, finite arithmetic overflow, optional null,
zero/positive values and the exact initial silent NaN report. Not an independent sample
or defect prevalence estimate; null is unknown metadata, never zero or proof of safety.
