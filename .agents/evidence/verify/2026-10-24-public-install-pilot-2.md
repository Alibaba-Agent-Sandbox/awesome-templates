# Published-package launch pilot

Result: PASS

[Run 40115231628](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40115231628)
passed both `python-hello` jobs and their cleanup steps. Each fresh hosted runner
installed CLI `0.4.16` from npmjs.org and client/server `0.3.1a5` from PyPI with
`--no-cache-dir`, verified installed metadata, and passed `pip check`. These are
host-runner package versions. The template image retains its own fixed server SDK
source from the recipe; this run does not claim an in-image server version of a5.

Exact source inputs:

- Templates: `e581d273aa1b7bbc099da8c4c7745c1728230364`.
- CLI: `413d575a688bd6f870c42c711d11346d176e0f38`.
- Python SDK: `1b235830bc4a8cbec275b530bf2dc2869e8d0c4b`.
- Providers: `e18489155697dcf2ee55a47b403396069d6cfa20`.

Provider installation and template selection used fixed local Git checkouts; this is
public package installation evidence, not the remote provider/template download
journey. Express exercised its native build path. OpenSandbox 1.1.1 exercised the
default direct endpoint and the CLI's unchanged default-recipe preparation. The
runner did not rewrite a template, substitute a Docker bridge address, or call its
HTTP API from inside the guest.

Both jobs passed manifest/runtime source identity, the two manifest smoke calls
independently through CLI, Python and host HTTP, wrong application token rejection
with HTTP 401, SDK process execution and file round trip. Both reports confirmed
sandbox and prepared artifact absence with zero cleanup failures, retained artifacts
or uncertain intents. The final hosted-runner backend cleanup steps also succeeded.

[Original sanitized reports](2026-10-24-public-install-pilot-2/) remain byte-for-byte
copies of their workflow artifacts. The first public installation attempt
[40114977362](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40114977362)
remains FAIL: its runners could not yet resolve PyPI `0.3.1a5`, and neither reached
cloud setup or application launch. Its existing receipt is not replaced by this pass.

This pilot does not certify other templates, real-model tasks, desktop, PTY,
interpreter, or server-proxy behavior. Full matrix results belong to their own
point-in-time receipt; https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/203
remains open until its requested acceptance is complete.
