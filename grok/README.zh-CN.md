# grok

## 做什么

运行真正的 xAI 官方 `@xai-official/grok@1.0.62` 无头编码 CLI。Rust 原生程序经 --prompt-file /dev/stdin 读取匿名 stdin，使用真实工具修改项目，返回缓冲 JSON 与实际退出码。本模板是官方 Grok Build；兼容模型通过不代表 xAI 托管模型或订阅已验证。

[Official xAI source snapshot](https://github.com/xai-org/grok-build/tree/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8), [native custom models](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/docs/user-guide/11-custom-models.md), [headless protocol](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/docs/user-guide/14-headless-mode.md).

## 技术栈

Alibaba generation2 basev0.0.49／Python3.13、SHA256 固定 Node24.16.0、npm integrity 锁定 Grok Build1.0.62及原始 Linuxx64/Rust 二进制。每次调用前校验二进制 SHA2562a46d9e4d7ebd7a9cff7f95716714b19dad5f21dd2a497822400b1fb128969aa。server 固定 e2cb27e24fde0a67112f82b8d44af463445a5d1a，以 user 运行，应用目录／工作区、端口9000。[Dockerfile](Dockerfile)、[依赖锁](package-lock.json)、[设计](../docs/design/grok.md)。

## 解决的问题

通过命名命令使用真实 Grok Build 编码能力，无需交互登录、共享开发者配置或宿主 CLI。已检查真实包名、帮助和源码快照，不假设参数，不替换原生 agent。模型／端点明确；验收中的生成代码只在新建自有云沙箱执行。

## 快速开始（CLI）

安装[已验证原生 CLI 入口](../docs/platform-steps.zh-CN.md)，配置授权 Express 访问。公开 COPY 输入需要先发布精确源码提交。unique-run／template／sandbox 均替换为本次自有值，等待官方 READY 后创建。命名调用为 `abx run`；CLI0.4.1 需显式选择 `abx --native run`。下面是复现流程，尚不代表通过记录。

```bash
python scripts/prepare_steps.py grok --output /tmp/grok-steps-<unique-run> \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/grok-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> grok_version
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

诊断预期为 `{"native_version":"1.0.62"}`。自动 steps／SDK 验收：

```bash
export ABX='abx --native'
python scripts/run_steps_e2e.py grok --sandbox-create sdk --http
```

命令服务配置模型后，可执行 `abx --native run <owned-sandbox-id> grok --json-args '{"prompt":"Inspect the existing project and fix its failing tests","cwd":"project","command_timeout":300}'`。project 必须已在 WORKSPACE 内存在。检查 exit_code 及原生 stopReason；安装／回复 marker 不代表编码成功。

## 快速开始（Python SDK）

按[成对固定源码](../docs/python-client-installation.md)安装 `agent-sandbox-client`，导入 `agent_sandbox`。示例只创建、删除本次自有沙箱并读取真实版本。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        print(await sb.run("grok_version", timeout=60))
    finally:
        await sb.kill()

asyncio.run(main())
```

真实编码前，在服务启动前注入 GROK_MODEL_API_KEY、GROK_MODEL_BASE_URL、GROK_MODEL。[显式进程配置](../docs/runtime-environment.zh-CN.md)说明预热9000进程不会自动获取稍后 create-time 环境。先调用 grok_setup_check 确认存在，再执行 `await sb.run("grok", prompt="Fix the existing calc.py and preserve test_calc.py", cwd="project", command_timeout=300, timeout=330)`。直接返回 `{stdout,stderr,exit_code,native_version}`，不流式返回 stdout。非零退出保留为非零 exit_code，不能当作成功。

## 快速开始（HTTP POST）

ABX_SERVER_URL 为 `sb.network.get_url(9000)`，服务 ABX_SERVER_TOKEN 与模型／提供方凭据独立。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/grok_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```

HTTP200 返回 `{"result":{"native_version":"1.0.62"}}`。`POST /commands/grok` 直接接收 `{prompt,cwd,command_timeout}`，无 args 包装。缺失／类型非法／未知参数400，认证失败401，未知命令404，语义守卫／执行异常500并含 `{error,type}`。执行结束的原生进程返回结构化结果，包括可能的非零 exit_code。客户端断开不取消有界进程；finally 仍清理自有后代和私有状态。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| grok_version | 无 | 实际固定原生版本 `{"native_version":"1.0.62"}`；不调用模型／登录 |
| grok_setup_check | 无 | mode=openai-compatible-byok、base_url_set／api_key_set／model_set 布尔值、xai_account_required:false；不联网／返回秘密 |
| grok | prompt：必填非空字符串，1..32768 UTF-8字节且无 NUL；cwd：可选字符串，默认空，最多4096字节，解析后必须为 WORKSPACE 内现存目录；command_timeout：整数1..600秒，默认300 | `{stdout:string,stderr:string,exit_code:int,native_version:"1.0.62"}`；原生工具执行及工作区文件修改 |

固定参数为 --output-format json、--always-approve、--no-plan、--no-subagents、--disable-web-search、--sandbox off、--model abx-approved、--max-turns20、--prompt-file /dev/stdin。工具白名单为 read_file/search_replace/grep/list_dir/run_terminal_cmd，禁用 Agent。原生 sandbox off 保留工具在外层沙箱内的 OS 权限；cwd 仅为参数边界。仅用于受信任调用者与全新自有一次性沙箱，无回滚承诺。提示和密钥值均不进入 argv。

stdout／stderr 各限256KiB；成功／失败／超时／溢出均清理自有进程组、pidfd 和唯一归属标记后代。调用串行，并发报 busy，不使用原 HOME。返回前脱敏显式模型密钥／端点及其 JSON 转义形式。只保留调用者请求的工作区产物，原生 HOME／配置／缓存／会话／team 状态均在调用后删除。


## 配置

| 名称 | 必需／默认 | 含义 |
| --- | --- | --- |
| GROK_MODEL_API_KEY | 模型必需，空 | 授权兼容端点密钥，仅作为原生 ABX_GROK_MODEL_KEY 传递 |
| GROK_MODEL_BASE_URL | 模型必需，空 | 显式 HTTPS API base；仅固定本地地址可用 HTTP；无用户信息／query／fragment；最多2048字符 |
| GROK_MODEL | 模型必需，空 | 实际模型标识，最多200个允许字符 |
| WORKSPACE | `/home/user/workspace` | 已存在工作区根目录 |
| ABX_SERVER_TOKEN | 可选，空 | 独立命名服务 Bearer 凭据 |

配置在 commands.py 加载时捕获。私有0600 config.toml 仅含显式 model/base 与 env_key="ABX_GROK_MODEL_KEY"，不保存密钥值，固定 chat_completions 后端。每次调用使用并删除私有 GROK_HOME/HOME/cache/session；关闭更新、leader、遥测/trace、记忆及后台 workflow。原生 shell_environment_policy 继承 core 并排除秘密变量；不转发调用者云/GitHub/厂商账号凭据。

## 资源

仅 Linuxx64，2vCPU、4096MB、9000端口、Express约10GiB rootfs；镜像限制8GiB。CLI 不需嵌套 Docker／KVM／GPU；真实编码需要兼容工具调用的模型和授权网络。未声明 Grok Build 托管／扩展／其他提供方验收或模型任务内存估计。

## 已验证

当前原生镜像／Express／SDK／模型验收仍待执行。保持 `tested_on: []` 和 experimental。本地 source fixture、真实无凭据 version/help 不代表编码或部署通过。

原生 JSON 的 text 会合并进度与最终回复。验收要求最后非空行恰为本次随机 marker，并同时验证 end_turn、正整数轮数与 session/request ID；源码、产物、原始测试和隐藏用例仍须独立通过。允许前面的进度文本；marker 后还有其他最终文本则失败。

## 二次开发

```bash
python -m pytest -q grok/test_commands.py grok/test_model_controller.py
python scripts/check_template.py grok --strict
python scripts/check_docs.py
```

官方二进制实际报告 grok1.0.62 (1474f9cbdd91)，并核对 SHA256。公开源码快照2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8 用于核对无头/自定义模型协议，不声称为二进制构建 commit。控制器通过真实 Python SDK 调用模型命令，再独立核对完整原始测试字节、源码修改、报告与随机产物，以及返回后的原始/隐藏用例和新 ACK。JSON 必须含 end_turn、正整数 num_turns 和真实 session/request ID，不能仅凭 marker 通过。生成源码仅在新建自有云沙箱执行。

## 贡献

阅读 [CONTRIBUTING](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)。维护版本、固定来源、双语和历史不可变证据。

## 问题反馈

[模板 Issue40](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/40)。[SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) 和 [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) 使用 `[templates]` 前缀，不发布凭据／私有日志。

## 许可证

包装器与官方 Grok Build 均为 Apache-2.0。[仓库许可](../LICENSE)、[上游许可](UPSTREAM-LICENSE.md)、[官方二进制第三方声明](THIRD_PARTY_NOTICES.md)。保留原始依赖声明，不提供托管账号或商标权利。
