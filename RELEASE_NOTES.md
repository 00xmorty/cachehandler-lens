# v0.2.0 — 2026-10-06

- Add privacy-filtered JSON output, explicit scan completeness and UTI-only document declarations.
- Reject intermediate symlink redirects (including Contents), skip non-regular plists and bound actual plist reads.
- Mark traversal errors incomplete, suppress filesystem error paths and expose document-type truncation.
- Preserve read-only/offline behavior and UNKNOWN registration/effective-default semantics.
- Add regression tests for structured output, UTI filtering, symlink redirects, incomplete scans and limits.

# v0.1.0 — 2026-10-02

First offline, bounded inspection of app-bundle document handler declarations. Prints safe extension/rank summaries without app names or paths. Registration and effective Finder default are explicitly UNKNOWN. macOS and Linux fixture tests included. No write, repair, network or telemetry functionality.
