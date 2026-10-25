# stagehand

## 做什么

使用真实 Node.js `@browserbasehq/stagehand@4.3.0` SDK、随包浏览器扩展和私有本地 Chromium。每次有界调用执行一条上游 `act` 指令，可选原生 `extract` 提取 `{text: string}`，并生成新 PNG。这里只提供本地浏览器切片，不承诺 Browserbase 托管会话、持久登录、完整自主规划或任意提取 schema。

## 技术栈

Alibaba generation2 base v0.0.49、SHA256 固定的 Node24.16.0、npm integrity 锁定的 Stagehand4.3.0/Zod4.4.3，以及明确披露、精确源码校验的连接参数补丁、Playwright1.58.0 Chromium1208/145.0.7632.6、Python3.13，server 固定 e2cb27e24fde0a67112f82b8d44af463445a5d1a。以非 root user 运行，目录 `/home/user/app`、端口9000。[Dockerfile](Dockerfile)、[锁文件](package-lock.json)、[设计](../docs/design/stagehand.md)。

## 解决的问题

通过 Agent Sandbox 命名命令执行真实 Stagehand 语义浏览器动作，无需 Browserbase 账号。固定4.3.0的 ModelConfig 不接受自定义 base URL；使用上游支持的 ClientLLM 回调，将结构化文本／图片请求交给显式配置的 OpenAI 兼容 Chat Completions 端点。DOM 解释、选择器、浏览器动作和提取仍由真实 SDK／扩展完成，不安装替代 agent 或假 CLI。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./stagehand --yes
abx run <sandbox-id> stagehand_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('stagehand_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/stagehand_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "4.3.0"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| stagehand_version | 无 | 实际 SDK 版本 `4.3.0`，不启动浏览器／模型 |
| stagehand_setup_check | 无 | 仅 `api_key_set`／`base_url_set`／`model_set` 布尔值、mode、`browserbase_account_required:false`，无网络／秘密 |
| stagehand_self_test | 无 | `STAGEHAND_NATIVE_OK`；全新私有离线浏览器／扩展、标题、PNG 和清理；60秒期限 |
| stagehand | `task`：必填非空字符串；`url`：必填 HTTP(S)，不含用户信息／控制符／空白；`extract_instruction`：可选字符串，默认空；`command_timeout`：整数1..600秒，默认180 | 一次原生动作，可选文本提取、新 PNG；每次私有浏览器 |

task／提取指令各最多32768 UTF-8字节，URL最多8192。结果含 `version`、`sdk_sha256`、`title`、`final_url`、`action:{success,message,actionDescription,actions}`、`extracted:null`或`{text}`、`model_calls`（最多8）、`screenshot_path`、`png_bytes`。产物为 WORKSPACE 下 `stagehand-artifacts/<random>.png`，最多8MiB；用 `sb.files.read_bytes` 读取，使用后只删除返回的自有路径，不覆盖原文件。操作串行，并发直接报 busy。stdout／stderr 各限256KiB，省略上游私有错误；非零退出、超时或无法确认清理均失败。

## 配置

| 环境变量 | 必需／默认 | 含义 |
| --- | --- | --- |
| STAGEHAND_API_KEY | 模型必需，空 | 授权兼容模型端点密钥，不是 Browserbase token |
| STAGEHAND_BASE_URL | 模型必需，空 | HTTPS API base，包含实际 API 前缀，追加 `/chat/completions`；仅本地开发可用 literal localhost HTTP；无用户信息／query／fragment |
| STAGEHAND_MODEL | 模型必需，空 | 实际模型名，最多200个允许的标识字符 |
| ABX_SERVER_TOKEN | 必填；清单为空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| WORKSPACE | `/home/user/app` | 已存在产物根目录 |

上游 ClientLLM 结构化请求支持文本和图片，必须完整返回 JSON-schema 结果；请求最多2MiB、响应1MiB，每次推理60秒，不自动重定向、重试或切换提供方。配置在服务 import 时读取。模型秘密只经匿名 stdin 内存传入 Node，不写文件、不进 argv／浏览器环境。浏览器只继承选定运行时／证书变量以及全新私有 HOME／cache／profile。明确在外层一次性沙箱中关闭 Chromium 内层 sandbox；这不构成租户安全边界。页面能访问沙箱可达网络，命令调用者需要受信任且认证。


固定兼容配置：SDK4.3.0 的 local connect schema 接受 extensionId，但工厂未转发。[patch_sdk.py](patch_sdk.py) 强制校验原始源码 SHA25638ec56a2a1af1fb72c3e361a66b256def8e3665cca527e0d337f8a76a8308bd1，只改一处转发。自有 Chrome 只预加载原 npm 包随附、未修改的扩展，观察真实 service-worker ID，再使用原生 localBrowser.connect／Stagehand.create／act／extract。运行时与独立控制器强制校验补丁后 SDK SHA256bdf3cd62126c1529e8a889cae17fd098303e24e962e491a4b20786de72c369e0。这是明确披露的上游补丁发行配置。失败诊断仅返回允许的阶段／HTTP状态／调用次数，不返回上游响应正文、私有端点或密钥。

## 资源

2vCPU、4096MB、端口9000、Express约10GiB rootfs。沙箱内不需要 Docker／KVM／GPU，镜像校验8GiB rootfs预算。需要本地浏览器／扩展以及兼容结构化输出的模型。无需、也未验证 Browserbase 云服务／缓存／托管浏览器。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

1.0.0 的原生工厂尝试通过调试端口调用 Extensions.loadUnpacked，固定 Chromium 返回 code-32000 Method not available；实际云端与 L1 自检失败记录保留。1.1.0 修复扩展连接后通过 L1／浏览器／HTTP，但首次独立真实模型仍失败，具体模型失败根因未认定。1.1.1 仅增加安全诊断，未放宽请求 schema、模型／浏览器断言或清理要求；新一轮真实模型通过不能据此推断旧模型失败原因。全部旧失败轮次均独立清理自有资源。

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
