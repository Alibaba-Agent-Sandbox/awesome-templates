# 提供方负责的模板准备

可移植输入是源码目录。注册模板 ID、镜像 URI 和启动引用属于具体提供方、账号和地域，不能跨云转换。[English](provider-preparation.md)。

## 准备职责

清单显式声明 `provides`、`workflows` 和 `default_workflow`。规划器只检查选中路径的操作、输入种类和启动方式；Provider 的成熟度与该路径是否已验证独立。

源码准备由对应 adapter 构建、推送并按平台协议注册。CLI 在临时构建目录解析官方配方的 `<region>`/`<tag>`，通过 Docker 阶段准备固定版本服务端 wheel。应用指令、非 root USER 和源码文件不变；其他未解析占位符在构建前报错，自定义基础镜像使用显式构建方案。应用部署 hooks 仍只由应用部署操作执行。

## 路径条件

模板的 Python、命名服务和软件由镜像提供。应用 HTTP 路径不依赖统一解释器。普通 exec、模板服务和统一解释器必须分别声明和检查；缺少上下文或实时流支持时明确拒绝，不能忽略参数或降级 shell。

E2B、Cube 和容器版使用平台托管引用，不能将 OCI image 当模板 ID。OpenSandbox 使用镜像及 execd，当前不承诺执行镜像原生 ENTRYPOINT。Python Provider 不进行源码准备，需显式准备的镜像或托管引用。

准备、配置、权限、网络和协议故障分别报告。平台凭据与模板应用凭据隔离，端点必须属于本次 sandbox 和 port；不自动重定向或匿名重试。

## 资源和验收

推送、注册和创建请求前先持久写 intent，成功后记录返回 ID；未知响应不能盲重试。仅清理本轮拥有的资源。镜像或原生模板没有已实现的删除协议时，报告保留项和人工恢复信息，不能宣称完全清理。

项目验证仅由可信 CI 收据推导，绑定精确输入、工作流、实际消费入口和网络位置。作者字段不能认证，历史 guest/bridge 通过不能认证统一 launch。参见[工作流契约与证据](workflows.zh-CN.md)、[调用指南](using-templates.zh-CN.md)和[step 指南](platform-steps.zh-CN.md)。
