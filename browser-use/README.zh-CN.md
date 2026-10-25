# Browser-use

[English](README.md).

## 做什么

在私有本地Chromium上运行真实browser-use0.13.11 Agent，读取文本DOM、操作网页，返回实际PNG、最终URL和结果。它补充无需模型的Playwright原语，不使用Browser Use Cloud或远程浏览器。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a3`，由 Dockerfile 直接安装。

FC v0.0.49、generation2、非root user、Linux x86_64、Python3.13。[requirements.lock](requirements.lock)固定browser-use0.13.11及全部传递依赖版本/SHA256，由[requirements.in](requirements.in)通过uv0.11.28生成。该版本依赖CDP-use，并非Python Playwright；显式Playwright1.58.0安装器选定Chromium1208/Google Chrome for Testing145.0.7632.6，--no-shell不再安装第二份headless shell。

## 解决的问题

让真实模型在自有沙箱使用本地浏览器，独立取回产物并清理进程。use_vision=false文本DOM不要求视觉模型。本模板不接云浏览器账号/计费、扩展或任意本地文件/shell操作。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./browser-use --yes
abx run <sandbox-id> browser_use_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('browser_use_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/browser_use_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "0.13.11"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| browser_use_version | none | actual installed0.13.11 string |
| browser_use_setup_check | none | installed/version/browser_installed and api_key_set/base_url_set/model_set flags |
| browser_use_self_test | none | BROWSER_USE_NATIVE_OK only after native CDP navigation/title/PNG and cleanup; no model |
| browser_use | task:str required, nonempty/no NUL/max256KiB UTF-8; url:str="", HTTP(S)/no userinfo/max8192 UTF-8 bytes; max_steps:int=8,1..20; command_timeout:int=300,1..900seconds | {result:str,final_url:str,screenshot_path:str,bytes:int,steps:int,done:bool,success:bool} |

真实worker显式使用Agent/BrowserSession/BrowserProfile/ChatOpenAI，不自动连接云。通过原生add_schema_to_system_prompt=true、dont_force_structured_output=true把schema放入系统提示并由库解析文本JSON，不要求模型服务支持特定strict response_format。

仅15项原生动作：done/navigate/click/input/scroll/wait/go_back/switch/close/find_text/find_elements/search_page/select_dropdown/dropdown_options/send_keys。构造Agent前后检查工具表。禁用文件/shell/evaluate/extract/upload/PDF/search及Agent截图动作；完成时封装自行获取真实截图。产物名随机且不能由调用者指定/覆盖。PNG16MiB为渲染后限制。最终URL直接查询实际目标信息，模型自述不是独立验证。

## 配置

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| BROWSER_USE_API_KEY | model turns | empty | explicitly supplied compatible-model credential, not Browser Use Cloud |
| BROWSER_USE_BASE_URL | model turns | empty | HTTP(S) model API; no userinfo/query/fragment |
| BROWSER_USE_MODEL | model turns | empty | explicit compatible chat model ID |
| BROWSER_USE_PYTHON | no | /opt/browser-use/bin/python | hash-locked native environment; actual0.13.11 checked |
| PLAYWRIGHT_BROWSERS_PATH | no | /opt/playwright | installed Chromium1208 cache |
| BROWSER_USE_BROWSER_BINARY | diagnostics | Chromium1208/chrome-linux64/chrome | executable override; actual145.0.7632.6 still required |
| WORKSPACE | no | /home/user/app | owned root for new browser-use-artifacts PNGs |
| ABX_SERVER_TOKEN | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

模型配置只通过私有文件stdin进入，不继承到Chromium。每次独立HOME/XDG/profile/原生文件目录，关闭遥测/云同步/默认扩展/use_cloud，不导入调用者账号或已保存浏览器。CDP启动显式请求回环地址，只公布命令9000。此容器模板显式设置chromium_sandbox=false，使用自有沙箱提供OS隔离，不依赖Docker自动探测。浏览器和模型仍有沙箱用户权限及网络，这不是额外OS隔离。结果和PNG可能含网页私密信息；返回字符串替换模型密钥/地址的完整值。

## 资源

2vCPU/2048MB，命令9000，可显式启动模型9010；独立SDK测试夹具使用9011。--disable-dev-shm-usage避免依赖大/dev/shm。每个服务只运行一个浏览器任务，并发重操作返回busy500。max_steps1..20，每步最多3动作；模型90秒/零重试/4096 token，原生动作30秒/步骤120秒/LLM100秒门禁；外层1..900秒另加有限清理。每路输出256KiB，PNG16MiB渲染后检查。正常成功/失败/期限均删除私有浏览器配置/文件并清理自有进程，PNG交由调用者保存。服务突然丢失或同用户恶意代码仍以删除自有沙箱为最终边界。镜像根文件系统8GiB构建门禁。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

python -m venv <new-prefix>后，用<new-prefix>/bin/python -m pip install --require-hashes -r browser-use/requirements.lock及pip check恢复。BROWSER_USE_PYTHON保留虚拟环境Python路径，不解析其符号链接，配置实际固定浏览器缓存/执行文件。python -m pytest -q browser-use/test_commands.py browser-use/test_model_controller.py。夹具响应/程序均人工编写，不在操作者主机运行真实模型生成shell。

[step指南](../docs/platform-steps.zh-CN.md)：python scripts/prepare_steps.py browser-use --output /tmp/browser-use-steps仅准备，python scripts/run_steps_e2e.py browser-use --timeout 1200实际执行。完整HTTP控制器关闭模型；单独真实模型SDK验收：python browser-use/model_e2e_test.py --sandbox-id <owned-fresh-sandbox-id>。需要固定SDK/httpx/Pillow、三个模型变量及空闲9010/9011，只拥有自己的夹具/服务/文件，独立确认计数3、提交nonce、PNG及监听/文件不存在，保留调用者沙箱。导出后需另行销毁自有沙箱。

## 贡献

遵循[CONTRIBUTING](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)、[设计](../docs/design/browser-use.md)，同步双语API/限制/证据。共享严格SHA256锁支持需先合并[PR146](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/146)。

## 问题反馈

[Issue51](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/51)；模板[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，客户端/服务[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

封装代码[Apache-2.0](../LICENSE)。Browser-use为MIT，保留[上游原许可](upstream-LICENSE)。保留Playwright发行的未修改Chrome for Testing二进制及捆绑许可/声明；Playwright为Apache-2.0。哈希固定依赖保留各自安装声明，不能把整个镜像统一重标Apache-2.0。不包含模型权重或云服务账号。

原生步骤失败时最多返回20条错误摘要，配置的模型密钥和端点精确脱敏后，每条限制为1024个 UTF-8 字节；SDK 验证器在验收断言前保留失败及清理事实。

### 当前平台 step 验收

[真实1.0.0 step](evidence/express-2026-10-20T153859Z.json)及[原完整 HTTP 控制器](evidence/verification-steps-2026-10-20T153859Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke、原生 CDP 导航／标题／PNG 自测，HTTP11 PASS/0 FAIL/1模型 SKIP，耗时224.94秒。执行器为官网全新安装的 CLI0.4.1（首个根参数 --native），NODE_PATH 已取消，无外部 SDK 模块注入。自有沙箱、模板及精确私有缓存均独立确认清理。保留 Python3.13、版本／哈希锁、固定 Chromium --no-shell、非 root 及8GiB根文件系统断言。早期 step 失败保留；本回执不改变独立镜像／模型结果范围。
