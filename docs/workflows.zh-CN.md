# 模板部署与应用运行

[English](workflows.md)

资源配置在 `template.yaml`。命名 `sandbox` 准备可复用模板及静态卷，命名 `serving` 通过组件原生 `props` 部署外置服务。两者可以单独或一起使用，见[资源规范](template-spec.zh-CN.md)。

普通源码模板的使用顺序是：下载目录、修改 `template.yaml`、执行 `abx deploy .`，再用模板自带 `run.py --template <template-id>` 创建动态实例并启动应用。`run.py` 的环境变量及 API 用法在各模板 README。部署本身不创建动态 Sandbox。

`template.startCommand` 和 `readyCommand` 保留 Provider 原生的模板准备阶段语义，不能替代每个动态实例的业务启动。容器监听端口、Provider 网络可达性、应用协议和认证分别由镜像/程序、Provider 和业务代码负责。

采用已有模板时，在 `template.reference` 填入所属 Provider 的引用；该资源属于借用，不更新或删除它。静态卷的引用同样不代表挂载；动态实例由业务代码或 SDK 选择挂载及租期。

需要更换 Dockerfile 时，直接修改 `template.buildConfig.dockerfile`；`context` 缺省为该文件所在目录。可以保留独立的备用 Dockerfile，但没有公开 build profile 层。Provider 的资源、镜像及网络能力以其实际合同为准，配方存在不代表跨 Provider 已验证。

先导出结果，再删除拥有的动态实例；部署创建的模板、卷和 Serving 资源单独管理。保留私有会话文件直到实例清理完成。详见[使用指南](using-templates.zh-CN.md)。
