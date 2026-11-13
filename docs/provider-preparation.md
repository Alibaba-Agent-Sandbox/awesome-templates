# Provider-owned template preparation

[中文](provider-preparation.zh-CN.md)

Each `sandbox.<name>` selects a Provider and validates its `template` against that Provider's contract. Template IDs, image URIs and volumes belong to a Provider/account/region; they cannot be converted across clouds. Express keeps region at `template.region`, shared by sibling static volumes.

`buildConfig` selects Dockerfile/context or native steps. Dockerfile builds push to `image` when supplied. Steps consume `image` and prepare a platform template; they do not promise to export the completed result as OCI. An image without buildConfig is used directly; reference borrows an existing template.

`registryConfig` provides optional authentication, certificate and pull-network overrides. The adapter handles reliably inferred registry type and ordinary Linux defaults. If registry instance identity cannot be resolved reliably, it must fail with configuration guidance instead of guessing. Installing storage clients in a Dockerfile does not create volumes, mount them or grant access.

Unsupported capabilities must fail before the operation rather than silently discard fields or change Providers. Other Providers need their own fields rather than copied Express properties. See [runtime configuration](runtime-environment.md) for dynamic startup and the [resource specification](template-spec.md) for static deployment.
