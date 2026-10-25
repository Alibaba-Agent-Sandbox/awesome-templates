# 模板启动与验证

模板描述要启动的环境、启动命令和对外服务。一次启动即可使用模板内容，无需选择工作流。[English](workflows.md)。

```sh
abx --provider alicloud-express template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello --yes
```

## 当前机器契约

源码清单和托管目录条目使用 `spec_version: 5`，目录索引使用 `schema_version: 2`。源码 schema 为 [template-v5.schema.json](../spec/template-v5.schema.json)。[共享启动规则](../spec/contracts/launch-v1.json)来自 [Python 契约仓库](https://github.com/Alibaba-Agent-Sandbox/python-sdk/tree/main/contracts)，通过 `scripts/sync_launch_contracts.py` 按精确提交同步并锁定。

`provides` 列出全部对外服务，包括协议、版本、端口和操作；`start_cmd` 启动模板，`ready_cmd` 检查就绪。命令继续在 `commands.py` 注册，不要求作者为每个操作重复声明启动方式或能力计划。

启动时按需准备源码，创建一个沙箱，执行启动和就绪命令，返回每个声明服务的端点。内置 server v2 协议额外检查健康及已声明的命令发现；其他协议保持可扩展，仅解析端点不代表其协议已验证。模板的就绪命令负责整体就绪检查。已经准备好的镜像或绑定 Provider 的原生模板引用提供运行环境，不改变模板服务。安装了工具不意味着立即执行它的业务任务：需要提示词、密码或工作目录的命令仍在启动后调用。例如数据库模板通过 `services_start` 接收密码与数据目录；启动模板不会编造这些参数。

Provider 负责镜像仓库、上传配置、原生模板注册、沙箱创建及端点解析。CLI/SDK 检查准备、创建、启动和已声明服务实际需要的操作。镜像包含 Python 不代表依赖 Provider 的解释器 API；调用解释器是独立操作，按真实支持情况处理。

## 部署拓扑

可选的 `application` 保留部署位置、适配器、hooks、状态和限额，用于显式应用部署。模板安装、源码准备和沙箱启动不会执行这些部署 hooks。[本地](examples/application-local/template.yaml)与[外部](examples/application-external/template.yaml)示例保持此边界。

## 资源归属与证据

源码快照和资源日志绑定源码、有效配置以及创建的资源。清理只删除本次运行拥有的资源，保留的镜像或原生模板必须明确报告。平台凭证与服务令牌保持分离。

静态校验只证明配置一致，不证明云端运行成功。一次启动验证记录精确的源码、清单、CLI、SDK、Provider 版本、全部服务检查、实际调用和独立清理结果。必需检查缺失或跳过都不算通过；模型任务和可选原生接口单独验证。

历史回执保持不可变，保留原工作流、消费入口及源码范围，不能重写为规范 5 的验收。`spec/contracts` 中的历史回执契约仍可用于读取旧证据，不要求当前作者声明工作流。目录记录本身不认证模板。

## 验证

安装 `scripts/requirements-spec.txt`，执行 `scripts/test_spec_tools.py`、`scripts/check_template.py --all`、`scripts/check_managed_catalog.py`、模板启动回归和 `scripts/check_docs.py`。本地检查不能代替真实平台启动及清理。

## 显式构建方案

源码可保留经过审查的 `build_profiles.<id>: {dockerfile: Dockerfile.<id>, context: "."}`。只有需要主动更换构建配方时，才使用 `--build-profile <id>`；它不选择不同应用内容或服务。`python-hello` 的 portable 配方与默认极速版配方仍独立。镜像和云端验收必须标明实际使用的配方。
