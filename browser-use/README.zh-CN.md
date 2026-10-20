# Browser-use

[English](README.md).

## 做什么

在私有本地Chromium上运行真实browser-use0.13.11 Agent，读取文本DOM、操作网页，返回实际PNG、最终URL和结果。它补充无需模型的Playwright原语，不使用Browser Use Cloud或远程浏览器。

## 技术栈

FC v0.0.49、generation2、非root user、Linux x86_64、Python3.13。[requirements.lock](requirements.lock)固定browser-use0.13.11及全部传递依赖版本/SHA256，由[requirements.in](requirements.in)通过uv0.11.28生成。该版本依赖CDP-use，并非Python Playwright；显式Playwright1.58.0安装器选定Chromium1208/Google Chrome for Testing145.0.7632.6，--no-shell不再安装第二份headless shell。SDK固定e2cb27e或匹配注入wheel。

## 解决的问题

让真实模型在自有沙箱使用本地浏览器，独立取回产物并清理进程。use_vision=false文本DOM不要求视觉模型。本模板不接云浏览器账号/计费、扩展或任意本地文件/shell操作。

## 快速开始（CLI）

```bash
abx template deploy ./browser-use -y
abx create --template <template-id> --timeout 900 -y
abx run <sandbox-id> browser_use_version
abx run <sandbox-id> browser_use_setup_check
abx run <sandbox-id> browser_use_self_test
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

deploy/create返回上述模板/沙箱ID。version/setup/self-test无需模型密钥，期望BROWSER_USE_NATIVE_OK。[入口兼容及提供方设置](../docs/using-templates.md#client-entry-compatibility)。创建时环境不能重新配置预热服务；真实模型采用下方SDK显式启动服务。

## 快速开始（Python SDK）

按[固定客户端源码说明](../docs/python-client-installation.md)安装agent-sandbox-client。相同原生自测后可选执行真实模型；操作者环境设置三个BROWSER_USE模型变量，不需要模型时移除可选段。

```python
import asyncio
import os
from pathlib import Path
import secrets
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900)
    clients = []
    try:
        native = sb.server_at(9000)
        clients.append(native)
        print(await native.commands.run("browser_use_self_test", timeout=90))
        # Optional real model turn; these three variables hold model settings.
        model = await sb.start_server(
            port=9010, commands="/home/user/app/commands.py", timeout=60,
            token=secrets.token_urlsafe(32),
            env={"BROWSER_USE_API_KEY": os.environ["BROWSER_USE_API_KEY"],
                 "BROWSER_USE_BASE_URL": os.environ["BROWSER_USE_BASE_URL"],
                 "BROWSER_USE_MODEL": os.environ["BROWSER_USE_MODEL"]})
        clients.append(model)
        result = await model.commands.run(
            "browser_use", task="Read the heading and summarize it briefly.",
            url="https://example.com/", max_steps=8,
            command_timeout=300, timeout=360)
        if not result["done"] or not result["success"]:
            raise RuntimeError("Native browser agent did not complete the task")
        png = await sb.files.read_bytes(result["screenshot_path"], max_bytes=16*1024**2)
        output = Path("browser-use-" + secrets.token_hex(8) + ".png")
        with output.open("xb") as file:
            file.write(png)
        print(result["result"], output)
    finally:
        await asyncio.gather(*(client.aclose() for client in clients), return_exceptions=True)
        try:
            await sb.kill()
        finally:
            await sb.close()

asyncio.run(main())
```

示例拥有该沙箱，删除前导出PNG。ServerClient.aclose只关闭HTTP客户端，最终sb.kill才清理该沙箱内远程进程。示例仅源码/语法检查，不能替代执行后的云端/模型回执。

## 快速开始（HTTP POST）

ABX_SERVER_URL来自运行中模板SDK network.get_url(9000)，ABX_SERVER_TOKEN为该服务已配置的进程令牌。

```bash
curl --fail-with-body --max-time 90 -X POST "$ABX_SERVER_URL/commands/browser_use_self_test" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{}'
```

返回{"result":"BROWSER_USE_NATIVE_OK"}。模型调用使用SDK启动的9010地址/令牌，POST /commands/browser_use，JSON为{"task":"Read the heading","url":"https://example.com/","max_steps":8,"command_timeout":300}。HTTP200的result包裹结构化结果；必须done和success都为true才表示原生任务成功。参数缺失/未声明/类型错误400，认证401，未知命令404；限制/配置/路径/版本/忙碌/期限/原生失败500。响应缓冲，客户端超时/断连不保证取消。

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
| ABX_SERVER_TOKEN | no | empty | command-server process bearer token |

模型配置只通过私有文件stdin进入，不继承到Chromium。每次独立HOME/XDG/profile/原生文件目录，关闭遥测/云同步/默认扩展/use_cloud，不导入调用者账号或已保存浏览器。CDP启动显式请求回环地址，只公布命令9000。浏览器和模型仍有沙箱用户权限及网络，这不是额外OS隔离。结果和PNG可能含网页私密信息；返回字符串替换模型密钥/地址的完整值。

## 资源

2vCPU/2048MB，命令9000，可显式启动模型9010；独立SDK测试夹具使用9011。--disable-dev-shm-usage避免依赖大/dev/shm。每个服务只运行一个浏览器任务，并发重操作返回busy500。max_steps1..20，每步最多3动作；模型30秒/零重试/4096 token，原生动作30秒/步骤60秒/LLM40秒门禁；外层1..900秒另加有限清理。每路输出256KiB，PNG16MiB渲染后检查。正常成功/失败/期限均删除私有浏览器配置/文件并清理自有进程，PNG交由调用者保存。服务突然丢失或同用户恶意代码仍以删除自有沙箱为最终边界。镜像根文件系统8GiB构建门禁。

## 已验证

新1.0.0尚无提供方通过回执。真实本地库/Chromium/协议/动作/独立计数/PNG夹具仅为L0，不代表真实模型或云端。待镜像/最新CI、真实SDK创建极速版及独立真实模型浏览器流程。其他提供方及架构未验证。

## 二次开发

python -m venv <new-prefix>后，用<new-prefix>/bin/python -m pip install --require-hashes -r browser-use/requirements.lock及pip check恢复。BROWSER_USE_PYTHON保留虚拟环境Python路径，不解析其符号链接，配置实际固定浏览器缓存/执行文件。python -m pytest -q browser-use/test_commands.py browser-use/test_model_controller.py。夹具响应/程序均人工编写，不在操作者主机运行真实模型生成shell。

[step指南](../docs/platform-steps.zh-CN.md)：python scripts/prepare_steps.py browser-use --output /tmp/browser-use-steps仅准备，python scripts/run_steps_e2e.py browser-use --timeout 1200实际执行。完整HTTP控制器关闭模型；单独真实模型SDK验收：python browser-use/model_e2e_test.py --sandbox-id <owned-fresh-sandbox-id>。需要固定SDK/httpx/Pillow、三个模型变量及空闲9010/9011，只拥有自己的夹具/服务/文件，独立确认计数3、提交nonce、PNG及监听/文件不存在，保留调用者沙箱。导出后需另行销毁自有沙箱。

## 贡献

遵循[CONTRIBUTING](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)、[设计](../docs/design/browser-use.md)，同步双语API/限制/证据。共享严格SHA256锁支持需先合并[PR146](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/146)。

## 问题反馈

[Issue51](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/51)；模板[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，客户端/服务[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

封装代码[Apache-2.0](../LICENSE)。Browser-use为MIT，保留[上游原许可](upstream-LICENSE)。Chromium为BSD类及第三方许可，声明随官方Playwright安装器保留；Playwright为Apache-2.0。哈希固定依赖保留各自安装声明，不能把整个镜像统一重标Apache-2.0。不包含模型权重或云服务账号。
