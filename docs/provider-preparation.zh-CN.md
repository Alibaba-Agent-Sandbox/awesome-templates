# Provider 负责的模板准备

[English](provider-preparation.md)

每个 `sandbox.<名称>` 指定一个 Provider；`template` 属性按其合同校验。模板 ID、镜像 URI 及卷属于特定 Provider、账号和地域，不能直接跨云转换。Express 地域保留在 `template.region`，同级静态卷采用该地域。

`buildConfig` 选择 Dockerfile/context 或原生 steps。Dockerfile 分支构建镜像，有 `image` 时向该地址推送；steps 分支将 `image` 作为输入并准备平台模板，不承诺导出完成后的 OCI 镜像。省略 buildConfig 且填写 image 时直接使用该镜像；reference 借用已有模板。

仓库认证、证书及拉取网络可用 `registryConfig` 覆盖。可推导的仓库类型和普通 Linux 系统类型由适配器处理。仓库实例身份无法可靠识别时应明确失败并指导配置，不猜测实例 ID。Dockerfile 中安装依赖不等于创建卷、挂载或授予权限。

Provider 能力不足应在操作前报错，不能静默忽略字段或自动换 Provider。其他 Provider 必须使用自己的字段，不直接套用 Express 配置。动态实例启动见[运行环境](runtime-environment.zh-CN.md)，静态部署见[资源规范](template-spec.zh-CN.md)。
