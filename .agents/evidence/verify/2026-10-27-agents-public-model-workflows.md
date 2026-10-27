# Public Agents CLI model workflows

Result: PARTIAL (local implementation; actual public run pending)

Date: 2026-10-27. Base80167d7. Native Codex0.162.1/Qwen0.23.0/Node24.16.0 and
server0.4.0a6 unchanged. Existing restricted HTTP policy unchanged.

- pytest test_model_setup/test_protocol/test_sdk_verifier PASS53. Real local
  server policy/protocol fixtures are synthetic and do not certify native coding.
- Explicit profile native Responses/no WebSockets/env key reference, no secret
  serialization, exclusive0600/idempotence/foreign/symlink config preservation.
- Default standalone verifier now selects published ProviderSandbox; controlled
  create failure reconciles exact owned absence instead of undefined-name failure.
- Template checker/docs PASS; actual both native adapters on public9000, complete
  documentation and independent artifacts/state/cleanup pending.
