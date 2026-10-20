# SDK local preview validation

Status: PARTIAL; genuine Express browser run pending.

Source-only operator utility: no Docker/commands/assets/manifest contract change. Six transport/ownership tests and three existing non-binary browser-controller checks PASS (9 passed,2 native-IDE cases deselected because their reproducible local binary cache was already cleaned). HTTP/WS tests use actual local fixtures; TLS policy uses real MemoryBIO handshakes. The earlier attempted network TLS fixture was intercepted by this operator environment and did not pass; it is not promoted. Independent listener release uses actual kernel rebinding because this environment accepts connections to otherwise absent local ports.

Dependency review identified upstream fixes newer than an initial local aiohttp3.13.3 draft; the published lock uses3.14.5 and official release SHA256 values for all transitive packages. No vulnerable draft lock was published. Actual Express upstream TLS, browser behavior and resource cleanup remain required; direct-default-domain image/browser failures stay immutable history.
