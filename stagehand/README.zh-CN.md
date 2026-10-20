# stagehand

## 做什么

使用真实 Node.js `@browserbasehq/stagehand@4.3.0` SDK、随包浏览器扩展和私有本地 Chromium。每次有界调用执行一条上游 `act` 指令，可选原生 `extract` 提取 `{text: string}`，并生成新 PNG。这里只提供本地浏览器切片，不承诺 Browserbase 托管会话、持久登录、完整自主规划或任意提取 schema。

## 技术栈

Alibaba generation2 base v0.0.49、SHA256 固定的 Node24.16.0、npm integrity 锁定的 Stagehand4.3.0/Zod4.4.3、Playwright1.58.0 Chromium1208/145.0.7632.6、Python3.13，server 固定 e2cb27e24fde0a67112f82b8d44af463445a5d1a。以非 root user 运行，目录 `/home/user/app`、端口9000。[Dockerfile](Dockerfile)、[锁文件](package-lock.json)、[设计](../docs/design/stagehand.md)。

## 解决的问题

通过 Agent Sandbox 命名命令执行真实 Stagehand 语义浏览器动作，无需 Browserbase 账号。固定4.3.0的 ModelConfig 不接受自定义 base URL；使用上游支持的 ClientLLM 回调，将结构化文本／图片请求交给显式配置的 OpenAI 兼容 Chat Completions 端点。DOM 解释、选择器、浏览器动作和提取仍由真实 SDK／扩展完成，不安装替代 agent 或假 CLI。

## 快速开始（CLI）

命名调用使用 `abx run`；CLI0.4.1 需要显式选择此入口，完整形式为下方 `abx --native run`。

安装[已验证原生 CLI 入口](../docs/platform-steps.zh-CN.md)，配置 Express 凭据。公开 COPY 输入需要先发布精确源码提交。unique-run／template／sandbox 占位符均替换为本次自有值，确认官方 READY 后创建。以下是原生 CLI 复现流程，本身不是云端通过记录。

```bash
python scripts/prepare_steps.py stagehand --output /tmp/stagehand-steps-<unique-run> \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/stagehand-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> stagehand_self_test
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

原生无模型自检成功返回 `STAGEHAND_NATIVE_OK`，实际验证浏览器／扩展、导航、标题、PNG 与清理。推荐规范控制器自动生成回执并记录资源归属：

```bash
export ABX='abx --native'
python scripts/run_steps_e2e.py stagehand --sandbox-create sdk --http
```

## 快速开始（Python SDK）

通过[成对固定源码](../docs/python-client-installation.md)安装 `agent-sandbox-client`，导入 `agent_sandbox`。示例只创建／删除本次自有沙箱并执行无模型自检。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        print(await sb.run("stagehand_self_test", timeout=90))
    finally:
        await sb.kill()

asyncio.run(main())
```

真实动作要求在命令服务启动前注入 `STAGEHAND_API_KEY`、`STAGEHAND_BASE_URL`、`STAGEHAND_MODEL`。预热9000进程不会自动获取稍后 create-time 环境；参阅[显式进程配置](../docs/runtime-environment.md)。配置后可执行 `await sb.run("stagehand", task="Click the Publish button", url="https://your-authorized-site.example/", extract_instruction="Read the displayed receipt", command_timeout=180, timeout=210)`。将网址替换为授权可访问页面，只在全新自有、无重要凭据的沙箱中运行。

## 快速开始（HTTP POST）

`ABX_SERVER_URL` 为沙箱9000端口 URL，即 `sb.network.get_url(9000)`。服务开启认证时，独立注入 `ABX_SERVER_TOKEN`，不要使用模型密钥充当服务令牌。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/stagehand_self_test" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```

HTTP200 返回 `{"result":"STAGEHAND_NATIVE_OK"}`。`POST /commands/stagehand` 直接传入参数 JSON，不包 args。缺失／类型非法／未知参数400，认证失败401，未知命令404，语义守卫／上游／模型／运行错误500并返回 `{error,type}`。结果为缓冲输出；客户端断开不会取消服务端有界任务。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| stagehand_version | 无 | 实际 SDK 版本 `4.3.0`，不启动浏览器／模型 |
| stagehand_setup_check | 无 | 仅 `api_key_set`／`base_url_set`／`model_set` 布尔值、mode、`browserbase_account_required:false`，无网络／秘密 |
| stagehand_self_test | 无 | `STAGEHAND_NATIVE_OK`；全新私有离线浏览器／扩展、标题、PNG 和清理；60秒期限 |
| stagehand | `task`：必填非空字符串；`url`：必填 HTTP(S)，不含用户信息／控制符／空白；`extract_instruction`：可选字符串，默认空；`command_timeout`：整数1..600秒，默认180 | 一次原生动作，可选文本提取、新 PNG；每次私有浏览器 |

task／提取指令各最多32768 UTF-8字节，URL最多8192。结果含 `version`、`title`、`final_url`、`action:{success,message,actionDescription,actions}`、`extracted:null`或`{text}`、`model_calls`（最多8）、`screenshot_path`、`png_bytes`。产物为 WORKSPACE 下 `stagehand-artifacts/<random>.png`，最多8MiB；用 `sb.files.read_bytes` 读取，使用后只删除返回的自有路径，不覆盖原文件。操作串行，并发直接报 busy。stdout／stderr 各限256KiB，省略上游私有错误；非零退出、超时或无法确认清理均失败。

## 配置

| 环境变量 | 必需／默认 | 含义 |
| --- | --- | --- |
| STAGEHAND_API_KEY | 模型必需，空 | 授权兼容模型端点密钥，不是 Browserbase token |
| STAGEHAND_BASE_URL | 模型必需，空 | HTTPS API base，包含实际 API 前缀，追加 `/chat/completions`；仅本地开发可用 literal localhost HTTP；无用户信息／query／fragment |
| STAGEHAND_MODEL | 模型必需，空 | 实际模型名，最多200个允许的标识字符 |
| ABX_SERVER_TOKEN | 可选，空 | 独立服务 Bearer 凭据 |
| WORKSPACE | `/home/user/app` | 已存在产物根目录 |

上游 ClientLLM 结构化请求支持文本和图片，必须完整返回 JSON-schema 结果；请求最多2MiB、响应1MiB，每次推理60秒，不自动重定向、重试或切换提供方。配置在服务 import 时读取。模型秘密只经匿名 stdin 内存传入 Node，不写文件、不进 argv／浏览器环境。浏览器只继承选定运行时／证书变量以及全新私有 HOME／cache／profile。明确在外层一次性沙箱中关闭 Chromium 内层 sandbox；这不构成租户安全边界。页面能访问沙箱可达网络，命令调用者需要受信任且认证。

## 资源

2vCPU、4096MB、端口9000、Express约10GiB rootfs。沙箱内不需要 Docker／KVM／GPU，镜像校验8GiB rootfs预算。需要本地浏览器／扩展以及兼容结构化输出的模型。无需、也未验证 Browserbase 云服务／缓存／托管浏览器。

## 已验证

当前尚无提供方或真实模型通过记录。源码／import／fixture 检查不代表云端验收。精确版本的原生 L1、Express SDK 创建／命令／模型及独立清理通过之前，保持 `tested_on: []` 和 experimental。

## 二次开发

```bash
npm ci --prefix stagehand --ignore-scripts --registry=https://registry.npmjs.org
node --test stagehand/test_transport.mjs
python -m pytest -q stagehand/test_commands.py
python scripts/check_template.py stagehand --strict
python scripts/check_docs.py
```

本地固定回调／子进程测试只验证传输和守卫。未设置 E2E_REQUIRE_CLI=1时，HTTP e2e 对缺失原生环境标记 SKIP；E2E_REQUIRE_LLM 不允许静默跳过，真实模型使用单独自有 SDK 控制器。更新时维护固定版本、私有资源归属、期限、双语及历史通过／失败记录。[steps 指南](../docs/platform-steps.zh-CN.md)说明源码哈希、传输和清理。

## 贡献

阅读 [CONTRIBUTING](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)。SDK／CLI 问题归对应仓库。

## 问题反馈

[模板 Issue68](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/68)。[SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) 与 [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) 使用 `[templates]` 前缀，不附凭据或私有日志。

## 许可证

包装代码：[Apache-2.0](../LICENSE)。Stagehand 和 Zod：MIT；保留 [Stagehand 上游许可](UPSTREAM-LICENSE.md)。Chromium／Node 和依赖保持原发行包许可与声明；不暗示 SaaS 源码或账号授权。
