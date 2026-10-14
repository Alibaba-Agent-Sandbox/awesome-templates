# 这批不做

下面这些先不要在 `awesome-templates` 里建目录。验收要求是：一个目录、一份 `python:3.12-slim` 的 Dockerfile、`commands.py` 里的 `@command` 真正去调上游 CLI，再用带密钥的 e2e 跑通。底层跑不了，或者安装方式还没钉成可复现的包版本，就留在这里。

`abx template install` 只在阿里云极速版（`alicloud-express`）上构建。新建一个目录不会变成 OpenSandbox 镜像，也不会变成 E2B 的 template id。

## SWE-bench / SWE-agent

SWE-bench 按实例评分：每道题有自己的仓库快照和 `FAIL_TO_PASS` 测试，官方 harness 用该实例的 Docker 镜像跑测试。SWE-agent 的入口是 `sweagent`，它自己再起一个环境去改仓库。

缺的是评测底层，不是又一个编码 CLI。当前沙箱是单个容器里的 `agent_sandbox.server`，没有实例镜像仓库，也没有从沙箱里启动兄弟容器的权限。嵌套 Docker 和下面的 K3s 是同一类缺口。没有这层，命名命令无法检出题目、跑隐藏测试、交回补丁分数。

## OSWorld

OSWorld 在一台带桌面的虚拟机里做计算机使用评测：截图或无障碍树进、鼠标键盘出。任务跑在 Ubuntu（也有 Windows）客户机上，不是一条 headless CLI。

缺虚拟机管理器、桌面会话、截图通道和输入注入。本仓库的 `desktop` 只是 E2B 上已有的 template id，OpenSandbox 没有接这张镜像，也不能当作 OSWorld 的客户机。一个 `python:3.12-slim` 目录替代不了这台虚拟机。

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

## Pi（E2B 的 `pi`）

Pi 是终端编码代理，自己的非交互入口是 `pi -p "<prompt>"`。E2B 已经发布了预置模板 id `pi`（文档里的创建方式是 `e2b sbx create pi`，或 `Sandbox.create('pi')`，密钥 `E2B_API_KEY` / `ANTHROPIC_API_KEY`）。在 E2B 上再派生用 `Template().fromTemplate('pi')`。

缺的是 E2B 模板注册这条链路。`abx template install` 写不进 E2B。在本仓库放一个 `pi/` 目录，不会变成 E2B 上那个 `pi`，也不会替换 `e2b sbx create pi` 拉起的镜像。要改 E2B 的 Pi 环境，用 E2B 的 template build，而不是极速版的安装命令。

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

- Gemini CLI：命令 `gemini -p "<prompt>"`（包 `@google/gemini-cli`，密钥 `GEMINI_API_KEY`）。非交互把提示词交给一个进程并退出，和 `claude -p` 同一类。
- Kimi CLI：命令 `kimi -p "<prompt>"`（包 `@moonshot-ai/kimi-code`）。`-p` 不进 TUI，脚本场景再用 `kimi --print -p "<prompt>"` 自动批准工具调用。
- Aider：命令 `aider --yes --message "<prompt>"`（PyPI 包 `aider-chat`）。它直接改当前 git 仓库并退出，适合收成一个带 `prompt` 的命名命令。
- OpenHands：命令 `openhands --headless -t "<task>"`。headless 必带 `-t` 或 `-f`，并且会自动批准动作，适合收成一个带任务文本的命名命令。
- Goose：命令 `goose run -t "<text>"`（长选项 `--text`）。`goose run` 执行完这段文本就退出，和命名命令「入参是一段任务、返回进程输出」的形态一致。
