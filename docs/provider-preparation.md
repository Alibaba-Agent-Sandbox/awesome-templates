# Provider-owned template preparation

A source directory is portable input. Native template IDs, image URIs and launch references belong to one provider/account/region and cannot be converted across clouds. [中文](provider-preparation.zh-CN.md).

## Preparation responsibility

The manifest declares one startup command and all services in `provides`. The planner derives the required provider operations from that startup and the services; authors do not select workflows. Provider maturity and actual launch verification remain separate.

The selected adapter builds, pushes and registers source through its native protocol. The CLI stages the official base recipe and resolves its `<region>`/`<tag>`; the Dockerfile installs its exact published server package. Application instructions, non-root USER and source files remain unchanged. Other unresolved placeholders fail preflight; a custom base is an explicit build profile. Application deployment hooks are separate from sandbox startup and run through their explicit application-deployment operation.

## Path requirements

Python, named services and software can come from the image. Application HTTP does not require a unified interpreter. Exec, template services and unified interpretation declare and check their own operations. Unsupported contexts and real-time streaming fail explicitly; parameters are never dropped or replaced with shell execution.

E2B, Cube and container edition consume managed native references, not raw OCI image IDs. OpenSandbox consumes images and execd; it does not promise native Dockerfile ENTRYPOINT startup. The unified Python `launch_template(...) -> TemplateSession` entry point does not build Registry source projects; callers supply a previously prepared provider image or managed reference.

Configuration, authorization, reachability and protocol failures are distinct. Platform and application credentials remain separate. Endpoints bind to the selected sandbox and port; no automatic redirects or anonymous retry.

## Ownership and acceptance

Persist intent before push/registration/create and record the returned ID afterward. Unknown responses are reconciled rather than retried blindly. Clean only resources owned by this invocation. Where image/native-template deletion is not implemented, report retained resources and manual recovery instead of complete cleanup.

Project verification requires trusted CI receipts bound to exact inputs, consumer and network position. Author fields cannot certify a path; historical guest/bridge success does not certify unified launch. See [launch contracts and evidence](workflows.md), [using templates](using-templates.md) and [platform steps](platform-steps.md).
