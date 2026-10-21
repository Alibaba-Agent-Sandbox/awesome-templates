# 暂缓项目与已实现切片

[English](backlog.md)。验收以[模板规范](template-spec.zh-CN.md)和当前模板回执为准。旧研究、失败和合并历史仍保留；固定版本、目录或PR合并本身不能证明提供商／模型成功。源模板与提供商托管ID的构建、运行契约不同。

## 已实现切片

| 产品 | 当前权威实现 | 范围 |
| --- | --- | --- |
| SWE | [原版任务与独立评测](../swe/README.zh-CN.md) | 明确的非Docker切片，不宣称完整排行榜 |
| OSWorld | [真实非特权桌面及原版评测](../osworld/README.zh-CN.md) | 选定原生桌面／浏览器任务；完整VM／应用集另行验收 |
| Pi | [固定原版编码CLI](../pi/README.zh-CN.md) | 显式工具权限及兼容模型，不代表E2B注册 |
| Aider | [固定原版CLI及源码修改验证](../aider/README.zh-CN.md) | 有限工作区与显式写入权限 |
| Grok Build | [官方原生CLI](../grok/README.zh-CN.md) | 固定版本／原包及厂商兼容配置；旧安装研究为历史 |
| QM | [原版harness与真实SDK后端](../qm/README.zh-CN.md) | 声明的工具／上下文／后端切片，不代表完整scope／快照 |
| QM sandbox | [原版QM工具上下文](../qm-sandbox/README.zh-CN.md) | 实际Agent Sandbox HTTP SDK后端，不代表Superserve注册 |
| Gemini | [原版CLI及显式兼容传输](../gemini/README.zh-CN.md) | Google认证与兼容模型／工具测试分别记录 |
| Kimi Code | [固定原版CLI](../kimi-code/README.zh-CN.md) | 以当前源码、命令和回执为准 |
| Goose | [固定原生运行时](../goose/README.zh-CN.md) | 显式配置模型和自有工作区，不依赖浮动安装声明 |

具体资格查看各README的已验证章节、manifest及日期回执。旧调查的draft、tested_on为空或未实现描述不能作为这些已交付源码的当前状态。原始失败记录保留为历史。

## Windows Agent Arena、手机沙箱、AndroidWorld、Omarchy

[有证据的可行性审查](feasibility/README.zh-CN.md)交付Issue37／38／39／43明确允许的决策方案；没有新增虚假已验证源模板。

- WAA依赖原版Windows11及快照；启动器支持KVM=N，不能单凭没有KVM就否认软件模拟。远程Windows原版任务／评测仍为设计，未运行。
- 手机沙箱需要真实设备租约与可观察操作；当前可用配置未建立设备池。
- AndroidWorld需要兼容API33模拟器、ADB和gRPC可访问性通道，远程真机或已安装Python包不能代替；软件模拟未测。
- Omarchy有CLI／无头维护脚本，但它们管理Arch桌面／系统。复制到Debian或显示源码dev版本不能算实际运行。

审查含真实Express SDK客体探测、独立清理、上游固定来源、提供商前置检查及远程集成验收设计，不宣称产品任务／模型通过。

## K3s

[Issue42](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/42)按其明确允许的证据决策路径处理。[七轮真实原生尝试及当前profile决定](feasibility/README.zh-CN.md#k3s)保留就绪／校验失败与自有资源独立清理；当前不发布可安装K3s模板或已验证工作集群。原版产品能在合适profile实际通过验收后再恢复实现。

## 其他研究

[市场调查](template-market-survey-2026-10.md)为日期研究输入；当前[目录](../awesome-templates.yaml)、源码README和Issue决定交付状态。OpenHands等新产品变体仍需固定来源、设计、有用API、实际调用测试和提供商证据；不能从Express部署推断其他提供商ID。
