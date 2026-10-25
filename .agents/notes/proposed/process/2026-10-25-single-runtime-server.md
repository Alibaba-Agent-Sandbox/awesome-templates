# Use one template application startup owner

Status: proposed

## Problem

The active bilingual runtime guide still taught a second port-9010 service, an internal Sandbox import and old direct endpoint handling. Its historical Aider result did not establish that procedure as the current unified startup path. The specification linked readers to that workaround.

## Decision

Recommend the existing CLI template launch, then public ProviderSandbox.connect and application_client for the running declared service. Remove the alternate server procedure and update both specification links. Preserve the Aider receipt and link it only as a separate historical experiment.

## API Design

No runtime or public API changes. The guide uses the existing python-hello command on port 9000, explicit application token and client close methods. It distinguishes connection cleanup from deleting the owned sandbox and retained template/image. It preserves startup-time token reading, health exemption and separate gateway authentication.

## Alternatives considered

Keeping two startup examples would continue to confuse application ownership. Implementing another server, compatibility API or environment mechanism is outside this documentation correction. Current environment investigations do not establish a platform-wide rule and are not folded into the stable specification.

## Dependencies

Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/223 and https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/221. Public CLI 0.5.6 and Python client/server 0.4.0a6 already exist. Author guidance links to the independently maintained SDK guide.

## Test Strategy

Check local links across current documents, both Python blocks' syntax/imports against the installed public client, signature binding, translations and diff hygiene. No cloud resources, image builds, model calls or dependency installs are needed to validate prose. Preserve historical evidence.

## Acceptance criteria

Both current languages and specification links use one startup owner and the actual public consumption API. Required current-head CI and independent review pass. Merge remains held until the ongoing frozen OpenSandbox matrix completes; this PR does not satisfy either linked Issue's full cloud acceptance.
