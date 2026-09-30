# Implementation notes

Date: 2026-09-30

- Kept the canonical graph independent from the LiteLLM loader so future adapters can reuse audits.
- Used Tarjan strongly connected components for deterministic cycle findings, including self-loops.
- Treats all fallback categories as possible edges for static reachability. This is intentionally conservative because a workload can encounter multiple failure classes.
- Refuses to calculate exposure when `num_retries` is absent instead of assuming an upstream default.
- Uses operator-owned model facts rather than mutable scraped catalogs.
- Added a hard scenario step bound so even a cyclic fixture cannot hang the replay command.
- Initial test expectation counted duplicate category edges as three paths. The implementation correctly deduplicated graph reachability to two unique terminal paths, so the test was corrected before evidence generation.
