# devin

[English](README.md)。

## 做什么

在自有一次性沙箱中，通过类型明确且有界的命名命令调用Cognition原版Devin CLI3000.11.92。推理与工具由原版负责；没有替代规划器或兼容模型兜底。自动工具必须显式allow_unsafe_tools=True。

## 技术栈

Alibaba generation2 Linuxx86_64基础镜像、Python3.13服务、[固定官方原包](https://static.devin.ai/cli/3000.11.92/devin-3000.11.92-x86_64-unknown-linux.tar.gz)。原版234文件／200878983字节，压缩67245544字节；SHA256为2d829139682e038cf122510f1170eee3d7060bcc7ebf92445cbc5d28c9fbcfa0，来自2026-10-21观察的官方平台manifest。[逐文件清单](upstream.json)、[server SDK固定来源](server-sdk.commit)。构建校验原包和文件，不执行原版；运行时检查root持有的原文件身份。厂商程序／文档／man手册保留独立条款。

## 解决的问题

提供可复现安装、明确权限、每次私有状态、输入输出／期限约束和自有进程清理。上游允许在用户自己的机器间复制原credentials.toml，因此无需把首次交互登录放入API流程；这条账号接入已实现，但没有账号时不宣称认证成功。

## 快速开始（CLI）

`abx run`在此使用`abx --native run`入口。先发布准确源码，以唯一运行名和公开40位提交替换<run>／<published-commit>。

使用实际native0.4.1命令及自己的Express配置，以本次部署／创建结果替换自有ID。

```bash
python scripts/prepare_steps.py devin --output /tmp/devin-steps-<run> \
  --source-commit <published-commit> --asset-transport parallel
python - <<'CONFIG'
from pathlib import Path
import yaml
p = Path("/tmp/devin-steps-<run>/template.yaml")
v = yaml.safe_load(p.read_text())
v["name"] = "devin-<run>"
p.write_text(yaml.safe_dump(v, sort_keys=False))
CONFIG
abx --native template deploy /tmp/devin-steps-<run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> devin_version
abx --native run <owned-sandbox-id> devin_native_check
abx --native run <owned-sandbox-id> devin_setup_check
# 进程启动前已配置原始账号文件；project目录须先创建：
abx --native run <owned-sandbox-id> devin --json-args '{"prompt":"Repair existing calc.py and preserve tests","cwd":"project","command_timeout":300,"allow_unsafe_tools":true}'
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

账号行仅语法检查。create-time环境不追溯配置预热服务；下文显式启动9010进程，CLI可用--server-port选择端口，认证必须匹配该进程。见[运行时环境](../docs/runtime-environment.md)。正式无账号测试调用原版--print，要求HTTP和SDK返回明确认证拒绝、文件字节不变及清理：

```bash
ABX='abx --native' python scripts/run_steps_e2e.py devin \
  --sandbox-create sdk --http --asset-transport oss
```

OSS需要[固定可选依赖](../scripts/requirements-steps-cache.txt)，只创建本次私有原包缓存，校验哈希／ACL并独立删除。steps无需本地Docker；Docker镜像另行验收。测试不注入账号／模型／操作端密钥。

## 快速开始（Python SDK）

安装[配套agent-sandbox-client](../docs/python-client-installation.md)。版本／帮助和无账号错误路径不需要账号。真实编码先在用户自己的授权机器使用原版devin auth login，按[官方认证文档](https://docs.devin.ai/cli/enterprise/devin-auth)复制敏感credentials.toml；该token可长期有效。DEVIN_CREDENTIALS_FILE是本包装层的输入文件路径，不是厂商API密钥变量。不要提交文件或放入模型提示。

下面真实账号示例仅做语法检查，缺账号时NOT_RUN。将原文件字节上传到WORKSPACE之外的私有路径、chmod0600后，显式启动独立9010服务及Bearer；模板ID必须本次自有。

```python
import asyncio, os, secrets, uuid
from pathlib import Path
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=900)
    server = None
    try:
        print(await sb.run("devin_version"))
        folder = "/home/user/devin-private-" + uuid.uuid4().hex
        await sb.commands.run("mkdir -m 700 " + folder)
        credential = folder + "/credentials.toml"
        await sb.files.write(credential, Path(os.environ["DEVIN_CREDENTIALS_FILE"]).read_bytes())
        await sb.commands.run("chmod 600 " + credential)
        project = "/home/user/app/devin-example-" + uuid.uuid4().hex
        await sb.commands.run("mkdir -m 700 " + project)
        await sb.files.write(project + "/calc.py", "def add(a,b): return a-b\n")
        token = secrets.token_urlsafe(32)
        server = await sb.start_server(port=9010, commands="/home/user/app/commands.py",
            token=token, env={"DEVIN_CREDENTIALS_FILE": credential, "ABX_PTY_PORT": "9011"})
        print(await server.commands.run("devin_setup_check"))
        result = await server.commands.run("devin", prompt="Repair existing calc.py and write report.txt",
            cwd=project, command_timeout=300, allow_unsafe_tools=True, timeout=420)
        print(result["stdout"])
    finally:
        try:
            if server is not None:
                await server.aclose()
        finally:
            try:
                await sb.kill()
            finally:
                await sb.close()

asyncio.run(main())
```

每次调用复制到全新$XDG_DATA_HOME/devin/credentials.toml并在结束后删除副本，保留调用方原文件；示例沙箱删除会移除上传件。沙箱TTL不是撤销原token。清理后独立回查不存在；不假定SDK有stop_server方法。

## 快速开始（HTTP POST）

使用已配置命令进程的转发URL和独立Bearer，JSON参数不包含厂商凭证内容。

```bash
curl --fail-with-body -X POST "$DEVIN_COMMAND_SERVER_URL/commands/devin" \
  -H "Authorization: Bearer $COMMAND_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"prompt":"Repair existing calc.py and write report.txt","cwd":"project","command_timeout":300,"allow_unsafe_tools":true}'
```

成功HTTP200封装`{"result":{"stdout":"...","stderr":"","exit_code":0,...}}`，包含stdout、stderr空字符串、exit_code0及身份字段。缺失／未知／类型错误参数400，命令认证401，未知命令404，语义／原生执行错误500。无账号拒绝是预期500程序错误路径，不是模型成功。错误只给有界退出码和类别，隐藏原始输出。/health、/commands、文件和shell共享认证边界。HTTP断开不取消云操作，仍由原期限清理。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| devin_version | 无 | 原文件身份校验及真实--version字符串 |
| devin_native_check | 无 | 原版--help；original_native/headless_print/private_config/explicit_permission/workspace_trust_control布尔字段 |
| devin_setup_check | 无 | mode/installed/pinned_version/credentials_file_set/requires_unsafe_optin/vendor_authentication_verified/compatible_model_fallback；仅状态 |
| devin | prompt必填字符串；cwd字符串默认空；command_timeout整数300；allow_unsafe_tools布尔False；model字符串默认空 | 缓冲原版最终stdout；明确授权后可执行文件／工具动作 |

prompt为1..32768UTF8字节、非空且无NUL；cwd最长4096UTF8字节、无NUL，必须解析为WORKSPACE内已有目录，空选择根目录。command_timeout整数1..600秒，布尔拒绝；allow_unsafe_tools必须精确True。model为空使用厂商默认，非空最多200ASCII字符[A-Za-z0-9_.:/-]、字母数字开头，不声明可用模型。cwd及祖先出现原生.devin目录／符号链接时原样拒绝，以保留固定私有配置。

固定argv为--config <私有JSON> --permission-mode dangerous --respect-workspace-trust false，可选--model，再加--print及原样prompt；cwd为受限项目。配置关闭更新／subagents／其他agent配置导入，私有HOME/config/data/cache/TMP隔离用户状态。原生dangerous模式使用外层自有沙箱，不启用嵌套sandbox、认证绕过或cloud模式。

原版退出0且stdout非空才返回stdout、stderr空、exit_code0、native_completed:true、native_version、archive_sha256、permission_profile:explicit-owned-sandbox-bypass、requested_model。此固定原版print是纯文本，native_completed只表示进程完成；真实代码／产物／模型结果仍需独立远程控制器验收。非零／空输出／超时／超量均报错，不返回部分成功。无任意额外argv或shell拼接。

## 配置

| 变量 | 默认／要求 | 含义 |
| --- | --- | --- |
| DEVIN_CREDENTIALS_FILE | 空；诊断／错误路径可缺，账号任务需要 | 包装层变量，模块导入捕获路径；绝对路径、WORKSPACE外、root或当前UID持有的普通非符号链接、无组／其他权限、1..65536字节合法UTF8TOML |
| WORKSPACE | /home/user/app | 导入捕获的项目根目录 |
| ABX_SERVER_TOKEN | 空／可选 | 独立命令服务Bearer，不是厂商账号 |

缺文件时让原版print明确返回登录拒绝；不执行交互登录、不虚构DEVIN_API_KEY、不借用其他模型／云密钥。子进程只收到最小私有状态环境，不继承操作端密钥或源凭证路径。返回stdout脱敏已知TOML字符串、服务Bearer／私有HOME／源文件路径；原生错误隐藏原输出。同一服务最多一个操作，重叠返回busy。

stdout和stderr各限256KiB；命令1..600秒，加最多90秒自有后代清理；客户端超时至少command_timeout+120秒。同OS用户／工具权限不是多租户文件隔离边界，只用于自有一次性沙箱及明确授权任务。

## 资源

仅Linuxx86_64，非root用户，2vCPU／4096MB／9000端口，构建限制根盘8GiB。原包展开200.9MB／压缩67.3MB。不声明KVM／Docker／GPU／桌面要求。账号任务需要厂商出口／授权账号／CLI角色。峰值RSS、认证吞吐、其他架构／提供商、交互／恢复／cloud／ACP／MCP／插件／委派均未认证。

## 已验证

尚未记录任何通过的提供方测试。

当前1.0.1将进程错误来源从Cursor修正为Devin；参数、固定原版程序、权限及成功契约不变。新的准确源码steps／SDK／HTTP／镜像验收待执行，1.0.0回执保留为历史。真实厂商账号／模型／编码仍NOT_RUN。[补充验证](../.agents/evidence/verify/2026-10-21-devin-diagnostic-origin.md)。

## 二次开发

```bash
python -m pytest -q devin/test_commands.py devin/test_controller.py devin/test_install.py
python scripts/check_template.py devin --strict
python scripts/check_docs.py
```

保留原字节／条款、官方固定哈希、显式权限、凭证输入隔离与清理。先发布COPY／helper源码再生成不可变steps，通用300MiB／15000线传限制不变。完整外部控制器必须真实执行原版无账号HTTP／SDK拒绝。取得真实账号后只在显式自有远程目标运行编码控制器：修改已有源码、原3项测试不变、报告／精确nonce、3原始和4held-out／返回后新ACK。生成代码不在操作端执行。

## 贡献

遵守[CONTRIBUTING](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.zh-CN.md)、[文档规范](../docs/documentation-standards.zh-CN.md)及[模板规范](../docs/template-spec.zh-CN.md)。独立源码、类型契约、双语文档／设计／目录和索引证据保持一致，最终head检查／review及普通固定SHA合并必需。

## 问题反馈

[Issue72](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/72)、[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。厂商认证／模型行为属于Cognition；不附凭证或私有原始日志。

## 许可证

本包装层Apache-2.0；Cognition原程序／文档／手册保留独立条款，见[声明](UPSTREAM-NOTICE.md)。Git不提交或重许可原版二进制／源码，不宣称厂商背书或独立再分发授权。
