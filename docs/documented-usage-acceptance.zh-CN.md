# 完成模板文档中的实际任务

[English](documented-usage-acceptance.md)

构建镜像、创建模板只说明准备步骤成功。使用新安装的已发布 CLI/SDK，按模板
README 配置 provider、独立应用令牌、所需账号和模型凭据，启动后完成文档中的
任务，检查并下载结果，再清理本次资源。

默认公开启动验证器会清除清单中默认值为空的环境变量，并关闭模型调用。
执行真实模型和业务控制器时，显式配置该模板文档列出的变量，然后运行：

```bash
python scripts/public_launch_e2e.py opencode \
  --provider alicloud-express --source ./opencode \
  --application-controller --real-usage --build-timeout 3600 \
  --output opencode-real-usage-attempt-1.json
```

此模式保留显式配置的清单环境变量作为运行时配置，开启真实模型调用，必须
执行控制器。出现 SKIP 或 NOT RUN 即使退出码为零也不通过，可能产生 API 费用。
云管理凭据不会传给控制器；模型 Key 只放运行配置，不放 Dockerfile、构建参数、
回执或日志。原有包版本、源码身份、应用认证和自有资源清理检查仍然执行。
Cursor/Devin 的无效 Key、缺账号模拟配置在此模式下关闭，必须配置真实账号；
工具要求专属账号时，通用兼容模型 Key 不能替代。

控制器通过还不能自动认定完整验收。对照运行时发现结果，逐一成功调用所有可
调用命令（包括隐藏命令）、自定义路由及启用的 SDK/原生接口，并检查结果。
原样执行 README 的任务和文件传输、配置步骤。模型工具还要展示切换第二个受
支持模型、配置 endpoint/API Key、按文档登录；检查真实响应或产物，不能只看
模型名称字符串。编程任务必须修改原有源码、生成新文件、保留原测试，再通过
独立的隐藏断言。未支持的操作和缺少的账号条件如实记录。

OpenSandbox 使用其 provider 文档的配置；需要时显式选择模板的 portable
构建方案，不暗中切换平台或镜像配方。原生托管条目使用各自所属 provider。

OpenSandbox 的 server-proxy 路由需要保留解析后的 URL 和网关头。代理会移除
Bearer Authorization；公开调用指南同时通过未被网关占用的 `X-Access-Token`
发送应用令牌。控制器对同一服务、已携带正确应用 Bearer 令牌的请求采用相同适配，
错误令牌仍然拒绝。无请求体的应用 DELETE 需要显式 `Content-Length: 0`
（例如 `httpx.request(..., content=b"")`）；代理以流转发 DELETE，应用服务器则
按约定拒绝 chunked 请求。不能覆盖网关头或改写显式提供的请求体。

公开 Python0.4.0a6 配合独立 CLI0.5.7，查询不存在的 OpenSandbox 时，可能得到
带稳定错误码 E2009 的通用 SandboxError。清理程序同时识别这个准确的不存在错误码
和对应异常类，再独立回读确认不存在；其他错误继续失败。这是调用方兼容处理，
不表示已修正公开版本的异常类。

每次运行保留新的有日期、脱敏工程证据，记录精确输入、已安装包、provider、
完整接口覆盖、业务结果、失败/跳过及独立确认的清理结果。当前版本至少一个
provider 完整通过后，可由 Registry 审阅并移除模板 Beta；历史或部分通过不能
替代。仅删除本次自有沙箱、模板和镜像；磁盘有限时逐个清理已完成的本地镜像
及不再需要的构建缓存。

每个完成的模板体验在 [blogs 仓库](https://github.com/Alibaba-Agent-Sandbox/blogs)
写成实践案例：从读者问题出发，说明安装配置、可执行流程、实际效果、二次开发
和限制。执行证据放工程记录，正文不写成测试报告，不发布没有实际得到的结果。
