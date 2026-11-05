# 托管 Agents API 参考

客户端使用稳定的 Gateway URL 和 `Authorization: Bearer <businessKey>`。
资源按认证 owner 隔离。不支持的设置会明确失败；提交前查询
`GET /v1/agent-sandbox/capabilities` 和部署允许的模型列表。
协议为 `agent-sandbox-managed-agents/v1`，参考 OpenAI Agents 的子集并提供本项目扩展，
不承诺任意 OpenAI SDK 互操作。

需要使用声明此协议的运行时发行版；已发布的 SDK 0.4.0a6 不提供托管 API。adapter 功能以实际部署返回的 capabilities 为准。


## 操作

公开入口如下。Health 只表示就绪检查，不证明模型任务成功。

| 方法 | 路径 | 成功码 |
| --- | --- | --- |
| `GET` | `/healthz` | 200 |
| `GET` | `/v1/agent-sandbox/capabilities` | 200 |
| `GET` | `/v1/models` | 200 |
| `GET` | `/v1/models/{model_id}` | 200 |
| `GET` | `/v1/agents/runtimes` | 200 |
| `POST` | `/v1/agents` | 201 |
| `GET` | `/v1/agents` | 200 |
| `GET` | `/v1/agents/{agent_id}` | 200 |
| `POST` | `/v1/agents/{agent_id}` | 200 |
| `DELETE` | `/v1/agents/{agent_id}` | 200 |
| `POST` | `/v1/agents/sessions` | 201 |
| `GET` | `/v1/agents/sessions` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}` | 200 |
| `POST` | `/v1/agents/sessions/{session_id}` | 200 |
| `DELETE` | `/v1/agents/sessions/{session_id}` | 200 |
| `POST` | `/v1/agents/sessions/{session_id}/events` | 202 |
| `GET` | `/v1/agents/sessions/{session_id}/events` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/items` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/turns` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/turns/{turn_id}` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/turns/{turn_id}/items` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/artifacts` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/artifacts/{artifact_id}` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/artifacts/{artifact_id}/content` | 200 |
| `DELETE` | `/v1/agents/sessions/{session_id}/artifacts/{artifact_id}` | 200 |
| `POST` | `/v1/files` | 200 |
| `GET` | `/v1/files` | 200 |
| `GET` | `/v1/files/{file_id}` | 200 |
| `GET` | `/v1/files/{file_id}/content` | 200 |
| `DELETE` | `/v1/files/{file_id}` | 200 |
| `GET` | `/v1/agents/environments` | 200 |
| `GET` | `/v1/agents/environments/{environment_id}` | 200 |
| `POST` | `/v1/agent-sandbox/sessions/{session_id}/close` | 202 |
| `GET` | `/v1/agent-sandbox/operations/{operation_id}` | 200 |
| `POST` | `/v1/agent-sandbox/sessions/{session_id}/submissions` | 202 |
| `GET` | `/v1/agent-sandbox/sessions/{session_id}/submissions` | 200 |
| `GET` | `/v1/agent-sandbox/sessions/{session_id}/submissions/{submission_id}` | 200 |
| `POST` | `/v1/agent-sandbox/sessions/{session_id}/turns/{turn_id}/cancel` | 202 |
| `POST` | `/v1/agent-sandbox/sessions/{session_id}/submissions/{submission_id}/cancel` | 202 |

## Session、输入和收据

使用内联 `agent` 或保存的 Agent 配置创建逻辑 Session，可附带初始 `input`。
Session 固定其配置快照；修改保存的 Agent 只影响之后创建的 Session。Session 更新只支持
metadata。本 profile 不支持任意远程工具、MCP endpoint 或工作区/环境创建；Environment
是 Session 计算状态的只读投影。

重试 Session 创建或输入时复用稳定的 `Idempotency-Key`。创建返回 201，带初始输入时
还返回 `X-Agent-Sandbox-Submission-Id`。`POST .../events` 接受支持的输入/取消事件，
返回 202、空响应体、收据头和 `Location`。查询托管 Submission 恢复接受状态及固定的
Turn ID。显式入队接口必须提供 `Idempotency-Key`，返回 Submission。响应丢失或租约到期
不能证明可以安全重放执行。

Turn 正在执行或采集产物时，不支持的 steering 返回
409 `active_turn_not_steerable`。Enqueue 创建下一轮，不是引导当前轮。
取消指定 Submission 或 Turn 返回 Operation；接受取消不代表计算已停止，需继续查询
Operation，不确定结果需要协调处理。

## 文件和产物

`POST /v1/files` 接受 multipart：`purpose=user_data` 和二进制 `file`。
在 Session 初始输入或后续输入中引用返回的 opaque ID：

```json
{"input":"Read the CSV and write /workspace/outputs/summary.csv",
 "x_agent_sandbox":{"input_files":[
   {"file_id":"file-id","path":"/workspace/input/sales.csv"}]}}
```

输入只在下一轮边界安装到 `/workspace/input/` 下。单独上传不会写入运行中工作区。
Artifact 是从 `/workspace/outputs/` 捕获的不可变字节，关联 Turn、路径和摘要。删除公开
Artifact 不删除工作区原文件。删除公开输入会移除其可见性；已冻结的 Submission 可保留
内部引用，直到能够安全回收。文件、产物、单轮和 owner 保留总量分别受大小限制。

## 分页、事件和清理

列表使用 opaque 游标，按能力契约支持 `limit`、`order`、`after` 或 `before`。
`has_more` 为真时保存返回的 `last_id`，不要从数据库位置推导游标。

GET Session events 提供持久化 SSE。断线后使用最后事件 ID 重连；回放不会重新运行
Agent。遇到明确的事件缺口或游标过期应读取已保存的 Turn/items。断线及客户端超时
不取消 Turn；慢订阅者和订阅者数量受限制。

Close 拒绝新任务，释放计算并保留已提交的历史/产物。查询 Operation 直到
`succeeded`；`failed` 或 `requires_reconcile` 需要操作方处理。Delete 移除公开资源后返回
200，正在执行/采集时返回 409。内部所有权记录可保留到确认清理完成。结果保留期到期会
独立于计算状态移除访问。

[模板用法](../agents-api/README.zh-CN.md) ·
[应用清单参考](managed-agent-applications.zh-CN.md)
