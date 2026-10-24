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
not a public package installation. An existing output file is never overwritten.

The manual **Public template launch matrix** GitHub workflow accepts exact reviewed
CLI, SDK and provider commits, a comma-separated selection or `all`, and either
backend or both. `all` currently selects 46 source templates. OpenSandbox uses
its real Docker server, server-proxy endpoint and an owned local registry.
Express uses the `PUBLIC_LAUNCH_*` credentials explicitly configured for that
workflow. Missing credentials fail the attempt; they never become a cloud pass.

Checks use each manifest's expected output where supplied. Diagnostic commands
without an `expect` require successful nonempty results independently on each
consumer; their output may legitimately vary. The suite does not claim real-model
business acceptance. The source recipes' smoke commands must be safe to repeat;
application-specific full controllers remain separate tests.

The runner deletes known owned sandboxes and confirms absence through a new SDK
connection. For Express, it deletes journal-owned templates and reads the complete
inventory, then removes exact owned Hangzhou ACR tags using the existing cleanup
verifier. Other registry types remain explicit pending cleanup. For the disposable
OpenSandbox registry it removes exact owned manifests, checks absence and removes
local tags. An uncertain intent is not blindly replayed. The private CLI journal
contains recovery identifiers; reports contain counts and outcomes, never keys or
native IDs. `PARTIAL` is a nonzero result and must be reconciled before claiming a
complete acceptance.

## 中文

本工具通过已安装 CLI 的 `template launch` 准备源码，然后从宿主 CLI、Python 和
HTTP 调用清单中的 smoke 命令。它不手改 Dockerfile，不在沙箱内 curl，也不改用
Docker bridge 地址。默认读取公开 Git 目录；测试候选输入可明确指定本地
`--source`。启动清单与实际运行命令源码都须和本地验证输入一致。

手动矩阵工作流接受准确的 CLI、SDK、provider 提交，以及模板选择和平台。
`all` 当前为 46 个源码模板。OpenSandbox 使用真实 Docker 服务和 server proxy；
Express 使用该工作流配置的凭据。缺凭据不能算通过。

有 `expect` 的命令逐入口断言输出；没有的诊断命令分别检查调用成功和非空结果，
不要求时间等动态信息相同。smoke 必须可重复执行，真实模型业务和完整应用控制器
另行验证，不由本次结果代替。

应用结果与资源清理分开记录。仅删除启动记录中确切属于本次的资源，并独立回查。
不认识的镜像仓库和不明确的提交保留为待处理，不能推定删除成功。`PARTIAL` 返回
非零退出码；原始失败不被之后的清理或重跑覆盖。
