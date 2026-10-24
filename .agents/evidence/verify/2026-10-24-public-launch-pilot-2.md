# Public launch pilot after native cleanup correction

Result: PASS

[Run 40109264062](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40109264062)
completed successfully for `python-hello` on both alicloud-express and OpenSandbox.
Exact inputs: templates `5d708617568fec0b647aaeb886f008a9725316a5`, CLI
`25e22d8f5c38bb0b7636ba699511da4f4695ec48`, paired SDK
`6398c6fdd777ff6c8ae9c7b2acb4cc52d457a633`, and providers
`4b4027cac0ec145aa89bdddda36cf8f7268c8d0e`.

Both jobs installed a packed candidate CLI, matching SDK source and local provider
checkout on independent Ubuntu hosted runners with Node22 and Python3.13.
This verifies installed-package public command behavior, not installation from npm/PyPI.
The unchanged default recipe was prepared by CLI `template launch`; no runner-side
Dockerfile rewrite, guest HTTP, or Docker bridge address substitution was used.

Both passed manifest and runtime-source identity, CLI/Python/host-HTTP expected
results, wrong-token rejection, SDK process execution and file write/read/removal.
Both reports independently confirmed sandbox and prepared artifact absence with
zero cleanup failures, retained artifacts or uncertain intents. Express used native
template deletion/listing plus exact ACR tag cleanup; OpenSandbox used its owned
local registry and independent sandbox cleanup.

OpenSandbox explicitly used the provider's default direct endpoint mode. This is not
proxy acceptance and does not replace the original failed proxy report. The separate
same-sandbox proxy authentication investigation is tracked in
https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues/31 . No real-model
business tasks or the other45 source templates are certified by this two-job pilot.

Original sanitized reports: [pilot2 directory](2026-10-24-public-launch-pilot-2/).
The earlier failed attempt and subsequent independent cleanup readback remain intact.
Issue https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/203 stays open
until the complete requested matrix and its cleanup are executed.
