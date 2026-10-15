# <name>

Copy this file to `docs/design/<name>.md` and fill every section before opening the template PR. Keep the headings. `scripts/check_template.py` requires them for a `spec_version: 2` template other than `_skeleton`.

## Purpose

Who runs this, and the job the sandbox does. One short paragraph.

## Capabilities

What the sandbox can do after it is READY: commands, files, ports, browsers, desktops. State the slice that Express can run when the full upstream product cannot.

## Exposed API

Every named command. For each one: name, parameters (name, type, required, default), return value, and the upstream argv it executes.

## How to build

Base image, pinned package versions, `start_cmd`, `ready_cmd`, and any build-time file that must be in the context. Link the Dockerfile lines that pin versions.

## Express feasibility

Feasible: yes | slice | no

Limiting factor: <the single hard constraint, or none>

Say whether Express (non-root `user`, 2 vCPU, no KVM, no Docker, no extra capabilities, about 10G rootfs, egress allowed) can run the whole template or only the slice in Capabilities.

## Risks

Secrets, network calls, privileged operations, unpinned downloads, and what the template refuses to do.

## Test plan

L0 command and expected result. L1 image pin to look for in the build log. L2 smoke list (`template.yaml` `smoke`) and the assertion. L3 only when a key is available, including the `ABX_E2E_OK` marker. L4 only for a provider this plan will actually run.
