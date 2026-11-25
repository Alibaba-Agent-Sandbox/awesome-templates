# 为已有 Sandbox 绑定模板 API

[English](registry-api.md)

模板可以附带 `registry.yaml` 和包内 OpenAPI 3.1 文件，让 CLI 展示业务操作并按名称调用。使用 0.6 CLI 预览版，通过 `abx sandbox --help` 查看已安装版本的选项。增加或绑定 API 声明不会安装、启动服务，也不会授予调用权限。服务启动仍由模板部署流程负责。

`template.yaml` 仍负责模板资源与启动。增加 `apis` 不会把已有模板转换成提议中的 `specVersion: 1` 资源格式。`registry-v1.schema.json` 的上架与初始化结构是另一部分；单独声明 API 使用其中的 `#/$defs/apiBindings`，不必填写上架字段。

## 模板包文件

把下面两个文件放在已有 `template.yaml` 旁边。案例描述一个已在 9000 端口监听的服务的 `hello` 命令。

```yaml
# registry.yaml
apis:
  commands:
    resource: sandbox.agent
    port: 9000
    openapi: ./openapi.yaml
```

```yaml
# openapi.yaml
openapi: 3.1.0
info:
  title: Hello API
  version: '1.0'
paths:
  /commands/hello:
    post:
      operationId: hello
      security:
        - applicationToken: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              additionalProperties: false
              required: [name]
              properties:
                name:
                  type: string
      responses:
        '200':
          description: Command result
components:
  securitySchemes:
    applicationToken:
      type: http
      scheme: bearer
```

`resource` 是选择绑定时使用的资源逻辑标签。当前 CLI 接受 `sandbox.NAME`，此字段尚不接受 Serving Gateway。`port` 是实际服务端口，不会替你启动监听。`operationId` 是操作名；本地别名可以缩短操作名称，无需修改 HTTP 路由或 Server SDK 装饰器。

## 绑定、查看和调用

将 `TARGET` 设置为已有 Sandbox ID，或指向该 Sandbox 的本地部署名称：

```bash
abx sandbox "$TARGET" --bind ./registry.yaml --resource sandbox.agent \
  --credential commands.applicationToken=config:server_token \
  --alias greet=commands:hello
abx sandbox "$TARGET" --help
abx sandbox "$TARGET" hello --help
abx sandbox "$TARGET" greet --body '{"name":"Ada"}'
```

`config:server_token` 读取已配置的应用令牌。对于独立运营的服务，先将运营者提供的令牌配置到环境变量，再用 `--credential commands.applicationToken=env:HELLO_API_TOKEN`。绑定保存来源引用，不保存令牌值。应用令牌与 Provider API Key、云 AK/SK 是不同凭据。

帮助来自保存的声明，可以离线读取；它不证明服务正在运行、用户有权限，也不意味着 CLI 能调用所有 OpenAPI 结构。实际调用仍会返回鉴权、参数校验与业务错误。再次绑定会替换该目标的 API、凭据引用及别名。调用 API 不会创建 Sandbox，也不会回退执行 Shell。

保留 `--body @request.json` 传入完整 JSON。路径、查询、请求头和请求体选项以已安装版本的操作帮助为准。多个 API 可以有同名操作，此时使用 `--api NAME` 或明确的本地别名。

## 编写约束

| 字段或行为 | 约定 |
| --- | --- |
| `apis` | 1–32 个命名 API 绑定 |
| API 名称 | 字母开头，后接字母、数字、`_` 或 `-`，最多 64 字符 |
| 每个绑定 | 仅有 `resource`、`port`、`openapi` 三个必填字段 |
| `resource` | `sandbox.NAME`，NAME 为字母开头的字母、数字、`_`、`-` 组合 |
| `port` | 1–65535 的整数 |
| `openapi` | 已存在的包内文件，解析符号链接后仍不能越界，不能是 URL |
| 文件 | Registry 与 OpenAPI 各不超过 1 MiB；兼容 JSON 的 YAML，不允许重复键或 YAML 别名 |
| OpenAPI | 3.1.x，同一 API 内可调用的 `operationId` 唯一 |
| 引用 | 仅内部、非递归 JSON Pointer；外部引用需先打包进文档 |
| 调用扩展 | 暂不支持 `x-abx-*` 扩展 |

模板检查器检查发布结构、本地路径、引用与操作身份。CLI 还会检查所支持的请求结构和鉴权子集。HTTP bearer 与请求头 API Key 可以绑定明确的凭据来源。OpenAPI 本身不会实现云 AK/SK 签名、OAuth 登录、文件上传、Shell 脚本或自动获取参数；这些行为需要实际已实现的操作或适配器，不能通过自创扩展声明为可用。

发布前执行 `python scripts/check_template.py 模板目录`。Registry 目录摘要只包含 API 与操作身份，不导出请求示例、默认值、鉴权值或服务 URL。所有公开源码中都不要放入凭据。
