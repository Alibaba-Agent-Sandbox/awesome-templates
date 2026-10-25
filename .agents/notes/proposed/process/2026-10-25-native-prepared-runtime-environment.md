# Preserve explicit Docker environment in prepared native acceptance

Status: proposed

## Problem

The native-step acceptance adapter prepared the original Dockerfile, then launched a temporary managed-reference manifest copied from the original YAML. That copy omitted explicit Dockerfile ENV values. A controlled agents-cli diagnostic on the same owned instance proved that the application lacked its installed agent PATH and succeeded after restarting only that owned application with the materialized environment.

## Decision

Retain only explicit, expanded Dockerfile ENV values as runtime defaults in the prepared manifest. Pass those values through the existing prepared-reference consumer; explicit original manifest environment entries take precedence. Build-only UV/cache/upload variables are not runtime configuration. Keep the image-backed consumer unchanged when it supplies no runtime environment.

## API Design

The maintenance-only prepared manifest helper and its existing exercise function accept an optional runtime_env mapping. The native adapter supplies the prepared manifest environment. There is no public CLI flag, new runner, template command, dependency, image or template version change.

This preserves image-style environment defaults for this adapter. It does not establish a combined precedence contract for the production native-steps command wrapper, which independently prefixes explicit ENV values. That cross-layer precedence question remains a separate review item.

## Alternatives considered

Changing business commands or Dockerfiles would hide the adapter loss. Copying the entire build environment would leak transient UV and upload configuration into runtime. Creating another startup path or modifying the frozen running batch would invalidate its evidence.

## Dependencies

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/227

The original public input is commit 389302f5dc9429a4b215801dbd4025d4dba95f7e, official CLI 0.5.5 and public client/server 0.4.0a6. CLI 0.5.6 is now formally published; current setup recommendations and the installed-CLI parser gate use it. The final new matrix awaits normal review/CI/merge. Historical receipts keep their original package versions.

## Test Strategy

Exercise explicit ENV expansion, original manifest priority, exclusion of build-only UV/cache configuration, forwarding through the existing native consumer and unchanged image-consumer behavior. Preserve the original failing native receipts and separate same-instance diagnostic. After current-head checks and review, run a fresh complete native supplemental matrix using public inputs.

## Acceptance criteria

Local regressions fail before the fix and pass after it. Required latest-head checks and independent review pass. Fresh cloud evidence retains original failures, exact provenance and independently confirmed owned cleanup. Native supplemental success cannot certify the blocked default Express Docker source journey.
