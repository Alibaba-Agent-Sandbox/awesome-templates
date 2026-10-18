# OSWorld writable image workspace — 2026-10-16

Status: PARTIAL. Refs [Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) and [draft PR 94](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/94).

## Actual third image result

Source ea6d7870f74ef046ec3708fa8103386c632437ff: [L1 run 38862566744](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38862566744), job 116848041735, FAIL. The actual Docker build succeeded, and the browser initialized successfully. Real image geometry was screen/outer 1024×768, viewport 1024×712 and content offset (0,56). This verifies the prior screen/viewport equality requirement was invalid for the pinned image. The subsequent smoke failed with PermissionError before task navigation when writing its disposable fixture in WORKSPACE. Its unchanged stage label still said browser-viewport; this label did not mean initialization failed.

Both full remote local suites succeeded: [PR run 38862566987](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38862566987) and [push run 38862561486](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38862561486). No successful image archive exists for this failed run.

## Correction

The Dockerfile's root-created WORKDIR was not assigned to the runtime user. `COPY --chown` assigned the copied files, but did not make their parent writable. Explicitly chown only `/home/user/app` to user:user before USER user. Keep all other permissions and HOME unchanged. The real L1 smoke's file-backed task write/remove remains a required behavioral check; no root fallback or disabled task is introduced. Set a separate fixture-creation diagnostic stage before the first write.

## Verification

PASS: 72 scoped regressions (43 OSWorld plus 29 existing selector), strict checker across all 19 directories, spec regressions (22 cases plus 25 subtests), changed Python syntax, local links and whitespace checks.

PASS native behavior A/B: with the same current worker and original HOME, a controlled owned workspace mode 0555 reproduced `PermissionError (fixture-creation)`. Making that same directory writable by its owner allowed the actual full GUI smoke, real upstream task score 0→1 and complete 4096-character Unicode DOM readback to pass. This uses the installed native Google Chrome 150 through official Playwright cache resolution; it validates the write boundary and source behavior, not image ownership or its pinned browser.

The new actual changed-image L1 remains pending. Earlier native and image evidence remains historical. Changed-image Express SDK/HTTP/CLI acceptance, owned provider cleanup and the full OSWorld benchmark remain unverified; the original Issue stays open.

## Source fingerprints

- `osworld/Dockerfile`: SHA-256 `633bcf37d2757675d8f46c6993acb8e6512b30d529b533d5a21d935d9f835123`.
- `osworld/runtime.py`: SHA-256 `a74944f97f6f3ee48057190dccbe2d2aee49305679f50c3a283bdd4ccf03bc55`.
- `osworld/commands.py`: SHA-256 `22f7814416e0dc52cb0c0b04deae8323467a785db6601d8b36603abcb396a78d`.
- `osworld/e2e_test.py`: SHA-256 `07a4fa0615a9329dff948d19c411c0e60e8b916465d725ea5aeff2f2ea3ab2d1`.
