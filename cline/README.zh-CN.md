# cline

## 做什么

运行真实官方 `cline@3.0.73`，采用有界无头 JSON/yolo 模式，经匿名 stdin 读取提示，使用原生工具修改工作区并返回缓冲 NDJSON 与实际退出码。显式选择 OpenAI 兼容提供方，不选择 Cline 托管账号。这里只验证 CLI 产品，不声称 VS Code 扩展或桌面 UI。

## 技术栈

Alibaba generation2 basev0.0.49／Python3.13、SHA256 固定 Node24.16.0、npm integrity 锁定 Cline3.0.73及原始 Linuxx64/Bun 二进制。每次调用前校验二进制 SHA2561ff8841d17d4d83763134c193d414e4f7fcf2ef56af759e5ebbe96727fc2c8f7。server 固定 e2cb27e24fde0a67112f82b8d44af463445a5d1a，以 user 运行，应用目录／工作区、端口9000。[Dockerfile](Dockerfile)、[依赖锁](package-lock.json)、[设计](../docs/design/cline.md)。

## 解决的问题

通过命名命令使用真实 Cline 编码能力，无需交互登录、共享开发者配置或宿主 CLI。已检查真实包名、帮助和源码 tag，不假设参数，不替换原生 agent。模型／端点明确；验收中的生成代码只在新建自有云沙箱执行。

## 快速开始（CLI）

安装[已验证原生 CLI 入口](../docs/platform-steps.zh-CN.md)，配置授权 Express 访问。公开 COPY 输入需要先发布精确源码提交。unique-run／template／sandbox 均替换为本次自有值，等待官方 READY 后创建。命名调用为 `abx run`；CLI0.4.1 需显式选择 `abx --native run`。下面是复现流程，尚不代表通过记录。

```bash
python scripts/prepare_steps.py cline --output /tmp/cline-steps-<unique-run> \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/cline-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> cline_version
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

诊断预期为 `{"native_version":"3.0.73"}`。自动 steps／SDK 验收：

```bash
export ABX='abx --native'
python scripts/run_steps_e2e.py cline --sandbox-create sdk --http
```

命令服务配置模型后，可执行 `abx --native run <owned-sandbox-id> cline --json-args '{"prompt":"Inspect the existing project and fix its failing tests","cwd":"project","command_timeout":300}'`。project 必须已在 WORKSPACE 内存在。检查 exit_code 及原生 run_result.finishReason；安装／回复 marker 不代表编码成功。

## 快速开始（Python SDK）

按[成对固定源码](../docs/python-client-installation.md)安装 `agent-sandbox-client`，导入 `agent_sandbox`。示例只创建、删除本次自有沙箱并读取真实版本。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        print(await sb.run("cline_version", timeout=60))
    finally:
        await sb.kill()

asyncio.run(main())
```

真实编码前，在服务启动前注入 CLINE_MODEL_API_KEY、CLINE_MODEL_BASE_URL、CLINE_MODEL。[显式进程配置](../docs/runtime-environment.zh-CN.md)说明预热9000进程不会自动获取稍后 create-time 环境。先调用 cline_setup_check 确认存在，再执行 `await sb.run("cline", prompt="Fix the existing calc.py and preserve test_calc.py", cwd="project", command_timeout=300, timeout=330)`。直接返回 `{stdout,stderr,exit_code,native_version}`，不流式返回 stdout。非零退出保留为非零 exit_code，不能当作成功。

## 快速开始（HTTP POST）

ABX_SERVER_URL 为 `sb.network.get_url(9000)`，服务 ABX_SERVER_TOKEN 与模型／提供方凭据独立。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/cline_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```

HTTP200 返回 `{"result":{"native_version":"3.0.73"}}`。`POST /commands/cline` 直接接收 `{prompt,cwd,command_timeout}`，无 args 包装。缺失／类型非法／未知参数400，认证失败401，未知命令404，语义守卫／执行异常500并含 `{error,type}`。执行结束的原生进程返回结构化结果，包括可能的非零 exit_code。客户端断开不取消有界进程；finally 仍清理自有后代和私有状态。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| cline_version | 无 | 实际固定原生版本 `{"native_version":"3.0.73"}`；不调用模型／登录 |
| cline_setup_check | 无 | mode=openai-compatible-byok、base_url_set／api_key_set／model_set 布尔值、cline_account_required:false；不联网／返回秘密 |
| cline | prompt：必填非空字符串，1..32768 UTF-8字节且无 NUL；cwd：可选字符串，默认空，最多4096字节，解析后必须为 WORKSPACE 内现存目录；command_timeout：整数1..600秒，默认300 | `{stdout:string,stderr:string,exit_code:int,native_version:"3.0.73"}`；原生工具执行及工作区文件修改 |

固定 argv 为 `--json --yolo --provider openai-compatible --model <configured> --cwd <resolved> --compaction off --retries 2 --timeout <seconds>`，并带本次私有 --config／--data-dir。提示经匿名 stdin 传入，不作为参数／shell。Yolo 为原生无监督 act／工具自动批准模式，上游该模式默认禁用 spawn／team。它不只读，不是文件系统／租户安全边界；只用于受信任调用者和全新自有、无重要文件／其他凭据的沙箱。cwd 参数边界不移除原生工具的 OS 权限，文件可能在失败前已修改，不承诺回滚。

stdout／stderr 各限256KiB；成功／失败／超时／溢出均清理自有进程组、pidfd 和唯一归属标记后代。调用串行，并发报 busy，不使用原 HOME。返回前脱敏显式模型密钥／端点及其 JSON 转义形式。只保留调用者请求的工作区产物，原生 HOME／配置／缓存／会话／team 状态均在调用后删除。

原生3.0.73在读取管道前检查 JSON 模式。模板使用固定、无秘密的占位句通过该前置条件；真实任务仍仅经匿名 stdin 传入，由上游追加。运行时1.0.1修复真实1.0.0云测失败，用户提示与凭据均不进入 argv。

运行时1.0.2将提供方配置写入原生实际读取的私有 data/settings/providers.json；上游 --data-dir 会在初始化前覆盖 CLINE_PROVIDER_SETTINGS_PATH。独立检查发现1.0.1原生实际配置缺少预期端点后，已停止该任务。必须先使用虚拟密钥验证原生请求确实到达本次自有端点，再注入已批准的真实模型密钥。

## 配置

| 名称 | 必需／默认 | 含义 |
| --- | --- | --- |
| CLINE_MODEL_API_KEY | 模型必需，空 | 授权兼容端点密钥，仅作为原生 OPENAI_API_KEY 传递 |
| CLINE_MODEL_BASE_URL | 模型必需，空 | 显式 HTTPS API base；仅固定本地地址可用 HTTP；无用户信息／query／fragment；最多2048字符 |
| CLINE_MODEL | 模型必需，空 | 实际模型标识，最多200个允许字符 |
| WORKSPACE | `/home/user/workspace` | 已存在工作区根目录 |
| ABX_SERVER_TOKEN | 可选，空 | 独立命名服务 Bearer 凭据 |

配置在 commands.py 加载时读取。包装器只向私有0600设置文件写提供方／模型／base元数据，不写模型密钥值；原生密钥按其文档从环境读取。原生状态受私有目录保护并在返回／失败时删除。关闭全局 telemetry／自动更新／运行时文件日志，以及公共／私有模型目录刷新。config／data／team／MCP 路径均每次隔离，不传宿主 GitHub／云密钥、二进制替换配置或 Cline 账号 token，宿主控制端凭据不进入编码进程。

## 资源

仅 Linuxx64，2vCPU、4096MB、9000端口、Express约10GiB rootfs；镜像限制8GiB。CLI 不需嵌套 Docker／KVM／GPU；真实编码需要兼容工具调用的模型和授权网络。未声明 Cline 托管／扩展／其他提供方验收或模型任务内存估计。

## 已验证


### 当前镜像验收 — 2026-10-22

| 提供方 | 当前版本与范围 | 证据 |
| --- | --- | --- |
| alicloud-express | 1.0.2；常规镜像、真实 CLI/SDK、完整 HTTP 8 PASS / 0 FAIL / 0 SKIP、沙箱/模板/私有镜像仓库独立清理 | [运行与 HTTP 回执](evidence/image-http-2026-10-22T105009Z.json) |
| opensandbox | 1.0.2；原始 Docker 后端、逐项 CLI/SDK 命名 smoke、完整 HTTP 8 PASS / 0 FAIL / 0 SKIP、SDK/容器/进程独立清理 | [原生源码镜像回执](evidence/opensandbox-2026-10-22T110504Z.json) |

CLI 在 OpenSandbox 中通过实际 `abx exec` 调用容器内命名 HTTP API；通用 `run_code` 仍不支持，`template launch` 的能力检查仍生效。缺少模型或厂商账号的检查按回执明确跳过，不计为真实模型通过。[复现与验收范围](../docs/source-image-acceptance.zh-CN.md)。

<details>
<summary>此前验收记录（保留原有时间与范围）</summary>

| 提供方 | 当前范围 | 记录 |
| --- | --- | --- |
| alicloud-express | 模板1.0.2；原生 steps、官方 READY、真实 Python SDK 创建、CLI/SDK 原生版本、真实模型编码和独立清理 | [2026-10-20](evidence/express-2026-10-20.json)、[完整模型证明](evidence/verification-steps-2026-10-20T201959Z.json) |

真实未修改的 Cline3.0.73原生 CLI 在显式已批准兼容端点使用 qwen3.8-flash。先以虚拟密钥进行真实原生路由检查，确认1次请求的自有端点／模型／Bearer完全匹配，并独立清理测试服务后，再注入真实密钥。真实 SDK 编码修复已有源码，原始测试保持字节一致，下载新报告／精确随机产物，返回后独立执行完整3项原始测试和4个隐藏用例，并匹配新 ACK：17PASS/0FAIL/0SKIP。完整基础 HTTP8PASS/0FAIL/0SKIP另行记录。自有测试项目、原生进程／HOME／状态、额外监听端口、外层沙箱和模板全部独立确认清理。当前运行时 L1 镜像与非 root 用户原生版本／SHA256检查另有记录；不代表实际镜像注册后的模型部署、编辑器扩展、托管服务或其他提供方。[最终工程证据](../.agents/evidence/verify/2026-10-20-cline-native-final.md)。

原生 submit_and_exit 会给已验证摘要添加固定前缀 `Submission recorded (verified): `。验证器仅解包此精确前缀，仍要求原生 completed／正整数迭代次数、摘要恰为本次随机 marker，以及全部独立文件／测试验证；未验证前缀和只输出 marker 不足以通过。之前的配置路径、stdin 前置条件、协议 fixture 和资源恢复失败／中断记录均保留。

</details>

## 二次开发

```bash
python -m pytest -q cline/test_commands.py cline/test_model_controller.py
python scripts/check_template.py cline --strict
python scripts/check_docs.py
```

固定上游 cli-v3.0.73／commitc718573538d76310f464541617ab665108a6c999 定义 JSON run_result，包含 completed finishReason／iterations／text。外部控制器使用真实成对 Python SDK ServerClient.commands.run 执行模型命令，再用独立 HTTP files／shell 校验。它要求真实终结事件，先上传已有故障源码、保留原测试字节，下载新报告／随机 marker 产物，再在自有云目标独立重跑完整原始测试与未提供给模型的用例，并要求新执行后 ACK，最后确认自有项目目录不存在。拒绝在宿主回环地址执行生成源码，且须显式自有远程 opt-in；强制真实模型不得静默跳过。本地固定进程／NDJSON／凭据 fixture 只证明验证器边界。[steps 指南](../docs/platform-steps.zh-CN.md)说明精确源码传输和资源恢复。

## 贡献

阅读 [CONTRIBUTING](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)。维护版本、固定来源、双语和历史不可变证据。

## 问题反馈

[模板 Issue66](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/66)。[SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) 和 [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) 使用 `[templates]` 前缀，不发布凭据／私有日志。

## 许可证

包装器和 Cline 均为 Apache-2.0。[仓库许可](../LICENSE)、[固定上游许可](UPSTREAM-LICENSE.md)。第三方运行时／依赖保持原始发行包声明，不暗示托管账号或商标授权。
