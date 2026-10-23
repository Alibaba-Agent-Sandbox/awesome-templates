# Provider-owned template preparation

A source directory is portable input. Native template IDs, image URIs and launch references belong to one provider/account/region and cannot be converted across clouds. [中文](provider-preparation.zh-CN.md).

## Preparation responsibility

The manifest explicitly declares `provides`, `workflows` and `default_workflow`. The planner checks only the selected path's operations, input kind and startup mode. Provider maturity is separate from verification of that path.

The selected adapter builds, pushes and registers source through its native protocol. It preserves Dockerfile FROM, USER, COPY and ENTRYPOINT; `build_base_image` replacement is removed. Unresolved placeholders fail preflight. Application deployment hooks still run only through explicit application deployment.

## Path requirements

Python, named services and software can come from the image. Application HTTP does not require a unified interpreter. Exec, template services and unified interpretation declare and check their own operations. Unsupported contexts and real-time streaming fail explicitly; parameters are never dropped or replaced with shell execution.

E2B, Cube and container edition consume managed native references, not raw OCI image IDs. OpenSandbox consumes images and execd; it does not promise native Dockerfile ENTRYPOINT startup. Python Provider does not prepare source; callers supply an explicitly prepared image or managed reference.

Configuration, authorization, reachability and protocol failures are distinct. Platform and application credentials remain separate. Endpoints bind to the selected sandbox and port; no automatic redirects or anonymous retry.

## Ownership and acceptance

Persist intent before push/registration/create and record the returned ID afterward. Unknown responses are reconciled rather than retried blindly. Clean only resources owned by this invocation. Where image/native-template deletion is not implemented, report retained resources and manual recovery instead of complete cleanup.

Project verification requires trusted CI receipts bound to exact inputs, workflow, consumer and network position. Author fields cannot certify a path; historical guest/bridge success does not certify unified launch. See [workflow contracts and evidence](workflows.md), [using templates](using-templates.md) and [platform steps](platform-steps.md).
