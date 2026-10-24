# Changelog

## Unreleased

- Validate managed service/operation references and exec startup commands with the same semantics as source templates; reject service bindings on other workflow kinds and commandless managed exec startup.
- Remove the unused legacy local runtime profile and document only the strict current managed catalog fields.
- Align13 template server fallbacks and the skeleton with the CI source pin; reject default/fallback drift and preserve old receipts as history. Changed template contracts receive patch versions and require new image/workflow acceptance.
- Pin Qwen Node24.16.0 with official x64/arm64 SHA256 verification instead of a moving setup script.

- Replace template specification 2/3 with specification4 and explicit provided services, workflows and a default workflow. Retired compatibility and handwritten verification fields are rejected.
- Separate application deployment topology from sandbox invocation paths, and managed inputs from source builds. Preserve application hooks and durable-state semantics.
- Bind full manifest identities without qualification exclusions. Historical receipts remain scoped reports; only independently trusted workflow evidence can certify a current path.
- Remove interpreter shell-fallback claims from managed exec verification. Keep Dockerfile/base/entrypoint inputs explicit.
