# Preflight names and existing file identity

2026-10-09. Apply one shared CLI check to all five file-reading commands before parsing
or report writes. Resolved paths handle ordinary aliases/symlinks; samefile identifies
existing hard links. Inputs can be shared among themselves, but no output may share
an input or prior output. Unrelated existing report replacement remains explicit CLI
behavior. interop exclusive new-directory semantics remain unchanged.

Tradeoff: local preflight is not an authorization or atomic-write barrier. A hostile
concurrent filesystem actor can change links after checking. Low-level report writers
remain general helpers. Multi-artifact publication can still be partial on later I/O
failure. Do not claim a filesystem sandbox or race-free preservation.
