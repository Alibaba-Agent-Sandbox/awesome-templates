# Immutable COPY source mode verification

Date: 2026-10-26
Result: PARTIAL
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/232

The [unchanged original failure](../../../next-app/evidence/verification-steps-2026-10-25T235550Z.json) records a first named CLI error E3000, no successful smoke/controller, and independent sandbox plus prepared-template absence. The [filtered source/mode diagnostic](2026-10-26-next-app-copy-permission-diagnostic.json) confirms that package.json and package-lock.json were Git 100644, local 0600 and generated immutable-fetch COPY 0600. Official CLI 0.5.6 retained the actual PermissionError / errno 13 for the static package path. No credentials, private endpoints or native resource identifiers are included.

Before the correction, the four selected mode/local cases returned two failures (0644/0600 and 0755/0700) and two passes (untracked and changed local 0640). A fifth, new Git-symlink negative case is included in the corrected suite; it is not counted as an executed old baseline case. After the correction, the combined preparation, native HTTP, image/archive, public-launch and actual-installed-parser checks passed 114 tests in 6.08 seconds with the official CLI 0.5.6 binary. The existing 0640 local behavior, changed-byte behavior, corrupt archive rejection and Git-symlink refusal remain exercised. Documentation links: 222 documents, zero failures; git diff --check passed.

The [independent candidate next-app control](../../../next-app/evidence/verification-steps-2026-10-26T001520Z.json) ran at exact candidate `3db65881372352f8cc390d54e3550b2d4ea8b6f4` with official CLI 0.5.6, client 0.4.0a6 and guest server 0.4.0a6. It passed in 114.225 seconds: both declared commands through CLI, SDK and external HTTP (six calls), controller 6 PASS / 0 FAIL / 0 SKIP, original startup, wrong-token rejection, runtime byte identity, and CLI/file round trips. Sandbox and prepared-template absence were independently confirmed; no owned cleanup remains unresolved. This is native prepared-source/application supplemental acceptance, not a Docker-to-ACR build.

The [static all-46 COPY audit](2026-10-26-all46-immutable-copy-mode-audit.json) forced the existing immutable archive branch without a cloud submission. Across 46 source templates and 232 declared COPY files, all candidate modes match their exact regular Git modes. All 232 private-checkout modes differed from those Git modes; the complete old/new table is preserved. All input byte hashes and runtime environment values were unchanged. This is a static provenance audit, not 46 extra cloud passes.

Latest-head CI remains pending. The frozen a936 all-template native matrix continues separately and is not modified. This helper change requires its own exact candidate evidence; the original matrix is never relabeled. Public CLI/SDK versions and business template inputs are unchanged. The default Express Docker journey remains BLOCKED.
