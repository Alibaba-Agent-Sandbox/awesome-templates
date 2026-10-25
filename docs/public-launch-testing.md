# Test the public template launch path

This runner tests source preparation through the installed `abx template launch`,
then calls the template's manifest smoke commands through host CLI, Python and
HTTP. The manual workflow also runs each unchanged full HTTP application controller
with generated owned fixtures and an explicit service token. Controller pass/fail/skip
counts are recorded separately; skipped real-model or vendor-account paths remain
unverified. It does not rewrite a Dockerfile, run guest curl or substitute a Docker
bridge address. Its report distinguishes application success from resource cleanup.

Install the reviewed CLI and matching Python SDK, configure the backend and Docker,
then run from this repository:

```bash
python scripts/public_launch_e2e.py python-hello --provider alicloud-express --output express-attempt-1.json
python scripts/public_launch_e2e.py python-hello --provider opensandbox --output opensandbox-attempt-1.json
python scripts/public_launch_e2e.py --list
```

The default source is the public Git catalog. A new published attempt resolves its
current public Git HEAD and pins that immutable commit in the requested Git ref.
The report keeps the original request, resolved source commit and verifier commit
separate; an exported image names the actual pinned public source, while the
artifact/run identity names the verifier revision. The launched manifest and runtime
command source must match this checkout. For a candidate revision use
`--source ./python-hello`; the report records that this was a local candidate,
not a public Git template lookup. CLI/SDK package installation is recorded separately. An existing output file is never overwritten.

The manual **Public template launch matrix** GitHub workflow accepts exact reviewed
CLI, SDK and provider commits, a comma-separated selection or `all`, and either
backend or both, plus `distribution: published` (the default) or `source`.
Published mode reads the release versions from those exact CLI/SDK commits,
installs the fixed published npm/PyPI packages, and verifies installed versions.
The SDK checkout supplies the Docker backend fixture. The provider is installed
from the public Git URL at the exact selected commit. Templates are resolved through
the default public Git catalog; their manifest and runtime source must match the
workflow checkout unchanged.
Published mode fails if a selected version has not been published. Source mode builds the exact CLI checkout with `npm ci` and installs both Python packages from the exact SDK checkout; it is pre-release candidate validation, not published-package acceptance. Reports include the installation distribution and exact CLI/SDK/provider/template commits. `all` currently selects 46 source templates, with at most four
independent runners active at once. OpenSandbox uses
its real Docker server, provider-resolved direct endpoint and an owned local registry.
An optional `export_images: true` saves the exact successful launch-owned image,
archive SHA256 and package/source provenance before cleanup. The one-day image
artifact supports a separately labelled prepared-image backend test; it does not
prove another backend's source preparation path. Export refuses foreign or
ambiguous images.
The workflow explicitly selects the provider default `use_server_proxy=false`; it
does not silently fall back from proxy mode. Proxy authentication is a separate probe.
Express uses the `PUBLIC_LAUNCH_*` credentials explicitly configured for that
workflow. Missing credentials fail the attempt; they never become a cloud pass.

Checks use each manifest's expected output where supplied. Diagnostic commands
without an `expect` require successful nonempty results independently on each
consumer; their output may legitimately vary. These cases prove the call path,
not the correctness of the reported business state. The suite does not claim real-model
business acceptance. The source recipes' smoke commands must be safe to repeat;
application-specific full controllers remain separate tests.

The runner deletes known owned sandboxes and confirms absence through independent SDK control-plane reads. For Express, it deletes journal-owned templates and reads the complete
inventory using explicit `--native --json` (without a standard-only `--format` flag),
then removes exact owned Hangzhou ACR tags using the existing cleanup
verifier. Other registry types remain explicit pending cleanup. For the disposable
OpenSandbox registry it removes exact owned manifests, checks absence and removes
local tags. An uncertain intent is not blindly replayed. The private CLI journal
contains recovery identifiers; raw subprocess diagnostics stay in a mode-0700 temporary
`abx-public-launch-*` directory with mode-0600 files and are not uploaded; reports contain counts and outcomes, never keys or
native IDs. The generated test alias, controlled failure phase/category, stable SDK
error code and numeric HTTP status may be recorded for recovery; dynamic exception
messages are never included. `PARTIAL` is a nonzero result and must be reconciled before claiming a
complete acceptance.

## Reuse an exported image for separate Express acceptance

On a host without Docker, a successful published OpenSandbox launch can export its exact owned image for a separate prepared-image Express run. This tests image registration and the actual Express sandbox/API; it does not prove Express source preparation on that host. Use an unexpired export from a completed successful workflow, the matching unchanged template input and a checksum-verified upstream `crane` executable:

```bash
ABX=abx python scripts/run_image_e2e_batch.py --workflow-run WORKFLOW_RUN_ID \
  --crane /path/to/verified-crane --private-root /path/to/private-staging \
  --output /path/to/express-results.json --rerun --workers 1
```

Public exports identify the pinned public template commit separately from the verifier workflow commit, installed official packages, observed runtime server version and the CLI source snapshot. The consumer validates both revisions, source bytes, archive bytes and image runtime bytes before registry transfer. It registers the image without starting an application, then reuses current `template launch` with the exact owned template ID and the original services/startup/environment. CLI, the public `ProviderSandbox` application client and host HTTP call that same service; there is no separate test-only application instance. Host HTTP respects the configured environment proxy and TLS verification. Registry credentials remain in anonymous RAM; each nonce-owned private repository, platform template and sandbox is cleaned and independently checked. Historical source-built L1 exports keep their original scope.

For the two Express-managed catalog entries, no image build is needed:

```bash
python scripts/verify_managed_templates.py base code-interpreter-v1 --cli abx --output managed-results
```

This uses the current bare-name public CLI launch, Python shell/files, non-root inventory and independent cleanup; the interpreter image also executes a real numerical-package dataframe operation. It does not certify persistent interpreter sessions. Other providers' managed entries retain their declared native identity and must not be substituted.

## 中文

本工具通过已安装 CLI 的 `template launch` 准备源码，然后从宿主 CLI、Python 和
HTTP 调用清单中的 smoke 命令。它不手改 Dockerfile，不在沙箱内 curl，也不改用
Docker bridge 地址。默认读取公开 Git 目录；测试候选输入可明确指定本地
`--source`。启动清单与实际运行命令源码都须和本地验证输入一致。

手动矩阵工作流接受准确的 CLI、SDK、provider 提交、模板选择和平台，以及 `distribution: published`（默认）或 `source`。
从这些精确提交读取版本，安装固定版本的 npm/PyPI 公开包并核对安装结果；SDK 源码只提供本地后端 fixture，provider 从公开 Git 地址安装精确提交；模板通过默认公开 Git 目录解析，并与本次工作流清单和运行源码逐字节核对。published 模式下未发布的版本会安装失败。source 模式使用 `npm ci` 构建精确 CLI checkout，并从精确 SDK checkout 安装两个 Python 包；这是发布前候选验证，不是公开包验收。报告记录安装来源和 CLI、SDK、provider、模板的精确提交。
`all` 当前为 46 个源码模板，最多同时运行四个独立 runner。OpenSandbox 使用真实 Docker 服务及 provider 返回的直连端点（明确选择默认的 `use_server_proxy=false`）；
Express 使用该工作流配置的凭据。缺凭据不能算通过。

有 `expect` 的命令逐入口断言输出；没有的诊断命令分别检查调用成功和非空结果，
不要求时间等动态信息相同；这种结果仅证明调用链成功，不能证明业务状态正确。
smoke 必须可重复执行，真实模型业务和完整应用控制器
另行验证，不由本次结果代替。

应用结果与资源清理分开记录。仅删除启动记录中确切属于本次的资源，并独立回查。
不认识的镜像仓库和不明确的提交保留为待处理，不能推定删除成功。`PARTIAL` 返回
非零退出码；原始失败不被之后的清理或重跑覆盖。

可选 `export_images: true` 会在清理前保存本次成功启动实际构建的唯一镜像、SHA256 和包/源码来源，保留一天，供另一个明确标记的已有镜像后端实验使用；它不能证明另一平台的源码准备路径。非本次或不唯一的镜像会拒绝导出。


## Native provider-owned catalog entries

Select `templates: managed` and `provider: opensandbox` in the same manual workflow. This native journey installs the
published npm CLI and paired PyPI client/server versions resolved from the selected
exact CLI/SDK commits, the pinned provider from its
public Git URL and upstream `opensandbox-code-interpreter==1.1.1`. It launches
`opensandbox-code-interpreter` through the public catalog, exercises CLI shell and
Python shell/files, then runs real native persistent/isolated interpreter contexts,
program error and context-deletion assertions. SDK NotFound and Docker observations
independently verify cleanup. The same attempt checks that the three foreign
provider identities (`base`, `code-interpreter-v1`, `desktop`) are rejected on
OpenSandbox without creating containers. These entries are reported
`NOT_APPLICABLE`, never as a successful cross-provider launch.

中文：同一手动工作流选择 `templates: managed`、`provider: opensandbox`，从公开包和公开
provider Git 地址开始，测试内置解释器模板的 CLI 启动、进程/文件，以及真实原生
持久上下文、隔离、程序异常和上下文删除；SDK 与 Docker 独立确认资源清理。
另外三个绑定其他提供方的内置标识会验证明确拒绝和未创建容器，记为
`NOT_APPLICABLE`，不能算跨平台启动成功。


The controller helper accepts provider `gateway_headers` separately from the generated
application token. It supplies validated string headers through
`E2E_GATEWAY_HEADERS_JSON` and the application token only through
`ABX_SERVER_TOKEN`. Retired token aliases are not read or injected. Standalone controllers
merge gateway headers into HTTP and Python application-client requests; application
Bearer authentication remains separate from gateway access-token headers. Arbitrary
operator environment keys are not forwarded. Invalid header objects or conflicting
Authorization headers fail before the controller starts.

中文：公开源码启动前会解析并固定当前 Git HEAD；报告分别记录最初请求、实际固定
源码提交和验证程序提交。测试客户端通过受控 JSON 环境变量传递 provider 网关头，
应用 Bearer 令牌只通过 `ABX_SERVER_TOKEN` 传递，不读取或注入旧变量别名，
也不借用其他操作员凭据。非法网关头和冲突的 Authorization 会在运行前明确失败。

The Dockerfile installs its exact published server package from the official PyPI
index, independently of a base image's configured mirror. Actual guest acceptance
reads back the installed distribution and compares it to that declaration. A
source-mode host SDK checkout does not imply a source-built guest server.

### 极速版独立镜像验证与内置模板

本机没有 Docker 时，可以消费公开包 OpenSandbox 启动流程导出的原镜像，单独验证极速版镜像注册、真实沙箱及 API。上方 `run_image_e2e_batch.py` 命令只接受成功工作流的未过期产物，并核对公开模板提交、验证器提交、完整内容指纹、实际运行字节与公开包来源；它不代表本机完成了极速版源码构建。镜像注册时不预启动应用，而是复用当前 `template launch` 和原清单的启动命令、服务与环境；CLI、Python 应用客户端及宿主 HTTP 均调用同一个真实服务，不另起测试专用服务。宿主 HTTP 遵循正常代理环境并保留 TLS 校验。临时私有镜像仓库、平台模板和沙箱均按本次唯一标识清理并独立复核，凭据不落盘。

`verify_managed_templates.py base code-interpreter-v1 --cli abx` 从公开目录按原生名称启动极速版内置模板，再验证 Python 进程／文件、CLI 与清理；数据处理镜像另执行实际 DataFrame 运算。不包含持久解释器会话验证，也不把其他平台的原生模板替换成近似镜像。

Current acceptance also executes the published CLI's process command and transfers
an owned UTF-8 file using `abx upload` and `abx download`. The SDK independently
reads the same bytes, and CLI stat/removal plus SDK absence confirm the owned file
round trip. These checks do not imply PTY or native interpreter support.
