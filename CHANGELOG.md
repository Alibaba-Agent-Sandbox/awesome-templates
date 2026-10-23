# Changelog

## Unreleased

- Replace template specification 2/3 with specification4 and explicit provided services, workflows and a default workflow. Retired compatibility and handwritten verification fields are rejected.
- Separate application deployment topology from sandbox invocation paths, and managed inputs from source builds. Preserve application hooks and durable-state semantics.
- Bind full manifest identities without qualification exclusions. Historical receipts remain scoped reports; only independently trusted workflow evidence can certify a current path.
- Remove interpreter shell-fallback claims from managed exec verification. Keep Dockerfile/base/entrypoint inputs explicit.
