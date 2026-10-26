# Preserve immutable Git COPY permissions

Status: proposed

## Problem

A native next-app attempt at a9362a8ca988aaed33cd0b19e3ed8ecb4cd88af7 failed with public CLI 0.5.6 reporting PermissionError / errno 13 for /opt/next-app/package.json. The private controller checkout had mode 0600, while the exact source commit recorded 100644. The existing materializer fetched the verified bytes from that Git archive but explicitly applied the controller checkout mode. Root-owned package metadata therefore became unreadable to the non-root application. Both owned resources were independently confirmed absent.

## Decision

Only when local bytes match the selected immutable source commit, read that commit's regular-file Git mode and use 0644 or 0755 in the generated COPY. Use --full-tree because the Git process runs from a template subdirectory. Reject missing/non-regular modes. Preserve actual filesystem permissions for inline, untracked or changed local content.

## API Design

No public API, CLI flag, SDK, Dockerfile, manifest or template version changes. Existing archive size, content-hash, secret-name, symlink and ownership boundaries remain. This repairs maintenance COPY provenance; it does not certify the default Express Docker-to-ACR journey, which remains blocked by host prerequisites.

## Alternatives considered

Globally changing checkout permissions would discard intentional local modes. Changing the application Dockerfile would mask an acceptance adapter defect. Unconditional normalization would weaken the existing local 0640 contract. Another build mode, runner or package release is unnecessary.

## Dependencies

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/232

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/231

## Test Strategy

Use real temporary Git repositories and execute generated COPY restoration: committed 0644 versus local 0600, committed 0755 versus local 0700, and unchanged local/untracked permissions. Keep corrupt archive rejection and reject a Git symlink even when a local regular file has matching bytes. Independently review the narrow implementation, then run the existing complete next-app native preparation plus CLI/SDK/HTTP controller once with official 0.5.6 / 0.4.0a6 and exact owned cleanup.

## Acceptance criteria

The two mode regressions fail before the correction and pass afterwards; integrated boundary checks pass. The next-app full control passes at its exact candidate, with sandbox and prepared-template absence independently established. Latest-head CI and review pass before a normal merge. The frozen a936 full matrix and its original next-app failure retain their original results and source; later evidence does not relabel them as a new-harness pass.
