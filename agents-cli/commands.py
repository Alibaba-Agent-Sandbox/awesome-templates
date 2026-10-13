"""Codex and Qwen Code on the sandbox Agents API.

The image does not install either CLI. A turn looks up ``codex`` or ``qwen``
on ``PATH`` and runs only that binary. Install the one you are about to call:

    npm install -g @openai/codex
    npm install -g @qwen-code/qwen-code

``E2E_RUN_LLM=0`` (set by the local template runner) prepends ``e2e-bin/``.
Those scripts stand in for the CLIs so the HTTP surface can be tested without
a model key. They are not shipped as the default ``PATH``.
"""

from __future__ import annotations

import os
from pathlib import Path

from easy_sandbox.server import CapabilityGroup, SandboxServer, default_table

_HERE = Path(__file__).resolve().parent
if os.environ.get("E2E_RUN_LLM") == "0":
    os.environ["PATH"] = str(_HERE / "e2e-bin") + os.pathsep + os.environ.get("PATH", "")

os.environ["EBX_SERVER_ENABLED_GROUPS"] = "agents"

table = default_table()
table.enable_group(CapabilityGroup.FILE_OPS)
table.enable_group(CapabilityGroup.PROCESS)
table.enable_group(CapabilityGroup.AGENTS)

server = SandboxServer(route_table=table)
if __name__ == "__main__":
    server.serve(port=int(os.environ.get("EBX_SERVER_PORT", "9000")))
