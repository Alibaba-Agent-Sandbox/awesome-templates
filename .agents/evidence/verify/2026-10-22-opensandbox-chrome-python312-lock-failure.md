# Native Chrome controller Python3.12 lock failure

Result: FAIL

[Run39756780475](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39756780475)
at8c65d434f897fbf2a55692c77c4cf44fe47191c4 failed during controller dependency
installation, before native backend creation. Strict hash mode rejected the
unpinned conditional `typing-extensions` requirement. No native acceptance
receipt was produced; this is not a runtime pass. Supplement the browser's
Python3.13 lock with the exact original frozen server pin/hashes for Python3.12,
retain hash enforcement and rerun Chrome.
