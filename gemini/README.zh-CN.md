# gemini

## 做什么

运行官方未修改的 Google Gemini CLI0.64.0规划和文本/文件/shell工具。保留原gemini/setup/version接口；新增gemini_byok通过本项目编写的GenerateContent到Chat文本工具适配器使用显式兼容上游。原CLI和工具引擎不变，不代表Google模型、OAuth、订阅或完整功能兼容。见[官方配置](https://geminicli.com/docs/reference/configuration/)。

## 技术栈

阿里云generation2基础镜像v0.0.49/Linuxx64/Python3.13/Node20；官方npm0.64.0以SHA512锁文件校验，[upstream.json](upstream.json)固定原449文件/98597935字节各自SHA256。原压缩包20841287字节/SHA256891a794e55c8319b6b78f6f8f13d6b8b2782a4709dfd2fcabf3a1f63ae8365e6。npm ci --omit=optional --ignore-scripts排除可选交互PTY/密钥链组件和安装脚本；保留上游代码和声明。服务端34e7e011c5569f77b7f605e65313be7498f6cf02，适配器/进程管理仅标准库。[Dockerfile](Dockerfile)、[设计](../docs/design/gemini.md)、[声明](UPSTREAM-NOTICE.md)。

## 解决的问题

让明确授权的Chat网关驱动原始Gemini文本工具规划，密钥不会发往默认Google地址。适配器转换原始函数schema、参数及关联结果，不执行工具、不替代规划器。原生API环境只指向自有本地适配器并使用临时token，工具环境不含真实上游密钥。

## 快速开始（CLI）

`abx run`的native入口为`abx --native run`。使用已验证CLI0.4.1和现有授权Express配置。替换占位符，先发布精确源码再生成不可变COPY，使用唯一任务名称，等待官方READY并保存资源ID清理。

```bash
python scripts/prepare_steps.py gemini --output /tmp/gemini-steps-<unique-run> \
  --server-commit 34e7e011c5569f77b7f605e65313be7498f6cf02
python - <<'CONFIG'
from pathlib import Path
import yaml
p=Path('/tmp/gemini-steps-<unique-run>/template.yaml')
v=yaml.safe_load(p.read_text());v['name']='gemini-<unique-run>'
p.write_text(yaml.safe_dump(v,sort_keys=False))
CONFIG
abx --native template deploy /tmp/gemini-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> gemini_version
abx --native run <owned-sandbox-id> gemini_native_check
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

规范资源流程：`ABX='abx --native' python scripts/run_steps_e2e.py gemini --sandbox-create sdk --http`。无需本地Docker；steps不等于镜像云端部署。已配置模型进程使用`abx --native run <owned-sandbox-id> gemini_byok --json-args '{"prompt":"Repair existing calc.py and preserve tests","cwd":"project","command_timeout":300}'`。

## 快速开始（Python SDK）

发行名agent-sandbox-client，遵循[固定配套源码安装](../docs/python-client-installation.md)。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox
async def main():
    sb=await Sandbox.create(template='<owned-template-id>',timeout=900)
    try:
        print(await sb.run('gemini_version',timeout=60))
        print(await sb.run('gemini_native_check',timeout=60))
    finally:
        await sb.kill()
asyncio.run(main())
```

命令进程启动前设置全部GEMINI_BYOK_*变量，检查gemini_byok_setup_check，再调用`await server.commands.run('gemini_byok',prompt='Repair existing calc.py; preserve tests',cwd='project',command_timeout=300,timeout=420)`。项目需预先创建。独立服务用sb.server_at(port,token=...)，关闭借用客户端。预热9000不会获得后续create环境，遵循[显式进程配置](../docs/runtime-environment.md)；独立9010进程使用匹配的独立Bearer。结果是缓冲后的直接对象。

## 快速开始（HTTP POST）

ABX_SERVER_URL来自对应进程sb.network.get_url(port)，服务Bearer与平台/模型密钥独立。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/gemini_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header 'Content-Type: application/json' --data '{}'
```

HTTP200返回{"result":"0.64.0"}。POST/commands/gemini_byok接收直接{prompt,cwd,command_timeout}JSON。缺失/未知/类型参数400、认证401、未知命令404；执行/语义错误500并脱敏。断连不取消已发上游任务，仍执行有界自有清理。

## 命令参考

| 命令 | 参数 | 结果及副作用 |
| --- | --- | --- |
| gemini_version | 无 | 原CLI0.64.0，无模型 |
| gemini_native_check | 无 | 原449文件身份及实际帮助参数original_native/headless_json/explicit_approval/owned_project_include |
| gemini_byok_setup_check | 无 | mode及model_key_set/model_base_set/model_set、vendor_account_verified:false/provider_default_fallback:false；不返回值，不发网络请求 |
| gemini_byok | prompt必需，非空1..32768UTF8字节/无NUL；cwd默认空字符串、最多4096字节、解析后位于WORKSPACE内的已有目录；command_timeout整数默认300、1..600秒、拒绝布尔值 | stdout/exit_code0/native_completed/native_version/archive_sha256/model/protocol/model_calls/native_tool_results/relay_calls；原生工具修改项目，不返回完整轨迹 |
| gemini_setup_check | 无 | 旧installed/version/pinned_version/密钥模型存在标志/workspace/设置路径、存在和JSON有效性；不修改配置、不认证 |
| gemini | prompt必需非空字符串；model默认空，再GEMINI_MODEL，再gemini-3.1-flash-lite；cwd默认空、已有且位于工作区内；command_timeout整数默认600、1..1800秒；yolo布尔默认False | 旧原生缓冲JSON字符串。False选择plan，True显式允许运行工具。必须GEMINI_API_KEY，不隐式复用OpenAI密钥/OAuth。新增隔离保证不覆盖旧模式 |

新增固定参数--prompt/--model/--output-format json/--approval-mode yolo/--include-directories <项目>。启动cwd为新建私有目录，提示明确项目绝对路径；固定SHA256且root持有的/opt/gemini/profile.json系统设置固定gemini-api-key认证、16模型会话轮，禁用hooks/skills/子Agent/更新/遥测，无配置MCP或已安装扩展。原生核心工具仅read_file/write_file/replace/run_shell_command/list_directory/glob/grep_search，不提供委派工具。原始及生成代码仅在自有可丢弃沙箱执行，项目指令仍是不可信输入。

仅转换文本与原生函数声明/结果；保留ID，原生缺失ID时按同一历史中名称顺序关联。明确转换Google schema类型大小写/nullable。拒绝图像/thinking/未知内容工具/错误结果关联/截断回复/错误模型路径token/重定向。Chat缓冲后输出原GenerateContent SSE，实际用量来自上游。最多32请求、请求2MiB、响应4MiB、原生16轮、stdout/stderr各256KiB；截止时间后最多额外90秒自有清理，客户端至少command_timeout+120，并发返回忙。成功要求原始非空成功回复、正数完成请求且无失败；编码另需原生工具结果和独立产物测试。

## 配置

| 名称 | 默认及要求 | 含义 |
| --- | --- | --- |
| GEMINI_BYOK_API_KEY | 空，BYOK必需 | 显式兼容上游密钥，仅父适配器持有 |
| GEMINI_BYOK_BASE_URL | 空，BYOK必需 | HTTPS Chat基址，最多2048字符，无userinfo/query/fragment；固定测试允许字面环回HTTP |
| GEMINI_BYOK_MODEL | 空，BYOK必需 | 真实选定模型，1..200允许标识字符 |
| GEMINI_API_KEY | 空，仅旧模式 | 原Google/原生兼容密钥，BYOK不隐式复用 |
| GEMINI_MODEL | gemini-3.1-flash-lite，仅旧模式 | 原有默认值，与显式BYOK模型分离 |
| WORKSPACE | /home/user/app | 已有项目根目录 |
| ABX_SERVER_TOKEN | 空，可选 | 独立命令服务Bearer |

BYOK模块导入时捕获设置，密钥最多8192字符且无控制字符。原生环境仅临时本地token、最小PATH、私有HOME/config/cache；真实密钥只发往精确授权Chat来源。同用户OS访问仍存在，cwd与环境过滤不是另一个租户边界。旧配置行为单独保留。结果与错误不包含私有地址、密钥或完整轨迹。

## 资源

声明2vCPU4096MB/Linuxx64/9000端口/8GiBrootfs预算，不需KVM/嵌套Docker/GPU/显示器。原包98.6MB，基础镜像已有Node20；排除可选交互组件。需授权模型出网。未认证峰值内存、镜像云端部署、其他提供商、Google OAuth/订阅及完整交互/恢复/PTY/图像/thinking/MCP/插件/委派产品。

## 已验证

当前2.1.1提供商、原生、模型和镜像资格待执行。本地81项固定及旧协议/进程/controller测试通过、1项跳过，9.40秒；跳过的是操作端未安装的真实CLI。原包校验、源码检查和固定测试不是原生/云端/模型验收。此前2.0.1回执保留为不可变历史，不能认证本次变更。

## 二次开发

```bash
python -m pytest -q gemini/test_byok.py gemini/test_adapter.py gemini/test_controller.py gemini/test_commands.py gemini/test_e2e_protocol.py
python scripts/check_template.py gemini --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py gemini --sandbox-create sdk --http
```

保留原始文件清单/锁/声明、真实密钥隔离、严格来源和内容拒绝、自有进程/RPC/私有目录/监听器清理。本地仅不执行代码的固定回复，原生及模型生成代码只在新建自有云目标执行。主e2e分发到当前严格BYOK controller，旧辅助和回归保留；记录分发与byok_e2e_test.py两者哈希。要求源码变化、原3测试字节不变、报告/精确nonce/原3加4隐藏测试/返回后新ACK和独立自有资源缺席确认。

## 贡献

遵循[CONTRIBUTING](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.zh-CN.md)、[文档规范](../docs/documentation-standards.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)，包含所属记录/证据、双语契约、最新提交检查review和正常合并。

## 问题反馈

[Issue30](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/30)、[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。原始上游行为使用上游渠道，不附加密钥或私有轨迹。

## 许可证

本模板/适配器及原Gemini CLI分别遵循各自Apache-2.0及[原始声明](UPSTREAM-NOTICE.md)，保留打包的第三方条款。[仓库许可](../LICENSE)。不代表Google背书或托管模型访问权。
