# Build and test a template with native platform steps

[中文](platform-steps.zh-CN.md). This maintenance path prepares the template on
Alibaba Express without a local Docker daemon. The normal public template launch
path is described in [using templates](using-templates.md). A step-build receipt
and a Docker image receipt are separate evidence.

Install the current published CLI and Python client/server using the
[installation guide](using-templates.md), then install checker and controller
dependencies from this repository. Supply the existing Express account through
process environment. No credentials are uploaded to Actions by these commands.

```bash
python -m pip install -r scripts/requirements-spec.txt
python scripts/run_steps_e2e.py python-hello --timeout 900
```

This command runs the entire existing application controller. It generates native
steps from the selected Dockerfile, calls the native provider preparation API,
waits for the exact owned template to become READY, and invokes the current
`abx template launch` with a temporary managed manifest containing that prepared
ID and the original startup, readiness, services and environment declarations.
It then tests named commands through CLI, Python application client and HTTP,
checks source identity and files/process operations, and independently destroys
and reads back absence of its sandbox and prepared template. There is one launch
path; there is no CLI-versus-SDK creation selector.

The internal native `template deploy --build steps` performs preparation only;
it does not start a second application or replace current public launch. Native
status must be actual JSON strings/objects, never Python repr strings. The public
`template launch` does not acquire a new `--build steps` option.

## Inspect preparation without creating cloud resources

```bash
python scripts/prepare_steps.py python-hello --output /tmp/python-hello-steps
```

Use a new staging directory. The converter preserves ordered RUN, ENV, WORKDIR,
USER, heredocs and continuations. It transfers explicit public COPY inputs with
hashes and file modes. Missing, private or escaping inputs fail before cloud
submission. Larger profiles fetch the immutable public source archive and verify
all copied bytes; publish the exact source commit before cloud execution. The
original Dockerfile installs published server 0.4.0a2 directly from official PyPI;
there is no injected wheel, Git-server fallback or server-source selector.

The default base resolves to region `cn-hangzhou`, tag `v0.0.49`. Use `--region` or
`--base-tag` only when intentionally selecting a different provider base. A changed
base PATH requires an explicitly verified `--base-path`. Runtime remains non-root
`user`; preparation uses root only where the original installation requires it.

## Large public assets

`--asset-transport parallel` uses bounded independent requests for reviewed
upstream archives. `--asset-transport oss` uses a temporary private same-account
asset cache and requires its optional local SDK. Both verify declared sizes and
hashes and preserve the existing 15,000-byte provider wire limit. They do not
relax archive size, native-vendor or credential boundaries. Only the reviewed Muse
artifact has its documented exact size exception. OSS cache absence must also be
independently verified before PASS. Local reuse through
`ABX_STEP_LOCAL_ARCHIVE_DIR` still requires every original size/hash check.

## Evidence and failures

The current runner writes a distinct `evidence/verification-steps-<timestamp>.json`
for every attempt. A pass requires the application controller, sandbox cleanup,
prepared-template cleanup and optional asset-cache cleanup. Failure retains its
private staging/journal outside the checkout for owned recovery; public evidence
contains controlled failure categories, never private URLs, IDs or credentials.
Real model/vendor-account skips remain unverified and do not inherit a smoke pass.
A selected matrix stops before creating more resources if owned cleanup is uncertain;
recover only its exact recorded resources, then explicitly select the remaining templates.

Earlier [44-template native checkpoint](../.agents/evidence/verify/2026-10-21-current-native-http44.json)
and other dated receipts retain their exact versions and calling paths. They do
not certify the current package pins or migrated launch consumer. New real cloud
and image acceptance are recorded separately.
