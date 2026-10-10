# Verify instrumentation without inference

2026-10-09. Use the actual pinned LiteLLM callback, official OTel exporter encoding and
three independent child processes per configuration. Fully mock HTTP through respx;
strip inherited credentials, proxies and exporter configuration; deny external DNS
and TCP connect/connect_ex before imports. No provider inference or credential needed.

Dedicated experimental CLIENT spans are supported; legacy INTERNAL and collapsed
SERVER exports remain inconclusive, not inferred safe. Keep optional dependencies out
of base installs and use a separate CI job. Bound workers, preserve timeout receipts
and local diagnostic logs, never publish raw exports or claim a full OS sandbox.

Tradeoffs: pinned SDKs add substantial optional dependencies; source-level socket
guards are not protection against hostile code, UDP or subprocess bypass. This fixture
contains trusted dependencies, synthetic messages and no privileged operation. Does
not validate live routing, real fallbacks, retries, streaming or provider billing.
