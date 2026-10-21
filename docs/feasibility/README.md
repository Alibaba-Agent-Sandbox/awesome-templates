# Platform and product feasibility

[中文](README.zh-CN.md). Review date:2026-10-21. Issues [37](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/37), [38](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/38), [39](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/39), [42](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/42) and [43](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/43) explicitly allow an evidence-backed decision/integration design. This delivers that outcome; these products are not installable verified templates.

| Product | Decision for the tested Express profile | Integration prerequisite |
| --- | --- | --- |
| Windows Agent Arena | Defer the complete Windows VM; do not replace it with a Linux version wrapper | An owned Windows11 WAA snapshot/VM with the original Windows server and licensed image, or a suitable VM/container host |
| Phone sandbox | Defer Android device provisioning; no usable device pool was established | A provider exposing a real authorized Android device/emulator and required control channels |
| AndroidWorld | Defer the original evaluation until a compatible device is supplied | API33/Pixel6-compatible emulator, original apps, ADB and emulator gRPC accessibility connection |
| K3s | No qualified template for the evaluated non-root generation2 profile; retain seven actual failed native attempts | A profile that actually supports the selected original server/API and, for a full cluster, privileged container/worker networking |
| Omarchy | Do not package the Arch desktop's maintenance helpers as a Debian application | An independently provisioned compatible Arch/Omarchy desktop/VM; remote maintenance is a separate product |

## Executed checks

An actual SDK-created, uniquely owned Express managed `base` ran [the read-only guest probe](../../scripts/guest_runtime_features.py), returned UID1000/Linux/x86_64/Debian13, and was killed with independent `get_info_by_id` absence verification. The guest exposed no `/dev/kvm`, `/dev/dri`, `/dev/net/tun` or Docker socket; opening KVM returned ENOENT. Docker, Podman, QEMU, Android emulator/ADB, pacman, systemctl and hyprctl were absent in this image. User namespace probe exited0; mount namespace probe exited1. Observed guest MemTotal was2093MiB despite the create request's4096MB: do not infer a larger effective memory allocation from requested parameters.

[Sanitized SDK/cleanup evidence](../../.agents/evidence/verify/2026-10-21-express-guest-features.json), [upstream pins/hash inventory](../../.agents/evidence/verify/2026-10-21-hardware-products-upstream.json), [other-provider prerequisite probes](../../.agents/evidence/verify/2026-10-21-other-provider-prerequisites.json).

These are managed-base observations. Missing preinstalled tools can be installed; missing KVM alone does not prove that software emulation is impossible. No emulator boot, Windows desktop action, AndroidWorld task/reset/evaluator or Omarchy system update passed in this review. These decisions certify no Express L2 product or model result, and add no misleading `tested_on` or installable catalog entry.

The provider prerequisite table below records the initial operator environment. Later hosted OpenSandbox interpreter verification is tracked separately in its [managed guide](../managed/opensandbox-code-interpreter/README.md); it is not a test of these hardware/cluster products.

## Provider scope

| Provider | Actual result |
| --- | --- |
| alicloud-express | Owned SDK guest probe and independent cleanupPASS; product acceptanceNOT_RUN |
| alicloud-container | No explicit cluster domain/base URL/API key configured; no ACS/ACK hardware or device-pool claim |
| opensandbox | No explicit server settings. Default local TCP accepted, but read-only `/openapi.json`, `/sandboxes`, `/health` returned RemoteProtocolError; no usable server established |
| cubesandbox | No explicit server settings. Default local TCP accepted, but the same read-only routes returned RemoteProtocolError; no usable CubeAPI established |
| e2b | No explicit ABX_E2B_API_KEY/configuration. Generic E2B_API_KEY equals the Express alias and was never forwarded |

A TCP accept does not prove a compatible sandbox service. Provider-advertised exec/files capabilities do not prove privileged nesting/KVM/devices. No new cluster was provisioned and no unrelated local process was changed. Recheck all prerequisites and the actual selected image when an endpoint/device becomes available; do not convert Express template IDs into another provider's image IDs.

## Product-specific findings

### Windows Agent Arena

Original [README at6d39ed88](https://github.com/microsoft/WindowsAgentArena/blob/6d39ed88c545a0d40a7a02e39b928e278df7332b/README.md) requires a Docker host and a Windows11 golden snapshot of approximately30GB, with a roughly6GB licensed evaluation ISO for setup. Its [launcher](https://github.com/microsoft/WindowsAgentArena/blob/6d39ed88c545a0d40a7a02e39b928e278df7332b/scripts/run.sh) defaults to8G VM RAM, requests NET_ADMIN and supports `KVM=N` when KVM is missing. Therefore “no KVM means WAA can never run” is incorrect. The supplied original full VM workflow has not been ported into the repository's non-root8GiB source-image profile. A Python evaluator import or HTTP mock would not demonstrate a Windows task.

Remote integration: run the original Windows server on a user-owned Windows VM; keep the original Linux client/evaluators pinned, connect through explicitly authorized private transport, and exercise one original task from reset through screenshot/action and original evaluator. Verify actual Windows files/application state, preserve the original test/evaluator, save a sanitized result and independently clean only run-owned session/artifacts. Do not kill the caller's VM or invent a generic control endpoint. The original upstream server/client contract must be reviewed before implementing a new named-command API. This remote workflow is a design, NOT_RUN without that VM.

### Phone sandbox

The available Express profile exposes no Android device, KVM or device manager. Other configured provider endpoints did not establish a usable device pool in this review. This is a statement about accessible configuration, not proof that those products cannot offer devices. A future integration must identify a real provider/device API, pin Android image/API/ABI and app licenses, authenticate the assigned device, check boot completion and ADB identity, run an actual input/screenshot/file round trip and clean only its own device lease. Reconnect/reset and cancellation must preserve unrelated devices. ADB package installation or an echo server is insufficient. Software emulation remains unmeasured, not ruled out.

### AndroidWorld

Original [README atf8e78c0](https://github.com/google-research/android_world/blob/f8e78c0ab0bb8b5daa681afd0296ed0193a98f1f/README.md) and [env_launcher](https://github.com/google-research/android_world/blob/f8e78c0ab0bb8b5daa681afd0296ed0193a98f1f/android_world/env/env_launcher.py) target Pixel6/API33 with an already launched emulator and gRPC8554 accessibility connection; the documented Docker path uses `--privileged`. A generic physical phone or remote ADB alone does not establish that interface. Software-emulated compatibility/performance was not tested.

Remote design: forward the original emulator console/ADB and authenticated gRPC channel from an explicitly owned compatible host, pin the upstream source and apps, initialize using the original `load_and_setup_env`, run a selected original task/evaluator, verify state before/after and repeat reset. Required device identity, accessibility observation, input action and evaluator success must be actual; model success is separate. Cleanup ends only owned forwards/processes/task fixtures, leaving caller devices untouched. No compatible emulator was available, so this remains NOT_RUN.

### Omarchy

Original [repository at087f73d8](https://github.com/omacom/omarchy/tree/087f73d899b456ce5275ebf27294d379585fbdb1) does have an Omarchy CLI and headless maintenance scripts. For example, [omarchy-version](https://github.com/omacom/omarchy/blob/087f73d899b456ce5275ebf27294d379585fbdb1/bin/omarchy-version) reads Arch pacman packages for the installed system, while [omarchy-update](https://github.com/omacom/omarchy/blob/087f73d899b456ce5275ebf27294d379585fbdb1/bin/omarchy-update) operates on system packages and a privileged Bash/sudo boundary. Its non-default source-directory `dev` output establishes no installed desktop. The [installation manual](https://learn.omacom.io/2/the-omarchy-manual/50/getting-started) describes an ISO/dedicated-drive distribution, not a Debian pip/npm application.

Defer a source template: maintaining a separate Arch desktop VM through its real CLI may be useful, but this review has no such system and no demonstrated benefit from copying system-update scripts into Debian. No destructive OS installer/update was run. Reopen implementation when an owned compatible VM and a concrete remote-maintenance task are supplied; then test original package/version checks, a bounded task with observable state and cleanup. Existing generic shell templates already provide a terminal; renaming one Omarchy would misrepresent the product.

## K3s

[Issue42](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/42) explicitly says “Express expected: no” and permits a decision based on evidence. No installable K3s entry is published for the evaluated profile. Full worker/container-runtime nesting was not established; a narrower original agentless control-plane validation prototype also did not meet its real readiness/server-side validation gate.

Seven canonical Alibaba Express attempts used originalv1.37.1+k3s1, source356c025475bbefaa09cf0d7e48e8e2adbbde57db and original81543330byte binary SHA25692b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0. They exercised step preparation, READY, actual SDK creation, original CLI/HTTP version/help and attempted original API startup. All seven failed full native acceptance and independently confirmed owned VM/template/cache cleanup. [Exact run inventory](../../.agents/evidence/verify/2026-10-21-k3s-final-feasibility.json).

Observed failures included upstream default-route selection and rejection of a link-local advertised IP. Supplying node IP removed the first failure; querying assigned interfaces still did not establish an accepted non-link-local address in the evaluated custom worker. A separate managed-base guest exposed a usable interface, which cannot be transferred as proof for a different registered image/profile. Do not infer all Express deployments are impossible from these specific failures. No synthetic advertised address, patched original binary or skipped readiness gate was used.

[Unqualified reviewed experiment](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/tree/0e28a5021473e11ed549fad6b08e5ccd796f9b07/k3s) and [rejected prototype decision](../../.agents/notes/rejected/2026-10-21-k3s-agentless-validation.md) preserve the exact implementation and limitations for future work. It is research history, not an installation recommendation. There is no current `abx template launch ...//k3s` or deploy/steps recipe advertised by this catalog.

A future implementation requires an actually accessible suitable provider/profile, exact original pins and license, actual readiness, SDK-triggered server-side valid/invalid manifest tests and independent cleanup. A full Kubernetes claim additionally needs a real worker, container runtime, pod scheduling/execution and observed network/storage behavior; the agentless slice cannot stand in for them. Standard hosted OpenSandbox interpreter verification is separate and does not establish privileged K3s support.

## Reproduce the guest observation

Install the [paired Python client](../python-client-installation.md), configure your own provider and run the same source through the SDK in an owned sandbox:

```python
import asyncio
from pathlib import Path
from agent_sandbox.api.sandbox import Sandbox
from agent_sandbox.models.errors import SandboxNotFoundError

async def main():
    sb = await Sandbox.create(template="base", cpu=2, memory=4096, timeout=180)
    sid = sb.id
    try:
        await sb.files.write("/tmp/owned-guest-feature-probe.py",
                             Path("scripts/guest_runtime_features.py").read_text())
        result = await sb.commands.run("python3 -I /tmp/owned-guest-feature-probe.py", timeout=30)
        assert result.exit_code == 0
        print(result.stdout)
    finally:
        try:
            await sb.kill()
        finally:
            await sb.close()
    try:
        await Sandbox.get_info_by_id(sid)
    except SandboxNotFoundError:
        pass
    else:
        raise RuntimeError("owned sandbox remains; cleanup is not verified")

asyncio.run(main())
```

This reproduces a feature probe, not any of the evaluated products. The recorded run additionally reconciled ambiguous creation by its unique metadata in a private owner journal. Never publish IDs, credentials or raw provider logs. Installation/build commands for a qualified product remain unavailable until a real source profile exists; there is no `abx template deploy` or steps recipe for these decisions.
