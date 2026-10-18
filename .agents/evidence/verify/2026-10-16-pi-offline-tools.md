# Pi offline tools, frozen dependency tree and changed-image export batch

Date: 2026-10-16
Result: PARTIAL

## Revision and observed product defect

Follow-up scope on draft [PR 86](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/86), after e83cfa32061d9a87f22e93deb00b30e5dea6be87. Exact files are the Pi runtime/installer/tool-smoke/npm lock, bilingual usage/design/current backlog, local/image workflows, image selector/export task policy and regressions. Historical survey files are unchanged.

The installed official Pi 1.3.0 `createFindToolDefinition(...).execute(...)` actually failed with exit 2 and `fd is not available and could not be downloaded` when offline and fd/fdfind were absent. Installed source confirms find requires fd, grep requires rg, and PI_OFFLINE disables their automatic downloads. Earlier protocol fixtures checked tool availability lists but did not execute those tools. Version-only image smoke could not detect this prerequisite. This is a real runtime gap, even if a particular base accidentally already supplies those binaries.

## Fix and provenance

- Official fd 10.5.0 and ripgrep 15.2.0 Linux musl archives are fixed by their immutable release URLs and GitHub-published SHA256 digests for x86_64/aarch64. Native x86_64 downloads total approximately 3.8 MB and both checked digests and actual versions passed. Native arm64 execution was NOT RUN; its published asset digests were verified as metadata.
- The complete extracted fd distribution, including LICENSE-MIT/LICENSE-APACHE, remains under /opt/pi-tools. The rg archive retains LICENSE-MIT, UNLICENSE, COPYING and other files; COPYING states MIT/Unlicense dual licensing. Actual archive files were inspected. Direct links to real fd/rg executables avoid Debian's fdfind naming ambiguity.
- Committed package.json requires exactly Pi 1.3.0; package-lock freezes all 118 resolved npm packages, with public official registry URLs/integrity. `npm install --package-lock-only --offline --ignore-scripts` passed without another package installation. Every locked package version matched the existing actual installation (118 checked, zero absent). Node 24's `npm ci --dry-run --offline --ignore-scripts --omit=dev` passed; this is lock validation, not a fresh native install. Actual image CI must execute npm ci.
- `pi_tools_check` invokes the installed official read/find/grep/ls implementations against disposable real files, with a fresh config and offline mode; no model request or custom replacement tool implementation is used. It is now a named command and template smoke. Image pins additionally check fd/rg versions.
- The public .github/image-export-policy.json temporarily enables all-selected automatic archive saving for the authorized changed-image L2 batch. It cannot alter image selection, build, keyless smoke or their results. Dispatch export_images=false still disables manual exports. Remove the task flag or set automatic=default after the batch; the ordinary automatic scope is Pi/python-hello. No cloud/model credentials are inputs and no registry push occurs in CI.

## Actual local verification

- Official read/find/grep/ls execution: PASS, `read/find/grep/ls OK`, no model, disposable fixture cleanup by the Python owner.
- Missing fd and missing rg: two real offline process regressions fail explicitly, rather than silently advertising working tools. Corrupted installer bytes are rejected before archive extraction/execution; unknown architecture refuses to download.
- `python -m pytest -q pi/test_commands.py pi/test_e2e_protocol.py pi/test_cli_protocol.py pi/test_install_tools.py scripts/test_select_image_templates.py`: 79 distinct PASS (command/process 25, verifier 18, actual CLI/tool protocol 5, installer 2, selector/export policy 29).
- `python scripts/test_spec_tools.py`: 22 PASS, including actual preparation of all 17 template contexts.
- `python scripts/check_template.py --all --strict`: 18 conformant directories, zero failures.
- Targeted Pi local HTTP suite: 10 PASS, including actual offline tools, exit 0; model acceptance explicitly SKIP. The target server and disposable fixture/config cleanup passed.
- The first tool-smoke assertion expected a grep line with no separator space; actual upstream output includes `:1: `. Correcting the fixture expectation produced the genuine tool pass above. This was a smoke assertion correction, not a model pass.

## Separate historical scope and pending gates

The earlier source/model 17-check pass belongs to b2857609735c1da8529ba8ecf3d065076cdfb542. It does not automatically verify this later tool/lock scope. Three precondition/diagnostic attempts had stopped before model invocation on local file-root HTTP 403; the current earlier evidence now states that count accurately.

The e83 image workflow run 38851965467 actually completed 17/17 images plus plan successfully, and both local runs 38851965438/38851960798 succeeded. Those results establish their old scope, including only the earlier Pi version smoke. New offline-tool/frozen-install image L1, all-selected archive upload, changed-image Express L2 and image-backed model L3 remain PENDING actual execution. Do not promote the catalog or list a verified provider on this evidence.

## Cleanup and limits

Per-command fixture/config directories and process groups are cleaned; downloaded archives use temporary directories and are removed after extraction. The small verified native distributions are retained in the isolated tool prefix for reuse. No cloud resource or model call was created by this follow-up. The process-group/setsid, buffered-output and HTTP-disconnect limits remain as documented. No stale failed/queued job is counted as a pass.

Independent peer review: PASS, no blocking findings. The reviewer independently re-fetched official release metadata and matched all four archive digests, inspected preserved license files, and actually executed the official four tools with the pinned native binaries in an independent disposable workspace/config (exit 0). The reviewer also checked that temporary all-selected saving cannot alter selection/gates and manual export false remains effective.
