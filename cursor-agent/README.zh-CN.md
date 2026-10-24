# Cursor Agent

[English](README.md)。

## 做什么

通过类型化命名命令，在自有一次性沙箱中运行原版 Cursor Agent CLI。推理和工具执行由原生 Cursor 完成。agent任务需要独立的CURSOR_API_KEY；不会复用兼容模型或操作端其他密钥。自动工具执行必须显式传入allow_unsafe_tools=True。

## 技术栈

固定官方CLI2026.10.19-6bbf2c4、Linux x86_64，原版启动器、内置Node及原生模块保持不变。原包183,733,394字节，控制端实测SHA256为`cf80cc18d8b33bf33e762353977ca1868cfc45290c92c0ffdcef83bb8b37b44f`，并非上游发布的校验和。460个普通文件共585,886,062字节。[完整清单](upstream.json)、[许可说明](UPSTREAM-NOTICE.md)、[设计](../docs/design/cursor-agent.md)。基础镜像为阿里云generation2，Python3.13；服务端源码固定34e7e011c5569f77b7f605e65313be7498f6cf02。

## 解决的问题

提供可复现安装、标量SDK/HTTP接口，以及有界执行和进程／私有状态清理。此模板是本地CLI运行环境；Cursor Cloud Agents及企业机器调度器不在认证范围内。真实厂商账号下的模型与代码行为，需要独立的真实凭证验收。

## 快速开始（CLI）

`abx run`命令在此显式选用`abx --native run`入口。

使用[已验证的原生CLI入口](../docs/using-templates.md#client-entry-compatibility)和已授权的Express配置。将<run>、<published-commit>、<owned-template-id>、<owned-sandbox-id>替换为唯一运行标记、公开40位源码提交和本次创建的资源。必须先发布精确源码；部署前将生成清单的name改成cursor-agent-<run>。

```bash
python scripts/prepare_steps.py cursor-agent --output /tmp/cursor-agent-steps-<run> \
  --source-commit <published-commit> --asset-transport parallel
python - <<'CONFIG'
from pathlib import Path
import yaml
p = Path("/tmp/cursor-agent-steps-<run>/template.yaml")
v = yaml.safe_load(p.read_text())
v["name"] = "cursor-agent-<run>"
p.write_text(yaml.safe_dump(v, sort_keys=False))
CONFIG
abx --native template deploy /tmp/cursor-agent-steps-<run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> agent_version
abx --native run <owned-sandbox-id> agent_native_check
abx --native run <owned-sandbox-id> agent_setup_check
# 命令服务在启动前已获得自己的厂商密钥时：
abx --native run <owned-sandbox-id> agent --json-args '{"prompt":"Repair existing calc.py and preserve tests","cwd":"project","command_timeout":300,"allow_unsafe_tools":true}'
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

先创建project。带真实厂商账号的调用行仅检查语法，未声称调用成功。create环境不会重新配置预热进程；参见下方显式启动和[运行时指南](../docs/runtime-environment.md)。原生CLI支持--server-port；SDK/HTTP示例使用独立认证的9010服务，认证信息必须与进程匹配。

正式无凭证测试仅在自有测试配方中设置明确无效的合成密钥，实际调用原版程序的HTTP和SDK错误路径；不会注入操作端厂商／模型密钥：

```bash
ABX='abx --native' python scripts/run_steps_e2e.py cursor-agent \
  --sandbox-create sdk --http --asset-transport oss
```

OSS传输需要[固定的可选缓存依赖](../scripts/requirements-steps-cache.txt)，仅创建本次私有临时对象，校验原包摘要／ACL并独立确认删除。原生steps无需本地Docker；Docker镜像验收单独记录。

## 快速开始（Python SDK）

按[配对源码安装](../docs/python-client-installation.md)安装agent-sandbox-client。在操作端安全环境中设置CURSOR_API_KEY；不把密钥值放入argv或命令JSON。<owned-template-id>属于本次部署，示例创建独立项目与沙箱。

```python
import asyncio, os, secrets, uuid
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=900)
    server = None
    try:
        print(await sb.run("agent_version"))
        project = "/home/user/app/cursor-example-" + uuid.uuid4().hex
        await sb.commands.run("mkdir -p " + project)
        await sb.files.write(project + "/calc.py", "def add(a,b): return a-b\n")
        token = secrets.token_urlsafe(32)
        server = await sb.start_server(port=9010, commands="/home/user/app/commands.py",
            token=token, env={"CURSOR_API_KEY": os.environ["CURSOR_API_KEY"], "ABX_PTY_PORT": "9011"})
        print(await server.commands.run("agent_setup_check"))
        result = await server.commands.run("agent", prompt="Repair existing calc.py and write report.txt",
            cwd=project, command_timeout=300, allow_unsafe_tools=True, timeout=420)
        print(result["stdout"])
    finally:
        if server is not None:
            await server.aclose()
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

未声称厂商账号调用行执行成功。沙箱寿命需覆盖命令及清理；命令超时与TTL分开。关闭借用服务客户端会关闭客户端传输；删除自有沙箱结束远程进程。自动化部署需独立确认资源已不存在。

## 快速开始（HTTP POST）

使用已配置进程的转发URL和独立Bearer；直接JSON参数不包含厂商密钥。

```bash
curl --fail-with-body -X POST "$CURSOR_COMMAND_SERVER_URL/commands/agent" \
  -H "Authorization: Bearer $COMMAND_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"prompt":"Repair existing calc.py and write report.txt","cwd":"project","command_timeout":300,"allow_unsafe_tools":true}'
```

HTTP200封装为`{"result":{"stdout":"...","stderr":"","exit_code":0,...}}`。缺失／未知／类型错误参数400，命令认证401，未知命令404，语义或原生执行错误500，错误仅给出有界类别与退出码。预期的无效密钥500是程序错误路径测试，不是模型成功。/health、/commands、文件和shell共享相同进程／认证边界。HTTP断开不取消云作业，原操作仍按期限清理。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| agent_version | 无 | 验证原文件后执行原生--version，返回固定版本字符串 |
| agent_native_check | 无 | original_native/headless_print/json_output/explicit_force/contained_workspace布尔字段，执行原生--help，无模型调用 |
| agent_setup_check | 无 | mode/installed/pinned_version/api_key_set/requires_unsafe_optin/vendor_authentication_verified/compatible_model_fallback；仅状态，无值或网络 |
| agent | prompt必填字符串；cwd字符串默认空；command_timeout整数300；allow_unsafe_tools布尔False；model字符串默认空 | 缓冲原生最终响应；明确授权后可读写文件和执行工具 |

prompt为1..32768UTF8字节，非空且无NUL。cwd最长4096UTF8字节、无NUL，必须解析为WORKSPACE内已存在目录；空值选根目录。command_timeout为1..600秒，布尔值拒绝。allow_unsafe_tools必须精确为True。model为空时使用厂商默认选择；非空最多200个ASCII标识字符[A-Za-z0-9_.:/-]且字母数字开头，不声明模型可用性。

成功结果包含stdout字符串、stderr空字符串、exit_code:0、native_completed:true、native_version、archive_sha256、permission_profile:explicit-owned-sandbox-bypass、requested_model。原生JSON必须type=result/subtype=success/is_error=false且最终文本非空。非零、格式错误、未完成、超时或超量均抛错，不返回部分成功。实际模型与代码产物另行验收。

固定原生argv为--print --output-format json --disable-auto-update --disable-project-configs --sandbox disabled --trust --force --workspace <受限项目>，可选--model及原样prompt。该显式模式使用外层自有沙箱隔离，禁用原生嵌套沙箱。参数通过argv传递；不暴露任意参数、认证绕过、操作端其他密钥兜底或替代规划器。

## 配置

| 变量 | 默认／要求 | 含义 |
| --- | --- | --- |
| CURSOR_API_KEY | 空；agent必需 | 厂商凭证，命令模块导入时捕获 |
| WORKSPACE | /home/user/app | 项目根目录，导入时捕获 |
| ABX_SERVER_TOKEN | 空／可选 | 独立命令服务Bearer，不是Cursor凭证 |

原生子进程只获得自身显式厂商密钥及私有HOME/config/data/cache/TMP等最小环境。固定原生参数关闭更新和项目配置加载；不使用操作系统钥匙串或原生持久会话。成功／失败／超时后删除每次私有状态。服务和工具共享OS用户，路径不是其他租户的隔离边界；自动工具仅用于自有一次性沙箱。

每个服务进程最多一个agent操作，重叠返回busy。stdout/stderr各限256KiB；命令1..600秒加最多90秒清理，客户端超时应至少command_timeout+120秒。已知厂商密钥、命令token、私有HOME值脱敏。私有会话或云资源ID不进入公开证据。

## 资源

仅Linux x86_64，2vCPU/4096MB/9000端口，非root用户，WORKSPACE为/home/user/app；构建检查8GiB根盘上限。原包解压585.9MB，压缩183.7MB。无需声明嵌套Docker、KVM、GPU或桌面能力。模型任务需要厂商出口与账号；峰值RSS和认证吞吐未测。其他架构／提供商、交互／恢复／MCP／插件／委派／云Agent功能未认证。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

```bash
python -m pytest -q cursor-agent/test_commands.py cursor-agent/test_controller.py cursor-agent/test_install.py
python scripts/check_template.py cursor-agent --strict
python scripts/check_docs.py
```

保留原文件摘要与许可、显式权限、私有状态和进程清理。变更的COPY／辅助源码必须先发布，再准备不可变steps；保持15000字节wire和通用300MiB原包限制。完整外部控制器必须执行真实原版HTTP及SDK无效密钥拒绝，安装／版本回执不能代替。有真实厂商凭证时，显式选择自有远程代码控制器：既有源码修复、原始3项测试字节不变、报告／精确随机标记、原始3项加独立4项断言、返回后新ACK。生成代码不在操作端运行。

## 贡献

阅读[贡献指南](../CONTRIBUTING.md)、[项目标准](../docs/project-standards.md)、[文档标准](../docs/documentation-standards.md)及[模板规范](../docs/template-spec.md)。独立模板、类型契约、双语文档、设计、目录、工程记录与当前源证据一起提交；完成最新CI／review后正常合并。

## 问题反馈

[Issue63](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/63)、[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。上游行为反馈给Cursor，不附凭证或私有会话。

## 许可证

自编写模板代码Apache-2.0；Anysphere原版软件和第三方许可保持原条款与声明，见[说明](UPSTREAM-NOTICE.md)。本Git仓库不分发上游二进制／源码，也不声称厂商背书。
