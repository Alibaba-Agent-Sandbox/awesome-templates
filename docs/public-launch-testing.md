# Test the public template launch path

This runner tests source preparation through the installed `abx template launch`,
then calls the template's manifest smoke commands through host CLI, Python and
HTTP. It does not rewrite a Dockerfile, run guest curl or substitute a Docker
bridge address. Its report distinguishes application success from resource cleanup.

Install the reviewed CLI and matching Python SDK, configure the backend and Docker,
then run from this repository:

```bash
python scripts/public_launch_e2e.py python-hello --provider alicloud-express --output express-attempt-1.json
python scripts/public_launch_e2e.py python-hello --provider opensandbox --output opensandbox-attempt-1.json
python scripts/public_launch_e2e.py --list
```

The default source is the public Git catalog. The launched manifest and runtime
command source must match this checkout. For a candidate revision use
`--source ./python-hello`; the report records that this was a local candidate,
not a public Git template lookup. CLI/SDK package installation is recorded separately. An existing output file is never overwritten.

The manual **Public template launch matrix** GitHub workflow accepts exact reviewed
CLI, SDK and provider commits, a comma-separated selection or `all`, and either
backend or both, plus `distribution: published` (the default) or `source`.
Published mode reads the release versions from those exact CLI/SDK commits,
installs the fixed published npm/PyPI packages, and verifies installed versions.
The SDK checkout supplies the Docker backend fixture; the provider installs from
the exact selected checkout. Template source uses this workflow checkout unchanged.
Published mode fails if a selected version has not been published. Source mode builds the exact CLI checkout with `npm ci` and installs both Python packages from the exact SDK checkout; it is pre-release candidate validation, not published-package acceptance. Reports include the installation distribution and exact CLI/SDK/provider/template commits. `all` currently selects 46 source templates, with at most four
independent runners active at once. OpenSandbox uses
its real Docker server, provider-resolved direct endpoint and an owned local registry.
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

## 中文

本工具通过已安装 CLI 的 `template launch` 准备源码，然后从宿主 CLI、Python 和
HTTP 调用清单中的 smoke 命令。它不手改 Dockerfile，不在沙箱内 curl，也不改用
Docker bridge 地址。默认读取公开 Git 目录；测试候选输入可明确指定本地
`--source`。启动清单与实际运行命令源码都须和本地验证输入一致。

手动矩阵工作流接受准确的 CLI、SDK、provider 提交、模板选择和平台，以及 `distribution: published`（默认）或 `source`。
从这些精确提交读取版本，安装固定版本的 npm/PyPI 公开包并核对安装结果；SDK 源码只提供本地后端 fixture，provider 安装精确 checkout，模板仍使用本次工作流的原始源码。published 模式下未发布的版本会安装失败。source 模式使用 `npm ci` 构建精确 CLI checkout，并从精确 SDK checkout 安装两个 Python 包；这是发布前候选验证，不是公开包验收。报告记录安装来源和 CLI、SDK、provider、模板的精确提交。
`all` 当前为 46 个源码模板，最多同时运行四个独立 runner。OpenSandbox 使用真实 Docker 服务及 provider 返回的直连端点（明确选择默认的 `use_server_proxy=false`）；
Express 使用该工作流配置的凭据。缺凭据不能算通过。

有 `expect` 的命令逐入口断言输出；没有的诊断命令分别检查调用成功和非空结果，
不要求时间等动态信息相同；这种结果仅证明调用链成功，不能证明业务状态正确。
smoke 必须可重复执行，真实模型业务和完整应用控制器
另行验证，不由本次结果代替。

应用结果与资源清理分开记录。仅删除启动记录中确切属于本次的资源，并独立回查。
不认识的镜像仓库和不明确的提交保留为待处理，不能推定删除成功。`PARTIAL` 返回
非零退出码；原始失败不被之后的清理或重跑覆盖。
