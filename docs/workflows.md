# Template launch and verification

A template describes the environment to start, its startup command and the services it exposes. Run one command; no workflow selection is required. [中文](workflows.zh-CN.md).

```sh
abx --provider alicloud-express template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello --yes
```

## Current machine contract

Source manifests and managed catalog entries use `spec_version: 5`; the catalog uses `schema_version: 2`. The source schema is [template-v5.schema.json](../spec/template-v5.schema.json). [Shared launch rules](../spec/contracts/launch-v1.json) are copied from the [Python contract owner](https://github.com/Alibaba-Agent-Sandbox/python-sdk/tree/main/contracts) with an exact source lock; synchronize them through `scripts/sync_launch_contracts.py`.

`provides` lists all exposed services, each with protocol, version, port and operations. `start_cmd` starts the template and `ready_cmd` checks readiness. The command registry remains in `commands.py`. There are no per-operation startup modes or user-written capability plans.

Launch prepares source when required, creates one sandbox, runs the startup command and readiness command, and returns every declared service endpoint. The built-in server v2 protocol additionally receives health checks and command discovery when declared. Other protocols remain extensible: endpoint resolution alone does not establish their protocol readiness; the template readiness command is responsible for its overall readiness. An already prepared image or a provider-bound native template identity supplies the environment without redefining the services. Installing a tool does not imply that its task should run immediately: commands that need a prompt, password or workspace remain callable after startup. For example, the database template exposes `services_start` with its explicit password and data-directory arguments; launch does not invent those inputs.

A provider owns its registry/upload configuration, native template registration, sandbox creation and endpoint resolution. CLI/SDK check the operations actually needed for creation, preparation, startup and declared services. Python software in an image does not require a provider interpreter API. Calling a provider interpreter remains an independent operation with its own support requirements.

## Deployment topology

The optional `application` mapping retains placement, deployment adapter, hooks, state and limits. It describes an explicit application deployment. Those hooks never run during template installation, source preparation or sandbox startup. Both [local](examples/application-local/template.yaml) and [external](examples/application-external/template.yaml) examples preserve this separation.

## Ownership and evidence

Source snapshots and resource journals bind the source, effective configuration and created resources. Cleanup deletes only resources owned by the run and reports retained images or native templates. Keep platform credentials and service tokens separate.

Static validation proves configuration consistency, not cloud execution. A launch verification records exact source/manifest/CLI/SDK/provider revisions, service checks, actual calls and independent cleanup. Missing or skipped required checks are not passes. Model tasks and optional native interfaces require their own tests.

Historical receipts are immutable and keep their original workflow, consumer and source scope. Do not rewrite them as specification 5 acceptance. The historical receipt contract files in `spec/contracts` remain available for reading old evidence; they do not impose workflow declarations on current authors. A catalog record does not itself certify a template.

## Validation

Install `scripts/requirements-spec.txt`, then run `scripts/test_spec_tools.py`, `scripts/check_template.py --all`, `scripts/check_managed_catalog.py`, the template-launch regressions and `scripts/check_docs.py`. These checks do not substitute for real provider launches and cleanup.

## Explicit build profiles

A source may retain a reviewed `build_profiles.<id>: {dockerfile: Dockerfile.<id>, context: "."}`. Choose `--build-profile <id>` only when intentionally changing its build recipe. This does not select different application contents or services. The `python-hello` portable recipe remains separate from the default Express recipe. An image-build or cloud acceptance claim must identify the recipe actually used.
