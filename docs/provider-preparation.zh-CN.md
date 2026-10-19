# 提供方负责的模板准备

可移植产物是源码目录。注册模板 ID、镜像 URI、基础镜像和启动引用属于各自提供方、
账号和地域，不能转换成另一朵云的模板 ID。[English](provider-preparation.md)。

## 准备职责

providers 值是前置要求提示。provider-preparation-required 表示选定提供方须将源码
准备为自己的后端产物再启动，不表示支持或验证通过，也不声称插件实现了自动准备。
已实现的自动操作归提供方：选择对应 base/profile、构建或获取适配镜像、上传可达
registry、调用原生注册 API，并返回自己的启动引用。源码目录、manifest、命令、版本
和哈希仍是权威，目录/Git 引用不是云端模板 ID。

| 提供方 | 准备与启动边界 |
| --- | --- |
| alicloud-express | FC base、generation、start/readiness；Dockerfile 或显式生成的 steps |
| alicloud-container | 自己的容器镜像、base、注册和启动引用 |
| cubesandbox | 自己的 runtime/镜像准备和注册模板引用 |
| e2b | 原生构建注册，不复用 Express key/ID |
| opensandbox | 自己可达镜像及服务启动，镜像 URI 不是其他云的模板 ID |

实际能力以提供方声明和当前实现为准。安装插件或展示命令不能补足缺失的准备实现。
契约见独立 [providers](https://github.com/Alibaba-Agent-Sandbox/awesome-providers)
及 [SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk)。本仓库不臆造端点或转换跨云 ID。

## 能力与不支持

capabilities 是实际需求。准备启动前与提供方匹配，缺 terminal、code、files、shell
或必要端口时明确报不支持，不得暗中删需求、换名或以原名称启动缩减产品。实现切片须有
明确设计、文档、manifest 和验收。

准备、凭据、账号/地域、镜像可达性或注册不可用时明确失败。凭据只用于对应提供方；
模型设置按服务进程启动边界注入。仅清理本轮创建资源。

## 验收

目录提示、自动准备结果和原生后端验收是独立声明。README Verified、tested_on、status
和[验收等级](template-spec.zh-CN.md)只按各自通过证据更新。Express 成功不能认证原生
E2B、Cube、OpenSandbox 或容器版；每个都需精确源码的真实部署、调用和自有清理。
保留失败和缺少的检查。

修改提示时同步双语和回归。[调用指南](using-templates.zh-CN.md)说明用法，
[step 指南](platform-steps.zh-CN.md)说明本仓库已执行的 Express 准备路径。
