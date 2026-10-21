# 平台与产品可行性

[English](README.md)。审查日期2026-10-21。Issue [37](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/37)、[38](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/38)、[39](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/39)、[42](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/42)、[43](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/43)明确允许有证据的决策／集成设计；这里交付该结果，并不宣称产品模板通过验证。

| 产品 | 当前决定 | 继续实现所需 |
| --- | --- | --- |
| Windows Agent Arena | 暂不打包完整Windows虚拟机；不以Linux版本查询替代产品 | 自有且有授权的Windows11 WAA快照／原版Windows服务，或合适虚拟机宿主 |
| Phone sandbox | 暂不实现Android设备分配；未建立可用设备池 | 真正可授权分配的Android设备／模拟器及控制通道 |
| AndroidWorld | 暂不执行完整原版评测 | API33／Pixel6兼容模拟器、原版应用、ADB和模拟器gRPC可访问性服务 |
| K3s | 本次非root／generation2环境无合格模板，保留七轮真实失败记录 | 实际支持原版API的profile；完整集群另需特权容器／工作节点网络 |
| Omarchy | 不把Arch系统维护脚本包装为Debian应用 | 独立配置的Arch／Omarchy桌面或虚拟机及明确维护任务 |

## 实测环境与证据

真实SDK创建的自有Express托管base执行了[只读探测](../../scripts/guest_runtime_features.py)：UID1000、Linux x86_64、Debian13，未开放/dev/kvm、/dev/dri、/dev/net/tun和Docker socket；打开KVM返回ENOENT。镜像未预装Docker、Podman、QEMU、Android模拟器／ADB、pacman、systemctl、hyprctl。用户命名空间探测退出0，挂载命名空间退出1。尽管创建参数请求4096MB，客体MemTotal只观察到2093MiB，因此不把请求值当成实际可用内存。沙箱删除后独立查询确认不存在。

[SDK与清理证据](../../.agents/evidence/verify/2026-10-21-express-guest-features.json)、[上游固定提交与文件哈希](../../.agents/evidence/verify/2026-10-21-hardware-products-upstream.json)、[其他提供商前置检查](../../.agents/evidence/verify/2026-10-21-other-provider-prerequisites.json)。缺少预装软件不等于不能安装；没有KVM也不能单独证明软件模拟不可行。本次没有通过模拟器启动、Windows桌面操作、AndroidWorld任务／重置／原版评测或Omarchy系统更新，不新增误导性tested_on或可安装目录。

## 提供商范围

Express的SDK环境探测和独立清理通过，四种产品本体验收NOT_RUN。alicloud-container没有显式集群域名／API地址／独立密钥；未验证ACS／ACK设备能力。OpenSandbox和CubeSandbox没有显式配置；默认本地TCP接受连接，但/openapi.json、/sandboxes、/health只读请求均RemoteProtocolError，未确认兼容服务可用。不能把TCP连接成功当作提供商API正常。没有显式ABX_E2B_API_KEY；通用E2B_API_KEY与Express别名相同，未向其他提供商发送。没有新建集群、修改无关本地服务或把Express模板ID转换成另一提供商镜像ID。

## Windows Agent Arena

[原版README（6d39ed88）](https://github.com/microsoft/WindowsAgentArena/blob/6d39ed88c545a0d40a7a02e39b928e278df7332b/README.md)需要Docker宿主、约30GB的Windows11黄金快照及初始化所需约6GB的授权评估ISO。[原版启动器](https://github.com/microsoft/WindowsAgentArena/blob/6d39ed88c545a0d40a7a02e39b928e278df7332b/scripts/run.sh)默认8G虚拟机内存、请求NET_ADMIN，并支持无KVM时KVM=N，故不能断言没有KVM就永远不能运行。原版完整工作流尚未适配仓库非root／8GiB源镜像约束；单纯导入评测模块或模拟HTTP不能证明Windows任务。

远程设计：在用户自有且有授权的Windows虚拟机运行原版服务，固定Linux客户端／评测器，通过明确授权的私有通道连接，从重置、截图、动作到原版评测执行真实任务，独立检查文件／应用状态并保留原始评测器。仅清理本次会话与文件，不删除用户虚拟机；实现API前先审查上游真实服务契约，不虚构通用远控接口。缺少该虚拟机，此流程NOT_RUN。

## Phone sandbox

已测Express没有可用Android设备／KVM／设备管理器，其他可用配置未建立设备池。这不代表相关提供商永远不支持设备。后续必须明确真实设备API，固定Android镜像／API／ABI及应用授权，认证分配设备，检查启动与ADB身份，实际执行输入／截图／文件往返并清理自有租约。重连、重置、取消须保留其他设备；安装ADB或回显服务不能代替该验收。软件模拟的兼容性与性能未测。

## AndroidWorld

[原版README（f8e78c0）](https://github.com/google-research/android_world/blob/f8e78c0ab0bb8b5daa681afd0296ed0193a98f1f/README.md)及[env_launcher](https://github.com/google-research/android_world/blob/f8e78c0ab0bb8b5daa681afd0296ed0193a98f1f/android_world/env/env_launcher.py)面向Pixel6／API33，要求已启动的模拟器和gRPC8554可访问性通道；文档Docker运行需要--privileged。普通真机或单独远程ADB不足以证明兼容。软件模拟未测试。

远程设计：由自有兼容宿主转发原版模拟器控制台／ADB及认证gRPC，固定上游与应用，调用原版load_and_setup_env，执行选定原版任务及评测，检查前后状态和重复重置。设备身份、观察、输入和评测成功均须真实；模型另行验收。仅清理本次转发／进程／任务文件，保留用户设备。当前无兼容模拟器，NOT_RUN。

## Omarchy

[原版仓库（087f73d8）](https://github.com/omacom/omarchy/tree/087f73d899b456ce5275ebf27294d379585fbdb1)确实有CLI和无头维护脚本，不能写成“没有CLI”。[omarchy-version](https://github.com/omacom/omarchy/blob/087f73d899b456ce5275ebf27294d379585fbdb1/bin/omarchy-version)查询Arch的pacman安装包；[omarchy-update](https://github.com/omacom/omarchy/blob/087f73d899b456ce5275ebf27294d379585fbdb1/bin/omarchy-update)依赖系统包管理及特权Bash／sudo边界。非默认源码路径显示dev并不证明桌面已安装。[官方安装指南](https://learn.omacom.io/2/the-omarchy-manual/50/getting-started)描述ISO／独立磁盘发行版。

暂不创建源模板：远程维护独立Arch桌面可能有价值，但当前没有该系统，也没有证据支持把更新脚本复制进Debian。未运行破坏性安装或系统更新。取得自有兼容虚拟机和具体任务后，再验证原版包／版本、有限操作的实际状态与清理。通用shell模板改名不能作为Omarchy实现。

## 复现与继续条件

使用[配套Python客户端](../python-client-installation.md)和自己的提供商配置，按[英文可执行SDK示例](README.md#reproduce-the-guest-observation)将scripts/guest_runtime_features.py写入自有沙箱、通过commands.run执行，kill后独立get_info_by_id确认不存在。已记录运行还通过唯一metadata在私有日志中核对不确定的创建结果。该过程只是特征探测，不是四个产品的运行。未提供已认证产品的deploy／steps配方，不应执行虚构命令。完整原版环境、真实任务、回归、SDK／HTTP、清理与镜像通过后才能增加可安装条目及提供商资格；新运行保留独立日期证据。
## K3s

[Issue42](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/42)明确预期Express可能不支持，并允许依据证据作决定。当前不发布K3s可安装条目。完整工作节点／容器运行时嵌套尚未建立；较小的原版无agent控制面校验实验也未通过真实API就绪与服务端校验验收。

七轮真实极速版验收使用原版v1.37.1+k3s1、上游提交356c025475bbefaa09cf0d7e48e8e2adbbde57db、81543330字节原始二进制及SHA25692b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0，实际经历steps准备、READY、SDK创建、原版CLI／HTTP版本与帮助及API启动尝试。完整原生验收七轮均失败，各轮自有沙箱／模板／缓存均独立确认清理。[准确记录](../../.agents/evidence/verify/2026-10-21-k3s-final-feasibility.json)。

实际故障包括原版默认路由选址、API拒绝链路本地广播地址；显式节点IP修复第一项，查询已分配网卡仍未在本次自定义worker建立合格非链路本地地址。独立托管base客体存在可用网卡，不能据此证明另一注册镜像／profile成功；这些结果也不能证明所有Express部署均不可能。不使用虚构广播地址、修改上游二进制或跳过就绪门禁。

[未取得资格的审查实验](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/tree/0e28a5021473e11ed549fad6b08e5ccd796f9b07/k3s)与[拒绝原型的工程决定](../../.agents/notes/rejected/2026-10-21-k3s-agentless-validation.md)保留来源与限制，仅作研究历史。当前目录不提供`abx template launch ...//k3s`或deploy／steps安装操作。

以后实现需实际可访问的适合提供商／profile、准确原版固定来源及许可证、真实就绪、SDK触发的合法／非法清单服务端校验与独立清理。完整Kubernetes声明还需真实工作节点、容器运行时、Pod调度／执行及网络／存储结果；无agent切片不能代替。托管OpenSandbox解释器验证属于另一产品，不证明特权K3s支持。其他提供商表记录最初操作者环境；后续托管解释器结果见[独立指南](../managed/opensandbox-code-interpreter/README.zh-CN.md)。
