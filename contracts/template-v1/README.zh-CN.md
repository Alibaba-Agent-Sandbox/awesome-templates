# Template v1 合同

[English](README.md)。

这里维护尚未启用的 v1 资源合同与纯归一化函数。当前 CLI、SDK、checker 与 Registry
仍使用原有合同；必须等消费者同步迁移后，才能把这里的配置向量作为部署配方。

本地资源入口是带 `specVersion: 1`、`name` 的 `template.yaml`，包含 Sandbox、Serving，
或通过明确的应用消费者联合使用两者。`registry.yaml` 只负责可选的上架与初始化描述，
资源解析不读取它；没有必填的运行时 `parameters`。

## 字段与阶段

- `sandbox.template` 在 `source`、`image`、已有 `reference` 中选且仅选一项。
  source 包含相对 Dockerfile、根构建上下文以及可选的 `profiles` 替代配方。
  `template.aliases` 保留查找别名，不代表允许覆盖其他云资源。
- `sandbox.template.props` 是真实模板准备接口的输入子集，不是原生管理 API 请求体。
  当前已知准备字段为 CPU 数和内存；Express 使用 MB，其他适配器按各自参考定义单位。
- `sandbox.instance` 是所选适配器的创建默认输入。`timeout` 为高层 API 寿命秒数
  （1–86400），`envs`、`metadata` 为字符串映射。环境空值声明保留既有 CLI 配置注入
  语义；纯函数不读取或生成凭据。准备阶段的规格不会悄悄复制到每一次创建请求。
- `sandbox.provider` 在尚未绑定的源码意图中可省略，执行时由现有 CLI/配置规则选择；
  与显式声明冲突时拒绝。求值后的执行输入必须有具体 Provider。带归属的已有引用仍须
  由真实 Provider 选择器校验，不能跨平台转换 ID。
- `sandbox.start`、`ready`、`services` 描述完整工作负载；服务声明协议、版本与端口，
  可选操作列表不等于后端权限。
- `deployment` 内使用原生 Serverless Devs 3 项目结构、组件标识与 props。
  本外壳不复制 FC schema，也不实现 Devs 变量、输出依赖、actions 或 flow。
- `application.type: agents-api` 显式选择现有托管消费者。`roles` 引用三个不同资源，
  `server` 选择源码或 digest 固定的镜像。`state` 和 `bindings` 保存实际配置引用，
  不要求用户再手工维护 binding JSON 文件。预算与自动认证默认只定义在一个来源中。
  托管寿命只填写 `sandbox.instance.timeout`（默认3600秒），内部 Session 最大寿命由它
  派生；公开 `sessions.maxLifetimeSeconds` 被拒绝，空闲/轮次预算须在寿命以内。

五个已知适配器只开放已有输入子集：Express 有按名称挂载卷与结构化寿命策略；
OpenSandbox 有已接入的 GPU 数量、安全访问与部分创建选项，但当前适配器没有 typed
卷/磁盘配额入口；E2B、Cube、容器版此处仅开放已确认的 timeout/env/metadata 创建输入，
不把未确认的资源透传称为原生支持。容器版已有 SandboxSet 卷保留仍是另一条能力。
本规范不把回调、内部请求类型或所有原生管理 API 自动变成 YAML。

第三方 Provider ID 不被禁止。求值后的第三方输入必须由绑定到真实已选 descriptor 的
`validateProvider` 校验，缺少校验时拒绝，不做万能透传。`contract.json` 记录当前静态
子集来源；消费者仍须将 schema 与实际实现版本锁定并检查一致性。本模块不安装或执行插件。

## 两阶段校验与执行数据

先用真实 JSON Schema 2020-12 校验器编译意图 schema，调用
`normalizeTemplateV1(raw, validateIntent, {stage: 'intent', provider})`。
得到的是补默认后的 v1 副本，原生表达式保留原文。

再将原生部署项目及私有资源载荷交给官方 Devs 解析器。不能用正则替换、仿造表达式语言，
也不能把求值后的秘密存入公开计划或构建文件。

随后使用 `schemaForStage(schema, 'resolved')` 及真实校验器，调用
`compileTemplateV1(parsed, validateResolved, {provider, validateProvider})`。
组件 props 仍须由所选组件原生 schema 校验，Provider 输入仍须进入真实 descriptor；
结构验证不等于组件或云端验收。

JavaScript 校验回调必须同步返回布尔值或抛错；Python 对应函数使用 snake_case，可接
`jsonschema` 的 `.validate`。归一化函数不读取进程环境、当前目录、凭据库、Registry
或云 API；compile 不输出旧的公开 spec5/6 版本标记。

私有结果包含现有执行器所需的工作负载、准备规格、实例环境、服务、端口、启动/就绪、
原生引用/镜像、别名与替代构建配方。托管结果还包含既有 application 字段、角色引用、
原生 roleProps 与 bindingValues。**这些临时值可能包含秘密，不能直接序列化成公开
计划、收据或镜像内容。**

托管函数身份/归属说明、内部环境变量与 bridge 的镜像/端口/启动参数由协调器生成，
显式冲突被拒绝。CPU、`memorySize: 4096`、日志和 VPC 等原生值按声明保留交给消费者。
bridge 使用 custom-container；当前协调器使用同一组件版本、求值后的地域和函数 RAM
角色，原生 role 与内部角色绑定不能冲突。这里不推导新的多角色 IAM 或通用托管流程。

## 可选初始化元数据

Registry schema 包含模板包身份/版本、双语简介、作者/许可证、标签、README、资源入口
与可选问题。问题使用标准非根 JSON Pointer 指向归一化资源文档中的实际字段；失效、
重复或非法目标报错。类型、约束与默认值来自目标资源及其 schema，表单不再维护一套
运行默认。

敏感问题声明 `environmentVariable`，目标必须是对应的原生 `${env('NAME')}` 或双引号
等价形式。这只是元数据一致性检查，不是表达式求值。收集值保存到私有配置/环境，不写
公开 YAML 字面值。`normalizeRegistryV1` 不负责收集、保存或应用答案；初始化消费者还
须依据目标 schema 校验非敏感值后再写入。

## 本地合同检查

使用仓库现有固定版本 Python 检查依赖，以及 `npm ci --prefix contracts/template-v1`。
运行本目录 Python 合同套件和 `npm test --prefix contracts/template-v1`；必要时用
`PYTHON` 选择 Python 环境。Node 套件真实调用 Python 消费者，比较完整归一化与编译结果。
向量覆盖五家支持子集、真实 Python 替代配方、未绑定/已绑定源码、原生表达式、FC/域名
意图、托管角色/私有绑定、无 Registry，以及阶段/字段/引用/冲突反例。

仓库现有规范、checker 与文档检查仍必须执行。真实表达式执行由 CLI 集成验证，构建、
部署、模型任务及资源释放由对应实现交付验证。跟踪事项：
[awesome-templates Issue309](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309)。

`sandbox.ports` 可选声明额外访问端口（去重整数1..65535）；compile 合并并排序 ports 与真实 services.port。端口不承诺已启动、协议或公共 Gateway 路由，不编造业务服务元数据。


## 源 YAML 读取

`parseYamlV1(textOrBytes)` / `parse_yaml_v1(text_or_bytes)` 与 `MAX_YAML_BYTES` 为模板、上架
metadata、目录文档提供同一个纯读取边界，不读文件或环境，也不求值 Devs 表达式。调用方
将文件读取限制为 MAX+1 字节。仅接受最多1MiB的严格UTF-8、单文档、字符串映射键及有限安全
JSON值；拒绝 alias、重复键和不支持的 tag。未使用的 anchor 可以保留。YAML版本声明只允许
1.2或省略。`!!str` 可固定字符串；其他显式标量 tag 不做改变 Core 类型的强制转换，因此
`!!float 1.0` 可用而 `!!float 1` 不属于v1源语法。日期、on/off保持字符串，`<<`不展开合并。

实际标量规则由 Node yaml2.9.1 Core 与 Python PyYAML6.0.3+yamlcore0.1.1 提供，不自行维护
resolver；异常不会回显源码。其他旧PyYAML用途不变。共享锁包含 `yaml-fixtures.json`，测试
调用两种真实解析器并比较完整结果。后续官方Devs解析是另一阶段，消费者传入私有项目时仍
须保持这里确定的类型，不能让第二次解析静默改值。
