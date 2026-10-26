# Immutable COPY source mode verification

Date: 2026-10-26
Result: PARTIAL
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/232

The [unchanged original failure](../../../next-app/evidence/verification-steps-2026-10-25T235550Z.json) records a first named CLI error E3000, no successful smoke/controller, and independent sandbox plus prepared-template absence. The [filtered source/mode diagnostic](2026-10-26-next-app-copy-permission-diagnostic.json) confirms that package.json and package-lock.json were Git 100644, local 0600 and generated immutable-fetch COPY 0600. Official CLI 0.5.6 retained the actual PermissionError / errno 13 for the static package path. No credentials, private endpoints or native resource identifiers are included.

Before the correction, the four selected mode/local cases returned two failures (0644/0600 and 0755/0700) and two passes (untracked and changed local 0640). A fifth, new Git-symlink negative case is included in the corrected suite; it is not counted as an executed old baseline case. After the correction, the combined preparation, native HTTP, image/archive, public-launch and actual-installed-parser checks passed 114 tests in 6.08 seconds with the official CLI 0.5.6 binary. The existing 0640 local behavior, changed-byte behavior, corrupt archive rejection and Git-symlink refusal remain exercised. Documentation links: 222 documents, zero failures; git diff --check passed.

Independent candidate cloud acceptance and latest-head CI remain pending. The frozen a936 all-template native matrix continues separately and is not modified. This helper change requires its own exact candidate evidence; the original matrix is never relabeled. Public CLI/SDK versions and business template inputs are unchanged. The default Express Docker journey remains BLOCKED.
