# Provider-owned template preparation

The source directory is the portable artifact. A registered template ID, image
URI, base image or launch reference belongs to one provider/account/region;
it cannot be converted into another provider's template ID.
[中文](provider-preparation.zh-CN.md).

## Preparation responsibility

Catalog `providers` values are prerequisite hints. The value
`provider-preparation-required` means the selected provider must prepare the
source for its backend before launch. It is not a supported/verified badge and
does not assert an installed plugin implements automatic preparation.

When implemented, automatic preparation belongs to the provider: choose its
base/profile, build or acquire the appropriate image, publish to a reachable
registry, register through native APIs and return its own launch reference.
The directory, manifest, commands, version and content hashes remain authoritative.
A directory or Git source reference is not a cloud template ID.

| Provider | Preparation and launch boundary |
| --- | --- |
| alicloud-express | Native FC base/generation/start/readiness; Dockerfile deployment or explicitly prepared platform steps |
| alicloud-container | Provider-owned container image/base/registration and native launch reference |
| cubesandbox | Provider-owned runtime/image preparation and registered template reference |
| e2b | Native E2B build/registration; Express keys and IDs do not transfer |
| opensandbox | Provider-owned reachable image and server startup; an image URI is not another cloud's template ID |

Actual operations depend on declared capabilities and current implementation.
Installing a plugin or showing a launch command does not implement preparation.
Contracts belong to the independent
[providers](https://github.com/Alibaba-Agent-Sandbox/awesome-providers) and
[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk). This repository does
not synthesize endpoints or convert cross-cloud IDs.

## Capabilities and unsupported operations

The template's capabilities remain its actual requirements. Validate them
against the selected provider before preparation/launch. If terminal, code,
files, shell or required ports are missing, report that capability as unsupported.
Do not remove the requirement, relabel another feature or silently launch a
reduced product. A deliberate slice needs explicit design, docs, manifest and
acceptance evidence.

Fail explicitly when preparation, credentials, account/region access, image
reachability or registration is unavailable. Keep credentials within their own
provider operation. Inject model settings at the documented server-process
boundary. Cleanup covers only resources created by that attempt.

## Acceptance

Catalog hints, automatic preparation results and actual native-backend
acceptance are separate claims. Keep README Verified, tested_on, catalog status
and [evidence tiers](template-spec.md#test-levels) unchanged until their checks
pass. Express success does not certify E2B, Cube, OpenSandbox or container edition.
Each needs real deployment/calls/owned cleanup at recorded source hashes.
Failures and missing checks remain explicit.

Change both languages and relevant regressions with these hints.
[Using templates](using-templates.md) covers callers; [platform steps](platform-steps.md)
covers the Express source-preparation path exercised in this repository.
