# Aider hardened image/controller recheck — 2026-10-16

Result: PARTIAL. Supplemental image/model acceptance PASS; canonical deployment
and parent/final remote gates remain required. Product controller tested:
`f76687e32a87d52fd50f7c774266db6155da3bcd`. Actual image product source:
`ecbabafca49fd8f5d0cf980842a7fa69ee66d7c6`, CI run `38856361807`, immutable
artifact `12026949932`. See [sanitized proof](../../../aider/evidence/image-runtime-hardened-2026-10-16.json).

## Executed verification

- `python -m pytest -q aider/test_e2e_protocol.py aider/test_commands.py`: 72 PASS,
  14.28 seconds, actual subprocess fixtures with synthetic HTTP/model. An independent
  peer review ran six static-exit negative controls: 6 PASS, 1.55 seconds.
- Standalone HTTP controller with local server: PASS with actual CLI and model
  explicitly SKIP because the host CLI is absent; not image acceptance.
- Supplemental controller command: `python cloud_image_batch.py aider 12026949932
  --head ecbabafca49fd8f5d0cf980842a7fa69ee66d7c6 --label hardened
  --reuse-reviewed-result <same-artifact-provenance>`: exit 0. The private runner
  supplied its isolated source-root and credential environment without recording
  values. This is registry transfer and official registration, not abx deployment.
- Official READY and all 56 server modules matched the pinned SDK. SDK/HTTP/CLI
  version probes passed. Keyless HTTP: 9 PASS / 0 FAIL / 1 model SKIP.
- Original unchanged image commands with explicitly selected model environment on
  owned port 9010: 21 genuine qwen3.8-flash checks PASS / 0 FAIL / 0 SKIP. Tests and
  held-out calculations require fresh post-agent acknowledgements and actual source
  compilation. Controller SHA equals the committed source before/after execution.
- Helper kill/absence, target kill/absence, template deletion, exact ACR tag and
  repository 404: seven flags TRUE. A subsequent independent read-only official
  paginated inventory, rejecting malformed/ambiguous rows, confirmed the exact
  unpredictable owned template name absent. No unrelated resource was deleted.

Historical earlier model evidence remains unchanged and is explicitly identified
as predating this guard. Image commands, Dockerfile, YAML, catalog and tested_on
have no changes. Canonical `scripts/express_e2e.py` and actual `abx template deploy`
are NOT RUN. No express receipt/provider promotion/merge is claimed.

Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/102 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/98.
