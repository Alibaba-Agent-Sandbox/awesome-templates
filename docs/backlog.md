# 暂缓项目与已启动切片

已启动的 Pi、Aider、SWE 和 OSWorld 浏览器切片见下文；其余计划尚未交付。验收以 [template-spec.md](./template-spec.md) 为准，实际运行时、固定版本和对应级别证据必须匹配。

`abx template install` 只在阿里云极速版（`alicloud-express`）上构建。新建一个目录不会变成 OpenSandbox 镜像，也不会变成 E2B 的 template id。

## SWE-bench / SWE-agent

[swe](../swe/README.md) 实现一个明确的非 Docker 切片：官方 mini-swe-agent 2.4.6、真正的 `pallets__flask-5014` base/test_patch、1FAIL+59PASS 基线及全新目录/venv 中的60项独立评价。显式授权才执行模型 shell，输出源码补丁与报告；不会下载整份数据集，也不包含标准答案补丁。实现与验收状态见 [Issue35](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/35) 和 [设计](./design/swe.md)。

仍缺官方每题 Docker 镜像和原始 Python3.11 环境；首个 Python3.13 镜像被原始弃用警告门槛拒绝，评测现固定官方 SHA 的原题 Python3.11.10；仍需单独验证新环境，不能发布官方 SWE-bench 分数。完整 SWE-agent、任意实例、批量 benchmark、SWE-rebench 和需要额外系统依赖的题目继续留在 backlog。沙箱没有 Docker 不能推出所有非 Docker 子流程都不可做。

## OSWorld

完整 OSWorld benchmark 仍需要各应用、VM 快照/reset 和相应任务/evaluator 集合；它不是一条 headless CLI。Express 无 KVM，不能据此承诺完整 benchmark 或排行榜分数。

[Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) 明确允许非特权桌面切片。新的 [osworld](../osworld/README.zh-CN.md) 目录独立基于 Alibaba 镜像，固定上游源码，提供真实 Xvfb/Openbox/DBus/Chromium、截图、AT-SPI、原生鼠标键盘/私有剪贴板 Unicode 输入，以及明确的浏览器 task 配置和上游评估函数子集。native 源码任务及独立 DOM/PNG 验证已通过；9a53b56 镜像已实际通过 L1、官方注册后的 Express 三端真实 GUI smoke、HTTP18/0skip 与 owned 清理。该补充 changed-image 云验证不替代完整 `abx template deploy`/规范 L2 runner，tested_on 仍空、状态仍 experimental。详见[最终证据](../.agents/evidence/verify/2026-10-16-osworld-changed-image.md)。Office、任意 launch/shell、VM/完整 benchmark 不包含在此切片，原 Issue 保持开放。它不是复制 E2B `desktop` template id，也不声明 OpenSandbox 客户机已可用。

## Windows Agent Arena

Windows Agent Arena 的任务跑在 Windows 客户机里，应用和评测脚本都是 Windows 的。

缺 Windows 虚拟机镜像和能启动它的虚拟化。极速版沙箱是 Linux 容器。验收已经写明：需要 Windows 虚拟机的评测不要做目录项。

## 手机沙箱

手机沙箱要的是一台设备或一台模拟器：屏幕、触摸，通常还有 adb 或厂商的设备协议。

缺设备集群或模拟器控制面，沙箱 API 里没有「插上一部手机」这种资源。是否做，等到底层有设备或模拟器之后再定。现在建目录也没有可调用的运行时。

## Android World

Android World 在 Android 模拟器里跑任务，通过 adb 和无障碍树操作应用。模拟器要 AVD 系统镜像，并且要 `/dev/kvm`（或同等嵌套虚拟化）。

缺 KVM 设备和系统镜像。当前容器不提供这块设备，`python:3.12-slim` 里也没有模拟器。和手机沙箱是同一类缺口，只是评测套件已经公开。

## Grok

xAI 的编码 CLI 已经存在：命令是 `grok`，非交互是 `grok -p "<prompt>"`，自动批准工具调用时加 `--always-approve`，密钥是 `XAI_API_KEY`。上游安装文档写的是 `curl -fsSL https://x.ai/cli/install.sh | bash`。

这批仍不建目录。那个安装入口是一段不钉版本的脚本，`docker build` 日志里看不到像 `@qwen-code/qwen-code@0.23.0` 这样的固定版本。验收要求先核实安装方式，再写进目录。缺的是可复现的安装物（钉死版本的包或二进制）以及一份对着这个二进制的 `commands.py`。Grok 自己的 `--sandbox` 是 CLI 内部的权限档，不是 Agent Sandbox 的模板。

## Pi（Alibaba 独立 CLI 切片）

[pi/](../pi/README.zh-CN.md) 已作为独立 experimental 模板实现：在 Alibaba 基础镜像内安装官方 `@earendil-works/pi-coding-agent@1.3.0` 和经 SHA256 校验的 Node 24.16.0，提供一次性 print 模式、只读诊断与显式可写工具。默认工具是 read/grep/find/ls；`allow_tools=true` 才允许 edit/write/bash。模型端点由 PI_BASE_URL、PI_MODEL、PI_API_KEY 配置，不复用用户扩展或持久会话。

官方 CLI 的本地源码服务已用 `qwen3.8-flash` 完成真实编程验收：先重现失败测试，模型改源码并生成新产物，保留原测试，再由独立进程运行隔离 unittest 与 held-out 检查。Pi 镜像 L1 正由独立 [PR #86](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/86) 的实际 CI 验证；镜像 Express L2 和镜像模型 L3 尚未通过，不列入 provider verified。详见[设计](design/pi.md)与[验证记录](../.agents/evidence/verify/2026-10-16-pi-runtime.md)。

E2B 的预置 `pi` template ID 及其注册/派生流程是另一条路线。本仓库安装 Alibaba CLI 模板既不向 E2B 注册，也不替换或验证 E2B 的镜像；E2B 注册缺口不再阻塞这个独立 Alibaba 切片。交互 TUI、RPC 会话和扩展安装不在本次命令面内。

## Aider（Alibaba 独立 CLI 切片）

[aider/](../aider/README.zh-CN.md) 已作为 independent experimental 模板实现，安装官方 PyPI `aider-chat==0.86.2`。该包要求 Python `>=3.10,<3.13`，因此单独固定 SHA256 校验的 Python 3.12.12，保留 Alibaba base 的 Python 3.13 server 和 Node 20。默认 ask 只读；显式 `allow_write=true` 才把选中文件的 stage 结果回写，禁自动提交、slash/bang 命令分派与自动确认。

实际 CI 镜像已完成独立 Express push、官方注册/READY、SDK/HTTP/CLI 和真实模型验收：预热 server 不会追溯接收 create-time envd 配置，需明确 `commands.start(env=...)` 启动镜像原 commands 的 9010 进程，并用对应端口访问。Qwen3.8-flash 真实改已有源码、生成报告及精确产物，原测试不变，独立 3 个 unittest 和 6 个 held-out 计算通过（完整模型 suite 21 PASS / 0 FAIL / 0 SKIP）。全部自有资源已清理回查。

[PR #88](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/88) 保持 draft；canonical `express_e2e.py` / `abx template deploy` L2 wrapper 尚未通过，不列入 provider verified。详见[设计](design/aider.md)、[补充镜像证据](../aider/evidence/image-runtime-2026-10-16-configured.json)和[工程验证记录](../.agents/evidence/verify/2026-10-16-aider-runtime.md)。

## K3s

K3s 要在节点上跑容器运行时：特权模式、cgroup、往往还要 `/dev/kmsg` 和内核模块。验收已经写明：沙箱里再跑需要特权嵌套容器的集群，不要做目录项。

缺嵌套容器权限和集群网络。当前数据面是容器里的 HTTP server，不是一个 Kubernetes 节点。

## Omarchy

Omarchy 是一套 Arch Linux 桌面配置（Hyprland 会话），安装对象是一整台 Arch 机器上的显示环境。它没有一条可以在无头容器里用提示词调起来的编码 CLI。

缺显示服务器、Hyprland 和 Arch 引导。验收对「只有桌面配置、没有可调用 CLI」的项目不建目录。

## qm

[yc-software/qm](https://github.com/yc-software/qm) 是一个带可插拔沙箱后端的 Agent 运行时。执行环境走它自己的 `Sandbox` 接口，后端包括本地 Docker、AWS MicroVM、E2B、Modal、Superserve 等。它不是一个 `qwen -p` 这种单二进制编码 CLI。

缺 QM 的后端路由和它选中的那套沙箱 API。本仓库的命名命令跑在 `agent_sandbox.server` 上，接不上 QM 的 scope、快照和后端租约。把 QM 的源码 COPY 进 `python:3.12-slim` 也不会得到那些后端。

## qm-sandbox

这是 QM 的沙箱层，不是又一个 CLI。文档里的一种具体接法是 Superserve：`SANDBOX_BACKEND=superserve`，模板名 `SUPERSERVE_TEMPLATE=qm-agent-0.1.0`，再加 `SUPERSERVE_API_KEY`。沙箱由 Superserve 从它自己的模板创建，虚机规格跟模板走。

缺 Superserve（或 QM 列出的其他后端）的控制面。极速版的 `abx template install` 不会注册 Superserve 模板，也不会把本仓库的 Dockerfile 变成 `qm-agent-0.1.0`。

## 以后可以单开一批的真实 CLI

这些是已经有非交互命令的编码 CLI，形态和现在的 `claude` / `codex` / `qwen` 相同：一个二进制、一段提示词、进程退出。做的时候仍要钉安装版本、写 `@command`、用密钥跑通 e2e。下面不写安装命令。

- Gemini CLI：目录 `gemini/` 已经按 experimental 接上 `@google/gemini-cli@0.64.0`，命令是 `gemini -p <prompt> --yolo --model <model>`，密钥 `GEMINI_API_KEY`。还缺带密钥且输出含 `ABX_E2E_OK` 的记录，所以不能标 official。
- Kimi CLI：命令 `kimi -p "<prompt>"`（包 `@moonshot-ai/kimi-code`）。`-p` 不进 TUI，脚本场景再用 `kimi --print -p "<prompt>"` 自动批准工具调用。
- OpenHands：命令 `openhands --headless -t "<task>"`。headless 必带 `-t` 或 `-f`，并且会自动批准动作，适合收成一个带任务文本的命名命令。
- Goose：命令 `goose run -t "<text>"`（长选项 `--text`）。`goose run` 执行完这段文本就退出，和命名命令「入参是一段任务、返回进程输出」的形态一致。
